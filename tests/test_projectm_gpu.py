"""GPU protocol ownership, explicit modes, fallback and visualizer transitions."""

from pathlib import Path
import subprocess
import sys
import threading
from types import SimpleNamespace
import tkinter as tk

import pytest
import hashlib
import json
import os

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_frontend as frontend, projectm_gpu as gpu
from netmon.core import projectm_pixels as pixels, projectm_profile as profiles
from netmon.core import radio_sandbox as sandbox
from netmon.core import projectm_native as native
from netmon.ui import projectm_pixel_window as ui
from tests.test_projectm_resolution import wait


@pytest.mark.parametrize("key", [None, True, 1, "GPU", "gpu\n", "unknown"])
def test_invalid_backend_fails_before_resources(key, monkeypatch, tmp_path):
    monkeypatch.setattr(gpu, "start", lambda *a, **kw: pytest.fail("GPU acquired"))
    monkeypatch.setattr(frontend, "_runtime", lambda: pytest.fail("CPU acquired"))
    for action in (
        lambda: frontend.start(None, tmp_path, backend=key),
        lambda: sidecar._ProjectMRequest(None, None, tmp_path, backend=key),
        lambda: sidecar.change_projectm_backend(None, None, key),
    ):
        with pytest.raises(ValueError):
            action()


@pytest.mark.parametrize("profile", profiles.PROFILES, ids=lambda p: p.key)
def test_gpu_config_restores_mesh_and_fixed_fps(profile, tmp_path):
    source = tmp_path / "presets"
    source.mkdir()
    (source / "one.milk").write_text("[preset00]\nfRating=3\n")
    work = tmp_path / "work"
    work.mkdir()
    frontend.prepare(work, source, resolution=profile.key, backend="gpu")
    text = (work / "config.inp").read_text()
    assert "Mesh X = 220\nMesh Y = 125\nFPS = 30\n" in text
    assert f"Texture Size = {profile.texture}\n" in text
    assert f"Window Width = {profile.width}\nWindow Height = {profile.height}\n" in text


@pytest.mark.parametrize("mode", ["cpu", "auto", "gpu"])
def test_explicit_mode_and_auto_fallback_do_not_expand_rights(
    mode, monkeypatch, tmp_path
):
    calls = []

    def fail_gpu(*a, **kw):
        calls.append("gpu")
        raise sandbox.RadioSandboxError("GPU unavailable")

    def fail_cpu():
        calls.append("cpu")
        raise RuntimeError("CPU runtime reached")

    monkeypatch.setattr(gpu, "start", fail_gpu)
    monkeypatch.setattr(frontend, "_runtime", fail_cpu)
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    playback = object.__new__(sandbox.SandboxProcess)
    with pytest.raises(
        Exception, match="GPU unavailable" if mode == "gpu" else "CPU runtime reached"
    ):
        frontend.start(playback, tmp_path, backend=mode)
    assert calls == (
        ["cpu"] if mode == "cpu" else ["gpu"] if mode == "gpu" else ["gpu", "cpu"]
    )


@pytest.mark.parametrize("mode", ["auto", "gpu"])
def test_gpu_success_never_starts_cpu(mode, monkeypatch, tmp_path):
    expected = object()
    monkeypatch.setattr(gpu, "start", lambda *a, **kw: expected)
    monkeypatch.setattr(frontend, "_runtime", lambda: pytest.fail("CPU reached"))
    assert frontend.start(None, tmp_path, backend=mode) is expected


@pytest.mark.parametrize("cancel", [False, True], ids=["cleanup-error", "cancelled"])
def test_cleanup_failure_or_cancel_does_not_start_fallback(
    cancel, monkeypatch, tmp_path
):
    ended = threading.Event()
    error = (
        sandbox.RadioSandboxError("cancelled")
        if cancel
        else gpu.CleanupError("cleanup incomplete")
    )

    def fail(*a, **kw):
        if cancel:
            ended.set()
        raise error

    monkeypatch.setattr(gpu, "start", fail)
    # A mistakenly entered CPU path must reach the sentinel, not be rejected
    # earlier for foreign playback or an unavailable host quota manager.
    playback = object.__new__(sandbox.SandboxProcess)
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    monkeypatch.setattr(frontend, "_runtime", lambda: pytest.fail("CPU reached"))
    with pytest.raises(type(error)) as caught:
        frontend.start(playback, tmp_path, backend="auto", cancelled=ended.is_set)
    assert caught.value is error


@pytest.mark.parametrize("header", [b"NMPG1 640x480\n", b"NMPG1 960x540\n", b"bad\n"])
def test_borrowed_stream_validates_marker_but_never_stops_renderer(header):
    expected = b"NMPG1 640x480\n"
    program = "import os,sys; h=bytes.fromhex(sys.argv[1]); os.write(1,h[:4]);os.write(1,h[4:]); data=b'x'*1228800;sys.stdout.buffer.write(data);sys.stdout.buffer.flush();sys.stdin.buffer.read(1)"
    child = subprocess.Popen(
        [sys.executable, "-I", "-S", "-B", "-c", program, header.hex()],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    stream = pixels.PixelStream(
        child,
        SimpleNamespace(cleanup=lambda: None),
        owns_process=False,
        marker=expected,
    )
    try:
        wait(lambda: bool(stream.error) or stream.frames.received == 1)
        if header == expected:
            assert not stream.error and stream.received_bytes == 1228800
            assert stream.frames.take() == b"x" * 1228800
        else:
            assert "marker" in stream.error and stream.frames.received == 0
        stream.stop()
        assert child.poll() is None and not child.stdout.closed
        assert not stream.thread.is_alive()
    finally:
        stream.stop()
        child.terminate()
        child.wait(timeout=3)
        child.stdin.close()
        child.stdout.close()


def test_gpu_command_grants_only_selected_device_and_private_inputs(
    monkeypatch, tmp_path
):
    device = gpu.Device(
        "/dev/dri/renderD128",
        "/sys/devices/pci0000:00/0000:2b:00.0",
        "0x1002",
        "amdgpu",
        "radeonsi",
        226,
        128,
    )
    monkeypatch.setattr(gpu, "inspect_device", lambda path: device)
    command = gpu._command(
        tmp_path,
        ((), ((Path("/tmp/binary"), "/app/bin/egl-renderer"),)),
        device,
        "1920x1080",
    )
    pos = command.index("--dev-bind")
    assert command[pos : pos + 3] == ["--dev-bind", device.path, device.path]
    assert command.count("--dev-bind") == 1
    assert "--clearenv" in command and "--unshare-net" in command
    assert command[-3:] == ["/app/bin/egl-renderer", "1920x1080", "performance"]
    assert not {
        "/dev/dri",
        "/dev/dri/card1",
        "/dev/snd",
        "/run/audio/pulse",
        "DISPLAY",
        "XAUTHORITY",
        "LIBGL_ALWAYS_SOFTWARE",
    } & set(command)
    changed = gpu.Device(
        device.path, device.sysfs, device.vendor, "nouveau", "nouveau", 226, 128
    )
    monkeypatch.setattr(gpu, "inspect_device", lambda path: changed)
    with pytest.raises(sandbox.RadioSandboxError, match="identität"):
        gpu._command(tmp_path, ((), ()), device, "1920x1080")


@pytest.mark.parametrize(
    "path",
    [
        "/dev/dri/card1",
        "/tmp/renderD128",
        "/dev/dri/renderD128/other",
        "/dev/dri/renderD128\n",
    ],
)
def test_device_path_rejects_primary_nodes_and_arbitrary_files(path):
    with pytest.raises(ValueError):
        gpu.inspect_device(path)


def test_gpu_switch_preserves_state_and_waits_for_previous_owner(monkeypatch, tmp_path):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    release = threading.Event()
    calls = []

    class Session(frontend.FrontendSession):
        def __init__(self, resolution, cpu_profile, preset_name, backend):
            self.resolution, self.cpu_profile, self.backend = (
                resolution,
                cpu_profile,
                backend,
            )
            self.pixels = SimpleNamespace(frames=pixels.FrameMailbox(resolution))
            self.presets = ("one.milk",)
            self.selected_preset = 0 if preset_name else None
            self.pid = 123

        def poll(self):
            return None

        def select_preset(self, index):
            pass

        def stop(self):
            assert release.wait(4)

    def start(
        pb, directory, *, cancelled, resolution, cpu_profile, preset_name, backend="cpu"
    ):
        calls.append((resolution, cpu_profile, preset_name, backend))
        return Session(resolution, cpu_profile, preset_name, backend)

    monkeypatch.setattr(frontend, "start", start)
    first = sidecar._ProjectMRequest(app, playback, tmp_path, preset_name="one.milk")
    app.radio_projectm_proc = first
    first.thread.start()
    owners = [first]
    try:
        wait(lambda: first.snapshot()[0] == "running")
        second = sidecar.change_projectm_backend(app, first, "gpu")
        owners.append(second)
        third = sidecar.change_projectm_resolution(app, second, "1920x1080")
        owners.append(third)
        assert len(calls) == 1
        release.set()
        wait(lambda: third.snapshot()[0] == "running")
        assert calls[-1] == ("1920x1080", "standard", "one.milk", "gpu")
        assert third.render_state() == ("gpu", "") and app.radio_proc is playback
        assert sidecar.change_projectm_backend(app, first, "cpu") is None
        fourth = sidecar.change_projectm_backend(app, third, "cpu")
        owners.append(fourth)
        wait(lambda: fourth.snapshot()[0] == "running")
        assert (
            fourth.resolution == "1920x1080"
            and fourth.selected_preset_name() == "one.milk"
        )
        assert app._projectm_backend == "cpu"
    finally:
        release.set()
        for owner in owners:
            owner.stop()
        for owner in owners:
            owner.thread.join(4)
        assert all(
            owner.done.is_set() and not owner.thread.is_alive() for owner in owners
        )


def test_tk_backend_menu_keeps_window_and_fullscreen(monkeypatch, tmp_path):
    root = tk.Tk()
    root.withdraw()
    playback = SimpleNamespace()
    root.radio_proc = playback
    first = sidecar._ProjectMRequest(root, playback, tmp_path)
    root.radio_projectm_proc = first
    view = ui.ensure(root, first)
    monkeypatch.setattr(
        sidecar._ProjectMRequest, "_run", lambda self: self.done.wait(4)
    )
    newer = None
    try:
        root.update()
        view.toggle_fullscreen()
        view.set_display_mode("fill")
        window, geometry = view.window, view.windowed_geometry
        view.show_menu(SimpleNamespace(x_root=20, y_root=20))
        view.menu.unpost()
        index = next(
            i
            for i in range(view.menu.index("end") + 1)
            if view.menu.type(i) == "cascade"
            and view.menu.entrycget(i, "label") == "Rendern"
        )
        menu = view.menu.nametowidget(view.menu.entrycget(index, "menu"))
        assert [menu.entrycget(i, "label") for i in range(3)] == [
            "Automatisch",
            "CPU",
            "GPU",
        ]
        menu.invoke(2)
        newer = root.radio_projectm_proc
        newer._actual_backend = "gpu"
        view.tick()
        assert newer is view.request and newer.backend == "gpu"
        assert view.backend_var.get() == "gpu" and "GPU" in view.window.title()
        assert (
            view.window is window
            and view.fullscreen
            and view.windowed_geometry == geometry
        )
        assert view.display_mode == "fill" and root.radio_proc is playback
        assert not view.set_backend("cpu", first)
    finally:
        if newer:
            newer.done.set()
            newer.thread.join(4)
        view.close()
        root.destroy()


@pytest.mark.parametrize("tamper", ["header", "binary"])
def test_gpu_artifact_binds_binary_and_egl_header(tamper, monkeypatch, tmp_path):
    source = tmp_path / "source"
    (source / "include").mkdir(parents=True)
    (source / "build").mkdir()
    (source / "pcm_renderer.cpp").write_text("renderer")
    (source / "egl_context.hpp").write_text("egl")
    binary = source / "build/egl-renderer"
    binary.write_bytes(b"binary")
    binary.chmod(0o700)
    payload = tmp_path / "payload"
    (payload / "lib").mkdir(parents=True)
    library = payload / "lib/libprojectM.so.3"
    library.write_bytes(b"library")
    library_hash = hashlib.sha256(library.read_bytes()).hexdigest()
    monkeypatch.setattr(native, "SOURCE", source)
    monkeypatch.setattr(native, "LIBRARY_SHA256", library_hash)
    record = dict(
        schema=1,
        library_sha256=library_hash,
        binary_sha256=native.digest(binary),
        sources={
            name: native.digest(source / name)
            for name in ("pcm_renderer.cpp", "egl_context.hpp")
        },
    )
    (source / "build/egl-build.json").write_text(json.dumps(record))
    assert native.gpu_artifact(payload) == binary
    target = source / "egl_context.hpp" if tamper == "header" else binary
    target.write_bytes(b"changed")
    with pytest.raises(sandbox.RadioSandboxError, match="veraltet"):
        native.gpu_artifact(payload)


@pytest.mark.parametrize("failure", ["pcm", "popen", "reader", "not-ready", "cancel"])
def test_gpu_partial_start_cleans_only_owned_resources(failure, monkeypatch, tmp_path):
    from netmon.core import projectm_pcm

    presets = tmp_path / "presets"
    presets.mkdir()
    (presets / "one.milk").write_text("[preset00]\nfRating=3\n")
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    monkeypatch.setattr(gpu, "candidate", lambda: SimpleNamespace(dri="radeonsi"))
    monkeypatch.setattr(gpu, "_runtime", lambda dri: ((), ()))
    monkeypatch.setattr(gpu, "_command", lambda *a: ["capsule"])
    monkeypatch.setattr(sandbox, "_limited", lambda command, profile: command)
    closed = []
    ended = threading.Event()
    audio_read, audio_write = os.pipe()
    os.close(audio_write)
    audio = SimpleNamespace(
        process=SimpleNamespace(stdout=os.fdopen(audio_read, "rb", buffering=0)),
        poll=lambda: None,
    )

    def stop_audio():
        closed.append("pcm")
        audio.process.stdout.close()

    audio.stop = stop_audio

    def start_pcm(*a, **kw):
        if failure == "pcm":
            raise RuntimeError("controlled PCM failure")
        if failure == "cancel":
            ended.set()
        return audio

    monkeypatch.setattr(projectm_pcm, "start", start_pcm)
    child = SimpleNamespace(stdout=None, poll=lambda: None)

    def spawn(*a, **kw):
        if failure == "popen":
            raise OSError("controlled Popen failure")
        closed.append("spawned")
        return child

    monkeypatch.setattr(subprocess, "Popen", spawn)
    monkeypatch.setattr(
        frontend,
        "_stop_process",
        lambda process: closed.append("renderer") if process is not None else None,
    )

    def pixel_reader(*a, **kw):
        if failure == "reader":
            raise RuntimeError("controlled reader failure")
        ready = threading.Event()
        ready.set()
        return SimpleNamespace(
            ready=ready,
            error="controlled invalid marker",
            frames=SimpleNamespace(received=0),
            stop=lambda: closed.append("pixels"),
        )

    monkeypatch.setattr(pixels, "PixelStream", pixel_reader)
    playback = object.__new__(sandbox.SandboxProcess)
    try:
        with pytest.raises((OSError, RuntimeError, sandbox.RadioSandboxError)):
            gpu.start(playback, presets, work_root=tmp_path, cancelled=ended.is_set)
        assert ("pcm" in closed) == (failure != "pcm")
        assert ("renderer" in closed) == (failure in {"reader", "not-ready"})
        assert ("pixels" in closed) == (failure == "not-ready")
        assert not list(tmp_path.glob("projectm-gpu-*"))
    finally:
        audio.process.stdout.close()
