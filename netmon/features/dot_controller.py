"""DoT controller helpers for NetMon."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox
import os
import re
import shutil
import socket
import ssl
import tempfile
import threading
import time

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread

try:
    from netmon.config.constants import DOT_DROPIN_DIR, DOT_DROPIN_PATH, DOT_PROFILES
except ModuleNotFoundError:
    from config.constants import DOT_DROPIN_DIR, DOT_DROPIN_PATH, DOT_PROFILES

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def _app_value(app, name, default=None):
    return app.__dict__.get(name, default)


def _app_var_get(app, name, default=""):
    var = _app_value(app, name)
    if var is None:
        return default
    try:
        value = var.get()
    except Exception:
        value = default
    return value if value is not None else default


def _app_var_set(app, name, value) -> bool:
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _app_callback(app, name):
    callback = getattr(app, name, None)
    return callback if callable(callback) else None


def _preferred_dnssec_mode(app):
    callback = _app_callback(app, "get_preferred_dnssec_mode")
    if callback is None:
        return ""
    return str(callback() or "").strip().lower()


def _vpn_dns_active_state(app):
    callback = _app_callback(app, "is_vpn_dns_active")
    if callback is not None:
        return callback()
    return is_vpn_dns_active(app)


def _confirm_dot_activation(app, action_label):
    callback = _app_callback(app, "confirm_dnssec_mode_activation")
    if callback is None:
        return True
    return bool(callback(action_label))


def _dot_status_text(app, ok):
    if _app_value(app, "dot_vpn_conflict"):
        return "DoT: aktiv, aber VPN-Konflikt"
    if ok is True:
        return "DoT: aktiv / Test ok"
    if ok is None and app.dot_enabled:
        return "DoT: aktiv"
    if ok is False and app.dot_enabled:
        return "DoT: aktiv, aber Test fehlgeschlagen"
    if ok is False:
        return "DoT: deaktiviert"
    return "DoT: unbekannt"


def _dot_profile_text(profile: str) -> str:
    return f"Profil: {(profile or '').strip() or '–'}"


def _dot_server_text(servers) -> str:
    return "Server: " + (", ".join(servers or []) if servers else "–")


def _dot_mode_text(mode: str) -> str:
    return "Modus: " + ((mode or "").strip() or "–")


def _dot_last_test_text(timestamp: float) -> str:
    return "Letzter Test: " + datetime.fromtimestamp(timestamp).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def _dot_test_hint_text(status: dict) -> str:
    if not isinstance(status, dict):
        return ""
    text = str(status.get("text") or "")
    if not status.get("enabled"):
        return ""
    if "Test: unklar" in text or "Test: fehlgeschlagen" in text:
        return "Hinweis: Für den DoT-Test Killswitch kurz AUS schalten."
    return ""


def set_dot_profile_choice_safe(app, choice):
    if threading.current_thread() is threading.main_thread():
        _app_var_set(app, "dot_choice", choice)
        return
    call_in_ui_thread(app, lambda c=choice: _app_var_set(app, "dot_choice", c))


def update_dot_light(app):
    if _app_value(app, "l_dot") is None:
        return
    if _app_value(app, "dot_vpn_conflict"):
        app.set_light(app.l_dot, "red")
    elif app.dot_last_test_ok is True:
        app.set_light(app.l_dot, "green")
    elif app.dot_enabled:
        app.set_light(app.l_dot, "green")
    elif _app_value(app, "dot_vpn_dns_active"):
        app.set_light(app.l_dot, "yellow")
    elif app.dot_last_test_ok is False:
        app.set_light(app.l_dot, "red")
    else:
        app.set_light(app.l_dot, "gray")


def update_dot_light_safe(app):
    if threading.current_thread() is threading.main_thread():
        update_dot_light(app)
        return
    call_in_ui_thread(app, lambda: update_dot_light(app))


def set_dot_state(
    app,
    ok,
    *,
    profile="",
    servers=None,
    mode="",
    enabled=None,
    timestamp=None,
    vpn_conflict=None,
    vpn_active=None,
):
    app.dot_last_test_ok = ok
    app.dot_last_test_ts = float(timestamp or time.time())
    if enabled is not None:
        app.dot_enabled = bool(enabled)
    if vpn_conflict is not None:
        app.dot_vpn_conflict = bool(vpn_conflict)
    if vpn_active is not None:
        app.dot_vpn_dns_active = bool(vpn_active)

    profile_text = (profile or "").strip() or "–"
    if profile_text != "–":
        _app_var_set(app, "dot_choice", profile_text)
    _app_var_set(app, "dot_profile_var", _dot_profile_text(profile_text))
    _app_var_set(app, "dot_server_var", _dot_server_text(servers))
    _app_var_set(app, "dot_mode_var", _dot_mode_text(mode))
    _app_var_set(app, "dot_last_test_var", _dot_last_test_text(app.dot_last_test_ts))

    _app_var_set(app, "dot_status_var", _dot_status_text(app, ok))

    update_dot_light(app)


def set_dot_state_safe(app, ok, **kwargs):
    if threading.current_thread() is threading.main_thread():
        set_dot_state(app, ok, **kwargs)
        return
    call_in_ui_thread(app, lambda: set_dot_state(app, ok, **kwargs))


def dot_profile_config(app, profile_name=None):
    selected = str(profile_name or _app_var_get(app, "dot_choice", "") or "").strip()
    if selected not in DOT_PROFILES:
        selected = "Cloudflare"
    return selected, DOT_PROFILES[selected]


def build_dot_dropin_content(app, profile_name=None):
    selected, profile = dot_profile_config(app, profile_name)
    hostname = (profile.get("hostname") or "").strip()
    dnssec_mode = "allow-downgrade"
    if _preferred_dnssec_mode(app) == "strict":
        dnssec_mode = "yes"
    dns_entries = []
    for server in profile.get("dns") or []:
        entry = str(server).strip()
        if not entry:
            continue
        if hostname:
            entry = f"{entry}#{hostname}"
        dns_entries.append(entry)
    lines = [
        "# Managed by NetMon",
        "[Resolve]",
        f"DNS={' '.join(dns_entries)}",
        "DNSOverTLS=yes",
        f"DNSSEC={dnssec_mode}",
        "Domains=~.",
        "",
    ]
    return selected, profile, "\n".join(lines)


def parse_dot_dropin(text):
    servers = []
    hostnames = []
    mode = ""
    dnssec_mode = ""
    enabled = False
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key == "dns":
            for token in value.split():
                item = token.strip()
                if not item:
                    continue
                if "#" in item:
                    server, host = item.split("#", 1)
                    servers.append(server.strip())
                    if host.strip():
                        hostnames.append(host.strip())
                else:
                    servers.append(item)
        elif key == "dnsovertls":
            mode = value
            enabled = value.lower() in {"yes", "opportunistic", "true"}
        elif key == "dnssec":
            dnssec_mode = value
    return {
        "enabled": enabled,
        "mode": mode or "–",
        "dnssec_mode": dnssec_mode or "",
        "servers": servers,
        "hostname": hostnames[0] if hostnames else "",
    }


def read_dot_dropin(app):
    try:
        with open(DOT_DROPIN_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        return ""
    except Exception as exc:
        app.log_debug_safe(f"DoT-Drop-in lesen fehlgeschlagen: {exc}")
        return ""


def is_vpn_dns_active(app):
    service = app._dns_control_service()
    if service is None:
        code, out = run_cmd(["resolvectl", "status"], timeout=8)
        if code != 0:
            return False, out
        return app.detect_vpn_active(out), out
    code, out = service.read_resolvectl_status(timeout=8)
    if code != 0:
        return False, out
    return service.detect_vpn_active(out), out


def detect_netmon_dot_dropin_conflict(app, path=None):
    service = app._dns_control_service()
    if service is None:
        path = path or DOT_DROPIN_PATH
        if not os.path.isfile(path):
            return False, ""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception as exc:
            return True, f"Datei vorhanden, aber nicht lesbar: {exc}"
        conflict = "DNS=" in content and "Domains=~." in content
        return conflict, content
    return service.detect_netmon_dot_dropin_conflict(path)


def dot_leak_conflict_warning_text():
    return (
        "DNS-Konflikt erkannt:\n\n"
        "NetMon DoT-Drop-in erzwingt globale DNS-Server, während VPN-DNS "
        "aktiv ist.\n\n"
        "Das kann DNS-Leaks verursachen.\n\n"
        "Empfehlung: NetMon DoT-Drop-in entfernen oder VPN-DNS bevorzugen."
    )


def infer_dot_profile_name(servers):
    normalized = tuple((servers or []))
    for name, profile in DOT_PROFILES.items():
        if tuple(profile.get("dns") or []) == normalized:
            return name
    return ""


def _resolved_dot_profile_name(dropin_cfg: dict, status_cfg: dict) -> str:
    dropin_servers = list(dropin_cfg.get("servers") or [])
    status_servers = list(status_cfg.get("servers") or [])
    profile_name = infer_dot_profile_name(dropin_servers or status_servers)
    if not profile_name and dropin_servers:
        profile_name = infer_dot_profile_name(dropin_servers)
    return profile_name


def _resolved_dot_mode(dropin_cfg: dict, status_cfg: dict) -> str:
    mode = str(dropin_cfg.get("mode") or "").strip()
    if mode in {"", "–"}:
        mode = str(status_cfg.get("mode") or "").strip()
    return mode or "–"


def parse_dot_resolvectl_status(status_text):
    mode = ""
    servers = []
    current_server = ""
    status_lines = (status_text or "").splitlines()
    for idx, raw_line in enumerate(status_lines):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("DNSOverTLS setting:"):
            mode = line.split(":", 1)[1].strip()
        elif "Protocols:" in line and not mode:
            if "+DNSOverTLS" in line:
                mode = "yes"
            elif "-DNSOverTLS" in line:
                mode = "no"
        elif line.startswith("Current DNS Server:"):
            value = line.split(":", 1)[1].strip()
            current_server = value.split("#", 1)[0].strip()
            if current_server:
                servers.append(current_server)
        elif line.startswith("DNS Servers:"):
            values = [line.split(":", 1)[1].strip()]
            j = idx + 1
            while j < len(status_lines):
                cont = status_lines[j]
                if cont.startswith("         ") or cont.startswith("        "):
                    values.append(cont.strip())
                    j += 1
                    continue
                break
            for block in values:
                for token in block.split():
                    server = token.split("#", 1)[0].strip()
                    if server:
                        servers.append(server)
    deduped_servers = []
    for server in servers:
        if server not in deduped_servers:
            deduped_servers.append(server)
    return {
        "mode": mode or "–",
        "servers": deduped_servers,
        "current_server": current_server,
    }


def parse_dot_status_from_resolvectl(output: str):
    text = output or ""
    lowered = text.lower()

    if "+DNSOverTLS" in text:
        return "active"
    if re.search(r"\bdns\s+over\s+tls\s*:\s*(yes|true|active)\b", lowered):
        return "active"
    if re.search(r"\bdnsovertls\s+setting\s*:\s*(yes|true)\b", lowered):
        return "active"
    if re.search(r"\bdnsovertls\s*=\s*(yes|true)\b", lowered):
        return "active"

    if "-DNSOverTLS" in text:
        return "inactive"
    if re.search(r"\bdns\s+over\s+tls\s*:\s*(no|false|inactive)\b", lowered):
        return "inactive"
    if re.search(r"\bdnsovertls\s+setting\s*:\s*(no|false)\b", lowered):
        return "inactive"
    if re.search(r"\bdnsovertls\s*=\s*(no|false)\b", lowered):
        return "inactive"

    return "unknown"


def dot_preflight():
    checks = {
        "sudo": shutil.which("sudo") is not None,
        "install": shutil.which("install") is not None,
        "systemctl": shutil.which("systemctl") is not None,
        "resolvectl": shutil.which("resolvectl") is not None,
    }
    missing = [name for name, ok in checks.items() if not ok]
    active = False
    active_detail = "unbekannt"
    if checks["systemctl"]:
        rc, out = run_cmd(["systemctl", "is-active", "systemd-resolved"], timeout=4)
        active_detail = (out or "").strip() or "unknown"
        active = rc == 0 and active_detail == "active"
    return {
        "checks": checks,
        "missing": missing,
        "available": not missing,
        "resolved_active": active,
        "resolved_state": active_detail,
    }


def dot_tls_probe(server, hostname, timeout=4):
    if not server or not hostname:
        return None, "TLS-Probe übersprungen (Servername fehlt)."
    try:
        context = ssl.create_default_context()
        with socket.create_connection((server, 853), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname):
                return True, f"TLS-Verbindung zu {server}:853 erfolgreich."
    except Exception as exc:
        return False, f"TLS-Verbindung zu {server}:853 fehlgeschlagen: {exc}"


def _is_timeout_result(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    return "timed out" in lowered or "timeout" in lowered


def collect_dot_status(app, run_test=False):
    preflight = dot_preflight()
    dropin_text = read_dot_dropin(app)
    dropin_cfg = parse_dot_dropin(dropin_text)
    resolvectl_status = ""
    resolvectl_dns = ""
    query_out = ""
    query_ok = None
    tls_ok = None
    tls_detail = ""
    dropin_conflict, _dropin_conflict_content = detect_netmon_dot_dropin_conflict(app)

    if preflight["checks"].get("resolvectl"):
        _, resolvectl_dns = run_cmd(["resolvectl", "dns"], timeout=6)
        _, resolvectl_status = run_cmd(["resolvectl", "status"], timeout=10)

    vpn_active = app.detect_vpn_active(resolvectl_status)
    vpn_conflict = bool(dropin_conflict and vpn_active)
    status_cfg = parse_dot_resolvectl_status(resolvectl_status)
    servers = dropin_cfg["servers"] or status_cfg["servers"]
    profile_name = _resolved_dot_profile_name(dropin_cfg, status_cfg)
    mode = _resolved_dot_mode(dropin_cfg, status_cfg)
    resolvectl_dot_state = parse_dot_status_from_resolvectl(resolvectl_status)
    enabled = (bool(dropin_text.strip()) and dropin_cfg["enabled"]) or (
        resolvectl_dot_state == "active"
    )
    summary_lines = ["=== DNS over TLS Status ===", "Resolver: systemd-resolved"]

    status_available = preflight["checks"].get("systemctl") and preflight["checks"].get(
        "resolvectl"
    )

    if not status_available:
        summary_lines.extend(
            [
                "DNS over TLS ist auf diesem System aktuell nicht verfügbar.",
                "",
                "Benötigt werden:",
                "- systemd-resolved",
                "- resolvectl",
            ]
        )
        return {
            "ok": None,
            "enabled": False,
            "profile": profile_name,
            "servers": servers,
            "mode": mode,
            "vpn_conflict": vpn_conflict,
            "vpn_active": vpn_active,
            "text": "\n".join(summary_lines),
        }

    summary_lines.append(
        f"systemd-resolved: {preflight['resolved_state'] or 'unbekannt'}"
    )
    summary_lines.append(f"Profil: {profile_name or '–'}")
    summary_lines.append(f"Server: {', '.join(servers) if servers else '–'}")
    summary_lines.append(f"DNS over TLS: {'aktiviert' if enabled else 'deaktiviert'}")
    summary_lines.append(f"Modus: {mode or '–'}")
    summary_lines.append(
        f"NetMon DoT Drop-in: {'vorhanden' if dropin_text.strip() else 'nicht vorhanden'}"
    )
    summary_lines.append(
        f"Globale DNS-Erzwingung: {'JA' if dropin_conflict else 'NEIN'}"
    )
    summary_lines.append(f"VPN aktiv: {'JA' if vpn_active else 'NEIN'}")
    if vpn_conflict:
        summary_lines.append("")
        summary_lines.append("Bewertung: DNS-Leak-Risiko durch DoT/VPN-Konflikt")
        summary_lines.append(
            "Empfehlung: DoT-Drop-in entfernen oder VPN-DNS bevorzugen."
        )

    if not preflight["resolved_active"]:
        summary_lines.append("Hinweis: systemd-resolved läuft aktuell nicht.")
        return {
            "ok": None,
            "enabled": enabled,
            "profile": profile_name,
            "servers": servers,
            "mode": mode,
            "vpn_conflict": vpn_conflict,
            "vpn_active": vpn_active,
            "text": "\n".join(summary_lines),
        }

    if run_test:
        rc_query, query_out = run_cmd(["resolvectl", "query", "example.com"], timeout=8)
        query_ok = rc_query == 0 and bool((query_out or "").strip())
        query_timeout = rc_query == 124 or _is_timeout_result(query_out)
        hostname = ""
        if profile_name in DOT_PROFILES:
            hostname = (DOT_PROFILES[profile_name].get("hostname") or "").strip()
        elif dropin_cfg.get("hostname"):
            hostname = dropin_cfg["hostname"]
        if servers:
            tls_ok, tls_detail = dot_tls_probe(servers[0], hostname)
        tls_timeout = _is_timeout_result(tls_detail)
        config_ok = enabled and mode.lower() in {"yes", "opportunistic"}
        if config_ok and query_ok and tls_ok is not False:
            final_ok = True
        elif config_ok and (query_timeout or tls_timeout):
            final_ok = None
        elif config_ok:
            final_ok = False
        else:
            final_ok = False
        if vpn_conflict:
            final_ok = None
        if final_ok is True:
            summary_lines.append("Test: erfolgreich")
        elif final_ok is None:
            summary_lines.append("Test: unklar")
        else:
            summary_lines.append("Test: fehlgeschlagen")
        if query_ok:
            summary_lines.append("Resolver-Abfrage: OK")
        elif query_timeout:
            summary_lines.append("Resolver-Abfrage: Timeout")
        else:
            summary_lines.append("Resolver-Abfrage: fehlgeschlagen")
        if tls_ok is None:
            summary_lines.append("TLS-Probe: übersprungen")
        elif tls_timeout:
            summary_lines.append("TLS-Probe: Timeout")
        else:
            summary_lines.append(f"TLS-Probe: {'OK' if tls_ok else 'fehlgeschlagen'}")
        if tls_detail:
            summary_lines.append(f"Hinweis: {tls_detail}")
    else:
        if enabled and preflight["resolved_active"]:
            final_ok = True
        elif resolvectl_dot_state == "inactive" or not enabled:
            final_ok = False
        else:
            final_ok = None
        if vpn_conflict:
            final_ok = None
        if enabled:
            summary_lines.append("Test: nicht durchgeführt")
        else:
            summary_lines.append("Test: nicht möglich (DoT nicht aktiv)")

    if resolvectl_dns:
        summary_lines.append("")
        summary_lines.append("---- resolvectl dns ----")
        summary_lines.append(resolvectl_dns.strip())
    if run_test and query_out:
        summary_lines.append("")
        summary_lines.append("---- resolvectl query example.com ----")
        summary_lines.append(query_out.strip())

    return {
        "ok": final_ok,
        "enabled": enabled,
        "profile": profile_name,
        "servers": servers,
        "mode": mode,
        "vpn_conflict": vpn_conflict,
        "vpn_active": vpn_active,
        "text": "\n".join(summary_lines).strip(),
    }


def show_dot_status_result(
    app,
    status,
    *,
    append=False,
    startup=False,
    show_output=None,
    emit_chad_warning=None,
):
    if show_output is None:
        show_output = not startup
    if emit_chad_warning is None:
        emit_chad_warning = not startup
    if not startup:
        app.nb.select(app.tab_dns)
    if show_output:
        app.update_dns_output(status.get("text", ""), append=append)
    _app_var_set(app, "dot_test_hint_var", _dot_test_hint_text(status))
    set_dot_state(
        app,
        status.get("ok"),
        profile=status.get("profile", ""),
        servers=status.get("servers") or [],
        mode=status.get("mode", ""),
        enabled=status.get("enabled"),
        vpn_conflict=status.get("vpn_conflict"),
        vpn_active=status.get("vpn_active"),
    )
    if emit_chad_warning and status.get("vpn_conflict"):
        app.append_to_chad_output("DNS Warnung", dot_leak_conflict_warning_text())
    if startup:
        app.dot_last_test_var.set("Letzter Test: Startprüfung")
    app.update_dns_controls_state_safe()


def startup_dot_status_check(app):
    try:
        show_dot_status_async(app, startup=True)
    except TypeError:
        try:
            show_dot_status_async(app)
        except Exception as exc:
            try:
                app.log(f"[WARN] DoT-Startprüfung fehlgeschlagen: {exc}")
            except Exception:
                pass
    except Exception as exc:
        try:
            app.log(f"[WARN] DoT-Startprüfung fehlgeschlagen: {exc}")
        except Exception:
            pass


def show_dot_status_async(app, startup=False):
    if app.dot_running:
        if not startup:
            app.log_safe("DoT-Status läuft bereits.")
        return
    app.dot_running = True
    if not startup:
        app.nb.select(app.tab_dns)
        app.log_safe("DoT-Status wird geprüft")

    def job():
        try:
            status = collect_dot_status(app, run_test=False)
            app.after(
                0,
                lambda s=status: show_dot_status_result(
                    app,
                    s,
                    startup=startup,
                ),
            )
            if not startup:
                if status.get("enabled"):
                    app.log_safe("DoT-Status aktualisiert")
                else:
                    app.log_safe("DoT-Status geprüft")
        except Exception as exc:
            error_text = str(exc)

            def fail():
                app.dot_status_var.set("DoT: unbekannt")
                app.dot_last_test_var.set(
                    "Letzter Test: Startprüfung fehlgeschlagen"
                    if startup
                    else "Letzter Test: fehlgeschlagen"
                )
                _app_var_set(app, "dot_test_hint_var", "")
                app.dot_last_test_ok = None
                app.dot_vpn_conflict = False
                app.dot_vpn_dns_active = False
                update_dot_light(app)
                if not startup:
                    app.log(f"[WARN] DoT-Statusprüfung fehlgeschlagen: {error_text}")

            call_in_ui_thread(app, fail)
        finally:
            app.dot_running = False

    threading.Thread(target=job, daemon=True).start()


def enable_dot_async(app):
    if app.dot_running:
        app.log_safe("DoT-Aktivierung läuft bereits.")
        return
    app.update_dns_controls_state_safe()
    vpn_active, raw = _vpn_dns_active_state(app)
    if vpn_active:
        warning = app.tr(
            "dot_warning_vpn_active",
            "VPN-DNS ist aktiv.\n\n"
            "NetMon wird DNS over TLS nicht global erzwingen, weil dadurch "
            "VPN-DNS überschrieben und DNS-Leaks entstehen können.\n\n"
            "Bitte nutze VPN-DNS oder deaktiviere zuerst das VPN.",
        )
        messagebox.showwarning(
            app.tr("dot_warning_blocked_title", "DoT blockiert"),
            warning,
            parent=app,
        )
        result = (
            "=== DNS over TLS ===\n\n"
            "Status: Aktivierung blockiert\n"
            "Grund: VPN-DNS ist aktiv.\n\n"
            "NetMon hat keine Systemänderung durchgeführt, damit VPN-DNS "
            "nicht überschrieben wird."
        )
        if raw:
            result += "\n\n---- resolvectl status ----\n" + raw.strip()
        app.nb.select(app.tab_dns)
        app.update_dns_output(result, append=True)
        app.dot_vpn_conflict = True
        app.dot_vpn_dns_active = True
        app.dot_last_test_ok = None
        update_dot_light(app)
        app.log_safe("DoT-Aktivierung blockiert: VPN-DNS aktiv")
        app.update_dns_controls_state_safe()
        return
    if not _confirm_dot_activation(app, "DoT aktivieren"):
        app.nb.select(app.tab_dns)
        app.update_dns_output(
            "=== DNS over TLS ===\n\n"
            "Status: abgebrochen\n"
            "Grund: DNSSEC Strict Mode wurde nicht bestätigt.",
            append=False,
        )
        app.log_safe("DoT-Aktivierung abgebrochen: DNSSEC Strict Mode nicht bestätigt")
        app.update_dns_controls_state_safe()
        return
    if not app.ensure_sudo_session("DoT aktivieren"):
        return
    app.dot_running = True
    app.nb.select(app.tab_dns)
    app.update_dns_output(
        "=== DNS over TLS ===\nStatus: Aktivierung läuft\n",
        append=False,
    )
    app.log_safe("DoT-Aktivierung gestartet")

    def job():
        tmp_path = ""
        previous_dropin = read_dot_dropin(app)
        wrote_dropin = False
        try:
            profile_name, _profile, content = build_dot_dropin_content(app)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(content)
                tmp_path = temp_file.name
            rc_dir, out_dir = run_cmd(
                ["sudo", "-n", "mkdir", "-p", DOT_DROPIN_DIR],
                timeout=10,
            )
            if rc_dir != 0:
                raise RuntimeError(
                    (out_dir or "").strip()
                    or "Drop-in-Verzeichnis konnte nicht erstellt werden."
                )
            rc_install, out_install = run_cmd(
                ["sudo", "-n", "install", "-m", "644", tmp_path, DOT_DROPIN_PATH],
                timeout=12,
            )
            if rc_install != 0:
                raise RuntimeError(
                    (out_install or "").strip()
                    or "DoT-Drop-in konnte nicht geschrieben werden."
                )
            wrote_dropin = True
            rc_restart, out_restart = run_cmd(
                ["sudo", "-n", "systemctl", "restart", "systemd-resolved"],
                timeout=15,
            )
            if rc_restart != 0:
                raise RuntimeError(
                    (out_restart or "").strip()
                    or "systemd-resolved konnte nicht neu gestartet werden."
                )
            status = collect_dot_status(app, run_test=True)
            if not status.get("profile"):
                status["profile"] = profile_name
            call_in_ui_thread(app, lambda s=status: show_dot_status_result(app, s))
            call_in_ui_thread(app, app._start_dns_guard_transition)
            app.log_safe(
                "DoT-Test erfolgreich"
                if status.get("ok")
                else "DoT-Test fehlgeschlagen"
            )
            app.log_safe("DoT-Konfiguration aktualisiert")
        except Exception as exc:
            app.after(
                0,
                lambda e=str(exc): show_dot_status_result(
                    app,
                    {
                        "ok": False,
                        "enabled": False,
                        "profile": app.dot_choice.get(),
                        "servers": [],
                        "mode": "–",
                        "vpn_conflict": False,
                        "text": "\n".join(
                            [
                                "=== DNS over TLS ===",
                                "Aktion: aktivieren",
                                "Ergebnis: fehlgeschlagen",
                                f"Details: {e}",
                            ]
                        ),
                    },
                ),
            )
            app.log_safe("DoT-Test fehlgeschlagen")
            if wrote_dropin:
                try:
                    app._restore_dot_dropin_backup(previous_dropin)
                    app._restart_resolved_for_dns_policy()
                except Exception:
                    pass
        finally:
            app.dot_running = False
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    threading.Thread(target=job, daemon=True).start()


def disable_dot_async(app):
    if app.dot_running:
        app.log_safe("DoT-Deaktivierung läuft bereits.")
        return
    if not app.ensure_sudo_session("DoT deaktivieren"):
        return
    app.dot_running = True
    app.nb.select(app.tab_dns)
    app.update_dns_output(
        "=== DNS over TLS ===\nStatus: Deaktivierung läuft\n",
        append=False,
    )
    app.log_safe("DoT-Deaktivierung gestartet")

    def job():
        try:
            rc_rm, out_rm = run_cmd(
                ["sudo", "-n", "rm", "-f", DOT_DROPIN_PATH], timeout=10
            )
            if rc_rm != 0:
                raise RuntimeError(
                    (out_rm or "").strip()
                    or "DoT-Drop-in konnte nicht entfernt werden."
                )
            rc_restart, out_restart = run_cmd(
                ["sudo", "-n", "systemctl", "restart", "systemd-resolved"],
                timeout=15,
            )
            if rc_restart != 0:
                raise RuntimeError(
                    (out_restart or "").strip()
                    or "systemd-resolved konnte nicht neu gestartet werden."
                )
            app.after(
                0,
                lambda: show_dot_status_result(
                    app,
                    {
                        "ok": False,
                        "enabled": False,
                        "profile": "",
                        "servers": [],
                        "mode": "aus",
                        "vpn_conflict": False,
                        "text": "\n".join(
                            [
                                "=== DNS over TLS ===",
                                "Aktion: deaktivieren",
                                "Ergebnis: erfolgreich",
                                "Hinweis: NetMon-Drop-in entfernt und systemd-resolved neu gestartet.",
                            ]
                        ),
                    },
                ),
            )
            call_in_ui_thread(app, app._start_dns_guard_transition)
            app.log_safe("DoT-Konfiguration aktualisiert")
        except Exception as exc:
            app.after(
                0,
                lambda e=str(exc): show_dot_status_result(
                    app,
                    {
                        "ok": False,
                        "enabled": app.dot_enabled,
                        "profile": app.dot_choice.get(),
                        "servers": [],
                        "mode": "–",
                        "vpn_conflict": False,
                        "text": "\n".join(
                            [
                                "=== DNS over TLS ===",
                                "Aktion: deaktivieren",
                                "Ergebnis: fehlgeschlagen",
                                f"Details: {e}",
                            ]
                        ),
                    },
                ),
            )
            app.log_safe("DoT-Deaktivierung fehlgeschlagen")
        finally:
            app.dot_running = False

    threading.Thread(target=job, daemon=True).start()


def test_dot_async(app):
    if app.dot_running:
        app.log_safe("DoT-Test läuft bereits.")
        return
    app.dot_running = True
    app.nb.select(app.tab_dns)
    app.dot_status_var.set("DoT-Test läuft")
    _app_var_set(app, "dot_test_hint_var", "")
    app.update_dns_output(
        "=== DNS over TLS ===\nStatus: Test läuft\n",
        append=False,
    )
    app.log_safe("DoT-Test gestartet")

    def job():
        try:
            status = collect_dot_status(app, run_test=True)
            call_in_ui_thread(app, lambda s=status: show_dot_status_result(app, s))
            app.log_safe(
                "DoT-Test erfolgreich"
                if status.get("ok")
                else "DoT-Test fehlgeschlagen"
            )
        finally:
            app.dot_running = False

    threading.Thread(target=job, daemon=True).start()
