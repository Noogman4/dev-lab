"""One popup, a self-contained assignment and user-controlled import categories."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
from tkinter import ttk
from urllib.parse import urlsplit

import pytest

from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_prompt_service as prompts
from netmon.services import linux_help_markdown_service as markdown
from netmon.services import linux_help_library_service as store
from netmon.ui import linux_help_reader as reader_ui
from netmon.ui import linux_help_resources as resources_ui
from netmon.ui.linux_help_prompt import ImportCategoryDialog, MarkdownPromptWindow
from netmon.ui.linux_help_resources import LIBRARIES, PYTHON_LIBRARIES, REFERENCES
from netmon.ui.tabs.linux_help_tab import build_linux_help_tab
from tests.test_linux_help_unified_markdown import app as app, entry, COMMAND

REAL_CONFIRM = controller.confirm_linux_help_import_category
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("kind", ["command", "glossary"])
def test_prompt_contains_pilot_quality_exact_sections_and_locked_identity(kind):
    item = {
        **COMMAND,
        "id": "my_id",
        "entry_type": kind,
        "category": "Unsere Kategorie",
        "name": "Begriff" if kind == "glossary" else "ls",
    }
    text = prompts.build_linux_help_markdown_prompt(
        item, wishes="Bitte ein Beispiel für Einsteiger."
    )
    head = text[text.index("---\n") :]
    meta, _lines, _start = markdown._document_parts(head)
    assert meta["id"] == item["id"] and meta["name"] == item["name"]
    assert meta["category"] == "Unsere Kategorie"
    assert meta["entry_type"] == kind
    sections = (
        prompts.GLOSSARY_SECTIONS if kind == "glossary" else prompts.COMMAND_SECTIONS
    )
    assert [line for line in text.splitlines() if line.startswith("## ")] == [
        f"## {n}. {name}" for n, name in enumerate(sections, 1)
    ]
    for phrase in (
        "500–900",
        "Alltagsvergleich",
        "Grenzen",
        "Primärquellen",
        "zwei",
        "Versionsabhängigkeiten",
        "nicht ausgeführt",
        "Syntaxprüfung",
        "256 KiB",
        "32768",
        "JSON-kompatiblen",
        "Kategorie hat der Nutzer",
        "Bitte ein Beispiel",
    ):
        assert phrase.casefold() in text.casefold()
    assert "git " not in text.casefold() and "commit" not in text.casefold()
    assert "it_0011" not in text
    if kind == "glossary":
        assert not {"command", "root_required", "risk_level"} & meta.keys()


def test_command_prompt_sections_match_bundled_command_template():
    headings = [
        line.split(". ", 1)[1]
        for line in (ROOT / "docs/linux-befehlsdatenbank/7z.md")
        .read_text()
        .splitlines()
        if line.startswith("## ")
    ]
    assert list(prompts.COMMAND_SECTIONS) == headings


def test_requested_language_is_consistent_in_header_and_assignment():
    text = prompts.build_linux_help_markdown_prompt(COMMAND, language="en")
    meta, _lines, _start = markdown._document_parts(text[text.index("---\n") :])
    assert meta["language"] == "en"
    assert "Verständliches Englisch" in text
    assert "Ausgabe-Sprache: en" in text


@pytest.fixture
def built_linux_tab(app):
    app.linux_help_tree.destroy()
    app.tools_nb = ttk.Notebook(app)
    app.tools_nb.pack(fill="both", expand=True)
    for name in (
        "refresh_linux_help_list",
        "clear_linux_help_filters",
        "reload_linux_help_data",
        "linux_help_new_entry",
        "linux_help_edit_selected",
        "linux_help_delete_selected",
        "on_linux_help_select",
        "show_linux_help_tree_menu",
    ):
        setattr(app, name, lambda *_a, **_k: None)
    build_linux_help_tab(app)
    return app


def test_both_buttons_open_same_popup_and_keep_the_draft(built_linux_tab):
    app = built_linux_tab
    app.btn_linux_help_prompt_top.invoke()
    first = app.linux_help_prompt_window
    first.name_var.set("Mein Entwurf")
    app.btn_linux_help_prompt_bottom.invoke()
    assert app.linux_help_prompt_window is first
    assert first.name_var.get() == "Mein Entwurf"
    assert (
        len([w for w in app.winfo_children() if isinstance(w, MarkdownPromptWindow)])
        == 1
    )
    assert app.btn_linux_help_prompt_top.grid_info()["column"] == 1
    assert app.btn_linux_help_reset_reading.grid_info()["column"] == 2
    assert app.btn_linux_help_prompt_bottom.grid_info()["column"] == 1
    assert app.btn_linux_help_reload.grid_info()["column"] == 2
    first.close()
    app.btn_linux_help_prompt_top.invoke()
    assert app.linux_help_prompt_window is not first


def test_resources_popup_position_and_links(built_linux_tab, monkeypatch):
    app = built_linux_tab
    calls = []
    monkeypatch.setattr(
        resources_ui,
        "LIBRARIES",
        (*LIBRARIES, ("http_legacy", "Alte HTTP-Quelle", "http://example.com/")),
    )
    monkeypatch.setattr(
        app,
        "_open_url_with_xdg_open",
        lambda url: calls.append(url) or True,
        raising=False,
    )
    app.update()
    new = app.btn_linux_help_resources
    prompt = app.btn_linux_help_prompt_top
    assert new.cget("text") == "Benutzte Libraries"
    assert new.grid_info()["column"] == prompt.grid_info()["column"]
    assert new.grid_info()["row"] == prompt.grid_info()["row"] + 1
    assert new.winfo_width() == prompt.winfo_width()
    new.invoke()
    window = app.linux_help_resources_window
    new.invoke()
    assert app.linux_help_resources_window is window
    assert app.grab_current() is None and not calls
    notebook = window.winfo_children()[0]
    assert [notebook.tab(i, "text") for i in range(2)] == [
        "Verwendete Libraries",
        "IT und Linux",
    ]
    libraries_pane = notebook.nametowidget(notebook.tabs()[0]).winfo_children()[0]
    assert "Alte HTTP-Quelle" not in libraries_pane.get("1.0", "end")
    assert not libraries_pane.tag_ranges("http_legacy")

    def click_link(page, key):
        notebook.select(page)
        text = notebook.nametowidget(notebook.tabs()[page]).winfo_children()[0]
        assert text.cget("state") == "disabled"
        start = text.tag_ranges(key)[0]
        text.see(start)
        app.update()
        x, y, width, height = text.bbox(start)
        coordinates = {"x": x + width // 2, "y": y + height // 2}
        text.event_generate("<Motion>", **coordinates)
        text.event_generate("<Button-1>", **coordinates)

    click_link(0, "networkx")
    click_link(1, "linux_man")
    assert calls == ["https://networkx.org/", "https://man7.org/linux/man-pages/"]
    window.winfo_children()[-1].invoke()
    assert not window.winfo_exists()


def test_resource_links_are_unique_and_have_translated_descriptions():
    resources = (*LIBRARIES, *PYTHON_LIBRARIES, *REFERENCES)
    assert len({key for key, _, _ in resources}) == len(resources)
    assert len({url for _, _, url in resources}) == len(resources)
    for language in ("de", "en"):
        labels = json.loads((ROOT / f"netmon/lang/{language}.json").read_text())
        for key, name, url in resources:
            parsed = urlsplit(url)
            assert parsed.scheme == "https" and parsed.hostname
            assert parsed.username is None
            assert labels[f"linux_help_resource_{key}"] != name


def test_linux_components_popup_renders_both_distributions(
    built_linux_tab, monkeypatch
):
    app = built_linux_tab
    opened = []
    monkeypatch.setattr(
        reader_ui.subprocess, "Popen", lambda args, **kwargs: opened.append(args)
    )
    app.update()
    button = app.btn_linux_help_components
    reset = app.btn_linux_help_reset_reading
    assert button.grid_info()["column"] == reset.grid_info()["column"] == 2
    assert button.grid_info()["row"] == reset.grid_info()["row"] + 1
    assert button.winfo_width() == reset.winfo_width()
    button.invoke()
    window = app.linux_help_components_window
    # The window manager needs a normal, resizable window for both controls.
    assert not window.transient()
    assert window.resizable() == (1, 1)
    button.invoke()
    assert app.linux_help_components_window is window
    notebook = window.winfo_children()[0]
    assert [notebook.tab(i, "text") for i in range(2)] == ["Zorin", "Mint"]
    zorin, mint = [notebook.nametowidget(path) for path in notebook.tabs()]
    reader = zorin.winfo_children()[0]
    assert reader.text.cget("state") == "disabled"
    assert len(reader.headings) == 11
    assert sum(block.kind == "table" for block in reader.document.blocks) == 11
    assert len(reader.links) == 4
    assert not opened
    app.update()
    reader.query.set("Wayland")
    reader.find()
    assert reader.matches
    first, last, *_ = reader.text.tag_ranges("search_hit")
    assert reader.text.get(first, last) == "Wayland"
    reader.query.set("🟣")
    reader.find()
    first, last = reader.text.tag_ranges("search_hit")
    assert reader.text.get(first, last) == "🟣"
    assert not reader.open_link("file:///tmp/unknown")
    assert reader.open_link("https://zorin.com/os/details/")
    assert opened == [["/usr/bin/xdg-open", "https://zorin.com/os/details/"]]
    notebook.select(mint)
    app.update()
    mint_reader = mint.winfo_children()[0]
    assert mint_reader.text.cget("state") == "disabled"
    assert len(mint_reader.headings) == 11
    assert sum(block.kind == "table" for block in mint_reader.document.blocks) == 11
    assert len(mint_reader.links) == 8
    mint_reader.query.set("Cinnamon")
    mint_reader.find()
    first, last, *_ = mint_reader.text.tag_ranges("search_hit")
    assert mint_reader.text.get(first, last) == "Cinnamon"
    mint_link = (
        "https://linuxmint-developer-guide.readthedocs.io/en/latest/cinnamon.html"
    )
    assert not reader.open_link(mint_link)
    assert not mint_reader.open_link("https://zorin.com/os/details/")
    assert mint_reader.open_link(mint_link)
    assert opened[-1] == ["/usr/bin/xdg-open", mint_link]
    window.winfo_children()[-1].invoke()
    assert not window.winfo_exists()


def test_popup_copy_and_chad_use_the_same_assignment_without_execution(
    app, monkeypatch
):
    import netmon.ui.linux_help_reader as reader

    monkeypatch.setattr(
        reader.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("Popup started a process"),
    )
    delivered = []
    app.set_chad_direct_prompt = lambda title, prompt: delivered.append((title, prompt))
    window = controller.open_linux_help_prompt(app)
    window.name_var.set("printf")
    window.command_var.set("printf '%s' '$(false)' ; false")
    window.category_var.set("Unsere Kategorie")
    window.wishes_text.insert("1.0", "Bitte einfach erklären.")
    assert delivered == [] and app.linux_help_data == []
    assert window.build_prompt()
    app.update()
    expected = window.prompt
    assert expected and window.preview.get("1.0", "end-1c") == expected
    assert window.copy_prompt()
    assert app.clipboard_get() == expected
    assert window.to_chad()
    assert delivered == [("Markdown-Dokumentation: printf", expected)]
    assert app.linux_help_data == []
    assert store.list_linux_help_documents() == []


def test_changes_invalidate_preview_and_actions(app):
    window = controller.open_linux_help_prompt(app)
    window.name_var.set("ls")
    window.command_var.set("ls")
    window.category_var.set("Dateien")
    assert window.build_prompt()
    window.category_var.set("Neue Kategorie")
    assert window.prompt == "" and not window.copy_prompt() and not window.to_chad()
    assert str(window.chad_button.cget("state")) == "disabled"
    assert window.build_prompt()
    assert "Neue Kategorie" in window.prompt


def test_category_and_name_are_required_and_long_input_is_bounded(app):
    window = controller.open_linux_help_prompt(app)
    window.name_var.set("ls")
    window.command_var.set("ls")
    assert not window.build_prompt()
    window.category_var.set("Dateien")
    window.command_var.set("ls\npwd")
    assert not window.build_prompt()
    window.command_var.set("ls")
    window.name_var.set("x" * 257)
    assert not window.build_prompt()
    window.name_var.set("ls")
    window.wishes_text.insert("1.0", "x" * 8001)
    assert not window.build_prompt()
    assert app.linux_help_data == []


def test_take_selection_keeps_id_and_glossary_has_no_command_field(app):
    item = entry(
        app,
        {
            "id": "my_term",
            "entry_type": "glossary",
            "name": "Mein Begriff",
            "category": "Eigene",
        },
    )
    app.linux_help_glossary = [item]
    app.linux_help_tree.insert("", "end", iid=item["id"])
    app.linux_help_tree.selection_set(item["id"])
    window = controller.open_linux_help_prompt(app)
    assert window.take_selection()
    app.update()
    assert window.kind() == "glossary"
    assert not window.command_entry.winfo_ismapped()
    assert window.build_prompt()
    assert window.draft["id"] == "my_term"
    head = window.prompt[window.prompt.index("---\n") :]
    meta, _lines, _start = markdown._document_parts(head)
    assert meta["category"] == "Eigene" and meta["entry_type"] == "glossary"
    assert "command" not in meta


def test_take_selection_includes_existing_markdown_for_reworking(app):
    saved = controller.save_entry_markdown(
        app,
        entry(app, COMMAND),
        "# Meine bisherige Fassung\n\nEine eigene vorhandene Erklärung.\n",
    )
    controller._show_saved_entry(app, saved)
    window = controller.open_linux_help_prompt(app)
    assert window.take_selection()
    assert window.build_prompt()
    assert "Eine eigene vorhandene Erklärung." in window.prompt
    assert window.draft["id"] == saved["id"]


def test_import_category_is_shown_validated_and_user_can_override(app):
    raw = {
        "id": "note",
        "entry_type": "command",
        "name": "Meine Anleitung",
        "category": "Vom Modell",
    }
    results = []

    def choose():
        dialog = next(
            w for w in app.winfo_children() if isinstance(w, ImportCategoryDialog)
        )
        try:
            results.append(dialog.category_var.get())
            if os.environ.get("NETMON_TEST_ISOLATED") == "1":
                from PIL import ImageGrab

                dialog.deiconify()
                dialog.lift()
                dialog.update()
                x, y = dialog.winfo_rootx(), dialog.winfo_rooty()
                ImageGrab.grab(
                    bbox=(x, y, x + dialog.winfo_width(), y + dialog.winfo_height()),
                    xdisplay=os.environ["DISPLAY"],
                ).save("/work/md-import-category.png")
            dialog.category_var.set("")
            results.append(dialog.validate())
            dialog.category_var.set("Von uns festgelegt")
            dialog.ok()
        finally:
            if dialog.winfo_exists():
                dialog.cancel()

    app.after(30, choose)
    result = REAL_CONFIRM(app, raw)
    assert results == ["Vom Modell", False]
    assert result["category"] == "Von uns festgelegt"
    assert raw["category"] == "Vom Modell"


def test_import_uses_confirmed_category_in_list_and_saved_markdown(
    app, tmp_path, monkeypatch
):
    source = tmp_path / "note.md"
    source.write_text("# Meine Anleitung\n\nEin Text.\n")
    monkeypatch.setattr(
        controller,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **_k: str(source)),
    )
    seen = []

    def confirm(_app, raw):
        seen.append(dict(raw))
        return {**raw, "category": "Unsere neue Kategorie"}

    monkeypatch.setattr(controller, "confirm_linux_help_import_category", confirm)
    saved = controller.import_linux_help_markdown_dialog(app)
    assert seen and saved["category"] == "Unsere neue Kategorie"
    assert (
        controller.load_entry_document(saved).metadata["category"]
        == "Unsere neue Kategorie"
    )
    controller.load_linux_help_data(app)
    assert (
        controller.get_linux_help_command_by_id(app, saved["id"])["category"]
        == "Unsere neue Kategorie"
    )


def test_cancel_category_confirmation_stores_nothing(app, tmp_path, monkeypatch):
    source = tmp_path / "note.md"
    source.write_text("# Neue Anleitung\n")
    monkeypatch.setattr(
        controller,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **_k: str(source)),
    )
    monkeypatch.setattr(
        controller, "confirm_linux_help_import_category", lambda *_a: None
    )
    before = Path(app.linux_help_data_path).read_bytes()
    assert controller.import_linux_help_markdown_dialog(app) is None
    assert Path(app.linux_help_data_path).read_bytes() == before
    assert store.list_linux_help_documents() == []


def test_generated_header_can_be_imported_into_the_same_reader(
    app, tmp_path, monkeypatch
):
    window = controller.open_linux_help_prompt(app)
    window.name_var.set("Mein printf")
    window.command_var.set("printf '%s' 'Grüße'")
    window.category_var.set("Unsere Beispiele")
    assert window.build_prompt()
    start = window.prompt.index("---\n")
    end = window.prompt.index("\n---\n", start + 4) + len("\n---\n")
    source = tmp_path / "answer.md"
    source.write_text(window.prompt[start:end] + "# Mein printf\n\nEine Erklärung.\n")
    monkeypatch.setattr(
        controller,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **_kw: str(source)),
    )
    saved = controller.import_linux_help_markdown_dialog(app)
    assert saved["id"] == window.draft["id"]
    assert saved["category"] == "Unsere Beispiele"
    assert saved["cmd"] == "printf '%s' 'Grüße'"
    reader = controller.open_linux_help_reader(app)
    assert reader.reader.document.metadata["name"] == "Mein printf"
    assert reader.reader.document.metadata["category"] == "Unsere Beispiele"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_prompt_popup_uses_host_theme_and_fits_narrow_window(app, theme):
    from netmon.app import App, LIGHT_THEME, DARK_THEME

    palette = DARK_THEME if theme == "dark" else LIGHT_THEME
    translations = json.loads((ROOT / "netmon/lang/de.json").read_text())
    app.tr = lambda key, fallback: translations.get(key, fallback)
    app.style = ttk.Style(app)
    app._app_theme = palette
    app._ensure_colorable_ttk_theme = lambda: App._ensure_colorable_ttk_theme(app)
    app._apply_tk_widget_theme = lambda widget, colors: App._apply_tk_widget_theme(
        app, widget, colors
    )
    App._apply_ttk_theme(app, palette)
    window = controller.open_linux_help_prompt(app)
    window.name_var.set("rsync")
    window.command_var.set("rsync --help")
    window.category_var.set("Dateien")
    window.wishes_text.insert(
        "1.0", "Bitte mit einem einfachen Beispiel und klaren Erklärungen."
    )
    assert window.build_prompt()
    for geometry, suffix in [("900x800+0+0", "normal"), ("720x680+0+0", "narrow")]:
        window.geometry(geometry)
        app.update()
        assert window.prompt
        assert window.preview.cget("background") == palette["text_bg"]
        assert window.preview.winfo_height() > 100
        assert (
            window.copy_button.winfo_rootx() + window.copy_button.winfo_width()
            <= window.winfo_rootx() + window.winfo_width()
        )
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            from PIL import ImageGrab

            x, y = window.winfo_rootx(), window.winfo_rooty()
            ImageGrab.grab(
                bbox=(x, y, x + window.winfo_width(), y + window.winfo_height()),
                xdisplay=os.environ["DISPLAY"],
            ).save(f"/work/md-prompt-{theme}-{suffix}.png")
