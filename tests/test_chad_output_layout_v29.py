"""Real Chad layout and last-line visibility under private Xvfb."""

import tkinter as tk
from tkinter import ttk

import pytest

from netmon.app import App
from netmon.features import chad_controller
from netmon.ui.tabs.chad_tab import build_chad_analysis_content


@pytest.fixture
def chad_app():
    root = tk.Tk()
    root.geometry("820x480")
    app = App.__new__(App)
    app.lang = {}
    app._app_theme = {}
    app.tab_chad_analysis = ttk.Frame(root, padding=10)
    app.tab_chad_analysis.pack(fill="both", expand=True)
    app.chad_enabled_var = tk.BooleanVar(master=root, value=True)
    app.chad_auto_scroll_var = tk.BooleanVar(master=root, value=True)
    for name in (
        "chad_analysis_status_var",
        "chad_dev_filter_status_var",
        "chad_online_status_var",
        "chad_chat_status_var",
        "chad_analysis_source_var",
    ):
        setattr(app, name, tk.StringVar(master=root, value="Status fixture"))
    app.chad_output_filter_var = tk.StringVar(master=root, value="Alles")
    app.attach_copy_paste_context_menu = lambda *args: None
    app._apply_chad_chat_theme = lambda *args: None
    app._update_chad_controls_state = lambda *args: None
    app.chad_output_entries = []
    try:
        build_chad_analysis_content(app, {})
        yield root, app
    finally:
        root.destroy()


@pytest.mark.parametrize("geometry", ["820x480", "1024x768", "1280x720"])
def test_long_wrapped_analysis_reaches_last_line_with_footer_visible(
    chad_app, geometry
):
    root, app = chad_app
    root.geometry(geometry)
    text = (
        "\n".join(f"{i}: " + "Private wrapped report line. " * 8 for i in range(80))
        + "\nLAST_LINE_VISIBLE_END."
    )
    chad_controller.append_to_chad_output(app, "Chad Antwort: fixture", text)
    root.update()
    widget = app.chad_analysis_text
    widget.see("end")
    root.update()
    assert text in widget.get("1.0", "end")
    assert widget.yview()[1] == 1.0
    line = widget.dlineinfo("end-1c")
    assert line is not None
    assert line[1] >= 0
    assert line[1] + line[3] <= widget.winfo_height()
    assert (
        widget.winfo_rooty() + widget.winfo_height()
        <= root.winfo_rooty() + root.winfo_height()
    )
