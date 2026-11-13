"""Synthetic stdin verdicts cannot authorize actions on a different file."""

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from netmon import app as app_module
from netmon.core import download_scan_fs as dfs, quarantine_fs as qfs
from netmon.features import clamav_controller as controller

CONTROLS = ["\r", "\n", "\t", "\x1b", "\x7f", "\x85", "\u2028", "\u2029", "\0"]


@pytest.mark.parametrize("control", CONTROLS)
@pytest.mark.parametrize("position", ["parent", "leaf"])
def test_scan_path_rejects_control_characters_before_open(
    tmp_path, monkeypatch, control, position
):
    path = (
        tmp_path
        / ("parent" + (control if position == "parent" else ""))
        / ("file" + (control if position == "leaf" else ""))
    )
    monkeypatch.setattr(
        dfs.os, "open", lambda *a, **k: pytest.fail("unsafe path was opened")
    )
    with pytest.raises(dfs.UnsafePath, match="Steuerzeichen"):
        dfs.open_scan_file(str(path))


@pytest.mark.parametrize("kind", ["file", "temp_folder"])
@pytest.mark.parametrize("control", CONTROLS)
def test_ui_refuses_unsafe_selected_paths_before_scan(
    tmp_path, monkeypatch, kind, control
):
    app = app_module.App.__new__(app_module.App)
    app.tr = lambda _key, fallback: fallback
    errors = []
    monkeypatch.setattr(
        app_module.messagebox,
        "showerror",
        lambda title, text, **kw: errors.append(text),
    )
    monkeypatch.setattr(
        app_module.os.path,
        "exists",
        lambda *a: pytest.fail("unsafe target reached scan preparation"),
    )
    app._run_download_scan(str(tmp_path / ("bad" + control + "name")), target_kind=kind)
    assert len(errors) == 1 and "Steuerzeichen" in errors[0]


@pytest.fixture
def scan_app(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir(mode=0o700)
    monkeypatch.setenv("HOME", str(home))
    app = app_module.App.__new__(app_module.App)
    app.security_clamav_running = False
    app.tr = lambda _key, fallback: fallback
    app._download_scan_clamav_available = lambda: True
    app.statuses, app.messages, app.reports, app.clamav_findings = [], [], [], []
    app._set_download_scan_status = lambda **kw: app.statuses.append(kw)
    app._update_download_scan_result_text = app.messages.append
    app._clamav_progress_start = lambda **kw: None
    app._clamav_progress_update_safe = lambda *_: None
    app._clamav_progress_finish_safe = lambda: None
    app._clamav_database_args = lambda: []
    app._clamav_parse_infected_count = controller.clamav_parse_infected_count
    app._clamav_parse_scanned_files = controller.clamav_parse_scanned_files
    app._clamav_allows_nonfatal_scan_completion = (
        controller.clamav_allows_nonfatal_scan_completion
    )
    app._clamav_extract_error_message = controller.clamav_extract_error_message
    app._clamav_extract_findings = lambda *a, **kw: pytest.fail(
        "single-file verdict reparsed as paths"
    )
    app._clamav_replace_open_findings = lambda findings: setattr(
        app, "clamav_findings", findings
    )
    app._download_scan_write_report = (
        lambda kind, text: app.reports.append(text) or "synthetic-report"
    )
    app._download_scan_maybe_move_clean_file = lambda *a: pytest.fail(
        "infected file released as clean"
    )
    app.clamav_quarantine_dir = str(home / ".quarantine")
    app._clamav_next_quarantine_path = lambda source: str(
        home / ".quarantine" / (Path(source).name + ".quarantined")
    )
    app.log_safe = lambda *_: None

    class InlineThread:
        def __init__(self, target, **kw):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module, "threading", SimpleNamespace(Thread=InlineThread))
    return app, home


def test_real_newline_path_cannot_forge_victim_finding(scan_app, monkeypatch):
    app, home = scan_app
    victim = home / "victim"
    victim.write_bytes(b"benign victim")
    source = home / ("detected\n" + str(victim))
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic detected source")
    errors = []
    app._run_clamscan_with_cancel = lambda *a, **kw: pytest.fail(
        "newline path reached scanner"
    )
    monkeypatch.setattr(
        app_module.messagebox, "showerror", lambda *a, **kw: errors.append(True)
    )
    app._run_download_scan(str(source), target_kind="file")
    assert errors == [True]
    assert app.clamav_findings == []
    assert victim.read_bytes() == b"benign victim"


def test_finding_is_bound_to_opened_file_even_without_path_filter(
    scan_app, monkeypatch
):
    app, home = scan_app
    victim = home / "victim"
    victim.write_bytes(b"benign victim")
    source = home / ("detected\n" + str(victim))
    source.parent.mkdir(parents=True)
    source.write_bytes(b"synthetic detected source")
    # Exercise the structural binding independently of the first-line defense.
    monkeypatch.setattr(dfs, "validate_scan_path", lambda path: None)
    app._run_clamscan_with_cancel = lambda *a, **kw: (
        1,
        "stdin: Synthetic.Test FOUND\nInfected files: 1\n",
        False,
    )
    app._run_download_scan(str(source), target_kind="file")
    assert len(app.clamav_findings) == 1
    item = app.clamav_findings[0]
    assert item["path"] == str(source)
    assert item["identity"] == qfs.file_identity(source.stat())
    assert controller.clamav_quarantine_item(app, item) == "moved"
    assert not source.exists()
    assert victim.read_bytes() == b"benign victim"
    assert Path(item["quarantine_path"]).read_bytes() == b"synthetic detected source"


def test_unrelated_output_paths_never_become_single_file_findings(
    scan_app, monkeypatch
):
    app, home = scan_app
    source, victim = home / "detected.bin", home / "victim"
    source.write_bytes(b"synthetic detected source")
    victim.write_bytes(b"benign victim")

    def scan(command, *, stdin_fd, **kw):
        assert command[-1] == "-"
        assert os.read(stdin_fd, 1024) == b"synthetic detected source"
        return (
            1,
            f"{victim}: Forged FOUND\nstdin: Real.Signature FOUND\nInfected files: 1\n",
            False,
        )

    app._run_clamscan_with_cancel = scan
    monkeypatch.setattr(
        qfs,
        "record_identity",
        lambda *a: pytest.fail("untrusted path identity captured"),
    )
    app._run_download_scan(str(source), target_kind="file")
    assert [item["path"] for item in app.clamav_findings] == [str(source)]
    assert app.clamav_findings[0]["signature"] == "Real.Signature"
    assert controller.clamav_quarantine_item(app, app.clamav_findings[0]) == "moved"
    assert victim.read_bytes() == b"benign victim"


@pytest.mark.parametrize("change", ["replacement", "in-place", "symlink"])
def test_identity_change_cannot_create_a_new_binding(tmp_path, change):
    source = tmp_path / "source"
    source.write_bytes(b"scanned bytes")
    replacement = tmp_path / "replacement"
    replacement.write_bytes(b"changed bytes")
    with dfs.open_scan_file(str(source)) as scanned:
        if change == "replacement":
            replacement.replace(source)
        elif change == "symlink":
            source.unlink()
            source.symlink_to(replacement)
        else:
            source.write_bytes(b"changed bytes")
        with pytest.raises(dfs.UnsafePath):
            controller.clamav_single_file_findings(
                "stdin: Test FOUND\n", scanned, "file", "now"
            )


def test_multiple_stdin_signatures_are_one_file_finding(tmp_path):
    source = tmp_path / "source: with spaces"
    source.write_bytes(b"scanned bytes")
    with dfs.open_scan_file(str(source)) as scanned:
        items = controller.clamav_single_file_findings(
            "stdin: A FOUND\nstdin: B FOUND\nstdin: A FOUND\n", scanned, "file", "now"
        )
    assert len(items) == 1 and items[0]["path"] == str(source)
    assert items[0]["signature"] == "A | B"


def test_detected_return_code_cannot_release_file_with_missing_stdin_record(scan_app):
    app, home = scan_app
    source = home / "source"
    source.write_bytes(b"scanned bytes")
    app._run_clamscan_with_cancel = lambda *a, **kw: (1, "Infected files: 0\n", False)
    app._run_download_scan(str(source), target_kind="file")
    assert app.statuses[-1]["status"] == "🔴 finding / suspicious"
    assert not app.clamav_findings
    assert source.read_bytes() == b"scanned bytes"
