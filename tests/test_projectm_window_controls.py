"""Real Tk mouse/menu behavior and bounded owner-side preset selection."""

import os
import re
import struct
import threading
import time
import tkinter as tk
from types import SimpleNamespace

import pytest
from PIL import Image

from netmon import netmon_projectm_sidecar as sidecar
from netmon.core import projectm_frontend as frontend, projectm_pixels as pixels
from netmon.ui import projectm_pixel_window as ui
from test_projectm_frontend import Component


def wait(predicate, root=None):
    end = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < end
        if root is not None:
            root.update()
        time.sleep(0.002)


@pytest.fixture
def window():
    root = tk.Tk()
    root.withdraw()
    selected = []
    request = SimpleNamespace(
        frames=pixels.FrameMailbox(),
        cancelled=threading.Event(),
        done=threading.Event(),
    )
    request.stop = request.cancelled.set
    request.preset_state = lambda: (("Pack/one.milk", "Pack/two.milk"), None)
    request.select_preset = lambda index: selected.append(index) or True
    root.radio_projectm_proc = request
    view = ui.ensure(root, request)
    root.update()
    yield root, view, request, selected
    view.close()
    root.destroy()


def double_click(root, view, stamp):
    for tick in (stamp, stamp + 100):
        view.label.event_generate("<ButtonPress-1>", x=50, y=50, time=tick)
        view.label.event_generate("<ButtonRelease-1>", x=50, y=50, time=tick + 20)
    root.update()


def menu_index(menu, label):
    return next(
        i
        for i in range(menu.index("end") + 1)
        if menu.type(i) != "separator" and menu.entrycget(i, "label") == label
    )


def test_double_click_toggles_and_escape_restores_window(window):
    root, view, request, _ = window
    geometry = view.window.geometry()
    double_click(root, view, 1000)
    assert view.fullscreen and view.fullscreen_var.get()
    double_click(root, view, 2000)
    assert not view.fullscreen and view.window.geometry() == geometry
    double_click(root, view, 3000)
    assert view.fullscreen
    view.window.focus_force()
    view.window.event_generate("<KeyPress-Escape>")
    root.update()
    assert not view.fullscreen and not request.cancelled.is_set()


def test_right_click_menu_selects_preset_and_automatic_mode(window):
    root, view, request, selected = window
    view.label.event_generate("<Button-3>", x=50, y=50, rootx=100, rooty=100)
    root.update()
    assert view.menu is not None
    submenu = root.nametowidget(
        view.menu.entrycget(menu_index(view.menu, "Presets"), "menu")
    )
    assert submenu.entrycget(0, "label") == "Pack/one.milk"
    submenu.invoke(1)
    assert selected == [1] and view.preset_var.get() == 1
    view.menu.invoke(menu_index(view.menu, "Automatischer Preset-Wechsel"))
    assert selected == [1, None]
    assert not request.cancelled.is_set()
    view.menu.unpost()


def test_picture_fits_larger_view_without_stretching(window):
    root, view, request, _ = window
    view.window.geometry("1000x600")
    root.update()
    request.frames.put(b"\x7f" * pixels.FRAME_BYTES)
    wait(lambda: view.displayed == 1, root)
    assert (view.photo.width(), view.photo.height()) == (800, 600)
    view.window.geometry("640x480")
    root.update()
    assert (view.photo.width(), view.photo.height()) == (640, 480)


@pytest.mark.parametrize(
    "geometry,mode,size,point,color",
    [
        ("1000x600", "fit", (800, 600), (400, 0), (255, 0, 0)),
        ("1000x600", "fill", (1000, 600), (500, 0), (0, 255, 0)),
        ("1000x600", "stretch", (1000, 600), (500, 0), (255, 0, 0)),
        ("600x900", "fit", (600, 450), (0, 225), (255, 0, 0)),
        ("600x900", "fill", (600, 900), (0, 450), (0, 255, 0)),
        ("600x900", "stretch", (600, 900), (0, 450), (255, 0, 0)),
    ],
)
def test_display_modes_scale_and_crop_pixels(
    window, geometry, mode, size, point, color
):
    root, view, request, _ = window
    view.window.geometry(geometry)
    root.update()
    assert view.set_display_mode(mode)
    image = Image.new("RGBA", (pixels.WIDTH, pixels.HEIGHT), (255, 0, 0, 255))
    image.paste((0, 255, 0, 255), (30, 30, 610, 450))
    request.frames.put(image.tobytes())
    wait(lambda: view.displayed == 1, root)
    assert (view.photo.width(), view.photo.height()) == size
    assert view.photo.tk.call(str(view.photo), "get", *point) == color


def test_display_menu_switches_last_frame_and_preserves_mode_in_fullscreen(window):
    root, view, request, selected = window
    view.window.geometry("1000x600")
    root.update()
    request.frames.put(b"\x10\x20\x30\xff" * (pixels.WIDTH * pixels.HEIGHT))
    wait(lambda: view.displayed == 1, root)
    view.label.event_generate("<Button-3>", x=50, y=50, rootx=100, rooty=100)
    root.update()
    menu = root.nametowidget(
        view.menu.entrycget(menu_index(view.menu, "Darstellung"), "menu")
    )
    assert [menu.entrycget(i, "label") for i in range(3)] == [
        label for _, label in ui.DISPLAY_MODES
    ]
    for index, (mode, _label) in enumerate(ui.DISPLAY_MODES):
        menu.invoke(index)
        assert view.display_mode == view.display_mode_var.get() == mode
        expected = (800, 600) if mode == "fit" else (1000, 600)
        assert (view.photo.width(), view.photo.height()) == expected
        view.toggle_fullscreen()
        view.exit_fullscreen()
        assert view.display_mode == mode
    assert not view.set_display_mode("unsupported")
    assert not selected and not request.cancelled.is_set()
    view.menu.unpost()


def test_old_result_for_different_mode_with_same_size_is_discarded(window, monkeypatch):
    root, view, request, _ = window
    view.window.geometry("1000x600")
    root.update()
    view.set_display_mode("fill")
    entered, release = threading.Event(), threading.Event()
    original = ui._scaled_image

    def blocked(image, size, mode):
        if threading.get_ident() == view.scaler.thread.ident:
            entered.set()
            assert release.wait(3)
        return original(image, size, mode)

    monkeypatch.setattr(ui, "_scaled_image", blocked)
    image = Image.new("RGBA", (pixels.WIDTH, pixels.HEIGHT), (255, 0, 0, 255))
    image.paste((0, 255, 0, 255), (30, 30, 610, 450))
    request.frames.put(image.tobytes())
    try:
        wait(entered.is_set, root)
        assert view.set_display_mode("stretch")
        assert view.photo.tk.call(str(view.photo), "get", 500, 0) == (255, 0, 0)
        release.set()
        # Wait without consuming the result; then let tick discard the old crop.
        wait(lambda: view.scaler._result is not None)
        root.update()
        until = time.monotonic() + 0.1
        while time.monotonic() < until:
            root.update()
            time.sleep(0.002)
        assert view.photo.tk.call(str(view.photo), "get", 500, 0) == (255, 0, 0)
        assert view.displayed == 0
    finally:
        release.set()


def test_stale_window_does_not_change_new_request(window):
    root, view, request, selected = window
    root.radio_projectm_proc = object()
    view.choose_preset(0)
    view.toggle_fullscreen()
    assert not selected and not view.fullscreen
    view.close(notify=False)
    assert not request.cancelled.is_set()


def test_large_menu_creates_only_pages_until_opened(window):
    root, view, _, selected = window
    menu = tk.Menu(view.window, tearoff=False)
    try:
        choices = tuple(f"{i}.milk" for i in range(50_000))
        view._fill_presets(menu, choices, 0, len(choices))
        assert menu.index("end") == 49
        page = root.nametowidget(menu.entrycget(0, "menu"))
        assert page.index("end") is None
        root.tk.call(page.cget("postcommand"))
        assert page.index("end") == 9
        leaf = root.nametowidget(page.entrycget(1, "menu"))
        root.tk.call(leaf.cget("postcommand"))
        leaf.invoke(7)
        assert selected == [107]
    finally:
        menu.destroy()


def test_prepared_choices_map_to_exact_snapshot_files(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "z.MILK").write_text("[preset00]\n")
    (source / "pack").mkdir()
    (source / "pack/a\nline.milk").write_text("[preset00]\n")
    directory = tmp_path / "stage"
    directory.mkdir()
    result = frontend.prepare(directory, source)
    assert result["preset_choices"] == ("pack/a\nline.milk", "z.MILK")
    names = (directory / "preset-list").read_text().splitlines()
    assert len(names) == 2 and all(
        re.fullmatch(r"[a-f0-9]{64}\.milk", n) for n in names
    )
    for label, name in zip(result["preset_choices"], names):
        assert (
            directory / "playlist" / name
        ).resolve() == directory / "presets" / label
    assert (directory / "preset-selection").read_bytes() == struct.pack(
        ">II", 0xFFFFFFFF, 0
    )


def test_selection_record_and_descriptor_lifetime(tmp_path):
    path = tmp_path / "selection"
    path.write_bytes(struct.pack(">II", 0xFFFFFFFF, 0))
    descriptor = os.open(path, os.O_WRONLY | os.O_CLOEXEC)
    session = frontend.FrontendSession(
        Component(),
        Component(),
        Component(),
        SimpleNamespace(cleanup=lambda: None),
        presets=("one", "two"),
        selection_fd=descriptor,
    )
    try:
        session.select_preset(1)
        assert path.read_bytes() == struct.pack(">II", 1, 0xFFFFFFFE)
        for bad in (True, -1, 2, "0"):
            with pytest.raises(ValueError):
                session.select_preset(bad)
        session.select_preset(None)
        assert path.read_bytes() == struct.pack(">II", 0xFFFFFFFF, 0)
    finally:
        session.stop()
    with pytest.raises(OSError):
        os.fstat(descriptor)
    with pytest.raises(RuntimeError):
        session.select_preset(0)


def test_tk_only_queues_selection_for_owner_thread(monkeypatch, tmp_path):
    playback = object()
    app = SimpleNamespace(radio_proc=playback)
    owner = sidecar._ProjectMRequest(app, playback, str(tmp_path))
    app.radio_projectm_proc = owner
    calls = []
    session = object.__new__(frontend.FrontendSession)
    session.pid = 123
    session.pixels = SimpleNamespace(frames=pixels.FrameMailbox())
    session.presets = ("one", "two")
    session.select_preset = lambda index: calls.append((index, threading.get_ident()))
    session.poll = lambda: None
    session.stop = lambda: None
    monkeypatch.setattr(frontend, "start", lambda *a, **kw: session)
    assert not owner.select_preset(0)
    owner.thread.start()
    try:
        wait(lambda: owner.snapshot()[0] == "running")
        assert owner.preset_state() == (("one", "two"), None)
        for index in (0, 1):
            assert owner.select_preset(index)
        wait(lambda: calls and calls[-1][0] == 1)
        assert all(tid == owner.thread.ident for index, tid in calls)
        assert owner.select_preset(None)
        wait(lambda: calls[-1][0] is None)
        for bad in (True, -1, 2, "0"):
            assert not owner.select_preset(bad)
    finally:
        owner.stop()
        owner.thread.join(3)
    assert owner.done.is_set() and not owner.thread.is_alive()
    assert not owner.select_preset(0)
