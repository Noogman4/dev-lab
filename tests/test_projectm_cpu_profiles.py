"""CPU settings agree across configuration, capsule, worker and owner changes."""

import os
from pathlib import Path
import sys
import threading
from types import SimpleNamespace
import tkinter as tk

import pytest
from PIL import Image

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_frontend as frontend, projectm_profile as profiles
from netmon.core import projectm_frontend_worker as worker, radio_sandbox as sandbox
from netmon.core.projectm_pixels import FrameMailbox
from netmon.ui import projectm_pixel_window as ui
from tests.test_projectm_resolution import wait


@pytest.mark.parametrize("cpu", profiles.CPU_PROFILES, ids=lambda p: p.key)
@pytest.mark.parametrize("resolution", profiles.PROFILES, ids=lambda p: p.key)
def test_cpu_settings_agree_and_only_renderer_cpu_budget_changes(
    cpu, resolution, monkeypatch, tmp_path
):
    presets = tmp_path / "presets"
    presets.mkdir()
    (presets / "one.milk").write_text("[preset00]\nfRating=3.0\n")
    work = tmp_path / "work"
    work.mkdir()
    frontend.prepare(work, presets, resolution=resolution.key, cpu_profile=cpu.key)
    assert f"FPS = {cpu.fps}\n" in (work / "config.inp").read_text()
    command = frontend._command(
        work,
        (Path("/usr/lib/python3.12"), (), ()),
        10,
        11,
        resolution.key,
        cpu.key,
    )
    assert command[command.index("LP_NUM_THREADS") + 1] == str(cpu.threads)
    assert command[command.index("LIBGL_ALWAYS_SOFTWARE") + 1] == "1"
    assert command[command.index("GALLIUM_DRIVER") + 1] == "llvmpipe"
    args = command[-4:]
    assert args == ["--cpu-profile", cpu.key, "--resolution", resolution.key]
    calls = []
    monkeypatch.setattr(sys, "argv", ["worker", *args])
    monkeypatch.setattr(worker, "limits", lambda: None)
    monkeypatch.setattr(os, "execv", lambda exe, argv: calls.append((exe, argv)))
    worker.main()
    assert calls == [
        ("/app/bin/pcm-renderer", ["/app/bin/pcm-renderer", resolution.key, cpu.key])
    ]
    assert (cpu.fps, cpu.threads, sandbox.QUOTAS[cpu.quota]["cpu"]) == (
        (25, 2, 200) if cpu.key == "standard" else (30, 4, 300)
    )
    assert {k: v for k, v in sandbox.QUOTAS[cpu.quota].items() if k != "cpu"} == {
        k: v for k, v in sandbox.QUOTAS["pm-renderer"].items() if k != "cpu"
    }
    limited = sandbox._limited(command, cpu.quota)
    assert f"CPUQuota={sandbox.QUOTAS[cpu.quota]['cpu']}%" in limited
    assert "MemoryMax=1G" in limited and "MemorySwapMax=0" in limited
    assert "TasksMax=64" in limited and "--nofile=256:256" in limited
    assert "--fsize=16777216:16777216" in limited
    assert not {"/dev/dri", "/dev/snd", "/run/user"} & set(command)


@pytest.mark.parametrize("key", [None, True, 30, "gpu", "auto", "performance\n", "4"])
def test_invalid_cpu_profile_never_acquires_resources(key, monkeypatch, tmp_path):
    monkeypatch.setattr(frontend, "_runtime", lambda: pytest.fail("Runtime reached"))
    monkeypatch.setattr(
        sandbox, "_prepare_directory", lambda _: pytest.fail("Directory reached")
    )
    for call in (
        lambda: frontend.start(None, tmp_path, cpu_profile=key),
        lambda: frontend.prepare(tmp_path, tmp_path, cpu_profile=key),
        lambda: frontend._command(tmp_path, (), 10, 11, cpu_profile=key),
        lambda: sidecar._ProjectMRequest(None, None, tmp_path, cpu_profile=key),
        lambda: sidecar.change_projectm_cpu_profile(None, None, key),
    ):
        with pytest.raises(ValueError):
            call()


@pytest.mark.parametrize(
    "args",
    [
        ["--cpu-profile"],
        ["--cpu-profile", "gpu"],
        ["--cpu-profile", "performance", "--resolution", "bad"],
        ["--cpu-profile", "performance", "--cpu-profile", "standard"],
        ["--resolution", "640x480", "--cpu-profile", "performance"],
    ],
)
def test_bad_worker_arguments_fail_before_limits_or_exec(args, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["worker", *args])
    monkeypatch.setattr(worker, "limits", lambda: pytest.fail("Limits reached"))
    monkeypatch.setattr(os, "execv", lambda *a: pytest.fail("Exec reached"))
    assert worker.main() == 2


def test_mixed_cpu_resolution_changes_wait_for_cleanup_and_keep_latest_preset(
    monkeypatch, tmp_path
):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    release = threading.Event()
    calls = []

    class Session(frontend.FrontendSession):
        def __init__(self, resolution, cpu_profile, preset_name):
            self.resolution, self.cpu_profile = resolution, cpu_profile
            self.pid = 123
            self.pixels = SimpleNamespace(frames=FrameMailbox(resolution))
            self.presets = ("a.milk", "z.milk")
            self.selected_preset = self.presets.index(preset_name)

        def poll(self):
            return None

        def select_preset(self, index):
            pass

        def stop(self):
            assert release.wait(4)

    def start(pb, directory, *, cancelled, resolution, cpu_profile, preset_name):
        assert pb is playback
        calls.append((resolution, cpu_profile, preset_name))
        return Session(resolution, cpu_profile, preset_name)

    monkeypatch.setattr(frontend, "start", start)
    first = sidecar._ProjectMRequest(app, playback, tmp_path, preset_name="z.milk")
    app.radio_projectm_proc = first
    owners = [first]
    first.thread.start()
    try:
        wait(lambda: first.snapshot()[0] == "running")
        second = sidecar.change_projectm_cpu_profile(app, first, "performance")
        owners.append(second)
        third = sidecar.change_projectm_resolution(app, second, "1920x1080")
        owners.append(third)
        fourth = sidecar.change_projectm_cpu_profile(app, third, "standard")
        owners.append(fourth)
        assert len(calls) == 1 and not first.done.is_set()
        assert sidecar.change_projectm_cpu_profile(app, first, "performance") is None
        release.set()
        wait(lambda: fourth.snapshot()[0] == "running")
        assert calls == [
            ("640x480", "standard", "z.milk"),
            ("1920x1080", "standard", "z.milk"),
        ]
        fifth = sidecar.change_projectm_cpu_profile(app, fourth, "performance")
        owners.append(fifth)
        wait(lambda: fifth.snapshot()[0] == "running")
        assert calls[-1] == ("1920x1080", "performance", "z.milk")
        assert sidecar.change_projectm_cpu_profile(app, fifth, "performance") is fifth
        assert app.radio_proc is playback
        assert app._projectm_cpu_profile == "performance"
        assert app._projectm_resolution == "1920x1080"
    finally:
        release.set()
        for owner in owners:
            owner.stop()
        for owner in owners:
            owner.thread.join(4)
        assert all(
            owner.done.is_set() and not owner.thread.is_alive() for owner in owners
        )


def test_cpu_menu_keeps_window_fullscreen_mode_preset_and_rejects_old_frame(
    monkeypatch, tmp_path
):
    root = tk.Tk()
    root.withdraw()
    playback = SimpleNamespace()
    root.radio_proc = playback
    first = sidecar._ProjectMRequest(root, playback, tmp_path)
    root.radio_projectm_proc = first
    first._presets = ("chosen.milk",)
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
    monkeypatch.setattr(
        sidecar._ProjectMRequest, "_run", lambda self: self.done.wait(3)
    )
    newer = None
    try:
        root.update()
        view.set_display_mode("fill")
        view.toggle_fullscreen()
        geometry, window = view.windowed_geometry, view.window
        view.scaler.submit(
            Image.new("RGB", (640, 480), "red"),
            view._target_size(),
            view.display_mode,
            view.generation,
        )
        assert entered.wait(2)
        view.show_menu(SimpleNamespace(x_root=20, y_root=20))
        view.menu.unpost()
        labels = [view.menu.entrycget(i, "label") for i in (0, 1, 2, 3)]
        assert "CPU-Leistung" in labels
        menu = view.menu.nametowidget(view.menu.entrycget(3, "menu"))
        assert [menu.entrycget(i, "label") for i in (0, 1)] == [
            "Standard",
            "Mehr Leistung",
        ]
        menu.invoke(1)
        newer = root.radio_projectm_proc
        assert newer is view.request and newer is not first
        assert newer.cpu_profile == "performance" and newer.resolution == "640x480"
        assert newer.selected_preset_name() == "chosen.milk"
        assert root.radio_proc is playback
        assert view.window is window and view.fullscreen and view.display_mode == "fill"
        assert (
            view.windowed_geometry == geometry
            and view.cpu_profile_var.get() == "performance"
        )
        assert view.photo is None and view.image is None
        assert not view.set_cpu_profile("standard", first)
        assert not view.set_resolution("1920x1080", first)
        view.choose_preset(None, first)
        assert newer.selected_preset_name() == "chosen.milk"
        release.set()
        wait(lambda: view.scaler._result is not None)
        view.tick()
        assert view.photo is None and view.displayed == 0
        newer.frames.put(b"\x10\x20\x30\xff" * (640 * 480))
        wait(lambda: view.displayed > 0, root)
        assert view.image.size == (640, 480)
        assert not view.closed
    finally:
        release.set()
        if newer is not None:
            newer.done.set()
            newer.thread.join(4)
        view.close()
        root.destroy()


def test_wrong_cpu_session_is_rejected_and_cleaned_up(monkeypatch, tmp_path):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, tmp_path, cpu_profile="performance")
    app.radio_projectm_proc = owner
    stopped = threading.Event()
    session = object.__new__(frontend.FrontendSession)
    session.resolution, session.cpu_profile = "640x480", "standard"
    session.pixels = SimpleNamespace(frames=FrameMailbox())
    session.stop = stopped.set
    monkeypatch.setattr(frontend, "start", lambda *a, **kw: session)
    owner.thread.start()
    owner.thread.join(4)
    assert owner.done.is_set() and stopped.is_set()
    assert owner.poll() == 2 and "CPU-Profil" in owner.snapshot()[1]
    assert app.radio_proc is playback


def test_cpu_switch_worker_failure_stops_no_radio_and_uses_no_fallback(
    monkeypatch, tmp_path
):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, tmp_path)
    app.radio_projectm_proc = owner

    def fail(self):
        raise RuntimeError("controlled worker failure")

    monkeypatch.setattr(threading.Thread, "start", fail)
    newer = sidecar.change_projectm_cpu_profile(app, owner, "performance")
    assert newer.done.is_set() and newer.poll() == 2 and owner.cancelled.is_set()
    assert app.radio_projectm_proc is newer and app.radio_proc is playback


def test_cpu_selection_survives_visualizer_stop_and_relaunch(monkeypatch, tmp_path):
    playback = sandbox.SandboxProcess(
        SimpleNamespace(), SimpleNamespace(name=str(tmp_path))
    )
    app = SimpleNamespace(radio_proc=playback)
    monkeypatch.setattr(threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(sidecar, "get_projectm_preset_dir", lambda app: tmp_path)
    first = sidecar._ProjectMRequest(app, playback, tmp_path, resolution="1280x720")
    app.radio_projectm_proc = first
    selected = sidecar.change_projectm_cpu_profile(app, first, "performance")
    selected.stop()
    selected.done.set()
    status = sidecar.launch_projectm_sidecar(app)
    assert status.starting and not status.launched
    assert app.radio_projectm_proc.cpu_profile == "performance"
    assert app.radio_projectm_proc.resolution == "1280x720"
    assert app.radio_proc is playback
