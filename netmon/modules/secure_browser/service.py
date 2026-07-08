"""Service layer placeholder for the NetMon Secure Browser module."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from types import ModuleType

from .models import BrowserContainer


LOGGER = logging.getLogger(__name__)


class SecureBrowserService:
    """Future entry point for the external Secure Browser Manager tool."""

    REPO_ROOT = Path(__file__).resolve().parents[3]
    TOOL_ROOT = REPO_ROOT / "tools/secure_browser_manager"
    TOOL_SCRIPT = TOOL_ROOT / "browser_container_builder.py"
    TOOL_CONFIG = TOOL_ROOT / "containers.example.json"
    MAX_PREVIEW_LINES = 20
    POLICY_BACKUP_DIRNAME = "policy-editor-backups"
    RUNTIME_INVENTORY_FILENAME = "netmon-secure-browser-container_inventory.md"
    COMMON_SOURCE_DIR_NAMES = (
        Path("/opt/netmon-browser/firefox"),
        Path.home() / "Programme" / "firefox-base" / "firefox",
    )

    def __init__(self, tool_root: Path | None = None) -> None:
        self.tool_root = (tool_root or self.TOOL_ROOT).resolve()
        self.tool_script = self.tool_root / "browser_container_builder.py"
        self.tool_config = self.tool_root / "containers.example.json"
        self._tool_module: ModuleType | None = None

    def _load_tool_module(self) -> ModuleType:
        if self._tool_module is not None:
            return self._tool_module
        spec = importlib.util.spec_from_file_location(
            "netmon_secure_browser_builder",
            self.tool_script,
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(
                f"Secure Browser Manager konnte nicht geladen werden: {self.tool_script}"
            )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            sys.modules.pop(spec.name, None)
            raise
        self._tool_module = module
        return module

    def _todo(self, action: str) -> None:
        LOGGER.info("Secure Browser service placeholder called: %s", action)
        raise NotImplementedError(
            f"Secure Browser service action '{action}' is not implemented yet."
        )

    def run_preflight_checks(self) -> list[str]:
        checks: list[str] = []
        checks.extend(self._check_tool_artifacts())
        checks.extend(self._check_firefox_source())
        checks.extend(self._check_menu_target())
        checks.extend(self._check_base_directory())
        return checks

    def _check_tool_artifacts(self) -> list[str]:
        checks = [
            (
                "Builder-Skript",
                self.tool_script,
                self.tool_script.is_file(),
            ),
            (
                "Builder-Konfiguration",
                self.tool_config,
                self.tool_config.is_file(),
            ),
        ]
        lines = []
        for label, path, ok in checks:
            status = "OK" if ok else "FEHLT"
            lines.append(f"- {label}: {status} ({path})")
        try:
            self._load_tool_module()
        except Exception as exc:
            lines.append(f"- Builder-Modul: FEHLER ({exc})")
        else:
            lines.append("- Builder-Modul: OK (intern ladbar)")
        return lines

    def _check_firefox_source(self) -> list[str]:
        configured_source = self._read_configured_source_firefox_dir()
        resolved_source = self.get_default_source_firefox_dir()
        if configured_source is not None:
            binary_path = configured_source / "firefox"
            source_exists = configured_source.is_dir()
            binary_exists = binary_path.is_file()
            source_status = "OK" if source_exists else "FEHLT"
            binary_status = "OK" if binary_exists else "FEHLT"
            lines = [
                f"- Firefox-Quelle (konfiguriert): {source_status} ({configured_source})",
                f"- Firefox-Binary (konfiguriert): {binary_status} ({binary_path})",
            ]
            if resolved_source is not None and resolved_source != configured_source:
                lines.append(f"- Firefox-Quelle (Fallback): OK ({resolved_source})")
            return lines
        if resolved_source is None:
            return [
                "- Firefox-Quelle: HINWEIS (keine gültige Standardquelle gefunden)"
            ]
        return [
            f"- Firefox-Quelle (Fallback): OK ({resolved_source})",
            f"- Firefox-Binary (Fallback): OK ({resolved_source / 'firefox'})",
        ]

    def _check_menu_target(self) -> list[str]:
        applications_dir = Path.home() / ".local/share/applications"
        parent_dir = applications_dir.parent
        if applications_dir.exists():
            writable = os.access(applications_dir, os.W_OK)
            status = "OK" if writable else "WARNUNG"
            detail = "beschreibbar" if writable else "nicht beschreibbar"
            return [f"- Menüpfad: {status} ({applications_dir}, {detail})"]
        parent_writable = parent_dir.exists() and os.access(parent_dir, os.W_OK)
        status = "OK" if parent_writable else "WARNUNG"
        detail = (
            "wird bei Bedarf anlegbar sein"
            if parent_writable
            else "Elternpfad nicht beschreibbar"
        )
        return [f"- Menüpfad: {status} ({applications_dir}, {detail})"]

    def _check_base_directory(self) -> list[str]:
        base_dir = self.get_default_base_dir()
        if base_dir.exists():
            writable = os.access(base_dir, os.W_OK)
            status = "OK" if writable else "WARNUNG"
            detail = "beschreibbar" if writable else "nicht beschreibbar"
            return [f"- Zielbasis: {status} ({base_dir}, {detail})"]
        parent = base_dir.parent
        parent_writable = parent.exists() and os.access(parent, os.W_OK)
        status = "OK" if parent_writable else "WARNUNG"
        detail = (
            "wird bei Bedarf anlegbar sein"
            if parent_writable
            else "Elternpfad nicht beschreibbar"
        )
        return [f"- Zielbasis: {status} ({base_dir}, {detail})"]

    def scan_containers(self) -> list[BrowserContainer]:
        module = self._load_tool_module()
        base_dir = Path(module.DEFAULT_BASE_DIR)
        containers = module.discover_existing_containers(base_dir)
        profiles = module.discover_firefox_profiles(module.DEFAULT_PROFILE_BASE_DIRS)
        module.correlate_profiles(containers, profiles)
        menu_entries = module.list_managed_menu_entries(module.DEFAULT_APPLICATIONS_DIR)
        result: list[BrowserContainer] = []
        for container in containers:
            associated = [
                entry
                for entry in menu_entries
                if entry.container_root == container.root_dir
                or entry.container_name == container.name
            ]
            effective_profile = module.get_effective_profile_path(container)
            status = module.derive_container_status(container, associated)
            result.append(
                BrowserContainer(
                    name=container.name,
                    path=container.root_dir,
                    binary_path=container.binary_path,
                    profile_path=effective_profile or Path(),
                    homepage_url="",
                    allowed_domains=list(container.domains),
                    icon_path=container.root_dir / "icons",
                    menu_entry_path=associated[0].path if associated else None,
                    status=status,
                )
            )
        return result

    def get_default_base_dir(self) -> Path:
        try:
            module = self._load_tool_module()
        except Exception:
            LOGGER.warning(
                "Secure Browser default base dir fallback used because builder could not be loaded."
            )
            return Path.home() / "Programme"
        return Path(module.DEFAULT_BASE_DIR)

    def list_create_presets(self) -> list[dict[str, object]]:
        content = self._read_tool_config_payload()
        if not content:
            return []
        containers = content.get("containers", [])
        if not isinstance(containers, list):
            return []
        presets: list[dict[str, object]] = []
        for item in containers:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            presets.append(item)
        return presets

    def _read_tool_config_payload(self) -> dict[str, object]:
        try:
            content = json.loads(self.tool_config.read_text(encoding="utf-8"))
        except FileNotFoundError:
            LOGGER.warning("Secure Browser preset config not found: %s", self.tool_config)
            return {}
        except json.JSONDecodeError:
            LOGGER.warning("Secure Browser preset config is invalid JSON: %s", self.tool_config)
            return {}
        return content

    def _read_configured_source_firefox_dir(self) -> Path | None:
        content = self._read_tool_config_payload()
        raw = content.get("default_source_firefox_dir")
        if isinstance(raw, str) and raw.strip():
            return Path(raw).expanduser().resolve()
        return None

    @staticmethod
    def _is_valid_source_firefox_dir(source_dir: Path | None) -> bool:
        if source_dir is None:
            return False
        return source_dir.is_dir() and (source_dir / "firefox").is_file()

    def _iter_source_firefox_candidates(self) -> list[Path]:
        candidates: list[Path] = []
        base_dir = self.get_default_base_dir()
        configured = self._read_configured_source_firefox_dir()
        for candidate in (
            configured,
            base_dir / "firefox-base" / "firefox",
            *self.COMMON_SOURCE_DIR_NAMES,
        ):
            if candidate is None:
                continue
            resolved = candidate.expanduser().resolve()
            if resolved not in candidates:
                candidates.append(resolved)
        return candidates

    def get_default_source_firefox_dir(self) -> Path | None:
        for candidate in self._iter_source_firefox_candidates():
            if self._is_valid_source_firefox_dir(candidate):
                return candidate
        configured = self._read_configured_source_firefox_dir()
        if configured is not None:
            LOGGER.warning(
                "Secure Browser configured Firefox source is not usable: %s",
                configured,
            )
        return None

    def build_generated_create_config(
        self,
        *,
        name: str,
        homepage_url: str,
        allowed_domains: list[str],
        target_dir: Path,
        menu_name: str,
        new_tab_url: str,
        icon_mode: str,
        security_profile: str = "Standard",
        allow_password_manager: bool = True,
        keep_cookies: bool = True,
        enable_website_filter: bool = True,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "containers": [
                {
                    "name": name,
                    "path": str(target_dir),
                    "homepage_url": homepage_url,
                    "new_tab_url": new_tab_url,
                    "menu_name": menu_name,
                    "allowed_domains": allowed_domains,
                    "icon_mode": icon_mode,
                    "security_profile": security_profile,
                    "allow_password_manager": allow_password_manager,
                    "keep_cookies": keep_cookies,
                    "enable_website_filter": enable_website_filter,
                }
            ]
        }
        source_dir = self.get_default_source_firefox_dir()
        if source_dir is not None:
            payload["default_source_firefox_dir"] = str(source_dir)
        return payload

    def _write_generated_create_config(self, payload: dict[str, object]) -> Path:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="netmon-secure-browser-",
            delete=False,
            dir="/tmp",
        ) as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=True)
            handle.write("\n")
            return Path(handle.name)

    def _get_runtime_inventory_path(self) -> Path:
        return Path(tempfile.gettempdir()) / self.RUNTIME_INVENTORY_FILENAME

    def build_create_preview(
        self,
        name: str,
        homepage_url: str,
        allowed_domains: list[str],
        *,
        target_dir: Path,
        menu_name: str,
        new_tab_url: str,
        icon_mode: str,
        security_profile: str = "Standard",
        allow_password_manager: bool = True,
        keep_cookies: bool = True,
        enable_website_filter: bool = True,
    ) -> dict[str, str]:
        source_dir = self.get_default_source_firefox_dir()
        generated_config = self.build_generated_create_config(
            name=name,
            homepage_url=homepage_url,
            allowed_domains=allowed_domains,
            target_dir=target_dir,
            menu_name=menu_name,
            new_tab_url=new_tab_url,
            icon_mode=icon_mode,
            security_profile=security_profile,
            allow_password_manager=allow_password_manager,
            keep_cookies=keep_cookies,
            enable_website_filter=enable_website_filter,
        )
        command = (
            f"python3 {self.tool_script} "
            f"--config <generierte-create-config> "
            f"--inventory {self._get_runtime_inventory_path()} "
            f"--only {name}"
        )
        return {
            "tool_script": str(self.tool_script),
            "tool_config": "<generierte-create-config>",
            "command": command,
            "payload": json.dumps(generated_config, indent=2, ensure_ascii=True),
            "source_firefox_dir": str(source_dir) if source_dir is not None else "",
        }

    def run_create_dry_run(
        self,
        *,
        name: str,
        homepage_url: str,
        allowed_domains: list[str],
        target_dir: Path,
        menu_name: str,
        new_tab_url: str,
        icon_mode: str,
        security_profile: str = "Standard",
        allow_password_manager: bool = True,
        keep_cookies: bool = True,
        enable_website_filter: bool = True,
    ) -> list[str]:
        module = self._load_tool_module()
        payload = self.build_generated_create_config(
            name=name,
            homepage_url=homepage_url,
            allowed_domains=allowed_domains,
            target_dir=target_dir,
            menu_name=menu_name,
            new_tab_url=new_tab_url,
            icon_mode=icon_mode,
            security_profile=security_profile,
            allow_password_manager=allow_password_manager,
            keep_cookies=keep_cookies,
            enable_website_filter=enable_website_filter,
        )
        specs = module.validate_config_payload(payload, self.get_default_base_dir())
        discovered = module.discover_existing_containers(self.get_default_base_dir())
        source_problems = module.select_missing_sources(specs, discovered)
        dry_run_lines = module.build_apply_plan(
            specs,
            discovered,
            module.DEFAULT_APPLICATIONS_DIR,
        )
        if source_problems:
            return [
                "Builder Dry-Run",
                "",
                "Quelle konnte noch nicht eindeutig bestimmt werden.",
                *[f"- {item}" for item in source_problems],
                "",
                *dry_run_lines,
            ]
        return ["Builder Dry-Run", "", *dry_run_lines]

    def build_apply_preview(
        self,
        *,
        name: str,
        target_dir: Path,
    ) -> dict[str, str]:
        command = (
            f"python3 {self.tool_script} "
            f"--config <generierte-create-config> "
            f"--inventory {self._get_runtime_inventory_path()} "
            f"--only {name} --apply"
        )
        return {
            "command": command,
            "target_dir": str(target_dir),
            "safety": (
                "Vor Ausführung muss der Dry-Run geprüft werden. "
                "Bestehende Zielordner führen zum Abbruch. "
                "Backups werden vor Änderungen angelegt."
            ),
        }

    def execute_create_apply(
        self,
        *,
        name: str,
        homepage_url: str,
        allowed_domains: list[str],
        target_dir: Path,
        menu_name: str,
        new_tab_url: str,
        icon_mode: str,
        security_profile: str = "Standard",
        allow_password_manager: bool = True,
        keep_cookies: bool = True,
        enable_website_filter: bool = True,
    ) -> dict[str, object]:
        config_path = self._write_generated_create_config(
            self.build_generated_create_config(
                name=name,
                homepage_url=homepage_url,
                allowed_domains=allowed_domains,
                target_dir=target_dir,
                menu_name=menu_name,
                new_tab_url=new_tab_url,
                icon_mode=icon_mode,
                security_profile=security_profile,
                allow_password_manager=allow_password_manager,
                keep_cookies=keep_cookies,
                enable_website_filter=enable_website_filter,
            )
        )
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(config_path),
            "--only",
            name,
            "--apply",
        ]
        return self._run_builder_command(command)

    def _run_builder_command(self, command: list[str]) -> dict[str, object]:
        final_command = list(command)
        if "--inventory" not in final_command:
            final_command.extend(
                ["--inventory", str(self._get_runtime_inventory_path())]
            )
        result = subprocess.run(
            final_command,
            check=False,
            capture_output=True,
            text=True,
            cwd=str(self.tool_root),
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return {
            "command": " ".join(final_command),
            "returncode": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
            "ok": result.returncode == 0,
        }

    def run_register_existing_dry_run(self, *, container_name: str | None = None) -> list[str]:
        module = self._load_tool_module()
        base_dir = self.get_default_base_dir()
        discovered = module.discover_existing_containers(base_dir)
        profiles = module.discover_firefox_profiles(module.DEFAULT_PROFILE_BASE_DIRS)
        module.correlate_profiles(discovered, profiles)
        candidates = module.get_register_existing_candidates(discovered)
        if container_name:
            candidates, _ = module.filter_by_only(candidates, [], container_name)
        return module.build_register_existing_plan(candidates, module.DEFAULT_APPLICATIONS_DIR)

    def execute_register_existing_apply(
        self,
        *,
        container_name: str | None = None,
    ) -> dict[str, object]:
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(self.tool_config),
            "--register-existing",
        ]
        if container_name:
            command.extend(["--only", container_name])
        command.append("--apply")
        return self._run_builder_command(command)

    def run_refresh_existing_dry_run(self, *, container_name: str | None = None) -> list[str]:
        module = self._load_tool_module()
        base_dir = self.get_default_base_dir()
        discovered = module.discover_existing_containers(base_dir)
        profiles = module.discover_firefox_profiles(module.DEFAULT_PROFILE_BASE_DIRS)
        module.correlate_profiles(discovered, profiles)
        if container_name:
            discovered, _ = module.filter_by_only(discovered, [], container_name)
        return module.build_refresh_existing_plan(discovered, module.DEFAULT_APPLICATIONS_DIR)

    def execute_refresh_existing_apply(
        self,
        *,
        container_name: str | None = None,
    ) -> dict[str, object]:
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(self.tool_config),
            "--refresh-existing",
        ]
        if container_name:
            command.extend(["--only", container_name])
        command.append("--apply")
        return self._run_builder_command(command)

    def run_repair_policy_dry_run(self, *, container_name: str | None = None) -> list[str]:
        module = self._load_tool_module()
        base_dir = self.get_default_base_dir()
        discovered = module.discover_existing_containers(base_dir)
        profiles = module.discover_firefox_profiles(module.DEFAULT_PROFILE_BASE_DIRS)
        module.correlate_profiles(discovered, profiles)
        if container_name:
            discovered, _ = module.filter_by_only(discovered, [], container_name)
        return module.build_repair_policy_plan(discovered)

    def execute_repair_policy_apply(
        self,
        *,
        container_name: str | None = None,
    ) -> dict[str, object]:
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(self.tool_config),
            "--repair-policy",
        ]
        if container_name:
            command.extend(["--only", container_name])
        command.append("--apply")
        return self._run_builder_command(command)

    def run_cleanup_menu_dry_run(self) -> list[str]:
        module = self._load_tool_module()
        lines, _targets = module.build_cleanup_menu_plan(module.DEFAULT_APPLICATIONS_DIR)
        return lines

    def execute_cleanup_menu_apply(self) -> dict[str, object]:
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(self.tool_config),
            "--cleanup-menu",
            "--apply",
        ]
        return self._run_builder_command(command)

    def run_uninstall_dry_run(self, *, container_name: str) -> list[str]:
        module = self._load_tool_module()
        base_dir = self.get_default_base_dir()
        discovered = module.discover_existing_containers(base_dir)
        profiles = module.discover_firefox_profiles(module.DEFAULT_PROFILE_BASE_DIRS)
        module.correlate_profiles(discovered, profiles)
        container = module.find_container_by_name(discovered, container_name)
        if container is None:
            raise ValueError(f"Container nicht gefunden: {container_name}")
        return module.build_uninstall_plan(
            container,
            module.DEFAULT_APPLICATIONS_DIR,
            base_dir,
        )

    def execute_uninstall_apply(self, *, container_name: str) -> dict[str, object]:
        command = [
            "python3",
            str(self.tool_script),
            "--config",
            str(self.tool_config),
            "--uninstall",
            container_name,
            "--apply",
        ]
        return self._run_builder_command(command)

    @staticmethod
    def _is_internal_profile(container: BrowserContainer) -> bool:
        try:
            container.profile_path.relative_to(container.path)
            return True
        except ValueError:
            return False

    @staticmethod
    def _is_external_firefox_profile(profile_path: Path) -> bool:
        profile_text = str(profile_path)
        home = Path.home()
        external_roots = [
            home / ".mozilla" / "firefox",
            home / ".config" / "mozilla" / "firefox",
        ]
        return any(profile_text.startswith(str(root)) for root in external_roots)

    @staticmethod
    def _exists_and_executable(path: Path) -> bool:
        return path.is_file() and os.access(path, os.X_OK)

    def verify_container(self, container: BrowserContainer) -> list[str]:
        checks: list[str] = []
        checks.append(
            "Containerordner: OK"
            if container.path.is_dir()
            else "Containerordner: fehlt"
        )
        checks.append(
            "Firefox-Binary: OK"
            if self._exists_and_executable(container.binary_path)
            else "Firefox-Binary: fehlt oder nicht ausführbar"
        )

        start_script = container.path / "start.sh"
        checks.append(
            "start.sh: OK"
            if start_script.is_file()
            else "start.sh: nicht gefunden"
        )

        launcher = container.path / "launcher.desktop"
        checks.append(
            "launcher.desktop: OK"
            if launcher.is_file()
            else "launcher.desktop: nicht gefunden"
        )

        profile_raw = str(container.profile_path)
        if not profile_raw or profile_raw == ".":
            checks.append("Profil: nicht erkannt")
        elif container.profile_path.is_dir():
            if self._is_internal_profile(container):
                checks.append("Profil: intern im Container")
            elif self._is_external_firefox_profile(container.profile_path):
                checks.append("Profil: extern unter Mozilla-Verzeichnis")
            else:
                checks.append("Profil: externes Verzeichnis")
        else:
            checks.append("Profil: Pfad hinterlegt, aber Verzeichnis fehlt")

        checks.append(
            "user.js: OK"
            if any(container.path.rglob("user.js"))
            else "user.js: nicht gefunden"
        )
        checks.append(
            "policies.json: OK"
            if any(container.path.rglob("policies.json"))
            else "policies.json: nicht gefunden"
        )

        if container.menu_entry_path is None:
            checks.append("Menüeintrag: nicht registriert")
        else:
            checks.append(
                "Menüeintrag: OK"
                if container.menu_entry_path.is_file()
                else "Menüeintrag: Pfad hinterlegt, Datei fehlt"
            )

        if container.icon_path is None:
            checks.append("Icon: nicht hinterlegt")
        else:
            checks.append(
                "Icon: vorhanden"
                if container.icon_path.exists()
                else "Icon: Pfad hinterlegt, Datei oder Ordner fehlt"
            )
        return checks

    def derive_risk_hints(self, container: BrowserContainer) -> list[str]:
        risks: list[str] = []
        start_script = container.path / "start.sh"
        launcher = container.path / "launcher.desktop"

        profile_raw = str(container.profile_path)
        if not profile_raw or profile_raw == ".":
            risks.append("Profilpfad nicht erkannt")
        elif self._is_external_firefox_profile(container.profile_path):
            risks.append("Externes Mozilla-Profil eingebunden")
            if not container.profile_path.is_dir():
                risks.append("Profilpfad zeigt auf fehlendes Verzeichnis")
        elif container.profile_path.is_dir():
            if self._is_external_firefox_profile(container.profile_path):
                risks.append("Externes Mozilla-Profil eingebunden")
            elif not self._is_internal_profile(container):
                risks.append("Profil liegt außerhalb des Containerordners")
        else:
            risks.append("Profilpfad zeigt auf fehlendes Verzeichnis")

        if not start_script.is_file():
            risks.append("start.sh fehlt")
        if not launcher.is_file():
            risks.append("launcher.desktop fehlt")
        if container.menu_entry_path is None:
            risks.append("Menüeintrag fehlt")
        elif not container.menu_entry_path.is_file():
            risks.append("Menüeintrag verweist auf fehlende Datei")
        if not self._exists_and_executable(container.binary_path):
            risks.append("Firefox-Binary fehlt oder ist nicht ausführbar")
        return risks or ["Keine offensichtlichen Risiken erkannt"]

    def _read_preview(self, path: Path) -> str:
        if not path.is_file():
            return "nicht gefunden"
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as exc:
            return f"nicht lesbar: {exc}"
        lines = text.splitlines()
        preview_lines = lines[: self.MAX_PREVIEW_LINES]
        preview = "\n".join(preview_lines).strip()
        if not preview:
            preview = "(leer)"
        if len(lines) > self.MAX_PREVIEW_LINES:
            preview += "\n..."
        return preview

    @staticmethod
    def _parse_desktop_entry(path: Path) -> dict[str, str]:
        if not path.is_file():
            return {}
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            return {}
        data: dict[str, str] = {}
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            data[key.strip()] = value.strip()
        return data

    @staticmethod
    def _parse_exec_target(data: dict[str, str]) -> Path | None:
        command = data.get("Exec", "").strip()
        if not command:
            return None
        tokens = command.split()
        if not tokens:
            return None
        index = 0
        if tokens[0] == "env":
            index = 1
            while index < len(tokens) and "=" in tokens[index]:
                index += 1
        if index >= len(tokens):
            return None
        return Path(tokens[index].strip('"')).expanduser()

    def read_container_artifacts(self, container: BrowserContainer) -> dict[str, str]:
        return {
            "start.sh": self._read_preview(container.path / "start.sh"),
            "launcher.desktop": self._read_preview(container.path / "launcher.desktop"),
        }

    def _get_policy_paths(self, container: BrowserContainer) -> tuple[Path, Path]:
        source_path = container.path / "policies.json"
        runtime_path = container.path / "firefox" / "distribution" / "policies.json"
        return source_path, runtime_path

    def read_policy_json(self, container: BrowserContainer) -> str:
        source_path, runtime_path = self._get_policy_paths(container)
        policy_path = source_path if source_path.is_file() else runtime_path
        if not policy_path.is_file():
            raise FileNotFoundError(f"policies.json nicht gefunden: {source_path}")
        try:
            payload = json.loads(policy_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"policies.json ist ungültig: {exc}") from exc
        return json.dumps(payload, indent=2, ensure_ascii=True) + "\n"

    def save_policy_json(self, container: BrowserContainer, content: str) -> dict[str, str]:
        source_path, runtime_path = self._get_policy_paths(container)
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ungültiges JSON: {exc}") from exc
        if not isinstance(payload, dict):
            raise ValueError("policies.json muss ein JSON-Objekt enthalten.")
        rendered = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = container.path / "backups" / self.POLICY_BACKUP_DIRNAME / stamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_paths: list[Path] = []
        if source_path.exists():
            source_backup = backup_dir / "policies.json"
            shutil.copy2(source_path, source_backup)
            backup_paths.append(source_backup)
        if runtime_path.exists():
            runtime_backup_dir = backup_dir / "firefox-distribution"
            runtime_backup_dir.mkdir(parents=True, exist_ok=True)
            runtime_backup = runtime_backup_dir / "policies.json"
            shutil.copy2(runtime_path, runtime_backup)
            backup_paths.append(runtime_backup)

        source_path.write_text(rendered, encoding="utf-8")
        runtime_path.parent.mkdir(parents=True, exist_ok=True)
        runtime_path.write_text(rendered, encoding="utf-8")
        return {
            "source_path": str(source_path),
            "runtime_path": str(runtime_path),
            "backup_dir": str(backup_dir),
            "backup_count": str(len(backup_paths)),
        }

    def _inspect_associated_menu_entries(
        self,
        container: BrowserContainer,
    ) -> list[dict[str, str]]:
        entry_paths: list[Path] = []
        try:
            module = self._load_tool_module()
            applications_dir = Path(module.DEFAULT_APPLICATIONS_DIR)
        except Exception:
            LOGGER.exception("Secure Browser menu entry discovery failed")
            applications_dir = Path.home() / ".local" / "share" / "applications"
        active_menu_data = (
            self._parse_desktop_entry(container.menu_entry_path)
            if container.menu_entry_path is not None
            else {}
        )
        active_name = active_menu_data.get("Name", "")
        desired_exec = container.path / "start.sh"
        if applications_dir.is_dir():
            for path in applications_dir.glob("*.desktop"):
                data = self._parse_desktop_entry(path)
                exec_target = self._parse_exec_target(data)
                same_exec = exec_target == desired_exec
                same_root = exec_target is not None and exec_target.parent == container.path
                same_name = bool(active_name) and data.get("Name", "") == active_name
                if same_exec or same_root or same_name:
                    entry_paths.append(path)
        if container.menu_entry_path is not None:
            entry_paths.append(container.menu_entry_path)
        unique_paths = sorted({path for path in entry_paths}, key=lambda item: str(item))
        entries: list[dict[str, str]] = []
        for path in unique_paths:
            data = self._parse_desktop_entry(path)
            entries.append(
                {
                    "Datei": path.name,
                    "Pfad": str(path),
                    "Name": data.get("Name", "nicht gesetzt"),
                    "Exec": data.get("Exec", "nicht gesetzt"),
                    "Icon": data.get("Icon", "nicht gesetzt"),
                    "Type": data.get("Type", "nicht gesetzt"),
                    "Categories": data.get("Categories", "nicht gesetzt"),
                    "Status": (
                        "aktiv"
                        if container.menu_entry_path is not None and path == container.menu_entry_path
                        else "zusätzlich"
                    ),
                }
            )
        return entries

    def inspect_launchers(self, container: BrowserContainer) -> dict[str, dict[str, str]]:
        launcher_data = self._parse_desktop_entry(container.path / "launcher.desktop")
        menu_data = (
            self._parse_desktop_entry(container.menu_entry_path)
            if container.menu_entry_path is not None
            else {}
        )
        return {
            "launcher.desktop": {
                "Type": launcher_data.get("Type", "nicht gesetzt"),
                "Name": launcher_data.get("Name", "nicht gesetzt"),
                "Exec": launcher_data.get("Exec", "nicht gesetzt"),
                "Icon": launcher_data.get("Icon", "nicht gesetzt"),
                "Categories": launcher_data.get("Categories", "nicht gesetzt"),
                "StartupNotify": launcher_data.get("StartupNotify", "nicht gesetzt"),
            },
            "menu_entry": {
                "Pfad": (
                    str(container.menu_entry_path)
                    if container.menu_entry_path is not None
                    else "nicht registriert"
                ),
                "Name": menu_data.get("Name", "nicht gesetzt"),
                "Exec": menu_data.get("Exec", "nicht gesetzt"),
                "Icon": menu_data.get("Icon", "nicht gesetzt"),
                "Categories": menu_data.get("Categories", "nicht gesetzt"),
                "Type": menu_data.get("Type", "nicht gesetzt"),
            },
            "menu_entries": self._inspect_associated_menu_entries(container),
        }

    def create_container(self) -> None:
        self._todo("create_container")

    def register_existing(self) -> None:
        self._todo("register_existing")

    def uninstall_container(self) -> None:
        self._todo("uninstall_container")

    def cleanup_menu(self) -> None:
        self._todo("cleanup_menu")

    def backup_container(self) -> None:
        self._todo("backup_container")

    def verify_selected_container(self) -> None:
        self._todo("verify_selected_container")
