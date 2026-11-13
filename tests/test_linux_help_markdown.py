"""Read-only Markdown pilot, renderer interactions and legacy-view fallback."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_markdown_service as markdown
from netmon.ui.linux_help_reader import LinuxHelpReader
from netmon.ui.tabs.linux_help_tab import build_linux_help_tab

ENTRY = {"id": "7z", "name": "7z", "cmd": "7z", "risk": "safe"}


def document(body):
    fields = {
        "id": "7z",
        "name": "7z",
        "command": "7z",
        "category": "Archive",
        "language": "de",
        "root_required": False,
        "risk_level": "caution",
    }
    return (
        "---\n"
        + "\n".join(f"{key}: {json.dumps(value)}" for key, value in fields.items())
        + "\n---\n"
        + body
    )


def test_real_pilot_contains_ten_sections_and_separate_code_and_table_blocks():
    item = markdown.load_command_document(ENTRY)
    assert item.metadata["root_required"] is False
    assert len([b for b in item.blocks if b.kind == "heading" and b.level == 2]) == 10
    assert any(b.kind == "code" and "7z x" in b.text for b in item.blocks)
    assert any(
        b.kind == "table" and any("-aos" in value for row in b.rows for value in row)
        for b in item.blocks
    )


@pytest.mark.parametrize(
    "item",
    [
        None,
        {},
        {**ENTRY, "name": "../7z"},
        {**ENTRY, "cmd": "7z; touch /tmp/payload"},
        {**ENTRY, "entry_type": "glossary"},
        {"name": "ls", "cmd": "ls"},
    ],
)
def test_only_exact_pilot_can_select_a_document(item):
    assert markdown.load_command_document(item) is None


@pytest.mark.parametrize(
    "body",
    [
        "# Title\n",
        "<script>alert(1)</script>\n",
        "![image](https://127.0.0.1/private)\n",
        "!include /etc/passwd\n",
    ],
)
def test_unrecognized_markup_remains_passive_text(body):
    parsed = markdown.parse_document(document(body))
    assert parsed.blocks[0].text == body.strip("\n").lstrip("# ")


@pytest.mark.parametrize(
    "failure",
    [
        "bytes",
        "lines",
        "blocks",
        "cells",
        "code",
        "unclosed",
        "wrong-table",
        "metadata",
        "controls",
    ],
)
def test_reader_input_limits_fail_instead_of_partial_render(monkeypatch, failure):
    text = document("## Good\n\nText")
    if failure == "bytes":
        monkeypatch.setattr(markdown, "MAX_BYTES", 8)
    elif failure == "lines":
        monkeypatch.setattr(markdown, "MAX_LINES", 2)
    elif failure == "blocks":
        monkeypatch.setattr(markdown, "MAX_BLOCKS", 1)
    elif failure == "cells":
        monkeypatch.setattr(markdown, "MAX_CELLS", 2)
        text = document("| A | B |\n| --- | --- |\n| One | Two |\n")
    elif failure == "code":
        monkeypatch.setattr(markdown, "MAX_CODE_CHARS", 1)
        text = document("```bash\nls\n```\n")
    elif failure == "unclosed":
        text = document("```bash\nls\n")
    elif failure == "wrong-table":
        text = document("| A | B |\n| --- | --- |\n| One |\n")
    elif failure == "metadata":
        text = text.replace('risk_level: "caution"', 'risk_level: "everything safe"')
    else:
        text += "\x00"
    with pytest.raises(ValueError):
        markdown.parse_document(text)


def test_local_file_is_bounded_and_symlink_or_fifo_is_not_read(monkeypatch, tmp_path):
    monkeypatch.setattr(markdown, "DOCUMENT_DIR", tmp_path)
    assert markdown.load_command_document(ENTRY) is None
    target = tmp_path / "other.md"
    target.write_text(document("## Test\nText"))
    path = tmp_path / "7z.md"
    path.symlink_to(target)
    with pytest.raises(OSError):
        markdown.load_command_document(ENTRY)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(ValueError):
        markdown.load_command_document(ENTRY)
    path.unlink()
    path.write_text(document("## Test\nText"))
    monkeypatch.setattr(markdown, "MAX_BYTES", 8)
    with pytest.raises(ValueError):
        markdown.load_command_document(ENTRY)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.7-zip.org/",
        "https://127.0.0.1/",
        "https://evil.example/",
        "https://evil.example\\@www.7-zip.org/",
        "https://www.7-zip.org:999/",
        "https://user@www.7-zip.org/",
        "https://www.7-zip.org:/",
        "https://www.7-zip.org/\n",
        "file:///etc/passwd",
    ],
)
def test_sources_cannot_choose_arbitrary_browser_targets(url):
    assert markdown.source_url(url) == ""


@pytest.fixture
def root():
    window = tk.Tk()
    window.geometry("1000x720")
    yield window
    window.destroy()


def test_reader_copy_search_toc_and_popout_do_not_execute(root, monkeypatch):
    import netmon.ui.linux_help_reader as ui

    monkeypatch.setattr(
        ui.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("Passive reader executed a process"),
    )
    reader = LinuxHelpReader(root)
    reader.pack(fill="both", expand=True)
    reader.set_document(markdown.load_command_document(ENTRY), ENTRY)
    root.update()
    assert len(reader.headings) == 10
    assert reader.text.cget("state") == "disabled"
    assert "weicht" in reader.status.get()
    for button, block in zip(
        reader.code_buttons, [b for b in reader.document.blocks if b.kind == "code"]
    ):
        button.invoke()
        assert reader.clipboard_get() == block.text.rstrip("\n")
    for query in ("7z a -t7z", "-aos", "Root-Rechte"):
        reader.query.set(query)
        reader.find()
        assert reader.matches
        if query == "-aos":
            assert any(
                widget is not reader.text for widget, _index, _mark in reader.matches
            )
        reader.find_next(-1)
        root.update()
    reader.contents.current(6)
    reader.jump_to_section()
    assert float(reader.text.yview()[0]) > 0
    reader.change_font(1)
    assert reader.normal_font.cget("size") == 12
    window = reader.open_window()
    root.update()
    assert window.reader.document is reader.document
    reader.show_empty()
    assert window.reader.document.metadata["id"] == "7z"
    assert not reader.text.get("1.0", "end").strip()
    assert not reader.cells and not reader.links and not reader.matches
    window.destroy()


def test_only_click_can_launch_reviewed_source_url(root, monkeypatch):
    import netmon.ui.linux_help_reader as ui

    calls = []
    monkeypatch.setattr(ui.subprocess, "Popen", lambda argv, **_k: calls.append(argv))
    reader = LinuxHelpReader(root)
    reader.set_document(markdown.load_command_document(ENTRY))
    assert calls == []
    assert not reader.open_source("https://127.0.0.1/")
    assert reader.open_source("https://www.7-zip.org/faq.html")
    assert calls == [["/usr/bin/xdg-open", "https://www.7-zip.org/faq.html"]]


def test_table_cells_wrap_and_resize_without_truncation(root):
    reader = LinuxHelpReader(root)
    reader.pack(fill="both", expand=True)
    reader.set_document(
        markdown.parse_document(
            document(
                "## Tabelle\n| Option | Erklärung |\n| --- | --- |\n| -aos | "
                + "Wort " * 25
                + "|\n"
            )
        )
    )
    root.geometry("700x500")
    root.update()
    reader._resize_windows()
    root.update()
    narrow = [int(cell.cget("height")) for cell, _mark in reader.cells]
    assert max(narrow) > 1
    assert all(
        cell.winfo_width() < reader.text.winfo_width() for cell, _mark in reader.cells
    )
    root.geometry("1100x720")
    root.update()
    assert max(int(cell.cget("height")) for cell, _mark in reader.cells) <= max(narrow)


def test_document_selection_falls_back_without_changing_the_catalog(root, monkeypatch):
    tree = ttk.Treeview(root)
    for name in ("7z", "ls"):
        tree.insert("", "end", iid=name, text=name)
    app = SimpleNamespace(
        linux_help_tree=tree,
        linux_help_data=[
            dict(ENTRY),
            {"id": "ls", "name": "ls", "cmd": "ls", "info": "Dateien auflisten"},
        ],
        tr=lambda _key, fallback: fallback,
    )
    original = dict(ENTRY)
    tree.selection_set("7z")
    window = controller.open_linux_help_reader(app)
    assert not window.transient()
    assert tuple(window.resizable()) == (1, 1)
    window.geometry("1280x980")
    root.update()
    assert window.winfo_width() == 1280 and window.winfo_height() == 980
    window.geometry("700x450")
    root.update()
    assert window.winfo_width() == 700 and window.winfo_height() == 450
    assert window.notebook.select() == str(window.reader)
    assert [window.notebook.tab(tab, "text") for tab in window.notebook.tabs()] == [
        "Kurzinfo",
        "Dokumentation",
    ]
    assert window.short_info.cget("state") == "disabled"
    assert "7z" in window.short_info.get("1.0", "end")
    assert ENTRY == original
    tree.selection_set("ls")
    controller.on_linux_help_select(app)
    assert (
        window.entry["name"] == "7z"
    )  # A single click does not change the open reader.
    assert controller.open_linux_help_reader(app) is window
    assert window.winfo_width() == 700 and window.winfo_height() == 450
    assert window.notebook.select() == str(window.short_frame)
    assert window.reader.document is None
    assert "Dateien auflisten" in window.short_info.get("1.0", "end")
    monkeypatch.setattr(
        markdown,
        "load_command_document",
        lambda _entry: (_ for _ in ()).throw(ValueError("broken")),
    )
    tree.selection_set("7z")
    assert controller.open_linux_help_reader(app) is window
    assert "nicht geladen" in window.reader.info.get()
    window.destroy()
    replacement = controller.open_linux_help_reader(app)
    assert replacement is not window
    replacement.destroy()


def test_linux_tab_double_click_uses_existing_reader_and_compact_management(root):
    translations = json.loads(
        (Path(__file__).resolve().parents[1] / "netmon/lang/de.json").read_text()
    )
    app = SimpleNamespace(
        tools_nb=ttk.Notebook(root),
        tr=lambda key, fallback: translations.get(key, fallback),
    )
    for name in ("status", "search", "category", "source", "risk_filter"):
        setattr(app, f"linux_help_{name}_var", tk.StringVar(master=root))
    for name in (
        "refresh_linux_help_list",
        "clear_linux_help_filters",
        "reload_linux_help_data",
        "linux_help_import_csv_dialog",
        "linux_help_export_csv_dialog",
        "send_linux_help_command_to_terminal",
        "linux_help_new_entry",
        "linux_help_edit_selected",
        "linux_help_delete_selected",
        "on_linux_help_select",
        "show_linux_help_tree_menu",
        "attach_chad_context_menu",
        "import_linux_help_pdf_dialog",
        "reload_linux_help_documents",
        "open_selected_linux_help_pdf",
        "open_linux_help_documents_folder",
        "on_linux_help_document_select",
        "show_linux_help_document_menu",
    ):
        setattr(app, name, lambda *_a, **_k: None)
    app.linux_help_data = [dict(ENTRY)]
    app.on_linux_help_select = lambda event=None: controller.on_linux_help_select(
        app, event
    )
    build_linux_help_tab(app)
    app.linux_help_edit_selected = lambda: pytest.fail("Double-click opened the editor")
    app.linux_help_status_var.set("Linux-Datenbank · Markdown-Muster: 7z")
    app.linux_help_tree.insert(
        "",
        "end",
        iid="7z",
        text="7z",
        values=(
            "Archive & Kompression",
            "Befehl",
            "Sicher (alter Eintrag)",
            "Nein",
            "archive, kompression",
            "Archive erstellen, prüfen und entpacken",
        ),
    )
    app.linux_help_tree.selection_set("7z")
    app.tools_nb.pack(fill="both", expand=True)
    root.update()
    assert app.linux_help_text is None
    assert not hasattr(app, "linux_help_detail_notebook")
    assert app.linux_help_documents_text.winfo_exists()
    assert app.btn_linux_help_import_pdf.winfo_exists()
    assert app.linux_help_tree.winfo_exists()
    app.linux_help_tree.event_generate("<<TreeviewSelect>>")
    root.update()
    assert app.linux_help_reader_window is None
    assert int(app.linux_help_documents_text.cget("height")) == 3
    if os.environ.get("NETMON_TEST_ISOLATED") == "1":
        from PIL import ImageGrab

        root.geometry("1120x940")
        root.update()
        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
            "/work/linux-help-tab-compact.png"
        )
    x, y, _width, height = app.linux_help_tree.bbox("7z")
    for stamp in (1000, 1100):
        for sequence, delay in (("<ButtonPress-1>", 0), ("<ButtonRelease-1>", 10)):
            app.linux_help_tree.event_generate(
                sequence, x=x + 15, y=y + height // 2, time=stamp + delay
            )
            root.update()
    window = app.linux_help_reader_window
    assert window is not None
    assert len(window.reader.headings) == 10
    assert len(window.notebook.tabs()) == 2
    assert window.notebook.select() == str(window.reader)
    assert (
        controller.open_linux_help_reader(
            app, SimpleNamespace(num=1, y=app.linux_help_tree.winfo_height() - 1)
        )
        == "break"
    )
    assert app.linux_help_reader_window is window
    assert "Risiko: Risiko:" not in window.short_info.get("1.0", "end")
    if os.environ.get("NETMON_TEST_ISOLATED") == "1":
        from PIL import ImageGrab

        window.geometry("1100x850+10+10")
        for name, bg, fg in (
            ("light", "#f4f6f8", "#101418"),
            ("dark", "#111418", "#e6edf3"),
        ):
            style = ttk.Style(root)
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            window.reader.contents.current(3)
            window.reader.jump_to_section()
            root.update()
            assert window.reader.text.cget("background") == bg
            assert window.short_info.cget("background") == bg
            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
                f"/work/linux-help-reader-tabs-{name}.png"
            )
        window.notebook.select(window.short_frame)
        root.update()
        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
            "/work/linux-help-reader-short-info.png"
        )
        window.destroy()
        assert Path("/work/linux-help-reader-tabs-dark.png").is_file()


def test_reader_keeps_glossary_read_only_and_supports_keyboard_and_close(root):
    tree = ttk.Treeview(root)
    tree.insert("", "end", iid="term", text="Algorithmus")
    tree.selection_set("term")
    app = SimpleNamespace(
        linux_help_tree=tree,
        linux_help_data=[],
        linux_help_glossary=[
            {
                "id": "term",
                "name": "Algorithmus",
                "entry_type": "glossary",
                "info": "Schrittfolge",
                "related": "Programm",
            }
        ],
        tr=lambda _key, fallback: fallback,
    )
    assert controller.open_linux_help_reader(app, SimpleNamespace(num="??")) == "break"
    window = app.linux_help_reader_window
    assert window.notebook.select() == str(window.short_frame)
    assert "Schrittfolge" in window.short_info.get("1.0", "end")
    assert "read-only" in window.short_info.get("1.0", "end")
    assert window.reader.document is None
    window.destroy()
    app.linux_help_data.clear()
    app.linux_help_glossary.clear()
    assert controller.open_linux_help_reader(app) is None
