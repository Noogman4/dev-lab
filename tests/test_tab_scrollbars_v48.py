"""Real Tk overflow checks using passive builders, without App startup or services."""

import os
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from netmon.modules.secure_browser.manager import SecureBrowserManager
from netmon.modules.secure_browser.ui import create_secure_browser_tab
from netmon.ui.tabs import (
    download_scan_tab,
    fun_tab,
    hdd_tab,
    log_tab,
    security_tabs,
    tools_tabs,
    vpn_slots_tab,
)
from tests.test_terminal_dock_v39 import open_dock, workspace as workspace


class PassiveApp(SimpleNamespace):
    """Only Tk variables and inert callbacks; no App services are inherited."""

    def __getattr__(self, name):
        if name.endswith("_var") or name.startswith("var_"):
            value = tk.StringVar(self.root, value="")
        else:

            def value(*args, **kwargs):
                return None

        setattr(self, name, value)
        return value


@pytest.fixture
def ui():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"
    root = tk.Tk()
    root.geometry("1400x1000")
    errors = []
    root.report_callback_exception = lambda *error: errors.append(error)
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)
    app = PassiveApp(
        root=root,
        nb=notebook,
        system_nb=notebook,
        tools_nb=notebook,
        security_nb=notebook,
        settings={},
        lang={},
        wg_profiles=[],
        vpn_slots=[],
        primary_vpn_slots=[],
        path_guard_last_result={},
    )
    app.tr = lambda key, default=None: default or key
    app._nmap_preset_options = lambda: {}
    try:
        yield root, app
        root.update()
        assert not errors
    finally:
        root.destroy()


def reveal(root, widget):
    child = widget
    while child.master is not None:
        parent = child.master
        if isinstance(parent, ttk.Notebook):
            parent.select(child)
        child = parent
    root.update()


def check_overflow(root, widget):
    """Drive the real scrollbar command and verify both directions of binding."""
    reveal(root, widget)
    bars = [
        child
        for child in widget.master.winfo_children()
        if isinstance(child, ttk.Scrollbar) and str(child.cget("orient")) == "vertical"
    ]
    assert len(bars) == 1, str(widget)
    bar = bars[0]
    assert widget.cget("yscrollcommand")
    assert bar.cget("command")
    assert bar.winfo_ismapped()
    assert bar.winfo_x() >= widget.winfo_x() + widget.winfo_width()
    selected = None
    state = None
    if isinstance(widget, tk.Text):
        state = str(widget.cget("state"))
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", "".join(f"Example line {i}\n" for i in range(500)))
        widget.tag_add("sel", "3.0", "3.end")
        selected = widget.get("sel.first", "sel.last")
        widget.configure(state=state)
    elif isinstance(widget, ttk.Treeview):
        columns = widget.cget("columns")
        for i in range(500):
            widget.insert("", "end", iid=f"example-{i}", values=[str(i)] * len(columns))
        widget.selection_set("example-3")
        selected = widget.selection()
    else:
        assert isinstance(widget, tk.Listbox)
        widget.delete(0, "end")
        widget.insert("end", *(f"Example row {i}" for i in range(500)))
        widget.selection_set(3)
        selected = widget.curselection()
    widget.yview_moveto(0)
    root.update()
    assert widget.yview()[0] == 0
    assert widget.yview()[1] < 1
    root.tk.call(bar.cget("command"), "moveto", 1.0)
    root.update()
    assert widget.yview()[0] > 0.5
    assert widget.yview()[1] == 1
    assert bar.get() == pytest.approx(widget.yview())
    widget.yview_moveto(0)
    root.update()
    assert bar.get()[0] == 0
    if isinstance(widget, tk.Text):
        assert str(widget.cget("state")) == state
        assert widget.get("sel.first", "sel.last") == selected
    elif isinstance(widget, ttk.Treeview):
        assert widget.selection() == selected
    else:
        assert widget.curselection() == selected


@pytest.mark.parametrize(
    "builder,names",
    [
        (hdd_tab.build_hdd_tab, ["hdd_table", "hdd_info_text"]),
        (fun_tab.build_fun_tab, ["fun_games_table"]),
        (vpn_slots_tab.build_vpn_slots_tab, ["vpn_table"]),
        (tools_tabs.build_basic_tools_tabs, ["iftop_text"]),
        (
            security_tabs.build_security_tabs,
            [
                "path_guard_detail",
                "process_guard_tree",
                "process_guard_detail",
                "startup_guard_details_text",
                "repository_guard_detail_text",
                "roots_baseline_guard_history_list",
                "firewall_tab_summary_text",
            ],
        ),
    ],
    ids=["hdd", "fun", "vpn", "tools", "guards"],
)
def test_actual_tab_displays_scroll_long_content(ui, builder, names):
    root, app = ui
    builder(app)
    for name in names:
        check_overflow(root, getattr(app, name))


def test_scan_capture_and_log_image_picker_scroll(ui):
    root, app = ui
    for name in ("scan", "packet_capture", "log"):
        frame = ttk.Frame(app.nb)
        app.nb.add(frame, text=name)
        setattr(app, f"tab_{name}", frame)
    download_scan_tab.build_download_scan_result_panel(app, app.tab_scan)
    security_tabs.build_packet_capture_output_panel(app)
    log_tab.build_log_tab(app)
    app.log_overlay_picker_frame.place(relx=0.1, rely=0.1, relwidth=0.8, relheight=0.8)
    for widget in (
        app.download_scan_result_text,
        app.packet_capture_text,
        app.log_overlay_picker_list,
    ):
        check_overflow(root, widget)
    if Path("/work").exists():
        from PIL import ImageGrab

        ImageGrab.grab().save("/work/log-picker-scrollbars.png")


def test_secure_browser_summary_scrolls_without_service_access(ui):
    root, app = ui
    service = Mock()
    manager = SecureBrowserManager(service=service)
    manager.render_preflight_text = lambda: "Synthetic preflight; no service access"
    frame = create_secure_browser_tab(app.nb, manager)
    app.nb.add(frame, text="Secure Browser")

    def descendants(widget):
        for child in widget.winfo_children():
            yield child
            yield from descendants(child)

    summary = next(
        child
        for child in descendants(frame)
        if isinstance(child, tk.Text) and int(child.cget("height")) == 3
    )
    check_overflow(root, summary)
    assert not service.mock_calls


@pytest.mark.parametrize("workspace", ["natural"], indirect=True)
def test_new_scrollbars_fit_analysis_workspace(workspace):
    root, app, errors = workspace
    app.attach_selection_copy_shortcuts = lambda *args: None
    app.attach_text_context_menu = lambda *args: None
    app.attach_chad_context_menu = lambda *args: None
    for name in ("status", "last_scan", "result_summary", "file"):
        setattr(app, f"download_scan_{name}_var", tk.StringVar(root, value="Test"))
    app.tab_packet_capture = ttk.Frame(app.nb)
    app.nb.add(app.tab_packet_capture, text="Capture")
    security_tabs.build_packet_capture_output_panel(app)
    scan = ttk.Frame(app.nb)
    app.nb.add(scan, text="D-Scan")
    download_scan_tab.build_download_scan_result_panel(app, scan)
    open_dock(root, app, errors)
    for widget in (app.packet_capture_text, app.download_scan_result_text):
        check_overflow(root, widget)
        assert widget.winfo_rooty() + widget.winfo_height() <= (
            root.winfo_rooty() + root.winfo_height()
        )
        root.geometry("1200x700")
        root.update()
        assert app.page_canvas.yview() == (0, 1)
    from PIL import ImageGrab

    ImageGrab.grab().save("/work/scan-output-analysis.png")
