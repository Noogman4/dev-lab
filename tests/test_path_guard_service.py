import os
import stat

from netmon.app import App
from netmon.services.path_guard_service import PathGuardService


def test_analyze_path_entries_flags_tmp_and_missing_and_dot(tmp_path):
    service = PathGuardService()
    safe_dir = tmp_path / "safe-bin"
    safe_dir.mkdir()
    missing_dir = "/definitely-missing-path-guard-dir"

    findings = service.analyze_path_entries(
        ["/tmp", ".", str(missing_dir), str(safe_dir)]
    )

    assert findings[0]["severity"] == "high"
    assert "Temporäres oder RAM-Verzeichnis im PATH." in findings[0]["issues"]
    assert findings[1]["severity"] == "high"
    assert "Aktuelles Verzeichnis '.' im PATH ist gefährlich." in findings[1]["issues"]
    assert findings[2]["severity"] == "medium"
    assert "PATH-Verzeichnis existiert nicht." in findings[2]["issues"]


def test_analyze_path_entries_flags_world_writable_directory(tmp_path):
    service = PathGuardService()
    writable_dir = tmp_path / "world-writable"
    writable_dir.mkdir()
    os.chmod(writable_dir, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    findings = service.analyze_path_entries([str(writable_dir)])

    assert findings[0]["severity"] == "high"
    assert "PATH-Verzeichnis ist für alle beschreibbar." in findings[0]["issues"]


def test_analyze_shell_profiles_flags_suspicious_path_export(tmp_path):
    service = PathGuardService()
    bashrc = tmp_path / ".bashrc"
    profile = tmp_path / ".profile"
    zshrc = tmp_path / ".zshrc"
    bashrc.write_text('export PATH="/tmp:$PATH"\n', encoding="utf-8")
    profile.write_text('export PATH="$HOME/bin:$PATH"\n', encoding="utf-8")

    service.get_shell_profile_paths = lambda: [
        str(bashrc),
        str(profile),
        str(zshrc),
    ]

    findings = service.analyze_shell_profiles()

    assert findings[0]["severity"] == "high"
    assert findings[0]["matches"][0]["line"] == 1
    assert (
        "Verdächtige PATH-Manipulation im Shell-Profil."
        in findings[0]["matches"][0]["issues"]
    )
    assert findings[1]["severity"] == "info"
    assert findings[1]["matches"][0]["severity"] == "info"
    assert (
        "Übliche User-Bin-Pfade werden eingebunden."
        in findings[1]["matches"][0]["issues"]
    )
    assert findings[2]["exists"] is False


def test_run_check_reports_high_risk_for_problematic_entries(tmp_path):
    service = PathGuardService()
    bashrc = tmp_path / ".bashrc"
    bashrc.write_text('export PATH="/tmp:$PATH"\n', encoding="utf-8")
    service.get_current_path_entries = lambda: ["/tmp", "/usr/bin"]
    service.get_shell_profile_paths = lambda: [str(bashrc)]

    result = service.run_check()

    assert result["risk"] == "hoch"
    assert result["counts"]["high"] >= 2


def test_run_check_keeps_normal_user_bins_and_missing_snap_low_risk(tmp_path):
    service = PathGuardService()
    bashrc = tmp_path / ".bashrc"
    profile = tmp_path / ".profile"
    bashrc.write_text(
        'export PATH="$HOME/bin:$HOME/.local/bin:$PATH"\n', encoding="utf-8"
    )
    profile.write_text(
        'PATH="$HOME/bin:$PATH"\nPATH="$HOME/.local/bin:$PATH"\n', encoding="utf-8"
    )

    service.get_current_path_entries = lambda: ["/snap/bin", "/usr/bin"]
    service.get_shell_profile_paths = lambda: [str(bashrc), str(profile)]

    result = service.run_check()

    assert result["risk"] == "niedrig"
    assert result["counts"] == {"high": 0, "medium": 0}
    assert result["path_findings"][0]["severity"] == "info"
    assert (
        "/snap/bin steht im PATH, existiert aber nicht."
        in result["path_findings"][0]["issues"]
    )
    assert result["profile_findings"][0]["severity"] == "info"
    assert result["profile_findings"][1]["severity"] == "info"


def test_format_path_guard_result_and_analyze_with_chad():
    app = App.__new__(App)
    app.lang = {}
    calls = []
    result = {
        "path_entries": ["/tmp", "/usr/bin"],
        "path_findings": [
            {
                "entry": "/tmp",
                "severity": "high",
                "issues": ["Temporäres oder RAM-Verzeichnis im PATH."],
            }
        ],
        "profile_findings": [
            {
                "path": "/home/test/.bashrc",
                "exists": True,
                "severity": "high",
                "matches": [
                    {
                        "line": 3,
                        "text": 'export PATH="/tmp:$PATH"',
                        "issues": ["Verdächtige PATH-Manipulation im Shell-Profil."],
                    }
                ],
            }
        ],
        "risk": "hoch",
        "counts": {"high": 2, "medium": 0},
    }
    app.path_guard_last_result = result
    app.prepare_chad_analysis = lambda title, text: calls.append((title, text))

    text = app.format_path_guard_result(result)
    app.analyze_path_guard_with_chad()

    assert "=== PATH Guard Prüfung ===" in text
    assert "[HOCH] /tmp" in text
    assert 'export PATH="/tmp:$PATH"' in text
    assert calls[0][0] == "PATH Guard Analyse"
    assert "Risiko: hoch" in calls[0][1]


def test_format_path_guard_result_shows_hints_for_normal_user_bins():
    app = App.__new__(App)
    app.lang = {}
    result = {
        "path_entries": ["/snap/bin", "/usr/bin"],
        "path_findings": [
            {
                "entry": "/snap/bin",
                "severity": "info",
                "issues": ["/snap/bin steht im PATH, existiert aber nicht."],
            }
        ],
        "profile_findings": [
            {
                "path": "/home/test/.bashrc",
                "exists": True,
                "severity": "info",
                "matches": [
                    {
                        "line": 1,
                        "text": 'export PATH="$HOME/bin:$HOME/.local/bin:$PATH"',
                        "severity": "info",
                        "issues": ["Übliche User-Bin-Pfade werden eingebunden."],
                    }
                ],
            }
        ],
        "risk": "niedrig",
        "counts": {"high": 0, "medium": 0},
    }

    text = app.format_path_guard_result(result)

    assert "Risiko: niedrig" in text
    assert "Hinweise:" in text
    assert "/snap/bin steht im PATH, existiert aber nicht." in text
    assert "~/.local/bin wird über .profile/.bashrc ergänzt. Das ist üblich." in text
    assert "~/bin wird über .profile/.bashrc ergänzt. Das ist üblich." in text
    assert "Keine auffällige PATH-Manipulation erkannt." in text


def test_format_path_guard_result_uses_english_translations_when_loaded():
    app = App.__new__(App)
    app.lang = {
        "path_guard_report_title": "=== PATH Guard Check ===",
        "path_guard_report_risk": "Risk: {value}",
        "path_guard_report_notes": "Notes:",
        "path_guard_report_none_detected": "No suspicious PATH manipulation detected.",
        "path_guard_risk_low": "low",
        "path_guard_issue_snap_missing": "/snap/bin is in PATH but does not exist.",
        "path_guard_hint_local_bin_common": "~/.local/bin is added via .profile/.bashrc. This is common.",
        "path_guard_hint_home_bin_common": "~/bin is added via .profile/.bashrc. This is common.",
    }
    result = {
        "path_entries": ["/snap/bin", "/usr/bin"],
        "path_findings": [
            {
                "entry": "/snap/bin",
                "severity": "info",
                "issues": ["/snap/bin steht im PATH, existiert aber nicht."],
            }
        ],
        "profile_findings": [
            {
                "path": "/home/test/.bashrc",
                "exists": True,
                "severity": "info",
                "matches": [
                    {
                        "line": 1,
                        "text": 'export PATH="$HOME/bin:$HOME/.local/bin:$PATH"',
                        "severity": "info",
                        "issues": ["Übliche User-Bin-Pfade werden eingebunden."],
                    }
                ],
            }
        ],
        "risk": "niedrig",
        "counts": {"high": 0, "medium": 0},
    }

    text = app.format_path_guard_result(result)

    assert "=== PATH Guard Check ===" in text
    assert "Risk: low" in text
    assert "Notes:" in text
    assert "/snap/bin is in PATH but does not exist." in text
    assert "~/.local/bin is added via .profile/.bashrc. This is common." in text
    assert "~/bin is added via .profile/.bashrc. This is common." in text
    assert "No suspicious PATH manipulation detected." in text
