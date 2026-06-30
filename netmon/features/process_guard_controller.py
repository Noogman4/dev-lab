"""Process Guard controller helpers for NetMon."""

from __future__ import annotations

import threading
import time


def _tr(app, key: str, fallback: str) -> str:
    if app is None:
        return fallback
    tr = getattr(app, "tr", None)
    if callable(tr):
        try:
            return tr(key, fallback)
        except Exception:
            return fallback
    return fallback


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


def _process_guard_service(app):
    return getattr(app, "process_guard_service", None)


def _process_guard_service_unavailable_message(app=None) -> str:
    service = _process_guard_service(app) if app is not None else None
    if service is not None:
        try:
            reason = str(service.availability_reason() or "").strip()
        except Exception:
            reason = ""
        if reason:
            return _tr(
                app,
                "process_guard_service_unavailable_with_reason",
                "Process Guard: Service nicht verfügbar ({reason})",
            ).format(reason=reason)
    return _tr(
        app,
        "process_guard_service_unavailable",
        "Process Guard: Service nicht verfügbar.",
    )


def _process_guard_service_unavailable_details(app=None) -> str:
    message = _process_guard_service_unavailable_message(app)
    return "\n".join(
        [
            "=== Process Guard ===",
            "",
            message,
            "",
            _tr(
                app,
                "process_guard_requires_psutil",
                "Hinweis: Process Guard benötigt das Paket python3-psutil.",
            ),
        ]
    )


def _process_guard_service_or_log(app):
    service = _process_guard_service(app)
    if service is None:
        app.log(_process_guard_service_unavailable_message(app))
    return service


def _process_guard_available_service_or_log(app):
    service = _process_guard_service(app)
    if service is None:
        app.log(_process_guard_service_unavailable_message(app))
        return None
    if not service.is_available():
        app.log(_process_guard_service_unavailable_message(app))
        return None
    return service


def _process_guard_trustlist_path(app) -> str:
    return str(getattr(app, "process_guard_trustlist_path", "") or "").strip()


def _process_guard_trustlist(app):
    service = _process_guard_service(app)
    if service is None:
        return {"trusted": {}}
    return service.load_trustlist(_process_guard_trustlist_path(app))


def _finish_process_guard_trustlist_action(
    app, *, ok: bool, err: str, success_message: str
):
    if ok:
        app.log(success_message)
        run_process_guard_check(app)
    else:
        app.log(f"Process Guard: Trustlist Fehler: {err}")


def _selected_process_guard_finding(app):
    return getattr(app, "process_guard_selected_finding", None)


def _selected_process_guard_finding_or_log(app):
    finding = _selected_process_guard_finding(app)
    if not finding:
        app.log(_tr(app, "process_guard_no_finding_selected", "Process Guard: Kein Fund ausgewählt."))
        return None
    return finding


def _selected_process_guard_tree_index(tree):
    if tree is None:
        return None
    try:
        selection = tuple(tree.selection())
    except Exception:
        selection = ()
    if not selection:
        return None
    try:
        index = int(tree.index(selection[0]))
    except Exception:
        return None
    return index if index >= 0 else None


def _selected_process_guard_visible_finding(app, tree):
    index = _selected_process_guard_tree_index(tree)
    if index is None:
        return None
    visible_findings = _app_list(app, "process_guard_visible_findings")
    if index < 0 or index >= len(visible_findings):
        return None
    return visible_findings[index]


def _process_guard_finding_name(finding, default: str = "-") -> str:
    return str((finding or {}).get("name", default) or default)


def _process_guard_last_result(app) -> dict:
    return getattr(app, "process_guard_last_result", {}) or {}


def _normalized_process_guard_filter_mode(filter_mode: str) -> str:
    mode = str(filter_mode or "all").strip().lower()
    if mode not in {"all", "high", "high_medium"}:
        return "all"
    return mode


def _process_guard_filter_mode(app) -> str:
    return _normalized_process_guard_filter_mode(
        getattr(app, "process_guard_filter_mode", "all")
    )


def _process_guard_monitoring_status_text(app_or_monitoring, monitoring: bool | None = None) -> str:
    app = app_or_monitoring if monitoring is not None else None
    monitoring = app_or_monitoring if monitoring is None else monitoring
    if monitoring:
        return _tr(app, "process_guard_monitoring_on", "Monitoring: aktiv")
    return _tr(app, "process_guard_monitoring_off", "Monitoring: aus")


def _process_guard_filter_label(
    app_or_filter_mode, filter_mode: str | None = None, *, context: str = "status"
) -> str:
    app = app_or_filter_mode if filter_mode is not None else None
    filter_mode = app_or_filter_mode if filter_mode is None else filter_mode
    label_map = {
        "status": {
            "all": _tr(app, "process_guard_filter_status_all", "Filter: alle"),
            "high": _tr(app, "process_guard_filter_status_high", "Filter: nur hoch"),
            "high_medium": _tr(
                app,
                "process_guard_filter_status_high_medium",
                "Filter: hoch + mittel",
            ),
        },
        "log": {
            "all": _tr(app, "process_guard_filter_log_all", "alle Funde"),
            "high": _tr(app, "process_guard_filter_log_high", "nur hohe Risiken"),
            "high_medium": _tr(
                app,
                "process_guard_filter_log_high_medium",
                "hohe + mittlere Risiken",
            ),
        },
    }
    labels = label_map["log"] if context == "log" else label_map["status"]
    return labels.get(str(filter_mode or "all"), labels["all"])


def _process_guard_visible_count_text(app_or_findings, findings=None) -> str:
    app = app_or_findings if findings is not None else None
    findings = app_or_findings if findings is None else findings
    return _tr(app, "process_guard_visible_count", "Sichtbare Funde: {count}").format(
        count=len(list(findings or []))
    )


def _process_guard_status_values(app) -> dict:
    return {
        "monitoring": _process_guard_monitoring_status_text(
            app,
            getattr(app, "process_guard_monitoring", False)
        ),
        "filter": _process_guard_filter_label(
            app,
            _process_guard_filter_mode(app), context="status"
        ),
        "visible_count": _process_guard_visible_count_text(
            app,
            _app_list(app, "process_guard_visible_findings")
        ),
    }


def _apply_process_guard_status_values(app, values: dict) -> None:
    status_values = dict(values or {})
    _app_var_set(
        app,
        "process_guard_monitoring_status_var",
        status_values.get("monitoring", "Monitoring: aus"),
    )
    _app_var_set(
        app,
        "process_guard_filter_status_var",
        status_values.get("filter", "Filter: alle"),
    )
    _app_var_set(
        app,
        "process_guard_visible_count_var",
        status_values.get("visible_count", "Sichtbare Funde: 0"),
    )


def _process_guard_visible_findings(result: dict, filter_mode: str):
    all_findings = list((result or {}).get("findings", []) or [])
    normalized = str(filter_mode or "all").strip().lower()
    if normalized == "high":
        return [item for item in all_findings if item.get("risk_level") == "high"]
    if normalized == "high_medium":
        return [
            item
            for item in all_findings
            if item.get("risk_level") in {"high", "medium"}
        ]
    return all_findings


def _process_guard_tree_row_values(finding) -> tuple:
    item = dict(finding or {})
    return (
        str(item.get("risk_level", "-")).upper(),
        item.get("pid", "-"),
        item.get("name", "-"),
        item.get("user", "-"),
        item.get("exe", "-"),
    )


def _process_guard_empty_trustlist_message() -> str:
    return "- Keine bekannten Process-Guard-Ausnahmen gespeichert."


def _process_guard_trustlist_header() -> str:
    return "=== Process Guard Vertrauensliste ==="


def _process_guard_trustlist_lines(trusted: dict) -> list[str]:
    lines = [_process_guard_trustlist_header(), ""]
    trusted_items = dict(trusted or {})
    if not trusted_items:
        lines.append(_process_guard_empty_trustlist_message())
        return lines
    for signature, item in sorted(trusted_items.items()):
        lines.append(
            f"- {item.get('name', '-')} | {item.get('exe', '-')} | User: {item.get('user', '-')}"
        )
        lines.append(f"  Parent: {item.get('parent_name', '-')}")
        lines.append(f"  Signatur: {signature}")
    return lines


def _process_guard_counts(findings) -> dict:
    local_findings = list(findings or [])
    return {
        "high": sum(1 for item in local_findings if item.get("risk_level") == "high"),
        "medium": sum(
            1 for item in local_findings if item.get("risk_level") == "medium"
        ),
        "low": sum(1 for item in local_findings if item.get("risk_level") == "low"),
    }


def _process_guard_light_state_for_risk(app_or_risk, risk: str | None = None):
    app = app_or_risk if risk is not None else None
    risk = app_or_risk if risk is None else risk
    normalized = str(risk or "").strip().lower()
    if normalized in {"hoch", "high"}:
        return "error", _tr(
            app,
            "process_guard_state_suspicious",
            "Process Guard: verdächtige Prozesse erkannt",
        )
    if normalized in {"mittel", "medium"}:
        return "warning", _tr(
            app,
            "process_guard_state_review_required",
            "Process Guard: Prüfbedarf",
        )
    return "ok", _tr(
        app,
        "process_guard_state_no_issues",
        "Process Guard: keine Auffälligkeiten",
    )


def _process_guard_monitoring_state_for_findings(app_or_findings, findings=None):
    app = app_or_findings if findings is not None else None
    local_findings = list(app_or_findings if findings is None else findings or [])
    counts = _process_guard_counts(local_findings)
    if counts["high"]:
        return (
            "error",
            _tr(
                app,
                "process_guard_monitoring_new_suspicious",
                "Process Guard: neue verdächtige Prozesse erkannt",
            ),
            _tr(
                app,
                "process_guard_monitoring_new_findings",
                "Process Guard: {count} neuer Fund/Funde erkannt.",
            ).format(count=len(local_findings)),
        )
    if local_findings:
        return (
            "warning",
            _tr(
                app,
                "process_guard_monitoring_new_review_required",
                "Process Guard: neue Prozesse mit Prüfbedarf",
            ),
            _tr(
                app,
                "process_guard_monitoring_new_findings",
                "Process Guard: {count} neuer Fund/Funde erkannt.",
            ).format(count=len(local_findings)),
        )
    return (
        "ok",
        _tr(
            app,
            "process_guard_monitoring_no_new_issues",
            "Process Guard: Monitoring aktiv, keine neuen Auffälligkeiten",
        ),
        "",
    )


def format_process_guard_result(result: dict, app=None) -> str:
    if not result or not result.get("available", False):
        return "\n".join(
            [
                "=== Process Guard ===",
                "",
                _process_guard_service_unavailable_message(app),
            ]
        )

    findings = list(result.get("findings", []) or [])
    counts = dict(result.get("counts", {}) or {})
    lines = [
        "=== Process Guard ===",
        "",
        _tr(app, "process_guard_report_checked_processes", "Geprüfte Prozesse: {count}").format(
            count=result.get("processes_count", 0)
        ),
        _tr(app, "process_guard_report_risk", "Risiko: {value}").format(
            value=result.get("risk", "-")
        ),
        _tr(app, "process_guard_report_high", "Hoch: {count}").format(
            count=counts.get("high", 0)
        ),
        _tr(app, "process_guard_report_medium", "Mittel: {count}").format(
            count=counts.get("medium", 0)
        ),
        _tr(app, "process_guard_report_low", "Niedrig: {count}").format(
            count=counts.get("low", 0)
        ),
        "",
    ]

    if findings:
        lines.append(_tr(app, "process_guard_report_conspicuous", "Auffällige Prozesse:"))
        for finding in findings[:12]:
            lines.append(
                f"- [{finding.get('risk_level', '-').upper()}] "
                + _tr(app, "process_guard_report_finding_header", "{name} (PID {pid})").format(
                    name=finding.get("name", "-"),
                    pid=finding.get("pid", "-"),
                )
            )
            lines.append(
                "  "
                + _tr(app, "process_guard_report_path", "Pfad: {value}").format(
                    value=finding.get("exe", "-")
                )
            )
            lines.append(
                "  "
                + _tr(
                    app,
                    "process_guard_report_user_parent",
                    "User: {user} | Parent: {parent}",
                ).format(
                    user=finding.get("user", "-"),
                    parent=finding.get("parent_name", "-"),
                )
            )
            for reason in finding.get("reasons", [])[:3]:
                lines.append(f"  - {reason}")
        if len(findings) > 12:
            lines.append(
                _tr(
                    app,
                    "process_guard_report_more_findings",
                    "- ... {count} weitere Funde",
                ).format(count=len(findings) - 12)
            )
    else:
        lines.append(_tr(app, "process_guard_report_conspicuous", "Auffällige Prozesse:"))
        lines.append(
            _tr(
                app,
                "process_guard_report_none",
                "- Keine auffälligen Prozesse erkannt.",
            )
        )

    lines.extend(["", _tr(app, "process_guard_report_result_header", "=== Ergebnis ===")])
    if counts.get("high", 0):
        lines.append(
            _tr(
                app,
                "process_guard_report_result_high",
                "✖ Verdächtige Prozesse erkannt",
            )
        )
    elif counts.get("medium", 0):
        lines.append(
            _tr(
                app,
                "process_guard_report_result_medium",
                "○ Prozesse mit Prüfbedarf erkannt",
            )
        )
    else:
        lines.append(
            _tr(
                app,
                "process_guard_report_result_ok",
                "✔ Keine auffälligen Prozesse erkannt",
            )
        )
    return "\n".join(lines)


def format_process_guard_details(finding: dict, app=None) -> str:
    lines = [
        _tr(app, "process_guard_details_header", "=== Process Guard Fund ==="),
        "",
        f"PID: {finding.get('pid', '-')}",
        f"PPID: {finding.get('ppid', '-')}",
        _tr(app, "process_guard_details_name", "Name: {value}").format(
            value=finding.get("name", "-")
        ),
        _tr(app, "process_guard_details_user", "User: {value}").format(
            value=finding.get("user", "-")
        ),
        _tr(app, "process_guard_details_risk", "Risiko: {value}").format(
            value=str(finding.get("risk_level", "-")).upper()
        ),
        _tr(app, "process_guard_details_score", "Score: {value}").format(
            value=finding.get("risk_score", "-")
        ),
        _tr(app, "process_guard_details_path", "Pfad: {value}").format(
            value=finding.get("exe", "-")
        ),
        _tr(app, "process_guard_details_cwd", "Arbeitsverzeichnis: {value}").format(
            value=finding.get("cwd", "-")
        ),
        _tr(app, "process_guard_details_parent", "Parent: {value}").format(
            value=finding.get("parent_name", "-")
        ),
        "",
        _tr(app, "process_guard_details_cmdline", "Kommandozeile:"),
    ]
    cmdline = list(finding.get("cmdline") or [])
    if cmdline:
        lines.append(" ".join(str(part or "") for part in cmdline).strip())
    else:
        lines.append("-")
    lines.extend(["", _tr(app, "process_guard_details_reasons", "Gründe:")])
    for reason in list(finding.get("reasons") or []):
        lines.append(f"- {reason}")
    return "\n".join(lines)


def set_process_guard_filter(app, filter_mode: str):
    mode = _normalized_process_guard_filter_mode(filter_mode)
    app.process_guard_filter_mode = mode
    refresh_process_guard_tree(app)
    app.log(
        _tr(
            app,
            "process_guard_log_filter_active",
            "Process Guard: Filter aktiv - {label}.",
        ).format(label=_process_guard_filter_label(app, mode, context="log"))
    )


def _process_guard_detail_widget(app):
    return _app_value(app, "process_guard_detail") or _app_value(app, "security_detail")


def _write_process_guard_text(
    widget, text: str, *, replace: bool = False, see_target: str = "end"
) -> bool:
    if widget is None:
        return False
    widget.configure(state="normal")
    if replace:
        widget.delete("1.0", "end")
    elif widget.index("end-1c") != "1.0":
        widget.insert("end", "\n\n")
    widget.insert("end", text)
    widget.see(see_target)
    widget.configure(state="normal")
    return True


def _replace_process_guard_text(widget, text: str) -> bool:
    return _write_process_guard_text(widget, text, replace=True, see_target="1.0")


def _select_process_guard_tab(app):
    select_tab = getattr(app, "_select_security_tab", None)
    process_tab = _app_value(app, "tab_process_guard")
    if callable(select_tab) and process_tab is not None:
        select_tab(process_tab)


def update_process_guard_status_line(app):
    values = _process_guard_status_values(app)
    _apply_process_guard_status_values(app, values)


def show_process_guard_trustlist(app):
    service = _process_guard_service_or_log(app)
    if service is None:
        return
    _select_process_guard_tab(app)
    trustlist = _process_guard_trustlist(app)
    lines = _process_guard_trustlist_lines(trustlist.get("trusted") or {})
    _append_process_guard_text(app, "\n".join(lines))


def mark_selected_process_guard_trusted(app):
    finding = _selected_process_guard_finding_or_log(app)
    if not finding:
        return
    service = _process_guard_service_or_log(app)
    if service is None:
        return
    ok, err = service.mark_trusted(finding, _process_guard_trustlist_path(app))
    _finish_process_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message=(
            "Process Guard: Fund als bekannt markiert: "
            f"{_process_guard_finding_name(finding)}"
        ),
    )


def remove_selected_process_guard_trusted(app):
    finding = _selected_process_guard_finding_or_log(app)
    if not finding:
        return
    service = _process_guard_service_or_log(app)
    if service is None:
        return
    ok, err = service.remove_trusted(finding, _process_guard_trustlist_path(app))
    _finish_process_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message=(
            "Process Guard: Fund aus Vertrauensliste entfernt: "
            f"{_process_guard_finding_name(finding)}"
        ),
    )


def reset_process_guard_trustlist(app):
    service = _process_guard_service_or_log(app)
    if service is None:
        return
    ok, err = service.reset_trustlist(_process_guard_trustlist_path(app))
    _finish_process_guard_trustlist_action(
        app,
        ok=ok,
        err=err,
        success_message="Process Guard: Vertrauensliste wurde zurückgesetzt.",
    )


def refresh_process_guard_tree(app):
    tree = _app_value(app, "process_guard_tree")
    if tree is None:
        return

    for item in tree.get_children():
        tree.delete(item)

    visible_findings = _process_guard_visible_findings(
        _process_guard_last_result(app),
        _process_guard_filter_mode(app),
    )

    app.process_guard_visible_findings = visible_findings
    app.process_guard_selected_finding = None

    for index, finding in enumerate(visible_findings):
        iid = f"pg-{index}"
        tree.insert(
            "",
            "end",
            iid=iid,
            values=_process_guard_tree_row_values(finding),
        )
    update_process_guard_status_line(app)


def on_process_guard_select(app, _event=None):
    tree = _app_value(app, "process_guard_tree")
    finding = _selected_process_guard_visible_finding(app, tree)
    if not finding:
        return
    app.process_guard_selected_finding = finding
    details = format_process_guard_details(finding, app)
    _replace_process_guard_text(_process_guard_detail_widget(app), details)


def _process_guard_light_values(state: str, message: str = "") -> tuple[str, str]:
    status_text = message or ""
    if state == "ok":
        return "green", status_text or "Process Guard: keine Auffälligkeiten"
    if state == "warning":
        return "yellow", status_text or "Process Guard: Prüfbedarf"
    if state == "error":
        return "red", status_text or "Process Guard: verdächtige Prozesse erkannt"
    return "gray", status_text or "Process Guard: noch nicht geprüft"


def _process_guard_monitoring_status_message(app_or_state, state: str | None = None) -> str:
    app = app_or_state if state is not None else None
    state = app_or_state if state is None else state
    return {
        "active": _tr(
            app,
            "process_guard_monitoring_status_active",
            "Process Guard: Monitoring aktiv",
        ),
        "stopped": _tr(
            app,
            "process_guard_monitoring_status_stopped",
            "Process Guard: Monitoring gestoppt",
        ),
    }.get(
        str(state or "").strip().lower(),
        _tr(
            app,
            "process_guard_monitoring_status_unknown",
            "Process Guard: Monitoring unbekannt",
        ),
    )


def _process_guard_monitoring_log_message(app_or_state, state: str | None = None) -> str:
    app = app_or_state if state is not None else None
    state = app_or_state if state is None else state
    return {
        "active": _tr(
            app,
            "process_guard_monitoring_log_started",
            "Process Guard: Monitoring gestartet.",
        ),
        "stopped": _tr(
            app,
            "process_guard_monitoring_log_stopped",
            "Process Guard: Monitoring gestoppt.",
        ),
    }.get(
        str(state or "").strip().lower(),
        _tr(
            app,
            "process_guard_monitoring_log_unknown",
            "Process Guard: Monitoring unbekannt.",
        ),
    )


def set_process_guard_light(app, state: str, message: str = ""):
    app.process_guard_last_state = str(state or "unknown")
    color, status_text = _process_guard_light_values(state, message)
    app.set_light(app.l_process_guard, color)
    app.process_guard_status_var.set(status_text)
    update_process_guard_status_line(app)


def _append_process_guard_text(app, text: str):
    detail_widget = _process_guard_detail_widget(app)
    _write_process_guard_text(detail_widget, text, replace=False, see_target="end")


def _scroll_process_guard_details_into_view(app) -> None:
    _select_process_guard_tab(app)
    detail_widget = _process_guard_detail_widget(app)
    if detail_widget is not None:
        try:
            detail_widget.see("1.0")
            detail_widget.focus_set()
        except Exception:
            pass
    scroll_fn = _app_value(app, "scroll_main_page_to_widget")
    if callable(scroll_fn) and detail_widget is not None:
        try:
            scroll_fn(detail_widget)
        except Exception:
            pass
    scroll_later_fn = _app_value(app, "scroll_main_page_to_widget_later")
    if callable(scroll_later_fn) and detail_widget is not None:
        try:
            scroll_later_fn(detail_widget, top_margin=16, delay_ms=100, repeat=4)
        except Exception:
            pass


def run_process_guard_check(app):
    try:
        _select_process_guard_tab(app)
        service = _process_guard_available_service_or_log(app)
        if service is None:
            message = _process_guard_service_unavailable_message(app)
            set_process_guard_light(app, "unknown", message)
            _replace_process_guard_text(
                _process_guard_detail_widget(app),
                _process_guard_service_unavailable_details(app),
            )
            return

        trustlist = _process_guard_trustlist(app)
        result = service.run_check(trustlist=trustlist)
        app.process_guard_last_result = result
        text = format_process_guard_result(result, app)
        light_state, status_text = _process_guard_light_state_for_risk(
            app,
            result.get("risk")
        )
        set_process_guard_light(app, light_state, status_text)

        refresh_process_guard_tree(app)
        _append_process_guard_text(app, text)
        _scroll_process_guard_details_into_view(app)
        app.log(f"Process Guard: Prüfung abgeschlossen (Risiko: {result.get('risk', '-')}).")
    except Exception as exc:
        set_process_guard_light(app, "error", "Process Guard: error during check")
        app.log(f"Process Guard: error: {exc}")


def analyze_process_guard_with_chad(app):
    result = _process_guard_last_result(app)
    if not result:
        app.log("Process Guard: no check available.")
        return
    app.prepare_chad_analysis(
        "Process Guard Analyse", format_process_guard_result(result, app)
    )


def analyze_selected_process_guard_with_chad(app):
    finding = _selected_process_guard_finding_or_log(app)
    if not finding:
        return
    app.prepare_chad_analysis(
        "Process Guard Fund Analyse",
        format_process_guard_details(finding, app),
    )


def apply_process_guard_monitoring_snapshot(app, processes, findings):
    local_findings = list(findings or [])
    counts = _process_guard_counts(local_findings)
    app.process_guard_last_result = {
        "available": True,
        "processes_count": len(list(processes or [])),
        "findings": local_findings,
        "risk": (
            "high" if counts["high"] else ("medium" if local_findings else "low")
        ),
        "counts": counts,
    }
    text = format_process_guard_result(app.process_guard_last_result, app)
    light_state, status_text, log_message = _process_guard_monitoring_state_for_findings(
        app, local_findings
    )
    set_process_guard_light(app, light_state, status_text)
    if log_message:
        app.log(log_message)
    refresh_process_guard_tree(app)
    _append_process_guard_text(app, text)


def start_process_guard_monitoring(app):
    if getattr(app, "process_guard_monitoring", False):
        app.log("Process Guard: monitoring is already running.")
        return
    _select_process_guard_tab(app)
    service = _process_guard_available_service_or_log(app)
    if service is None:
        message = _process_guard_service_unavailable_message(app)
        set_process_guard_light(app, "unknown", message)
        _replace_process_guard_text(
            _process_guard_detail_widget(app),
            _process_guard_service_unavailable_details(app),
        )
        return

    app.process_guard_monitoring = True
    app.process_guard_status_var.set(
        _process_guard_monitoring_status_message(app, "active")
    )
    update_process_guard_status_line(app)
    app.log(_process_guard_monitoring_log_message(app, "active"))

    def worker():
        while getattr(app, "process_guard_monitoring", False):
            try:
                processes = service.snapshot_processes()
                findings, known = service.detect_new_findings(
                    processes,
                    getattr(app, "process_guard_known_processes", set()),
                    trustlist=_process_guard_trustlist(app),
                )
                app.process_guard_known_processes = known
                app.after(
                    0,
                    lambda current_processes=list(processes), current_findings=list(
                        findings
                    ): apply_process_guard_monitoring_snapshot(
                        app,
                        current_processes,
                        current_findings,
                    ),
                )
            except Exception as exc:
                app.after(
                    0,
                    lambda error_text=str(exc): app.log(
                        f"Process Guard monitoring error: {error_text}"
                    ),
                )
            time.sleep(4)

    app.process_guard_monitor_thread = threading.Thread(target=worker, daemon=True)
    app.process_guard_monitor_thread.start()


def stop_process_guard_monitoring(app):
    if not getattr(app, "process_guard_monitoring", False):
        app.log("Process Guard: monitoring is already stopped.")
        return
    app.process_guard_monitoring = False
    app.process_guard_status_var.set(
        _process_guard_monitoring_status_message(app, "stopped")
    )
    update_process_guard_status_line(app)
    app.log(_process_guard_monitoring_log_message(app, "stopped"))
