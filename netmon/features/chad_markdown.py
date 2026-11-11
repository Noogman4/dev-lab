"""Conservative Markdown typography in Tk Text, preserving original source."""

from bisect import bisect_right
import re
from tkinter import font as tkfont


def _tick_end(text, start, end):
    run = re.match(r"`+", text[start:end])[0]
    close = re.compile(r"(?<!`)" + re.escape(run) + r"(?!`)").search(
        text, start + len(run), end
    )
    return (start + len(run), close.start(), close.end()) if close else None


def _close_marker(text, marker, start, end):
    i = start
    while i < end:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            code = _tick_end(text, i, end)
            if code:
                i = code[2]
                continue
        if text[i] == marker[0]:
            run = re.match(re.escape(marker[0]) + r"+", text[i:end])[0]
            if (
                (run == marker or len(run) == 3)
                and i > start
                and not text[i - 1].isspace()
                and not (
                    marker[0] == "_"
                    and i + len(run) < end
                    and text[i + len(run)].isalnum()
                )
            ):
                # A shared closing run can finish nested emphasis first, e.g.
                # **bold *italic***. The outer marker uses its trailing part.
                return i + len(run) - len(marker)
            i += len(run)
        else:
            i += 1
    return None


def _inline(text, start, end, spans, context, bold=False, italic=False):
    i = start
    while i < end:
        char = text[i]
        if char == "\\" and i + 1 < end and text[i + 1] in r"\`*_{}[]()#+-.!":
            spans.append((i, i + 1, "syntax"))
            i += 2
            continue
        if char == "`":
            code = _tick_end(text, i, end)
            if code and code[0] < code[1]:
                spans.extend(
                    (
                        (i, code[0], "syntax"),
                        (code[0], code[1], "code"),
                        (code[1], code[2], "syntax"),
                    )
                )
                i = code[2]
                continue
        if char in "*_":
            marker = re.match(re.escape(char) + r"+", text[i:end])[0]
            content = i + len(marker)
            if (
                len(marker) <= 3
                and content < end
                and not text[content].isspace()
                and not (char == "_" and i > 0 and text[i - 1].isalnum())
            ):
                close = _close_marker(text, marker, content, end)
                if close is not None:
                    strong = bold or len(marker) >= 2
                    slant = italic or len(marker) in (1, 3)
                    style = "bi" if strong and slant else "b" if strong else "i"
                    spans.extend(
                        (
                            (i, content, "syntax"),
                            (content, close, f"font_{context}_{style}"),
                            (close, close + len(marker), "syntax"),
                        )
                    )
                    _inline(text, content, close, spans, context, strong, slant)
                    i = close + len(marker)
                    continue
            i += len(marker)
            continue
        i += 1


def find_spans(body, blocks):
    """Return source ranges for the supported, complete Markdown constructs."""
    spans = []
    excluded = set()
    for block in blocks:
        excluded.update(range(block.first_line, block.last_line + 1))
    offset = 0
    for number, line in enumerate(body.split("\n")):
        end = offset + len(line)
        if number in excluded:
            offset = end + 1
            continue
        context, content, content_end = 0, offset, end
        heading = re.match(r" {0,3}(#{1,6})[ \t]+", line)
        item = re.match(r"([ \t]*)(?:[-+*]|\d+[.)])[ \t]+", line)
        if heading:
            context = len(heading[1])
            content += heading.end()
            spans.extend(
                ((offset, end, f"heading_{context}"), (offset, content, "syntax"))
            )
            closing = re.search(r"[ \t]+#+[ \t]*$", line[heading.end() :])
            if closing:
                content_end = content + closing.start()
                spans.append((content_end, end, "syntax"))
        elif item:
            depth = min(8, len(item[1].expandtabs(4)) // 2)
            spans.append((offset, end, f"list_{depth}"))
            if item[1]:
                spans.append((offset, offset + len(item[1]), "syntax"))
            content += item.end()
        elif line.startswith(("    ", "\t")):
            # Indented data/code is deliberately left literal.
            offset = end + 1
            continue
        _inline(body, content, content_end, spans, context)
        offset = end + 1
    return spans


def apply(widget, start, body, blocks):
    """Style source before code-header windows are inserted and shift indices."""
    fonts = widget.__dict__.setdefault("_chad_markdown_fonts", {})
    base = tkfont.nametofont("TkDefaultFont", root=widget).actual()

    def font(context=0, style=""):
        key = (context, style, base["family"], base["size"])
        if key not in fonts:
            size = abs(base["size"]) + (
                {1: 7, 2: 5, 3: 3, 4: 2, 5: 1, 6: 0}.get(context, 0)
            )
            if base["size"] < 0:
                size = -size
            fonts[key] = tkfont.Font(
                root=widget,
                family=base["family"],
                size=size,
                weight="bold" if context or "b" in style else "normal",
                slant="italic" if "i" in style else "roman",
            )
        return fonts[key]

    widget.tag_configure("chad_md_body", font=font(), spacing1=2, spacing3=6)
    widget.tag_add("chad_md_body", start, "end-1c")
    widget.tag_configure("chad_md_syntax", elide=True)
    widget.tag_configure(
        "chad_md_code", font="TkFixedFont", background="#e5e7eb", foreground="#17212b"
    )
    # Tk 8.6 columns use Tcl character units, while '+ chars' arithmetic can
    # count a non-BMP character differently. Use explicit line.column indices.
    lines = body.split("\n")
    offsets = []
    pos = 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1

    def index(offset):
        line = bisect_right(offsets, offset) - 1
        column = int(
            widget.tk.call("string", "length", lines[line][: offset - offsets[line]])
        )
        line_number = widget.index(f"{start} + {line} lines linestart").split(".")[0]
        return widget.index(f"{line_number}.{column}")

    for begin, end, kind in find_spans(body, blocks):
        tag = "chad_md_" + kind
        if kind.startswith("heading_"):
            level = int(kind.split("_")[1])
            widget.tag_configure(tag, font=font(level), spacing1=12, spacing3=7)
        elif kind.startswith("font_"):
            _, context, style = kind.split("_")
            widget.tag_configure(tag, font=font(int(context), style))
        elif kind.startswith("list_"):
            margin = 14 + int(kind.split("_")[1]) * 18
            widget.tag_configure(
                tag, lmargin1=margin, lmargin2=margin + 22, spacing1=2, spacing3=4
            )
        widget.tag_add(tag, index(begin), index(end))
    # Nested emphasis and inline commands take precedence over outer emphasis.
    for tag in widget.tag_names():
        if tag.startswith("chad_md_font_") and tag.endswith("_bi"):
            widget.tag_raise(tag)
    widget.tag_raise("chad_md_code")
    widget.tag_raise("chad_md_syntax")
    widget.tag_raise("sel")
