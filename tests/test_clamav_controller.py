import json

from netmon.features import clamav_controller


def test_clamav_runtime_state_reads_scan_fields():
    app = type(
        "DummyApp",
        (),
        {
            "clamav_scan_started_at": 12.5,
            "clamav_scanned_files": 42,
            "clamav_expected_files": 100,
        },
    )()

    assert clamav_controller._clamav_runtime_state(app) == (12.5, 42, 100)


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
