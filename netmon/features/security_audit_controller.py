"""Security audit controller helpers for NetMon."""

from __future__ import annotations

import os
import re
import threading
from datetime import datetime
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


def open_lynis_tab(app):
    app._select_security_tab(app.tab_lynis)


def _lynis_running(app) -> bool:
    return bool(_app_value(app, "lynis_running", False))


def _lynis_summary_text(mode: str) -> str:
    return (
        "Quick Scan wird ausgeführt ..."
        if mode == "quick"
        else "Full Security Scan wird ausgeführt ..."
    )


def _lynis_start_log_message(mode: str) -> str:
    return (
        "Lynis Quick Scan gestartet (ohne root)"
        if mode == "quick"
        else "Lynis Full Scan gestartet (sudo erforderlich)"
    )


def _lynis_finish_log_message(mode: str, rc: int) -> str:
    label = "Quick" if mode == "quick" else "Full"
    if rc == 0:
        return f"Lynis {label} Scan abgeschlossen."
    if rc == 124:
        return f"Lynis {label} Scan Timeout (rc=124)."
    return f"Lynis {label} Scan fehlgeschlagen (rc={rc})."


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
        _app_var_set(app, "lynis_summary_var", "Noch kein Audit ausgeführt.")


def update_lynis_output(app, text: str, *, append: bool = False, normalize_output_fn):
    widget = _app_value(app, "lynis_text")
    if widget is None:
        return
    clean_text = normalize_output_fn(text)
    _set_text_widget_content(widget, clean_text, append=append)


def extract_lynis_issues_and_recommendations(text: str, *, normalize_output_fn) -> str:
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
        return (
            "=== Lynis Probleme & Empfehlungen ===\n\n"
            "Keine eindeutigen Probleme oder Empfehlungen gefunden."
        )

    return "=== Lynis Probleme & Empfehlungen ===\n\n" + "\n".join(lines)


def show_lynis_issues_only(app, *, normalize_output_fn):
    text = _app_value(app, "lynis_last_output", "") or ""
    if not text.strip():
        app.log("Lynis: Keine Ausgabe vorhanden.")
        return

    filtered = extract_lynis_issues_and_recommendations(
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
        app.log("Lynis: Keine Ausgabe vorhanden.")
        return

    filtered = extract_lynis_issues_and_recommendations(
        text,
        normalize_output_fn=normalize_output_fn,
    )
    app.prepare_chad_analysis("Lynis Probleme Analyse", filtered)


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

    status = "OK" if rc == 0 else f"Fehler (rc={rc})"
    _app_var_set(
        app,
        "lynis_summary_var",
        f"Status: {status} | Hardening Index: {hardening} | Warnings: {warnings_count} | Suggestions: {suggestions_count}",
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
    clean_output = normalize_output_fn(out or "Keine Ausgabe.")
    app.lynis_last_output = clean_output
    timed_out = rc == 124
    _app_var_set(
        app,
        "lynis_status_var",
        (
            "abgeschlossen"
            if rc == 0
            else ("Timeout" if timed_out else f"Fehler (rc={rc})")
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
    app.log(_lynis_finish_log_message(mode, rc))


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
        timeout_note = (
            f"Scan nach {timeout}s beendet (Timeout).\n"
            "Hinweis: Full Scans können je nach System länger dauern."
        )
        clean = normalize_output_fn(
            f"{timeout_note}\n\n{clean}" if clean else timeout_note
        )
    output = normalize_output_fn(f"{header}\n\n{clean or 'Keine Ausgabe.'}")
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
        app.log_safe("Lynis-Audit läuft bereits.")
        app.open_lynis_tab()
        return
    if not has_cmd_runner("lynis"):
        app.lynis_status_var.set("nicht installiert")
        app.lynis_summary_var.set("Lynis fehlt. Installationshinweis im Log verfügbar.")
        app.update_lynis_output(
            "Lynis ist nicht installiert. Bitte den Installationshinweis im Log verwenden."
        )
        app.show_lynis_install_hint()
        app.open_lynis_tab()
        return

    app.lynis_running = True
    app.lynis_active_process = "thread"
    app.lynis_status_var.set("läuft")
    app.lynis_summary_var.set(_lynis_summary_text(mode))
    app.open_lynis_tab()
    app.clear_lynis_output()
    app.update_lynis_output(f"{header}\n\nScan gestartet. Ausgabe folgt ...")
    app._set_lynis_buttons_state(False)
    app.log(_lynis_start_log_message(mode))
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
        header="=== Lynis Quick Scan (eingeschränkt) ===",
    )


def run_lynis_full(app):
    messagebox.showinfo(
        "Lynis Full Scan",
        "Dieser Scan benötigt Administratorrechte (sudo).\n\n"
        "Er führt eine vollständige Sicherheitsprüfung durch.",
        parent=app,
    )
    if not app.ensure_sudo_session("Lynis Full Security Scan"):
        return
    app._start_lynis_scan(
        mode="full",
        cmd=["sudo", "lynis", "audit", "system", "--no-colors"],
        timeout=600,
        header="=== Lynis Full Security Scan (sudo) ===",
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


def clear_rkhunter_output(app):
    update_rkhunter_output(app, "")
    if not bool(_app_value(app, "rkhunter_running", False)) and not bool(
        _app_value(app, "rkhunter_updating", False)
    ):
        _app_var_set(app, "rkhunter_summary_var", "Noch kein Scan ausgeführt.")


def update_rkhunter_summary_from_output(app, output: str, rc: int):
    cleaned_output = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", output or "")
    warning_count = len(re.findall(r"\bWarning\b", cleaned_output, re.IGNORECASE))
    ok_count = len(re.findall(r"\bOK\b", cleaned_output, re.IGNORECASE))
    suspect_hits = len(
        re.findall(
            r"\b(found|suspect|infected|rootkit)\b", cleaned_output, re.IGNORECASE
        )
    )

    status = "unauffällig"
    if warning_count > 0 or suspect_hits > 0:
        status = "Hinweise/Warnungen gefunden"
    if rc not in (0,):
        status = f"Prüfung beendet (rc={rc})"

    _app_var_set(
        app,
        "rkhunter_summary_var",
        f"Warnungen: {warning_count} | OK-Meldungen: {ok_count} | Status: {status}",
    )
    app.rkhunter_last_result = {
        "rc": rc,
        "warnings": warning_count,
        "ok": ok_count,
        "suspect_hits": suspect_hits,
        "status": status,
    }


def _set_rkhunter_action_buttons_state(app, enabled: bool):
    dep_status = _app_value(app, "dep_status", {}) or {}
    state = "normal" if enabled and dep_status.get("rkhunter") else "disabled"
    update_btn = _app_value(app, "btn_rkhunter_update")
    if update_btn is not None:
        update_btn.configure(state=state)
    scan_btn = _app_value(app, "btn_rkhunter_scan")
    if scan_btn is not None:
        scan_btn.configure(state=state)


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
        _app_var_set(app, "rkhunter_status_var", "Konfig-Problem")
    else:
        _app_var_set(
            app,
            "rkhunter_status_var",
            "bereit" if rc == 0 else f"Update-Fehler (rc={rc})",
        )
    app.update_rkhunter_output(out or "Keine Ausgabe.")
    if app._looks_like_rkhunter_web_cmd_issue(out):
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Update durch fehlerhafte WEB_CMD-Konfiguration blockiert.",
        )
        app.show_rkhunter_web_cmd_hint()
    elif update_problem:
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "RKHunter update failed | Reason: mirror database/config problem detected | Action available: Repair configuration and retry update",
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
            app.rkhunter_last_update_var.set("Updates aktuell")
        elif rc == 0:
            app.rkhunter_last_update_var.set(datetime.now().strftime("%Y-%m-%d"))
        _app_var_set(
            app,
            "rkhunter_summary_var",
            (
                "rkhunter-Datenbasis aktualisiert."
                if rc == 0
                else f"Update beendet (rc={rc})."
            ),
        )
    _set_rkhunter_action_buttons_state(app, True)
    app.log_safe(
        "rkhunter-Update abgeschlossen."
        if rc == 0
        else f"rkhunter-Update fehlgeschlagen (rc={rc})."
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
        app.log_safe("rkhunter läuft bereits.")
        app.open_rkhunter_tab()
        return
    if not is_rkhunter_installed_fn():
        _app_var_set(app, "rkhunter_status_var", "nicht installiert")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter fehlt. Installationshinweis im Log verfügbar.",
        )
        app.update_rkhunter_output(
            "rkhunter ist nicht installiert. Bitte den Installationshinweis im Log verwenden."
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Update"):
        _app_var_set(app, "rkhunter_status_var", "sudo abgebrochen")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Update wurde ohne sudo-Freigabe nicht gestartet.",
        )
        app.update_rkhunter_output(
            "rkhunter benötigt Root-Rechte. Bitte sudo-Freigabe erteilen und den Update-Vorgang erneut starten."
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    app._set_rkhunter_repair_available(False)
    _app_var_set(app, "rkhunter_status_var", "update läuft")
    _app_var_set(app, "rkhunter_summary_var", "rkhunter-Update wird ausgeführt ...")
    app.open_rkhunter_tab()
    app.update_rkhunter_output("rkhunter Update wird gestartet...")
    _set_rkhunter_action_buttons_state(app, False)
    app.log_safe("rkhunter-Update gestartet.")
    threading.Thread(target=app._rkhunter_update_worker, daemon=True).start()


def finish_rkhunter_repair(
    app, backup_rc, backup_out, repair_rc, repair_out, *, backup_path
):
    if backup_rc != 0:
        app.rkhunter_updating = False
        app.rkhunter_active_process = None
        _app_var_set(app, "rkhunter_status_var", "Repair-Fehler")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "Backup der rkhunter-Konfiguration fehlgeschlagen.",
        )
        app.update_rkhunter_output(
            (backup_out or "Backup fehlgeschlagen.")
            + "\n\nKeine Änderungen wurden angewendet."
        )
        _set_rkhunter_action_buttons_state(app, True)
        app._set_rkhunter_repair_available(True)
        app.log_safe(
            "rkhunter-Repair fehlgeschlagen: Backup konnte nicht erstellt werden."
        )
        return

    if repair_rc != 0:
        app.rkhunter_updating = False
        app.rkhunter_active_process = None
        _app_var_set(app, "rkhunter_status_var", "Repair-Fehler")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Konfiguration konnte nicht repariert werden.",
        )
        app.update_rkhunter_output(
            (repair_out or "Repair fehlgeschlagen.") + f"\n\nBackup: {backup_path}"
        )
        _set_rkhunter_action_buttons_state(app, True)
        app._set_rkhunter_repair_available(True)
        app.log_safe(
            "rkhunter-Repair fehlgeschlagen: Konfiguration konnte nicht geschrieben werden."
        )
        return

    app.update_rkhunter_output(
        "RKHunter update configuration repaired\n"
        f"Backup: {backup_path}\n\n"
        "Update wird erneut ausgeführt ...",
        append=False,
    )
    _app_var_set(app, "rkhunter_summary_var", "RKHunter update configuration repaired")
    _app_var_set(app, "rkhunter_status_var", "retry update läuft")
    app.log_safe("rkhunter-Konfiguration repariert, Update wird erneut gestartet.")
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
        app.log_safe("rkhunter läuft bereits.")
        app.open_rkhunter_tab()
        return
    if not is_rkhunter_installed_fn():
        _app_var_set(app, "rkhunter_status_var", "nicht installiert")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter fehlt. Installationshinweis im Log verfügbar.",
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Repair"):
        _app_var_set(app, "rkhunter_status_var", "sudo abgebrochen")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Repair wurde ohne sudo-Freigabe nicht gestartet.",
        )
        app.update_rkhunter_output(
            "rkhunter-Repair benötigt Root-Rechte. Bitte sudo-Freigabe erteilen und die Reparatur erneut starten."
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_updating = True
    app.rkhunter_active_process = "thread"
    _app_var_set(app, "rkhunter_status_var", "repair läuft")
    _app_var_set(
        app,
        "rkhunter_summary_var",
        "RKHunter update failed | Reason: mirror database/config problem detected | Action available: Repair configuration and retry update",
    )
    app.open_rkhunter_tab()
    app.update_rkhunter_output(
        "RKHunter update failed\n"
        "Reason: mirror database/config problem detected\n"
        "Action available: Repair configuration and retry update\n\n"
        "Backup wird erstellt und Konfiguration repariert ...",
        append=False,
    )
    _set_rkhunter_action_buttons_state(app, False)
    app._set_rkhunter_repair_available(False)
    app.log_safe("rkhunter-Repair gestartet.")
    threading.Thread(target=app._rkhunter_repair_worker, daemon=True).start()


def finish_rkhunter_scan(app, rc, out):
    app.rkhunter_running = False
    app.rkhunter_active_process = None
    if app._looks_like_rkhunter_web_cmd_issue(out):
        _app_var_set(app, "rkhunter_status_var", "Konfig-Fehler")
    else:
        _app_var_set(
            app,
            "rkhunter_status_var",
            "abgeschlossen" if rc == 0 else f"Fehler/Warnung (rc={rc})",
        )
    app.update_rkhunter_output(out or "Keine Ausgabe.")
    if app._looks_like_rkhunter_web_cmd_issue(out):
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Scan durch fehlerhafte WEB_CMD-Konfiguration blockiert.",
        )
        app.show_rkhunter_web_cmd_hint()
    else:
        app._update_rkhunter_summary_from_output(out or "", rc)
    _set_rkhunter_action_buttons_state(app, True)
    app.log_safe(
        "rkhunter-Scan abgeschlossen."
        if rc == 0
        else "rkhunter-Scan mit Hinweis/Warnung beendet."
    )


def rkhunter_scan_worker(app):
    rc, out = run_cmd(
        ["sudo", "-n", "rkhunter", "--check", "--skip-keypress", "--nocolors"],
        timeout=1800,
    )
    call_in_ui_thread(app, lambda r=rc, o=out: app._finish_rkhunter_scan(r, o))


def rkhunter_scan_async(
    app,
    *,
    is_rkhunter_installed_fn,
):
    if app.rkhunter_running or app.rkhunter_updating:
        app.log_safe("rkhunter läuft bereits.")
        app.open_rkhunter_tab()
        return
    if not is_rkhunter_installed_fn():
        _app_var_set(app, "rkhunter_status_var", "nicht installiert")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter fehlt. Installationshinweis im Log verfügbar.",
        )
        app.update_rkhunter_output(
            "rkhunter ist nicht installiert. Bitte den Installationshinweis im Log verwenden."
        )
        app.show_rkhunter_install_hint()
        app.open_rkhunter_tab()
        return
    if not app.ensure_sudo_session("rkhunter Scan"):
        _app_var_set(app, "rkhunter_status_var", "sudo abgebrochen")
        _app_var_set(
            app,
            "rkhunter_summary_var",
            "rkhunter-Scan wurde ohne sudo-Freigabe nicht gestartet.",
        )
        app.update_rkhunter_output(
            "rkhunter benötigt Root-Rechte. Bitte sudo-Freigabe erteilen und den Scan erneut starten."
        )
        app.open_rkhunter_tab()
        return

    app.rkhunter_running = True
    app.rkhunter_active_process = "thread"
    _app_var_set(app, "rkhunter_status_var", "scan läuft")
    _app_var_set(app, "rkhunter_summary_var", "rkhunter-Scan wird ausgeführt ...")
    app.open_rkhunter_tab()
    app.clear_rkhunter_output()
    app.update_rkhunter_output("rkhunter-Scan gestartet. Ausgabe folgt ...")
    _set_rkhunter_action_buttons_state(app, False)
    app.log_safe("rkhunter-Scan gestartet.")
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
            "Prüfung: läuft"
            if bool(_app_value(app, "startup_guard_running", False))
            else "Prüfung: bereit"
        ),
    )
    _app_var_set(
        app,
        "startup_guard_visible_count_var",
        f"Sichtbare Einträge: {len(_app_list(app, 'startup_guard_visible_entries'))}",
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
        "=== Startup Guard Prüfung ===",
        "",
        f"Aktuelle Einträge: {current_count}",
        "",
        "Neue Einträge:",
    ]
    if new_entries:
        lines.extend(format_startup_guard_entry(entry) for entry in new_entries)
    else:
        lines.append("- Keine neuen Einträge.")

    lines.extend(["", "Entfernte Einträge:"])
    if removed_entries:
        lines.extend(format_startup_guard_entry(entry) for entry in removed_entries)
    else:
        lines.append("- Keine entfernten Einträge.")

    lines.extend(["", "Geänderte Einträge:"])
    if changed_entries:
        for item in changed_entries:
            before = item.get("before") or {}
            after = item.get("after") or {}
            lines.append(format_startup_guard_entry(after or before))
            lines.append(
                "  Änderung: "
                f"sha256 {before.get('sha256', '') != after.get('sha256', '')}, "
                f"size {before.get('size', 0)} -> {after.get('size', 0)}, "
                f"mtime {before.get('mtime', 0)} -> {after.get('mtime', 0)}"
            )
    else:
        lines.append("- Keine geänderten Einträge.")

    lines.extend(["", "Vertrauensliste / bekannt:"])
    if trusted_entries:
        for entry in trusted_entries:
            item = startup_guard_status_entry("TRUSTED", entry)
            lines.append(format_startup_guard_entry(item))
    else:
        lines.append("- Keine bekannten Einträge.")

    lines.extend(["", "Unverändert:"])
    lines.append(f"Anzahl: {len(unchanged_entries)}")
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
    lines = ["=== Startup Guard Vertrauensliste ===", ""]

    if not trusted:
        lines.append(
            app.tr(
                "startup_guard_trustlist_empty",
                "Keine Einträge vorhanden.",
            )
        )
    else:
        for path, item in sorted(trusted.items()):
            lines.append(f"- {item.get('name', '-')}")
            lines.append(f"  Pfad: {path}")
            lines.append(f"  SHA256: {item.get('sha256', '-')}")
            lines.append(f"  Markiert: {item.get('trusted_at', '-')}")
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
        entries = service.collect_entries()
        ok, err = service.save_baseline(
            app.startup_guard_baseline_path,
            entries,
        )

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
            "\n".join(
                [
                    "=== Startup Guard Prüfung ===",
                    "",
                    "Es ist noch keine Baseline vorhanden.",
                    "Bitte zuerst 'Baseline erstellen' ausführen.",
                ]
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
        baseline = service.load_baseline(app.startup_guard_baseline_path)
        trustlist = _startup_guard_trustlist(app)
        current = service.collect_entries()
        result = service.compare_to_baseline(baseline, current, trustlist)

        def finish():
            app.startup_guard_running = False
            app.startup_guard_last_result = result
            app.startup_guard_status_var.set(
                app.tr(
                    "startup_guard_status_check_done",
                    "Prüfung abgeschlossen",
                )
            )
            update_startup_guard_status_line(app)
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
    lines = []
    hints = []
    suspicious_found = False

    lines.append("=== PATH Guard Prüfung ===")
    lines.append("")
    lines.append(f"Risiko: {result.get('risk', '-')}")
    lines.append(f"Hoch: {result.get('counts', {}).get('high', 0)}")
    lines.append(f"Mittel: {result.get('counts', {}).get('medium', 0)}")
    lines.append("")

    lines.append("Aktueller PATH:")
    for idx, entry in enumerate(result.get("path_entries", []), start=1):
        lines.append(f"{idx}. {entry}")

    lines.append("")
    lines.append("PATH-Einträge:")
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
                    hints.append(issue)
                elif "User-Bin-Pfad" in issue:
                    hints.append(f"{entry} ist als User-Bin-Pfad im PATH eingebunden.")
            continue
        relevant_path_findings = True
        suspicious_found = True
        lines.append(f"- [{sev.upper()}] {entry}")
        for issue in issues:
            lines.append(f"  - {issue}")
    if not relevant_path_findings:
        lines.append("- Keine auffälligen PATH-Einträge erkannt.")

    lines.append("")
    lines.append("Shell-Profile:")
    for profile in result.get("profile_findings", []):
        path = profile.get("path", "-")
        exists = profile.get("exists", False)
        severity = profile.get("severity", "ok")
        matches = profile.get("matches", [])
        lines.append(
            f"- {path} ({'vorhanden' if exists else 'nicht vorhanden'}, {severity})"
        )
        for match in matches:
            if match.get("severity") == "info":
                text = str(match.get("text") or "")
                if "$HOME/.local/bin" in text or "~/.local/bin" in text:
                    hints.append(
                        "~/.local/bin wird über .profile/.bashrc eingebunden. Das ist üblich."
                    )
                if "$HOME/bin" in text or "~/bin" in text:
                    hints.append(
                        "~/bin wird über .profile/.bashrc eingebunden. Das ist üblich."
                    )
                continue
            if match.get("severity") in {"medium", "high"}:
                suspicious_found = True
            lines.append(f"  Zeile {match.get('line')}: {match.get('text')}")
            for issue in match.get("issues", []):
                lines.append(f"    - {issue}")

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
        lines.append("Hinweise:")
        for hint in unique_hints:
            lines.append(f"- {hint}")

    lines.append("")
    if suspicious_found:
        lines.append("Verdächtige PATH-Manipulationen sollten geprüft werden.")
    else:
        lines.append("Keine verdächtige PATH-Manipulation erkannt.")

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
        service = _app_value(app, "path_guard_service")
        if service is None:
            app.set_path_guard_light("unknown", "PATH Guard: Service nicht verfügbar.")
            app.log("PATH Guard: Service nicht verfügbar.")
            return
        result = service.run_check()
        app.path_guard_last_result = result
        text = format_path_guard_result(result)
        risk = str(result.get("risk") or "").strip().lower()

        if risk == "hoch":
            app.set_path_guard_light("error", "PATH Guard: Risiko hoch")
        elif risk == "mittel":
            app.set_path_guard_light("warning", "PATH Guard: Risiko mittel")
        elif risk == "niedrig":
            app.set_path_guard_light("ok", "PATH Guard: Risiko niedrig")
        else:
            app.set_path_guard_light("unknown", "PATH Guard: Risiko unbekannt")

        detail_widget = _app_value(app, "security_detail")
        if detail_widget is not None:
            detail_widget.configure(state="normal")
            if detail_widget.index("end-1c") != "1.0":
                detail_widget.insert("end", "\n\n")
            detail_widget.insert("end", text)
            detail_widget.see("end")
            detail_widget.configure(state="normal")
        app.log(f"PATH Guard: Prüfung abgeschlossen (Risiko: {result.get('risk')}).")
    except Exception as exc:
        app.set_path_guard_light("error", "PATH Guard: Fehler bei der Prüfung")
        app.log(f"PATH Guard: Fehler: {exc}")


def analyze_path_guard_with_chad(app):
    result = _app_value(app, "path_guard_last_result")
    if not result:
        app.log("PATH Guard: Keine Prüfung vorhanden.")
        return

    text = format_path_guard_result(result)
    app.prepare_chad_analysis("PATH Guard Analyse", text)
