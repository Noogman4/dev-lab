"""Copy legacy personal data to the system Documents folder without replacing it."""

import hashlib
import json
import os
from pathlib import Path
import secrets
import stat

from netmon.core.import_limits import read_bounded_bytes
from netmon.core.private_logs import _private_directory
from netmon.core.private_state import private_state_lock
from netmon.core.state import get_netmon_documents_dir
from netmon.core.utils import safe_write_json

_PREPARED = set()
_REPORT = "Migration/uebernahme-v1.json"
_JSON_LIMIT = 32 * 1024 * 1024


def legacy_sources(target):
    home = Path.home()
    config = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config") / "netmon"
    state = Path(os.environ.get("XDG_STATE_HOME") or home / ".local/state") / "netmon"
    data = Path(os.environ.get("XDG_DATA_HOME") or home / ".local/share") / "netmon"
    sources = []
    for name in ("Documents", "Dokumente"):
        old = home / name / "NetMon"
        if old.absolute() != target.absolute():
            sources.append((old, Path(), name + "-NetMon"))
    sources += [
        (config, Path("Config"), "Config-alt"),
        (data / "fun", Path("Fun"), "Fun-alt"),
        (data / "wireguard", Path("WireGuard"), "WireGuard-alt"),
        (state / "captures", Path("Captures"), "Mitschnitte-alt"),
        (state / "radio_recordings", Path("Radio/Aufnahmen"), "Aufnahmen-alt"),
        (state / "radio_playlists", Path("Radio/Playlisten"), "Playlisten-alt"),
        (state / "logs", Path("Logs"), "Logs-alt"),
        (
            state / "linux_help_reading.json",
            Path("LinuxHelp/reading.json"),
            "Lesefortschritt-alt",
        ),
    ]
    for name in ("Bilder", "Pictures"):
        sources.append((home / name / "Log-Pics", Path("Log-Pics"), name + "-Log-Pics"))
    for name in ("radio_db.json", "radio_db_meta.json"):
        sources.append((state / name, Path("Radio") / name, "Radio-alt"))
    for name in (
        "netmon_radio_app.log",
        "radio_launcher_start.log",
        "startup_error.log",
    ):
        sources.append((state / name, Path("Logs") / name, "Protokolle-alt"))
    for name in ("radio_stations.json", "radio_favorites.json", "radio_settings.json"):
        sources.append((config / name, Path("Radio") / name, "Radio-Config-alt"))
    for name in (
        "security_baseline.json",
        "startup_guard_baseline.json",
        "repository_guard_baseline.json",
        "repository_guard_trustlist.json",
        "startup_guard_trustlist.json",
        "process_guard_trustlist.json",
        "roots_baseline_guard_baseline.json",
        "roots_baseline_guard_whitelist.json",
        "clamav_findings.json",
    ):
        sources.append((state / name, Path("Security") / name, "Security-alt"))
    return sources


def _open_source(path):
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    path = Path(path).absolute()
    directory = os.open("/", flags)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, flags, dir_fd=directory)
            os.close(directory)
            directory = child
        return os.open(
            path.name,
            os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
            dir_fd=directory,
        )
    finally:
        os.close(directory)


def _digest(path):
    with os.fdopen(_open_source(path), "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Keine reguläre Datei")
        digest = hashlib.sha256()
        remaining = info.st_size
        while remaining:
            chunk = stream.read(min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError("Quelldatei wurde während der Prüfung verändert")
            digest.update(chunk)
            remaining -= len(chunk)
        after = os.fstat(stream.fileno())
        if (info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("Quelldatei wurde während der Prüfung verändert")
        return digest.hexdigest()


def _copy_file(source, destination, root, label, report):
    """Publish one complete, private regular file, using exclusive hard-link creation."""
    with os.fdopen(_open_source(source), "rb") as incoming:
        before = os.fstat(incoming.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Keine reguläre Quelldatei")
        with _private_directory(destination.parent) as directory:
            temporary = ".netmon-copy-" + secrets.token_hex(12)
            descriptor = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            try:
                digest = hashlib.sha256()
                with os.fdopen(descriptor, "wb") as outgoing:
                    remaining = before.st_size
                    while remaining:
                        chunk = incoming.read(min(1024 * 1024, remaining))
                        if not chunk:
                            raise ValueError(
                                "Quelldatei wurde während des Kopierens verändert"
                            )
                        outgoing.write(chunk)
                        digest.update(chunk)
                        remaining -= len(chunk)
                    after = os.fstat(incoming.fileno())
                    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                        after.st_size,
                        after.st_mtime_ns,
                        after.st_ctime_ns,
                    ):
                        raise ValueError(
                            "Quelldatei wurde während des Kopierens verändert"
                        )
                    outgoing.flush()
                    os.fchmod(
                        outgoing.fileno(), 0o700 if before.st_mode & 0o111 else 0o600
                    )
                checksum = digest.hexdigest()
                try:
                    existing = os.stat(
                        destination.name, dir_fd=directory, follow_symlinks=False
                    )
                except FileNotFoundError:
                    existing = None
                if existing is None:
                    os.link(
                        temporary,
                        destination.name,
                        src_dir_fd=directory,
                        dst_dir_fd=directory,
                        follow_symlinks=False,
                    )
                    report["copied"] += 1
                    final = destination
                elif (
                    stat.S_ISREG(existing.st_mode) and _digest(destination) == checksum
                ):
                    report["identical"] += 1
                    report["files"].append(
                        {
                            "source": str(source),
                            "target": str(destination.relative_to(root)),
                            "sha256": checksum,
                        }
                    )
                    return
                else:
                    conflict = (
                        root
                        / "Migration/Konflikte"
                        / label
                        / destination.relative_to(root)
                    )
                    # Hash suffix makes multiple differing sources independently recoverable.
                    conflict = conflict.with_name(
                        conflict.stem + "-" + checksum[:16] + conflict.suffix
                    )
                    with _private_directory(conflict.parent) as conflicts:
                        try:
                            os.link(
                                temporary,
                                conflict.name,
                                src_dir_fd=directory,
                                dst_dir_fd=conflicts,
                                follow_symlinks=False,
                            )
                        except FileExistsError:
                            if _digest(conflict) != checksum:
                                raise ValueError(
                                    "Konfliktziel enthält bereits abweichende Daten"
                                )
                    report["conflicts"].append(str(conflict.relative_to(root)))
                    final = conflict
                report["files"].append(
                    {
                        "source": str(source),
                        "target": str(final.relative_to(root)),
                        "sha256": checksum,
                    }
                )
            finally:
                os.unlink(temporary, dir_fd=directory)


def _copy_tree(source, destination, root, label, report):
    if not source.exists() and not source.is_symlink():
        return
    if source.is_symlink():
        report["skipped"].append(str(source))
        return
    if source.is_file():
        _copy_file(source, destination, root, label, report)
        return

    def fail_walk(error):
        raise error

    for directory, dirs, files in os.walk(source, followlinks=False, onerror=fail_walk):
        folder = Path(directory)
        for name in list(dirs):
            if (folder / name).is_symlink() or name == "Migration":
                dirs.remove(name)
                report["skipped"].append(str(folder / name))
        for name in files:
            item = folder / name
            if item.is_symlink() or not item.is_file():
                report["skipped"].append(str(item))
                continue
            _copy_file(
                item, destination / item.relative_to(source), root, label, report
            )


def _mapped(value, mappings):
    if isinstance(value, str):
        expanded = os.path.expanduser(value)
        for source, target in mappings:
            if expanded == source or expanded.startswith(source + os.sep):
                return target + expanded[len(source) :]
        return value
    if isinstance(value, list):
        return [_mapped(item, mappings) for item in value]
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            mapped_key = _mapped(key, mappings)
            if mapped_key in result:
                raise ValueError(
                    "Zwei gespeicherte Pfade würden denselben Eintrag überschreiben"
                )
            result[mapped_key] = _mapped(item, mappings)
        return result
    return value


def _rewrite_paths(root, sources, report):
    mappings = sorted(
        [(str(source), str(root / relative)) for source, relative, _ in sources],
        key=lambda pair: -len(pair[0]),
    )
    mappings.extend(
        (str(folder), str(root / "Log-Pics"))
        for folder in (
            Path("/usr/share/netmon/assets/log-pics"),
            Path("/opt/netmon/assets/log-pics"),
            Path("/opt/netmon-dark/assets/log-pics"),
            Path(__file__).resolve().parents[2] / "tools/Log-Pics",
        )
    )
    candidates = (
        list((root / "Config").glob("*.json"))
        + list((root / "Radio").glob("*settings.json"))
        + list((root / "LinuxHelp/meta").glob("*.json"))
    )
    for path in candidates:
        payload = read_bounded_bytes(path, _JSON_LIMIT, label="Pfadübernahme")
        value = json.loads(payload)
        updated = _mapped(value, mappings)
        if updated == value:
            continue
        original = root / "Migration/Originale" / path.relative_to(root)
        _copy_file(path, original, root, "Vor-Pfadanpassung", report)
        ok, error = safe_write_json(path, updated, indent=2, ensure_ascii=False)
        if not ok:
            raise OSError(error)
        report["rewritten"].append(
            {"path": str(path.relative_to(root)), "sha256": _digest(path)}
        )


def _asset_sources():
    candidates = [
        Path("/usr/share/netmon/assets/log-pics"),
        Path("/opt/netmon-dark/assets/log-pics"),
        Path(__file__).resolve().parents[2] / "tools/Log-Pics",
    ]
    return next((folder for folder in candidates if folder.is_dir()), None)


def _migrate_user_files(root, *, assets=True):
    """Copy once. Existing targets win; originals and conflicts are preserved."""
    root = Path(root or get_netmon_documents_dir()).absolute()
    with _private_directory(root):
        pass
    for name in (
        "Config",
        "Security",
        "Radio",
        "Radio/Aufnahmen",
        "Radio/Playlisten",
        "Fun",
        "WireGuard",
        "Log-Pics",
        "LinuxHelp",
        "Captures",
        "Logs",
        "Migration",
    ):
        with _private_directory(root / name):
            pass
    marker = root / _REPORT
    old = {}
    if marker.exists():
        old = json.loads(
            read_bounded_bytes(marker, 32 * 1024 * 1024, label="Übernahmebericht")
        )
    completed = (
        old.get("version") == 1
        and old.get("target") == str(root)
        and old.get("complete") is True
    )
    report = (
        old
        if completed
        else {
            "version": 1,
            "target": str(root),
            "complete": False,
            "copied": 0,
            "identical": 0,
            "files": [],
            "conflicts": [],
            "skipped": [],
            "rewritten": [],
            "errors": [],
        }
    )
    sources = legacy_sources(root)
    if not completed:
        for source, relative, label in sources:
            try:
                _copy_tree(source, root / relative, root, label, report)
            except (OSError, ValueError) as exc:
                report["errors"].append({"source": str(source), "error": str(exc)})
        try:
            _rewrite_paths(root, sources, report)
        except (OSError, ValueError) as exc:
            report["errors"].append({"source": "Pfadanpassung", "error": str(exc)})
    if assets and (folder := _asset_sources()) is not None:
        for image in folder.iterdir():
            if (
                image.suffix.lower() not in {".png", ".jpg", ".jpeg"}
                or image.is_symlink()
            ):
                continue
            destination = root / "Log-Pics" / image.name
            if destination.exists() or destination.is_symlink():
                continue
            try:
                _copy_file(image, destination, root, "Paketbilder", report)
            except (OSError, ValueError) as exc:
                report["errors"].append({"source": str(image), "error": str(exc)})
    report["complete"] = not report["errors"]
    ok, error = safe_write_json(marker, report, indent=2, ensure_ascii=False)
    if not ok:
        raise OSError(error)
    return report


def migrate_user_files(root=None, *, assets=True):
    """Serialize first-use preparation across the main app and standalone Radio."""
    root = Path(root or get_netmon_documents_dir()).absolute()
    with _private_directory(root):
        pass
    with _private_directory(root / "Migration"):
        pass
    with private_state_lock(root / "Migration/.uebernahme.lock"):
        return _migrate_user_files(root, assets=assets)


def prepare_user_files():
    root = get_netmon_documents_dir()
    if root in _PREPARED:
        return
    report = migrate_user_files(root)
    if not report["complete"]:
        raise RuntimeError(
            "NetMon-Benutzerdateien konnten nicht vollständig übernommen werden. Bericht: "
            + str(Path(root) / _REPORT)
        )
    _PREPARED.add(root)
