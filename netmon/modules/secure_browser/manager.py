"""UI-facing manager placeholder for the NetMon Secure Browser module."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import secrets
from urllib.parse import urlparse

from .models import BrowserContainer

from .service import SecureBrowserService

LOGGER = logging.getLogger(__name__)

COMMON_THIRD_LEVEL_SUFFIXES = {
    "co.uk",
    "org.uk",
    "gov.uk",
    "ac.uk",
    "co.jp",
    "com.au",
    "net.au",
    "org.au",
}

LOGIN_SUBDOMAIN_PREFIXES = {
    "account",
    "accounts",
    "auth",
    "id",
    "login",
    "secure",
    "signin",
    "sso",
}


class SecureBrowserManager:
    """Thin coordinator between the Secure Browser UI and service layer."""

    STATUS_FILTER_ALL = "Alle"
    RISK_FILTER_ALL = "Alle"
    RISK_FILTER_ONLY_RISKS = "Nur Risiken"
    RISK_FILTER_ONLY_EXTERNAL = "Nur externe Profile"
    CREATE_DEFAULT_NAME = "firefox-Neu"
    CREATE_DEFAULT_NEW_TAB = "about:blank"
    CREATE_DEFAULT_ICON_MODE = "favicon"
    CREATE_DEFAULT_SECURITY_PROFILE = "Standard"
    SECURITY_PROFILE_COMPATIBLE = "Kompatibel"
    SECURITY_PROFILE_STANDARD = "Standard"
    SECURITY_PROFILE_STRICT = "Streng"
    SECURITY_PROFILE_CUSTOM = "Benutzerdefiniert"
    APPLY_CONFIRM_TOKEN = "APPLY"
    REGISTER_CONFIRM_TOKEN = "REGISTER"
    REFRESH_CONFIRM_TOKEN = "REFRESH"
    REPAIR_POLICY_CONFIRM_TOKEN = "REPAIR"
    CLEANUP_CONFIRM_TOKEN = "CLEANUP"
    UNINSTALL_CONFIRM_TOKEN = "UNINSTALL"
    VIEW_OVERVIEW = "Übersicht"
    VIEW_LAUNCHER = "Launcher"
    VIEW_ARTIFACTS = "Artefakte"
    POLICY_EDIT_CONFIRM_TOKEN = "SAVE"
    WEBSITE_FILTER_BLOCK_PATTERN = "<all_urls>"
    CONTAINER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
    CREATE_DOMAIN_BUNDLES = {
        "github.com": {
            "domains": [
                "github.com",
                "githubusercontent.com",
                "githubassets.com",
            ],
            "slug": "github",
            "display_name": "GitHub",
        },
        "chatgpt.com": {
            "domains": [
                "chatgpt.com",
                "openai.com",
                "platform.openai.com",
                "auth.openai.com",
                "oaistatic.com",
                "oaiusercontent.com",
            ],
            "slug": "openai",
            "display_name": "OpenAI",
        },
        "openai.com": {
            "domains": [
                "chatgpt.com",
                "openai.com",
                "platform.openai.com",
                "auth.openai.com",
                "oaistatic.com",
                "oaiusercontent.com",
            ],
            "slug": "openai",
            "display_name": "OpenAI",
        },
        "name.com": {
            "domains": [
                "name.com",
                "www.name.com",
            ],
            "slug": "namecom",
            "display_name": "Name.com",
        },
        "cpanel.netmonroots.com": {
            "domains": [
                "netmonroots.com",
                "cpanel.netmonroots.com",
                "netmonroots.com:2083",
            ],
            "slug": "cpanel",
            "display_name": "cPanel",
        },
        "netmonroots.com": {
            "domains": [
                "netmonroots.com",
                "cpanel.netmonroots.com",
                "netmonroots.com:2083",
            ],
            "slug": "cpanel",
            "display_name": "cPanel",
        },
        "amazon.de": {
            "domains": [
                "amazon.de",
                "amazon.com",
                "media-amazon.com",
                "ssl-images-amazon.com",
            ],
            "slug": "amazon",
            "display_name": "Amazon",
        },
        "amazon.com": {
            "domains": [
                "amazon.de",
                "amazon.com",
                "media-amazon.com",
                "ssl-images-amazon.com",
            ],
            "slug": "amazon",
            "display_name": "Amazon",
        },
        "netflix.com": {
            "domains": [
                "netflix.com",
                "nflxvideo.net",
                "nflximg.net",
            ],
            "slug": "netflix",
            "display_name": "Netflix",
        },
    }

    def __init__(self, service: SecureBrowserService | None = None, tr=None) -> None:
        self.service = service or SecureBrowserService()
        self.last_scan: list[BrowserContainer] = []
        self._tr = tr

    def T(self, key: str, default: str) -> str:
        if callable(self._tr):
            try:
                return str(self._tr(key, default))
            except Exception:
                return default
        return default

    def todo_action(self, action: str) -> None:
        LOGGER.info("Secure Browser manager TODO action requested: %s", action)

    def scan_inventory(self) -> list[BrowserContainer]:
        self.last_scan = self.service.scan_containers()
        return self.last_scan

    @staticmethod
    def create_child_lock_payload(password: str) -> dict[str, object]:
        if not isinstance(password, str) or not password:
            raise ValueError("Für die Kindersicherung wurde kein Passwort eingegeben.")
        salt = secrets.token_bytes(16)
        iterations = 200_000
        password_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return {
            "algorithm": "pbkdf2_sha256",
            "salt": salt.hex(),
            "password_hash": password_hash.hex(),
            "iterations": iterations,
        }

    @staticmethod
    def is_protected_firefox_base_name(container_name: str | None) -> bool:
        normalized = re.sub(
            r"[-_.\s]+", "", str(container_name or "").strip().lower()
        )
        return normalized == "firefoxbase"

    def render_preflight_text(self) -> str:
        try:
            lines = self.service.run_preflight_checks()
        except Exception as exc:
            LOGGER.exception("Secure Browser preflight failed")
            return "\n".join(
                [
                    self.T(
                        "secure_browser_preflight_title", "Secure-Browser-Preflight"
                    ),
                    "",
                    f"- {self.T('secure_browser_preflight_status_label', 'Status')}: {self.T('secure_browser_preflight_status_error', 'Fehler')} ({exc})",
                    f"- {self.T('secure_browser_preflight_effect_label', 'Wirkung')}: {self.T('secure_browser_preflight_effect_no_changes', 'keine Änderungen ausgeführt')}",
                ]
            )
        return "\n".join(
            [
                self.T("secure_browser_preflight_title", "Secure-Browser-Preflight"),
                "",
                f"- {self.T('secure_browser_preflight_mode_label', 'Modus')}: {self.T('secure_browser_preflight_mode_read_only', 'read-only')}",
                f"- {self.T('secure_browser_preflight_dependencies_label', 'Abhängigkeiten')}: {self.T('secure_browser_preflight_dependencies_none', 'bei fehlender Firefox-Laufzeit oder Firefox-Basis den Setup-Assistenten verwenden')}",
                *lines,
            ]
        )

    @staticmethod
    def _format_profile_path(container: BrowserContainer) -> str:
        profile_raw = str(container.profile_path)
        return profile_raw if profile_raw and profile_raw != "." else "nicht erkannt"

    @staticmethod
    def _format_menu_entry(container: BrowserContainer) -> str:
        return (
            str(container.menu_entry_path)
            if container.menu_entry_path is not None
            else "kein Menüeintrag"
        )

    @staticmethod
    def _render_menu_entries_section(launcher_info: dict[str, object]) -> list[str]:
        raw_entries = launcher_info.get("menu_entries")
        if not isinstance(raw_entries, list) or not raw_entries:
            fallback = launcher_info.get("menu_entry", {})
            if not isinstance(fallback, dict):
                fallback = {}
            return [
                "[Gefundene Menüeinträge]",
                "- Keine zusätzlichen Menüeinträge erkannt",
                "",
                "[Menüeintrag strukturiert]",
                *[f"- {key}: {value}" for key, value in fallback.items()],
            ]
        lines = ["[Gefundene Menüeinträge]"]
        for index, entry in enumerate(raw_entries, start=1):
            if not isinstance(entry, dict):
                continue
            lines.extend(
                [
                    f"- Eintrag {index}",
                    f"  Datei: {entry.get('Datei', 'nicht gesetzt')}",
                    f"  Pfad: {entry.get('Pfad', 'nicht gesetzt')}",
                    f"  Name: {entry.get('Name', 'nicht gesetzt')}",
                    f"  Exec: {entry.get('Exec', 'nicht gesetzt')}",
                    f"  Icon: {entry.get('Icon', 'nicht gesetzt')}",
                    f"  Status: {entry.get('Status', 'nicht gesetzt')}",
                ]
            )
        fallback = launcher_info.get("menu_entry", {})
        if isinstance(fallback, dict):
            lines.extend(
                [
                    "",
                    "[Aktiver Menüeintrag strukturiert]",
                    *[f"- {key}: {value}" for key, value in fallback.items()],
                ]
            )
        return lines

    def get_status_filter_options(self) -> list[str]:
        statuses = sorted(
            {container.status for container in self.last_scan if container.status}
        )
        return [self.STATUS_FILTER_ALL, *statuses]

    def get_risk_filter_options(self) -> list[str]:
        return [
            self.RISK_FILTER_ALL,
            self.RISK_FILTER_ONLY_RISKS,
            self.RISK_FILTER_ONLY_EXTERNAL,
        ]

    def get_create_preset_names(self) -> list[str]:
        presets = self.service.list_create_presets()
        return [str(item["name"]) for item in presets if item.get("name")]

    def get_create_preset(self, preset_name: str) -> dict[str, object] | None:
        for item in self.service.list_create_presets():
            if item.get("name") == preset_name:
                return item
        return None

    @staticmethod
    def derive_menu_name(container_name: str) -> str:
        suffix = container_name.removeprefix("firefox-").replace("-", " ").strip()
        return suffix or "Browser"

    @staticmethod
    def normalize_website_url(website_url: str) -> str:
        raw = (website_url or "").strip()
        if not raw:
            return "https://example.com"
        if "://" not in raw:
            raw = f"https://{raw}"
        return raw

    @classmethod
    def normalize_allowed_domain(cls, value: str) -> str | None:
        raw = (value or "").strip()
        if not raw:
            return None
        candidate = raw if "://" in raw else f"https://{raw}"
        parsed = urlparse(candidate)
        host = parsed.hostname.lower() if parsed.hostname else ""
        if not host:
            return None
        if parsed.port is not None:
            return f"{host}:{parsed.port}"
        return host

    @classmethod
    def normalize_allowed_domains(cls, values: list[str]) -> list[str]:
        normalized: list[str] = []
        for value in values:
            cleaned = cls.normalize_allowed_domain(value)
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized

    @classmethod
    def _derive_known_bundle(cls, host_without_port: str) -> dict[str, object] | None:
        host = host_without_port.lower()
        candidates = [host, host.removeprefix("www.")]
        host_parts = [part for part in host.removeprefix("www.").split(".") if part]
        if len(host_parts) > 2 and host_parts[0] in LOGIN_SUBDOMAIN_PREFIXES:
            candidates.append(".".join(host_parts[1:]))
        for candidate in candidates:
            if candidate in cls.CREATE_DOMAIN_BUNDLES:
                return dict(cls.CREATE_DOMAIN_BUNDLES[candidate])
        return None

    @staticmethod
    def _guess_domain_scope(host_without_port: str) -> list[str]:
        host = host_without_port.lower().removeprefix("www.")
        parts = [part for part in host.split(".") if part]
        if len(parts) < 2:
            return [host] if host else []
        candidate_root = ".".join(parts[-2:])
        if len(parts) >= 3:
            candidate_suffix = ".".join(parts[-2:])
            if candidate_suffix in COMMON_THIRD_LEVEL_SUFFIXES and len(parts) >= 3:
                candidate_root = ".".join(parts[-3:])
        domains = [host]
        if candidate_root not in domains:
            domains.append(candidate_root)
        if host_without_port.startswith("www.") and host_without_port not in domains:
            domains.insert(0, host_without_port.lower())
        return domains

    @classmethod
    def derive_create_defaults(cls, website_url: str) -> dict[str, object]:
        normalized_url = cls.normalize_website_url(website_url)
        parsed = urlparse(normalized_url)
        host = parsed.netloc.lower()
        host_without_port = host.split(":", 1)[0]
        explicit_port = parsed.port
        host_base = host_without_port.removeprefix("www.")
        known_bundle = cls._derive_known_bundle(host_without_port)
        if known_bundle and known_bundle.get("homepage_url"):
            normalized_url = str(known_bundle["homepage_url"])
        slug = (
            str(known_bundle["slug"])
            if known_bundle and known_bundle.get("slug")
            else re.sub(r"[^a-z0-9]+", "-", host_base).strip("-") or "neu"
        )
        container_name = f"firefox-{slug}"
        allowed_domains = (
            list(known_bundle["domains"])
            if known_bundle and isinstance(known_bundle.get("domains"), list)
            else None
        )
        if not allowed_domains:
            allowed_domains = (
                cls._guess_domain_scope(host_without_port)
                if host_without_port
                else ["example.com"]
            )
        if explicit_port and host_without_port:
            with_port = f"{host_without_port}:{explicit_port}"
            if with_port not in allowed_domains:
                allowed_domains.insert(0, with_port)
        display_name = (
            str(known_bundle["display_name"])
            if known_bundle and known_bundle.get("display_name")
            else " ".join(part.capitalize() for part in slug.split("-") if part)
            or "Browser"
        )
        return {
            "homepage_url": normalized_url,
            "container_name": container_name,
            "allowed_domains": allowed_domains,
            "menu_name": display_name,
            "security_profile": cls.CREATE_DEFAULT_SECURITY_PROFILE,
            "allow_password_manager": True,
            "keep_cookies": True,
            "enable_website_filter": True,
        }

    @classmethod
    def get_security_profile_options(cls) -> list[str]:
        return [
            cls.SECURITY_PROFILE_COMPATIBLE,
            cls.SECURITY_PROFILE_STANDARD,
            cls.SECURITY_PROFILE_STRICT,
            cls.SECURITY_PROFILE_CUSTOM,
        ]

    @classmethod
    def resolve_security_options(
        cls,
        security_profile: str,
        *,
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
    ) -> dict[str, object]:
        normalized = (security_profile or cls.CREATE_DEFAULT_SECURITY_PROFILE).strip()
        defaults = {
            cls.SECURITY_PROFILE_COMPATIBLE: {
                "allow_password_manager": True,
                "keep_cookies": True,
                "enable_website_filter": False,
            },
            cls.SECURITY_PROFILE_STANDARD: {
                "allow_password_manager": True,
                "keep_cookies": True,
                "enable_website_filter": True,
            },
            cls.SECURITY_PROFILE_STRICT: {
                "allow_password_manager": False,
                "keep_cookies": False,
                "enable_website_filter": True,
            },
            cls.SECURITY_PROFILE_CUSTOM: {
                "allow_password_manager": True,
                "keep_cookies": True,
                "enable_website_filter": True,
            },
        }
        if normalized not in defaults:
            normalized = cls.CREATE_DEFAULT_SECURITY_PROFILE
        resolved = dict(defaults[normalized])
        if allow_password_manager is not None:
            resolved["allow_password_manager"] = allow_password_manager
        if keep_cookies is not None:
            resolved["keep_cookies"] = keep_cookies
        if enable_website_filter is not None:
            resolved["enable_website_filter"] = enable_website_filter
        if normalized != cls.SECURITY_PROFILE_CUSTOM:
            if resolved != defaults[normalized]:
                normalized = cls.SECURITY_PROFILE_CUSTOM
        resolved["security_profile"] = normalized
        return resolved

    def _resolve_create_inputs(
        self,
        name: str,
        website_url: str,
        allowed_domains_raw: str,
        menu_name: str,
        new_tab_url: str,
        icon_mode: str,
        security_profile: str = "",
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
    ) -> dict[str, object]:
        defaults = self.derive_create_defaults(website_url)
        normalized_name = (name or "").strip() or str(defaults["container_name"])
        if not self.CONTAINER_NAME_PATTERN.fullmatch(normalized_name):
            raise ValueError(
                "Ungültiger Containername. Erlaubt sind nur A-Z, a-z, 0-9, Punkt, Unterstrich und Bindestrich."
            )
        if normalized_name in {".", ".."}:
            raise ValueError(
                "Ungültiger Containername. '.' oder '..' sind nicht erlaubt."
            )
        explicit_name = bool((name or "").strip())
        homepage = str(defaults["homepage_url"])
        normalized_menu_name = (menu_name or "").strip() or self.derive_menu_name(
            normalized_name
        )
        if not menu_name.strip() and not explicit_name:
            normalized_menu_name = str(defaults["menu_name"])
        normalized_new_tab_url = (
            new_tab_url or ""
        ).strip() or self.CREATE_DEFAULT_NEW_TAB
        normalized_icon_mode = (
            icon_mode or ""
        ).strip() or self.CREATE_DEFAULT_ICON_MODE
        security = self.resolve_security_options(
            (security_profile or "").strip() or str(defaults["security_profile"]),
            allow_password_manager=allow_password_manager,
            keep_cookies=keep_cookies,
            enable_website_filter=enable_website_filter,
        )
        allowed_domains = [
            item.strip() for item in allowed_domains_raw.split(",") if item.strip()
        ]
        if not allowed_domains:
            allowed_domains = list(defaults["allowed_domains"])
        allowed_domains = self.normalize_allowed_domains(allowed_domains)
        if not allowed_domains:
            allowed_domains = self.normalize_allowed_domains(
                list(defaults["allowed_domains"])
            )
        return {
            "name": normalized_name,
            "homepage": homepage,
            "menu_name": normalized_menu_name,
            "new_tab_url": normalized_new_tab_url,
            "icon_mode": normalized_icon_mode,
            "allowed_domains": allowed_domains,
            "security_profile": str(security["security_profile"]),
            "allow_password_manager": bool(security["allow_password_manager"]),
            "keep_cookies": bool(security["keep_cookies"]),
            "enable_website_filter": bool(security["enable_website_filter"]),
        }

    def _matches_risk_filter(
        self,
        container: BrowserContainer,
        risk_filter: str | None = None,
    ) -> bool:
        if not risk_filter or risk_filter == self.RISK_FILTER_ALL:
            return True
        try:
            risks = self.service.derive_risk_hints(container)
        except Exception:
            return False
        meaningful_risks = [
            risk for risk in risks if risk != "Keine offensichtlichen Risiken erkannt"
        ]
        if risk_filter == self.RISK_FILTER_ONLY_RISKS:
            return bool(meaningful_risks)
        if risk_filter == self.RISK_FILTER_ONLY_EXTERNAL:
            return any("Externes Mozilla-Profil" in risk for risk in risks)
        return True

    def get_filtered_containers(
        self,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> list[BrowserContainer]:
        if not status_filter or status_filter == self.STATUS_FILTER_ALL:
            filtered = list(self.last_scan)
        else:
            filtered = [
                container
                for container in self.last_scan
                if container.status == status_filter
            ]
        filtered = [
            container
            for container in filtered
            if self._matches_risk_filter(container, risk_filter)
        ]
        query = (search_query or "").strip().lower()
        if not query:
            return filtered
        return [
            container
            for container in filtered
            if query in container.name.lower()
            or any(query in domain.lower() for domain in container.allowed_domains)
        ]

    def get_container_names(
        self,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> list[str]:
        return [
            container.name
            for container in self.get_filtered_containers(
                status_filter,
                search_query,
                risk_filter,
            )
        ]

    def get_container_by_name(
        self,
        name: str,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> BrowserContainer | None:
        for container in self.get_filtered_containers(
            status_filter,
            search_query,
            risk_filter,
        ):
            if container.name == name:
                return container
        return None

    def render_inventory_summary(
        self,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        total_count = len(self.last_scan)
        count = len(
            self.get_filtered_containers(
                status_filter,
                search_query,
                risk_filter,
            )
        )
        if count == 0:
            return self.T(
                "secure_browser_inventory_none",
                "Keine Secure-Browser-Container erkannt.",
            )
        if (
            search_query
            and status_filter
            and status_filter != self.STATUS_FILTER_ALL
            and risk_filter
            and risk_filter != self.RISK_FILTER_ALL
        ):
            return self.T(
                "secure_browser_inventory_summary_status_risk_search",
                "{count} von {total} Secure-Browser-Containern mit Status {status}, Filter {risk} passend zu '{query}' erkannt.",
            ).format(
                count=count,
                total=total_count,
                status=status_filter,
                risk=risk_filter,
                query=search_query,
            )
        if search_query and risk_filter and risk_filter != self.RISK_FILTER_ALL:
            return self.T(
                "secure_browser_inventory_summary_risk_search",
                "{count} von {total} Secure-Browser-Containern mit Filter {risk} passend zu '{query}' erkannt.",
            ).format(
                count=count, total=total_count, risk=risk_filter, query=search_query
            )
        if risk_filter and risk_filter != self.RISK_FILTER_ALL:
            return self.T(
                "secure_browser_inventory_summary_risk",
                "{count} von {total} Secure-Browser-Containern mit Filter {risk} erkannt.",
            ).format(count=count, total=total_count, risk=risk_filter)
        if search_query and status_filter and status_filter != self.STATUS_FILTER_ALL:
            return self.T(
                "secure_browser_inventory_summary_status_search",
                "{count} von {total} Secure-Browser-Containern mit Status {status} passend zu '{query}' erkannt.",
            ).format(
                count=count, total=total_count, status=status_filter, query=search_query
            )
        if search_query:
            return self.T(
                "secure_browser_inventory_summary_search",
                "{count} von {total} Secure-Browser-Containern passend zu '{query}' erkannt.",
            ).format(count=count, total=total_count, query=search_query)
        if status_filter and status_filter != self.STATUS_FILTER_ALL:
            return self.T(
                "secure_browser_inventory_summary_status",
                "{count} von {total} Secure-Browser-Containern mit Status {status} erkannt.",
            ).format(count=count, total=total_count, status=status_filter)
        return self.T(
            "secure_browser_inventory_summary_default",
            "{count} Secure-Browser-Container erkannt.",
        ).format(count=count)

    def render_inventory_metrics(self) -> str:
        if not self.last_scan:
            return self.T("secure_browser_inventory_metrics_none", "Kennzahlen: keine")
        counts: dict[str, int] = {}
        external_profiles = 0
        missing_launchers = 0
        missing_menu_entries = 0
        for container in self.last_scan:
            label = container.status or "unbekannt"
            counts[label] = counts.get(label, 0) + 1
            try:
                risks = self.service.derive_risk_hints(container)
            except Exception:
                risks = []
            if any("Externes Mozilla-Profil" in risk for risk in risks):
                external_profiles += 1
            if any("launcher.desktop fehlt" in risk for risk in risks):
                missing_launchers += 1
            if any("Menüeintrag fehlt" in risk for risk in risks):
                missing_menu_entries += 1
        parts = [f"Gesamt: {len(self.last_scan)}"]
        parts.extend(f"{status}: {counts[status]}" for status in sorted(counts))
        parts.extend(
            [
                f"externe Profile: {external_profiles}",
                f"fehlende Launcher: {missing_launchers}",
                f"fehlende Menüeinträge: {missing_menu_entries}",
            ]
        )
        return self.T(
            "secure_browser_inventory_metrics_prefix", "Kennzahlen: "
        ) + " | ".join(parts)

    @staticmethod
    def _render_hardening_summary_lines(
        security_profile: str,
        allow_password_manager: bool,
        keep_cookies: bool,
        enable_website_filter: bool,
    ) -> list[str]:
        compatibility_risk = "mittel"
        if not enable_website_filter:
            compatibility_risk = "niedrig"
        elif not keep_cookies or not allow_password_manager:
            compatibility_risk = "hoch"
        return [
            "Hardening-Zusammenfassung",
            f"- Sicherheitsprofil: {security_profile}",
            f"- Passwortspeicher: {'erlaubt' if allow_password_manager else 'deaktiviert'}",
            f"- Cookies: {'bleiben erhalten' if keep_cookies else 'werden beim Beenden gelöscht'}",
            f"- Website-Filter: {'aktiv' if enable_website_filter else 'deaktiviert'}",
            f"- Kompatibilitätsrisiko: {compatibility_risk}",
        ]

    def render_create_browser_draft(
        self,
        name: str,
        homepage_url: str,
        allowed_domains_raw: str,
        menu_name: str = "",
        new_tab_url: str = "",
        icon_mode: str = "",
        security_profile: str = "",
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
    ) -> str:
        base_dir = self.service.get_default_base_dir()
        resolved = self._resolve_create_inputs(
            name,
            homepage_url,
            allowed_domains_raw,
            menu_name,
            new_tab_url,
            icon_mode,
            security_profile,
            allow_password_manager,
            keep_cookies,
            enable_website_filter,
        )
        normalized_name = str(resolved["name"])
        homepage = str(resolved["homepage"])
        normalized_menu_name = str(resolved["menu_name"])
        normalized_new_tab_url = str(resolved["new_tab_url"])
        normalized_icon_mode = str(resolved["icon_mode"])
        allowed_domains = list(resolved["allowed_domains"])
        normalized_security_profile = str(resolved["security_profile"])
        resolved_allow_password_manager = bool(resolved["allow_password_manager"])
        resolved_keep_cookies = bool(resolved["keep_cookies"])
        resolved_enable_website_filter = bool(resolved["enable_website_filter"])
        target_dir = base_dir / normalized_name
        warnings: list[str] = []
        if not normalized_name.startswith("firefox-"):
            warnings.append("Containername sollte mit 'firefox-' beginnen")
        parsed_homepage = urlparse(homepage)
        if (
            parsed_homepage.scheme not in {"http", "https"}
            or not parsed_homepage.netloc
        ):
            warnings.append("Startseite ist keine gültige http(s)-URL")
        if normalized_new_tab_url != "about:blank":
            parsed_new_tab = urlparse(normalized_new_tab_url)
            if (
                parsed_new_tab.scheme not in {"http", "https"}
                or not parsed_new_tab.netloc
            ):
                warnings.append(
                    "Neue-Tab-URL ist weder about:blank noch gültiges http(s)"
                )
        for domain in allowed_domains:
            host = domain.split(":", 1)[0].strip()
            if "." not in host:
                warnings.append(f"Domain wirkt unvollständig: {domain}")
        if normalized_icon_mode not in {"favicon", "default", "custom"}:
            warnings.append(f"Icon-Modus ist unbekannt: {normalized_icon_mode}")
        if target_dir.exists():
            warnings.append(f"Zielordner existiert bereits: {target_dir}")
        preview = self.service.build_create_preview(
            normalized_name,
            homepage,
            allowed_domains,
            target_dir=target_dir,
            menu_name=normalized_menu_name,
            new_tab_url=normalized_new_tab_url,
            icon_mode=normalized_icon_mode,
            security_profile=normalized_security_profile,
            allow_password_manager=resolved_allow_password_manager,
            keep_cookies=resolved_keep_cookies,
            enable_website_filter=resolved_enable_website_filter,
        )
        status_line = (
            "Validierung: ohne Befund"
            if not warnings
            else f"Validierung: {len(warnings)} Hinweis(e)"
        )
        return "\n".join(
            [
                "Neuer Browser",
                "",
                "Dry-Run-Entwurf",
                f"- Zielbasis: {base_dir}",
                f"- Zielordner: {target_dir}",
                f"- Webseite: {homepage}",
                f"- Containername: {normalized_name}",
                f"- Startseite: {homepage}",
                f"- Neue Tabs: {normalized_new_tab_url}",
                f"- Menüname: {normalized_menu_name}",
                f"- Icon-Modus: {normalized_icon_mode}",
                f"- Erlaubte Domains: {', '.join(allowed_domains)}",
                "- Startmodus: ./firefox/firefox --no-remote --profile ./profile",
                "- Sicherheitsmodus: nur Entwurf, keine Dateien geschrieben",
                f"- {status_line}",
                "",
                *self._render_hardening_summary_lines(
                    normalized_security_profile,
                    resolved_allow_password_manager,
                    resolved_keep_cookies,
                    resolved_enable_website_filter,
                ),
                "",
                "Validierung",
                *(
                    [f"- {warning}" for warning in warnings]
                    if warnings
                    else ["- Keine Warnungen erkannt"]
                ),
                "",
                "Geplanter Inhalt",
                "- firefox/",
                "- profile/",
                "- start.sh",
                "- backup.sh",
                "- README.md",
                "- user.js",
                "- policies.json",
                "- launcher.desktop",
                "",
                "Builder-Vorschau",
                f"- Tool: {preview['tool_script']}",
                f"- Beispiel-Config: {preview['tool_config']}",
                (
                    f"- Firefox-Quelle: {preview['source_firefox_dir']}"
                    if preview.get("source_firefox_dir")
                    else "- Firefox-Quelle: nicht vorkonfiguriert"
                ),
                f"- Geplanter Aufruf: {preview['command']}",
                "- Ausführung: deaktiviert, aktuell nur NetMon-Vorschau",
                "",
                "Geplante Container-Definition",
                "```json",
                preview["payload"],
                "```",
            ]
        )

    def render_create_browser_builder_dry_run(
        self,
        name: str,
        homepage_url: str,
        allowed_domains_raw: str,
        menu_name: str = "",
        new_tab_url: str = "",
        icon_mode: str = "",
        security_profile: str = "",
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
    ) -> str:
        base_dir = self.service.get_default_base_dir()
        resolved = self._resolve_create_inputs(
            name,
            homepage_url,
            allowed_domains_raw,
            menu_name,
            new_tab_url,
            icon_mode,
            security_profile,
            allow_password_manager,
            keep_cookies,
            enable_website_filter,
        )
        normalized_name = str(resolved["name"])
        homepage = str(resolved["homepage"])
        normalized_menu_name = str(resolved["menu_name"])
        normalized_new_tab_url = str(resolved["new_tab_url"])
        normalized_icon_mode = str(resolved["icon_mode"])
        allowed_domains = list(resolved["allowed_domains"])
        normalized_security_profile = str(resolved["security_profile"])
        resolved_allow_password_manager = bool(resolved["allow_password_manager"])
        resolved_keep_cookies = bool(resolved["keep_cookies"])
        resolved_enable_website_filter = bool(resolved["enable_website_filter"])
        target_dir = base_dir / normalized_name
        lines = self.service.run_create_dry_run(
            name=normalized_name,
            homepage_url=homepage,
            allowed_domains=allowed_domains,
            target_dir=target_dir,
            menu_name=normalized_menu_name,
            new_tab_url=normalized_new_tab_url,
            icon_mode=normalized_icon_mode,
            security_profile=normalized_security_profile,
            allow_password_manager=resolved_allow_password_manager,
            keep_cookies=resolved_keep_cookies,
            enable_website_filter=resolved_enable_website_filter,
        )
        header = [
            "Neuer Browser",
            "",
            "Builder-Dry-Run",
            "- Ausführung: intern, read-only, ohne --apply",
            f"- Zielordner: {target_dir}",
            *self._render_hardening_summary_lines(
                normalized_security_profile,
                resolved_allow_password_manager,
                resolved_keep_cookies,
                resolved_enable_website_filter,
            ),
            "",
        ]
        return "\n".join([*header, *lines])

    def render_create_browser_apply_preview(
        self,
        name: str,
        homepage_url: str,
        allowed_domains_raw: str,
        menu_name: str = "",
        new_tab_url: str = "",
        icon_mode: str = "",
        security_profile: str = "",
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
        confirmation: str = "",
    ) -> str:
        base_dir = self.service.get_default_base_dir()
        resolved = self._resolve_create_inputs(
            name,
            homepage_url,
            allowed_domains_raw,
            menu_name,
            new_tab_url,
            icon_mode,
            security_profile,
            allow_password_manager,
            keep_cookies,
            enable_website_filter,
        )
        normalized_name = str(resolved["name"])
        homepage = str(resolved["homepage"])
        normalized_menu_name = str(resolved["menu_name"])
        normalized_new_tab_url = str(resolved["new_tab_url"])
        normalized_icon_mode = str(resolved["icon_mode"])
        allowed_domains = list(resolved["allowed_domains"])
        normalized_security_profile = str(resolved["security_profile"])
        resolved_allow_password_manager = bool(resolved["allow_password_manager"])
        resolved_keep_cookies = bool(resolved["keep_cookies"])
        resolved_enable_website_filter = bool(resolved["enable_website_filter"])
        target_dir = base_dir / normalized_name
        apply_preview = self.service.build_apply_preview(
            name=normalized_name,
            target_dir=target_dir,
        )
        confirmation_text = (confirmation or "").strip()
        lines = [
            "Neuer Browser",
            "",
            "Apply-Vorbereitung",
            "- Status: noch nicht ausgeführt",
            f"- Zielordner: {target_dir}",
            f"- Bestätigungscode erforderlich: {self.APPLY_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {confirmation_text or 'leer'}",
            "",
            *self._render_hardening_summary_lines(
                normalized_security_profile,
                resolved_allow_password_manager,
                resolved_keep_cookies,
                resolved_enable_website_filter,
            ),
            "",
            "Sicherheitsregeln",
            "- Kein automatischer Start von --apply in dieser Integrationsstufe",
            "- Erst Dry-Run prüfen, dann bewusste Freigabe erteilen",
            "- Bestehende Zielordner bleiben unberührt und führen zum Abbruch",
            f"- Hinweis: {apply_preview['safety']}",
            "",
            "Geplanter Apply-Aufruf",
            f"- {apply_preview['command']}",
        ]
        if confirmation_text != self.APPLY_CONFIRM_TOKEN:
            lines.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                    (
                        f"- Für die nächste Ausbaustufe muss exakt "
                        f"`{self.APPLY_CONFIRM_TOKEN}` eingegeben werden."
                    ),
                ]
            )
            return "\n".join(lines)
        dry_run_lines = self.service.run_create_dry_run(
            name=normalized_name,
            homepage_url=homepage,
            allowed_domains=allowed_domains,
            target_dir=target_dir,
            menu_name=normalized_menu_name,
            new_tab_url=normalized_new_tab_url,
            icon_mode=normalized_icon_mode,
            security_profile=normalized_security_profile,
            allow_password_manager=resolved_allow_password_manager,
            keep_cookies=resolved_keep_cookies,
            enable_website_filter=resolved_enable_website_filter,
        )
        lines.extend(
            [
                "",
                "Freigabe",
                "- Bestätigungscode akzeptiert.",
                "- Nächster Schritt wäre ein separater, expliziter Write-Pfad.",
                "",
                *dry_run_lines,
            ]
        )
        return "\n".join(lines)

    def execute_create_browser_apply(
        self,
        name: str,
        homepage_url: str,
        allowed_domains_raw: str,
        menu_name: str = "",
        new_tab_url: str = "",
        icon_mode: str = "",
        security_profile: str = "",
        allow_password_manager: bool | None = None,
        keep_cookies: bool | None = None,
        enable_website_filter: bool | None = None,
        confirmation: str = "",
        child_lock: dict[str, object] | None = None,
    ) -> str:
        preview = self.render_create_browser_apply_preview(
            name,
            homepage_url,
            allowed_domains_raw,
            menu_name,
            new_tab_url,
            icon_mode,
            security_profile,
            allow_password_manager,
            keep_cookies,
            enable_website_filter,
            confirmation,
        )
        if (confirmation or "").strip() != self.APPLY_CONFIRM_TOKEN:
            return preview
        resolved = self._resolve_create_inputs(
            name,
            homepage_url,
            allowed_domains_raw,
            menu_name,
            new_tab_url,
            icon_mode,
            security_profile,
            allow_password_manager,
            keep_cookies,
            enable_website_filter,
        )
        base_dir = self.service.get_default_base_dir()
        normalized_name = str(resolved["name"])
        homepage = str(resolved["homepage"])
        normalized_menu_name = str(resolved["menu_name"])
        normalized_new_tab_url = str(resolved["new_tab_url"])
        normalized_icon_mode = str(resolved["icon_mode"])
        allowed_domains = list(resolved["allowed_domains"])
        normalized_security_profile = str(resolved["security_profile"])
        resolved_allow_password_manager = bool(resolved["allow_password_manager"])
        resolved_keep_cookies = bool(resolved["keep_cookies"])
        resolved_enable_website_filter = bool(resolved["enable_website_filter"])
        result = self.service.execute_create_apply(
            name=normalized_name,
            homepage_url=homepage,
            allowed_domains=allowed_domains,
            target_dir=base_dir / normalized_name,
            menu_name=normalized_menu_name,
            new_tab_url=normalized_new_tab_url,
            icon_mode=normalized_icon_mode,
            security_profile=normalized_security_profile,
            allow_password_manager=resolved_allow_password_manager,
            keep_cookies=resolved_keep_cookies,
            enable_website_filter=resolved_enable_website_filter,
            child_lock=child_lock,
        )
        lines = [
            preview,
            "",
            "Apply-Ausführung",
            f"- Befehl: {result['command']}",
            f"- Return-Code: {result['returncode']}",
            f"- Status: {'OK' if result['ok'] else 'Fehler'}",
        ]
        stdout = str(result.get("stdout", "")).strip()
        stderr = str(result.get("stderr", "")).strip()
        if stdout:
            lines.extend(["", "stdout", "```text", stdout, "```"])
        if stderr:
            lines.extend(["", "stderr", "```text", stderr, "```"])
        rendered = "\n".join(lines)
        if not result.get("ok"):
            raise RuntimeError(rendered)
        return rendered

    def _render_execution_result(
        self,
        title: str,
        preview: str,
        result: dict[str, object],
    ) -> str:
        lines = [
            preview,
            "",
            title,
            f"- Befehl: {result['command']}",
            f"- Return-Code: {result['returncode']}",
            f"- Status: {'OK' if result['ok'] else 'Fehler'}",
        ]
        stdout = str(result.get("stdout", "")).strip()
        stderr = str(result.get("stderr", "")).strip()
        if stdout:
            lines.extend(["", "stdout", "```text", stdout, "```"])
        if stderr:
            lines.extend(["", "stderr", "```text", stderr, "```"])
        rendered = "\n".join(lines)
        if not result.get("ok"):
            raise RuntimeError(rendered)
        return rendered

    def render_register_existing_preview(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        name = (container_name or "").strip() or None
        token = (confirmation or "").strip()
        lines = self.service.run_register_existing_dry_run(container_name=name)
        header = [
            "Bestehende Container registrieren",
            "",
            "Register-Vorbereitung",
            f"- Auswahl: {name or 'alle erkannten Bestandscontainer'}",
            f"- Bestätigungscode erforderlich: {self.REGISTER_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {token or 'leer'}",
            "- Modus: Dry-Run intern, ohne Schreibzugriffe",
            "- Wirkung: start.sh, launcher.desktop und Menüeintrag werden bei Bedarf nachgezogen",
            "",
            *lines,
        ]
        if token != self.REGISTER_CONFIRM_TOKEN:
            header.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                ]
            )
        else:
            header.extend(["", "Freigabe", "- Bestätigungscode akzeptiert."])
        return "\n".join(header)

    def execute_register_existing_apply(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        preview = self.render_register_existing_preview(container_name, confirmation)
        if (confirmation or "").strip() != self.REGISTER_CONFIRM_TOKEN:
            return preview
        result = self.service.execute_register_existing_apply(
            container_name=(container_name or "").strip() or None
        )
        return self._render_execution_result("Register-Ausführung", preview, result)

    def render_refresh_existing_preview(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        name = (container_name or "").strip() or None
        token = (confirmation or "").strip()
        lines = self.service.run_refresh_existing_dry_run(container_name=name)
        header = [
            "Launcher/Icon aktualisieren",
            "",
            "Refresh-Vorbereitung",
            f"- Auswahl: {name or 'alle erkannten Bestandscontainer'}",
            f"- Bestätigungscode erforderlich: {self.REFRESH_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {token or 'leer'}",
            "- Modus: Dry-Run intern, ohne Schreibzugriffe",
            "- Wirkung: start.sh, launcher.desktop, Menüeintrag und Icon werden gezielt erneuert",
            "- Schutz: keine Änderung an Profilen, user.js oder policies.json",
            "",
            *lines,
        ]
        if token != self.REFRESH_CONFIRM_TOKEN:
            header.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                ]
            )
        else:
            header.extend(["", "Freigabe", "- Bestätigungscode akzeptiert."])
        return "\n".join(header)

    def execute_refresh_existing_apply(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        preview = self.render_refresh_existing_preview(container_name, confirmation)
        if (confirmation or "").strip() != self.REFRESH_CONFIRM_TOKEN:
            return preview
        result = self.service.execute_refresh_existing_apply(
            container_name=(container_name or "").strip() or None
        )
        rendered = self._render_execution_result("Refresh-Ausführung", preview, result)
        if result.get("ok"):
            rendered = "\n".join(
                [
                    rendered,
                    "",
                    "Hinweis",
                    "- Wenn das neue Icon noch nicht sichtbar ist, liegt meist nur ein Desktop-/Startmenü-Cache vor.",
                    "- In diesem Fall NetMon schließen, ab- und wieder anmelden oder das Startmenü kurz neu laden.",
                ]
            )
        return rendered

    def container_child_lock_enabled(self, container_name: str) -> bool:
        container = self.get_container_by_name(container_name)
        if container is None:
            return False
        try:
            return bool(self.service.container_child_lock_enabled(container))
        except Exception:
            LOGGER.exception("Secure Browser child lock status failed")
            return False

    def configure_container_child_lock(
        self,
        container_name: str,
        child_lock: dict[str, object] | None,
    ) -> None:
        container = self.get_container_by_name(container_name)
        if container is None:
            raise ValueError(
                self.T(
                    "secure_browser_container_missing_from_inventory",
                    "Container nicht mehr in der letzten Inventur vorhanden.",
                )
            )
        self.service.configure_container_child_lock(container, child_lock)

    def render_repair_policy_preview(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        name = (container_name or "").strip() or None
        token = (confirmation or "").strip()
        lines = self.service.run_repair_policy_dry_run(container_name=name)
        header = [
            "Policy reparieren",
            "",
            "Repair-Vorbereitung",
            f"- Auswahl: {name or 'alle erkannten Bestandscontainer'}",
            f"- Bestätigungscode erforderlich: {self.REPAIR_POLICY_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {token or 'leer'}",
            "- Modus: Dry-Run intern, ohne Schreibzugriffe",
            "- Wirkung: policies.json und user.js werden auf das aktuelle Domain-/Subdomain-Schema angehoben",
            "- Schutz: keine Änderung an Binary, Launcher, Menüeintrag oder Cookies/Profildaten",
            "",
            *lines,
        ]
        if token != self.REPAIR_POLICY_CONFIRM_TOKEN:
            header.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                ]
            )
        else:
            header.extend(["", "Freigabe", "- Bestätigungscode akzeptiert."])
        return "\n".join(header)

    def execute_repair_policy_apply(
        self,
        container_name: str | None = None,
        confirmation: str = "",
    ) -> str:
        preview = self.render_repair_policy_preview(container_name, confirmation)
        if (confirmation or "").strip() != self.REPAIR_POLICY_CONFIRM_TOKEN:
            return preview
        result = self.service.execute_repair_policy_apply(
            container_name=(container_name or "").strip() or None
        )
        return self._render_execution_result("Repair-Ausführung", preview, result)

    def render_cleanup_menu_preview(self, confirmation: str = "") -> str:
        token = (confirmation or "").strip()
        lines = self.service.run_cleanup_menu_dry_run()
        header = [
            "Menü bereinigen",
            "",
            "Cleanup-Vorbereitung",
            f"- Bestätigungscode erforderlich: {self.CLEANUP_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {token or 'leer'}",
            "- Modus: Dry-Run intern, ohne Schreibzugriffe",
            "",
            *lines,
        ]
        if token != self.CLEANUP_CONFIRM_TOKEN:
            header.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                ]
            )
        else:
            header.extend(["", "Freigabe", "- Bestätigungscode akzeptiert."])
        return "\n".join(header)

    def execute_cleanup_menu_apply(self, confirmation: str = "") -> str:
        preview = self.render_cleanup_menu_preview(confirmation)
        if (confirmation or "").strip() != self.CLEANUP_CONFIRM_TOKEN:
            return preview
        result = self.service.execute_cleanup_menu_apply()
        return self._render_execution_result("Cleanup-Ausführung", preview, result)

    def render_uninstall_preview(
        self,
        container_name: str | None,
        confirmation: str = "",
    ) -> str:
        name = (container_name or "").strip()
        token = (confirmation or "").strip()
        if not name:
            return "Entfernen\n\nKein Container ausgewählt."
        if self.is_protected_firefox_base_name(name):
            return "\n".join(
                [
                    "Entfernen",
                    "",
                    "Firefox-Basis geschützt",
                    f"- Verzeichnis: {name}",
                    "- Abbruch: Die Firefox-Basis wird zum Anlegen neuer Browser benötigt.",
                    "- Hinweis: Reparatur oder Neuinstallation erfolgt über den SetupManager.",
                ]
            )
        try:
            lines = self.service.run_uninstall_dry_run(container_name=name)
        except ValueError as exc:
            return "\n".join(
                [
                    "Entfernen",
                    "",
                    "Uninstall-Vorbereitung",
                    f"- Container: {name}",
                    "- Status: nicht verfügbar",
                    f"- Hinweis: {exc}",
                    "",
                    "Freigabe",
                    "- Abbruch: Der Container ist nicht mehr in der aktuellen Inventur.",
                ]
            )
        except Exception as exc:
            return "\n".join(
                [
                    "Entfernen",
                    "",
                    "Uninstall-Vorbereitung",
                    f"- Container: {name}",
                    "- Status: Fehler",
                    f"- Hinweis: {exc}",
                ]
            )
        header = [
            "Entfernen",
            "",
            "Uninstall-Vorbereitung",
            f"- Container: {name}",
            f"- Bestätigungscode erforderlich: {self.UNINSTALL_CONFIRM_TOKEN}",
            f"- Eingegebener Code: {token or 'leer'}",
            "- Modus: Dry-Run intern, ohne Schreibzugriffe",
            "",
            *lines,
        ]
        if token != self.UNINSTALL_CONFIRM_TOKEN:
            header.extend(
                [
                    "",
                    "Freigabe",
                    "- Noch blockiert: Bestätigungscode stimmt nicht.",
                ]
            )
        else:
            header.extend(["", "Freigabe", "- Bestätigungscode akzeptiert."])
        return "\n".join(header)

    def execute_uninstall_apply(
        self,
        container_name: str | None,
        confirmation: str = "",
    ) -> str:
        preview = self.render_uninstall_preview(container_name, confirmation)
        name = (container_name or "").strip()
        if (
            not name
            or self.is_protected_firefox_base_name(name)
            or (confirmation or "").strip() != self.UNINSTALL_CONFIRM_TOKEN
            or "Container nicht gefunden:" in preview
            or "Abbruch: Der Container ist nicht mehr in der aktuellen Inventur."
            in preview
        ):
            return preview
        result = self.service.execute_uninstall_apply(container_name=name)
        return self._render_execution_result("Uninstall-Ausführung", preview, result)

    def render_container_detail(self, container: BrowserContainer | None) -> str:
        if container is None:
            return self.T(
                "secure_browser_no_container_selected", "Kein Container ausgewählt."
            )
        domains = (
            ", ".join(container.allowed_domains)
            if container.allowed_domains
            else self.T("secure_browser_value_none", "keine")
        )
        detail_lines = [
            f"- {self.T('secure_browser_detail_status', 'Status')}: {container.status}",
            f"- {self.T('secure_browser_detail_path', 'Pfad')}: {container.path}",
            f"- {self.T('secure_browser_detail_binary', 'Binary')}: {container.binary_path}",
            f"- {self.T('secure_browser_detail_profile', 'Profil')}: {self._format_profile_path(container)}",
            f"- {self.T('secure_browser_detail_menu', 'Menü')}: {self._format_menu_entry(container)}",
            f"- {self.T('secure_browser_detail_homepage', 'Homepage')}: {container.homepage_url or self.T('secure_browser_value_not_set', 'nicht hinterlegt')}",
            f"- {self.T('secure_browser_detail_domains', 'Domains')}: {domains}",
        ]
        return "\n".join(
            [
                container.name,
                "",
                self.T("secure_browser_section_overview", "Übersicht"),
                *detail_lines,
            ]
        )

    def render_container_report(
        self,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if not container_name:
            return self.T(
                "secure_browser_no_container_selected", "Kein Container ausgewählt."
            )
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            return self.T(
                "secure_browser_container_missing_from_inventory",
                "Container nicht mehr in der letzten Inventur vorhanden.",
            )
        checks = self.service.verify_container(container)
        risks = self.service.derive_risk_hints(container)
        artifacts = self.service.read_container_artifacts(container)
        launcher_info = self.service.inspect_launchers(container)
        return "\n".join(
            [
                self.render_container_detail(container),
                "",
                self.T("secure_browser_section_risks", "Risiko-Hinweise"),
                *[f"- {risk}" for risk in risks],
                "",
                self.T("secure_browser_section_verification", "Verifikation"),
                *[f"- {check}" for check in checks],
                "",
                self.T("secure_browser_section_launcher_check", "Launcher-Prüfung"),
                "",
                self.T(
                    "secure_browser_block_launcher_structured",
                    "[launcher.desktop strukturiert]",
                ),
                *[
                    f"- {key}: {value}"
                    for key, value in launcher_info["launcher.desktop"].items()
                ],
                "",
                *self._render_menu_entries_section(launcher_info),
                "",
                self.T("secure_browser_section_artifacts", "Artefakte"),
                "[start.sh]",
                artifacts["start.sh"],
                "",
                "[launcher.desktop]",
                artifacts["launcher.desktop"],
            ]
        )

    def render_artifact_report(
        self,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if not container_name:
            return self.T(
                "secure_browser_no_container_selected", "Kein Container ausgewählt."
            )
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            return self.T(
                "secure_browser_container_missing_from_inventory",
                "Container nicht mehr in der letzten Inventur vorhanden.",
            )
        artifacts = self.service.read_container_artifacts(container)
        return "\n".join(
            [
                container.name,
                "",
                self.T("secure_browser_section_artifacts", "Artefakte"),
                "",
                "[start.sh]",
                artifacts["start.sh"],
                "",
                "[launcher.desktop]",
                artifacts["launcher.desktop"],
            ]
        )

    def render_selected_view(
        self,
        view_mode: str,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if view_mode == self.VIEW_LAUNCHER:
            return self.render_launcher_report(
                container_name,
                status_filter,
                search_query,
                risk_filter,
            )
        if view_mode == self.VIEW_ARTIFACTS:
            return self.render_artifact_report(
                container_name,
                status_filter,
                search_query,
                risk_filter,
            )
        return self.render_container_report(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )

    def render_launcher_report(
        self,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if not container_name:
            return self.T(
                "secure_browser_no_container_selected", "Kein Container ausgewählt."
            )
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            return self.T(
                "secure_browser_container_missing_from_inventory",
                "Container nicht mehr in der letzten Inventur vorhanden.",
            )
        launcher_info = self.service.inspect_launchers(container)
        artifacts = self.service.read_container_artifacts(container)
        return "\n".join(
            [
                container.name,
                "",
                self.T("secure_browser_section_launcher_check", "Launcher-Prüfung"),
                "",
                self.T(
                    "secure_browser_block_launcher_structured",
                    "[launcher.desktop strukturiert]",
                ),
                *[
                    f"- {key}: {value}"
                    for key, value in launcher_info["launcher.desktop"].items()
                ],
                "",
                *self._render_menu_entries_section(launcher_info),
                "",
                self.T(
                    "secure_browser_block_launcher_preview",
                    "[launcher.desktop Vorschau]",
                ),
                artifacts["launcher.desktop"],
            ]
        )

    def render_policy_editor(
        self,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if not container_name:
            return self.T(
                "secure_browser_no_container_selected", "Kein Container ausgewählt."
            )
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            return self.T(
                "secure_browser_container_missing_from_inventory",
                "Container nicht mehr in der letzten Inventur vorhanden.",
            )
        policy_json = self.service.read_policy_json(container)
        return "\n".join(
            [
                f"{container.name}",
                "",
                self.T("secure_browser_section_whitelist_editor", "Whitelist-Editor"),
                "",
                f"- {self.T('secure_browser_whitelist_file', 'Datei')}: policies.json",
                f"- {self.T('secure_browser_preflight_mode_label', 'Modus')}: {self.T('secure_browser_whitelist_mode_manual', 'manuelle Bearbeitung')}",
                f"- {self.T('secure_browser_note_label', 'Hinweis')}: {self.T('secure_browser_whitelist_note_backup', 'Vor dem Speichern wird automatisch ein Backup angelegt.')}",
                f"- {self.T('secure_browser_note_label', 'Hinweis')}: {self.T('secure_browser_whitelist_note_runtime', 'Änderungen wirken auf Root- und Runtime-policies.json.')}",
                "",
                "```json",
                policy_json.rstrip(),
                "```",
            ]
        )

    def execute_policy_save_apply(
        self,
        container_name: str | None,
        content: str,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        if not container_name:
            raise ValueError(
                self.T(
                    "secure_browser_no_container_selected", "Kein Container ausgewählt."
                )
            )
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            raise ValueError(
                self.T(
                    "secure_browser_container_missing_from_inventory",
                    "Container nicht mehr in der letzten Inventur vorhanden.",
                )
            )
        result = self.service.save_policy_json(container, content)
        return "\n".join(
            [
                f"{container.name}",
                "",
                self.T("secure_browser_whitelist_saved_title", "Whitelist gespeichert"),
                "",
                f"- {self.T('secure_browser_whitelist_source', 'Quelle')}: {result['source_path']}",
                f"- {self.T('secure_browser_whitelist_runtime', 'Runtime')}: {result['runtime_path']}",
                f"- {self.T('secure_browser_whitelist_backup', 'Backup')}: {result['backup_dir']}",
                f"- {self.T('secure_browser_whitelist_saved_files', 'Gesicherte Dateien')}: {result['backup_count']}",
                f"- {self.T('secure_browser_note_label', 'Hinweis')}: {self.T('secure_browser_whitelist_restart_note', 'Für bereits offene Browserfenster den Container neu starten.')}",
            ]
        )

    @staticmethod
    def _make_policy_exception_patterns(url_or_domain: str) -> list[str]:
        raw = str(url_or_domain or "").strip()
        if not raw:
            raise ValueError("Keine URL angegeben.")
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        host = (parsed.hostname or "").strip().lower()
        if not host or "." not in host:
            raise ValueError("Ungültige URL oder Domain für die Ausnahme.")
        port = parsed.port
        path = parsed.path or "/"
        normalized_path = path if path.startswith("/") else f"/{path}"
        if port:
            return [f"{parsed.scheme or 'https'}://{host}:{port}{normalized_path}*"]
        patterns = [f"{parsed.scheme or '*'}://{host}{normalized_path}*"]
        if normalized_path == "/":
            patterns = [f"*://{host}/*"]
            base_host = host.removeprefix("www.")
            if host.startswith("www.") and base_host:
                patterns.append(f"*://{base_host}/*")
            elif "." in host:
                patterns.append(f"*://www.{host}/*")
            wildcard_host = base_host or host
            if "." in wildcard_host:
                patterns.append(f"*://*.{wildcard_host}/*")
        return patterns

    def append_policy_exception_json(self, content: str, url_or_domain: str) -> str:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ungültiges JSON im Whitelist-Editor: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("policies.json muss ein JSON-Objekt enthalten.")
        policies = payload.setdefault("policies", {})
        if not isinstance(policies, dict):
            raise ValueError("policies muss ein JSON-Objekt sein.")
        website_filter = policies.setdefault("WebsiteFilter", {})
        if not isinstance(website_filter, dict):
            raise ValueError("WebsiteFilter muss ein JSON-Objekt sein.")
        block_list = website_filter.setdefault(
            "Block", [self.WEBSITE_FILTER_BLOCK_PATTERN]
        )
        if not isinstance(block_list, list):
            raise ValueError("WebsiteFilter.Block muss eine Liste sein.")
        block_list[:] = [
            (
                self.WEBSITE_FILTER_BLOCK_PATTERN
                if item in {"<all_urls>", "*://*/*"}
                else item
            )
            for item in block_list
        ]
        block_list[:] = list(dict.fromkeys(block_list))
        if self.WEBSITE_FILTER_BLOCK_PATTERN not in block_list:
            block_list.insert(0, self.WEBSITE_FILTER_BLOCK_PATTERN)
        exceptions = website_filter.setdefault("Exceptions", [])
        if not isinstance(exceptions, list):
            raise ValueError("WebsiteFilter.Exceptions muss eine Liste sein.")
        for pattern in self._make_policy_exception_patterns(url_or_domain):
            if pattern not in exceptions:
                exceptions.append(pattern)
        return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"

    def get_copy_payload(
        self,
        container_name: str | None,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> dict[str, str]:
        if not container_name:
            return {"path": "", "exec": ""}
        container = self.get_container_by_name(
            container_name,
            status_filter,
            search_query,
            risk_filter,
        )
        if container is None:
            return {"path": "", "exec": ""}
        try:
            launcher_info = self.service.inspect_launchers(container)
        except Exception:
            return {
                "path": str(container.path),
                "exec": "",
            }
        launcher_exec = launcher_info["launcher.desktop"].get("Exec", "")
        menu_exec = launcher_info["menu_entry"].get("Exec", "")
        exec_value = launcher_exec if launcher_exec != "nicht gesetzt" else menu_exec
        if exec_value == "nicht gesetzt":
            exec_value = ""
        return {
            "path": str(container.path),
            "exec": exec_value,
        }

    def render_inventory_export(
        self,
        status_filter: str | None = None,
        search_query: str | None = None,
        risk_filter: str | None = None,
    ) -> str:
        containers = self.get_filtered_containers(
            status_filter,
            search_query,
            risk_filter,
        )
        if not containers:
            return "# Secure Browser Inventory\n\n" + self.T(
                "secure_browser_inventory_no_containers_short",
                "Keine Container erkannt.",
            )
        lines = [
            "# Secure Browser Inventory",
            "",
            self.render_inventory_summary(status_filter, search_query, risk_filter),
            "",
        ]
        for container in containers:
            domains = (
                ", ".join(container.allowed_domains)
                if container.allowed_domains
                else self.T("secure_browser_value_none", "keine")
            )
            lines.extend(
                [
                    f"## {container.name}",
                    f"- {self.T('secure_browser_detail_status', 'Status')}: {container.status}",
                    f"- {self.T('secure_browser_detail_path', 'Pfad')}: {container.path}",
                    f"- {self.T('secure_browser_detail_binary', 'Binary')}: {container.binary_path}",
                    f"- {self.T('secure_browser_detail_profile', 'Profil')}: {self._format_profile_path(container)}",
                    f"- {self.T('secure_browser_detail_menu', 'Menü')}: {self._format_menu_entry(container)}",
                    f"- {self.T('secure_browser_detail_homepage', 'Homepage')}: {container.homepage_url or self.T('secure_browser_value_not_set', 'nicht hinterlegt')}",
                    f"- {self.T('secure_browser_detail_domains', 'Domains')}: {domains}",
                    "",
                ]
            )
        return "\n".join(lines).rstrip()

    def render_inventory_text(self) -> str:
        containers = self.scan_inventory()
        if not containers:
            return self.T(
                "secure_browser_inventory_none",
                "Keine Secure-Browser-Container erkannt.",
            )
        lines = []
        for container in containers:
            profile = self._format_profile_path(container)
            menu_entry = self._format_menu_entry(container)
            domains = (
                ", ".join(container.allowed_domains)
                if container.allowed_domains
                else self.T("secure_browser_value_none", "keine")
            )
            lines.extend(
                [
                    f"{container.name}",
                    f"  {self.T('secure_browser_detail_status', 'Status')}: {container.status}",
                    f"  {self.T('secure_browser_detail_path', 'Pfad')}: {container.path}",
                    f"  {self.T('secure_browser_detail_binary', 'Binary')}: {container.binary_path}",
                    f"  {self.T('secure_browser_detail_profile', 'Profil')}: {profile}",
                    f"  {self.T('secure_browser_detail_menu', 'Menü')}: {menu_entry}",
                    f"  {self.T('secure_browser_detail_domains', 'Domains')}: {domains}",
                    "",
                ]
            )
        return "\n".join(lines).rstrip()
