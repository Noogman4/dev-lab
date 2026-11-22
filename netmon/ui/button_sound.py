"""Optional sound feedback for NetMon controls."""

from pathlib import Path
import subprocess
import threading

_PLAYER = Path("/usr/bin/paplay")
_SOUND = Path("/usr/share/sounds/freedesktop/stereo/audio-volume-change.oga")
_STATUS_CLICK_TAG = "NetMonStatusClick"


def bind_status_click_sound(widget):
    tags = widget.bindtags()
    if _STATUS_CLICK_TAG not in tags:
        # Context menu handlers can stop dispatch with "break".
        widget.bindtags((_STATUS_CLICK_TAG, *tags))


def bind_status_menu_click_sound(menu, source, play_command):
    if hasattr(source, "bindtags") and _STATUS_CLICK_TAG in source.bindtags():
        bind_menu_click_sound(menu, play_command)


def bind_menu_click_sound(menu, play_command):
    if not play_command:
        return

    last = menu.index("end")
    if last is None:
        return

    # Let Tk decide when to invoke the entry, including its disabled state.
    prefix = f"{play_command}\n"
    for index in range(last + 1):
        if menu.type(index) in ("command", "checkbutton", "radiobutton"):
            action = str(menu.entrycget(index, "command"))
            if action and not action.startswith(prefix):
                menu.entryconfigure(index, command=prefix + action)


def install_button_sound(root, *, enabled):
    if not (_PLAYER.is_file() and _SOUND.is_file()):
        return

    playing = threading.Lock()

    def play_sound():
        try:
            subprocess.run(
                [str(_PLAYER), str(_SOUND)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=1,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass
        finally:
            playing.release()

    def play():
        if enabled() and playing.acquire(blocking=False):
            try:
                threading.Thread(target=play_sound, daemon=True).start()
            except RuntimeError:
                playing.release()

    play_command = root.register(play)
    for sequence in ("<Button-1>", "<Button-3>"):
        root.tk.call("bind", _STATUS_CLICK_TAG, sequence, play_command)

    button_action = f'if {{[%W cget -command] ne ""}} {{{play_command}}}'
    for widget_class, sound_action in (
        ("TButton", button_action),
        ("TCheckbutton", play_command),
    ):
        for sequence, states in (
            ("<ButtonRelease-1>", "pressed !disabled"),
            ("<space>", "!disabled"),
            ("<<Invoke>>", "!disabled"),
        ):
            # Check the same state as Tk before it clears the pressed state.
            native_binding = root.bind_class(widget_class, sequence)
            sound_binding = f"%W instate {{{states}}} {{{sound_action}}}"
            root.tk.call(
                "bind", widget_class, sequence, f"{sound_binding}\n{native_binding}"
            )

    # Use the same tab hit test as Tk before it changes the selection.
    native_binding = root.bind_class("TNotebook", "<Button-1>")
    tab_index = "[%W index @%x,%y]"
    sound_binding = (
        f'if {{{tab_index} ne "" && [%W tab {tab_index} -state] eq "normal"}} '
        f"{{{play_command}}}"
    )
    root.tk.call(
        "bind", "TNotebook", "<Button-1>", f"{sound_binding}\n{native_binding}"
    )

    # Tk maps this window only when it opens the combobox list.
    root.tk.call("bind", "ComboboxPopdown", "<Map>", f"+{play_command}")

    # The listbox's nearest row can be outside the clicked area on an empty
    # list or when releasing the mouse beyond the entries.
    native_binding = root.bind_class("ComboboxListbox", "<ButtonRelease-1>")
    sound_binding = (
        'if {[%W curselection] ne "" && %x >= 0 && %x < [winfo width %W]} {\n'
        "    set netmon_row [%W bbox [%W nearest %y]]\n"
        '    if {$netmon_row ne "" && %y >= [lindex $netmon_row 1] && '
        f"%y < [lindex $netmon_row 1] + [lindex $netmon_row 3]}} {{{play_command}}}\n"
        "}"
    )
    root.tk.call(
        "bind",
        "ComboboxListbox",
        "<ButtonRelease-1>",
        f"{sound_binding}\n{native_binding}",
    )
    return play_command
