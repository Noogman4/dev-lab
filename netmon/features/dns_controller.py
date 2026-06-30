"""DNS controller helpers for NetMon."""

from __future__ import annotations

from tkinter import messagebox
import os

try:
    from netmon.config.constants import DNS_PROFILES, DOT_DROPIN_PATH
except ModuleNotFoundError:
    from config.constants import DNS_PROFILES, DOT_DROPIN_PATH

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def _app_value(app, name, default=None):
    return app.__dict__.get(name, default)


def _app_callback(app, name):
    callback = getattr(app, name, None)
    return callback if callable(callback) else None


def _tr(app, key, fallback):
    callback = _app_callback(app, "tr")
    if callback is None:
        return fallback
    try:
        return callback(key, fallback)
    except Exception:
        return fallback


def _invoke_optional_app_callback(callback, app, *, safe=False):
    if callback is None:
        return None
    if safe:
        try:
            return callback()
        except TypeError:
            try:
                return callback(app)
            except Exception:
                return None
        except Exception:
            return None
    try:
        return callback()
    except TypeError:
        return callback(app)


def _dns_choice_value(app, default=""):
    choice_var = _app_value(app, "dns_choice")
    if choice_var is None:
        return str(default or "")
    try:
        value = choice_var.get()
    except Exception:
        value = default
    return str(value or default)


def _select_dns_tab(app):
    app.nb.select(app.tab_dns)


def _refresh_dns_state(app, *, safe=False):
    refresh_fn = _app_callback(app, "refresh_dns_policy_status")
    if refresh_fn is None:
        refresh_fn = refresh_dns_policy_status
    _invoke_optional_app_callback(refresh_fn, app, safe=safe)
    app.update_dns_controls_state_safe()


def use_vpn_dns(app):
    service = app._dns_control_service()
    if service is None:
        nm_ok, nm_details = app._apply_nm_dns_policy_to_targets(ignore_auto_dns=True)
        rm_ok, rm_detail = app._remove_manual_dns_dropin()
        restart_ok, restart_detail = app._restart_resolved_for_dns_policy()
        success = nm_ok and rm_ok and restart_ok
        lines = [
            app.tr("dns_control_report_title", "=== DNS Control ==="),
            app.tr(
                "dns_control_action_enforce_vpn_dns",
                "Action: enforce VPN DNS",
            ),
            app.tr(
                "dns_control_result_value",
                "Result: {value}",
            ).format(
                value=app.tr("dns_result_successful", "successful")
                if success
                else app.tr("dns_result_failed", "failed")
            ),
            "",
            app.tr("dns_section_system", "[System]"),
            (
                app.tr(
                    "dns_dot_dropin_removed",
                    "✔ NetMon DoT configuration removed",
                )
                if rm_ok
                else app.tr(
                    "dns_dot_dropin_remove_failed",
                    "✖ Error removing NetMon DoT configuration: {detail}",
                ).format(detail=rm_detail or app.tr("dns_value_unknown", "unknown"))
            ),
            (
                app.tr(
                    "dns_resolved_restarted",
                    "✔ systemd-resolved restarted",
                )
                if restart_ok
                else app.tr(
                    "dns_resolved_restart_failed",
                    "✖ Error restarting systemd-resolved: {detail}",
                ).format(
                    detail=restart_detail or app.tr("dns_result_failed", "failed")
                )
            ),
            "",
            app.tr("dns_section_networkmanager", "[NetworkManager]"),
            *nm_details,
        ]
        return success, "\n".join(lines).strip()
    return service.apply_vpn_dns_policy(targets=app._active_nm_dns_targets())


def normalize_dns_profile_choice(app, choice=None):
    selected = str(choice or _dns_choice_value(app) or "").strip()
    if selected in DNS_PROFILES:
        return selected
    is_custom_choice = _app_callback(app, "_is_custom_dns_choice")
    register_custom_choice = _app_callback(app, "_register_manual_dns_choice")
    if is_custom_choice is not None and is_custom_choice(selected):
        if register_custom_choice is not None:
            normalized = register_custom_choice(selected)
            if normalized:
                return normalized
        return selected
    return app.tr("dns_profile_system_auto", "System (DHCP/auto)")


def apply_dns_profile_choice_via_control(app, choice):
    normalized_choice = normalize_dns_profile_choice(app, choice)
    resolve_servers = _app_callback(app, "_dns_servers_for_choice")
    if resolve_servers is not None:
        servers = resolve_servers(normalized_choice)
    else:
        servers = DNS_PROFILES.get(normalized_choice)

    if normalized_choice == "System (DHCP/auto)":
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

    previous_dropin = app._read_dot_dropin()
    nm_ok, nm_details = app._apply_nm_dns_policy_to_targets(ignore_auto_dns=True)
    dropin_ok, dropin_detail = app._write_manual_dns_dropin(normalized_choice)
    restart_ok, restart_detail = app._restart_resolved_for_dns_policy()
    if dropin_ok and not restart_ok:
        restore_ok, restore_detail = app._restore_dot_dropin_backup(previous_dropin)
        if restore_ok:
            app._restart_resolved_for_dns_policy()
            dropin_detail = "NetMon DoT-Konfiguration wurde nach Fehler zurückgerollt."
        else:
            dropin_detail = "Rollback fehlgeschlagen: " + (
                restore_detail
                or "vorherige Konfiguration konnte nicht wiederhergestellt werden."
            )
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


def format_dns_profile_control_result(app, result, *, heading, action):
    dropin_state = str(result.get("dropin_state", "") or "").strip().lower()
    dropin_state_label = {
        "written": app.tr("dns_value_written", "written"),
        "removed": app.tr("dns_value_removed", "removed"),
        "updated": app.tr("dns_value_updated", "updated"),
    }.get(dropin_state, result.get("dropin_state", app.tr("dns_value_updated", "updated")))
    lines = [
        heading,
        _tr(app, "dns_action_value", "Aktion: {value}").format(value=action),
        _tr(app, "dns_profile_value", "Profil: {value}").format(
            value=result.get("choice", "-")
        ),
    ]
    servers = [
        str(server).strip()
        for server in (result.get("servers") or [])
        if str(server).strip()
    ]
    if servers:
        lines.append(
            _tr(app, "dns_server_value", "Server: {value}").format(
                value=" • ".join(servers)
            )
        )
    lines.extend(
        [
            _tr(app, "dns_result_value", "Ergebnis: {value}").format(
                value=_tr(app, "dns_result_successful", "erfolgreich")
                if result.get("success")
                else _tr(app, "dns_result_failed", "fehlgeschlagen")
            ),
            "",
            _tr(app, "dns_section_networkmanager", "[NetworkManager]"),
            *(
                result.get("nm_details")
                or [_tr(app, "dns_no_details_available", "Keine Details verfügbar.")]
            ),
            "",
            _tr(app, "dns_section_system", "[System]"),
            (
                _tr(
                    app,
                    "dns_dot_dropin_state_value",
                    "✔ NetMon-DoT-Konfiguration {value}",
                ).format(
                    value=dropin_state_label
                )
                if result.get("dropin_ok")
                else _tr(
                    app,
                    "dns_dot_dropin_error",
                    "✖ Fehler in der NetMon-DoT-Konfiguration: {detail}",
                ).format(
                    detail=result.get("dropin_detail")
                    or _tr(app, "dns_value_unknown", "unbekannt")
                )
            ),
            (
                _tr(
                    app,
                    "dns_resolved_restarted",
                    "✔ systemd-resolved neu gestartet",
                )
                if result.get("restart_ok")
                else _tr(
                    app,
                    "dns_resolved_restart_failed",
                    "✖ Fehler beim Neustart von systemd-resolved: {detail}",
                ).format(
                    detail=result.get("restart_detail")
                    or _tr(app, "dns_result_failed", "fehlgeschlagen")
                )
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
        app,
        result,
        heading=_tr(app, "dns_control_report_title", "=== DNS-Steuerung ==="),
        action=_tr(app, "dns_control_action_enable_user_dns", "Benutzer-DNS aktivieren"),
    )


def enforce_dns_policy(app):
    vpn_active = app.is_vpn_active()
    return use_vpn_dns(app) if vpn_active else use_user_dns(app)


def _translate_dns_policy_warning(app, warning: str) -> str:
    text = str(warning or "").strip()
    mapping = {
        "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt.": app.tr(
            "dns_warning_vpn_with_global_dns",
            "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt.",
        ),
        "NetMon DoT-Drop-in erzwingt globale DNS-Server trotz aktivem VPN-DNS.": app.tr(
            "dns_warning_dot_dropin_forces_global_dns",
            "NetMon DoT-Drop-in erzwingt globale DNS-Server trotz aktivem VPN-DNS.",
        ),
        "Docker/veth-Interfaces wurden erkannt. Diese erzeugen zusätzliche DNS-Kontexte, werden aber von DNS-Control ignoriert.": app.tr(
            "dns_warning_docker_veth_ignored",
            "Docker/veth-Interfaces wurden erkannt. Diese erzeugen zusätzliche DNS-Kontexte, werden aber von DNS-Control ignoriert.",
        ),
        "DNSSEC ist strikt aktiv, obwohl VPN-DNS erkannt wurde.": app.tr(
            "dns_warning_dnssec_strict_with_vpn_dns",
            "DNSSEC ist strikt aktiv, obwohl VPN-DNS erkannt wurde.",
        ),
        "Mehrere DNS-Quellen sind gleichzeitig sichtbar.": app.tr(
            "dns_warning_multiple_dns_sources",
            "Mehrere DNS-Quellen sind gleichzeitig sichtbar.",
        ),
        "DoT ist aktiv, während VPN-DNS genutzt wird. Das ist nicht automatisch falsch, sollte aber bewusst geprüft werden.": app.tr(
            "dns_warning_dot_active_with_vpn_dns",
            "DoT ist aktiv, während VPN-DNS genutzt wird. Das ist nicht automatisch falsch, sollte aber bewusst geprüft werden.",
        ),
    }
    return mapping.get(text, text)


def refresh_dns_policy_status(app):
    code, out = run_cmd(["resolvectl", "status"], timeout=8)
    evaluation = evaluate_dns_policy(app, out if code == 0 else "")
    conflicts = [
        _translate_dns_policy_warning(app, item)
        for item in list(evaluation.get("warnings") or [])
    ]
    conflicts_text = (
        app.tr("dns_conflicts_foreign_detected", "Fremde DNS erkannt")
        if evaluation.get("conflict")
        else (
            app.tr("dns_conflicts_none_value", "keine")
            if not conflicts
            else "; ".join(conflicts)
        )
    )
    app.dns_resolver_status_var.set(
        app.tr(
            "dns_status_active_resolver_value",
            "Aktiver Resolver: {resolver}",
        ).format(
            resolver=evaluation.get(
                "resolver_label",
                app.tr("dns_value_unknown", "unbekannt"),
            )
        )
    )
    app.dns_conflict_status_var.set(
        app.tr("dns_status_conflicts_value", "Konflikte: {conflicts}").format(
            conflicts=conflicts_text
        )
    )
    return {
        "resolver": evaluation.get(
            "resolver_label", app.tr("dns_value_unknown", "unbekannt")
        ),
        "conflicts": conflicts_text,
        "vpn_active": bool(evaluation.get("vpn_active")),
        "servers": list(evaluation.get("active_dns") or []),
        "dropin_present": bool(evaluation.get("dot_dropin_exists")),
        "dropin_conflict": bool(evaluation.get("dot_dropin_conflict")),
        "risk": evaluation.get("risk", app.tr("dns_value_unknown", "unbekannt")),
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
    return service.evaluate_dns_policy(resolvectl_output=resolvectl_output)


def show_dns_policy_result(app, text, *, startup=False):
    if not startup:
        _select_dns_tab(app)
        app.update_dns_output(text, append=True)
    refresh_dns_policy_status(app)


def apply_dns(
    app,
    choice=None,
    refresh_ui=True,
    update_choice_var=True,
    confirm_dnssec=True,
):
    controls_locked, lock_reason = app._dns_controls_locked()
    if controls_locked:
        locked_choice = choice
        if locked_choice is None:
            locked_choice = _dns_choice_value(app, None)
        if lock_reason == "vpn" and app.should_accept_vpn_dns_for_stealth(
            locked_choice or "System (DHCP/auto)",
            vpn_active=True,
        ):
            app.log_safe("DNS wird im Stealthmodus vom VPN-Profil verwaltet.")
            _refresh_dns_state(app, safe=True)
            return True
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
        _select_dns_tab(app)
        app.update_dns_output(result)
        app.log_safe(log_message)
        _refresh_dns_state(app, safe=True)
        return False

    choice = normalize_dns_profile_choice(app, choice)
    if update_choice_var:
        app._set_dns_choice_safe(choice)

    if confirm_dnssec and choice != "System (DHCP/auto)":
        confirmer = _app_callback(app, "confirm_dnssec_mode_activation")
        if confirmer is not None and not confirmer("DNS anwenden"):
            _select_dns_tab(app)
            app.update_dns_output(
                app.tr(
                    "dns_apply_cancelled_output",
                    "=== DNS anwenden ===\nStatus: abgebrochen\nGrund: DNSSEC Strict Mode wurde nicht bestätigt.",
                )
            )
            app.log_safe("DNS anwenden abgebrochen: DNSSEC Strict Mode nicht bestätigt")
            _refresh_dns_state(app, safe=True)
            return False

    _select_dns_tab(app)
    app.log_safe("DNS-Profil wird angewendet...")

    result = apply_dns_profile_choice_via_control(app, choice)
    app.update_dns_output(
        format_dns_profile_control_result(
            app,
            result,
            heading=app.tr("dns_apply_heading", "=== DNS anwenden ==="),
            action=app.tr("dns_apply_action", "apply DNS profile"),
        )
    )

    if not result["success"]:
        app.log_safe("DNS anwenden fehlgeschlagen")
        _refresh_dns_state(app)
        return False

    app.log_safe(f"DNS-Profil angewendet: {choice}")
    app.last_dns_consistency_ok = None
    app.last_dns_consistency_ts = 0.0
    app.dns_consistency_enabled = True
    app.dns_consistency_one_shot = True
    collect_dot_status = _app_callback(app, "_collect_dot_status")
    show_dot_status_result = _app_callback(app, "_show_dot_status_result")
    if collect_dot_status is not None and show_dot_status_result is not None:
        try:
            dot_status = collect_dot_status(run_test=False)
            show_dot_status_result(
                dot_status,
                startup=True,
                show_output=False,
                emit_chad_warning=False,
            )
        except Exception:
            pass
    try:
        app.rebuild_dns_guard_whitelist()
    except Exception:
        pass
    try:
        app.run_dns_guard_check_once(auto_repair=False)
    except Exception:
        pass
    app.dns_consistency_check_async(force=True)
    _refresh_dns_state(app)
    if refresh_ui:
        app.refresh_safe()
    return True
