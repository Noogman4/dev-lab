"""Pure network helper functions used by the NetMon UI layer."""

from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse


def is_local_or_lan_ip(ip: str) -> bool:
    s = (ip or "").strip()
    if not s:
        return False
    try:
        addr = ipaddress.ip_address(s)
    except ValueError:
        return False
    if addr.is_loopback:
        return True
    if addr.is_private:
        return True
    if addr.is_link_local:
        return True
    return False


def is_safe_trace_target(target: str) -> bool:
    t = (target or "").strip()
    if not t:
        return False

    if re.search(r"[ \t\r\n;&|`$(){}[\]<>\\\"']", t):
        return False

    try:
        ipaddress.ip_address(t)
        return True
    except ValueError:
        pass

    if len(t) > 253:
        return False
    if t.endswith("."):
        t = t[:-1]
    labels = t.split(".")
    if any(len(lbl) == 0 or len(lbl) > 63 for lbl in labels):
        return False
    hostname_re = re.compile(r"^[A-Za-z0-9-]+$")
    for lbl in labels:
        if not hostname_re.match(lbl):
            return False
        if lbl.startswith("-") or lbl.endswith("-"):
            return False
    return True


def is_safe_nmap_target(target: str) -> bool:
    t = (target or "").strip()
    if not t:
        return False

    if re.search(r"[ \t\r\n;&|`$(){}[\]<>\"']", t):
        return False

    try:
        ipaddress.ip_network(t, strict=False)
        return True
    except ValueError:
        pass

    return is_safe_trace_target(t)


def normalize_external_url_target(target: str) -> str:
    raw = (target or "").strip()
    if not raw:
        return ""
    if re.search(r"[\r\n\t]", raw):
        return ""

    url = raw
    if not re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://", url):
        url = "https://" + url

    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"}:
        return ""
    if not parsed.netloc:
        return ""
    return url


def parse_traceroute_hops(output: str):
    hops = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue
        m = re.match(r"^(\d+)\s+(\*|[0-9A-Fa-f\.:]+)\s+(?:(\d+(?:\.\d+)?)\s*ms)?", line)
        if m:
            hop = int(m.group(1))
            ip = m.group(2)
            rtt = m.group(3)
            hops.append(
                {
                    "hop": hop,
                    "ip": ip,
                    "rtt_ms": float(rtt) if rtt is not None else None,
                    "raw": line,
                }
            )
    return hops


def format_traceroute_table(hops):
    rows = list(hops or [])
    if not rows:
        return ""

    header = f"{'Hop':<4} | {'IP-Adresse':<18} | {'RTT (ms)':>8}"
    sep = "-" * len(header)
    lines = [header, sep]
    for item in rows:
        hop = item.get("hop", "-")
        ip = (item.get("ip") or "*").strip() or "*"
        rtt_ms = item.get("rtt_ms")
        rtt = "-" if rtt_ms is None else f"{float(rtt_ms):.1f}"
        lines.append(f"{str(hop):<4} | {ip:<18} | {rtt:>8}")
    return "\n".join(lines)


def parse_cf_trace(output: str):
    info = {}
    for line in (output or "").splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            info[k.strip()] = v.strip()
    return info


def parse_nmap_open_tcp_ports(output: str):
    ports = []
    for line in (output or "").splitlines():
        m = re.match(r"^(\d+)/tcp\s+open\b", line.strip(), re.IGNORECASE)
        if not m:
            continue
        try:
            ports.append(int(m.group(1)))
        except ValueError:
            continue
    return sorted(set(ports))


def parse_ss_lines(output: str):
    conns = []
    for line in (output or "").splitlines():
        line = line.strip()
        if not line:
            continue

        parts = line.split()
        proto = parts[0] if len(parts) > 0 else "?"
        state = "?"
        local = "?"
        remote = "?"

        if len(parts) >= 6:
            state = parts[1]
            local = parts[4]
            remote = parts[5]
        elif len(parts) >= 5:
            state = parts[1]
            local = parts[3]
            remote = parts[4]

        pid = ""
        proc = ""

        um = re.search(r"users:\(\((.+)\)\)", line)
        if um:
            blob = um.group(1)
            nm = re.search(r'"([^"]+)"', blob)
            pm = re.search(r"pid=(\d+)", blob)
            if nm:
                proc = nm.group(1)
            if pm:
                pid = pm.group(1)

        conns.append(
            {
                "proto": proto,
                "state": state,
                "local": local,
                "remote": remote,
                "pid": pid,
                "proc": proc,
                "raw": line,
            }
        )
    return conns


__all__ = [
    "format_traceroute_table",
    "is_local_or_lan_ip",
    "is_safe_nmap_target",
    "is_safe_trace_target",
    "normalize_external_url_target",
    "parse_cf_trace",
    "parse_nmap_open_tcp_ports",
    "parse_ss_lines",
    "parse_traceroute_hops",
]
