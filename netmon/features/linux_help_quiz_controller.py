"""One nonmodal learning window and an application-lifetime Tk timer."""

import time
import tkinter as tk

try:
    from netmon.services.linux_help_quiz_service import QuizState
except ModuleNotFoundError:
    from services.linux_help_quiz_service import QuizState


def _value(app, name):
    # Tk's __getattr__ delegates unknown attributes to Tcl.
    return vars(app).get(name)


def quiz_state(app):
    state = _value(app, "linux_help_quiz_state")
    if state is None:
        state = QuizState()
        app.linux_help_quiz_state = state
    return state


def open_linux_help_quiz(app, *, automatic=False):
    window = _value(app, "linux_help_quiz_window")
    if window is not None and window.winfo_exists():
        if not automatic:
            window.deiconify()
            window.lift()
        return window
    try:
        from netmon.ui.linux_help_quiz import QuizWindow
    except ModuleNotFoundError:
        from ui.linux_help_quiz import QuizWindow
    parent = app.linux_help_tree.winfo_toplevel()
    window = QuizWindow(parent, app, quiz_state(app), automatic=automatic)
    app.linux_help_quiz_window = window
    return window


def _visible_dialog(root):
    if root.grab_current() is not None:
        return True
    pending = list(root.winfo_children())
    while pending:
        widget = pending.pop()
        if isinstance(widget, tk.Toplevel) and widget.winfo_viewable():
            return True
        pending.extend(widget.winfo_children())
    return False


class QuizScheduler:
    def __init__(self, app, root, *, now=None):
        self.app = app
        self.root = root
        self.now = now or time.monotonic
        self.handle = None
        self.due = None
        self.closed = False
        root.bind("<Destroy>", self._destroyed, add="+")
        self.reset()

    def reset(self, *, minutes=None):
        self.cancel()
        state = quiz_state(self.app)
        if not self.closed and not state.error and state.data["settings"]["enabled"]:
            delay = state.data["settings"]["minutes"] if minutes is None else minutes
            self.due = self.now() + delay * 60
            self._arm()
        else:
            self.due = None

    def cancel(self):
        if self.handle is not None:
            self.root.after_cancel(self.handle)
            self.handle = None

    def _arm(self, delay=None):
        if not self.closed and self.due is not None:
            milliseconds = (
                max(100, min(60000, int((self.due - self.now()) * 1000)))
                if delay is None
                else delay
            )
            self.handle = self.root.after(milliseconds, self.tick)

    def tick(self):
        self.handle = None
        state = quiz_state(self.app)
        if self.closed or state.error or not state.data["settings"]["enabled"]:
            self.due = None
            return
        if self.now() < self.due:
            self._arm()
            return
        existing = _value(self.app, "linux_help_quiz_window")
        if (existing is not None and existing.winfo_exists()) or _visible_dialog(
            self.root
        ):
            self._arm(30000)
            return
        try:
            open_linux_help_quiz(self.app, automatic=True)
        except (OSError, ValueError, tk.TclError):
            # A failed reminder must never stop NetMon's event loop.
            self._arm(60000)

    def _destroyed(self, event):
        if event.widget is self.root:
            self.closed = True
            self.cancel()


def initialize_linux_help_quiz(app):
    if _value(app, "linux_help_quiz_scheduler") is None:
        root = app.linux_help_tree.winfo_toplevel()
        app.linux_help_quiz_scheduler = QuizScheduler(app, root)
