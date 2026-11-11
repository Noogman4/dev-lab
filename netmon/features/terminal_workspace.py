"""Fit the existing terminal/tab workspace to the main canvas viewport."""

import tkinter as tk
from tkinter import ttk


class TerminalWorkspace:
    def __init__(self, app, host):
        self.host = host
        self.canvas = app.__dict__.get("page_canvas")
        self.page = app.__dict__.get("page")
        self.window = app.__dict__.get("page_window")
        self.active = False
        self.binding = None

    def enter(self):
        if (
            self.active
            or self.canvas is None
            or self.page is None
            or self.window is None
        ):
            return
        if self.host.master is not self.page:
            return
        self.canvas.update_idletasks()
        self.host_grid = dict(self.host.grid_info())
        self.page_widgets = [
            (widget, dict(widget.grid_info()))
            for widget in self.page.grid_slaves()
            if widget is not self.host
        ]
        self.original_height = self.canvas.itemcget(self.window, "height")
        self.original_view = self.canvas.yview()[0]
        self.scrollbars = []
        for widget in self.canvas.master.winfo_children():
            if (
                isinstance(widget, ttk.Scrollbar)
                and str(widget.cget("orient")) == "vertical"
            ):
                if widget.winfo_manager() == "pack":
                    self.scrollbars.append((widget, dict(widget.pack_info())))
        self.active = True
        for widget, _grid in self.page_widgets:
            widget.grid_remove()
        for widget, _pack in self.scrollbars:
            widget.pack_forget()
        self.host.grid_remove()
        self.host.place(x=0, y=0, relwidth=1, relheight=1)
        self.host.lift()
        self.binding = self.canvas.bind("<Configure>", self._fit, add="+")
        self._fit()

    def _fit(self, _event=None):
        if not self.active:
            return
        width, height = max(1, self.canvas.winfo_width()), max(
            1, self.canvas.winfo_height()
        )
        self.canvas.itemconfigure(self.window, width=width, height=height)
        self.canvas.configure(scrollregion=(0, 0, width, height))
        self.canvas.yview_moveto(0)

    def exit(self, *, restore=True):
        if not self.active:
            return
        self.active = False
        try:
            if self.binding is not None:
                self.canvas.unbind("<Configure>", self.binding)
                self.binding = None
            if not restore:
                return
            self.host.place_forget()
            self.host.grid(**self.host_grid)
            for widget, grid in self.page_widgets:
                widget.grid(**grid)
            for widget, pack in self.scrollbars:
                widget.pack(**pack)
            self.canvas.itemconfigure(self.window, height=self.original_height)
            self.canvas.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self.canvas.yview_moveto(self.original_view)
        except tk.TclError:
            # The application may already be destroying the canvas and page.
            pass
