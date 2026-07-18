"""Security audit controller helpers for NetMon."""

from __future__ import annotations

import os
import re
import threading
from datetime import datetime
from time import monotonic
from tkinter import messagebox

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd

try:
    from netmon.services.rkhunter_analysis_service import (
        analyze_rkhunter_output,
        extract_replaced_script_paths,
        extract_warning_command_paths,
    )
except ModuleNotFoundError:
    from services.rkhunter_analysis_service import (
        analyze_rkhunter_output,
        extract_replaced_script_paths,
        extract_warning_command_paths,
    )


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


def open_lynis_tab(app):
    app._select_security_tab(app.tab_lynis)


def _lynis_running(app) -> bool:
    return bool(_app_value(app, "lynis_running", False))


def _lynis_summary_text(app_or_mode, mode: str | None = None) -> str:
    app = app_or_mode if mode is not None else None
    mode = app_or_mode if mode is None else mode
    return (
        _tr(app, "lynis_summary_running_quick", "Schnellaudit wird ausgeführt ...")
        if mode == "quick"
        else _tr(
            app,
            "lynis_summary_running_full",
            "Vollständiger Sicherheitsscan wird ausgeführt ...",
        )
    )


def _lynis_start_log_message(app_or_mode, mode: str | None = None) -> str:
    app = app_or_mode if mode is not None else None
    mode = app_or_mode if mode is None else mode
    return (
        _tr(
            app,
            "lynis_log_quick_started",
            "Lynis Schnellaudit gestartet (ohne root)",
        )
        if mode == "quick"
        else _tr(
            app,
            "lynis_log_full_started",
            "Lynis Vollscan gestartet (sudo erforderlich)",
        )
    )


def _lynis_finish_log_message(
    app_or_mode, mode: str | None = None, rc: int | None = None
) -> str:
    if rc is None:
        app = None
        rc = mode
        mode = app_or_mode
    else:
        app = app_or_mode
    label = (
        _tr(app, "lynis_mode_quick", "Schnellaudit")
        if mode == "quick"
        else _tr(app, "lynis_mode_full", "Vollscan")
    )
    if rc == 0:
        return _tr(
            app,
            "lynis_log_finished",
            "Lynis {label} abgeschlossen.",
        ).format(label=label)
    if rc == 124:
        return _tr(
            app,
            "lynis_log_timeout",
            "Lynis {label} Timeout (rc=124).",
        ).format(label=label)
    return _tr(
        app,
        "lynis_log_failed",
        "Lynis {label} fehlgeschlagen (rc={rc}).",
    ).format(label=label, rc=rc)


def _set_text_widget_content(widget, text: str, *, append: bool = False):
    if widget is None:
        return
    widget.configure(state="normal")
    if not append:
        widget.delete("1.0", "end")
    if text:
        if append and widget.index("end-1c") != "1.0":
            widget.insert("end", "\n\n")
        widget.insert("end", text)
    widget.see("end")
    widget.configure(state="disabled")


def clear_lynis_output(app):
    widget = _app_value(app, "lynis_text")
    if widget is None:
        return
    _set_text_widget_content(widget, "", append=False)
    app.lynis_last_output = ""
    if not bool(_app_value(app, "lynis_running", False)):
        _app_var_set(
            app,
            "lynis_summary_var",
            app.tr("lynis_summary_default", "Noch kein Audit ausgeführt."),
        )


def update_lynis_output(app, text: str, *, append: bool = False, normalize_output_fn):
    widget = _app_value(app, "lynis_text")
    if widget is None:
        return
    clean_text = normalize_output_fn(text)
    _set_text_widget_content(widget, clean_text, append=append)


def extract_lynis_issues_and_recommendations(
    app, text: str, *, normalize_output_fn
) -> str:
    text = normalize_output_fn(text)

    keep_keywords = [
        "warning",
        "warnings",
        "suggestion",
        "suggestions",
        "recommendation",
        "recommendations",
        "found",
        "not found",
        "disabled",
        "not enabled",
        "nicht gefunden",
        "nicht aktiviert",
        "dateien gefunden",
        "unsicher",
        "fehler",
        "problem",
        "hardening",
    ]

    lines = []
    for line in text.splitlines():
        low = line.lower()
        if any(keyword in low for keyword in keep_keywords):
            if "gefunden" in low and not (
                "dateien gefunden" in low
                or "warn" in low
                or "problem" in low
                or "fehler" in low
            ):
                continue
            lines.append(line)

    if not lines:
        return app.tr(
            "lynis_issues_header_empty",
            "=== Lynis Probleme & Empfehlungen ===\n\nKeine klaren Probleme oder Empfehlungen gefunden.",
        )

    return app.tr(
        "lynis_issues_header",
        "=== Lynis Probleme & Empfehlungen ===\n\n",
    ) + "\n".join(lines)


def show_lynis_issues_only(app, *, normalize_output_fn):
    text = _app_value(app, "lynis_last_output", "") or ""
    if not text.strip():
        app.log(app.tr("lynis_log_no_output", "Lynis: Keine Ausgabe vorhanden."))
        return

    filtered = extract_lynis_issues_and_recommendations(
        app,
        text,
        normalize_output_fn=normalize_output_fn,
    )
    _set_text_widget_content(_app_value(app, "lynis_text"), filtered, append=False)


def show_lynis_full_output(app):
    text = _app_value(app, "lynis_last_output", "") or ""
    if not text.strip():
        return

    _set_text_widget_content(_app_value(app, "lynis_text"), text, append=False)


def analyze_lynis_issues_with_chad(app, *, normalize_output_fn):
    text = _app_value(app, "lynis_last_output", "") or ""
    if not text.strip():
        app.log(app.tr("lynis_log_no_output", "Lynis: Keine Ausgabe vorhanden."))
        return

    filtered = extract_lynis_issues_and_recommendations(
        app,
        text,
        normalize_output_fn=normalize_output_fn,
    )
    app.prepare_chad_analysis(
        app.tr("lynis_chad_analysis_title", "Lynis issues analysis"),
        filtered,
    )


def update_lynis_summary_from_output(app, output: str, rc: int, *, normalize_output_fn):
    cleaned_output = normalize_output_fn(output)

    def extract_value(label):
        patterns = [
            rf"{label}\s*\((\d+)\)",
            rf"{label}\s*:?\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, cleaned_output, re.IGNORECASE)
            if match:
                return match.group(1)
        return "-"

    hardening = extract_value("Hardening index")
    warnings_count = extract_value("Warnings")
    suggestions_count = extract_value("Suggestions")

    status = (
        app.tr("lynis_status_ok", "OK")
        if rc == 0
        else app.tr("lynis_status_error_rc", "Error (rc={rc})").format(rc=rc)
    )
    _app_var_set(
        app,
        "lynis_summary_var",
        app.tr(
            "lynis_summary_result",
            "Status: {status} | Hardening Index: {hardening} | Warnings: {warnings_count} | Suggestions: {suggestions_count}",
        ).format(
            status=status,
            hardening=hardening,
            warnings_count=warnings_count,
            suggestions_count=suggestions_count,
        ),
    )
    app.lynis_last_result = {
        "rc": rc,
        "hardening_index": hardening,
        "warnings": warnings_count,
        "suggestions": suggestions_count,
    }


def set_lynis_buttons_state(app, enabled: bool):
    state = "normal" if enabled else "disabled"
    dep_status = _app_value(app, "dep_status", {}) or {}
    feature_enabled = bool(dep_status.get("lynis"))
    quick_btn = _app_value(app, "btn_lynis_quick")
    if quick_btn is not None:
        quick_btn.configure(state=state if enabled and feature_enabled else "disabled")
    full_btn = _app_value(app, "btn_lynis_full")
    if full_btn is not None:
        full_btn.configure(state=state if enabled and feature_enabled else "disabled")


def finish_lynis_audit(app, rc, out, *, mode: str = "quick", normalize_output_fn):
    app.lynis_running = False
    app.lynis_active_process = None
    clean_output = normalize_output_fn(out or app.tr("lynis_output_none", "No output."))
    app.lynis_last_output = clean_output
    timed_out = rc == 124
    _app_var_set(
        app,
        "lynis_status_var",
        (
            _tr(app, "lynis_status_finished", "abgeschlossen")
            if rc == 0
            else (
                _tr(app, "lynis_status_timeout", "Timeout")
                if timed_out
                else _tr(app, "lynis_status_error_rc", "Fehler (rc={rc})").format(rc=rc)
            )
        ),
    )
    app.update_lynis_output(clean_output, append=False)
    update_lynis_summary_from_output(
        app,
        clean_output,
        rc,
        normalize_output_fn=normalize_output_fn,
    )
    set_lynis_buttons_state(app, True)
    app.log(_lynis_finish_log_message(app, mode, rc))


def lynis_scan_worker(
    app,
    cmd,
    timeout: int,
    mode: str,
    header: str,
    *,
    normalize_output_fn,
    run_cmd_fn=None,
):
    runner = run_cmd_fn or run_cmd
    rc, out = runner(cmd, timeout=timeout)
    clean = normalize_output_fn(out)
    if rc == 124:
        timeout_note = app.tr(
            "lynis_timeout_note",
            "Scan stopped after {timeout}s (timeout).\nNote: Full scans can take longer depending on the system.",
        ).format(timeout=timeout)
        clean = normalize_output_fn(
            f"{timeout_note}\n\n{clean}" if clean else timeout_note
        )
    output = normalize_output_fn(
        f"{header}\n\n{clean or app.tr('lynis_output_none', 'No output.')}"
    )
    app.after(
        0,
        lambda r=rc, o=output, m=mode: app._finish_lynis_audit(r, o, mode=m),
    )


def start_lynis_scan(
    app,
    *,
    mode: str,
    cmd,
    timeout: int,
    header: str,
    has_cmd_fn=None,
    threading_module=None,
):
    has_cmd_runner = has_cmd_fn or has_cmd
    threading_runner = threading_module or threading
    if _lynis_running(app):
        app.log_safe(
            app.tr("lynis_log_already_running", "Lynis audit is already running.")
        )
        app.open_lynis_tab()
        return
    if not has_cmd_runner("lynis"):
        app.lynis_status_var.set(app.tr("lynis_status_not_installed", "not installed"))
        app.lynis_summary_var.set(
            app.tr(
                "lynis_summary_missing",
                "Lynis is missing. Installation hint available in the log.",
            )
        )
        app.update_lynis_output(
            app.tr(
                "lynis_output_missing",
                "Lynis is not installed. Please use the installation hint from the log.",
            )
        )
        app.show_lynis_install_hint()
        app.open_lynis_tab()
        return

    app.lynis_running = True
    app.lynis_active_process = "thread"
    app.lynis_status_var.set(app.tr("lynis_status_running", "running"))
    app.lynis_summary_var.set(_lynis_summary_text(app, mode))
    app.open_lynis_tab()
    app.clear_lynis_output()
    app.update_lynis_output(
        f"{header}\n\n{app.tr('lynis_output_scan_started', 'Scan started. Output will follow ...')}"
    )
    app._set_lynis_buttons_state(False)
    app.log(_lynis_start_log_message(app, mode))
    threading_runner.Thread(
        target=app._lynis_scan_worker,
        args=(cmd, timeout, mode, header),
        daemon=True,
    ).start()


def run_lynis_quick(app):
    app._start_lynis_scan(
        mode="quick",
        cmd=["lynis", "audit", "system", "--no-colors"],
        timeout=120,
        header=app.tr(
            "lynis_header_quick",
            "=== Lynis Schnellaudit (eingeschränkt) ===",
        ),
    )


def run_lynis_full(app):
    messagebox.showinfo(
        app.tr("lynis_full_info_title", "Lynis Vollscan"),
        app.tr(
            "lynis_full_info_body",
            "Dieser Scan benötigt Administratorrechte (sudo).\n\nEr führt eine vollständige Sicherheitsprüfung durch.",
        ),
        parent=app,
    )
    if not app.ensure_sudo_session("Lynis Full Security Scan"):
        return
    app._start_lynis_scan(
        mode="full",
        cmd=["sudo", "lynis", "audit", "system", "--no-colors"],
        timeout=600,
        header=app.tr(
            "lynis_header_full",
            "=== Lynis Vollständiger Sicherheitsscan (sudo) ===",
        ),
    )


def lynis_audit_async(app):
    app.run_lynis_quick()


def set_rkhunter_repair_available(app, enabled):
    app.rkhunter_repair_available = bool(enabled)
    repair_btn = _app_value(app, "btn_rkhunter_repair")
    if repair_btn is not None:
        repair_btn.configure(
            state="normal" if app.rkhunter_repair_available else "disabled"
        )


def open_rkhunter_tab(app):
    app._select_security_tab(app.tab_rkhunter)


def update_rkhunter_output(app, text: str, *, append: bool = False):
    _set_text_widget_content(_app_value(app, "rkhunter_text"), text, append=append)


def show_rkhunter_scan_output(app):
    app.open_rkhunter_tab()
    text = _app_value(app, "rkhunter_last_scan_output", "") or ""
    if not text.strip():
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_no_scan_view",
                "No rkhunter scan output is available yet.",
            )
        )
        return
    app.update_rkhunter_output(text, append=False)


def clear_rkhunter_output(app):
    update_rkhunter_output(app, "")
    app.rkhunter_last_result = {}
    app.rkhunter_last_scan_output = ""
    set_rkhunter_propupd_available(app, False)
    if not bool(_app_value(app, "rkhunter_running", False)) and not bool(
        _app_value(app, "rkhunter_updating", False)
    ):
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr("rkhunter_summary_default", "No scan executed yet."),
        )


def set_rkhunter_propupd_available(app, enabled):
    app.rkhunter_propupd_available = bool(enabled)
    button = _app_value(app, "btn_rkhunter_propupd")
    if button is not None:
        button.configure(
            state="normal" if app.rkhunter_propupd_available else "disabled"
        )


def set_rkhunter_progress(app, value: int, message: str):
    value = max(0, min(100, int(value)))
    progress_var = _app_value(app, "rkhunter_progress_var")
    if progress_var is not None:
        progress_var.set(value)
    progress_text_var = _app_value(app, "rkhunter_progress_text_var")
    if progress_text_var is not None:
        progress_text_var.set(message)
    progress_bar = _app_value(app, "rkhunter_progress_bar")
    if progress_bar is not None:
        progress_bar.configure(value=value)


def _set_rkhunter_progress_value(app, value: int):
    value = max(0, min(100, int(value)))
    progress_var = _app_value(app, "rkhunter_progress_var")
    if progress_var is not None:
        progress_var.set(value)
    progress_bar = _app_value(app, "rkhunter_progress_bar")
    if progress_bar is not None:
        progress_bar.configure(value=value)


def start_rkhunter_progress_animation(app, *, duration_seconds: int = 120):
    app.rkhunter_progress_animation_started_at = monotonic()
    app.rkhunter_progress_animation_duration = max(1, int(duration_seconds))
    app.rkhunter_progress_animation_active = True
    _animate_rkhunter_progress(app)


def stop_rkhunter_progress_animation(app):
    app.rkhunter_progress_animation_active = False
    after_id = _app_value(app, "rkhunter_progress_animation_after_id")
    if after_id:
        try:
            app.after_cancel(after_id)
        except Exception:
            pass
    app.rkhunter_progress_animation_after_id = None


def _animate_rkhunter_progress(app):
    if not bool(_app_value(app, "rkhunter_progress_animation_active", False)):
        return
    if not bool(_app_value(app, "rkhunter_running", False)):
        stop_rkhunter_progress_animation(app)
        return

    started_at = float(_app_value(app, "rkhunter_progress_animation_started_at", 0.0))
    duration = int(_app_value(app, "rkhunter_progress_animation_duration", 120))
    elapsed = max(0.0, monotonic() - started_at)
    target = min(92, 10 + int((elapsed / duration) * 82))
    progress_var = _app_value(app, "rkhunter_progress_var")
    try:
        current = int(progress_var.get()) if progress_var is not None else 0
    except Exception:
        current = 0
    if target > current:
        _set_rkhunter_progress_value(app, target)
    app.rkhunter_progress_animation_after_id = app.after(
        1000, lambda: _animate_rkhunter_progress(app)
    )


def _rkhunter_propupd_gate_valid(result) -> bool:
    result = result if isinstance(result, dict) else {}
    critical_flags = result.get("critical_flags") or {}
    return bool(
        result.get("propupd_allowed") is True
        and result.get("risk") == "low"
        and result.get("scan_completed") is True
        and result.get("dpkg_verified") is True
        and not result.get("critical")
        and not result.get("review")
        and not any(critical_flags.values())
    )


def _rkhunter_risk_label(app, risk: str) -> str:
    labels = {
        "low": app.tr("rkhunter_risk_low", "Low"),
        "medium": app.tr("rkhunter_risk_medium", "Medium"),
        "high": app.tr("rkhunter_risk_high", "High"),
    }
    return labels.get(risk, labels["medium"])


def _rkhunter_propupd_blockers(app, result) -> list[str]:
    result = result if isinstance(result, dict) else {}
    blockers = []
    if result.get("scan_completed") is not True:
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_scan_incomplete",
                "scan did not complete cleanly",
            )
        )
    if result.get("risk") != "low":
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_risk_not_low",
                "overall risk is not low",
            )
        )
    if result.get("dpkg_verified") is not True:
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_dpkg",
                "dpkg verification is not clean",
            )
        )
    if result.get("critical"):
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_critical",
                "critical findings are present",
            )
        )
    if result.get("review"):
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_review",
                "unexplained warnings require review",
            )
        )
    critical_flags = result.get("critical_flags") or {}
    if any(critical_flags.values()):
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_safety_flags",
                "security safety checks are not satisfied",
            )
        )
    if not blockers and result.get("propupd_allowed") is not True:
        blockers.append(
            app.tr(
                "rkhunter_propupd_block_gate",
                "safety gate is not satisfied",
            )
        )
    return blockers


def _format_rkhunter_finding_group(app, title_key, title_fallback, findings):
    if not findings:
        return []
    lines = [app.tr(title_key, title_fallback)]
    for item in findings[:12]:
        lines.append(f"- {item.get('line', '').strip()}")
    if len(findings) > 12:
        lines.append(
            app.tr(
                "rkhunter_analysis_more_findings",
                "- {count} additional findings are available in the raw output.",
            ).format(count=len(findings) - 12)
        )
    return lines


def format_rkhunter_analysis(app, result) -> str:
    risk = result.get("risk", "medium")
    risk_label = _rkhunter_risk_label(app, risk)
    if risk == "high":
        assessment = app.tr(
            "rkhunter_analysis_assessment_high",
            "Security-critical indicators were detected. Do not update the reference database.",
        )
        recommendations = [
            app.tr(
                "rkhunter_analysis_recommend_isolate",
                "Disconnect the system from untrusted networks and verify the critical findings from a trusted environment.",
            ),
            app.tr(
                "rkhunter_analysis_recommend_packages",
                "Verify affected system programs with the package manager before replacing or restoring files.",
            ),
        ]
    elif risk == "medium":
        assessment = app.tr(
            "rkhunter_analysis_assessment_medium",
            "No confirmed rootkit was identified, but one or more findings require manual verification.",
        )
        recommendations = [
            app.tr(
                "rkhunter_analysis_recommend_review",
                "Check the origin, owner, package assignment, and modification time of every yellow finding.",
            ),
            app.tr(
                "rkhunter_analysis_recommend_rescan",
                "Resolve unexplained changes and run rkhunter and dpkg verification again.",
            ),
        ]
    else:
        assessment = app.tr(
            "rkhunter_analysis_assessment_low",
            "No security-critical indicators were detected. Reported changes match known system or development patterns.",
        )
        recommendations = [
            app.tr(
                "rkhunter_analysis_recommend_updates",
                "Keep system packages and rkhunter data current and repeat the scan after significant updates.",
            )
        ]
        if result.get("propupd_allowed"):
            recommendations.append(
                app.tr(
                    "rkhunter_propupd_recommendation",
                    "The system appears trustworthy. The rkhunter file properties can be accepted as the new reference.",
                )
            )
    if not _rkhunter_propupd_gate_valid(result):
        recommendations.append(
            app.tr(
                "rkhunter_propupd_blocked_summary",
                "Reference acceptance locked: {reasons}.",
            ).format(reasons=", ".join(_rkhunter_propupd_blockers(app, result)))
        )

    finding_lines = []
    finding_lines.extend(
        _format_rkhunter_finding_group(
            app,
            "rkhunter_analysis_critical_heading",
            "Critical:",
            result.get("critical") or [],
        )
    )
    finding_lines.extend(
        _format_rkhunter_finding_group(
            app,
            "rkhunter_analysis_review_heading",
            "Review recommended:",
            result.get("review") or [],
        )
    )
    if not finding_lines:
        finding_lines.append(
            app.tr(
                "rkhunter_analysis_no_relevant_findings",
                "No security-relevant anomalies were detected.",
            )
        )

    expected = result.get("expected") or []
    false_positive_lines = [
        f"- {item.get('line', '').strip()}" for item in expected[:12]
    ] or [
        app.tr(
            "rkhunter_analysis_no_false_positives",
            "No typical false-positive pattern required a separate explanation.",
        )
    ]

    return "\n".join(
        [
            app.tr(
                "rkhunter_analysis_heading",
                "=== Intelligent rkhunter analysis ===",
            ),
            "",
            app.tr("rkhunter_analysis_short_heading", "1. Short assessment"),
            assessment,
            "",
            app.tr("rkhunter_analysis_findings_heading", "2. Relevant findings"),
            *finding_lines,
            "",
            app.tr("rkhunter_analysis_risk_heading", "3. Risk"),
            risk_label,
            "",
            app.tr(
                "rkhunter_analysis_recommendations_heading",
                "4. Recommended actions",
            ),
            *(f"- {item}" for item in recommendations),
            "",
            app.tr(
                "rkhunter_analysis_false_positives_heading",
                "5. Typical false-positive classification",
            ),
            *false_positive_lines,
        ]
    )


def update_rkhunter_summary_from_output(
    app,
    output: str,
    rc: int,
    *,
    dpkg_output: str = "",
    dpkg_rc: int | None = None,
    dpkg_owner_output: str = "",
    file_type_output: str = "",
):
    cleaned_output = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output or "")
    warning_count = len(re.findall(r"\bWarning\b", cleaned_output, re.IGNORECASE))
    ok_count = len(re.findall(r"\bOK\b", cleaned_output, re.IGNORECASE))
    result = analyze_rkhunter_output(
        cleaned_output,
        rc,
        dpkg_output=dpkg_output,
        dpkg_rc=dpkg_rc,
        dpkg_owner_output=dpkg_owner_output,
        file_type_output=file_type_output,
    )
    status = _rkhunter_risk_label(app, result["risk"])

    _app_var_set(
        app,
        "rkhunter_summary_var",
        app.tr(
            "rkhunter_summary_intelligent_result",
            "Risk: {risk} | Expected: {expected_count} | Review: {review_count} | Critical: {critical_count}",
        ).format(
            risk=status,
            expected_count=len(result["expected"]),
            review_count=len(result["review"]),
            critical_count=len(result["critical"]),
        ),
    )
    result.update(
        {
            "warnings": warning_count,
            "ok": ok_count,
            "suspect_hits": len(result["critical"]),
            "status": status,
        }
    )
    app.rkhunter_last_result = result
    set_rkhunter_propupd_available(app, _rkhunter_propupd_gate_valid(result))
    return result


def _set_rkhunter_action_buttons_state(app, enabled: bool):
    dep_status = _app_value(app, "dep_status", {}) or {}
    state = "normal" if enabled and dep_status.get("rkhunter") else "disabled"
    update_btn = _app_value(app, "btn_rkhunter_update")
    if update_btn is not None:
        update_btn.configure(state=state)
    scan_btn = _app_value(app, "btn_rkhunter_scan")
    if scan_btn is not None:
        scan_btn.configure(state=state)
    propupd_btn = _app_value(app, "btn_rkhunter_propupd")
    if propupd_btn is not None:
        propupd_btn.configure(
            state=(
                state
                if state == "normal"
                and _rkhunter_propupd_gate_valid(
                    _app_value(app, "rkhunter_last_result", {})
                )
                else "disabled"
            )
        )
    log_btn = _app_value(app, "btn_rkhunter_log")
    if log_btn is not None:
        log_btn.configure(state=state)
    show_scan_btn = _app_value(app, "btn_rkhunter_show_scan")
    if show_scan_btn is not None:
        show_scan_btn.configure(state=state)
    revoke_btn = _app_value(app, "btn_rkhunter_revoke_reference")
    if revoke_btn is not None:
        revoke_btn.configure(state=state)


def show_rkhunter_log(app):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        app.open_rkhunter_tab()
        return
    rc, out = run_cmd(["sudo", "-n", "cat", "/var/log/rkhunter.log"], timeout=30)
    app.open_rkhunter_tab()
    if rc == 0 and out:
        app.update_rkhunter_output(
            app.tr("rkhunter_log_view_header", "=== rkhunter log file ===")
            + "\n\n"
            + out,
            append=False,
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr("rkhunter_summary_log_loaded", "rkhunter log file loaded."),
        )
        app.log_safe(app.tr("rkhunter_log_loaded", "rkhunter log file loaded."))
        return
    message = app.tr(
        "rkhunter_log_load_failed",
        "The rkhunter log file could not be read (rc={rc}).",
    ).format(rc=rc)
    app.update_rkhunter_output(f"{message}\n{out or ''}".strip(), append=False)
    _app_var_set(app, "rkhunter_summary_var", message)
    app.log_safe(message)


def finish_rkhunter_update(
    app,
    rc,
    out,
    *,
    detect_update_failure_fn,
):
    app.rkhunter_updating = False
    app.rkhunter_active_process = None
    update_problem = detect_update_failure_fn(out or "")
    app._set_rkhunter_repair_available(update_problem)
    if app._looks_like_rkhunter_web_cmd_issue(out) or update_problem:
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_config_problem", "config problem"),
        )
    else:
        _app_var_set(
            app,
            "rkhunter_status_var",
            (
                app.tr("rkhunter_status_ready", "ready")
                if rc == 0
                else app.tr(
                    "rkhunter_status_update_error", "update error (rc={rc})"
                ).format(rc=rc)
            ),
        )
    if app._looks_like_rkhunter_web_cmd_issue(out):
        app.rkhunter_last_scan_output = out or app.tr(
            "rkhunter_output_none", "No output."
        )
        app.update_rkhunter_output(app.rkhunter_last_scan_output)
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_web_cmd_update_blocked",
                "rkhunter update blocked by an invalid WEB_CMD configuration.",
            ),
        )
        app.show_rkhunter_web_cmd_hint()
    elif update_problem:
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_update_problem",
                "rkhunter update failed | Reason: mirror database/config problem detected | Action available: Repair configuration and retry update",
            ),
        )
    else:
        lowered_out = (out or "").strip().lower()
        if rc == 0 and any(
            marker in lowered_out
            for marker in (
                "already has the latest",
                "already up to date",
                "no updates available",
                "not updated",
            )
        ):
            app.rkhunter_last_update_var.set(
                app.tr("rkhunter_last_update_current", "Up to date")
            )
        elif rc == 0:
            app.rkhunter_last_update_var.set(datetime.now().strftime("%Y-%m-%d"))
        _app_var_set(
            app,
            "rkhunter_summary_var",
            (
                app.tr("rkhunter_summary_updated", "rkhunter data set updated.")
                if rc == 0
                else app.tr(
                    "rkhunter_summary_update_finished_rc", "update finished (rc={rc})."
                ).format(rc=rc)
            ),
        )
    _set_rkhunter_action_buttons_state(app, True)
    app.log_safe(
        app.tr("rkhunter_log_update_finished", "rkhunter update completed.")
        if rc == 0
        else app.tr(
            "rkhunter_log_update_failed", "rkhunter update failed (rc={rc})."
        ).format(rc=rc)
    )


def rkhunter_update_worker(app, *, run_rkhunter_update_fn):
    rc, out = run_rkhunter_update_fn(timeout=600)
    call_in_ui_thread(app, lambda r=rc, o=out: app._finish_rkhunter_update(r, o))


def rkhunter_update_async(
    app,
    *,
    is_rkhunter_installed_fn,
):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        app.open_rkhunter_tab()
        return
    if not is_rkhunter_installed_fn():
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_not_installed", "not installed"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_missing",
                "rkhunter is missing. Installation hint available in the log.",
            ),
        )
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_missing",
                "rkhunter is not installed. Please use the installation hint from the log.",
            )
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Update"):
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_sudo_cancelled", "sudo canceled"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_update_sudo_cancelled",
                "rkhunter update was not started because sudo was not approved.",
            ),
        )
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_update_sudo_needed",
                "rkhunter requires root privileges. Please grant sudo approval and start the update again.",
            )
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    app._set_rkhunter_repair_available(False)
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_status_update_running", "update running"),
    )
    _app_var_set(
        app,
        "rkhunter_summary_var",
        app.tr("rkhunter_summary_update_running", "rkhunter update is running ..."),
    )
    app.open_rkhunter_tab()
    app.update_rkhunter_output(
        app.tr("rkhunter_output_update_starting", "Starting rkhunter update...")
    )
    _set_rkhunter_action_buttons_state(app, False)
    app.log_safe(app.tr("rkhunter_log_update_started", "rkhunter update started."))
    threading.Thread(target=app._rkhunter_update_worker, daemon=True).start()


def finish_rkhunter_repair(
    app, backup_rc, backup_out, repair_rc, repair_out, *, backup_path
):
    if backup_rc != 0:
        app.rkhunter_updating = False
        app.rkhunter_active_process = None
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_repair_error", "repair error"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_backup_failed",
                "Backup of the rkhunter configuration failed.",
            ),
        )
        app.update_rkhunter_output(
            (backup_out or app.tr("rkhunter_output_backup_failed", "Backup failed."))
            + "\n\n"
            + app.tr("rkhunter_output_no_changes_applied", "No changes were applied.")
        )
        _set_rkhunter_action_buttons_state(app, True)
        app._set_rkhunter_repair_available(True)
        app.log_safe(
            app.tr(
                "rkhunter_log_repair_backup_failed",
                "rkhunter repair failed: backup could not be created.",
            )
        )
        return

    if repair_rc != 0:
        app.rkhunter_updating = False
        app.rkhunter_active_process = None
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_repair_error", "repair error"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_repair_failed",
                "rkhunter configuration could not be repaired.",
            ),
        )
        app.update_rkhunter_output(
            (repair_out or app.tr("rkhunter_output_repair_failed", "Repair failed."))
            + f"\n\n{app.tr('rkhunter_label_backup', 'Backup')}: {backup_path}"
        )
        _set_rkhunter_action_buttons_state(app, True)
        app._set_rkhunter_repair_available(True)
        app.log_safe(
            app.tr(
                "rkhunter_log_repair_write_failed",
                "rkhunter repair failed: configuration could not be written.",
            )
        )
        return

    app.update_rkhunter_output(
        app.tr(
            "rkhunter_output_repair_success",
            "rkhunter update configuration repaired\nBackup: {backup_path}\n\nUpdate will be started again ...",
        ).format(backup_path=backup_path),
        append=False,
    )
    _app_var_set(
        app,
        "rkhunter_summary_var",
        app.tr(
            "rkhunter_summary_repair_success", "rkhunter update configuration repaired"
        ),
    )
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_status_retry_update_running", "retry update running"),
    )
    app.log_safe(
        app.tr(
            "rkhunter_log_repair_retry",
            "rkhunter configuration repaired, update will be started again.",
        )
    )
    threading.Thread(target=app._rkhunter_update_worker, daemon=True).start()


def rkhunter_repair_worker(
    app,
    *,
    rkhunter_backup_config_fn,
    rkhunter_repair_config_fn,
):
    backup_rc, backup_out = rkhunter_backup_config_fn()
    repair_rc, repair_out = rkhunter_repair_config_fn()
    app.after(
        0,
        lambda brc=backup_rc, bout=backup_out, rrc=repair_rc, rout=repair_out: app._finish_rkhunter_repair(
            brc, bout, rrc, rout
        ),
    )


def rkhunter_repair_update_async(
    app,
    *,
    is_rkhunter_installed_fn,
):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        app.open_rkhunter_tab()
        return
    if not is_rkhunter_installed_fn():
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_not_installed", "not installed"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_missing",
                "rkhunter is missing. Installation hint available in the log.",
            ),
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Repair"):
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_sudo_cancelled", "sudo canceled"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_repair_sudo_cancelled",
                "rkhunter repair was not started because sudo was not approved.",
            ),
        )
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_repair_sudo_needed",
                "rkhunter repair requires root privileges. Please grant sudo approval and start the repair again.",
            )
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_status_repair_running", "repair running"),
    )
    _app_var_set(
        app,
        "rkhunter_summary_var",
        app.tr(
            "rkhunter_summary_update_problem",
            "rkhunter update failed | Reason: mirror database/config problem detected | Action available: Repair configuration and retry update",
        ),
    )
    app.open_rkhunter_tab()
    app.update_rkhunter_output(
        app.tr(
            "rkhunter_output_repair_running",
            "rkhunter update failed\nReason: mirror database/config problem detected\nAction available: Repair configuration and retry update\n\nCreating backup and repairing configuration ...",
        ),
        append=False,
    )
    _set_rkhunter_action_buttons_state(app, False)
    app._set_rkhunter_repair_available(False)
    app.log_safe(app.tr("rkhunter_log_repair_started", "rkhunter repair started."))
    threading.Thread(target=app._rkhunter_repair_worker, daemon=True).start()


def finish_rkhunter_scan(
    app,
    rc,
    out,
    dpkg_rc=None,
    dpkg_out="",
    dpkg_owner_out="",
    file_type_out="",
):
    stop_rkhunter_progress_animation(app)
    set_rkhunter_progress(
        app,
        85,
        app.tr("rkhunter_progress_analyzing", "Analyzing scan result ..."),
    )
    app.rkhunter_running = False
    app.rkhunter_active_process = None
    if app._looks_like_rkhunter_web_cmd_issue(out):
        app.rkhunter_last_result = {}
        set_rkhunter_propupd_available(app, False)
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_config_error", "config error"),
        )
    else:
        if rc == 0:
            status = app.tr("rkhunter_status_finished", "finished")
        elif rc == 1:
            status = app.tr(
                "rkhunter_status_finished_with_warnings",
                "finished with warnings",
            )
        else:
            status = app.tr("rkhunter_status_error_rc", "error (rc={rc})").format(rc=rc)
        _app_var_set(
            app,
            "rkhunter_status_var",
            status,
        )
    app.update_rkhunter_output(out or app.tr("rkhunter_output_none", "No output."))
    if app._looks_like_rkhunter_web_cmd_issue(out):
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_web_cmd_scan_blocked",
                "rkhunter scan blocked by an invalid WEB_CMD configuration.",
            ),
        )
        app.show_rkhunter_web_cmd_hint()
    else:
        result = app._update_rkhunter_summary_from_output(
            out or "",
            rc,
            dpkg_output=dpkg_out,
            dpkg_rc=dpkg_rc,
            dpkg_owner_output=dpkg_owner_out,
            file_type_output=file_type_out,
        )
        analysis_text = format_rkhunter_analysis(app, result)
        app.rkhunter_last_scan_output = "\n\n".join(
            [out or app.tr("rkhunter_output_none", "No output."), analysis_text]
        )
        app.update_rkhunter_output(app.rkhunter_last_scan_output)
    _set_rkhunter_action_buttons_state(app, True)
    set_rkhunter_progress(
        app,
        100,
        app.tr("rkhunter_progress_finished", "Scan finished."),
    )
    app.log_safe(
        app.tr("rkhunter_log_scan_finished", "rkhunter scan completed.")
        if rc == 0
        else app.tr(
            "rkhunter_log_scan_warning",
            "rkhunter scan finished with a warning / notice.",
        )
    )


def rkhunter_scan_worker(app):
    call_in_ui_thread(
        app,
        lambda: set_rkhunter_progress(
            app,
            20,
            app.tr("rkhunter_progress_rkhunter_running", "Running rkhunter scan ..."),
        ),
    )
    rc, out = run_cmd(
        ["sudo", "-n", "rkhunter", "--check", "--skip-keypress", "--nocolors"],
        timeout=1800,
    )
    log_rc, log_out = run_cmd(
        ["sudo", "-n", "cat", "/var/log/rkhunter.log"], timeout=30
    )
    log_evidence = _extract_rkhunter_log_evidence(log_out if log_rc == 0 else "")
    combined_out = f"{out or ''}{log_evidence}"
    call_in_ui_thread(
        app,
        lambda: set_rkhunter_progress(
            app,
            65,
            app.tr(
                "rkhunter_progress_verifying_packages",
                "Checking warnings ...",
            ),
        ),
    )
    evidence_paths = sorted(
        set(extract_replaced_script_paths(combined_out))
        | set(extract_warning_command_paths(combined_out))
    )
    if has_cmd("dpkg"):
        dpkg_rc, dpkg_out = run_cmd(["sudo", "-n", "dpkg", "-V"], timeout=300)
        owner_lines = []
        for path in evidence_paths:
            owner_rc, owner_out = run_cmd(["dpkg", "-S", path], timeout=30)
            owner_lines.append(f"{path}\t{owner_rc}\t{(owner_out or '').strip()}")
        dpkg_owner_out = "\n".join(owner_lines)
    else:
        dpkg_rc, dpkg_out = 127, "dpkg is not available"
        dpkg_owner_out = ""
    if has_cmd("file"):
        file_lines = []
        for path in evidence_paths:
            file_rc, file_out = run_cmd(["file", "-b", path], timeout=30)
            file_lines.append(f"{path}\t{file_rc}\t{(file_out or '').strip()}")
        file_type_out = "\n".join(file_lines)
    else:
        file_type_out = ""
    call_in_ui_thread(
        app,
        lambda r=rc, o=combined_out, dr=dpkg_rc, do=dpkg_out, dso=dpkg_owner_out, fto=file_type_out: app._finish_rkhunter_scan(
            r, o, dr, do, dso, fto
        ),
    )


def finish_rkhunter_propupd(app, rc, out):
    app.rkhunter_updating = False
    app.rkhunter_active_process = None
    result = _app_value(app, "rkhunter_last_result", {}) or {}
    result["propupd_allowed"] = False
    set_rkhunter_propupd_available(app, False)
    if rc == 0:
        message = app.tr(
            "rkhunter_propupd_success",
            "The reference database was updated successfully. Future scans compare the system with this trusted state.",
        )
        _app_var_set(
            app, "rkhunter_status_var", app.tr("rkhunter_status_ready", "ready")
        )
        app.update_rkhunter_output(message, append=True)
        messagebox.showinfo(
            app.tr("rkhunter_propupd_title", "Update rkhunter reference"),
            message,
            parent=app,
        )
        app.log_safe(message)
    else:
        message = app.tr(
            "rkhunter_propupd_failed",
            "The rkhunter reference database could not be updated (rc={rc}).",
        ).format(rc=rc)
        _app_var_set(app, "rkhunter_status_var", message)
        app.update_rkhunter_output(f"{message}\n{out or ''}".strip(), append=True)
        messagebox.showerror(
            app.tr("rkhunter_propupd_title", "Update rkhunter reference"),
            message,
            parent=app,
        )
        app.log_safe(message)
    _set_rkhunter_action_buttons_state(app, True)


def rkhunter_propupd_worker(app, *, run_rkhunter_propupd_fn):
    rc, out = run_rkhunter_propupd_fn(timeout=600)
    call_in_ui_thread(app, lambda r=rc, o=out: app._finish_rkhunter_propupd(r, o))


def rkhunter_propupd_async(app, *, is_rkhunter_installed_fn):
    result = _app_value(app, "rkhunter_last_result", {}) or {}
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        return
    if not is_rkhunter_installed_fn() or not _rkhunter_propupd_gate_valid(result):
        set_rkhunter_propupd_available(app, False)
        messagebox.showwarning(
            app.tr("rkhunter_propupd_title", "Update rkhunter reference"),
            app.tr(
                "rkhunter_propupd_not_allowed",
                "The safety requirements are not met. Run a complete scan and resolve all critical or unexplained findings first.",
            ),
            parent=app,
        )
        return
    confirmed = messagebox.askyesno(
        app.tr("rkhunter_propupd_title", "Update rkhunter reference"),
        app.tr(
            "rkhunter_propupd_confirmation",
            "The system appears trustworthy. Accept the current rkhunter file properties as the new reference?",
        ),
        parent=app,
    )
    if not confirmed or not _rkhunter_propupd_gate_valid(result):
        return
    if not app.ensure_sudo_session("rkhunter --propupd"):
        return
    if not _rkhunter_propupd_gate_valid(result):
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    set_rkhunter_propupd_available(app, False)
    _set_rkhunter_action_buttons_state(app, False)
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_propupd_running", "updating reference"),
    )
    threading.Thread(target=app._rkhunter_propupd_worker, daemon=True).start()


def finish_rkhunter_revoke_reference(app, rc, out):
    app.rkhunter_updating = False
    app.rkhunter_active_process = None
    result = _app_value(app, "rkhunter_last_result", {}) or {}
    result["propupd_allowed"] = False
    set_rkhunter_propupd_available(app, False)
    if rc == 0:
        message = app.tr(
            "rkhunter_revoke_reference_success",
            "The previous rkhunter reference database was restored. Run a new scan before accepting another reference.",
        )
        _app_var_set(
            app, "rkhunter_status_var", app.tr("rkhunter_status_ready", "ready")
        )
        app.update_rkhunter_output(message, append=True)
        messagebox.showinfo(
            app.tr("rkhunter_revoke_reference_title", "Revoke rkhunter reference"),
            message,
            parent=app,
        )
        app.log_safe(message)
    else:
        message = app.tr(
            "rkhunter_revoke_reference_failed",
            "The previous rkhunter reference database could not be restored (rc={rc}).",
        ).format(rc=rc)
        detail = (out or "").strip()
        display_message = f"{message}\n\n{detail}" if detail else message
        _app_var_set(app, "rkhunter_status_var", message)
        app.update_rkhunter_output(display_message, append=True)
        messagebox.showerror(
            app.tr("rkhunter_revoke_reference_title", "Revoke rkhunter reference"),
            display_message,
            parent=app,
        )
        app.log_safe(message)
    _set_rkhunter_action_buttons_state(app, True)


def rkhunter_revoke_reference_worker(app, *, restore_rkhunter_property_database_fn):
    rc, out = restore_rkhunter_property_database_fn()
    call_in_ui_thread(
        app, lambda r=rc, o=out: app._finish_rkhunter_revoke_reference(r, o)
    )


def rkhunter_revoke_reference_async(app, *, is_rkhunter_installed_fn):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        return
    if not is_rkhunter_installed_fn():
        messagebox.showwarning(
            app.tr("rkhunter_revoke_reference_title", "Revoke rkhunter reference"),
            app.tr(
                "rkhunter_revoke_reference_not_allowed",
                "rkhunter is not installed. The reference cannot be restored.",
            ),
            parent=app,
        )
        return
    confirmed = messagebox.askyesno(
        app.tr("rkhunter_revoke_reference_title", "Revoke rkhunter reference"),
        app.tr(
            "rkhunter_revoke_reference_confirmation",
            "Restore the previous rkhunter reference database from the NetMon backup?",
        ),
        parent=app,
    )
    if not confirmed:
        return
    if not app.ensure_sudo_session("rkhunter reference restore"):
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    set_rkhunter_propupd_available(app, False)
    _set_rkhunter_action_buttons_state(app, False)
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_revoke_reference_running", "restoring reference"),
    )
    threading.Thread(target=app._rkhunter_revoke_reference_worker, daemon=True).start()


def _extract_rkhunter_log_evidence(log_output: str) -> str:
    evidence_lines = []
    for line in (log_output or "").splitlines():
        lowered = line.lower()
        if (
            "hidden file" in lowered
            or "hidden directory" in lowered
            or "suspect file" in lowered
            or "[ warning ]" in lowered
        ):
            evidence_lines.append(line.strip())
    if not evidence_lines:
        return ""
    return "\n".join(["", "=== rkhunter log evidence ===", *evidence_lines])


def rkhunter_scan_async(
    app,
    *,
    is_rkhunter_installed_fn,
):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe(
            app.tr("rkhunter_log_already_running", "rkhunter is already running.")
        )
        app.open_rkhunter_tab()
        return
    app.rkhunter_last_result = {}
    set_rkhunter_propupd_available(app, False)
    if not is_rkhunter_installed_fn():
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_not_installed", "not installed"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_missing",
                "rkhunter is missing. Installation hint available in the log.",
            ),
        )
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_missing",
                "rkhunter is not installed. Please use the installation hint from the log.",
            )
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Scan"):
        _app_var_set(
            app,
            "rkhunter_status_var",
            app.tr("rkhunter_status_sudo_cancelled", "sudo canceled"),
        )
        _app_var_set(
            app,
            "rkhunter_summary_var",
            app.tr(
                "rkhunter_summary_scan_sudo_cancelled",
                "rkhunter scan was not started because sudo was not approved.",
            ),
        )
        app.update_rkhunter_output(
            app.tr(
                "rkhunter_output_scan_sudo_needed",
                "rkhunter requires root privileges. Please grant sudo approval and start the scan again.",
            )
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_running = True
    app.rkhunter_active_process = "thread"
    _app_var_set(
        app,
        "rkhunter_status_var",
        app.tr("rkhunter_status_scan_running", "scan running"),
    )
    _app_var_set(
        app,
        "rkhunter_summary_var",
        app.tr("rkhunter_summary_scan_running", "rkhunter scan is running ..."),
    )
    set_rkhunter_progress(
        app,
        10,
        app.tr("rkhunter_progress_starting", "Starting scan ..."),
    )
    start_rkhunter_progress_animation(app, duration_seconds=120)
    app.open_rkhunter_tab()
    app.clear_rkhunter_output()
    app.update_rkhunter_output(
        app.tr(
            "rkhunter_output_scan_started",
            "rkhunter scan started. Output will follow ...",
        )
    )
    _set_rkhunter_action_buttons_state(app, False)
    app.log_safe(app.tr("rkhunter_log_scan_started", "rkhunter scan started."))
    threading.Thread(target=app._rkhunter_scan_worker, daemon=True).start()


def open_startup_guard_tab(app):
    app._select_security_tab(app.tab_startup_guard)


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


def _startup_guard_service(app):
    return _app_value(app, "startup_guard_service")


def _startup_guard_trustlist_path(app) -> str:
    return str(_app_value(app, "startup_guard_trustlist_path", "") or "").strip()


def _startup_guard_trustlist(app):
    service = _startup_guard_service(app)
    if service is None:
        return {"trusted": {}}
    return service.load_trustlist(_startup_guard_trustlist_path(app))


def update_startup_guard_status_line(app):
    _app_var_set(
        app,
        "startup_guard_run_status_var",
        (
            app.tr("startup_guard_run_status_running", "Check: running")
            if bool(_app_value(app, "startup_guard_running", False))
            else app.tr("startup_guard_run_status_ready", "Check: ready")
        ),
    )
    _app_var_set(
        app,
        "startup_guard_visible_count_var",
        app.tr(
            "startup_guard_visible_entries_count",
            "Visible entries: {count}",
        ).format(count=len(_app_list(app, "startup_guard_visible_entries"))),
    )


def update_startup_guard_output(app, text: str, *, append: bool = False):
    detail_widget = _app_value(app, "startup_guard_details_text")
    if detail_widget is None:
        return
    detail_widget.configure(state="normal")
    if not append:
        detail_widget.delete("1.0", "end")
    if text:
        if append and detail_widget.index("end-1c") != "1.0":
            detail_widget.insert("end", "\n\n")
        detail_widget.insert("end", text)
    detail_widget.see("end")
    detail_widget.configure(state="disabled")
    scroll_fn = _app_value(app, "scroll_main_page_to_widget")
    if callable(scroll_fn):
        try:
            scroll_fn(detail_widget)
        except Exception:
            pass


def _app_update_startup_guard_output(app, text: str, *, append: bool = False):
    writer = _app_value(app, "update_startup_guard_output")
    if callable(writer):
        writer(text, append=append)
        return
    update_startup_guard_output(app, text, append=append)


def clear_startup_guard_output(app):
    tree = _app_value(app, "startup_guard_tree")
    if tree is not None:
        tree.delete(*tree.get_children())
    app.startup_guard_visible_entries = []
    app.startup_guard_selected_entry = None
    update_startup_guard_output(app, "")
    update_startup_guard_status_line(app)
    if not app.startup_guard_running:
        app.startup_guard_status_var.set(
            app.tr(
                "startup_guard_status_ready_no_baseline",
                "Startup Guard bereit. Noch keine Baseline geladen.",
            )
        )


def format_startup_guard_entry(entry: dict) -> str:
    source = str(entry.get("source") or "–").strip()
    name = str(entry.get("name") or os.path.basename(entry.get("path") or "") or "–")
    path = str(entry.get("path") or "–").strip()
    return f"- [{source}] {name} | {path}"


def render_startup_guard_result(app, result: dict, current_count: int) -> str:
    new_entries = list(result.get("new") or [])
    removed_entries = list(result.get("removed") or [])
    changed_entries = list(result.get("changed") or [])
    trusted_entries = list(result.get("trusted") or [])
    unchanged_entries = list(result.get("unchanged") or [])

    lines = [
        app.tr("startup_guard_report_title", "=== Startup Guard Prüfung ==="),
        "",
        app.tr(
            "startup_guard_report_current_entries", "Current entries: {count}"
        ).format(count=current_count),
        "",
        app.tr("startup_guard_report_new_entries", "New entries:"),
    ]
    if new_entries:
        lines.extend(format_startup_guard_entry(entry) for entry in new_entries)
    else:
        lines.append(app.tr("startup_guard_report_no_new_entries", "- No new entries."))

    lines.extend(
        ["", app.tr("startup_guard_report_removed_entries", "Removed entries:")]
    )
    if removed_entries:
        lines.extend(format_startup_guard_entry(entry) for entry in removed_entries)
    else:
        lines.append(
            app.tr("startup_guard_report_no_removed_entries", "- No removed entries.")
        )

    lines.extend(
        ["", app.tr("startup_guard_report_changed_entries", "Changed entries:")]
    )
    if changed_entries:
        for item in changed_entries:
            before = item.get("before") or {}
            after = item.get("after") or {}
            lines.append(format_startup_guard_entry(after or before))
            lines.append(
                app.tr(
                    "startup_guard_report_change_details",
                    "  Change: sha256 {sha_changed}, size {size_before} -> {size_after}, mtime {mtime_before} -> {mtime_after}",
                ).format(
                    sha_changed=before.get("sha256", "") != after.get("sha256", ""),
                    size_before=before.get("size", 0),
                    size_after=after.get("size", 0),
                    mtime_before=before.get("mtime", 0),
                    mtime_after=after.get("mtime", 0),
                )
            )
    else:
        lines.append(
            app.tr("startup_guard_report_no_changed_entries", "- No changed entries.")
        )

    lines.extend(
        ["", app.tr("startup_guard_report_trusted_entries", "Trust list / known:")]
    )
    if trusted_entries:
        for entry in trusted_entries:
            item = startup_guard_status_entry("TRUSTED", entry)
            lines.append(format_startup_guard_entry(item))
    else:
        lines.append(
            app.tr("startup_guard_report_no_trusted_entries", "- No known entries.")
        )

    lines.extend(["", app.tr("startup_guard_report_unchanged", "Unchanged:")])
    lines.append(
        app.tr("startup_guard_report_count", "Count: {count}").format(
            count=len(unchanged_entries)
        )
    )
    return "\n".join(lines)


def startup_guard_status_entry(status: str, entry) -> dict:
    if status in {"CHANGED", "TRUSTED"} and (
        (entry or {}).get("before") is not None
        or (entry or {}).get("after") is not None
    ):
        before = dict((entry or {}).get("before") or {})
        after = dict((entry or {}).get("after") or {})
        item = dict(after or before)
        item["_before"] = before
        item["_after"] = after
    else:
        item = dict(entry or {})
    item["_status"] = status
    return item


def show_startup_guard_result(app, result):
    tree = _app_value(app, "startup_guard_tree")
    if tree is not None:
        tree.delete(*tree.get_children())
    app.startup_guard_visible_entries = []
    app.startup_guard_selected_entry = None

    groups = [
        ("NEW", result.get("new", [])),
        ("CHANGED", result.get("changed", [])),
        ("REMOVED", result.get("removed", [])),
        ("TRUSTED", result.get("trusted", [])),
        ("UNCHANGED", result.get("unchanged", [])),
    ]

    for status, entries in groups:
        for entry in entries:
            item = startup_guard_status_entry(status, entry)
            app.startup_guard_visible_entries.append(item)
            if tree is not None:
                tree.insert(
                    "",
                    "end",
                    values=(
                        status,
                        item.get("source", "-"),
                        item.get("name", "-"),
                        item.get("path", "-"),
                    ),
                )

    summary_text = render_startup_guard_result(
        app,
        result,
        len(app.startup_guard_visible_entries),
    )
    update_startup_guard_status_line(app)
    _app_update_startup_guard_output(app, summary_text)


def format_startup_guard_entry_details(entry: dict) -> str:
    lines = []
    lines.append("=== Startup Guard Eintrag ===")
    lines.append("")
    lines.append(f"Status: {entry.get('_status', '-')}")
    lines.append(f"Quelle: {entry.get('source', '-')}")
    lines.append(f"Name: {entry.get('name', '-')}")
    lines.append(f"Pfad: {entry.get('path', '-')}")
    lines.append(f"Größe: {entry.get('size', '-')}")
    lines.append(f"MTime: {entry.get('mtime', '-')}")
    lines.append(f"SHA256: {entry.get('sha256', '-')}")

    before = entry.get("_before") or {}
    after = entry.get("_after") or {}
    if entry.get("_status") == "CHANGED" and before:
        lines.append("")
        lines.append("Vorher:")
        lines.append(f"Größe: {before.get('size', '-')}")
        lines.append(f"MTime: {before.get('mtime', '-')}")
        lines.append(f"SHA256: {before.get('sha256', '-')}")
        if after:
            lines.append("")
            lines.append("Nachher:")
            lines.append(f"Größe: {after.get('size', '-')}")
            lines.append(f"MTime: {after.get('mtime', '-')}")
            lines.append(f"SHA256: {after.get('sha256', '-')}")

    lines.append("")

    path = entry.get("path", "")
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read(12000)
            lines.append("Dateiinhalt/Ausschnitt:")
            lines.append("-" * 40)
            lines.append(content)
        except Exception as exc:
            lines.append(f"Datei konnte nicht gelesen werden: {exc}")
    else:
        lines.append("Datei nicht vorhanden oder entfernt.")

    return "\n".join(lines)


def on_startup_guard_select(app, _event=None):
    tree = _app_value(app, "startup_guard_tree")
    if tree is None:
        return
    selection = tree.selection()
    if not selection:
        return

    index = tree.index(selection[0])
    visible_entries = _app_list(app, "startup_guard_visible_entries")
    if index < 0 or index >= len(visible_entries):
        return

    entry = visible_entries[index]
    app.startup_guard_selected_entry = entry
    details = format_startup_guard_entry_details(entry)
    _app_update_startup_guard_output(app, details)


def analyze_selected_startup_entry_with_chad(app):
    entry = _app_value(app, "startup_guard_selected_entry")
    if not entry:
        app.log(
            app.tr(
                "startup_guard_log_no_entry_selected",
                "Startup Guard: Kein Eintrag ausgewählt.",
            )
        )
        return

    details = format_startup_guard_entry_details(entry)
    app.prepare_chad_analysis("Startup Guard Eintrag Analyse", details)


def analyze_startup_guard_changes_with_chad(app):
    result = _app_value(app, "startup_guard_last_result")
    if not result:
        app.log(
            app.tr(
                "startup_guard_log_no_check_available",
                "Startup Guard: Keine Prüfung vorhanden.",
            )
        )
        return

    parts = ["=== Startup Guard Änderungen ===", ""]
    for label, key in [
        ("Neue Einträge", "new"),
        ("Geänderte Einträge", "changed"),
        ("Entfernte Einträge", "removed"),
    ]:
        entries = list(result.get(key) or [])
        parts.append(label + ":")
        if not entries:
            parts.append("- keine")
        else:
            for entry in entries:
                if key == "changed":
                    before = (entry or {}).get("before") or {}
                    after = (entry or {}).get("after") or {}
                    parts.append(
                        f"- {after.get('source', before.get('source', '-'))}: "
                        f"{after.get('name', before.get('name', '-'))} | "
                        f"{after.get('path', before.get('path', '-'))}"
                    )
                    parts.append(
                        "  SHA256 alt/neu: "
                        f"{before.get('sha256', '-')} -> {after.get('sha256', '-')}"
                    )
                else:
                    parts.append(
                        f"- {entry.get('source', '-')}: {entry.get('name', '-')} | "
                        f"{entry.get('path', '-')}"
                    )
                    parts.append(f"  SHA256: {entry.get('sha256', '-')}")
        parts.append("")

    text = "\n".join(parts)
    app.prepare_chad_analysis("Startup Guard Änderungen Analyse", text)


def startup_guard_mark_selected_trusted(app):
    entry = _app_value(app, "startup_guard_selected_entry")
    if not entry:
        app.log(
            app.tr(
                "startup_guard_log_no_entry_selected",
                "Startup Guard: Kein Eintrag ausgewählt.",
            )
        )
        return

    if entry.get("_status") == "REMOVED":
        app.log(
            app.tr(
                "startup_guard_log_removed_cannot_trust",
                "Startup Guard: Entfernte Einträge können nicht als bekannt markiert werden.",
            )
        )
        return

    ok, err = _startup_guard_service(app).mark_trusted(
        entry.get("path", ""),
        entry,
        _startup_guard_trustlist_path(app),
    )
    if ok:
        app.log(
            app.tr(
                "startup_guard_log_marked_trusted",
                "Startup Guard: Eintrag als bekannt markiert: {name}",
            ).format(name=entry.get("name", "-"))
        )
        app.startup_guard_check()
    else:
        app.log(
            app.tr(
                "startup_guard_log_trustlist_error",
                "Startup Guard: Trustlist Fehler: {error}",
            ).format(error=err)
        )


def startup_guard_remove_selected_trusted(app):
    entry = _app_value(app, "startup_guard_selected_entry")
    if not entry:
        app.log(
            app.tr(
                "startup_guard_log_no_entry_selected",
                "Startup Guard: Kein Eintrag ausgewählt.",
            )
        )
        return

    ok, err = _startup_guard_service(app).remove_trusted(
        entry.get("path", ""),
        _startup_guard_trustlist_path(app),
    )
    if ok:
        app.log(
            app.tr(
                "startup_guard_log_removed_trusted",
                "Startup Guard: Eintrag aus Vertrauensliste entfernt: {name}",
            ).format(name=entry.get("name", "-"))
        )
        app.startup_guard_check()
    else:
        app.log(
            app.tr(
                "startup_guard_log_trustlist_error",
                "Startup Guard: Trustlist Fehler: {error}",
            ).format(error=err)
        )


def startup_guard_show_trustlist(app):
    trustlist = _startup_guard_trustlist(app)
    trusted = dict(trustlist.get("trusted") or {})
    lines = [
        app.tr("startup_guard_trustlist_title", "=== Startup Guard Trust List ==="),
        "",
    ]

    if not trusted:
        lines.append(
            app.tr(
                "startup_guard_trustlist_empty",
                "No entries available.",
            )
        )
    else:
        for path, item in sorted(trusted.items()):
            lines.append(f"- {item.get('name', '-')}")
            lines.append(
                app.tr("startup_guard_trustlist_path", "  Path: {path}").format(
                    path=path
                )
            )
            lines.append(
                app.tr("startup_guard_trustlist_sha256", "  SHA256: {sha256}").format(
                    sha256=item.get("sha256", "-")
                )
            )
            lines.append(
                app.tr(
                    "startup_guard_trustlist_marked", "  Marked: {timestamp}"
                ).format(timestamp=item.get("trusted_at", "-"))
            )
            lines.append("")

    app.open_startup_guard_tab()
    app.update_startup_guard_output("\n".join(lines))


def startup_guard_reset_trustlist(app):
    service = _startup_guard_service(app)
    if service is None:
        app.log(
            app.tr(
                "startup_guard_status_service_unavailable",
                "Startup Guard: Service nicht verfügbar",
            )
        )
        return

    ok, err = service.reset_trustlist(_startup_guard_trustlist_path(app))
    if ok:
        app.log("Startup Guard: Vertrauensliste wurde zurückgesetzt.")
        app.startup_guard_check()
    else:
        app.log(
            app.tr(
                "startup_guard_log_trustlist_error",
                "Startup Guard: Trustlist Fehler: {error}",
            ).format(error=err)
        )


def set_startup_guard_light(app, state: str, message: str = ""):
    app.startup_guard_last_state = str(state or "off")
    status_text = message or ""

    if state == "ok":
        app.set_light(app.l_startup_guard, "green")
        if not status_text:
            status_text = app.tr(
                "startup_guard_status_ok",
                "Startup Guard: OK",
            )
    elif state == "changed":
        app.set_light(app.l_startup_guard, "yellow")
        if not status_text:
            status_text = app.tr(
                "startup_guard_status_changed",
                "Startup Guard: Änderungen erkannt",
            )
    elif state == "error":
        app.set_light(app.l_startup_guard, "red")
        if not status_text:
            status_text = app.tr(
                "startup_guard_status_error",
                "Startup Guard: Fehler",
            )
    else:
        app.set_light(app.l_startup_guard, "gray")
        if not status_text:
            status_text = app.tr(
                "startup_guard_status_no_baseline",
                "Startup Guard: keine Baseline",
            )

    app.startup_guard_status_var.set(status_text)
    update_startup_guard_status_line(app)


def startup_guard_startup_check(app):
    try:
        service = _startup_guard_service(app)
        if service is None:
            app.set_startup_guard_light(
                "error",
                app.tr(
                    "startup_guard_status_service_unavailable",
                    "Startup Guard: Service nicht verfügbar",
                ),
            )
            return
        if not os.path.isfile(app.startup_guard_baseline_path):
            app.set_startup_guard_light(
                "off",
                app.tr(
                    "startup_guard_status_no_baseline_available",
                    "Startup Guard: keine Baseline vorhanden",
                ),
            )
            return

        baseline = service.load_baseline(app.startup_guard_baseline_path)
        trustlist = _startup_guard_trustlist(app)
        if not isinstance(baseline, dict) or "entries" not in baseline:
            app.set_startup_guard_light(
                "error",
                app.tr(
                    "startup_guard_status_baseline_load_failed",
                    "Startup Guard: Baseline konnte nicht geladen werden",
                ),
            )
            return

        current = service.collect_entries()
        result = service.compare_to_baseline(baseline, current, trustlist)
        changed_count = (
            len(result.get("new", []))
            + len(result.get("changed", []))
            + len(result.get("removed", []))
        )

        if changed_count == 0:
            app.set_startup_guard_light(
                "ok",
                app.tr(
                    "startup_guard_status_no_changes",
                    "Startup Guard: keine Änderungen",
                ),
            )
        else:
            app.set_startup_guard_light(
                "changed",
                app.tr(
                    "startup_guard_status_changes_detected_count",
                    "Startup Guard: {count} Änderung(en) erkannt",
                ).format(count=changed_count),
            )
    except Exception as exc:
        app.set_startup_guard_light(
            "error",
            app.tr(
                "startup_guard_status_startcheck_error",
                "Startup Guard: Fehler beim Startcheck: {error}",
            ).format(error=exc),
        )


def startup_guard_create_baseline(app):
    if app.startup_guard_running:
        app.log_safe(
            app.tr(
                "startup_guard_log_already_running",
                "Startup Guard läuft bereits.",
            )
        )
        app.open_startup_guard_tab()
        return
    service = _startup_guard_service(app)
    if service is None:
        app.set_startup_guard_light(
            "error",
            app.tr(
                "startup_guard_status_service_unavailable",
                "Startup Guard: Service nicht verfügbar",
            ),
        )
        app.update_startup_guard_output(
            app.tr(
                "startup_guard_output_service_unavailable",
                "Startup Guard Service ist nicht verfügbar. Bitte Installation prüfen.",
            )
        )
        app.open_startup_guard_tab()
        return

    app.startup_guard_running = True
    app.startup_guard_status_var.set(
        app.tr(
            "startup_guard_status_creating_baseline",
            "Baseline wird erstellt ...",
        )
    )
    update_startup_guard_status_line(app)
    app.open_startup_guard_tab()
    app.update_startup_guard_output(
        app.tr(
            "startup_guard_output_creating_baseline",
            "Startup Guard Baseline wird erstellt ...",
        )
    )

    def worker():
        try:
            entries = service.collect_entries()
            ok, err = service.save_baseline(
                app.startup_guard_baseline_path,
                entries,
            )
        except Exception as exc:
            entries = []
            ok, err = False, str(exc)

        def finish():
            app.startup_guard_running = False
            update_startup_guard_status_line(app)
            if ok:
                app.startup_guard_status_var.set(
                    app.tr(
                        "startup_guard_status_baseline_created_count",
                        "Baseline erstellt ({count} Einträge)",
                    ).format(count=len(entries))
                )
                app.update_startup_guard_output(
                    "\n".join(
                        [
                            "=== Startup Guard Baseline ===",
                            f"Datei: {app.startup_guard_baseline_path}",
                            f"Einträge: {len(entries)}",
                            "",
                            "Hinweis: Diese Baseline dient nur dem späteren Vergleich.",
                        ]
                    )
                )
                app.set_startup_guard_light(
                    "ok",
                    app.tr(
                        "startup_guard_status_baseline_created",
                        "Startup Guard: Baseline erstellt",
                    ),
                )
                app.log(
                    app.tr(
                        "startup_guard_log_baseline_created_count",
                        "Startup Guard: Baseline erstellt ({count} Einträge).",
                    ).format(count=len(entries))
                )
            else:
                app.update_startup_guard_output(
                    "\n".join(
                        [
                            "=== Startup Guard Baseline ===",
                            "Ergebnis: fehlgeschlagen",
                            f"Details: {err}",
                        ]
                    )
                )
                app.set_startup_guard_light(
                    "error",
                    app.tr(
                        "startup_guard_status_error",
                        "Startup Guard: Fehler",
                    ),
                )
                app.log(
                    app.tr(
                        "startup_guard_log_baseline_error",
                        "Startup Guard: Baseline Fehler: {error}",
                    ).format(error=err)
                )

        call_in_ui_thread(app, finish)

    threading.Thread(target=worker, daemon=True).start()


def startup_guard_check(app):
    if app.startup_guard_running:
        app.log_safe(
            app.tr(
                "startup_guard_log_already_running",
                "Startup Guard läuft bereits.",
            )
        )
        app.open_startup_guard_tab()
        return
    service = _startup_guard_service(app)
    if service is None:
        app.set_startup_guard_light(
            "error",
            app.tr(
                "startup_guard_status_service_unavailable",
                "Startup Guard: Service nicht verfügbar",
            ),
        )
        app.update_startup_guard_output(
            app.tr(
                "startup_guard_output_service_unavailable",
                "Startup Guard Service ist nicht verfügbar. Bitte Installation prüfen.",
            )
        )
        app.open_startup_guard_tab()
        return
    if not os.path.isfile(app.startup_guard_baseline_path):
        app.set_startup_guard_light(
            "off",
            app.tr(
                "startup_guard_status_no_baseline_available",
                "Startup Guard: keine Baseline vorhanden",
            ),
        )
        app.update_startup_guard_output(
            app.tr(
                "startup_guard_output_no_baseline",
                "=== Startup Guard Prüfung ===\n\nNo baseline exists yet.\nPlease run 'Create baseline' first.",
            )
        )
        app.open_startup_guard_tab()
        app.log(
            app.tr(
                "startup_guard_log_no_baseline_available",
                "Startup Guard: Keine Baseline vorhanden.",
            )
        )
        return

    app.startup_guard_running = True
    app.startup_guard_status_var.set(
        app.tr(
            "startup_guard_status_check_running",
            "Startup wird geprüft ...",
        )
    )
    update_startup_guard_status_line(app)
    app.open_startup_guard_tab()
    app.update_startup_guard_output(
        app.tr(
            "startup_guard_output_check_running",
            "Startup Guard Prüfung läuft ...",
        )
    )

    def worker():
        try:
            baseline = service.load_baseline(app.startup_guard_baseline_path)
            trustlist = _startup_guard_trustlist(app)
            current = service.collect_entries()
            result = service.compare_to_baseline(baseline, current, trustlist)
            error = ""
        except Exception as exc:
            result = {}
            error = str(exc)

        def finish():
            app.startup_guard_running = False
            update_startup_guard_status_line(app)
            if error:
                app.startup_guard_last_result = {}
                app.startup_guard_status_var.set(
                    app.tr(
                        "startup_guard_status_error",
                        "Startup Guard: Fehler",
                    )
                )
                app.update_startup_guard_output(
                    app.tr(
                        "startup_guard_output_failed",
                        "=== Startup Guard Prüfung ===\n\nResult: failed\nDetails: {error}",
                    ).format(error=error)
                )
                app.set_startup_guard_light(
                    "error",
                    app.tr(
                        "startup_guard_status_error",
                        "Startup Guard: Fehler",
                    ),
                )
                app.log(f"Startup Guard: Prüfung fehlgeschlagen: {error}")
                return
            app.startup_guard_last_result = result
            app.startup_guard_status_var.set(
                app.tr(
                    "startup_guard_status_check_done",
                    "Prüfung abgeschlossen",
                )
            )
            app.show_startup_guard_result(result)
            changed_count = (
                len(result.get("new", []))
                + len(result.get("changed", []))
                + len(result.get("removed", []))
            )
            if changed_count == 0:
                app.set_startup_guard_light(
                    "ok",
                    app.tr(
                        "startup_guard_status_no_changes",
                        "Startup Guard: keine Änderungen",
                    ),
                )
            else:
                app.set_startup_guard_light(
                    "changed",
                    app.tr(
                        "startup_guard_status_changes_detected_count",
                        "Startup Guard: {count} Änderung(en) erkannt",
                    ).format(count=changed_count),
                )
            app.log(
                app.tr(
                    "startup_guard_log_check_done_counts",
                    "Startup Guard: Prüfung abgeschlossen (neu={new}, entfernt={removed}, geändert={changed}).",
                ).format(
                    new=len(result.get("new") or []),
                    removed=len(result.get("removed") or []),
                    changed=len(result.get("changed") or []),
                )
            )

        call_in_ui_thread(app, finish)

    threading.Thread(target=worker, daemon=True).start()


def format_path_guard_result(result: dict) -> str:
    return _format_path_guard_result(None, result)


def _path_guard_text(
    app, key: str, default_de: str, default_en: str | None = None
) -> str:
    if app is None:
        return default_en if default_en is not None else default_de
    return app.tr(key, default_de)


def _translate_path_guard_issue(app, text: str) -> str:
    raw = str(text or "").strip()
    mapping = {
        "PATH-Verzeichnis ist für alle beschreibbar.": (
            "path_guard_issue_world_writable",
            "PATH-Verzeichnis ist für alle beschreibbar.",
            "PATH directory is writable by everyone.",
        ),
        "PATH-Verzeichnis ist gruppenbeschreibbar.": (
            "path_guard_issue_group_writable",
            "PATH-Verzeichnis ist gruppenbeschreibbar.",
            "PATH directory is group-writable.",
        ),
        "Ungewöhnlicher PATH-Eintrag steht sehr weit vorne.": (
            "path_guard_issue_unusual_early",
            "Ungewöhnlicher PATH-Eintrag steht sehr weit vorne.",
            "Unusual PATH entry appears very early in PATH.",
        ),
        "Üblicher User-Bin-Pfad im PATH.": (
            "path_guard_issue_user_bin_present",
            "Üblicher User-Bin-Pfad im PATH.",
            "Common user bin path is present in PATH.",
        ),
        "Verdächtige PATH-Manipulation im Shell-Profil.": (
            "path_guard_issue_shell_profile_suspicious",
            "Verdächtige PATH-Manipulation im Shell-Profil.",
            "Suspicious PATH manipulation in shell profile.",
        ),
        "Übliche User-Bin-Pfade werden eingebunden.": (
            "path_guard_issue_user_bins_added",
            "Übliche User-Bin-Pfade werden eingebunden.",
            "Common user bin paths are being added.",
        ),
        "/snap/bin steht im PATH, existiert aber nicht.": (
            "path_guard_issue_snap_missing",
            "/snap/bin steht im PATH, existiert aber nicht.",
            "/snap/bin is in PATH but does not exist.",
        ),
    }
    if raw.startswith("Rechte konnten nicht geprüft werden:"):
        detail = raw.split(":", 1)[1].strip()
        return _path_guard_text(
            app,
            "path_guard_issue_permissions_unknown",
            "Rechte konnten nicht geprüft werden: {detail}",
            "Permissions could not be checked: {detail}",
        ).format(detail=detail)
    if raw.startswith("Datei konnte nicht gelesen werden:"):
        detail = raw.split(":", 1)[1].strip()
        return _path_guard_text(
            app,
            "path_guard_issue_file_unreadable",
            "Datei konnte nicht gelesen werden: {detail}",
            "File could not be read: {detail}",
        ).format(detail=detail)
    if raw in mapping:
        key, default_de, default_en = mapping[raw]
        return _path_guard_text(app, key, default_de, default_en)
    return raw


def _translate_path_guard_risk(app, risk: str) -> str:
    raw = str(risk or "").strip().lower()
    mapping = {
        "hoch": (
            "path_guard_risk_high",
            "hoch",
            "high",
        ),
        "mittel": (
            "path_guard_risk_medium",
            "mittel",
            "medium",
        ),
        "niedrig": (
            "path_guard_risk_low",
            "niedrig",
            "low",
        ),
        "unbekannt": (
            "path_guard_risk_unknown",
            "unbekannt",
            "unknown",
        ),
    }
    if raw in mapping:
        key, default_de, default_en = mapping[raw]
        return _path_guard_text(app, key, default_de, default_en)
    return raw or "-"


def _translate_path_guard_severity(app, severity: str) -> str:
    raw = str(severity or "").strip().lower()
    mapping = {
        "high": ("path_guard_severity_high", "hoch", "high"),
        "medium": ("path_guard_severity_medium", "mittel", "medium"),
        "low": ("path_guard_severity_low", "niedrig", "low"),
        "info": ("path_guard_severity_info", "info", "info"),
        "ok": ("path_guard_severity_ok", "ok", "ok"),
        "unknown": ("path_guard_severity_unknown", "unbekannt", "unknown"),
    }
    if raw in mapping:
        key, default_de, default_en = mapping[raw]
        return _path_guard_text(app, key, default_de, default_en)
    return raw or "-"


def _format_path_guard_result(app, result: dict) -> str:
    lines = []
    hints = []
    suspicious_found = False

    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_title",
            "=== PATH Guard Prüfung ===",
            "=== PATH Guard Check ===",
        )
    )
    lines.append("")
    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_risk",
            "Risiko: {value}",
            "Risk: {value}",
        ).format(value=_translate_path_guard_risk(app, result.get("risk", "-")))
    )
    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_high_count",
            "Hoch: {count}",
            "High: {count}",
        ).format(count=result.get("counts", {}).get("high", 0))
    )
    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_medium_count",
            "Mittel: {count}",
            "Medium: {count}",
        ).format(count=result.get("counts", {}).get("medium", 0))
    )
    lines.append("")

    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_current_path",
            "Aktueller PATH:",
            "Current PATH:",
        )
    )
    for idx, entry in enumerate(result.get("path_entries", []), start=1):
        lines.append(f"{idx}. {entry}")

    lines.append("")
    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_path_entries",
            "PATH-Einträge:",
            "PATH entries:",
        )
    )
    relevant_path_findings = False
    for item in result.get("path_findings", []):
        sev = item.get("severity", "ok")
        entry = item.get("entry", "-")
        issues = item.get("issues", [])
        if sev == "ok":
            continue
        if sev == "info":
            for issue in issues:
                if "/snap/bin" in issue:
                    hints.append(_translate_path_guard_issue(app, issue))
                elif "User-Bin-Pfad" in issue:
                    hints.append(
                        _path_guard_text(
                            app,
                            "path_guard_hint_user_bin_entry",
                            "{entry} ist als User-Bin-Pfad im PATH enthalten.",
                            "{entry} is included in PATH as a user bin path.",
                        ).format(entry=entry)
                    )
            continue
        relevant_path_findings = True
        suspicious_found = True
        lines.append(f"- [{_translate_path_guard_severity(app, sev).upper()}] {entry}")
        for issue in issues:
            lines.append(f"  - {_translate_path_guard_issue(app, issue)}")
    if not relevant_path_findings:
        lines.append(
            _path_guard_text(
                app,
                "path_guard_report_no_suspicious_entries",
                "- Keine auffälligen PATH-Einträge erkannt.",
                "- No suspicious PATH entries detected.",
            )
        )

    lines.append("")
    lines.append(
        _path_guard_text(
            app,
            "path_guard_report_shell_profiles",
            "Shell-Profile:",
            "Shell profiles:",
        )
    )
    for profile in result.get("profile_findings", []):
        path = profile.get("path", "-")
        exists = profile.get("exists", False)
        severity = profile.get("severity", "ok")
        matches = profile.get("matches", [])
        lines.append(
            _path_guard_text(
                app,
                "path_guard_report_profile_status",
                "- {path} ({presence}, {severity})",
                "- {path} ({presence}, {severity})",
            ).format(
                path=path,
                presence=_path_guard_text(
                    app,
                    (
                        "path_guard_presence_present"
                        if exists
                        else "path_guard_presence_missing"
                    ),
                    "vorhanden" if exists else "nicht vorhanden",
                    "present" if exists else "not present",
                ),
                severity=_translate_path_guard_severity(app, severity),
            )
        )
        for match in matches:
            if match.get("severity") == "info":
                text = str(match.get("text") or "")
                if "$HOME/.local/bin" in text or "~/.local/bin" in text:
                    hints.append(
                        _path_guard_text(
                            app,
                            "path_guard_hint_local_bin_common",
                            "~/.local/bin wird über .profile/.bashrc ergänzt. Das ist üblich.",
                            "~/.local/bin is added via .profile/.bashrc. This is common.",
                        )
                    )
                if "$HOME/bin" in text or "~/bin" in text:
                    hints.append(
                        _path_guard_text(
                            app,
                            "path_guard_hint_home_bin_common",
                            "~/bin wird über .profile/.bashrc ergänzt. Das ist üblich.",
                            "~/bin is added via .profile/.bashrc. This is common.",
                        )
                    )
                continue
            if match.get("severity") in {"medium", "high"}:
                suspicious_found = True
            lines.append(
                _path_guard_text(
                    app,
                    "path_guard_report_profile_line",
                    "  Zeile {line}: {text}",
                    "  Line {line}: {text}",
                ).format(line=match.get("line"), text=match.get("text"))
            )
            for issue in match.get("issues", []):
                lines.append(f"    - {_translate_path_guard_issue(app, issue)}")

    unique_hints = []
    seen_hints = set()
    for hint in hints:
        normalized = str(hint or "").strip()
        if not normalized or normalized in seen_hints:
            continue
        seen_hints.add(normalized)
        unique_hints.append(normalized)

    if unique_hints:
        lines.append("")
        lines.append(
            _path_guard_text(
                app,
                "path_guard_report_notes",
                "Hinweise:",
                "Notes:",
            )
        )
        for hint in unique_hints:
            lines.append(f"- {hint}")

    lines.append("")
    if suspicious_found:
        lines.append(
            _path_guard_text(
                app,
                "path_guard_report_review_needed",
                "Auffällige PATH-Manipulationen sollten geprüft werden.",
                "Suspicious PATH manipulations should be reviewed.",
            )
        )
    else:
        lines.append(
            _path_guard_text(
                app,
                "path_guard_report_none_detected",
                "Keine auffällige PATH-Manipulation erkannt.",
                "No suspicious PATH manipulation detected.",
            )
        )

    return "\n".join(lines)


def set_path_guard_light(app, state: str, message: str = ""):
    app.path_guard_last_state = str(state or "unknown")
    status_text = message or ""
    light = _app_value(app, "l_path_guard")

    if state == "ok":
        app.set_light(light, "green")
        if not status_text:
            status_text = "PATH Guard: Risiko niedrig"
    elif state == "warning":
        app.set_light(light, "yellow")
        if not status_text:
            status_text = "PATH Guard: Risiko mittel"
    elif state == "error":
        app.set_light(light, "red")
        if not status_text:
            status_text = "PATH Guard: Risiko hoch"
    else:
        app.set_light(light, "gray")
        if not status_text:
            status_text = "PATH Guard: noch nicht geprüft"

    _app_var_set(app, "path_guard_status_var", status_text)


def run_path_guard_check(app):
    try:
        open_tab = _app_value(app, "_open_security_menu_target_tab")
        if callable(open_tab):
            open_tab("path_guard")
        service = _app_value(app, "path_guard_service")
        if service is None:
            app.set_path_guard_light("unknown", "PATH Guard: Service nicht verfügbar.")
            app.log("PATH Guard: Service nicht verfügbar.")
            return
        result = service.run_check()
        app.path_guard_last_result = result
        text = _format_path_guard_result(app, result)
        risk = str(result.get("risk") or "").strip().lower()

        if risk == "hoch":
            app.set_path_guard_light("error", "PATH Guard: Risiko hoch")
        elif risk == "mittel":
            app.set_path_guard_light("warning", "PATH Guard: Risiko mittel")
        elif risk == "niedrig":
            app.set_path_guard_light("ok", "PATH Guard: Risiko niedrig")
        else:
            app.set_path_guard_light("unknown", "PATH Guard: Risiko unbekannt")

        detail_widget = _app_value(app, "path_guard_detail") or _app_value(
            app, "security_detail"
        )
        if detail_widget is not None:
            detail_widget.configure(state="normal")
            detail_widget.delete("1.0", "end")
            detail_widget.insert("1.0", text)
            detail_widget.see("1.0")
            try:
                detail_widget.focus_set()
            except Exception:
                pass
            direct_scroll_fn = _app_value(app, "scroll_main_page_to_widget")
            if callable(direct_scroll_fn):
                try:
                    direct_scroll_fn(detail_widget)
                except Exception:
                    pass
            scroll_fn = _app_value(app, "scroll_main_page_to_widget_later")
            if callable(scroll_fn):
                try:
                    scroll_fn(detail_widget, top_margin=16, delay_ms=100, repeat=4)
                except Exception:
                    pass
        app.log(f"PATH Guard: Prüfung abgeschlossen (Risiko: {result.get('risk')}).")
    except Exception as exc:
        app.set_path_guard_light("error", "PATH Guard: Fehler bei der Prüfung")
        app.log(f"PATH Guard: Fehler: {exc}")


def analyze_path_guard_with_chad(app):
    result = _app_value(app, "path_guard_last_result")
    if not result:
        app.log("PATH Guard: Keine Prüfung vorhanden.")
        return

    text = _format_path_guard_result(app, result)
    app.prepare_chad_analysis("PATH Guard Analyse", text)
