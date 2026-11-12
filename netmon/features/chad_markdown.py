"""Conservative Markdown typography in Tk Text, preserving original source."""

from bisect import bisect_right
import re
from functools import lru_cache
from tkinter import font as tkfont

# Provider answers and imported analyses are untrusted. Delimiter matching
# rescans line suffixes, so all styling in one render shares a work budget;
# when it runs out, the rest is shown as plain source text.
MAX_MARKDOWN_CHARS = 200_000
MAX_INLINE_LINE_CHARS = 8_192
MAX_NESTING = 16
MAX_TICK_RUN = 32
MAX_RENDER_STEPS = 1_000_000
MAX_RENDER_SPANS = 20_000

_TICKS = re.compile(r"`+")
_RUNS = {"*": re.compile(r"\*+"), "_": re.compile(r"_+")}


class BudgetExceeded(Exception):
    pass


class RenderBudget:
    """Work shared by every Markdown body of one output render."""

    def __init__(self, steps=MAX_RENDER_STEPS, spans=MAX_RENDER_SPANS):
        self.steps = steps
        self.spans = spans
        self.exhausted = False

    def charge(self, amount=1):
        self.steps -= amount
        if self.steps < 0:
            self.exhausted = True
            raise BudgetExceeded

    def add_spans(self, amount):
        self.spans -= amount
        if self.spans < 0:
            self.exhausted = True
            raise BudgetExceeded


@lru_cache(maxsize=MAX_TICK_RUN)
def _tick_close(length):
    return re.compile(r"(?<!`)" + "`" * length + r"(?!`)")


def _tick_end(text, start, end, budget):
    run = _TICKS.match(text, start, end).end() - start
    if run > MAX_TICK_RUN:
        budget.charge(run)
        return None
    close = _tick_close(run).search(text, start + run, end)
    budget.charge((close.end() if close else end) - start)
    return (start + run, close.start(), close.end()) if close else None


def _close_marker(text, marker, start, end, budget):
    i = start
    while i < end:
        budget.charge()
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "`":
            code = _tick_end(text, i, end, budget)
            if code:
                i = code[2]
                continue
        if text[i] == marker[0]:
            run = _RUNS[marker[0]].match(text, i, end).group()
            budget.charge(len(run))
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


def _inline(
    text, start, end, spans, context, budget, bold=False, italic=False, depth=0
):
    i = start
    while i < end:
        budget.charge()
        char = text[i]
        if char == "\\" and i + 1 < end and text[i + 1] in r"\`*_{}[]()#+-.!":
            spans.append((i, i + 1, "syntax"))
            i += 2
            continue
        if char == "`":
            code = _tick_end(text, i, end, budget)
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
            marker = _RUNS[char].match(text, i, end).group()
            budget.charge(len(marker))
            content = i + len(marker)
            if (
                len(marker) <= 3
                and content < end
                and not text[content].isspace()
                and not (char == "_" and i > 0 and text[i - 1].isalnum())
            ):
                close = _close_marker(text, marker, content, end, budget)
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
                    budget.add_spans(3)
                    if depth < MAX_NESTING:
                        _inline(
                            text,
                            content,
                            close,
                            spans,
                            context,
                            budget,
                            strong,
                            slant,
                            depth + 1,
                        )
                    i = close + len(marker)
                    continue
            i += len(marker)
            continue
        i += 1


def find_spans(body, blocks, budget=None):
    """Return source ranges for the supported, complete Markdown constructs.

    Returns no spans (plain text) when the body or the shared render budget
    exceeds its limits.
    """
    budget = RenderBudget() if budget is None else budget
    if budget.exhausted or len(body) > MAX_MARKDOWN_CHARS:
        return []
    try:
        spans = _find_spans(body, blocks, budget)
        budget.add_spans(len(spans))
    except BudgetExceeded:
        return []
    return spans


def _closing_hashes(rest):
    """Start of a closing ``[ \\t]+#+[ \\t]*$`` run, found in linear time."""
    trimmed = rest.rstrip(" \t")
    before = trimmed.rstrip("#")
    if len(before) == len(trimmed) or not before or before[-1] not in " \t":
        return None
    return len(before.rstrip(" \t"))


def _find_spans(body, blocks, budget):
    spans = []
    excluded = set()
    for block in blocks:
        excluded.update(range(block.first_line, block.last_line + 1))
    offset = 0
    for number, line in enumerate(body.split("\n")):
        budget.charge()
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
            closing = _closing_hashes(line[heading.end() :])
            if closing is not None:
                content_end = content + closing
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
        if len(line) <= MAX_INLINE_LINE_CHARS:
            _inline(body, content, content_end, spans, context, budget)
        offset = end + 1
    return spans


def apply(widget, start, body, blocks, budget=None):
    """Style source before code-header windows are inserted and shift indices."""
    spans = find_spans(body, blocks, budget)
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

    for begin, end, kind in spans:
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
