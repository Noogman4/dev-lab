"""Tooltip widget helpers for NetMon."""

from __future__ import annotations

import tkinter as tk


class SimpleTooltip:
    def __init__(self, widget, text, enabled_var, delay_ms=500, wraplength=320):
        self.widget = widget
        self.text = text
        self.enabled_var = enabled_var
        self.delay_ms = delay_ms
        self.wraplength = wraplength
        self.tipwindow = None
        self.after_id = None

        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")

    def _on_enter(self, _event=None):
        if not self.enabled_var.get():
            return
        self._schedule()

    def _on_leave(self, _event=None):
        self._unschedule()
        self._hide()

    def _schedule(self):
        self._unschedule()
        self.after_id = self.widget.after(self.delay_ms, self._show)

    def _unschedule(self):
        if self.after_id is not None:
            try:
                self.widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def _show(self):
        if self.tipwindow is not None or not self.enabled_var.get():
            return
        x = self.widget.winfo_rootx() + 14
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw,
            text=self.text,
            justify="left",
            background="#ffffe0",
            relief="solid",
            borderwidth=1,
            wraplength=self.wraplength,
            padx=6,
            pady=4,
        )
        label.pack()
        self.tipwindow = tw

    def _hide(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw is not None:
            try:
                tw.destroy()
            except Exception:
                pass
