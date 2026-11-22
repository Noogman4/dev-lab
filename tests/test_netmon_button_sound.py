import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon.features import terminal_dock
from netmon.ui import button_sound
from netmon.ui.tabs.settings_tab import build_settings_general_system


@pytest.fixture
def root():
    try:
        window = tk.Tk()
    except tk.TclError as exc:
        pytest.skip(f"Tk display unavailable: {exc}")
    try:
        yield window
    finally:
        window.destroy()


@pytest.fixture
def installed_sound(root, monkeypatch, tmp_path):
    player = tmp_path / "paplay"
    sound = tmp_path / "audio-volume-change.oga"
    for path in (player, sound):
        path.touch()
    monkeypatch.setattr(button_sound, "_PLAYER", player)
    monkeypatch.setattr(button_sound, "_SOUND", sound)
    events = []

    class InlineThread:
        def __init__(self, *, target, daemon):
            assert daemon
            self.target = target

        def start(self):
            self.target()

    def play(args, **_kwargs):
        assert args == [str(player), str(sound)]
        events.append("sound")

    monkeypatch.setattr(
        button_sound,
        "threading",
        SimpleNamespace(Lock=button_sound.threading.Lock, Thread=InlineThread),
    )
    monkeypatch.setattr(button_sound.subprocess, "run", play)
    enabled = tk.BooleanVar(root, value=True)
    play_command = button_sound.install_button_sound(root, enabled=enabled.get)
    return enabled, events, play_command


def test_sound_follows_button_activation(root, installed_sound):
    enabled, events, _ = installed_sound
    button = ttk.Button(root, text="Run", command=lambda: events.append("action"))
    button.pack()
    root.update()
    button.focus_force()
    root.update()

    button.event_generate("<ButtonRelease-1>", x=5, y=5)
    button.event_generate("<Button-1>", x=5, y=5)
    assert events == []
    button.event_generate("<ButtonRelease-1>", x=5, y=5)
    button.event_generate("<KeyPress-space>")
    assert events == ["sound", "action", "sound", "action"]

    events.clear()
    button.event_generate("<Button-1>", x=5, y=5)
    button.event_generate("<Leave>", x=-5, y=5, state=0x100)
    button.event_generate("<ButtonRelease-1>", x=-5, y=5)
    button.state(["disabled"])
    button.event_generate("<Button-1>", x=5, y=5)
    button.event_generate("<ButtonRelease-1>", x=5, y=5)
    button.event_generate("<KeyPress-space>")
    assert events == []

    button.state(["!disabled"])
    button.invoke()
    assert events == ["action"]

    events.clear()
    enabled.set(False)
    button.event_generate("<Button-1>", x=5, y=5)
    button.event_generate("<ButtonRelease-1>", x=5, y=5)
    button.event_generate("<KeyPress-space>")
    assert events == ["action", "action"]

    enabled.set(True)
    button.event_generate("<KeyPress-space>")
    assert events == ["action", "action", "sound", "action"]


def test_checkbox_without_command_plays_sound_only_when_activated(
    root, installed_sound
):
    enabled, events, _ = installed_sound
    selected = tk.BooleanVar(root, value=False)
    checkbox = ttk.Checkbutton(root, text="Option", variable=selected)
    checkbox.pack()
    root.update()
    checkbox.focus_force()
    root.update()

    checkbox.event_generate("<Button-1>", x=5, y=5)
    checkbox.event_generate("<Leave>", x=-5, y=5, state=0x100)
    checkbox.event_generate("<ButtonRelease-1>", x=-5, y=5)
    assert not selected.get() and events == []

    checkbox.event_generate("<Button-1>", x=5, y=5)
    checkbox.event_generate("<ButtonRelease-1>", x=5, y=5)
    assert selected.get() and events == ["sound"]

    checkbox.event_generate("<space>")
    assert not selected.get() and events == ["sound", "sound"]

    checkbox.state(["disabled"])
    checkbox.event_generate("<Button-1>", x=5, y=5)
    checkbox.event_generate("<ButtonRelease-1>", x=5, y=5)
    checkbox.event_generate("<<Invoke>>")
    assert not selected.get() and events == ["sound", "sound"]

    checkbox.state(["!disabled"])
    selected.set(True)
    assert events == ["sound", "sound"]

    enabled.set(False)
    checkbox.event_generate("<<Invoke>>")
    assert not selected.get() and events == ["sound", "sound"]


def test_security_systemcheck_checkboxes_use_click_sound(root, installed_sound):
    _, events, _ = installed_sound
    app = App.__new__(App)
    app.tr = lambda _key, fallback: fallback
    app._applying_chad_systemcheck_profile = False
    app.chad_systemcheck_profile_var = tk.StringVar(root, value="full")
    app.chad_security_tools_status_var = tk.StringVar(root)
    app.security_systemcheck_status_var = tk.StringVar(root)
    app.refresh_chad_security_tools_status = lambda: None
    variables = {}
    for name in (
        "security_summary",
        "startup_guard",
        "path_guard",
        "process_guard",
        "lynis",
        "rkhunter",
        "clamav",
    ):
        variable = tk.BooleanVar(root, value=False)
        setattr(app, f"var_systemcheck_{name}", variable)
        variables[str(variable)] = variable
    panel = app.build_security_systemcheck_panel(root)
    root.update()

    toggle_grid = panel.winfo_children()[0]
    checkboxes = [
        widget
        for column in toggle_grid.winfo_children()
        for widget in column.winfo_children()
    ]
    assert len(checkboxes) == len(variables)
    for checkbox in checkboxes:
        checkbox.event_generate("<Button-1>", x=5, y=5)
        checkbox.event_generate("<ButtonRelease-1>", x=5, y=5)
        assert variables[str(checkbox.cget("variable"))].get()

    assert events == ["sound"] * len(checkboxes)
    assert app.chad_systemcheck_profile_var.get() == "custom"


def test_sound_follows_mouse_clicks_on_enabled_tabs(root, installed_sound):
    enabled, events, _ = installed_sound
    notebook = ttk.Notebook(root, width=440, height=120)
    notebook.pack()
    first, second, disabled = [ttk.Frame(notebook) for _ in range(3)]
    notebook.add(first, text="First")
    notebook.add(second, text="Second")
    notebook.add(disabled, text="Disabled", state="disabled")
    root.update()

    def click_tab(index):
        for y in range(notebook.winfo_height()):
            for x in range(notebook.winfo_width()):
                hit = root.tk.call(str(notebook), "index", f"@{x},{y}")
                if str(hit) == str(index):
                    notebook.event_generate("<Button-1>", x=x, y=y)
                    return
        pytest.fail(f"No clickable area found for tab {index}")

    click_tab(1)
    assert notebook.select() == str(second)
    assert events == ["sound"]

    click_tab(1)
    assert events == ["sound", "sound"]

    click_tab(2)
    blank_x = notebook.winfo_width() - 5
    assert root.tk.call(str(notebook), "index", f"@{blank_x},5") == ""
    notebook.event_generate("<Button-1>", x=blank_x, y=5)
    assert notebook.select() == str(second)
    assert events == ["sound", "sound"]

    notebook.select(first)
    root.update()
    assert events == ["sound", "sound"]

    enabled.set(False)
    click_tab(1)
    assert notebook.select() == str(second)
    assert events == ["sound", "sound"]


def test_status_light_and_text_play_sound_before_existing_actions(
    root, installed_sound
):
    enabled, events, _ = installed_sound
    app = App.__new__(App)
    app.on_light_click = lambda key: events.append(key)
    light = app.make_light(root, "Firewall")
    app._bind_light_click(light, "ufw")
    canvas, _, label = light

    def context_menu(event):
        events.append(("menu", event.widget))
        return "break"

    for widget in (canvas, label):
        widget.bind("<Button-3>", context_menu)
    root.bind("<Button-3>", lambda _event: events.append("propagated"))
    status_text = ttk.Label(root, text="Logging: low")
    status_text.pack()
    button_sound.bind_status_click_sound(status_text)
    ordinary_text = ttk.Label(root, text="Other text")
    ordinary_text.pack()
    root.update()

    for widget in (canvas, label):
        events.clear()
        widget.event_generate("<Button-1>", x=5, y=5)
        widget.event_generate("<Button-3>", x=5, y=5)
        assert events == ["sound", "ufw", "sound", ("menu", widget)]

    events.clear()
    status_text.event_generate("<Button-1>", x=5, y=5)
    status_text.event_generate("<Button-3>", x=5, y=5)
    ordinary_text.event_generate("<Button-1>", x=5, y=5)
    assert events == ["sound", "sound", "propagated"]

    events.clear()
    enabled.set(False)
    label.event_generate("<Button-1>", x=5, y=5)
    label.event_generate("<Button-3>", x=5, y=5)
    assert events == ["ufw", ("menu", label)]


def test_status_context_menu_plays_sound_when_an_entry_is_selected(
    root, installed_sound
):
    enabled, events, play_command = installed_sound
    app = App.__new__(App)
    app._click_sound_command = play_command
    app._close_active_context_menu = lambda: None
    app._schedule_active_context_menu_close = lambda: None
    _, _, label = app.make_light(root, "VPN")
    app._bind_light_click((label,), "vpn")
    ordinary_label = ttk.Label(root, text="Other text")
    menu = tk.Menu(root, tearoff=False)
    menu.add_command(label="CH-685", command=lambda: events.append("connect"))
    menu.add_command(
        label="Unavailable", state="disabled", command=lambda: events.append("disabled")
    )
    menu.add_separator()
    menu.add_command(label="VPN trennen", command=lambda: events.append("disconnect"))
    status_event = SimpleNamespace(widget=label, x_root=30, y_root=30)
    root.update()

    assert app._show_context_menu(menu, status_event) == "break"
    root.update()
    assert events == []
    menu.invoke(1)
    menu.invoke(2)
    y = menu.yposition(0) + 3
    menu.event_generate("<Enter>", x=5, y=y)
    menu.event_generate("<Motion>", x=5, y=y)
    assert menu.index("active") == 0
    assert events == []
    menu.event_generate("<Button-1>", x=5, y=y)
    menu.event_generate("<ButtonRelease-1>", x=5, y=y)
    assert events == ["sound", "connect"]

    app._show_context_menu(menu, status_event)
    menu.invoke(3)
    assert events == ["sound", "connect", "sound", "disconnect"]
    enabled.set(False)
    menu.invoke(0)
    assert events == ["sound", "connect", "sound", "disconnect", "connect"]
    menu.unpost()

    enabled.set(True)
    events.clear()
    ordinary_menu = tk.Menu(root, tearoff=False)
    ordinary_menu.add_command(label="Copy", command=lambda: events.append("copy"))
    app._show_context_menu(
        ordinary_menu, SimpleNamespace(widget=ordinary_label, x_root=30, y_root=30)
    )
    ordinary_menu.invoke(0)
    assert events == ["copy"]


def test_missing_sound_leaves_native_binding(root, monkeypatch, tmp_path):
    monkeypatch.setattr(button_sound, "_SOUND", tmp_path / "missing.oga")
    original = root.bind_class("TButton", "<ButtonRelease-1>")
    original_notebook = root.bind_class("TNotebook", "<Button-1>")
    assert button_sound.install_button_sound(root, enabled=lambda: True) is None
    assert root.bind_class("TButton", "<ButtonRelease-1>") == original
    assert root.bind_class("TNotebook", "<Button-1>") == original_notebook


@pytest.mark.parametrize("state", ["readonly", "normal"])
def test_combobox_plays_sound_when_opened_and_when_clicking_a_row(
    root, installed_sound, state
):
    enabled, events, _ = installed_sound
    combo = ttk.Combobox(root, values=("First", "Second"), state=state)
    combo.current(0)
    combo.bind("<<ComboboxSelected>>", lambda _event: events.append(combo.get()))
    combo.pack()
    root.update()

    y = combo.winfo_height() // 2
    arrow_x = next(
        x for x in range(combo.winfo_width()) if combo.identify(x, y).endswith("arrow")
    )
    popdown = root.tk.call("ttk::combobox::PopdownWindow", str(combo))
    listbox = f"{popdown}.f.l"

    def open_by_mouse():
        combo.event_generate("<ButtonPress-1>", x=arrow_x, y=y)
        combo.event_generate("<ButtonRelease-1>", x=arrow_x, y=y)
        root.update()

    def click_row(row):
        _, row_y, _, row_height = root.tk.call(listbox, "bbox", row)
        row_y += row_height // 2
        for event in ("<Motion>", "<ButtonPress-1>", "<ButtonRelease-1>"):
            root.tk.call("event", "generate", listbox, event, "-x", 5, "-y", row_y)
        root.update()

    assert events == []
    if state == "normal":
        combo.event_generate("<ButtonPress-1>", x=5, y=y)
        combo.event_generate("<ButtonRelease-1>", x=5, y=y)
        root.update()
        assert not root.tk.getboolean(root.tk.call("winfo", "ismapped", popdown))
        assert events == []

    combo.state(["disabled"])
    open_by_mouse()
    assert events == []
    combo.state(["!disabled"])

    open_by_mouse()
    assert events == ["sound"]
    click_row(1)
    assert events == ["sound", "sound", "Second"]
    assert combo.current() == 1

    open_by_mouse()
    root.tk.call("event", "generate", listbox, "<Escape>")
    root.update()
    assert events == ["sound", "sound", "Second", "sound"]

    enabled.set(False)
    events.clear()
    open_by_mouse()
    click_row(0)
    assert events == ["First"]
    assert combo.current() == 0


def test_terminal_choice_plays_sound_on_open_and_selection(
    root, installed_sound, monkeypatch
):
    enabled, events, play_command = installed_sound
    app = App.__new__(App)
    app._click_sound_command = play_command
    app.tr = lambda _key, fallback: fallback
    app.add_tooltip = lambda *_args: None
    monkeypatch.setattr(
        terminal_dock, "open_terminal", lambda _app, mode: events.append(mode)
    )
    launcher = app._build_terminal_launcher(root)
    _, choice = launcher.winfo_children()
    menu = choice.nametowidget(choice.cget("menu"))
    root.update()

    def click(widget, x, y):
        widget.event_generate("<Button-1>", x=x, y=y)
        widget.event_generate("<ButtonRelease-1>", x=x, y=y)

    choice.state(["disabled"])
    click(choice, 5, 5)
    assert not menu.winfo_ismapped()
    assert events == []
    choice.state(["!disabled"])

    for index, mode in enumerate(("docked", "external")):
        events.clear()
        x = 5 if index == 0 else choice.winfo_width() - 5
        click(choice, x, 5)
        assert menu.winfo_ismapped()
        assert events == ["sound"]

        y = menu.yposition(index) + 3
        menu.event_generate("<Enter>", x=5, y=y)
        menu.event_generate("<Motion>", x=5, y=y)
        click(menu, 5, y)
        assert events == ["sound", "sound", mode]
        assert not menu.winfo_ismapped()

    enabled.set(False)
    events.clear()
    click(choice, 5, 5)
    assert menu.winfo_ismapped()
    menu.invoke(0)
    assert events == ["docked"]


def test_setup_checkbox_persists_click_sound_preference(root, tmp_path):
    app = App.__new__(App)
    app.tr = lambda key, fallback=None: fallback or key
    app.settings = app._default_settings_payload()
    app.netmon_config_dir = str(tmp_path)
    app.netmon_config_path = str(tmp_path / "config.json")
    app.log = lambda message: pytest.fail(message)
    app.var_button_sound = tk.BooleanVar(
        root, value=app.settings["button_sound_enabled"]
    )
    app.autostart_var = tk.BooleanVar(root)
    app.radio_desktop_launcher_var = tk.BooleanVar(root)
    app.var_start_security_monitoring = tk.BooleanVar(root)
    app.var_language = tk.StringVar(root)
    app.var_theme_choice = tk.StringVar(root)
    app.var_isp_dns_fallback_profile = tk.StringVar(root)
    app._language_choice_values = lambda: ("Deutsch",)

    build_settings_general_system(app, root, {"dark": "Dark"}, [])
    group = root.winfo_children()[0]
    checkbox = next(
        widget
        for widget in group.winfo_children()
        if isinstance(widget, ttk.Checkbutton)
        and widget.cget("variable") == str(app.var_button_sound)
    )
    assert checkbox.instate(["selected"])

    checkbox.invoke()
    assert app.var_button_sound.get() is False
    app.settings = app._default_settings_payload()
    app.load_settings()
    assert app.settings["button_sound_enabled"] is False

    checkbox.invoke()
    assert app.var_button_sound.get() is True
    app.settings = app._default_settings_payload()
    app.settings["button_sound_enabled"] = False
    app.load_settings()
    assert app.settings["button_sound_enabled"] is True
