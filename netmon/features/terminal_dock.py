"""Reversible terminal workspace: original action columns or terminal + tabs."""

import json
import os
from pathlib import Path
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk

try:
    from netmon.features.terminal_workspace import TerminalWorkspace
    from netmon.ui.terminal_helper import TERMINAL_MENU_LABELS
except ModuleNotFoundError:
    from features.terminal_workspace import TerminalWorkspace
    from ui.terminal_helper import TERMINAL_MENU_LABELS


def _tr(app, key, fallback):
    return app.tr(key, fallback)


def _reap(process):
    """Only reap/terminate this owned helper, never signal arbitrary user PIDs."""
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    finally:
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()


class TerminalDock:
    def __init__(self, app):
        self.app = app
        self.main = app.main_work_area
        self.sidebar = app.right_sidebar
        self.host = self.main.master
        self.workspace = TerminalWorkspace(app, self.host)
        self.process = None
        self.job = None
        self.resize_job = None
        self.reveal_job = None
        self.active = True
        self.ready = False
        self.detached = False
        self.transition = None
        self.layout_active = False
        self.buffer = b""
        self.started = time.monotonic()
        self.main_grid = dict(self.main.grid_info())
        self.sidebar_grid = dict(self.sidebar.grid_info())
        self.columns = [dict(self.host.columnconfigure(i)) for i in range(3)]
        self.main_column = dict(self.main.columnconfigure(0))
        self.toplevel = self.host.winfo_toplevel()
        self.window_minimum = self.toplevel.minsize()
        combo = app.__dict__.get("chad_output_filter_combo")
        self.output_controls = combo.master if combo is not None else None
        self.output_controls_grid = (
            dict(self.output_controls.grid_info())
            if self.output_controls is not None
            else None
        )
        self.initial_width = max(320, self.sidebar.winfo_width())
        self.initialized_sash = False

        self.pane = tk.PanedWindow(
            self.host,
            orient="horizontal",
            sashwidth=8,
            sashrelief="raised",
            showhandle=True,
            handlesize=16,
            opaqueresize=True,
            borderwidth=0,
        )
        self.panel = ttk.Frame(self.pane, padding=(0, 0, 4, 0))
        self.panel.columnconfigure(0, weight=1)
        # Keep the terminal near Chad's bottom composer instead of stretching
        # a mostly empty shell from the top of the workspace to the bottom.
        self.panel.rowconfigure(0, weight=1)
        self.terminal_card = ttk.Frame(self.panel, height=560)
        self.terminal_card.grid(row=1, column=0, sticky="ew")
        self.terminal_card.grid_propagate(False)
        self.terminal_card.columnconfigure(0, weight=1)
        self.terminal_card.rowconfigure(2, weight=1)
        self.panel.bind("<Configure>", self._fit_terminal)
        toolbar = ttk.Frame(self.terminal_card)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self.status = tk.StringVar(
            master=self.panel,
            value=_tr(app, "terminal_dock_starting", "Terminal startet …"),
        )
        status_line = ttk.Frame(self.terminal_card)
        status_line.grid(row=1, column=0, sticky="ew")
        ttk.Label(status_line, textvariable=self.status).pack(side="left")
        self.buttons = {}
        for action, key, fallback in (
            ("copy", "terminal_dock_copy", "Kopieren"),
            ("paste", "terminal_dock_paste", "Einfügen"),
            ("interrupt", "terminal_dock_interrupt", "Strg+C"),
            ("detach", "terminal_dock_detach", "Abdocken"),
        ):
            button = ttk.Button(
                status_line if action == "detach" else toolbar,
                text=_tr(app, key, fallback),
                command=lambda action=action: (
                    self.detach() if action == "detach" else self.send(action)
                ),
            )
            button.pack(side="right" if action == "detach" else "left", padx=(0, 3))
            button.configure(state="disabled")
            self.buttons[action] = button
        ttk.Button(
            toolbar,
            text=_tr(app, "terminal_dock_close", "Schließen"),
            command=self.close,
        ).pack(side="right")
        self.toolbar = toolbar
        self.min_terminal = 300
        self.min_main = 600
        self.surface = tk.Frame(
            self.terminal_card, container=True, background="#101418", takefocus=True
        )
        self.surface.grid(row=2, column=0, sticky="nsew")
        self.surface.bind("<Configure>", self._schedule_resize)
        self.surface.bind("<FocusIn>", lambda _event: self.send("focus"))
        self.pane.bind("<Configure>", self._clamp)
        self.pane.bind("<ButtonRelease-1>", self._clamp, add="+")
        self.destroy_binding = self.host.bind("<Destroy>", self._destroyed, add="+")
        self.focus_binding = self.toplevel.bind(
            "<ButtonPress-1>", self._focus_tk, add="+"
        )

    def _fit_terminal(self, event):
        if self.active:
            height = (
                max(1, event.height)
                if self.workspace.active
                else max(1, min(560, event.height * 4 // 5))
            )
            if self.terminal_card.cget("height") != height:
                self.terminal_card.configure(height=height)

    def _focus_tk(self, event):
        if self.active and not self.detached and event.widget is not self.surface:
            self.send("blur")
            event.widget.focus_force()

    def _reveal_terminal(self):
        self.reveal_job = None
        if self.active and self.ready and not self.detached:
            self.app.scroll_main_page_to_widget(self.terminal_card)
            self.send("focus")

    def _show_layout(self):
        self.layout_active = True
        self.workspace.enter()
        if self.focus_binding is None:
            self.focus_binding = self.toplevel.bind(
                "<ButtonPress-1>", self._focus_tk, add="+"
            )
        self.main.grid_remove()
        self.sidebar.grid_remove()
        for i in range(3):
            self.host.columnconfigure(
                i, minsize=0, weight=1 if i == 0 else 0, uniform=""
            )
        self.main.columnconfigure(0, minsize=0)
        self.pane.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.pane.add(self.panel, minsize=280, stretch="never")
        self.pane.add(self.main, minsize=600, stretch="always")
        # main is an existing sibling of the paned window; keep its window
        # above the temporary pane without destroying/reparenting the tabs.
        self.main.lift(self.pane)
        if self.output_controls is not None:
            self.output_controls.grid_configure(
                row=1, column=0, columnspan=3, sticky="e"
            )
        self.pane.update_idletasks()
        self.min_terminal = max(300, self.toolbar.winfo_reqwidth() + 12)
        self.min_main = max(
            600,
            (
                (self.output_controls.winfo_reqwidth() + 40)
                if self.output_controls is not None
                else 600
            ),
        )
        minimum = (
            self.min_terminal
            + self.min_main
            + 8
            + self.toplevel.winfo_width()
            - self.host.winfo_width()
        )
        if minimum > self.toplevel.winfo_screenwidth():
            if self.detached:
                self._restore_layout(destroy=False)
                messagebox.showerror(
                    _tr(self.app, "btn_terminal", "Terminal"),
                    _tr(
                        self.app,
                        "terminal_dock_narrow",
                        "Für das eingehängte Terminal ist der Bildschirm zu schmal. Bitte ein externes Terminal verwenden.",
                    ),
                    parent=self.toplevel,
                )
            else:
                self._failed(
                    "terminal_dock_narrow",
                    "Für das eingehängte Terminal ist der Bildschirm zu schmal. Bitte ein externes Terminal verwenden.",
                )
            return False
        self.toplevel.minsize(
            max(self.window_minimum[0], minimum), self.window_minimum[1]
        )
        self._clamp()
        return True

    def start(self):
        try:
            if not self._show_layout():
                return
            helper = Path(__file__).resolve().parents[1] / "ui/terminal_helper.py"
            env = {**os.environ, "GDK_BACKEND": "x11", "PYTHONDONTWRITEBYTECODE": "1"}
            self.process = subprocess.Popen(
                [
                    "/usr/bin/python3",
                    "-I",
                    "-B",
                    str(helper),
                    "--parent",
                    str(self.surface.winfo_id()),
                    "--width",
                    str(self.surface.winfo_width()),
                    "--height",
                    str(self.surface.winfo_height()),
                    "--menu-labels",
                    json.dumps(
                        {
                            key: _tr(self.app, f"terminal_menu_{key}", fallback)
                            for key, fallback in TERMINAL_MENU_LABELS.items()
                        }
                    ),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                env=env,
                start_new_session=True,
            )
            os.set_blocking(self.process.stdin.fileno(), False)
            os.set_blocking(self.process.stdout.fileno(), False)
            os.set_blocking(self.process.stderr.fileno(), False)
            self.job = self.host.after(30, self._poll)
            self.app.nb.select(self.app.tab_chad_analysis)
        except Exception:
            self._failed()

    def _clamp(self, _event=None):
        if not self.active or len(self.pane.panes()) < 2:
            return
        width = max(1, self.pane.winfo_width())
        low = self.min_terminal
        right_min = self.min_main
        high = max(low, width - right_min - 8)
        self.pane.paneconfigure(self.panel, minsize=low)
        self.pane.paneconfigure(self.main, minsize=right_min)
        current = self.pane.sash_coord(0)[0]
        target = max(
            low, min(high, current if self.initialized_sash else self.initial_width)
        )
        self.initialized_sash = True
        if current != target:
            self.pane.sash_place(0, target, 0)

    def _schedule_resize(self, _event=None):
        if self.active and self.resize_job is None:
            self.resize_job = self.host.after_idle(self._resize)

    def _resize(self):
        self.resize_job = None
        if self.active and self.ready and not self.detached:
            self.send(
                "resize",
                width=self.surface.winfo_width(),
                height=self.surface.winfo_height(),
            )

    def detach(self):
        if self.active and self.ready and not self.detached and self.transition is None:
            self.transition = ("external", time.monotonic())
            for button in self.buttons.values():
                button.configure(state="disabled")
            self.send("detach")

    def attach(self):
        if self.active and self.ready and self.detached and self.transition is None:
            if not self._show_layout():
                return
            self.transition = ("docked", time.monotonic())
            self.send("attach")

    def _mode_changed(self, message):
        mode = message.get("mode")
        if (
            self.transition is None
            or mode != self.transition[0]
            or message.get("pid") != self.shell_pid
            or type(message.get("window")) is not int
            or message["window"] <= 0
        ):
            self._failed()
            return
        self.transition = None
        self.detached = mode == "external"
        self.window_id = message["window"]
        if self.detached:
            self._restore_layout(destroy=False)
        else:
            self._resize()
            for button in self.buttons.values():
                button.configure(state="normal")
            self.reveal_job = self.host.after_idle(self._reveal_terminal)
        _remember_mode(self.app, mode)

    def send(self, action, **values):
        process = self.process
        if not self.active or process is None or process.poll() is not None:
            return
        try:
            process.stdin.write(
                (json.dumps({"action": action, **values}) + "\n").encode()
            )
            process.stdin.flush()
        except BlockingIOError:
            # Superseded resize/focus controls must never block the Tk loop.
            return
        except (OSError, ValueError):
            self.close()

    def _poll(self):
        self.job = None
        if not self.active:
            return
        process = self.process
        try:
            chunk = os.read(process.stdout.fileno(), 8192)
        except BlockingIOError:
            chunk = b""
        self.buffer += chunk
        if len(self.buffer) > 16384:
            self._failed()
            return
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            try:
                message = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(message, dict):
                self._failed()
                return
            if message.get("event") == "error":
                self._failed()
                return
            if message.get("event") == "exited":
                self.close()
                return
            if message.get("event") == "mode":
                self._mode_changed(message)
                if not self.active:
                    return
            if message.get("event") == "move-failed":
                if self.transition is not None and self.transition[0] == "docked":
                    self._restore_layout(destroy=False)
                self.transition = None
                for button in self.buttons.values():
                    button.configure(state="normal")
                messagebox.showerror(
                    _tr(self.app, "btn_terminal", "Terminal"),
                    _tr(
                        self.app,
                        "terminal_dock_move_failed",
                        "Terminal konnte nicht verschoben werden. Die Sitzung bleibt geöffnet.",
                    ),
                    parent=self.toplevel,
                )
            if message.get("event") == "ready":
                if not all(
                    type(message.get(name)) is int and message[name] > 0
                    for name in ("window", "pid")
                ):
                    self._failed()
                    return
                first_ready = not self.ready
                self.ready = True
                self.window_id = message["window"]
                self.shell_pid = message["pid"]
                self.status.set(
                    _tr(self.app, "terminal_dock_ready", "Bash · Strg+Umschalt+C / V")
                )
                for button in self.buttons.values():
                    button.configure(state="normal")
                self._resize()
                if first_ready:
                    _remember_mode(self.app, "docked")
                    self.reveal_job = self.host.after_idle(self._reveal_terminal)
        # Drain GTK diagnostics without logging shell data or blocking the GUI.
        try:
            os.read(process.stderr.fileno(), 8192)
        except BlockingIOError:
            pass
        if (
            process.poll() is not None
            or (not self.ready and time.monotonic() - self.started > 8)
            or (
                self.transition is not None
                and time.monotonic() - self.transition[1] > 8
            )
        ):
            self._failed()
            return
        self.job = self.host.after(50, self._poll)

    def _failed(
        self,
        key="terminal_dock_unavailable",
        fallback="Terminal konnte nicht eingebettet werden. Benötigt werden GTK3/VTE und eine X11-/XWayland-Anzeige. Rechtsklick auf Terminal öffnet weiterhin ein externes Terminal.",
    ):
        self.close()
        if not self.app.__dict__.get("_netmon_closing"):
            messagebox.showerror(
                _tr(self.app, "btn_terminal", "Terminal"),
                _tr(self.app, key, fallback),
                parent=self.host.winfo_toplevel(),
            )

    def _destroyed(self, event):
        if event.widget is self.host:
            self.close(restore=False)

    def _restore_layout(self, *, destroy):
        for job in (self.resize_job, self.reveal_job):
            if job is not None:
                self.host.after_cancel(job)
        self.resize_job = self.reveal_job = None
        if self.focus_binding is not None:
            self.toplevel.unbind("<ButtonPress-1>", self.focus_binding)
            self.focus_binding = None
        if self.layout_active:
            self.layout_active = False
            self.pane.forget(self.main)
            self.pane.grid_remove()
            for i, config in enumerate(self.columns):
                self.host.columnconfigure(i, **config)
            self.main.columnconfigure(0, **self.main_column)
            self.toplevel.minsize(*self.window_minimum)
            if self.output_controls is not None:
                self.output_controls.grid(**self.output_controls_grid)
            self.main.grid(**self.main_grid)
            self.sidebar.grid(**self.sidebar_grid)
            self.workspace.exit()
        if destroy:
            self.pane.destroy()

    def close(self, restore=True):
        if not self.active:
            return
        self.active = False
        if self.process is not None and self.process.poll() is None:
            try:
                self.process.stdin.write(b'{"action":"close"}\n')
                self.process.stdin.flush()
            except (OSError, ValueError):
                pass
        for job in (self.job, self.resize_job, self.reveal_job):
            if job is not None:
                try:
                    self.host.after_cancel(job)
                except tk.TclError:
                    pass
        self.job = self.resize_job = self.reveal_job = None
        try:
            self.host.unbind("<Destroy>", self.destroy_binding)
            if restore:
                self._restore_layout(destroy=True)
            else:
                self.workspace.exit(restore=False)
                if self.focus_binding is not None:
                    self.toplevel.unbind("<ButtonPress-1>", self.focus_binding)
                self.pane.destroy()
        except tk.TclError:
            pass
        if self.app.__dict__.get("terminal_dock") is self:
            self.app.terminal_dock = None
        if self.process is not None:
            try:
                self.process.stdin.close()
            except OSError:
                pass
            threading.Thread(target=_reap, args=(self.process,), daemon=True).start()


def toggle(app):
    current = app.__dict__.get("terminal_dock")
    if current is not None and current.active:
        current.close()
        return
    if app.tk.call("tk", "windowingsystem") != "x11":
        messagebox.showerror(
            _tr(app, "btn_terminal", "Terminal"),
            _tr(
                app,
                "terminal_dock_display",
                "Einbetten ist nur unter X11/XWayland verfügbar. Rechtsklick auf Terminal öffnet ein externes Terminal.",
            ),
            parent=app,
        )
        return
    dock = app.terminal_dock = TerminalDock(app)
    dock.start()


def _remember_mode(app, mode):
    settings = app.__dict__.get("settings")
    if isinstance(settings, dict) and settings.get("terminal_start_mode") != mode:
        settings["terminal_start_mode"] = mode
        app.save_settings(log_success=False)


def open_terminal(app, mode=None):
    current = app.__dict__.get("terminal_dock")
    if current is not None and current.active:
        if mode == "external" and not current.detached:
            current.detach()
        elif mode == "docked" and current.detached:
            current.attach()
        elif current.detached:
            current.send("focus")
        else:
            current._reveal_terminal()
        return
    settings = app.__dict__.get("settings") or {}
    mode = mode if mode is not None else settings.get("terminal_start_mode", "docked")
    if mode == "external":
        if app.open_external_terminal():
            _remember_mode(app, "external")
    else:
        toggle(app)


def _choice_menu(app, owner):
    menu = tk.Menu(owner, tearoff=False)
    for mode, key, fallback in (
        ("docked", "terminal_dock_open", "Analysemodus"),
        ("external", "terminal_dock_open_external", "Als eigenes Fenster öffnen"),
    ):
        menu.add_command(
            label=_tr(app, key, fallback),
            command=lambda mode=mode: open_terminal(app, mode),
        )
    return menu


def build_launcher(app, parent):
    frame = ttk.Frame(parent)
    frame.pack(side="right", padx=(0, 8))
    button = ttk.Button(
        frame,
        text=_tr(app, "btn_terminal", "Terminal"),
        command=lambda: open_terminal(app),
    )
    button.pack(side="left")
    button.bind("<Button-3>", app.show_terminal_menu)
    choice = ttk.Menubutton(frame, text="▾", width=2, direction="below")
    choice.configure(menu=_choice_menu(app, choice))
    choice.pack(side="left")
    app.add_tooltip(
        button,
        _tr(
            app,
            "tooltip_terminal",
            "Terminal öffnen. Über ▾ Analysemodus oder eigenes Fenster wählen. Die letzte Startart wird gespeichert.",
        ),
    )
    app.add_tooltip(
        choice, _tr(app, "terminal_dock_choice", "Terminal-Startart auswählen")
    )
    return frame


def external_menu(app, event):
    previous = app.__dict__.get("_terminal_external_menu")
    if previous is not None:
        previous.destroy()
    menu = _choice_menu(app, app)
    app._terminal_external_menu = menu
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        menu.grab_release()
