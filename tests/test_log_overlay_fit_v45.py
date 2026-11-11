"""Log picture fitting in the real Tk widgets and isolated analysis workspace."""

import os
from pathlib import Path
import subprocess
from types import SimpleNamespace
import tkinter as tk
from unittest.mock import Mock

from PIL import Image, ImageDraw, ImageTk
import pytest

from netmon import app as app_module
from netmon.app import App
from netmon.ui.tabs.log_tab import build_log_tab
from tests.test_terminal_dock_v39 import open_dock, spin, workspace as workspace


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


@pytest.fixture
def overlay_app():
    root = tk.Tk()
    root.geometry("600x400")
    app = App.__new__(App)
    app.tk, app._w, app.children = root.tk, root._w, root.children
    app.lang = {}
    app.log_overlay_source_image = app.log_overlay_source_photo = None
    app.log_overlay_photo = None
    app.log_view_frame = tk.Frame(root)
    app.log_view_frame.pack(fill="both", expand=True)
    app.log_overlay_label = tk.Label(app.log_view_frame, anchor="center", bg="#111111")
    app.log_overlay_label.pack(fill="both", expand=True)
    app.terminal_dock = SimpleNamespace(workspace=SimpleNamespace(active=True))
    root.update()
    try:
        yield root, app
    finally:
        root.destroy()


@pytest.mark.parametrize("size", [(400, 400), (1200, 300), (300, 1200)])
def test_fit_preserves_all_image_edges_and_normal_mode_still_covers(overlay_app, size):
    root, app = overlay_app
    source = Image.new("RGB", size, "#999999")
    draw = ImageDraw.Draw(source)
    width, height = size
    draw.rectangle((0, 0, 12, height - 1), fill="red")
    draw.rectangle((width - 13, 0, width - 1, height - 1), fill="green")
    draw.rectangle((0, 0, width - 1, 12), fill="blue")
    draw.rectangle((0, height - 13, width - 1, height - 1), fill="yellow")
    original = source.tobytes()
    app.log_overlay_source_image = source
    for geometry in ("600x400", "450x500"):
        root.geometry(geometry)
        root.update()
        app._render_log_overlay_image()
        rendered = ImageTk.getimage(app.log_overlay_photo).convert("RGB")
        w, h = rendered.size
        assert w <= app.log_view_frame.winfo_width()
        assert h <= app.log_view_frame.winfo_height()
        assert abs(w * height - h * width) <= max(width, height)
        assert rendered.getpixel((0, h // 2)) == (255, 0, 0)
        assert rendered.getpixel((w - 1, h // 2)) == (0, 128, 0)
        assert rendered.getpixel((w // 2, 0)) == (0, 0, 255)
        assert rendered.getpixel((w // 2, h - 1)) == (255, 255, 0)
        assert app.log_overlay_label.cget("anchor") == "center"
    app.terminal_dock.workspace.active = False
    app._render_log_overlay_image()
    assert (app.log_overlay_photo.width(), app.log_overlay_photo.height()) == (
        app.log_view_frame.winfo_width(),
        app.log_view_frame.winfo_height(),
    )
    assert app.log_overlay_source_image is source and source.tobytes() == original


def test_native_tk_fallback_fits_without_pillow(overlay_app, monkeypatch):
    _root, app = overlay_app
    monkeypatch.setattr(app_module, "Image", None)
    monkeypatch.setattr(app_module, "ImageTk", None)
    source = tk.PhotoImage(width=1600, height=800)
    source.put("cyan", to=(0, 0, 1600, 800))
    app.log_overlay_source_photo = source
    app._render_log_overlay_image()
    assert app.log_overlay_photo.width() <= app.log_view_frame.winfo_width()
    assert app.log_overlay_photo.height() <= app.log_view_frame.winfo_height()
    assert (source.width(), source.height()) == (1600, 800)
    app.terminal_dock.workspace.active = False
    app._render_log_overlay_image()
    assert app.log_overlay_photo is source


@pytest.mark.parametrize("workspace", ["natural"], indirect=True)
def test_real_log_picture_fits_analysis_and_restores_normal_cover(workspace):
    root, app, errors = workspace
    app.dep_installer_button_var = tk.StringVar(master=root, value="Komponenten")
    app.var_auto_log_clear = tk.BooleanVar(master=root, value=False)
    app.attach_chad_context_menu = lambda *args: None
    app._restore_log_overlay_from_config = Mock()
    app._persist_log_overlay_preferences = Mock()
    app.log_overlay_active = False
    app.log_overlay_picker_open = False
    app.log_overlay_source_image = app.log_overlay_source_photo = None
    build_log_tab(app)
    path = Path(__file__).parents[1] / "tools/Log-Pics/Netmon.png"
    with Image.open(path) as image:
        app.log_overlay_source_image = image.convert("RGB")
    app.log_overlay_image_path = str(path)
    app.nb.select(app.tab_log)
    root.update()
    app._render_log_overlay_image()
    app._set_log_overlay_visible(True, persist=False)
    dock = open_dock(root, app, errors)
    app.nb.select(app.tab_log)
    root.update()
    for geometry in ("1280x600", "1280x800"):
        root.geometry(geometry)
        root.update()
        assert canvas_view(app) == (0, 1)
        assert app.log_overlay_photo.width() <= app.log_view_frame.winfo_width()
        assert app.log_overlay_photo.height() <= app.log_view_frame.winfo_height()
        assert app.log_overlay_label.cget("anchor") == "center"
    subprocess.run(
        ["import", "-window", str(root.winfo_id()), "/work/log-image-analysis.png"],
        check=True,
        timeout=10,
    )
    process = dock.process
    dock.close()
    spin(root, lambda: process.poll() is not None)
    root.update()
    assert (app.log_overlay_photo.width(), app.log_overlay_photo.height()) == (
        app.log_view_frame.winfo_width(),
        app.log_view_frame.winfo_height(),
    )
    app._persist_log_overlay_preferences.assert_not_called()
    assert not errors.called


def canvas_view(app):
    return app.page_canvas.yview()
