"""Conservative, display-only UFW assessment. Never authorizes a network action.

Socket binding and UFW configuration cannot establish external reachability.
An unknown source address or ingress interface leaves scoped rules conditional.
"""

import ipaddress
import re


def listener_address(listener):
    host = str(listener.get("host") or "").split("%", 1)[0]
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def port_matches(expression, port):
    if not expression:
        return True
    for part in str(expression).split(","):
        try:
            low, _, high = part.partition(":")
            if int(low) <= int(port) <= int(high or low):
                return True
        except (TypeError, ValueError):
            return None
    return False


def _address_matches(value, address, *, source=False):
    text = str(value or "").strip()
    if text.lower() in {"anywhere", "any", "*", ""}:
        return True
    try:
        network = ipaddress.ip_network(text, strict=False)
    except ValueError:
        return None  # application profiles and unparsed restrictions
    if address is not None and network.version != address.version:
        return False
    if network.prefixlen == 0:
        return True
    if source or address is None or address.is_unspecified:
        return None
    return address in network


def _rule_matches(listener, rule):
    if str(rule.get("direction") or "IN").upper() != "IN":
        return False
    address = listener_address(listener)
    if address is not None and (address.version == 6) != bool(rule.get("is_ipv6")):
        return False
    proto = str(rule.get("proto") or "").lower()
    if proto and proto != str(listener.get("proto") or "").lower():
        return False
    port_match = port_matches(rule.get("port"), listener.get("port"))
    if port_match is False:
        return False
    target = str(rule.get("to") or "")
    if rule.get("port"):
        target = re.sub(
            rf"(?:^|\s)(?:port\s+)?{re.escape(str(rule['port']))}(?:/(?:tcp|udp))?(?=\s|$)",
            " ",
            target,
            flags=re.IGNORECASE,
        ).strip()
    target_match = _address_matches(target, address)
    source_match = _address_matches(rule.get("from"), address, source=True)
    if target_match is False or source_match is False:
        return False
    interface = str(rule.get("interface") or "")
    bound_interface = str(listener.get("interface") or "")
    if not bound_interface and "%" in str(listener.get("host") or ""):
        bound_interface = str(listener["host"]).split("%", 1)[1]
    if interface and bound_interface and interface != bound_interface:
        return False
    if (
        address is None
        or port_match is None
        or target_match is None
        or source_match is None
        or (interface and not bound_interface)
    ):
        return None
    return True


def assess_inbound(listener, rules, *, status="unknown", default_in="-"):
    """Keep UFW rule order; conditional rules never prove a general IN allow."""
    if str(status).lower() == "inactive":
        return {"state": "inactive", "basis": "status", "policy": "-"}
    if str(status).lower() != "active":
        return {"state": "unknown", "basis": "status", "policy": "-"}
    conditional = False
    for rule in rules:
        match = _rule_matches(listener, rule)
        if match is False:
            continue
        if match is None:
            conditional = True
            continue
        if conditional:
            return {"state": "conditional", "basis": "scope", "policy": "-"}
        policy = str(rule.get("policy") or "").upper()
        state = {
            "ALLOW": "allowed",
            "DENY": "blocked",
            "REJECT": "blocked",
            "LIMIT": "limited",
        }.get(policy, "unknown")
        return {"state": state, "basis": "rule", "policy": policy}
    if conditional:
        return {"state": "conditional", "basis": "scope", "policy": "-"}
    policy = str(default_in).upper()
    state = {"ALLOW": "allowed", "DENY": "blocked", "REJECT": "blocked"}.get(
        policy, "unknown"
    )
    return {"state": state, "basis": "default", "policy": policy}


def wireguard_listen_ports(output):
    """Parse only `wg show all listen-port`; no keys, peers or configs needed."""
    ports = {}
    for line in str(output or "").splitlines():
        fields = line.split()
        if len(fields) != 2 or not re.fullmatch(r"[A-Za-z0-9_.:+-]{1,64}", fields[0]):
            continue
        try:
            port = int(fields[1])
        except ValueError:
            continue
        if 0 < port <= 65535:
            ports.setdefault(port, []).append(fields[0])
    return {port: tuple(sorted(set(interfaces))) for port, interfaces in ports.items()}
