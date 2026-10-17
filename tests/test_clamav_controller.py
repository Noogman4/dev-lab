import json
from types import SimpleNamespace

from netmon.features import clamav_controller


class DummyVar:
    def __init__(self, value=None):
        self.value = value

    def set(self, value):
        self.value = value

    def get(self):
        return self.value


class DummyAfterApp(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.after_calls = []
        self.after_cancel_calls = []

    def after(self, delay, callback):
        self.after_calls.append((delay, callback))
        return f"after-{len(self.after_calls)}"

    def after_cancel(self, after_id):
        self.after_cancel_calls.append(after_id)


def test_clamav_runtime_state_reads_scan_fields():
    app = type(
        "DummyApp",
        (),
        {
            "clamav_scan_started_at": 12.5,
            "clamav_scanned_files": 42,
            "clamav_expected_files": 100,
        },
    )

    assert clamav_controller._clamav_runtime_state(app) == (12.5, 42, 100)


def test_clamav_progress_apply_updates_status_fields_for_known_total(monkeypatch):
    app = SimpleNamespace(
        clamav_scan_started_at=100.0,
        clamav_scanned_files=25,
        clamav_expected_files=100,
        security_clamav_running=True,
        clamav_runtime_var=DummyVar(),
        clamav_scanned_files_var=DummyVar(),
        clamav_speed_var=DummyVar(),
        clamav_eta_var=DummyVar(),
    )
    monkeypatch.setattr(clamav_controller.time, "time", lambda: 110.0)

    clamav_controller.clamav_progress_apply(app)

    assert app.clamav_runtime_var.get() == "00:10"
    assert app.clamav_scanned_files_var.get() == "25"
    assert app.clamav_speed_var.get() == "2.5 Dateien/s"
    assert app.clamav_eta_var.get() == "~30 s"


def test_clamav_progress_apply_handles_unknown_total_without_progress_ui(monkeypatch):
    app = SimpleNamespace(
        clamav_scan_started_at=100.0,
        clamav_scanned_files=0,
        clamav_expected_files=None,
        security_clamav_running=True,
        clamav_runtime_var=DummyVar(),
        clamav_scanned_files_var=DummyVar(),
        clamav_speed_var=DummyVar(),
        clamav_eta_var=DummyVar(),
    )
    monkeypatch.setattr(clamav_controller.time, "time", lambda: 130.0)

    clamav_controller.clamav_progress_apply(app)

    assert app.clamav_runtime_var.get() == "00:30"
    assert app.clamav_scanned_files_var.get() == "0"
    assert app.clamav_speed_var.get() == "-"
    assert app.clamav_eta_var.get() == "-"


def test_clamav_progress_start_schedules_periodic_tick(monkeypatch):
    app = DummyAfterApp(
        clamav_progress_after_id=None,
        clamav_scan_started_at=0.0,
        clamav_scanned_files=0,
        clamav_expected_files=None,
        security_clamav_running=True,
        clamav_runtime_var=DummyVar(),
        clamav_scanned_files_var=DummyVar(),
        clamav_speed_var=DummyVar(),
        clamav_eta_var=DummyVar(),
    )
    monkeypatch.setattr(clamav_controller.time, "time", lambda: 100.0)

    clamav_controller.clamav_progress_start(app)

    assert app.clamav_runtime_var.get() == "00:00"
    assert app.clamav_progress_after_id == "after-1"
    assert app.after_calls[0][0] == clamav_controller.CLAMAV_PROGRESS_TICK_MS


def test_clamav_progress_tick_reschedules_while_scan_running(monkeypatch):
    app = DummyAfterApp(
        clamav_progress_after_id="after-0",
        clamav_scan_started_at=100.0,
        clamav_scanned_files=0,
        clamav_expected_files=None,
        security_clamav_running=True,
        clamav_runtime_var=DummyVar(),
        clamav_scanned_files_var=DummyVar(),
        clamav_speed_var=DummyVar(),
        clamav_eta_var=DummyVar(),
    )
    monkeypatch.setattr(clamav_controller.time, "time", lambda: 101.0)

    clamav_controller.clamav_progress_tick(app)

    assert app.clamav_runtime_var.get() == "00:01"
    assert app.clamav_progress_after_id == "after-1"
    assert app.after_calls[0][0] == clamav_controller.CLAMAV_PROGRESS_TICK_MS


def test_clamav_progress_finish_resets_scan_runtime_state():
    app = SimpleNamespace(
        clamav_progress_after_id=None,
        clamav_scan_started_at=100.0,
        clamav_scanned_files=10,
        clamav_expected_files=20,
        security_clamav_running=False,
        clamav_runtime_var=DummyVar(),
        clamav_scanned_files_var=DummyVar(),
        clamav_speed_var=DummyVar(),
        clamav_eta_var=DummyVar(),
    )

    clamav_controller.clamav_progress_finish_safe(app)

    assert app.clamav_scan_started_at == 0.0
    assert app.clamav_expected_files is None
    assert app.clamav_eta_var.get() == "-"


def test_clamav_scan_failure_lines_include_error_details():
    output = "\n".join(
        [
            "LibClamAV Error: cli_loaddbdir(): No supported database files found",
            "ERROR: Can't open file or directory",
        ]
    )
    app = SimpleNamespace(tr=lambda _key, default: default)

    lines = clamav_controller.clamav_scan_failure_lines(
        app,
        "ClamAV-Schnellscan fehlgeschlagen.",
        "/tmp",
        0,
        2,
        output,
    )

    assert lines[:4] == [
        "ClamAV-Schnellscan fehlgeschlagen.",
        "Ziel: /tmp",
        "Dateien gescannt: 0",
        "Rückgabecode: 2",
    ]
    assert (
        "Details: LibClamAV Error: cli_loaddbdir(): No supported database files found"
        in lines
    )
    assert "ClamAV-Ausgabe:" in lines


def test_clamav_database_dir_has_signatures_detects_cvd_files(tmp_path):
    db_dir = tmp_path / "clamav-db"
    db_dir.mkdir()
    (db_dir / "daily.cvd").write_text("dummy", encoding="utf-8")

    assert clamav_controller.clamav_database_dir_has_signatures(str(db_dir)) is True


def test_clamav_user_database_dir_prefers_xdg_data_home(monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", "/tmp/netmon-xdg")

    assert (
        clamav_controller.clamav_user_database_dir()
        == "/tmp/netmon-xdg/netmon/clamav-db"
    )


def test_clamav_user_database_dir_falls_back_to_local_share(monkeypatch):
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    monkeypatch.setattr(
        clamav_controller.os.path,
        "expanduser",
        lambda path: "/home/tester" if path == "~tester" else path,
    )
    monkeypatch.setattr(clamav_controller.getpass, "getuser", lambda: "tester")

    assert (
        clamav_controller.clamav_user_database_dir()
        == "/home/tester/.local/share/netmon/clamav-db"
    )


def test_clamav_database_args_prefers_app_database_dir(tmp_path, monkeypatch):
    db_dir = tmp_path / "netmon-clamav-db"
    db_dir.mkdir()
    db_dir.chmod(0o700)
    (db_dir / "main.cld").write_text("dummy", encoding="utf-8")
    monkeypatch.setattr(
        clamav_controller,
        "clamav_user_database_dir",
        lambda: str(tmp_path / "unused-db"),
    )
    app = SimpleNamespace(clamav_database_dir=str(db_dir))

    assert clamav_controller.clamav_database_args(app) == ["--database", str(db_dir)]


def test_clamav_database_args_skips_insecure_user_database_dir(tmp_path, monkeypatch):
    insecure_db_dir = tmp_path / "insecure-db"
    insecure_db_dir.mkdir()
    insecure_db_dir.chmod(0o755)
    (insecure_db_dir / "main.cld").write_text("dummy", encoding="utf-8")

    secure_system_dir = tmp_path / "system-db"
    secure_system_dir.mkdir()
    (secure_system_dir / "daily.cvd").write_text("dummy", encoding="utf-8")

    monkeypatch.setattr(
        clamav_controller,
        "clamav_user_database_dir",
        lambda: str(insecure_db_dir),
    )

    original_has_signatures = clamav_controller.clamav_database_dir_has_signatures

    def fake_has_signatures(path):
        if path == "/var/lib/clamav":
            return True
        return original_has_signatures(path)

    monkeypatch.setattr(
        clamav_controller,
        "clamav_database_dir_has_signatures",
        fake_has_signatures,
    )
    app = SimpleNamespace(clamav_database_dir=str(insecure_db_dir))

    assert clamav_controller.clamav_database_args(app) == [
        "--database",
        "/var/lib/clamav",
    ]


def test_clamav_quick_excluded_roots_keeps_existing_heavy_dirs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    cache_dir = home / ".cache"
    trash_dir = home / ".local" / "share" / "Trash"
    steam_dir = home / ".steam"
    for path in (cache_dir, trash_dir, steam_dir):
        path.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        clamav_controller.os.path, "expanduser", lambda _path: str(home)
    )

    excluded = clamav_controller.clamav_quick_excluded_roots()

    assert str(cache_dir.resolve()) in excluded
    assert str(trash_dir.resolve()) in excluded
    assert str(steam_dir.resolve()) in excluded


def test_clamav_exclude_dir_args_escapes_paths():
    args = clamav_controller.clamav_exclude_dir_args(
        ["/tmp/a+b", "/tmp/a+b", "/tmp/space dir"]
    )

    assert args == [
        r"--exclude-dir=^/tmp/a\+b($|/)",
        r"--exclude-dir=^/tmp/space\ dir($|/)",
    ]


def test_clamav_quick_targets_for_app_uses_configured_defaults_and_custom_paths(
    tmp_path, monkeypatch
):
    home = tmp_path / "home"
    downloads = home / "Downloads"
    documents = home / "Dokumente"
    custom = tmp_path / "custom"
    downloads.mkdir(parents=True)
    documents.mkdir(parents=True)
    custom.mkdir(parents=True)
    monkeypatch.setattr(
        clamav_controller.os.path, "expanduser", lambda _path: str(home)
    )
    app = SimpleNamespace(
        settings={
            "clamav_quickscan_targets": ["downloads", "documents_de"],
            "clamav_quickscan_custom_paths": [str(custom)],
        },
        clamav_quickscan_target_ids=[],
        clamav_quickscan_custom_paths=[],
    )

    targets, used_fallback = clamav_controller.clamav_quick_targets_for_app(app)

    assert used_fallback is False
    assert targets == [
        str(downloads.resolve()),
        str(documents.resolve()),
        str(custom.resolve()),
    ]


def test_clamav_load_quickscan_config_uses_defaults_when_setting_missing():
    app = SimpleNamespace(settings={})

    target_ids, custom_paths = clamav_controller.clamav_load_quickscan_config(app)

    assert target_ids == clamav_controller.clamav_default_quick_target_ids()
    assert custom_paths == []


def test_clamav_nonfatal_completion_requires_scanned_files():
    output = "LibClamAV Error: cli_loaddbdir(): No supported database files found"

    assert clamav_controller.clamav_allows_nonfatal_scan_completion(output, 0) is False


def test_clamav_nonfatal_completion_allows_access_warnings_after_real_scan():
    output = "\n".join(
        [
            "/root/private: Can't open file or directory ERROR",
            "Scanned files: 12",
        ]
    )

    assert clamav_controller.clamav_allows_nonfatal_scan_completion(output, 12) is True


def test_clamav_summary_int_extracts_matching_label_value():
    output = "Scanned files: 12\nInfected files: 3\n"

    assert clamav_controller._clamav_summary_int(output, "Scanned files") == 12
    assert clamav_controller._clamav_summary_int(output, "Infected files") == 3


def test_clamav_summary_int_returns_none_for_invalid_or_missing_value():
    assert (
        clamav_controller._clamav_summary_int(
            "Scanned files: unknown\n", "Scanned files"
        )
        is None
    )
    assert (
        clamav_controller._clamav_summary_int("Infected files: 0\n", "Scanned files")
        is None
    )


def test_clamav_parse_infected_count_falls_back_to_found_lines():
    output = "/tmp/a: Eicar-Test-Signature FOUND\n/tmp/b: Other FOUND\n"

    assert clamav_controller.clamav_parse_infected_count(output) == 2


def test_load_clamav_findings_skips_invalid_entries_and_keeps_recent_300(tmp_path):
    findings_path = tmp_path / "clamav_findings.json"
    payload = [{"path": "", "signature": "skip"}]
    payload.extend(
        {
            "path": f"/tmp/file-{index}",
            "signature": f"Sig-{index}",
            "status": "found",
            "timestamp": f"2026-06-06 00:{index:02d}:00",
        }
        for index in range(305)
    )
    findings_path.write_text(json.dumps(payload), encoding="utf-8")

    app = type("DummyApp", (), {"clamav_findings_path": str(findings_path)})()
    app.clamav_findings = []
    app.log_debug = lambda _message: None

    clamav_controller.load_clamav_findings(app)

    assert len(app.clamav_findings) == 300
    assert app.clamav_findings[0]["path"] == "/tmp/file-5"
    assert app.clamav_findings[-1]["path"] == "/tmp/file-304"


def test_clamav_replace_open_findings_keeps_quarantine_history(tmp_path):
    findings_path = tmp_path / "clamav_findings.json"
    saved = []
    button_updates = []
    app = type("DummyApp", (), {"clamav_findings_path": str(findings_path)})()
    app.clamav_findings = [
        {
            "path": "/tmp/found-old",
            "status": "found",
            "signature": "Old",
            "timestamp": "2026-06-06 10:00:00",
        },
        {
            "path": "/tmp/quarantine",
            "status": "quarantine",
            "signature": "Kept",
            "timestamp": "2026-06-06 09:00:00",
            "quarantine_path": "/tmp/q/file",
        },
    ]
    app.log_debug = lambda _message: None

    original_save = clamav_controller.save_clamav_findings
    original_buttons = clamav_controller.update_clamav_findings_buttons_state_safe
    clamav_controller.save_clamav_findings = lambda current_app: saved.append(
        list(current_app.clamav_findings)
    )
    clamav_controller.update_clamav_findings_buttons_state_safe = (
        lambda current_app: button_updates.append(current_app)
    )
    try:
        clamav_controller.clamav_replace_open_findings(
            app,
            [
                {
                    "path": "/tmp/found-new",
                    "status": "found",
                    "signature": "New",
                    "timestamp": "2026-06-06 11:00:00",
                }
            ],
        )
    finally:
        clamav_controller.save_clamav_findings = original_save
        clamav_controller.update_clamav_findings_buttons_state_safe = original_buttons

    assert app.clamav_findings == [
        {
            "path": "/tmp/quarantine",
            "status": "quarantine",
            "signature": "Kept",
            "timestamp": "2026-06-06 09:00:00",
            "quarantine_path": "/tmp/q/file",
        },
        {
            "path": "/tmp/found-new",
            "status": "found",
            "signature": "New",
            "timestamp": "2026-06-06 11:00:00",
        },
    ]
    assert saved and saved[-1] == app.clamav_findings
    assert button_updates == [app]
