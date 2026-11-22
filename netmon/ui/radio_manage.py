"""Station management popup with ordinary actions and an inline random switch."""

import tkinter as tk
from tkinter import ttk

from netmon.ui import radio_random


class StationManagePopup(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.withdraw()
        self.overrideredirect(True)
        self.transient(app.winfo_toplevel())
        self.app = app
        self.actions = ttk.Frame(self, padding=4)
        self.actions.pack(fill="both", expand=True)
        self.actions.columnconfigure(0, weight=1)
        self.rows = []
        self.random_controls = radio_random.build_controls(app, self.actions)
        self.bind("<Escape>", lambda event: self.hide())
        self.bind("<FocusOut>", lambda event: self.after_idle(self._check_focus))
        self.bind("<Up>", lambda event: self._step_focus(-1))
        self.bind("<Down>", lambda event: self._step_focus(1))
        root = app.winfo_toplevel()
        binding = root.bind("<ButtonPress-1>", self._outside_click, add="+")

        def cleanup(event):
            if event.widget is self:
                root.unbind("<ButtonPress-1>", binding)

        self.bind("<Destroy>", cleanup)

    def _outside_click(self, event):
        if self.winfo_ismapped() and event.widget is not self.app.radio_manage_button:
            self.hide()

    def _check_focus(self):
        if self.winfo_exists() and self.winfo_ismapped():
            focus = self.focus_get()
            if focus is None or focus.winfo_toplevel() is not self:
                self.hide()

    def hide(self):
        self.withdraw()
        self.app.radio_manage_button.state(["!pressed"])
        return "break"

    def _step_focus(self, direction):
        controls = [
            widget
            for widget in self.rows
            if isinstance(widget, ttk.Button) and "disabled" not in widget.state()
        ] + [self.app.radio_random_button, self.app.radio_random_settings_button]
        current = self.focus_get()
        index = controls.index(current) if current in controls else -1
        controls[(index + direction) % len(controls)].focus_set()
        return "break"

    def _invoke(self, index):
        self.hide()
        self.app.radio_manage_menu.invoke(index)

    def toggle(self):
        if self.winfo_ismapped():
            return self.hide()
        app = self.app
        app._refresh_radio_manage_menu()
        for widget in self.rows:
            widget.destroy()
        self.rows = []
        theme = app._app_theme or app._theme_with_palette(app._start_theme_name)
        app.style.configure(
            "RadioManageItem.TButton",
            anchor="w",
            padding=(8, 4),
            borderwidth=0,
            relief="flat",
            background=theme["panel_bg"],
            foreground=theme["fg"],
        )
        menu = app.radio_manage_menu
        for index in range(menu.index("end") + 1):
            if menu.type(index) == "separator":
                widget = ttk.Separator(self.actions)
            elif menu.entrycget(index, "state") == "disabled" and index == 0:
                widget = ttk.Label(
                    self.actions, text=menu.entrycget(index, "label"), padding=(8, 4)
                )
            else:
                widget = ttk.Button(
                    self.actions,
                    text=menu.entrycget(index, "label"),
                    style="RadioManageItem.TButton",
                    command=lambda i=index: self._invoke(i),
                )
                if menu.entrycget(index, "state") == "disabled":
                    widget.state(["disabled"])
            widget.grid(row=index, column=0, sticky="ew")
            self.rows.append(widget)
        row = len(self.rows)
        separator = ttk.Separator(self.actions)
        separator.grid(row=row, column=0, sticky="ew", pady=4)
        self.rows.append(separator)
        self.random_controls.grid(row=row + 1, column=0, sticky="ew", padx=8, pady=4)
        radio_random.refresh_controls(app)
        self.configure(background=theme["border"], borderwidth=1)
        app._apply_tk_widget_theme(self, theme)
        self.update_idletasks()
        anchor = app.radio_manage_button
        width, height = self.winfo_reqwidth(), self.winfo_reqheight()
        x = min(
            max(0, anchor.winfo_rootx() + anchor.winfo_width() - width),
            self.winfo_screenwidth() - width,
        )
        y = anchor.winfo_rooty() + anchor.winfo_height()
        if y + height > self.winfo_screenheight():
            y = max(0, anchor.winfo_rooty() - height)
        self.geometry(f"+{x}+{y}")
        self.deiconify()
        self.lift()
        self.focus_force()
        app.radio_manage_button.state(["pressed"])
        self._step_focus(1)
        return "break"
