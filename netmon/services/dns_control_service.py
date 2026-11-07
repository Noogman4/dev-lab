"""Central DNS evaluation and repair helpers for NetMon."""

from __future__ import annotations

import ipaddress
import os
import re
import threading
import uuid
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
    AUTO_DNS_RELEASE_BLOCK_REASON = (
        "DHCP-/ISP-DNS-Freigabe vorläufig gesperrt; "
        "sichere Koordination mit VPN-Wechseln fehlt."
    )

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
        self._vpn_repair_lock = threading.Lock()
        self.dns_mutation_lock = threading.RLock()
        self._unresolved_vpn_state = None
        self._resolved_reload_pending = False
        self._nm_activation_pending = {}

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

    def verify_dns_profile(self, servers: list[str]) -> tuple[bool, str]:
        """Confirm the observed resolver list, without changing any DNS state."""
        try:
            expected = {self.normalize_dns_server(server) for server in servers}
            if not expected:
                return False, "Resolver-Profil unklar: keine Zielserver."
            for server in expected:
                ipaddress.ip_address(server)
            rc, text = self.read_resolvectl_status()
            snapshot = self.parse_dns_snapshot(text, status_ok=rc == 0)
            if not snapshot["status_ok"] or snapshot["parse_errors"]:
                return (
                    False,
                    "Resolver-Zustand nicht vollständig lesbar; Profil nicht bestätigt.",
                )
            actual = set(snapshot["active_dns"])
            if actual != expected:
                return False, (
                    "Resolver-Profil abweichend. Erwartet: "
                    + ", ".join(sorted(expected))
                    + "; erkannt: "
                    + (", ".join(sorted(actual)) or "keine DNS-Server")
                    + ". Konfiguration prüfen."
                )
            return True, "Resolver-Profil bestätigt: " + ", ".join(sorted(actual))
        except Exception:
            return False, "Resolver-Zustand nicht prüfbar; Profil nicht bestätigt."

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

    def get_wireguard_interfaces(self) -> set[str] | None:
        interfaces: set[str] = set()
        inventory_known = False

        if self.has_cmd("wg"):
            rc, out = self.run_cmd(["wg", "show", "interfaces"], timeout=6)
            if rc == 0:
                inventory_known = True
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
            if rc == 0:
                inventory_known = True
            if rc == 0 and out:
                for line in out.splitlines():
                    parts = line.split(":", 2)
                    if len(parts) < 2:
                        continue
                    iface = parts[1].strip().split("@", 1)[0].strip()
                    if iface:
                        interfaces.add(iface)

        return interfaces if inventory_known else None

    def normalize_dns_server(self, dns_server: str) -> str:
        value = str(dns_server or "").strip().split("#", 1)[0].strip().strip("[]")
        try:
            # IPv6 interface zones are part of the link identity, not discarded.
            return str(ipaddress.ip_address(value))
        except ValueError:
            return value.lower()

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

    def read_dns_snapshot(self, timeout: int = 8) -> dict:
        code, text = self.read_resolvectl_status(timeout=timeout)
        snapshot = self.parse_dns_snapshot(text, status_ok=code == 0)
        conflict, content = self.detect_netmon_dot_dropin_conflict()
        snapshot.update(dot_dropin_conflict=conflict, dot_dropin_content=content)
        return snapshot

    def parse_dns_snapshot(self, text: str, *, status_ok: bool = True) -> dict:
        links = []
        global_section = {"dns_servers": [], "domains": [], "default_route": None}
        current = global_section
        collecting = ""
        # Keep inventory success in this snapshot, not mutable service state:
        # UI/status workers may query concurrently.
        inventory = self.get_wireguard_interfaces() if status_ok else None
        wireguard_ifaces = inventory or set()
        recognized = False
        parse_errors = []

        def set_default_route(value):
            previous = current["default_route"]
            if value is None or (previous is not None and previous != value):
                parse_errors.append("Widersprüchliche/ungültige DefaultRoute-Angabe")
            current["default_route"] = value

        for raw in (text or "").splitlines():
            line = raw.strip()
            if line == "Global":
                recognized = True
                current = global_section
                collecting = ""
                continue
            if line.startswith("Link "):
                recognized = True
                match = re.search(r"\(([^)]+)\)", line)
                iface = match[1].strip() if match else ""
                if not iface:
                    parse_errors.append("Ungültiger Link-Header")
                current = {
                    "header": line,
                    "iface": iface,
                    "is_vpn": iface in wireguard_ifaces
                    or any(t in iface.lower() for t in self.VPN_TOKENS),
                    "dns_servers": [],
                    "current_dns_server": "",
                    "domains": [],
                    "default_route": None,
                    "dns_scope": None,
                }
                links.append(current)
                collecting = ""
                continue
            if not line:
                collecting = ""
                continue
            if line.startswith("Protocols:"):
                positive = "+DefaultRoute" in line
                negative = "-DefaultRoute" in line
                if positive and negative:
                    parse_errors.append("Widersprüchliche DefaultRoute-Flags")
                elif positive or negative:
                    set_default_route(positive)
                collecting = ""
                continue
            if line.startswith(
                ("DefaultRoute setting:", "Default Route:", "DefaultRoute:")
            ):
                value = line.split(":", 1)[1].strip().lower()
                set_default_route({"yes": True, "no": False}.get(value))
                collecting = ""
                continue
            if line.startswith("Current Scopes:"):
                current["dns_scope"] = "DNS" in line.split(":", 1)[1].split()
                collecting = ""
                continue
            if line.startswith("Current DNS Server:"):
                value = line.split(":", 1)[1].strip()
                current["current_dns_server"] = self.normalize_dns_server(value)
                current["dns_servers"].extend(value.split())
                collecting = ""
                continue
            if line.startswith(("DNS Servers:", "DNS Domain:")):
                collecting = (
                    "dns_servers" if line.startswith("DNS Servers:") else "domains"
                )
                current[collecting].extend(line.split(":", 1)[1].split())
                continue
            # Continuations must be indented values, not another status field.
            if collecting == "dns_servers":
                tokens = self._dns_server_continuation_tokens(line)
                if tokens:
                    current[collecting].extend(tokens)
                    continue
            elif collecting == "domains" and ":" not in line:
                current[collecting].extend(line.split())
                continue
            collecting = ""
        for section in [global_section, *links]:
            for token in section["dns_servers"]:
                try:
                    ipaddress.ip_address(self.normalize_dns_server(token))
                except ValueError:
                    parse_errors.append("Ungültige DNS-Adresse")
            section["dns_servers"] = sorted(
                {self.normalize_dns_server(x) for x in section["dns_servers"] if x}
            )
            section["domains"] = sorted(
                {
                    x.lower().rstrip(".") if x not in {"~.", "."} else "~."
                    for x in section["domains"]
                }
            )
        known = status_ok and recognized
        vpn_found = any(x["is_vpn"] for x in links)
        wireguard_links = {
            x["iface"]
            for x in links
            if x["iface"]
            and (
                x["iface"].lower().startswith("wg") or "wireguard" in x["iface"].lower()
            )
        }
        inventory_conflict = inventory is not None and any(
            iface not in inventory for iface in wireguard_links
        )
        vpn_state = (
            "unknown"
            if inventory_conflict
            else (
                "active"
                if vpn_found
                else "inactive" if inventory == set() else "unknown"
            )
        )
        return {
            "text": text or "",
            "status_ok": known,
            "vpn_state": (
                vpn_state if known and all(x["iface"] for x in links) else "unknown"
            ),
            "parse_errors": parse_errors,
            "global": global_section,
            "links": links,
            "active_dns": sorted(
                {
                    d
                    for section in [global_section, *links]
                    for d in section["dns_servers"]
                }
            ),
            "dot_active": "+dnsovertls" in (text or "").lower()
            or "dns over tls: yes" in (text or "").lower(),
        }

    def parse_link_sections(self, resolvectl_output: str) -> list[dict]:
        return self.parse_dns_snapshot(resolvectl_output)["links"]

    def vpn_dns_routing(self, snapshot: dict) -> dict:
        links = snapshot["links"]
        vpn = [
            x
            for x in links
            if x["is_vpn"] and x["dns_servers"] and x.get("dns_scope") is not False
        ]
        vpn_dns = sorted({d for x in vpn for d in x["dns_servers"]})
        vpn_domains = {d for x in vpn for d in x["domains"]}
        root_route = "~." in vpn_domains
        exposed = []
        split_ifaces = []
        for section in [snapshot["global"], *[x for x in links if not x["is_vpn"]]]:
            if not section["dns_servers"] or section.get("dns_scope") is False:
                continue
            domains = set(section["domains"])
            # Search domains also route DNS; '~' changes search expansion only.
            overlap = {d.lstrip("~") for d in domains} & {
                d.lstrip("~") for d in vpn_domains
            }
            specific = bool(domains) and "~." not in domains and not overlap
            if specific:
                if section.get("iface"):
                    split_ifaces.append(section["iface"])
                # Specific domains do not disable a link's default route.
                # Preserve intentional split profiles; an unsafe general route
                # remains visible even when we cannot safely rewrite that profile.
                if root_route or (
                    section.get("iface") and section.get("default_route") is False
                ):
                    continue
                exposed.append(section)
                continue
            if overlap or "~." in domains:
                exposed.append(section)
            elif root_route:
                continue
            elif not section.get("iface") or section.get("default_route") is not False:
                exposed.append(section)
        return {
            "vpn_dns": vpn_dns,
            "exposed_dns": sorted({d for x in exposed for d in x["dns_servers"]}),
            "repair_ifaces": sorted({x["iface"] for x in exposed if x.get("iface")}),
            "split_ifaces": sorted(split_ifaces),
            "policy_unknown": bool(snapshot.get("parse_errors"))
            or snapshot["vpn_state"] == "unknown"
            or (snapshot["vpn_state"] == "active" and not vpn_dns),
        }

    def _dns_server_continuation_tokens(self, line: str) -> list[str]:
        tokens = str(line or "").strip().split()
        if not tokens:
            return []
        if all(token.count(".") > 0 or ":" in token for token in tokens):
            return tokens
        return []

    def find_vpn_dns_servers(self, resolvectl_output: str) -> tuple[str, list[str]]:
        sections = [
            s
            for s in self.parse_link_sections(resolvectl_output)
            if s["is_vpn"] and s["dns_servers"]
        ]
        return (
            (
                sections[0]["iface"],
                sorted({d for s in sections for d in s["dns_servers"]}),
            )
            if sections
            else ("", [])
        )

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
        return self.evaluate_dns_snapshot(self.parse_dns_snapshot(resolvectl_output))

    def evaluate_dns_snapshot(self, snapshot: dict) -> dict:
        text = snapshot["text"]
        lower_text = text.lower()
        vpn_active = snapshot["vpn_state"] == "active"
        active_dns = snapshot["active_dns"]
        routing = self.vpn_dns_routing(snapshot)
        vpn_dns = routing["vpn_dns"]
        physical_dns = sorted(
            {d for x in snapshot["links"] if not x["is_vpn"] for d in x["dns_servers"]}
        )
        global_dns = (
            routing["exposed_dns"] if vpn_active else snapshot["global"]["dns_servers"]
        )
        if "dot_dropin_content" in snapshot:
            dot_dropin_conflict, dot_dropin_content = (
                snapshot["dot_dropin_conflict"],
                snapshot["dot_dropin_content"],
            )
        else:
            dot_dropin_conflict, dot_dropin_content = (
                self.detect_netmon_dot_dropin_conflict()
            )
        dot_dropin_exists = bool(dot_dropin_content)
        dot_active = "+dnsovertls" in lower_text or "dns over tls: yes" in lower_text
        dnssec_mode = self.detect_dnssec_mode(text)
        dnssec_strict = dnssec_mode == "yes"
        dnssec_allow_downgrade = dnssec_mode == "allow-downgrade"
        docker_detected = any(token in lower_text for token in ("docker0", "veth"))
        # Only eligible competing routes are policy evidence. Shadowed global
        # resolvers and intentional split DNS remain visible as diagnostics.
        vpn_dns_detected = vpn_dns if vpn_active else []
        public_dns_detected = global_dns if vpn_active else active_dns
        only_vpn_dns = (
            vpn_active
            and bool(vpn_dns)
            and not global_dns
            and not routing["policy_unknown"]
        )
        multiple_dns_sources = vpn_active and bool(vpn_dns) and bool(global_dns)
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

        if routing["policy_unknown"]:
            risk = "unbekannt"
            recommendations = ["DNS-/VPN-Status unklar; keine automatische Änderung."]

        return {
            "vpn_active": vpn_active,
            "vpn_state": snapshot["vpn_state"],
            "policy_unknown": routing["policy_unknown"],
            "repair_ifaces": routing["repair_ifaces"],
            "split_ifaces": routing["split_ifaces"],
            "configured_global_dns": snapshot["global"]["dns_servers"],
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

        if evaluation["policy_unknown"]:
            risk = _tr("dns_leak_unknown", "unknown")
            status = _tr(
                "dns_leak_status_unknown",
                "VPN/DNS status unknown; no policy conclusion",
            )
        elif evaluation["vpn_active"]:
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
                    _tr("dns_leak_unknown", "unknown")
                    if evaluation["vpn_state"] == "unknown"
                    else (
                        _tr("dns_leak_yes", "YES")
                        if evaluation["vpn_active"]
                        else _tr("dns_leak_no", "NO")
                    )
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
                        _tr("dns_leak_unknown", "unknown")
                        if evaluation["policy_unknown"]
                        else (
                            _tr("dns_leak_yes", "YES")
                            if leak
                            else _tr("dns_leak_no", "NO")
                        )
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
        if evaluation["policy_unknown"]:
            lines.append(f"- {evaluation['recommendation']}")
        elif leak:
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

    def read_nm_dns_profiles(self, targets: list[tuple[str, str]]) -> list[dict]:
        if not self.has_cmd("nmcli"):
            raise ValueError("nmcli fehlt – NetworkManager ist nicht verfügbar.")
        profiles = []
        fields = "connection.uuid,connection.interface-name,connection.type,ipv4.ignore-auto-dns,ipv6.ignore-auto-dns,ipv4.dns,ipv6.dns"
        for iface, name in targets:
            rc, out = self.run_cmd(
                ["nmcli", "-g", fields, "con", "show", "id", name],
                timeout=8,
                # Empty final DNS fields are part of the seven-field snapshot.
                preserve_output=True,
            )
            values = (out or "").split("\n")
            if values and values[-1] == "":
                values.pop()
            if rc or len(values) != 7:
                raise ValueError(
                    f"DNS-Profil nicht vollständig lesbar: {name} ({iface})"
                )
            identity, bound_iface, kind, dns4_auto, dns6_auto, dns4, dns6 = values
            try:
                canonical = str(uuid.UUID(identity))
            except ValueError as exc:
                raise ValueError(f"Ungültige Profil-UUID: {name}") from exc
            if (
                identity.lower() != canonical
                or (bound_iface and bound_iface != iface)
                or not self.is_physical_dns_candidate(name, kind, iface)
            ):
                raise ValueError(f"DNS-Profilidentität abweichend: {name} ({iface})")
            if dns4_auto not in {"yes", "no"} or dns6_auto not in {"yes", "no"}:
                raise ValueError(f"Auto-DNS-Zustand unklar: {name}")
            rc, active = self.run_cmd(
                ["nmcli", "-g", "GENERAL.CON-UUID", "device", "show", iface], timeout=8
            )
            if rc or (active or "").strip().lower() != canonical:
                raise ValueError(f"Aktive Verbindung geändert: {iface}")
            profiles.append(
                {
                    "iface": iface,
                    "name": name,
                    "uuid": canonical,
                    "properties": {
                        "ipv4.ignore-auto-dns": dns4_auto,
                        "ipv6.ignore-auto-dns": dns6_auto,
                        "ipv4.dns": dns4,
                        "ipv6.dns": dns6,
                    },
                }
            )
        return profiles

    def _apply_nm_dns_profiles(
        self, profiles: list[dict], ignore_auto_dns: bool
    ) -> tuple[bool, list[str]]:
        if ignore_auto_dns is not True:
            return False, [self.AUTO_DNS_RELEASE_BLOCK_REASON]
        details = []
        desired = {
            "ipv4.ignore-auto-dns": "yes",
            "ipv6.ignore-auto-dns": "yes",
            "ipv4.dns": "",
            "ipv6.dns": "",
        }
        for profile in profiles:
            changes = {
                key: value
                for key, value in desired.items()
                if profile["properties"][key] != value
            }
            pending = self._nm_activation_pending.get(profile["uuid"])
            retry_activation = pending == (profile["iface"], desired) and not changes
            if not changes and not retry_activation:
                details.append(
                    f"✔ Bereits korrekt: {profile['name']} ({profile['iface']}); keine Aktivierung"
                )
                continue
            # Revalidate identity AND the settings used to build this plan.
            live = self.read_nm_dns_profiles([(profile["iface"], profile["name"])])[0]
            if live != profile:
                raise ValueError(
                    f"DNS-Profil während Planung geändert: {profile['name']}"
                )
            if changes:
                command = ["sudo", "-n", "nmcli", "con", "mod", "uuid", profile["uuid"]]
                for key, value in changes.items():
                    command.extend([key, value])
                rc, out = self.run_cmd(command, timeout=12)
                if rc:
                    return False, details + [
                        f"✖ DNS-Änderung fehlgeschlagen: {out}; mögliche Teiländerungen prüfen"
                    ]
                # Retain our own successful modify before the fallible readback.
                # Retrying still requires matching UUID, interface and settings.
                self._nm_activation_pending[profile["uuid"]] = (
                    profile["iface"],
                    dict(desired),
                )
                updated = self.read_nm_dns_profiles(
                    [(profile["iface"], profile["name"])]
                )[0]
                if (
                    updated["uuid"] != profile["uuid"]
                    or updated["properties"] != desired
                ):
                    return False, details + [
                        "✖ DNS-Profil nach Änderung nicht bestätigt; keine Aktivierung"
                    ]
                # A failed activation may be explicitly retried without rewriting
                # the profile; an initially correct profile never gets this flag.
                self._nm_activation_pending[profile["uuid"]] = (
                    profile["iface"],
                    desired,
                )
            rc, out = self.run_cmd(
                ["sudo", "-n", "nmcli", "con", "up", "uuid", profile["uuid"]],
                timeout=12,
            )
            if rc:
                return False, details + [
                    f"✖ Aktivierung fehlgeschlagen: {out}; Teiländerungen können bestehen bleiben"
                ]
            self._nm_activation_pending.pop(profile["uuid"], None)
            details.append(
                f"✔ DNS-Eigenschaften geändert und Verbindung aktiviert: {profile['name']} ({profile['iface']})"
            )
        return True, details

    def apply_nm_dns_policy_to_targets(
        self, *, ignore_auto_dns: bool, targets: list[tuple[str, str]]
    ) -> tuple[bool, list[str]]:
        if ignore_auto_dns is not True:
            return False, [self.AUTO_DNS_RELEASE_BLOCK_REASON]
        if not targets:
            return False, ["Keine aktive physische LAN/WLAN-Connection gefunden."]
        with self.dns_mutation_lock:
            try:
                return self._apply_nm_dns_profiles(
                    self.read_nm_dns_profiles(targets), ignore_auto_dns
                )
            except ValueError as exc:
                return False, [str(exc)]

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

    @staticmethod
    def _snapshot_key(snapshot: dict) -> tuple:
        def section_key(section):
            return (
                section.get("iface", ""),
                tuple(section["dns_servers"]),
                tuple(section["domains"]),
                section["default_route"],
                section.get("dns_scope"),
                section.get("is_vpn"),
            )

        return (
            snapshot["vpn_state"],
            section_key(snapshot["global"]),
            tuple(sorted((section_key(x) for x in snapshot["links"]), key=repr)),
            snapshot.get("dot_dropin_content", ""),
            tuple(snapshot.get("parse_errors", ())),
        )

    def _repair_key(self, snapshot: dict, profiles: list[dict]) -> tuple:
        return (
            self._snapshot_key(snapshot),
            tuple(
                sorted(
                    (p["iface"], p["uuid"], tuple(sorted(p["properties"].items())))
                    for p in profiles
                )
            ),
            self._resolved_reload_pending,
        )

    def non_vpn_guard_repair_key(self, snapshot, allowed, targets):
        return (
            self._repair_key(
                snapshot, self.read_nm_dns_profiles(targets) if targets else []
            ),
            tuple(allowed),
        )

    def _vpn_plan_current(self, before, current, expected_dropin, *, planned_ifaces=()):
        planned_ifaces = set(planned_ifaces)

        def vpn_links(snapshot):
            return sorted(
                (
                    x["iface"],
                    tuple(x["dns_servers"]),
                    tuple(x["domains"]),
                    x["default_route"],
                    x.get("dns_scope"),
                )
                for x in snapshot["links"]
                if x["is_vpn"]
            )

        return (
            current["vpn_state"] == "active"
            and not self.evaluate_dns_snapshot(current)["policy_unknown"]
            and vpn_links(current) == vpn_links(before)
            and self._resolver_routing_key(before, planned_ifaces=planned_ifaces)
            == self._resolver_routing_key(current, planned_ifaces=planned_ifaces)
            and all(
                not section.get("dns_servers")
                for section in current.get("links", ())
                if section.get("iface") in planned_ifaces and not section.get("is_vpn")
            )
            and current.get("dot_dropin_content", "") == expected_dropin
        )

    @staticmethod
    def _resolver_routing_key(snapshot, *, planned_ifaces=()):
        """Return every parsed resolver input that can change DNS routing."""
        planned_ifaces = set(planned_ifaces)

        def section_key(section):
            return (
                section.get("iface", ""),
                tuple(section.get("dns_servers", ())),
                tuple(section.get("domains", ())),
                section.get("default_route"),
                section.get("dns_scope"),
                section.get("is_vpn"),
            )

        return (
            snapshot.get("vpn_state"),
            bool(snapshot.get("status_ok")),
            tuple(snapshot.get("parse_errors", ())),
            section_key(snapshot.get("global", {})),
            tuple(
                sorted(
                    (
                        (
                            (
                                section.get("iface", ""),
                                (),
                                (),
                                None,
                                None,
                                section.get("is_vpn"),
                            )
                            if section.get("iface") in planned_ifaces
                            and not section.get("is_vpn")
                            else section_key(section)
                        )
                        for section in snapshot.get("links", ())
                    ),
                    key=repr,
                )
            ),
        )

    def clear_vpn_repair_backoff(self) -> None:
        self._unresolved_vpn_state = None

    def apply_vpn_dns_policy(
        self,
        *,
        targets: list[tuple[str, str]],
        automatic: bool = False,
        snapshot: dict | None = None,
    ) -> tuple[bool, str]:
        if not self._vpn_repair_lock.acquire(blocking=False):
            return (
                False,
                "DNS Control: Reparatur läuft bereits; keine weitere Änderung.",
            )
        if not self.dns_mutation_lock.acquire(blocking=False):
            self._vpn_repair_lock.release()
            return (
                False,
                "DNS Control: DNS-Änderung läuft bereits; keine weitere Änderung.",
            )
        lines = [
            "=== DNS Control ===",
            "Aktion: VPN-DNS erzwingen",
            "Auslöser: "
            + ("automatische Prüfung" if automatic else "ausdrückliche Benutzeraktion"),
        ]
        selected = []
        before = snapshot
        try:
            before = before or self.read_dns_snapshot()
            policy = self.evaluate_dns_snapshot(before)
            if before["vpn_state"] != "active" or policy["policy_unknown"]:
                return False, "\n".join(
                    lines
                    + ["VPN-/DNS-Status unklar oder VPN nicht aktiv; keine Änderung."]
                )
            if automatic and not policy["conflict"]:
                self.clear_vpn_repair_backoff()
                return True, "\n".join(lines + ["DNS-Policy korrekt; keine Änderung."])
            unsafe_split_routes = sorted(
                set(policy["repair_ifaces"]) & set(policy["split_ifaces"])
            )
            if automatic and unsafe_split_routes:
                unresolved_key = self._repair_key(before, [])
                if unresolved_key == self._unresolved_vpn_state:
                    return False, "\n".join(
                        lines
                        + [
                            "Unveränderter Split-DNS-/DefaultRoute-Konflikt; "
                            "sicherer Eingriff fehlt, Wiederholung unterdrückt."
                        ]
                    )
                self._unresolved_vpn_state = unresolved_key
                return False, "\n".join(
                    lines
                    + [
                        "Parallele Default-DNS-Route auf Split-DNS-Interface erkannt ("
                        + ", ".join(unsafe_split_routes)
                        + "); sicherer gezielter NM-Eingriff nicht möglich. "
                        "Konflikt bleibt ausdrücklich ungeklärt; Split-DNS bleibt erhalten."
                    ]
                )
            selected = [
                (iface, name)
                for iface, name in targets
                if iface not in policy["split_ifaces"]
                and (not automatic or iface in policy["repair_ifaces"])
            ]
            profiles = self.read_nm_dns_profiles(selected) if selected else []
            key = self._repair_key(before, profiles)
            if automatic and key == self._unresolved_vpn_state:
                return False, "\n".join(
                    lines
                    + [
                        "Unveränderte ungeklärte DNS-Abweichung; wirkungslose Wiederholung unterdrückt."
                    ]
                )
            # No mutation may use a resolver state superseded while reading NM.
            fresh = self.read_dns_snapshot()
            if self._snapshot_key(fresh) != self._snapshot_key(before):
                return False, "\n".join(
                    lines
                    + ["DNS-/VPN-Zustand während Planung geändert; keine Änderung."]
                )
            ok, details = self._apply_nm_dns_profiles(profiles, True)
            lines.extend(details)
            if not ok:
                raise ValueError(
                    "DNS-Profiländerung unvollständig; keine weiteren Änderungen."
                )
            current = self.read_dns_snapshot()
            if not self._vpn_plan_current(
                before,
                current,
                before.get("dot_dropin_content", ""),
                planned_ifaces={iface for iface, _name in selected},
            ):
                raise ValueError(
                    "DNS-/VPN-Zustand nach Aktivierung geändert; Reparaturplan gestoppt"
                )
            remove = bool(before.get("dot_dropin_content")) and (
                not automatic or policy["dot_dropin_conflict"]
            )
            if remove:
                ok, detail = self.remove_dropin()
                if not ok or os.path.lexists(self.dot_dropin_path):
                    raise ValueError(
                        f"DoT-Datei nicht entfernt: {detail}; kein Neustart."
                    )
                self._resolved_reload_pending = True
                lines.append("✔ NetMon DoT-Konfiguration entfernt")
            if self._resolved_reload_pending:
                current = self.read_dns_snapshot()
                expected_dropin = "" if remove else before.get("dot_dropin_content", "")
                if not self._vpn_plan_current(
                    before,
                    current,
                    expected_dropin,
                    planned_ifaces={iface for iface, _name in selected},
                ):
                    raise ValueError(
                        "DNS-/VPN-Zustand vor Resolver-Neustart geändert; Plan gestoppt"
                    )
                ok, detail = self.restart_resolved()
                if not ok:
                    raise ValueError(f"Resolver-Neustart fehlgeschlagen: {detail}")
                self._resolved_reload_pending = False
                lines.append(
                    "✔ systemd-resolved nach Konfigurationsänderung neu gestartet"
                )
            after = self.read_dns_snapshot()
            verified = self.evaluate_dns_snapshot(after)
            success = (
                after["vpn_state"] == "active"
                and not verified["policy_unknown"]
                and not verified["conflict"]
            )
            if success:
                self.clear_vpn_repair_backoff()
                lines.append(
                    "✔ DNS-Policy nachgeprüft; korrekt (keine unnötige erneute Aktivierung)"
                )
            else:
                self._unresolved_vpn_state = self._repair_key(
                    after, self.read_nm_dns_profiles(selected) if selected else []
                )
                lines.append(
                    "✖ DNS-Policy weiterhin ungeklärt/abweichend; Befehlsannahme ist kein Reparaturnachweis."
                )
            return success, "\n".join(lines)
        except ValueError as exc:
            lines.append(
                f"{exc}; mögliche Teiländerungen bleiben sichtbar, keine weiteren Änderungen."
            )
            # Capture partial progress so an unchanged failure is not replayed.
            try:
                after = self.read_dns_snapshot()
                self._unresolved_vpn_state = self._repair_key(
                    after, self.read_nm_dns_profiles(selected) if selected else []
                )
            except ValueError:
                self._unresolved_vpn_state = None
            return False, "\n".join(lines)
        finally:
            self.dns_mutation_lock.release()
            self._vpn_repair_lock.release()


__all__ = ["DNSControlService"]
