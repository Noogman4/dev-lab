"""Real code-block rendering/copy and Markdown round trips in private Tk."""

import json
from pathlib import Path
import shutil
import subprocess

import pytest

from netmon.features import chad_code_blocks as code_blocks
from netmon.features import chad_controller as controller
from tests import test_chad_output_layout_v29 as layout_fixtures

chad_app = layout_fixtures.chad_app


@pytest.mark.parametrize(
    "opening,closing",
    [
        ("```bash", "```"),
        ("~~~sh", "~~~~"),
        ("````python", "`````"),
        ("   ```", "  ```"),
    ],
)
def test_parser_preserves_commands_and_indentation(opening, closing):
    source = f"Intro\n{opening}\n  echo 'one'  \nprintf 'two'\n{closing}\nAfter."
    blocks = code_blocks.find_code_blocks(source)
    assert len(blocks) == 1
    assert blocks[0].code == "  echo 'one'  \nprintf 'two'"
    assert blocks[0].closed


def test_short_or_different_fence_is_code_not_a_closing_delimiter():
    source = "````text\n```\n~~~\n````"
    block = code_blocks.find_code_blocks(source)[0]
    assert block.code == "```\n~~~" and block.closed


@pytest.mark.parametrize(
    "source",
    [
        "`inline`",
        "    ```bash\necho one\n    ```",
        "No code here.",
        "```not`valid\ntext",
    ],
)
def test_plain_or_inline_text_is_not_a_fenced_code_block(source):
    assert not code_blocks.find_code_blocks(source)


def test_unclosed_block_preserves_received_text_without_invented_completion():
    block = code_blocks.find_code_blocks("before\n```bash\nprintf 'unfinished")[0]
    assert not block.closed
    assert block.code == "printf 'unfinished"


def test_real_copy_buttons_and_transcript_keep_code_exact(chad_app):
    root, app = chad_app
    source = "Vorher 😀\n```bash\nsudo apt autoremove\nprintf '%s' 'ä'\n```\nDazwischen\n~~~python\n  print('two')  \n~~~\nDanach."
    controller.append_to_chad_output(app, "Chad Antwort: Code", source)
    root.update()
    widget = app.chad_analysis_text
    assert (
        controller.get_chad_transcript_text(app)
        == "--- Chad Antwort: Code ---\n" + source
    )
    assert len(app.chad_code_blocks) == 2
    for block, expected in zip(
        app.chad_code_blocks,
        ["sudo apt autoremove\nprintf '%s' 'ä'", "  print('two')  "],
    ):
        icon = str(block["button"].cget("image"))
        block["button"].invoke()
        assert root.clipboard_get() == expected
        assert str(block["button"].cget("text")) == "Kopiert"
        assert str(block["button"].cget("compound")) == "image"
        assert str(block["button"].cget("image")) != icon
        assert block["button"].winfo_rootx() > block["frame"].winfo_rootx()
    assert app.chad_output_entries[0]["text"] == source
    assert widget.tag_cget("chad_code", "background") == "#e5e7eb"
    assert widget.tag_cget("chad_code", "foreground") == "#17212b"
    assert widget.tag_ranges("chad_code_fence")
    start = widget.search("sudo apt", "1.0")
    assert "chad_code" in widget.tag_names(start)
    widget.tag_add("sel", start, f"{start} lineend")
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    app._copy_text_widget_selection(widget)
    assert root.clipboard_get() == "sudo apt autoremove"


def test_icon_copy_works_from_keyboard_and_explains_itself_with_tooltip(chad_app):
    root, app = chad_app
    controller.append_to_chad_output(
        app, "Chad Antwort", "```bash\necho 'einzeln'\n```"
    )
    root.update()
    block = app.chad_code_blocks[0]
    button, tooltip = block["button"], block["tooltip"]
    assert str(button.cget("takefocus")) == "1"
    button.focus_force()
    root.update()
    tooltip._show()
    assert tooltip.tipwindow.winfo_exists()
    assert tooltip.tipwindow.winfo_children()[0].cget("text") == "Kopieren"
    width = button.winfo_reqwidth()
    button.event_generate("<KeyPress-space>")
    button.event_generate("<KeyRelease-space>")
    root.update()
    assert root.clipboard_get() == "echo 'einzeln'"
    assert tooltip.text == "Kopiert"
    assert tooltip.tipwindow is None
    assert button.winfo_reqwidth() == width


def test_icon_tooltip_respects_setting_and_cleans_up_on_refresh(chad_app):
    import tkinter as tk

    root, app = chad_app
    app.tooltips_enabled = tk.BooleanVar(master=root, value=False)
    controller.append_to_chad_output(app, "Chad Antwort", "```bash\necho fixture\n```")
    root.update()
    tooltip = app.chad_code_blocks[0]["tooltip"]
    tooltip._show()
    assert tooltip.tipwindow is None
    app.tooltips_enabled.set(True)
    tooltip._show()
    window = tooltip.tipwindow
    tooltip._schedule()
    assert tooltip.after_id is not None
    button = app.chad_code_blocks[0]["button"]
    button.pack_forget()
    root.update()
    assert tooltip.after_id is None
    assert tooltip.tipwindow is None
    assert not window.winfo_exists()
    button.pack(side="right")
    root.update()
    tooltip._show()
    window = tooltip.tipwindow
    tooltip._schedule()
    app.chad_output_entries = []
    controller.refresh_chad_output_view(app)
    root.update()
    assert tooltip.after_id is None
    assert tooltip.tipwindow is None
    assert not window.winfo_exists()


def test_refresh_filter_resize_and_clear_destroy_old_headers(chad_app):
    root, app = chad_app
    controller.append_to_chad_output(
        app, "Chad Antwort: Code", "```bash\necho answer\n```"
    )
    controller.append_to_chad_output(app, "System", "```text\nreport\n```")
    root.update()
    old = [b["frame"] for b in app.chad_code_blocks]
    app.chad_output_filter_var.set("Nur Antworten")
    controller.refresh_chad_output_view(app)
    root.update()
    assert all(not frame.winfo_exists() for frame in old)
    assert len(app.chad_code_blocks) == 1
    for geometry in ["1100x650", "650x480", "900x650"]:
        root.geometry(geometry)
        root.update()
        frame = app.chad_code_blocks[0]["frame"]
        button = app.chad_code_blocks[0]["button"]
        assert frame.winfo_width() <= app.chad_analysis_text.winfo_width()
        assert button.winfo_ismapped()
        assert (
            button.winfo_rootx() + button.winfo_width()
            <= frame.winfo_rootx() + frame.winfo_width()
        )
    old = [b["frame"] for b in app.chad_code_blocks]
    app.chad_output_entries = []
    controller.refresh_chad_output_view(app)
    assert not app.chad_code_blocks
    assert all(not frame.winfo_exists() for frame in old)


def test_save_and_reload_keep_original_markdown_and_restore_buttons(
    chad_app, tmp_path, monkeypatch
):
    root, app = chad_app
    source = "Description\n```bash\necho 'saved'\n```"
    app.chad_analysis_current_prompt = "private fixture"
    app.chad_online_result = ""
    app.chad_chat_history = []
    controller.append_to_chad_output(app, "Chad Antwort: saved", source)
    path = tmp_path / "analysis.json"
    monkeypatch.setattr(
        controller.filedialog, "asksaveasfilename", lambda **kwargs: str(path)
    )
    controller.save_chad_analysis_to_file(app)
    saved = json.loads(path.read_text())
    assert saved["output_entries"][0]["text"] == source
    assert "Kopieren" not in saved["transcript"]
    assert "```bash" in saved["transcript"]
    app.chad_output_entries = []
    controller.refresh_chad_output_view(app)
    monkeypatch.setattr(
        controller.filedialog, "askopenfilename", lambda **kwargs: str(path)
    )
    controller.load_chad_analysis_from_file(app)
    root.update()
    assert len(app.chad_code_blocks) == 1
    app.chad_code_blocks[0]["button"].invoke()
    assert root.clipboard_get() == "echo 'saved'"


def test_open_block_is_marked_as_open_and_clipboard_failure_is_visible(
    chad_app, monkeypatch
):
    root, app = chad_app
    controller.append_to_chad_output(
        app, "Chad Antwort: partial", "```bash\necho incomplete"
    )
    root.update()
    block = app.chad_code_blocks[0]
    assert not block["closed"] and "offener Codeblock" in block["language"]
    dialogs = []
    monkeypatch.setattr(
        code_blocks.messagebox,
        "showerror",
        lambda *args, **kwargs: dialogs.append(args),
    )
    monkeypatch.setattr(
        app.chad_analysis_text,
        "clipboard_append",
        lambda value: (_ for _ in ()).throw(code_blocks.tk.TclError("fixture")),
    )
    block["button"].invoke()
    assert dialogs and dialogs[0][0] == "Kopieren fehlgeschlagen"


def test_code_block_visual_fixture(chad_app):
    root, app = chad_app
    root.geometry("1100x700")
    app.chad_dev_filter_status_var.set("Codeblöcke zum Kopieren")
    controller.append_to_chad_output(
        app,
        "Chad Antwort: Beispiel",
        "**Schritt 1:** Dienste prüfen\n\n```bash\nsystemctl --failed\nprintf '%s\\n' 'Beispiel mit Einrückung'\n```\n\n**Schritt 2:** Ergebnis auswerten.\n\n```python\nfor item in ['eins', 'zwei']:\n    print(item)\n```\n\nVollständiger Ausgabetext.",
    )
    root.update()
    app.chad_analysis_text.see("1.0")
    root.update()
    if shutil.which("import"):
        subprocess.run(
            ["import", "-window", str(root.winfo_id()), "/work/chad-code-blocks.png"],
            check=True,
            timeout=10,
        )
        assert Path("/work/chad-code-blocks.png").is_file()
