#!/usr/bin/env python3
"""Scan and build isolated Firefox standalone containers safely."""

from __future__ import annotations

import argparse
import configparser
import json
import os
import re
import shlex
import shutil
import sqlite3
import stat
import sys
import tarfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin, urlparse

# Support the standalone CLI and the installed /usr/lib/netmon/tools layout.
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from netmon.core import icon_http
from netmon.core.icon_payload import sanitize_icon


def get_default_base_dir() -> Path:
    documents_dir = (os.environ.get("XDG_DOCUMENTS_DIR") or "").strip()
    if documents_dir:
        documents_root = Path(os.path.expanduser(documents_dir))
    else:
        documents_root = next(
            (
                path
                for path in (Path.home() / "Documents", Path.home() / "Dokumente")
                if path.is_dir()
            ),
            Path.home() / "Documents",
        )
    return documents_root / "NetMon" / "Secure Browser"


DEFAULT_BASE_DIR = get_default_base_dir()
DEFAULT_CONFIG_PATH = Path("containers.json")
DEFAULT_INVENTORY_PATH = Path("container_inventory.md")
DEFAULT_APPLICATIONS_DIR = Path.home() / ".local" / "share" / "applications"
DEFAULT_UNINSTALLED_DIRNAME = "browser-container-builder-uninstalled"
FIREFOX_BASE_DIRNAME = "firefox-base"
DEFAULT_PROFILE_BASE_DIRS = [
    Path.home() / ".config" / "mozilla" / "firefox",
    Path.home() / ".mozilla" / "firefox",
]
MAX_SCAN_FILE_SIZE = 256 * 1024
MAX_VERSION_FILE_SIZE = 64 * 1024
MAX_SCAN_ENTRIES = 100_000
MAX_SCAN_DEPTH = 32
MAX_SCAN_CONTAINERS = 256
MAX_SCAN_TEXT_BYTES = 16 * 1024 * 1024
MAX_PROFILE_HISTORY_ROWS = 5000
CONTAINER_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
DEFAULT_ICON_MODE = "favicon"
DEFAULT_THEME_ICON = "firefox"
WEBSITE_FILTER_BLOCK_PATTERN = "<all_urls>"
FAVICON_TIMEOUT_SECONDS = 10
FAVICON_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}
SKIP_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".cache",
    "node_modules",
    DEFAULT_UNINSTALLED_DIRNAME,
}
ARTIFACT_SKIP_DIR_NAMES = {
    "backups",
    "browser-container-builder-backups",
    DEFAULT_UNINSTALLED_DIRNAME,
}
DOMAIN_PATTERN = re.compile(
    r"(?<![@\w-])(?:https?://)?([A-Za-z0-9.-]+\.[A-Za-z]{2,})(?::\d+)?(?:/|$)"
)
VERSION_PATTERN = re.compile(r"[0-9]{1,3}(?:\.[0-9]{1,3}){1,3}(?:[ab][0-9]{1,3}|esr)?")
HOMEPAGE_PREF_PATTERN = re.compile(r'browser\.startup\.homepage"\s*,\s*"([^"]+)"')
PROFILE_MATCH_RULES = {
    "firefox-ProtonMail": ["mail.proton.me", "account.proton.me"],
    "firefox-chatgpt": [
        "chatgpt.com",
        "openai.com",
        "auth.openai.com",
        "oaistatic.com",
        "oaiusercontent.com",
    ],
    "firefox-gmail": ["mail.google.com", "accounts.google.com"],
    "firefox-netflix": ["netflix.com", "nflxvideo.net"],
    "firefox-primevideo": ["primevideo.com", "amazon.de", "amazon.com"],
    "firefox-youtube": ["youtube.com", "googlevideo.com", "ytimg.com"],
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
REGISTER_EXISTING_MENU_NAMES = {
    "firefox-GitHub": "GitHub",
    "firefox-OpenAI": "OpenAI",
    "firefox-NameCom": "Name.com",
    "firefox-cPanel": "cPanel",
    "firefox-Amazon": "Amazon",
    "firefox-Netflix": "Netflix",
    "firefox-SparkasseUlm": "Sparkasse Ulm",
    "firefox-ProtonMail": "ProtonMail",
    "firefox-netflix": "Netflix",
    "firefox-primevideo": "Prime Video",
    "firefox-youtube": "YouTube",
    "firefox-gmail": "Gmail",
    "firefox-chatgpt": "ChatGPT",
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
            "oaistatic.com",
            "oaiusercontent.com",
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
    {
        "name": "firefox-Amazon",
        "allowed_domains": [
            "amazon.de",
            "amazon.com",
            "media-amazon.com",
            "ssl-images-amazon.com",
        ],
    },
    {
        "name": "firefox-Netflix",
        "allowed_domains": [
            "netflix.com",
            "nflxvideo.net",
            "nflximg.net",
        ],
    },
    {
        "name": "firefox-SparkasseUlm",
        "allowed_domains": [
            "sparkasse-ulm.de",
            "www.sparkasse-ulm.de",
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
    launcher_path: Path | None = None


@dataclass
class ContainerSpec:
    name: str
    path: Path
    allowed_domains: list[str]
    source_firefox_dir: Path | None
    homepage_url: str | None = None
    new_tab_url: str | None = None
    menu_name: str | None = None
    icon_mode: str | None = None
    custom_icon_path: Path | None = None
    notes: str | None = None
    security_profile: str | None = None
    allow_password_manager: bool | None = None
    keep_cookies: bool | None = None
    enable_website_filter: bool | None = None
    child_lock: dict[str, Any] | None = None


@dataclass
class FirefoxProfile:
    path: Path
    domains: list[str]
    sources: list[str]


@dataclass
class IconPlan:
    mode: str
    source_domain: str | None
    attempt_url: str | None
    storage_path: Path
    fallback_path: Path


@dataclass
class MenuEntryInfo:
    path: Path
    exec_target: Path | None
    container_root: Path | None
    container_name: str | None
    is_orphan: bool


class IconLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self.manifests: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attrs_dict = {key.lower(): value or "" for key, value in attrs}
        rel = attrs_dict.get("rel", "").lower()
        href = attrs_dict.get("href", "")
        if not href or len(href) > 4096:
            return
        rel_tokens = {token for token in rel.split() if token}
        if "icon" in rel_tokens or "apple-touch-icon" in rel_tokens:
            if len(self.links) < icon_http.MAX_METADATA_LINKS:
                self.links.append((rel, href))
        elif "manifest" in rel_tokens:
            if len(self.manifests) < icon_http.MAX_METADATA_LINKS:
                self.manifests.append(href)


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
        help=(f"Markdown inventory output path (default: {DEFAULT_INVENTORY_PATH})"),
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
    parser.add_argument(
        "--register-existing",
        action="store_true",
        help=(
            "Register existing standalone Firefox containers in the user menu "
            "without changing profiles, user.js, or policies.json."
        ),
    )
    parser.add_argument(
        "--refresh-existing",
        action="store_true",
        help=(
            "Refresh start.sh, launcher.desktop, menu entry, and icon for existing "
            "containers without changing profiles, user.js, or policies.json."
        ),
    )
    parser.add_argument(
        "--repair-policy",
        action="store_true",
        help=(
            "Repair policies.json and user.js for existing containers using the "
            "current domain/subdomain rules without changing profile data, "
            "binary, launcher, or menu entry."
        ),
    )
    parser.add_argument(
        "--cleanup-menu",
        action="store_true",
        help="Inspect or clean duplicate/orphaned netmon-secure-browser menu entries.",
    )
    parser.add_argument(
        "--list-installed",
        action="store_true",
        help="List discovered containers, launchers, menu entries, and profile status.",
    )
    parser.add_argument(
        "--uninstall",
        metavar="CONTAINERNAME",
        help="Safely uninstall a single managed container after a dry-run.",
    )
    return parser.parse_args(argv)


def ensure_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


@contextmanager
def open_scan_directory(path: Path):
    """Anchor every path component without following links (POSIX only)."""
    if not all(
        hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_DIRECTORY", "O_NONBLOCK")
    ):
        raise OSError("Safe passive file access is unavailable on this platform.")
    absolute = Path(os.path.abspath(path))
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_NONBLOCK
    traverse_flags = flags | getattr(os, "O_PATH", 0)
    descriptor = os.open(absolute.anchor, traverse_flags)
    try:
        for part in absolute.parts[1:]:
            child = os.open(part, traverse_flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(".", flags, dir_fd=descriptor)
        os.close(descriptor)
        descriptor = child
        yield descriptor
    finally:
        os.close(descriptor)


def read_small_regular_bytes(path: Path, limit: int) -> bytes | None:
    """Read at most limit+1 bytes; never follow links or block on a FIFO."""
    try:
        with open_scan_directory(path.parent) as parent:
            before = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                return None
            descriptor = os.open(
                path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent
            )
            with os.fdopen(descriptor, "rb") as handle:
                opened = os.fstat(handle.fileno())
                if (
                    not stat.S_ISREG(opened.st_mode)
                    or opened.st_size > limit
                    or (before.st_dev, before.st_ino) != (opened.st_dev, opened.st_ino)
                ):
                    return None
                content = handle.read(limit + 1)
                after = os.fstat(handle.fileno())
                if len(content) > limit or (
                    opened.st_size,
                    opened.st_mtime_ns,
                    opened.st_ctime_ns,
                ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    return None
                return content
    except (OSError, ValueError):
        return None


@dataclass
class ScanBudget:
    entries: int = 0
    text_bytes: int = 0

    def count(self):
        self.entries += 1
        if self.entries > MAX_SCAN_ENTRIES:
            raise ValueError(
                "Passive inventory entry budget exceeded; scan incomplete."
            )

    def count_text(self, content: bytes):
        self.text_bytes += len(content)
        if self.text_bytes > MAX_SCAN_TEXT_BYTES:
            raise ValueError("Passive inventory text budget exceeded; scan incomplete.")


def iter_scan_entries(
    root: Path, *, recursive=True, skip_names=(), skip_firefox_base=False, budget=None
):
    """Stream regular files/directories with bounded work and no symlink traversal."""
    budget = budget if budget is not None else ScanBudget()
    pending = [(root, 0)]
    while pending:
        directory, depth = pending.pop()
        try:
            with (
                open_scan_directory(directory) as descriptor,
                os.scandir(descriptor) as entries,
            ):
                for entry in entries:
                    budget.count()
                    if entry.name in skip_names or (
                        skip_firefox_base and is_firefox_base_dir_name(entry.name)
                    ):
                        continue
                    mode = entry.stat(follow_symlinks=False).st_mode
                    path = directory / entry.name
                    if stat.S_ISDIR(mode):
                        yield path, True
                        if recursive:
                            if depth >= MAX_SCAN_DEPTH:
                                raise ValueError(
                                    "Passive inventory depth budget exceeded; scan incomplete."
                                )
                            pending.append((path, depth + 1))
                    elif stat.S_ISREG(mode):
                        yield path, False
        except OSError:
            continue


def is_executable_file(path: Path) -> bool:
    try:
        mode = path.lstat().st_mode
    except OSError:
        return False
    return stat.S_ISREG(mode) and bool(mode & stat.S_IXUSR)


def is_firefox_base_dir_name(name: str) -> bool:
    normalized = re.sub(r"[-_.\s]+", "", str(name or "").strip().lower())
    return normalized == FIREFOX_BASE_DIRNAME.replace("-", "")


def iter_candidate_binaries(base_dir: Path, budget=None) -> list[Path]:
    candidates: list[Path] = []
    for path, directory in iter_scan_entries(
        base_dir, skip_names=SKIP_DIR_NAMES, skip_firefox_base=True, budget=budget
    ):
        if (
            not directory
            and path.name == "firefox"
            and path.parent.name == "firefox"
            and is_executable_file(path)
        ):
            if len(candidates) >= MAX_SCAN_CONTAINERS:
                raise ValueError(
                    "Passive inventory container budget exceeded; scan incomplete."
                )
            candidates.append(path)
    return sorted(candidates)


def read_firefox_version(binary_path: Path) -> str:
    """Display untrusted Firefox metadata; never execute a discovered program."""
    if (
        binary_path.name != "firefox"
        or binary_path.parent.name != "firefox"
        or not is_executable_file(binary_path)
    ):
        return "unbekannt"
    content = read_small_regular_bytes(
        binary_path.parent / "application.ini", MAX_VERSION_FILE_SIZE
    )
    if content is None:
        return "unbekannt"
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        parser.read_string(content.decode("utf-8"))
        if parser.defaults() or parser.get("App", "Name") != "Firefox":
            return "unbekannt"
        if parser.get("App", "Vendor", fallback="Mozilla") != "Mozilla":
            return "unbekannt"
        version = parser.get("App", "Version")
    except (configparser.Error, UnicodeError, ValueError):
        return "unbekannt"
    return (
        version
        if len(version) <= 32 and VERSION_PATTERN.fullmatch(version)
        else "unbekannt"
    )


def read_text_if_small(path: Path, *, budget=None) -> str:
    content = read_small_regular_bytes(path, MAX_SCAN_FILE_SIZE)
    if content is not None and budget is not None:
        budget.count_text(content)
    return content.decode("utf-8", errors="ignore") if content is not None else ""


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


def search_files(root_dir: Path, filename: str, *, budget=None) -> list[Path]:
    return sorted(
        path
        for path, directory in iter_scan_entries(
            root_dir, skip_names=ARTIFACT_SKIP_DIR_NAMES, budget=budget
        )
        if not directory and path.name == filename
    )


def detect_profile_path(
    root_dir: Path, start_script: Path | None, *, budget=None
) -> Path | None:
    if start_script:
        script_text = read_text_if_small(start_script)
        match = re.search(
            r"--profile\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s]+))",
            script_text,
        )
        if match:
            raw_value = next(group for group in match.groups() if group)
            try:
                candidate = (start_script.parent / raw_value).resolve()
                if candidate.is_dir():
                    return candidate
            except (OSError, RuntimeError):
                pass
    direct_profile = root_dir / "profile"
    if direct_profile.is_dir():
        return direct_profile
    for candidate, directory in sorted(
        iter_scan_entries(root_dir, recursive=False, budget=budget)
    ):
        if directory and candidate.name.startswith("profile"):
            return candidate
    for candidate in search_files(root_dir, "prefs.js", budget=budget):
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
        for candidate, directory in sorted(
            iter_scan_entries(base_dir, recursive=False)
        ):
            if not directory:
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


def score_profile_match(
    profile: FirefoxProfile, expected_domains: list[str]
) -> tuple[int, list[str]]:
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


def get_effective_profile_path(container: DiscoveredContainer) -> Path | None:
    return container.profile_path or container.correlated_profile_path


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
        risks.append(
            "Profil liegt unter ~/.mozilla und sollte nicht veraendert werden."
        )
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
    if not (root_dir / "launcher.desktop").exists() and not list(
        root_dir.glob("*.desktop")
    ):
        risks.append("Keine Desktop-Datei erkannt.")
    return risks


def discover_container(binary_path: Path, *, budget=None) -> DiscoveredContainer:
    budget = budget if budget is not None else ScanBudget()
    root_dir = binary_path.parent.parent
    artifacts = sorted(
        path
        for path, directory in iter_scan_entries(
            root_dir, skip_names=ARTIFACT_SKIP_DIR_NAMES, budget=budget
        )
        if not directory
    )
    start_script = root_dir / "start.sh"
    if start_script not in artifacts:
        matches = [path for path in artifacts if path.name == "start.sh"]
        start_script = matches[0] if matches else None
    desktop_files = [
        path
        for path in artifacts
        if path.parent == root_dir and path.suffix == ".desktop"
    ]
    user_js_files = [path for path in artifacts if path.name == "user.js"]
    policies_files = [path for path in artifacts if path.name == "policies.json"]
    profile_path = detect_profile_path(root_dir, start_script, budget=budget)
    text_sources: list[str] = []
    for path in [start_script, *desktop_files, *user_js_files, *policies_files]:
        if path is not None:
            text_sources.append(read_text_if_small(path, budget=budget))
    domains = sorted(
        {domain for text in text_sources for domain in extract_domains_from_text(text)}
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
        version=read_firefox_version(binary_path),
        profile_path=profile_path,
        start_command=start_command,
        domains=domains,
        purpose=purpose,
        risk_hints=risks,
        start_script=start_script,
        desktop_files=desktop_files,
        user_js_files=user_js_files,
        policies_files=policies_files,
        launcher_path=desktop_files[0] if desktop_files else None,
    )


def discover_existing_containers(base_dir: Path) -> list[DiscoveredContainer]:
    budget = ScanBudget()
    return [
        discover_container(binary, budget=budget)
        for binary in iter_candidate_binaries(base_dir, budget=budget)
    ]


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
        scored_matches.sort(key=lambda item: (-item[0], str(item[1].path)))
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


def get_register_existing_candidates(
    containers: list[DiscoveredContainer],
) -> list[DiscoveredContainer]:
    return list(containers)


def normalize_container_key(name: str) -> str:
    normalized = name.lower().removeprefix("firefox-")
    return re.sub(r"[^a-z0-9]+", "", normalized)


def normalize_allowed_domain(value: str) -> str | None:
    raw = value.strip()
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


def normalize_allowed_domains(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        cleaned = normalize_allowed_domain(value)
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def get_known_container_defaults(
    container_name: str,
    *,
    purpose: str | None = None,
    domains: list[str] | None = None,
) -> dict[str, Any] | None:
    target_keys = [normalize_container_key(container_name)]
    if purpose:
        purpose_key = normalize_container_key(purpose)
        if purpose_key and purpose_key not in target_keys:
            target_keys.append(purpose_key)
    normalized_domains = normalize_allowed_domains(domains or [])
    for item in DEFAULT_CONTAINERS:
        name = item.get("name")
        if not isinstance(name, str):
            continue
        item_key = normalize_container_key(name)
        if item_key in target_keys:
            return dict(item)
        item_domains = normalize_allowed_domains(
            [
                value
                for value in item.get("allowed_domains", [])
                if isinstance(value, str)
            ]
        )
        if normalized_domains and any(
            domain in item_domains for domain in normalized_domains
        ):
            return dict(item)
        if normalized_domains:
            derived_domains = []
            for domain in normalized_domains:
                host = domain.split(":", 1)[0].removeprefix("www.")
                parts = [part for part in host.split(".") if part]
                if len(parts) > 2 and parts[0] in LOGIN_SUBDOMAIN_PREFIXES:
                    derived_domains.append(".".join(parts[1:]))
            if derived_domains and any(
                domain in item_domains or f"www.{domain}" in item_domains
                for domain in derived_domains
            ):
                return dict(item)
    return None


def make_match_patterns(domain: str) -> list[str]:
    normalized_domain = normalize_allowed_domain(domain)
    if normalized_domain is None:
        return []
    host, _, port = normalized_domain.partition(":")
    patterns: list[str] = []
    if port:
        patterns.append(f"https://{host}/*")
        return patterns
    patterns.append(f"*://{host}/*")
    base_host = host.removeprefix("www.")
    if host.startswith("www.") and base_host:
        patterns.append(f"*://{base_host}/*")
    elif "." in host:
        patterns.append(f"*://www.{host}/*")
    wildcard_host = base_host or host
    if "." in wildcard_host:
        patterns.append(f"*://*.{wildcard_host}/*")
    return patterns


def resolve_security_profile(spec: ContainerSpec) -> dict[str, object]:
    profile = (spec.security_profile or "standard").strip().lower()
    defaults = {
        "compatible": {
            "allow_password_manager": True,
            "keep_cookies": True,
            "enable_website_filter": False,
        },
        "standard": {
            "allow_password_manager": True,
            "keep_cookies": True,
            "enable_website_filter": True,
        },
        "strict": {
            "allow_password_manager": False,
            "keep_cookies": False,
            "enable_website_filter": True,
        },
        "custom": {
            "allow_password_manager": True,
            "keep_cookies": True,
            "enable_website_filter": True,
        },
    }
    if profile not in defaults:
        profile = "standard"
    resolved = dict(defaults[profile])
    if spec.allow_password_manager is not None:
        resolved["allow_password_manager"] = spec.allow_password_manager
        if profile != "custom":
            profile = "custom"
    if spec.keep_cookies is not None:
        resolved["keep_cookies"] = spec.keep_cookies
        if profile != "custom":
            profile = "custom"
    if spec.enable_website_filter is not None:
        resolved["enable_website_filter"] = spec.enable_website_filter
        if profile != "custom":
            profile = "custom"
    resolved["security_profile"] = profile
    return resolved


def get_homepage_url(spec: ContainerSpec) -> str:
    if spec.homepage_url:
        return spec.homepage_url
    host = spec.allowed_domains[0].split(":", 1)[0]
    return f"https://{host}"


def get_new_tab_url(spec: ContainerSpec) -> str:
    return spec.new_tab_url or "about:blank"


def get_icon_mode(spec: ContainerSpec) -> str:
    return spec.icon_mode or DEFAULT_ICON_MODE


def get_icon_storage_dir(spec: ContainerSpec) -> Path:
    return spec.path / "icons"


def get_icon_storage_path(spec: ContainerSpec, suffix: str = ".png") -> Path:
    return get_icon_storage_dir(spec) / f"favicon{suffix}"


def get_icon_source_domain(spec: ContainerSpec) -> str | None:
    homepage_url = spec.homepage_url or (
        f"https://{spec.allowed_domains[0]}" if spec.allowed_domains else None
    )
    if homepage_url:
        hostname = urlparse(homepage_url).hostname
        if hostname:
            return hostname
    if spec.allowed_domains:
        return spec.allowed_domains[0].split(":", 1)[0]
    return None


def get_fallback_icon_path(spec: ContainerSpec) -> Path:
    if spec.custom_icon_path is not None:
        return spec.custom_icon_path
    return get_container_icon_path(spec)


def get_existing_icon_reference(
    spec: ContainerSpec,
    *,
    raster_only: bool = False,
) -> Path | None:
    suffixes = (".png", ".ico") if raster_only else (".png", ".ico", ".svg")
    icon_dir = get_icon_storage_dir(spec)
    for suffix in suffixes:
        candidate = icon_dir / f"favicon{suffix}"
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def get_fallback_icon_reference(spec: ContainerSpec) -> str:
    if spec.custom_icon_path is not None and spec.custom_icon_path.exists():
        return str(spec.custom_icon_path)
    existing_icon = get_existing_icon_reference(spec)
    if existing_icon is not None:
        return str(existing_icon)
    return DEFAULT_THEME_ICON


def build_icon_plan(spec: ContainerSpec) -> IconPlan:
    mode = get_icon_mode(spec)
    source_domain = get_icon_source_domain(spec)
    attempt_url = (
        f"https://{source_domain}/favicon.ico"
        if mode == "favicon" and source_domain
        else None
    )
    suffix = (
        spec.custom_icon_path.suffix
        if mode == "custom" and spec.custom_icon_path
        else ".png"
    )
    return IconPlan(
        mode=mode,
        source_domain=source_domain,
        attempt_url=attempt_url,
        storage_path=get_icon_storage_path(spec, suffix=suffix or ".png"),
        fallback_path=get_container_icon_path(spec),
    )


def get_menu_filename(spec: ContainerSpec) -> str:
    return f"netmon-secure-browser-{spec.name.lower()}.desktop"


def get_wm_class_name(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(name or "").strip().lower())
    slug = slug.strip(".-") or "browser"
    return f"netmon-secure-browser-{slug}"


def get_spec_wm_class(spec: ContainerSpec) -> str:
    return get_wm_class_name(spec.name)


def get_container_wm_class(container: DiscoveredContainer) -> str:
    return get_wm_class_name(container.name)


def get_default_menu_name(spec: ContainerSpec) -> str:
    label = spec.name.removeprefix("firefox-")
    display_map = {
        "amazon": "Amazon",
        "chatgpt": "ChatGPT",
        "cpanel": "cPanel",
        "github": "GitHub",
        "netflix": "Netflix",
        "sparkasseulm": "Sparkasse Ulm",
        "openai": "OpenAI",
        "namecom": "Name.com",
    }
    display_label = display_map.get(label.lower(), label)
    return display_label


def get_menu_name(spec: ContainerSpec) -> str:
    return spec.menu_name or get_default_menu_name(spec)


def get_menu_entry_path(spec: ContainerSpec, applications_dir: Path) -> Path:
    return applications_dir / get_menu_filename(spec)


def get_uninstall_base_dir(base_dir: Path) -> Path:
    state_home = (os.environ.get("XDG_STATE_HOME") or "").strip()
    if state_home:
        state_root = Path(os.path.expanduser(state_home))
    else:
        state_root = Path.home() / ".local" / "state"
    return state_root / "netmon" / DEFAULT_UNINSTALLED_DIRNAME


def get_container_icon_path(spec: ContainerSpec) -> Path:
    candidates = [
        spec.path
        / "firefox"
        / "browser"
        / "chrome"
        / "icons"
        / "default"
        / "default128.png",
        spec.path
        / "firefox"
        / "browser"
        / "chrome"
        / "icons"
        / "default"
        / "default64.png",
        spec.path
        / "firefox"
        / "browser"
        / "chrome"
        / "icons"
        / "default"
        / "default32.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def guess_icon_suffix(content_type: str | None, url: str) -> str:
    lowered = (content_type or "").lower()
    if "image/png" in lowered:
        return ".png"
    if "image/svg" in lowered:
        return ".svg"
    if "image/x-icon" in lowered or "image/vnd.microsoft.icon" in lowered:
        return ".ico"
    if "image/" in lowered:
        return "." + lowered.split("image/", 1)[1].split(";")[0]
    suffix = Path(urlparse(url).path).suffix.lower()
    return suffix if suffix in {".png", ".svg", ".ico"} else ".ico"


def detect_icon_payload_suffix(
    payload: bytes,
    content_type: str | None,
    url: str,
) -> str | None:
    if payload.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if payload.startswith(b"\x00\x00\x01\x00"):
        return ".ico"
    lowered = (content_type or "").lower()
    if "svg" in lowered or url.lower().endswith(".svg"):
        try:
            snippet = payload[:512].decode("utf-8", errors="ignore").lower()
        except Exception:
            return None
        if "<svg" in snippet:
            return ".svg"
    return None


def extract_png_from_ico(payload: bytes) -> bytes | None:
    if len(payload) < 22 or not payload.startswith(b"\x00\x00\x01\x00"):
        return None
    image_count = int.from_bytes(payload[4:6], "little")
    if image_count < 1:
        return None
    for index in range(image_count):
        entry_offset = 6 + (index * 16)
        if len(payload) < entry_offset + 16:
            return None
        image_size = int.from_bytes(
            payload[entry_offset + 8 : entry_offset + 12], "little"
        )
        image_offset = int.from_bytes(
            payload[entry_offset + 12 : entry_offset + 16],
            "little",
        )
        if image_size <= 0 or image_offset <= 0:
            continue
        image_end = image_offset + image_size
        if image_end > len(payload):
            continue
        candidate = payload[image_offset:image_end]
        if candidate.startswith(b"\x89PNG\r\n\x1a\n"):
            return candidate
    return None


def fetch_url(
    url: str, *, kind="icon", budget=None, origin=None, origins=None
) -> tuple[bytes, str | None]:
    limit = {
        "html": icon_http.HTML_BYTES,
        "manifest": icon_http.MANIFEST_BYTES,
        "icon": icon_http.ICON_BYTES,
    }[kind]
    response = icon_http.fetch(
        url,
        limit=limit,
        budget=budget,
        origin=origin,
        origins=origins,
        timeout=FAVICON_TIMEOUT_SECONDS,
        headers=FAVICON_REQUEST_HEADERS,
    )
    if budget is not None:
        budget.last_url = response.url
    return response.data, response.content_type


def same_origin_links(urls, base_url):
    base = icon_http.parse_url(base_url)
    result = []
    for value in urls[: icon_http.MAX_METADATA_LINKS]:
        try:
            target = icon_http.parse_url(value)
            if target.origin == base.origin and target.url not in result:
                result.append(target.url)
        except (ValueError, UnicodeError):
            continue
    return result[: icon_http.MAX_CANDIDATES]


def extract_icon_links(html: str, base_url: str) -> list[str]:
    parser = IconLinkParser()
    parser.feed(html)
    prioritized: list[tuple[int, str]] = []
    for rel, href in parser.links:
        rel_tokens = {token for token in rel.split() if token}
        is_png = href.lower().endswith(".png") or "png" in href.lower()
        score = 4
        if is_png and "icon" in rel_tokens and "shortcut" not in rel_tokens:
            score = 0
        elif is_png:
            score = 1
        elif "icon" in rel_tokens and "shortcut" not in rel_tokens:
            score = 2
        elif "apple-touch-icon" in rel_tokens:
            score = 3
        prioritized.append((score, urljoin(base_url, href)))
    return same_origin_links(
        [url for _, url in sorted(prioritized, key=lambda item: (item[0], item[1]))],
        base_url,
    )


def extract_manifest_links(html: str, base_url: str) -> list[str]:
    parser = IconLinkParser()
    parser.feed(html)
    return same_origin_links(
        [urljoin(base_url, href) for href in parser.manifests], base_url
    )[: icon_http.MAX_MANIFESTS]


def extract_manifest_icon_links(manifest_text: str, base_url: str) -> list[str]:
    try:
        payload = json.loads(manifest_text)
    except (ValueError, RecursionError):
        return []
    if not isinstance(payload, dict):
        return []
    icons = payload.get("icons")
    if not isinstance(icons, list):
        return []
    prioritized: list[tuple[int, int, str]] = []
    for item in icons[: icon_http.MAX_METADATA_LINKS]:
        if not isinstance(item, dict):
            continue
        src = str(item.get("src") or "").strip()
        if not src:
            continue
        icon_url = urljoin(base_url, src)
        lower_url = icon_url.lower()
        sizes_text = str(item.get("sizes") or "").strip().lower()
        best_size = 0
        for token in sizes_text.split()[:8]:
            if "x" not in token:
                continue
            width_text, _sep, height_text = token.partition("x")
            try:
                best_size = max(best_size, int(width_text), int(height_text))
            except ValueError:
                continue
        if lower_url.endswith(".png"):
            score = 0
        elif lower_url.endswith(".ico"):
            score = 1
        elif lower_url.endswith(".svg"):
            score = 3
        else:
            score = 2
        prioritized.append((score, -best_size, icon_url))
    prioritized.sort(key=lambda item: (item[0], item[1], item[2]))
    return same_origin_links([url for _score, _neg_size, url in prioritized], base_url)


def get_public_favicon_fallback_urls(source_domain: str) -> list[str]:
    encoded = quote(source_domain, safe="")
    return [
        f"https://www.google.com/s2/favicons?domain={encoded}&sz=64",
    ]


def resolve_favicon_download(
    spec: ContainerSpec,
) -> tuple[str | None, bytes | None, str | None]:
    budget = icon_http.DownloadBudget(seconds=20, max_requests=12)
    try:
        homepage_url = get_homepage_url(spec)
        icon_http.parse_url(homepage_url)
    except (ValueError, UnicodeError):
        return None, None, None
    metadata_urls = []
    try:
        budget.last_url = homepage_url
        html, content_type = fetch_url(homepage_url, kind="html", budget=budget)
        homepage_url = budget.last_url
        if content_type == "text/html":
            text = html.decode("utf-8", errors="replace")
            metadata_urls.extend(extract_icon_links(text, homepage_url))
            for manifest_url in extract_manifest_links(text, homepage_url):
                try:
                    budget.last_url = manifest_url
                    manifest, _ = fetch_url(
                        manifest_url,
                        kind="manifest",
                        budget=budget,
                        origin=icon_http.parse_url(homepage_url).origin,
                    )
                    metadata_urls.extend(
                        extract_manifest_icon_links(
                            manifest.decode("utf-8", errors="replace"), budget.last_url
                        )
                    )
                except Exception:
                    continue
    except Exception:
        pass
    origin = icon_http.parse_url(homepage_url).origin
    direct = urljoin(homepage_url, "/favicon.ico")
    fallback = get_public_favicon_fallback_urls(icon_http.parse_url(homepage_url).host)[
        0
    ]
    service_origins = frozenset(
        [
            ("https", "www.google.com", 443),
            *[("https", f"t{i}.gstatic.com", 443) for i in range(4)],
        ]
    )
    candidates = list(dict.fromkeys(metadata_urls))[: icon_http.MAX_CANDIDATES - 2] + [
        direct,
        fallback,
    ]
    svg = None
    seen = set()
    for url in candidates:
        if url in seen:
            continue
        seen.add(url)
        try:
            payload, content_type = fetch_url(
                url,
                kind="icon",
                budget=budget,
                origin=None if url == fallback else origin,
                origins=service_origins if url == fallback else None,
            )
            suffix, payload = sanitize_icon(payload)
            if suffix == ".svg":
                svg = svg or (url, payload, "image/svg+xml")
            else:
                return url, payload, "image/png" if suffix == ".png" else content_type
        except Exception:
            continue
    return svg or (None, None, None)


def prepare_container_icon(spec: ContainerSpec) -> tuple[str, str | None]:
    icon_plan = build_icon_plan(spec)
    mode = icon_plan.mode
    if mode == "default":
        return get_fallback_icon_reference(spec), None
    if mode == "custom":
        if spec.custom_icon_path and spec.custom_icon_path.exists():
            target_path = get_icon_storage_path(
                spec, spec.custom_icon_path.suffix or ".png"
            )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            backup_existing_icons(spec)
            shutil.copy2(spec.custom_icon_path, target_path)
            return str(target_path), None
        return (
            get_fallback_icon_reference(spec),
            "Custom icon path not found, fallback used.",
        )
    download_url, payload, content_type = resolve_favicon_download(spec)
    if download_url and payload:
        suffix = detect_icon_payload_suffix(payload, content_type, download_url)
        if suffix is None:
            return (
                get_fallback_icon_reference(spec),
                "Favicon payload ungueltig, fallback icon used.",
            )
        if suffix == ".ico":
            extracted_png = extract_png_from_ico(payload)
            if extracted_png is not None:
                payload = extracted_png
                suffix = ".png"
        if suffix == ".svg":
            existing_raster = get_existing_icon_reference(spec, raster_only=True)
            if existing_raster is not None:
                return (
                    str(existing_raster),
                    "SVG favicon skipped because an existing raster icon is available.",
                )
        try:
            suffix, payload = sanitize_icon(payload)
        except Exception:
            return (
                get_fallback_icon_reference(spec),
                "Favicon payload ungueltig, fallback icon used.",
            )
        target_path = get_icon_storage_path(spec, suffix)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        backup_existing_icons(spec)
        target_path.write_bytes(payload)
        return str(target_path), None
    return (
        get_fallback_icon_reference(spec),
        "Favicon download failed, fallback icon used.",
    )


def build_register_existing_spec(container: DiscoveredContainer) -> ContainerSpec:
    allowed_domains = container.domains or PROFILE_MATCH_RULES.get(container.name, [])
    homepage_url = (
        f"https://{allowed_domains[0].split(':', 1)[0]}" if allowed_domains else None
    )
    return ContainerSpec(
        name=container.name,
        path=container.root_dir,
        allowed_domains=allowed_domains,
        source_firefox_dir=container.binary_path.parent,
        homepage_url=homepage_url,
        menu_name=REGISTER_EXISTING_MENU_NAMES.get(container.name),
        icon_mode="favicon",
        notes="Registrierter Bestandscontainer ohne Aenderung an Profil, user.js oder policies.json.",
    )


def merge_allowed_domains(
    primary: list[str],
    secondary: list[str],
) -> list[str]:
    merged: list[str] = []
    for domain in [*primary, *secondary]:
        cleaned = normalize_allowed_domain(domain)
        if cleaned and cleaned not in merged:
            merged.append(cleaned)
    return merged


def read_existing_homepage_url(container: DiscoveredContainer) -> str | None:
    policy_path = container.root_dir / "policies.json"
    if policy_path.is_file():
        try:
            payload = json.loads(read_text_if_small(policy_path))
        except (OSError, ValueError, RecursionError):
            payload = {}
        if not isinstance(payload, dict):
            payload = {}
        homepage = (
            payload.get("_builder_metadata", {}).get("homepage_url")
            if isinstance(payload.get("_builder_metadata"), dict)
            else None
        )
        if isinstance(homepage, str) and homepage.strip():
            return homepage.strip()
        policies = payload.get("policies")
        if isinstance(policies, dict):
            homepage_policy = policies.get("Homepage")
            if isinstance(homepage_policy, dict):
                url = homepage_policy.get("URL")
                if isinstance(url, str) and url.strip():
                    return url.strip()
    user_js_path = container.root_dir / "user.js"
    if user_js_path.is_file():
        content = read_text_if_small(user_js_path)
        match = HOMEPAGE_PREF_PATTERN.search(content)
        if match:
            return match.group(1).strip()
    return None


def read_existing_allowed_domains(container: DiscoveredContainer) -> list[str]:
    for policy_path in (
        container.root_dir / "policies.json",
        container.root_dir / "firefox" / "distribution" / "policies.json",
    ):
        if not policy_path.is_file():
            continue
        try:
            payload = json.loads(read_text_if_small(policy_path))
        except (OSError, ValueError, RecursionError):
            continue
        if not isinstance(payload, dict):
            continue
        metadata = payload.get("_builder_metadata")
        if not isinstance(metadata, dict):
            continue
        domains = metadata.get("allowed_domains")
        if not isinstance(domains, list):
            continue
        normalized = normalize_allowed_domains(
            [item for item in domains if isinstance(item, str)]
        )
        if normalized:
            return normalized
    return list(container.domains)


def build_repair_policy_spec(container: DiscoveredContainer) -> ContainerSpec:
    known_defaults = (
        get_known_container_defaults(
            container.name,
            purpose=container.purpose,
            domains=container.domains,
        )
        or {}
    )
    known_domains = known_defaults.get("allowed_domains")
    bundle_domains = (
        [item for item in known_domains if isinstance(item, str) and item.strip()]
        if isinstance(known_domains, list)
        else []
    )
    existing_domains = list(container.domains)
    fallback_domains = PROFILE_MATCH_RULES.get(container.name, [])
    allowed_domains = merge_allowed_domains(
        existing_domains,
        bundle_domains or fallback_domains,
    )
    existing_homepage_url = read_existing_homepage_url(container)
    existing_homepage_host = (
        urlparse(existing_homepage_url).hostname if existing_homepage_url else None
    )
    if existing_homepage_host:
        existing_domains = merge_allowed_domains(
            [existing_homepage_host], existing_domains
        )
    homepage_domain = (
        existing_homepage_host
        if existing_homepage_host
        else (
            existing_domains[0]
            if existing_domains
            else (allowed_domains[0] if allowed_domains else "")
        )
    )
    homepage_url = (
        existing_homepage_url
        if existing_homepage_url
        else f"https://{homepage_domain.split(':', 1)[0]}" if homepage_domain else None
    )
    return ContainerSpec(
        name=container.name,
        path=container.root_dir,
        allowed_domains=allowed_domains,
        source_firefox_dir=container.binary_path.parent,
        homepage_url=homepage_url,
        new_tab_url="about:blank",
        menu_name=REGISTER_EXISTING_MENU_NAMES.get(container.name),
        notes=(
            "Reparierter Bestandscontainer mit aktualisierten Domain- und "
            "Subdomain-Regeln in policies.json und user.js."
        ),
    )
    return ContainerSpec(
        name=container.name,
        path=container.root_dir,
        allowed_domains=allowed_domains,
        source_firefox_dir=container.binary_path.parent,
        homepage_url=homepage_url,
        menu_name=REGISTER_EXISTING_MENU_NAMES.get(container.name),
        icon_mode="favicon",
        notes="Registrierter Bestandscontainer ohne Aenderung an Profil, user.js oder policies.json.",
    )


def parse_desktop_exec_target(path: Path) -> Path | None:
    text = read_text_if_small(path)
    for line in text.splitlines():
        if not line.startswith("Exec="):
            continue
        command = line.split("=", 1)[1].strip()
        if not command:
            return None
        try:
            tokens = shlex.split(command)
        except ValueError:
            return None
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
    return None


def read_desktop_entry_value(path: Path, key: str) -> str | None:
    prefix = f"{key}="
    text = read_text_if_small(path)
    for line in text.splitlines():
        if line.startswith(prefix):
            value = line.split("=", 1)[1].strip()
            return value or None
    return None


def build_desktop_exec_command(desktop_file: Path, start_script: Path) -> str:
    desktop_name = desktop_file.name
    return (
        f'env BAMF_DESKTOP_FILE_HINT="{desktop_file}" '
        f'GIO_LAUNCHED_DESKTOP_FILE="{desktop_file}" '
        f'MOZ_DESKTOP_FILE="{desktop_name}" '
        f'"{start_script}"'
    )


def is_uninstalled_backup_path(path: Path | None) -> bool:
    if path is None:
        return False
    return any(parent.name == DEFAULT_UNINSTALLED_DIRNAME for parent in path.parents)


def list_managed_menu_entries(applications_dir: Path) -> list[MenuEntryInfo]:
    entries: list[MenuEntryInfo] = []
    if not applications_dir.is_dir():
        return entries
    for path, directory in sorted(iter_scan_entries(applications_dir, recursive=False)):
        if (
            directory
            or not path.name.startswith("netmon-secure-browser-")
            or path.suffix != ".desktop"
        ):
            continue
        exec_target = parse_desktop_exec_target(path)
        container_root = exec_target.parent if exec_target else None
        container_name = container_root.name if container_root else None
        is_orphan = (
            exec_target is None
            or not exec_target.exists()
            or is_uninstalled_backup_path(exec_target)
        )
        entries.append(
            MenuEntryInfo(
                path=path,
                exec_target=exec_target,
                container_root=container_root,
                container_name=container_name,
                is_orphan=is_orphan,
            )
        )
    return entries


def is_external_profile(profile_path: Path | None, container_root: Path) -> bool:
    if profile_path is None:
        return False
    try:
        profile_path.relative_to(container_root)
        return False
    except ValueError:
        return True


def derive_container_status(
    container: DiscoveredContainer,
    menu_entries: list[MenuEntryInfo],
) -> str:
    if len(menu_entries) > 1:
        return "Menü doppelt"
    if container.launcher_path is None:
        return "Launcher fehlt"
    effective_profile = get_effective_profile_path(container)
    if is_external_profile(effective_profile, container.root_dir):
        return "Profil extern"
    if len(menu_entries) == 1:
        return "vollständig"
    return "Menüeintrag fehlt"


def find_container_by_name(
    containers: list[DiscoveredContainer],
    name: str,
) -> DiscoveredContainer | None:
    for container in containers:
        if container.name == name:
            return container
    return None


def build_policies_payload(spec: ContainerSpec) -> dict[str, Any]:
    security = resolve_security_profile(spec)
    exceptions: list[str] = []
    for domain in spec.allowed_domains:
        for pattern in make_match_patterns(domain):
            if pattern not in exceptions:
                exceptions.append(pattern)
    homepage_url = get_homepage_url(spec)
    policies: dict[str, Any] = {
        "DisableTelemetry": True,
        "DisablePocket": True,
        "DisableFirefoxStudies": True,
        "DisableFirefoxAccounts": True,
        "DisableFormHistory": True,
        "DisableProfileImport": True,
        "DisableMasterPasswordCreation": False,
        "OfferToSaveLogins": bool(security["allow_password_manager"]),
        "DontCheckDefaultBrowser": True,
        "NoDefaultBookmarks": True,
        "OverrideFirstRunPage": "",
        "OverridePostUpdatePage": "",
        "PasswordManagerEnabled": bool(security["allow_password_manager"]),
        "Homepage": {
            "URL": homepage_url,
            "Locked": False,
            "StartPage": "homepage",
        },
    }
    if bool(security["enable_website_filter"]):
        policies["WebsiteFilter"] = {
            "Block": [WEBSITE_FILTER_BLOCK_PATTERN],
            "Exceptions": exceptions,
        }
    return {
        "policies": policies,
        "_builder_metadata": {
            "allowed_domains": spec.allowed_domains,
            "homepage_url": homepage_url,
            "new_tab_url": get_new_tab_url(spec),
            "security_profile": security["security_profile"],
            "allow_password_manager": bool(security["allow_password_manager"]),
            "keep_cookies": bool(security["keep_cookies"]),
            "enable_website_filter": bool(security["enable_website_filter"]),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
    }


def build_user_js_content(spec: ContainerSpec) -> str:
    security = resolve_security_profile(spec)
    homepage_url = json.dumps(get_homepage_url(spec))
    new_tab_url = json.dumps(get_new_tab_url(spec))
    keep_cookies = bool(security["keep_cookies"])
    allow_password_manager = bool(security["allow_password_manager"])
    lines = [
        "// Generated by browser_container_builder.py",
        f"// Container: {spec.name}",
        f"// Security profile: {security['security_profile']}",
        'user_pref("app.normandy.enabled", false);',
        'user_pref("app.shield.optoutstudies.enabled", false);',
        'user_pref("browser.aboutwelcome.enabled", false);',
        f'user_pref("browser.newtab.url", {new_tab_url});',
        f'user_pref("browser.startup.homepage", {homepage_url});',
        'user_pref("browser.startup.page", 1);',
        'user_pref("startup.homepage_override_url", "");',
        'user_pref("startup.homepage_welcome_url", "");',
        'user_pref("startup.homepage_welcome_url.additional", "");',
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
        f'user_pref("network.cookie.lifetimePolicy", {0 if keep_cookies else 2});',
        'user_pref("network.dns.disablePrefetch", true);',
        'user_pref("network.http.speculative-parallel-limit", 0);',
        'user_pref("network.predictor.enabled", false);',
        'user_pref("network.trr.mode", 5);',
        'user_pref("privacy.clearOnShutdown.cache", true);',
        f'user_pref("privacy.clearOnShutdown.cookies", {str((not keep_cookies)).lower()});',
        'user_pref("privacy.clearOnShutdown.downloads", true);',
        'user_pref("privacy.clearOnShutdown.formdata", true);',
        'user_pref("privacy.clearOnShutdown.history", true);',
        'user_pref("privacy.clearOnShutdown.offlineApps", true);',
        'user_pref("privacy.clearOnShutdown.sessions", true);',
        f'user_pref("privacy.sanitize.sanitizeOnShutdown", {str((not keep_cookies)).lower()});',
        'user_pref("privacy.trackingprotection.enabled", true);',
        'user_pref("privacy.trackingprotection.pbmode.enabled", true);',
        f'user_pref("signon.autofillForms", {str(allow_password_manager).lower()});',
        f'user_pref("signon.rememberSignons", {str(allow_password_manager).lower()});',
        'user_pref("toolkit.telemetry.enabled", false);',
    ]
    return "\n".join(lines) + "\n"


def build_start_script(spec: ContainerSpec) -> str:
    wm_class = shlex.quote(get_spec_wm_class(spec))
    return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WM_CLASS={wm_class}
DESKTOP_FILE_HINT="${{BAMF_DESKTOP_FILE_HINT:-${{GIO_LAUNCHED_DESKTOP_FILE:-}}}}"
if [ -n "$DESKTOP_FILE_HINT" ]; then
    export BAMF_DESKTOP_FILE_HINT="$DESKTOP_FILE_HINT"
    export GIO_LAUNCHED_DESKTOP_FILE="$DESKTOP_FILE_HINT"
    export MOZ_DESKTOP_FILE="${{MOZ_DESKTOP_FILE:-${{DESKTOP_FILE_HINT##*/}}}}"
fi
if [ "${{XDG_SESSION_TYPE:-}}" = "wayland" ] && [ "${{NETMON_SECURE_BROWSER_NATIVE_WAYLAND:-0}}" != "1" ]; then
    export MOZ_ENABLE_WAYLAND=0
    export GDK_BACKEND=x11
fi
STATE_BASE="${{XDG_STATE_HOME:-$HOME/.local/state}}"
LOCK_ROOT="$STATE_BASE/netmon/secure-browser"
LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
PID_FILE="$LOCK_DIR/pid"

focus_existing_window() {{
    if command -v wmctrl >/dev/null 2>&1; then
        wmctrl -x -a "$WM_CLASS" >/dev/null 2>&1 && return 0
    fi
    if command -v xdotool >/dev/null 2>&1; then
        local window_id
        window_id="$(xdotool search --class "$WM_CLASS" 2>/dev/null | head -n 1 || true)"
        if [ -n "$window_id" ]; then
            xdotool windowactivate "$window_id" >/dev/null 2>&1 && return 0
        fi
    fi
    return 1
}}

lock_pid_is_running() {{
    [ -f "$PID_FILE" ] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    case "$pid" in
        ''|*[!0-9]*) return 1 ;;
    esac
    kill -0 "$pid" >/dev/null 2>&1
}}

if [ -f "$SCRIPT_DIR/child-lock.json" ]; then
    python3 "$SCRIPT_DIR/browser_lock.py" "$SCRIPT_DIR/child-lock.json" || exit 1
fi

if ! mkdir -p "$LOCK_ROOT" 2>/dev/null; then
    LOCK_ROOT="$SCRIPT_DIR/.netmon-state"
    LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
    PID_FILE="$LOCK_DIR/pid"
    mkdir -p "$LOCK_ROOT"
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    if lock_pid_is_running; then
        focus_existing_window || true
        exit 0
    fi
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
        LOCK_ROOT="$SCRIPT_DIR/.netmon-state"
        LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
        PID_FILE="$LOCK_DIR/pid"
        mkdir -p "$LOCK_ROOT"
        if ! mkdir "$LOCK_DIR" 2>/dev/null; then
            if lock_pid_is_running; then
                focus_existing_window || true
                exit 0
            fi
            rm -rf "$LOCK_DIR" 2>/dev/null || true
            mkdir "$LOCK_DIR"
        fi
    fi
fi

if [ -f "$SCRIPT_DIR/user.js" ]; then
    cp "$SCRIPT_DIR/user.js" "$SCRIPT_DIR/profile/user.js"
fi

if [ -f "$SCRIPT_DIR/policies.json" ]; then
    mkdir -p "$SCRIPT_DIR/firefox/distribution"
    cp "$SCRIPT_DIR/policies.json" "$SCRIPT_DIR/firefox/distribution/policies.json"
fi

if [ "${{NETMON_SECURE_BROWSER_LEGACY_START:-0}}" = "1" ]; then
    exec "$SCRIPT_DIR/firefox/firefox" --no-remote --profile "$SCRIPT_DIR/profile" "$@"
fi

printf '%s\\n' "$$" > "$PID_FILE"
exec "$SCRIPT_DIR/firefox/firefox" --class "$WM_CLASS" --no-remote --profile "$SCRIPT_DIR/profile" "$@"
"""


def build_browser_lock_helper() -> str:
    return """#!/usr/bin/env python3
import hashlib
import hmac
import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog


def main() -> int:
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    salt = bytes.fromhex(config["salt"])
    expected = bytes.fromhex(config["password_hash"])
    iterations = int(config.get("iterations", 200000))
    root = tk.Tk()
    root.withdraw()
    try:
        for _attempt in range(3):
            password = simpledialog.askstring(
                "Secure Browser Kindersicherung",
                "Passwort eingeben:",
                show="*",
                parent=root,
            )
            if password is None:
                return 1
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, iterations
            )
            if hmac.compare_digest(actual, expected):
                return 0
            messagebox.showerror(
                "Secure Browser Kindersicherung",
                "Passwort ist nicht korrekt.",
                parent=root,
            )
        return 1
    finally:
        root.destroy()


if __name__ == "__main__":
    raise SystemExit(main())
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
- Kein Firefox Sync und kein Profilimport.
- Der Firefox-Passwortmanager bleibt pro Container aktiv, damit Zugangsdaten getrennt je Dienst gespeichert werden koennen.
- Notiz: {notes}
"""


def _desktop_field(text: str) -> str:
    return str(text or "").replace("\r", " ").replace("\n", " ").strip()


def build_launcher_content(
    spec: ContainerSpec, icon_path: str | Path | None = None
) -> str:
    absolute_start = spec.path / "start.sh"
    launcher_path = spec.path / "launcher.desktop"
    effective_icon_path = icon_path or get_fallback_icon_reference(spec)
    safe_name = _desktop_field(spec.name)
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={safe_name}
Comment=Isolierter Firefox-Container fuer {safe_name}
Exec={build_desktop_exec_command(launcher_path, absolute_start)}
Icon={effective_icon_path}
Terminal=false
Categories=Network;WebBrowser;
StartupNotify=true
StartupWMClass={get_spec_wm_class(spec)}
"""


def build_existing_start_script(
    container: DiscoveredContainer, profile_path: Path
) -> str:
    wm_class = shlex.quote(get_container_wm_class(container))
    profile_arg = shlex.quote(str(profile_path))
    return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
WM_CLASS={wm_class}
PROFILE_PATH={profile_arg}
DESKTOP_FILE_HINT="${{BAMF_DESKTOP_FILE_HINT:-${{GIO_LAUNCHED_DESKTOP_FILE:-}}}}"
if [ -n "$DESKTOP_FILE_HINT" ]; then
    export BAMF_DESKTOP_FILE_HINT="$DESKTOP_FILE_HINT"
    export GIO_LAUNCHED_DESKTOP_FILE="$DESKTOP_FILE_HINT"
    export MOZ_DESKTOP_FILE="${{MOZ_DESKTOP_FILE:-${{DESKTOP_FILE_HINT##*/}}}}"
fi
if [ "${{XDG_SESSION_TYPE:-}}" = "wayland" ] && [ "${{NETMON_SECURE_BROWSER_NATIVE_WAYLAND:-0}}" != "1" ]; then
    export MOZ_ENABLE_WAYLAND=0
    export GDK_BACKEND=x11
fi
STATE_BASE="${{XDG_STATE_HOME:-$HOME/.local/state}}"
LOCK_ROOT="$STATE_BASE/netmon/secure-browser"
LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
PID_FILE="$LOCK_DIR/pid"

focus_existing_window() {{
    if command -v wmctrl >/dev/null 2>&1; then
        wmctrl -x -a "$WM_CLASS" >/dev/null 2>&1 && return 0
    fi
    if command -v xdotool >/dev/null 2>&1; then
        local window_id
        window_id="$(xdotool search --class "$WM_CLASS" 2>/dev/null | head -n 1 || true)"
        if [ -n "$window_id" ]; then
            xdotool windowactivate "$window_id" >/dev/null 2>&1 && return 0
        fi
    fi
    return 1
}}

lock_pid_is_running() {{
    [ -f "$PID_FILE" ] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    case "$pid" in
        ''|*[!0-9]*) return 1 ;;
    esac
    kill -0 "$pid" >/dev/null 2>&1
}}

if [ -f "$SCRIPT_DIR/child-lock.json" ]; then
    python3 "$SCRIPT_DIR/browser_lock.py" "$SCRIPT_DIR/child-lock.json" || exit 1
fi

if ! mkdir -p "$LOCK_ROOT" 2>/dev/null; then
    LOCK_ROOT="$SCRIPT_DIR/.netmon-state"
    LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
    PID_FILE="$LOCK_DIR/pid"
    mkdir -p "$LOCK_ROOT"
fi
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    if lock_pid_is_running; then
        focus_existing_window || true
        exit 0
    fi
    rm -rf "$LOCK_DIR" 2>/dev/null || true
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
        LOCK_ROOT="$SCRIPT_DIR/.netmon-state"
        LOCK_DIR="$LOCK_ROOT/$WM_CLASS.lock"
        PID_FILE="$LOCK_DIR/pid"
        mkdir -p "$LOCK_ROOT"
        if ! mkdir "$LOCK_DIR" 2>/dev/null; then
            if lock_pid_is_running; then
                focus_existing_window || true
                exit 0
            fi
            rm -rf "$LOCK_DIR" 2>/dev/null || true
            mkdir "$LOCK_DIR"
        fi
    fi
fi

if [ "${{NETMON_SECURE_BROWSER_LEGACY_START:-0}}" = "1" ]; then
    exec "$SCRIPT_DIR/firefox/firefox" --no-remote --profile "$PROFILE_PATH" "$@"
fi

printf '%s\\n' "$$" > "$PID_FILE"
exec "$SCRIPT_DIR/firefox/firefox" --class "$WM_CLASS" --no-remote --profile "$PROFILE_PATH" "$@"
"""


def build_existing_launcher_content(
    container: DiscoveredContainer,
    menu_name: str,
    icon_path: str | Path,
) -> str:
    absolute_start = container.root_dir / "start.sh"
    launcher_path = container.root_dir / "launcher.desktop"
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={_desktop_field(menu_name)}
Comment=Registrierter Firefox-Bestandscontainer fuer {_desktop_field(container.name)}
Exec={build_desktop_exec_command(launcher_path, absolute_start)}
Icon={icon_path}
Terminal=false
Categories=Network;Security;
StartupNotify=true
StartupWMClass={get_container_wm_class(container)}
"""


def build_menu_launcher_content(
    spec: ContainerSpec,
    icon_path: str | Path | None = None,
    desktop_file_path: Path | None = None,
) -> str:
    absolute_start = spec.path / "start.sh"
    menu_entry_path = desktop_file_path or get_menu_entry_path(
        spec, DEFAULT_APPLICATIONS_DIR
    )
    effective_icon_path = icon_path or get_fallback_icon_reference(spec)
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name={_desktop_field(get_menu_name(spec))}
Comment=NetMon Secure Browser fuer {_desktop_field(spec.name)}
Exec={build_desktop_exec_command(menu_entry_path, absolute_start)}
Icon={effective_icon_path}
Terminal=false
Categories=Network;Security;
StartupNotify=true
StartupWMClass={get_spec_wm_class(spec)}
"""


def validate_config_payload(
    payload: dict[str, Any], base_dir: Path
) -> list[ContainerSpec]:
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
        if not CONTAINER_NAME_PATTERN.fullmatch(name):
            raise ValueError(
                f"Container name enthaelt unzulaessige Zeichen (nur A-Z a-z 0-9 . _ - erlaubt): {name}"
            )
        if name in {".", ".."}:
            raise ValueError(f"Container name darf nicht '.' oder '..' sein: {name}")
        if not isinstance(allowed_domains, list) or not all(
            isinstance(item, str) and item.strip() for item in allowed_domains
        ):
            raise ValueError(
                f"Container '{name}' requires a non-empty string list in "
                "'allowed_domains'."
            )
        normalized_allowed_domains = normalize_allowed_domains(allowed_domains)
        if not normalized_allowed_domains:
            raise ValueError(
                f"Container '{name}' requires at least one valid domain in "
                "'allowed_domains'."
            )
        path_raw = entry.get("path")
        path = ensure_path(path_raw) if isinstance(path_raw, str) else base_dir / name
        source_raw = entry.get("source_firefox_dir")
        source = (
            ensure_path(source_raw) if isinstance(source_raw, str) else default_source
        )
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
            entry.get("menu_name") if isinstance(entry.get("menu_name"), str) else None
        )
        icon_mode = (
            entry.get("icon_mode") if isinstance(entry.get("icon_mode"), str) else None
        )
        custom_icon_path = (
            ensure_path(entry.get("custom_icon_path"))
            if isinstance(entry.get("custom_icon_path"), str)
            else None
        )
        notes = entry.get("notes") if isinstance(entry.get("notes"), str) else None
        security_profile = (
            entry.get("security_profile")
            if isinstance(entry.get("security_profile"), str)
            else None
        )
        allow_password_manager = (
            entry.get("allow_password_manager")
            if isinstance(entry.get("allow_password_manager"), bool)
            else None
        )
        keep_cookies = (
            entry.get("keep_cookies")
            if isinstance(entry.get("keep_cookies"), bool)
            else None
        )
        enable_website_filter = (
            entry.get("enable_website_filter")
            if isinstance(entry.get("enable_website_filter"), bool)
            else None
        )
        child_lock = entry.get("child_lock")
        if child_lock is not None:
            if not isinstance(child_lock, dict):
                raise ValueError(f"Container '{name}': child_lock must be an object.")
            required_lock_fields = {"salt", "password_hash", "iterations"}
            if not required_lock_fields.issubset(child_lock):
                raise ValueError(f"Container '{name}': child_lock is incomplete.")
            try:
                salt_bytes = bytes.fromhex(str(child_lock["salt"]))
                hash_bytes = bytes.fromhex(str(child_lock["password_hash"]))
                iterations = int(child_lock["iterations"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Container '{name}': child_lock is invalid.") from exc
            if len(salt_bytes) < 16 or len(hash_bytes) != 32:
                raise ValueError(
                    f"Container '{name}': child_lock hash data is invalid."
                )
            if iterations < 100000:
                raise ValueError(
                    f"Container '{name}': child_lock iterations are too low."
                )
            child_lock = {
                "algorithm": "pbkdf2_sha256",
                "salt": str(child_lock["salt"]),
                "password_hash": str(child_lock["password_hash"]),
                "iterations": iterations,
            }
        specs.append(
            ContainerSpec(
                name=name,
                path=path,
                allowed_domains=normalized_allowed_domains,
                source_firefox_dir=source,
                homepage_url=homepage_url,
                new_tab_url=new_tab_url,
                menu_name=menu_name,
                icon_mode=icon_mode,
                custom_icon_path=custom_icon_path,
                notes=notes,
                security_profile=security_profile,
                allow_password_manager=allow_password_manager,
                keep_cookies=keep_cookies,
                enable_website_filter=enable_website_filter,
                child_lock=child_lock,
            )
        )
    return specs


def load_config(config_path: Path, base_dir: Path) -> list[ContainerSpec]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    return validate_config_payload(payload, base_dir)


def select_missing_sources(
    specs: list[ContainerSpec], discovered: list[DiscoveredContainer]
) -> list[str]:
    source_candidates = sorted(
        {container.binary_path.parent for container in discovered}
    )
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
        "- Versionsangaben: lokale Metadaten, kein Echtheitsnachweis.",
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
        profile = (
            str(container.profile_path) if container.profile_path else "nicht erkannt"
        )
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


def build_register_existing_plan(
    containers: list[DiscoveredContainer],
    applications_dir: Path,
) -> list[str]:
    lines = ["Dry-Run Register Existing", ""]
    for container in containers:
        spec = build_register_existing_spec(container)
        icon_plan = build_icon_plan(spec)
        effective_profile = get_effective_profile_path(container)
        start_path = container.root_dir / "start.sh"
        launcher_path = container.root_dir / "launcher.desktop"
        menu_path = get_menu_entry_path(spec, applications_dir)
        lines.extend(
            [
                f"- {container.name}",
                f"  Ziel: {container.root_dir}",
                f"  Profil: {effective_profile if effective_profile else 'NICHT ERKANNT'}",
                f"  start.sh: {'besteht bereits' if start_path.exists() else 'wird erstellt'}",
                f"  launcher.desktop: {'besteht bereits' if launcher_path.exists() else 'wird erstellt'}",
                f"  Icon-Modus: {icon_plan.mode}",
                f"  Icon-Domain: {icon_plan.source_domain if icon_plan.source_domain else 'nicht erkannt'}",
                f"  Favicon-URL: {icon_plan.attempt_url if icon_plan.attempt_url else 'kein Abruf'}",
                f"  Icon-Ziel: {icon_plan.storage_path}",
                f"  Menueeintrag: {menu_path}",
                (
                    "  Menue-Status: Bestehender Menueeintrag wird direkt ersetzt"
                    if menu_path.exists()
                    else "  Menue-Status: Neuer Menueeintrag wird erstellt"
                ),
                (
                    "  Status: OK"
                    if effective_profile is not None
                    else "  Status: ABBRUCH: Kein Profilpfad erkannt"
                ),
            ]
        )
    return lines


def build_refresh_existing_plan(
    containers: list[DiscoveredContainer],
    applications_dir: Path,
) -> list[str]:
    lines = ["Dry-Run Refresh Existing", ""]
    for container in containers:
        spec = build_register_existing_spec(container)
        icon_plan = build_icon_plan(spec)
        effective_profile = get_effective_profile_path(container)
        start_path = container.root_dir / "start.sh"
        launcher_path = container.root_dir / "launcher.desktop"
        menu_path = get_menu_entry_path(spec, applications_dir)
        lines.extend(
            [
                f"- {container.name}",
                f"  Ziel: {container.root_dir}",
                f"  Profil: {effective_profile if effective_profile else 'NICHT ERKANNT'}",
                (
                    "  start.sh: wird gesichert und aktualisiert"
                    if start_path.exists()
                    else "  start.sh: wird erstellt"
                ),
                (
                    "  launcher.desktop: wird gesichert und aktualisiert"
                    if launcher_path.exists()
                    else "  launcher.desktop: wird erstellt"
                ),
                f"  Icon-Modus: {icon_plan.mode}",
                f"  Icon-Domain: {icon_plan.source_domain if icon_plan.source_domain else 'nicht erkannt'}",
                f"  Favicon-URL: {icon_plan.attempt_url if icon_plan.attempt_url else 'kein Abruf'}",
                f"  Icon-Ziel: {icon_plan.storage_path}",
                f"  Menueeintrag: {menu_path}",
                (
                    "  Menue-Status: Bestehender Menueeintrag wird direkt ersetzt"
                    if menu_path.exists()
                    else "  Menue-Status: Neuer Menueeintrag wird erstellt"
                ),
                (
                    "  Status: OK"
                    if effective_profile is not None
                    else "  Status: ABBRUCH: Kein Profilpfad erkannt"
                ),
            ]
        )
    return lines


def build_repair_policy_plan(
    containers: list[DiscoveredContainer],
) -> list[str]:
    lines = ["Dry-Run Repair Policy", ""]
    for container in containers:
        spec = build_repair_policy_spec(container)
        effective_profile = get_effective_profile_path(container)
        profile_user_js = (
            effective_profile / "user.js"
            if effective_profile and effective_profile.is_dir()
            else None
        )
        distribution_policy = (
            container.root_dir / "firefox" / "distribution" / "policies.json"
        )
        lines.extend(
            [
                f"- {container.name}",
                f"  Ziel: {container.root_dir}",
                f"  Homepage: {get_homepage_url(spec) if spec.homepage_url else 'nicht gesetzt'}",
                f"  Domains: {', '.join(spec.allowed_domains) if spec.allowed_domains else 'keine'}",
                (
                    "  policies.json: wird gesichert und aktualisiert"
                    if (container.root_dir / "policies.json").exists()
                    else "  policies.json: wird erstellt"
                ),
                (
                    "  distribution/policies.json: wird gesichert und aktualisiert"
                    if distribution_policy.exists()
                    else "  distribution/policies.json: wird erstellt"
                ),
                (
                    "  user.js: wird gesichert und aktualisiert"
                    if (container.root_dir / "user.js").exists()
                    else "  user.js: wird erstellt"
                ),
                (
                    "  profile/user.js: wird gesichert und aktualisiert"
                    if profile_user_js and profile_user_js.exists()
                    else (
                        "  profile/user.js: wird erstellt"
                        if profile_user_js
                        else "  profile/user.js: externes Profil wird nicht beschrieben"
                    )
                ),
                "  Status: OK",
            ]
        )
    return lines


def build_list_installed_report(
    containers: list[DiscoveredContainer],
    applications_dir: Path,
) -> list[str]:
    menu_entries = list_managed_menu_entries(applications_dir)
    lines = ["Installed Containers", ""]
    for container in containers:
        associated = [
            entry
            for entry in menu_entries
            if entry.container_root == container.root_dir
            or entry.container_name == container.name
        ]
        effective_profile = get_effective_profile_path(container)
        lines.extend(
            [
                f"- {container.name}",
                f"  Container: {container.root_dir}",
                f"  Launcher: {container.launcher_path if container.launcher_path else 'nicht erkannt'}",
                (
                    "  Menueeintraege: "
                    + ", ".join(str(entry.path) for entry in associated)
                    if associated
                    else "  Menueeintraege: keine"
                ),
                f"  Profil: {effective_profile if effective_profile else 'nicht erkannt'}",
                f"  Status: {derive_container_status(container, associated)}",
            ]
        )
    if not containers:
        lines.append("Keine Container erkannt.")
    return lines


def build_cleanup_menu_plan(
    applications_dir: Path,
) -> tuple[list[str], list[MenuEntryInfo]]:
    menu_entries = list_managed_menu_entries(applications_dir)
    duplicates: list[MenuEntryInfo] = []
    grouped: dict[str, list[MenuEntryInfo]] = {}
    for entry in menu_entries:
        key = str(entry.container_root) if entry.container_root else entry.path.stem
        grouped.setdefault(key, []).append(entry)
    for items in grouped.values():
        if len(items) > 1:
            duplicates.extend(items[1:])
    removable = [entry for entry in menu_entries if entry.is_orphan] + duplicates
    unique_removable_map = {str(entry.path): entry for entry in removable}
    unique_removable = list(unique_removable_map.values())
    lines = ["Dry-Run Cleanup Menu", ""]
    for entry in menu_entries:
        reasons: list[str] = []
        if entry.is_orphan:
            reasons.append("verwaist")
        if entry in duplicates:
            reasons.append("doppelt")
        status = ", ".join(reasons) if reasons else "behalten"
        lines.append(f"- {entry.path}: {status}")
    if not menu_entries:
        lines.append("Keine netmon-secure-browser-*.desktop Eintraege erkannt.")
    return lines, unique_removable


def build_uninstall_plan(
    container: DiscoveredContainer,
    applications_dir: Path,
    base_dir: Path,
) -> list[str]:
    associated = [
        entry
        for entry in list_managed_menu_entries(applications_dir)
        if entry.container_root == container.root_dir
        or entry.container_name == container.name
    ]
    effective_profile = get_effective_profile_path(container)
    uninstall_target = (
        get_uninstall_base_dir(base_dir)
        / datetime.now().strftime("%Y%m%d_%H%M%S")
        / container.name
    )
    lines = [
        "Dry-Run Uninstall",
        "",
        f"- Container: {container.name}",
        f"  Quelle: {container.root_dir}",
        f"  Verschieben nach: {uninstall_target}",
        (
            f"  Menueeintraege: {', '.join(str(entry.path) for entry in associated)}"
            if associated
            else "  Menueeintraege: keine"
        ),
        (
            "  Profil: Externes Profil erkannt, wird nicht geloescht"
            if is_external_profile(effective_profile, container.root_dir)
            else f"  Profil: {effective_profile if effective_profile else 'nicht erkannt'}"
        ),
    ]
    return lines


def build_apply_plan(
    specs: list[ContainerSpec],
    discovered: list[DiscoveredContainer],
    applications_dir: Path,
) -> list[str]:
    existing_paths = {container.root_dir.resolve() for container in discovered}
    lines = ["Dry-Run Plan", ""]
    for spec in specs:
        target = spec.path.resolve()
        source = (
            str(spec.source_firefox_dir) if spec.source_firefox_dir else "UNGESETZT"
        )
        icon_plan = build_icon_plan(spec)
        menu_entry_path = get_menu_entry_path(spec, applications_dir)
        if menu_entry_path.exists():
            menu_status = "Bestehender Menueeintrag wird direkt ersetzt"
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
                f"  Icon-Modus: {icon_plan.mode}",
                f"  Icon-Domain: {icon_plan.source_domain if icon_plan.source_domain else 'nicht erkannt'}",
                f"  Favicon-URL: {icon_plan.attempt_url if icon_plan.attempt_url else 'kein Abruf'}",
                f"  Icon-Ziel: {icon_plan.storage_path}",
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


def backup_existing_file(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "browser-container-builder-backups" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / path.name
    shutil.copy2(path, backup_path)
    return backup_path


def backup_existing_icons(spec: ContainerSpec) -> None:
    icon_dir = get_icon_storage_dir(spec)
    if not icon_dir.exists():
        return
    for existing_icon in icon_dir.glob("favicon.*"):
        backup_existing_file(existing_icon)


def remove_conflicting_menu_entries(
    spec: ContainerSpec,
    applications_dir: Path,
    current_menu_entry_path: Path,
) -> None:
    desired_name = get_menu_name(spec)
    desired_exec = spec.path / "start.sh"
    for candidate in applications_dir.glob("*.desktop"):
        if candidate == current_menu_entry_path or not candidate.is_file():
            continue
        candidate_name = read_desktop_entry_value(candidate, "Name")
        candidate_exec = parse_desktop_exec_target(candidate)
        same_exec = candidate_exec == desired_exec
        same_root = candidate_exec is not None and candidate_exec.parent == spec.path
        same_name_for_same_root = candidate_name == desired_name and same_root
        if not (same_exec or same_root or same_name_for_same_root):
            continue
        candidate.unlink()


def install_menu_entry(
    spec: ContainerSpec,
    applications_dir: Path,
    icon_path: Path | None = None,
) -> Path:
    applications_dir.mkdir(parents=True, exist_ok=True)
    menu_entry_path = get_menu_entry_path(spec, applications_dir)
    remove_conflicting_menu_entries(spec, applications_dir, menu_entry_path)
    write_text(
        menu_entry_path,
        build_menu_launcher_content(
            spec,
            icon_path=icon_path,
            desktop_file_path=menu_entry_path,
        ),
        executable=True,
    )
    return menu_entry_path


def install_existing_menu_entry(
    container: DiscoveredContainer,
    applications_dir: Path,
    icon_path: Path | None = None,
) -> Path:
    spec = build_register_existing_spec(container)
    applications_dir.mkdir(parents=True, exist_ok=True)
    menu_entry_path = get_menu_entry_path(spec, applications_dir)
    remove_conflicting_menu_entries(spec, applications_dir, menu_entry_path)
    write_text(
        menu_entry_path,
        build_menu_launcher_content(
            spec,
            icon_path=icon_path,
            desktop_file_path=menu_entry_path,
        ),
        executable=True,
    )
    return menu_entry_path


def remove_menu_entries(
    entries: list[MenuEntryInfo],
) -> None:
    for entry in entries:
        if entry.path.exists():
            entry.path.unlink()


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
    write_text(spec.path / "start.sh", build_start_script(spec), executable=True)
    if spec.child_lock:
        lock_path = spec.path / "child-lock.json"
        write_json(lock_path, spec.child_lock)
        lock_path.chmod(0o600)
        write_text(
            spec.path / "browser_lock.py",
            build_browser_lock_helper(),
            executable=True,
        )
    write_text(spec.path / "backup.sh", build_backup_script(spec), executable=True)
    write_text(spec.path / "README.md", build_container_readme(spec))
    icon_path, warning = prepare_container_icon(spec)
    if warning:
        print(f"Warnung: {spec.name}: {warning}")
    write_text(
        spec.path / "launcher.desktop",
        build_launcher_content(spec, icon_path),
        executable=True,
    )
    return install_menu_entry(spec, applications_dir, icon_path)


def register_existing_container(
    container: DiscoveredContainer,
    applications_dir: Path,
) -> Path:
    effective_profile = get_effective_profile_path(container)
    if effective_profile is None:
        raise RuntimeError(f"{container.name}: Kein Profilpfad erkannt.")
    start_path = container.root_dir / "start.sh"
    if not start_path.exists():
        write_text(
            start_path,
            build_existing_start_script(container, effective_profile),
            executable=True,
        )
    spec = build_register_existing_spec(container)
    icon_path, warning = prepare_container_icon(spec)
    if warning:
        print(f"Warnung: {container.name}: {warning}")
    launcher_path = container.root_dir / "launcher.desktop"
    if not launcher_path.exists():
        write_text(
            launcher_path,
            build_existing_launcher_content(
                container,
                get_menu_name(spec),
                icon_path,
            ),
            executable=True,
        )
    return install_existing_menu_entry(container, applications_dir, icon_path)


def refresh_existing_container(
    container: DiscoveredContainer,
    applications_dir: Path,
) -> Path:
    effective_profile = get_effective_profile_path(container)
    if effective_profile is None:
        raise RuntimeError(f"{container.name}: Kein Profilpfad erkannt.")
    start_path = container.root_dir / "start.sh"
    if start_path.exists():
        backup_existing_file(start_path)
    write_text(
        start_path,
        build_existing_start_script(container, effective_profile),
        executable=True,
    )
    spec = build_register_existing_spec(container)
    icon_path, warning = prepare_container_icon(spec)
    if warning:
        print(f"Warnung: {container.name}: {warning}")
    launcher_path = container.root_dir / "launcher.desktop"
    if launcher_path.exists():
        backup_existing_file(launcher_path)
    write_text(
        launcher_path,
        build_existing_launcher_content(
            container,
            get_menu_name(spec),
            icon_path,
        ),
        executable=True,
    )
    return install_existing_menu_entry(container, applications_dir, icon_path)


def repair_existing_policy_container(container: DiscoveredContainer) -> None:
    spec = build_repair_policy_spec(container)
    policies_payload = build_policies_payload(spec)
    user_js_content = build_user_js_content(spec)
    root_policy = container.root_dir / "policies.json"
    root_user_js = container.root_dir / "user.js"
    distribution_dir = container.root_dir / "firefox" / "distribution"
    distribution_policy = distribution_dir / "policies.json"
    effective_profile = get_effective_profile_path(container)

    for path in [root_policy, root_user_js, distribution_policy]:
        if path.exists():
            backup_existing_file(path)

    write_json(root_policy, policies_payload)
    distribution_dir.mkdir(parents=True, exist_ok=True)
    write_json(distribution_policy, policies_payload)
    write_text(root_user_js, user_js_content)

    if effective_profile is not None:
        try:
            effective_profile.relative_to(container.root_dir)
        except ValueError:
            return
        profile_user_js = effective_profile / "user.js"
        if profile_user_js.exists():
            backup_existing_file(profile_user_js)
        effective_profile.mkdir(parents=True, exist_ok=True)
        write_text(profile_user_js, user_js_content)


def uninstall_container(
    container: DiscoveredContainer,
    applications_dir: Path,
    base_dir: Path,
) -> Path:
    if is_firefox_base_dir_name(container.name):
        raise ValueError(
            "Die Firefox-Basis ist geschützt und kann nicht als Container "
            "deinstalliert werden."
        )
    associated = [
        entry
        for entry in list_managed_menu_entries(applications_dir)
        if entry.container_root == container.root_dir
        or entry.container_name == container.name
    ]
    uninstall_root = get_uninstall_base_dir(base_dir) / datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    uninstall_root.mkdir(parents=True, exist_ok=False)
    destination = uninstall_root / container.name
    shutil.move(str(container.root_dir), str(destination))
    remove_menu_entries(associated)
    return destination


def main(argv: list[str] | None = None, applications_dir: Path | None = None) -> int:
    args = parse_args(argv)
    base_dir = ensure_path(args.base_dir)
    inventory_path = ensure_path(args.inventory)
    effective_applications_dir = applications_dir or DEFAULT_APPLICATIONS_DIR
    mode_count = sum(
        [
            bool(args.register_existing),
            bool(args.refresh_existing),
            bool(args.repair_policy),
            bool(args.cleanup_menu),
            bool(args.list_installed),
            bool(args.uninstall),
        ]
    )

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(
            f"Base directory could not be created: {base_dir} ({exc})", file=sys.stderr
        )
        return 1
    if mode_count > 1:
        print(
            "Bitte genau einen Verwaltungsmodus gleichzeitig verwenden.",
            file=sys.stderr,
        )
        return 1

    discovered = discover_existing_containers(base_dir)
    profiles = discover_firefox_profiles(DEFAULT_PROFILE_BASE_DIRS)
    correlate_profiles(discovered, profiles)

    if args.list_installed:
        write_inventory(inventory_path, base_dir, discovered)
        dry_run_lines = build_list_installed_report(
            discovered, effective_applications_dir
        )
        source_problems = []
    elif args.cleanup_menu:
        write_inventory(inventory_path, base_dir, discovered)
        dry_run_lines, cleanup_targets = build_cleanup_menu_plan(
            effective_applications_dir
        )
        source_problems = []
    elif args.uninstall:
        write_inventory(inventory_path, base_dir, discovered)
        target_container = find_container_by_name(discovered, args.uninstall)
        if target_container is None:
            print(
                f"Unbekannter Containername fuer --uninstall: {args.uninstall}",
                file=sys.stderr,
            )
            return 1
        dry_run_lines = build_uninstall_plan(
            target_container, effective_applications_dir, base_dir
        )
        source_problems = []
    elif args.register_existing:
        candidates = get_register_existing_candidates(discovered)
        try:
            candidates, _ = filter_by_only(candidates, [], args.only)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_inventory(inventory_path, base_dir, candidates)
        dry_run_lines = build_register_existing_plan(
            candidates, effective_applications_dir
        )
        source_problems: list[str] = []
    elif args.refresh_existing:
        candidates = discovered
        try:
            candidates, _ = filter_by_only(candidates, [], args.only)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_inventory(inventory_path, base_dir, candidates)
        dry_run_lines = build_refresh_existing_plan(
            candidates, effective_applications_dir
        )
        source_problems = []
    elif args.repair_policy:
        candidates = discovered
        try:
            candidates, _ = filter_by_only(candidates, [], args.only)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        write_inventory(inventory_path, base_dir, candidates)
        dry_run_lines = build_repair_policy_plan(candidates)
        source_problems = []
    else:
        config_path = ensure_path(args.config)
        if not config_path.is_file():
            print(f"Config file not found: {config_path}", file=sys.stderr)
            return 1
        try:
            specs = load_config(config_path, base_dir)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 1
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
    if args.list_installed:
        return 0
    if not args.apply:
        print("")
        if args.register_existing:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echte Registrierung mit --apply starten."
            )
        elif args.refresh_existing:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echte Aktualisierung mit --apply starten."
            )
        elif args.repair_policy:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echte Policy-Reparatur mit --apply starten."
            )
        elif args.cleanup_menu:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echtes Menu-Cleanup mit --apply starten."
            )
        elif args.uninstall:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echte Deinstallation mit --apply starten."
            )
        else:
            print(
                "Keine Aenderungen ausgefuehrt. Fuer echte Erstellung mit --apply starten."
            )
        return 0

    try:
        if args.cleanup_menu:
            remove_menu_entries(cleanup_targets)
            backup_dir = base_dir
        elif args.uninstall:
            destination = uninstall_container(
                target_container, effective_applications_dir, base_dir
            )
            backup_dir = destination.parent
        elif args.register_existing:
            backup_dir = create_builder_backup(
                base_dir,
                inventory_path,
                [build_register_existing_spec(container) for container in candidates],
                dry_run_lines,
            )
            for container in candidates:
                register_existing_container(container, effective_applications_dir)
        elif args.refresh_existing:
            backup_dir = create_builder_backup(
                base_dir,
                inventory_path,
                [build_register_existing_spec(container) for container in candidates],
                dry_run_lines,
            )
            for container in candidates:
                refresh_existing_container(container, effective_applications_dir)
        elif args.repair_policy:
            backup_dir = create_builder_backup(
                base_dir,
                inventory_path,
                [build_repair_policy_spec(container) for container in candidates],
                dry_run_lines,
            )
            for container in candidates:
                repair_existing_policy_container(container)
        else:
            ensure_apply_safe(specs)
            backup_dir = create_builder_backup(
                base_dir, inventory_path, specs, dry_run_lines
            )
            for spec in specs:
                create_container(spec, effective_applications_dir)
    except Exception as exc:  # pragma: no cover - surfaced to the user
        print(str(exc), file=sys.stderr)
        return 1

    print("")
    print(f"Backup angelegt unter: {backup_dir}")
    if args.cleanup_menu:
        print("Menueeintraege wurden bereinigt.")
    elif args.uninstall:
        print("Container wurde in das Uninstall-Backup verschoben.")
    elif args.register_existing:
        print("Bestehende Container wurden registriert.")
    elif args.refresh_existing:
        print("Bestehende Launcher/Icon-Artefakte wurden aktualisiert.")
    elif args.repair_policy:
        print("Bestehende Policy/User.js-Artefakte wurden aktualisiert.")
    else:
        print("Container wurden erstellt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
