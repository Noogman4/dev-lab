"""Security audit controller helpers for NetMon."""

from __future__ import annotations

import collections
import os
import json
import grp
import platform
import pwd
import re
import shutil
import stat
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from time import monotonic
from tkinter import messagebox

try:
    from netmon.core.privileged_config import write_privileged_config
except ModuleNotFoundError:
    from core.privileged_config import write_privileged_config

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread

try:
    from netmon.core.command import check_sudo_nopasswd, run_cmd
except ModuleNotFoundError:
    from core.command import check_sudo_nopasswd, run_cmd

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

try:
    from netmon.services.repository_guard_service import RepositoryGuardService
except ModuleNotFoundError:
    try:
        from services.repository_guard_service import RepositoryGuardService
    except ModuleNotFoundError:
        RepositoryGuardService = None


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


LYNIS_ISSUE_KEEP_KEYWORDS = (
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
)


def _lynis_issue_line_is_relevant(line: str) -> bool:
    low = str(line or "").lower()
    if not any(keyword in low for keyword in LYNIS_ISSUE_KEEP_KEYWORDS):
        return False
    if "gefunden" in low and not (
        "dateien gefunden" in low
        or "warn" in low
        or "problem" in low
        or "fehler" in low
    ):
        return False
    return True


def _lynis_relevant_issue_lines(text: str) -> list[str]:
    return [
        line
        for line in str(text or "").splitlines()
        if _lynis_issue_line_is_relevant(line)
    ]


def extract_lynis_issues_and_recommendations(
    app, text: str, *, normalize_output_fn
) -> str:
    text = normalize_output_fn(text)

    lines = _lynis_relevant_issue_lines(text)

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


def _lynis_summary_value(cleaned_output: str, label: str) -> str:
    label_text = str(label or "").strip()
    if not label_text:
        return "-"
    patterns = [
        rf"{re.escape(label_text)}\s*\((\d+)\)",
        rf"{re.escape(label_text)}\s*:?\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, cleaned_output or "", re.IGNORECASE)
        if match:
            return match.group(1)
    return "-"


def update_lynis_summary_from_output(app, output: str, rc: int, *, normalize_output_fn):
    cleaned_output = normalize_output_fn(output)

    hardening = _lynis_summary_value(cleaned_output, "Hardening index")
    warnings_count = _lynis_summary_value(cleaned_output, "Warnings")
    suggestions_count = _lynis_summary_value(cleaned_output, "Suggestions")
    tests_count = _lynis_summary_value(cleaned_output, "Tests performed")
    _app_var_set(
        app,
        "lynis_hardening_index_var",
        app.tr(
            "lynis_hardening_index_value",
            "Hardening Index: {value}",
        ).format(value=hardening),
    )

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
        "tests": tests_count,
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
    if _app_list(app, "security_baseline_results"):
        app.security_baseline_results = _attach_lynis_references(
            app, _app_list(app, "security_baseline_results")
        )
        app.lynis_security_baseline_state = _lynis_security_baseline_state(app)
        refresh_security_baseline_overview(app)
        refresh_security_baseline_table(app)
        save_fn = _app_value(app, "_save_security_baseline", None)
        if callable(save_fn):
            try:
                save_fn()
            except Exception:
                pass
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
        _app_var_set(
            app,
            "lynis_hardening_index_var",
            app.tr("lynis_hardening_index_default", "Hardening Index: -"),
        )
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
    _app_var_set(
        app,
        "lynis_hardening_index_var",
        app.tr("lynis_hardening_index_default", "Hardening Index: -"),
    )
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


SECURITY_BASELINE_PROFILES = {
    "zorin_desktop_development": {
        "id": "zorin_desktop_development",
        "name": "NetMon Security Baseline",
        "profile": "Desktop / Development",
        "version": "1.0",
        "reference": "Zorin OS 18 / Ubuntu 24.04",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Zorin OS",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
    },
    "ubuntu_desktop_development": {
        "id": "ubuntu_desktop_development",
        "name": "NetMon Security Baseline",
        "profile": "Desktop / Development",
        "version": "1.0",
        "reference": "Ubuntu 24.04 Desktop",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Ubuntu",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
    },
    "linuxmint_desktop_development": {
        "id": "linuxmint_desktop_development",
        "name": "NetMon Security Baseline",
        "profile": "Desktop / Development",
        "version": "1.0",
        "reference": "Linux Mint 22 Desktop",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Linux Mint",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
    },
    "debian_desktop_development": {
        "id": "debian_desktop_development",
        "name": "NetMon Security Baseline",
        "profile": "Desktop / Development",
        "version": "1.0",
        "reference": "Debian 12/13 Desktop",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Debian",
        "base_distribution": "Debian",
        "roles": ["desktop", "development"],
        "apply_supported": "mit Anpassungen",
    },
    "desktop_safe_v1": {
        "id": "desktop_safe_v1",
        "name": "NetMon Security Baseline",
        "profile": "Desktop Safe",
        "version": "1.0",
        "reference": "Zorin / Mint / Ubuntu Desktop",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Desktop Linux",
        "base_distribution": "Ubuntu 24.04 / Debian-like",
        "roles": ["desktop", "safe", "compatibility"],
        "mode": "safe",
        "requires_snapshot": True,
        "apply_supported": True,
        "sections": {
            "services": {
                "keep": [
                    "dbus.service",
                    "gdm.service",
                    "cron.service",
                    "wpa_supplicant.service",
                    "udisks2.service",
                    "fail2ban.service",
                    "unattended-upgrades.service",
                    "getty@tty1.service",
                    "tpm-udev.service",
                    "thermald.service",
                ],
                "auto_optional": [
                    {
                        "name": "whoopsie.service",
                        "action": "disable",
                        "enabled_if": "service_exists",
                    },
                    {
                        "name": "systemd-bsod.service",
                        "action": "disable",
                        "enabled_if": "service_exists",
                    },
                ],
                "manual_review": [
                    {
                        "name": "snapd.service",
                        "reason": "Nur deaktivieren, wenn keine Snap-Pakete genutzt werden.",
                    },
                    {
                        "name": "rc-local.service",
                        "reason": "Nur deaktivieren, wenn /etc/rc.local ungenutzt ist.",
                    },
                    {
                        "name": "anacron.service",
                        "reason": "Nur nach Profilpruefung deaktivieren.",
                    },
                    {
                        "name": "networkd-dispatcher.service",
                        "reason": "Nur nach Abhaengigkeitspruefung deaktivieren.",
                    },
                    {
                        "name": "fancontrol.service",
                        "reason": "Nur deaktivieren, wenn die manuelle Lueftersteuerung ungenutzt ist.",
                    },
                ],
            },
            "checks": {
                "overrides": {
                    "fw.ufw_rules_non_empty": {
                        "profile_policy": "manual_if_missing",
                        "expected": "profilabhaengig",
                        "exceptions": "Im Safe-Profil genuegt eine aktive UFW-Grundabsicherung. Zusaetzliche Regeln bleiben kontextabhaengig.",
                    },
                    "fw.fail2ban_installed": {
                        "profile_policy": "recommended",
                        "expected": "empfohlen",
                    },
                    "fw.fail2ban_active": {
                        "profile_policy": "recommended",
                        "expected": "empfohlen",
                    },
                    "fw.fail2ban_jail_local_exists": {
                        "profile_policy": "recommended",
                        "expected": "empfohlen",
                    },
                    "tools.rkhunter_installed": {
                        "profile_policy": "recommended",
                        "expected": "empfohlen",
                    },
                    "tools.clamav_installed": {
                        "profile_policy": "recommended",
                        "expected": "empfohlen",
                    },
                },
                "manual_review": [
                    {
                        "id": "deleted_files_in_use",
                        "reason": "Nach Updates Neustart oder gezielten Dienstneustart pruefen.",
                    },
                    {
                        "id": "remote_logging",
                        "reason": "Optional, kein Desktop-Safe-Standard.",
                    },
                    {
                        "id": "sysstat_enabled",
                        "reason": "Optional, kein Pflicht-Hardening fuer Desktop Safe.",
                    },
                    {
                        "id": "kernel.modules_disabled",
                        "reason": "Nicht automatisch in Desktop Safe setzen.",
                    },
                ],
            },
        },
    },
    "ubuntu_server_hardening": {
        "id": "ubuntu_server_hardening",
        "name": "NetMon Security Baseline",
        "profile": "Server / Haertung",
        "version": "1.0",
        "reference": "Ubuntu 24.04 Server",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Ubuntu",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["server", "hardening"],
        "apply_supported": "teilweise",
        "sections": {
            "checks": {
                "overrides": {
                    "sysctl.net.ipv4.conf.all.rp_filter": {
                        "profile_policy": "strict_rp_filter",
                        "expected": "1",
                    },
                    "sysctl.net.ipv4.conf.default.rp_filter": {
                        "profile_policy": "strict_rp_filter",
                        "expected": "1",
                    },
                }
            }
        },
    },
    "zorin_vpn_multi_interface": {
        "id": "zorin_vpn_multi_interface",
        "name": "NetMon Security Baseline",
        "profile": "VPN / Multi-Interface",
        "version": "1.0",
        "reference": "Zorin OS 18 / Ubuntu 24.04",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Zorin OS",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
        "sections": {
            "checks": {
                "manual_review": [
                    {
                        "id": "vpn_interface_rules",
                        "reason": "VPN-Interfaces, Tunnel-Endpunkte und Routing-Regeln muessen nach Aufbau und Slot-Modell manuell bewertet werden.",
                    }
                ]
            }
        },
    },
    "ubuntu_vpn_multi_interface": {
        "id": "ubuntu_vpn_multi_interface",
        "name": "NetMon Security Baseline",
        "profile": "VPN / Multi-Interface",
        "version": "1.0",
        "reference": "Ubuntu 24.04 VPN / Multi-Interface",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Ubuntu",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
        "sections": {
            "checks": {
                "manual_review": [
                    {
                        "id": "vpn_interface_rules",
                        "reason": "VPN-Interfaces, Tunnel-Endpunkte und Routing-Regeln muessen nach Aufbau und Slot-Modell manuell bewertet werden.",
                    }
                ]
            }
        },
    },
    "linuxmint_vpn_multi_interface": {
        "id": "linuxmint_vpn_multi_interface",
        "name": "NetMon Security Baseline",
        "profile": "VPN / Multi-Interface",
        "version": "1.0",
        "reference": "Linux Mint 22 VPN / Multi-Interface",
        "date": "19.07.2026",
        "os_family": "debian_like",
        "distribution": "Linux Mint",
        "base_distribution": "Ubuntu 24.04",
        "roles": ["desktop", "development", "vpn", "multi-interface"],
        "apply_supported": True,
        "sections": {
            "checks": {
                "manual_review": [
                    {
                        "id": "vpn_interface_rules",
                        "reason": "VPN-Interfaces, Tunnel-Endpunkte und Routing-Regeln muessen nach Aufbau und Slot-Modell manuell bewertet werden.",
                    }
                ]
            }
        },
    },
    "fedora_workstation_review": {
        "id": "fedora_workstation_review",
        "name": "NetMon Security Baseline",
        "profile": "Workstation / Review",
        "version": "1.0",
        "reference": "Fedora Workstation",
        "date": "19.07.2026",
        "os_family": "rpm_like",
        "distribution": "Fedora",
        "base_distribution": "Fedora",
        "roles": ["desktop", "development"],
        "apply_supported": False,
    },
}

SECURITY_BASELINE_DEFAULT_PROFILE_ID = "zorin_desktop_development"
SECURITY_BASELINE_PROFILE = dict(
    SECURITY_BASELINE_PROFILES[SECURITY_BASELINE_DEFAULT_PROFILE_ID]
)
SECURITY_BASELINE_SYSCTL_DROPIN_PATH = "/etc/sysctl.d/99-zz-netmon-hardening.conf"
SECURITY_BASELINE_UFW_SYSCTL_PATH = "/etc/ufw/sysctl.conf"
SECURITY_BASELINE_UFW_SYSCTL_OVERRIDES = {
    "net.ipv4.conf.all.log_martians": "1",
    "net.ipv4.conf.default.log_martians": "1",
}
SECURITY_BASELINE_TRANSFER_SCHEMA = "netmon.security-baseline.transfer"
SECURITY_BASELINE_TRANSFER_SCHEMA_VERSION = 1

# Fester, dokumentierter Satz von Sysctl-Schluesseln, die NetMon ueber die
# Baseline-Apply-Stufe in /etc/sysctl.d/ schreiben darf (siehe
# docs/security/KERNEL_SYSCTL.md). Importierte Transferpakete duerfen keine
# anderen Schluessel einschleusen — sonst liesse sich z. B.
# kernel.core_pattern = |/pfad/skript setzen und als root ausfuehren.
SECURITY_BASELINE_ALLOWED_SYSCTL_KEYS = frozenset(
    {
        "kernel.kptr_restrict",
        "kernel.sysrq",
        "kernel.perf_event_paranoid",
        "kernel.unprivileged_bpf_disabled",
        "fs.protected_fifos",
        "net.ipv4.conf.all.log_martians",
        "net.ipv4.conf.default.log_martians",
        "net.ipv4.conf.default.accept_source_route",
        "net.ipv4.conf.all.rp_filter",
        "net.ipv4.conf.default.rp_filter",
    }
)

# Struktureller Zusatzschutz: gueltige Sysctl-Schluessel bestehen nur aus
# Kleinbuchstaben/Ziffern/Unterstrich, punktgetrennt (mind. zwei Segmente).
_SYSCTL_KEY_RE = re.compile(r"^[a-z0-9_]+(?:\.[a-z0-9_]+)+$")
# Erlaubte Werte sind einfache Tokens (Zahlen, Wortwerte, leerzeichengetrennte
# Zahlenlisten). Keine Zeilenumbrueche, Pipes, Slashes oder Shell-Metazeichen —
# das schliesst core_pattern-artige Pipe-Handler und mehrzeilige Injektion aus.
_SYSCTL_VALUE_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9 _.,:+-]*[A-Za-z0-9])?$")


def _is_allowed_sysctl_key(key: str) -> bool:
    key = str(key or "").strip()
    return (
        bool(_SYSCTL_KEY_RE.match(key)) and key in SECURITY_BASELINE_ALLOWED_SYSCTL_KEYS
    )


def _is_valid_sysctl_value(value: str) -> bool:
    value = str(value or "")
    if value != value.strip() or "\n" in value or "\r" in value:
        return False
    return bool(_SYSCTL_VALUE_RE.match(value))


SECURITY_BASELINE_UFW_PROFILES = {
    "desktop_development_minimal_v1": {
        "id": "desktop_development_minimal_v1",
        "name": "Desktop / Development Minimal UFW",
        "profile_targets": [
            "zorin_desktop_development",
            "ubuntu_desktop_development",
            "linuxmint_desktop_development",
            "debian_desktop_development",
            "desktop_safe_v1",
        ],
        "default_incoming": "deny",
        "default_outgoing": "allow",
        "post_apply_note": "Weitere Dienstfreigaben nur bewusst und einsatzbezogen setzen.",
        "rules": [
            {"type": "interface", "direction": "in", "iface": "lo"},
            {"type": "interface", "direction": "out", "iface": "lo"},
        ],
    },
    "server_hardening_minimal_v1": {
        "id": "server_hardening_minimal_v1",
        "name": "Server / Haertung Minimal UFW",
        "profile_targets": [
            "ubuntu_server_hardening",
        ],
        "default_incoming": "deny",
        "default_outgoing": "allow",
        "post_apply_note": "Server-spezifische Dienstports wie SSH, HTTPS oder Monitoring bleiben bewusst manuelle Freigaben.",
        "rules": [
            {"type": "interface", "direction": "in", "iface": "lo"},
            {"type": "interface", "direction": "out", "iface": "lo"},
        ],
    },
    "vpn_multi_interface_minimal_v1": {
        "id": "vpn_multi_interface_minimal_v1",
        "name": "VPN / Multi-Interface Minimal UFW",
        "profile_targets": [
            "zorin_vpn_multi_interface",
            "ubuntu_vpn_multi_interface",
            "linuxmint_vpn_multi_interface",
        ],
        "default_incoming": "deny",
        "default_outgoing": "allow",
        "post_apply_note": "VPN-Interfaces, Tunnel-Endpunkte und spezielle Routing-Regeln werden bewusst nicht automatisch abgeleitet und muessen zusaetzlich manuell oder slot-basiert freigegeben werden.",
        "rules": [
            {"type": "interface", "direction": "in", "iface": "lo"},
            {"type": "interface", "direction": "out", "iface": "lo"},
        ],
    },
}

SECURITY_BASELINE_LYNIS_MATCH_RULES = {
    "boot.uefi_active": {"topics": ["uefi", "efi"]},
    "boot.grub_password_protected": {
        "topics": ["grub", "boot loader", "bootloader"],
    },
    "boot.secure_boot_state": {"topics": ["secure boot"]},
    "fw.ufw_installed": {"topics": ["ufw"]},
    "fw.ufw_active": {"topics": ["ufw", "firewall"]},
    "fw.ufw_rules_non_empty": {
        "topics": ["ufw", "firewall", "packet filter", "iptables", "nftables"],
    },
    "fw.fail2ban_installed": {"topics": ["fail2ban"]},
    "fw.fail2ban_active": {"topics": ["fail2ban"]},
    "fw.fail2ban_jail_local_exists": {"topics": ["fail2ban", "jail"]},
    "tools.lynis_installed": {"topics": ["lynis"]},
    "tools.rkhunter_installed": {"topics": ["rkhunter", "rootkit"]},
    "tools.clamav_installed": {"topics": ["clamav", "malware"]},
    "tools.apt_listchanges_installed": {"topics": ["apt-listchanges"]},
    "tools.needrestart_installed": {"topics": ["needrestart"]},
    "tools.libpam_tmpdir_installed": {"topics": ["libpam-tmpdir", "pam_tmpdir"]},
    "tools.debsums_present": {"topics": ["debsums"]},
    "auth.apparmor_active": {"topics": ["apparmor"]},
    "auth.umask_027": {"topics": ["umask"]},
    "auth.pam_password_strength": {
        "topics": ["pam_pwquality", "pam_cracklib", "password strength"],
    },
    "auth.no_empty_password_accounts": {
        "topics": ["empty password", "passwordless", "shadow"],
    },
    "auth.unique_uid_gid": {"topics": ["duplicate uid", "duplicate gid", "uid", "gid"]},
    "auth.home_permissions_checked": {
        "topics": ["home directory", "home permissions"],
    },
    "pkg.dpkg_rc_residue_checked": {"topics": ["dpkg", "package residue"]},
    "pkg.critical_file_permissions_checked": {
        "topics": ["sudoers", "shadow", "file permissions"],
    },
    "pkg.apt_upgradable_packages": {"topics": ["apt", "package update"]},
    "sysctl.kernel.kptr_restrict": {"topics": ["kptr_restrict", "kernel pointer"]},
    "sysctl.kernel.sysrq": {"topics": ["sysrq"]},
    "sysctl.kernel.perf_event_paranoid": {"topics": ["perf_event_paranoid"]},
    "sysctl.kernel.unprivileged_bpf_disabled": {
        "topics": ["unprivileged_bpf", "bpf"],
    },
    "sysctl.fs.protected_fifos": {"topics": ["protected_fifos", "fifo"]},
    "sysctl.net.ipv4.conf.all.log_martians": {"topics": ["log_martians", "martian"]},
    "sysctl.net.ipv4.conf.default.log_martians": {
        "topics": ["log_martians", "martian"],
    },
    "sysctl.net.ipv4.conf.default.accept_source_route": {
        "topics": ["accept_source_route", "source route"],
    },
    "sysctl.net.ipv4.conf.all.rp_filter": {
        "topics": ["rp_filter", "reverse path"],
    },
    "sysctl.net.ipv4.conf.default.rp_filter": {
        "topics": ["rp_filter", "reverse path"],
    },
}


SECURITY_BASELINE_CHECKS = [
    {
        "id": "boot.uefi_active",
        "group": "Bootschutz",
        "title": "UEFI aktiv",
        "expected": "ja",
        "source": "Systembefehl",
        "description": "Prueft, ob das System im UEFI-Modus gestartet wurde.",
        "security_benefit": "UEFI ist Grundlage fuer moderne Bootschutzmechanismen.",
        "side_effects": "Keine; reine Lesekontrolle.",
        "exceptions": "Legacy-BIOS-Systeme muessen gesondert eingeordnet werden.",
        "command": "test -d /sys/firmware/efi && echo ja || echo nein",
        "config_source": "/sys/firmware/efi",
        "check_kind": "shell_bool",
    },
    {
        "id": "boot.grub_password_protected",
        "group": "Bootschutz",
        "title": "GRUB-Passwortschutz erkannt",
        "expected": "ja",
        "source": "Datei",
        "description": "Prueft, ob GRUB Hinweise auf Passwort- oder PBKDF2-Schutz enthaelt.",
        "security_benefit": "Erschwert unautorisierte Boot-Parameter-Aenderungen.",
        "side_effects": "GRUB-Aenderungen muessen manuell gewartet werden.",
        "exceptions": "Abweichungen koennen in Test- oder Recovery-Umgebungen bewusst sein.",
        "command": "grep -E 'password|pbkdf2' /boot/grub/grub.cfg >/dev/null 2>&1 && echo ja || echo nein",
        "config_source": "/boot/grub/grub.cfg",
        "check_kind": "shell_bool",
    },
    {
        "id": "boot.secure_boot_state",
        "group": "Bootschutz",
        "title": "Secure Boot",
        "expected": "aktiviert",
        "source": "Systembefehl",
        "description": "Liest den Secure-Boot- und Plattformmodus aus der UEFI-Firmware und bewertet den Zustand abhaengig vom gewaehlten Systemprofil.",
        "security_benefit": "Secure Boot kann verhindern, dass nicht vertrauenswuerdige oder nicht signierte Boot-Komponenten waehrend des Systemstarts geladen werden.",
        "side_effects": "Secure Boot kann eigene Kernelmodule, aeltere Treiber, bestimmte Dual-Boot-Konfigurationen und Entwicklungs- oder Testworkflows einschraenken.",
        "exceptions": "Desktop-, Entwicklungs-, Testlabor- und Dual-Boot-Systeme koennen Secure Boot bewusst deaktiviert haben. In diesen Profilen soll der Zustand dokumentiert, aber nicht automatisch als kritischer Fehler bewertet werden.",
        "command": "LANG=C LC_ALL=C mokutil --sb-state",
        "config_source": "UEFI/Firmware",
        "check_kind": "secure_boot",
        "manual_when_disabled": True,
    },
    {
        "id": "fw.ufw_installed",
        "group": "Firewall",
        "title": "UFW installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob das UFW-Paket installiert ist.",
        "security_benefit": "UFW stellt die Standard-Firewall fuer das Desktop-/Development-Profil bereit.",
        "side_effects": "Keine; reine Paketabfrage.",
        "exceptions": "Alternative Firewall-Loesungen muessen manuell bewertet werden.",
        "command": "dpkg-query -W -f='${Status}' ufw 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "fw.ufw_active",
        "group": "Firewall",
        "title": "UFW aktiv",
        "expected": "ja",
        "source": "Dienststatus",
        "description": "Prueft, ob UFW als Host-Firewall aktiv ist.",
        "security_benefit": "Grundlegender Hostschutz fuer eingehende und ausgehende Regeln.",
        "side_effects": "Regeln muessen zum Netzprofil passen.",
        "exceptions": "Alternative Firewall-Loesungen muessen manuell bewertet werden.",
        "command": "LANG=C LC_ALL=C ufw status",
        "config_source": "UFW Laufzeitstatus",
        "check_kind": "ufw_active",
    },
    {
        "id": "fw.ufw_rules_non_empty",
        "group": "Firewall",
        "title": "Benutzerdefinierte UFW-Regeln vorhanden",
        "expected": "ja",
        "source": "Systembefehl",
        "description": "Prueft, ob UFW aktiv ist und mindestens eine konkrete benutzerdefinierte Regel im aktuellen Laufzeitstatus enthaelt.",
        "security_benefit": "Ein aktiver Regelsatz mit konkreten Regeln zeigt, dass die Firewall ueber reine Standardrichtlinien hinaus bewusst konfiguriert wurde.",
        "side_effects": "VPN-, Multi-Interface- und Server-Systeme koennen umfangreiche oder bewusst spezielle Regeln benoetigen. Die Pruefung bewertet nur das Vorhandensein, nicht die fachliche Qualitaet der Regeln.",
        "exceptions": "Alternative Firewall-Loesungen wie nftables, iptables oder firewalld sowie bewusst minimalistische UFW-Konfigurationen muessen separat bewertet werden.",
        "command": "LANG=C LC_ALL=C ufw status numbered",
        "config_source": "UFW Laufzeitstatus",
        "check_kind": "ufw_rules_non_empty",
    },
    {
        "id": "fw.fail2ban_installed",
        "group": "Firewall",
        "title": "Fail2ban installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob das Fail2ban-Paket installiert ist.",
        "security_benefit": "Fail2ban kann wiederholte Fehlversuche und offensichtliche Missbrauchsmuster begrenzen.",
        "side_effects": "Jails muessen zum realen Dienstprofil passen.",
        "exceptions": "Auf einzelnen Desktop-Systemen kann Fail2ban bewusst fehlen.",
        "command": "dpkg-query -W -f='${Status}' fail2ban 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "fw.fail2ban_active",
        "group": "Firewall",
        "title": "Fail2ban aktiv",
        "expected": "ja",
        "source": "Dienststatus",
        "description": "Prueft, ob der Fail2ban-Dienst aktiv ist.",
        "security_benefit": "Erkennt und blockiert wiederholte Fehlversuche.",
        "side_effects": "Falsch positive Sperren sind bei aggressiven Jails moeglich.",
        "exceptions": "Einige Desktop-Systeme setzen Fail2ban nur selektiv ein.",
        "command": "systemctl is-active fail2ban",
        "config_source": "systemd / fail2ban",
        "check_kind": "systemctl_active",
    },
    {
        "id": "fw.fail2ban_jail_local_exists",
        "group": "Firewall",
        "title": "/etc/fail2ban/jail.local vorhanden",
        "expected": "ja",
        "source": "Datei",
        "description": "Prueft, ob eine lokale Fail2ban-Konfigurationsdatei vorhanden ist.",
        "security_benefit": "Dokumentiert bewusste lokale Jail-Anpassungen ausserhalb der Paketdefaults.",
        "side_effects": "Keine; reine Existenzpruefung.",
        "exceptions": "Einzelne Installationen nutzen bewusst nur jail.d/-Snippets.",
        "command": "test -f /etc/fail2ban/jail.local && echo ja || echo nein",
        "config_source": "/etc/fail2ban/jail.local",
        "check_kind": "shell_bool",
    },
    {
        "id": "tools.lynis_installed",
        "group": "Tools",
        "title": "Lynis installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob Lynis lokal verfuegbar ist.",
        "security_benefit": "Lynis liefert Audit- und Hardening-Hinweise als Referenzsignal.",
        "side_effects": "Keine; reine Paketabfrage.",
        "exceptions": "In Minimalumgebungen kann das Tool bewusst fehlen.",
        "command": "dpkg-query -W -f='${Status}' lynis 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.rkhunter_installed",
        "group": "Tools",
        "title": "rkhunter installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob rkhunter lokal verfuegbar ist.",
        "security_benefit": "rkhunter deckt Rootkit- und Integritaetsfragen ab.",
        "side_effects": "Kann in gepflegten Dev-Systemen Warnungen erzeugen, die manuell eingeordnet werden muessen.",
        "exceptions": "Einzelne Systeme nutzen stattdessen andere Integritaetswerkzeuge.",
        "command": "dpkg-query -W -f='${Status}' rkhunter 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.clamav_installed",
        "group": "Tools",
        "title": "ClamAV installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob ClamAV lokal verfuegbar ist.",
        "security_benefit": "ClamAV kann zusaetzliche Malware-Signaturpruefungen liefern.",
        "side_effects": "Signaturpflege und Scanzeiten muessen beruecksichtigt werden.",
        "exceptions": "In einzelnen Dev-Systemen kann ClamAV bewusst fehlen.",
        "command": "dpkg-query -W -f='${Status}' clamav 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.apt_listchanges_installed",
        "group": "Tools",
        "title": "apt-listchanges installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob apt-listchanges installiert ist.",
        "security_benefit": "Hilft, sicherheitsrelevante Paket-Aenderungen bewusster wahrzunehmen.",
        "side_effects": "Keine; reine Paketabfrage.",
        "exceptions": "Kann in automatisierten Umgebungen bewusst weggelassen sein.",
        "command": "dpkg-query -W -f='${Status}' apt-listchanges 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.needrestart_installed",
        "group": "Tools",
        "title": "needrestart installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob needrestart installiert ist.",
        "security_benefit": "Hilft, notwendige Neustarts nach sicherheitsrelevanten Updates sichtbar zu machen.",
        "side_effects": "Keine; reine Paketabfrage.",
        "exceptions": "In einzelnen Umgebungen koennen andere Workflows genutzt werden.",
        "command": "dpkg-query -W -f='${Status}' needrestart 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.libpam_tmpdir_installed",
        "group": "Tools",
        "title": "libpam-tmpdir installiert",
        "expected": "ja",
        "source": "Paketstatus",
        "description": "Prueft, ob libpam-tmpdir installiert ist.",
        "security_benefit": "Hilft, pro Nutzer getrennte TMP-Verzeichnisse bereitzustellen.",
        "side_effects": "Einzelne alte Workflows koennen TMP-Pfade anders erwarten.",
        "exceptions": "Minimal- oder Spezialumgebungen koennen bewusst anders arbeiten.",
        "command": "dpkg-query -W -f='${Status}' libpam-tmpdir 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_installed",
    },
    {
        "id": "tools.debsums_present",
        "group": "Tools",
        "title": "debsums vorhanden",
        "expected": "optional",
        "source": "Paketstatus",
        "description": "Prueft, ob debsums installiert ist.",
        "security_benefit": "Kann Paketintegritaet fuer installierte Dateien zusaetzlich sichtbar machen.",
        "side_effects": "Nicht jede Installation fuehrt das Paket standardmaessig mit.",
        "exceptions": "Im Profil als optional dokumentiert.",
        "command": "dpkg-query -W -f='${Status}' debsums 2>/dev/null",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "package_optional",
    },
    {
        "id": "auth.apparmor_active",
        "group": "Authentifizierung",
        "title": "AppArmor aktiv",
        "expected": "ja",
        "source": "Systembefehl",
        "description": "Prueft, ob AppArmor auf dem System aktiv ist.",
        "security_benefit": "Zusaetzliche Einschraenkung von Anwendungen ueber Mandatory Access Control.",
        "side_effects": "Einzelne Profile koennen Nacharbeit benoetigen.",
        "exceptions": "Alternativ koennen andere MAC-Systeme vorhanden sein.",
        "command": "aa-status --enabled",
        "config_source": "AppArmor Laufzeitstatus",
        "check_kind": "apparmor_active",
    },
    {
        "id": "auth.umask_027",
        "group": "Authentifizierung",
        "title": "UMASK 027 gesetzt",
        "expected": "027",
        "source": "Datei",
        "description": "Prueft, ob in den ueblichen Systemkonfigurationen eine Standard-UMASK von 027 definiert ist.",
        "security_benefit": "Eine UMASK von 027 verhindert, dass neu angelegte Dateien und Verzeichnisse standardmaessig fuer andere Benutzer lesbar oder beschreibbar sind.",
        "side_effects": "Programme oder gemeinsame Arbeitsverzeichnisse koennen zusaetzliche Freigaben erfordern, wenn andere Benutzer Zugriff auf neu erstellte Dateien benoetigen.",
        "exceptions": "Die effektive UMASK kann zusaetzlich durch PAM, Shell-Profile, Benutzerkonfigurationen oder einzelne Dienste festgelegt werden. Mehrere Konfigurationsquellen muessen daher gemeinsam bewertet werden.",
        "command": "grep -RHE '^[[:space:]]*(UMASK|umask)[[:space:]]+[0-7]{3,4}([[:space:]]|$)' /etc/login.defs /etc/profile /etc/profile.d 2>/dev/null",
        "config_source": "/etc/login.defs /etc/profile /etc/profile.d/",
        "check_kind": "umask_value",
    },
    {
        "id": "auth.pam_password_strength",
        "group": "Authentifizierung",
        "title": "PAM-Passwortstaerke aktiv",
        "expected": "ja",
        "source": "Datei",
        "description": "Prueft, ob PAM Passwortqualitaet ueber pam_pwquality oder pam_cracklib konfiguriert ist.",
        "security_benefit": "Hilft, triviale oder zu schwache Passwoerter zu vermeiden.",
        "side_effects": "Strenge Regeln koennen Bedienaufwand erhoehen.",
        "exceptions": "Alternativ koennen zentrale Directory-Policies gelten.",
        "command": "grep -R 'pam_pwquality\\|pam_cracklib' /etc/pam.d 2>/dev/null",
        "config_source": "/etc/pam.d/",
        "check_kind": "grep_exists",
    },
    {
        "id": "auth.no_empty_password_accounts",
        "group": "Authentifizierung",
        "title": "Keine Konten ohne Passwort",
        "expected": "0",
        "source": "Datei",
        "description": "Prueft, ob in /etc/shadow Konten ohne Passwortfeld vorhanden sind.",
        "security_benefit": "Verhindert triviale lokale Anmeldemoeglichkeiten ohne Passwort.",
        "side_effects": "Servicekonten muessen korrekt gesperrt oder dokumentiert sein.",
        "exceptions": "Spezielle Appliance- oder Recovery-Konten muessen manuell eingeordnet werden.",
        "command": "awk -F: '($2==\"\"){count++} END {print count+0}' /etc/shadow 2>/dev/null",
        "config_source": "/etc/shadow",
        "check_kind": "numeric_zero",
    },
    {
        "id": "auth.unique_uid_gid",
        "group": "Authentifizierung",
        "title": "Eindeutige Benutzer- und Gruppen-IDs geprueft",
        "expected": "0",
        "source": "Datei",
        "description": "Prueft auf doppelte UID- oder GID-Werte in passwd und group.",
        "security_benefit": "Reduziert unklare Zuordnungen und Rechtekonflikte zwischen Konten.",
        "side_effects": "Systeme mit bewusst geteilten IDs muessen manuell bewertet werden.",
        "exceptions": "Spezielle Legacy- oder Migrationsfaelle.",
        "command": "python3 - <<'PY'\nimport collections\nuid=collections.Counter()\ngid=collections.Counter()\nwith open('/etc/passwd', encoding='utf-8', errors='replace') as handle:\n    for line in handle:\n        parts=line.rstrip('\\n').split(':')\n        if len(parts) > 3:\n            uid[parts[2]] += 1\nwith open('/etc/group', encoding='utf-8', errors='replace') as handle:\n    for line in handle:\n        parts=line.rstrip('\\n').split(':')\n        if len(parts) > 2:\n            gid[parts[2]] += 1\nprint(sum(1 for value in uid.values() if value > 1) + sum(1 for value in gid.values() if value > 1))\nPY",
        "config_source": "/etc/passwd /etc/group",
        "check_kind": "numeric_zero",
    },
    {
        "id": "auth.home_permissions_checked",
        "group": "Authentifizierung",
        "title": "Home-Verzeichnisrechte sicher konfiguriert",
        "expected": "keine Schreibrechte fuer Gruppe oder andere Benutzer",
        "source": "Datei",
        "description": "Prueft die Unix-Dateirechte und optional vorhandene ACLs der Home-Verzeichnisse unter /home.",
        "security_benefit": "Restriktive Home-Verzeichnisrechte verhindern, dass andere lokale Benutzer persoenliche Dateien lesen, veraendern oder unerwuenschte Dateien im Verzeichnis ablegen.",
        "side_effects": "Gemeinsame Arbeitsverzeichnisse, Schulungsrechner und Laborumgebungen koennen bewusst weiter gefasste Rechte benoetigen.",
        "exceptions": "Shared-Workstation-, Team-, Labor- oder Netzwerk-Home-Konfigurationen muessen separat bewertet werden.",
        "command": "python3 - <<'PY'\nimport grp\nimport os\nimport pwd\nimport shutil\nimport stat\nimport subprocess\n\nhome = '/home'\ngetfacl = shutil.which('getfacl')\ntry:\n    entries = sorted(os.scandir(home), key=lambda item: item.path)\nexcept OSError as exc:\n    print(f'ERROR {home} {exc}')\n    raise SystemExit(2)\n\nfor entry in entries:\n    path = entry.path\n    try:\n        st = entry.stat(follow_symlinks=False)\n    except OSError as exc:\n        print(f'ERROR {path} {exc}')\n        continue\n    try:\n        owner = pwd.getpwuid(st.st_uid).pw_name\n    except KeyError:\n        owner = str(st.st_uid)\n    try:\n        group = grp.getgrgid(st.st_gid).gr_name\n    except KeyError:\n        group = str(st.st_gid)\n    mode = format(stat.S_IMODE(st.st_mode), '04o')[-3:]\n    kind = 'dir' if stat.S_ISDIR(st.st_mode) else 'symlink' if stat.S_ISLNK(st.st_mode) else 'other'\n    acl = 'unknown'\n    if getfacl and kind == 'dir':\n        try:\n            proc = subprocess.run([getfacl, '-cp', path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=5, check=False)\n            if proc.returncode == 0:\n                extra = False\n                for raw in (proc.stdout or '').splitlines():\n                    line = raw.strip()\n                    if line.startswith('user:') and not line.startswith('user::'):\n                        extra = True\n                    if line.startswith('group:') and not line.startswith('group::'):\n                        extra = True\n                acl = 'extra' if extra else 'none'\n            else:\n                acl = 'error'\n        except Exception:\n            acl = 'error'\n    print(f'{mode} {owner} {group} {path} acl={acl} type={kind}')\nPY",
        "config_source": "/home/*",
        "check_kind": "home_permissions",
    },
    {
        "id": "pkg.dpkg_rc_residue_checked",
        "group": "Pakete",
        "title": "Alte dpkg-Konfigurationsreste geprueft",
        "expected": "0",
        "source": "Paketstatus",
        "description": "Prueft auf rc-Eintraege in der dpkg-Datenbank und markiert vorhandene Reste als manuelle Nachpruefung.",
        "security_benefit": "Hilft, Altlasten und unerwartete Restkonfigurationen sichtbar zu machen.",
        "side_effects": "Nicht jeder rc-Eintrag ist sicherheitsrelevant.",
        "exceptions": "Historische Paketwechsel oder bewusst aufbewahrte Konfigurationen.",
        "command": "dpkg -l 2>/dev/null | awk '/^rc/ {count++} END {print count+0}'",
        "config_source": "dpkg / Paketdatenbank",
        "check_kind": "manual_zero",
    },
    {
        "id": "pkg.critical_file_permissions_checked",
        "group": "Pakete",
        "title": "Kritische Systemdateirechte geprueft",
        "expected": "distributionsuebliche sichere Standardrechte",
        "source": "Datei",
        "description": "Prueft Eigentuemer, Gruppe und Dateirechte kritischer Systemdateien auf bekannte sichere Standardkonfigurationen.",
        "security_benefit": "Fehlerhafte Berechtigungen auf zentralen Systemdateien koennen zu Rechteausweitungen, Offenlegung sensibler Informationen oder Manipulation sicherheitsrelevanter Konfigurationen fuehren.",
        "side_effects": "Keine. Die Pruefung liest ausschliesslich Metadaten der Dateien aus.",
        "exceptions": "Einzelne Linux-Distributionen oder sicherheitsgehaertete Systeme koennen bewusst abweichende, aber ebenfalls sichere Berechtigungen verwenden. Diese sollen als Pruefbedarf und nicht automatisch als Fehler bewertet werden.",
        "command": "stat -c '%a %U %G %n' /etc/passwd /etc/shadow /etc/sudoers 2>/dev/null",
        "config_source": "/etc/passwd /etc/shadow /etc/sudoers",
        "check_kind": "critical_file_permissions",
    },
    {
        "id": "pkg.apt_upgradable_packages",
        "group": "Pakete",
        "title": "Ausstehende APT-Paketupdates",
        "expected": "0",
        "source": "Paketstatus",
        "description": "Prueft, wie viele installierte Pakete ueber den APT-Paketmanager aktualisiert werden koennen.",
        "security_benefit": "Ausstehende Paketupdates koennen Fehlerkorrekturen und Sicherheitsaktualisierungen enthalten. Die Pruefung macht moeglichen Wartungsbedarf sichtbar.",
        "side_effects": "Updates koennen Abhaengigkeiten, Treiber, Dienste oder Anwendungsfunktionen veraendern. Groessere Aktualisierungen sollten bei Bedarf vorher gesichert oder getestet werden.",
        "exceptions": "Bewusst zurueckgehaltene Pakete, Paket-Pinning, Test-Repositories oder absichtlich verschobene Aktualisierungen muessen manuell eingeordnet werden.",
        "command": "LANG=C LC_ALL=C apt list --upgradable 2>/dev/null",
        "config_source": "APT Paketstatus",
        "check_kind": "apt_upgradable",
        "detail_note_text": "Diese Pruefung erkennt verfuegbare Updates, aber nicht zuverlaessig, ob diese sicherheitsrelevant sind. NetMon nimmt keine automatische Aktualisierung vor.",
    },
    {
        "id": "pkg.apt_repository_signed_by_scoped",
        "group": "Paketverwaltung und Repository-Sicherheit",
        "title": "APT-Repository ohne eingeschraenkten Signaturschluessel",
        "expected": "keine doppelten aktiven Fremdquellen ohne Signed-By",
        "source": "APT-Quellen",
        "description": "Prueft aktive APT-Quelldateien, doppelte Fremdquellen, fehlende Signed-By-Angaben, alte distUpgrade-Reste, deaktivierte oder gesicherte Repo-Dateien und globale Drittanbieter-Keyrings.",
        "security_benefit": "Eine repository-spezifische Schluesselzuordnung begrenzt, fuer welche Paketquelle ein Signaturschluessel verwendet werden darf.",
        "side_effects": "Keine. Die Pruefung liest ausschliesslich Quellen, Keyring-Verweise und erkannte Zusatzdateien.",
        "exceptions": "Historische Upgrade-Reste, bewusst deaktivierte Quellen oder noch nicht migrierte Fremdquellen muessen manuell eingeordnet werden.",
        "command": "RepositoryGuardService scan (read-only)",
        "config_source": "/etc/apt/sources.list /etc/apt/sources.list.d/ /etc/apt/trusted.gpg.d/",
        "check_kind": "apt_repository_guard",
        "detail_note_text": "Automatische Korrektur: Nein. Aenderungen an Paketquellen muessen bestaetigt und durch Sicherungen abgesichert werden.",
    },
    {
        "id": "sysctl.kernel.kptr_restrict",
        "group": "Kernel",
        "title": "kernel.kptr_restrict",
        "expected": "2",
        "source": "sysctl",
        "description": "Schraenkt die Offenlegung von Kernel-Zeigern ein.",
        "security_benefit": "Erschwert Informationsgewinn fuer lokale Angriffe.",
        "side_effects": "Kann Low-Level-Debugging einschraenken.",
        "exceptions": "Temporare Debug-Sessions mit dokumentierter Begruendung.",
        "command": "sysctl -n kernel.kptr_restrict",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.kernel.sysrq",
        "group": "Kernel",
        "title": "kernel.sysrq",
        "expected": "0",
        "source": "sysctl",
        "description": "Deaktiviert Magic-SysRq-Sonderfunktionen im Normalbetrieb.",
        "security_benefit": "Reduziert Missbrauch lokaler Notfallfunktionen.",
        "side_effects": "Administratorische Notfallfunktionen sind nicht sofort verfuegbar.",
        "exceptions": "Physisch kontrollierte Laborsysteme.",
        "command": "sysctl -n kernel.sysrq",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.kernel.perf_event_paranoid",
        "group": "Kernel",
        "title": "kernel.perf_event_paranoid",
        "expected": "3",
        "source": "sysctl",
        "description": "Begrenzt unprivilegierten Zugriff auf Performance-Metriken.",
        "security_benefit": "Reduziert moegliche Seitenkanal- und Observability-Angriffsoberflaechen.",
        "side_effects": "Einzelne Profiling-Workflows benoetigen mehr Rechte.",
        "exceptions": "Dedizierte Performance- oder Profiler-Labors.",
        "command": "sysctl -n kernel.perf_event_paranoid",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.kernel.unprivileged_bpf_disabled",
        "group": "Kernel",
        "title": "kernel.unprivileged_bpf_disabled",
        "expected": "1",
        "source": "sysctl",
        "description": "Deaktiviert unprivilegierte BPF-Nutzung.",
        "security_benefit": "Verringert die Angriffsoberflaeche in einem sensiblen Kernel-Bereich.",
        "side_effects": "Einzelne eBPF- oder Observability-Workflows benoetigen Root.",
        "exceptions": "Dedizierte eBPF-Entwicklungsumgebungen.",
        "command": "sysctl -n kernel.unprivileged_bpf_disabled",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.fs.protected_fifos",
        "group": "Kernel",
        "title": "fs.protected_fifos",
        "expected": "2",
        "source": "sysctl",
        "description": "Haertet den Umgang mit FIFOs in gemeinsam beschreibbaren Bereichen.",
        "security_benefit": "Reduziert Link- und Race-nahe Angriffsvektoren.",
        "side_effects": "Seltene Legacy-Anwendungen koennen betroffen sein.",
        "exceptions": "Dokumentierte Altsoftware mit Kompatibilitaetsbedarf.",
        "command": "sysctl -n fs.protected_fifos",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.net.ipv4.conf.all.log_martians",
        "group": "Kernel",
        "title": "net.ipv4.conf.all.log_martians",
        "expected": "1",
        "source": "sysctl",
        "description": "Aktiviert Logging fuer verdaechtige Pakete auf vorhandenen Interfaces.",
        "security_benefit": "Verbessert Sichtbarkeit fuer Netzwerkauffaelligkeiten.",
        "side_effects": "Erhoeht die Logmenge.",
        "exceptions": "Systeme mit bewusst minimierter Protokollierung.",
        "command": "sysctl -n net.ipv4.conf.all.log_martians",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.net.ipv4.conf.default.log_martians",
        "group": "Kernel",
        "title": "net.ipv4.conf.default.log_martians",
        "expected": "1",
        "source": "sysctl",
        "description": "Aktiviert Logging fuer verdaechtige Pakete auf neuen Interfaces.",
        "security_benefit": "Sichert die gleiche Logging-Strategie fuer dynamische Interfaces.",
        "side_effects": "Erhoeht die Logmenge auf Systemen mit vielen Interface-Wechseln.",
        "exceptions": "Abweichende Logging-Strategien muessen bewusst dokumentiert sein.",
        "command": "sysctl -n net.ipv4.conf.default.log_martians",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.net.ipv4.conf.default.accept_source_route",
        "group": "Kernel",
        "title": "net.ipv4.conf.default.accept_source_route",
        "expected": "0",
        "source": "sysctl",
        "description": "Deaktiviert Source-Routed-Pakete fuer neue Interfaces.",
        "security_benefit": "Reduziert veraltete Routing-Angriffsvektoren.",
        "side_effects": "Praktisch selten relevant.",
        "exceptions": "Spezielle Legacy- oder Labor-Netze.",
        "command": "sysctl -n net.ipv4.conf.default.accept_source_route",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "sysctl",
    },
    {
        "id": "sysctl.net.ipv4.conf.all.rp_filter",
        "group": "Kernel",
        "title": "net.ipv4.conf.all.rp_filter",
        "expected": "2",
        "source": "sysctl",
        "description": "Prueft den Reverse-Path-Filter fuer bestehende Interfaces.",
        "security_benefit": "Bietet Spoofing-Schutz bei besserer Kompatibilitaet fuer komplexe Routing-Szenarien.",
        "side_effects": "Weniger strikt als Wert 1, dafuer praxistauglicher fuer VPN und Multi-Interface.",
        "exceptions": "Single-Interface-Systeme koennen bewusst strict mode 1 nutzen.",
        "command": "sysctl -n net.ipv4.conf.all.rp_filter",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "rp_filter",
    },
    {
        "id": "sysctl.net.ipv4.conf.default.rp_filter",
        "group": "Kernel",
        "title": "net.ipv4.conf.default.rp_filter",
        "expected": "2",
        "source": "sysctl",
        "description": "Prueft den Reverse-Path-Filter fuer neue Interfaces.",
        "security_benefit": "Sichert die gleiche Routing-Strategie auch fuer dynamische Interfaces.",
        "side_effects": "Wie bei all.rp_filter: Kompromiss zwischen Schutz und Kompatibilitaet.",
        "exceptions": "Single-Interface-Systeme koennen bewusst strict mode 1 nutzen.",
        "command": "sysctl -n net.ipv4.conf.default.rp_filter",
        "config_source": "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "check_kind": "rp_filter",
    },
]


def _baseline_checks(app):
    profile = _active_baseline_profile(app)
    active_profile_id = str(profile.get("id") or SECURITY_BASELINE_DEFAULT_PROFILE_ID)
    checks = _app_value(app, "security_baseline_checks")
    cached_profile_id = str(
        _app_value(app, "security_baseline_checks_profile_id", "") or ""
    )
    if checks and cached_profile_id == active_profile_id:
        return checks
    checks = []
    for item in SECURITY_BASELINE_CHECKS:
        spec = _enrich_baseline_check_spec(dict(item))
        if active_profile_id not in set(spec.get("profile_targets") or []):
            continue
        spec = _apply_profile_check_overrides(spec, profile)
        checks.append(spec)
    checks.extend(_profile_advisory_checks(profile))
    app.security_baseline_checks = checks
    app.security_baseline_checks_profile_id = active_profile_id
    return checks


def _baseline_profile_catalog() -> dict[str, dict]:
    return {key: dict(value) for key, value in SECURITY_BASELINE_PROFILES.items()}


def _baseline_system_context(app=None) -> dict[str, object]:
    os_release = {}
    if app is not None:
        reader = getattr(app, "_read_os_release", None)
        if callable(reader):
            try:
                os_release = dict(reader() or {})
            except Exception:
                os_release = {}
    if not os_release:
        try:
            os_release = dict(platform.freedesktop_os_release() or {})
        except Exception:
            os_release = {}
    distro_id = str(os_release.get("ID") or "").strip().lower()
    like_tokens = {
        token.strip().lower()
        for token in str(os_release.get("ID_LIKE") or "").split()
        if token.strip()
    }
    name_tokens = {
        token.strip().lower()
        for token in re.split(
            r"[^a-z0-9]+",
            " ".join(
                [
                    str(os_release.get("NAME") or ""),
                    str(os_release.get("PRETTY_NAME") or ""),
                ]
            ).lower(),
        )
        if token.strip()
    }
    tokens = {token for token in {distro_id, *like_tokens, *name_tokens} if token}
    family = "cross_platform"
    if tokens & {
        "ubuntu",
        "debian",
        "linuxmint",
        "mint",
        "zorin",
        "pop",
        "elementary",
        "neon",
        "kali",
        "parrot",
    }:
        family = "debian_like"
    elif tokens & {"fedora", "rhel", "centos", "rocky", "almalinux", "nobara"}:
        family = "rpm_like"
    return {
        "os_release": os_release,
        "id": distro_id,
        "tokens": tokens,
        "family": family,
    }


def _profile_matches_system(profile: dict, system_context: dict[str, object]) -> bool:
    profile_family = str(profile.get("os_family") or "cross_platform").strip().lower()
    system_family = (
        str(system_context.get("family") or "cross_platform").strip().lower()
    )
    if profile_family not in {"", "cross_platform"} and system_family not in {
        "",
        "cross_platform",
        profile_family,
    }:
        return False

    distribution = str(profile.get("distribution") or "").strip().lower()
    base_distribution = str(profile.get("base_distribution") or "").strip().lower()
    tokens = set(system_context.get("tokens") or set())
    distro_id = str(system_context.get("id") or "").strip().lower()

    if distribution == "desktop linux":
        return system_family == "debian_like"
    if distribution == "zorin os":
        return "zorin" in tokens or distro_id == "zorin"
    if distribution == "linux mint":
        return distro_id in {"linuxmint", "mint"} or "mint" in tokens
    if distribution == "ubuntu":
        return "ubuntu" in tokens or distro_id in {
            "linuxmint",
            "mint",
            "pop",
            "elementary",
            "neon",
            "zorin",
        }
    if distribution == "debian":
        return distro_id == "debian" or (
            "debian" in tokens
            and "ubuntu" not in tokens
            and distro_id not in {"linuxmint", "mint", "zorin"}
        )
    if distribution == "fedora":
        return "fedora" in tokens or distro_id == "fedora"
    if "ubuntu" in base_distribution:
        return system_family == "debian_like" and (
            "ubuntu" in tokens
            or distro_id in {"linuxmint", "mint", "pop", "elementary", "neon", "zorin"}
        )
    if "debian" in base_distribution:
        return system_family == "debian_like"
    return True


def _recommended_baseline_profile_id(app=None) -> str:
    system_context = _baseline_system_context(app)
    compatible = [
        (profile_id, profile)
        for profile_id, profile in _baseline_profile_catalog().items()
        if _profile_matches_system(profile, system_context)
    ]
    if not compatible:
        return SECURITY_BASELINE_DEFAULT_PROFILE_ID

    distro_id = str(system_context.get("id") or "").strip().lower()
    if distro_id == "zorin":
        preferred = "zorin_desktop_development"
    elif distro_id == "ubuntu":
        preferred = "ubuntu_desktop_development"
    elif distro_id in {"linuxmint", "mint"}:
        preferred = "linuxmint_desktop_development"
    elif distro_id == "debian":
        preferred = "debian_desktop_development"
    elif distro_id in {"pop", "elementary", "neon"}:
        preferred = "ubuntu_desktop_development"
    elif distro_id == "fedora":
        preferred = "fedora_workstation_review"
    else:
        preferred = ""
    if preferred and any(
        profile_id == preferred for profile_id, _profile in compatible
    ):
        return preferred
    if any(profile_id == "desktop_safe_v1" for profile_id, _profile in compatible):
        return "desktop_safe_v1"
    return compatible[0][0]


def _baseline_profile_choice_label(profile: dict) -> str:
    item = dict(profile or {})
    distribution = str(item.get("distribution") or "").strip()
    profile_name = str(item.get("profile") or item.get("id") or "").strip() or "-"
    if distribution:
        return f"{distribution} | {profile_name}"
    return profile_name


def baseline_profile_choice_items(app=None) -> list[tuple[str, str]]:
    system_context = _baseline_system_context(app) if app is not None else None
    items = []
    for profile_id, profile in _baseline_profile_catalog().items():
        if system_context is not None and not _profile_matches_system(
            profile, system_context
        ):
            continue
        items.append((profile_id, _baseline_profile_choice_label(profile)))
    return items


def _active_baseline_profile(app=None) -> dict:
    profile_id = ""
    if app is not None:
        profile_id = str(
            _app_value(app, "security_baseline_profile_id", "") or ""
        ).strip()
    if not profile_id:
        profile_id = (
            _recommended_baseline_profile_id(app)
            if app is not None
            else SECURITY_BASELINE_DEFAULT_PROFILE_ID
        )
    profile = SECURITY_BASELINE_PROFILES.get(profile_id)
    if profile is None or (
        app is not None
        and not _profile_matches_system(profile, _baseline_system_context(app))
    ):
        resolved_id = (
            _recommended_baseline_profile_id(app)
            if app is not None
            else SECURITY_BASELINE_DEFAULT_PROFILE_ID
        )
        profile = SECURITY_BASELINE_PROFILES.get(
            resolved_id,
            SECURITY_BASELINE_PROFILES[SECURITY_BASELINE_DEFAULT_PROFILE_ID],
        )
    return dict(profile)


def _profile_section(profile: dict, *keys: str):
    data = dict(profile or {})
    for key in keys:
        value = data.get(key)
        if not isinstance(value, dict):
            return {}
        data = value
    return dict(data)


def _profile_check_overrides(profile: dict) -> dict[str, dict]:
    overrides = _profile_section(profile, "sections", "checks", "overrides")
    normalized = {}
    for check_id, payload in overrides.items():
        if isinstance(payload, dict) and str(check_id or "").strip():
            normalized[str(check_id).strip()] = dict(payload)
    return normalized


def _apply_profile_check_overrides(spec: dict, profile: dict) -> dict:
    updated = dict(spec)
    override = _profile_check_overrides(profile).get(str(spec.get("id") or "").strip())
    if override:
        updated.update(dict(override))
    return updated


def _profile_advisory_slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return cleaned or "entry"


def _profile_advisory_title(check_id: str) -> str:
    normalized = str(check_id or "").strip()
    for item in SECURITY_BASELINE_CHECKS:
        if str(item.get("id") or "").strip() == normalized:
            return str(item.get("title") or normalized)
    return f"Lynis: {normalized}"


def _profile_advisory_checks(profile: dict) -> list[dict]:
    profile_id = str(profile.get("id") or SECURITY_BASELINE_DEFAULT_PROFILE_ID).strip()
    services = _profile_section(profile, "sections", "services")
    checks_section = _profile_section(profile, "sections", "checks")
    advisory_checks = []

    for item in list(services.get("auto_optional") or []):
        if not isinstance(item, dict):
            continue
        service_name = str(item.get("name") or "").strip()
        if not service_name:
            continue
        advisory_checks.append(
            _enrich_baseline_check_spec(
                {
                    "id": f"profile.advisory.optional_service.{profile_id}.{_profile_advisory_slug(service_name)}",
                    "group": "Profilhinweise",
                    "title": f"Optionaler Dienst: {service_name}",
                    "expected": "optional",
                    "source": "Baseline-Profil",
                    "description": "Dieser Dienst ist im aktiven Profil als optionaler Hardening-Schritt hinterlegt und wird nicht automatisch als allgemeiner Sollzustand fuer alle Systeme bewertet.",
                    "security_benefit": "Macht profilabhaengige Zusatzhaertung sichtbar, bevor sie angewendet wird.",
                    "side_effects": "Das Deaktivieren kann Diagnose-, Komfort- oder Desktop-Funktionen beeinflussen.",
                    "exceptions": "Nur anwenden, wenn Rolle und Arbeitsweise des Systems dazu passen.",
                    "command": "Profilhinweis",
                    "config_source": "Aktives Baseline-Profil",
                    "check_kind": "profile_advisory",
                    "advisory_status": "Empfehlung",
                    "advisory_actual": "Optionaler Profilschritt",
                    "advisory_reason": f"{_service_action_label(item)} ist im aktiven Profil als optionaler Zusatzschritt hinterlegt.",
                    "detail_note_text": "Kein Live-Check. Dieser Eintrag dient als profilbezogener Hinweis fuer die geplante Haertung.",
                    "profile_targets": [profile_id],
                    "platform_family": str(
                        profile.get("os_family") or "cross_platform"
                    ),
                }
            )
        )

    for item in list(services.get("manual_review") or []):
        if not isinstance(item, dict):
            continue
        service_name = str(item.get("name") or "").strip()
        if not service_name:
            continue
        advisory_checks.append(
            _enrich_baseline_check_spec(
                {
                    "id": f"profile.advisory.service_review.{profile_id}.{_profile_advisory_slug(service_name)}",
                    "group": "Profilhinweise",
                    "title": f"Dienst manuell pruefen: {service_name}",
                    "expected": "manuell bewerten",
                    "source": "Baseline-Profil",
                    "description": "Dieser Dienst ist im aktiven Profil bewusst nicht fuer eine pauschale Automatisierung freigegeben.",
                    "security_benefit": "Verhindert, dass kontextabhaengige Dienste blind deaktiviert werden.",
                    "side_effects": "Die Entscheidung haengt von installierten Paketen, Desktop-Funktionen und Betriebsrolle ab.",
                    "exceptions": "Kann je nach Systemrolle erforderlich oder entbehrlich sein.",
                    "command": "Profilhinweis",
                    "config_source": "Aktives Baseline-Profil",
                    "check_kind": "profile_advisory",
                    "advisory_status": "Manuelle Pruefung erforderlich",
                    "advisory_actual": "Manuelle Profilentscheidung",
                    "advisory_reason": str(
                        item.get("reason")
                        or "Dieser Dienst muss im Profilkontext manuell bewertet werden."
                    ),
                    "detail_note_text": "Kein Live-Check. Dieser Eintrag stammt aus dem aktiven Baseline-Profil.",
                    "profile_targets": [profile_id],
                    "platform_family": str(
                        profile.get("os_family") or "cross_platform"
                    ),
                }
            )
        )

    for item in list(checks_section.get("manual_review") or []):
        if not isinstance(item, dict):
            continue
        check_id = str(item.get("id") or "").strip()
        if not check_id:
            continue
        advisory_checks.append(
            _enrich_baseline_check_spec(
                {
                    "id": f"profile.advisory.check_review.{profile_id}.{_profile_advisory_slug(check_id)}",
                    "group": "Profilhinweise",
                    "title": f"Profil-Hinweis: {_profile_advisory_title(check_id)}",
                    "expected": "manuell bewerten",
                    "source": "Baseline-Profil",
                    "description": "Dieser Punkt ist im aktiven Profil bewusst als Review-Thema markiert und nicht als harter globaler Sollwert hinterlegt.",
                    "security_benefit": "Macht profilbezogene Abwaegungen fuer Safe-, Server- oder VPN-Rollen transparent.",
                    "side_effects": "Keine direkte Automatisierung; die Bewertung bleibt beim Benutzer.",
                    "exceptions": "Je nach Einsatzrolle kann die Entscheidung bewusst anders ausfallen.",
                    "command": "Profilhinweis",
                    "config_source": "Aktives Baseline-Profil",
                    "check_kind": "profile_advisory",
                    "advisory_status": "Empfehlung",
                    "advisory_actual": "Profil-Review",
                    "advisory_reason": str(
                        item.get("reason")
                        or "Dieser Punkt ist im aktiven Profil als manueller Review markiert."
                    ),
                    "detail_note_text": "Kein Live-Check. Dieser Eintrag dient als Profilkontext fuer die Baseline-Bewertung.",
                    "profile_targets": [profile_id],
                    "platform_family": str(
                        profile.get("os_family") or "cross_platform"
                    ),
                }
            )
        )

    return advisory_checks


def _baseline_check_platform_family(spec: dict) -> str:
    check_id = str(spec.get("id") or "")
    if check_id.startswith(("fw.", "tools.", "pkg.")):
        return "debian_like"
    return "cross_platform"


def _baseline_check_profile_targets(spec: dict) -> list[str]:
    check_id = str(spec.get("id") or "")
    if check_id == "boot.secure_boot_state":
        return [
            "zorin_desktop_development",
            "ubuntu_desktop_development",
            "linuxmint_desktop_development",
            "debian_desktop_development",
            "desktop_safe_v1",
            "ubuntu_server_hardening",
            "zorin_vpn_multi_interface",
            "ubuntu_vpn_multi_interface",
            "linuxmint_vpn_multi_interface",
            "fedora_workstation_review",
        ]
    if check_id.startswith(("fw.", "tools.", "pkg.", "sysctl.", "auth.")):
        return [
            "zorin_desktop_development",
            "ubuntu_desktop_development",
            "linuxmint_desktop_development",
            "debian_desktop_development",
            "desktop_safe_v1",
            "ubuntu_server_hardening",
            "zorin_vpn_multi_interface",
            "ubuntu_vpn_multi_interface",
            "linuxmint_vpn_multi_interface",
        ]
    return list(SECURITY_BASELINE_PROFILES.keys())


def _baseline_check_hardening_plan(spec: dict) -> dict[str, str]:
    check_id = str(spec.get("id") or "")
    kind = str(spec.get("check_kind") or "")
    if check_id == "fw.ufw_active":
        return {
            "apply_supported": "Ja, mit Freigabe",
            "apply_strategy": "guided",
            "remediation_summary": "UFW aktivieren und den resultierenden Laufzeitstatus gegen das Netzprofil pruefen.",
            "rollback_hint": "Vor Aktivierung bestehende Firewall-Policies und UFW-Status dokumentieren.",
        }
    if check_id == "fw.ufw_rules_non_empty":
        return {
            "apply_supported": "Teilweise",
            "apply_strategy": "manual_profile_required",
            "remediation_summary": "Benutzerdefinierte UFW-Regeln nur aus einem freigegebenen Netzprofil oder Slot-Modell ableiten.",
            "rollback_hint": "Regeln vor Aenderungen exportieren und Interface-/VPN-Abhaengigkeiten dokumentieren.",
        }
    if kind in {"sysctl", "rp_filter"}:
        return {
            "apply_supported": "Ja, mit Freigabe",
            "apply_strategy": "planned",
            "remediation_summary": "Sysctl-Werte ueber eine dedizierte Datei unter /etc/sysctl.d/ setzen und danach neu laden.",
            "rollback_hint": "Vorherige Werte und betroffene sysctl-Dateien sichern; Ruecknahme ueber Backup oder Drop-in-Entfernung.",
        }
    if check_id in {"auth.no_empty_password_accounts", "auth.pam_password_strength"}:
        return {
            "apply_supported": "Teilweise",
            "apply_strategy": "manual_sensitive",
            "remediation_summary": "Authentifizierungs- und Passwortregeln nur mit expliziter Freigabe und distributionsspezifischer PAM-Pruefung aendern.",
            "rollback_hint": "Vor Aenderungen /etc/pam.d/, /etc/shadow und relevante Login-Konfigurationen sichern.",
        }
    if check_id == "pkg.critical_file_permissions_checked":
        return {
            "apply_supported": "Ja, mit Freigabe",
            "apply_strategy": "guided",
            "remediation_summary": "Abweichende Dateirechte und Eigentuemer nur nach distributionsbezogener Validierung korrigieren.",
            "rollback_hint": "Vorherige Modus-, UID- und GID-Werte dokumentieren, um chmod/chown rueckgängig machen zu koennen.",
        }
    if kind in {"package_installed", "package_optional"}:
        return {
            "apply_supported": "Ja, distributionsabhaengig",
            "apply_strategy": "package_manager",
            "remediation_summary": "Fehlende Pakete nur ueber den nativen Paketmanager des Zielsystems installieren.",
            "rollback_hint": "Installierte Pakete und Konfigurationsaenderungen dokumentieren; Entfernung nur nach Abhaengigkeitspruefung.",
        }
    return {
        "apply_supported": "Nur manuell",
        "apply_strategy": "manual_review",
        "remediation_summary": "Dieser Check ist als Bewertungs- oder Review-Schritt gedacht und derzeit nicht fuer automatische Härtung vorgesehen.",
        "rollback_hint": "Vor jeder Aenderung den Ausgangszustand dokumentieren und ein passendes Backup anlegen.",
    }


def _enrich_baseline_check_spec(spec: dict) -> dict:
    spec["profile_targets"] = list(
        spec.get("profile_targets") or _baseline_check_profile_targets(spec)
    )
    spec["platform_family"] = str(
        spec.get("platform_family") or _baseline_check_platform_family(spec)
    )
    spec["requires_root_read"] = bool(
        spec.get("requires_root_read", _spec_requires_root_read(spec))
    )
    spec.update(_baseline_check_hardening_plan(spec))
    return spec


def _sysctl_baseline_specs(app=None) -> list[dict]:
    return [
        dict(item)
        for item in _baseline_checks(app)
        if str(item.get("check_kind") or "") in {"sysctl", "rp_filter"}
    ]


def _sysctl_dropin_path(app=None) -> str:
    configured = ""
    if app is not None:
        configured = str(
            _app_value(app, "security_baseline_sysctl_dropin_path", "") or ""
        ).strip()
    return configured or SECURITY_BASELINE_SYSCTL_DROPIN_PATH


def _sysctl_runtime_key(spec: dict) -> str:
    check_id = str(spec.get("id") or "").strip()
    if check_id.startswith("sysctl."):
        return check_id[len("sysctl.") :]
    command = str(spec.get("command") or "").strip()
    match = re.search(r"sysctl\s+-n\s+([A-Za-z0-9_.]+)", command)
    if match:
        return str(match.group(1) or "").strip()
    return ""


def _active_ufw_baseline_profile(app=None) -> dict | None:
    active_profile = _active_baseline_profile(app)
    active_profile_id = str(active_profile.get("id") or "").strip()
    for profile in SECURITY_BASELINE_UFW_PROFILES.values():
        if active_profile_id in set(profile.get("profile_targets") or []):
            return dict(profile)
    return None


def _active_optional_service_actions(app=None) -> list[dict]:
    profile = _active_baseline_profile(app)
    services = dict((profile.get("sections") or {}).get("services") or {})
    actions = []
    for item in list(services.get("auto_optional") or []):
        if isinstance(item, dict) and str(item.get("name") or "").strip():
            actions.append(dict(item))
    return actions


def _service_action_label(action: dict) -> str:
    name = str((action or {}).get("name") or "").strip()
    command = str((action or {}).get("action") or "").strip().lower()
    if command == "disable":
        return f"{name} deaktivieren"
    return name or "Dienstaktion"


def _optional_services_overview_text(app=None) -> str:
    actions = _active_optional_service_actions(app)
    if not actions:
        return _tr(
            app,
            "baseline_optional_services_overview_none",
            "Optionale Dienste im Profil: keine.",
        )
    services = ", ".join(_service_action_label(action) for action in actions)
    return _tr(
        app,
        "baseline_optional_services_overview_value",
        "Optionale Dienste im Profil: {services}. Werden beim Anwenden separat bestaetigt.",
    ).format(services=services)


def _service_unit_exists(unit_name: str, *, run_cmd_fn=None) -> bool:
    unit = str(unit_name or "").strip()
    if not unit:
        return False
    runner = run_cmd_fn or run_cmd
    rc, out = runner(
        ["systemctl", "list-unit-files", unit, "--no-legend", "--no-pager"],
        timeout=15,
    )
    if rc != 0:
        return False
    first_line = (
        str(out or "").splitlines()[0].strip() if str(out or "").strip() else ""
    )
    return first_line.startswith(unit)


def _apply_optional_service_actions(
    app,
    actions: list[dict],
    *,
    run_cmd_fn=None,
    askyesno_fn=None,
    showerror_fn=None,
) -> tuple[bool, list[str], bool]:
    runner = run_cmd_fn or run_cmd
    askyesno_runner = askyesno_fn or messagebox.askyesno
    showerror_runner = showerror_fn or messagebox.showerror

    available_actions = []
    for action in list(actions or []):
        unit_name = str(action.get("name") or "").strip()
        if not unit_name:
            continue
        enabled_if = str(action.get("enabled_if") or "").strip().lower()
        if enabled_if == "service_exists" and not _service_unit_exists(
            unit_name, run_cmd_fn=runner
        ):
            continue
        available_actions.append(dict(action))

    if not available_actions:
        return True, [], False

    labels = [_service_action_label(action) for action in available_actions]
    prompt = app.tr(
        "baseline_optional_services_confirm",
        "Optionaler Safe-Schritt:\n\nDie folgenden Desktop-Dienste koennen zusaetzlich deaktiviert werden:\n{services}\n\nJetzt ebenfalls anwenden?",
    ).format(services="\n".join(f"- {label}" for label in labels))
    if not askyesno_runner(
        app.tr("baseline_optional_services_title", "Optionale Dienste"),
        prompt,
        parent=app,
    ):
        return True, [], True

    completed = []
    for action in available_actions:
        unit_name = str(action.get("name") or "").strip()
        command = str(action.get("action") or "").strip().lower()
        if command != "disable":
            continue
        rc, out = runner(
            ["sudo", "-n", "systemctl", "disable", "--now", unit_name],
            timeout=30,
        )
        if rc != 0:
            showerror_runner(
                app.tr("baseline_optional_services_title", "Optionale Dienste"),
                app.tr(
                    "baseline_optional_services_failed",
                    "Mindestens ein optionaler Dienst konnte nicht deaktiviert werden.",
                )
                + f"\n\n{unit_name}\n\n{out}",
                parent=app,
            )
            return False, completed, False
        completed.append(unit_name)
        app.log_safe(f"Security Baseline Optionaldienst deaktiviert: {unit_name}")
    return True, completed, False


def _ufw_rule_preview_text(rule: dict) -> str:
    key = _ufw_rule_key(rule)
    if key is None:
        return "ungueltige Regel"
    if key[0] == "iface":
        _tag, direction, iface = key
        return f"allow {direction} on {iface}"
    _tag, ip_val, port = key
    return f"allow out to {ip_val} port {port}/udp"


def _security_baseline_apply_plan(
    app=None, *, transfer_package: dict | None = None
) -> dict:
    if transfer_package is None and app is not None:
        loaded_package = _app_value(app, "security_baseline_transfer_package")
        if isinstance(loaded_package, dict):
            transfer_package = loaded_package
    if isinstance(transfer_package, dict):
        return _transfer_plan_from_package(transfer_package)
    profile = _active_baseline_profile(app)
    target_path = _sysctl_dropin_path(app)
    sysctl_specs = []
    if bool(profile.get("apply_supported")):
        sysctl_specs = _sysctl_baseline_specs(app)
    ufw_profile = _active_ufw_baseline_profile(app)
    optional_services = _active_optional_service_actions(app)

    actions = []
    preview_lines = []
    rollback_lines = []

    if sysctl_specs:
        actions.append("sysctl")
        preview_lines.append(f"Sysctl Drop-in: {target_path}")
        for spec in sysctl_specs:
            preview_lines.append(
                f"  - {spec.get('title', spec.get('id', 'sysctl'))} = {spec.get('expected', '-')}"
            )
        rollback_lines.append(
            "Sysctl: Vorherige Drop-in-Datei sichern oder den NetMon-Drop-in entfernen und sysctl neu laden."
        )

    if ufw_profile is not None:
        actions.append("ufw")
        preview_lines.append(
            "UFW Defaults: "
            f"incoming={ufw_profile.get('default_incoming', '-')}, "
            f"outgoing={ufw_profile.get('default_outgoing', '-')}"
        )
        for rule in ufw_profile.get("rules", []) or []:
            preview_lines.append(f"  - {_ufw_rule_preview_text(rule)}")
        profile_note = str(ufw_profile.get("post_apply_note") or "").strip()
        if profile_note:
            preview_lines.append(f"UFW Hinweis: {profile_note}")
        rollback_lines.append(
            "UFW: Vorherige Default-Policies und bestehende Regeln dokumentieren; NetMon-added Profilregeln koennen gezielt entfernt werden."
        )

    if optional_services:
        actions.append("services_optional")
        preview_lines.append("Optionale Dienste (separate Bestätigung):")
        for action in optional_services:
            preview_lines.append(f"  - {_service_action_label(action)}")
        rollback_lines.append(
            "Optionale Dienste: Bei Bedarf betroffene Dienste wieder mit systemctl enable --now <dienst> aktivieren."
        )

    return {
        "profile": profile,
        "actions": actions,
        "preview_lines": preview_lines,
        "rollback_lines": rollback_lines,
        "preview_text": "\n".join(preview_lines).strip(),
        "rollback_text": "\n".join(rollback_lines).strip(),
        "sysctl_specs": sysctl_specs,
        "ufw_profile": ufw_profile,
        "optional_services": optional_services,
    }


def _security_baseline_transfer_status_default(app=None) -> str:
    return _tr(
        app,
        "baseline_transfer_status_default",
        "Transferpaket: keines geladen",
    )


def _security_baseline_transfer_status_loaded(
    package: dict, *, app=None, source_path: str = ""
) -> str:
    baseline = dict(package.get("baseline") or {})
    profile_name = str(
        baseline.get("profile")
        or baseline.get("id")
        or baseline.get("reference")
        or "unbekannt"
    ).strip()
    source_name = os.path.basename(str(source_path or "").strip()) or "-"
    return _tr(
        app,
        "baseline_transfer_status_loaded",
        "Transferpaket: {profile} | Quelle: {source}",
    ).format(profile=profile_name, source=source_name)


def _set_security_baseline_transfer_state(
    app,
    package: dict | None = None,
    *,
    source_path: str = "",
) -> None:
    if package:
        app.security_baseline_transfer_package = dict(package)
        app.security_baseline_transfer_source_path = str(source_path or "").strip()
        _app_var_set(
            app,
            "security_baseline_transfer_var",
            _security_baseline_transfer_status_loaded(
                package,
                app=app,
                source_path=source_path,
            ),
        )
        return
    app.security_baseline_transfer_package = None
    app.security_baseline_transfer_source_path = ""
    _app_var_set(
        app,
        "security_baseline_transfer_var",
        _security_baseline_transfer_status_default(app),
    )


def clear_security_baseline_transfer(
    app,
    *,
    showinfo_fn=None,
) -> bool:
    loaded_package = _app_value(app, "security_baseline_transfer_package")
    if not isinstance(loaded_package, dict):
        _set_security_baseline_transfer_state(app, None)
        return False
    _set_security_baseline_transfer_state(app, None)
    app.log_safe("Security Baseline Transfer entladen.")
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showinfo_runner(
        _tr(app, "baseline_transfer_clear_title", "Transferpaket entladen"),
        _tr(
            app,
            "baseline_transfer_clear_success",
            "Das geladene Baseline-Transferpaket wurde entladen. Die Profil-Haertung verwendet wieder nur das lokale Baseline-Profil.",
        ),
        parent=app,
    )
    return True


def _security_baseline_transfer_sysctl_entries(app=None) -> list[dict]:
    entries = []
    for spec in _sysctl_baseline_specs(app):
        entries.append(
            {
                "id": str(spec.get("id") or "").strip(),
                "title": str(spec.get("title") or spec.get("id") or "").strip(),
                "key": _sysctl_runtime_key(spec),
                "expected": str(spec.get("expected") or "").strip(),
                "group": str(spec.get("group") or "").strip(),
            }
        )
    return [entry for entry in entries if entry.get("key")]


def build_security_baseline_transfer_package(app=None) -> dict:
    profile = _active_baseline_profile(app)
    payload = {
        "schema": SECURITY_BASELINE_TRANSFER_SCHEMA,
        "schema_version": SECURITY_BASELINE_TRANSFER_SCHEMA_VERSION,
        "exported_at": datetime.now().isoformat(),
        "baseline": {
            "id": str(profile.get("id") or "").strip(),
            "name": str(profile.get("name") or "").strip(),
            "profile": str(profile.get("profile") or "").strip(),
            "version": str(profile.get("version") or "").strip(),
            "reference": str(profile.get("reference") or "").strip(),
            "date": str(profile.get("date") or "").strip(),
            "os_family": str(profile.get("os_family") or "").strip(),
            "distribution": str(profile.get("distribution") or "").strip(),
            "base_distribution": str(profile.get("base_distribution") or "").strip(),
            "roles": list(profile.get("roles") or []),
            "apply_supported": profile.get("apply_supported"),
        },
        "sysctl": {
            "dropin_path": _sysctl_dropin_path(app),
            "entries": _security_baseline_transfer_sysctl_entries(app),
        },
        "ufw": _active_ufw_baseline_profile(app),
        "notes": [
            "Nur freigegebene und begrenzte NetMon-Hardening-Schritte werden exportiert.",
            "Dienst-, Port-, VPN- und standortspezifische Regeln bleiben bewusst manuell.",
        ],
    }
    return payload


def default_security_baseline_transfer_filename(app=None) -> str:
    package = build_security_baseline_transfer_package(app)
    profile_id = str(
        (package.get("baseline") or {}).get("id")
        or SECURITY_BASELINE_DEFAULT_PROFILE_ID
    ).strip()
    stamp = datetime.now().strftime("%Y-%m-%d")
    return f"netmon_security_baseline_transfer_{profile_id}_{stamp}.json"


def _write_security_baseline_transfer_package(
    path: str, payload: dict
) -> tuple[bool, str | None]:
    try:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


def _read_security_baseline_transfer_package(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _sanitize_transfer_sysctl_entries(entries) -> list[dict]:
    normalized = []
    for raw in list(entries or []):
        if not isinstance(raw, dict):
            continue
        key = str(raw.get("key") or "").strip()
        expected = str(raw.get("expected") or "").strip()
        if not key or expected == "":
            continue
        # Importierte Transferpakete sind angreiferkontrollierbar. Nur bekannte,
        # dokumentierte Schluessel mit gueltigem Wertformat duerfen bis in die
        # Sysctl-Drop-in-Datei (die als root geladen wird) durchreichen — sonst
        # liesse sich ueber key/expected eine beliebige Direktive einschleusen.
        if not _is_allowed_sysctl_key(key):
            raise ValueError(
                f"Transferpaket enthaelt einen nicht erlaubten Sysctl-Schluessel: {key!r}"
            )
        if not _is_valid_sysctl_value(expected):
            raise ValueError(
                f"Transferpaket enthaelt einen ungueltigen Sysctl-Wert fuer {key}: {expected!r}"
            )
        # check_id wird ausschliesslich aus dem validierten Schluessel abgeleitet;
        # das rohe id-Feld des Pakets wird bewusst nicht uebernommen.
        check_id = f"sysctl.{key}"
        normalized.append(
            {
                "id": check_id,
                "title": str(raw.get("title") or check_id).strip(),
                "group": str(raw.get("group") or "Kernel").strip(),
                "expected": expected,
                "command": f"sysctl -n {key}",
                "check_kind": "rp_filter" if key.endswith(".rp_filter") else "sysctl",
            }
        )
    return normalized


def _sanitize_transfer_ufw_profile(profile: dict | None) -> dict | None:
    if not isinstance(profile, dict):
        return None
    default_incoming = str(profile.get("default_incoming") or "").strip().lower()
    default_outgoing = str(profile.get("default_outgoing") or "").strip().lower()
    if default_incoming not in {"allow", "deny", "reject"}:
        raise ValueError("UFW-Transferprofil enthaelt keine gueltige Incoming-Policy.")
    if default_outgoing not in {"allow", "deny", "reject"}:
        raise ValueError("UFW-Transferprofil enthaelt keine gueltige Outgoing-Policy.")
    rules = []
    for raw_rule in list(profile.get("rules") or []):
        if not isinstance(raw_rule, dict):
            continue
        candidate = dict(raw_rule)
        if _ufw_rule_key(candidate) is None:
            raise ValueError(
                "UFW-Transferprofil enthaelt mindestens eine ungueltige Regel."
            )
        rules.append(candidate)
    return {
        "id": str(profile.get("id") or "imported_ufw_profile").strip(),
        "name": str(profile.get("name") or "Imported UFW Profile").strip(),
        "profile_targets": list(profile.get("profile_targets") or []),
        "default_incoming": default_incoming,
        "default_outgoing": default_outgoing,
        "post_apply_note": str(profile.get("post_apply_note") or "").strip(),
        "rules": rules,
    }


def _validate_security_baseline_transfer_package(payload) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Transferpaket ist kein JSON-Objekt.")
    if str(payload.get("schema") or "").strip() != SECURITY_BASELINE_TRANSFER_SCHEMA:
        raise ValueError("Transferpaket besitzt ein unbekanntes Schema.")
    if (
        int(payload.get("schema_version") or 0)
        != SECURITY_BASELINE_TRANSFER_SCHEMA_VERSION
    ):
        raise ValueError(
            "Transferpaket besitzt eine nicht unterstuetzte Schema-Version."
        )

    baseline = dict(payload.get("baseline") or {})
    profile_id = str(baseline.get("id") or "").strip()
    if not profile_id:
        raise ValueError("Transferpaket enthaelt keine Baseline-Profilkennung.")

    sysctl = dict(payload.get("sysctl") or {})
    sysctl_entries = _sanitize_transfer_sysctl_entries(sysctl.get("entries") or [])
    ufw_profile = _sanitize_transfer_ufw_profile(payload.get("ufw"))
    if not sysctl_entries and ufw_profile is None:
        raise ValueError("Transferpaket enthaelt keine anwendbaren Hardening-Schritte.")

    return {
        "schema": SECURITY_BASELINE_TRANSFER_SCHEMA,
        "schema_version": SECURITY_BASELINE_TRANSFER_SCHEMA_VERSION,
        "exported_at": str(payload.get("exported_at") or "").strip(),
        "baseline": {
            "id": profile_id,
            "name": str(baseline.get("name") or "").strip(),
            "profile": str(baseline.get("profile") or profile_id).strip(),
            "version": str(baseline.get("version") or "").strip(),
            "reference": str(baseline.get("reference") or "").strip(),
            "date": str(baseline.get("date") or "").strip(),
            "os_family": str(baseline.get("os_family") or "").strip(),
            "distribution": str(baseline.get("distribution") or "").strip(),
            "base_distribution": str(baseline.get("base_distribution") or "").strip(),
            "roles": list(baseline.get("roles") or []),
            "apply_supported": baseline.get("apply_supported"),
        },
        "sysctl": {
            "dropin_path": str(
                sysctl.get("dropin_path") or SECURITY_BASELINE_SYSCTL_DROPIN_PATH
            ).strip(),
            "entries": sysctl_entries,
        },
        "ufw": ufw_profile,
        "notes": [
            str(item).strip()
            for item in list(payload.get("notes") or [])
            if str(item).strip()
        ],
    }


def _transfer_plan_from_package(package: dict) -> dict:
    baseline = dict(package.get("baseline") or {})
    sysctl = dict(package.get("sysctl") or {})
    sysctl_specs = list(sysctl.get("entries") or [])
    ufw_profile = package.get("ufw")
    actions = []
    preview_lines = []
    rollback_lines = []
    if sysctl_specs:
        actions.append("sysctl")
        preview_lines.append(
            f"Sysctl Drop-in: {str(sysctl.get('dropin_path') or SECURITY_BASELINE_SYSCTL_DROPIN_PATH).strip()}"
        )
        for spec in sysctl_specs:
            preview_lines.append(
                f"  - {spec.get('title', spec.get('id', 'sysctl'))} = {spec.get('expected', '-')}"
            )
        rollback_lines.append(
            "Sysctl: Vorherige Drop-in-Datei sichern oder den NetMon-Drop-in entfernen und sysctl neu laden."
        )
    if isinstance(ufw_profile, dict):
        actions.append("ufw")
        preview_lines.append(
            "UFW Defaults: "
            f"incoming={ufw_profile.get('default_incoming', '-')}, "
            f"outgoing={ufw_profile.get('default_outgoing', '-')}"
        )
        for rule in ufw_profile.get("rules", []) or []:
            preview_lines.append(f"  - {_ufw_rule_preview_text(rule)}")
        profile_note = str(ufw_profile.get("post_apply_note") or "").strip()
        if profile_note:
            preview_lines.append(f"UFW Hinweis: {profile_note}")
        rollback_lines.append(
            "UFW: Vorherige Default-Policies und bestehende Regeln dokumentieren; NetMon-added Profilregeln koennen gezielt entfernt werden."
        )
    return {
        "profile": baseline,
        "actions": actions,
        "preview_lines": preview_lines,
        "rollback_lines": rollback_lines,
        "preview_text": "\n".join(preview_lines).strip(),
        "rollback_text": "\n".join(rollback_lines).strip(),
        "sysctl_specs": sysctl_specs,
        "ufw_profile": ufw_profile,
        "transfer_package": package,
    }


def _transfer_sysctl_map(package: dict) -> dict[str, str]:
    sysctl = dict(package.get("sysctl") or {})
    mapping = {}
    for entry in list(sysctl.get("entries") or []):
        if not isinstance(entry, dict):
            continue
        key = _sysctl_runtime_key(entry) or str(entry.get("key") or "").strip()
        expected = str(entry.get("expected") or "").strip()
        if key and expected != "":
            mapping[key] = expected
    return mapping


def _transfer_ufw_rule_strings(package: dict) -> list[str]:
    ufw = package.get("ufw")
    if not isinstance(ufw, dict):
        return []
    result = []
    for rule in list(ufw.get("rules") or []):
        if isinstance(rule, dict):
            result.append(_ufw_rule_preview_text(rule))
    return result


def security_baseline_transfer_comparison_text(
    app,
    *,
    transfer_package: dict | None = None,
) -> str:
    imported = transfer_package
    if imported is None:
        loaded = _app_value(app, "security_baseline_transfer_package")
        if isinstance(loaded, dict):
            imported = loaded
    if not isinstance(imported, dict):
        return ""

    local = build_security_baseline_transfer_package(app)
    local_baseline = dict(local.get("baseline") or {})
    imported_baseline = dict(imported.get("baseline") or {})
    local_sysctl = _transfer_sysctl_map(local)
    imported_sysctl = _transfer_sysctl_map(imported)
    local_ufw = local.get("ufw") if isinstance(local.get("ufw"), dict) else None
    imported_ufw = (
        imported.get("ufw") if isinstance(imported.get("ufw"), dict) else None
    )

    lines = [
        _tr(
            app,
            "baseline_transfer_compare_heading",
            "Vergleich lokales Profil vs. importiertes Transferpaket",
        ),
        "",
        _tr(app, "baseline_transfer_compare_section_profile", "Profil"),
        f"- {_tr(app, 'baseline_transfer_compare_local', 'Lokal')}: "
        f"{local_baseline.get('profile') or local_baseline.get('id') or '-'} "
        f"[{local_baseline.get('id') or '-'}]",
        f"- {_tr(app, 'baseline_transfer_compare_imported', 'Importiert')}: "
        f"{imported_baseline.get('profile') or imported_baseline.get('id') or '-'} "
        f"[{imported_baseline.get('id') or '-'}]",
        f"- Reference: {local_baseline.get('reference') or '-'} | {imported_baseline.get('reference') or '-'}",
        f"- OS family: {local_baseline.get('os_family') or '-'} | {imported_baseline.get('os_family') or '-'}",
        "",
        _tr(app, "baseline_transfer_compare_section_sysctl", "Sysctl"),
    ]

    all_sysctl_keys = sorted(set(local_sysctl) | set(imported_sysctl))
    if not all_sysctl_keys:
        lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))
    for key in all_sysctl_keys:
        local_value = local_sysctl.get(key, "-")
        imported_value = imported_sysctl.get(key, "-")
        marker = "==" if local_value == imported_value else "!="
        lines.append(f"- {key}: {local_value} {marker} {imported_value}")

    lines.extend(
        [
            "",
            _tr(app, "baseline_transfer_compare_section_ufw", "UFW"),
        ]
    )
    if local_ufw is None and imported_ufw is None:
        lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))
    else:
        local_defaults = (
            f"incoming={local_ufw.get('default_incoming', '-')}, outgoing={local_ufw.get('default_outgoing', '-')}"
            if local_ufw
            else "-"
        )
        imported_defaults = (
            f"incoming={imported_ufw.get('default_incoming', '-')}, outgoing={imported_ufw.get('default_outgoing', '-')}"
            if imported_ufw
            else "-"
        )
        lines.append(f"- Defaults: {local_defaults} | {imported_defaults}")
        local_rules = _transfer_ufw_rule_strings(local)
        imported_rules = _transfer_ufw_rule_strings(imported)
        if local_rules or imported_rules:
            lines.append(
                f"- {_tr(app, 'baseline_transfer_compare_local', 'Lokal')} Regeln:"
            )
            lines.extend([f"  - {rule}" for rule in (local_rules or ["-"])])
            lines.append(
                f"- {_tr(app, 'baseline_transfer_compare_imported', 'Importiert')} Regeln:"
            )
            lines.extend([f"  - {rule}" for rule in (imported_rules or ["-"])])

    return "\n".join(lines).strip()


def security_baseline_transfer_package_text(
    app,
    *,
    transfer_package: dict | None = None,
    source_path: str = "",
) -> str:
    loaded = transfer_package
    if loaded is None:
        current = _app_value(app, "security_baseline_transfer_package")
        if isinstance(current, dict):
            loaded = current
    if not isinstance(loaded, dict):
        return ""

    baseline = dict(loaded.get("baseline") or {})
    sysctl = dict(loaded.get("sysctl") or {})
    ufw = loaded.get("ufw") if isinstance(loaded.get("ufw"), dict) else None
    notes = [
        str(item).strip()
        for item in list(loaded.get("notes") or [])
        if str(item).strip()
    ]
    exported_at = str(loaded.get("exported_at") or "-").strip() or "-"
    schema = str(loaded.get("schema") or "-").strip() or "-"
    schema_version = str(loaded.get("schema_version") or "-").strip() or "-"
    effective_source = str(
        source_path or _app_value(app, "security_baseline_transfer_source_path") or ""
    ).strip()
    source_name = os.path.basename(effective_source) or "-"

    lines = [
        _tr(
            app,
            "baseline_transfer_show_heading",
            "Geladenes Transferpaket",
        ),
        "",
        _tr(app, "baseline_transfer_compare_section_profile", "Profil"),
        f"- Source: {source_name}",
        f"- Exported at: {exported_at}",
        f"- Schema: {schema} v{schema_version}",
        f"- Name: {baseline.get('profile') or baseline.get('name') or baseline.get('id') or '-'}",
        f"- ID: {baseline.get('id') or '-'}",
        f"- Version: {baseline.get('version') or '-'}",
        f"- Reference: {baseline.get('reference') or '-'}",
        f"- OS family: {baseline.get('os_family') or '-'}",
        f"- Distribution: {baseline.get('distribution') or '-'}",
        f"- Base distribution: {baseline.get('base_distribution') or '-'}",
        f"- Roles: {', '.join(list(baseline.get('roles') or [])) or '-'}",
        "",
        _tr(app, "baseline_transfer_compare_section_sysctl", "Sysctl"),
        f"- Drop-in: {str(sysctl.get('dropin_path') or SECURITY_BASELINE_SYSCTL_DROPIN_PATH).strip()}",
    ]

    sysctl_entries = list(sysctl.get("entries") or [])
    if not sysctl_entries:
        lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))
    else:
        for entry in sysctl_entries:
            if not isinstance(entry, dict):
                continue
            key = (
                _sysctl_runtime_key(entry)
                or str(entry.get("key") or entry.get("id") or "sysctl").strip()
            )
            expected = str(entry.get("expected") or "-").strip() or "-"
            lines.append(f"- {key} = {expected}")

    lines.extend(
        [
            "",
            _tr(app, "baseline_transfer_compare_section_ufw", "UFW"),
        ]
    )
    if ufw is None:
        lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))
    else:
        lines.append(
            "- Defaults: "
            f"incoming={ufw.get('default_incoming', '-')}, "
            f"outgoing={ufw.get('default_outgoing', '-')}"
        )
        rules = _transfer_ufw_rule_strings(loaded)
        if rules:
            lines.extend([f"- {rule}" for rule in rules])
        else:
            lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))

    lines.extend(
        [
            "",
            _tr(app, "baseline_transfer_show_notes", "Hinweise"),
        ]
    )
    if notes:
        lines.extend([f"- {note}" for note in notes])
    else:
        lines.append(_tr(app, "baseline_transfer_compare_none", "Keine Eintraege."))

    return "\n".join(lines).strip()


def _read_ufw_status_with_mode(mode: str, *, run_cmd_fn=None) -> tuple[int, str]:
    runner = run_cmd_fn or run_cmd
    args = ["sudo", "-n", "env", "LANG=C", "LC_ALL=C", "ufw", "status"]
    if mode == "verbose":
        args.append("verbose")
    elif mode == "numbered":
        args.append("numbered")
    return runner(args, timeout=12)


def _parse_ufw_default_policies(status_text: str) -> tuple[str | None, str | None]:
    low = str(status_text or "").lower()
    match = re.search(
        r"default:\s*(allow|deny|reject)\s*\(incoming\)\s*,\s*"
        r"(allow|deny|reject)\s*\(outgoing\)",
        low,
    )
    if not match:
        return None, None
    return match.group(1), match.group(2)


def _ufw_rule_key(rule: dict) -> tuple | None:
    rule_type = str((rule or {}).get("type") or "").strip().lower()
    if rule_type == "interface":
        direction = str((rule or {}).get("direction") or "").strip().lower()
        iface = str((rule or {}).get("iface") or "").strip().lower()
        if direction in {"in", "out"} and iface:
            return ("iface", direction, iface)
    if rule_type == "endpoint":
        ip_val = str((rule or {}).get("ip") or "").strip().lower()
        port = str((rule or {}).get("port") or "").strip().lower()
        if ip_val and port:
            return ("endpoint", ip_val, port)
    return None


def _existing_ufw_profile_rule_keys(status_text: str) -> set[tuple]:
    keys = set()
    for raw_line in str(status_text or "").splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue
        line = re.sub(r"^\[\s*\d+\]\s+", "", line)
        if "allow" not in line:
            continue
        if " on lo" in line:
            if re.search(r"\bin\b", line):
                keys.add(("iface", "in", "lo"))
            if re.search(r"\bout\b", line):
                keys.add(("iface", "out", "lo"))
    return keys


def _ensure_ufw_profile_rule(
    rule: dict,
    *,
    run_cmd_fn=None,
    known_keys=None,
) -> tuple[bool, bool, str, set[tuple]]:
    runner = run_cmd_fn or run_cmd
    keys = known_keys if isinstance(known_keys, set) else set()
    key = _ufw_rule_key(rule)
    if key is None:
        return False, False, "ungueltige UFW-Baseline-Regel", keys
    if key in keys:
        return True, False, "exists", keys

    rule_type = key[0]
    if rule_type == "iface":
        _tag, direction, iface = key
        rc, out = runner(
            ["sudo", "-n", "ufw", "allow", direction, "on", iface],
            timeout=20,
        )
    else:
        _tag, ip_val, port = key
        rc, out = runner(
            [
                "sudo",
                "-n",
                "ufw",
                "allow",
                "out",
                "to",
                ip_val,
                "port",
                port,
                "proto",
                "udp",
            ],
            timeout=20,
        )
    if rc == 0:
        keys.add(key)
        return True, True, "added", keys
    return False, False, (out or "").strip() or "unknown", keys


def _delete_ufw_profile_rule(rule: dict, *, run_cmd_fn=None):
    runner = run_cmd_fn or run_cmd
    key = _ufw_rule_key(rule)
    if key is None:
        return
    if key[0] == "iface":
        _tag, direction, iface = key
        rc, out = runner(
            ["sudo", "-n", "ufw", "delete", "allow", direction, "on", iface],
            timeout=20,
        )
    else:
        _tag, ip_val, port = key
        rc, out = runner(
            [
                "sudo",
                "-n",
                "ufw",
                "delete",
                "allow",
                "out",
                "to",
                ip_val,
                "port",
                port,
                "proto",
                "udp",
            ],
            timeout=20,
        )
    if rc != 0:
        raise RuntimeError(out or "UFW-Regel konnte nicht entfernt werden.")


def _run_checked_command(args: list[str], *, run_cmd_fn=None, timeout: int = 20):
    runner = run_cmd_fn or run_cmd
    rc, out = runner(args, timeout=timeout)
    if rc != 0:
        raise RuntimeError(out or "Befehl fehlgeschlagen.")
    return out


def _ufw_profile_matches_status(profile: dict, status_text: str) -> bool:
    status_state = _parse_ufw_status_state(status_text)
    if status_state != "active":
        return False
    incoming, outgoing = _parse_ufw_default_policies(status_text)
    if incoming != str(profile.get("default_incoming") or "").lower():
        return False
    if outgoing != str(profile.get("default_outgoing") or "").lower():
        return False
    keys = _existing_ufw_profile_rule_keys(status_text)
    for rule in profile.get("rules", []) or []:
        key = _ufw_rule_key(rule)
        if key is not None and key not in keys:
            return False
    return True


def _build_sysctl_dropin_content(specs: list[dict]) -> str:
    header = [
        "# NetMon Security Baseline",
        "# Generated: 2026-07-19",
        "# Profile: Desktop / Development",
        "",
    ]
    lines = []
    for spec in specs:
        check_id = str(spec.get("id") or "")
        if not check_id.startswith("sysctl."):
            continue
        key = check_id.split("sysctl.", 1)[1]
        value = str(spec.get("expected") or "").strip()
        if not key or not value:
            continue
        # Zweite Verteidigungslinie direkt an der Schreibsenke: selbst wenn ein
        # Spec auf anderem Weg als ueber den Transfer-Import hereinkommt, darf nur
        # ein erlaubter Schluessel mit unbedenklichem Wert in die Drop-in-Datei.
        if not _is_allowed_sysctl_key(key) or not _is_valid_sysctl_value(value):
            continue
        lines.append(f"{key} = {value}")
    return "\n".join(header + lines) + "\n"


# Eine sysctl-Konfigzeile ist entweder leer, ein Kommentar oder "key = value".
_SYSCTL_CONFIG_LINE_RE = re.compile(r"^\s*[\w./-]+\s*=")


def _implausible_sysctl_config_line(content: str) -> str:
    """Erste Zeile, die keine sysctl-Konfigzeile sein kann - sonst "".

    run_cmd fuehrt stderr mit stdout zusammen (core/command.py), deshalb kann
    eine sudo-Warnung ("unable to resolve host ...") mit rc=0 im vermeintlichen
    Dateiinhalt landen. Bei Read-Modify-Write wuerde sie als root in die
    Konfigdatei zurueckgeschrieben. Lieber abbrechen als eine unerwartete Zeile
    in einer Root-Konfigdatei zu persistieren oder still zu verwerfen.
    """
    for raw_line in str(content or "").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not _SYSCTL_CONFIG_LINE_RE.match(raw_line):
            return stripped
    return ""


def _read_existing_sysctl_dropin(path: str, *, run_cmd_fn=None) -> tuple[bool, str]:
    runner = run_cmd_fn or run_cmd
    rc_test, _out_test = runner(["sudo", "-n", "test", "-f", path], timeout=5)
    if rc_test != 0:
        return False, ""
    rc_cat, out_cat = runner(["sudo", "-n", "cat", path], timeout=10)
    if rc_cat != 0:
        raise RuntimeError(out_cat or f"Datei konnte nicht gelesen werden: {path}")
    suspicious = _implausible_sysctl_config_line(out_cat)
    if suspicious:
        raise RuntimeError(f"Unerwarteter Inhalt in {path}: {suspicious[:80]}")
    return True, out_cat if out_cat.endswith("\n") else f"{out_cat}\n"


def _restore_sysctl_dropin(
    path: str,
    existed_before: bool,
    previous_content: str,
    *,
    run_cmd_fn=None,
):
    runner = run_cmd_fn or run_cmd
    if existed_before:
        rc_cp, out_cp = write_privileged_config(
            path,
            previous_content,
            run_cmd_fn=runner,
            timeout=10,
        )
        if rc_cp != 0:
            raise RuntimeError(
                out_cp or f"Datei konnte nicht wiederhergestellt werden: {path}"
            )
    else:
        rc_rm, out_rm = runner(["sudo", "-n", "rm", "-f", path], timeout=10)
        if rc_rm != 0:
            raise RuntimeError(out_rm or f"Datei konnte nicht entfernt werden: {path}")
    rc_load, out_load = runner(["sudo", "-n", "sysctl", "--system"], timeout=20)
    if rc_load != 0:
        raise RuntimeError(out_load or "sysctl --system fehlgeschlagen")


def _apply_sysctl_dropin(
    path: str,
    content: str,
    *,
    run_cmd_fn=None,
    rollback_tx=None,
) -> tuple[bool, str]:
    runner = run_cmd_fn or run_cmd
    existed_before, previous_content = _read_existing_sysctl_dropin(
        path, run_cmd_fn=runner
    )
    if rollback_tx is not None:
        rollback_tx.add_rollback(
            "Vorherige Sysctl-Drop-in wiederherstellen",
            lambda p=path, existed=existed_before, prev=previous_content: _restore_sysctl_dropin(
                p,
                existed,
                prev,
                run_cmd_fn=runner,
            ),
        )

    rc_cp, out_cp = write_privileged_config(
        path,
        content,
        run_cmd_fn=runner,
        timeout=10,
    )
    if rc_cp != 0:
        return False, out_cp or f"Datei konnte nicht geschrieben werden: {path}"
    rc_load, out_load = runner(["sudo", "-n", "sysctl", "--system"], timeout=20)
    if rc_load != 0:
        return False, out_load or "sysctl --system fehlgeschlagen"
    return True, out_load


def _build_ufw_sysctl_override_content(
    content: str,
    overrides: dict[str, str],
) -> tuple[str, bool]:
    # Zweite Verteidigungslinie direkt an der Schreibsenke - analog zu
    # _render_sysctl_dropin_content. /etc/ufw/sysctl.conf ueberschreibt laut
    # eigenem Header /etc/sysctl.conf und /etc/sysctl.d, wirkt also eher
    # staerker als die Drop-in-Datei und darf nicht schwaecher gefiltert sein.
    normalized_overrides = {}
    for key, value in overrides.items():
        normalized_key = _normalize_sysctl_config_key(key)
        normalized_value = str(value).strip()
        if not normalized_key or not normalized_value:
            continue
        if not _is_allowed_sysctl_key(normalized_key):
            continue
        if not _is_valid_sysctl_value(normalized_value):
            continue
        normalized_overrides[normalized_key] = normalized_value
    seen = set()
    changed = False
    rendered = []
    for raw_line in str(content or "").splitlines():
        if (
            raw_line.strip()
            and not raw_line.lstrip().startswith("#")
            and "=" in raw_line
        ):
            line_key, _line_value = raw_line.split("=", 1)
            normalized_key = _normalize_sysctl_config_key(line_key)
            if normalized_key in normalized_overrides:
                seen.add(normalized_key)
                next_line = f"{line_key.strip()}={normalized_overrides[normalized_key]}"
                rendered.append(next_line)
                changed = changed or next_line != raw_line
                continue
        rendered.append(raw_line)

    missing = [key for key in normalized_overrides if key not in seen]
    if missing:
        if rendered and rendered[-1].strip():
            rendered.append("")
        rendered.append("# NetMon persistent hardening overrides")
        for key in missing:
            rendered.append(f"{key.replace('.', '/')}={normalized_overrides[key]}")
        changed = True

    return "\n".join(rendered) + "\n", changed


def _restore_ufw_sysctl_config(
    path: str,
    backup_path: str,
    *,
    run_cmd_fn=None,
):
    runner = run_cmd_fn or run_cmd
    rc_restore, out_restore = runner(
        ["sudo", "-n", "cp", "-a", backup_path, path],
        timeout=10,
    )
    if rc_restore != 0:
        raise RuntimeError(
            out_restore
            or f"UFW-sysctl-Backup konnte nicht wiederhergestellt werden: {backup_path}"
        )
    rc_load, out_load = runner(
        ["sudo", "-n", "sysctl", "-e", "-q", "-p", path],
        timeout=20,
    )
    if rc_load != 0:
        raise RuntimeError(out_load or "UFW-sysctl-Reload fehlgeschlagen")


def _apply_ufw_sysctl_overrides(
    path: str = SECURITY_BASELINE_UFW_SYSCTL_PATH,
    overrides: dict[str, str] | None = None,
    *,
    run_cmd_fn=None,
    rollback_tx=None,
) -> tuple[bool, str]:
    runner = run_cmd_fn or run_cmd
    desired = dict(overrides or SECURITY_BASELINE_UFW_SYSCTL_OVERRIDES)
    rc_test, out_test = runner(["sudo", "-n", "test", "-f", path], timeout=5)
    if rc_test != 0:
        return False, out_test or f"UFW-sysctl-Datei fehlt: {path}"
    rc_cat, content = runner(["sudo", "-n", "cat", path], timeout=10)
    if rc_cat != 0:
        return False, content or f"UFW-sysctl-Datei konnte nicht gelesen werden: {path}"
    suspicious = _implausible_sysctl_config_line(content)
    if suspicious:
        return False, f"Unerwarteter Inhalt in {path}: {suspicious[:80]}"

    next_content, changed = _build_ufw_sysctl_override_content(content, desired)
    backup_path = ""
    if changed:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_path = f"{path}.netmon-backup-{timestamp}"
        rc_backup, out_backup = runner(
            ["sudo", "-n", "cp", "-a", path, backup_path],
            timeout=10,
        )
        if rc_backup != 0:
            return (
                False,
                out_backup
                or f"UFW-sysctl-Backup konnte nicht erstellt werden: {backup_path}",
            )
        if rollback_tx is not None:
            rollback_tx.add_rollback(
                "Vorherige UFW-sysctl-Konfiguration wiederherstellen",
                lambda p=path, b=backup_path: _restore_ufw_sysctl_config(
                    p,
                    b,
                    run_cmd_fn=runner,
                ),
            )

        rc_cp, out_cp = write_privileged_config(
            path,
            next_content,
            run_cmd_fn=runner,
            timeout=10,
        )
        if rc_cp != 0:
            return (
                False,
                out_cp or f"UFW-sysctl-Datei konnte nicht geschrieben werden: {path}",
            )

    rc_load, out_load = runner(
        ["sudo", "-n", "sysctl", "-e", "-q", "-p", path],
        timeout=20,
    )
    if rc_load != 0:
        return False, out_load or "UFW-sysctl-Reload fehlgeschlagen"
    if changed:
        return True, f"UFW-sysctl-Konfiguration angepasst. Backup: {backup_path}"
    return True, "UFW-sysctl-Konfiguration war bereits passend; Werte neu geladen."


def _lynis_security_baseline_state(app) -> dict:
    return {
        "profile": _active_baseline_profile(app),
        "last_checked": str(
            _app_value(app, "security_baseline_last_checked", "") or ""
        ),
        "results": list(_app_value(app, "security_baseline_results", []) or []),
        "lynis_result": dict(_app_value(app, "lynis_last_result", {}) or {}),
    }


def restore_security_baseline_state(app) -> bool:
    state = _app_value(app, "lynis_security_baseline_state", {}) or {}
    if not isinstance(state, dict) or not state:
        return False
    app.security_baseline_results = list(state.get("results", []) or [])
    app.security_baseline_last_checked = str(state.get("last_checked", "") or "")
    return True


def _lynis_line_category(line: str) -> str:
    low = str(line or "").lower()
    if "warning" in low or "warnung" in low:
        return "Warnung"
    if "suggestion" in low or "recommendation" in low or "empfehlung" in low:
        return "Empfehlung"
    if "hardening" in low or "härtung" in low:
        return "Hardening"
    if (
        "disabled" in low
        or "not enabled" in low
        or "not found" in low
        or "nicht aktiviert" in low
        or "nicht gefunden" in low
    ):
        return "Hinweis"
    return "Kontext"


def _line_is_relevant_lynis_finding(line: str) -> bool:
    return _lynis_line_category(line) != "Kontext"


def _parse_lynis_findings(text: str) -> list[dict[str, str]]:
    findings = []
    for line in str(text or "").splitlines():
        stripped = str(line or "").strip()
        if not stripped or not _line_is_relevant_lynis_finding(stripped):
            continue
        findings.append(
            {
                "category": _lynis_line_category(stripped),
                "line": stripped,
                "normalized": stripped.lower(),
            }
        )
    return findings


def _lynis_finding_matches_rule(finding: dict, rule: dict) -> bool:
    normalized = str(finding.get("normalized") or "")
    topics = [str(topic).lower() for topic in rule.get("topics", []) or []]
    signals = [str(signal).lower() for signal in rule.get("signals", []) or []]
    if topics and not any(topic in normalized for topic in topics):
        return False
    if signals and not any(signal in normalized for signal in signals):
        return False
    return True


def _find_lynis_findings_for_check(app, check_id: str) -> list[dict[str, str]]:
    text = str(_app_value(app, "lynis_last_output", "") or "").strip()
    if not text:
        return []
    rule = SECURITY_BASELINE_LYNIS_MATCH_RULES.get(check_id, {})
    if not rule:
        return []
    matches = [
        finding
        for finding in _parse_lynis_findings(text)
        if _lynis_finding_matches_rule(finding, rule)
    ]
    unique = []
    seen = set()
    for finding in matches:
        line = str(finding.get("line") or "")
        if line and line not in seen:
            seen.add(line)
            unique.append(finding)
    return unique[:5]


def _attach_lynis_references(app, rows: list[dict]) -> list[dict]:
    for row in rows:
        check_id = str(row.get("id") or "")
        row.pop("lynis_findings", None)
        if row.pop("lynis_reference_dynamic", False):
            row["lynis_reference"] = ""
        matched_findings = _find_lynis_findings_for_check(app, check_id)
        if matched_findings:
            row["lynis_findings"] = [
                {
                    "category": finding.get("category", ""),
                    "line": finding.get("line", ""),
                }
                for finding in matched_findings
            ]
            row["lynis_reference"] = "\n".join(
                "{category}: {line}".format(
                    category=finding.get("category", "Hinweis"),
                    line=finding.get("line", ""),
                )
                for finding in matched_findings
            )
            row["lynis_reference_dynamic"] = True
    return rows


def _run_read_command(command: str, *, run_cmd_fn=None, timeout: int = 15):
    runner = run_cmd_fn or run_cmd
    return runner(["bash", "-lc", command], timeout=timeout)


ROOT_REQUIRED_BASELINE_CHECK_IDS = {
    "auth.no_empty_password_accounts",
    "fw.ufw_active",
    "fw.ufw_rules_non_empty",
    "pkg.critical_file_permissions_checked",
}


def _spec_requires_root_read(spec: dict) -> bool:
    return str(spec.get("id") or "").strip() in ROOT_REQUIRED_BASELINE_CHECK_IDS


def _spec_root_required_reason(spec: dict) -> str:
    check_id = str(spec.get("id") or "").strip()
    source = str(
        spec.get("config_source") or spec.get("source") or "geschuetzte Quelle"
    )
    if check_id == "auth.no_empty_password_accounts":
        return "Das Lesen von /etc/shadow benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."
    if check_id == "fw.ufw_active":
        return "Das Lesen von `ufw status` benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."
    if check_id == "fw.ufw_rules_non_empty":
        return "Das Lesen von `ufw status numbered` benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."
    if check_id == "pkg.critical_file_permissions_checked":
        return "Die Pruefung der kritischen Systemdateien benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."
    return f"Das Lesen von {source} benoetigt Administratorrechte, die NetMon aktuell nicht besitzt."


def _detect_hardening_privilege_context(app=None) -> dict[str, object]:
    is_root = False
    try:
        is_root = os.geteuid() == 0
    except AttributeError:
        is_root = False

    has_sudo_session = False
    if not is_root:
        try:
            has_sudo_session = check_sudo_nopasswd()
        except Exception:
            has_sudo_session = False

    pkexec_authorized = False
    if app is not None:
        try:
            pkexec_authorized = bool(
                getattr(app, "__dict__", {}).get("pkexec_authorized", False)
            )
        except Exception:
            pkexec_authorized = False

    root_available = is_root or has_sudo_session or pkexec_authorized
    if is_root:
        source = "geteuid"
    elif has_sudo_session:
        source = "sudo -n true"
    elif pkexec_authorized:
        source = "pkexec authorization"
    else:
        source = "keine privilegierte Session"

    return {
        "is_root": is_root,
        "has_sudo_session": has_sudo_session,
        "root_available": root_available,
        "source": source,
        "pkexec_authorized": pkexec_authorized,
    }


def _permission_error_text(text: str) -> bool:
    low = str(text or "").lower()
    return any(
        token in low
        for token in (
            "permission denied",
            "operation not permitted",
            "root",
            "must be superuser",
            "superuser",
            "access denied",
        )
    )


def _missing_file_text(text: str) -> bool:
    low = str(text or "").lower()
    return any(
        token in low
        for token in (
            "no such file",
            "not found",
            "nicht gefunden",
            "keine lesbare",
            "datei nicht gefunden",
            "cannot stat",
        )
    )


def _mark_root_required(result: dict, *, reason: str, error: str = "") -> dict:
    result["status"] = "Root-Rechte erforderlich"
    result["reason"] = reason
    if error:
        result["check_error"] = error
    return result


def _mark_check_error(result: dict, *, reason: str, error: str = "") -> dict:
    result["status"] = "Fehler bei der Pruefung"
    result["reason"] = reason
    if error:
        result["check_error"] = error
    return result


def _apply_baseline_diagnostics(
    result: dict,
    *,
    root_context: dict[str, object] | None,
    check_method: str,
    value_source: str = "",
):
    context = root_context or {}
    root_used = bool(context.get("is_root"))
    if not root_used and bool(context.get("has_sudo_session")):
        root_used = str(check_method).startswith("sudo:")
    result["root_used"] = "Ja" if root_used else "Nein"
    result["check_method"] = check_method
    result["value_source"] = value_source or str(result.get("config_source") or "-")
    result["privilege_source"] = str(context.get("source") or "unbekannt")
    result["root_available"] = bool(context.get("root_available", False))


def _run_privileged_read_command(
    command: str,
    *,
    root_context: dict[str, object] | None,
    run_cmd_fn=None,
    timeout: int = 15,
) -> tuple[int, str, str]:
    context = root_context or {}
    runner = run_cmd_fn or run_cmd
    if bool(context.get("is_root")):
        rc, out = runner(["bash", "-lc", command], timeout=timeout)
        return rc, out, "root:bash -lc"
    if bool(context.get("has_sudo_session")):
        rc, out = runner(["sudo", "-n", "bash", "-lc", command], timeout=timeout)
        return rc, out, "sudo:bash -lc"
    if bool(context.get("pkexec_authorized")) and has_cmd("pkexec"):
        rc, out = runner(["pkexec", "/bin/bash", "-lc", command], timeout=timeout)
        return rc, out, "pkexec:bash -lc"
    rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn, timeout=timeout)
    return rc, out, "shell:bash -lc"


def _proc_sys_path_for_key(key: str) -> Path:
    return Path("/proc/sys").joinpath(*str(key).split("."))


def _read_text_file(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def _read_sysctl_value_native(key: str) -> str:
    return _read_text_file(_proc_sys_path_for_key(key)).strip()


def _normalize_sysctl_config_key(key: str) -> str:
    return str(key or "").strip().replace("/", ".")


def _sysctl_config_source_value(path: str | Path, key: str) -> str | None:
    expected_key = _normalize_sysctl_config_key(key)
    try:
        lines = _read_text_file(path).splitlines()
    except OSError:
        return None

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        line_key, line_value = line.split("=", 1)
        if _normalize_sysctl_config_key(line_key) == expected_key:
            return line_value.strip()
    return None


def _sysctl_config_source_contains_expected(spec: dict, expected: str) -> bool:
    check_id = str(spec.get("id") or "").strip()
    config_source = str(spec.get("config_source") or "").strip()
    if not check_id.startswith("sysctl.") or not config_source:
        return False

    key = check_id.split("sysctl.", 1)[1]
    configured_value = _sysctl_config_source_value(config_source, key)
    return configured_value == str(expected).strip()


def _sysctl_ufw_override_value(spec: dict) -> str | None:
    check_id = str(spec.get("id") or "").strip()
    if not check_id.startswith("sysctl."):
        return None
    key = check_id.split("sysctl.", 1)[1]
    return _sysctl_config_source_value("/etc/ufw/sysctl.conf", key)


def _sysctl_ufw_override_hint(spec: dict, expected: str) -> str:
    if not _sysctl_config_source_contains_expected(spec, expected):
        return ""
    ufw_value = _sysctl_ufw_override_value(spec)
    if ufw_value is None or ufw_value == str(expected).strip():
        return ""
    return (
        f"/etc/ufw/sysctl.conf setzt denselben Wert auf {ufw_value}; "
        "ufw.service kann die systemd-sysctl-Werte beim Start ueberschreiben."
    )


def _count_empty_password_accounts_native() -> int:
    count = 0
    for raw_line in _read_text_file("/etc/shadow").splitlines():
        if not raw_line:
            continue
        parts = raw_line.split(":")
        if len(parts) > 1 and parts[1] == "":
            count += 1
    return count


def _boot_uefi_active_native() -> bool:
    return Path("/sys/firmware/efi").is_dir()


def _grub_password_protected_native() -> tuple[bool, str]:
    candidates = [
        Path("/boot/grub/grub.cfg"),
        Path("/boot/grub2/grub.cfg"),
    ]
    for path in candidates:
        if not path.is_file():
            continue
        text = _read_text_file(path)
        return bool(re.search(r"(password|pbkdf2)", text, re.IGNORECASE)), str(path)
    raise FileNotFoundError(
        "Keine lesbare GRUB-Konfiguration unter /boot/grub/grub.cfg oder /boot/grub2/grub.cfg gefunden."
    )


def _pam_password_strength_native() -> tuple[bool, list[str]]:
    matches = []
    pam_dir = Path("/etc/pam.d")
    for path in sorted(pam_dir.rglob("*")):
        if not path.is_file():
            continue
        try:
            for raw_line in _read_text_file(path).splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "pam_pwquality" in line or "pam_cracklib" in line:
                    matches.append(f"{path}: {line}")
        except OSError:
            continue
    return bool(matches), matches


def _count_duplicate_uid_gid_native() -> int:
    uid_counts = collections.Counter()
    gid_counts = collections.Counter()
    for raw_line in _read_text_file("/etc/passwd").splitlines():
        parts = raw_line.rstrip("\n").split(":")
        if len(parts) > 3:
            uid_counts[parts[2]] += 1
    for raw_line in _read_text_file("/etc/group").splitlines():
        parts = raw_line.rstrip("\n").split(":")
        if len(parts) > 2:
            gid_counts[parts[2]] += 1
    return sum(1 for value in uid_counts.values() if value > 1) + sum(
        1 for value in gid_counts.values() if value > 1
    )


def _critical_file_entries_native() -> list[dict[str, str]]:
    entries = []
    for path_text in CRITICAL_FILE_POLICY.keys():
        path = Path(path_text)
        st = path.stat()
        mode = format(stat.S_IMODE(st.st_mode), "03o")
        try:
            owner = pwd.getpwuid(st.st_uid).pw_name
        except KeyError:
            owner = str(st.st_uid)
        try:
            group = grp.getgrgid(st.st_gid).gr_name
        except KeyError:
            group = str(st.st_gid)
        entries.append(
            {
                "mode": mode,
                "owner": owner,
                "group": group,
                "path": path_text,
            }
        )
    return entries


def _home_permission_entries_native() -> tuple[int, str]:
    home = Path("/home")
    getfacl = shutil.which("getfacl")
    try:
        entries = sorted(os.scandir(home), key=lambda item: item.path)
    except OSError as exc:
        return 2, f"ERROR {home} {exc}"

    rendered = []
    for entry in entries:
        path = entry.path
        try:
            st = entry.stat(follow_symlinks=False)
        except OSError as exc:
            rendered.append(f"ERROR {path} {exc}")
            continue
        try:
            owner = pwd.getpwuid(st.st_uid).pw_name
        except KeyError:
            owner = str(st.st_uid)
        try:
            group = grp.getgrgid(st.st_gid).gr_name
        except KeyError:
            group = str(st.st_gid)
        mode = format(stat.S_IMODE(st.st_mode), "04o")[-3:]
        kind = (
            "dir"
            if stat.S_ISDIR(st.st_mode)
            else "symlink" if stat.S_ISLNK(st.st_mode) else "other"
        )
        acl = "unknown"
        if getfacl and kind == "dir":
            try:
                proc = subprocess.run(
                    [getfacl, "-cp", path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=5,
                    check=False,
                )
                if proc.returncode == 0:
                    extra = False
                    for raw in (proc.stdout or "").splitlines():
                        line = raw.strip()
                        if line.startswith("user:") and not line.startswith("user::"):
                            extra = True
                        if line.startswith("group:") and not line.startswith("group::"):
                            extra = True
                    acl = "extra" if extra else "none"
                else:
                    acl = "error"
            except Exception:
                acl = "error"
        rendered.append(f"{mode} {owner} {group} {path} acl={acl} type={kind}")
    return 0, "\n".join(rendered)


def _read_native_root_check(
    spec: dict,
    *,
    root_context: dict[str, object] | None,
    run_cmd_fn=None,
) -> tuple[int, str, str]:
    check_id = str(spec.get("id") or "")
    kind = str(spec.get("check_kind") or "")
    context = root_context or {}
    root_available = bool(context.get("root_available"))
    is_root = bool(context.get("is_root"))
    allow_mock_shell = run_cmd_fn is not None and run_cmd_fn is not run_cmd

    if check_id == "boot.uefi_active" and not allow_mock_shell:
        return (
            0,
            "ja" if _boot_uefi_active_native() else "nein",
            "python:/sys/firmware/efi",
        )

    if check_id == "boot.grub_password_protected" and not allow_mock_shell:
        try:
            enabled, path = _grub_password_protected_native()
            return 0, ("ja" if enabled else "nein"), f"python:{path}"
        except OSError as exc:
            return 1, str(exc), "python:/boot/grub/grub.cfg"

    if check_id == "auth.no_empty_password_accounts":
        if is_root:
            return 0, str(_count_empty_password_accounts_native()), "python:/etc/shadow"
        if root_available:
            rc, out, method = _run_privileged_read_command(
                str(spec.get("command") or ""),
                root_context=context,
                run_cmd_fn=run_cmd_fn,
                timeout=15,
            )
            return rc, out, f"{method}:/etc/shadow"
        if allow_mock_shell:
            rc, out = _run_read_command(
                str(spec.get("command") or ""), run_cmd_fn=run_cmd_fn
            )
            return rc, out, "shell:/etc/shadow"
        return 77, "", "python:/etc/shadow"

    if kind in {"sysctl", "rp_filter"}:
        key = str(spec.get("id") or "").split("sysctl.", 1)[-1]
        if allow_mock_shell:
            rc, out = _run_read_command(
                str(spec.get("command") or ""), run_cmd_fn=run_cmd_fn
            )
            return rc, out, f"shell:{_proc_sys_path_for_key(key)}"
        try:
            return (
                0,
                _read_sysctl_value_native(key),
                f"python:{_proc_sys_path_for_key(key)}",
            )
        except OSError as exc:
            return 1, str(exc), f"python:{_proc_sys_path_for_key(key)}"

    if check_id == "auth.pam_password_strength":
        if not allow_mock_shell:
            found, matches = _pam_password_strength_native()
            return (0 if found else 1), "\n".join(matches), "python:/etc/pam.d"
        command = str(spec.get("command") or "")
        if root_available:
            rc, out, method = _run_privileged_read_command(
                command,
                root_context=context,
                run_cmd_fn=run_cmd_fn,
                timeout=15,
            )
            return rc, out, f"{method}:/etc/pam.d"
        if allow_mock_shell:
            rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
            return rc, out, "shell:/etc/pam.d"
        rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
        return rc, out, "shell:/etc/pam.d"

    if check_id == "auth.unique_uid_gid" and not allow_mock_shell:
        try:
            return (
                0,
                str(_count_duplicate_uid_gid_native()),
                "python:/etc/passwd,/etc/group",
            )
        except OSError as exc:
            return 1, str(exc), "python:/etc/passwd,/etc/group"

    if check_id == "auth.home_permissions_checked" and not allow_mock_shell:
        rc, out = _home_permission_entries_native()
        return rc, out, "python:/home"

    if check_id == "pkg.critical_file_permissions_checked":
        if is_root:
            entries = _critical_file_entries_native()
            rendered = "\n".join(
                f"{entry['mode']} {entry['owner']} {entry['group']} {entry['path']}"
                for entry in entries
            )
            return 0, rendered, "python:stat:/etc/passwd,/etc/shadow,/etc/sudoers"
        command = str(spec.get("command") or "")
        if root_available:
            rc, out, method = _run_privileged_read_command(
                command,
                root_context=context,
                run_cmd_fn=run_cmd_fn,
                timeout=15,
            )
            return rc, out, f"{method}:stat:/etc/passwd,/etc/shadow,/etc/sudoers"
        if allow_mock_shell:
            rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
            return rc, out, "shell:stat:/etc/passwd,/etc/shadow,/etc/sudoers"
        return 77, "", "python:stat:/etc/passwd,/etc/shadow,/etc/sudoers"

    if check_id == "fw.ufw_rules_non_empty":
        command = str(spec.get("command") or "")
        if root_available and not allow_mock_shell:
            rc, out, method = _run_privileged_read_command(
                command,
                root_context=context,
                run_cmd_fn=run_cmd_fn,
                timeout=15,
            )
            return rc, out, f"{method}:ufw:status numbered"
        rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
        return rc, out, "shell:ufw:status numbered"

    if check_id == "fw.ufw_active":
        command = str(spec.get("command") or "")
        if root_available and not allow_mock_shell:
            rc, out, method = _run_privileged_read_command(
                command,
                root_context=context,
                run_cmd_fn=run_cmd_fn,
                timeout=15,
            )
            return rc, out, f"{method}:ufw:status"
        rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
        return rc, out, "shell:ufw:status"

    return None, "", ""


def _parse_ufw_status_state(status_text: str) -> str | None:
    for raw_line in str(status_text or "").splitlines():
        line = raw_line.strip().lower()
        if line == "status: active":
            return "active"
        if line == "status: inactive":
            return "inactive"
    return None


def _security_baseline_profile_name(app=None) -> str:
    active = _active_baseline_profile(app)
    if app is not None:
        for attr in (
            "security_baseline_profile",
            "security_profile",
            "system_security_profile",
        ):
            value = str(_app_value(app, attr, "") or "").strip()
            if value:
                return value
    return str(active.get("profile") or "Desktop / Development")


def _secure_boot_profile_mode(profile_name: str) -> str:
    text = str(profile_name or "").lower()
    if any(token in text for token in ("server", "härtung", "haertung", "hardening")):
        return "strict"
    if any(
        token in text for token in ("testlabor", "test lab", "dual-boot", "dual boot")
    ):
        return "document"
    return "document"


def _parse_secure_boot_state(text: str) -> dict[str, object]:
    low = str(text or "").lower()
    state = {
        "secure_boot_supported": None,
        "secure_boot_enabled": None,
        "platform_mode": None,
        "mokutil_available": True,
        "check_success": False,
        "check_error": None,
    }
    if "secureboot enabled" in low:
        state["secure_boot_supported"] = True
        state["secure_boot_enabled"] = True
        state["check_success"] = True
    elif "secureboot disabled" in low:
        state["secure_boot_supported"] = True
        state["secure_boot_enabled"] = False
        state["check_success"] = True

    if "platform is in setup mode" in low:
        state["platform_mode"] = "setup"
    elif "platform is in user mode" in low:
        state["platform_mode"] = "user"

    if any(
        signal in low
        for signal in (
            "efi variables are not supported",
            "efi variables are not supported on this system",
            "secure boot not supported",
        )
    ):
        state["secure_boot_supported"] = False
        state["secure_boot_enabled"] = None
        state["check_success"] = True

    if "mokutil" in low and ("not found" in low or "no such file" in low):
        state["mokutil_available"] = False
        state["check_error"] = str(text or "").strip() or "mokutil nicht verfuegbar"

    if (
        state["check_success"] is False
        and not state["check_error"]
        and str(text or "").strip()
    ):
        state["check_error"] = str(text or "").strip()
    return state


def _secure_boot_actual_text(state: dict[str, object]) -> str:
    supported = state.get("secure_boot_supported")
    enabled = state.get("secure_boot_enabled")
    platform_mode = state.get("platform_mode")
    if supported is False:
        return "nicht unterstuetzt oder kein UEFI-Zugriff"
    if enabled is True:
        parts = ["aktiviert"]
    elif enabled is False:
        parts = ["deaktiviert"]
    else:
        return "Pruefung fehlgeschlagen"
    if platform_mode == "setup":
        parts.append("Plattform im Setup Mode")
    elif platform_mode == "user":
        parts.append("Plattform im User Mode")
    return "; ".join(parts)


def _ufw_numbered_rule_lines(status_text: str) -> list[str]:
    return [
        raw_line.strip()
        for raw_line in str(status_text or "").splitlines()
        if re.match(r"^\[\s*[0-9]+\]", raw_line.strip())
    ]


def _parse_umask_findings(text: str) -> list[dict[str, str]]:
    findings = []
    pattern = re.compile(
        r"^[\t ]*(?P<keyword>UMASK|umask)[\t ]+(?P<value>[0-7]{3,4})(?:[\t ]|$)",
        re.IGNORECASE,
    )
    for raw_line in str(text or "").splitlines():
        source = "unbekannte Quelle"
        line = raw_line.strip()
        if ":" in raw_line:
            source, line = raw_line.split(":", 1)
            source = source.strip() or "unbekannte Quelle"
            line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        findings.append(
            {
                "source": source,
                "value": match.group("value"),
                "line": line,
            }
        )
    return findings


def _format_umask_sources(findings: list[dict[str, str]]) -> str:
    parts = []
    seen = set()
    for finding in findings:
        source = str(finding.get("source") or "unbekannte Quelle")
        value = str(finding.get("value") or "")
        item = f"{source}: {value}" if value else source
        if item in seen:
            continue
        seen.add(item)
        parts.append(item)
    return "\n".join(parts)


def _parse_home_permission_entries(text: str) -> tuple[list[dict[str, str]], list[str]]:
    entries = []
    errors = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("ERROR "):
            errors.append(line)
            continue
        parts = line.split()
        if len(parts) < 4:
            errors.append(f"Unerwartete Zeile: {line}")
            continue
        mode, owner, group, path = parts[:4]
        meta = {"acl": "unknown", "type": "dir"}
        for token in parts[4:]:
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            meta[key.strip()] = value.strip()
        entries.append(
            {
                "mode": mode[-3:],
                "owner": owner,
                "group": group,
                "path": path,
                "acl": meta.get("acl", "unknown"),
                "type": meta.get("type", "dir"),
            }
        )
    return entries, errors


def _home_owner_matches_path(entry: dict[str, str]) -> bool:
    path = str(entry.get("path") or "")
    owner = str(entry.get("owner") or "")
    if not path.startswith("/home/"):
        return False
    name = path.rstrip("/").rsplit("/", 1)[-1]
    return bool(name) and name == owner


def _evaluate_home_entry(entry: dict[str, str]) -> dict[str, str]:
    mode_text = str(entry.get("mode") or "")
    status = "Manuelle Pruefung erforderlich"

    try:
        mode_value = int(mode_text[-3:], 8)
    except ValueError:
        return {
            **entry,
            "status": status,
            "reason": "Der gelesene Modus ist nicht auswertbar.",
        }

    if str(entry.get("type") or "dir") != "dir":
        return {
            **entry,
            "status": status,
            "reason": "Der Home-Pfad ist kein normales Verzeichnis.",
        }

    if not _home_owner_matches_path(entry):
        return {
            **entry,
            "status": status,
            "reason": "Der Eigentuemer passt nicht plausibel zum Home-Verzeichnisnamen.",
        }

    if str(entry.get("acl") or "") == "extra":
        return {
            **entry,
            "status": status,
            "reason": "Zusaetzliche Benutzer- oder Gruppen-ACLs wurden erkannt.",
        }

    if str(entry.get("acl") or "") == "error":
        return {
            **entry,
            "status": status,
            "reason": "Vorhandene ACLs konnten nicht zuverlaessig gelesen werden.",
        }

    group_write = bool(mode_value & 0o020)
    other_write = bool(mode_value & 0o002)
    if group_write or other_write:
        return {
            **entry,
            "status": "Nicht erfuellt",
            "reason": "Das Home-Verzeichnis ist fuer Gruppe oder andere Benutzer beschreibbar.",
        }

    other_bits = mode_value & 0o007
    if other_bits:
        return {
            **entry,
            "status": status,
            "reason": "Andere Benutzer koennen das Home-Verzeichnis moeglicherweise betreten oder Inhalte lesen.",
        }

    return {
        **entry,
        "status": "Erfuellt",
        "reason": "Das Home-Verzeichnis ist fuer andere Benutzer nicht zugaenglich und besitzt keine Schreibrechte fuer Gruppe oder andere Benutzer.",
    }


def _format_home_entry_summary(entry: dict[str, str]) -> str:
    status_label = {
        "Erfuellt": "erfuellt",
        "Nicht erfuellt": "nicht erfuellt",
        "Manuelle Pruefung erforderlich": "manuelle Pruefung",
    }.get(str(entry.get("status") or ""), "manuelle Pruefung")
    suffix = ""
    if str(entry.get("acl") or "") == "extra":
        suffix = ", zusaetzliche ACLs vorhanden"
    return (
        f"{entry.get('path', '-')}: {entry.get('mode', '-')}{suffix} - {status_label}"
    )


def _parse_apt_upgradable_packages(text: str) -> tuple[list[dict[str, str]], list[str]]:
    packages = []
    ignored = []
    pattern = re.compile(
        r"^(?P<name_repo>\S+)\s+"
        r"(?P<candidate>\S+)\s+"
        r"(?P<architecture>\S+)"
        r"(?:\s+\[(?P<meta>.+)\])?$"
    )
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        low = line.lower()
        if low.startswith("listing"):
            continue
        if low.startswith(("warning:", "n:", "w:")):
            ignored.append(line)
            continue
        match = pattern.match(line)
        if not match:
            ignored.append(line)
            continue
        name_repo = match.group("name_repo")
        if "/" in name_repo:
            package_name, repository = name_repo.split("/", 1)
        else:
            package_name, repository = name_repo, ""
        installed_version = ""
        meta = match.group("meta") or ""
        meta_match = re.search(r"upgradable from:\s*([^\]]+)", meta, re.IGNORECASE)
        if meta_match:
            installed_version = meta_match.group(1).strip()
        packages.append(
            {
                "package_name": package_name,
                "repository": repository,
                "candidate_version": match.group("candidate"),
                "architecture": match.group("architecture"),
                "installed_version": installed_version,
            }
        )
    return packages, ignored


def _format_apt_upgradable_detail(packages: list[dict[str, str]]) -> str:
    if not packages:
        return "0 aktualisierbare APT-Pakete"
    lines = [f"{len(packages)} aktualisierbare APT-Pakete:"]
    for package in packages:
        lines.extend(
            [
                "",
                str(package.get("package_name") or "-"),
                f"  installiert: {package.get('installed_version') or '-'}",
                f"  verfuegbar: {package.get('candidate_version') or '-'}",
                f"  architektur: {package.get('architecture') or '-'}",
                f"  repository: {package.get('repository') or '-'}",
            ]
        )
    return "\n".join(lines)


APT_REPOSITORY_GUARD_FINDING_CODES = {
    "repo_no_signed_by",
    "repo_duplicate_source",
    "repo_duplicate_source_variant",
    "repo_legacy_distupgrade_file",
    "repo_disabled_file_present",
    "repo_backup_file_present",
    "repo_global_third_party_keyring",
    "repo_signed_by_missing_file",
}


def _baseline_repository_guard_service(app=None):
    existing = _app_value(app, "repository_guard_service", None)
    if existing is not None:
        return existing
    if RepositoryGuardService is None:
        return None
    source_patterns = []
    for pattern in (
        "/etc/apt/sources.list",
        "/etc/apt/sources.list.d/*.list",
        "/etc/apt/sources.list.d/*.sources",
    ):
        if any(token in pattern for token in "*?[]") or os.path.exists(pattern):
            source_patterns.append(pattern)
    return RepositoryGuardService(
        source_patterns=source_patterns,
        flatpak_available_fn=lambda: False,
    )


def _repository_guard_relevant_findings(scan_result: dict) -> list[dict]:
    return [
        item
        for item in list((scan_result or {}).get("findings") or [])
        if str(item.get("code") or "") in APT_REPOSITORY_GUARD_FINDING_CODES
    ]


def _format_repository_guard_detail(scan_result: dict) -> str:
    scan_result = dict(scan_result or {})
    lines = ["Analysierte Dateien:"]
    source_paths = sorted(
        {
            str(item.get("file_path") or "").strip()
            for item in list(scan_result.get("sources") or [])
            if str(item.get("file_path") or "").strip()
        }
    )
    if source_paths:
        lines.extend([f"- {path}" for path in source_paths])
    else:
        lines.append("- keine aktiven APT-Quelldateien erkannt")

    lines.append("")
    lines.append("Aktive Repositorys:")
    for item in list(scan_result.get("sources") or []):
        if str(item.get("kind") or "") != "apt" or not bool(item.get("enabled", True)):
            continue
        components = " ".join(list(item.get("components") or [])) or "-"
        signed_by = str(item.get("signed_by") or "-").strip() or "-"
        lines.append(
            f"- {item.get('uri', '-')} | suite={item.get('suite', '-')} | components={components} | signed-by={signed_by}"
        )

    auxiliary_files = list(scan_result.get("auxiliary_files") or [])
    if auxiliary_files:
        lines.append("")
        lines.append("Zusatzdateien:")
        for item in auxiliary_files:
            lines.append(f"- {item.get('file_path', '-')} [{item.get('state', '-')}]")

    global_keyrings = list(scan_result.get("global_keyrings") or [])
    if global_keyrings:
        lines.append("")
        lines.append("Globale Keyrings:")
        for item in global_keyrings:
            lines.append(f"- {item.get('file_path', '-')} [{item.get('scope', '-')}]")

    findings = _repository_guard_relevant_findings(scan_result)
    lines.append("")
    lines.append("Erkannte Auffaelligkeiten:")
    if findings:
        for item in findings:
            details = dict(item.get("details") or {})
            path = str(details.get("file_path") or "").strip()
            suffix = f" ({path})" if path else ""
            lines.append(
                f"- [{item.get('code', '-')}] {item.get('summary', '-')}{suffix}"
            )
    else:
        lines.append("- keine")
    return "\n".join(lines).strip()


CRITICAL_FILE_POLICY = {
    "/etc/passwd": {
        "allowed": {("644", "root", "root")},
        "max_mode": 0o644,
        "owner": "root",
        "group": "root",
        "label": "644 root:root",
    },
    "/etc/shadow": {
        "allowed": {
            ("640", "root", "shadow"),
            ("600", "root", "root"),
            ("600", "root", "shadow"),
            ("640", "root", "root"),
        },
        "max_mode": 0o640,
        "owner": "root",
        "group": None,
        "label": "640 root:shadow oder restriktiver Sonderfall",
    },
    "/etc/sudoers": {
        "allowed": {("440", "root", "root"), ("400", "root", "root")},
        "max_mode": 0o440,
        "owner": "root",
        "group": "root",
        "label": "440 root:root oder 400 root:root",
    },
}


def _parse_critical_file_entries(text: str) -> tuple[list[dict[str, str]], list[str]]:
    entries = []
    errors = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(("stat:", "ERROR ", "cannot stat", "Permission denied")):
            errors.append(line)
            continue
        parts = line.split(maxsplit=3)
        if len(parts) != 4:
            errors.append(f"Unerwartete Zeile: {line}")
            continue
        mode, owner, group, path = parts
        entries.append(
            {
                "mode": mode[-3:],
                "owner": owner,
                "group": group,
                "path": path,
            }
        )
    return entries, errors


def _critical_file_mode_value(mode_text: str) -> int | None:
    try:
        return int(str(mode_text)[-3:], 8)
    except ValueError:
        return None


def _evaluate_critical_file_entry(entry: dict[str, str]) -> dict[str, str]:
    path = str(entry.get("path") or "")
    mode = str(entry.get("mode") or "")
    owner = str(entry.get("owner") or "")
    group = str(entry.get("group") or "")
    policy = CRITICAL_FILE_POLICY.get(path)
    if policy is None:
        return {
            **entry,
            "status": "Manuelle Pruefung erforderlich",
            "reason": "Die Datei gehoert nicht zum bekannten Sollprofil.",
        }

    mode_value = _critical_file_mode_value(mode)
    if mode_value is None:
        return {
            **entry,
            "status": "Manuelle Pruefung erforderlich",
            "reason": "Der gelesene Dateimodus ist nicht auswertbar.",
        }

    current = (mode, owner, group)
    if current in policy["allowed"]:
        return {
            **entry,
            "status": "Erfuellt",
            "reason": "Die Datei entspricht einem bekannten sicheren Standardwert.",
            "expected_label": str(policy["label"]),
        }

    if owner != policy["owner"]:
        reason = "Der Eigentuemer weicht vom erwarteten Benutzer root ab."
    elif policy["group"] is not None and group != policy["group"]:
        reason = f"Die Gruppe weicht von {policy['group']} ab."
    elif path == "/etc/shadow" and mode_value & 0o004:
        reason = "Andere Benutzer besitzen Leserechte auf /etc/shadow."
    elif mode_value & 0o022:
        reason = "Die Datei ist fuer Gruppe oder andere Benutzer beschreibbar."
    elif mode_value > int(policy["max_mode"]):
        reason = "Die Dateirechte sind weiter gefasst als der sichere Sollwert."
    else:
        return {
            **entry,
            "status": "Manuelle Pruefung erforderlich",
            "reason": "Die Berechtigungen weichen vom bekannten Standard ab und muessen distributionsbezogen bewertet werden.",
            "expected_label": str(policy["label"]),
        }

    return {
        **entry,
        "status": "Nicht erfuellt",
        "reason": reason,
        "expected_label": str(policy["label"]),
    }


def _format_critical_file_summary(entry: dict[str, str]) -> str:
    marker = {
        "Erfuellt": "OK",
        "Nicht erfuellt": "FEHLER",
        "Manuelle Pruefung erforderlich": "PRUEFBEDARF",
    }.get(str(entry.get("status") or ""), "PRUEFBEDARF")
    path = str(entry.get("path") or "-")
    return (
        f"{path}: {entry.get('mode', '-')} "
        f"{entry.get('owner', '-')}:{entry.get('group', '-')} {marker}"
    )


def _baseline_result_from_spec(spec: dict) -> dict:
    result = dict(spec)
    result.update(
        {
            "actual": "-",
            "status": "Nicht geprueft",
            "reason": "Noch keine Baseline-Pruefung durchgeführt.",
            "lynis_reference": "",
            "check_error": "",
            "root_used": "Nein",
            "check_method": "",
            "value_source": str(spec.get("config_source") or "-"),
            "privilege_source": "unbekannt",
            "root_available": False,
            "requires_root_read": bool(
                spec.get("requires_root_read", _spec_requires_root_read(spec))
            ),
        }
    )
    return result


def _parse_int(text: str) -> int | None:
    try:
        return int(str(text or "").strip())
    except Exception:
        return None


def _shell_bool_actual(rc: int, text: str) -> str:
    clean = str(text or "").strip().lower()
    if rc == 0:
        if clean in {"ja", "yes", "true", "1", "active", "enabled"}:
            return "ja"
        if clean in {"nein", "no", "false", "0", "inactive", "disabled"}:
            return "nein"
        return "ja" if clean else "nein"
    return "nein"


def _baseline_summary_counts(rows: list[dict]) -> dict[str, int]:
    counts = {
        "ok": 0,
        "manual": 0,
        "deviation": 0,
        "not_met": 0,
        "not_applicable": 0,
        "root_required": 0,
        "check_error": 0,
        "not_checkable": 0,
    }
    for row in rows:
        status = str(row.get("status") or "")
        if status == "Erfuellt":
            counts["ok"] += 1
        elif status == "Empfehlung":
            counts["manual"] += 1
        elif status == "Manuelle Pruefung erforderlich":
            counts["manual"] += 1
        elif status == "Bewusste Abweichung":
            counts["deviation"] += 1
        elif status == "Nicht erfuellt":
            counts["not_met"] += 1
        elif status == "Nicht anwendbar":
            counts["not_applicable"] += 1
        elif status == "Root-Rechte erforderlich":
            counts["root_required"] += 1
        elif status == "Fehler bei der Pruefung":
            counts["check_error"] += 1
        elif status == "Nicht pruefbar":
            counts["not_checkable"] += 1
    return counts


def _baseline_status_sort_key(status: str) -> int:
    order = {
        "Nicht erfuellt": 0,
        "Empfehlung": 1,
        "Manuelle Pruefung erforderlich": 2,
        "Bewusste Abweichung": 2,
        "Root-Rechte erforderlich": 3,
        "Fehler bei der Pruefung": 4,
        "Nicht pruefbar": 5,
        "Nicht anwendbar": 6,
        "Erfuellt": 7,
        "Nicht geprueft": 8,
    }
    return int(order.get(str(status or ""), 99))


def _evaluate_baseline_check(
    spec: dict,
    *,
    run_cmd_fn=None,
    app=None,
    root_context: dict[str, object] | None = None,
) -> dict:
    result = _baseline_result_from_spec(spec)
    kind = str(spec.get("check_kind") or "")
    policy = str(spec.get("profile_policy") or "").strip().lower()
    if kind == "profile_advisory":
        result["actual"] = str(spec.get("advisory_actual") or "Profilhinweis")
        result["status"] = str(
            spec.get("advisory_status") or "Manuelle Pruefung erforderlich"
        )
        result["reason"] = str(
            spec.get("advisory_reason")
            or "Dieser Eintrag dient als profilbezogener Hinweis."
        )
        result["check_success"] = True
        result["check_method"] = "profile:advisory"
        result["value_source"] = str(
            spec.get("config_source") or "Aktives Baseline-Profil"
        )
        return result
    if kind == "apt_repository_guard":
        service = _baseline_repository_guard_service(app)
        if service is None:
            result["actual"] = "Pruefung fehlgeschlagen"
            _mark_check_error(
                result,
                reason="Die Repository-Pruefung ist lokal nicht verfuegbar.",
                error="RepositoryGuardService fehlt",
            )
            return result
        try:
            scan_result = service.scan()
        except Exception as exc:
            result["actual"] = "Pruefung fehlgeschlagen"
            _mark_check_error(
                result,
                reason="Die Repository-Pruefung konnte technisch nicht ausgefuehrt werden.",
                error=str(exc),
            )
            return result

        relevant_findings = _repository_guard_relevant_findings(scan_result)
        errors = list(scan_result.get("errors") or [])
        result["detail_output"] = _format_repository_guard_detail(scan_result)
        result["repository_guard_result"] = scan_result
        result["check_success"] = not errors
        result["check_error"] = "\n".join(
            str(item.get("message") or "")
            for item in errors
            if str(item.get("message") or "").strip()
        )
        result["actual"] = (
            "keine Auffaelligkeiten"
            if not relevant_findings
            else f"{len(relevant_findings)} Auffaelligkeit(en)"
        )
        if errors:
            _mark_check_error(
                result,
                reason="Die Repository-Pruefung konnte nicht vollstaendig ausgewertet werden.",
                error=result["check_error"],
            )
            return result
        if relevant_findings:
            result["status"] = "Empfehlung"
            result["reason"] = (
                "Mindestens eine APT-Fremdquelle besitzt keine explizite Signed-By-Zuordnung, ist mehrfach vorhanden oder es wurden alte/deaktivierte Repository-Reste erkannt."
            )
        else:
            result["status"] = "Erfuellt"
            result["reason"] = (
                "Es wurden keine fehlenden Signed-By-Angaben, doppelten aktiven Fremdquellen oder auffaelligen Upgrade-Reste erkannt."
            )
        result["value_source"] = str(spec.get("config_source") or "-")
        result["check_method"] = "python:RepositoryGuardService.scan"
        return result

    command = str(spec.get("command") or "")
    root_context = root_context or _detect_hardening_privilege_context(app)
    native_rc, native_out, native_method = _read_native_root_check(
        spec,
        root_context=root_context,
        run_cmd_fn=run_cmd_fn,
    )
    if native_rc is None:
        rc, out = _run_read_command(command, run_cmd_fn=run_cmd_fn)
        check_method = "shell:bash -lc"
        value_source = str(spec.get("config_source") or "-")
    else:
        rc, out = native_rc, native_out
        check_method = native_method
        value_source = (
            native_method.split(":", 1)[-1]
            if native_method
            else str(spec.get("config_source") or "-")
        )
    text = str(out or "").strip()
    low = text.lower()
    expected = str(spec.get("expected") or "")
    _apply_baseline_diagnostics(
        result,
        root_context=root_context,
        check_method=check_method,
        value_source=value_source,
    )
    if rc == 77 and _spec_requires_root_read(spec):
        result["actual"] = "Root-Rechte fehlen"
        _mark_root_required(
            result,
            reason=_spec_root_required_reason(spec),
        )
        return result

    if kind == "sysctl":
        actual = text if rc == 0 and text else "unbekannt"
        result["actual"] = actual
        if rc != 0:
            _mark_check_error(
                result,
                reason="Der sysctl-Wert konnte nicht lesend ermittelt werden.",
                error=text,
            )
        elif actual == expected:
            result["status"] = "Erfuellt"
            result["reason"] = (
                "Der gelesene sysctl-Wert entspricht dem Desktop-/Development-Soll."
            )
        elif _sysctl_config_source_contains_expected(spec, expected):
            ufw_hint = _sysctl_ufw_override_hint(spec, expected)
            result["status"] = "Nicht erfuellt"
            if ufw_hint:
                result["reason"] = (
                    "Der gelesene sysctl-Wert weicht vom dokumentierten Soll ab, "
                    "obwohl die NetMon-Drop-in-Datei den Sollwert enthaelt. "
                    f"{ufw_hint}"
                )
            else:
                result["reason"] = (
                    "Der gelesene sysctl-Wert weicht vom dokumentierten Soll ab, "
                    "obwohl die NetMon-Drop-in-Datei den Sollwert enthaelt. "
                    "Bitte sysctl --system, Boot-Anwendung oder spaetere Ueberschreibungen pruefen."
                )
        else:
            result["status"] = "Nicht erfuellt"
            result["reason"] = (
                "Der gelesene sysctl-Wert weicht vom dokumentierten Soll ab."
            )
        return result

    if kind == "rp_filter":
        actual = text if rc == 0 and text else "unbekannt"
        result["actual"] = actual
        ufw_hint = _sysctl_ufw_override_hint(spec, expected)
        if policy == "strict_rp_filter":
            result["lynis_reference"] = (
                "Im Server-/Haertungsprofil bewertet NetMon strict mode 1 als Soll. "
                "Wert 2 bleibt als kompatible, aber weniger strikte Abweichung sichtbar."
            )
        else:
            result["lynis_reference"] = (
                "Lynis erwartet in manchen Szenarien strict mode 1. "
                "NetMon behandelt 2 fuer VPN-/WireGuard-/Multi-Interface-Systeme als profilgerecht."
            )
        if rc != 0:
            _mark_check_error(
                result,
                reason="Der rp_filter-Wert konnte nicht lesend ermittelt werden.",
                error=text,
            )
        elif policy == "strict_rp_filter" and actual == "1":
            result["status"] = "Erfuellt"
            result["reason"] = (
                "rp_filter=1 entspricht im Server-/Haertungsprofil dem strikten Soll."
            )
        elif policy == "strict_rp_filter" and actual == "2":
            result["status"] = "Bewusste Abweichung"
            result["reason"] = (
                "rp_filter=2 ist kompatibler, weicht im Server-/Haertungsprofil aber bewusst vom strikten Soll 1 ab."
            )
        elif actual == "2":
            result["status"] = "Erfuellt"
            result["reason"] = (
                "rp_filter=2 ist im Desktop-/Development-Profil bewusst zulaessig."
            )
        elif actual == "1":
            result["status"] = "Bewusste Abweichung"
            result["reason"] = (
                "Strict mode 1 kann fuer einfache Single-Interface-Systeme bewusst gesetzt sein."
            )
        else:
            result["status"] = "Nicht erfuellt"
            result["reason"] = (
                "Der rp_filter-Wert passt weder zum Profil-Soll noch zu einer typischen Ausnahme."
            )
        if ufw_hint and result["status"] != "Fehler bei der Pruefung":
            result["reason"] = f"{result['reason']} {ufw_hint}"
        return result

    if kind == "secure_boot":
        state = _parse_secure_boot_state(text)
        profile_name = _security_baseline_profile_name(app)
        profile_mode = _secure_boot_profile_mode(profile_name)
        result.update(state)
        result["profile"] = profile_name
        result["actual"] = _secure_boot_actual_text(state)
        result["lynis_reference"] = (
            "Secure Boot deaktiviert bedeutet, dass eine Schutzschicht gegen nicht vertrauenswuerdige Boot-Komponenten nicht aktiv ist. Die Gesamteinordnung haengt vom Systemprofil und Einsatzkontext ab."
        )

        if rc != 0 or state.get("check_error") and not state.get("check_success"):
            if state.get("secure_boot_supported") is False:
                result["status"] = "Nicht anwendbar"
                result["reason"] = (
                    "Der Secure-Boot-Status konnte auf diesem System nicht als anwendbar bestaetigt werden. Moeglicherweise wurde das System im Legacy-BIOS-Modus gestartet oder die Firmware stellt keine Secure-Boot-Informationen bereit."
                )
            else:
                result["actual"] = "Pruefung fehlgeschlagen"
                result["status"] = "Fehler bei der Pruefung"
                result["check_success"] = False
                result["check_error"] = (
                    state.get("check_error") or text or f"mokutil rc={rc}"
                )
                result["reason"] = (
                    "Die Secure-Boot-Pruefung konnte technisch nicht zuverlaessig abgeschlossen werden."
                )
            return result

        if state.get("secure_boot_supported") is False:
            result["status"] = "Nicht anwendbar"
            result["reason"] = (
                "Der Secure-Boot-Status konnte auf diesem System nicht als anwendbar bestaetigt werden. Moeglicherweise wurde das System im Legacy-BIOS-Modus gestartet oder die Firmware stellt keine Secure-Boot-Informationen bereit."
            )
        elif state.get("secure_boot_enabled") is True:
            result["status"] = "Erfuellt"
            result["severity"] = "OK"
            result["reason"] = (
                "Secure Boot ist aktiviert. Die Firmware prueft beim Systemstart die Signaturen unterstuetzter Boot-Komponenten."
            )
        elif state.get("secure_boot_enabled") is False:
            if profile_mode == "strict":
                result["status"] = "Nicht erfuellt"
                result["severity"] = "Mittel"
            else:
                result["status"] = "Manuelle Pruefung erforderlich"
                result["severity"] = "Hinweis"
            if state.get("platform_mode") == "setup":
                result["reason"] = (
                    "Secure Boot ist deaktiviert und die UEFI-Plattform befindet sich im Setup Mode. Dies weist typischerweise darauf hin, dass kein aktiver Platform Key vorhanden ist. Der Zustand kann bewusst gewaehlt oder durch zurueckgesetzte Secure-Boot-Schluessel entstanden sein."
                )
            elif profile_mode == "strict":
                result["reason"] = (
                    "Secure Boot ist deaktiviert. Das gewaehlte Server- oder Haertungsprofil setzt aktivierten Secure Boot voraus."
                )
            else:
                result["reason"] = (
                    "Secure Boot ist deaktiviert. Im Desktop- oder Entwicklungsprofil ist dies nicht automatisch kritisch, sollte aber als bewusste Konfigurationsentscheidung dokumentiert werden."
                )
        else:
            result["actual"] = "Pruefung fehlgeschlagen"
            result["status"] = "Fehler bei der Pruefung"
            result["check_success"] = False
            result["check_error"] = (
                state.get("check_error") or text or "Unerwartete mokutil-Ausgabe"
            )
            result["reason"] = (
                "Die Secure-Boot-Ausgabe konnte nicht eindeutig ausgewertet werden."
            )
        return result

    if kind == "ufw_active":
        if rc != 0 and not text:
            result["actual"] = "unbekannt"
            _mark_check_error(
                result,
                reason="UFW konnte nicht lesend abgefragt werden.",
            )
        else:
            status_state = _parse_ufw_status_state(text)
            if status_state is None:
                if _permission_error_text(text):
                    if root_context.get("root_available"):
                        result["actual"] = "Pruefung fehlgeschlagen"
                        _mark_check_error(
                            result,
                            reason="Der UFW-Status konnte trotz vorhandener privilegierter Session nicht gelesen werden.",
                            error=text,
                        )
                    else:
                        result["actual"] = "Root-Rechte fehlen"
                        _mark_root_required(
                            result,
                            reason="Das Lesen von `ufw status` benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                            error=text,
                        )
                else:
                    result["actual"] = "unbekannt"
                    _mark_check_error(
                        result,
                        reason="Der UFW-Status konnte nicht eindeutig aus der englischen Ausgabe gelesen werden.",
                        error=text,
                    )
            else:
                is_active = status_state == "active"
                result["actual"] = "ja" if is_active else "nein"
                result["status"] = "Erfuellt" if is_active else "Nicht erfuellt"
                result["reason"] = (
                    "UFW meldet einen aktiven Firewall-Status."
                    if is_active
                    else "UFW meldet einen inaktiven Firewall-Status."
                )
        return result

    if kind == "ufw_rules_non_empty":
        rule_lines = _ufw_numbered_rule_lines(text)
        rule_count = len(rule_lines)
        status_state = _parse_ufw_status_state(text)
        result["ufw_active"] = status_state == "active"
        result["rule_count"] = rule_count
        result["rules_detected"] = rule_count > 0
        result["check_error"] = None
        result["detail_output"] = "\n".join(
            [f"Erkannte Regeln: {rule_count}", *rule_lines]
        )

        if rc != 0:
            error_text = text or f"ufw status numbered rc={rc}"
            if _permission_error_text(error_text):
                if root_context.get("root_available"):
                    result["actual"] = "Pruefung fehlgeschlagen"
                    _mark_check_error(
                        result,
                        reason="Der UFW-Regelsatz konnte trotz vorhandener privilegierter Session nicht gelesen werden.",
                        error=error_text,
                    )
                else:
                    result["actual"] = "Root-Rechte fehlen"
                    _mark_root_required(
                        result,
                        reason="Das Lesen von `ufw status numbered` benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                        error=error_text,
                    )
            else:
                result["actual"] = "Pruefung fehlgeschlagen"
                _mark_check_error(
                    result,
                    reason="Der UFW-Regelsatz konnte technisch nicht zuverlaessig gelesen werden.",
                    error=error_text,
                )
            if text:
                result["detail_output"] = "\n".join(
                    [f"Erkannte Regeln: {rule_count}", text]
                )
        elif status_state == "inactive":
            result["actual"] = "UFW nicht aktiv"
            result["status"] = "Nicht erfuellt"
            result["ufw_active"] = False
            result["reason"] = (
                "UFW ist nicht aktiv. Daher konnte kein aktiver benutzerdefinierter Regelsatz bestaetigt werden."
            )
        elif status_state != "active":
            result["actual"] = "Pruefung fehlgeschlagen"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["ufw_active"] = None
            result["check_error"] = "UFW-Statuszeile fehlt oder ist unerwartet."
            result["reason"] = (
                "Der UFW-Aktivstatus konnte aus der englischen Ausgabe nicht eindeutig gelesen werden."
            )
            if text:
                result["detail_output"] = "\n".join(
                    [f"Erkannte Regeln: {rule_count}", text]
                )
        elif rule_count > 0:
            result["actual"] = "ja"
            result["status"] = "Erfuellt"
            result["reason"] = (
                "UFW ist aktiv und enthaelt konkrete benutzerdefinierte Regeln."
            )
        else:
            result["actual"] = "nein"
            if policy == "manual_if_missing":
                result["status"] = "Manuelle Pruefung erforderlich"
                result["reason"] = (
                    "UFW ist aktiv, es wurden jedoch keine zusaetzlichen Regeln erkannt. Im aktiven Profil ist das kein pauschaler Fehler, sondern muss gegen Rolle, Dienste und Netzpfade manuell bewertet werden."
                )
            else:
                result["status"] = "Nicht erfuellt"
                result["reason"] = (
                    "UFW ist aktiv, es wurden jedoch keine konkreten benutzerdefinierten Regeln erkannt. Fuer diesen Check gilt der Sollwert damit als nicht erfuellt; Default-Richtlinien oder alternative Firewall-Konfigurationen koennen zusaetzlich separat bewertet werden."
                )
        return result

    if kind == "systemctl_active":
        if rc != 0 and not text:
            result["actual"] = "unbekannt"
            _mark_check_error(
                result,
                reason="Der Dienststatus konnte nicht lesend abgefragt werden.",
            )
        else:
            is_active = low.startswith("active")
            result["actual"] = "ja" if is_active else (text or "nein")
            if is_active:
                result["status"] = "Erfuellt"
                result["reason"] = "Der Dienst meldet den Zustand aktiv."
            elif policy == "recommended":
                result["status"] = "Empfehlung"
                result["reason"] = (
                    "Der Dienst ist im aktiven Profil empfohlen, aber nicht zwingend vorgeschrieben."
                )
            elif policy == "manual_if_missing":
                result["status"] = "Manuelle Pruefung erforderlich"
                result["reason"] = (
                    "Der Dienst ist nicht aktiv und muss im Profilkontext manuell bewertet werden."
                )
            else:
                result["status"] = "Nicht erfuellt"
                result["reason"] = "Der Dienst meldet keinen aktiven Zustand."
        return result

    if kind == "package_installed":
        installed = rc == 0 and "install ok installed" in low
        result["actual"] = "ja" if installed else "nein"
        if installed:
            result["status"] = "Erfuellt"
            result["reason"] = "Das Paket ist installiert."
        elif policy == "recommended":
            result["status"] = "Empfehlung"
            result["reason"] = (
                "Das Paket ist im aktiven Profil empfohlen, aber nicht zwingend vorgeschrieben."
            )
        elif policy == "manual_if_missing":
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Das Paket fehlt und muss im Kontext des aktiven Profils manuell bewertet werden."
            )
        else:
            result["status"] = "Nicht erfuellt"
            result["reason"] = "Das Paket ist nicht installiert."
        return result

    if kind == "package_optional":
        installed = rc == 0 and "install ok installed" in low
        result["actual"] = "ja" if installed else "nein"
        result["status"] = "Erfuellt" if installed else "Nicht anwendbar"
        result["reason"] = (
            "Das optionale Paket ist installiert."
            if installed
            else "Das Paket ist in diesem Profil optional und fehlt daher nicht automatisch kritisch."
        )
        return result

    if kind == "apparmor_active":
        if rc == 0:
            result["actual"] = "ja"
            result["status"] = "Erfuellt"
            result["reason"] = "AppArmor meldet einen aktiven Zustand."
        elif text:
            result["actual"] = text
            result["status"] = "Nicht erfuellt"
            result["reason"] = "AppArmor meldet keinen aktiven Zustand."
        else:
            result["actual"] = "unbekannt"
            _mark_check_error(
                result,
                reason="AppArmor konnte nicht lesend abgefragt werden.",
            )
        return result

    if kind == "umask_value":
        findings = _parse_umask_findings(text)
        result["detected_sources"] = [
            str(item.get("source") or "unbekannte Quelle") for item in findings
        ]
        result["detected_values"] = [
            str(item.get("value") or "") for item in findings if item.get("value")
        ]
        sources_summary = _format_umask_sources(findings)
        if sources_summary:
            result["config_source"] = sources_summary
            result["raw_output"] = sources_summary

        if rc not in {0, 1}:
            result["actual"] = "Pruefung fehlgeschlagen"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Die UMASK-Pruefung konnte technisch nicht zuverlaessig abgeschlossen werden."
            )
            if text:
                result["raw_output"] = text
            return result

        if not findings:
            result["actual"] = "Nicht gesetzt"
            result["status"] = "Nicht erfuellt"
            result["reason"] = (
                "In den geprueften Konfigurationsquellen wurde keine Standard-UMASK gefunden."
            )
            return result

        unique_values = sorted({str(item.get("value") or "") for item in findings})
        if len(unique_values) > 1:
            result["actual"] = "Mehrere Werte gefunden"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Mehrere UMASK-Einstellungen wurden gefunden. Welche Einstellung effektiv gilt, haengt von Anmeldeart, Shell, PAM-Konfiguration und Ladereihenfolge ab."
            )
            result["conflict_detected"] = True
            return result

        actual = unique_values[0]
        result["actual"] = actual
        result["effective_value"] = actual
        if actual == expected:
            result["status"] = "Erfuellt"
            result["reason"] = (
                "Eine Standard-UMASK von 027 wurde in den geprueften Quellen gefunden."
            )
        else:
            result["status"] = "Nicht erfuellt"
            result["reason"] = (
                "Es wurde eine Standard-UMASK gefunden, sie entspricht jedoch nicht dem erwarteten Wert 027."
            )
        return result

    if kind == "home_permissions":
        entries, errors = _parse_home_permission_entries(text)
        evaluated = [_evaluate_home_entry(entry) for entry in entries]
        result["home_entries"] = evaluated
        result["check_error"] = "\n".join(errors) if errors else None
        result["detail_output"] = "\n".join(
            [_format_home_entry_summary(entry) for entry in evaluated] + errors
        )

        if rc != 0 and not evaluated:
            result["actual"] = "Pruefung fehlgeschlagen"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Die Home-Verzeichnisrechte konnten technisch nicht zuverlaessig gelesen werden."
            )
            return result

        if not evaluated:
            result["actual"] = "Keine Home-Verzeichnisse gefunden"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Unter /home wurden keine auswertbaren Home-Verzeichnisse gefunden."
            )
            return result

        counts = {
            "Erfuellt": sum(1 for entry in evaluated if entry["status"] == "Erfuellt"),
            "Manuelle Pruefung erforderlich": sum(
                1
                for entry in evaluated
                if entry["status"] == "Manuelle Pruefung erforderlich"
            ),
            "Nicht erfuellt": sum(
                1 for entry in evaluated if entry["status"] == "Nicht erfuellt"
            ),
        }
        if len(evaluated) == 1:
            only = evaluated[0]
            actual = str(only.get("mode") or "-")
            if str(only.get("acl") or "") == "extra":
                actual = f"{actual}, zusaetzliche ACLs vorhanden"
            result["actual"] = actual
            result["config_source"] = str(only.get("path") or "/home/*")
            result["reason"] = str(only.get("reason") or "")
        else:
            result["actual"] = (
                f"{len(evaluated)} Home-Verzeichnisse geprueft; "
                f"{counts['Erfuellt']} erfuellt; "
                f"{counts['Manuelle Pruefung erforderlich']} manuell; "
                f"{counts['Nicht erfuellt']} nicht erfuellt"
            )
            result["config_source"] = "\n".join(
                str(entry.get("path") or "-") for entry in evaluated
            )

        if counts["Nicht erfuellt"]:
            result["status"] = "Nicht erfuellt"
            if len(evaluated) > 1:
                result["reason"] = (
                    "Mindestens ein Home-Verzeichnis ist fuer Gruppe oder andere Benutzer beschreibbar."
                )
        elif counts["Manuelle Pruefung erforderlich"] or errors:
            result["status"] = "Manuelle Pruefung erforderlich"
            if len(evaluated) > 1:
                result["reason"] = (
                    "Mindestens ein Home-Verzeichnis benoetigt eine bewusste manuelle Bewertung."
                )
        else:
            result["status"] = "Erfuellt"
            if len(evaluated) > 1:
                result["reason"] = (
                    "Alle geprueften Home-Verzeichnisse besitzen keine Schreibrechte fuer Gruppe oder andere Benutzer und sind fuer andere Benutzer nicht zugaenglich."
                )
        return result

    if kind == "apt_upgradable":
        packages, ignored_lines = _parse_apt_upgradable_packages(text)
        count = len(packages)
        result["upgradable_count"] = count
        result["upgradable_packages"] = packages
        result["check_success"] = rc == 0
        result["check_error"] = None
        result["security_relevance_known"] = False
        result["detail_output"] = _format_apt_upgradable_detail(packages)

        if rc != 0:
            result["actual"] = "Pruefung fehlgeschlagen"
            result["status"] = "Manuelle Pruefung erforderlich"
            result["check_success"] = False
            result["check_error"] = text or f"apt list --upgradable rc={rc}"
            result["reason"] = (
                "Die APT-Pruefung konnte technisch nicht zuverlaessig abgeschlossen werden."
            )
            if text:
                result["detail_output"] = text
            return result

        if ignored_lines and not packages:
            meaningful = [
                line
                for line in ignored_lines
                if not line.lower().startswith(("warning:", "n:", "w:"))
            ]
            if meaningful:
                result["actual"] = "Pruefung fehlgeschlagen"
                result["status"] = "Manuelle Pruefung erforderlich"
                result["check_success"] = False
                result["check_error"] = "\n".join(meaningful)
                result["reason"] = (
                    "Die APT-Ausgabe konnte nicht eindeutig als Paketliste ausgewertet werden."
                )
                result["detail_output"] = "\n".join(ignored_lines)
                return result

        result["actual"] = str(count)
        if count == 0:
            result["status"] = "Erfuellt"
            result["reason"] = "Es wurden keine aktualisierbaren APT-Pakete gefunden."
        else:
            result["status"] = "Manuelle Pruefung erforderlich"
            if count == 1:
                result["reason"] = (
                    "Es wurde 1 aktualisierbares APT-Paket gefunden. Ob dieses Update sicherheitsrelevant, funktional oder optional ist, muss anhand der Paketinformationen bewertet werden."
                )
            else:
                result["reason"] = (
                    f"Es wurden {count} aktualisierbare APT-Pakete gefunden. Ob diese Updates sicherheitsrelevant, funktional oder optional sind, muss anhand der Paketinformationen bewertet werden."
                )
        return result

    if kind == "critical_file_permissions":
        entries, errors = _parse_critical_file_entries(text)
        evaluated = [_evaluate_critical_file_entry(entry) for entry in entries]
        seen_paths = {str(entry.get("path") or "") for entry in evaluated}
        missing_paths = [
            path for path in CRITICAL_FILE_POLICY.keys() if path not in seen_paths
        ]
        for path in missing_paths:
            errors.append(f"Datei nicht gefunden: {path}")
        result["critical_file_entries"] = evaluated
        result["check_error"] = "\n".join(errors) if errors else None
        result["detail_output"] = "\n".join(
            [_format_critical_file_summary(entry) for entry in evaluated] + errors
        )

        if rc != 0 and not evaluated:
            if not root_context.get("root_available"):
                result["actual"] = "Root-Rechte fehlen"
                _mark_root_required(
                    result,
                    reason="Die Pruefung der kritischen Systemdateien benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                    error=text,
                )
            else:
                result["actual"] = "Pruefung fehlgeschlagen"
                _mark_check_error(
                    result,
                    reason="Die kritischen Systemdateirechte konnten technisch nicht zuverlaessig gelesen werden.",
                    error=text,
                )
            return result

        if errors and not evaluated and not root_context.get("root_available"):
            result["actual"] = "Root-Rechte fehlen"
            _mark_root_required(
                result,
                reason="Die Pruefung der kritischen Systemdateien benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                error="\n".join(errors),
            )
            return result
        if (
            errors
            and any(_permission_error_text(item) for item in errors)
            and not root_context.get("root_available")
        ):
            result["actual"] = "Root-Rechte fehlen"
            _mark_root_required(
                result,
                reason="Mindestens eine kritische Systemdatei ist ohne Administratorrechte nicht lesbar.",
                error="\n".join(errors),
            )
            return result
        if errors and any(_permission_error_text(item) for item in errors):
            result["actual"] = "Pruefung fehlgeschlagen"
            _mark_check_error(
                result,
                reason="Mindestens eine kritische Systemdatei konnte trotz vorhandener Rechte nicht gelesen werden.",
                error="\n".join(errors),
            )
            return result

        if not evaluated:
            result["actual"] = "Pruefung fehlgeschlagen"
            _mark_check_error(
                result,
                reason="Die stat-Ausgabe enthielt keine auswertbaren Dateieintraege.",
                error=text,
            )
            return result

        if errors:
            result["actual"] = (
                "Datei nicht gefunden" if missing_paths else "Pruefung fehlgeschlagen"
            )
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Mindestens eine kritische Systemdatei konnte nicht zuverlaessig bewertet werden."
            )
            return result

        failed = [entry for entry in evaluated if entry["status"] == "Nicht erfuellt"]
        manual = [
            entry
            for entry in evaluated
            if entry["status"] == "Manuelle Pruefung erforderlich"
        ]
        if failed:
            result["actual"] = "\n".join(
                f"{entry.get('path')}: {entry.get('mode')} {entry.get('owner')}:{entry.get('group')}"
                for entry in failed
            )
            result["status"] = "Nicht erfuellt"
            result["reason"] = "; ".join(
                f"{entry.get('path')}: {entry.get('reason')}" for entry in failed
            )
        elif manual:
            result["actual"] = "\n".join(
                f"{entry.get('path')}: {entry.get('mode')} {entry.get('owner')}:{entry.get('group')}"
                for entry in manual
            )
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = "; ".join(
                f"{entry.get('path')}: {entry.get('reason')}" for entry in manual
            )
        else:
            result["actual"] = "Alle geprueften Dateien entsprechen den Sollwerten"
            result["status"] = "Erfuellt"
            result["reason"] = (
                "Eigentuemer, Gruppen und Dateirechte der kritischen Systemdateien entsprechen bekannten sicheren Standardkonfigurationen."
            )
        return result

    if kind in {"shell_bool", "grep_exists"}:
        actual = _shell_bool_actual(rc, text)
        result["actual"] = actual
        if rc != 0:
            if str(
                spec.get("id") or ""
            ) == "boot.grub_password_protected" and _missing_file_text(text):
                result["actual"] = "GRUB-Konfiguration nicht gefunden"
                result["status"] = "Nicht anwendbar"
                result["reason"] = (
                    "Es wurde keine lesbare GRUB-Konfiguration an den erwarteten Standardpfaden gefunden. Das System verwendet moeglicherweise einen anderen Bootloader oder eine abweichende GRUB-Struktur."
                )
                result["detail_output"] = text
            elif _permission_error_text(text):
                if root_context.get("root_available"):
                    _mark_check_error(
                        result,
                        reason="Die Pruefung konnte trotz vorhandener Rechte nicht erfolgreich gelesen werden.",
                        error=text,
                    )
                else:
                    _mark_root_required(
                        result,
                        reason="Diese Pruefung benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                        error=text,
                    )
            elif text and actual == "nein" and kind == "grep_exists":
                result["status"] = "Nicht erfuellt"
                result["reason"] = (
                    "Die lesende Pruefung hat den erwarteten Zustand nicht bestaetigt."
                )
            elif text:
                result["actual"] = "Pruefung fehlgeschlagen"
                _mark_check_error(
                    result,
                    reason="Die lesende Pruefung konnte technisch nicht zuverlaessig gelesen werden.",
                    error=text,
                )
            else:
                if actual == expected:
                    result["status"] = "Erfuellt"
                    result["reason"] = (
                        "Die lesende Pruefung hat den erwarteten Zustand bestaetigt."
                    )
                elif policy == "recommended":
                    result["status"] = "Empfehlung"
                    result["reason"] = (
                        "Der gepruefte Zustand ist im aktiven Profil empfohlen, aber nicht zwingend vorgeschrieben."
                    )
                elif policy == "manual_if_missing":
                    result["status"] = "Manuelle Pruefung erforderlich"
                    result["reason"] = (
                        "Der gepruefte Zustand weicht vom Profilhinweis ab und muss manuell bewertet werden."
                    )
                else:
                    result["status"] = "Nicht erfuellt"
                    result["reason"] = (
                        "Die lesende Pruefung hat den erwarteten Zustand nicht bestaetigt."
                    )
        else:
            if actual == expected:
                result["status"] = "Erfuellt"
                result["reason"] = (
                    "Die lesende Pruefung hat den erwarteten Zustand bestaetigt."
                )
            elif policy == "recommended":
                result["status"] = "Empfehlung"
                result["reason"] = (
                    "Der gepruefte Zustand ist im aktiven Profil empfohlen, aber nicht zwingend vorgeschrieben."
                )
            elif policy == "manual_if_missing":
                result["status"] = "Manuelle Pruefung erforderlich"
                result["reason"] = (
                    "Der gepruefte Zustand weicht vom Profilhinweis ab und muss manuell bewertet werden."
                )
            else:
                result["status"] = "Nicht erfuellt"
                result["reason"] = (
                    "Die lesende Pruefung hat den erwarteten Zustand nicht bestaetigt."
                )
        return result

    if kind == "numeric_zero":
        count = _parse_int(text)
        result["actual"] = str(count) if count is not None else (text or "unbekannt")
        if count is None:
            if (
                not text
                and not root_context.get("root_available")
                and str(spec.get("id") or "") == "auth.no_empty_password_accounts"
            ):
                result["actual"] = "Root-Rechte fehlen"
                _mark_root_required(
                    result,
                    reason="Das Lesen von /etc/shadow benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                )
            elif _permission_error_text(text):
                if root_context.get("root_available"):
                    _mark_check_error(
                        result,
                        reason="Die lesende Pruefung lieferte trotz vorhandener Rechte keinen auswertbaren Zahlenwert.",
                        error=text,
                    )
                else:
                    _mark_root_required(
                        result,
                        reason="Diese Pruefung benoetigt Administratorrechte, die NetMon aktuell nicht besitzt.",
                        error=text,
                    )
            else:
                _mark_check_error(
                    result,
                    reason="Die lesende Pruefung lieferte keinen auswertbaren Zahlenwert.",
                    error=text,
                )
        elif count == 0:
            result["status"] = "Erfuellt"
            result["reason"] = "Die lesende Pruefung ergab keine Auffaelligkeiten."
        else:
            result["status"] = "Nicht erfuellt"
            result["reason"] = (
                "Die lesende Pruefung ergab eine oder mehrere Auffaelligkeiten."
            )
        return result

    if kind == "manual_zero":
        count = _parse_int(text)
        result["actual"] = str(count) if count is not None else (text or "unbekannt")
        if count is None:
            _mark_check_error(
                result,
                reason="Die lesende Pruefung lieferte keinen auswertbaren Zahlenwert.",
                error=text,
            )
        elif count == 0:
            result["status"] = "Erfuellt"
            result["reason"] = "Es wurden keine auffaelligen Eintraege gemeldet."
        else:
            result["status"] = "Manuelle Pruefung erforderlich"
            result["reason"] = (
                "Es wurden Eintraege gefunden, die im Einsatzkontext manuell bewertet werden muessen."
            )
        return result

    if kind == "manual_review":
        rendered = text or "Keine lesbaren Details zurückgegeben."
        lines = [line for line in rendered.splitlines() if str(line).strip()]
        result["actual"] = (
            f"{len(lines)} Eintrag(e) gelesen" if lines else "keine Eintraege"
        )
        result["status"] = "Manuelle Pruefung erforderlich"
        result["reason"] = (
            "Die technischen Rohdaten wurden gelesen, die Sicherheitsbewertung bleibt bewusst manuell."
        )
        result["detail_output"] = rendered
        return result

    return result


def _baseline_detail_text(item: dict) -> str:
    return "\n".join(
        [
            f"{item.get('detail_title_label', 'Titel')}: {item.get('title', '-')}",
            f"{item.get('detail_group_label', 'Gruppe')}: {item.get('group', '-')}",
            f"{item.get('detail_status_label', 'Status')}: {item.get('status', '-')}",
            f"{item.get('detail_expected_label', 'Sollwert')}: {item.get('expected', '-')}",
            f"{item.get('detail_actual_label', 'Ist-Wert')}: {item.get('actual', '-')}",
            "",
            f"{item.get('detail_description_label', 'Beschreibung')}:",
            str(item.get("description") or "-"),
            "",
            f"{item.get('detail_reason_label', 'Begruendung')}:",
            str(item.get("reason") or "-"),
            "",
            f"{item.get('detail_benefit_label', 'Sicherheitsnutzen')}:",
            str(item.get("security_benefit") or "-"),
            "",
            f"{item.get('detail_side_effects_label', 'Moegliche Nebenwirkungen')}:",
            str(item.get("side_effects") or "-"),
            "",
            f"{item.get('detail_exceptions_label', 'Ausnahmen')}:",
            str(item.get("exceptions") or "-"),
            "",
            f"{item.get('detail_profiles_label', 'Profil-Ziele')}:",
            ", ".join(item.get("profile_targets") or ["-"]),
            "",
            f"{item.get('detail_platform_label', 'Plattformfamilie')}:",
            str(item.get("platform_family") or "-"),
            "",
            f"{item.get('detail_apply_supported_label', 'Automatisierbare Haertung')}:",
            str(item.get("apply_supported") or "-"),
            "",
            f"{item.get('detail_apply_strategy_label', 'Anwende-Strategie')}:",
            str(item.get("apply_strategy") or "-"),
            "",
            f"{item.get('detail_remediation_label', 'Geplante Massnahme')}:",
            str(item.get("remediation_summary") or "-"),
            "",
            f"{item.get('detail_rollback_label', 'Rollback-Hinweis')}:",
            str(item.get("rollback_hint") or "-"),
            "",
            f"{item.get('detail_command_label', 'Pruefbefehl')}:",
            str(item.get("command") or "-"),
            "",
            f"{item.get('detail_root_used_label', 'Root verwendet')}:",
            str(item.get("root_used") or "Nein"),
            "",
            f"{item.get('detail_root_required_label', 'Root fuer Lesekontrolle erforderlich')}:",
            "Ja" if bool(item.get("requires_root_read")) else "Nein",
            "",
            f"{item.get('detail_privilege_source_label', 'Privilegquelle')}:",
            str(item.get("privilege_source") or "-"),
            "",
            f"{item.get('detail_method_label', 'Pruefmethode')}:",
            str(item.get("check_method") or "-"),
            "",
            f"{item.get('detail_value_source_label', 'Wertquelle')}:",
            str(item.get("value_source") or "-"),
            "",
            f"{item.get('detail_source_label', 'Konfigurationsquelle')}:",
            str(item.get("config_source") or "-"),
            *(
                [
                    "",
                    f"{item.get('detail_error_label', 'Fehlermeldung')}:",
                    str(item.get("check_error") or "-"),
                ]
                if item.get("check_error")
                else []
            ),
            *(
                [
                    "",
                    f"{item.get('detail_raw_label', 'Gelesene Rohdaten')}:",
                    str(item.get("detail_output") or "-"),
                ]
                if item.get("detail_output")
                else []
            ),
            "",
            f"{item.get('detail_lynis_label', 'Lynis-Bezug')}:",
            str(
                item.get("lynis_reference")
                or item.get(
                    "detail_lynis_empty",
                    "Kein direkter Lynis-Bezug hinterlegt.",
                )
            ),
            "",
            f"{item.get('detail_note_label', 'Hinweis')}:",
            item.get("detail_note_text", "Keine automatische Korrektur durch NetMon."),
        ]
    )


def _set_baseline_detail_text(app, text: str):
    widget = _app_value(app, "security_baseline_detail_text")
    _set_text_widget_content(widget, text, append=False)


def show_security_baseline_list_view(app):
    list_view = _app_value(app, "security_baseline_list_view")
    detail_view = _app_value(app, "security_baseline_detail_view")
    try:
        if detail_view is not None:
            detail_view.grid_remove()
    except Exception:
        pass
    try:
        if list_view is not None:
            list_view.grid()
    except Exception:
        pass
    _app_var_set(
        app,
        "security_baseline_detail_heading_var",
        app.tr("baseline_group_details", "Check Details"),
    )
    app.security_baseline_current_view = "list"


def show_security_baseline_detail_view(app, *, title: str = ""):
    list_view = _app_value(app, "security_baseline_list_view")
    detail_view = _app_value(app, "security_baseline_detail_view")
    try:
        if list_view is not None:
            list_view.grid_remove()
    except Exception:
        pass
    try:
        if detail_view is not None:
            detail_view.grid()
    except Exception:
        pass
    heading = str(title or "").strip() or app.tr(
        "baseline_group_details", "Check Details"
    )
    _app_var_set(app, "security_baseline_detail_heading_var", heading)
    app.security_baseline_current_view = "detail"


def refresh_security_baseline_overview(app):
    profile = _active_baseline_profile(app)
    if (
        app is not None
        and str(_app_value(app, "security_baseline_profile_id", "") or "").strip()
        != str(profile.get("id") or "").strip()
    ):
        app.security_baseline_profile_id = str(profile.get("id") or "").strip()
    available_choices = baseline_profile_choice_items(app)
    (
        _app_value(app, "security_baseline_profile_choice_labels", {}).clear()
        if isinstance(_app_value(app, "security_baseline_profile_choice_labels"), dict)
        else None
    )
    (
        _app_value(app, "security_baseline_profile_choice_ids_by_label", {}).clear()
        if isinstance(
            _app_value(app, "security_baseline_profile_choice_ids_by_label"), dict
        )
        else None
    )
    if app is not None:
        app.security_baseline_profile_choice_labels = {
            profile_id: label for profile_id, label in available_choices
        }
        app.security_baseline_profile_choice_ids_by_label = {
            label: profile_id for profile_id, label in available_choices
        }
    combo = _app_value(app, "security_baseline_profile_combo")
    if combo is not None:
        try:
            combo.configure(values=[label for _profile_id, label in available_choices])
        except Exception:
            pass
    _app_var_set(
        app,
        "security_baseline_profile_choice_var",
        _baseline_profile_choice_label(profile),
    )
    _app_var_set(
        app,
        "security_baseline_profile_var",
        app.tr("baseline_profile_value", "Profil: {value}").format(
            value=profile["profile"]
        ),
    )
    _app_var_set(
        app,
        "security_baseline_version_var",
        app.tr("baseline_version_value", "Baseline: {name} {version}").format(
            name=profile["name"],
            version=profile["version"],
        ),
    )
    _app_var_set(
        app,
        "security_baseline_reference_var",
        app.tr("baseline_reference_value", "Referenz: {value}").format(
            value=profile["reference"]
        ),
    )
    _app_var_set(
        app,
        "security_baseline_date_var",
        app.tr("baseline_date_value", "Stand: {value}").format(value=profile["date"]),
    )
    last_checked = str(
        _app_value(app, "security_baseline_last_checked", "") or ""
    ).strip()
    _app_var_set(
        app,
        "security_baseline_last_check_var",
        (
            app.tr(
                "baseline_last_check_value",
                "Letzte Baseline-Pruefung: {value}",
            ).format(value=last_checked)
            if last_checked
            else app.tr(
                "baseline_last_check_default",
                "Letzte Baseline-Pruefung: noch nicht durchgeführt",
            )
        ),
    )
    rows = _app_list(app, "security_baseline_results")
    if rows:
        counts = _baseline_summary_counts(rows)
        total = len(rows)
        status_text = app.tr(
            "baseline_status_value",
            "Gesamtstatus: {ok}/{total} erfüllt | {manual} manuell | {deviation} Abweichung",
        ).format(
            ok=counts["ok"],
            total=total,
            manual=counts["manual"],
            deviation=counts["deviation"],
        )
    else:
        status_text = app.tr(
            "baseline_status_default",
            "Gesamtstatus: noch keine Baseline-Pruefung",
        )
    _app_var_set(app, "security_baseline_status_var", status_text)
    lynis_result = _app_value(app, "lynis_last_result", {}) or {}
    if lynis_result:
        lynis_text = app.tr(
            "baseline_lynis_summary_value",
            "Lynis: Index {index} | Warnungen {warnings} | Tests {tests}",
        ).format(
            index=lynis_result.get("hardening_index", "-"),
            warnings=lynis_result.get("warnings", "-"),
            tests=lynis_result.get("tests", lynis_result.get("suggestions", "-")),
        )
    else:
        lynis_text = app.tr("baseline_lynis_summary_default", "Lynis: keine Daten")
    _app_var_set(app, "security_baseline_lynis_summary_var", lynis_text)
    _app_var_set(
        app,
        "security_baseline_optional_services_var",
        _optional_services_overview_text(app),
    )


def _filtered_baseline_rows(app) -> list[dict]:
    rows = _app_list(app, "security_baseline_results")
    mode = str(_app_value(app, "security_baseline_filter_mode", "all") or "all")
    if mode == "deviations":
        return [
            row
            for row in rows
            if row.get("status") in {"Nicht erfuellt", "Bewusste Abweichung"}
        ]
    if mode == "manual":
        return [
            row
            for row in rows
            if row.get("status") in {"Manuelle Pruefung erforderlich", "Empfehlung"}
        ]
    if mode == "kernel":
        return [row for row in rows if row.get("group") == "Kernel"]
    return rows


def refresh_security_baseline_table(app):
    table = _app_value(app, "security_baseline_tree")
    if table is None:
        return
    try:
        for item_id in list(table.get_children()):
            table.delete(item_id)
    except Exception:
        return
    rows = _filtered_baseline_rows(app)
    app.security_baseline_visible_rows = rows
    tag_map = {
        "Erfuellt": ("ok",),
        "Empfehlung": ("manual",),
        "Nicht erfuellt": ("error",),
        "Bewusste Abweichung": ("deviation",),
        "Manuelle Pruefung erforderlich": ("manual",),
        "Nicht anwendbar": ("na",),
        "Nicht pruefbar": ("unknown",),
        "Root-Rechte erforderlich": ("unknown",),
        "Fehler bei der Pruefung": ("manual",),
        "Nicht geprueft": ("idle",),
    }
    if not rows:
        table.insert(
            "",
            "end",
            values=(
                "-",
                "-",
                app.tr(
                    "baseline_table_placeholder",
                    "Noch keine Baseline-Pruefung durchgeführt",
                ),
                "-",
                "-",
                "-",
            ),
            tags=("idle",),
        )
        _set_baseline_detail_text(
            app,
            app.tr(
                "baseline_detail_placeholder",
                "Noch kein Check ausgewaehlt.",
            ),
        )
        show_security_baseline_list_view(app)
        return
    sorted_rows = sorted(
        rows,
        key=lambda item: (
            _baseline_status_sort_key(str(item.get("status") or "")),
            str(item.get("title") or ""),
        ),
    )
    app.security_baseline_visible_rows = sorted_rows
    for row in sorted_rows:
        table.insert(
            "",
            "end",
            values=(
                row.get("status", "-"),
                row.get("group", "-"),
                row.get("title", "-"),
                row.get("expected", "-"),
                row.get("actual", "-"),
                row.get("source", "-"),
            ),
            tags=tag_map.get(str(row.get("status") or ""), ("idle",)),
        )
    _set_baseline_detail_text(
        app,
        app.tr("baseline_detail_placeholder", "Noch kein Check ausgewaehlt."),
    )
    show_security_baseline_list_view(app)


def apply_security_baseline_filter(app, mode: str):
    app.security_baseline_filter_mode = str(mode or "all")
    refresh_security_baseline_table(app)


def apply_security_baseline_profile_choice(app, choice_label: str):
    normalized = str(choice_label or "").strip()
    if not normalized:
        return
    selected_id = ""
    for profile_id, label in baseline_profile_choice_items():
        if label == normalized or profile_id == normalized:
            selected_id = profile_id
            break
    if not selected_id:
        return
    app.security_baseline_profile_id = selected_id
    app.security_baseline_checks = []
    app.security_baseline_checks_profile_id = ""
    reran = False
    if _app_list(app, "security_baseline_results"):
        run_security_baseline_checks(app)
        reran = True
    if not reran:
        refresh_security_baseline_overview(app)
        refresh_security_baseline_table(app)
    save_fn = getattr(app, "save_settings", None)
    if callable(save_fn):
        try:
            save_fn(log_success=False)
        except Exception:
            pass


def on_security_baseline_select(app, _event=None):
    table = _app_value(app, "security_baseline_tree")
    rows = _app_list(app, "security_baseline_visible_rows")
    if table is None or not rows:
        _set_baseline_detail_text(
            app, app.tr("baseline_detail_placeholder", "Noch kein Check ausgewaehlt.")
        )
        return
    try:
        selection = list(table.selection())
        if not selection:
            _set_baseline_detail_text(
                app,
                app.tr("baseline_detail_placeholder", "Noch kein Check ausgewaehlt."),
            )
            return
        index = int(table.index(selection[0]))
    except Exception:
        _set_baseline_detail_text(
            app, app.tr("baseline_detail_placeholder", "Noch kein Check ausgewaehlt.")
        )
        return
    if index < 0 or index >= len(rows):
        _set_baseline_detail_text(
            app, app.tr("baseline_detail_placeholder", "Noch kein Check ausgewaehlt.")
        )
        return
    row = dict(rows[index])
    row.update(
        {
            "detail_title_label": app.tr("baseline_detail_title", "Titel"),
            "detail_group_label": app.tr("baseline_detail_group", "Gruppe"),
            "detail_status_label": app.tr("baseline_detail_status", "Status"),
            "detail_expected_label": app.tr("baseline_detail_expected", "Sollwert"),
            "detail_actual_label": app.tr("baseline_detail_actual", "Ist-Wert"),
            "detail_description_label": app.tr(
                "baseline_detail_description", "Beschreibung"
            ),
            "detail_reason_label": app.tr("baseline_detail_reason", "Begruendung"),
            "detail_benefit_label": app.tr(
                "baseline_detail_benefit", "Sicherheitsnutzen"
            ),
            "detail_side_effects_label": app.tr(
                "baseline_detail_side_effects", "Moegliche Nebenwirkungen"
            ),
            "detail_exceptions_label": app.tr(
                "baseline_detail_exceptions", "Ausnahmen"
            ),
            "detail_profiles_label": app.tr("baseline_detail_profiles", "Profil-Ziele"),
            "detail_platform_label": app.tr(
                "baseline_detail_platform", "Plattformfamilie"
            ),
            "detail_apply_supported_label": app.tr(
                "baseline_detail_apply_supported", "Automatisierbare Haertung"
            ),
            "detail_apply_strategy_label": app.tr(
                "baseline_detail_apply_strategy", "Anwende-Strategie"
            ),
            "detail_remediation_label": app.tr(
                "baseline_detail_remediation", "Geplante Massnahme"
            ),
            "detail_rollback_label": app.tr(
                "baseline_detail_rollback", "Rollback-Hinweis"
            ),
            "detail_command_label": app.tr("baseline_detail_command", "Pruefbefehl"),
            "detail_root_used_label": app.tr(
                "baseline_detail_root_used", "Root verwendet"
            ),
            "detail_root_required_label": app.tr(
                "baseline_detail_root_required",
                "Root fuer Lesekontrolle erforderlich",
            ),
            "detail_privilege_source_label": app.tr(
                "baseline_detail_privilege_source",
                "Privilegquelle",
            ),
            "detail_method_label": app.tr("baseline_detail_method", "Pruefmethode"),
            "detail_value_source_label": app.tr(
                "baseline_detail_value_source", "Wertquelle"
            ),
            "detail_source_label": app.tr(
                "baseline_detail_source", "Konfigurationsquelle"
            ),
            "detail_error_label": app.tr("baseline_detail_error", "Fehlermeldung"),
            "detail_raw_label": app.tr("baseline_detail_raw", "Gelesene Rohdaten"),
            "detail_lynis_label": app.tr("baseline_detail_lynis", "Lynis-Bezug"),
            "detail_lynis_empty": app.tr(
                "baseline_detail_lynis_empty",
                "Kein direkter Lynis-Bezug hinterlegt.",
            ),
            "detail_note_label": app.tr("baseline_detail_note", "Hinweis"),
            "detail_note_text": row.get("detail_note_text")
            or app.tr(
                "baseline_detail_note_text",
                "Keine automatische Korrektur durch NetMon.",
            ),
        }
    )
    _set_baseline_detail_text(app, _baseline_detail_text(row))
    show_security_baseline_detail_view(
        app,
        title=str(
            row.get("title") or app.tr("baseline_group_details", "Check Details")
        ),
    )


def check_security_baseline_privileges(app, *, showinfo_fn=None):
    showinfo = showinfo_fn or messagebox.showinfo
    root_context = _detect_hardening_privilege_context(app)
    root_checks = [
        row for row in _baseline_checks(app) if bool(row.get("requires_root_read"))
    ]
    title = app.tr(
        "baseline_root_check_title",
        "Root-Check fuer Baseline",
    )
    status_text = (
        app.tr("baseline_root_check_available", "Ja")
        if root_context.get("root_available")
        else app.tr("baseline_root_check_unavailable", "Nein")
    )
    lines = [
        app.tr(
            "baseline_root_check_intro",
            "Prueft, ob Baseline-Checks mit Root-Lesebedarf aktuell ausfuehrbar sind.",
        ),
        "",
        f"{app.tr('baseline_root_check_status_label', 'Root-Lesechecks verfuegbar')}: {status_text}",
        f"{app.tr('baseline_root_check_source_label', 'Privilegkontext')}: {root_context.get('source', 'unbekannt')}",
        f"{app.tr('baseline_root_check_count_label', 'Betroffene Checks')}: {len(root_checks)}",
    ]
    if root_checks:
        lines.extend(
            [
                "",
                f"{app.tr('baseline_root_check_list_label', 'Checks mit Root-Lesebedarf')}:",
            ]
        )
        lines.extend(f"- {item.get('title', '-')}" for item in root_checks)
    if not root_context.get("root_available"):
        lines.extend(
            [
                "",
                app.tr(
                    "baseline_root_check_hint_missing",
                    "Hinweis: Vor der Baseline-Pruefung zuerst eine privilegierte Session aktivieren, z. B. ueber `sudo -v` oder eine NetMon-Aktion mit sudo-Freigabe.",
                ),
            ]
        )
    else:
        lines.extend(
            [
                "",
                app.tr(
                    "baseline_root_check_hint_ok",
                    "Die markierten Root-Lesechecks sollten jetzt ohne Status 'Root-Rechte erforderlich' auswertbar sein.",
                ),
            ]
        )
    text = "\n".join(lines).strip()
    app.log_safe(
        f"Baseline Root-Check: root_available={root_context.get('root_available')} "
        f"source={root_context.get('source', 'unbekannt')} checks={len(root_checks)}"
    )
    showinfo(title, text, parent=app)
    return {
        "root_context": root_context,
        "root_checks": root_checks,
        "message": text,
    }


def run_security_baseline_checks(app, *, run_cmd_fn=None):
    root_context = _detect_hardening_privilege_context(app)
    rows = [
        _evaluate_baseline_check(
            spec,
            run_cmd_fn=run_cmd_fn,
            app=app,
            root_context=root_context,
        )
        for spec in _baseline_checks(app)
    ]
    rows = _attach_lynis_references(app, rows)
    app.security_baseline_results = rows
    app.security_baseline_last_checked = datetime.now().strftime("%d.%m.%Y %H:%M")
    app.lynis_security_baseline_state = _lynis_security_baseline_state(app)
    refresh_security_baseline_overview(app)
    refresh_security_baseline_table(app)
    save_fn = _app_value(app, "_save_security_baseline", None)
    if callable(save_fn):
        try:
            save_fn()
        except Exception:
            pass
    app.log_safe(
        "Security Baseline im Lynis-Tab lesend aktualisiert."
        f" Privilegkontext: {root_context.get('source', 'unbekannt')}."
    )


def apply_security_baseline_sysctl(
    app,
    *,
    run_cmd_fn=None,
    askyesno_fn=None,
    showinfo_fn=None,
    showerror_fn=None,
    require_confirmation: bool = True,
    require_sudo_session: bool = True,
    rerun_baseline: bool = True,
    show_success_dialog: bool = True,
    override_specs: list[dict] | None = None,
):
    askyesno_runner = askyesno_fn or messagebox.askyesno
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showerror_runner = showerror_fn or messagebox.showerror
    profile = _active_baseline_profile(app)
    if override_specs is None and not bool(profile.get("apply_supported")):
        showerror_runner(
            app.tr("baseline_apply_sysctl_title", "Sysctl-Haertung anwenden"),
            app.tr(
                "baseline_apply_sysctl_profile_unsupported",
                "Das aktive Baseline-Profil ist nicht fuer automatische Sysctl-Haertung freigegeben.",
            ),
            parent=app,
        )
        return False

    specs = (
        [dict(item) for item in list(override_specs or [])]
        if override_specs is not None
        else _sysctl_baseline_specs(app)
    )
    if not specs:
        showerror_runner(
            app.tr("baseline_apply_sysctl_title", "Sysctl-Haertung anwenden"),
            app.tr(
                "baseline_apply_sysctl_missing_specs",
                "Es wurden keine Sysctl-Baseline-Werte gefunden.",
            ),
            parent=app,
        )
        return False

    if require_confirmation:
        if not askyesno_runner(
            app.tr("baseline_apply_sysctl_title", "Sysctl-Haertung anwenden"),
            app.tr(
                "baseline_apply_sysctl_confirm",
                "NetMon schreibt die Sysctl-Baseline in eine dedizierte Drop-in-Datei unter /etc/sysctl.d/ und laedt die Werte neu.\n\nFortfahren?",
            ),
            parent=app,
        ):
            return False

    if require_sudo_session and not app.ensure_sudo_session(
        "Security Baseline Sysctl-Haertung anwenden"
    ):
        return False

    target_path = _sysctl_dropin_path(app)
    content = _build_sysctl_dropin_content(specs)
    tx = None
    new_tx = _app_value(app, "_new_rollback_transaction", None)
    if callable(new_tx):
        try:
            tx = new_tx("Security Baseline Sysctl")
        except Exception:
            tx = None

    ok, detail = _apply_sysctl_dropin(
        target_path,
        content,
        run_cmd_fn=run_cmd_fn,
        rollback_tx=tx,
    )
    if not ok:
        rollback_ok = True
        if tx is not None:
            rollback_ok = tx.rollback()
        showerror_runner(
            app.tr("baseline_apply_sysctl_title", "Sysctl-Haertung anwenden"),
            app.tr(
                "baseline_apply_sysctl_failed",
                "Die Sysctl-Haertung konnte nicht erfolgreich angewendet werden.",
            )
            + (f"\n\n{detail}" if detail else ""),
            parent=app,
        )
        if not rollback_ok:
            app.log_safe(
                "Security Baseline Sysctl: Rollback unvollstaendig, bitte /etc/sysctl.d/ und aktive sysctl-Werte manuell pruefen."
            )
        return False

    if tx is not None:
        tx.commit()
    app.log_safe(f"Security Baseline Sysctl-Haertung angewendet: {target_path}")
    if rerun_baseline:
        run_security_baseline_checks(app, run_cmd_fn=run_cmd_fn)
    if show_success_dialog:
        showinfo_runner(
            app.tr("baseline_apply_sysctl_title", "Sysctl-Haertung anwenden"),
            app.tr(
                "baseline_apply_sysctl_success",
                "Die Sysctl-Baseline wurde angewendet und anschliessend erneut geprueft.",
            ),
            parent=app,
        )
    return True


def apply_security_baseline_ufw(
    app,
    *,
    run_cmd_fn=None,
    askyesno_fn=None,
    showinfo_fn=None,
    showerror_fn=None,
    require_confirmation: bool = True,
    require_sudo_session: bool = True,
    rerun_baseline: bool = True,
    show_success_dialog: bool = True,
    override_profile: dict | None = None,
):
    askyesno_runner = askyesno_fn or messagebox.askyesno
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showerror_runner = showerror_fn or messagebox.showerror
    profile = (
        dict(override_profile)
        if isinstance(override_profile, dict)
        else _active_ufw_baseline_profile(app)
    )
    if profile is None:
        showerror_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_profile_unsupported",
                "Das aktive Baseline-Profil besitzt derzeit kein freigegebenes UFW-Regelprofil.",
            ),
            parent=app,
        )
        return False

    if require_confirmation:
        if not askyesno_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_confirm",
                "NetMon aktiviert UFW bei Bedarf, setzt die Default-Policies auf das freigegebene Baseline-Profil und fuegt die expliziten Profilregeln hinzu.\n\nFortfahren?",
            ),
            parent=app,
        ):
            return False

    if require_sudo_session and not app.ensure_sudo_session(
        "Security Baseline UFW-Haertung anwenden"
    ):
        return False

    tx = None
    new_tx = _app_value(app, "_new_rollback_transaction", None)
    if callable(new_tx):
        try:
            tx = new_tx("Security Baseline UFW")
        except Exception:
            tx = None

    rc_before, status_before = _read_ufw_status_with_mode(
        "verbose", run_cmd_fn=run_cmd_fn
    )
    if rc_before != 0:
        showerror_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_status_failed",
                "Der aktuelle UFW-Status konnte vor der Anwendung nicht gelesen werden.",
            )
            + (f"\n\n{status_before}" if status_before else ""),
            parent=app,
        )
        return False

    previous_status = _parse_ufw_status_state(status_before)
    previous_incoming, previous_outgoing = _parse_ufw_default_policies(status_before)
    if previous_incoming is None or previous_outgoing is None:
        showerror_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_defaults_unknown",
                "Die aktuellen UFW-Default-Policies konnten nicht eindeutig gelesen werden. Die Anwendung wird aus Sicherheitsgruenden abgebrochen.",
            ),
            parent=app,
        )
        return False

    runner = run_cmd_fn or run_cmd
    if previous_status != "active":
        rc_enable, out_enable = runner(
            ["sudo", "-n", "ufw", "--force", "enable"], timeout=40
        )
        if rc_enable != 0:
            showerror_runner(
                app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
                app.tr(
                    "baseline_apply_ufw_enable_failed",
                    "UFW konnte nicht aktiviert werden.",
                )
                + (f"\n\n{out_enable}" if out_enable else ""),
                parent=app,
            )
            return False
        if tx is not None:
            tx.add_rollback(
                "UFW wieder deaktivieren",
                lambda: _run_checked_command(
                    ["sudo", "-n", "ufw", "--force", "disable"],
                    run_cmd_fn=run_cmd_fn,
                    timeout=20,
                ),
            )

    desired_incoming = str(profile.get("default_incoming") or "").strip().lower()
    desired_outgoing = str(profile.get("default_outgoing") or "").strip().lower()
    if previous_incoming != desired_incoming:
        rc_in, out_in = runner(
            ["sudo", "-n", "ufw", "default", desired_incoming, "incoming"],
            timeout=20,
        )
        if rc_in != 0:
            if tx is not None:
                tx.rollback()
            showerror_runner(
                app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
                app.tr(
                    "baseline_apply_ufw_defaults_failed",
                    "Die UFW-Default-Policies konnten nicht gesetzt werden.",
                )
                + (f"\n\n{out_in}" if out_in else ""),
                parent=app,
            )
            return False
        if tx is not None:
            tx.add_rollback(
                "Vorherige Incoming-Policy wiederherstellen",
                lambda incoming=previous_incoming: _run_checked_command(
                    ["sudo", "-n", "ufw", "default", incoming, "incoming"],
                    run_cmd_fn=run_cmd_fn,
                    timeout=20,
                ),
            )

    if previous_outgoing != desired_outgoing:
        rc_out, out_out = runner(
            ["sudo", "-n", "ufw", "default", desired_outgoing, "outgoing"],
            timeout=20,
        )
        if rc_out != 0:
            if tx is not None:
                tx.rollback()
            showerror_runner(
                app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
                app.tr(
                    "baseline_apply_ufw_defaults_failed",
                    "Die UFW-Default-Policies konnten nicht gesetzt werden.",
                )
                + (f"\n\n{out_out}" if out_out else ""),
                parent=app,
            )
            return False
        if tx is not None:
            tx.add_rollback(
                "Vorherige Outgoing-Policy wiederherstellen",
                lambda outgoing=previous_outgoing: _run_checked_command(
                    ["sudo", "-n", "ufw", "default", outgoing, "outgoing"],
                    run_cmd_fn=run_cmd_fn,
                    timeout=20,
                ),
            )

    _, numbered_before = _read_ufw_status_with_mode("numbered", run_cmd_fn=run_cmd_fn)
    known_keys = _existing_ufw_profile_rule_keys(numbered_before)
    for rule in profile.get("rules", []) or []:
        ok, added, detail, known_keys = _ensure_ufw_profile_rule(
            rule,
            run_cmd_fn=run_cmd_fn,
            known_keys=known_keys,
        )
        if not ok:
            rollback_ok = True
            if tx is not None:
                rollback_ok = tx.rollback()
            showerror_runner(
                app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
                app.tr(
                    "baseline_apply_ufw_rule_failed",
                    "Mindestens eine UFW-Baseline-Regel konnte nicht gesetzt werden.",
                )
                + (f"\n\n{detail}" if detail else ""),
                parent=app,
            )
            if not rollback_ok:
                app.log_safe(
                    "Security Baseline UFW: Rollback unvollstaendig, bitte UFW-Status und Default-Policies manuell pruefen."
                )
            return False
        if added and tx is not None:
            tx.add_rollback(
                "Hinzugefuegte UFW-Regel entfernen",
                lambda current_rule=dict(rule): _delete_ufw_profile_rule(
                    current_rule,
                    run_cmd_fn=run_cmd_fn,
                ),
            )

    ufw_sysctl_ok, ufw_sysctl_detail = _apply_ufw_sysctl_overrides(
        run_cmd_fn=run_cmd_fn,
        rollback_tx=tx,
    )
    if not ufw_sysctl_ok:
        rollback_ok = True
        if tx is not None:
            rollback_ok = tx.rollback()
        showerror_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_sysctl_failed",
                "Die UFW-sysctl-Konfiguration konnte nicht dauerhaft angepasst werden.",
            )
            + (f"\n\n{ufw_sysctl_detail}" if ufw_sysctl_detail else ""),
            parent=app,
        )
        if not rollback_ok:
            app.log_safe(
                "Security Baseline UFW: Rollback unvollstaendig, bitte UFW-Status, Regeln und /etc/ufw/sysctl.conf manuell pruefen."
            )
        return False

    rc_after, status_after = _read_ufw_status_with_mode(
        "verbose", run_cmd_fn=run_cmd_fn
    )
    if rc_after != 0 or not _ufw_profile_matches_status(profile, status_after):
        rollback_ok = True
        if tx is not None:
            rollback_ok = tx.rollback()
        showerror_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_verify_failed",
                "Der UFW-Endzustand entspricht nicht vollstaendig dem freigegebenen Baseline-Profil.",
            )
            + (f"\n\n{status_after}" if status_after else ""),
            parent=app,
        )
        if not rollback_ok:
            app.log_safe(
                "Security Baseline UFW: Rollback unvollstaendig, bitte UFW-Status und Regeln manuell pruefen."
            )
        return False

    if tx is not None:
        tx.commit()
    app.log_safe(
        "Security Baseline UFW-Haertung angewendet: "
        f"{profile.get('name', profile.get('id', 'UFW-Profil'))}"
    )
    if ufw_sysctl_detail:
        app.log_safe(f"Security Baseline UFW-sysctl: {ufw_sysctl_detail}")
    profile_note = str(profile.get("post_apply_note") or "").strip()
    if profile_note:
        app.log_safe(f"Security Baseline UFW-Hinweis: {profile_note}")
    if rerun_baseline:
        run_security_baseline_checks(app, run_cmd_fn=run_cmd_fn)
    if show_success_dialog:
        showinfo_runner(
            app.tr("baseline_apply_ufw_title", "Firewall-Haertung anwenden"),
            app.tr(
                "baseline_apply_ufw_success",
                "Das UFW-Baseline-Profil wurde angewendet und anschliessend erneut geprueft.",
            )
            + (f"\n\n{profile_note}" if profile_note else ""),
            parent=app,
        )
    return True


def apply_security_baseline_profile(
    app,
    *,
    run_cmd_fn=None,
    askyesno_fn=None,
    showinfo_fn=None,
    showerror_fn=None,
    transfer_package: dict | None = None,
):
    askyesno_runner = askyesno_fn or messagebox.askyesno
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showerror_runner = showerror_fn or messagebox.showerror

    plan = _security_baseline_apply_plan(app, transfer_package=transfer_package)
    actions = list(plan.get("actions") or [])
    if not actions:
        showerror_runner(
            app.tr("baseline_apply_all_title", "Baseline-Haertung anwenden"),
            app.tr(
                "baseline_apply_all_unsupported",
                "Das aktive Baseline-Profil besitzt derzeit keine freigegebenen automatischen Hardening-Schritte.",
            ),
            parent=app,
        )
        return False

    profile = plan.get("profile") or {}
    profile_name = str(profile.get("profile") or profile.get("id") or "Baseline-Profil")
    preview_text = str(plan.get("preview_text") or "").strip()
    rollback_text = str(plan.get("rollback_text") or "").strip()
    confirm_text = app.tr(
        "baseline_apply_all_confirm",
        "NetMon wendet jetzt alle freigegebenen Hardening-Schritte fuer das aktive Baseline-Profil an.\n\nProfil: {profile}\n\nVorschau:\n{preview}\n\nRollback-Hinweise:\n{rollback}\n\nFortfahren?",
    ).format(
        profile=profile_name,
        preview=preview_text or "-",
        rollback=rollback_text or "-",
    )
    confirm_title = app.tr("baseline_apply_all_title", "Baseline-Haertung anwenden")
    confirm_dialog = _app_value(app, "confirm_security_baseline_apply", None)
    use_custom_confirm_dialog = callable(confirm_dialog) and (
        askyesno_fn is None or askyesno_runner is messagebox.askyesno
    )
    if use_custom_confirm_dialog:
        if not confirm_dialog(
            confirm_title,
            profile_name=profile_name,
            preview_text=preview_text,
            rollback_text=rollback_text,
        ):
            return False
    elif not askyesno_runner(
        confirm_title,
        confirm_text,
        parent=app,
    ):
        return False

    if not app.ensure_sudo_session("Security Baseline Profil-Haertung anwenden"):
        return False

    completed = []
    if "sysctl" in actions:
        if not apply_security_baseline_sysctl(
            app,
            run_cmd_fn=run_cmd_fn,
            askyesno_fn=askyesno_fn,
            showinfo_fn=lambda *args, **kwargs: None,
            showerror_fn=showerror_runner,
            require_confirmation=False,
            require_sudo_session=False,
            rerun_baseline=False,
            show_success_dialog=False,
            override_specs=plan.get("sysctl_specs"),
        ):
            if completed:
                app.log_safe(
                    "Security Baseline Profil-Haertung teilweise angewendet: "
                    + ", ".join(completed)
                )
            return False
        completed.append("sysctl")

    if "ufw" in actions:
        if not apply_security_baseline_ufw(
            app,
            run_cmd_fn=run_cmd_fn,
            askyesno_fn=askyesno_fn,
            showinfo_fn=lambda *args, **kwargs: None,
            showerror_fn=showerror_runner,
            require_confirmation=False,
            require_sudo_session=False,
            rerun_baseline=False,
            show_success_dialog=False,
            override_profile=plan.get("ufw_profile"),
        ):
            if completed:
                app.log_safe(
                    "Security Baseline Profil-Haertung teilweise angewendet: "
                    + ", ".join(completed)
                )
            return False
        completed.append("ufw")

    if "services_optional" in actions:
        services_ok, applied_services, skipped_by_user = (
            _apply_optional_service_actions(
                app,
                list(plan.get("optional_services") or []),
                run_cmd_fn=run_cmd_fn,
                askyesno_fn=askyesno_fn,
                showerror_fn=showerror_runner,
            )
        )
        if not services_ok:
            if completed:
                app.log_safe(
                    "Security Baseline Profil-Haertung teilweise angewendet: "
                    + ", ".join(completed)
                )
            return False
        if applied_services:
            completed.append("optionale Dienste")
        elif skipped_by_user:
            app.log_safe(
                "Security Baseline Optionaldienste übersprungen: "
                + ", ".join(
                    str(item.get("name") or "").strip()
                    for item in list(plan.get("optional_services") or [])
                    if str(item.get("name") or "").strip()
                )
            )

    run_security_baseline_checks(app, run_cmd_fn=run_cmd_fn)
    completed_text = ", ".join(completed)
    app.log_safe(
        "Security Baseline Profil-Haertung angewendet: "
        f"{profile_name} ({completed_text})"
    )
    showinfo_runner(
        app.tr("baseline_apply_all_title", "Baseline-Haertung anwenden"),
        app.tr(
            "baseline_apply_all_success",
            "Die freigegebenen Hardening-Schritte fuer das aktive Baseline-Profil wurden angewendet und anschliessend erneut geprueft.",
        )
        + f"\n\n{app.tr('baseline_apply_all_applied_steps', 'Angewendete Schritte')}: {completed_text}"
        + (
            f"\n\n{app.tr('baseline_apply_all_rollback_label', 'Rollback-Hinweise')}:\n{rollback_text}"
            if rollback_text
            else ""
        ),
        parent=app,
    )
    return True


def export_security_baseline_transfer(
    app,
    path: str,
    *,
    showinfo_fn=None,
    showerror_fn=None,
):
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showerror_runner = showerror_fn or messagebox.showerror
    package = build_security_baseline_transfer_package(app)
    ok, error = _write_security_baseline_transfer_package(path, package)
    if not ok:
        showerror_runner(
            _tr(
                app,
                "baseline_transfer_export_title",
                "Baseline-Transferpaket exportieren",
            ),
            _tr(
                app,
                "baseline_transfer_export_failed",
                "Das Baseline-Transferpaket konnte nicht geschrieben werden.",
            )
            + (f"\n\n{error}" if error else ""),
            parent=app,
        )
        return False
    app.log_safe(f"Security Baseline Transfer exportiert: {path}")
    showinfo_runner(
        _tr(
            app, "baseline_transfer_export_title", "Baseline-Transferpaket exportieren"
        ),
        _tr(
            app,
            "baseline_transfer_export_success",
            "Das Baseline-Transferpaket wurde erfolgreich exportiert.",
        )
        + f"\n\n{path}",
        parent=app,
    )
    return True


def import_security_baseline_transfer(
    app,
    path: str,
    *,
    run_cmd_fn=None,
    askyesno_fn=None,
    showinfo_fn=None,
    showerror_fn=None,
):
    askyesno_runner = askyesno_fn or messagebox.askyesno
    showinfo_runner = showinfo_fn or messagebox.showinfo
    showerror_runner = showerror_fn or messagebox.showerror
    try:
        package = _validate_security_baseline_transfer_package(
            _read_security_baseline_transfer_package(path)
        )
    except Exception as exc:
        showerror_runner(
            _tr(
                app,
                "baseline_transfer_import_title",
                "Baseline-Transferpaket importieren",
            ),
            _tr(
                app,
                "baseline_transfer_import_failed",
                "Das Baseline-Transferpaket konnte nicht gelesen oder validiert werden.",
            )
            + f"\n\n{exc}",
            parent=app,
        )
        return False

    _set_security_baseline_transfer_state(app, package, source_path=path)
    profile_id = str((package.get("baseline") or {}).get("id") or "").strip()
    if profile_id in SECURITY_BASELINE_PROFILES:
        app.security_baseline_profile_id = profile_id
        refresh_security_baseline_overview(app)
        refresh_security_baseline_table(app)

    app.log_safe(f"Security Baseline Transfer importiert: {path}")
    if askyesno_runner(
        _tr(
            app, "baseline_transfer_import_title", "Baseline-Transferpaket importieren"
        ),
        _tr(
            app,
            "baseline_transfer_import_apply_now",
            "Das Transferpaket wurde geladen.\n\nSoll die enthaltene Profil-Haertung jetzt auf dieses System angewendet werden?",
        ),
        parent=app,
    ):
        return apply_security_baseline_profile(
            app,
            run_cmd_fn=run_cmd_fn,
            askyesno_fn=askyesno_runner,
            showinfo_fn=showinfo_runner,
            showerror_fn=showerror_runner,
            transfer_package=package,
        )

    showinfo_runner(
        _tr(
            app, "baseline_transfer_import_title", "Baseline-Transferpaket importieren"
        ),
        _tr(
            app,
            "baseline_transfer_import_success",
            "Das Baseline-Transferpaket wurde geladen. Du kannst die Profil-Haertung jetzt direkt aus dem Hardening-Tab anwenden.",
        ),
        parent=app,
    )
    return True


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
        if _rkhunter_log_line_is_evidence(line):
            evidence_lines.append(line.strip())
    if not evidence_lines:
        return ""
    return "\n".join(["", "=== rkhunter log evidence ===", *evidence_lines])


def _rkhunter_log_line_is_evidence(line: str) -> bool:
    lowered = str(line or "").lower()
    return (
        "hidden file" in lowered
        or "hidden directory" in lowered
        or "suspect file" in lowered
        or "[ warning ]" in lowered
    )


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
    if app is None:
        return default
    data = getattr(app, "__dict__", None)
    if isinstance(data, dict) and name in data:
        return data.get(name, default)
    try:
        return object.__getattribute__(app, name)
    except AttributeError:
        return default


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
