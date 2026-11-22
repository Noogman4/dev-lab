"""Personal Markdown stays passive, bounded, portable and separate from commands."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk

import pytest

from netmon.core.utils import protect_user_json_writes
from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_library_service as library
from netmon.services import linux_help_prompt_service as prompts
from netmon.services.linux_help_markdown_service import MAX_BYTES
from netmon.services.linux_help_reading_service import ReadingState


@pytest.fixture
def storage(tmp_path, monkeypatch):
    base = tmp_path / "NetMon"

    def subdir(*parts):
        path = base.joinpath(*parts)
        path.mkdir(mode=0o700, parents=True, exist_ok=True)
        return str(path)

    monkeypatch.setattr(library, "get_netmon_documents_subdir", subdir)
    return base


def imported(
    tmp_path, text="# Eigene Hilfe\n\n```sh\nprintf '%s' 'Grüße; $(false)'\n```\n"
):
    path = tmp_path / "Hilfe.md"
    path.write_text(text, encoding="utf-8")
    return library.import_linux_help_markdown(path)


def test_import_preserves_source_and_code_and_uses_unique_library_ids(
    storage, tmp_path
):
    first = imported(tmp_path)
    second = library.import_linux_help_markdown(tmp_path / "Hilfe.md")
    assert first["id"] != second["id"]
    assert (
        Path(first["markdown_path"]).read_bytes()
        == (tmp_path / "Hilfe.md").read_bytes()
    )
    assert Path(first["markdown_path"]).stat().st_mode & 0o777 == 0o600
    document = library.load_linux_help_markdown(first)
    assert any(
        block.kind == "code" and "Grüße; $(false)" in block.text
        for block in document.blocks
    )
    assert {item["id"] for item in library.list_linux_help_documents()} == {
        first["id"],
        second["id"],
    }
    assert not list(storage.rglob("*.pdf"))


@pytest.mark.parametrize(
    "text", ["", "```sh\nmissing closing fence", "bad\x00text", "x" * (MAX_BYTES + 1)]
)
def test_invalid_markdown_is_rejected_without_bundle(storage, tmp_path, text):
    with pytest.raises(ValueError):
        imported(tmp_path, text)
    assert not list(storage.rglob("*.md"))
    assert not list(storage.rglob("*.json"))


def test_source_symlink_and_nonregular_source_are_rejected(storage, tmp_path):
    source = tmp_path / "real.md"
    source.write_text("# Text")
    link = tmp_path / "link.md"
    link.symlink_to(source)
    with pytest.raises(OSError):
        library.import_linux_help_markdown(link)
    pipe = tmp_path / "pipe.md"
    os.mkfifo(pipe)
    with pytest.raises(ValueError):
        library.import_linux_help_markdown(pipe)


def test_failed_metadata_write_leaves_original_and_no_partial_markdown(
    storage, tmp_path, monkeypatch
):
    monkeypatch.setattr(
        library, "safe_write_json", lambda *_a, **_k: (False, "test failure")
    )
    with pytest.raises(RuntimeError):
        imported(tmp_path)
    assert (tmp_path / "Hilfe.md").exists()
    assert not list(storage.rglob("*.md"))


def test_bad_metadata_entry_does_not_hide_valid_library_documents(storage, tmp_path):
    metadata = imported(tmp_path)
    bad = storage / "LinuxHelp/meta/123.json"
    bad.write_text('{"id":123}')
    assert [item["id"] for item in library.list_linux_help_documents()] == [
        metadata["id"]
    ]


def test_restore_freeze_blocks_new_document(storage, tmp_path):
    protect_user_json_writes(storage)
    try:
        with pytest.raises(PermissionError):
            imported(tmp_path)
    finally:
        protect_user_json_writes(storage, enabled=False)
    assert not list(storage.rglob("*.md"))


def test_paths_in_metadata_do_not_allow_open_or_delete_outside_library(
    storage, tmp_path
):
    metadata = imported(tmp_path)
    original = tmp_path / "personal.md"
    original.write_text("keep this")
    metadata["markdown_path"] = metadata["pdf_path"] = str(original)
    metadata["json_path"] = str(original)
    managed_meta = storage / "LinuxHelp/meta" / (metadata["id"] + ".json")
    managed_meta.write_text(json.dumps(metadata))
    assert library.load_linux_help_markdown(metadata).blocks[0].text == "Eigene Hilfe"
    result = library.delete_linux_help_document(metadata["id"])
    assert len(result["deleted"]) == 2
    assert original.read_text() == "keep this"


def test_managed_symlink_cannot_be_read_or_deleted(storage, tmp_path):
    metadata = imported(tmp_path)
    managed = Path(metadata["markdown_path"])
    managed.unlink()
    original = tmp_path / "personal.md"
    original.write_text("keep this")
    managed.symlink_to(original)
    with pytest.raises(ValueError):
        library.load_linux_help_markdown(metadata)
    with pytest.raises(ValueError):
        library.delete_linux_help_document(metadata["id"])
    assert original.read_text() == "keep this"
    assert Path(metadata["json_path"]).exists()


def test_pdf_metadata_is_ignored_and_pdf_import_is_not_available(storage, tmp_path):
    meta = storage / "LinuxHelp/meta"
    meta.mkdir(parents=True)
    (meta / "old.json").write_text(json.dumps({"id": "old", "pdf_path": "/unused.pdf"}))
    assert library.list_linux_help_documents() == []
    assert library.get_linux_help_document_by_id("old") is None
    assert not hasattr(library, "import_linux_help_pdf")


def test_markdown_prompt_preserves_example_and_never_requests_pdf():
    example = "printf '%s' '$(false); Grüße'"
    prompt = prompts.build_linux_help_markdown_prompt(
        {"name": "printf", "example": example}
    )
    assert example in prompt
    assert "Markdown" in prompt and "PDF" not in prompt
    assert not hasattr(prompts, "build_linux_help_pdf_prompt")


def test_markdown_opens_from_unified_list_and_keeps_progress(storage, tmp_path):
    if not os.environ.get("DISPLAY"):
        pytest.skip("Xvfb required")
    root = tk.Tk()
    try:
        from tkinter import ttk

        app = SimpleNamespace(
            linux_help_tree=ttk.Treeview(root),
            linux_help_selected_id="own",
            linux_help_data_path=str(storage / "commands.json"),
            linux_help_data=[],
            linux_help_glossary_path=str(storage / "glossary.json"),
            linux_help_glossary=[],
            linux_help_status_var=tk.StringVar(master=root),
            linux_help_reading_state=ReadingState(tmp_path / "reading.json"),
            tr=lambda _k, fallback: fallback,
        )
        item = {
            "id": "own",
            "name": "Eigene Hilfe",
            "category": "Eigene",
            "cmd": "",
            "risk": "caution",
        }
        saved = controller.save_entry_markdown(
            app, item, "# Eigene Hilfe\n\n```sh\nprintf '%s' 'Grüße'\n```\n"
        )
        app.linux_help_tree.insert("", "end", iid="own")
        window = controller.open_linux_help_reader(app)
        root.update()
        assert window.entry["id"] == "own"
        assert window.notebook.select() == str(window.reader)
        window.bookmark_button.invoke()
        state = ReadingState(tmp_path / "reading.json").get(saved)
        assert state["read"] and state["bookmark"]["tab"] == "documentation"
        window.destroy()
        replacement = controller.open_linux_help_reader(app)
        assert replacement.reading_state == state
    finally:
        root.destroy()
