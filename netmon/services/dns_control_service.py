"""Central DNS evaluation and repair helpers for NetMon."""

from __future__ import annotations

import ipaddress
import os
import re
from typing import Callable

try:
    from netmon.core.privileged_config import write_privileged_config
except ModuleNotFoundError:
    from core.privileged_config import write_privileged_config

RunCmd = Callable[..., tuple[int, str]]
HasCmd = Callable[[str], bool]


class DNSControlService:
    """Encapsulates DNS parsing, policy evaluation and safe repair actions."""

    VPN_TOKENS = ("proton", "wireguard", "wg", "tun", "vpn")
    FORBIDDEN_DEVICE_TOKENS = ("wg", "tun", "vpn", "docker", "br-")
    FORBIDDEN_NAME_TOKENS = (
        "vpn",
        "wireguard",
        "proton",
        "docker",
        "bridge",
        "loopback",
        "tun",
    )
    SKIP_DEVICE_NAMES = {"lo", "docker0"}
    ALLOWED_TYPES = {"ethernet", "wifi", "802-3-ethernet", "802-11-wireless"}

    def __init__(
        self,
        run_cmd: RunCmd,
        has_cmd: HasCmd,
        *,
        dot_dropin_path: str,
        dot_dropin_dir: str,
    ) -> None:
        self.run_cmd = run_cmd
        self.has_cmd = has_cmd
        self.dot_dropin_path = dot_dropin_path
        self.dot_dropin_dir = dot_dropin_dir

    @staticmethod
    def _translate_policy_warning(warning: str, tr=None) -> str:
        text = str(warning or "").strip()

        def _tr(key: str, fallback: str) -> str:
            if callable(tr):
                try:
                    return tr(key, fallback)
                except Exception:
                    return fallback
            return fallback

        mapping = {
            "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt.": _tr(
                "dns_warning_vpn_with_global_dns",
                "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt.",
            ),
            "NetMon DoT-Drop-in erzwingt globale DNS-Server trotz aktivem VPN-DNS.": _tr(
                "dns_warning_dot_dropin_forces_global_dns",
                "NetMon DoT-Drop-in erzwingt globale DNS-Server trotz aktivem VPN-DNS.",
            ),
            "Docker/veth-Interfaces wurden erkannt. Diese erzeugen zusätzliche DNS-Kontexte, werden aber von DNS-Control ignoriert.": _tr(
                "dns_warning_docker_veth_ignored",
                "Docker/veth-Interfaces wurden erkannt. Diese erzeugen zusätzliche DNS-Kontexte, werden aber von DNS-Control ignoriert.",
            ),
            "DNSSEC ist strikt aktiv, obwohl VPN-DNS erkannt wurde.": _tr(
                "dns_warning_dnssec_strict_with_vpn_dns",
                "DNSSEC ist strikt aktiv, obwohl VPN-DNS erkannt wurde.",
            ),
            "Mehrere DNS-Quellen sind gleichzeitig sichtbar.": _tr(
                "dns_warning_multiple_dns_sources",
                "Mehrere DNS-Quellen sind gleichzeitig sichtbar.",
            ),
            "DoT ist aktiv, während VPN-DNS genutzt wird. Das ist nicht automatisch falsch, sollte aber bewusst geprüft werden.": _tr(
                "dns_warning_dot_active_with_vpn_dns",
                "DoT ist aktiv, während VPN-DNS genutzt wird. Das ist nicht automatisch falsch, sollte aber bewusst geprüft werden.",
            ),
        }
        return mapping.get(text, text)

    def read_resolvectl_status(self, timeout: int = 8) -> tuple[int, str]:
        return self.run_cmd(["resolvectl", "status"], timeout=timeout)

    def parse_active_dns_servers(self, resolvectl_output: str) -> list[str]:
        servers: list[str] = []
        collecting = False

        for line in (resolvectl_output or "").splitlines():
            stripped = line.strip()
            if not stripped:
                collecting = False
                continue

            if stripped.startswith("Current DNS Server:"):
                value = stripped.split(":", 1)[1].strip()
                if value:
                    servers.extend(value.split())
                collecting = False
                continue

            if stripped.startswith("DNS Servers:"):
                value = stripped.split(":", 1)[1].strip()
                if value:
                    servers.extend(value.split())
                collecting = True
                continue

            if collecting and not stripped.endswith(":"):
                tokens = self._dns_server_continuation_tokens(stripped)
                if tokens:
                    servers.extend(tokens)
                    continue
                collecting = False

        return sorted(set(server for server in servers if server))

    def detect_vpn_active(self, resolvectl_output: str) -> bool:
        for section in self.parse_link_sections(resolvectl_output):
            if section.get("is_vpn"):
                return True
        return False

    def get_wireguard_interfaces(self) -> set[str]:
        interfaces: set[str] = set()

        if self.has_cmd("wg"):
            rc, out = self.run_cmd(["wg", "show", "interfaces"], timeout=6)
            if rc == 0 and out:
                interfaces.update(
                    token.strip() for token in out.split() if str(token or "").strip()
                )
                if interfaces:
                    return interfaces

        if self.has_cmd("ip"):
            rc, out = self.run_cmd(
                ["ip", "-o", "link", "show", "type", "wireguard"],
                timeout=6,
            )
            if rc == 0 and out:
                for line in out.splitlines():
                    parts = line.split(":", 2)
                    if len(parts) < 2:
                        continue
                    iface = parts[1].strip().split("@", 1)[0].strip()
                    if iface:
                        interfaces.add(iface)

        return interfaces

    def normalize_dns_server(self, dns_server: str) -> str:
        value = (dns_server or "").strip().strip("[]")
        if not value:
            return ""
        if "#" in value:
            value = value.split("#", 1)[0].strip()
        if "%" in value:
            value = value.split("%", 1)[0]
        return value

    def detect_dnssec_mode(self, resolvectl_output: str) -> str:
        lower_text = (resolvectl_output or "").lower()
        if "dnssec=yes" in lower_text or "dnssec setting: yes" in lower_text:
            return "yes"
        if (
            "dnssec=allow-downgrade" in lower_text
            or "dnssec setting: allow-downgrade" in lower_text
        ):
            return "allow-downgrade"
        if "dnssec=no" in lower_text or "dnssec setting: no" in lower_text:
            return "no"
        if "dnssec" in lower_text:
            return "unknown"
        return "unknown"

    def dns_server_is_private_or_local(self, dns_server: str) -> bool:
        value = self.normalize_dns_server(dns_server)
        if not value:
            return False
        try:
            addr = ipaddress.ip_address(value)
        except ValueError:
            return False
        return addr.is_private or addr.is_loopback or addr.is_link_local

    def is_vpn_dns_server(self, dns_server: str) -> bool:
        value = self.normalize_dns_server(dns_server)
        if not value:
            return False
        if value.startswith("10."):
            return True
        if value.startswith("192.168."):
            return True
        if value.startswith("172."):
            try:
                second_octet = int(value.split(".", 2)[1])
            except Exception:
                second_octet = -1
            if 16 <= second_octet <= 31:
                return True
        if ":" in value and value.lower().startswith("2a07:b944"):
            return True
        return False

    def parse_link_sections(self, resolvectl_output: str) -> list[dict]:
        sections: list[dict] = []
        current: dict | None = None
        collecting = False
        wireguard_ifaces = self.get_wireguard_interfaces()

        def finalize_current() -> None:
            nonlocal current, collecting
            if current is not None:
                current["dns_servers"] = sorted(set(current["dns_servers"]))
                sections.append(current)
            current = None
            collecting = False

        for raw_line in (resolvectl_output or "").splitlines():
            stripped = raw_line.strip()
            if stripped.startswith("Link "):
                finalize_current()
                iface = ""
                match = re.search(r"\(([^)]+)\)", stripped)
                if match:
                    iface = match.group(1).strip()
                lowered = stripped.lower()
                iface_lower = iface.lower()
                current = {
                    "header": stripped,
                    "iface": iface,
                    "is_vpn": (
                        bool(iface and iface in wireguard_ifaces)
                        or bool(
                            any(token in lowered for token in self.VPN_TOKENS)
                            or any(token in iface_lower for token in self.VPN_TOKENS)
                        )
                    ),
                    "dns_servers": [],
                    "current_dns_server": "",
                }
                continue

            if current is None:
                continue

            if not stripped:
                collecting = False
                continue

            if stripped.startswith("Current DNS Server:"):
                value = stripped.split(":", 1)[1].strip()
                current["current_dns_server"] = value
                if value:
                    current["dns_servers"].extend(value.split())
                collecting = False
                continue

            if stripped.startswith("DNS Servers:"):
                value = stripped.split(":", 1)[1].strip()
                if value:
                    current["dns_servers"].extend(value.split())
                collecting = True
                continue

            if collecting and not stripped.endswith(":"):
                tokens = self._dns_server_continuation_tokens(stripped)
                if tokens:
                    current["dns_servers"].extend(tokens)
                    continue
                collecting = False

        finalize_current()
        return sections

    def _dns_server_continuation_tokens(self, line: str) -> list[str]:
        tokens = str(line or "").strip().split()
        if not tokens:
            return []
        if all(token.count(".") > 0 or ":" in token for token in tokens):
            return tokens
        return []

    def find_vpn_dns_servers(self, resolvectl_output: str) -> tuple[str, list[str]]:
        for section in self.parse_link_sections(resolvectl_output):
            if section["is_vpn"] and section["dns_servers"]:
                return section["iface"], section["dns_servers"]
        return "", []

    def dns_sources_for_sections(
        self, resolvectl_output: str
    ) -> tuple[list[str], list[str]]:
        vpn_dns: list[str] = []
        physical_dns: list[str] = []
        for section in self.parse_link_sections(resolvectl_output):
            target = vpn_dns if section["is_vpn"] else physical_dns
            target.extend(section["dns_servers"])
        return sorted(set(vpn_dns)), sorted(set(physical_dns))

    def is_physical_dns_candidate(self, name: str, conn_type: str, device: str) -> bool:
        n = str(name or "").strip().lower()
        t = str(conn_type or "").strip().lower()
        d = str(device or "").strip().lower()

        if t not in self.ALLOWED_TYPES:
            return False
        if not d:
            return False
        if d in self.SKIP_DEVICE_NAMES or d.startswith("veth"):
            return False
        if any(token in n for token in self.FORBIDDEN_NAME_TOKENS):
            return False
        if any(token in d for token in self.FORBIDDEN_NAME_TOKENS):
            return False
        return True

    def nm_active_connections_detailed(self) -> list[tuple[str, str, str]]:
        _, out = self.run_cmd(
            ["nmcli", "-t", "-f", "NAME,DEVICE,TYPE", "con", "show", "--active"],
            timeout=5,
        )
        rows: list[tuple[str, str, str]] = []
        for line in (out or "").splitlines():
            parts = line.split(":")
            if len(parts) < 3:
                continue
            name, device, conn_type = parts[0], parts[1], parts[2]
            if name and device:
                rows.append((name, device, conn_type))
        return rows

    def active_nm_dns_targets(
        self,
        *,
        default_iface: str = "",
        default_connection: str = "",
    ) -> list[tuple[str, str]]:
        return self.filter_physical_nm_targets(
            self.nm_active_connections_detailed(),
            default_iface=default_iface,
            default_connection=default_connection,
        )

    def filter_physical_nm_targets(
        self,
        connections: list[tuple[str, str, str]],
        *,
        default_iface: str = "",
        default_connection: str = "",
    ) -> list[tuple[str, str]]:
        targets: list[tuple[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for name, device, conn_type in connections:
            if not self.is_physical_dns_candidate(name, conn_type, device):
                continue
            key = (device.strip(), name.strip())
            if key in seen:
                continue
            seen.add(key)
            targets.append(key)
        if targets:
            return targets

        if (
            default_iface
            and default_connection
            and self.is_physical_dns_candidate(
                default_connection, "ethernet", default_iface
            )
        ):
            return [(default_iface, default_connection)]
        return []

    def detect_netmon_dot_dropin_conflict(
        self,
        path: str | None = None,
    ) -> tuple[bool, str]:
        candidate = path or self.dot_dropin_path
        if not os.path.isfile(candidate):
            return False, ""

        try:
            with open(candidate, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception as exc:
            return True, f"Datei vorhanden, aber nicht lesbar: {exc}"

        conflict = "DNS=" in content and "Domains=~." in content
        return conflict, content

    def evaluate_dns_policy(
        self,
        *,
        resolvectl_output: str,
    ) -> dict:
        text = resolvectl_output or ""
        lower_text = text.lower()
        vpn_active = self.detect_vpn_active(text)
        active_dns = self.parse_active_dns_servers(text)
        vpn_dns, physical_dns = self.dns_sources_for_sections(text)
        global_dns = [
            dns for dns in physical_dns if not self.dns_server_is_private_or_local(dns)
        ]
        if not vpn_dns and not physical_dns:
            global_dns = [
                dns
                for dns in active_dns
                if not self.dns_server_is_private_or_local(dns)
            ]
        dot_dropin_conflict, dot_dropin_content = (
            self.detect_netmon_dot_dropin_conflict()
        )
        dot_dropin_exists = bool(dot_dropin_content)
        dot_active = "+dnsovertls" in lower_text or "dns over tls: yes" in lower_text
        dnssec_mode = self.detect_dnssec_mode(resolvectl_output)
        dnssec_strict = dnssec_mode == "yes"
        dnssec_allow_downgrade = dnssec_mode == "allow-downgrade"
        docker_detected = any(token in lower_text for token in ("docker0", "veth"))
        vpn_dns_detected = sorted(
            set(
                dns
                for dns in active_dns
                if self.is_vpn_dns_server(dns) or dns in vpn_dns
            )
        )
        public_dns_detected = sorted(
            set(dns for dns in active_dns if dns not in vpn_dns_detected)
        )
        only_vpn_dns = vpn_active and bool(vpn_dns_detected) and not public_dns_detected
        multiple_dns_sources = (
            vpn_active and bool(vpn_dns_detected) and bool(public_dns_detected)
        )
        public_dns_while_vpn = vpn_active and bool(global_dns)
        conflict = public_dns_while_vpn or (vpn_active and dot_dropin_conflict)

        resolver_label = "unbekannt"
        if vpn_active and vpn_dns:
            resolver_label = f"VPN ({vpn_dns[0]})"
        elif dot_dropin_exists and active_dns:
            resolver_label = f"Global/DoT ({active_dns[0]})"
        elif physical_dns:
            resolver_label = f"Physisch ({physical_dns[0]})"
        elif active_dns:
            resolver_label = f"System ({active_dns[0]})"

        warnings: list[str] = []
        recommendations: list[str] = []
        risk = "niedrig"

        if vpn_active and global_dns:
            warnings.append(
                "VPN ist aktiv, aber zusätzlich wurden öffentliche/globale DNS-Server erkannt."
            )
            recommendations.append(
                "Globales/User-DNS entfernen und VPN-DNS bevorzugen."
            )
            risk = "hoch"
        elif vpn_active and only_vpn_dns:
            risk = "niedrig"
        elif vpn_active and multiple_dns_sources:
            risk = "mittel"
        elif vpn_active:
            risk = "niedrig"
        else:
            risk = "niedrig"

        if vpn_active and dot_dropin_conflict:
            warnings.append(
                "NetMon DoT-Drop-in erzwingt globale DNS-Server trotz aktivem VPN-DNS."
            )
            if (
                "Globales/User-DNS entfernen und VPN-DNS bevorzugen."
                not in recommendations
            ):
                recommendations.append(
                    "Globales/User-DNS entfernen und VPN-DNS bevorzugen."
                )
            risk = "hoch"

        if docker_detected and not only_vpn_dns:
            warnings.append(
                "Docker/veth-Interfaces wurden erkannt. Diese erzeugen zusätzliche DNS-Kontexte, werden aber von DNS-Control ignoriert."
            )
            if risk == "niedrig":
                risk = "mittel"

        if dnssec_strict and vpn_active and not only_vpn_dns:
            warnings.append("DNSSEC ist strikt aktiv, obwohl VPN-DNS erkannt wurde.")
            recommendations.append(
                "DNSSEC=allow-downgrade ist mit VPN-DNS oft kompatibler als strict."
            )
            if risk == "niedrig":
                risk = "mittel"

        if multiple_dns_sources and risk == "niedrig":
            warnings.append("Mehrere DNS-Quellen sind gleichzeitig sichtbar.")
            recommendations.append(
                "Resolver-Prioritäten prüfen und nur eine Quelle aktiv bevorzugen."
            )
            risk = "mittel"

        if dot_active and vpn_active and not dot_dropin_conflict and not only_vpn_dns:
            warnings.append(
                "DoT ist aktiv, während VPN-DNS genutzt wird. Das ist nicht automatisch falsch, sollte aber bewusst geprüft werden."
            )
            recommendations.append(
                "VPN-DNS bevorzugen und globales DoT nur ohne VPN aktivieren."
            )
            if risk == "niedrig":
                risk = "mittel"

        if not recommendations:
            if vpn_active and vpn_dns and not global_dns and not dot_dropin_conflict:
                recommendations.append("VPN-DNS aktiv, keine Aktion nötig.")
            elif not vpn_active and dot_dropin_exists:
                recommendations.append(
                    "Manuelles DoT ist aktiv. Das ist ohne VPN grundsätzlich unkritisch."
                )
            else:
                recommendations.append("Keine Änderung empfohlen.")

        return {
            "vpn_active": vpn_active,
            "vpn_dns": vpn_dns,
            "vpn_dns_detected": vpn_dns_detected,
            "global_dns": global_dns,
            "public_dns_detected": public_dns_detected,
            "physical_dns": physical_dns,
            "active_dns": active_dns,
            "dot_dropin_exists": dot_dropin_exists,
            "dot_dropin_conflict": dot_dropin_conflict,
            "dot_active": dot_active,
            "dnssec_strict": dnssec_strict,
            "dnssec_allow_downgrade": dnssec_allow_downgrade,
            "dnssec_mode": dnssec_mode,
            "docker_detected": docker_detected,
            "multiple_dns_sources": multiple_dns_sources,
            "only_vpn_dns": only_vpn_dns,
            "leak": public_dns_while_vpn,
            "conflict": conflict,
            "risk": risk,
            "recommendation": recommendations[0],
            "recommendations": recommendations,
            "warnings": warnings,
            "resolver_label": resolver_label,
        }

    def build_dns_health_report(self, resolvectl_output: str, tr=None) -> str:
        def _tr(key: str, fallback: str) -> str:
            if callable(tr):
                try:
                    return tr(key, fallback)
                except Exception:
                    return fallback
            return fallback

        evaluation = self.evaluate_dns_policy(resolvectl_output=resolvectl_output)
        active_dns = list(evaluation.get("active_dns") or [])
        primary_dns = active_dns[0] if active_dns else ""
        fallback_dns = active_dns[1] if len(active_dns) > 1 else ""
        dnssec_active = bool(
            evaluation.get("dnssec_strict") or evaluation.get("dnssec_allow_downgrade")
        )
        dot_active = bool(evaluation.get("dot_active"))
        conflict = bool(evaluation.get("conflict"))
        warnings = list(evaluation.get("warnings") or [])

        lines = [_tr("dns_health_report_title", "=== DNS Health Check ==="), ""]

        if primary_dns:
            lines.append(
                _tr("dns_health_primary_dns", "✔ Active DNS server: {dns}").format(
                    dns=primary_dns
                )
            )
        else:
            lines.append(
                _tr("dns_health_no_primary_dns", "✖ No active DNS server detected")
            )

        if fallback_dns:
            lines.append(
                _tr("dns_health_fallback_dns", "✔ Fallback DNS: {dns}").format(
                    dns=fallback_dns
                )
            )

        lines.append(
            _tr("dns_health_dot_active", "✔ DNS-over-TLS: active")
            if dot_active
            else _tr("dns_health_dot_inactive", "✖ DNS-over-TLS not active")
        )

        if evaluation.get("dnssec_strict"):
            lines.append(
                _tr("dns_health_dnssec_strict", "✔ DNSSEC: active (Strict Mode)")
            )
        elif evaluation.get("dnssec_allow_downgrade"):
            lines.append(
                _tr(
                    "dns_health_dnssec_fallback",
                    "○ DNSSEC: active (fallback possible)",
                )
            )
        else:
            lines.append(_tr("dns_health_dnssec_unavailable", "✖ DNSSEC unavailable"))

        lines.extend(["", _tr("result_section_title", "=== Result ===")])
        if primary_dns and dot_active and dnssec_active and not conflict:
            lines.append(_tr("dns_health_result_stable", "✔ DNS configuration stable"))
            lines.append(_tr("dns_health_result_no_issues", "✔ No anomalies detected"))
        else:
            if conflict:
                lines.append(
                    _tr("dns_health_result_conflict", "✖ DNS-Konfiguration auffällig")
                )
                lines.append(
                    _tr(
                        "dns_health_result_conflict_hint",
                        "✖ Möglicher DNS-Konflikt erkannt",
                    )
                )
            else:
                lines.append(
                    _tr("dns_health_result_limited", "✖ DNS configuration limited")
                )
                if warnings:
                    lines.append(
                        f"✖ {self._translate_policy_warning(warnings[0], tr=tr)}"
                    )
                else:
                    lines.append(
                        _tr("dns_health_result_issues", "✖ Anomalies detected")
                    )
        return "\n".join(lines).rstrip()

    def build_dns_leak_check_result(
        self,
        *,
        resolvectl_output: str,
        dns_servers: list[str],
        public_ip: str,
        tr=None,
    ) -> str:
        def _tr(key: str, fallback: str) -> str:
            if callable(tr):
                try:
                    return tr(key, fallback)
                except Exception:
                    return fallback
            return fallback

        evaluation = self.evaluate_dns_policy(resolvectl_output=resolvectl_output)
        leak = bool(evaluation["leak"])
        only_vpn_dns = bool(evaluation["only_vpn_dns"])
        multiple_dns_sources = bool(evaluation["multiple_dns_sources"])

        if evaluation["vpn_active"]:
            if leak:
                risk = _tr("dns_leak_risk_high", "high")
                status = _tr(
                    "dns_leak_status_leak_detected",
                    "Leak detected / public DNS additionally active",
                )
            elif only_vpn_dns:
                risk = _tr("dns_leak_risk_low", "low")
                status = _tr(
                    "dns_leak_status_vpn_only",
                    "OK / VPN DNS exclusively active",
                )
            elif multiple_dns_sources:
                risk = _tr("dns_leak_risk_medium", "medium")
                status = _tr(
                    "dns_leak_status_conflict",
                    "Leak possible / configuration conflict",
                )
            else:
                risk = _tr("dns_leak_risk_low", "low")
                status = _tr("dns_leak_status_ok", "OK / leak-free")
        else:
            risk = _tr("dns_leak_risk_low", "low")
            status = _tr("dns_leak_status_vpn_inactive", "VPN not active")

        lines = [
            _tr("dns_leak_report_title", "=== DNS Leak Check ==="),
            "",
            _tr("dns_leak_public_ip", "Public IP: {ip}").format(
                ip=public_ip or _tr("dns_leak_unknown", "unknown")
            ),
            _tr("dns_leak_vpn_detected", "VPN detected: {value}").format(
                value=(
                    _tr("dns_leak_yes", "YES")
                    if evaluation["vpn_active"]
                    else _tr("dns_leak_no", "NO")
                )
            ),
            "",
            _tr("dns_leak_dns_servers", "DNS servers:"),
        ]
        if dns_servers:
            for dns in dns_servers:
                lines.append(f"- {dns}")
        else:
            lines.append(
                f"- {_tr('dns_leak_no_dns_servers', 'No DNS servers detected')}"
            )

        lines.extend(
            [
                "",
                _tr("dns_leak_detected", "Leak detected: {value}").format(
                    value=(
                        _tr("dns_leak_yes", "YES") if leak else _tr("dns_leak_no", "NO")
                    )
                ),
                _tr("dns_leak_status_line", "Status: {status}").format(status=status),
                _tr("dns_leak_risk_line", "Risk: {risk}").format(risk=risk),
                "",
            ]
        )

        if evaluation["global_dns"]:
            lines.append(_tr("dns_leak_findings", "Findings:"))
            for dns in evaluation["global_dns"]:
                lines.append(
                    _tr(
                        "dns_leak_public_dns_detected", "Public DNS detected: {dns}"
                    ).format(dns=dns)
                )
            lines.append("")

        lines.append(_tr("dns_leak_recommendation", "Recommendation:"))
        if leak:
            lines.append(
                f"- {_tr('dns_leak_action_enforce_vpn_dns', 'Enforce VPN DNS')}"
            )
            lines.append(
                f"- {_tr('dns_leak_action_check_resolved', 'Check systemd-resolved')}"
            )
            lines.append(
                f"- {_tr('dns_leak_action_remove_global_dns', 'Remove global/user DNS')}"
            )
        elif only_vpn_dns:
            lines.append(
                f"- {_tr('dns_leak_action_none_needed', 'VPN DNS active, no action needed')}"
            )
        elif not evaluation["vpn_active"]:
            lines.append(
                f"- {_tr('dns_leak_action_vpn_inactive', 'VPN not active; no VPN leak to assess')}"
            )
        else:
            lines.append(f"- {evaluation['recommendation']}")

        return "\n".join(lines)

    def apply_nm_dns_policy_to_targets(
        self,
        *,
        ignore_auto_dns: bool,
        targets: list[tuple[str, str]],
    ) -> tuple[bool, list[str]]:
        if not self.has_cmd("nmcli"):
            return False, ["nmcli fehlt – NetworkManager ist nicht verfügbar."]
        if not targets:
            return False, ["Keine aktive physische LAN/WLAN-Connection gefunden."]

        details: list[str] = []
        success = True
        ignore_value = "yes" if ignore_auto_dns else "no"

        def run_step(cmd: list[str], *, error_prefix: str) -> tuple[bool, str]:
            rc, out = self.run_cmd(cmd, timeout=12)
            if rc == 0:
                return True, ""
            message = (out or "").strip() or "unbekannter Fehler"
            return False, f"{error_prefix}: {message}"

        for iface, con in targets:
            details.append(f"✔ Verbindung erkannt: {con} ({iface})")

            ipv4_ok, ipv4_err = run_step(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "con",
                    "mod",
                    con,
                    "ipv4.ignore-auto-dns",
                    ignore_value,
                ],
                error_prefix="✖ Fehler beim Setzen von Auto-DNS (IPv4)",
            )
            ipv6_ok, ipv6_err = run_step(
                [
                    "sudo",
                    "-n",
                    "nmcli",
                    "con",
                    "mod",
                    con,
                    "ipv6.ignore-auto-dns",
                    ignore_value,
                ],
                error_prefix="✖ Fehler beim Setzen von Auto-DNS (IPv6)",
            )
            if ipv4_ok and ipv6_ok:
                auto_dns_label = "deaktiviert" if ignore_auto_dns else "aktiviert"
                details.append(f"✔ Auto-DNS {auto_dns_label} (IPv4 / IPv6)")
            else:
                success = False
                if ipv4_err:
                    details.append(ipv4_err)
                if ipv6_err:
                    details.append(ipv6_err)

            dns4_ok, dns4_err = run_step(
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.dns", ""],
                error_prefix="✖ Fehler beim Zurücksetzen der DNS-Server (IPv4)",
            )
            dns6_ok, dns6_err = run_step(
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv6.dns", ""],
                error_prefix="✖ Fehler beim Zurücksetzen der DNS-Server (IPv6)",
            )
            if dns4_ok and dns6_ok:
                details.append("✔ Manuelle DNS-Server zurückgesetzt")
            else:
                success = False
                if dns4_err:
                    details.append(dns4_err)
                if dns6_err:
                    details.append(dns6_err)

            up_ok, up_err = run_step(
                ["sudo", "-n", "nmcli", "con", "up", con],
                error_prefix="✖ Fehler beim Neustart der Verbindung",
            )
            if up_ok:
                details.append("✔ Verbindung neu gestartet")
            else:
                success = False
                details.append(up_err)

            details.append("")
        return success, details

    def write_dropin(self, content: str) -> tuple[bool, str]:
        rc, out = write_privileged_config(
            self.dot_dropin_path,
            content,
            run_cmd_fn=self.run_cmd,
            timeout=12,
        )
        return rc == 0, (out or "").strip()

    def remove_dropin(self) -> tuple[bool, str]:
        rc, out = self.run_cmd(
            ["sudo", "-n", "rm", "-f", self.dot_dropin_path],
            timeout=10,
        )
        return rc == 0, (out or "").strip()

    def restart_resolved(self) -> tuple[bool, str]:
        rc, out = self.run_cmd(
            ["sudo", "-n", "systemctl", "restart", "systemd-resolved"],
            timeout=15,
        )
        return rc == 0, (out or "").strip()

    def apply_vpn_dns_policy(
        self, *, targets: list[tuple[str, str]]
    ) -> tuple[bool, str]:
        nm_ok, nm_details = self.apply_nm_dns_policy_to_targets(
            ignore_auto_dns=True,
            targets=targets,
        )
        rm_ok, rm_detail = self.remove_dropin()
        restart_ok, restart_detail = self.restart_resolved()
        success = nm_ok and rm_ok and restart_ok

        lines = [
            "=== DNS Control ===",
            "Aktion: VPN-DNS erzwingen",
            f"Ergebnis: {'erfolgreich' if success else 'fehlgeschlagen'}",
            "",
            "[System]",
            (
                "✔ NetMon DoT-Konfiguration entfernt"
                if rm_ok
                else f"✖ Fehler beim Entfernen der NetMon DoT-Konfiguration: {rm_detail or 'unknown'}"
            ),
            (
                "✔ systemd-resolved neu gestartet"
                if restart_ok
                else f"✖ Fehler beim Neustarten von systemd-resolved: {restart_detail or 'fehlgeschlagen'}"
            ),
            "",
            "[NetworkManager]",
            *nm_details,
        ]
        return success, "\n".join(lines).strip()


__all__ = ["DNSControlService"]
