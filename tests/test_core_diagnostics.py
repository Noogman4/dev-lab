from datetime import datetime, timezone
from types import SimpleNamespace

from netmon.core import diagnostics


def test_diagnostic_report_path_sanitizes_kind(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Documents" / "NetMon"
    monkeypatch.setattr(diagnostics, "get_netmon_documents_dir", lambda: str(docs_dir))
    monkeypatch.setattr(
        diagnostics,
        "uuid4",
        lambda: SimpleNamespace(hex="abcdef1234567890"),
    )

    path = diagnostics.diagnostic_report_path(
        " Start Fehler / DNS? ",
        moment=datetime(2026, 7, 20, 20, 0, 0, tzinfo=timezone.utc),
    )

    assert path == str(
        docs_dir
        / "diagnostics"
        / "netmon-start-fehler-dns-20260720-200000-abcdef12.json"
    )


def test_latest_diagnostic_report_path_ignores_non_reports(monkeypatch, tmp_path):
    reports_dir = tmp_path / "diagnostics"
    reports_dir.mkdir()
    older = reports_dir / "netmon-startup-older.json"
    newer = reports_dir / "netmon-startup-newer.json"
    ignored_name = reports_dir / "other.json"
    ignored_dir = reports_dir / "netmon-directory.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")
    ignored_name.write_text("{}", encoding="utf-8")
    ignored_dir.mkdir()
    older.touch()
    newer.touch()
    monkeypatch.setattr(diagnostics, "diagnostic_reports_dir", lambda: str(reports_dir))
    monkeypatch.setattr(
        diagnostics.os.path,
        "getmtime",
        lambda path: 1 if str(path).endswith("older.json") else 2,
    )

    assert diagnostics.latest_diagnostic_report_path() == str(newer)


def test_redact_diagnostic_value_converts_tuple_to_redacted_list():
    value = {
        "items": (
            "contact sven@example.invalid",
            {"path": "/home/sven/project", "secret": "token=abc"},
        )
    }

    assert diagnostics.redact_diagnostic_value(value) == {
        "items": [
            "contact [EMAIL_REDACTED]",
            {"path": "/home/[USER_REDACTED]/project", "secret": "token=[REDACTED]"},
        ]
    }
