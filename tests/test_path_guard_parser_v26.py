"""PATH parsing against private executable lookup and real isolated Tk widgets."""

import os
import subprocess

import pytest

from netmon.features import path_guard_controller as controller
from netmon.services.path_guard_service import PathGuardService
from tests import test_path_guard_review_ui_v24 as ui_fixtures
from tests import test_path_guard_review_v24 as review_fixtures

model = review_fixtures.model
ui = ui_fixtures.ui


@pytest.mark.parametrize(
    "raw,empty_indices",
    [
        ("", [0]),
        (":/usr/bin", [0]),
        ("/usr/bin:", [1]),
        ("/usr/bin::/bin", [1]),
        ("::", [0, 1, 2]),
        ("/usr/bin:/bin", []),
    ],
)
def test_empty_components_are_preserved_and_reported_high(
    tmp_path, monkeypatch, raw, empty_indices
):
    monkeypatch.setenv("PATH", raw)
    service = PathGuardService(tmp_path / "private" / "reviews.json")
    service.get_shell_profile_paths = lambda: []
    result = service.run_check()
    assert result["path_entries"] == raw.split(os.pathsep)
    empty = [r for r in result["path_findings"] if r["entry"] == ""]
    assert [r["index"] for r in empty] == empty_indices
    for row in empty:
        assert row["severity"] == "high"
        assert (
            "Leerer PATH-Eintrag verweist auf das aktuelle Verzeichnis."
            in row["issues"]
        )
        assert "PATH-Verzeichnis existiert nicht." not in row["issues"]
    if empty_indices:
        assert result["risk"] == "hoch"
        reviews = [r for r in result["review_items"] if r["target"] == ""]
        assert reviews and not any(r["can_accept"] or r["can_repair"] for r in reviews)


def test_unset_path_is_distinct_from_an_explicit_empty_path(monkeypatch):
    monkeypatch.delenv("PATH", raising=False)
    assert PathGuardService().get_current_path_entries() == []
    monkeypatch.setenv("PATH", "")
    assert PathGuardService().get_current_path_entries() == [""]


@pytest.mark.parametrize("raw", ["", ":/usr/bin", "/usr/bin:", "/usr/bin::/bin"])
def test_empty_component_matches_real_current_directory_lookup(
    tmp_path, monkeypatch, raw
):
    command = tmp_path / "netmon-v26-fixture-command"
    command.write_text("#!/bin/sh\nprintf 'current-directory-fixture'\n")
    command.chmod(0o700)
    monkeypatch.setenv("PATH", raw)
    service = PathGuardService()
    entries = service.get_current_path_entries()
    assert "" in entries
    result = subprocess.run(
        [command.name],
        cwd=tmp_path,
        env={"PATH": raw},
        text=True,
        capture_output=True,
        check=True,
        timeout=5,
    )
    assert result.stdout == "current-directory-fixture"
    assert any(
        r["entry"] == "" and r["severity"] == "high"
        for r in service.analyze_path_entries(entries)
    )


@pytest.mark.parametrize("name", ["bin ", " bin", " ", "bin\t", "bin ä"])
def test_whitespace_in_directory_names_matches_real_lookup(tmp_path, monkeypatch, name):
    target = tmp_path / name
    target.mkdir()
    command = target / "netmon-v26-fixture-command"
    command.write_text("#!/bin/sh\nprintf 'literal-path-fixture'\n")
    command.chmod(0o700)
    monkeypatch.setenv("PATH", str(target))
    service = PathGuardService()
    assert service.get_current_path_entries() == [str(target)]
    assert service.analyze_path_entries(service.get_current_path_entries())[0]["exists"]
    result = subprocess.run(
        [command.name],
        env={"PATH": str(target)},
        text=True,
        capture_output=True,
        check=True,
        timeout=5,
    )
    assert result.stdout == "literal-path-fixture"


def test_empty_component_turns_reviewed_gui_red_and_exports_explanation(ui, model):
    app, _dialogs = ui
    before = model.service.run_check()["review_items"][0]
    model.service.accept_finding(before["id"], before["fingerprint"])
    app.run_path_guard_check()
    assert app.colors[-1] == "green"
    model.paths.insert(0, "")
    app.run_path_guard_check()
    assert app.colors[-1] == "red"
    row = next(
        r for r in app.path_guard_last_result["review_items"] if r["target"] == ""
    )
    table = app.path_guard_findings_table
    table.selection_set(row["id"])
    controller.update_buttons(app)
    assert "aktuelles Verzeichnis" in table.item(row["id"], "values")[1]
    assert str(app.path_guard_review_buttons["accept"].cget("state")) == "disabled"
    assert str(app.path_guard_review_buttons["repair"].cget("state")) == "disabled"
    root = table.winfo_toplevel()
    app.clipboard_clear = root.clipboard_clear
    app.clipboard_append = root.clipboard_append
    assert controller.copy_prompt(app)
    assert "leerer Eintrag → aktuelles Verzeichnis" in root.clipboard_get()
    assert (
        "Leerer PATH-Eintrag verweist auf das aktuelle Verzeichnis."
        in root.clipboard_get()
    )
