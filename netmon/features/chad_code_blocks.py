"""Fenced code presentation in Tk Text; original Markdown remains exportable."""

from dataclasses import dataclass
import re
import tkinter as tk
from tkinter import messagebox, ttk

from . import chad_markdown

try:
    from netmon.ui.widgets.tooltip import SimpleTooltip
except ModuleNotFoundError:
    from ui.widgets.tooltip import SimpleTooltip


def _copy_icons(widget):
    """Draw theme-colored overlapping sheets/check without a font dependency."""
    size = max(20, round(float(widget.tk.call("tk", "scaling")) * 12))
    color = ttk.Style(widget).lookup("TButton", "foreground") or "#17212b"
    copy = tk.PhotoImage(master=widget, width=size, height=size)
    check = tk.PhotoImage(master=widget, width=size, height=size)
    sheets = (
        (2, 2, 13, 4),
        (2, 2, 4, 13),
        (2, 11, 6, 13),
        (11, 2, 13, 6),
        (6, 6, 18, 8),
        (6, 6, 8, 18),
        (6, 16, 18, 18),
        (16, 6, 18, 18),
    )
    tick = [(4, 10), (5, 11), (6, 12), (7, 13)] + [(x, 20 - x) for x in range(8, 17)]
    for icon, rectangles in (
        (copy, sheets),
        (check, [(x, y, x + 2, y + 2) for x, y in tick]),
    ):
        for rect in rectangles:
            icon.put(color, to=tuple(round(value * size / 20) for value in rect))
    return copy, check


@dataclass(frozen=True)
class CodeBlock:
    first_line: int
    last_line: int
    language: str
    code: str
    closed: bool


def find_code_blocks(text):
    lines = text.split("\n")
    blocks = []
    index = 0
    while index < len(lines):
        opening = re.fullmatch(r" {0,3}(`{3,}|~{3,})([^\r\n]*)\r?", lines[index])
        if opening is None or (opening[1][0] == "`" and "`" in opening[2]):
            index += 1
            continue
        fence, info = opening.groups()
        close = re.compile(
            r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*\r?"
        )
        end = index + 1
        while end < len(lines) and not close.fullmatch(lines[end]):
            end += 1
        closed = end < len(lines)
        blocks.append(
            CodeBlock(
                index,
                end if closed else len(lines) - 1,
                info.strip().split()[0][:40] if info.strip() else "",
                "\n".join(lines[index + 1 : end]),
                closed,
            )
        )
        index = end + 1
    return blocks


def clear(app):
    for item in app.__dict__.get("chad_code_blocks", []):
        try:
            item["frame"].destroy()
        except tk.TclError:
            pass
    app.chad_code_blocks = []


def resize_headers(app, widget):
    width = max(120, widget.winfo_width() - 32)
    for item in app.__dict__.get("chad_code_blocks", []):
        frame = item["frame"]
        if frame.winfo_exists() and frame.winfo_reqwidth() != width:
            frame.configure(width=width)


def insert_body(app, widget, body, body_tag, *, markdown=False):
    # Keep existing non-GUI consumers/test doubles on the plain text path.
    if not isinstance(widget, tk.Text):
        widget.insert("end", body, body_tag)
        return
    start = widget.index("end-1c")
    widget.insert("end", body, body_tag)
    blocks = find_code_blocks(body)
    if markdown:
        chad_markdown.apply(
            widget, start, body, blocks, app.__dict__.get("chad_markdown_budget")
        )
    if not blocks:
        return
    widget.tag_configure(
        "chad_code",
        background="#e5e7eb",
        foreground="#17212b",
        font="TkFixedFont",
        lmargin1=12,
        lmargin2=12,
        rmargin=12,
        spacing1=2,
        spacing3=2,
        wrap="char",
    )
    widget.tag_configure("chad_code_fence", elide=True)
    widget.tag_raise("chad_code")
    widget.tag_raise("chad_code_fence")
    widget.tag_raise("sel")
    if not widget.__dict__.get("_chad_code_resize_bound"):
        widget.bind("<Configure>", lambda _event: resize_headers(app, widget), add="+")
        widget._chad_code_resize_bound = True
    items = app.__dict__.setdefault("chad_code_blocks", [])
    created = []
    # Work backwards: inserted windows must not shift later raw line positions.
    for block in reversed(blocks):
        opening = widget.index(f"{start} + {block.first_line} lines linestart")
        closing = widget.index(f"{start} + {block.last_line} lines linestart")
        end = widget.index(f"{closing} lineend")
        widget.tag_add("chad_code", opening, end if not block.closed else f"{end} + 1c")
        widget.tag_add("chad_code_fence", opening, f"{opening} lineend")
        if block.closed:
            widget.tag_add("chad_code_fence", closing, end)
        frame = tk.Frame(
            widget,
            background="#e5e7eb",
            height=30,
            width=max(120, widget.winfo_width() - 32),
        )
        frame.pack_propagate(False)
        language = block.language or app.tr("chad_code_label", "Code")
        if not block.closed:
            language += " · " + app.tr("chad_code_open", "offener Codeblock")
        label = tk.Label(
            frame, text=language, background="#e5e7eb", foreground="#17212b", anchor="w"
        )
        copy_icon, copied_icon = _copy_icons(frame)
        button = ttk.Button(
            frame,
            text=app.tr("chad_code_copy", "Kopieren"),
            image=copy_icon,
            compound="image",
            padding=(4, 3),
            takefocus=True,
        )
        # Keep localized text as widget metadata, but display only the icon.
        button._chad_copy_icons = (copy_icon, copied_icon)
        enabled = app.__dict__.get("tooltips_enabled")
        if enabled is None:
            enabled = tk.BooleanVar(master=button, value=True)
        tooltip = SimpleTooltip(button, app.tr("chad_code_copy", "Kopieren"), enabled)
        button.bind("<FocusIn>", tooltip._on_enter, add="+")
        button.bind("<FocusOut>", tooltip._on_leave, add="+")
        button.bind("<Unmap>", tooltip._on_leave, add="+")
        button.bind("<Destroy>", tooltip._on_leave, add="+")

        def copy_code(
            value=block.code, button=button, icon=copied_icon, tooltip=tooltip
        ):
            try:
                widget.clipboard_clear()
                widget.clipboard_append(value)
            except tk.TclError:
                messagebox.showerror(
                    app.tr("chad_code_copy_failed", "Kopieren fehlgeschlagen"),
                    app.tr(
                        "chad_code_clipboard_unavailable",
                        "Zwischenablage nicht verfügbar.",
                    ),
                    parent=widget.winfo_toplevel(),
                )
                return
            tooltip._on_leave()
            tooltip.text = app.tr("chad_code_copied", "Kopiert")
            button.configure(image=icon, text=tooltip.text)

        button.configure(command=copy_code)
        button.pack(side="right", padx=8, pady=2)
        label.pack(side="left", fill="x", expand=True, padx=8, anchor="w")
        frame.configure(
            height=max(30, button.winfo_reqheight() + 4, label.winfo_reqheight() + 4)
        )
        widget.window_create(opening, window=frame, align="center")
        created.append(
            {
                "frame": frame,
                "button": button,
                "tooltip": tooltip,
                "code": block.code,
                "language": language,
                "closed": block.closed,
            }
        )
    items.extend(reversed(created))
    resize_headers(app, widget)
