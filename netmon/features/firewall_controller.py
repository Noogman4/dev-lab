"""Firewall controller helpers for NetMon."""

from __future__ import annotations

import importlib
import hashlib
import ipaddress
import re
import threading
import time
import tkinter as tk
from collections import Counter
from contextlib import contextmanager, nullcontext
from functools import wraps
from tkinter import messagebox, ttk

from . import vpn_controller

try:
    from netmon.core import nm_ownership
    from netmon.core.killswitch_journal import KillswitchJournal as KillswitchJournal
    from netmon.core.killswitch_journal import PENDING
    from netmon.core.ufw_snapshot import UfwSnapshotClient as UfwSnapshotClient
    from netmon.core.ufw_snapshot import SnapshotError, valid_interface_name
except ModuleNotFoundError:
    from core import nm_ownership
    from core.killswitch_journal import KillswitchJournal as KillswitchJournal
    from core.killswitch_journal import PENDING
    from core.ufw_snapshot import UfwSnapshotClient as UfwSnapshotClient
    from core.ufw_snapshot import SnapshotError, valid_interface_name

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


def firewall_implementation_identity():
    """Record file identities at startup to distinguish same-version installs."""
    paths = {
        "controller": __file__,
        "snapshot": importlib.import_module(UfwSnapshotClient.__module__).__file__,
        "executed_helper": importlib.import_module(UfwSnapshotClient.__module__).HELPER,
        "app": importlib.import_module("netmon.app").__file__,
        "vpn": importlib.import_module("netmon.features.vpn_controller").__file__,
    }
    parts = []
    for label, path in paths.items():
        try:
            with open(path, "rb") as stream:
                digest = hashlib.sha256(stream.read()).hexdigest()
        except OSError:
            digest = "unreadable"
        parts.append(f"{label}={path} file_sha256={digest}")
    return "[FirewallDiag] " + " | ".join(parts)


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

    ports = r"\d{1,5}(?::\d{1,5})?(?:,\d{1,5}(?::\d{1,5})?)*"
    m = re.search(
        rf"(?:^|\s)(?P<port>{ports})/(?P<proto>tcp|udp)(?=\s|$)", text, re.IGNORECASE
    )
    if m:
        port_val = m.group("port")
        proto_val = m.group("proto").lower()
    else:
        m_port = re.search(rf"\bport\s+(?P<port>{ports})(?=\s|$)", text, re.IGNORECASE)
        if not m_port:
            # Without /proto UFW renders a standalone destination port.
            # Restrict this to the destination field, never address octets.
            m_port = re.search(rf"(?:^|\s)(?P<port>{ports})(?=\s|$)", text)
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

    if re.fullmatch(r"[-=\s]+", text):
        return True

    return False


def parse_ufw_structured_rule(raw_line):
    line = str(raw_line or "").split("#", 1)[0].strip()
    if is_ufw_non_rule_line(line):
        return None

    line_norm = re.sub(r"\s+", " ", line).strip()
    action_match = re.search(
        r"\b(ALLOW|DENY|REJECT|LIMIT)\b(?:\s+(IN|OUT|FWD))?\b",
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
    fields = []
    logtype = ""
    for value in (to_field, from_field):
        value = re.sub(
            r"\s+", " ", re.sub(r"\(v6\)", " ", value, flags=re.IGNORECASE)
        ).strip()
        marker = re.search(r"\s+\((log(?:-all)?)\)$", value, re.IGNORECASE)
        if marker:
            logtype = marker[1].lower()
            value = value[: marker.start()].rstrip()
        fields.append(value)
    to_clean, from_clean = fields

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
    if logtype:
        display = f"{display} ({logtype})"

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
    first_port = re.match(r"[0-9]+", str(rule.get("port") or ""))
    port = int(first_port[0]) if first_port else 0
    if category == "interface":
        return ((rule.get("interface") or ""), direction, policy)
    if category == "standard_port":
        proto = rule.get("proto") or ""
        return (port, proto, direction, policy, rule.get("display") or "")
    if category == "vpn_endpoint":
        return (
            ip_sort_key(rule.get("ip")),
            port,
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


def _network_operation_method(app, name):
    try:
        method = object.__getattribute__(app, name)
    except AttributeError:
        return None
    return method if callable(method) else None


def _run_cmd(app, args, timeout=0, text=True):
    transaction = _instance_override(app, "_active_firewall_snapshot")
    if (
        transaction is not None
        and list(args[:3]) == ["sudo", "-n", "ufw"]
        and list(args[3:4]) != ["status"]
    ):
        return transaction.run(args, timeout=timeout, text=text)
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
    transaction = _instance_override(app, "_active_firewall_snapshot")
    if transaction is not None:
        return transaction
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


def _snapshot_client_for(app):
    return _instance_override(app, "firewall_snapshots") or UfwSnapshotClient()


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


def select_killswitch_vpn_endpoints(app, status_text, *, referenced_profiles=None):
    """Use the same selected endpoints for apply and diagnostic verification."""
    provider = _network_operation_method(app, "get_killswitch_vpn_endpoints")
    candidates = (
        list(provider()) if callable(provider) else get_killswitch_vpn_endpoints(app)
    )
    if callable(_instance_override(app, "get_killswitch_vpn_endpoints")):
        return candidates  # Explicit injected providers supply a selected plan.
    profile_provider = _instance_override(app, "get_killswitch_vpn_profiles")
    if callable(profile_provider):
        referenced_profiles = profile_provider()
    elif referenced_profiles is None:
        collect = _network_operation_method(app, "_collect_referenced_vpn_profiles")
        referenced_profiles = (
            collect(include_active=True)
            if callable(collect)
            else get_killswitch_vpn_profiles(app)
        )
    selected = {
        _endpoint_key(*app.parse_vpn_endpoint(profile))
        for profile in referenced_profiles
    }
    for line in (status_text or "").splitlines():
        rule = parse_ufw_structured_rule(line)
        if (
            rule
            and rule["policy"] == "ALLOW"
            and rule["direction"] == "OUT"
            and rule["proto"] == "udp"
            and not rule["interface"]
            and rule["from"].lower() in {"anywhere", "any", "0.0.0.0/0", "::/0"}
            and rule["ip"]
        ):
            selected.add(_endpoint_key(rule["ip"], rule["port"]))
    return [
        endpoint
        for endpoint in candidates
        if _endpoint_key(*endpoint) is not None and _endpoint_key(*endpoint) in selected
    ]


def verify_killswitch_rules(
    app,
    status_text,
    enabled,
    wg_ifaces=None,
    handshake_rules=None,
    *,
    allow_empty_plan=False,
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

    first_interface_out = {}
    for line in status_text.splitlines():
        rule = parse_ufw_structured_rule(line)
        if rule and rule["direction"] == "OUT" and rule["interface"]:
            first_interface_out.setdefault((rule["is_ipv6"], rule["interface"]), rule)
        if rule is None and not is_ufw_non_rule_line(line):
            issues.append("UFW-Regel konnte nicht sicher ausgewertet werden.")
        if _is_global_block(rule):
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
        if not wg_ifaces and not handshake_rules and not allow_empty_plan:
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
        # Interface-bound rules on the active tunnels are not global grants.
        # A blocked interface must have an unrestricted leading DENY in both
        # families before its service rules receive the same treatment.
        safe_bound_interfaces = {"lo", *wg_ifaces}
        anywhere = {"anywhere", "any", "0.0.0.0/0", "::/0"}
        for iface in {key[1] for key in first_interface_out}:
            if all(
                (rule := first_interface_out.get((ipv6, iface)))
                and rule["policy"] == "DENY"
                and rule["to"].lower() in anywhere
                and rule["from"].lower() in anywhere
                for ipv6 in (False, True)
            ):
                safe_bound_interfaces.add(iface)
        for port, proto in (
            ("53", "udp"),
            ("53", "tcp"),
            ("80", "tcp"),
            ("443", "tcp"),
        ):
            if ufw_has_outgoing_port_rule(
                status_text,
                port,
                proto,
                handshake_rules=handshake_rules,
                ignore_interfaces=safe_bound_interfaces,
            ):
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


def _is_global_block(rule):
    anywhere = {"anywhere", "0.0.0.0/0", "::/0"}
    return bool(
        rule
        and rule["policy"] in {"DENY", "REJECT"}
        and rule["direction"] in {"IN", "OUT"}
        and not rule["interface"]
        and rule["to"].lower() in anywhere
        and rule["from"].lower() in anywhere
    )


def _journal_phase(app):
    journal = _instance_override(app, "killswitch_journal")
    return journal.phase() if journal is not None else "absent"


def _journal_mark(app, phase):
    journal = _instance_override(app, "killswitch_journal")
    try:
        if journal is not None:
            journal.mark(phase)
        return True
    except (OSError, ValueError):
        app.killswitch_recovery_required = True
        app.log_safe(
            "Killswitch-Zustand konnte nicht dauerhaft gespeichert werden; manuelle Prüfung erforderlich."
        )
        return False


def _protected_closed_plan(app):
    snapshots = _instance_override(app, "firewall_snapshots")
    if snapshots is None:
        return False
    try:
        result = snapshots.request("state", {})
        return result.get("state") == "on" and result.get("closed") is True
    except Exception:
        return False


def classify_killswitch_state(app, status_text, *, phase="absent"):
    """Diagnostic state only; never establishes ownership or authorizes cleanup."""
    if phase in PENDING or _app_value(app, "killswitch_recovery_required", False):
        return "recovery"
    if any(
        _is_global_block(parse_ufw_structured_rule(line))
        for line in status_text.splitlines()
    ):
        return "recovery"
    try:
        ifaces = sorted(set(app.get_wg_interfaces()))
        endpoints = select_killswitch_vpn_endpoints(app, status_text)
        enabled, _ = verify_killswitch_rules(
            app,
            status_text,
            True,
            ifaces,
            endpoints,
            allow_empty_plan=not ifaces
            and not endpoints
            and _protected_closed_plan(app),
        )
        if enabled:
            return "on"
        disabled, _ = verify_killswitch_rules(
            app, status_text, False, ifaces, endpoints
        )
        return "off" if disabled else "unknown"
    except Exception:
        return "unknown"


def killswitch_state(app):
    phase = _journal_phase(app)
    if _app_value(app, "_killswitch_transition_running", False) and phase not in {
        "recovery_required",
        "unreadable",
    }:
        return "transition"
    if phase in PENDING or _app_value(app, "killswitch_recovery_required", False):
        return "recovery"
    snapshots = _instance_override(app, "firewall_snapshots")
    protected_state = "absent"
    if snapshots is not None:
        protected_state = snapshots.state()
        if protected_state not in {"absent", "off", "reviewed"}:
            return protected_state
    try:
        with app.ufw_lock:
            rc, out = app._read_ufw_status(verbose=True)
        if (phase == "manual_reviewed" or protected_state == "reviewed") and rc == 0:
            return (
                "recovery"
                if any(
                    _is_global_block(parse_ufw_structured_rule(line))
                    for line in out.splitlines()
                )
                else "reviewed"
            )
        if protected_state == "off" and rc == 0:
            return (
                "recovery"
                if any(
                    _is_global_block(parse_ufw_structured_rule(line))
                    for line in out.splitlines()
                )
                else "off"
            )
        return (
            classify_killswitch_state(app, out, phase=phase) if rc == 0 else "unknown"
        )
    except Exception:
        return "unknown"


def cached_killswitch_state(app):
    """Never wait for a sudo/root RPC in Tk refresh; publish a bounded-age sample."""
    if _app_value(app, "_killswitch_transition_running", False):
        return "transition"
    if _journal_phase(app) in PENDING or _app_value(
        app, "killswitch_recovery_required", False
    ):
        return "recovery"
    lock = app.__dict__.setdefault("_killswitch_status_lock", threading.Lock())
    with lock:
        sample = app.__dict__.get("_killswitch_cached_state", (0, "unknown"))
        if time.monotonic() - sample[0] > 3 and not app.__dict__.get(
            "_killswitch_status_worker"
        ):
            app._killswitch_status_worker = True
            generation = app.__dict__.get("_killswitch_status_generation", 0)

            def observe():
                try:
                    state = killswitch_state(app)
                    with lock:
                        if generation == app.__dict__.get(
                            "_killswitch_status_generation", 0
                        ):
                            app._killswitch_cached_state = (time.monotonic(), state)
                finally:
                    app._killswitch_status_worker = False

            threading.Thread(target=observe, daemon=True).start()
        return sample[1] if time.monotonic() - sample[0] < 10 else "unknown"


def _invalidate_killswitch_cache(app):
    app._killswitch_status_generation = (
        app.__dict__.get("_killswitch_status_generation", 0) + 1
    )
    app.__dict__.pop("_killswitch_cached_state", None)


def unrelated_ufw_writes_blocked(app):
    if _instance_override(
        app, "_active_firewall_snapshot"
    ) is not None or firewall_recovery_pending(app):
        return True
    snapshots = _instance_override(app, "firewall_snapshots")
    if snapshots is None:
        return False
    state = snapshots.state()
    if state == "on":
        return True
    # An old installed Killswitch may predate protected snapshots.
    rc, text = app._read_ufw_status(verbose=True)
    if rc != 0:
        return True
    if any(
        _is_global_block(parse_ufw_structured_rule(row)) for row in text.splitlines()
    ):
        return True
    # Ordinary VPN allowances after OFF must not become pending restoration.
    # Retain the recognizable legacy Killswitch fence without assuming ownership.
    return ufw_default_policy_matches(text, outgoing="deny") and all(
        ufw_has_interface_rule(text, "lo", direction) for direction in ("in", "out")
    )


def guarded_ufw_command(app, args, *, runner=None, lock_held=False, **kwargs):
    runner = runner or run_cmd
    tokens = list(args)
    indices = [
        i for i, token in enumerate(tokens) if str(token).rsplit("/", 1)[-1] == "ufw"
    ]
    if not indices or tokens[indices[0] + 1 : indices[0] + 2] in (
        ["status"],
        ["show"],
        ["version"],
    ):
        return runner(tokens, **kwargs)
    lock = app.__dict__.setdefault("ufw_lock", threading.Lock())
    with nullcontext() if lock_held else lock:
        if unrelated_ufw_writes_blocked(app):
            return (
                1,
                "UFW-Schreibzugriff gesperrt: Killswitch aktiv oder Wiederherstellung ungeklärt.",
            )
        return runner(tokens, **kwargs)


def unrelated_ufw_operation(function):
    """Hold the shared operation coordinator across multi-step UFW changes."""

    @wraps(function)
    def guarded(app, *args, **kwargs):
        begin = _network_operation_method(app, "_try_begin_network_operation")
        if begin is not None and not begin("UFW-Einstellungen ändern"):
            return False
        try:
            if unrelated_ufw_writes_blocked(app):
                app.log_safe(
                    "UFW-Einstellungen gesperrt: Killswitch aktiv oder Wiederherstellung ungeklärt."
                )
                return False
            return function(app, *args, **kwargs)
        finally:
            if begin is not None:
                end = _network_operation_method(app, "_end_network_operation")
                if end is not None:
                    end()

    return guarded


def acknowledge_manual_firewall_review(app):
    if not app._confirm_danger_action(
        "killswitch:manual-review",
        title="Firewall manuell geprüft",
        prompt="Nur nach eigener Prüfung beider Adressfamilien bestätigen. "
        "Diese Aktion beendet die Wiederherstellungsmarkierung, verändert keine "
        "UFW-Regeln und stellt keine frühere Konfiguration wieder her. "
        "Eine noch aktive Sicherung wird geschützt archiviert und für weitere "
        "automatische Rollbacks stillgelegt. Zuvor müssen die ursprünglichen "
        "Policies wiederhergestellt und alle zusätzlichen Schnittstellen-DROP-Regeln "
        "zurückgenommen sein. Andere bewusst beibehaltene Admin-Regeln bleiben erhalten.",
        cooldown_s=0,
        require_phrase="MANUELL GEPRUEFT",
    ):
        return False

    def finish():
        begin = _network_operation_method(app, "_try_begin_network_operation")
        if begin is not None and not begin("Firewallprüfung abschließen"):
            return False
        try:
            with app.ufw_lock:
                _snapshot_client_for(app).acknowledge()
                if not _journal_mark(app, "manual_reviewed"):
                    return False
                app.killswitch_recovery_required = False
                _invalidate_killswitch_cache(app)
            app.log_safe(
                "Manuelle Firewallprüfung bestätigt; nur die Wiederherstellungsmarkierung beendet. Keine Firewallregeln geändert und kein automatisches Rollback ausgeführt."
            )
            return True
        except Exception as exc:
            detail = str(exc) if isinstance(exc, SnapshotError) else type(exc).__name__
            app.log_safe(f"Manuelle Firewallprüfung nicht abgeschlossen: {detail}.")
            return False
        finally:
            end = _network_operation_method(app, "_end_network_operation")
            if end is not None:
                end()

    app.run_async(finish, job_name="Firewallprüfung abschließen")
    return True


def firewall_recovery_pending(app):
    if (
        _app_value(app, "killswitch_recovery_required", False)
        or _journal_phase(app) in PENDING
    ):
        return True
    snapshots = _instance_override(app, "firewall_snapshots")
    return snapshots is not None and snapshots.state() in {"recovery", "unknown"}


def killswitch_status_label(app, state):
    labels = {
        "reviewed": (
            "header_killswitch_reviewed",
            "Killswitch: manuell geprüft; kein automatisches Rollback",
        ),
        "on": ("header_killswitch_on", "Killswitch: ON"),
        "off": ("header_killswitch_off", "Killswitch: OFF"),
        "recovery": (
            "header_killswitch_recovery",
            "Killswitch: WIEDERHERSTELLUNG NÖTIG",
        ),
        "unknown": ("header_killswitch_unknown", "Killswitch: UNBEKANNT"),
        "transition": ("header_killswitch_transition", "Killswitch: WIRD GEÄNDERT"),
    }
    key, fallback = labels.get(state, labels["unknown"])
    return app.tr(key, fallback)


def killswitch_is_on(app):
    wg_ifaces = sorted(set(app.get_wg_interfaces()))
    with app.ufw_lock:
        rc, out = app._read_ufw_status(verbose=True)

    if rc != 0:
        return False

    handshake_rules = select_killswitch_vpn_endpoints(app, out)
    verified, _issues = verify_killswitch_rules(
        app,
        out,
        enabled=True,
        wg_ifaces=wg_ifaces,
        handshake_rules=handshake_rules,
        allow_empty_plan=not wg_ifaces
        and not handshake_rules
        and _protected_closed_plan(app),
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
    snapshots = _snapshot_client_for(app)
    owns_transaction = _instance_override(app, "_active_firewall_snapshot") is None
    try:
        if owns_transaction:
            snapshots.begin()
            app._active_firewall_snapshot = snapshots
        abort = getattr(snapshots, "abort_unmodified", None)
        if callable(abort) and abort():
            app.killswitch_recovery_required = False
            _journal_mark(app, "off_verified")
            if owns_transaction:
                app.__dict__.pop("_active_firewall_snapshot", None)
            app.log_safe(
                "Killswitch-Vorgang vor einer verbleibenden Firewalländerung abgebrochen; keine Notfallsperre gesetzt."
            )
            return False
        snapshots.recovery()
    except Exception:
        if owns_transaction:
            app.__dict__.pop("_active_firewall_snapshot", None)
        retired_off = False
        if not owns_transaction:
            try:
                state = snapshots.request("state", {})
                retired_off = (
                    isinstance(state, dict)
                    and state.get("state") == "off"
                    and state.get("retired") is True
                )
            except Exception:
                pass
        if retired_off:
            app.log_safe(
                "Killswitch-Abgleich durch zwischenzeitlich bestätigtes AUS abgebrochen. "
                "Aktuelle Firewall-Regeln müssen geprüft werden. Eine verbleibende "
                "Wiederherstellungsmarkierung kann nach eigener Prüfung beider "
                "Adressfamilien im Killswitch-Menü über "
                "„Wiederherstellung manuell geprüft …“ abgeschlossen werden."
            )
            return False
        app.log_safe(
            "UFW-Notfallsperre nicht verifiziert: geschützter Snapshotpfad nicht verfügbar; manuelle Wiederherstellung erforderlich."
        )
        return False
    # A protected transaction must exist before a recovery marker can persist.
    app.killswitch_recovery_required = True
    _journal_mark(app, "recovery_required")
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
        except Exception:  # noqa: BLE001 - recovery must continue after runner errors
            rc = 1
        if rc and command[:2] == ["insert", "1"]:
            fallback = ["sudo", "-n", "ufw", *command[2:]]
            try:
                if network_service is not None:
                    rc, _out = network_service.run(fallback, timeout=20)
                else:
                    rc, _out = _run_cmd(app, fallback, timeout=20)
            except Exception:
                rc = 1
        failures |= rc != 0
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
    if owns_transaction:
        app.__dict__.pop("_active_firewall_snapshot", None)
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
        prior_transaction = _instance_override(app, "_active_firewall_snapshot")
        try:
            return _recover_killswitch_failure_locked(app)
        finally:
            if prior_transaction is None:
                app.__dict__.pop("_active_firewall_snapshot", None)


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


def killswitch_on_sync(app, refresh_ui=True, *, require_active=False):
    begin_op = _network_operation_method(app, "_try_begin_network_operation")
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
        app._killswitch_transition_running = True
        _invalidate_killswitch_cache(app)
        collect_profiles = _network_operation_method(
            app, "_collect_referenced_vpn_profiles"
        )
        if callable(collect_profiles):
            referenced_profiles = collect_profiles(include_active=True)
        else:
            profile_provider = _network_operation_method(
                app, "get_killswitch_vpn_profiles"
            )
            referenced_profiles = (
                list(profile_provider()) if callable(profile_provider) else []
            )
        catalog = _network_operation_method(app, "list_wg_profiles")
        known_profiles = set(referenced_profiles) | (
            set(catalog()) if catalog else set()
        )
        profile_ifaces = set(known_profiles)
        resolver = _network_operation_method(app, "resolve_profile_family_runtime")
        resolved_profiles = {}
        if resolver is not None:
            for profile in sorted(known_profiles):
                resolved = resolver(
                    profile, log_missing=False, create_missing_ipv4=False
                )
                resolved_profiles[profile] = resolved
                # Configuration determines what must be fenced; only the
                # protected live identity check may authorize a grant.
                profile_ifaces.update(
                    str(resolved.get(key) or "").strip()
                    for key in ("effective_ipv4_interface", "effective_ipv6_interface")
                    if str(resolved.get(key) or "").strip()
                )
                # Existing family variants can have grants left from a prior
                # IPv6 setting, even when they are not the effective interface.
                profile_ifaces.update(
                    str(name).strip()
                    for name in resolved.get("endpoint_profiles", [])
                    if str(name).strip()
                )
        else:
            collect_ifaces = _network_operation_method(
                app, "_collect_interface_rules_for_profiles"
            )
            if collect_ifaces:
                profile_ifaces.update(collect_ifaces(referenced_profiles))
        known_ifaces = profile_ifaces | set(app.get_wg_interfaces())
        invalid_ifaces = {
            name for name in known_ifaces if not valid_interface_name(name)
        }
        for name in sorted(invalid_ifaces):
            app.log_safe(
                f"Killswitch: Profil-/Interface-Name {name!r} ist kein zulässiger Interface-Name; keine Interface-Regel dafür geplant."
            )
        profile_ifaces -= invalid_ifaces
        known_ifaces -= invalid_ifaces
        wg_ifaces = sorted(
            vpn_controller._verified_firewall_interfaces(
                app,
                {
                    iface
                    for iface in known_ifaces
                    if nm_ownership.verified_interface(iface)
                },
            )
        )
        blocked_ifaces = sorted(profile_ifaces - set(wg_ifaces) - {"lo"})
        log_debug = _network_operation_method(app, "log_debug")
        resolver = _network_operation_method(app, "resolve_profile_family_runtime")
        for profile in referenced_profiles:
            if not callable(log_debug) or not callable(resolver):
                break
            resolved = resolved_profiles[profile]
            log_debug(
                f"[DEBUG] UFW-Regeln für {profile} basieren auf "
                f"IPv4={resolved.get('effective_ipv4_interface') or '-'}, "
                f"IPv6={resolved.get('effective_ipv6_interface') or 'None'}"
            )
        non_ip_endpoints = []
        collector = _network_operation_method(app, "collect_non_ip_endpoint_profiles")
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
            notice = tuple(
                sorted(
                    (item.get("profile"), item.get("host"))
                    for item in non_ip_endpoints
                    if item.get("profile") and item.get("host")
                )
            )
            if app.__dict__.get("_killswitch_non_ip_notice") != notice:
                app.__dict__["_killswitch_non_ip_notice"] = notice
                app.log_safe(warning_text)

        network_service = _network_service_for(app)
        with app.ufw_lock, _killswitch_apply_guard(app) as mutation:
            rc_s, out_s = app._read_ufw_status()
            if rc_s != 0:
                app.log_safe(
                    "Killswitch-Aktivierung abgebrochen: UFW-Status nicht lesbar."
                )
                return False
            if _journal_phase(app) in PENDING or _app_value(
                app, "killswitch_recovery_required", False
            ):
                app.log_safe(
                    "Killswitch-Aktivierung gesperrt: ungeklärte Wiederherstellung; bestehende Regeln bleiben erhalten."
                )
                return False
            if any(
                _is_global_block(parse_ufw_structured_rule(line))
                for line in out_s.splitlines()
            ):
                app.log_safe(
                    "Killswitch-Aktivierung gesperrt: globale Sperrregeln müssen zuerst manuell geprüft werden."
                )
                return False
            # Only interfaces with existing rules need a fence. A large catalog
            # of unused profiles must not create redundant DROP rules or exceed
            # the protected plan's bounded size.
            existing_ifaces = {
                rule["interface"]
                for line in out_s.splitlines()
                if (rule := parse_ufw_structured_rule(line)) and rule["interface"]
            }
            blocked_ifaces = sorted(set(blocked_ifaces) & existing_ifaces)
            handshake_rules = sorted(
                set(
                    select_killswitch_vpn_endpoints(
                        app, out_s, referenced_profiles=referenced_profiles
                    )
                )
            )
            closed_plan = not wg_ifaces and not handshake_rules
            if closed_plan and not require_active:
                app.log_safe(
                    app.tr(
                        "killswitch_log_no_selected_endpoint",
                        "Kein nutzbarer Killswitch-Plan: kein ausgewähltes/aktives Profil mit IP-Endpoint, kein bestätigter Tunnel und keine passende bestehende Endpoint-Freigabe. Ungenutzte Katalogprofile allein reichen nicht.",
                    )
                )
                return False
            snapshots = _snapshot_client_for(app)
            begin_options = {}
            if blocked_ifaces:
                begin_options["blocked_interfaces"] = blocked_ifaces
            if require_active:
                begin_options["require_active"] = True
            snapshots.begin(wg_ifaces, handshake_rules, **begin_options)
            app._active_firewall_snapshot = snapshots
            network_service = snapshots
            if not _journal_mark(app, "applying"):
                return False
            mutation[0] = True

            # Keep existing grants; names alone do not prove NetMon ownership.
            # Inactive/unverified profile interfaces receive a leading fence.
            cmds = [
                ["sudo", "-n", "ufw", "insert", "1", "deny", direction, "on", iface]
                for iface in blocked_ifaces
                for direction in ("in", "out")
            ] + [
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
                if (
                    cmd[3:5] in (["allow", "in"], ["allow", "out"])
                    and len(cmd) == 7
                    and cmd[5] == "on"
                    and cmd[6] != "lo"
                    and not nm_ownership.verified_interface(cmd[6])
                ):
                    command_failures.append(
                        (cmd, "WireGuard-Identitaet nicht bestaetigt")
                    )
                    break
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
                **({"allow_empty_plan": True} if closed_plan else {}),
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

            if not _journal_mark(app, "active"):
                _recover_killswitch_failure_locked(app)
                return False
            try:
                snapshots.commit()
            except Exception:
                _recover_killswitch_failure_locked(app)
                return False
            app.__dict__.pop("_vpn_firewall_sync_pending", None)

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
        elif closed_plan:
            app.log_safe(
                "Killswitch AN – kein Tunnel oder Handshake-Ziel freigegeben; nur Loopback erlaubt."
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
        detail = str(exc) if isinstance(exc, SnapshotError) else type(exc).__name__
        app.log_safe(f"Killswitch-Aktivierung fehlgeschlagen: {detail}")
        if refresh_ui:
            app.refresh_safe()
        return False
    finally:
        app._killswitch_transition_running = False
        _invalidate_killswitch_cache(app)
        app.__dict__.pop("_active_firewall_snapshot", None)
        end_op = _network_operation_method(app, "_end_network_operation")
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
    begin_op = _network_operation_method(app, "_try_begin_network_operation")
    if callable(begin_op) and not begin_op("Killswitch deaktivieren"):
        if refresh_ui:
            app.refresh_safe()
        return False
    try:
        app._killswitch_transition_running = True
        _invalidate_killswitch_cache(app)
        snapshots = _snapshot_client_for(app)
        with app.ufw_lock:
            # The protected helper persists restoring before its first write.
            # Do not invent a pending mutation when sudo/helper/snapshot is absent.
            snapshots.restore()
            if snapshots.state() != "off":
                raise RuntimeError("UFW snapshot restoration is not verified")
            if not _journal_mark(app, "off_verified"):
                return False
            app.killswitch_recovery_required = False
            app.__dict__.pop("_vpn_firewall_sync_pending", None)
        app.log_safe(
            "Killswitch AUS – vorheriger UFW-Zustand verifiziert wiederhergestellt; UFW bleibt aktiv."
        )
        if refresh_ui:
            app.refresh_safe()
        return True
    except Exception as exc:
        # A rejected request (including missing helper/snapshot) is not evidence
        # that this OFF attempt changed the firewall. Root state stays authoritative.
        if isinstance(exc, SnapshotError) and exc.code == "rollback_failed":
            app.killswitch_recovery_required = True
            _journal_mark(app, "recovery_required")
        detail = str(exc) if isinstance(exc, SnapshotError) else type(exc).__name__
        app.log_safe(
            f"Killswitch-Deaktivierung fehlgeschlagen: {detail}; manuelle Prüfung erforderlich."
        )
        return False
    finally:
        app._killswitch_transition_running = False
        _invalidate_killswitch_cache(app)
        end_op = _network_operation_method(app, "_end_network_operation")
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


SUDO_STATUS_BACKOFF_SECONDS = 30.0
_SUDO_PASSWORD_REQUIRED = re.compile(
    r"^sudo: .*(password|passwort)", re.IGNORECASE | re.MULTILINE
)


def begin_refresh_scope(app) -> dict:
    """Passive display snapshot owned by the calling (refresh) thread only."""
    scope = {}
    app.__dict__["_ufw_status_scope"] = (threading.get_ident(), scope)
    return scope


def end_refresh_scope(app) -> None:
    current = app.__dict__.get("_ufw_status_scope")
    if isinstance(current, tuple) and current[0] == threading.get_ident():
        app.__dict__.pop("_ufw_status_scope", None)


def refresh_scope(app):
    """The snapshot dict if the caller is the refresh that owns it, else None.

    Other threads and every explicit operation (reconcile, switches, kill
    switch, repairs) always read live and never see the sudo backoff.
    """
    if app is None:
        return None
    current = app.__dict__.get("_ufw_status_scope")
    if (
        isinstance(current, tuple)
        and len(current) == 2
        and current[0] == threading.get_ident()
        and isinstance(current[1], dict)
    ):
        return current[1]
    return None


def sudo_status_backoff_active(app) -> bool:
    """True only for passive refresh reads after a recent sudo password failure."""
    if refresh_scope(app) is None:
        return False
    return time.monotonic() < float(app.__dict__.get("_ufw_sudo_backoff_until", 0.0))


def note_ufw_status_result(app, rc, out) -> None:
    """Remember a sudo password failure briefly; any success clears it.

    Without this, the Tk refresh paid ~35 ms for a failing sudo three times
    every 3 s (measured stall source in the visualizer window).
    """
    if app is None:
        return
    if rc == 0:
        app.__dict__.pop("_ufw_sudo_backoff_until", None)
    elif _SUDO_PASSWORD_REQUIRED.search(str(out or "")):
        app.__dict__["_ufw_sudo_backoff_until"] = (
            time.monotonic() + SUDO_STATUS_BACKOFF_SECONDS
        )


def read_ufw_status(app=None, verbose=False):
    cmd = ["sudo", "-n", "ufw", "status"]
    if verbose:
        cmd.append("verbose")
    if app is None:
        return run_cmd(cmd, timeout=12 if verbose else 8)
    # One refresh cycle shares a single status snapshot per flavour; only the
    # refresh thread itself uses it (see refresh_scope).
    scope = refresh_scope(app)
    if isinstance(scope, dict) and verbose in scope:
        return scope[verbose]
    if sudo_status_backoff_active(app):
        result = (1, "")
    else:
        result = _run_cmd(app, cmd, timeout=12 if verbose else 8)
        try:
            note_ufw_status_result(app, result[0], result[1])
        except Exception:
            pass
    if isinstance(scope, dict):
        scope[verbose] = result
    return result


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
        line_l = line.split("#", 1)[0].strip().lower()
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
    try:
        address = ipaddress.ip_address(endpoint_ip)
        port = str(int(endpoint_port))
    except ValueError:
        return False
    for line in status_text.splitlines():
        rule = parse_ufw_structured_rule(line)
        if (
            not rule
            or rule["policy"] != "ALLOW"
            or rule["direction"] != "OUT"
            or rule["proto"] != "udp"
            or not rule["ip"]
        ):
            continue
        if _endpoint_key(rule["ip"], rule["port"]) == (str(address), port):
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
        if not nm_ownership.verified_interface(iface):
            return False, False, "WireGuard-Identitaet nicht bestaetigt", known_keys
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


def _endpoint_key(address, port):
    try:
        number = int(port)
        if not 1 <= number <= 65535:
            return None
        return str(ipaddress.ip_address(address)), str(number)
    except (ValueError, TypeError):
        return None


def _port_expression_contains(expression, port):
    """Match bounded UFW port lists/ranges without expanding all port numbers."""
    try:
        wanted = int(port)
        spans = [part.split(":") for part in str(expression).split(",")]
        if not 1 <= wanted <= 65535 or any(
            len(span) not in {1, 2} or not all(item.isdigit() for item in span)
            for span in spans
        ):
            return False
        bounds = [(int(span[0]), int(span[-1])) for span in spans]
        if any(not 1 <= lower <= upper <= 65535 for lower, upper in bounds):
            return False
        return any(lower <= wanted <= upper for lower, upper in bounds)
    except (ValueError, TypeError):
        return False


def ufw_has_outgoing_port_rule(
    status_text, port, proto, *, handshake_rules=None, ignore_interfaces=()
):
    port = str(port or "").strip()
    proto = str(proto or "").strip().lower()
    if not port or not proto:
        return False
    approved = {_endpoint_key(*endpoint) for endpoint in handshake_rules or []}
    ignored = set(ignore_interfaces)
    for line in (status_text or "").splitlines():
        rule = parse_ufw_structured_rule(line)
        if not rule or rule["policy"] != "ALLOW" or rule["direction"] != "OUT":
            continue
        if rule["interface"] in ignored:
            continue
        # A destination port without /proto applies to both TCP and UDP.
        rule_port = str(rule["port"] or "")
        if not _port_expression_contains(rule_port, port) or rule["proto"] not in {
            "",
            proto,
        }:
            continue
        if (
            rule["proto"] == "udp"
            and not rule["interface"]
            and rule["ip"]
            and _endpoint_key(rule["ip"], rule_port) in approved
        ):
            continue
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

        rc, out = guarded_ufw_command(
            app, ["sudo", "-n", "ufw", "--force", "enable"], timeout=40, runner=run_cmd
        )

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

        rc, out = guarded_ufw_command(
            app, ["sudo", "-n", "ufw", "disable"], timeout=40, runner=run_cmd
        )

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
    rc_before, out_before = guarded_ufw_command(
        app, ["ufw", "status", "verbose"], timeout=5, runner=run_cmd
    )
    debug_logger(f"[DEBUG BEFORE] ufw status verbose rc={rc_before}")
    debug_logger(f"[DEBUG BEFORE] {out_before}")
    rc, out = guarded_ufw_command(
        app, ["sudo", "-n", "ufw", "logging", "high"], timeout=12, runner=run_cmd
    )
    if rc != 0:
        rc, out = guarded_ufw_command(
            app, ["ufw", "logging", "high"], timeout=12, runner=run_cmd
        )
    if rc == 0:
        rc_after, out_after = guarded_ufw_command(
            app, ["ufw", "status", "verbose"], timeout=5, runner=run_cmd
        )
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
            _, status_out = guarded_ufw_command(
                app,
                ["sudo", "-n", "ufw", "status", "numbered"],
                timeout=12,
                runner=run_cmd,
                lock_held=True,
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
            rc, out = guarded_ufw_command(
                app,
                ["sudo", "-n", "ufw", "allow", "22/tcp"],
                timeout=15,
                runner=run_cmd,
                lock_held=True,
            )
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

    def _log_later(message):
        app.after(0, lambda m=message: app.log(m))

    def _read_status():
        with app.ufw_lock:
            _, out = guarded_ufw_command(
                app,
                ["sudo", "-n", "ufw", "status", "numbered"],
                timeout=12,
                runner=run_cmd,
                lock_held=True,
            )
        return str(out or "")

    def _log_status_unavailable():
        _log_later(
            app.tr(
                "ssh_log_status_numbered_unavailable",
                "UFW status numbered leer/unverfügbar.",
            )
        )

    def _log_snapshot(targets, review):
        for _, rule in review:
            _log_later(
                app.tr(
                    "ssh_log_rule_needs_review",
                    "SSH/UFW: nicht entfernt, Regel enthält neben Port 22 weitere "
                    "Ports, bitte manuell prüfen: {rule}",
                ).format(rule=rule)
            )
        if not targets:
            _log_later(
                app.tr(
                    "ssh_log_no_port_22_rule",
                    "SSH/UFW: keine Port-22-Regel gefunden.",
                )
            )

    def delete_job(confirmed=None):
        # UFW numbers shift with every rule change. Each delete therefore
        # re-reads the numbered list under the same lock scope and only
        # removes rules that were part of the confirmed snapshot. Without a
        # dialog (auto) the first locked snapshot is the confirmed one.
        pending = Counter(confirmed) if confirmed is not None else None
        remaining = sum(pending.values()) if pending is not None else 0
        while pending is None or remaining > 0:
            target = None
            rc2, del_out = None, ""
            with app.ufw_lock:
                _, out = guarded_ufw_command(
                    app,
                    ["sudo", "-n", "ufw", "status", "numbered"],
                    timeout=12,
                    runner=run_cmd,
                    lock_held=True,
                )
                out = str(out or "")
                targets, review = _numbered_ssh_rules(out) if out.strip() else ([], [])
                first_snapshot = pending is None and bool(out.strip())
                if first_snapshot:
                    pending = Counter(rule for _, rule in targets)
                    remaining = len(targets)
                candidates = [
                    item for item in targets if pending and pending[item[1]] > 0
                ]
                if candidates and remaining > 0:
                    target = max(candidates)
                    remaining -= 1
                    rc2, del_out = guarded_ufw_command(
                        app,
                        ["sudo", "-n", "ufw", "--force", "delete", str(target[0])],
                        timeout=12,
                        runner=run_cmd,
                        lock_held=True,
                    )
            if not out.strip():
                _log_status_unavailable()
                break
            if first_snapshot:
                _log_snapshot(targets, review)
                if not targets:
                    return
            if target is None:
                break
            rule = target[1]
            if rc2 == 0:
                pending[rule] -= 1
                _log_later(
                    app.tr(
                        "ssh_log_removed",
                        "SSH/UFW entfernt: {rule}",
                    ).format(rule=rule)
                )
            else:
                _log_later(
                    app.tr(
                        "ssh_log_delete_failed",
                        "SSH/UFW delete failed: {message}",
                    ).format(message=del_out)
                )
                break

        _schedule_firewall_refresh(app)

    def confirm(targets, review):
        body = app.tr(
            "ssh_remove_confirm_rules_body",
            "Diese UFW-Regeln für eingehendes SSH (Port 22/TCP) werden "
            "entfernt:\n\n{rules}\n\n"
            "Wenn du per SSH verbunden bist, kannst du dich aussperren.\n\n"
            "Wirklich fortfahren?",
        ).format(rules="\n".join(f"• {rule}" for _, rule in targets))
        if review:
            body += "\n\n" + app.tr(
                "ssh_remove_confirm_review_note",
                "Nicht entfernt, weil weitere Ports betroffen wären "
                "(bitte manuell prüfen):\n{rules}",
            ).format(rules="\n".join(f"• {rule}" for _, rule in review))
        ok = messagebox.askyesno(
            app.tr("ssh_remove_confirm_title", "Achtung"), body, parent=app
        )
        if not ok:
            app.log(app.tr("ssh_log_cancelled", "SSH/UFW: Abgebrochen."))
            return
        confirmed = [rule for _, rule in targets]
        threading.Thread(target=lambda: delete_job(confirmed), daemon=True).start()

    def read_job():
        out = _read_status()
        if not out.strip():
            _log_status_unavailable()
            return
        targets, review = _numbered_ssh_rules(out)
        if not targets:
            _log_snapshot(targets, review)
            return
        call_in_ui_thread(app, lambda: confirm(targets, review))

    threading.Thread(target=delete_job if auto else read_job, daemon=True).start()


_SSH_REMOVABLE_POLICIES = frozenset({"ALLOW", "LIMIT"})


def _port_expression_includes(expression, port):
    """True if a UFW multiport/range expression such as ``21,22:25`` covers port."""
    for token in str(expression or "").split(","):
        bounds = token.strip().split(":")
        try:
            values = [int(value) for value in bounds]
        except ValueError:
            continue
        if len(values) == 1 and values[0] == port:
            return True
        if len(values) == 2 and values[0] <= port <= values[1]:
            return True
    return False


def _classify_ssh_rule(rule):
    """Classify one parsed UFW rule for SSH cleanup.

    ``"remove"``: inbound ALLOW/LIMIT for exactly port 22 (tcp or any
    protocol) or the ``OpenSSH`` application profile. ``"review"``: inbound
    ALLOW/LIMIT whose multiport/range also covers 22; deleting it would drop
    other ports too. ``None``: everything else, including addresses,
    interfaces or comments that merely contain ``22`` and DENY/REJECT rules,
    whose removal would open SSH instead of closing it.
    """
    if not rule:
        return None
    if str(rule.get("direction") or "").upper() != "IN":
        return None
    if str(rule.get("policy") or "").upper() not in _SSH_REMOVABLE_POLICIES:
        return None
    if str(rule.get("to") or "").split()[-1:] == ["OpenSSH"]:
        return "remove"
    if str(rule.get("proto") or "").strip().lower() not in ("", "tcp"):
        return None
    port = str(rule.get("port") or "").strip()
    if port == "22":
        return "remove"
    if _port_expression_includes(port, 22):
        return "review"
    return None


def _numbered_ssh_rules(status_text):
    """Split ``ufw status numbered`` into SSH rules to remove and to review.

    Both lists hold ``(number, normalized rule text)``. Column padding depends
    on the widest row, so the text is whitespace normalized to stay comparable
    across snapshots.
    """
    targets, review = [], []
    for line in str(status_text or "").splitlines():
        parsed = parse_ufw_numbered_rule(line)
        kind = _classify_ssh_rule(parsed)
        if kind is None:
            continue
        # Keep comments: they help the confirmation and tighten the identity.
        text = re.sub(r"^\[\s*\d+\]\s*", "", str(parsed.get("numbered_raw") or ""))
        entry = (parsed["number"], " ".join(text.split()))
        (targets if kind == "remove" else review).append(entry)
    return targets, review


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
                rc, out = guarded_ufw_command(
                    app, command, timeout=20, runner=run_cmd, lock_held=True
                )
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
        # UFW numbers are snapshot-local cursors: resolve and delete inside one
        # lock scope so no in-process writer can renumber the rule in between.
        rc_delete, out_delete = None, ""
        matches = []
        with app.ufw_lock:
            rc_status, out_status = guarded_ufw_command(
                app,
                ["sudo", "-n", "ufw", "status", "numbered"],
                timeout=20,
                runner=run_cmd,
                lock_held=True,
            )
            if rc_status == 0 and str(out_status or "").strip():
                for raw_line in str(out_status or "").splitlines():
                    parsed = parse_ufw_numbered_rule(raw_line)
                    if parsed is None:
                        continue
                    if _firewall_rule_matches_selected(parsed, meta):
                        matches.append(parsed)
                if len(matches) == 1:
                    rc_delete, out_delete = guarded_ufw_command(
                        app,
                        [
                            "sudo",
                            "-n",
                            "ufw",
                            "--force",
                            "delete",
                            str(matches[0]["number"]),
                        ],
                        timeout=20,
                        runner=run_cmd,
                        lock_held=True,
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
