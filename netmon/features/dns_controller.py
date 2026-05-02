"""DNS controller helpers for NetMon."""

from __future__ import annotations

from tkinter import messagebox
import os

try:
    from netmon.config.constants import DNS_MODE_LABELS, DNS_PROFILES, DOT_DROPIN_PATH
except ModuleNotFoundError:
    from config.constants import DNS_MODE_LABELS, DNS_PROFILES, DOT_DROPIN_PATH

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def use_vpn_dns(app):
    service = app._dns_control_service()
    if service is None:
        nm_ok, nm_details = app._apply_nm_dns_policy_to_targets(ignore_auto_dns=True)
        rm_ok, rm_detail = app._remove_manual_dns_dropin()
        restart_ok, restart_detail = app._restart_resolved_for_dns_policy()
        success = nm_ok and rm_ok and restart_ok
        lines = [
            "=== DNS Control ===",
            "Aktion: VPN-DNS erzwingen",
            f"Ergebnis: {'erfolgreich' if success else 'fehlgeschlagen'}",
            "",
            "NetMon DoT Drop-in:",
            "entfernt" if rm_ok else f"Fehler: {rm_detail or 'unknown'}",
            "",
            "NetworkManager:",
            *nm_details,
            "systemd-resolved Restart:",
            "OK" if restart_ok else (restart_detail or "fehlgeschlagen"),
        ]
        return success, "\n".join(lines).strip()
    return service.apply_vpn_dns_policy(targets=app._active_nm_dns_targets())


def dns_mode_from_label(value):
    candidate = str(value or "").strip()
    if candidate in DNS_MODE_LABELS:
        return candidate
    lowered = candidate.lower()
    for mode, label in DNS_MODE_LABELS.items():
        if lowered == label.lower():
            return mode
    return "auto"


def dns_mode_label(mode):
    return DNS_MODE_LABELS.get(dns_mode_from_label(mode), DNS_MODE_LABELS["auto"])


def current_dns_mode(app):
    mode = dns_mode_from_label(app.__dict__.get("dns_mode", "auto"))
    mode_var = app.__dict__.get("dns_mode_var")
    if mode_var is not None:
        mode = dns_mode_from_label(mode_var.get() or mode)
    return mode


def set_dns_mode(app, mode, persist=True, update_var=True):
    normalized = dns_mode_from_label(mode)
    app.dns_mode = normalized
    if update_var and "dns_mode_var" in app.__dict__:
        app.dns_mode_var.set(dns_mode_label(normalized))
    if persist and "privacy_config" in app.__dict__:
        try:
            app.save_privacy_config()
        except Exception:
            pass
    return normalized


def on_dns_mode_selected(app):
    mode = set_dns_mode(app, app.dns_mode_var.get())
    refresh_dns_policy_status(app)
    app.chad_analysis_status_var.set(f"DNS-Modus gewählt: {dns_mode_label(mode)}")


def dns_mode_display_name(mode):
    mapping = {
        "auto": "AUTO",
        "vpn": "VPN-PRIORITY",
        "manual": "MANUAL",
    }
    return mapping.get(dns_mode_from_label(mode), "AUTO")


def normalize_dns_profile_choice(app, choice=None):
    selected = (choice or app.dns_choice.get() or "").strip()
    if selected not in DNS_PROFILES:
        return "System (DHCP/auto)"
    return selected


def apply_dns_profile_choice_via_control(app, choice):
    normalized_choice = normalize_dns_profile_choice(app, choice)
    servers = DNS_PROFILES.get(normalized_choice)

    if servers is None:
        nm_ok, nm_details = app._apply_nm_dns_policy_to_targets(ignore_auto_dns=False)
        dropin_ok, dropin_detail = app._remove_manual_dns_dropin()
        restart_ok, restart_detail = app._restart_resolved_for_dns_policy()
        return {
            "choice": normalized_choice,
            "servers": [],
            "success": nm_ok and dropin_ok and restart_ok,
            "nm_details": list(nm_details),
            "dropin_ok": dropin_ok,
            "dropin_detail": dropin_detail,
            "dropin_state": "entfernt",
            "restart_ok": restart_ok,
            "restart_detail": restart_detail,
        }

    nm_ok, nm_details = app._apply_nm_dns_policy_to_targets(ignore_auto_dns=True)
    dropin_ok, dropin_detail = app._write_manual_dns_dropin(normalized_choice)
    restart_ok, restart_detail = app._restart_resolved_for_dns_policy()
    return {
        "choice": normalized_choice,
        "servers": [str(server).strip() for server in servers if str(server).strip()],
        "success": nm_ok and dropin_ok and restart_ok,
        "nm_details": list(nm_details),
        "dropin_ok": dropin_ok,
        "dropin_detail": dropin_detail,
        "dropin_state": "geschrieben",
        "restart_ok": restart_ok,
        "restart_detail": restart_detail,
    }


def format_dns_profile_control_result(result, *, heading, action):
    lines = [
        heading,
        f"Aktion: {action}",
        f"Profil: {result.get('choice', '-')}",
    ]
    servers = [
        str(server).strip()
        for server in (result.get("servers") or [])
        if str(server).strip()
    ]
    if servers:
        lines.append(f"Server: {' '.join(servers)}")
    lines.extend(
        [
            f"Ergebnis: {'erfolgreich' if result.get('success') else 'fehlgeschlagen'}",
            "",
            "NetworkManager:",
            *(result.get("nm_details") or ["Keine Details verfügbar."]),
            "NetMon DoT Drop-in:",
            (
                result.get("dropin_state", "aktualisiert")
                if result.get("dropin_ok")
                else f"Fehler: {result.get('dropin_detail') or 'unknown'}"
            ),
            "systemd-resolved Restart:",
            (
                "OK"
                if result.get("restart_ok")
                else (result.get("restart_detail") or "fehlgeschlagen")
            ),
        ]
    )
    return "\n".join(lines).strip()


def use_user_dns(app):
    if app.is_vpn_active():
        return app.warn_manual_dns_with_vpn()

    dns_choice = normalize_dns_profile_choice(app, app._manual_dns_choice())
    app._set_dns_choice_safe(dns_choice)
    result = apply_dns_profile_choice_via_control(app, dns_choice)
    return result["success"], format_dns_profile_control_result(
        result,
        heading="=== DNS Control ===",
        action="User DNS aktivieren",
    )


def enforce_dns_policy(app):
    vpn_active = app.is_vpn_active()
    mode = app._current_dns_mode()

    if mode == "auto":
        return use_vpn_dns(app) if vpn_active else use_user_dns(app)
    if mode == "vpn":
        return use_vpn_dns(app) if vpn_active else app.warn_no_vpn()
    if mode == "manual":
        return use_user_dns(app)
    return False, "=== DNS Control ===\nUnbekannter DNS-Modus."


def refresh_dns_policy_status(app):
    mode = current_dns_mode(app)
    code, out = run_cmd(["resolvectl", "status"], timeout=8)
    evaluation = evaluate_dns_policy(app, out if code == 0 else "")
    conflicts = list(evaluation.get("warnings") or [])
    if mode == "vpn" and not evaluation.get("vpn_active"):
        conflicts.append("VPN-PRIORITY ohne aktives VPN")
    if mode == "manual" and evaluation.get("vpn_active"):
        conflicts.append("MANUAL ist bei aktivem VPN blockiert")
    conflicts_text = "keine" if not conflicts else "; ".join(conflicts)

    app.dns_mode_status_var.set(f"Aktiver DNS-Modus: {dns_mode_display_name(mode)}")
    app.dns_resolver_status_var.set(
        f"Aktiver Resolver: {evaluation.get('resolver_label', 'unbekannt')}"
    )
    app.dns_conflict_status_var.set(f"Konflikte: {conflicts_text}")
    return {
        "mode": mode,
        "resolver": evaluation.get("resolver_label", "unbekannt"),
        "conflicts": conflicts_text,
        "vpn_active": bool(evaluation.get("vpn_active")),
        "servers": list(evaluation.get("active_dns") or []),
        "dropin_present": bool(evaluation.get("dot_dropin_exists")),
        "dropin_conflict": bool(evaluation.get("dot_dropin_conflict")),
        "risk": evaluation.get("risk", "unbekannt"),
    }


def evaluate_dns_policy(app, resolvectl_output: str) -> dict:
    service = app._dns_control_service()
    if service is None:
        return {
            "vpn_active": False,
            "vpn_dns": [],
            "global_dns": [],
            "physical_dns": [],
            "active_dns": [],
            "dot_dropin_exists": os.path.isfile(DOT_DROPIN_PATH),
            "dot_dropin_conflict": False,
            "conflict": False,
            "risk": "unbekannt",
            "recommendation": "DNS-Control-Service nicht verfügbar.",
            "recommendations": ["DNS-Control-Service nicht verfügbar."],
            "warnings": [],
            "resolver_label": "unbekannt",
        }
    return service.evaluate_dns_policy(
        resolvectl_output=resolvectl_output,
        dns_mode=current_dns_mode(app),
    )


def show_dns_policy_result(app, text, *, startup=False):
    if not startup:
        app.nb.select(app.tab_dns)
        app.update_dns_output(text, append=True)
    refresh_dns_policy_status(app)


def apply_dns(app, choice=None, refresh_ui=True, update_choice_var=True):
    controls_locked, lock_reason = app._dns_controls_locked()
    if controls_locked:
        if lock_reason == "transition":
            warning_message = app.tr(
                "dns_warning_locked_transition_message",
                "Es läuft gerade ein VPN-/DNS-Wechsel.\n\n"
                "Bitte warten, bis der Vorgang abgeschlossen ist. "
                "Währenddessen ist ein manueller DNS-Wechsel gesperrt.",
            )
            result = (
                "=== DNS anwenden ===\n"
                "Status: blockiert\n"
                "Grund: VPN-/DNS-Wechsel läuft.\n\n"
                "Bitte warten, bis der laufende Vorgang abgeschlossen ist."
            )
            log_message = "DNS anwenden blockiert: VPN-/DNS-Wechsel läuft"
        else:
            warning_message = app.tr(
                "dns_warning_locked_vpn_message",
                "VPN ist aktiv.\n\n"
                "DNS wird vom VPN-Profil verwaltet. "
                "Ein manueller DNS-Wechsel kann DNS-Leaks verursachen.",
            )
            result = (
                "=== DNS anwenden ===\n"
                "Status: blockiert\n"
                "Grund: VPN ist aktiv.\n\n"
                "DNS wird vom VPN-Profil verwaltet. Ein manueller DNS-Wechsel "
                "würde DNS-Leaks verursachen."
            )
            log_message = "DNS anwenden blockiert: VPN aktiv"
        messagebox.showwarning(
            app.tr("dns_warning_locked_title", "DNS gesperrt"),
            warning_message,
            parent=app,
        )
        app.nb.select(app.tab_dns)
        app.update_dns_output(result)
        app.log_safe(log_message)
        app.update_dns_controls_state_safe()
        return False

    choice = normalize_dns_profile_choice(app, choice)
    if update_choice_var:
        app._set_dns_choice_safe(choice)

    app.nb.select(app.tab_dns)
    app.log_safe("DNS-Profil wird angewendet...")

    result = apply_dns_profile_choice_via_control(app, choice)
    app.update_dns_output(
        format_dns_profile_control_result(
            result,
            heading="=== DNS anwenden ===",
            action="DNS-Profil anwenden",
        )
    )

    if not result["success"]:
        app.log_safe("DNS anwenden fehlgeschlagen")
        app.refresh_dns_policy_status()
        app.update_dns_controls_state_safe()
        return False

    app.log_safe(f"DNS-Profil angewendet: {choice}")
    app.last_dns_consistency_ok = None
    app.last_dns_consistency_ts = 0.0
    app.dns_consistency_enabled = True
    app.dns_consistency_one_shot = True
    app.dns_consistency_check_async(force=True)
    app.refresh_dns_policy_status()
    app.update_dns_controls_state_safe()
    if refresh_ui:
        app.refresh_safe()
    return True
