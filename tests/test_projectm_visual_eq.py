"""Visualizer-only EQ: fixed record, read-only bind, owner-thread writes, slider UI."""

import os
import threading
import time
import tkinter as tk
from types import SimpleNamespace

import pytest

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_frontend as frontend
from netmon.core import projectm_gpu as gpu
from netmon.core import projectm_pixels as pixels
from netmon.core import projectm_profile as profiles
from netmon.core import radio_sandbox as sandbox
from netmon.ui import projectm_pixel_window as ui
from test_projectm_frontend import Component
from test_radio_sandbox import Child

EQ = profiles.VisualEq


def wait(predicate, root=None, timeout=3):
    end = time.monotonic() + timeout
    while not predicate():
        assert time.monotonic() < end
        if root is not None:
            root.update()
        time.sleep(0.002)


# ── Record format ────────────────────────────────────────────────────────────


def test_neutral_and_extreme_records():
    assert profiles.encode_visual_eq(profiles.NEUTRAL_EQ) == bytes.fromhex(
        "00000001fffffffe"
    )
    record = profiles.encode_visual_eq(EQ(-12, 12, 6))
    assert len(record) == 8 and record[:4] == bytes((0xF4, 0x0C, 0x06, 1))
    assert all(a ^ b == 0xFF for a, b in zip(record[:4], record[4:]))


@pytest.mark.parametrize(
    "bad",
    [
        EQ(13, 0, 0),
        EQ(0, -13, 0),
        EQ(0, 0, 100),
        EQ(True, 0, 0),
        EQ(1.0, 0, 0),
        EQ("1", 0, 0),
        (0, 0, 0),
        None,
    ],
)
def test_invalid_values_are_rejected(bad):
    with pytest.raises(ValueError):
        profiles.encode_visual_eq(bad)


# ── Snapshot and capsule binds ───────────────────────────────────────────────


@pytest.fixture
def presets(tmp_path):
    source = tmp_path / "presets"
    source.mkdir()
    (source / "one.milk").write_text("[preset00]\nfRating=3\n")
    return source


def test_prepare_writes_requested_start_values(presets, tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    frontend.prepare(work, presets, visual_eq=EQ(6, -3, 2))
    assert (work / "visual-eq").read_bytes() == profiles.encode_visual_eq(EQ(6, -3, 2))
    other = tmp_path / "neutral"
    other.mkdir()
    frontend.prepare(other, presets)
    assert (other / "visual-eq").read_bytes() == profiles.encode_visual_eq(
        profiles.NEUTRAL_EQ
    )


def test_cpu_capsule_binds_eq_record_read_only_once(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_sandbox_command", lambda *a, **k: ["bwrap", "--"])
    command = frontend._command(tmp_path, ((), (), ()), 10, 11)
    position = command.index("/run/visual-eq")
    assert command[position - 2 : position + 1] == [
        "--ro-bind",
        str(tmp_path / "visual-eq"),
        "/run/visual-eq",
    ]
    assert command.count("/run/visual-eq") == 1


def test_gpu_capsule_binds_eq_record_read_only_once(tmp_path, monkeypatch):
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
    command = gpu._command(tmp_path, ((), ()), device, "640x480")
    position = command.index("/run/visual-eq")
    assert command[position - 2 : position + 1] == [
        "--ro-bind",
        str(tmp_path / "visual-eq"),
        "/run/visual-eq",
    ]
    assert command.count("/run/visual-eq") == 1


# ── Session writes and descriptor lifetime ───────────────────────────────────


def test_session_writes_fixed_record_and_closes_descriptor(tmp_path):
    path = tmp_path / "visual-eq"
    path.write_bytes(profiles.encode_visual_eq(profiles.NEUTRAL_EQ))
    descriptor = os.open(path, os.O_WRONLY | os.O_CLOEXEC)
    session = frontend.FrontendSession(
        Component(),
        Component(),
        Component(),
        SimpleNamespace(cleanup=lambda: None),
        eq_fd=descriptor,
    )
    try:
        session.set_visual_eq(EQ(9, -6, 3))
        assert path.read_bytes() == profiles.encode_visual_eq(EQ(9, -6, 3))
        assert session.visual_eq == EQ(9, -6, 3)
        with pytest.raises(ValueError):
            session.set_visual_eq(EQ(20, 0, 0))
        assert path.read_bytes() == profiles.encode_visual_eq(EQ(9, -6, 3))
    finally:
        session.stop()
    with pytest.raises(OSError):
        os.fstat(descriptor)
    with pytest.raises(RuntimeError):
        session.set_visual_eq(profiles.NEUTRAL_EQ)


def _eq_fds():
    found = []
    for name in os.listdir("/proc/self/fd"):
        try:
            if os.readlink(f"/proc/self/fd/{name}").endswith("visual-eq"):
                found.append(name)
        except OSError:
            pass
    return found


def test_start_failure_closes_eq_descriptor(presets, tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_require_quota_manager", lambda: None)
    monkeypatch.setattr(frontend, "_runtime", lambda: (tmp_path, (), ()))
    playback = sandbox.SandboxProcess(
        Child(), SimpleNamespace(name=str(tmp_path), cleanup=lambda: None)
    )

    def failing_pcm(*_a, **_k):
        assert len(_eq_fds()) == 1  # opened and still owned by start()
        raise RuntimeError("synthetic PCM failure")

    monkeypatch.setattr(frontend.projectm_pcm, "start", failing_pcm)
    with pytest.raises(RuntimeError):
        frontend.start(playback, presets, work_root=tmp_path, visual_eq=EQ(3, 3, 3))
    assert _eq_fds() == []
    assert not list(tmp_path.glob("projectm-frontend-*"))


# ── Owner thread ─────────────────────────────────────────────────────────────


def _owner_with_session(monkeypatch, tmp_path, visual_eq=None):
    playback = object()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, str(tmp_path), visual_eq=visual_eq)
    app.radio_projectm_proc = owner
    calls, starts = [], []
    session = object.__new__(frontend.FrontendSession)
    session.pid = 123
    session.pixels = SimpleNamespace(frames=pixels.FrameMailbox())
    session.presets = ()
    session.set_visual_eq = lambda eq: calls.append((eq, threading.get_ident()))
    session.poll = lambda: None
    session.stop = lambda: None

    def start(*_a, **kwargs):
        starts.append(kwargs.get("visual_eq"))
        return session

    monkeypatch.setattr(frontend, "start", start)
    return app, owner, calls, starts


def test_tk_only_queues_newest_eq_for_owner_thread(monkeypatch, tmp_path):
    app, owner, calls, starts = _owner_with_session(monkeypatch, tmp_path)
    owner.thread.start()
    try:
        wait(lambda: owner.snapshot()[0] == "running")
        assert starts == [None]  # neutral start passes no extra keyword
        for value in (1, 2, 3):
            assert owner.set_visual_eq(EQ(value, 0, 0))
        wait(lambda: calls and calls[-1][0] == EQ(3, 0, 0))
        assert all(tid == owner.thread.ident for _eq, tid in calls)
        assert owner.visual_eq == EQ(3, 0, 0)
        for bad in (EQ(13, 0, 0), (1, 2, 3), None):
            assert not owner.set_visual_eq(bad)
    finally:
        owner.stop()
        owner.thread.join(3)
    assert not owner.set_visual_eq(EQ(1, 1, 1))


def test_non_neutral_start_value_reaches_the_session(monkeypatch, tmp_path):
    _app, owner, _calls, starts = _owner_with_session(
        monkeypatch, tmp_path, visual_eq=EQ(6, 0, -3)
    )
    owner.thread.start()
    try:
        wait(lambda: owner.snapshot()[0] == "running")
        assert starts == [EQ(6, 0, -3)]
    finally:
        owner.stop()
        owner.thread.join(3)


def test_profile_change_keeps_current_eq(monkeypatch, tmp_path):
    playback = SimpleNamespace()
    app = SimpleNamespace(radio_proc=playback)
    current = sidecar._ProjectMRequest(app, playback, tmp_path, visual_eq=EQ(4, 5, 6))
    app.radio_projectm_proc = current
    monkeypatch.setattr(sidecar._ProjectMRequest, "_run", lambda self: None)
    newer = sidecar.change_projectm_resolution(app, current, "960x540")
    try:
        assert newer is not current and newer.visual_eq == EQ(4, 5, 6)
    finally:
        newer.thread.join(3)


# ── Slider window ────────────────────────────────────────────────────────────


@pytest.fixture
def window():
    root = tk.Tk()
    root.withdraw()
    received = []
    request = SimpleNamespace(
        frames=pixels.FrameMailbox(),
        cancelled=threading.Event(),
        done=threading.Event(),
        visual_eq=EQ(2, -2, 0),
        set_visual_eq=lambda eq: received.append(eq) or True,
    )
    request.stop = request.cancelled.set
    root.radio_projectm_proc = request
    view = ui.ensure(root, request)
    root.update()
    yield root, view, request, received
    view.close()
    root.destroy()


def test_menu_offers_slider_window_with_current_values(window):
    root, view, _request, _received = window
    view.show_menu(SimpleNamespace(x_root=10, y_root=10))
    view.menu.unpost()
    labels = [
        view.menu.entrycget(i, "label")
        for i in range(view.menu.index("end") + 1)
        if view.menu.type(i) not in {"separator"}
    ]
    assert "Klang für Visualisierung…" in labels
    eq_window = view.open_visual_eq()
    root.update()
    assert view.open_visual_eq() is eq_window  # one window per pixel window
    assert [
        int(view.eq_scales[k].get()) for k in ("bass_db", "treble_db", "sensitivity_db")
    ] == [2, -2, 0]
    for scale in view.eq_scales.values():
        assert scale.cget("from") == -12 and scale.cget("to") == 12


def test_sliders_feed_owner_and_remember_app_value(window):
    root, view, _request, received = window
    view.open_visual_eq()
    view.eq_scales["bass_db"].set(9)
    root.update()
    assert view._visual_eq_changed()
    assert received[-1] == EQ(9, -2, 0) and root._projectm_visual_eq == EQ(9, -2, 0)
    assert view.reset_visual_eq()
    assert received[-1] == profiles.NEUTRAL_EQ
    assert all(int(s.get()) == 0 for s in view.eq_scales.values())


def test_stale_window_cannot_change_new_owner(window):
    root, view, _request, received = window
    view.open_visual_eq()
    root.radio_projectm_proc = object()
    before = list(received)
    view.eq_scales["treble_db"].set(7)
    root.update()
    assert not view._visual_eq_changed()
    assert received == before


def test_closing_pixel_window_closes_slider_window(window):
    root, view, _request, _received = window
    eq_window = view.open_visual_eq()
    root.update()
    view.close()
    assert view.eq_window is None
    assert not eq_window.winfo_exists()
