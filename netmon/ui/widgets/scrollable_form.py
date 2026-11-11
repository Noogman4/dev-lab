"""A bounded form viewport with local wheel and keyboard-focus handling."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ScrollableForm:
    """Keep controls in a tab viewport without changing global mouse bindings."""

    def __init__(self, parent, *, padding=12):
        self.wrap = ttk.Frame(parent)
        self.wrap.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(self.wrap, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(
            self.wrap, orient="vertical", command=self.canvas.yview
        )
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.content = ttk.Frame(self.canvas, padding=padding)
        self.window = self.canvas.create_window(
            (0, 0), window=self.content, anchor="nw"
        )
        self.canvas.bind("<Configure>", self._fit)
        self.content.bind("<Configure>", self._fit)
        self.tag = f"NetMonFormScroll{self.canvas}"
        self.sequences = ("<MouseWheel>", "<Button-4>", "<Button-5>", "<FocusIn>")
        for sequence in self.sequences:
            callback = self._reveal_focus if sequence == "<FocusIn>" else self._wheel
            self.canvas.bind_class(self.tag, sequence, callback)
        self.canvas.bind("<Destroy>", self._cleanup)

    def _fit(self, _event=None):
        width = max(1, self.canvas.winfo_width())
        height = max(self.canvas.winfo_height(), self.content.winfo_reqheight())
        self.canvas.itemconfigure(self.window, width=width, height=height)
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def bind_controls(self):
        """Call after building the form so all existing controls share its tag."""

        def attach(widget):
            tags = widget.bindtags()
            if self.tag not in tags:
                widget.bindtags((tags[0], self.tag, *tags[1:]))
            for child in widget.winfo_children():
                attach(child)

        attach(self.canvas)
        attach(self.scrollbar)

    def _wheel(self, event):
        number = getattr(event, "num", None)
        delta = int(getattr(event, "delta", 0) or 0)
        if number in (4, 5):
            step = -1 if number == 4 else 1
        elif delta:
            step = max(1, abs(delta) // 120) * (-1 if delta > 0 else 1)
        else:
            return "break"
        # Keep long outputs independently scrollable; at their edge, scroll the form.
        widget = event.widget
        if isinstance(widget, (tk.Text, tk.Listbox, ttk.Treeview)):
            first, last = widget.yview()
            if (step < 0 and first > 0) or (step > 0 and last < 1):
                widget.yview_scroll(step, "units")
                return "break"
        self.canvas.yview_scroll(step, "units")
        return "break"

    def _reveal_focus(self, event):
        widget = event.widget
        parent = widget
        while parent is not None and parent is not self.content:
            parent = parent.master
        if parent is None or widget.winfo_height() > self.canvas.winfo_height():
            return
        top = widget.winfo_rooty() - self.content.winfo_rooty()
        bottom = top + widget.winfo_height()
        visible_top = self.canvas.canvasy(0)
        target = None
        if top < visible_top:
            target = top
        elif bottom > visible_top + self.canvas.winfo_height():
            target = bottom - self.canvas.winfo_height()
        if target is not None:
            self.canvas.yview_moveto(
                max(0, target) / max(1, self.content.winfo_height())
            )

    def _cleanup(self, event):
        if event.widget is self.canvas:
            for sequence in self.sequences:
                self.canvas.unbind_class(self.tag, sequence)
