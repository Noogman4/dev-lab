"""Fixed profile boundary, worker agreement and owner-only visualizer replacement."""

import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
from types import SimpleNamespace
import tkinter as tk

import pytest
from PIL import Image

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_profile as profiles, projectm_pixels as pixels
from netmon.core import projectm_frontend as frontend, projectm_display as display
from netmon.core import (
    projectm_pixel_worker,
    projectm_display_worker,
    projectm_frontend_worker,
)
from netmon.ui import projectm_pixel_window as ui


def wait(predicate, root=None):
    deadline = time.monotonic() + 4
    while not predicate():
        assert time.monotonic() < deadline
        if root is not None:
            root.update()
        time.sleep(0.002)


@pytest.mark.parametrize("profile", profiles.PROFILES, ids=lambda p: p.key)
def test_profile_sizes_fragmented_frames_and_latest_mailbox(profile):
    parser = pixels.RawFrames(profile.key)
    mailbox = pixels.FrameMailbox(profile.key)
    frame = b"\x12\x34\x56\xff" * (profile.width * profile.height)
    data = frame * 2 + b"partial"
    for offset in range(0, len(data), pixels.CHUNK):
        result = parser.feed(data[offset : offset + pixels.CHUNK])
        if result is not None:
            mailbox.put(result)
    assert mailbox.take() == frame and mailbox.take() is None
    assert mailbox.received == 2 and mailbox.dropped == 1
    assert parser.buffer == b"partial"
    assert parser.peak <= profile.frame_bytes + pixels.CHUNK
    with pytest.raises(ValueError):
        mailbox.put(frame[:-1])
    with pytest.raises(ValueError):
        mailbox.put(frame + b"x")
    if profile.key != profiles.DEFAULT:
        with pytest.raises(ValueError):
            mailbox.put(b"x" * pixels.FRAME_BYTES)


@pytest.mark.parametrize(
    "key", [None, True, 1080, "1920x1081", "4096x2160", "../640x480", "640x480\n"]
)
def test_unknown_profile_fails_before_any_start(key, monkeypatch, tmp_path):
    def forbidden(*a, **kw):
        raise AssertionError(
            "No runtime or resource acquisition before profile validation"
        )

    monkeypatch.setattr(frontend, "_runtime", forbidden)
    monkeypatch.setattr(display, "_runtime", forbidden)
    monkeypatch.setattr(pixels, "_runtime", forbidden)
    for start in (
        lambda: frontend.start(None, tmp_path, resolution=key),
        lambda: display.start(resolution=key),
        lambda: pixels.start(None, resolution=key),
    ):
        with pytest.raises(ValueError):
            start()


@pytest.mark.parametrize("profile", profiles.PROFILES, ids=lambda p: p.key)
def test_all_workers_use_selected_profile_and_lower_limits(profile, monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["worker", "--resolution", profile.key])
    monkeypatch.setattr(projectm_pixel_worker.resource, "getrlimit", lambda _: (32, 64))
    monkeypatch.setattr(
        projectm_pixel_worker.resource, "setrlimit", lambda n, v: calls.append((n, v))
    )
    monkeypatch.setattr(os, "execv", lambda exe, argv: calls.append((exe, argv)))
    for worker in (
        projectm_pixel_worker,
        projectm_display_worker,
        projectm_frontend_worker,
    ):
        calls.clear()
        assert worker.main() is None
        assert all(bound == (32, 32) for _, bound in calls[:-1])
        exe, argv = calls[-1]
        if worker is projectm_pixel_worker:
            assert argv[argv.index("-video_size") + 1] == profile.key
        elif worker is projectm_display_worker:
            assert f"{profile.key}x24" in argv
            assert "-nolisten" in argv and "-iglx" in argv
        else:
            assert argv == ["/app/bin/pcm-renderer", profile.key, "standard"]
        monkeypatch.setattr(sys, "argv", ["worker", "--resolution", "9999x9999"])
        calls.clear()
        assert worker.main() == 2 and calls == []
        monkeypatch.setattr(sys, "argv", ["worker", "--resolution", profile.key])


@pytest.mark.parametrize("profile", profiles.PROFILES, ids=lambda p: p.key)
def test_commands_have_readonly_profile_and_exact_argv(profile, tmp_path):
    commands = (
        pixels._command(
            tmp_path, (Path("/usr/lib/python3.12"), ()), 10, 11, profile.key
        ),
        display._command(tmp_path, Path("/usr/lib/python3.12"), (), 11, profile.key),
        frontend._command(
            tmp_path, (Path("/usr/lib/python3.12"), (), ()), 10, 11, profile.key
        ),
    )
    for command in commands:
        pos = command.index("/run/projectm-profile.py")
        assert command[pos - 2 : pos + 1] == [
            "--ro-bind",
            str(Path(profiles.__file__)),
            "/run/projectm-profile.py",
        ]
        assert command[-2:] == ["--resolution", profile.key]
        assert "--clearenv" in command and "--unshare-net" in command
        assert not {"/dev/dri", "/dev/snd", "/run/user", "/run/audio/pulse"} & set(
            command
        )


@pytest.mark.parametrize("profile", profiles.PROFILES, ids=lambda p: p.key)
def test_snapshot_config_and_selection_match_name_not_previous_index(profile, tmp_path):
    presets = tmp_path / "original"
    presets.mkdir()
    for name in ("a.milk", "z.milk"):
        (presets / name).write_text("[preset00]\nfRating=3.0\n")
    directory = tmp_path / "work"
    directory.mkdir()
    result = frontend.prepare(
        directory, presets, resolution=profile.key, preset_name="z.milk"
    )
    config = (directory / "config.inp").read_text()
    for text in (
        f"Window Width = {profile.width}",
        f"Window Height = {profile.height}",
        f"Texture Size = {profile.texture}",
    ):
        assert text in config
    assert result["selected_preset"] == 1
    assert (directory / "preset-selection").read_bytes() == struct.pack(
        ">II", 1, 0xFFFFFFFE
    )
    other = tmp_path / "absent"
    other.mkdir()
    assert (
        frontend.prepare(
            other, presets, resolution=profile.key, preset_name="gone.milk"
        )["selected_preset"]
        is None
    )
    assert (other / "preset-selection").read_bytes() == struct.pack(
        ">II", 0xFFFFFFFF, 0
    )


def test_resolution_changes_wait_for_cleanup_and_keep_only_latest_owner(
    monkeypatch, tmp_path
):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    calls, sessions = [], []
    release = threading.Event()

    class Session(frontend.FrontendSession):
        def __init__(self, resolution, preset_name):
            self.resolution = resolution
            self.pid = 123
            self.pixels = SimpleNamespace(frames=pixels.FrameMailbox(resolution))
            self.presets = ("a.milk", "z.milk")
            self.selected_preset = (
                self.presets.index(preset_name) if preset_name else None
            )

        def poll(self):
            return None

        def select_preset(self, index):
            pass

        def stop(self):
            assert release.wait(4)
            sessions.append(self.resolution)

    def start(pb, directory, *, cancelled, resolution, preset_name, cpu_profile):
        assert cpu_profile == "standard"
        assert pb is playback
        calls.append((resolution, preset_name, threading.get_ident()))
        return Session(resolution, preset_name)

    monkeypatch.setattr(frontend, "start", start)
    first = sidecar._ProjectMRequest(app, playback, tmp_path)
    app.radio_projectm_proc = first
    owners = [first]
    first.thread.start()
    try:
        wait(lambda: first.snapshot()[0] == "running")
        assert first.select_preset(1)
        second = sidecar.change_projectm_resolution(app, first, "960x540")
        owners.append(second)
        third = sidecar.change_projectm_resolution(app, second, "1920x1080")
        owners.append(third)
        assert second.cancelled.is_set() and not first.done.is_set()
        assert len(calls) == 1
        assert sidecar.change_projectm_resolution(app, first, "1280x720") is None
        release.set()
        wait(lambda: third.snapshot()[0] == "running")
        assert [(key, name) for key, name, tid in calls] == [
            ("640x480", None),
            ("1920x1080", "z.milk"),
        ]
        assert calls[-1][2] == third.thread.ident
        assert app.radio_proc is playback
        assert third.preset_state() == (("a.milk", "z.milk"), 1)
        assert sidecar.change_projectm_resolution(app, third, "1920x1080") is third
        assert third.select_preset(None)
        fourth = sidecar.change_projectm_resolution(app, third, "1280x720")
        owners.append(fourth)
        wait(lambda: fourth.snapshot()[0] == "running")
        assert calls[-1][1] is None
    finally:
        release.set()
        for owner in owners:
            owner.stop()
        for owner in owners:
            owner.thread.join(4)
        assert all(
            owner.done.is_set() and not owner.thread.is_alive() for owner in owners
        )


def test_tk_resolution_menu_keeps_window_and_discards_old_same_size_result(
    monkeypatch, tmp_path
):
    root = tk.Tk()
    root.withdraw()
    playback = SimpleNamespace()
    root.radio_proc = playback
    first = sidecar._ProjectMRequest(root, playback, tmp_path)
    root.radio_projectm_proc = first
    first._presets = ("one",)
    first.phase = "running"
    first.select_preset(0)
    view = ui.ensure(root, first)
    entered, release = threading.Event(), threading.Event()
    original = ui._scaled_image

    def slow(image, size, mode):
        entered.set()
        assert release.wait(4)
        return original(image, size, mode)

    monkeypatch.setattr(ui, "_scaled_image", slow)
    # Hold owner startup to inspect UI without any subprocesses.
    monkeypatch.setattr(
        sidecar._ProjectMRequest, "_run", lambda self: self.done.wait(3)
    )
    newer = None
    try:
        root.update()
        view.set_display_mode("stretch")
        view.toggle_fullscreen()
        view.scaler.submit(
            Image.new("RGB", (640, 480), "red"),
            view._target_size(),
            "stretch",
            view.generation,
        )
        assert entered.wait(2)
        view.show_menu(SimpleNamespace(x_root=20, y_root=20))
        view.menu.unpost()
        index = next(
            i
            for i in range(view.menu.index("end") + 1)
            if view.menu.type(i) == "cascade"
            and view.menu.entrycget(i, "label") == "Auflösung"
        )
        menu = view.menu.nametowidget(view.menu.entrycget(index, "menu"))
        assert menu.index("end") == 3
        menu.invoke(3)
        newer = root.radio_projectm_proc
        assert newer is view.request and newer is not first
        assert (
            view.profile.key == "1920x1080"
            and view.fullscreen
            and view.display_mode == "stretch"
        )
        assert root.radio_proc is playback and newer.selected_preset_name() == "one"
        assert view.image is None and view.photo is None
        view.choose_preset(0, first)
        assert not newer._preset_pending
        assert not view.set_resolution("960x540", first)
        release.set()
        wait(lambda: view.scaler._result is not None)
        view.tick()
        assert view.photo is None and view.displayed == 0
        newer.frames.put(b"\x10\x20\x30\xff" * (1920 * 1080))
        wait(lambda: view.displayed > 0, root)
        assert view.image.size == (1920, 1080)
        assert not view.closed
    finally:
        release.set()
        if newer is not None:
            newer.done.set()
            newer.thread.join(4)
        view.close()
        root.destroy()


@pytest.mark.parametrize("profile", profiles.PROFILES[1:], ids=lambda p: p.key)
def test_profile_byte_budget_refill(profile, monkeypatch):
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(pixels, "time", SimpleNamespace(monotonic=lambda: clock.now))
    # Finite command-driven producer, including if the guards are disabled.
    program = f"""
import sys
frame = b'x' * {profile.frame_bytes}
for _ in range(4):
    cmd = sys.stdin.buffer.read(1)
    if not cmd: break
    for _ in range(4 if cmd == b'b' else 1):
        sys.stdout.buffer.write(frame if cmd != b'p' else frame[:4096])
    sys.stdout.buffer.flush()
"""
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", "-B", "-c", program],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stream = pixels.PixelStream(
        process, SimpleNamespace(cleanup=lambda: None), profile.key
    )
    try:

        def send(cmd):
            process.stdin.write(cmd)
            process.stdin.flush()

        send(b"b")
        wait(lambda: stream.frames.received == 4)
        assert not stream.error and stream.received_bytes == 4 * profile.frame_bytes
        clock.now = 0.1
        # Reader samples its clock before select (at most 50 ms); let it observe
        # the new tick while the command-driven producer is idle.
        time.sleep(0.07)
        send(b"b")
        wait(lambda: stream.frames.received == 8)
        assert not stream.error
        send(b"f")  # No further reader-clock refill.
        wait(lambda: bool(stream.error))
        assert "rate exceeded" in stream.error
        assert (
            8 * profile.frame_bytes
            < stream.received_bytes
            <= 8 * profile.frame_bytes + pixels.CHUNK
        )
        assert stream.frames.received <= 8
    finally:
        stream.stop()
        process.stdin.close()
        assert not stream.thread.is_alive() and process.poll() is not None


@pytest.mark.parametrize("profile", profiles.PROFILES[1:], ids=lambda p: p.key)
def test_profile_partial_bytes_do_not_extend_deadline(profile, monkeypatch):
    clock = SimpleNamespace(now=0.0)
    monkeypatch.setattr(pixels, "time", SimpleNamespace(monotonic=lambda: clock.now))
    program = "import sys;sys.stdout.buffer.write(b'x'*4096);sys.stdout.buffer.flush();sys.stdin.buffer.read(1)"
    process = subprocess.Popen(
        [sys.executable, "-I", "-S", "-B", "-c", program],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stream = pixels.PixelStream(
        process, SimpleNamespace(cleanup=lambda: None), profile.key
    )
    try:
        wait(lambda: stream.received_bytes == 4096)
        clock.now = 5.5
        wait(lambda: bool(stream.error))
        assert "stalled" in stream.error and stream.frames.received == 0
    finally:
        stream.stop()
        process.stdin.close()
        assert not stream.thread.is_alive() and process.poll() is not None


def test_wrong_profile_session_is_rejected_and_cleaned_up(monkeypatch, tmp_path):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, tmp_path, resolution="1920x1080")
    app.radio_projectm_proc = owner
    stopped = threading.Event()
    session = object.__new__(frontend.FrontendSession)
    session.resolution = "640x480"
    session.pixels = SimpleNamespace(frames=pixels.FrameMailbox())
    session.stop = stopped.set
    monkeypatch.setattr(frontend, "start", lambda *a, **kw: session)
    owner.thread.start()
    owner.thread.join(4)
    assert owner.done.is_set() and stopped.is_set()
    assert owner.snapshot()[0] == "error" and owner.poll() == 2
    assert "Auflösungsprofil" in owner.snapshot()[1]
    assert app.radio_proc is playback and owner.frames.received == 0


def test_switch_worker_failure_has_no_fallback_or_radio_stop(monkeypatch, tmp_path):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, tmp_path)
    app.radio_projectm_proc = owner

    def fail(_self):
        raise RuntimeError("controlled worker failure")

    monkeypatch.setattr(threading.Thread, "start", fail)
    newer = sidecar.change_projectm_resolution(app, owner, "1920x1080")
    assert newer is app.radio_projectm_proc and owner.cancelled.is_set()
    assert newer.done.is_set() and newer.poll() == 2 and newer.snapshot()[0] == "error"
    assert newer.previous is owner and app.radio_proc is playback
