"""Firewall controller helpers for NetMon."""

from __future__ import annotations

import importlib
import ipaddress
import re
import threading
import tkinter as tk
from contextlib import contextmanager
from tkinter import messagebox, ttk

try:
    from netmon.core.utils import call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import call_in_ui_thread

try:
    from netmon.core.command import run_cmd
except ModuleNotFoundError:
    from core.command import run_cmd


def _app_value(app, name, default=None):
    return app.__dict__.get(name, default)


def _app_var_get(app, name, default=""):
    var = _app_value(app, name)
    try:
        value = var.get()
    except Exception:
        value = default
    return str(value or default)


def _app_var_set(app, name, value):
    var = _app_value(app, name)
    if var is None:
        return False
    try:
        var.set(value)
    except Exception:
        return False
    return True


def _firewall_dialog_parent(app):
    return _app_value(app, "add_firewall_rule_dialog", app)


def _add_firewall_rule_form_values(app):
    return {
        "action_label": _app_var_get(app, "add_firewall_rule_action_var", "Erlauben"),
        "direction_label": _app_var_get(
            app, "add_firewall_rule_direction_var", "Eingehend"
        ),
        "protocol_label": _app_var_get(app, "add_firewall_rule_protocol_var", "TCP"),
        "port_text": _app_var_get(app, "add_firewall_rule_port_var", "").strip(),
        "source_text": (
            _app_var_get(app, "add_firewall_rule_source_var", "any").strip() or "any"
        ),
    }


def _add_firewall_rule_protocols(protocol_label):
    return {"TCP": ("tcp",), "UDP": ("udp",), "TCP + UDP": ("tcp", "udp")}.get(
        protocol_label,
        ("tcp",),
    )


def _firewall_rule_row_meta(app):
    meta = _app_value(app, "firewall_rule_row_meta", {})
    return meta if isinstance(meta, dict) else {}


def _refresh_firewall_views(app):
    try:
        app.refresh()
    except Exception:
        pass

    refresh_view = getattr(app, "refresh_firewall_transparency_view", None)
    if not callable(refresh_view):
        return

    try:
        refresh_view()
    except Exception:
        pass
    for delay in (250, 900):
        try:
            app.after(delay, refresh_view)
        except Exception:
            pass


def _schedule_firewall_refresh(app):
    try:
        call_in_ui_thread(app, app.refresh)
    except Exception:
        try:
            app.refresh()
        except Exception:
            pass


def _schedule_ufw_logging_light(app, delay=500):
    callback = _app_value(app, "update_ufw_logging_light")
    if not callable(callback):
        return
    try:
        app.after(delay, callback)
    except Exception:
        pass


def _firewall_logger(app):
    logger = getattr(app, "log_safe", None)
    if callable(logger):
        return logger
    return app.log


def _firewall_debug_logger(app):
    logger = getattr(app, "log_network_debug", None)
    if callable(logger):
        return logger
    return _firewall_logger(app)


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


def split_ufw_interface_clause(text):
    value = str(text or "").strip()
    match = re.search(
        r"^(?P<base>.+?)\s+on\s+(?P<iface>[A-Za-z0-9_.:-]+)$",
        value,
        re.IGNORECASE,
    )
    if not match:
        return value, None
    return match.group("base").strip(), match.group("iface").strip()


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
    to_clean = re.sub(
        r"\s+", " ", re.sub(r"\(v6\)", " ", to_field, flags=re.IGNORECASE)
    ).strip()
    from_clean = re.sub(
        r"\s+", " ", re.sub(r"\(v6\)", " ", from_field, flags=re.IGNORECASE)
    ).strip()

    target_base, target_interface = split_ufw_interface_clause(to_clean)
    source_base, source_interface = split_ufw_interface_clause(from_clean)
    interface = target_interface or source_interface

    if target_interface:
        to_clean = target_base
    if source_interface:
        from_clean = source_base

    ip_val, port_val, proto_val = extract_ip_port_proto_from_ufw_to(target_base)

    category = _ufw_rule_category(
        interface=interface,
        ip_val=ip_val,
        port_val=port_val,
        proto_val=proto_val,
    )
    display = _ufw_rule_display(
        category=category,
        target_base=target_base,
        line_norm=line_norm,
        ip_val=ip_val,
        port_val=port_val,
        proto_val=proto_val,
    )

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


def _ufw_rule_category(*, interface, ip_val, port_val, proto_val):
    if interface:
        return "interface"
    if str(proto_val or "").lower() == "udp" and ip_val and port_val:
        return "vpn_endpoint"
    if port_val:
        return "standard_port"
    return "other"


def _ufw_rule_display(
    *,
    category,
    target_base,
    line_norm,
    ip_val,
    port_val,
    proto_val,
):
    if category == "interface":
        return target_base or "Anywhere"
    if category == "vpn_endpoint":
        return f"{ip_val}:{port_val}/{proto_val}"
    if category == "standard_port":
        if ip_val and proto_val:
            return f"{ip_val}:{port_val}/{proto_val}"
        if proto_val:
            return f"{port_val}/{proto_val}"
        return f"{port_val}"
    return target_base or line_norm


def parse_ufw_numbered_rule(raw_line):
    line = str(raw_line or "").strip()
    match = re.match(r"^\[\s*(?P<number>\d+)\]\s+(?P<rule>.+)$", line)
    if not match:
        return None
    parsed = parse_ufw_structured_rule(match.group("rule"))
    if parsed is None:
        return None
    parsed["number"] = int(match.group("number"))
    parsed["numbered_raw"] = line
    return parsed


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


def ufw_rule_identity_key(rule):
    return (
        str(rule.get("policy") or "").upper(),
        str(rule.get("direction") or "").upper(),
        str(rule.get("display") or rule.get("target_base") or rule.get("to") or "")
        .strip()
        .lower(),
        str(rule.get("interface") or "").strip().lower(),
        str(rule.get("proto") or "").strip().lower(),
        str(rule.get("port") or "").strip().lower(),
        bool(rule.get("is_ipv6")),
        str(rule.get("ip") or "").strip().lower(),
        str(rule.get("from") or "").strip().lower(),
    )


def _firewall_rule_matches_selected(candidate, selected):
    return (
        str(candidate.get("policy") or "").upper()
        == str(selected.get("policy") or "").upper()
        and str(candidate.get("direction") or "").upper()
        == str(selected.get("direction") or "").upper()
        and str(candidate.get("proto") or "").lower()
        == str(selected.get("proto") or "").lower()
        and str(candidate.get("from") or "").strip()
        == str(selected.get("from") or "").strip()
        and str(candidate.get("to") or "").strip()
        == str(selected.get("to") or "").strip()
        and str(candidate.get("display") or "").strip()
        == str(selected.get("display") or "").strip()
        and str(candidate.get("interface") or "").strip()
        == str(selected.get("interface") or "").strip()
    )


def _format_firewall_rule_summary(rule):
    policy = str(rule.get("policy") or "-").upper()
    direction = str(rule.get("direction") or "-").upper()
    target = str(rule.get("display") or rule.get("to") or "-")
    source = str(rule.get("from") or "-")
    proto = str(rule.get("proto") or "").lower().strip() or "alle"
    return f"{policy} {direction} | {target} | {proto} | von {source}"


def _format_firewall_rule_summary_multiline(rule):
    return "\n".join(
        [
            f"Aktion: {str(rule.get('policy') or '-').upper()}",
            f"Richtung: {str(rule.get('direction') or '-').upper()}",
            f"Ziel: {str(rule.get('display') or rule.get('to') or '-')}",
            f"Protokoll: {str(rule.get('proto') or '').lower().strip() or 'alle'}",
            f"Quelle: {str(rule.get('from') or '-')}",
        ]
    )


def update_firewall_rule_remove_button_state(app, _event=None):
    button = _app_value(app, "firewall_rule_remove_button")
    table = _app_value(app, "firewall_rules_table")
    if button is None or table is None:
        return False
    try:
        has_selection = bool(table.selection())
        button.configure(state=("normal" if has_selection else "disabled"))
        return has_selection
    except Exception:
        return False


def on_firewall_rule_select(app, _event=None):
    update_firewall_rule_remove_button_state(app)
    table = _app_value(app, "firewall_rules_table")
    detail_vars = {
        "action": _app_value(app, "firewall_rule_detail_action_var"),
        "direction": _app_value(app, "firewall_rule_detail_direction_var"),
        "target": _app_value(app, "firewall_rule_detail_target_var"),
        "protocol": _app_value(app, "firewall_rule_detail_protocol_var"),
        "source": _app_value(app, "firewall_rule_detail_source_var"),
        "note": _app_value(app, "firewall_rule_detail_note_var"),
    }
    if table is None or any(var is None for var in detail_vars.values()):
        return

    def _set_default_details():
        try:
            detail_vars["action"].set("keine Auswahl")
            detail_vars["direction"].set("keine Auswahl")
            detail_vars["target"].set("Noch keine Firewall-Regel ausgewählt.")
            detail_vars["protocol"].set("keine Auswahl")
            detail_vars["source"].set("keine Auswahl")
            detail_vars["note"].set("kein Hinweis")
        except Exception:
            pass

    try:
        selection = table.selection()
    except Exception:
        selection = ()
    if not selection:
        _set_default_details()
        return
    meta = _app_value(app, "firewall_rule_row_meta", {}).get(selection[0], {})
    if not meta:
        _set_default_details()
        try:
            detail_vars["target"].set(
                "Details für die ausgewählte Regel sind nicht verfügbar."
            )
        except Exception:
            pass
        return

    target_text = str(meta.get("display") or meta.get("to") or "-")
    port = str(meta.get("port") or "").strip()
    interface = str(meta.get("interface") or "").strip()
    proto_text = str(meta.get("proto") or "").lower().strip() or "alle"
    if port and port not in target_text:
        target_text = f"{target_text} | Port {port}"
    if interface:
        target_text = f"{target_text} | IF {interface}"

    note = str(meta.get("note") or meta.get("direction_label") or "").strip()
    try:
        detail_vars["action"].set(str(meta.get("policy") or "-").upper())
        detail_vars["direction"].set(str(meta.get("direction") or "-").upper())
        detail_vars["target"].set(target_text)
        detail_vars["protocol"].set(proto_text)
        detail_vars["source"].set(str(meta.get("from") or "-"))
        detail_vars["note"].set(note or "kein Hinweis")
    except Exception:
        pass


def format_ufw_rule_lines(rules):
    if not rules:
        return ["(keine Regeln)"]

    dedup = {}
    for rule in rules:
        key = ufw_rule_identity_key(rule)
        current = dedup.get(key)
        if current is None:
            dedup[key] = {"rule": rule, "count": 1}
        else:
            current["count"] += 1

    rows = sorted(
        dedup.values(),
        key=lambda item: ufw_rule_sort_key(item["rule"]),
    )

    return [
        format_ufw_rule_line(item["rule"], duplicate_count=item["count"])
        for item in rows
    ]


def format_ufw_rule_line(rule, duplicate_count=1):
    action = str(rule.get("policy") or "-").upper()
    direction = str(rule.get("direction") or "-").upper()
    target = str(rule.get("display") or rule.get("to") or rule.get("raw") or "-")
    target = target.strip() or "-"
    if rule.get("is_ipv6") and "(v6)" not in target.lower():
        target = f"{target} (v6)"
    interface = str(rule.get("interface") or "").strip()
    if interface:
        target = f"{target} on {interface}"
    suffix = f" [DUP x{duplicate_count}]" if int(duplicate_count or 1) > 1 else ""
    return f"{action:<5} {direction:<3} {target}{suffix}"


def format_ufw_status_grouped(
    status_label, default_in, default_out, rules, metadata=None
):
    v4_rules = [r for r in rules if not r.get("is_ipv6")]
    v6_rules = [r for r in rules if r.get("is_ipv6")]

    def by_cat(items, cat):
        return [r for r in items if r.get("category") == cat]

    metadata = metadata or []
    sections = [
        "Firewall status",
        f"Active: {status_label}",
        f"Default IN: {default_in}",
        f"Default OUT: {default_out}",
    ]
    if metadata:
        sections.append("")
        sections.append("Metadata")
        for item in metadata:
            sections.append(f"- {item}")

    sections.extend(
        [
            "",
            "=== INTERFACE RULES (IPv4) ===",
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
                "=== OTHER (IPv4) ===",
                *format_ufw_rule_lines(v4_other),
            ]
        )

    sections.extend(
        [
            "",
            "=== INTERFACE RULES (IPv6) ===",
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
                "=== OTHER (IPv6) ===",
                *format_ufw_rule_lines(v6_other),
            ]
        )

    return "\n".join(sections)


def _instance_override(app, name):
    return (getattr(app, "__dict__", {}) or {}).get(name)


def _run_cmd(app, args, timeout=0, text=True):
    override = _instance_override(app, "run_cmd")
    if callable(override):
        return override(args, timeout=timeout, text=text)
    module_name = getattr(getattr(app, "__class__", None), "__module__", "")
    if module_name:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            module = None
        runner = getattr(module, "run_cmd", None) if module is not None else None
        if callable(runner):
            return runner(args, timeout=timeout, text=text)
    return run_cmd(args, timeout=timeout, text=text)


def _network_service_for(app):
    override = _instance_override(app, "_network_service")
    if callable(override):
        try:
            return override()
        except Exception:
            return None
    network_service = getattr(app, "_network_service", None)
    if callable(network_service):
        try:
            return network_service()
        except Exception:
            return None
    return None


def get_killswitch_vpn_profiles(app):
    override = _instance_override(app, "get_killswitch_vpn_profiles")
    if callable(override):
        try:
            return list(override())
        except Exception:
            return []
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
    override = _instance_override(app, "get_killswitch_vpn_endpoints")
    if callable(override):
        try:
            return list(override())
        except Exception:
            return []
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

    for line in status_text.splitlines():
        rule = parse_ufw_structured_rule(line)
        if rule and (
            rule["policy"] in {"DENY", "REJECT"}
            and not rule["interface"]
            and rule["to"] == "Anywhere"
            and rule["from"] == "Anywhere"
        ):
            issues.append(
                "Globale Sperrregel vorhanden; manuelle UFW-Pruefung erforderlich."
            )
            break

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
        for port, proto in (
            ("53", "udp"),
            ("53", "tcp"),
            ("80", "tcp"),
            ("443", "tcp"),
        ):
            if ufw_has_outgoing_port_rule(status_text, port, proto):
                issues.append(
                    f"Globale OUT-Regel {port}/{proto} hebt den Killswitch auf."
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


def _killswitch_failure_is_closed(status_text):
    """Require leading unrestricted deny rules for both UFW address families.

    Defaults alone cannot override successful ALLOW rules from a partial apply.
    This verifies UFW user rules, not existing conntrack sessions/before.rules.
    """
    if not re.search(r"^Status: active$", status_text, re.MULTILINE):
        return False
    first = {}
    for line in status_text.splitlines():
        rule = parse_ufw_structured_rule(line)
        if rule is None:
            if is_ufw_non_rule_line(line) or re.fullmatch(r"[-\s]+", line):
                continue
            return False  # Unknown policy (e.g. LIMIT) must not be skipped.
        if rule["direction"] not in {"IN", "OUT"}:
            return False  # An ambiguous rule must not be silently ignored.
        key = (rule["is_ipv6"], rule["direction"])
        first.setdefault(key, rule)
    for ipv6 in (False, True):
        for direction in ("IN", "OUT"):
            rule = first.get((ipv6, direction))
            if not rule or not (
                rule["policy"] == "DENY"
                and not rule["interface"]
                and rule["to"] == "Anywhere"
                and rule["from"] == "Anywhere"
            ):
                return False
    return True


def _recover_killswitch_failure_locked(app):
    """Fail closed; caller holds ufw_lock through apply, verify and recovery.

    Exact rollback is unavailable. Keep restrictive emergency rules and require
    manual recovery instead of guessing the previous policy. Never delete rules
    here: their ownership/pre-existence is unknown.
    """
    network_service = _network_service_for(app)
    commands = [
        ["insert", "1", "deny", "out", "from", "any", "to", "any"],
        ["insert", "1", "deny", "in", "from", "any", "to", "any"],
        ["default", "deny", "outgoing"],
        ["default", "deny", "incoming"],
        ["--force", "enable"],
    ]
    failures = False
    for command in commands:
        try:
            args = ["sudo", "-n", "ufw", *command]
            if network_service is not None:
                rc, _out = network_service.run(args, timeout=20)
            else:
                rc, _out = _run_cmd(app, args, timeout=20)
            failures |= rc != 0
        except Exception:  # noqa: BLE001 - recovery must continue after runner errors
            # Try the remaining restrictions even if one runner call raises.
            failures = True
    try:
        rc, status = app._read_ufw_status(verbose=True)
        verified = rc == 0 and _killswitch_failure_is_closed(status)
    except Exception:  # noqa: BLE001 - never report unverified recovery as success
        verified = False
    app.killswitch_recovery_required = True
    app.log_safe(
        "Killswitch-Fehler: keine exakte Wiederherstellung des vorherigen "
        "UFW-Zustands. Manuelle Firewall-Wiederherstellung erforderlich. "
        + (
            "Restriktive UFW-Notfallregeln fuer IPv4/IPv6 wurden verifiziert; "
            "bestehende Verbindungen und UFW-before-Regeln sind davon ausgenommen."
            if verified and not failures
            else "WARNUNG: UFW-Notfallsperre konnte nicht vollstaendig "
            "verifiziert werden; Netzwerkschutz ist NICHT garantiert."
        )
    )
    return verified and not failures


@contextmanager
def _killswitch_apply_guard(app):
    mutation = [False]
    try:
        yield mutation
    except Exception:
        if mutation[0]:
            _recover_killswitch_failure_locked(app)
        raise


def recover_firewall_after_killswitch_failure(app):
    lock = _instance_override(app, "ufw_lock")
    if lock is None:
        lock = threading.Lock()
        app.ufw_lock = lock
    with lock:
        return _recover_killswitch_failure_locked(app)


def _read_ufw_status_numbered(app):
    return _run_cmd(app, ["sudo", "-n", "ufw", "status", "numbered"], timeout=12)


def _log_killswitch_numbered_debug(app, label):
    debug_logger = _firewall_debug_logger(app)
    debug_logger(f"[DEBUG] UFW {label}:")
    rc, out = _read_ufw_status_numbered(app)
    if out:
        debug_logger(out)
    elif rc != 0:
        debug_logger(f"ufw status numbered fehlgeschlagen: rc={rc}")


def _known_killswitch_wg_ifaces(app, referenced_profiles=None):
    known = set()

    def add_iface(value):
        iface = str(value or "").strip()
        if iface:
            known.add(iface)

    for iface in _app_value(app, "wg_profiles", []) or []:
        add_iface(iface)
    for iface in app.get_wg_interfaces() or []:
        add_iface(iface)
    for slot in _app_value(app, "vpn_slots", []) or []:
        add_iface(slot.get("profile"))
    for slot in _app_value(app, "primary_vpn_slots", []) or []:
        add_iface(slot.get("profile"))
    for iface in ["proton", "proton-de", "USA", "USA__ipv4", "Irland", "NL"]:
        add_iface(iface)

    profiles = set()
    for profile in referenced_profiles or []:
        name = str(profile or "").strip()
        if name:
            profiles.add(name)
    if not profiles:
        collector = _instance_override(app, "_collect_referenced_vpn_profiles")
        if callable(collector):
            try:
                profiles.update(collector(include_active=True) or [])
            except Exception:
                pass
    if profiles:
        iface_collector = _instance_override(
            app, "_collect_interface_rules_for_profiles"
        )
        if callable(iface_collector):
            try:
                collected = iface_collector(sorted(profiles))
            except TypeError:
                collected = iface_collector(
                    sorted(profiles), include_family_candidates=True
                )
            except Exception:
                collected = []
            for iface in collected or []:
                add_iface(iface)

    return sorted({iface for iface in known if iface})


def _remove_residual_killswitch_rules(app, wg_ifaces, handshake_rules, *, strict=False):
    rc, out = _read_ufw_status_numbered(app)
    if rc != 0 or not (out or "").strip():
        if strict:
            raise RuntimeError("UFW-Regeln vor Killswitch-Aktivierung nicht lesbar")
        return 0

    allowed_ifaces = {"lo", *{str(iface).strip() for iface in (wg_ifaces or [])}}
    allowed_ifaces.discard("")
    allowed_endpoints = {
        (str(ip).strip(), str(port).strip())
        for ip, port in (handshake_rules or [])
        if str(ip).strip() and str(port).strip()
    }
    allowed_standard_ports = {
        ("53", "udp"),
        ("53", "tcp"),
        ("443", "tcp"),
        ("80", "tcp"),
    }

    delete_nums = []
    for num, rest in parse_ufw_status_numbered(out):
        parsed = parse_ufw_structured_rule(rest)
        if not parsed:
            continue
        if (parsed.get("policy") or "").upper() != "ALLOW":
            continue
        category = parsed.get("category")
        direction = (parsed.get("direction") or "").upper()
        should_delete = False
        if category == "interface":
            iface = (parsed.get("interface") or "").strip()
            should_delete = iface in allowed_ifaces and direction in {"IN", "OUT"}
        elif category == "vpn_endpoint":
            endpoint = (
                str(parsed.get("ip") or "").strip(),
                str(parsed.get("port") or "").strip(),
            )
            proto = (parsed.get("proto") or "").strip().lower()
            should_delete = (
                direction == "OUT" and proto == "udp" and endpoint in allowed_endpoints
            )
        elif category == "standard_port":
            port = str(parsed.get("port") or "").strip()
            proto = (parsed.get("proto") or "").strip().lower()
            should_delete = (
                direction == "OUT" and (port, proto) in allowed_standard_ports
            )
        if should_delete:
            delete_nums.append(num)

    removed = 0
    for num in sorted(set(delete_nums), reverse=True):
        rc_del, _out_del = _run_cmd(
            app,
            ["sudo", "-n", "ufw", "--force", "delete", str(num)],
            timeout=12,
        )
        if rc_del == 0:
            removed += 1
        elif strict:
            raise RuntimeError("UFW-Regel konnte nicht entfernt werden")
    return removed


def killswitch_on_sync(app, refresh_ui=True):
    begin_op = _instance_override(app, "_try_begin_network_operation")
    if callable(begin_op):
        started = begin_op("Killswitch aktivieren")
    else:
        started = True
    if not started:
        if refresh_ui:
            app.refresh_safe()
        return False
    refresh_after_failure = False
    try:
        collect_profiles = _instance_override(app, "_collect_referenced_vpn_profiles")
        if callable(collect_profiles):
            referenced_profiles = collect_profiles(include_active=True)
        else:
            profile_provider = _instance_override(app, "get_killswitch_vpn_profiles")
            referenced_profiles = (
                list(profile_provider()) if callable(profile_provider) else []
            )
        collect_ifaces = _instance_override(
            app, "_collect_interface_rules_for_profiles"
        )
        if callable(collect_ifaces):
            wg_ifaces = sorted(set(collect_ifaces(referenced_profiles)))
        else:
            wg_ifaces = []
        wg_ifaces = sorted(set(wg_ifaces) | set(app.get_wg_interfaces()))
        endpoint_provider = _instance_override(app, "get_killswitch_vpn_endpoints")
        if callable(endpoint_provider):
            handshake_rules = sorted(set(endpoint_provider()))
        else:
            handshake_rules = sorted(set(get_killswitch_vpn_endpoints(app)))
        log_debug = _instance_override(app, "log_debug")
        resolver = _instance_override(app, "resolve_profile_family_runtime")
        for profile in referenced_profiles:
            if not callable(log_debug) or not callable(resolver):
                break
            resolved = resolver(profile, log_missing=False)
            log_debug(
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

        non_ip_endpoints = []
        collector = _instance_override(app, "collect_non_ip_endpoint_profiles")
        if callable(collector):
            try:
                non_ip_endpoints = list(collector(referenced_profiles) or [])
            except Exception:
                non_ip_endpoints = []
        if non_ip_endpoints:
            detail_lines = [
                f"- {item.get('profile')}: {item.get('host')}"
                for item in non_ip_endpoints
                if item.get("profile") and item.get("host")
            ]
            warning_text = app.tr(
                "killswitch_warn_non_ip_endpoints",
                "Einige WireGuard-Profile nutzen Hostnamen statt fester IP-Adressen.\n"
                "Für die UFW-Handshake-Regeln des Killswitch werden diese Endpoints nicht übernommen.\n\n"
                "Betroffene Profile:\n{details}\n\n"
                "Empfehlung: feste Endpoint-IP verwenden, wenn der Killswitch diese Verbindung absichern soll.",
            ).format(details="\n".join(detail_lines) or "-")
            try:
                messagebox.showwarning(
                    app.tr(
                        "killswitch_warn_non_ip_endpoints_title",
                        "Killswitch-Hinweis zu WireGuard-Endpoints",
                    ),
                    warning_text,
                    parent=app,
                )
            except Exception:
                pass
            app.log_safe(warning_text)

        network_service = _network_service_for(app)
        with app.ufw_lock, _killswitch_apply_guard(app) as mutation:
            rc_s, out_s = app._read_ufw_status()
            if rc_s != 0:
                app.log_safe(
                    "Killswitch-Aktivierung abgebrochen: UFW-Status nicht lesbar."
                )
                return False
            ufw_on = app._ufw_status_is_active(out_s)
            mutation[0] = True
            if not ufw_on:
                if network_service is not None:
                    rc_enable, out_enable = network_service.ufw_enable_force(timeout=20)
                else:
                    rc_enable, out_enable = _run_cmd(
                        app,
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
                    _recover_killswitch_failure_locked(app)
                    return False

            _remove_residual_killswitch_rules(
                app, wg_ifaces, handshake_rules, strict=True
            )

            cmds = [
                ["sudo", "-n", "ufw", "default", "deny", "outgoing"],
                ["sudo", "-n", "ufw", "default", "deny", "incoming"],
                ["sudo", "-n", "ufw", "allow", "in", "on", "lo"],
                ["sudo", "-n", "ufw", "allow", "out", "on", "lo"],
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
                    rc_cmd, out_cmd = _run_cmd(app, cmd, timeout=20)
                if rc_cmd != 0:
                    command_failures.append((cmd, out_cmd))
                    break

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
                _recover_killswitch_failure_locked(app)
                refresh_after_failure = refresh_ui
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
                _recover_killswitch_failure_locked(app)
                refresh_after_failure = refresh_ui
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
                _recover_killswitch_failure_locked(app)
                refresh_after_failure = refresh_ui
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
    except Exception as exc:  # noqa: BLE001 - expose activation failure after recovery
        app.log_safe(f"Killswitch-Aktivierung fehlgeschlagen: {type(exc).__name__}")
        if refresh_ui:
            app.refresh_safe()
        return False
    finally:
        end_op = _instance_override(app, "_end_network_operation")
        if callable(end_op):
            end_op()
        if refresh_after_failure:
            # refresh_safe can synchronously query killswitch_is_on and must
            # therefore run after the non-reentrant ufw_lock was released.
            app.refresh_safe()


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
    begin_op = _instance_override(app, "_try_begin_network_operation")
    if callable(begin_op):
        started = begin_op("Killswitch deaktivieren")
    else:
        started = True
    if not started:
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        network_service = _network_service_for(app)
        with app.ufw_lock:
            rc_s, out_s = app._read_ufw_status()
            ufw_on = (rc_s == 0) and app._ufw_status_is_active(out_s)
            if not ufw_on:
                if network_service is not None:
                    rc_enable, out_enable = network_service.ufw_enable_force(timeout=20)
                else:
                    rc_enable, out_enable = _run_cmd(
                        app,
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

            collect_profiles = _instance_override(
                app, "_collect_referenced_vpn_profiles"
            )
            if callable(collect_profiles):
                referenced_profiles = collect_profiles(include_active=True)
            else:
                list_profiles = _instance_override(app, "list_wg_profiles")
                referenced_profiles = (
                    list(list_profiles()) if callable(list_profiles) else []
                )
            collect_ifaces = _instance_override(
                app, "_collect_interface_rules_for_profiles"
            )
            if callable(collect_ifaces):
                configured_real_ifaces = set(collect_ifaces(referenced_profiles))
            else:
                configured_real_ifaces = set()
            active_ifaces = {
                str(iface).strip()
                for iface in app.get_wg_interfaces()
                if str(iface).strip()
            }
            wg_ifaces = sorted(configured_real_ifaces | active_ifaces)
            wg_ifaces = sorted({w for w in wg_ifaces if w})
            known_wg_ifaces = _known_killswitch_wg_ifaces(app, referenced_profiles)
            endpoint_provider = _instance_override(app, "get_killswitch_vpn_endpoints")
            if callable(endpoint_provider):
                handshake_rules = sorted(set(endpoint_provider()))
            else:
                handshake_rules = sorted(set(get_killswitch_vpn_endpoints(app)))

            _log_killswitch_numbered_debug(app, "vor Killswitch AUS")

            cleanup_cmds = [
                ["sudo", "-n", "ufw", "delete", "allow", "in", "on", "lo"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "on", "lo"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "53/udp"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "53/tcp"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "443/tcp"],
                ["sudo", "-n", "ufw", "delete", "allow", "out", "80/tcp"],
            ]
            for wg_if in known_wg_ifaces:
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
                    _run_cmd(app, cmd, timeout=20)

            _remove_residual_killswitch_rules(app, known_wg_ifaces, handshake_rules)

            default_cmds = [
                ["sudo", "-n", "ufw", "default", "allow", "outgoing"],
                ["sudo", "-n", "ufw", "default", "deny", "incoming"],
            ]
            command_failures = []
            for cmd in default_cmds:
                if network_service is not None:
                    rc_cmd, out_cmd = network_service.run(cmd, timeout=20)
                else:
                    rc_cmd, out_cmd = _run_cmd(app, cmd, timeout=20)
                if rc_cmd != 0:
                    command_failures.append((cmd, out_cmd))

            rc_v, out_v = app._read_ufw_status(verbose=True)

        _log_killswitch_numbered_debug(app, "nach Killswitch AUS")

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
            wg_ifaces=known_wg_ifaces,
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
        end_op = _instance_override(app, "_end_network_operation")
        if callable(end_op):
            end_op()


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


def read_ufw_status(app=None, verbose=False):
    cmd = ["sudo", "-n", "ufw", "status"]
    if verbose:
        cmd.append("verbose")
    if app is not None:
        return _run_cmd(app, cmd, timeout=12 if verbose else 8)
    return run_cmd(cmd, timeout=12 if verbose else 8)


def ufw_status_state(status_text):
    for raw_line in (status_text or "").splitlines():
        line = raw_line.strip().lower()
        if line == "status: active":
            return "active"
        if line == "status: inactive":
            return "inactive"
    return None


def ufw_status_is_active(status_text):
    return ufw_status_state(status_text) == "active"


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

        key = ufw_rule_identity_key(parsed)
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
                call_in_ui_thread(app, lambda: app.log(out))
        else:
            app.after(
                0,
                lambda: app.log(app.tr("firewall_log_enabled", "Firewall aktiviert.")),
            )

        call_in_ui_thread(app, app.refresh)

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
                call_in_ui_thread(app, lambda: app.log(out))
        else:
            app.after(
                0,
                lambda: app.log(
                    app.tr("firewall_log_disabled", "Firewall deaktiviert.")
                ),
            )

        call_in_ui_thread(app, app.refresh)

    app.run_async(job)


def security_set_ufw_logging_high(app):
    if not app.ensure_sudo_session("UFW Logging HIGH setzen"):
        return
    logger = _firewall_logger(app)
    debug_logger = _firewall_debug_logger(app)
    rc_before, out_before = run_cmd(["ufw", "status", "verbose"], timeout=5)
    debug_logger(f"[DEBUG BEFORE] ufw status verbose rc={rc_before}")
    debug_logger(f"[DEBUG BEFORE] {out_before}")
    rc, out = run_cmd(["sudo", "-n", "ufw", "logging", "high"], timeout=12)
    if rc != 0:
        rc, out = run_cmd(["ufw", "logging", "high"], timeout=12)
    if rc == 0:
        rc_after, out_after = run_cmd(["ufw", "status", "verbose"], timeout=5)
        debug_logger(f"[DEBUG AFTER] ufw status verbose rc={rc_after}")
        debug_logger(f"[DEBUG AFTER] {out_after}")
        app.security_log_level = app._security_query_log_level()
        logger(f"Security: UFW Logging auf {app.security_log_level} gesetzt.")
        app._security_update_status("green" if app.security_monitoring else "gray")
        _schedule_ufw_logging_light(app)
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
                    _schedule_firewall_refresh(app)
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

        _schedule_firewall_refresh(app)

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

        _schedule_firewall_refresh(app)

    threading.Thread(target=job, daemon=True).start()


def _is_valid_port_token(port_text):
    text = str(port_text or "").strip()
    if not text:
        return False
    if re.fullmatch(r"\d{1,5}", text):
        try:
            value = int(text)
        except ValueError:
            return False
        return 1 <= value <= 65535
    match = re.fullmatch(r"(\d{1,5}):(\d{1,5})", text)
    if not match:
        return False
    start = int(match.group(1))
    end = int(match.group(2))
    return 1 <= start <= end <= 65535


def _is_valid_source_token(source_text):
    text = str(source_text or "").strip()
    if not text or text.lower() == "any":
        return True
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        pass
    try:
        ipaddress.ip_network(text, strict=False)
        return True
    except ValueError:
        return False


def _validate_add_firewall_rule_form(app):
    values = _add_firewall_rule_form_values(app)

    action_map = {"Erlauben": "allow", "Blockieren": "deny"}
    direction_map = {"Eingehend": "in", "Ausgehend": "out"}

    errors = []
    warnings = []

    if not _is_valid_port_token(values["port_text"]):
        errors.append("Bitte einen gültigen Port oder Portbereich eingeben.")
    if not _is_valid_source_token(values["source_text"]):
        errors.append(
            'Quelle / Subnetz ist ungültig. Erlaubt sind "any", IP oder CIDR.'
        )

    protocols = _add_firewall_rule_protocols(values["protocol_label"])
    action = action_map.get(values["action_label"], "allow")
    direction = direction_map.get(values["direction_label"], "in")

    if values["source_text"].lower() == "any":
        warnings.append("Diese Regel gilt für jede Quelle.")
    if values["protocol_label"] == "TCP + UDP":
        warnings.append(
            "Diese Auswahl erstellt intern zwei Firewall-Regeln: TCP und UDP."
        )

    commands = []
    plain_parts = []
    for proto in protocols:
        commands.append(
            f"ufw {action} {direction} proto {proto} from {values['source_text']} to any port {values['port_text'] or '<Port fehlt>'}"
        )
        plain_parts.append(
            f"{'Erlaubt' if action == 'allow' else 'Blockiert'} "
            f"{'eingehenden' if direction == 'in' else 'ausgehenden'} "
            f"{proto.upper()}-Verkehr auf Port {values['port_text'] or '<Port fehlt>'} "
            f"von {values['source_text']}."
        )

    if errors:
        status_text = "Eingaben prüfen"
        status_color = "#b00020"
    elif warnings:
        status_text = "Bitte Hinweise beachten"
        status_color = "#9a6700"
    else:
        status_text = "Regel ist bereit"
        status_color = "#1a7f37"

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "commands": commands,
        "plain_parts": plain_parts,
        "status_text": status_text,
        "status_color": status_color,
    }


def _build_add_firewall_rule_command_args(app):
    validation = _validate_add_firewall_rule_form(app)
    if not validation["valid"]:
        return validation, []

    action_map = {"Erlauben": "allow", "Blockieren": "deny"}
    direction_map = {"Eingehend": "in", "Ausgehend": "out"}
    values = _add_firewall_rule_form_values(app)

    action = action_map.get(values["action_label"], "allow")
    direction = direction_map.get(values["direction_label"], "in")
    protocols = _add_firewall_rule_protocols(values["protocol_label"])

    commands = []
    for proto in protocols:
        commands.append(
            [
                "sudo",
                "-n",
                "ufw",
                action,
                direction,
                "proto",
                proto,
                "from",
                values["source_text"],
                "to",
                "any",
                "port",
                values["port_text"],
            ]
        )
    return validation, commands


def update_add_firewall_rule_preview(app, *_args):
    validation = _validate_add_firewall_rule_form(app)
    cmd = "\n".join(validation["commands"]) if validation["commands"] else ""
    plain = "\n".join(validation["plain_parts"]) if validation["plain_parts"] else ""
    _app_var_set(app, "add_firewall_rule_preview_cmd_var", cmd)
    _app_var_set(app, "add_firewall_rule_preview_plain_var", plain)
    notes = (
        validation["errors"] or validation["warnings"] or [validation["status_text"]]
    )
    _app_var_set(app, "add_firewall_rule_status_var", " | ".join(notes))
    label = _app_value(app, "add_firewall_rule_status_label")
    if label is not None:
        try:
            label.configure(foreground=validation["status_color"])
        except Exception:
            pass
    button = _app_value(app, "add_firewall_rule_apply_button")
    if button is not None:
        try:
            button.configure(state=("normal" if validation["valid"] else "disabled"))
        except Exception:
            pass
    return validation


def apply_add_firewall_rule(app):
    validation, commands = _build_add_firewall_rule_command_args(app)
    if not validation["valid"]:
        update_add_firewall_rule_preview(app)
        return False

    preview_text = "\n".join(validation["commands"])
    if not messagebox.askyesno(
        app.tr("firewall_rule_apply_title", "Firewall-Regel anwenden"),
        app.tr(
            "firewall_rule_apply_confirm",
            "Soll diese Firewall-Regel wirklich angewendet werden?\n\n{preview}",
        ).format(preview=preview_text),
        parent=_app_value(app, "add_firewall_rule_dialog", app),
    ):
        try:
            app.log("Firewall-Regel-Erstellung abgebrochen.")
        except Exception:
            pass
        return False

    if not app.ensure_sudo_session("Firewall-Regel hinzufügen"):
        return False

    apply_button = _app_value(app, "add_firewall_rule_apply_button")
    status_label = _app_value(app, "add_firewall_rule_status_label")
    if apply_button is not None:
        try:
            apply_button.configure(state="disabled")
        except Exception:
            pass
    _app_var_set(
        app,
        "add_firewall_rule_status_var",
        app.tr(
            "firewall_rule_apply_status_running",
            "Firewall-Regel wird angewendet...",
        ),
    )
    if status_label is not None:
        try:
            status_label.configure(foreground="#1a7f37")
        except Exception:
            pass

    comment_text = _app_var_get(app, "add_firewall_rule_comment_var", "").strip()

    def job():
        outputs = []
        failed = []
        with app.ufw_lock:
            for command in commands:
                rc, out = run_cmd(command, timeout=20)
                outputs.append((command, rc, out))
                if rc != 0:
                    failed.append((command, out))

        def done():
            if failed:
                _app_var_set(
                    app,
                    "add_firewall_rule_status_var",
                    app.tr(
                        "firewall_rule_apply_status_failed",
                        "Firewall-Regel konnte nicht angewendet werden.",
                    ),
                )
                if status_label is not None:
                    try:
                        status_label.configure(foreground="#b00020")
                    except Exception:
                        pass
                if apply_button is not None:
                    try:
                        apply_button.configure(state="normal")
                    except Exception:
                        pass
                details = "\n\n".join(
                    f'{" ".join(command)}\n{str(out or "").strip() or "Unbekannter Fehler"}'
                    for command, out in failed
                )
                messagebox.showerror(
                    app.tr("firewall_rule_dialog_title", "Firewall-Regel"),
                    app.tr(
                        "firewall_rule_apply_error",
                        "Firewall-Regel konnte nicht angewendet werden.\n\n{details}",
                    ).format(details=details),
                    parent=_firewall_dialog_parent(app),
                )
                try:
                    app.log("Firewall-Regel konnte nicht angewendet werden.")
                    for command, out in failed:
                        app.log(f'UFW Fehler: {" ".join(command)}')
                        if out:
                            app.log(str(out).strip())
                except Exception:
                    pass
                return

            rule_count = len(outputs)
            rule_word = "Regel" if rule_count == 1 else "Regeln"
            summary_lines = []
            try:
                for command, _rc, _out in outputs:
                    rendered = " ".join(command[3:])
                    summary_lines.append(rendered)
                    app.log("Firewall-Regel hinzugefügt: " + rendered)
                if comment_text:
                    app.log("Firewall-Regel Kommentar: " + comment_text)
            except Exception:
                pass
            try:
                info_lines = [f"{rule_count} Firewall-{rule_word} angewendet.", ""]
                info_lines.extend(summary_lines)
                if comment_text:
                    info_lines.extend(
                        [
                            "",
                            app.tr(
                                "firewall_rule_comment_prefix",
                                "Kommentar: {comment}",
                            ).format(comment=comment_text),
                        ]
                    )
                messagebox.showinfo(
                    app.tr("firewall_rule_dialog_title", "Firewall-Regel"),
                    "\n".join(info_lines),
                    parent=getattr(app, "add_firewall_rule_dialog", app),
                )
            except Exception:
                pass
            close_dialog = _app_value(app, "add_firewall_rule_dialog_close")
            if callable(close_dialog):
                try:
                    close_dialog()
                except Exception:
                    pass
            else:
                dialog = _app_value(app, "add_firewall_rule_dialog")
                try:
                    app.add_firewall_rule_dialog = None
                    dialog.destroy()
                except Exception:
                    pass
            _refresh_firewall_views(app)

        call_in_ui_thread(app, done)

    threading.Thread(target=job, daemon=True).start()
    return True


def remove_selected_firewall_rule(app):
    table = _app_value(app, "firewall_rules_table")
    if table is None:
        return False

    selection = table.selection()
    if not selection:
        messagebox.showwarning(
            app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
            app.tr(
                "firewall_rule_remove_select_first",
                "Bitte zuerst eine Firewall-Regel in der Tabelle auswählen.",
            ),
            parent=app,
        )
        return False

    row_id = selection[0]
    meta = _firewall_rule_row_meta(app).get(row_id)
    if not meta:
        messagebox.showerror(
            app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
            app.tr(
                "firewall_rule_remove_read_error",
                "Die ausgewählte Regel konnte nicht eindeutig gelesen werden.",
            ),
            parent=app,
        )
        return False

    summary = _format_firewall_rule_summary(meta)
    summary_multiline = _format_firewall_rule_summary_multiline(meta)
    warning = ""
    try:
        if str(meta.get("port") or "").strip() == "22":
            warning = "\n\nAchtung: Diese Regel betrifft Port 22 und kann SSH-Zugriff beeinflussen."
    except Exception:
        warning = ""

    if not messagebox.askyesno(
        app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
        app.tr(
            "firewall_rule_remove_confirm",
            "Soll diese Firewall-Regel wirklich entfernt werden?\n\n{summary}{warning}",
        ).format(summary=summary_multiline, warning=warning),
        parent=app,
    ):
        try:
            app.log("Firewall-Regel-Entfernung abgebrochen.")
        except Exception:
            pass
        return False

    if not app.ensure_sudo_session("Firewall-Regel entfernen"):
        return False

    def job():
        with app.ufw_lock:
            rc_status, out_status = run_cmd(
                ["sudo", "-n", "ufw", "status", "numbered"],
                timeout=20,
            )

        if rc_status != 0 or not str(out_status or "").strip():

            def _status_failed():
                messagebox.showerror(
                    app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
                    app.tr(
                        "firewall_rule_remove_status_unreadable",
                        "UFW status numbered konnte nicht gelesen werden.",
                    ),
                    parent=app,
                )
                try:
                    app.log(
                        "Firewall-Regel konnte nicht entfernt werden: status numbered nicht lesbar."
                    )
                    if out_status:
                        app.log(str(out_status).strip())
                except Exception:
                    pass

            call_in_ui_thread(app, _status_failed)
            return

        matches = []
        for raw_line in str(out_status or "").splitlines():
            parsed = parse_ufw_numbered_rule(raw_line)
            if parsed is None:
                continue
            if _firewall_rule_matches_selected(parsed, meta):
                matches.append(parsed)

        def _ambiguous_or_missing(message):
            messagebox.showerror(
                app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
                message,
                parent=app,
            )
            try:
                app.log(message)
            except Exception:
                pass

        if not matches:
            app.after(
                0,
                lambda: _ambiguous_or_missing(
                    "Die ausgewählte Firewall-Regel wurde in 'ufw status numbered' nicht gefunden."
                ),
            )
            return

        if len(matches) > 1:
            app.after(
                0,
                lambda: _ambiguous_or_missing(
                    "Die ausgewählte Firewall-Regel ist mehrfach vorhanden. "
                    "Löschung wurde zur Sicherheit abgebrochen.\n\n"
                    "Auswahl:\n"
                    + summary_multiline
                    + "\n\nGefundene UFW-Nummern: "
                    + ", ".join(str(item.get("number")) for item in matches)
                ),
            )
            return

        match = matches[0]
        with app.ufw_lock:
            rc_delete, out_delete = run_cmd(
                ["sudo", "-n", "ufw", "--force", "delete", str(match["number"])],
                timeout=20,
            )

        def done():
            if rc_delete != 0:
                messagebox.showerror(
                    app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
                    app.tr(
                        "firewall_rule_remove_failed",
                        "Firewall-Regel konnte nicht entfernt werden.\n\n{error}",
                    ).format(
                        error=(str(out_delete or "").strip() or "Unbekannter Fehler")
                    ),
                    parent=app,
                )
                try:
                    app.log("Firewall-Regel konnte nicht entfernt werden.")
                    if out_delete:
                        app.log(str(out_delete).strip())
                except Exception:
                    pass
                return

            try:
                app.log("Firewall-Regel entfernt: " + summary)
            except Exception:
                pass
            try:
                messagebox.showinfo(
                    app.tr("firewall_rule_remove_title", "Firewall-Regel entfernen"),
                    app.tr(
                        "firewall_rule_remove_success",
                        "Firewall-Regel entfernt.\n\n{summary}",
                    ).format(summary=summary_multiline),
                    parent=app,
                )
            except Exception:
                pass
            _refresh_firewall_views(app)

        call_in_ui_thread(app, done)

    threading.Thread(target=job, daemon=True).start()
    return True


def open_add_firewall_rule_dialog(app):
    existing = _app_value(app, "add_firewall_rule_dialog")
    try:
        if existing is not None and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return existing
    except Exception:
        pass

    win = tk.Toplevel(app)
    win.title("Firewall-Regel hinzufügen")
    win.transient(app)
    win.resizable(False, False)
    try:
        win.grab_set()
    except Exception:
        pass

    app.add_firewall_rule_dialog = win
    app.add_firewall_rule_action_var = tk.StringVar(value="Erlauben")
    app.add_firewall_rule_direction_var = tk.StringVar(value="Eingehend")
    app.add_firewall_rule_protocol_var = tk.StringVar(value="TCP")
    app.add_firewall_rule_port_var = tk.StringVar(value="")
    app.add_firewall_rule_source_var = tk.StringVar(value="any")
    app.add_firewall_rule_comment_var = tk.StringVar(value="")
    app.add_firewall_rule_preview_cmd_var = tk.StringVar(value="")
    app.add_firewall_rule_preview_plain_var = tk.StringVar(value="")
    app.add_firewall_rule_status_var = tk.StringVar(value="")

    container = ttk.Frame(win, padding=12)
    container.grid(row=0, column=0, sticky="nsew")
    win.columnconfigure(0, weight=1)
    win.rowconfigure(0, weight=1)
    for col in range(2):
        container.columnconfigure(col, weight=1)

    ttk.Label(
        container,
        text="Erstellt eine einfache UFW-Regel für Port, Richtung und Quelle.",
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

    ttk.Label(container, text="Aktion").grid(row=1, column=0, sticky="w")
    ttk.Label(container, text="Richtung").grid(row=1, column=1, sticky="w")

    action_combo = ttk.Combobox(
        container,
        textvariable=app.add_firewall_rule_action_var,
        values=("Erlauben", "Blockieren"),
        state="readonly",
    )
    action_combo.grid(row=2, column=0, sticky="ew", padx=(0, 6))
    direction_combo = ttk.Combobox(
        container,
        textvariable=app.add_firewall_rule_direction_var,
        values=("Eingehend", "Ausgehend"),
        state="readonly",
    )
    direction_combo.grid(row=2, column=1, sticky="ew", padx=(6, 0))

    ttk.Label(container, text="Protokoll").grid(
        row=3, column=0, sticky="w", pady=(10, 0)
    )
    ttk.Label(container, text="Port").grid(row=3, column=1, sticky="w", pady=(10, 0))

    protocol_combo = ttk.Combobox(
        container,
        textvariable=app.add_firewall_rule_protocol_var,
        values=("TCP", "UDP", "TCP + UDP"),
        state="readonly",
    )
    protocol_combo.grid(row=4, column=0, sticky="ew", padx=(0, 6))
    port_entry = ttk.Entry(container, textvariable=app.add_firewall_rule_port_var)
    port_entry.grid(row=4, column=1, sticky="ew", padx=(6, 0))
    ttk.Label(
        container,
        text="Beispiel: 22, 443 oder 8000:8010",
    ).grid(row=5, column=1, sticky="w", padx=(6, 0), pady=(4, 0))

    ttk.Label(container, text="Quelle / Subnetz").grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(10, 0)
    )
    source_entry = ttk.Entry(container, textvariable=app.add_firewall_rule_source_var)
    source_entry.grid(row=7, column=0, columnspan=2, sticky="ew")
    ttk.Label(
        container,
        text='Leer oder "any" erlaubt jede Quelle. Beispiel: 192.168.1.10 oder 10.0.0.0/24',
    ).grid(row=8, column=0, columnspan=2, sticky="w", pady=(4, 0))

    ttk.Label(container, text="Kommentar").grid(
        row=9, column=0, columnspan=2, sticky="w", pady=(10, 0)
    )
    comment_entry = ttk.Entry(container, textvariable=app.add_firewall_rule_comment_var)
    comment_entry.grid(row=10, column=0, columnspan=2, sticky="ew")

    preview_group = ttk.LabelFrame(container, text="Vorschau", padding=8)
    preview_group.grid(row=11, column=0, columnspan=2, sticky="ew", pady=(12, 0))
    preview_group.columnconfigure(0, weight=1)
    app.add_firewall_rule_status_label = ttk.Label(
        preview_group,
        textvariable=app.add_firewall_rule_status_var,
        wraplength=460,
        justify="left",
    )
    app.add_firewall_rule_status_label.grid(row=0, column=0, sticky="w", pady=(0, 6))
    ttk.Label(preview_group, text="UFW-Befehl").grid(row=1, column=0, sticky="w")
    ttk.Label(
        preview_group,
        textvariable=app.add_firewall_rule_preview_cmd_var,
        justify="left",
    ).grid(row=2, column=0, sticky="w", pady=(2, 6))
    ttk.Label(
        preview_group,
        textvariable=app.add_firewall_rule_preview_plain_var,
        wraplength=460,
        justify="left",
    ).grid(row=3, column=0, sticky="w")

    button_row = ttk.Frame(container)
    button_row.grid(row=12, column=0, columnspan=2, sticky="e", pady=(12, 0))

    def _close_dialog():
        try:
            win.grab_release()
        except Exception:
            pass
        app.add_firewall_rule_dialog = None
        app.add_firewall_rule_status_label = None
        app.add_firewall_rule_apply_button = None
        app.add_firewall_rule_dialog_close = None
        win.destroy()

    app.add_firewall_rule_dialog_close = _close_dialog

    ttk.Button(
        button_row,
        text="Abbrechen",
        command=_close_dialog,
    ).pack(side="left")
    app.add_firewall_rule_apply_button = ttk.Button(
        button_row,
        text="Regel anwenden",
        state="disabled",
        command=lambda: apply_add_firewall_rule(app),
    )
    app.add_firewall_rule_apply_button.pack(side="left", padx=(8, 0))

    win.protocol("WM_DELETE_WINDOW", _close_dialog)

    for var in (
        app.add_firewall_rule_action_var,
        app.add_firewall_rule_direction_var,
        app.add_firewall_rule_protocol_var,
        app.add_firewall_rule_port_var,
        app.add_firewall_rule_source_var,
    ):
        try:
            var.trace_add("write", lambda *_args: update_add_firewall_rule_preview(app))
        except Exception:
            pass

    update_add_firewall_rule_preview(app)
    try:
        port_entry.focus_set()
    except Exception:
        pass
    return win
