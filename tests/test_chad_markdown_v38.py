"""Actual Tk Markdown typography, source round trips and exact command copies."""

import json
from pathlib import Path
import shutil
import subprocess
from tkinter import font as tkfont

import pytest

from netmon.features import chad_controller as controller
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app
SOURCE = """# Ergebnis der Prüfung

😀 **Fett**, *kursiv* und ***beides***. Prüfe `resolvectl status` zuerst.

## Nächste Schritte

- **Resolver prüfen:** Server mit dem gewählten Profil vergleichen.
  - Danach die tatsächliche Ausgabe ansehen.
1. Nur diesen Befehl kopieren:

```bash
printf '%s\\n' '**wörtlich**' 'kernel_task' '`nicht auswerten`'
```

2. Die Ausgabe anschließend beurteilen.

Der vollständige Text bleibt erhalten."""


def show(root, app, source=SOURCE, title="Chad Antwort"):
    controller.append_to_chad_output(app, title, source)
    root.update()
    return app.chad_analysis_text


def tagged_font(widget, word, tag_prefix):
    position = widget.search(word, "1.0")
    assert position, word
    tag = next(tag for tag in widget.tag_names(position) if tag.startswith(tag_prefix))
    return tkfont.Font(root=widget, font=widget.tag_cget(tag, "font")).actual()


@pytest.mark.parametrize("level", range(1, 7))
def test_heading_prefix_hidden_and_font_sized_without_changing_source(chad_app, level):
    root, app = chad_app
    source = "#" * level + " **Überschrift** ###\nNormaler Absatz."
    widget = show(root, app, source)
    assert source in controller.get_chad_transcript_text(app)
    assert widget.search("#", "1.0") == ""
    assert widget.search("**", "1.0") == ""
    heading = tagged_font(widget, "Überschrift", f"chad_md_font_{level}_")
    base = tkfont.nametofont("TkDefaultFont", root=widget).actual()
    assert abs(heading["size"]) >= abs(base["size"])
    assert heading["weight"] == "bold"
    position = widget.search("Überschrift", "1.0")
    assert f"chad_md_heading_{level}" in widget.tag_names(position)


@pytest.mark.parametrize(
    "source,word,weight,slant",
    [
        ("**Fett**", "Fett", "bold", "roman"),
        ("__Fett__", "Fett", "bold", "roman"),
        ("*Kursiv*", "Kursiv", "normal", "italic"),
        ("_Kursiv_", "Kursiv", "normal", "italic"),
        ("***Beides***", "Beides", "bold", "italic"),
        ("___Beides___", "Beides", "bold", "italic"),
        ("**Fett und *Kursiv* zusammen**", "Kursiv", "bold", "italic"),
        ("*Kursiv und **Fett** zusammen*", "Fett", "bold", "italic"),
        ("**Fett und *Kursiv***", "Kursiv", "bold", "italic"),
        ("*Kursiv und **Fett***", "Fett", "bold", "italic"),
    ],
)
def test_emphasis_and_nested_emphasis_have_real_fonts(
    chad_app, source, word, weight, slant
):
    root, app = chad_app
    widget = show(root, app, source)
    position = widget.search(word, "1.0")
    styles = [
        tag for tag in widget.tag_names(position) if tag.startswith("chad_md_font_")
    ]
    actual = tkfont.Font(root=widget, font=widget.tag_cget(styles[-1], "font")).actual()
    assert (actual["weight"], actual["slant"]) == (weight, slant)
    assert widget.get("2.0", "end-1c") == source


def test_unicode_inline_commands_lists_and_code_copy_keep_source_exact(chad_app):
    root, app = chad_app
    root.geometry("1100x850")
    widget = show(root, app)
    assert controller.get_chad_transcript_text(app) == "--- Chad Antwort ---\n" + SOURCE
    assert "chad_md_font_0_b" in widget.tag_names(widget.search("Fett", "1.0"))
    inline = widget.search("resolvectl status", "1.0")
    assert "chad_md_code" in widget.tag_names(inline)
    assert widget.tag_cget("chad_md_code", "background") == "#e5e7eb"
    assert "chad_md_list_0" in widget.tag_names(widget.search("Resolver prüfen", "1.0"))
    assert "chad_md_list_1" in widget.tag_names(widget.search("Danach", "1.0"))
    assert int(widget.tag_cget("chad_md_list_1", "lmargin1")) > int(
        widget.tag_cget("chad_md_list_0", "lmargin1")
    )
    literal = widget.search("**wörtlich**", "1.0")
    assert literal
    assert "chad_code" in widget.tag_names(literal)
    assert "chad_md_syntax" not in widget.tag_names(literal)
    assert len(app.chad_code_blocks) == 1
    app.chad_code_blocks[0]["button"].invoke()
    assert (
        root.clipboard_get()
        == "printf '%s\\n' '**wörtlich**' 'kernel_task' '`nicht auswerten`'"
    )
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    widget.tag_add("sel", inline, f"{inline} + {len('resolvectl status')} chars")
    app._copy_text_widget_selection(widget)
    assert root.clipboard_get() == "resolvectl status"


@pytest.mark.parametrize(
    "source,visible",
    [
        ("kernel_task und file_name_test", "kernel_task und file_name_test"),
        ("Nicht geschlossen: **Fett", "**Fett"),
        ("Nicht geschlossen: `Befehl", "`Befehl"),
        (r"\*wörtlich\*", "*wörtlich*"),
        ("Absatz\n    **eingerückte Daten**", "**eingerückte Daten**"),
        ("<script>alert('literal')</script>", "<script>"),
    ],
)
def test_literals_escapes_and_incomplete_markup_remain_readable(
    chad_app, source, visible
):
    root, app = chad_app
    widget = show(root, app, source)
    assert source in controller.get_chad_transcript_text(app)
    assert widget.search(visible, "1.0")


def test_backticks_protect_emphasis_inside_code_and_open_fences(chad_app):
    root, app = chad_app
    source = "**Fett mit `a**b` im Satz** und ``echo `x` **literal**``.\n```bash\n**offener Code**"
    widget = show(root, app, source)
    assert widget.search("a**b", "1.0")
    assert widget.search("**literal**", "1.0")
    assert widget.search("**offener Code**", "1.0")
    assert len(app.chad_code_blocks) == 1 and not app.chad_code_blocks[0]["closed"]
    app.chad_code_blocks[0]["button"].invoke()
    assert root.clipboard_get() == "**offener Code**"


def test_prepared_prompts_user_messages_and_error_data_stay_literal(chad_app):
    root, app = chad_app
    controller.set_chad_direct_prompt(
        app, "Vorbereitung", "# Rohdaten **nicht formatieren**"
    )
    show(root, app, "**Eigene Eingabe**", "Du")
    controller.append_to_chad_output(app, "API-Fehler", "**Fehlerdaten**", kind="error")
    widget = app.chad_analysis_text
    assert widget.search("# Rohdaten **nicht formatieren**", "1.0")
    assert widget.search("**Eigene Eingabe**", "1.0")
    assert widget.search("**Fehlerdaten**", "1.0")


def test_save_reload_filter_and_selection_retain_original_markdown(
    chad_app, monkeypatch, tmp_path
):
    root, app = chad_app
    app.chad_analysis_current_prompt = "Vorbereiteter Prompt"
    app.chad_online_result = SOURCE
    app.chad_chat_history = []
    widget = show(root, app)
    start = widget.search("Fett", "1.0")
    widget.tag_add("sel", start, f"{start} + 4 chars")
    selection = widget.tag_ranges("sel")
    controller.append_to_chad_output(app, "Chad Antwort", "Weitere **Antwort**")
    root.update()
    assert widget.tag_ranges("sel") == selection
    path = tmp_path / "markdown.json"
    monkeypatch.setattr(
        controller.filedialog, "asksaveasfilename", lambda **k: str(path)
    )
    controller.save_chad_analysis_to_file(app)
    data = json.loads(path.read_text())
    assert data["output_entries"][0]["text"] == SOURCE
    assert SOURCE in data["transcript"]
    controller.clear_chad_analysis(app)
    monkeypatch.setattr(controller.filedialog, "askopenfilename", lambda **k: str(path))
    controller.load_chad_analysis_from_file(app)
    app.chad_output_filter_var.set("Nur Antworten")
    controller.refresh_chad_output_view(app)
    root.update()
    assert "chad_md_font_0_b" in widget.tag_names(widget.search("Fett", "1.0"))
    assert SOURCE in controller.get_chad_transcript_text(app)
    app.chad_code_blocks[0]["button"].invoke()
    assert "**wörtlich**" in root.clipboard_get()


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_markdown_visual_fixture(chad_app, theme):
    root, app = chad_app
    root.geometry("1100x850")
    if theme == "dark":
        app.chad_analysis_text.configure(background="#101418", foreground="#e6e8eb")
    app.chad_dev_filter_status_var.set(
        "Markdown: Überschriften, Hervorhebungen, Listen und Code"
    )
    widget = show(root, app)
    widget.see("1.0")
    root.update()
    if shutil.which("import"):
        target = f"/work/chad-markdown-{theme}.png"
        subprocess.run(
            ["import", "-window", str(root.winfo_id()), target], check=True, timeout=10
        )
        assert Path(target).is_file()
