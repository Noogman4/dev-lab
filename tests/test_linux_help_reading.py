"""Reading progress persists independently of catalogs; UI actions stay passive."""

import json
from pathlib import Path
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon.core.private_state import read_private_json, write_private_json
from netmon.features import linux_help_controller as controller
from netmon.services.linux_help_reading_service import ReadingState, entry_key

ENTRY = {"id": "7z", "name": "7z", "cmd": "7z", "risk": "safe"}
OTHER = {"id": "ls", "name": "ls", "cmd": "ls", "risk": "safe"}
BOOKMARK = {"tab": "documentation", "position": 0.4}


def test_progress_survives_restart_without_transferring_to_changed_command(tmp_path):
    path = tmp_path / "reading.json"
    state = ReadingState(path)
    state.change(ENTRY, read=True, bookmark=BOOKMARK)
    reopened = ReadingState(path)
    assert reopened.get(ENTRY) == {"read": True, "bookmark": BOOKMARK}
    assert reopened.get(dict(ENTRY, cmd="7z x other.7z")) == {"read": False}
    assert reopened.get(dict(ENTRY, entry_type="glossary")) == {"read": False}
    assert path.stat().st_mode & 0o777 == 0o600
    assert "7z" not in path.read_text()


def test_separate_instances_preserve_updates_and_reset_retains_bookmarks(tmp_path):
    path = tmp_path / "reading.json"
    first, second = ReadingState(path), ReadingState(path)
    first.change(ENTRY, read=True, bookmark=BOOKMARK)
    second.change(OTHER, read=True)
    first.change(reset_read=True)
    restored = ReadingState(path)
    assert restored.get(ENTRY) == {"read": False, "bookmark": BOOKMARK}
    assert restored.get(OTHER) == {"read": False}
    restored.change(ENTRY, bookmark=None)
    assert read_private_json(path)["entries"] == {}


@pytest.mark.parametrize(
    "bookmark",
    [
        {},
        {"tab": [], "position": 0},
        {"tab": "other", "position": 0},
        {"tab": "documentation", "position": -0.1},
        {"tab": "documentation", "position": 1.1},
        {"tab": "documentation", "position": True},
        {"tab": "documentation", "position": float("nan")},
    ],
)
def test_invalid_bookmark_does_not_replace_saved_progress(tmp_path, bookmark):
    path = tmp_path / "reading.json"
    state = ReadingState(path)
    state.change(ENTRY, read=True)
    before = path.read_bytes()
    with pytest.raises(ValueError):
        state.change(ENTRY, bookmark=bookmark)
    assert path.read_bytes() == before
    assert state.get(ENTRY) == {"read": True}


@pytest.mark.parametrize(
    "name", ["reading.json", ".reading.json.lock", ".linux_help_reading_update.lock"]
)
def test_symlinked_state_or_lock_never_changes_target(tmp_path, name):
    target = tmp_path / "target"
    target.write_text("keep this")
    (tmp_path / name).symlink_to(target)
    state = ReadingState(tmp_path / "reading.json")
    with pytest.raises(OSError):
        state.change(ENTRY, read=True)
    assert target.read_text() == "keep this"
    assert (tmp_path / name).is_symlink()


@pytest.mark.parametrize(
    "payload",
    [
        '{"version":true,"entries":{}}',
        '{"version":1,"entries":[]}',
        "{broken",
        "x" * (128 * 1024 + 1),
    ],
)
def test_invalid_or_oversized_saved_state_is_not_silently_overwritten(
    tmp_path, payload
):
    path = tmp_path / "reading.json"
    path.write_text(payload)
    path.chmod(0o600)
    state = ReadingState(path)
    assert state.get(ENTRY) == {"read": False}
    with pytest.raises((ValueError, OSError)):
        state.change(ENTRY, read=True)
    assert path.read_text() == payload


def test_all_713_entries_can_have_progress_and_bookmarks_within_file_limit(tmp_path):
    path = tmp_path / "reading.json"
    state = ReadingState(path)
    records = [{"id": str(n), "name": str(n), "cmd": str(n)} for n in range(713)]
    payload = {
        "version": 1,
        "entries": {
            entry_key(item): {"read": True, "bookmark": BOOKMARK} for item in records
        },
    }
    write_private_json(path, payload)
    state = ReadingState(path)
    assert len(state.entries) == 713
    assert state.get(records[-1]) == {"read": True, "bookmark": BOOKMARK}
    state.change(records[-1], read=False)
    assert len(ReadingState(path).entries) == 713


@pytest.fixture
def root():
    window = tk.Tk()
    window.geometry("1100x800")
    yield window
    window.destroy()


def app_for(root, tmp_path):
    translations = json.loads(
        (Path(__file__).resolve().parents[1] / "netmon/lang/de.json").read_text()
    )
    tree = ttk.Treeview(
        root,
        columns=("category", "source", "risk", "root", "tags", "summary", "reading"),
    )
    tree.pack(fill="both", expand=True)
    app = SimpleNamespace(
        linux_help_tree=tree,
        linux_help_data=[
            dict(ENTRY, category="Archive", info="Archive"),
            dict(
                OTHER,
                category="Dateien",
                explanation="\n".join(f"Zeile {n}" for n in range(150)),
            ),
        ],
        linux_help_glossary=[],
        linux_help_reading_state=ReadingState(tmp_path / "reading.json"),
        tr=lambda key, fallback: translations.get(key, fallback),
        linux_help_bookmarks_only_var=tk.BooleanVar(master=root),
        linux_help_status_var=tk.StringVar(master=root),
    )
    controller.rebuild_linux_help_indexes(app)
    controller.refresh_linux_help_list(app)
    return app


def test_only_opening_marks_read_and_reused_reader_changes_the_right_entry(
    root, tmp_path, monkeypatch
):
    import netmon.ui.linux_help_reader as ui

    monkeypatch.setattr(
        ui.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("Reading started a process"),
    )
    app = app_for(root, tmp_path)
    app.linux_help_tree.selection_set("7z")
    controller.on_linux_help_select(app)
    assert not app.linux_help_reading_state.get(ENTRY)["read"]
    window = controller.open_linux_help_reader(app)
    root.update()
    assert "linux_help_read" in app.linux_help_tree.item("7z", "tags")
    assert app.linux_help_tree.set("7z", "reading") == "Gelesen"
    window.bookmark_button.invoke()
    before = app.linux_help_reading_state.get(ENTRY)
    app.linux_help_tree.selection_set("ls")
    assert controller.open_linux_help_reader(app) is window
    root.update()
    window.notebook.select(window.short_frame)
    window.short_info.yview_moveto(0.4)
    window.bookmark_button.invoke()
    window.read_button.invoke()
    assert app.linux_help_reading_state.get(ENTRY) == before
    assert app.linux_help_reading_state.get(OTHER)["bookmark"]["tab"] == "short_info"
    assert app.linux_help_tree.set("ls", "reading") == "★ · Ungelesen"
    assert "linux_help_read" not in app.linux_help_tree.item("ls", "tags")


def test_bookmark_restores_tab_and_position_after_window_recreation(root, tmp_path):
    app = app_for(root, tmp_path)
    app.linux_help_tree.selection_set("7z")
    window = controller.open_linux_help_reader(app)
    root.update()
    window.reader.text.yview_moveto(0.4)
    window.bookmark_button.invoke()
    position = app.linux_help_reading_state.get(ENTRY)["bookmark"]["position"]
    assert position > 0.2
    window.destroy()
    app.linux_help_reading_state = ReadingState(tmp_path / "reading.json")
    window = controller.open_linux_help_reader(app)
    root.update()
    window.notebook.select(window.short_frame)
    window.bookmark_jump_button.invoke()
    root.update()
    assert window.notebook.select() == str(window.reader)
    assert window.reader.text.yview()[0] == pytest.approx(position, abs=0.02)
    window.bookmark_remove_button.invoke()
    assert "bookmark" not in ReadingState(tmp_path / "reading.json").get(ENTRY)
    assert str(window.bookmark_jump_button.cget("state")) == "disabled"


def test_bookmark_filter_and_confirmed_reset_keep_bookmarks(
    root, tmp_path, monkeypatch
):
    app = app_for(root, tmp_path)
    app.linux_help_tree.selection_set("7z")
    window = controller.open_linux_help_reader(app)
    root.update()
    window.bookmark_button.invoke()
    controller.change_linux_help_reading(app, OTHER, read=True)
    app.linux_help_bookmarks_only_var.set(True)
    controller.refresh_linux_help_list(app)
    assert app.linux_help_tree.get_children() == ("7z",)
    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *_a, **_k: False)
    assert not controller.reset_linux_help_reading(app)
    assert app.linux_help_reading_state.get(ENTRY)["read"]
    monkeypatch.setattr(controller.messagebox, "askyesno", lambda *_a, **_k: True)
    assert controller.reset_linux_help_reading(app)
    assert not window.read_var.get()
    assert not app.linux_help_reading_state.get(OTHER)["read"]
    assert app.linux_help_reading_state.get(ENTRY)["bookmark"]
    assert app.linux_help_tree.set("7z", "reading") == "★ · Ungelesen"
    window.bookmark_remove_button.invoke()
    assert not app.linux_help_tree.get_children()
    controller.clear_linux_help_filters(app)
    assert set(app.linux_help_tree.get_children()) == {"7z", "ls"}


def test_failed_save_keeps_reader_usable_and_does_not_claim_progress(
    root, tmp_path, monkeypatch
):
    app = app_for(root, tmp_path)
    original = json.dumps(app.linux_help_data)

    def fail(*_a, **_k):
        raise PermissionError("Rejected state")

    monkeypatch.setattr(app.linux_help_reading_state, "change", fail)
    app.linux_help_tree.selection_set("7z")
    window = controller.open_linux_help_reader(app)
    assert not window.read_var.get()
    assert "nicht gespeichert" in window.reading_status.get()
    assert window.reader.document is not None
    window.read_button.invoke()
    assert not window.read_var.get()
    window.bookmark_button.invoke()
    assert "bookmark" not in window.reading_state
    assert json.dumps(app.linux_help_data) == original


def test_read_color_tracks_theme_without_changing_risk(root, tmp_path):
    app = app_for(root, tmp_path)
    controller.change_linux_help_reading(app, ENTRY, read=True)
    original_risk = app.linux_help_tree.set("7z", "risk")
    style = ttk.Style(root)
    previous = style.lookup("Treeview", "background")
    colors = []
    try:
        for background in ("#ffffff", "#111418"):
            style.configure("Treeview", background=background)
            controller.style_linux_help_reading(app)
            colors.append(
                app.linux_help_tree.tag_configure("linux_help_read", "background")
            )
            assert app.linux_help_tree.set("7z", "risk") == original_risk
        assert colors[0] != colors[1]
    finally:
        style.configure("Treeview", background=previous)
