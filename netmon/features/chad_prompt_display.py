"""Fold completed analysis prompts without changing text, exports or selection."""

import tkinter as tk
from tkinter import ttk

from . import chad_code_blocks


def clear(app):
    for item in app.__dict__.get("chad_prompt_views", []):
        try:
            item["button"].destroy()
        except tk.TclError:
            pass
    app.chad_prompt_views = []


def insert_body(app, widget, entry, body, body_tag):
    if entry.get("prompt_foldable") is not True or not isinstance(widget, tk.Text):
        chad_code_blocks.insert_body(
            app,
            widget,
            body,
            body_tag,
            markdown=entry.get("kind") == "answer"
            and body != app.__dict__.get("chad_analysis_current_prompt"),
        )
        return

    views = app.__dict__.setdefault("chad_prompt_views", [])
    tag = f"chad_prompt_body_{len(views)}"
    button = ttk.Button(widget, takefocus=True)
    # Place the control on the existing header line, without adding raw text.
    widget.window_create("end-2c", window=button, padx=8, pady=2, align="center")
    start = widget.index("end-1c")
    chad_code_blocks.insert_body(app, widget, body, body_tag)
    widget.tag_add(tag, start, widget.index("end-1c"))
    widget.tag_raise(tag)

    def update():
        collapsed = entry.get("prompt_collapsed") is True
        # Empty means no override: expanded prompts retain elided code fences.
        widget.tag_configure(tag, elide=True if collapsed else "")
        button.configure(
            text=app.tr(
                "chad_prompt_show" if collapsed else "chad_prompt_hide",
                "Verwendeten Prompt anzeigen" if collapsed else "Prompt einklappen",
            )
        )

    def toggle():
        entry["prompt_collapsed"] = entry.get("prompt_collapsed") is not True
        update()
        try:
            app.update_chad_output_layout()
        except Exception:
            pass

    button.configure(command=toggle)
    views.append({"entry": entry, "button": button, "tag": tag})
    update()
