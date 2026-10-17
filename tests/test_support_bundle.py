import os
from datetime import datetime, timezone

from netmon.core import support_bundle


def test_support_package_path_uses_utc_style_timestamp(monkeypatch, tmp_path):
    monkeypatch.setattr(support_bundle, "support_packages_dir", lambda: str(tmp_path))

    path = support_bundle.support_package_path(
        moment=datetime(2026, 7, 20, 20, 33, 1, tzinfo=timezone.utc)
    )

    assert path == str(tmp_path / "netmon-support-20260720-203301.zip")


def test_support_bundle_inputs_filters_missing_and_duplicate_files(
    monkeypatch, tmp_path
):
    diagnostics_dir = tmp_path / "diagnostics"
    runtime_logs_dir = tmp_path / "runtime-logs"
    state_dir = tmp_path / "state"
    diagnostics_dir.mkdir()
    runtime_logs_dir.mkdir()
    (state_dir / "logs").mkdir(parents=True)

    report = diagnostics_dir / "netmon-report.json"
    report.write_text("{}", encoding="utf-8")
    crash_log = diagnostics_dir / "crash.log"
    crash_log.write_text("boom", encoding="utf-8")
    runtime_log = runtime_logs_dir / "runtime.log"
    runtime_log.write_text("runtime", encoding="utf-8")

    monkeypatch.setattr(
        support_bundle, "diagnostic_reports_dir", lambda: str(diagnostics_dir)
    )
    monkeypatch.setattr(
        support_bundle, "latest_diagnostic_report_path", lambda: str(report)
    )
    monkeypatch.setattr(
        support_bundle,
        "get_netmon_documents_subdir",
        lambda *_parts: str(runtime_logs_dir),
    )
    monkeypatch.setattr(support_bundle, "get_netmon_state_dir", lambda: str(state_dir))

    result = support_bundle.support_bundle_inputs()

    assert result == [
        os.path.abspath(report),
        os.path.abspath(crash_log),
        os.path.abspath(runtime_log),
    ]


def test_build_support_manifest_redacts_metadata(monkeypatch):
    monkeypatch.setattr(support_bundle, "current_os_label", lambda: "Test OS")
    monkeypatch.setattr(
        support_bundle,
        "diagnostic_system_info",
        lambda: {"home": "/home/sven/project", "token": "abc123"},
    )

    manifest = support_bundle.build_support_manifest(
        metadata={
            "email": "sven@example.invalid",
            "detail": "api_key=secret123",
        },
        files=["/tmp/report.json"],
    )

    assert manifest["os"] == "Test OS"
    assert manifest["system"]["home"] == "/home/[USER_REDACTED]/project"
    assert manifest["system"]["token"] == "abc123"
    assert manifest["metadata"]["email"] == "[EMAIL_REDACTED]"
    assert manifest["metadata"]["detail"] == "api_key=[REDACTED]"
    assert manifest["files"] == ["/tmp/report.json"]
