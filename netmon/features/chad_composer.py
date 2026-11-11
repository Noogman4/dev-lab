"""Compact Chad input: bounded growth and standard send/newline shortcuts."""

import tkinter as tk


def _grid_padding(widget):
    value = widget.grid_info().get("pady", 0)
    values = (
        value if isinstance(value, (tuple, list)) else widget.tk.splitlist(str(value))
    )
    parts = tuple(widget.winfo_pixels(part) for part in values)
    return sum(parts if len(parts) == 2 else parts * 2)


def _row_height(frame, row):
    return max(
        (
            child.winfo_reqheight() + _grid_padding(child)
            for child in frame.grid_slaves(row=row)
        ),
        default=0,
    )


def _text_padding(widget):
    return 2 * sum(
        widget.winfo_pixels(widget.cget(option))
        for option in ("borderwidth", "highlightthickness", "pady")
    )


def _workspace_rows(widget, output, line_height):
    # Match the Chad builder's output/composer/footer rows. Measure only fixed
    # controls, never the current input/output allocation: that would feed
    # delayed geometry changes back into each other and cause resize loops.
    input_box = widget.master
    composer = input_box.master
    layout = composer.master
    output_frame = output.master.master.master
    fixed = (
        _row_height(composer, 0)
        + _row_height(composer, 2)
        + _row_height(layout, 2)
        + _row_height(output_frame, 0)
        + _grid_padding(input_box)
        + _grid_padding(composer)
        + _grid_padding(output_frame)
        + _text_padding(widget)
        + _text_padding(output)
    )
    return max(3, (layout.winfo_height() - fixed - 6 * line_height) // line_height)


def bind_input(app):
    widget = app.chad_chat_input
    pending = None
    output_binding = None
    output_job = None

    def resize():
        nonlocal pending
        pending = None
        if not widget.winfo_exists() or widget.winfo_width() <= 1:
            return
        # Count rendered lines, so soft wrapping grows the composer as well.
        count = widget.count("1.0", "end-1c", "displaylines")
        rows = max(3, min(12, (count[0] if count else 0) + 1))
        dock = app.__dict__.get("terminal_dock")
        workspace = getattr(dock, "workspace", None)
        output = app.__dict__.get("chad_analysis_text")
        if workspace is not None and workspace.active and output is not None:
            # Leave at least six output lines in a small fixed workspace.
            line_height = max(
                1,
                int(
                    widget.tk.call("font", "metrics", widget.cget("font"), "-linespace")
                ),
            )
            rows = min(rows, _workspace_rows(widget, output, line_height))
        if int(widget.cget("height")) != rows:
            widget.configure(height=rows)

    def schedule_resize(_event=None):
        nonlocal pending
        if pending is None:
            pending = widget.after_idle(resize)

    def watch_output():
        nonlocal output_binding, output_job
        output_job = None
        output = app.__dict__.get("chad_analysis_text")
        if output is not None:
            output_binding = (
                output,
                output.bind("<Configure>", schedule_resize, add="+"),
            )

    def modified(_event=None):
        if widget.edit_modified():
            widget.edit_modified(False)
            schedule_resize()

    def destroy(_event=None):
        nonlocal pending, output_job
        for job in (pending, output_job):
            if job is not None:
                try:
                    widget.after_cancel(job)
                except tk.TclError:
                    pass
        pending = output_job = None
        app.tab_chad_analysis.unbind("<Configure>", layout_binding)
        if output_binding is not None:
            output, binding = output_binding
            try:
                output.unbind("<Configure>", binding)
            except tk.TclError:
                pass

    def send(_event=None):
        app.send_chad_chat_message()
        return "break"

    def keypad_newline(_event=None):
        # Tk does not consistently map keypad Shift+Enter to Text's newline.
        widget.event_generate("<Shift-Return>")
        return "break"

    for key in ("Return", "KP_Enter"):
        widget.bind(f"<{key}>", send)
        # The more-specific binding bypasses send; Tk's Text class inserts the
        # newline normally, including selection replacement and cursor movement.
        widget.bind(f"<Shift-{key}>", lambda _event: None)
    widget.bind("<Shift-KP_Enter>", keypad_newline)
    widget.bind("<<Modified>>", modified, add="+")
    widget.bind("<Configure>", schedule_resize, add="+")
    widget.bind("<<ThemeChanged>>", schedule_resize, add="+")
    widget.bind("<Destroy>", destroy, add="+")
    layout_binding = app.tab_chad_analysis.bind("<Configure>", schedule_resize, add="+")
    output_job = widget.after_idle(watch_output)
    schedule_resize()
