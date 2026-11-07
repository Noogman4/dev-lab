"""Private Xvfb terminal embedding and reversible docking tests."""

import json
import ctypes
import os
from pathlib import Path
import select
import subprocess
import time
import tkinter as tk
from tkinter import ttk
from unittest.mock import Mock

import pytest

from netmon.app import App
from netmon.features import chad_controller, terminal_dock
from netmon.ui.tabs.chad_tab import build_chad_analysis_content


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


@pytest.fixture
def workspace(monkeypatch, request):
    root = tk.Tk()
    callback_errors = []
    root.report_callback_exception = lambda *error: callback_errors.append(error)
    root.geometry("1280x800")
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    container = root
    canvas = None
    main_row = 0
    if getattr(request, "param", False):
        root.geometry("1280x600")
        outer = ttk.Frame(root)
        outer.grid(row=0, column=0, columnspan=2, sticky="nsew")
        canvas = tk.Canvas(outer, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)
        page_scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        page_scroll.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=page_scroll.set)
        container = ttk.Frame(canvas)
        container.columnconfigure(1, weight=1)
        main_row = 1
        page_window = canvas.create_window(
            (0, 0),
            window=container,
            anchor="nw",
            height=(0 if request.param == "natural" else 1500),
        )
        header = ttk.Frame(container, height=150)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)
        ttk.Label(header, text="NetMon Kopfbereich").grid()
        bottom = ttk.Frame(container, height=30)
        bottom.grid(row=2, column=0, columnspan=2, sticky="ew")
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(page_window, width=event.width),
        )
        container.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
    left = ttk.Frame(container, width=200)
    left.grid(row=main_row, column=0, sticky="nsew")
    left.grid_propagate(False)
    ttk.Label(left, text="Ampel / VPN unverändert").pack()
    right = ttk.Frame(container)
    right.grid(row=main_row, column=1, sticky="nsew")
    for column, minimum, weight in [(0, 700, 4), (1, 180, 1), (2, 180, 1)]:
        right.columnconfigure(column, minsize=minimum, weight=weight)
    right.rowconfigure(0, weight=1)
    app = App.__new__(App)
    app.tk, app._w, app.children = root.tk, root._w, root.children
    if canvas is not None:
        app.page_canvas, app.page = canvas, container
        app.page_window = page_window
        app.fixture_header, app.fixture_scrollbar = header, page_scroll
    app.lang = {}
    app.settings = {"terminal_start_mode": "docked"}
    app.save_settings = Mock()
    app.add_tooltip = lambda *a: None
    app._app_theme = {}
    app.main_work_area = ttk.Frame(right)
    app.main_work_area.grid(row=0, column=0, sticky="nsew")
    app.main_work_area.columnconfigure(0, weight=1, minsize=700)
    app.main_work_area.rowconfigure(1, weight=1)
    app.right_sidebar = ttk.Frame(right)
    app.right_sidebar.grid(row=0, column=1, columnspan=2, sticky="new")
    for column in range(2):
        group = ttk.LabelFrame(app.right_sidebar, text=f"Aktionsspalte {column+1}")
        group.grid(row=0, column=column, sticky="nsew")
        for name in ["DNS", "VPN", "Tools"]:
            ttk.Button(group, text=name).pack(fill="x")
    app.nb = ttk.Notebook(app.main_work_area)
    app.nb.grid(row=1, column=0, sticky="nsew")
    app.tab_chad_analysis = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_chad_analysis, text="Chad")
    if getattr(request, "param", False) == "natural":
        tall_tab = ttk.Frame(app.nb, height=2500, width=700)
        app.nb.add(tall_tab, text="Großer anderer Tab")
    app.chad_enabled_var = tk.BooleanVar(master=root, value=True)
    app.chad_auto_scroll_var = tk.BooleanVar(master=root, value=True)
    app.tooltips_enabled = tk.BooleanVar(master=root, value=False)
    for name in (
        "chad_analysis_status_var",
        "chad_dev_filter_status_var",
        "chad_online_status_var",
        "chad_chat_status_var",
        "chad_analysis_source_var",
    ):
        setattr(app, name, tk.StringVar(master=root, value="Private fixture"))
    app.chad_output_filter_var = tk.StringVar(master=root, value="Alles")
    app.chad_output_entries = []
    app.attach_copy_paste_context_menu = lambda *a: None
    app._apply_chad_chat_theme = lambda *a: None
    app._update_chad_controls_state = lambda *a: None
    build_chad_analysis_content(app, {})
    app.chad_chat_input.insert("1.0", "Ungesendeter Entwurf")
    chad_controller.append_to_chad_output(
        app,
        "Chad Antwort",
        "# Diagnose\n\nLinks den Befehl ausführen.\n```bash\nprintf 'Terminal funktioniert\\n'\n```\nDanach das Ergebnis prüfen.",
    )
    errors = Mock()
    monkeypatch.setattr(terminal_dock.messagebox, "showerror", errors)
    monkeypatch.setenv("GTK_IM_MODULE", "gtk-im-context-simple")
    root.update()
    try:
        yield root, app, errors
    finally:
        dock = app.__dict__.get("terminal_dock")
        if dock is not None:
            dock.close()
            if dock.process is not None:
                dock.process.wait(timeout=4)
        if root.winfo_exists():
            root.destroy()
        assert not callback_errors, callback_errors


def open_dock(root, app, errors):
    app.toggle_docked_terminal()
    dock = app.terminal_dock
    assert dock is not None, errors.call_args_list
    spin(root, lambda: dock.ready or not dock.active)
    assert dock.ready and dock.active, errors.call_args_list
    return dock


class PrivateKeys:
    """Native XTest events restricted to this test's isolated Xvfb display."""

    def __init__(self):
        assert os.environ.get("NETMON_TEST_ISOLATED") == "1"
        self.x = ctypes.CDLL("libX11.so.6")
        self.t = ctypes.CDLL("libXtst.so.6")
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.x.XOpenDisplay(None)
        assert self.display
        self.x.XStringToKeysym.argtypes = [ctypes.c_char_p]
        self.x.XStringToKeysym.restype = ctypes.c_ulong
        self.x.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        self.x.XKeysymToKeycode.restype = ctypes.c_uint
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.t.XTestFakeKeyEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self.t.XTestFakeMotionEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_ulong,
        ]
        self.t.XTestFakeButtonEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_int,
            ctypes.c_ulong,
        ]

    def key(self, name):
        code = self.x.XKeysymToKeycode(
            self.display, self.x.XStringToKeysym(name.encode())
        )
        self.t.XTestFakeKeyEvent(self.display, code, 1, 0)
        self.t.XTestFakeKeyEvent(self.display, code, 0, 0)
        self.x.XFlush(self.display)

    def shortcut(self, modifiers, name):
        codes = [
            self.x.XKeysymToKeycode(self.display, self.x.XStringToKeysym(m.encode()))
            for m in modifiers
        ]
        for code in codes:
            self.t.XTestFakeKeyEvent(self.display, code, 1, 0)
        self.key(name)
        for code in reversed(codes):
            self.t.XTestFakeKeyEvent(self.display, code, 0, 0)
        self.x.XFlush(self.display)

    def click(self, widget, x=20, y=20):
        self.t.XTestFakeMotionEvent(
            self.display, -1, widget.winfo_rootx() + x, widget.winfo_rooty() + y, 0
        )
        self.t.XTestFakeButtonEvent(self.display, 1, 1, 0)
        self.t.XTestFakeButtonEvent(self.display, 1, 0, 0)
        self.x.XFlush(self.display)

    def close(self):
        self.x.XCloseDisplay(self.display)

    def drag(self, root, widget, x, y, offset):
        self.t.XTestFakeMotionEvent(
            self.display, -1, widget.winfo_rootx() + x, widget.winfo_rooty() + y, 0
        )
        self.t.XTestFakeButtonEvent(self.display, 1, 1, 0)
        self.x.XSync(self.display, False)
        root.update()
        self.t.XTestFakeMotionEvent(
            self.display,
            -1,
            widget.winfo_rootx() + x + offset,
            widget.winfo_rooty() + y,
            0,
        )
        self.x.XSync(self.display, False)
        root.update()
        self.t.XTestFakeButtonEvent(self.display, 1, 0, 0)
        self.x.XSync(self.display, False)
        root.update()


def paste_and_enter(root, app, dock, keys, command):
    root.clipboard_clear()
    root.clipboard_append(command)
    dock.buttons["paste"].invoke()
    until = time.monotonic() + 0.2
    spin(root, lambda: time.monotonic() >= until)
    keys.key("Return")


def test_dock_preserves_widgets_and_restores_geometry(workspace):
    root, app, errors = workspace
    main, sidebar, text, input_field = (
        app.main_work_area,
        app.right_sidebar,
        app.chad_analysis_text,
        app.chad_chat_input,
    )
    grid = dict(main.grid_info()), dict(sidebar.grid_info())
    columns = [dict(main.master.columnconfigure(i)) for i in range(3)]
    minimum = root.minsize()
    controls = app.chad_output_filter_combo.master
    controls_grid = dict(controls.grid_info())
    dock = open_dock(root, app, errors)
    assert not sidebar.winfo_ismapped()
    assert main.winfo_manager() == "panedwindow"
    assert dock.surface.winfo_rootx() < text.winfo_rootx()
    assert app.chad_analysis_text is text and app.chad_chat_input is input_field
    assert input_field.get("1.0", "end-1c") == "Ungesendeter Entwurf"
    assert controls.grid_info()["row"] == 1
    assert dock.buttons["paste"].winfo_ismapped()
    process = dock.process
    app.toggle_docked_terminal()
    spin(root, lambda: process.poll() is not None)
    assert app.terminal_dock is None
    assert main.grid_info() == grid[0] and sidebar.grid_info() == grid[1]
    assert [dict(main.master.columnconfigure(i)) for i in range(3)] == columns
    assert controls.grid_info() == controls_grid
    assert root.minsize() == minimum
    assert sidebar.winfo_ismapped()
    assert app.chad_analysis_text is text and app.chad_chat_input is input_field
    assert not errors.called


def test_native_keyboard_shell_and_focus_return_to_chad(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    keys = PrivateKeys()
    try:
        keys.click(dock.surface)
        output = Path("/work/native-terminal-result")
        paste_and_enter(root, app, dock, keys, f"printf native-terminal-ok > {output}")
        spin(root, output.exists)
        assert output.read_text() == "native-terminal-ok"
        keys.click(app.chad_chat_input, 30, 10)
        root.update()
        keys.key("x")
        spin(root, lambda: "x" in app.chad_chat_input.get("1.0", "end-1c"))
        assert app.chad_analysis_text.get("1.0", "end").find("Diagnose") >= 0
        keys.click(dock.surface)
        process = dock.process
        paste_and_enter(root, app, dock, keys, "exit")
        spin(root, lambda: not dock.active)
        spin(root, lambda: process.poll() is not None)
        assert app.right_sidebar.winfo_ismapped()
        assert not errors.called
    finally:
        keys.close()


def test_divider_clamps_resizes_embedded_window_and_reopens(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    for target in [-2000, 100000, dock.initial_width]:
        dock.pane.sash_place(0, target, 0)
        dock._clamp()
        root.update()
        x = dock.pane.sash_coord(0)[0]
        assert x >= dock.min_terminal
        assert dock.main.winfo_width() >= dock.min_main
        assert (
            app.chad_chat_input.winfo_rootx() + app.chad_chat_input.winfo_width()
            <= root.winfo_rootx() + root.winfo_width()
        )
    until = time.monotonic() + 0.3
    spin(root, lambda: time.monotonic() >= until)
    info = subprocess.run(
        ["xwininfo", "-id", str(dock.window_id)],
        text=True,
        capture_output=True,
        check=True,
    ).stdout
    assert f"Width: {dock.surface.winfo_width()}" in info
    process = dock.process
    dock.close()
    spin(root, lambda: process.poll() is not None)
    second = open_dock(root, app, errors)
    assert second is not dock
    assert app.chad_chat_input.get("1.0", "end-1c") == "Ungesendeter Entwurf"
    assert not errors.called


def test_native_divider_drag_updates_real_pty_columns(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    keys = PrivateKeys()
    try:
        before = Path("/work/pty-before-size")
        after = Path("/work/pty-after-size")
        paste_and_enter(root, app, dock, keys, f"stty size > {before}")
        spin(root, before.exists)
        first = tuple(map(int, before.read_text().split()))
        x = dock.pane.sash_coord(0)[0]
        keys.drag(root, dock.pane, x + 3, 100, 50)
        assert dock.pane.sash_coord(0)[0] != x
        until = time.monotonic() + 0.3
        spin(root, lambda: time.monotonic() >= until)
        paste_and_enter(root, app, dock, keys, f"stty size > {after}")
        spin(root, after.exists)
        second = tuple(map(int, after.read_text().split()))
        assert second[1] > first[1]
        assert dock.main.winfo_width() >= dock.min_main
        assert not errors.called
    finally:
        keys.close()


def test_compact_terminal_stays_bottom_aligned_when_window_resizes(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    for height in (900, 600, 480):
        root.geometry(f"1280x{height}")
        root.update()
        assert 280 < dock.surface.winfo_height() < 560
        previous_height = min(280, dock.panel.winfo_height() * 2 // 5)
        assert abs(dock.terminal_card.winfo_height() - 2 * previous_height) <= 1
        assert dock.terminal_card.winfo_height() <= dock.panel.winfo_height() * 0.8
        bottom = dock.surface.winfo_rooty() + dock.surface.winfo_height()
        assert abs(bottom - (dock.main.winfo_rooty() + dock.main.winfo_height())) <= 2
        assert dock.surface.winfo_rooty() > app.chad_analysis_text.winfo_rooty()
        assert app.chad_chat_input.winfo_ismapped()
    assert not errors.called


def test_window_height_updates_real_terminal_rows(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    keys = PrivateKeys()
    try:
        before = Path("/work/pty-before-height")
        after = Path("/work/pty-after-height")
        paste_and_enter(root, app, dock, keys, f"stty size > {before}")
        spin(root, before.exists)
        first = tuple(map(int, before.read_text().split()))
        root.geometry("1280x480")
        root.update()
        until = time.monotonic() + 0.3
        spin(root, lambda: time.monotonic() >= until)
        paste_and_enter(root, app, dock, keys, f"stty size > {after}")
        spin(root, after.exists)
        second = tuple(map(int, after.read_text().split()))
        assert 2 < second[0] < first[0] < 40
        assert not errors.called
    finally:
        keys.close()


@pytest.mark.parametrize("workspace", [True, "natural"], indirect=True)
def test_workspace_fits_viewport_and_restores_normal_page(workspace):
    root, app, errors = workspace
    canvas = app.page_canvas
    canvas.yview_moveto(0.3)
    root.update()
    original_view = canvas.yview()[0]
    original_height = canvas.itemcget(app.page_window, "height")
    host_grid = dict(app.main_work_area.master.grid_info())
    dock = open_dock(root, app, errors)
    spin(root, lambda: dock.reveal_job is None and canvas.yview() == (0, 1))
    assert dock.workspace.active and dock.host.winfo_manager() == "place"
    assert not app.fixture_header.winfo_ismapped()
    assert not app.fixture_scrollbar.winfo_ismapped()
    top = canvas.winfo_rooty()
    assert dock.terminal_card.winfo_rooty() >= top
    assert (
        dock.surface.winfo_rooty() + dock.surface.winfo_height()
        <= top + canvas.winfo_height()
    )
    assert app.chad_chat_input.winfo_ismapped()
    app.chad_chat_input.delete("1.0", "end")
    app.chad_chat_input.insert("1.0", "\n".join(["Lange Eingabe"] * 30))
    chad_controller.append_to_chad_output(
        app, "Chad Antwort", "\n".join(["Ausgabe"] * 150)
    )
    previous_rows = 12
    for height in (800, 600, 480):
        root.geometry(f"1280x{height}")
        root.update()
        canvas.yview_scroll(20, "units")
        app._scroll_down(None)
        app._scroll_up(None)
        assert canvas.yview() == (0, 1)
        rows = int(app.chad_chat_input.cget("height"))
        assert 3 <= rows <= 12
        if height == 800:
            assert rows == 12
        assert rows <= previous_rows
        previous_rows = rows
        for widget in (
            dock.terminal_card,
            app.btn_chad_send,
            app.chad_chat_input,
            app.chad_analysis_text,
        ):
            assert widget.winfo_rooty() >= canvas.winfo_rooty()
            assert (
                widget.winfo_rooty() + widget.winfo_height()
                <= canvas.winfo_rooty() + canvas.winfo_height()
            )
        assert app.chad_analysis_text.winfo_height() >= 40
    app.chad_analysis_text.yview_moveto(1)
    assert app.chad_analysis_text.yview()[0] > 0
    assert canvas.yview() == (0, 1)
    root.geometry("1280x600")
    root.update()
    subprocess.run(
        ["import", "-window", str(root.winfo_id()), "/work/terminal-workspace.png"],
        check=True,
        timeout=10,
    )
    process = dock.process
    dock.close()
    spin(root, lambda: process.poll() is not None)
    assert dock.host.grid_info() == host_grid
    assert canvas.itemcget(app.page_window, "height") == original_height
    assert abs(canvas.yview()[0] - original_view) < 0.01
    assert app.fixture_header.winfo_ismapped()
    assert app.fixture_scrollbar.winfo_ismapped()
    second = open_dock(root, app, errors)
    spin(root, lambda: second.reveal_job is None and canvas.yview() == (0, 1))
    assert not errors.called


def test_timeout_restores_controls_and_reaps_unresponsive_helper(
    workspace, monkeypatch
):
    root, app, errors = workspace
    original = subprocess.Popen

    def unresponsive(*args, **kwargs):
        return original(
            ["/usr/bin/python3", "-I", "-c", "import time; time.sleep(60)"], **kwargs
        )

    monkeypatch.setattr(terminal_dock.subprocess, "Popen", unresponsive)
    app.toggle_docked_terminal()
    dock = app.terminal_dock
    dock.host.after_cancel(dock.job)
    dock.job = None
    dock.started -= 20
    started = time.monotonic()
    dock._poll()
    assert time.monotonic() - started < 1
    root.update()
    assert app.terminal_dock is None and app.right_sidebar.winfo_ismapped()
    dock.process.wait(timeout=4)
    assert errors.call_count == 1


def test_narrow_display_does_not_start_terminal_or_change_controls(
    workspace, monkeypatch
):
    root, app, errors = workspace
    monkeypatch.setattr(root, "winfo_screenwidth", lambda: 320)
    launch = Mock()
    monkeypatch.setattr(terminal_dock.subprocess, "Popen", launch)
    grid = dict(app.main_work_area.grid_info())
    minimum = root.minsize()
    app.toggle_docked_terminal()
    root.update()
    assert app.terminal_dock is None
    assert app.main_work_area.grid_info() == grid
    assert app.right_sidebar.winfo_ismapped()
    assert root.minsize() == minimum
    launch.assert_not_called()
    assert errors.call_count == 1


def test_external_terminal_menu_remains_visible_and_uses_existing_action(workspace):
    from types import SimpleNamespace

    root, app, errors = workspace
    app.open_external_terminal = Mock(return_value=True)
    app.show_terminal_menu(SimpleNamespace(x_root=20, y_root=30))
    root.update()
    menu = app._terminal_external_menu
    assert menu.winfo_ismapped()
    assert menu.entrycget(0, "label") == "Analysemodus"
    assert menu.entrycget(1, "label") == "Als eigenes Fenster öffnen"
    menu.invoke(1)
    app.open_external_terminal.assert_called_once_with()
    menu.unpost()
    assert app.__dict__.get("terminal_dock") is None
    assert not errors.called


def test_start_failure_restores_controls_without_fallback_launch(
    workspace, monkeypatch
):
    root, app, errors = workspace
    main_grid = dict(app.main_work_area.grid_info())
    monkeypatch.setattr(
        terminal_dock.subprocess,
        "Popen",
        Mock(side_effect=OSError("fixture launch failed")),
    )
    app.toggle_docked_terminal()
    root.update()
    assert app.terminal_dock is None
    assert app.main_work_area.grid_info() == main_grid
    assert app.right_sidebar.winfo_ismapped()
    assert errors.call_count == 1


@pytest.mark.parametrize("detached", [False, True])
def test_destroy_workspace_stops_owned_helper(workspace, detached):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    if detached:
        dock.detach()
        spin(root, lambda: dock.detached)
    process = dock.process
    dock.host.destroy()
    root.update()
    assert not dock.active
    process.wait(timeout=4)
    assert not errors.called


def test_launcher_has_main_button_and_start_mode_choices(workspace, monkeypatch):
    root, app, errors = workspace
    launch = Mock()
    monkeypatch.setattr(terminal_dock, "open_terminal", launch)
    launcher_row = ttk.Frame(app.right_sidebar)
    launcher_row.grid(row=1, column=0, columnspan=2)
    frame = app._build_terminal_launcher(launcher_row)
    root.update()
    button, choice = frame.winfo_children()
    assert button.cget("text") == "Terminal" and choice.cget("text") == "▾"
    button.invoke()
    launch.assert_called_once_with(app)
    menu = choice.nametowidget(choice.cget("menu"))
    menu.invoke(0)
    assert launch.call_args.args == (app, "docked")
    menu.invoke(1)
    assert launch.call_args.args == (app, "external")
    frame.destroy()
    assert not errors.called


def test_start_mode_persists_through_existing_settings_file(workspace):
    _root, app, errors = workspace
    app.netmon_config_dir = "/work/config/terminal-settings"
    app.netmon_config_path = app.netmon_config_dir + "/settings.json"
    app.log = Mock()
    del app.save_settings
    app.settings["keep_existing_setting"] = "unchanged"
    app.open_external_terminal = Mock(return_value=True)
    terminal_dock.open_terminal(app, "external")
    stored = json.loads(Path(app.netmon_config_path).read_text())
    assert stored["terminal_start_mode"] == "external"
    assert stored["keep_existing_setting"] == "unchanged"
    app.settings = {"terminal_start_mode": "docked"}
    app.load_settings()
    assert app.settings["terminal_start_mode"] == "external"
    terminal_dock.open_terminal(app)
    assert app.open_external_terminal.call_count == 2
    assert app.__dict__.get("terminal_dock") is None
    assert not errors.called


def test_failed_external_start_does_not_save_new_preference(workspace):
    _root, app, errors = workspace
    app.open_external_terminal = Mock(return_value=False)
    terminal_dock.open_terminal(app, "external")
    assert app.settings["terminal_start_mode"] == "docked"
    app.save_settings.assert_not_called()
    assert not errors.called


@pytest.mark.parametrize("workspace", [False, True], indirect=True)
def test_native_undock_redock_preserves_shell_and_output(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    process, pid = dock.process, dock.shell_pid
    keys = PrivateKeys()
    try:
        before = Path(f"/work/session-before-{pid}")
        paste_and_enter(
            root,
            app,
            dock,
            keys,
            f"NETMON_SESSION_SENTINEL=bleibt; cd /work; printf 'Vor dem Abdocken\\n'; printf '%s' $$ > {before}",
        )
        spin(root, before.exists)
        assert int(before.read_text()) == pid
        dock.buttons["detach"].invoke()
        spin(root, lambda: dock.detached)
        assert dock.process is process and dock.shell_pid == pid
        assert app.right_sidebar.winfo_ismapped()
        assert app.main_work_area.winfo_manager() == "grid"
        assert app.settings["terminal_start_mode"] == "external"
        after = Path(f"/work/session-detached-{pid}")
        root.clipboard_clear()
        root.clipboard_append(f"printf '%s:%s' $NETMON_SESSION_SENTINEL $PWD > {after}")
        terminal_dock.open_terminal(app)  # Raise the existing session.
        until = time.monotonic() + 0.2
        spin(root, lambda: time.monotonic() >= until)
        keys.shortcut(["Control_L", "Shift_L"], "v")
        until = time.monotonic() + 0.2
        spin(root, lambda: time.monotonic() >= until)
        keys.key("Return")
        spin(root, after.exists)
        assert after.read_text() == "bleibt:/work"
        subprocess.run(
            ["import", "-window", str(dock.window_id), "/work/terminal-detached.png"],
            check=True,
            timeout=10,
        )
        terminal_dock.open_terminal(app, "docked")
        spin(root, lambda: not dock.detached and dock.transition is None)
        assert dock.process is process and dock.shell_pid == pid
        assert not app.right_sidebar.winfo_ismapped()
        assert app.settings["terminal_start_mode"] == "docked"
        resumed = Path(f"/work/session-redocked-{pid}")
        paste_and_enter(
            root,
            app,
            dock,
            keys,
            f"printf '%s:%s' $NETMON_SESSION_SENTINEL $$ > {resumed}",
        )
        spin(root, resumed.exists)
        assert resumed.read_text() == f"bleibt:{pid}"
        root.update()
        subprocess.run(
            ["import", "-window", str(root.winfo_id()), "/work/terminal-redocked.png"],
            check=True,
            timeout=10,
        )
        paste_and_enter(root, app, dock, keys, "exit")
        spin(root, lambda: not dock.active)
        assert app.right_sidebar.winfo_ismapped()
        assert not errors.called
    finally:
        keys.close()


def test_closing_detached_window_exits_owned_session(workspace):
    from netmon.ui.terminal_helper import XEmbedFocus

    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    dock.detach()
    spin(root, lambda: dock.detached)
    bridge = XEmbedFocus()  # The test's private Xvfb, never the host display.
    try:
        event = bridge.Event()
        event.client.type = 33
        event.client.display = bridge.display
        event.client.window = dock.window_id
        event.client.message_type = bridge.x.XInternAtom(
            bridge.display, b"WM_PROTOCOLS", False
        )
        event.client.format = 32
        event.client.data.l[0] = bridge.x.XInternAtom(
            bridge.display, b"WM_DELETE_WINDOW", False
        )
        bridge.x.XSendEvent(
            bridge.display, dock.window_id, False, 0, ctypes.byref(event)
        )
        bridge.x.XFlush(bridge.display)
        spin(root, lambda: not dock.active)
        assert app.right_sidebar.winfo_ismapped()
        assert not errors.called
    finally:
        bridge.close()


def test_narrow_reattach_preserves_detached_session(workspace, monkeypatch):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    dock.detach()
    spin(root, lambda: dock.detached)
    process = dock.process
    monkeypatch.setattr(dock.toplevel, "winfo_screenwidth", lambda: 800)
    terminal_dock.open_terminal(app, "docked")
    root.update()
    assert dock.active and dock.detached and dock.transition is None
    assert process.poll() is None
    assert app.right_sidebar.winfo_ismapped()
    assert app.settings["terminal_start_mode"] == "external"
    assert errors.call_count == 1


def test_docked_terminal_visual_fixture(workspace):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    keys = PrivateKeys()
    try:
        output = Path("/work/terminal-visual-ready")
        paste_and_enter(
            root,
            app,
            dock,
            keys,
            f"printf 'Terminal funktioniert\\n'; printf ok > {output}",
        )
        spin(root, output.exists)
        root.update()
        subprocess.run(
            ["import", "-window", str(root.winfo_id()), "/work/terminal-docked.png"],
            check=True,
            timeout=10,
        )
        assert not errors.called
    finally:
        keys.close()


def spin(root, predicate, timeout=6):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(0.01)
    subprocess.run(
        ["import", "-window", str(root.winfo_id()), "/work/terminal-failure.png"],
        timeout=10,
        check=False,
    )
    raise AssertionError("Timed out waiting for private terminal fixture")


def test_native_vte_can_embed_in_tk_frame():
    root = tk.Tk()
    root.geometry("1000x700")
    frame = tk.Frame(root, container=True, background="black")
    frame.pack(fill="both", expand=True)
    root.update()
    helper = Path(__file__).parents[1] / "netmon/ui/terminal_helper.py"
    env = {**os.environ, "GDK_BACKEND": "x11", "NO_AT_BRIDGE": "1"}
    process = subprocess.Popen(
        [
            "/usr/bin/python3",
            "-I",
            "-B",
            str(helper),
            "--parent",
            str(frame.winfo_id()),
            "--width",
            "1000",
            "--height",
            "700",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    messages = []

    def receive():
        if select.select([process.stdout], [], [], 0)[0]:
            line = process.stdout.readline()
            if line:
                messages.append(json.loads(line))
        return bool(messages) or process.poll() is not None

    try:
        spin(root, receive)
        assert messages and messages[-1]["event"] == "ready", (
            messages,
            process.poll(),
            process.stderr.read() if process.poll() is not None else "",
        )
        window = messages[-1]["window"]
        info = subprocess.run(
            ["xwininfo", "-id", str(frame.winfo_id()), "-children"],
            text=True,
            capture_output=True,
            check=True,
        )
        assert hex(window) in info.stdout
        pane = tk.PanedWindow(root, orient="horizontal")
        sibling = ttk.Frame(root)
        frame.pack_forget()
        pane.pack(fill="both", expand=True)
        pane.add(frame, minsize=200)
        pane.add(sibling, minsize=200)
        root.update()
        assert len(pane.panes()) == 2
    finally:
        if process.poll() is None:
            process.stdin.write(b'{"action":"close"}\n')
            process.stdin.flush()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        Path("/work/terminal-helper-stderr.txt").write_bytes(process.stderr.read())
        root.destroy()
