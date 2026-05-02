"""Firewall controller helpers for NetMon."""

from __future__ import annotations

import ipaddress
import re
import threading
from tkinter import messagebox

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def parse_ufw_action(action_text):
    text = str(action_text or "").strip()
    if not text:
        return "", ""
    parts = text.upper().split()
    policy = parts[0] if parts else ""
    direction = ""
    for token in parts[1:]:
        if token in {"IN", "OUT"}:
            direction = token
            break
    if not direction:
        lower = text.lower()
        if " out" in lower or lower.endswith("out"):
            direction = "OUT"
        elif " in" in lower or lower.endswith("in"):
            direction = "IN"
    return policy, direction


def extract_ip_port_proto_from_ufw_to(to_text):
    text = str(to_text or "").strip()
    ip_val = None
    port_val = None
    proto_val = ""

    m = re.search(r"(?P<port>\d{1,5})/(?P<proto>tcp|udp)\b", text, re.IGNORECASE)
    if m:
        port_val = m.group("port")
        proto_val = m.group("proto").lower()
    else:
        m_port = re.search(r"\bport\s+(?P<port>\d{1,5})\b", text, re.IGNORECASE)
        if m_port:
            port_val = m_port.group("port")

    cleaned = (
        text.replace("[", " ").replace("]", " ").replace("(", " ").replace(")", " ")
    )
    for token in re.split(r"[\s,]+", cleaned):
        cand = token.strip()
        if not cand:
            continue
        try:
            ipaddress.ip_address(cand)
            ip_val = cand
            break
        except ValueError:
            continue

    return ip_val, port_val, proto_val


def is_ufw_non_rule_line(line):
    text = str(line or "").strip()
    if not text:
        return True

    lower = text.lower()
    meta_prefixes = (
        "status:",
        "new profiles:",
        "logging:",
        "protokollierung:",
        "voreinstellung:",
        "default:",
    )
    if lower.startswith(meta_prefixes):
        return True

    header_tokens = {
        "aktion",
        "action",
        "zu",
        "to",
        "von",
        "from",
    }
    compact = re.sub(r"\s+", " ", text).strip().lower()
    if compact in {
        "aktion zu von",
        "action to from",
        "to action from",
        "zu aktion von",
    }:
        return True
    if set(compact.split()) <= header_tokens and len(compact.split()) >= 2:
        return True

    if re.fullmatch(r"[-=]{3,}.*", text):
        return True

    return False


def parse_ufw_structured_rule(raw_line):
    line = str(raw_line or "").strip()
    if is_ufw_non_rule_line(line):
        return None

    line_norm = re.sub(r"\s+", " ", line).strip()
    action_match = re.search(
        r"\b(ALLOW|DENY|REJECT)\b(?:\s+(IN|OUT))?\b",
        line_norm,
        re.IGNORECASE,
    )
    if not action_match:
        return None

    policy = (action_match.group(1) or "").upper()
    direction = (action_match.group(2) or "").upper()

    to_field = line_norm[: action_match.start()].strip()
    from_field = line_norm[action_match.end() :].strip()
    if not to_field:
        return None

    is_ipv6 = "(v6)" in line.lower()
    to_clean = re.sub(r"\s*\(v6\)\s*", "", to_field, flags=re.IGNORECASE).strip()
    from_clean = re.sub(r"\s*\(v6\)\s*", "", from_field, flags=re.IGNORECASE).strip()

    interface = None
    target_base = to_clean
    m_iface = re.search(
        r"^(?P<target>.+?)\s+on\s+(?P<iface>[A-Za-z0-9_.:-]+)$",
        to_clean,
        re.IGNORECASE,
    )
    if m_iface:
        target_base = m_iface.group("target").strip()
        interface = m_iface.group("iface").strip()

    ip_val, port_val, proto_val = extract_ip_port_proto_from_ufw_to(target_base)

    category = "other"
    if interface:
        category = "interface"
    elif proto_val.lower() == "udp" and ip_val and port_val:
        category = "vpn_endpoint"
    elif port_val:
        category = "standard_port"

    if category == "interface":
        display = target_base or "Anywhere"
    elif category == "vpn_endpoint":
        display = f"{ip_val}:{port_val}/{proto_val}"
    elif category == "standard_port":
        if ip_val and proto_val:
            display = f"{ip_val}:{port_val}/{proto_val}"
        elif proto_val:
            display = f"{port_val}/{proto_val}"
        else:
            display = f"{port_val}"
    else:
        display = target_base or line_norm

    return {
        "direction": direction,
        "policy": policy,
        "interface": interface,
        "ip": ip_val,
        "port": port_val,
        "proto": proto_val,
        "is_ipv6": bool(is_ipv6),
        "raw": line,
        "to": to_clean,
        "from": from_clean,
        "category": category,
        "target_base": target_base,
        "display": display,
    }


def ip_sort_key(value):
    text = str(value or "").strip()
    if not text:
        return (2, "")
    try:
        addr = ipaddress.ip_address(text)
        return (0, addr.version, int(addr))
    except ValueError:
        return (1, text)


def ufw_rule_sort_key(rule):
    category = rule.get("category")
    policy = rule.get("policy") or ""
    direction = rule.get("direction") or ""
    if category == "interface":
        return ((rule.get("interface") or ""), direction, policy)
    if category == "standard_port":
        port = int(rule.get("port") or 0)
        proto = rule.get("proto") or ""
        return (port, proto, direction, policy, rule.get("display") or "")
    if category == "vpn_endpoint":
        return (
            ip_sort_key(rule.get("ip")),
            int(rule.get("port") or 0),
            direction,
            policy,
        )
    return (rule.get("display") or rule.get("raw") or "",)


def format_ufw_rule_lines(rules):
    if not rules:
        return ["(keine Regeln)"]

    dedup = {}
    for rule in rules:
        action = (rule.get("policy") or "-").upper() or "-"
        direction = (rule.get("direction") or "-").upper() or "-"
        target = (
            rule.get("display") or rule.get("to") or rule.get("raw") or "-"
        ).strip() or "-"
        iface = (rule.get("interface") or "-").strip() or "-"
        key = (action, direction, target, iface)
        dedup[key] = dedup.get(key, 0) + 1

    rows = sorted(
        dedup.items(),
        key=lambda item: (item[0][0], item[0][1], item[0][2], item[0][3]),
    )

    action_w = 6
    direction_w = 9
    target_w = 30
    iface_w = 18

    header = f"{'AKTION':<6} {'RICHTUNG':<9} {'ZIEL':<30} {'INTERFACE':<18}"
    sep = "-" * len(header)

    lines = [header, sep]
    for (action, direction, target, iface), count in rows:
        action = (action or "-")[:action_w]
        direction = (direction or "-")[:direction_w]
        iface = (iface or "-")[:iface_w]
        if len(target) > target_w:
            target = target[: target_w - 1] + "…"
        suffix = f" [DUP x{count}]" if count > 1 else ""
        lines.append(f"{action:<6} {direction:<9} {target:<30} {iface:<18}{suffix}")
    return lines


def format_ufw_status_grouped(
    status_label, default_in, default_out, rules, metadata=None
):
    v4_rules = [r for r in rules if not r.get("is_ipv6")]
    v6_rules = [r for r in rules if r.get("is_ipv6")]

    def by_cat(items, cat):
        return [r for r in items if r.get("category") == cat]

    metadata = metadata or []
    sections = [
        "Firewall-Status",
        f"Aktiv: {status_label}",
        f"Default IN: {default_in}",
        f"Default OUT: {default_out}",
    ]
    if metadata:
        sections.append("")
        sections.append("Metadaten")
        for item in metadata:
            sections.append(f"- {item}")

    sections.extend(
        [
            "",
            "=== INTERFACE REGELN (IPv4) ===",
            *format_ufw_rule_lines(by_cat(v4_rules, "interface")),
            "",
            "=== STANDARD PORTS (IPv4) ===",
            *format_ufw_rule_lines(by_cat(v4_rules, "standard_port")),
            "",
            "=== VPN ENDPOINTS (UDP IPv4) ===",
            *format_ufw_rule_lines(by_cat(v4_rules, "vpn_endpoint")),
        ]
    )

    v4_other = by_cat(v4_rules, "other")
    if v4_other:
        sections.extend(
            [
                "",
                "=== SONSTIGES (IPv4) ===",
                *format_ufw_rule_lines(v4_other),
            ]
        )

    sections.extend(
        [
            "",
            "=== INTERFACE REGELN (IPv6) ===",
            *format_ufw_rule_lines(by_cat(v6_rules, "interface")),
            "",
            "=== STANDARD PORTS (IPv6) ===",
            *format_ufw_rule_lines(by_cat(v6_rules, "standard_port")),
            "",
            "=== VPN ENDPOINTS (UDP IPv6) ===",
            *format_ufw_rule_lines(by_cat(v6_rules, "vpn_endpoint")),
        ]
    )

    v6_other = by_cat(v6_rules, "other")
    if v6_other:
        sections.extend(
            [
                "",
                "=== SONSTIGES (IPv6) ===",
                *format_ufw_rule_lines(v6_other),
            ]
        )

    return "\n".join(sections)


def get_killswitch_vpn_profiles(app):
    profiles = []
    seen = set()
    candidates = [app.active_wg_profile(), *app.list_wg_profiles()]
    for profile in candidates:
        name = (profile or "").strip()
        if not name or name in seen:
            continue
        endpoint_ip, endpoint_port = app.parse_vpn_endpoint(name)
        if endpoint_ip and endpoint_port:
            seen.add(name)
            profiles.append(name)
    return profiles


def get_killswitch_vpn_endpoints(app):
    endpoints = []
    seen = set()
    for profile in get_killswitch_vpn_profiles(app):
        endpoint_ip, endpoint_port = app.parse_vpn_endpoint(profile)
        key = (endpoint_ip, endpoint_port)
        if not endpoint_ip or not endpoint_port or key in seen:
            continue
        seen.add(key)
        endpoints.append(key)
    return endpoints


def verify_killswitch_rules(
    app,
    status_text,
    enabled,
    wg_ifaces=None,
    handshake_rules=None,
):
    wg_ifaces = sorted(
        {str(iface).strip() for iface in (wg_ifaces or []) if str(iface).strip()}
    )
    handshake_rules = sorted(
        {
            (str(ip).strip(), str(port).strip())
            for ip, port in (handshake_rules or [])
            if str(ip).strip() and str(port).strip()
        }
    )
    issues = []

    if not app._ufw_status_is_active(status_text):
        issues.append("UFW ist nicht aktiv.")
        return False, issues

    if enabled:
        if not app._ufw_default_policy_matches(
            status_text,
            incoming="deny",
            outgoing="deny",
        ):
            issues.append("UFW Default-Policy ist nicht auf deny/deny gesetzt.")
        if not app._ufw_has_interface_rule(status_text, "lo", "in"):
            issues.append("Loopback-IN-Regel fehlt.")
        if not app._ufw_has_interface_rule(status_text, "lo", "out"):
            issues.append("Loopback-OUT-Regel fehlt.")
        if not wg_ifaces and not handshake_rules:
            issues.append("Weder WireGuard-Interface noch Handshake-Regel vorhanden.")
        for wg_if in wg_ifaces:
            if not app._ufw_has_interface_rule(status_text, wg_if, "in"):
                issues.append(f"WireGuard-IN-Regel fehlt fuer {wg_if}.")
            if not app._ufw_has_interface_rule(status_text, wg_if, "out"):
                issues.append(f"WireGuard-OUT-Regel fehlt fuer {wg_if}.")
        for endpoint_ip, endpoint_port in handshake_rules:
            if not app._ufw_has_endpoint_rule(
                status_text,
                endpoint_ip,
                endpoint_port,
            ):
                issues.append(
                    f"Handshake-Regel fehlt fuer {endpoint_ip}:{endpoint_port}/udp."
                )

        return not issues, issues

    if not app._ufw_default_policy_matches(
        status_text,
        incoming="deny",
        outgoing="allow",
    ):
        issues.append("UFW Default-Policy ist nicht auf deny/allow zurueckgesetzt.")
    if app._ufw_has_interface_rule(status_text, "lo", "in"):
        issues.append("Loopback-IN-Regel ist noch vorhanden.")
    if app._ufw_has_interface_rule(status_text, "lo", "out"):
        issues.append("Loopback-OUT-Regel ist noch vorhanden.")
    for wg_if in wg_ifaces:
        if app._ufw_has_interface_rule(status_text, wg_if, "in"):
            issues.append(f"WireGuard-IN-Regel fuer {wg_if} ist noch vorhanden.")
        if app._ufw_has_interface_rule(status_text, wg_if, "out"):
            issues.append(f"WireGuard-OUT-Regel fuer {wg_if} ist noch vorhanden.")
    for endpoint_ip, endpoint_port in handshake_rules:
        if app._ufw_has_endpoint_rule(status_text, endpoint_ip, endpoint_port):
            issues.append(
                f"Handshake-Regel fuer {endpoint_ip}:{endpoint_port}/udp ist noch vorhanden."
            )
    return not issues, issues


def killswitch_is_on(app):
    wg_ifaces = sorted(set(app.get_wg_interfaces()))
    handshake_rules = get_killswitch_vpn_endpoints(app)
    with app.ufw_lock:
        rc, out = app._read_ufw_status(verbose=True)

    if rc != 0:
        return False

    verified, _issues = verify_killswitch_rules(
        app,
        out,
        enabled=True,
        wg_ifaces=wg_ifaces,
        handshake_rules=handshake_rules,
    )
    return verified


def recover_firewall_after_killswitch_failure(app):
    network_service = app._network_service()
    cmds = [
        ["sudo", "-n", "ufw", "default", "allow", "outgoing"],
        ["sudo", "-n", "ufw", "default", "deny", "incoming"],
        ["sudo", "-n", "ufw", "allow", "out", "53/udp"],
        ["sudo", "-n", "ufw", "allow", "out", "53/tcp"],
        ["sudo", "-n", "ufw", "allow", "out", "443/tcp"],
        ["sudo", "-n", "ufw", "allow", "out", "80/tcp"],
    ]
    with app.ufw_lock:
        for cmd in cmds:
            if network_service is not None:
                network_service.run(cmd, timeout=20)
            else:
                run_cmd(cmd, timeout=20)


def killswitch_on_sync(app, refresh_ui=True):
    if not app._try_begin_network_operation("Killswitch aktivieren"):
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        referenced_profiles = app._collect_referenced_vpn_profiles(include_active=True)
        wg_ifaces = sorted(
            set(app._collect_interface_rules_for_profiles(referenced_profiles))
        )
        wg_ifaces = sorted(set(wg_ifaces) | set(app.get_wg_interfaces()))
        handshake_rules = sorted(set(app.get_killswitch_vpn_endpoints()))
        for profile in app._collect_referenced_vpn_profiles(include_active=True):
            resolved = app.resolve_profile_family_runtime(profile, log_missing=False)
            app.log_debug(
                f"[DEBUG] UFW-Regeln für {profile} basieren auf "
                f"IPv4={resolved.get('effective_ipv4_interface') or '-'}, "
                f"IPv6={resolved.get('effective_ipv6_interface') or 'None'}"
            )
        if not wg_ifaces and not handshake_rules:
            app.log_safe(
                app.tr(
                    "killswitch_log_no_profile_with_endpoint",
                    "Kein WireGuard-Profil mit Endpoint gefunden – Killswitch kann nicht aktiviert werden.",
                )
            )
            return False

        network_service = app._network_service()
        with app.ufw_lock:
            rc_s, out_s = app._read_ufw_status()
            ufw_on = (rc_s == 0) and app._ufw_status_is_active(out_s)
            if not ufw_on:
                if network_service is not None:
                    rc_enable, out_enable = network_service.ufw_enable_force(timeout=20)
                else:
                    rc_enable, out_enable = run_cmd(
                        ["sudo", "-n", "ufw", "--force", "enable"],
                        timeout=20,
                    )
                if rc_enable != 0:
                    app.log_safe(
                        app.tr(
                            "killswitch_log_enable_failed_ufw",
                            "Killswitch-Aktivierung fehlgeschlagen: UFW konnte nicht aktiviert werden.",
                        )
                    )
                    if out_enable:
                        app.log_safe(out_enable)
                    return False

            cmds = [
                ["sudo", "-n", "ufw", "default", "deny", "outgoing"],
                ["sudo", "-n", "ufw", "default", "deny", "incoming"],
                ["sudo", "-n", "ufw", "allow", "in", "on", "lo"],
                ["sudo", "-n", "ufw", "allow", "out", "on", "lo"],
                ["sudo", "-n", "ufw", "allow", "out", "53/udp"],
                ["sudo", "-n", "ufw", "allow", "out", "53/tcp"],
                ["sudo", "-n", "ufw", "allow", "out", "443/tcp"],
                ["sudo", "-n", "ufw", "allow", "out", "80/tcp"],
            ]
            for wg_if in wg_ifaces:
                cmds.extend(
                    [
                        ["sudo", "-n", "ufw", "allow", "out", "on", wg_if],
                        ["sudo", "-n", "ufw", "allow", "in", "on", wg_if],
                    ]
                )
            for endpoint_ip, endpoint_port in handshake_rules:
                cmds.append(
                    [
                        "sudo",
                        "-n",
                        "ufw",
                        "allow",
                        "out",
                        "to",
                        endpoint_ip,
                        "port",
                        endpoint_port,
                        "proto",
                        "udp",
                    ]
                )

            command_failures = []
            for cmd in cmds:
                if network_service is not None:
                    rc_cmd, out_cmd = network_service.run(cmd, timeout=20)
                else:
                    rc_cmd, out_cmd = run_cmd(cmd, timeout=20)
                if rc_cmd != 0:
                    command_failures.append((cmd, out_cmd))

            rc_v, out_v = app._read_ufw_status(verbose=True)

        if command_failures:
            failed_cmd = " ".join(command_failures[0][0][3:])
            app.log_safe(
                app.tr(
                    "killswitch_log_enable_failed_command",
                    "Killswitch-Aktivierung fehlgeschlagen: UFW-Befehl fehlgeschlagen ({command}).",
                ).format(command=failed_cmd)
            )
            failure_out = command_failures[0][1]
            if failure_out:
                app.log_safe(failure_out)
            app._recover_firewall_after_killswitch_failure()
            if refresh_ui:
                app.refresh_safe()
            return False

        if rc_v != 0:
            app.log_safe(
                app.tr(
                    "killswitch_log_enable_failed_verify",
                    "Killswitch-Aktivierung fehlgeschlagen: UFW-Status konnte nicht verifiziert werden.",
                )
            )
            if out_v:
                app.log_safe(out_v)
            app._recover_firewall_after_killswitch_failure()
            if refresh_ui:
                app.refresh_safe()
            return False

        verified, issues = app._verify_killswitch_rules(
            out_v,
            enabled=True,
            wg_ifaces=wg_ifaces,
            handshake_rules=handshake_rules,
        )
        if not verified:
            app.log_safe(
                app.tr(
                    "killswitch_log_enable_incomplete",
                    "Killswitch-Aktivierung unvollstaendig: UFW-Regeln entsprechen nicht dem erwarteten Endzustand.",
                )
            )
            app.log_safe(
                app.tr("label_details_prefix", "Details: ") + "; ".join(issues[:3])
            )
            app._recover_firewall_after_killswitch_failure()
            if refresh_ui:
                app.refresh_safe()
            return False

        for endpoint_ip, endpoint_port in handshake_rules:
            app.log_safe(
                app.tr(
                    "killswitch_log_handshake_allowed",
                    "Killswitch: WireGuard Handshake erlaubt für {endpoint}",
                ).format(endpoint=f"{endpoint_ip}:{endpoint_port}")
            )
        if wg_ifaces:
            allowed_ifaces = ", ".join(wg_ifaces)
            app.log_safe(
                app.tr(
                    "killswitch_log_enabled_ifaces",
                    "Killswitch AN – nur Traffic über {ifaces}, Loopback und WireGuard-Handshake erlaubt.",
                ).format(ifaces=allowed_ifaces)
            )
        else:
            app.log_safe(
                app.tr(
                    "killswitch_log_enabled_basic",
                    "Killswitch AN – Loopback und WireGuard-Handshake erlaubt, Tunnelaufbau kann starten.",
                )
            )
        if refresh_ui:
            app.refresh_safe()
        return True
    finally:
        app._end_network_operation()


def killswitch_on(
    app,
    async_mode=True,
    ensure_sudo=True,
    refresh_ui=True,
    interactive_guard=True,
):
    if (
        interactive_guard
        and ensure_sudo
        and not app._confirm_danger_action(
            "killswitch:on",
            title=app.tr("killswitch_confirm_enable_title", "Killswitch aktivieren"),
            prompt=app.tr(
                "killswitch_confirm_enable_prompt",
                "Diese Aktion setzt UFW auf restriktive Regeln.\n"
                "Ohne aktiven VPN-Tunnel kann Internetzugang blockiert werden.\n\n"
                "Wirklich fortfahren?",
            ),
            cooldown_s=0,
            require_phrase="AUSFUEHREN",
        )
    ):
        app.log(
            app.tr(
                "killswitch_log_enable_cancelled",
                "Killswitch-Aktivierung abgebrochen.",
            )
        )
        return False

    if ensure_sudo and not app.ensure_sudo_session("Killswitch aktivieren"):
        return False
    if not async_mode:
        return app._killswitch_on_sync(refresh_ui=refresh_ui)

    def job():
        app._killswitch_on_sync(refresh_ui=refresh_ui)

    app.run_async(job)
    return True


def killswitch_off_sync(app, refresh_ui=True):
    if not app._try_begin_network_operation("Killswitch deaktivieren"):
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        network_service = app._network_service()
        with app.ufw_lock:
            rc_s, out_s = app._read_ufw_status()
            ufw_on = (rc_s == 0) and app._ufw_status_is_active(out_s)
            if not ufw_on:
                if network_service is not None:
                    rc_enable, out_enable = network_service.ufw_enable_force(timeout=20)
                else:
                    rc_enable, out_enable = run_cmd(
                        ["sudo", "-n", "ufw", "--force", "enable"],
                        timeout=20,
                    )
                if rc_enable != 0:
                    app.log_safe(
                        app.tr(
                            "killswitch_log_disable_failed_ufw",
                            "Killswitch-Deaktivierung fehlgeschlagen: UFW konnte nicht aktiviert werden.",
                        )
                    )
                    if out_enable:
                        app.log_safe(out_enable)
                    return False

            referenced_profiles = app._collect_referenced_vpn_profiles(
                include_active=True
            )
            configured_real_ifaces = set(
                app._collect_interface_rules_for_profiles(referenced_profiles)
            )
            active_ifaces = {
                str(iface).strip()
                for iface in app.get_wg_interfaces()
                if str(iface).strip()
            }
            wg_ifaces = sorted(configured_real_ifaces | active_ifaces)
            wg_ifaces = sorted({w for w in wg_ifaces if w})
            handshake_rules = sorted(set(app.get_killswitch_vpn_endpoints()))

            cleanup_cmds = [
                ["sudo", "-n", "ufw", "delete", "allow", "in", "on", "lo"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "on", "lo"],
            ]
            for wg_if in wg_ifaces:
                cleanup_cmds.extend(
                    [
                        [
                            "sudo",
                            "-n",
                            "ufw",
                            "delete",
                            "allow",
                            "out",
                            "on",
                            wg_if,
                        ],
                        ["sudo", "-n", "ufw", "delete", "allow", "in", "on", wg_if],
                    ]
                )
            for endpoint_ip, endpoint_port in handshake_rules:
                cleanup_cmds.append(
                    [
                        "sudo",
                        "-n",
                        "ufw",
                        "delete",
                        "allow",
                        "out",
                        "to",
                        endpoint_ip,
                        "port",
                        endpoint_port,
                        "proto",
                        "udp",
                    ]
                )

            for cmd in cleanup_cmds:
                if network_service is not None:
                    network_service.run(cmd, timeout=20)
                else:
                    run_cmd(cmd, timeout=20)

            default_cmds = [
                ["sudo", "-n", "ufw", "default", "allow", "outgoing"],
                ["sudo", "-n", "ufw", "default", "deny", "incoming"],
            ]
            command_failures = []
            for cmd in default_cmds:
                if network_service is not None:
                    rc_cmd, out_cmd = network_service.run(cmd, timeout=20)
                else:
                    rc_cmd, out_cmd = run_cmd(cmd, timeout=20)
                if rc_cmd != 0:
                    command_failures.append((cmd, out_cmd))

            rc_v, out_v = app._read_ufw_status(verbose=True)

        if command_failures:
            failed_cmd = " ".join(command_failures[0][0][3:])
            app.log_safe(
                app.tr(
                    "killswitch_log_disable_failed_command",
                    "Killswitch-Deaktivierung fehlgeschlagen: UFW-Befehl fehlgeschlagen ({command}).",
                ).format(command=failed_cmd)
            )
            failure_out = command_failures[0][1]
            if failure_out:
                app.log_safe(failure_out)
            if refresh_ui:
                app.refresh_safe()
            return False

        if rc_v != 0:
            app.log_safe(
                app.tr(
                    "killswitch_log_disable_failed_verify",
                    "Killswitch-Deaktivierung fehlgeschlagen: UFW-Status konnte nicht verifiziert werden.",
                )
            )
            if out_v:
                app.log_safe(out_v)
            if refresh_ui:
                app.refresh_safe()
            return False

        verified, issues = app._verify_killswitch_rules(
            out_v,
            enabled=False,
            wg_ifaces=wg_ifaces,
            handshake_rules=handshake_rules,
        )
        if not verified:
            app.log_safe(
                app.tr(
                    "killswitch_log_disable_incomplete",
                    "Killswitch-Deaktivierung unvollstaendig: UFW-Regeln entsprechen nicht dem erwarteten Endzustand.",
                )
            )
            app.log_safe(
                app.tr("label_details_prefix", "Details: ") + "; ".join(issues[:3])
            )
            if refresh_ui:
                app.refresh_safe()
            return False

        app.log_safe(
            app.tr(
                "killswitch_log_disabled",
                "Killswitch AUS – UFW bleibt aktiv, normales Routing wieder erlaubt.",
            )
        )
        if refresh_ui:
            app.refresh_safe()
        return True
    finally:
        app._end_network_operation()


def killswitch_off(
    app,
    async_mode=True,
    ensure_sudo=True,
    refresh_ui=True,
    interactive_guard=True,
):
    if (
        interactive_guard
        and ensure_sudo
        and not app._confirm_danger_action(
            "killswitch:off",
            title=app.tr(
                "killswitch_confirm_disable_title",
                "Killswitch deaktivieren",
            ),
            prompt=app.tr(
                "killswitch_confirm_disable_prompt",
                "Diese Aktion hebt restriktive Killswitch-Regeln auf.\n"
                "Danach ist normales Routing wieder erlaubt.\n\n"
                "Wirklich fortfahren?",
            ),
            cooldown_s=0,
            require_phrase="AUSFUEHREN",
        )
    ):
        app.log(
            app.tr(
                "killswitch_log_disable_cancelled",
                "Killswitch-Deaktivierung abgebrochen.",
            )
        )
        return False

    if ensure_sudo and not app.ensure_sudo_session("Killswitch deaktivieren"):
        return False
    if not async_mode:
        return app._killswitch_off_sync(refresh_ui=refresh_ui)

    def job():
        app._killswitch_off_sync(refresh_ui=refresh_ui)

    app.run_async(job)
    return True


def read_ufw_status(verbose=False):
    cmd = ["sudo", "-n", "ufw", "status"]
    if verbose:
        cmd.append("verbose")
    return run_cmd(cmd, timeout=12 if verbose else 8)


def ufw_status_is_active(status_text):
    text = (status_text or "").strip().lower()
    if "inactive" in text or "inaktiv" in text:
        return False
    if "status:" in text and ("active" in text or "aktiv" in text):
        return True
    if "status:" in text and ("inactive" not in text) and ("inaktiv" not in text):
        return True
    return False


def ufw_rule_lines(status_text):
    lines = []
    for line in (status_text or "").splitlines():
        line_l = line.strip().lower()
        if not line_l:
            continue
        if line_l.startswith(("status:", "to", "--", "action", "from")):
            continue
        if line_l.startswith(("default:", "voreinstellung:")):
            continue
        lines.append(line_l)
    return lines


def ufw_default_policy_matches(status_text, incoming=None, outgoing=None):
    text = (status_text or "").lower()
    if (
        incoming == "deny"
        and "deny (incoming)" not in text
        and "deny (eingehend)" not in text
    ):
        return False
    if (
        outgoing == "deny"
        and "deny (outgoing)" not in text
        and "deny (abgehend)" not in text
    ):
        return False
    if (
        outgoing == "allow"
        and "allow (outgoing)" not in text
        and "allow (abgehend)" not in text
    ):
        return False
    return True


def ufw_has_interface_rule(status_text, iface, direction):
    iface = (iface or "").strip().lower()
    direction = (direction or "").strip().lower()
    if not iface or direction not in {"in", "out"}:
        return False
    for line in ufw_rule_lines(status_text):
        if (
            "allow" not in line and "zulassen" not in line
        ) or f"on {iface}" not in line:
            continue
        if re.search(rf"\b{direction}\b", line):
            return True
    return False


def ufw_has_endpoint_rule(status_text, endpoint_ip, endpoint_port):
    endpoint_ip = str(endpoint_ip or "").strip().lower()
    endpoint_port = str(endpoint_port or "").strip().lower()
    if not endpoint_ip or not endpoint_port:
        return False
    for line in ufw_rule_lines(status_text):
        if "allow" not in line and "zulassen" not in line:
            continue
        if endpoint_ip not in line or endpoint_port not in line:
            continue
        if "udp" not in line:
            continue
        if re.search(r"\bout\b", line):
            return True
    return False


def ufw_existing_rule_keys(status_text):
    keys = set()
    for raw_line in (status_text or "").splitlines():
        parsed = parse_ufw_structured_rule(raw_line)
        if not parsed:
            continue
        policy = (parsed.get("policy") or "").upper()
        direction = (parsed.get("direction") or "").upper()
        if policy != "ALLOW":
            continue

        iface = (parsed.get("interface") or "").strip().lower()
        if iface and direction in {"IN", "OUT"}:
            keys.add(("iface", direction.lower(), iface))

        ip_val = (parsed.get("ip") or "").strip().lower()
        port = str(parsed.get("port") or "").strip().lower()
        proto = (parsed.get("proto") or "").strip().lower()
        if direction == "OUT" and proto == "udp" and ip_val and port:
            keys.add(("endpoint", ip_val, port))
    return keys


def ensure_ufw_rule_exists(rule, *, network_service=None, known_keys=None):
    rule_type = (rule or {}).get("type")
    known_keys = known_keys if isinstance(known_keys, set) else set()

    if rule_type == "interface":
        iface = str((rule or {}).get("iface") or "").strip()
        direction = str((rule or {}).get("direction") or "").strip().lower()
        if not iface or direction not in {"in", "out"}:
            return False, False, "ungültige Interface-Regel", known_keys
        key = ("iface", direction, iface.lower())
        if key in known_keys:
            return True, False, "exists", known_keys
        if network_service is not None:
            rc_cmd, out_cmd = network_service.ufw_allow_on_iface(
                direction, iface, timeout=20
            )
        else:
            rc_cmd, out_cmd = run_cmd(
                ["sudo", "-n", "ufw", "allow", direction, "on", iface],
                timeout=20,
            )
        if rc_cmd == 0:
            known_keys.add(key)
            return True, True, "added", known_keys
        return False, False, (out_cmd or "").strip() or "unknown", known_keys

    if rule_type == "endpoint":
        ip_val = str((rule or {}).get("ip") or "").strip()
        port = str((rule or {}).get("port") or "").strip()
        if not ip_val or not port:
            return False, False, "ungültige Endpoint-Regel", known_keys
        key = ("endpoint", ip_val.lower(), port.lower())
        if key in known_keys:
            return True, False, "exists", known_keys
        if network_service is not None:
            rc_cmd, out_cmd = network_service.ufw_allow_udp_endpoint(
                ip_val, port, timeout=20
            )
        else:
            rc_cmd, out_cmd = run_cmd(
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
        if rc_cmd == 0:
            known_keys.add(key)
            return True, True, "added", known_keys
        return False, False, (out_cmd or "").strip() or "unknown", known_keys

    return False, False, "unbekannter Regeltyp", known_keys


def parse_ufw_status_numbered(status_numbered_text):
    entries = []
    for raw in (status_numbered_text or "").splitlines():
        line = raw.strip()
        match = re.match(r"^\[\s*(\d+)\]\s+(.*)$", line)
        if not match:
            continue
        try:
            num = int(match.group(1))
        except ValueError:
            continue
        entries.append((num, match.group(2).strip()))
    return entries


def dedupe_vpn_ufw_rules():
    rc, out = run_cmd(["sudo", "-n", "ufw", "status", "numbered"], timeout=12)
    if rc != 0 or not (out or "").strip():
        return 0

    parsed_entries = []
    for num, rest in parse_ufw_status_numbered(out):
        parsed = parse_ufw_structured_rule(rest)
        if not parsed:
            continue
        if (parsed.get("policy") or "").upper() != "ALLOW":
            continue
        category = parsed.get("category")
        if category not in {"interface", "vpn_endpoint"}:
            continue

        key = (
            (parsed.get("policy") or "").upper(),
            (parsed.get("direction") or "").upper(),
            bool(parsed.get("is_ipv6")),
            category,
            (parsed.get("interface") or "").strip().lower(),
            (parsed.get("ip") or "").strip().lower(),
            str(parsed.get("port") or "").strip().lower(),
            (parsed.get("proto") or "").strip().lower(),
            (parsed.get("to") or "").strip().lower(),
            (parsed.get("from") or "").strip().lower(),
        )
        parsed_entries.append((num, key, parsed))

    buckets = {}
    for num, key, parsed in parsed_entries:
        buckets.setdefault(key, []).append((num, parsed))

    delete_nums = []
    for items in buckets.values():
        if len(items) <= 1:
            continue
        items_sorted = sorted(items, key=lambda x: x[0])
        for num, _parsed in items_sorted[1:]:
            delete_nums.append(num)

    if not delete_nums:
        return 0

    removed = 0
    for num in sorted(set(delete_nums), reverse=True):
        rc_del, _out_del = run_cmd(
            ["sudo", "-n", "ufw", "--force", "delete", str(num)],
            timeout=12,
        )
        if rc_del == 0:
            removed += 1
    return removed


def ufw_has_outgoing_port_rule(status_text, port, proto):
    port = str(port or "").strip()
    proto = str(proto or "").strip().lower()
    if not port or not proto:
        return False
    for line in ufw_rule_lines(status_text):
        if "allow" not in line and "zulassen" not in line:
            continue
        if not re.search(r"\bout\b", line):
            continue
        if proto not in line:
            continue
        if re.search(rf"\b{re.escape(port)}(?:/{re.escape(proto)})?\b", line):
            return True
    return False


def check_ufw_active(app):
    with app.ufw_lock:
        rc, out = app._read_ufw_status()
    if rc != 0:
        return False
    return app._ufw_status_is_active(out)


def check_ssh_rule_active(app):
    with app.ufw_lock:
        rc, out = app._read_ufw_status()
    if rc != 0:
        return None
    if not app._ufw_status_is_active(out):
        return None

    ssh_patterns = (
        r"(^|\s)22/tcp(\s|$)",
        r"(^|\s)ssh(\s|$)",
    )
    for line in app._ufw_rule_lines(out):
        if "allow" not in line and "zulassen" not in line:
            continue
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in ssh_patterns):
            return True
    return False


def fw_enable(app, interactive_guard=True):
    if interactive_guard and not app._confirm_danger_action(
        "firewall:enable",
        title=app.tr("firewall_confirm_enable_title", "Firewall aktivieren"),
        prompt=app.tr(
            "firewall_confirm_enable_prompt",
            "Diese Aktion aktiviert UFW systemweit.\n"
            "Dadurch kann sich das Netzwerkverhalten sofort ändern.\n\n"
            "Wirklich fortfahren?",
        ),
        cooldown_s=0,
        require_phrase="AUSFUEHREN",
    ):
        app.log(
            app.tr(
                "firewall_log_enable_cancelled",
                "Firewall-Aktivierung abgebrochen.",
            )
        )
        return

    if not app.ensure_sudo_session("Firewall aktivieren"):
        return

    def job():
        if app.check_ufw_active():
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "firewall_log_already_enabled",
                        "Firewall ist bereits aktiv.",
                    )
                ),
            )
            return

        rc, out = run_cmd(["sudo", "-n", "ufw", "--force", "enable"], timeout=40)

        if rc != 0:
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "firewall_log_enable_failed",
                        "Firewall konnte NICHT aktiviert werden",
                    )
                ),
            )
            if out:
                app.after(0, lambda: app.log(out))
        else:
            app.after(
                0,
                lambda: app.log(app.tr("firewall_log_enabled", "Firewall aktiviert.")),
            )

        app.after(0, app.refresh)

    app.run_async(job)


def fw_status(app):
    if not app.ensure_sudo_session("Firewall Status lesen"):
        return
    with app.ufw_lock:
        rc, out = run_cmd(["sudo", "-n", "ufw", "status", "verbose"], timeout=12)

    if rc != 0:
        app.log(
            app.tr(
                "firewall_log_status_read_failed",
                "Firewall-Status konnte nicht gelesen werden.",
            )
        )
        if out:
            app.log(out)
        return

    status_label = "unbekannt"
    default_in = "-"
    default_out = "-"
    metadata_lines = []
    structured_rules = []

    for raw_line in (out or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        if lower.startswith("status:"):
            status_label = line.split(":", 1)[1].strip() or "unbekannt"
            continue

        if lower.startswith("default:") or lower.startswith("voreinstellung:"):
            default_text = line.split(":", 1)[1].strip() if ":" in line else line
            match_in = re.search(
                r"(allow|deny|reject)\s*\((incoming|eingehend)\)",
                default_text,
                re.IGNORECASE,
            )
            match_out = re.search(
                r"(allow|deny|reject)\s*\((outgoing|abgehend|ausgehend)\)",
                default_text,
                re.IGNORECASE,
            )
            if match_in:
                default_in = match_in.group(1).upper()
            if match_out:
                default_out = match_out.group(1).upper()
            metadata_lines.append(line)
            continue

        if (
            lower.startswith("logging:")
            or lower.startswith("protokollierung:")
            or lower.startswith("new profiles:")
        ):
            metadata_lines.append(line)
            continue

        if is_ufw_non_rule_line(line):
            continue

        parsed = parse_ufw_structured_rule(line)
        if parsed is not None:
            structured_rules.append(parsed)

    summary = format_ufw_status_grouped(
        status_label=status_label,
        default_in=default_in,
        default_out=default_out,
        rules=structured_rules,
        metadata=metadata_lines,
    )
    app.log(summary)


def fw_disable(app, interactive_guard=True):
    if interactive_guard and not app._confirm_danger_action(
        "firewall:disable",
        title=app.tr("firewall_confirm_disable_title", "Firewall deaktivieren"),
        prompt=app.tr(
            "firewall_confirm_disable_prompt",
            "Diese Aktion deaktiviert UFW systemweit.\n"
            "Dein System kann dadurch unmittelbar weniger geschützt sein.\n\n"
            "Wirklich fortfahren?",
        ),
        cooldown_s=0,
        require_phrase="AUSFUEHREN",
    ):
        app.log(
            app.tr(
                "firewall_log_disable_cancelled",
                "Firewall-Deaktivierung abgebrochen.",
            )
        )
        return

    if not app.ensure_sudo_session("Firewall deaktivieren"):
        return

    def job():
        if not app.check_ufw_active():
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "firewall_log_already_disabled",
                        "Firewall ist bereits deaktiviert.",
                    )
                ),
            )
            return

        rc, out = run_cmd(["sudo", "-n", "ufw", "disable"], timeout=40)

        if rc != 0:
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "firewall_log_disable_failed",
                        "Firewall konnte NICHT deaktiviert werden",
                    )
                ),
            )
            if out:
                app.after(0, lambda: app.log(out))
        else:
            app.after(
                0,
                lambda: app.log(
                    app.tr("firewall_log_disabled", "Firewall deaktiviert.")
                ),
            )

        app.after(0, app.refresh)

    app.run_async(job)


def security_set_ufw_logging_high(app):
    if not app.ensure_sudo_session("UFW Logging HIGH setzen"):
        return
    rc, out = run_cmd(["sudo", "-n", "ufw", "logging", "high"], timeout=12)
    if rc != 0:
        rc, out = run_cmd(["ufw", "logging", "high"], timeout=12)
    if rc == 0:
        app.security_log_level = "HIGH"
        app.log("Security: UFW Logging auf HIGH gesetzt.")
        app._security_update_status("green" if app.security_monitoring else "gray")
    else:
        app.log(f"Security: UFW Logging HIGH fehlgeschlagen: {out}")


def allow_ssh_rule_async(app):
    if not app.ensure_sudo_session("SSH UFW-Regel setzen"):
        return

    def job():
        with app.ufw_lock:
            _, status_out = run_cmd(
                ["sudo", "-n", "ufw", "status", "numbered"], timeout=12
            )
        if status_out.strip():
            for line in status_out.splitlines():
                if re.search(
                    r"(^|[^0-9])22/tcp([^0-9]|$)",
                    line,
                    re.IGNORECASE,
                ) or re.search(r"(^|[^0-9])22([^0-9]|$)", line):
                    app.after(
                        0,
                        lambda: app.log(
                            app.tr(
                                "ssh_log_port_22_already_allowed",
                                "SSH/UFW: Port 22 ist bereits freigegeben.",
                            )
                        ),
                    )
                    app.after(0, app.refresh)
                    return

        with app.ufw_lock:
            rc, out = run_cmd(["sudo", "-n", "ufw", "allow", "22/tcp"], timeout=15)
        if rc == 0:
            msg = (out or "").strip() or app.tr("ssh_rule_set", "Regel gesetzt.")
            app.after(
                0,
                lambda m=msg: app.log(
                    app.tr("ssh_log_rule_set", "SSH/UFW gesetzt: {message}").format(
                        message=m
                    )
                ),
            )
        else:
            msg = (out or "").strip() or app.tr(
                "label_unknown_error",
                "unbekannter Fehler",
            )
            app.after(
                0,
                lambda m=msg: app.log(
                    app.tr(
                        "ssh_log_rule_set_failed",
                        "SSH/UFW setzen fehlgeschlagen: {message}",
                    ).format(message=m)
                ),
            )

        app.after(0, app.refresh)

    threading.Thread(target=job, daemon=True).start()


def remove_ssh_rule_async(app, auto=False):
    if not app.ensure_sudo_session("SSH UFW-Regeln entfernen"):
        return
    if not auto:
        ok = messagebox.askyesno(
            app.tr("ssh_remove_confirm_title", "Achtung"),
            app.tr(
                "ssh_remove_confirm_body",
                "Das entfernt UFW-Regeln für SSH (Port 22).\n"
                "Wenn du per SSH verbunden bist, kannst du dich aussperren.\n\n"
                "Wirklich fortfahren?",
            ),
        )
        if not ok:
            app.log(app.tr("ssh_log_cancelled", "SSH/UFW: Abgebrochen."))
            return

    def job():
        with app.ufw_lock:
            _, out = run_cmd(["sudo", "-n", "ufw", "status", "numbered"], timeout=12)
        if not out.strip():
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "ssh_log_status_numbered_unavailable",
                        "UFW status numbered leer/unverfügbar.",
                    )
                ),
            )
            return

        matches = []
        for line in out.splitlines():
            m = re.match(r"^\[\s*(\d+)\]\s+(.*)$", line.strip())
            if not m:
                continue
            num = int(m.group(1))
            rest = m.group(2)
            if re.search(r"(^|[^0-9])22([^0-9]|$)", rest):
                matches.append((num, rest))

        if not matches:
            app.after(
                0,
                lambda: app.log(
                    app.tr(
                        "ssh_log_no_port_22_rule",
                        "SSH/UFW: keine Port-22-Regel gefunden.",
                    )
                ),
            )
            return

        matches.sort(key=lambda x: x[0], reverse=True)
        for num, rest in matches:
            with app.ufw_lock:
                rc2, del_out = run_cmd(
                    ["sudo", "-n", "ufw", "--force", "delete", str(num)],
                    timeout=12,
                )
            if rc2 == 0:
                app.after(
                    0,
                    lambda r=rest: app.log(
                        app.tr(
                            "ssh_log_removed",
                            "SSH/UFW entfernt: {rule}",
                        ).format(rule=r)
                    ),
                )
            else:
                app.after(
                    0,
                    lambda o=del_out: app.log(
                        app.tr(
                            "ssh_log_delete_failed",
                            "SSH/UFW delete failed: {message}",
                        ).format(message=o)
                    ),
                )

        app.after(0, app.refresh)

    threading.Thread(target=job, daemon=True).start()
