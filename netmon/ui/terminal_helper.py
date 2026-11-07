"""Separate GTK3/VTE terminal process embedded in NetMon's own X11 frame.

Run with system Python: the source venv need not import GTK or mix GTK/Tk loops.
The private stdin/stdout protocol carries controls/status, never shell output.
"""

import argparse
import ctypes
import json
import os
import sys

TERMINAL_MENU_LABELS = {
    "copy_selection": "Auswahl kopieren",
    "copy_all": "Alles kopieren",
    "select_all": "Alles auswählen",
    "unselect_all": "Auswahl aufheben",
    "paste": "Einfügen",
    "interrupt": "Vorgang abbrechen (Strg+C)",
    "scroll_bottom": "Zum Ende springen",
    "zoom_in": "Schrift vergrößern",
    "zoom_out": "Schrift verkleinern",
    "zoom_reset": "Standardgröße",
}


def create_terminal_context_menu(terminal, focus, labels=None):
    """Build actions in the VTE process; clipboard contents stay out of IPC."""
    from gi.repository import Gdk, Gio, GLib, Gtk, Vte

    labels = labels or {}
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)

    def copy_all():
        # The memory stream includes retained scrollback without changing the
        # current selection, scroll position or the shell's input line.
        stream = Gio.MemoryOutputStream.new_resizable()
        terminal.write_contents_sync(stream, Vte.WriteFlags.DEFAULT, None)
        stream.close(None)
        text = stream.steal_as_bytes().get_data().decode("utf-8", errors="replace")
        clipboard.set_text(text, -1)

    def bottom():
        adjustment = terminal.get_vadjustment()
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())

    scale = terminal.get_font_scale()
    selected = terminal.get_has_selection()
    actions = (
        (
            "copy_selection",
            lambda: terminal.copy_clipboard_format(Vte.Format.TEXT),
            selected,
        ),
        ("copy_all", copy_all, True),
        ("select_all", terminal.select_all, True),
        ("unselect_all", terminal.unselect_all, selected),
        None,
        ("paste", terminal.paste_clipboard, clipboard.wait_is_text_available()),
        None,
        ("interrupt", lambda: terminal.feed_child(b"\x03"), True),
        None,
        ("scroll_bottom", bottom, True),
        None,
        (
            "zoom_in",
            lambda: terminal.set_font_scale(min(2.0, round(scale + 0.1, 2))),
            scale < 2.0,
        ),
        (
            "zoom_out",
            lambda: terminal.set_font_scale(max(0.6, round(scale - 0.1, 2))),
            scale > 0.6,
        ),
        ("zoom_reset", lambda: terminal.set_font_scale(1.0), scale != 1.0),
    )
    menu = Gtk.Menu()
    menu.attach_to_widget(terminal, None)
    for action in actions:
        if action is None:
            menu.append(Gtk.SeparatorMenuItem())
            continue
        name, callback, enabled = action
        item = Gtk.MenuItem(label=labels.get(name, TERMINAL_MENU_LABELS[name]))
        item.set_name(name)
        item.set_sensitive(enabled)
        item.connect("activate", lambda _item, callback=callback: callback())
        menu.append(item)
    menu.connect("deactivate", lambda *_args: GLib.idle_add(focus))
    menu.show_all()
    return menu


class XEmbedFocus:
    """Tk is not GtkSocket: notify our own GtkPlug of keyboard activation."""

    class Data(ctypes.Union):
        _fields_ = [
            ("b", ctypes.c_char * 20),
            ("s", ctypes.c_short * 10),
            ("l", ctypes.c_long * 5),
        ]

    def __init__(self):
        class Client(ctypes.Structure):
            _fields_ = [
                ("type", ctypes.c_int),
                ("serial", ctypes.c_ulong),
                ("send_event", ctypes.c_int),
                ("display", ctypes.c_void_p),
                ("window", ctypes.c_ulong),
                ("message_type", ctypes.c_ulong),
                ("format", ctypes.c_int),
                ("data", XEmbedFocus.Data),
            ]

        class Event(ctypes.Union):
            _fields_ = [("client", Client), ("padding", ctypes.c_long * 24)]

        self.Event = Event
        self.x = ctypes.CDLL("libX11.so.6")
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.x.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.x.XInternAtom.restype = ctypes.c_ulong
        self.x.XSendEvent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_ulong,
            ctypes.c_int,
            ctypes.c_long,
            ctypes.POINTER(Event),
        ]
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.x.XCloseDisplay.argtypes = [ctypes.c_void_p]
        self.display = self.x.XOpenDisplay(None)
        if not self.display:
            raise RuntimeError("X11 unavailable")
        self.atom = self.x.XInternAtom(self.display, b"_XEMBED", False)

    def notify(self, window, messages):
        for message in messages:
            event = self.Event()
            event.client.type = 33
            event.client.display = self.display
            event.client.window = window
            event.client.message_type = self.atom
            event.client.format = 32
            event.client.data.l[1] = message
            self.x.XSendEvent(self.display, window, False, 0, ctypes.byref(event))
        self.x.XFlush(self.display)

    def focus(self, window):
        self.notify(window, (1, 4))  # WINDOW_ACTIVATE, FOCUS_IN/current.

    def blur(self, window):
        self.notify(window, (5, 2))  # FOCUS_OUT, WINDOW_DEACTIVATE.

    def close(self):
        self.x.XCloseDisplay(self.display)


def report(event, **values):
    print(json.dumps({"event": event, **values}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", required=True, type=int)
    parser.add_argument("--width", type=int, default=440)
    parser.add_argument("--height", type=int, default=650)
    parser.add_argument("--menu-labels", default="{}")
    args = parser.parse_args()
    if args.parent <= 0:
        parser.error("Invalid parent window")
    try:
        menu_labels = json.loads(args.menu_labels)
    except ValueError:
        parser.error("Invalid menu labels")
    if not isinstance(menu_labels, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in menu_labels.items()
    ):
        parser.error("Invalid menu labels")
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("Gdk", "3.0")
        gi.require_version("GdkX11", "3.0")
        gi.require_version("Vte", "2.91")
        from gi.repository import Gdk, GdkX11, GLib, Gtk, Pango, Vte
    except (ImportError, ValueError):
        report("error", reason="dependencies")
        return 2
    if not Gtk.init_check()[0] or not hasattr(Gtk, "Plug"):
        report("error", reason="display")
        return 2

    plug = Gtk.Plug.new(args.parent)
    embed_focus = XEmbedFocus()
    terminal = Vte.Terminal()
    terminal.set_font(Pango.FontDescription("Monospace 10"))
    terminal.set_scrollback_lines(10000)
    terminal.set_audible_bell(False)
    terminal.set_allow_hyperlink(False)
    terminal.set_scroll_on_output(False)
    terminal.set_scroll_on_keystroke(True)
    foreground, background = Gdk.RGBA(), Gdk.RGBA()
    foreground.parse("#e6e8eb")
    background.parse("#101418")
    terminal.set_colors(foreground, background, [])
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
    box.pack_start(terminal, True, True, 0)
    box.pack_end(
        Gtk.Scrollbar(
            orientation=Gtk.Orientation.VERTICAL, adjustment=terminal.get_vadjustment()
        ),
        False,
        False,
        0,
    )
    plug.add(box)
    detached_window = None
    child_pid = None
    context_menu = None

    def quit_loop(*_args):
        if Gtk.main_level() > 0:
            Gtk.main_quit()
        return False

    def resize(width, height):
        if detached_window is not None:
            return
        width = max(40, min(16384, int(width)))
        height = max(40, min(16384, int(height)))
        plug.resize(width, height)
        if plug.get_window() is not None:
            plug.get_window().resize(width, height)

    def focus(*_args):
        if detached_window is not None:
            detached_window.present_with_time(Gtk.get_current_event_time())
            detached_window.get_window().focus(Gdk.CURRENT_TIME)
            terminal.grab_focus()
            return False
        if plug.get_window() is not None:
            embed_focus.focus(plug.get_id())
            plug.get_window().focus(Gdk.CURRENT_TIME)
        terminal.grab_focus()
        return False

    def copy():
        terminal.copy_clipboard_format(Vte.Format.TEXT)

    def paste():
        terminal.paste_clipboard()
        focus()

    def popup_menu(_widget, event=None):
        nonlocal context_menu
        if context_menu is not None:
            context_menu.destroy()
        context_menu = create_terminal_context_menu(terminal, focus, menu_labels)
        if event is not None:
            context_menu.popup_at_pointer(event)
        else:
            context_menu.popup_at_widget(
                terminal, Gdk.Gravity.SOUTH_WEST, Gdk.Gravity.NORTH_WEST, None
            )
        return True

    def button_press(widget, event):
        focus()
        if event.button == 3:
            return popup_menu(widget, event)
        return False

    def move(detach):
        nonlocal detached_window
        if detach and detached_window is None:
            window = Gtk.Window(title="NetMon · Terminal")
            window.set_default_size(850, 560)
            window.connect("delete-event", quit_loop)
            # Python keeps a strong reference to box across remove/add, so the
            # same VTE widget, PTY and scrollback move without a second spawn.
            plug.remove(box)
            try:
                window.add(box)
            except Exception:
                plug.add(box)
                window.destroy()
                raise
            detached_window = window
            plug.hide()
            window.show_all()
        elif not detach and detached_window is not None:
            window = detached_window
            window.remove(box)
            try:
                plug.add(box)
            except Exception:
                window.add(box)
                raise
            detached_window = None
            plug.show_all()
            plug.get_window().show()
            window.destroy()
        focus()
        report(
            "mode",
            mode="external" if detached_window is not None else "docked",
            window=(
                GdkX11.X11Window.get_xid(detached_window.get_window())
                if detached_window
                else plug.get_id()
            ),
            pid=child_pid,
        )

    def key(_widget, event):
        modifiers = event.state & (
            Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK
        )
        both = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK
        name = Gdk.keyval_name(event.keyval).lower()
        if modifiers == both and name in {"a", "c", "v"}:
            if name == "a":
                terminal.select_all()
            else:
                copy() if name == "c" else paste()
            return True
        return False

    def read_control(_source, condition):
        if condition & GLib.IO_HUP:
            quit_loop()
            return False
        line = sys.stdin.readline(1024)
        if not line:
            quit_loop()
            return False
        try:
            message = json.loads(line)
            action = message.get("action")
            if action == "resize":
                resize(message["width"], message["height"])
            elif action == "focus":
                focus()
            elif action == "blur":
                if detached_window is None:
                    embed_focus.blur(plug.get_id())
            elif action in {"detach", "attach"}:
                try:
                    move(action == "detach")
                except Exception:
                    report("move-failed")
            elif action == "copy":
                copy()
            elif action == "paste":
                paste()
            elif action == "interrupt":
                terminal.feed_child(b"\x03")
                focus()
            elif action == "close":
                quit_loop()
                return False
        except (ValueError, TypeError, KeyError, AttributeError):
            pass
        return True

    def spawned(_terminal, pid, error, _data):
        nonlocal child_pid
        if error:
            report("error", reason="spawn")
            quit_loop()
        else:
            child_pid = pid
            report("ready", pid=pid, window=plug.get_id())
            focus()

    def exited(_terminal, status):
        report("exited", status=status)
        quit_loop()

    terminal.connect("button-press-event", button_press)
    terminal.connect("popup-menu", popup_menu)
    terminal.connect("key-press-event", key)
    terminal.connect("child-exited", exited)
    plug.connect("delete-event", quit_loop)
    plug.show_all()
    # GtkSocket normally maps the plug after observing _XEMBED_INFO. The Tk
    # container has no GtkSocket, so explicitly map our own child Gdk window.
    plug.get_window().show()
    resize(args.width, args.height)
    GLib.io_add_watch(sys.stdin, GLib.IO_IN | GLib.IO_HUP, read_control)
    # Start a fresh interactive Bash; no command is inserted or sent from Chad.
    terminal.spawn_async(
        Vte.PtyFlags.DEFAULT,
        os.path.expanduser("~"),
        ["/bin/bash", "--noprofile", "--norc", "-i"],
        ["TERM=xterm-256color", "COLORTERM=truecolor"],
        GLib.SpawnFlags(Vte.SPAWN_NO_SYSTEMD_SCOPE),
        None,
        None,
        -1,
        None,
        spawned,
        None,
    )
    Gtk.main()
    if context_menu is not None:
        context_menu.destroy()
    if detached_window is not None:
        detached_window.destroy()
    plug.destroy()
    embed_focus.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
