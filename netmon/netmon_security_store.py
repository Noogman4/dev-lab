"""Security event store/analyzer helpers for NetMon."""

from __future__ import annotations

import time


class NetmonSecurityStore:
    """Pure helpers for filtering, statistics and scan detection."""

    @staticmethod
    def _is_relevant_level(level) -> bool:
        lvl = str(level or "").upper()
        if not lvl:
            return False
        return ("WARN" in lvl) or ("ALERT" in lvl) or ("CRITICAL" in lvl)

    def filtered_events(self, events, filter_mode="all", limit=400):
        events = list(events or [])
        if filter_mode == "portscan":
            base = [e for e in events if e.get("type") == "Portscan-Verdacht"]
        elif filter_mode == "relevant":
            base = [e for e in events if self._is_relevant_level(e.get("level"))]
        elif filter_mode == "external":
            base = [e for e in events if e.get("external")]
        else:
            base = events
        return base[-max(1, int(limit)) :]

    def compute_stats(self, events):
        events = list(events or [])
        total = len(events)
        block = sum(
            1 for e in events if e.get("type") == "UFW BLOCK" and e.get("external")
        )
        scan = sum(1 for e in events if e.get("type") == "Portscan-Verdacht")

        src_count = {}
        port_count = {}
        for e in events:
            if not e.get("external"):
                continue
            src = e.get("src", "-")
            src_count[src] = src_count.get(src, 0) + 1
            port = e.get("port", "-")
            if port and port != "-":
                port_count[port] = port_count.get(port, 0) + 1

        top_ip = max(src_count.items(), key=lambda kv: kv[1])[0] if src_count else "–"
        top_port = (
            max(port_count.items(), key=lambda kv: kv[1])[0] if port_count else "–"
        )
        return total, block, scan, top_ip, top_port

    def detect_portscan(self, events, last_portscan_alert):
        now = time.time()
        events = list(events or [])
        last_portscan_alert = (
            last_portscan_alert if isinstance(last_portscan_alert, dict) else {}
        )

        recent = [
            e
            for e in events
            if now - e.get("epoch", now) <= 90
            and e.get("external")
            and e.get("type") == "UFW BLOCK"
        ]
        by_ip = {}
        for e in recent:
            ip = e.get("src") or "-"
            entry = by_ip.setdefault(
                ip, {"count": 0, "ports": set(), "latest": e.get("time", "-")}
            )
            entry["count"] += 1
            p = e.get("port")
            if p and p != "-":
                entry["ports"].add(p)
            entry["latest"] = e.get("time", entry["latest"])

        def severity_for(count, unique_ports):
            if count >= 40 or unique_ports >= 25:
                return 5
            if count >= 25 or unique_ports >= 15:
                return 4
            if count >= 12 or unique_ports >= 8:
                return 3
            if count >= 6 or unique_ports >= 4:
                return 2
            if count >= 1:
                return 1
            return 0

        def severity_label(level):
            return {
                1: "INFO",
                2: "WARN",
                3: "ALERT",
                4: "CRITICAL",
                5: "CRITICAL",
            }.get(level, "INFO")

        findings = []
        for ip, info in by_ip.items():
            sev = severity_for(info["count"], len(info["ports"]))
            if sev < 2:
                continue
            last_alert = last_portscan_alert.get(ip, 0.0)
            if now - last_alert < 120:
                continue
            last_portscan_alert[ip] = now
            sev_label = severity_label(sev)
            findings.append(
                {
                    "time": info["latest"],
                    "type": "Portscan-Verdacht",
                    "src": ip,
                    "port": str(len(info["ports"])),
                    "proto": "-",
                    "level": f"L{sev} {sev_label}",
                    "action": "SUSPECT",
                    "raw": (
                        f"Portscan-Verdacht: SRC={ip}, Level=L{sev} {sev_label}, "
                        f"Events={info['count']}, verschiedene Ports={len(info['ports'])}"
                    ),
                    "key": f"portscan|{ip}|L{sev}|{int(now // 120)}",
                    "epoch": now,
                    "external": True,
                    "severity": sev,
                }
            )
        return findings
