"""Light indicator helpers for NetMon."""

from __future__ import annotations


def make_light(parent, label, *, tk_module, ttk_module):
    frame = ttk_module.Frame(parent)
    frame.pack(fill="x", pady=4)
    canvas = tk_module.Canvas(frame, width=18, height=18, highlightthickness=0)
    canvas.pack(side="left")
    dot = canvas.create_oval(2, 2, 16, 16, fill="gray")
    text_label = ttk_module.Label(frame, text=label)
    text_label.pack(side="left", padx=8)
    return canvas, dot, text_label


def set_light(light, color):
    light[0].itemconfig(light[1], fill=color)
