"""Security parser helpers for NetMon."""

from __future__ import annotations

import re
import time
from typing import Callable, Dict, Optional


class NetmonSecurityParser:
    """Parses raw security log lines into normalized event dicts."""

    @staticmethod
    def _to_int(value: str, default: int = -1) -> int:
        try:
            return int((value or "").strip())
        except (TypeError, ValueError, AttributeError):
            return default

    def _is_harmless_return_traffic_rst(
        self,
        *,
        line: str,
        kv: Dict[str, str],
        is_local_or_lan_ip_fn: Callable[[str], bool],
    ) -> bool:
        proto = (kv.get("PROTO") or "").upper()
        if proto != "TCP":
            return False

        # UFW flags are often present as plain tokens (e.g. "RST")
        if "RST" not in line.upper().split():
            return False

        src = (kv.get("SRC") or "").strip()
        dst = (kv.get("DST") or "").strip()
        if not src or not dst:
            return False

        # only external -> local/private return traffic
        if is_local_or_lan_ip_fn(src):
            return False
        if not is_local_or_lan_ip_fn(dst):
            return False

        spt = self._to_int(kv.get("SPT"), default=-1)
        dpt = self._to_int(kv.get("DPT"), default=-1)
        if spt <= 0 or dpt <= 0:
            return False

        # conservative: typical web return traffic to local ephemeral destination
        if spt not in {443, 80, 853}:
            return False
        if dpt <= 1024:
            return False

        # avoid reclassifying clear scan-style probing frames
        upper_line = line.upper()
        if "SYN" in upper_line and "RST" not in upper_line:
            return False

        return True

    def parse_ufw_block_line(
        self,
        line: str,
        *,
        aggregated: Dict[str, int],
        dedup_cache: Dict[str, tuple],
        is_local_or_lan_ip_fn: Callable[[str], bool],
        log_debug_fn: Optional[Callable[[str], None]] = None,
    ):
        if "[UFW BLOCK]" not in line:
            return None

        when = (line.split(" kernel:", 1)[0] or "").strip()

        kv = dict(re.findall(r"([A-Z]+)=([^ ]*)", line))
        src = kv.get("SRC", "-")
        dpt = kv.get("DPT", "-")
        proto = kv.get("PROTO", "-")
        is_local = bool(is_local_or_lan_ip_fn(src))

        class_tag = "BLOCK"
        harmless_rst = self._is_harmless_return_traffic_rst(
            line=line,
            kv=kv,
            is_local_or_lan_ip_fn=is_local_or_lan_ip_fn,
        )
        if harmless_rst:
            class_tag = "HARMLESS_RST"

        key = f"{src}|{dpt}|{proto}|{class_tag}"

        now = time.time()

        if is_local:
            category = "Other Local"
            if dpt == "53":
                category = "DNS"
            elif dpt == "5353" and proto == "UDP":
                category = "mDNS"
            elif src.startswith("172.17."):
                category = "Docker"
            elif proto == "ICMPv6":
                category = "ICMPv6"

            aggregated[category] = aggregated.get(category, 0) + 1
            return None

        if key in dedup_cache:
            count, last_time = dedup_cache[key]
            if now - last_time < 60:
                dedup_cache[key] = (count + 1, now)
                return None
            if count > 1 and callable(log_debug_fn):
                log_debug_fn(f"Dedupliziertes externe Block: {key} x{count}")
            dedup_cache[key] = (1, now)
        else:
            dedup_cache[key] = (1, now)

        full_key = f"{when}|{key}|EXT"
        if harmless_rst:
            spt = kv.get("SPT", "-")
            return {
                "time": when,
                "type": "HARMLESS RETURN TRAFFIC",
                "src": src,
                "port": dpt,
                "proto": proto,
                "level": "INFO",
                "action": "IGNORE",
                "raw": f"{line}\nBewertung: harmloser Rückverkehr (TCP RST)",
                "key": full_key,
                "epoch": now,
                "external": True,
                "classification": "harmless_return_traffic_rst",
                "summary": f"[INFO] harmless return traffic (RST) from {src}:{spt}",
            }

        return {
            "time": when,
            "type": "UFW BLOCK",
            "src": src,
            "port": dpt,
            "proto": proto,
            "level": "L1 INFO",
            "action": "BLOCK",
            "raw": line,
            "key": full_key,
            "epoch": now,
            "external": True,
        }
