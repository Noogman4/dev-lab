#!/usr/bin/env python3
"""Scan and build isolated Firefox standalone containers safely."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

DEFAULT_BASE_DIR = Path("/home/happy/Programme")
DEFAULT_CONFIG_PATH = Path("containers.json")
DEFAULT_INVENTORY_PATH = Path("container_inventory.md")
DEFAULT_APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"
DEFAULT_PROFILE_BASE_DIRS = [
    Path("/home/happy/.config/mozilla/firefox"),
    Path("/home/happy/.mozilla/firefox"),
]
MAX_SCAN_FILE_SIZE = 256 * 1024
MAX_PROFILE_HISTORY_ROWS = 5000
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".cache",
    "node_modules",
}
DOMAIN_PATTERN = re.compile(
    r"(?<![@\w-])(?:https?://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?::\d+)?(?:/|$)"
)
VERSION_PATTERN = re.compile(r"(\d+(?:\.\d+)+)")
PROFILE_MATCH_RULES = {
    "firefox-ProtonMail": ["mail.proton.me", "account.proton.me"],
    "firefox-chatgpt": ["chatgpt.com", "openai.com", "auth.openai.com"],
    "firefox-gmail": ["mail.google.com", "accounts.google.com"],
    "firefox-netflix": ["netflix.com", "nflxvideo.net"],
    "firefox-primevideo": ["primevideo.com", "amazon.de", "amazon.com"],
    "firefox-youtube": ["youtube.com", "googlevideo.com", "ytimg.com"],
}


DEFAULT_CONTAINERS = [
    {
        "name": "firefox-GitHub",
        "allowed_domains": [
            "github.com",
            "githubusercontent.com",
            "githubassets.com",
        ],
    },
    {
        "name": "firefox-OpenAI",
        "allowed_domains": [
            "chatgpt.com",
            "openai.com",
            "platform.openai.com",
            "auth.openai.com",
        ],
    },
    {
        "name": "firefox-NameCom",
        "allowed_domains": [
            "name.com",
            "www.name.com",
        ],
    },
    {
        "name": "firefox-cPanel",
        "allowed_domains": [
            "netmonroots.com",
            "cpanel.netmonroots.com",
            "netmonroots.com:2083",
        ],
    },
]


@dataclass
class DiscoveredContainer:
    name: str
    root_dir: Path
    binary_path: Path
    version: str
    profile_path: Path | None
    start_command: str | None
    domains: list[str]
    purpose: str | None
    risk_hints: list[str]
    correlated_profile_path: Path | None = None
    correlation_reason: str | None = None
    start_script_suggestion: str | None = None
    start_script: Path | None = None
    desktop_files: list[Path] = field(default_factory=list)
    user_js_files: list[Path] = field(default_factory=list)
    policies_files: list[Path] = field(default_factory=list)


@dataclass
class ContainerSpec:
    name: str
    path: Path
    allowed_domains: list[str]
    source_firefox_dir: Path | None
    homepage_url: str | None = None
    new_tab_url: str | None = None
    menu_name: str | None = None
    notes: str | None = None


@dataclass
class FirefoxProfile:
    path: Path
    domains: list[str]
    sources: list[str]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recognize existing Firefox standalone containers, create an "
            "inventory, and prepare new isolated containers."
        )
    )
    parser.add_argument(
        "--base-dir",
        default=str(DEFAULT_BASE_DIR),
        help=f"Base directory to scan and create containers in (default: {DEFAULT_BASE_DIR})",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Container configuration JSON (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--inventory",
        default=str(DEFAULT_INVENTORY_PATH),
        help=(
            f"Markdown inventory output path (default: {DEFAULT_INVENTORY_PATH})"
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply planned changes after showing the dry-run output.",
    )
    parser.add_argument(
        "--only",
        help=(
            "Process only the specified container name for inventory, dry-run, "
            "and --apply."
        ),
    )
    return parser.parse_args(argv)


def ensure_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def is_executable_file(path: Path) -> bool:
    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    return path.is_file() and bool(mode & stat.S_IXUSR)


def iter_candidate_binaries(base_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for current_root, dirnames, filenames in os.walk(base_dir):
        dirnames[:] = [name for name in dirnames if name not in SKIP_DIR_NAMES]
        if "firefox" not in filenames:
            continue
        binary_path = Path(current_root) / "firefox"
        if binary_path.parent.name != "firefox":
            continue
        if is_executable_file(binary_path):
            candidates.append(binary_path)
    return sorted(set(candidates))


def run_firefox_version(binary_path: Path) -> str:
    try:
        result = subprocess.run(
            [str(binary_path), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "unbekannt"
    output = " ".join(part.strip() for part in [result.stdout, result.stderr] if part)
    match = VERSION_PATTERN.search(output)
    return match.group(1) if match else (output.strip() or "unbekannt")


def read_text_if_small(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_SCAN_FILE_SIZE:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def read_places_domains(profile_dir: Path) -> list[str]:
    places_path = profile_dir / "places.sqlite"
    if not places_path.is_file():
        return []
    query = (
        "SELECT url FROM moz_places "
        "WHERE url IS NOT NULL "
        "ORDER BY last_visit_date DESC "
        f"LIMIT {MAX_PROFILE_HISTORY_ROWS}"
    )
    try:
        connection = sqlite3.connect(
            f"file:{places_path}?mode=ro&immutable=1",
            uri=True,
            timeout=2,
        )
    except sqlite3.Error:
        return []
    try:
        cursor = connection.execute(query)
        urls = [row[0] for row in cursor.fetchall() if row and row[0]]
    except sqlite3.Error:
        return []
    finally:
        connection.close()
    return extract_domains_from_text("\n".join(urls))


def search_files(root_dir: Path, filename: str) -> list[Path]:
    return sorted(path for path in root_dir.rglob(filename) if path.is_file())


def detect_profile_path(root_dir: Path, start_script: Path | None) -> Path | None:
    if start_script:
        script_text = read_text_if_small(start_script)
        match = re.search(
            r"--profile\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s]+))",
            script_text,
        )
        if match:
            raw_value = next(group for group in match.groups() if group)
            candidate = (start_script.parent / raw_value).resolve()
            if candidate.exists():
                return candidate
    direct_profile = root_dir / "profile"
    if direct_profile.is_dir():
        return direct_profile
    for candidate in sorted(root_dir.glob("profile*")):
        if candidate.is_dir():
            return candidate
    for candidate in root_dir.rglob("prefs.js"):
        return candidate.parent
    return None


def extract_domains_from_text(text: str) -> list[str]:
    domains: set[str] = set()
    for match in DOMAIN_PATTERN.finditer(text):
        domain = match.group(1).lower().strip(".")
        if domain:
            domains.add(domain)
    return sorted(domains)


def infer_purpose(name: str, domains: list[str]) -> str | None:
    combined = " ".join([name.lower(), *domains])
    if "github" in combined:
        return "GitHub"
    if "openai" in combined or "chatgpt" in combined:
        return "OpenAI"
    if "name.com" in combined:
        return "Name.com"
    if "cpanel" in combined or "2083" in combined:
        return "cPanel"
    return None


def discover_firefox_profiles(base_dirs: list[Path]) -> list[FirefoxProfile]:
    profiles: list[FirefoxProfile] = []
    for base_dir in base_dirs:
        if not base_dir.is_dir():
            continue
        for candidate in sorted(base_dir.iterdir()):
            if not candidate.is_dir():
                continue
            domains: set[str] = set()
            sources: list[str] = []
            history_domains = read_places_domains(candidate)
            if history_domains:
                domains.update(history_domains)
                sources.append("places.sqlite")
            for filename in ["prefs.js", "user.js", "handlers.json"]:
                text = read_text_if_small(candidate / filename)
                matched = extract_domains_from_text(text)
                if matched:
                    domains.update(matched)
                    sources.append(filename)
            if domains:
                profiles.append(
                    FirefoxProfile(
                        path=candidate,
                        domains=sorted(domains),
                        sources=sorted(set(sources)),
                    )
                )
    return profiles


def score_profile_match(profile: FirefoxProfile, expected_domains: list[str]) -> tuple[int, list[str]]:
    matched_domains: list[str] = []
    for expected in expected_domains:
        expected_host = expected.split(":", 1)[0].lower()
        if any(
            domain == expected_host or domain.endswith(f".{expected_host}")
            for domain in profile.domains
        ):
            matched_domains.append(expected)
    return len(matched_domains), matched_domains


def suggest_start_script(container: DiscoveredContainer, profile_path: Path) -> str:
    return (
        "# Nur Vorschlag, nicht automatisch schreiben\n"
        f'cd "{container.root_dir}" && '
        f'./firefox/firefox --no-remote --profile "{profile_path}"'
    )


def detect_start_command(start_script: Path | None) -> str | None:
    if not start_script:
        return None
    script_text = read_text_if_small(start_script)
    for line in script_text.splitlines():
        stripped = line.strip()
        if "firefox" in stripped and not stripped.startswith("#"):
            return stripped
    return f"bash {start_script}"


def build_risk_hints(
    root_dir: Path,
    profile_path: Path | None,
    start_command: str | None,
    user_js_files: list[Path],
    policies_files: list[Path],
    domains: list[str],
) -> list[str]:
    risks: list[str] = []
    if profile_path is None:
        risks.append("Kein Profilordner erkannt.")
    elif str(profile_path).startswith(str(Path.home() / ".mozilla")):
        risks.append("Profil liegt unter ~/.mozilla und sollte nicht veraendert werden.")
    elif str(profile_path).startswith(str(Path.home() / ".config" / "mozilla")):
        risks.append(
            "Profil liegt unter ~/.config/mozilla und sollte nicht veraendert werden."
        )
    if start_command is None:
        risks.append("Kein Startbefehl erkannt.")
    else:
        if "--no-remote" not in start_command:
            risks.append("Startbefehl nutzt kein --no-remote.")
        if "--profile" not in start_command:
            risks.append("Startbefehl nutzt kein explizites --profile.")
    if not user_js_files:
        risks.append("Keine user.js erkannt.")
    if not policies_files:
        risks.append("Keine policies.json erkannt.")
    if not domains:
        risks.append("Keine eindeutigen Domains oder kein Zweck erkennbar.")
    if not (root_dir / "launcher.desktop").exists() and not list(root_dir.glob("*.desktop")):
        risks.append("Keine Desktop-Datei erkannt.")
    return risks


def discover_container(binary_path: Path) -> DiscoveredContainer:
    root_dir = binary_path.parent.parent
    start_script = root_dir / "start.sh"
    if not start_script.exists():
        matches = search_files(root_dir, "start.sh")
        start_script = matches[0] if matches else None
    desktop_files = sorted(root_dir.glob("*.desktop"))
    user_js_files = search_files(root_dir, "user.js")
    policies_files = search_files(root_dir, "policies.json")
    profile_path = detect_profile_path(root_dir, start_script)
    text_sources: list[str] = []
    for path in [start_script, *desktop_files, *user_js_files, *policies_files]:
        if path is not None:
            text_sources.append(read_text_if_small(path))
    domains = sorted(
        {
            domain
            for text in text_sources
            for domain in extract_domains_from_text(text)
        }
    )
    start_command = detect_start_command(start_script)
    purpose = infer_purpose(root_dir.name, domains)
    risks = build_risk_hints(
        root_dir=root_dir,
        profile_path=profile_path,
        start_command=start_command,
        user_js_files=user_js_files,
        policies_files=policies_files,
        domains=domains,
    )
    return DiscoveredContainer(
        name=root_dir.name,
        root_dir=root_dir,
        binary_path=binary_path,
        version=run_firefox_version(binary_path),
        profile_path=profile_path,
        start_command=start_command,
        domains=domains,
        purpose=purpose,
        risk_hints=risks,
        start_script=start_script,
        desktop_files=desktop_files,
        user_js_files=user_js_files,
        policies_files=policies_files,
    )


def discover_existing_containers(base_dir: Path) -> list[DiscoveredContainer]:
    return [discover_container(binary) for binary in iter_candidate_binaries(base_dir)]


def correlate_profiles(
    containers: list[DiscoveredContainer],
    profiles: list[FirefoxProfile],
) -> None:
    for container in containers:
        expected_domains = PROFILE_MATCH_RULES.get(container.name)
        if not expected_domains:
            continue
        scored_matches: list[tuple[int, FirefoxProfile, list[str]]] = []
        for profile in profiles:
            score, matched_domains = score_profile_match(profile, expected_domains)
            if score:
                scored_matches.append((score, profile, matched_domains))
        if not scored_matches:
            container.risk_hints.append(
                "Kein wahrscheinliches Mozilla-Profil ueber Domain-Treffer gefunden."
            )
            continue
        scored_matches.sort(
            key=lambda item: (-item[0], str(item[1].path))
        )
        best_score, best_profile, matched_domains = scored_matches[0]
        container.correlated_profile_path = best_profile.path
        container.correlation_reason = (
            "Domain-Treffer "
            + ", ".join(matched_domains)
            + f" aus {', '.join(best_profile.sources)}"
        )
        if container.start_command is None:
            container.start_script_suggestion = suggest_start_script(
                container, best_profile.path
            )
        if best_score < len(expected_domains):
            container.risk_hints.append(
                "Profilzuordnung ist heuristisch und basiert nur auf Teiltreffern."
            )


def filter_by_only(
    containers: list[DiscoveredContainer],
    specs: list[ContainerSpec],
    only_name: str | None,
) -> tuple[list[DiscoveredContainer], list[ContainerSpec]]:
    if not only_name:
        return containers, specs
    filtered_containers = [
        container for container in containers if container.name == only_name
    ]
    filtered_specs = [spec for spec in specs if spec.name == only_name]
    if not filtered_containers and not filtered_specs:
        raise ValueError(
            f"Unbekannter Containername fuer --only: {only_name}. "
            "Bitte einen vorhandenen oder konfigurierten Containernamen verwenden."
        )
    return filtered_containers, filtered_specs


def make_match_patterns(domain: str) -> list[str]:
    host, _, port = domain.partition(":")
    patterns: list[str] = []
    if port:
        patterns.append(f"https://{host}/*")
        return patterns
    patterns.append(f"*://{host}/*")
    if host.count(".") == 1:
        patterns.append(f"*://*.{host}/*")
    elif host.startswith("www."):
        patterns.append(f"*://{host.removeprefix('www.')}/*")
    return patterns


def get_homepage_url(spec: ContainerSpec) -> str:
    if spec.homepage_url:
        return spec.homepage_url
    host = spec.allowed_domains[0].split(":", 1)[0]
    return f"https://{host}"


def get_new_tab_url(spec: ContainerSpec) -> str:
    return spec.new_tab_url or "about:blank"


def get_menu_filename(spec: ContainerSpec) -> str:
    return f"netmon-secure-browser-{spec.name.lower()}.desktop"


def get_default_menu_name(spec: ContainerSpec) -> str:
    label = spec.name.removeprefix("firefox-")
    display_map = {
        "github": "GitHub",
        "openai": "OpenAI",
        "namecom": "Name.com",
        "cpanel": "cPanel",
    }
    display_label = display_map.get(label.lower(), label)
    return f"NetMon Secure Browser – {display_label}"


def get_menu_name(spec: ContainerSpec) -> str:
    return spec.menu_name or get_default_menu_name(spec)


def get_menu_entry_path(spec: ContainerSpec, applications_dir: Path) -> Path:
    return applications_dir / get_menu_filename(spec)


def get_menu_backup_dir(applications_dir: Path) -> Path:
    return applications_dir / "browser-container-builder-backups"


def get_menu_backup_path(menu_entry_path: Path, applications_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return get_menu_backup_dir(applications_dir) / stamp / menu_entry_path.name


def get_container_icon_path(spec: ContainerSpec) -> Path:
    candidates = [
        spec.path / "firefox" / "browser" / "chrome" / "icons" / "default" / "default128.png",
        spec.path / "firefox" / "browser" / "chrome" / "icons" / "default" / "default64.png",
        spec.path / "firefox" / "browser" / "chrome" / "icons" / "default" / "default32.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_policies_payload(spec: ContainerSpec) -> dict[str, Any]:
    exceptions: list[str] = []
    for domain in spec.allowed_domains:
        for pattern in make_match_patterns(domain):
            if pattern not in exceptions:
                exceptions.append(pattern)
    homepage_url = get_homepage_url(spec)
    return {
        "policies": {
            "DisableTelemetry": True,
            "DisablePocket": True,
            "DisableFirefoxStudies": True,
            "DisableFirefoxAccounts": True,
            "DisableFormHistory": True,
            "DisableProfileImport": True,
            "DisableMasterPasswordCreation": True,
            "OfferToSaveLogins": False,
            "DontCheckDefaultBrowser": True,
            "NoDefaultBookmarks": True,
            "PasswordManagerEnabled": False,
            "Homepage": {
                "URL": homepage_url,
                "Locked": False,
                "StartPage": "homepage",
            },
            "WebsiteFilter": {
                "Block": ["<all_urls>"],
                "Exceptions": exceptions,
            },
        },
        "_builder_metadata": {
            "allowed_domains": spec.allowed_domains,
            "homepage_url": homepage_url,
            "new_tab_url": get_new_tab_url(spec),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
    }


def build_user_js_content(spec: ContainerSpec) -> str:
    homepage_url = get_homepage_url(spec)
    new_tab_url = get_new_tab_url(spec)
    lines = [
        '// Generated by browser_container_builder.py',
        f'// Container: {spec.name}',
        'user_pref("app.normandy.enabled", false);',
        'user_pref("app.shield.optoutstudies.enabled", false);',
        f'user_pref("browser.newtab.url", "{new_tab_url}");',
        f'user_pref("browser.startup.homepage", "{homepage_url}");',
        'user_pref("browser.startup.page", 1);',
        'user_pref("browser.contentblocking.category", "strict");',
        'user_pref("browser.formfill.enable", false);',
        'user_pref("browser.newtabpage.enabled", false);',
        'user_pref("browser.newtabpage.activity-stream.feeds.discoverystreamfeed", false);',
        'user_pref("browser.newtabpage.activity-stream.enabled", false);',
        'user_pref("browser.newtabpage.activity-stream.feeds.section.topstories", false);',
        'user_pref("browser.newtabpage.activity-stream.showSponsoredTopSites", false);',
        'user_pref("browser.newtabpage.activity-stream.showSponsored", false);',
        'user_pref("browser.ping-centre.telemetry", false);',
        'user_pref("browser.search.suggest.enabled", false);',
        'user_pref("browser.tabs.crashReporting.sendReport", false);',
        'user_pref("browser.urlbar.suggest.quicksuggest", false);',
        'user_pref("browser.urlbar.suggest.searches", false);',
        'user_pref("browser.urlbar.trending.featureGate", false);',
        'user_pref("cookiebanners.service.mode", 2);',
        'user_pref("datareporting.healthreport.uploadEnabled", false);',
        'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
        'user_pref("dom.security.https_only_mode", true);',
        'user_pref("extensions.formautofill.addresses.enabled", false);',
        'user_pref("extensions.formautofill.creditCards.enabled", false);',
        'user_pref("extensions.pocket.enabled", false);',
        'user_pref("media.peerconnection.enabled", false);',
        'user_pref("network.cookie.cookieBehavior", 1);',
        'user_pref("network.cookie.lifetimePolicy", 2);',
        'user_pref("network.dns.disablePrefetch", true);',
        'user_pref("network.http.speculative-parallel-limit", 0);',
        'user_pref("network.predictor.enabled", false);',
        'user_pref("network.trr.mode", 5);',
        'user_pref("privacy.clearOnShutdown.cache", true);',
        'user_pref("privacy.clearOnShutdown.cookies", true);',
        'user_pref("privacy.clearOnShutdown.downloads", true);',
        'user_pref("privacy.clearOnShutdown.formdata", true);',
        'user_pref("privacy.clearOnShutdown.history", true);',
        'user_pref("privacy.clearOnShutdown.offlineApps", true);',
        'user_pref("privacy.clearOnShutdown.sessions", true);',
        'user_pref("privacy.sanitize.sanitizeOnShutdown", true);',
        'user_pref("privacy.trackingprotection.enabled", true);',
        'user_pref("privacy.trackingprotection.pbmode.enabled", true);',
        'user_pref("signon.autofillForms", false);',
        'user_pref("signon.rememberSignons", false);',
        'user_pref("toolkit.telemetry.enabled", false);',
    ]
    return "\n".join(lines) + "\n"


def build_start_script() -> str:
    return """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if [ -f "$SCRIPT_DIR/user.js" ]; then
    cp "$SCRIPT_DIR/user.js" "$SCRIPT_DIR/profile/user.js"
fi

if [ -f "$SCRIPT_DIR/policies.json" ]; then
    mkdir -p "$SCRIPT_DIR/firefox/distribution"
    cp "$SCRIPT_DIR/policies.json" "$SCRIPT_DIR/firefox/distribution/policies.json"
fi

exec "$SCRIPT_DIR/firefox/firefox" --no-remote --profile "$SCRIPT_DIR/profile" "$@"
"""


def build_backup_script(spec: ContainerSpec) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
STAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="$SCRIPT_DIR/backups/$STAMP"

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/{spec.name}_profile_backup.tar.gz" -C "$SCRIPT_DIR" \\
    profile user.js policies.json README.md launcher.desktop start.sh

printf 'Backup erstellt: %s\\n' "$BACKUP_DIR/{spec.name}_profile_backup.tar.gz"
"""


def build_container_readme(spec: ContainerSpec) -> str:
    domains = "\n".join(f"- `{domain}`" for domain in spec.allowed_domains)
    homepage_url = get_homepage_url(spec)
    new_tab_url = get_new_tab_url(spec)
    menu_filename = get_menu_filename(spec)
    menu_name = get_menu_name(spec)
    notes = spec.notes or "Keine zusaetzlichen Hinweise."
    return f"""# {spec.name}

Separater Firefox-Standalone-Container mit eigenem Profil und eigener Startlogik.

## Start

```bash
./start.sh
```

## Struktur

- `firefox/`
- `profile/`
- `start.sh`
- `backup.sh`
- `user.js`
- `policies.json`
- `launcher.desktop`

## Erlaubte Domains

{domains}

## Startseite

- Startseite: `{homepage_url}`
- Neue Tabs: `{new_tab_url}`

## Startmenue

- Menue-Name: `{menu_name}`
- Menue-Datei: `{menu_filename}`
- Zielpfad: `~/.local/share/applications/{menu_filename}`

## Hinweise

- Standardstart: `./firefox/firefox --no-remote --profile ./profile`
- `WebsiteFilter` blockiert standardmaessig alle Seiten und erlaubt nur die Ausnahmen aus `policies.json`.
- Port-spezifische Ziele wie `netmonroots.com:2083` koennen von Firefox `WebsiteFilter` nicht exakt nach Port eingeschraenkt werden.
- Cookies werden beim Beenden geloescht.
- Kein Firefox Sync, kein Profilimport, keine automatische Login-Uebernahme.
- Notiz: {notes}
"""


def build_launcher_content(spec: ContainerSpec) -> str:
    absolute_start = spec.path / "start.sh"
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={spec.name}
Comment=Isolierter Firefox-Container fuer {spec.name}
Exec={absolute_start}
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
"""


def build_menu_launcher_content(spec: ContainerSpec) -> str:
    absolute_start = spec.path / "start.sh"
    icon_path = get_container_icon_path(spec)
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={get_menu_name(spec)}
Comment=NetMon Secure Browser fuer {spec.name}
Exec={absolute_start}
Icon={icon_path}
Terminal=false
Categories=Network;Security;
StartupNotify=true
"""


def validate_config_payload(payload: dict[str, Any], base_dir: Path) -> list[ContainerSpec]:
    default_source_raw = payload.get("default_source_firefox_dir")
    default_source = (
        ensure_path(default_source_raw) if isinstance(default_source_raw, str) else None
    )
    raw_containers = payload.get("containers")
    if not isinstance(raw_containers, list) or not raw_containers:
        raise ValueError("Config must contain a non-empty 'containers' list.")
    specs: list[ContainerSpec] = []
    for entry in raw_containers:
        if not isinstance(entry, dict):
            raise ValueError("Each container entry must be an object.")
        name = entry.get("name")
        allowed_domains = entry.get("allowed_domains")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Each container entry requires a non-empty 'name'.")
        if not isinstance(allowed_domains, list) or not all(
            isinstance(item, str) and item.strip() for item in allowed_domains
        ):
            raise ValueError(
                f"Container '{name}' requires a non-empty string list in "
                "'allowed_domains'."
            )
        path_raw = entry.get("path")
        path = ensure_path(path_raw) if isinstance(path_raw, str) else base_dir / name
        source_raw = entry.get("source_firefox_dir")
        source = ensure_path(source_raw) if isinstance(source_raw, str) else default_source
        homepage_url = (
            entry.get("homepage_url")
            if isinstance(entry.get("homepage_url"), str)
            else None
        )
        new_tab_url = (
            entry.get("new_tab_url")
            if isinstance(entry.get("new_tab_url"), str)
            else None
        )
        menu_name = (
            entry.get("menu_name")
            if isinstance(entry.get("menu_name"), str)
            else None
        )
        notes = entry.get("notes") if isinstance(entry.get("notes"), str) else None
        specs.append(
            ContainerSpec(
                name=name,
                path=path,
                allowed_domains=allowed_domains,
                source_firefox_dir=source,
                homepage_url=homepage_url,
                new_tab_url=new_tab_url,
                menu_name=menu_name,
                notes=notes,
            )
        )
    return specs


def load_config(config_path: Path, base_dir: Path) -> list[ContainerSpec]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return validate_config_payload(payload, base_dir)


def select_missing_sources(
    specs: list[ContainerSpec], discovered: list[DiscoveredContainer]
) -> list[str]:
    source_candidates = sorted({container.binary_path.parent for container in discovered})
    problems: list[str] = []
    for spec in specs:
        if spec.source_firefox_dir is not None:
            continue
        if len(source_candidates) == 1:
            spec.source_firefox_dir = source_candidates[0]
            continue
        problems.append(
            f"{spec.name}: source_firefox_dir fehlt und konnte nicht eindeutig "
            "automatisch bestimmt werden."
        )
    return problems


def write_inventory(
    inventory_path: Path,
    base_dir: Path,
    containers: list[DiscoveredContainer],
) -> None:
    lines = [
        "# Firefox Container Inventory",
        "",
        f"- Scan-Basis: `{base_dir}`",
        f"- Erstellt am: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Gefundene Container: `{len(containers)}`",
        "",
    ]
    if not containers:
        lines.extend(
            [
                "Keine Firefox-Standalone-Container mit `firefox/firefox` Binary erkannt.",
                "",
            ]
        )
    for container in containers:
        profile = str(container.profile_path) if container.profile_path else "nicht erkannt"
        correlated_profile = (
            str(container.correlated_profile_path)
            if container.correlated_profile_path
            else "nicht erkannt"
        )
        correlation_reason = container.correlation_reason or "kein Domain-Treffer"
        start_command = container.start_command or "nicht erkannt"
        start_suggestion = container.start_script_suggestion or "kein Vorschlag noetig"
        purpose = container.purpose or "nicht eindeutig"
        domains = ", ".join(container.domains) if container.domains else "keine"
        risks = container.risk_hints or ["Keine offensichtlichen Risiken erkannt."]
        lines.extend(
            [
                f"## {container.name}",
                "",
                f"- Containername: `{container.name}`",
                f"- Pfad zur Binary: `{container.binary_path}`",
                f"- Firefox-Version: `{container.version}`",
                f"- Profilpfad: `{profile}`",
                f"- Profilpfad erkannt: `{correlated_profile}`",
                f"- Zuordnungsgrund: `{correlation_reason}`",
                "- Sicherheit: `keine automatische Aenderung bestehender Container`",
                f"- Startbefehl: `{start_command}`",
                f"- Optionaler start.sh-Vorschlag: `{start_suggestion}`",
                f"- Erkannte Domains/Zweck: `{domains}` / `{purpose}`",
                "- Risiko-Hinweise:",
                *[f"  - {risk}" for risk in risks],
                "",
            ]
        )
    inventory_path.write_text("\n".join(lines), encoding="utf-8")


def build_apply_plan(
    specs: list[ContainerSpec],
    discovered: list[DiscoveredContainer],
    applications_dir: Path,
) -> list[str]:
    existing_paths = {container.root_dir.resolve() for container in discovered}
    lines = ["Dry-Run Plan", ""]
    for spec in specs:
        target = spec.path.resolve()
        source = str(spec.source_firefox_dir) if spec.source_firefox_dir else "UNGESETZT"
        menu_entry_path = get_menu_entry_path(spec, applications_dir)
        if menu_entry_path.exists():
            menu_status = (
                "Backup und Ueberschreiben des bestehenden Menueeintrags vorgesehen"
            )
        else:
            menu_status = "Neuer Menueeintrag wird erstellt"
        if target.exists() or target in existing_paths:
            status = "ABBRUCH: Zielordner existiert bereits"
        else:
            status = "OK: Zielordner frei"
        lines.extend(
            [
                f"- {spec.name}",
                f"  Ziel: {target}",
                f"  Firefox-Quelle: {source}",
                f"  Domains: {', '.join(spec.allowed_domains)}",
                f"  Menueeintrag: {menu_entry_path}",
                f"  Menue-Name: {get_menu_name(spec)}",
                f"  Menue-Status: {menu_status}",
                f"  Status: {status}",
            ]
        )
    return lines


def ensure_apply_safe(specs: list[ContainerSpec]) -> None:
    conflicts = [str(spec.path) for spec in specs if spec.path.exists()]
    if conflicts:
        raise RuntimeError(
            "Abbruch wegen bestehender Zielordner:\n- " + "\n- ".join(conflicts)
        )
    missing_sources = [
        f"{spec.name}: {spec.source_firefox_dir}"
        for spec in specs
        if spec.source_firefox_dir is None or not spec.source_firefox_dir.is_dir()
    ]
    if missing_sources:
        raise RuntimeError(
            "Abbruch wegen fehlender oder ungueltiger Firefox-Quellen:\n- "
            + "\n- ".join(missing_sources)
        )


def create_builder_backup(
    base_dir: Path,
    inventory_path: Path,
    specs: list[ContainerSpec],
    dry_run_lines: list[str],
) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = base_dir / "browser-container-builder-backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "inventory_path": str(inventory_path),
        "targets": [str(spec.path) for spec in specs],
    }
    (backup_dir / "plan.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (backup_dir / "dry_run.txt").write_text(
        "\n".join(dry_run_lines) + "\n", encoding="utf-8"
    )
    if inventory_path.exists():
        shutil.copy2(inventory_path, backup_dir / inventory_path.name)
    tar_path = backup_dir / "pre_apply_snapshot.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for path in [backup_dir / "plan.json", backup_dir / "dry_run.txt"]:
            tar.add(path, arcname=path.name)
        if inventory_path.exists():
            tar.add(backup_dir / inventory_path.name, arcname=inventory_path.name)
    return backup_dir


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, content: str, executable: bool = False) -> None:
    path.write_text(content, encoding="utf-8")
    if executable:
        current_mode = path.stat().st_mode
        path.chmod(current_mode | stat.S_IXUSR)


def backup_menu_entry(menu_entry_path: Path, applications_dir: Path) -> Path:
    backup_path = get_menu_backup_path(menu_entry_path, applications_dir)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(menu_entry_path, backup_path)
    return backup_path


def install_menu_entry(spec: ContainerSpec, applications_dir: Path) -> Path:
    applications_dir.mkdir(parents=True, exist_ok=True)
    menu_entry_path = get_menu_entry_path(spec, applications_dir)
    if menu_entry_path.exists():
        backup_menu_entry(menu_entry_path, applications_dir)
    write_text(menu_entry_path, build_menu_launcher_content(spec))
    return menu_entry_path


def create_container(spec: ContainerSpec, applications_dir: Path) -> Path:
    spec.path.mkdir(parents=True, exist_ok=False)
    firefox_target = spec.path / "firefox"
    shutil.copytree(spec.source_firefox_dir, firefox_target, symlinks=True)
    (spec.path / "profile").mkdir()
    policies_payload = build_policies_payload(spec)
    write_json(spec.path / "policies.json", policies_payload)
    distribution_dir = firefox_target / "distribution"
    distribution_dir.mkdir(parents=True, exist_ok=True)
    write_json(distribution_dir / "policies.json", policies_payload)
    user_js_content = build_user_js_content(spec)
    write_text(spec.path / "user.js", user_js_content)
    write_text(spec.path / "profile" / "user.js", user_js_content)
    write_text(spec.path / "start.sh", build_start_script(), executable=True)
    write_text(spec.path / "backup.sh", build_backup_script(spec), executable=True)
    write_text(spec.path / "README.md", build_container_readme(spec))
    write_text(spec.path / "launcher.desktop", build_launcher_content(spec))
    return install_menu_entry(spec, applications_dir)


def main(argv: list[str] | None = None, applications_dir: Path | None = None) -> int:
    args = parse_args(argv)
    base_dir = ensure_path(args.base_dir)
    config_path = ensure_path(args.config)
    inventory_path = ensure_path(args.inventory)
    effective_applications_dir = applications_dir or DEFAULT_APPLICATIONS_DIR

    if not base_dir.is_dir():
        print(f"Base directory not found: {base_dir}", file=sys.stderr)
        return 1
    if not config_path.is_file():
        print(f"Config file not found: {config_path}", file=sys.stderr)
        return 1

    discovered = discover_existing_containers(base_dir)
    profiles = discover_firefox_profiles(DEFAULT_PROFILE_BASE_DIRS)
    correlate_profiles(discovered, profiles)
    specs = load_config(config_path, base_dir)
    try:
        discovered, specs = filter_by_only(discovered, specs, args.only)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    write_inventory(inventory_path, base_dir, discovered)
    source_problems = select_missing_sources(specs, discovered)
    dry_run_lines = build_apply_plan(specs, discovered, effective_applications_dir)

    print("\n".join(dry_run_lines))
    print("")
    print(f"Inventory written to: {inventory_path}")
    if source_problems:
        print("Quellwarnungen:")
        for problem in source_problems:
            print(f"- {problem}")
    if not args.apply:
        print("")
        print("Keine Aenderungen ausgefuehrt. Fuer echte Erstellung mit --apply starten.")
        return 0

    try:
        ensure_apply_safe(specs)
        backup_dir = create_builder_backup(base_dir, inventory_path, specs, dry_run_lines)
        for spec in specs:
            create_container(spec, effective_applications_dir)
    except Exception as exc:  # pragma: no cover - surfaced to the user
        print(str(exc), file=sys.stderr)
        return 1

    print("")
    print(f"Backup angelegt unter: {backup_dir}")
    print("Container wurden erstellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
