"""Real GTK/VTE menu actions and native input on a private Xvfb display."""

import json
import os
from pathlib import Path
import re
import subprocess
import time

import pytest

from tests.test_terminal_dock_v39 import (
    PrivateKeys,
    open_dock,
    paste_and_enter,
    spin,
    workspace as workspace,
)


@pytest.fixture(autouse=True)
def require_isolation():
    assert os.environ.get("NETMON_TEST_ISOLATED") == "1"


GTK_CHECK = r"""
import importlib.util, json, sys, time
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gdk, GLib, Gtk, Vte
spec = importlib.util.spec_from_file_location("helper", sys.argv[1])
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
labels = json.load(open(sys.argv[2]))
labels = {k.removeprefix("terminal_menu_"): v for k, v in labels.items()
          if k.startswith("terminal_menu_")}
window = Gtk.Window()
window.set_default_size(600, 300)
terminal = Vte.Terminal()
terminal.set_scrollback_lines(10000)
window.add(terminal)
window.show_all()
def pump():
    until = time.monotonic() + .15
    while time.monotonic() < until:
        while Gtk.events_pending(): Gtk.main_iteration_do(False)
        time.sleep(.001)
pump()
terminal.feed(("FIRST-HISTORY-ä\r\n" + "".join(f"row-{i:03}\r\n" for i in range(200))
               + "LAST-HISTORY-ö").encode())
pump()
clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
clipboard.clear()
focus_calls = []
def focus():
    focus_calls.append(True)
    terminal.grab_focus()
    return False
def menu():
    m = helper.create_terminal_context_menu(terminal, focus, labels)
    items = {w.get_name(): w for w in m.get_children()
             if not isinstance(w, Gtk.SeparatorMenuItem)}
    return m, items
m, items = menu()
assert len(items) == 10
assert not items["copy_selection"].get_sensitive()
assert not items["unselect_all"].get_sensitive()
assert not items["paste"].get_sensitive()
assert not items["zoom_reset"].get_sensitive()
assert items["copy_all"].get_label() == "Copy all"
items["select_all"].activate()
pump()
assert terminal.get_has_selection()
m.destroy()
m, items = menu()
assert items["copy_selection"].get_sensitive()
items["copy_selection"].activate()
pump()
selection = clipboard.wait_for_text()
assert "FIRST-HISTORY-ä" in selection and "LAST-HISTORY-ö" in selection
adj = terminal.get_vadjustment()
adj.set_value(adj.get_lower() + 7)
view_before = adj.get_value()
clipboard.set_text("sentinel", -1)
items["copy_all"].activate()
pump()
all_text = clipboard.wait_for_text()
assert "FIRST-HISTORY-ä" in all_text and "LAST-HISTORY-ö" in all_text
assert terminal.get_has_selection() and adj.get_value() == view_before
items["copy_selection"].activate()
pump()
assert clipboard.wait_for_text() == selection
items["scroll_bottom"].activate()
assert adj.get_value() == adj.get_upper() - adj.get_page_size()
items["unselect_all"].activate()
assert not terminal.get_has_selection()
items["zoom_in"].activate()
assert abs(terminal.get_font_scale() - 1.1) < .001
m.destroy()
for step in range(15):
    m, items = menu()
    if items["zoom_in"].get_sensitive(): items["zoom_in"].activate()
    m.destroy()
m, items = menu()
assert terminal.get_font_scale() == 2 and not items["zoom_in"].get_sensitive()
m.destroy()
for step in range(20):
    m, items = menu()
    if items["zoom_out"].get_sensitive(): items["zoom_out"].activate()
    m.destroy()
m, items = menu()
assert abs(terminal.get_font_scale() - .6) < .001
assert not items["zoom_out"].get_sensitive()
assert items["zoom_reset"].get_sensitive()
items["zoom_reset"].activate()
assert terminal.get_font_scale() == 1
assert items["paste"].get_sensitive()
m.emit("deactivate")
pump()
assert focus_calls
m.destroy()
window.destroy()
print("NETMON_MENU_RESULT " + json.dumps({"items":10, "scrollback_characters":len(all_text),
                  "selection_preserved":True, "scroll_position_preserved":True,
                  "zoom_bounds":[.6,2], "language":"en"}))
"""


def test_real_vte_menu_clipboard_states_scrollback_selection_and_zoom():
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [
            "xvfb-run",
            "-a",
            "-e",
            "/work/menu-unit-xvfb.log",
            "-s",
            "-screen 0 1280x1024x24 -nolisten tcp -extension GLX",
            "/usr/bin/python3",
            "-I",
            "-B",
            "-c",
            GTK_CHECK,
            str(root / "netmon/ui/terminal_helper.py"),
            str(root / "netmon/lang/en.json"),
        ],
        capture_output=True,
        text=True,
        timeout=20,
    )
    Path("/work/menu-gtk-stderr.txt").write_text(result.stderr)
    Path("/work/menu-gtk-stdout.txt").write_text(result.stdout)
    assert result.returncode == 0, result.stdout + result.stderr
    reports = [
        line.removeprefix("NETMON_MENU_RESULT ")
        for line in result.stdout.splitlines()
        if line.startswith("NETMON_MENU_RESULT ")
    ]
    assert len(reports) == 1, result.stdout + result.stderr
    data = json.loads(reports[0])
    assert data["scrollback_characters"] > 1000
    Path("/work/menu-gtk-result.json").write_text(reports[0] + "\n")


def pause(root, seconds=0.15):
    until = time.monotonic() + seconds
    spin(root, lambda: time.monotonic() >= until)


def right_click(root, dock, keys):
    # Read only our owned helper's X window on this private test display.
    info = subprocess.run(
        ["xwininfo", "-id", str(dock.window_id)],
        capture_output=True,
        text=True,
        check=True,
        timeout=5,
    ).stdout
    x = int(re.search(r"Absolute upper-left X:\s*(-?\d+)", info)[1])
    y = int(re.search(r"Absolute upper-left Y:\s*(-?\d+)", info)[1])
    keys.t.XTestFakeMotionEvent(keys.display, -1, x + 30, y + 55, 0)
    keys.t.XTestFakeButtonEvent(keys.display, 3, 1, 0)
    keys.t.XTestFakeButtonEvent(keys.display, 3, 0, 0)
    keys.x.XFlush(keys.display)
    pause(root)


def activate(root, keys, down=0):
    keys.key("Home")
    for _ in range(down):
        keys.key("Down")
    keys.key("Return")
    pause(root)


def native_command(root, dock, keys, command):
    root.clipboard_clear()
    root.clipboard_append(command)
    dock.send("focus")
    pause(root)
    keys.shortcut(["Control_L", "Shift_L"], "v")
    pause(root)
    keys.key("Return")


@pytest.mark.parametrize("detached", [False, True], ids=["docked", "detached"])
def test_native_popup_copy_and_paste_keep_same_shell_and_require_enter(
    workspace, detached
):
    root, app, errors = workspace
    dock = open_dock(root, app, errors)
    keys = PrivateKeys()
    pid = dock.shell_pid
    try:
        ready = Path(f"/work/menu-output-ready-{detached}")
        paste_and_enter(
            root,
            app,
            dock,
            keys,
            "printf 'OFFSCREEN-%s\\n' START; "
            "for i in {1..150}; do printf 'line-%03d\\n' $i; done; "
            f"printf 'OUTPUT-END-%s\\n' DONE; touch {ready}",
        )
        spin(root, ready.exists)
        if detached:
            dock.detach()
            spin(root, lambda: dock.detached and dock.transition is None)
        right_click(root, dock, keys)
        subprocess.run(
            ["import", "-window", "root", f"/work/context-menu-{detached}.png"],
            check=True,
            timeout=10,
        )
        # Without a selection the first enabled item is Copy all.
        activate(root, keys)
        copied = root.clipboard_get()
        assert "OFFSCREEN-START" in copied and "OUTPUT-END-DONE" in copied
        right_click(root, dock, keys)
        activate(root, keys, 1)  # Select all.
        right_click(root, dock, keys)
        activate(root, keys)  # Copy selection is now the first enabled item.
        assert "OFFSCREEN-START" in root.clipboard_get()
        right_click(root, dock, keys)
        activate(root, keys, 1)  # Copy all with a selection.
        assert "OFFSCREEN-START" in root.clipboard_get()
        right_click(root, dock, keys)
        activate(root, keys, 3)  # Clear selection.
        output = Path(f"/work/menu-paste-{detached}")
        root.clipboard_clear()
        root.clipboard_append(f"printf menu-paste-ok > {output}")
        root.update()
        # Shift+F10 uses the same menu as a physical right click.
        dock.send("focus")
        pause(root)
        keys.shortcut(["Shift_L"], "F10")
        pause(root)
        activate(root, keys, 2)  # Copy all, Select all, Paste; disabled items skipped.
        assert not output.exists(), "Menu paste must not send Enter"
        keys.key("Return")
        spin(root, output.exists)
        assert output.read_text() == "menu-paste-ok"
        busy = Path(f"/work/menu-busy-{detached}")
        finished = Path(f"/work/menu-should-not-finish-{detached}")
        native_command(root, dock, keys, f"touch {busy}; sleep 20 && touch {finished}")
        spin(root, busy.exists)
        right_click(root, dock, keys)
        activate(root, keys, 3)  # Interrupt the foreground job, not the shell.
        resumed = Path(f"/work/menu-resumed-{detached}")
        native_command(root, dock, keys, f"printf '%s' $$ > {resumed}")
        spin(root, resumed.exists)
        assert int(resumed.read_text()) == pid and not finished.exists()
        assert dock.shell_pid == pid and dock.active
        assert not errors.called
    finally:
        keys.close()
