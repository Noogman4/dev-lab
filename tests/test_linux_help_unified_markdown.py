"""One list for bundled and personal Markdown, including editing and collisions."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_library_service as store
from netmon.services import linux_help_markdown_service as bundled
from netmon.services.linux_help_library_markdown import format_entry_markdown
from netmon.services.linux_help_reading_service import ReadingState

ROOT = Path(__file__).resolve().parents[1]
COMMAND = {
    "id": "ls",
    "entry_type": "command",
    "name": "ls",
    "cmd": "ls",
    "category": "Dateien",
    "risk": "safe",
    "info": "Dateien zeigen",
}


@pytest.fixture
def app(tmp_path, monkeypatch):
    root = tk.Tk()
    root.geometry("1050x800")
    directory = tmp_path / "NetMon"
    directory.mkdir(mode=0o700)

    def subdir(*parts):
        path = directory.joinpath(*parts)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(store, "get_netmon_documents_subdir", subdir)
    monkeypatch.setattr(
        controller, "confirm_linux_help_import_category", lambda _app, raw: dict(raw)
    )
    root.tr = lambda key, fallback: fallback
    root.linux_help_data_path = subdir("Config") + "/commands.json"
    root.linux_help_glossary_path = subdir("Config") + "/glossary.json"
    root.linux_help_glossary_seed_path = ""
    root.linux_help_data = []
    root.linux_help_glossary = []
    Path(root.linux_help_data_path).write_text("[]")
    Path(root.linux_help_glossary_path).write_text('{"entries":[]}')
    for name in ("category", "source", "risk_filter", "search", "status"):
        setattr(root, "linux_help_" + name + "_var", tk.StringVar(master=root))
    root.linux_help_bookmarks_only_var = tk.BooleanVar(master=root)
    root.linux_help_reading_state = ReadingState(directory / "LinuxHelp/reading.json")
    root.linux_help_tree = ttk.Treeview(
        root,
        columns=("category", "source", "risk", "root", "tags", "summary", "reading"),
    )
    root.linux_help_tree.pack(fill="both", expand=True)
    controller.rebuild_linux_help_indexes(root)
    controller.rebuild_linux_help_glossary_indexes(root)
    yield root
    root.destroy()


def entry(app, raw):
    normalize = (
        controller.normalize_linux_help_glossary_entry
        if raw.get("entry_type") == "glossary"
        else controller.normalize_linux_help_entry
    )
    return normalize(app, raw)


def test_personal_markdown_survives_reload_and_opens_from_same_list(app):
    item = entry(
        app, {"id": "my_note", "name": "Meine Notiz", "cmd": "", "category": "Eigene"}
    )
    saved = controller.save_entry_markdown(app, item, "# Meine Notiz\n\nNur Text.\n")
    controller.load_linux_help_data(app)
    restored = controller.get_linux_help_command_by_id(app, saved["id"])
    assert restored["markdown_id"] == saved["markdown_id"]
    assert restored["cmd"] == ""
    assert controller.load_entry_document(restored).blocks[0].text == "Meine Notiz"
    assert len(app.linux_help_data) == 1
    controller._show_saved_entry(app, restored)
    window = controller.open_linux_help_reader(app)
    assert window.reader.document.metadata["name"] == "Meine Notiz"
    assert window.entry["id"] == saved["id"]


def test_editing_bundled_command_creates_personal_override_without_touching_source(app):
    source = bundled.DOCUMENT_DIR / "ls.md"
    original = source.read_bytes()
    base = entry(app, COMMAND)
    app.linux_help_data = [base]
    saved = controller.save_entry_markdown(
        app, base, "# Meine ls-Erklärung\n\nGeändert.\n", target=base
    )
    assert len(app.linux_help_data) == 1
    assert source.read_bytes() == original
    assert controller.load_entry_document(saved).blocks[0].text == "Meine ls-Erklärung"
    controller.load_linux_help_data(app)
    assert (
        controller.get_linux_help_command_by_id(app, "ls")["markdown_id"]
        == saved["markdown_id"]
    )


def test_personal_glossary_survives_serialization_without_command_fields(app):
    item = entry(
        app,
        {
            "id": "my_term",
            "entry_type": "glossary",
            "name": "Mein Begriff",
            "tags": ["eigene"],
            "related": ["Variable"],
        },
    )
    saved = controller.save_entry_markdown(app, item, "# Mein Begriff\n\nErklärung.\n")
    controller.load_linux_help_data(app)
    restored = controller.get_linux_help_command_by_id(app, "my_term")
    assert restored["markdown_id"] == saved["markdown_id"]
    doc = controller.load_entry_document(restored)
    assert doc.metadata["entry_type"] == "glossary"
    assert not {"command", "root_required", "risk_level"} & doc.metadata.keys()
    assert len(app.linux_help_glossary) == 1


def test_failed_entry_save_keeps_old_revision_and_original_entry(app, monkeypatch):
    first = controller.save_entry_markdown(
        app, entry(app, COMMAND), "# Erste Fassung\n"
    )
    before = Path(app.linux_help_data_path).read_bytes()
    old_path = Path(
        store.get_linux_help_document_by_id(first["markdown_id"])["markdown_path"]
    )
    old = old_path.read_bytes()
    monkeypatch.setattr(
        controller, "safe_write_json", lambda *_a, **_k: (False, "write failure")
    )
    with pytest.raises(OSError):
        controller.save_entry_markdown(
            app, dict(first, name="Neu"), "# Zweite Fassung\n", target=first
        )
    assert app.linux_help_data == [first]
    assert Path(app.linux_help_data_path).read_bytes() == before
    assert old_path.read_bytes() == old
    assert [item["id"] for item in store.list_linux_help_documents()] == [
        first["markdown_id"]
    ]


@pytest.mark.parametrize("choice,count", [(True, 1), (False, 2), (None, 1)])
def test_import_duplicate_requires_update_new_or_cancel(
    app, tmp_path, monkeypatch, choice, count
):
    original = entry(app, COMMAND)
    app.linux_help_data = [original]
    source = tmp_path / "ls.md"
    source.write_text(
        format_entry_markdown(original, "# Neue Dokumentation\n\nDetails.\n")
    )
    monkeypatch.setattr(
        controller,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **_k: str(source)),
    )
    requests = []
    monkeypatch.setattr(
        controller,
        "messagebox",
        SimpleNamespace(askyesnocancel=lambda *a, **kw: requests.append(a) or choice),
    )
    result = controller.import_linux_help_markdown_dialog(app)
    assert requests
    assert len(app.linux_help_data) == count
    if choice is None:
        assert result is None
        assert not store.list_linux_help_documents()
    else:
        assert result["id"] == ("ls" if choice else "ls_2")
        assert (
            controller.load_entry_document(result).blocks[0].text
            == "Neue Dokumentation"
        )
        if not choice:
            assert app.linux_help_data[0] is original


def test_plain_markdown_title_is_visible_and_code_never_runs(
    app, tmp_path, monkeypatch
):
    source = tmp_path / "random-filename.md"
    source.write_text(
        "# Meine Anleitung\n\nBeschreibung.\n\n```sh\nfalse; $(false)\n```\n"
    )
    monkeypatch.setattr(
        controller,
        "filedialog",
        SimpleNamespace(askopenfilename=lambda **_k: str(source)),
    )
    import netmon.ui.linux_help_reader as ui

    monkeypatch.setattr(
        ui.subprocess, "Popen", lambda *_a, **_k: pytest.fail("Imported code executed")
    )
    saved = controller.import_linux_help_markdown_dialog(app)
    assert saved["name"] == "Meine Anleitung"
    assert saved["cmd"] == ""
    assert saved["info"] == "Beschreibung."
    window = controller.open_linux_help_reader(app)
    window.reader.code_buttons[0].invoke()
    assert app.clipboard_get() == "false; $(false)"


def test_previous_markdown_library_is_adopted_once_but_pdf_is_ignored(app, tmp_path):
    source = tmp_path / "old.md"
    source.write_text("# Bisherige Anleitung\n")
    metadata = store.import_linux_help_markdown(source)
    legacy = {
        "entry_type": "document",
        "id": metadata["id"],
        "name": metadata["title"],
        "cmd": "",
    }
    app.linux_help_reading_state.change(
        legacy, read=True, bookmark={"tab": "documentation", "position": 0.3}
    )
    Path(store.linux_help_meta_dir(), "old_pdf.json").write_text(
        json.dumps({"id": "old_pdf", "pdf_path": "/unused.pdf"})
    )
    controller.load_linux_help_data(app)
    assert len(app.linux_help_data) == 1
    saved = app.linux_help_data[0]
    assert saved["markdown_id"] == metadata["id"]
    assert app.linux_help_reading_state.get(saved) == {
        "read": True,
        "bookmark": {"tab": "documentation", "position": 0.3},
    }
    controller.load_linux_help_data(app)
    assert len(app.linux_help_data) == 1
    assert (
        controller.load_entry_document(app.linux_help_data[0]).blocks[0].text
        == "Bisherige Anleitung"
    )


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_editor_changes_actual_markdown_and_updates_open_reader(
    app, monkeypatch, theme
):
    from netmon.app import App, DARK_THEME, LIGHT_THEME

    palette = DARK_THEME if theme == "dark" else LIGHT_THEME
    app.style = ttk.Style(app)
    app._app_theme = palette
    app._ensure_colorable_ttk_theme = lambda: App._ensure_colorable_ttk_theme(app)
    app._apply_tk_widget_theme = lambda widget, colors: App._apply_tk_widget_theme(
        app, widget, colors
    )
    App._apply_ttk_theme(app, palette)
    saved = controller.save_entry_markdown(
        app, entry(app, COMMAND), "# Ursprünglich\n\nAlt.\n"
    )
    controller._show_saved_entry(app, saved)
    window = controller.open_linux_help_reader(app)
    monkeypatch.setattr(
        controller,
        "messagebox",
        SimpleNamespace(showerror=lambda *a, **kw: pytest.fail(str(a))),
    )
    dialog = controller.open_linux_help_entry_dialog(app, item=saved)
    app.update()
    assert dialog.markdown_text.get("1.0", "end-1c").startswith("# Ursprünglich")
    assert dialog.markdown_text.cget("background") == palette["text_bg"]
    assert dialog.markdown_text.cget("foreground") == palette["text_fg"]
    if os.environ.get("NETMON_TEST_ISOLATED") == "1":
        from PIL import ImageGrab

        dialog.geometry("1000x780+0+0")
        app.update()
        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
            f"/work/linux-help-markdown-editor-{theme}.png"
        )
    dialog.markdown_text.delete("1.0", "end")
    dialog.markdown_text.insert("1.0", "# Bearbeitet\n\nNeuer Text.\n")
    dialog.save_button.invoke()
    app.update()
    assert not dialog.winfo_exists()
    assert (
        controller.load_entry_document(app.linux_help_data[0]).blocks[0].text
        == "Bearbeitet"
    )
    assert window.reader.document.blocks[0].text == "Bearbeitet"
    controller.load_linux_help_data(app)
    assert (
        controller.load_entry_document(app.linux_help_data[0]).blocks[0].text
        == "Bearbeitet"
    )


def test_delete_removes_only_own_managed_revision(app, monkeypatch, tmp_path):
    original = (bundled.DOCUMENT_DIR / "ls.md").read_bytes()
    saved = controller.save_entry_markdown(
        app, entry(app, COMMAND), "# Eigene Version\n"
    )
    app.linux_help_selected_id = saved["id"]
    outside = tmp_path / "keep.md"
    outside.write_text("keep")
    metadata = store.get_linux_help_document_by_id(saved["markdown_id"])
    metadata["markdown_path"] = str(outside)
    Path(metadata["json_path"]).write_text(json.dumps(metadata))
    monkeypatch.setattr(
        controller, "messagebox", SimpleNamespace(askyesno=lambda *_a, **_k: True)
    )
    controller.linux_help_delete_selected(app)
    assert app.linux_help_data == []
    assert not store.list_linux_help_documents()
    assert outside.read_text() == "keep"
    assert (bundled.DOCUMENT_DIR / "ls.md").read_bytes() == original
    controller.load_linux_help_data(app)
    assert app.linux_help_data == []


def test_new_entry_editor_saves_markdown_instead_of_only_short_info(app, monkeypatch):
    raw = entry(
        app, {"name": "Mein Befehl", "cmd": "printf test", "category": "Eigene"}
    )
    dialog = controller.open_linux_help_entry_dialog(app, item=raw, is_new=True)
    dialog.markdown_text.delete("1.0", "end")
    dialog.markdown_text.insert("1.0", "# Selbst geschrieben\n\nEin neuer Text.\n")
    dialog.save_button.invoke()
    assert len(app.linux_help_data) == 1
    assert (
        controller.load_entry_document(app.linux_help_data[0]).blocks[0].text
        == "Selbst geschrieben"
    )


def test_missing_personal_metadata_does_not_prevent_removing_the_entry(
    app, monkeypatch
):
    saved = controller.save_entry_markdown(
        app, entry(app, COMMAND), "# Eigene Fassung\n"
    )
    metadata = store.get_linux_help_document_by_id(saved["markdown_id"])
    Path(metadata["json_path"]).unlink()
    app.linux_help_selected_id = saved["id"]
    monkeypatch.setattr(
        controller, "messagebox", SimpleNamespace(askyesno=lambda *_a, **_k: True)
    )
    controller.linux_help_delete_selected(app)
    assert app.linux_help_data == []
    assert json.loads(Path(app.linux_help_data_path).read_text()) == []
