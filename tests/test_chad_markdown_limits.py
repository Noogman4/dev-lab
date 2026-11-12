"""Untrusted Markdown must not monopolize the Tk thread (scan 4852934e #2)."""

import re
import time

import pytest

from netmon.features import chad_controller as controller
from netmon.features import chad_markdown as md
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app

# Unterminated emphasis openers: each one used to rescan the rest of its line.
ADVERSARIAL_LINE = "*a " * 2700


def test_unterminated_openers_fall_back_to_plain_text_quickly():
    body = "\n".join([ADVERSARIAL_LINE] * 40)
    started = time.perf_counter()
    assert md.find_spans(body, []) == []
    assert time.perf_counter() - started < 2.0


def test_unterminated_code_ticks_are_bounded():
    body = "\n".join(["`a *b " * 1300] * 40)
    started = time.perf_counter()
    md.find_spans(body, [])
    assert time.perf_counter() - started < 2.0


def test_render_budget_is_shared_between_bodies():
    budget = md.RenderBudget()
    assert md.find_spans(ADVERSARIAL_LINE, [], budget) == []
    assert budget.exhausted
    # Later bodies of the same render stay plain and cost nothing.
    assert md.find_spans("**fett**", [], budget) == []
    assert md.find_spans("**fett**", []) != []


def test_span_budget_falls_back_to_plain_text():
    budget = md.RenderBudget(spans=5)
    assert md.find_spans("*a* *b* *c*", [], budget) == []
    assert budget.exhausted


def test_oversized_body_is_plain_text():
    body = "**x** " * (md.MAX_MARKDOWN_CHARS // 6 + 1)
    assert len(body) > md.MAX_MARKDOWN_CHARS
    assert md.find_spans(body, []) == []


def test_overlong_line_keeps_block_style_without_inline_scan():
    line = "# **Titel** " + "x" * md.MAX_INLINE_LINE_CHARS
    spans = md.find_spans(line + "\n**kurz**", [])
    kinds = {kind for _begin, _end, kind in spans}
    assert "heading_1" in kinds
    assert not any(
        kind.startswith("font_1_") for kind in kinds
    ), "inline styling skipped on the long line"
    assert any(kind == "font_0_b" for kind in kinds)


def test_huge_backtick_run_is_literal():
    body = "`" * (md.MAX_TICK_RUN + 1) + "code" + "`" * (md.MAX_TICK_RUN + 1)
    assert not any(kind == "code" for _b, _e, kind in md.find_spans(body, []))
    ticks = "`" * md.MAX_TICK_RUN
    assert any(
        kind == "code" for _b, _e, kind in md.find_spans(ticks + "c" + ticks, [])
    )


@pytest.mark.parametrize(
    "rest",
    [
        "Titel ##",
        "Titel ##  ",
        "Titel\t#",
        "Titel#",
        "##",
        "",
        "a # b",
        "a ## #",
        " ##",
    ],
)
def test_closing_hashes_match_the_former_regex(rest):
    match = re.search(r"[ \t]+#+[ \t]*$", rest)
    assert md._closing_hashes(rest) == (match.start() if match else None)


def test_normal_answer_styles_unchanged():
    spans = md.find_spans("# Kopf ##\n- **fett** und *kursiv* `code`", [])
    kinds = [kind for _b, _e, kind in spans]
    assert "heading_1" in kinds and "list_0" in kinds
    assert "font_0_b" in kinds and "font_0_i" in kinds and "code" in kinds


def test_imported_adversarial_answers_render_plain_and_fast(chad_app):
    root, app = chad_app
    body = "\n".join([ADVERSARIAL_LINE] * 8)
    app.chad_output_entries = [
        {"title": f"Chad Antwort {n}", "text": body, "kind": "answer"}
        for n in range(30)
    ] + [{"title": "Chad Antwort Ende", "text": "**fett**", "kind": "answer"}]
    started = time.perf_counter()
    controller.refresh_chad_output_view(app)
    root.update()
    assert time.perf_counter() - started < 10.0
    widget = app.chad_analysis_text
    assert widget.search(ADVERSARIAL_LINE[:30], "1.0")
    assert app.__dict__.get("chad_markdown_budget") is None
