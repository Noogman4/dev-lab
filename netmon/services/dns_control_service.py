"""Central DNS evaluation and repair helpers for NetMon."""

from __future__ import annotations

import ipaddress
import os
import re
import tempfile
from typing import Callable

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
                tokens = stripped.split()
                if tokens and all(token.count(".") or ":" in token for token in tokens):
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
                tokens = stripped.split()
                if tokens and all(token.count(".") or ":" in token for token in tokens):
                    current["dns_servers"].extend(tokens)
                    continue
                collecting = False

        finalize_current()
        return sections

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
        dns_mode: str = "auto",
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
        dnssec_strict = (
            "dnssec=yes" in lower_text or "dnssec setting: yes" in lower_text
        )
        dnssec_allow_downgrade = (
            "dnssec=allow-downgrade" in lower_text
            or "dnssec setting: allow-downgrade" in lower_text
        )
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
            "dns_mode": dns_mode,
        }

    def build_dns_health_report(
        self, resolvectl_output: str, *, dns_mode: str = "auto"
    ) -> str:
        evaluation = self.evaluate_dns_policy(
            resolvectl_output=resolvectl_output,
            dns_mode=dns_mode,
        )

        lines = [
            "=== DNS Health Check ===",
            "",
            f"DNS-Modus: {dns_mode.upper()}",
            f"VPN-DNS erkannt: {'JA' if evaluation['vpn_active'] else 'NEIN'}",
            f"DNS over TLS aktiv: {'JA' if evaluation['dot_active'] else 'NEIN'}",
            f"NetMon DoT Drop-in: {'vorhanden' if evaluation['dot_dropin_exists'] else 'nicht vorhanden'}",
            f"Globale DNS-Erzwingung: {'JA' if evaluation['dot_dropin_conflict'] else 'NEIN'}",
            f"Docker/veth erkannt: {'JA' if evaluation['docker_detected'] else 'NEIN'}",
            f"Mehrere DNS-Quellen: {'JA' if evaluation['multiple_dns_sources'] else 'NEIN'}",
            f"Aktiver Resolver: {evaluation['resolver_label']}",
        ]
        if evaluation["conflict"]:
            lines.append("Bewertung: DNS-Leak-Risiko")
        lines.extend(
            [
                f"Risiko: {evaluation['risk']}",
                "",
                "VPN-DNS:",
            ]
        )
        if evaluation["vpn_dns"]:
            for dns in evaluation["vpn_dns"]:
                lines.append(f"- {dns}")
        else:
            lines.append("- Keine VPN-DNS-Server erkannt")

        lines.append("")
        lines.append("Globale/öffentliche DNS:")
        if evaluation["global_dns"]:
            for dns in evaluation["global_dns"]:
                lines.append(f"- {dns}")
        else:
            lines.append("- leer")

        lines.append("")
        lines.append("Physische LAN/WLAN-DNS:")
        if evaluation["physical_dns"]:
            for dns in evaluation["physical_dns"]:
                lines.append(f"- {dns}")
        else:
            lines.append("- leer")

        lines.append("")
        lines.append("Auffälligkeiten:")
        if evaluation["warnings"]:
            for warning in evaluation["warnings"]:
                lines.append(f"- {warning}")
        else:
            lines.append("- Keine kritischen Auffälligkeiten erkannt.")

        lines.append("")
        lines.append("Empfehlungen:")
        for recommendation in evaluation["recommendations"]:
            lines.append(f"- {recommendation}")

        lines.append("")
        lines.append("Rohdaten:")
        lines.append(resolvectl_output or "")
        return "\n".join(lines).rstrip()

    def build_dns_leak_check_result(
        self,
        *,
        resolvectl_output: str,
        dns_servers: list[str],
        public_ip: str,
    ) -> str:
        evaluation = self.evaluate_dns_policy(resolvectl_output=resolvectl_output)
        leak = bool(evaluation["leak"])
        only_vpn_dns = bool(evaluation["only_vpn_dns"])
        multiple_dns_sources = bool(evaluation["multiple_dns_sources"])

        if evaluation["vpn_active"]:
            if leak:
                risk = "hoch"
                status = "Leak erkannt / öffentlicher DNS zusätzlich aktiv"
            elif only_vpn_dns:
                risk = "niedrig"
                status = "OK / VPN-DNS exklusiv aktiv"
            elif multiple_dns_sources:
                risk = "mittel"
                status = "Leak möglich / Konfigurationskonflikt"
            else:
                risk = "niedrig"
                status = "OK / leak-frei"
        else:
            risk = "niedrig"
            status = "VPN nicht aktiv"

        lines = [
            "=== DNS Leak Check ===",
            "",
            f"Öffentliche IP: {public_ip or 'unbekannt'}",
            f"VPN erkannt: {'JA' if evaluation['vpn_active'] else 'NEIN'}",
            "",
            "DNS Server:",
        ]
        if dns_servers:
            for dns in dns_servers:
                lines.append(f"- {dns}")
        else:
            lines.append("- Keine DNS-Server erkannt")

        lines.extend(
            [
                "",
                f"Leak erkannt: {'JA' if leak else 'NEIN'}",
                f"Status: {status}",
                f"Risiko: {risk}",
                "",
            ]
        )

        if evaluation["global_dns"]:
            lines.append("Auffälligkeiten:")
            for dns in evaluation["global_dns"]:
                lines.append(f"- Öffentlicher DNS erkannt: {dns}")
            lines.append("")

        lines.append("Empfehlung:")
        if leak:
            lines.append("- VPN-DNS erzwingen")
            lines.append("- systemd-resolved prüfen")
            lines.append("- Globales/User-DNS entfernen")
        elif only_vpn_dns:
            lines.append("- VPN-DNS aktiv, keine Aktion nötig")
        elif not evaluation["vpn_active"]:
            lines.append("- VPN nicht aktiv; kein VPN-Leak zu bewerten")
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

        for iface, con in targets:
            cmds = [
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
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv4.dns", ""],
                ["sudo", "-n", "nmcli", "con", "mod", con, "ipv6.dns", ""],
                ["sudo", "-n", "nmcli", "con", "up", con],
            ]
            details.append(f"Connection: {con} ({iface})")
            for cmd in cmds:
                rc, out = self.run_cmd(cmd, timeout=12)
                details.append(f"$ {' '.join(cmd)}")
                details.append(f"rc={rc}")
                if out:
                    details.append((out or "").strip())
                if rc != 0:
                    success = False
                details.append("")
        return success, details

    def write_dropin(self, content: str) -> tuple[bool, str]:
        tmp_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", delete=False
            ) as temp_file:
                temp_file.write(content)
                tmp_path = temp_file.name
            rc_dir, out_dir = self.run_cmd(
                ["sudo", "-n", "mkdir", "-p", self.dot_dropin_dir],
                timeout=10,
            )
            if rc_dir != 0:
                return False, (out_dir or "").strip() or "Drop-in-Verzeichnis fehlt."
            rc_install, out_install = self.run_cmd(
                ["sudo", "-n", "install", "-m", "644", tmp_path, self.dot_dropin_path],
                timeout=12,
            )
            if rc_install != 0:
                return (
                    False,
                    (out_install or "").strip()
                    or "DNS-Drop-in konnte nicht geschrieben werden.",
                )
            return True, ""
        finally:
            if tmp_path:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

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
            "NetMon DoT Drop-in:",
            "entfernt" if rm_ok else f"Fehler: {rm_detail or 'unknown'}",
            "",
            "NetworkManager:",
            *nm_details,
            "systemd-resolved Restart:",
            "OK" if restart_ok else (restart_detail or "fehlgeschlagen"),
        ]
        return success, "\n".join(lines).strip()


__all__ = ["DNSControlService"]
