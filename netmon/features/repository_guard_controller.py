"""Repository Guard controller helpers for NetMon."""

from __future__ import annotations

import json
import shlex
import os
from datetime import datetime

try:
    from tkinter import filedialog
except Exception:
    filedialog = None


KEYRING_RELATED_CODES = {
    "repo_no_signed_by",
    "repo_signed_by_missing_file",
    "repo_signed_by_unexpected_path",
    "repo_signed_by_unexpected_location",
}

BASELINE_RELATED_CODES = {
    "repo_baseline_new",
    "repo_baseline_removed",
    "repo_baseline_changed",
    "repo_baseline_moved",
}


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _app_list(app, name: str):
    return list(_app_value(app, name, []) or [])


def _app_var_set(app, name: str, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _repository_guard_service(app):
    return getattr(app, "repository_guard_service", None)


def _repository_guard_service_unavailable_message() -> str:
    return "Repository Guard: Service nicht verfügbar."


def _tr(app, key: str, fallback: str) -> str:
    callback = getattr(app, "tr", None)
    if not callable(callback):
        return fallback
    try:
        return callback(key, fallback)
    except Exception:
        return fallback


def _repo_text(
    app,
    key: str,
    default_de: str,
    default_en: str | None = None,
) -> str:
    if app is None:
        return default_en if default_en is not None else default_de
    return _tr(app, key, default_de)


def _repository_guard_trust_state_label(
    app_or_trust_state, trust_state: str | None = None
) -> str:
    if trust_state is None:
        app = None
        trust_state = app_or_trust_state
    else:
        app = app_or_trust_state
    return {
        "known": (
            _tr(app, "repository_guard_trust_state_known", "bekannt")
            if app is not None
            else "bekannt"
        ),
        "trusted": (
            _tr(app, "repository_guard_trust_state_trusted", "vertraut")
            if app is not None
            else "vertraut"
        ),
        "review": (
            _tr(app, "repository_guard_trust_state_review", "prüfen")
            if app is not None
            else "prüfen"
        ),
    }.get(str(trust_state or "").strip().lower(), "-")


def _repository_guard_trustlist_path(app) -> str:
    return str(getattr(app, "repository_guard_trustlist_path", "") or "").strip()


def _repository_guard_baseline_path(app) -> str:
    return str(getattr(app, "repository_guard_baseline_path", "") or "").strip()


def _repository_guard_missing_baseline_path_message() -> str:
    return "Repository Guard: Baseline-Pfad fehlt."


def _repository_guard_trustlist(app) -> dict:
    service = _repository_guard_service(app)
    if service is None:
        return {"trusted_hosts": {}}
    return service.load_trustlist(_repository_guard_trustlist_path(app))


def _finish_repository_guard_trustlist_action(
    app, *, ok: bool, err: str, success_message: str
) -> None:
    if not ok:
        app.log(f"Repository Guard: Trustlist Fehler: {err}")
        return
    app.log(success_message)
    run_repository_guard_scan(app)


def _repository_guard_last_result(app) -> dict:
    return dict(_app_value(app, "repository_guard_last_result", {}) or {})


def _repository_guard_selected_source(app) -> dict | None:
    return getattr(app, "repository_guard_selected_source", None)


def _repository_guard_selected_finding(app) -> dict | None:
    return getattr(app, "repository_guard_selected_finding", None)


def _repository_guard_selected_source_or_log(app) -> dict | None:
    source = _repository_guard_selected_source(app)
    if not source:
        app.log("Repository Guard: Keine Quelle ausgewählt.")
        return None
    return source


def _copy_repository_guard_payload(
    app,
    payload: str,
    *,
    success_message: str,
    failure_prefix: str,
) -> bool:
    try:
        app.clipboard_clear()
        app.clipboard_append(payload)
    except Exception as exc:
        app.log(f"{failure_prefix}: {exc}")
        return False
    app.log(success_message)
    return True


def run_repository_guard_scan(app):
    service = _repository_guard_service(app)
    if service is None:
        _set_status(
            app,
            status="Repository Guard: Service nicht verfügbar",
            scan_status="Scan: Service nicht verfügbar",
        )
        app.log(_repository_guard_service_unavailable_message())
        return

    try:
        trustlist = _repository_guard_trustlist(app)
        result = service.scan(trustlist=trustlist)
    except Exception as exc:
        _set_status(
            app,
            status="Repository Guard: Fehler",
            scan_status="Scan: fehlgeschlagen",
        )
        _set_summary(app, "Quellen: 0 | Findings: 0 | Warnungen: 0 | Fehler: 1")
        _set_detail_text(
            app,
            "=== Repository Guard ===\n\n" f"Scan fehlgeschlagen:\n{exc}",
        )
        app.log(f"Repository Guard: Scan fehlgeschlagen: {exc}")
        return

    baseline_path = _repository_guard_baseline_path(app)
    if baseline_path and os.path.isfile(baseline_path):
        baseline = service.load_baseline(baseline_path)
        comparison = service.compare_to_baseline(
            baseline,
            list(result.get("sources") or []),
        )
        result["baseline"] = comparison
        _apply_baseline_findings(result, comparison)

    show_repository_guard_result(app, result)
    app.log(
        "Repository Guard: Scan abgeschlossen "
        f"(Quellen={result.get('summary', {}).get('repositories_total', 0)}, "
        f"Findings={result.get('summary', {}).get('findings_total', 0)})."
    )


def show_repository_guard_result(app, result: dict):
    app.repository_guard_last_result = dict(result or {})
    app.repository_guard_selected_source = None
    app.repository_guard_selected_finding = None

    status_map = {
        "ok": app.tr("repository_guard_state_ok", "Repository Guard: OK"),
        "notice": app.tr(
            "repository_guard_state_notice",
            "Repository Guard: notices",
        ),
        "warning": app.tr(
            "repository_guard_state_warning",
            "Repository Guard: warnings detected",
        ),
        "critical": app.tr(
            "repository_guard_state_critical",
            "Repository Guard: critical findings",
        ),
        "error": app.tr("repository_guard_state_error", "Repository Guard: error"),
        "unchecked": app.tr(
            "repository_guard_state_unchecked",
            "Repository Guard: not checked",
        ),
    }
    state = str(result.get("status") or "unchecked").strip().lower()
    checked_at = str(result.get("checked_at") or "-").strip()
    summary = dict(result.get("summary") or {})
    active_sources = [
        item for item in list(result.get("sources") or []) if item.get("enabled", True)
    ]
    third_party_active = [
        item
        for item in active_sources
        if str(item.get("origin_class") or "") == "unknown"
    ]
    trusted_active = [
        item for item in active_sources if bool(item.get("trusted_host", False))
    ]

    _set_status(
        app,
        status=status_map.get(
            state,
            app.tr(
                "repository_guard_state_unknown",
                "Repository Guard: unknown status",
            ),
        ),
        scan_status=app.tr(
            "repository_guard_last_scan", "Last scan: {timestamp}"
        ).format(timestamp=checked_at),
    )
    _set_summary(
        app,
        app.tr(
            "repository_guard_summary_value",
            "Sources active: {active_count} | Third-party active: {third_party_count} | Trusted: {trusted_count} | Findings: {findings_total} | Warnings: {warning} | Changes: {changes}",
        ).format(
            active_count=len(active_sources),
            third_party_count=len(third_party_active),
            trusted_count=len(trusted_active),
            findings_total=summary.get("findings_total", 0),
            warning=summary.get("warning", 0),
            changes=_baseline_change_count(result),
        ),
    )

    update_repository_guard_filter_status_line(app)
    update_repository_guard_status_light(app, state)
    refresh_repository_guard_sources_tree(app)
    refresh_repository_guard_findings_tree(app)

    _set_detail_text(
        app,
        format_repository_guard_result(result, app),
    )


def refresh_repository_guard_sources_tree(app):
    tree = _app_value(app, "repository_guard_sources_tree")
    if tree is None:
        return

    for item in tree.get_children():
        tree.delete(item)

    all_sources = list((_repository_guard_last_result(app)).get("sources", []) or [])
    filter_mode = str(
        getattr(app, "repository_guard_source_filter_mode", "all") or "all"
    )
    if filter_mode == "apt":
        sources = [item for item in all_sources if item.get("kind") == "apt"]
    elif filter_mode == "flatpak":
        sources = [item for item in all_sources if item.get("kind") == "flatpak"]
    elif filter_mode == "active":
        sources = [item for item in all_sources if item.get("enabled", True)]
    elif filter_mode == "third_party":
        sources = [
            item
            for item in all_sources
            if str(item.get("origin_class") or "") == "unknown"
        ]
    elif filter_mode == "trusted":
        sources = [
            item for item in all_sources if bool(item.get("trusted_host", False))
        ]
    elif filter_mode == "review":
        sources = [
            item
            for item in all_sources
            if item.get("enabled", True)
            and str(item.get("origin_class") or "") == "unknown"
            and not bool(item.get("trusted_host", False))
        ]
    else:
        sources = all_sources

    app.repository_guard_visible_sources = sources
    for index, source in enumerate(sources):
        iid = f"repo-src-{index}"
        tree.insert(
            "",
            "end",
            iid=iid,
            values=(
                (
                    app.tr("repository_guard_source_state_active", "active")
                    if source.get("enabled", True)
                    else app.tr("repository_guard_source_state_disabled", "disabled")
                ),
                source.get("repo_type", "-"),
                _repository_guard_trust_state_label(app, source.get("trust_state")),
                source.get("host", "-") or "-",
                source.get("suite", "-"),
                ", ".join(source.get("components", []) or ["-"]),
                source.get("uri", "-"),
                source.get("file_path", "-"),
            ),
        )
    update_repository_guard_filter_status_line(app)


def refresh_repository_guard_findings_tree(app):
    tree = _app_value(app, "repository_guard_findings_tree")
    if tree is None:
        return

    for item in tree.get_children():
        tree.delete(item)

    all_findings = list((_repository_guard_last_result(app)).get("findings", []) or [])
    filter_mode = str(
        getattr(app, "repository_guard_finding_filter_mode", "all") or "all"
    )
    source_map = _repository_guard_source_map(app)
    if filter_mode == "relevant":
        findings = [
            item
            for item in all_findings
            if str(item.get("severity") or "").lower()
            in {"critical", "error", "warning"}
        ]
    elif filter_mode == "baseline":
        findings = [
            item
            for item in all_findings
            if str(item.get("code") or "").startswith("repo_baseline_")
        ]
    elif filter_mode == "keyring":
        findings = [
            item for item in all_findings if is_repository_guard_keyring_finding(item)
        ]
    elif filter_mode == "review":
        findings = [
            item
            for item in all_findings
            if is_repository_guard_review_finding(item, source_map)
        ]
    elif filter_mode == "warnings":
        findings = [
            item
            for item in all_findings
            if str(item.get("severity") or "").lower()
            in {"critical", "error", "warning"}
        ]
    elif filter_mode == "notices":
        findings = [
            item
            for item in all_findings
            if str(item.get("severity") or "").lower() in {"notice", "info"}
        ]
    else:
        findings = all_findings

    app.repository_guard_visible_findings = findings
    _configure_repository_guard_finding_tags(tree)
    for index, finding in enumerate(findings):
        iid = f"repo-find-{index}"
        severity = str(finding.get("severity", "-")).upper()
        tree.insert(
            "",
            "end",
            iid=iid,
            values=(
                severity,
                finding.get("code", "-"),
                finding.get("summary", "-"),
            ),
            tags=(str(finding.get("severity") or "").lower(),),
        )
    update_repository_guard_filter_status_line(app)


def on_repository_guard_source_select(app, _event=None):
    tree = _app_value(app, "repository_guard_sources_tree")
    if tree is None:
        return
    source = _selected_repository_guard_tree_item(
        tree,
        _app_list(app, "repository_guard_visible_sources"),
    )
    if source is None:
        app.repository_guard_selected_source = None
        return
    app.repository_guard_selected_source = source
    _set_detail_text(app, format_repository_guard_source_details(source, app))


def on_repository_guard_finding_select(app, _event=None):
    tree = _app_value(app, "repository_guard_findings_tree")
    if tree is None:
        return
    finding = _selected_repository_guard_tree_item(
        tree,
        _app_list(app, "repository_guard_visible_findings"),
    )
    if finding is None:
        app.repository_guard_selected_finding = None
        return
    app.repository_guard_selected_finding = finding
    _set_detail_text(app, format_repository_guard_finding_details(app, finding))


def format_repository_guard_result(result: dict, app=None) -> str:
    summary = dict(result.get("summary") or {})
    sources = list(result.get("sources") or [])
    active_sources = [item for item in sources if item.get("enabled", True)]
    third_party_active = [
        item
        for item in active_sources
        if str(item.get("origin_class") or "") == "unknown"
    ]
    lines = [
        _repo_text(
            app,
            "repository_guard_report_title",
            "=== Repository Guard ===",
            "=== Repository Guard ===",
        ),
        "",
        _repo_text(app, "label_status", "Status:", "Status:")
        + f" {result.get('status', '-')}",
        _repo_text(
            app,
            "repository_guard_report_checked_at",
            "Geprüft am:",
            "Checked at:",
        )
        + f" {result.get('checked_at', '-')}",
        _repo_text(
            app,
            "repository_guard_report_total_sources",
            "Quellen gesamt: {count}",
            "Total sources: {count}",
        ).format(count=summary.get("repositories_total", 0)),
        _repo_text(
            app,
            "repository_guard_report_active_sources",
            "Quellen aktiv: {count}",
            "Active sources: {count}",
        ).format(count=len(active_sources)),
        _repo_text(
            app,
            "repository_guard_report_third_party_active",
            "Drittquellen aktiv: {count}",
            "Third-party active: {count}",
        ).format(count=len(third_party_active)),
        _repo_text(
            app,
            "repository_guard_report_trusted_hosts_active",
            "Vertraute Hosts aktiv: {count}",
            "Trusted hosts active: {count}",
        ).format(
            count=sum(1 for item in active_sources if item.get("trusted_host", False))
        ),
        _repo_text(
            app,
            "repository_guard_report_findings",
            "Befunde: {count}",
            "Findings: {count}",
        ).format(count=summary.get("findings_total", 0)),
        _repo_text(
            app,
            "repository_guard_report_warnings",
            "Warnungen: {count}",
            "Warnings: {count}",
        ).format(count=summary.get("warning", 0)),
        _repo_text(
            app,
            "repository_guard_report_notices",
            "Hinweise: {count}",
            "Notices: {count}",
        ).format(count=summary.get("notice", 0)),
        _repo_text(
            app,
            "repository_guard_report_errors",
            "Fehler: {count}",
            "Errors: {count}",
        ).format(count=summary.get("errors", 0)),
        _repo_text(
            app,
            "repository_guard_report_baseline_changes",
            "Baseline-Änderungen: {count}",
            "Baseline changes: {count}",
        ).format(count=_baseline_change_count(result)),
        "",
        _repo_text(
            app,
            "repository_guard_report_note_header",
            "Hinweis:",
            "Note:",
        ),
        _repo_text(
            app,
            "repository_guard_report_note_body",
            "APT-.list, Deb822-.sources und Flatpak-Remotes werden aktuell lokal eingelesen.",
            "APT .list, Deb822 .sources, and Flatpak remotes are currently read locally.",
        ),
    ]
    return "\n".join(lines)


def format_repository_guard_source_details(source: dict, app=None) -> str:
    lines = [
        _repo_text(
            app,
            "repository_guard_source_details_title",
            "=== Repository-Quelle ===",
            "=== Repository Source ===",
        ),
        "",
        f"{_repo_text(app, 'label_id', 'ID', 'ID')}: {source.get('id', '-')}",
        _repo_text(
            app,
            "repository_guard_source_details_active",
            "Aktiv: {value}",
            "Active: {value}",
        ).format(value="ja" if source.get("enabled", True) else "nein"),
        _repo_text(
            app,
            "repository_guard_source_details_type",
            "Typ: {value}",
            "Type: {value}",
        ).format(value=source.get("repo_type", "-")),
        f"URI: {source.get('uri', '-')}",
        _repo_text(
            app,
            "repository_guard_source_details_host",
            "Host: {value}",
            "Host: {value}",
        ).format(value=source.get("host", "-") or "-"),
        _repo_text(
            app,
            "repository_guard_source_details_trust",
            "Vertrauen: {value}",
            "Trust: {value}",
        ).format(
            value=_repository_guard_trust_state_label(app, source.get("trust_state"))
        ),
        _repo_text(
            app,
            "repository_guard_source_details_suite",
            "Suite: {value}",
            "Suite: {value}",
        ).format(value=source.get("suite", "-")),
        _repo_text(
            app,
            "repository_guard_source_details_format",
            "Format: {value}",
            "Format: {value}",
        ).format(value=source.get("format", "-")),
        _repo_text(
            app,
            "repository_guard_source_details_components",
            "Komponenten: {value}",
            "Components: {value}",
        ).format(value=", ".join(source.get("components", []) or ["-"])),
        _repo_text(
            app,
            "repository_guard_source_details_file",
            "Datei: {value}",
            "File: {value}",
        ).format(value=source.get("file_path", "-")),
        _repo_text(
            app,
            "repository_guard_source_details_line",
            "Zeile: {value}",
            "Line: {value}",
        ).format(value=source.get("line_no", "-")),
        f"signed-by: {source.get('signed_by', '-') or '-'}",
        _repo_text(
            app,
            "repository_guard_source_details_origin",
            "Herkunft: {value}",
            "Origin: {value}",
        ).format(value=source.get("origin_class", "-")),
        "",
        _repo_text(
            app,
            "repository_guard_source_details_raw_line",
            "Rohzeile:",
            "Raw line:",
        ),
        source.get("raw_line", "-"),
    ]
    return "\n".join(lines)


def format_repository_guard_finding_details(app, finding: dict) -> str:
    source_id = str(finding.get("source_id") or "").strip()
    source = _repository_guard_source_map(app).get(source_id)

    lines = [
        _repo_text(
            app,
            "repository_guard_finding_details_title",
            "=== Repository-Befund ===",
            "=== Repository Finding ===",
        ),
        "",
        _repo_text(
            app,
            "repository_guard_finding_details_severity",
            "Schwere: {value}",
            "Severity: {value}",
        ).format(value=str(finding.get("severity", "-")).upper()),
        _repo_text(
            app,
            "repository_guard_finding_details_code",
            "Code: {value}",
            "Code: {value}",
        ).format(value=finding.get("code", "-")),
        _repo_text(
            app,
            "repository_guard_finding_details_label_title",
            "Titel: {value}",
            "Title: {value}",
        ).format(value=finding.get("title", "-")),
        "",
        _repo_text(
            app,
            "repository_guard_finding_details_summary",
            "Zusammenfassung: {value}",
            "Summary: {value}",
        ).format(value=finding.get("summary", "-")),
    ]
    details = dict(finding.get("details") or {})
    if details:
        lines.extend(["", _repo_text(app, "btn_details", "Details", "Details") + ":"])
        for key in sorted(details):
            lines.append(f"- {key}: {details.get(key)}")
    recommendations = get_repository_guard_finding_recommendations(
        finding, source=source
    )
    if recommendations:
        lines.extend(
            [
                "",
                _repo_text(
                    app,
                    "repository_guard_finding_details_recommendations",
                    "Empfohlene Prüfung:",
                    "Recommended checks:",
                ),
            ]
        )
        for item in recommendations:
            lines.append(f"- {item}")
    if source is not None:
        lines.extend(
            [
                "",
                _repo_text(
                    app,
                    "repository_guard_finding_details_related_source",
                    "Zugehörige Quelle:",
                    "Related source:",
                ),
                f"- {_repo_text(app, 'repository_guard_col_type', 'Typ', 'Type')}: {source.get('repo_type', '-')}",
                f"- URI: {source.get('uri', '-')}",
                f"- {_repo_text(app, 'repository_guard_col_file', 'Datei', 'File')}: {source.get('file_path', '-')}",
                f"- {_repo_text(app, 'repository_guard_source_details_line', 'Zeile: {value}', 'Line: {value}').format(value=source.get('line_no', '-'))}",
            ]
        )
    return "\n".join(lines)


def get_repository_guard_finding_recommendations(
    finding: dict,
    *,
    source: dict | None = None,
) -> list[str]:
    code = str(finding.get("code") or "").strip()
    host = str((source or {}).get("host") or "").strip()
    uri = str((source or {}).get("uri") or "").strip()
    recommendations = {
        "repo_http_used": [
            "Prüfen, ob die Quelle HTTPS unterstützt, und die URI wenn möglich auf HTTPS umstellen.",
            "Wenn nur HTTP verfügbar ist, Quelle bewusst dokumentieren und besonders auf Signaturfehler achten.",
        ],
        "repo_unknown_origin": [
            "Prüfen, ob Host und Zweck der Quelle bekannt und gewollt sind.",
            "Bei bewusst genutzten Drittquellen den Host optional in die Repository-Trustlist übernehmen.",
        ],
        "repo_no_signed_by": [
            "Prüfen, ob der Anbieter eine aktuelle `signed-by=`-Einbindung mit eigener Keyring-Datei empfiehlt.",
            "Wenn möglich die Quelle auf eine dedizierte Keyring-Datei unter `/usr/share/keyrings/` oder `/etc/apt/keyrings/` umstellen.",
        ],
        "repo_signed_by_missing_file": [
            "Prüfen, ob die referenzierte Keyring-Datei gelöscht, verschoben oder nie angelegt wurde.",
            "Falls die Quelle gewollt ist, den empfohlenen GPG-Key erneut sauber in eine dedizierte Keyring-Datei importieren.",
        ],
        "repo_signed_by_unexpected_path": [
            "Prüfen, ob `signed-by` wirklich auf eine absolute Datei zeigt.",
            "Relative oder ungewöhnliche Pfade nach Möglichkeit durch einen klaren Keyring-Pfad ersetzen.",
        ],
        "repo_signed_by_unexpected_location": [
            "Prüfen, warum die Keyring-Datei außerhalb der üblichen APT-Keyring-Verzeichnisse liegt.",
            "Wenn möglich die Datei in `/usr/share/keyrings/` oder `/etc/apt/keyrings/` migrieren.",
        ],
        "repo_duplicate_source": [
            "Prüfen, ob derselbe Eintrag versehentlich mehrfach in verschiedenen Dateien vorhanden ist.",
            "Nicht benötigte Dubletten entfernen, damit APT-Warnungen und Pflegeaufwand sinken.",
        ],
        "repo_duplicate_source_variant": [
            "Prüfen, warum dieselbe Quelle mehrfach mit unterschiedlichen Optionen oder Schlüsselbindungen eingetragen ist.",
            "Wenn nur eine Variante gewollt ist, die übrigen Einträge bereinigen.",
        ],
        "repo_baseline_new": [
            "Prüfen, wann und wodurch diese Quelle neu hinzugekommen ist.",
            "Wenn die Änderung gewollt ist, nach Kontrolle die Baseline jetzt aktualisieren.",
        ],
        "repo_baseline_removed": [
            "Prüfen, ob die entfernte Quelle bewusst entfernt oder unbeabsichtigt verloren gegangen ist.",
            "Wenn die Änderung gewollt ist, nach Kontrolle die Baseline jetzt aktualisieren.",
        ],
        "repo_baseline_changed": [
            "Prüfen, welche Felder sich seit der Baseline geändert haben und ob die Änderung erwartet war.",
            "Wenn die Änderung gewollt ist, nach Kontrolle die Baseline jetzt aktualisieren.",
        ],
        "repo_baseline_moved": [
            "Prüfen, ob die Quelle nur organisatorisch verschoben wurde oder ob parallel weitere Änderungen erfolgt sind.",
            "Wenn alles plausibel ist, kann die neue Position mit 'Baseline jetzt aktualisieren' als Referenz übernommen werden.",
        ],
        "repo_empty_components": [
            "Prüfen, ob der Eintrag unvollständig ist oder bewusst keine Komponenten verwendet.",
        ],
        "repo_deb_src_enabled": [
            "Prüfen, ob Quellpakete auf diesem System wirklich benötigt werden.",
            "Wenn nicht, kann `deb-src` deaktiviert bleiben oder wieder deaktiviert werden.",
        ],
        "repo_disabled_entry": [
            "Meist kein Handlungsbedarf. Nur prüfen, ob der deaktivierte Eintrag bewusst auskommentiert wurde.",
        ],
    }.get(code, [])

    if code == "repo_unknown_origin" and host:
        recommendations.append(f"Betroffener Host: `{host}`")
    if code in {"repo_http_used", "repo_baseline_new", "repo_baseline_changed"} and uri:
        recommendations.append(f"Betroffene URI: `{uri}`")
    return recommendations


def is_repository_guard_keyring_finding(finding: dict) -> bool:
    return str(finding.get("code") or "").strip() in KEYRING_RELATED_CODES


def is_repository_guard_review_finding(
    finding: dict,
    source_map: dict[str, dict] | None = None,
) -> bool:
    severity = str(finding.get("severity") or "").strip().lower()
    if severity not in {"critical", "error", "warning"}:
        return False
    source = dict((source_map or {}).get(str(finding.get("source_id") or ""), {}) or {})
    if not source:
        return False
    return (
        bool(source.get("enabled", True))
        and str(source.get("origin_class") or "") == "unknown"
        and not bool(source.get("trusted_host", False))
    )


def _repository_guard_source_map(app) -> dict[str, dict]:
    all_sources = list(
        (getattr(app, "repository_guard_last_result", {}) or {}).get("sources", [])
        or []
    )
    return {
        str(item.get("id") or ""): item
        for item in all_sources
        if str(item.get("id") or "")
    }


def set_repository_guard_source_filter(app, filter_mode: str):
    _set_repository_guard_filter(
        app,
        filter_mode,
        attr_name="repository_guard_source_filter_mode",
        normalize=_repository_guard_source_filter_mode,
        refresh=refresh_repository_guard_sources_tree,
        log_prefix="Quellenfilter",
    )


def set_repository_guard_finding_filter(app, filter_mode: str):
    _set_repository_guard_filter(
        app,
        filter_mode,
        attr_name="repository_guard_finding_filter_mode",
        normalize=_repository_guard_finding_filter_mode,
        refresh=refresh_repository_guard_findings_tree,
        log_prefix="Finding-Filter",
    )


def copy_repository_guard_report(app):
    payload = _repository_guard_report_payload(
        _app_value(app, "repository_guard_last_result", {}) or {},
        _read_repository_guard_detail_text(app),
    )
    _copy_repository_guard_payload(
        app,
        payload,
        success_message="Repository Guard: Ergebnis in Zwischenablage kopiert.",
        failure_prefix="Repository Guard: Kopieren fehlgeschlagen",
    )


def clear_repository_guard_view(app):
    app.repository_guard_last_result = {}
    app.repository_guard_visible_sources = []
    app.repository_guard_visible_findings = []
    app.repository_guard_selected_source = None
    app.repository_guard_selected_finding = None
    app.repository_guard_source_filter_mode = "all"
    app.repository_guard_finding_filter_mode = "relevant"

    _set_status(
        app,
        status=app.tr("repository_guard_status_not_checked", "Status: Nicht geprüft"),
        scan_status=app.tr(
            "repository_guard_scan_unavailable",
            "Repository-Scan: Noch nicht verfügbar",
        ),
    )
    _set_summary(
        app,
        app.tr(
            "repository_guard_summary_empty",
            "Quellen: 0 | Funde: 0 | Warnungen: 0 | Fehler: 0",
        ),
    )
    update_repository_guard_filter_status_line(app)
    refresh_repository_guard_sources_tree(app)
    refresh_repository_guard_findings_tree(app)
    update_repository_guard_status_light(app, "unchecked")
    _set_detail_text(
        app,
        app.tr(
            "repository_guard_detail_placeholder",
            "Repository-Guard-Details erscheinen hier.\n\nNach gewollten Repository-Aenderungen: Erst scannen, dann die Baseline aktualisieren.\n",
        ),
    )
    app.log("Repository Guard: Anzeige geleert.")


def run_repository_guard_primary_action(app):
    finding, source = _repository_guard_selection_context(app)
    action = get_repository_guard_primary_action(finding, source=source)
    action_type = action.get("type", "")

    if action_type == "save_baseline":
        create_repository_guard_baseline(app)
        return
    if action_type == "mark_trusted":
        mark_selected_repository_guard_trusted(app)
        return
    if action_type == "copy_snippet":
        copy_repository_guard_quick_action_snippet(app)
        return
    app.log("Repository Guard: Keine passende Quick-Action verfügbar.")


def copy_repository_guard_quick_action_snippet(app):
    finding, source = _repository_guard_selection_context(app)
    snippet = get_repository_guard_quick_action_snippet(finding, source=source)
    if not snippet:
        app.log("Repository Guard: Kein Quick-Action-Snippet verfügbar.")
        return
    _copy_repository_guard_payload(
        app,
        snippet,
        success_message="Repository Guard: Quick-Action-Snippet kopiert.",
        failure_prefix="Repository Guard: Snippet konnte nicht kopiert werden",
    )


def copy_repository_guard_selected_uri(app):
    finding, source = _repository_guard_selection_context(app)
    uri = get_repository_guard_selected_uri(finding, source=source)
    if not uri:
        app.log("Repository Guard: Keine URI verfügbar.")
        return
    _copy_repository_guard_payload(
        app,
        uri,
        success_message=f"Repository Guard: URI kopiert: {uri}",
        failure_prefix="Repository Guard: URI konnte nicht kopiert werden",
    )


def copy_repository_guard_selected_file_path(app):
    finding, source = _repository_guard_selection_context(app)
    path = get_repository_guard_selected_file_path(finding, source=source)
    if not path:
        app.log("Repository Guard: Kein Dateipfad verfügbar.")
        return
    _copy_repository_guard_payload(
        app,
        path,
        success_message=f"Repository Guard: Dateipfad kopiert: {path}",
        failure_prefix="Repository Guard: Dateipfad konnte nicht kopiert werden",
    )


def get_repository_guard_primary_action(
    finding: dict | None,
    *,
    source: dict | None = None,
) -> dict:
    code = str((finding or {}).get("code") or "").strip()
    if code in BASELINE_RELATED_CODES:
        return {"type": "save_baseline", "label": "Baseline jetzt aktualisieren"}
    if (
        source
        and str(source.get("origin_class") or "") == "unknown"
        and not bool(source.get("trusted_host", False))
    ):
        return {"type": "mark_trusted", "label": "Host vertrauen"}
    if get_repository_guard_quick_action_snippet(finding, source=source):
        return {"type": "copy_snippet", "label": "Snippet kopieren"}
    return {"type": "", "label": ""}


def get_repository_guard_quick_action_snippet(
    finding: dict | None,
    *,
    source: dict | None = None,
) -> str:
    code = str((finding or {}).get("code") or "").strip()
    details = dict((finding or {}).get("details") or {})
    uri = get_repository_guard_selected_uri(finding, source=source)
    path = get_repository_guard_selected_file_path(finding, source=source)
    host = str((source or {}).get("host") or "").strip()
    keyring_path = str(details.get("keyring_path") or "").strip()
    quoted_uri = shlex.quote(uri) if uri else ""
    quoted_path = shlex.quote(path) if path else ""
    quoted_host = shlex.quote(host) if host else ""
    quoted_keyring_path = shlex.quote(keyring_path) if keyring_path else ""

    if code == "repo_http_used" and uri:
        return (
            f"grep -Rni -- {quoted_uri} /etc/apt/sources.list /etc/apt/sources.list.d"
        )
    if code == "repo_unknown_origin" and host:
        return (
            f"grep -Rni -- {quoted_host} /etc/apt/sources.list /etc/apt/sources.list.d"
        )
    if code == "repo_no_signed_by" and path:
        return f"grep -n 'signed-by\\|^deb' {quoted_path}"
    if code == "repo_signed_by_missing_file" and keyring_path:
        return f"ls -l {quoted_keyring_path}"
    if code == "repo_signed_by_unexpected_path" and path:
        return f"grep -n 'signed-by' {quoted_path}"
    if code == "repo_signed_by_unexpected_location" and keyring_path:
        return f"ls -l {quoted_keyring_path}"
    if code in {"repo_duplicate_source", "repo_duplicate_source_variant"} and host:
        return (
            f"grep -Rni -- {quoted_host} /etc/apt/sources.list /etc/apt/sources.list.d"
        )
    if code in BASELINE_RELATED_CODES:
        return "Repository Guard: Nach Prüfung 'Baseline jetzt aktualisieren' im Tab ausführen."
    if path:
        return f"grep -n . {quoted_path}"
    return ""


def get_repository_guard_selected_uri(
    finding: dict | None,
    *,
    source: dict | None = None,
) -> str:
    return _repository_guard_selected_detail_value(
        finding,
        source=source,
        source_key="uri",
        detail_keys=("uri", "uri_after", "uri_before"),
    )


def get_repository_guard_selected_file_path(
    finding: dict | None,
    *,
    source: dict | None = None,
) -> str:
    return _repository_guard_selected_detail_value(
        finding,
        source=source,
        source_key="file_path",
        detail_keys=("file_path", "file_path_after", "file_path_before"),
    )


def _repository_guard_selected_detail_value(
    finding: dict | None,
    *,
    source: dict | None,
    source_key: str,
    detail_keys: tuple[str, ...],
) -> str:
    details = dict((finding or {}).get("details") or {})
    if source and str(source.get(source_key) or "").strip():
        return str(source.get(source_key) or "").strip()
    for key in detail_keys:
        value = str(details.get(key) or "").strip()
        if value:
            return value
    return ""


def _resolve_repository_guard_selected_source(
    app,
    *,
    finding: dict | None = None,
) -> dict | None:
    selected_source = _repository_guard_selected_source(app)
    if selected_source:
        return selected_source
    source_id = _repository_guard_source_id(finding)
    if not source_id:
        return None
    return _repository_guard_source_map(app).get(source_id)


def _repository_guard_selection_context(app) -> tuple[dict | None, dict | None]:
    finding = _repository_guard_selected_finding(app)
    source = _resolve_repository_guard_selected_source(app, finding=finding)
    return finding, source


def _set_repository_guard_filter(
    app,
    filter_mode: str,
    *,
    attr_name: str,
    normalize,
    refresh,
    log_prefix: str,
):
    mode = normalize(filter_mode)
    setattr(app, attr_name, mode)
    refresh(app)
    app.log(f"Repository Guard: {log_prefix} aktiv - {mode}.")


def _selected_repository_guard_tree_index(selection_id: str):
    try:
        return int(str(selection_id).rsplit("-", 1)[-1])
    except Exception:
        return None


def _selected_repository_guard_tree_item(tree, items):
    if tree is None:
        return None
    try:
        selection = tuple(tree.selection())
    except Exception:
        selection = ()
    if not selection:
        return None
    index = _selected_repository_guard_tree_index(selection[0])
    if index is None:
        return None
    visible_items = list(items or [])
    if index < 0 or index >= len(visible_items):
        return None
    return visible_items[index]


def _repository_guard_source_id(finding: dict | None) -> str:
    return str((finding or {}).get("source_id") or "").strip()


def _repository_guard_source_filter_mode(filter_mode: str) -> str:
    mode = str(filter_mode or "all").strip().lower()
    if mode not in {
        "all",
        "apt",
        "flatpak",
        "active",
        "third_party",
        "trusted",
        "review",
    }:
        return "all"
    return mode


def _repository_guard_finding_filter_mode(filter_mode: str) -> str:
    mode = str(filter_mode or "all").strip().lower()
    if mode not in {
        "all",
        "relevant",
        "baseline",
        "keyring",
        "review",
        "warnings",
        "notices",
    }:
        return "all"
    return mode


def _repository_guard_source_filter_status_text(filter_mode: str) -> str:
    return {
        "all": "Quellenfilter: alle",
        "apt": "Quellenfilter: nur APT",
        "flatpak": "Quellenfilter: nur Flatpak",
        "active": "Quellenfilter: nur aktiv",
        "third_party": "Quellenfilter: nur Drittquellen",
        "trusted": "Quellenfilter: nur vertraute Hosts",
        "review": "Quellenfilter: nur prüfen",
    }.get(str(filter_mode or "all").strip().lower(), "Quellenfilter: alle")


def _repository_guard_finding_filter_status_text(filter_mode: str) -> str:
    return {
        "all": "Finding-Filter: alle",
        "relevant": "Finding-Filter: relevant",
        "baseline": "Finding-Filter: Baseline-Änderungen",
        "keyring": "Finding-Filter: Keyring-Probleme",
        "review": "Finding-Filter: Drittquellen-Prüfung",
        "warnings": "Finding-Filter: Warnungen + Fehler",
        "notices": "Finding-Filter: Hinweise + Info",
    }.get(str(filter_mode or "all").strip().lower(), "Finding-Filter: alle")


def _repository_guard_status_light_color(state: str) -> str:
    return {
        "unchecked": "#7a7f87",
        "ok": "#2fbf71",
        "notice": "#175cd3",
        "warning": "#f79009",
        "critical": "#d92d20",
        "error": "#d92d20",
    }.get(str(state or "").strip().lower(), "#7a7f87")


def export_repository_guard_report(app):
    if filedialog is None:
        app.log("Repository Guard: Dateidialog nicht verfügbar.")
        return

    result = _repository_guard_last_result(app)
    if not result:
        app.log("Repository Guard: Noch kein Ergebnis zum Exportieren vorhanden.")
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    initial_dir = str(getattr(app, "netmon_state_dir", "") or os.getcwd())
    initial_name = f"netmon_repository_guard_{stamp}.json"
    try:
        path = filedialog.asksaveasfilename(
            parent=app,
            title=app.tr(
                "repository_guard_export_dialog_title",
                "Repository Guard Export",
            ),
            initialdir=initial_dir,
            initialfile=initial_name,
            defaultextension=".json",
            filetypes=[
                (app.tr("filetype_json", "JSON-Dateien"), "*.json"),
                (app.tr("filetype_text", "Text-Dateien"), "*.txt"),
                (app.tr("filetype_all", "Alle Dateien"), "*.*"),
            ],
        )
    except Exception as exc:
        app.log(f"Repository Guard: Speicherdialog fehlgeschlagen: {exc}")
        return
    if not path:
        return

    try:
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_repository_guard_export_payload(path, result))
        app.log(f"Repository Guard: Ergebnis exportiert: {path}")
    except Exception as exc:
        app.log(f"Repository Guard: Export fehlgeschlagen: {exc}")


def create_repository_guard_baseline(app):
    service = _repository_guard_service(app)
    if service is None:
        app.log(_repository_guard_service_unavailable_message())
        return

    try:
        trustlist = _repository_guard_trustlist(app)
        result = service.scan(trustlist=trustlist)
    except Exception as exc:
        app.log(f"Repository Guard: Baseline konnte nicht erstellt werden: {exc}")
        return

    baseline_path = _repository_guard_baseline_path(app)
    if not baseline_path:
        app.log(_repository_guard_missing_baseline_path_message())
        return

    baseline_exists = os.path.isfile(baseline_path)

    ok, err = service.save_baseline(baseline_path, list(result.get("sources") or []))
    if not ok:
        app.log(f"Repository Guard: Baseline aktualisieren fehlgeschlagen: {err}")
        return

    result["baseline"] = {
        "new": [],
        "removed": [],
        "changed": [],
        "moved": [],
        "unchanged": list(result.get("sources") or []),
    }
    show_repository_guard_result(app, result)
    if baseline_exists:
        app.log(f"Repository Guard: Baseline aktualisiert: {baseline_path}")
    else:
        app.log(f"Repository Guard: Baseline erstellt: {baseline_path}")


def reset_repository_guard_baseline(app):
    baseline_path = _repository_guard_baseline_path(app)
    if not baseline_path:
        app.log(_repository_guard_missing_baseline_path_message())
        return
    if not os.path.isfile(baseline_path):
        app.log(
            "Repository Guard: Keine gespeicherte Baseline zum Zurücksetzen vorhanden."
        )
        return

    try:
        os.remove(baseline_path)
    except Exception as exc:
        app.log(f"Repository Guard: Baseline konnte nicht zurückgesetzt werden: {exc}")
        return

    service = _repository_guard_service(app)
    if service is not None:
        try:
            trustlist = _repository_guard_trustlist(app)
            result = service.scan(trustlist=trustlist)
            show_repository_guard_result(app, result)
        except Exception as exc:
            app.log(
                f"Repository Guard: Baseline entfernt, aber Ansicht konnte nicht neu geladen werden: {exc}"
            )

    app.log("Repository Guard: Baseline wurde zurückgesetzt.")


def mark_selected_repository_guard_trusted(app):
    source = _repository_guard_selected_source_or_log(app)
    if source is None:
        return
    service = _repository_guard_service(app)
    if service is None:
        app.log(_repository_guard_service_unavailable_message())
        return
    trustlist_path = _repository_guard_trustlist_path(app)
    ok, err = service.mark_host_trusted(source, trustlist_path)
    _finish_repository_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message=(
            "Repository Guard: Host als vertraut markiert: "
            f"{source.get('host', '-') or '-'}"
        ),
    )


def remove_selected_repository_guard_trusted(app):
    source = _repository_guard_selected_source_or_log(app)
    if source is None:
        return
    service = _repository_guard_service(app)
    if service is None:
        app.log(_repository_guard_service_unavailable_message())
        return
    trustlist_path = _repository_guard_trustlist_path(app)
    ok, err = service.remove_host_trusted(source, trustlist_path)
    _finish_repository_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message=(
            "Repository Guard: Host aus Vertrauensliste entfernt: "
            f"{source.get('host', '-') or '-'}"
        ),
    )


def show_repository_guard_trustlist(app):
    service = _repository_guard_service(app)
    if service is None:
        app.log(_repository_guard_service_unavailable_message())
        return
    trustlist = _repository_guard_trustlist(app)
    trusted_hosts = dict(trustlist.get("trusted_hosts") or {})
    lines = ["=== Repository Guard Vertrauensliste ===", ""]
    if not trusted_hosts:
        lines.append(_repository_guard_empty_trustlist_message())
    else:
        for host, item in sorted(trusted_hosts.items()):
            lines.extend(_repository_guard_trustlist_host_lines(host, item))
    _set_detail_text(app, "\n".join(lines))
    app.log("Repository Guard: Vertrauensliste angezeigt.")


def reset_repository_guard_trustlist(app):
    service = _repository_guard_service(app)
    if service is None:
        app.log(_repository_guard_service_unavailable_message())
        return
    trustlist_path = _repository_guard_trustlist_path(app)
    ok, err = service.reset_trustlist(trustlist_path)
    _finish_repository_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message="Repository Guard: Vertrauensliste wurde zurückgesetzt.",
    )


def update_repository_guard_filter_status_line(app):
    source_labels = dict(
        getattr(app, "repository_guard_source_filter_labels", {}) or {}
    )
    finding_labels = dict(
        getattr(app, "repository_guard_finding_filter_labels", {}) or {}
    )

    source_mode = str(
        getattr(app, "repository_guard_source_filter_mode", "all") or "all"
    )
    _apply_repository_guard_filter_status(
        app,
        labels=source_labels,
        mode=source_mode,
        status_var_name="repository_guard_source_filter_status_var",
        choice_var_name="repository_guard_source_filter_choice_var",
        status_text_fn=_repository_guard_source_filter_status_text,
        default_key="all",
        default_label="Alle",
    )

    finding_mode = str(
        getattr(app, "repository_guard_finding_filter_mode", "all") or "all"
    )
    _apply_repository_guard_filter_status(
        app,
        labels=finding_labels,
        mode=finding_mode,
        status_var_name="repository_guard_finding_filter_status_var",
        choice_var_name="repository_guard_finding_filter_choice_var",
        status_text_fn=_repository_guard_finding_filter_status_text,
        default_key="relevant",
        default_label="Relevant",
    )


def update_repository_guard_status_light(app, state: str):
    light = _app_value(app, "repository_guard_status_light")
    item = _app_value(app, "repository_guard_status_light_item")
    if light is None or item is None:
        return
    color = _repository_guard_status_light_color(state)
    try:
        light.itemconfig(item, fill=color, outline=color)
    except Exception:
        pass


def _repository_guard_filter_choice_text(
    labels: dict,
    mode: str,
    *,
    default_key: str,
    default_label: str,
) -> str:
    label_map = dict(labels or {})
    normalized_mode = str(mode or "").strip().lower()
    return str(
        label_map.get(normalized_mode, label_map.get(default_key, default_label))
        or default_label
    )


def _repository_guard_empty_trustlist_message() -> str:
    return "Keine vertrauten Hosts gespeichert."


def _repository_guard_trustlist_host_lines(host: str, item: dict) -> list[str]:
    entry = dict(item or {})
    return [
        f"- Host: {host}",
        f"  URI: {entry.get('uri', '-')}",
        f"  Typ: {entry.get('repo_type', '-')}",
        f"  Markiert: {entry.get('trusted_at', '-')}",
        "",
    ]


def _apply_repository_guard_filter_status(
    app,
    *,
    labels: dict,
    mode: str,
    status_var_name: str,
    choice_var_name: str,
    status_text_fn,
    default_key: str,
    default_label: str,
) -> None:
    _app_var_set(app, status_var_name, status_text_fn(mode))
    _app_var_set(
        app,
        choice_var_name,
        _repository_guard_filter_choice_text(
            labels,
            mode,
            default_key=default_key,
            default_label=default_label,
        ),
    )


def _configure_repository_guard_finding_tags(tree):
    try:
        tree.tag_configure("critical", foreground="#b42318")
        tree.tag_configure("error", foreground="#b42318")
        tree.tag_configure("warning", foreground="#b54708")
        tree.tag_configure("notice", foreground="#175cd3")
        tree.tag_configure("info", foreground="#027a48")
    except Exception:
        pass


def _read_repository_guard_detail_text(app) -> str:
    widget = _app_value(app, "repository_guard_detail_text")
    if widget is None:
        return ""
    try:
        return widget.get("1.0", "end").strip()
    except Exception:
        return ""


def _repository_guard_details_header() -> str:
    return "=== Details ==="


def _repository_guard_report_payload(result: dict, details: str) -> str:
    payload = format_repository_guard_result(dict(result or {}))
    detail_text = str(details or "").strip()
    if not detail_text:
        return payload
    return f"{payload}\n\n{_repository_guard_details_header()}\n\n{detail_text}"


def _repository_guard_text_export_payload(result: dict) -> str:
    return format_repository_guard_result(dict(result or {})).rstrip("\n") + "\n"


def _repository_guard_json_export_payload(result: dict) -> str:
    return (
        json.dumps(dict(result or {}), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n"
    )


def _repository_guard_export_payload(path: str, result: dict) -> str:
    if str(path or "").strip().lower().endswith(".txt"):
        return _repository_guard_text_export_payload(result)
    return _repository_guard_json_export_payload(result)


def _apply_baseline_findings(result: dict, comparison: dict):
    findings = list(result.get("findings") or [])
    for source in list(comparison.get("new") or []):
        findings.append(
            {
                "id": f"finding:repo_baseline_new:{source.get('id', '-')}",
                "severity": "warning",
                "code": "repo_baseline_new",
                "title": "Neue Quelle seit Baseline",
                "summary": "Diese Quelle ist seit der letzten Baseline neu hinzugekommen.",
                "source_id": source.get("id", ""),
                "details": {
                    "file_path": source.get("file_path", ""),
                    "uri": source.get("uri", ""),
                },
            }
        )
    for source in list(comparison.get("removed") or []):
        findings.append(
            {
                "id": f"finding:repo_baseline_removed:{source.get('id', '-')}",
                "severity": "warning",
                "code": "repo_baseline_removed",
                "title": "Quelle seit Baseline entfernt",
                "summary": "Diese Quelle war in der letzten Baseline vorhanden, ist aktuell aber nicht mehr sichtbar.",
                "source_id": "",
                "details": {
                    "file_path": source.get("file_path", ""),
                    "uri": source.get("uri", ""),
                    "baseline_source_id": source.get("id", ""),
                },
            }
        )
    for item in list(comparison.get("moved") or []):
        after = dict(item.get("after") or {})
        before = dict(item.get("before") or {})
        findings.append(
            {
                "id": f"finding:repo_baseline_moved:{after.get('id') or before.get('id', '-')}",
                "severity": "notice",
                "code": "repo_baseline_moved",
                "title": "Quelle seit Baseline verschoben",
                "summary": "Diese Quelle ist weiterhin vorhanden, wurde aber an eine andere Stelle verschoben.",
                "source_id": after.get("id", "") or before.get("id", ""),
                "details": {
                    "file_path_before": before.get("file_path", ""),
                    "line_no_before": before.get("line_no", ""),
                    "file_path_after": after.get("file_path", ""),
                    "line_no_after": after.get("line_no", ""),
                    "uri": after.get("uri", "") or before.get("uri", ""),
                },
            }
        )
    for item in list(comparison.get("changed") or []):
        after = dict(item.get("after") or {})
        before = dict(item.get("before") or {})
        findings.append(
            {
                "id": f"finding:repo_baseline_changed:{after.get('id') or before.get('id', '-')}",
                "severity": "warning",
                "code": "repo_baseline_changed",
                "title": "Quelle seit Baseline geändert",
                "summary": "Diese Quelle hat sich seit der letzten Baseline verändert.",
                "source_id": after.get("id", "") or before.get("id", ""),
                "details": {
                    "file_path": after.get("file_path", "")
                    or before.get("file_path", ""),
                    "uri_before": before.get("uri", ""),
                    "uri_after": after.get("uri", ""),
                    "signed_by_before": before.get("signed_by", ""),
                    "signed_by_after": after.get("signed_by", ""),
                    "changed_fields": ", ".join(item.get("changed_fields") or []),
                },
            }
        )
    result["findings"] = sorted(
        findings,
        key=lambda item: (_severity_rank(item.get("severity")), item.get("id", "")),
    )
    summary = dict(result.get("summary") or {})
    summary["findings_total"] = len(result["findings"])
    summary["warning"] = sum(
        1 for item in result["findings"] if str(item.get("severity") or "") == "warning"
    )
    summary["notice"] = sum(
        1 for item in result["findings"] if str(item.get("severity") or "") == "notice"
    )
    summary["info"] = sum(
        1 for item in result["findings"] if str(item.get("severity") or "") == "info"
    )
    summary["critical"] = sum(
        1
        for item in result["findings"]
        if str(item.get("severity") or "") == "critical"
    )
    summary["errors"] = sum(
        1 for item in result["findings"] if str(item.get("severity") or "") == "error"
    )
    result["summary"] = summary


def _baseline_change_count(result: dict) -> int:
    baseline = dict(result.get("baseline") or {})
    return (
        len(list(baseline.get("new") or []))
        + len(list(baseline.get("removed") or []))
        + len(list(baseline.get("changed") or []))
        + len(list(baseline.get("moved") or []))
    )


def _severity_rank(severity: str | None) -> int:
    order = {
        "critical": 0,
        "error": 1,
        "warning": 2,
        "notice": 3,
        "info": 4,
    }
    return order.get(str(severity or "").strip().lower(), 9)


def _set_detail_text(app, text: str):
    widget = _app_value(app, "repository_guard_detail_text")
    if widget is None:
        return
    try:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", str(text or "").strip() + "\n")
        widget.configure(state="disabled")
    except Exception:
        pass


def _set_status(app, *, status: str, scan_status: str):
    _app_var_set(app, "repository_guard_status_var", status)
    _app_var_set(app, "repository_guard_scan_status_var", scan_status)


def _set_summary(app, text: str):
    _app_var_set(app, "repository_guard_summary_var", text)
