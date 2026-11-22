"""Versioned personal backups. No system registrations, commands or trust import."""

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
import tempfile

from netmon.config.constants import NETMON_APP_VERSION
from netmon.core.import_limits import _JSON_STRING
from netmon.core.private_logs import _private_directory
from netmon.core.private_state import private_state_lock
from netmon.core.user_files import _open_source, _mapped

MANIFEST = "netmon_documents_backup_manifest.json"
FORMAT = "netmon-user-backup"
FORMAT_VERSION = 1
DATA_VERSION = 1
MAX_ENTRIES = 150_000
MAX_FILE_BYTES = 8 * 1024**3
MAX_TOTAL_BYTES = 64 * 1024**3
MAX_MANIFEST_BYTES = 32 * 1024**2
MAX_JSON_BYTES = 32 * 1024**2
ARCHIVE_AREAS = {"Security", "Logs", "diagnostics", "support"}
_EXCLUDED_ROOTS = {"Migration", "Wiederherstellungen"}


class BackupError(ValueError):
    """A backup is incomplete, unsupported, unsafe or changed since preview."""


class PartialRestoreError(BackupError):
    """Canonical writes started; retain the in-process write freeze until exit."""


def _absolute(path):
    path = Path(path)
    if ".." in path.parts:
        raise BackupError("Unsicherer Ordnerpfad.")
    return Path(os.path.abspath(path))


def _relative(value):
    if not isinstance(value, str) or len(value) > 4096:
        raise BackupError("Ungültiger Dateipfad im Sicherungsinventar.")
    try:
        value.encode("utf-8")
    except UnicodeError as exc:
        raise BackupError("Ungültiger UTF-8-Dateipfad.") from exc
    parts = value.split("/")
    if (
        not value
        or len(parts) > 64
        or any(p in {"", ".", ".."} or len(p.encode()) > 255 for p in parts)
        or "\\" in value
        or any(ord(c) < 32 or ord(c) == 127 for c in value)
    ):
        raise BackupError("Unsicherer Dateipfad im Sicherungsinventar.")
    return PurePosixPath(value)


def _identity(info):
    return tuple(
        getattr(info, "st_" + key)
        for key in (
            "dev",
            "ino",
            "uid",
            "mode",
            "nlink",
            "size",
            "mtime_ns",
            "ctime_ns",
        )
    )


@contextmanager
def _directory(path):
    """Read-only descriptor walk; never follow directory links or chmod input."""
    path = _absolute(path)
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    fd = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _read_file(path, *, collect=False, limit=MAX_FILE_BYTES, private=False):
    with os.fdopen(_open_source(path), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise BackupError("Keine einzelne reguläre Datei: " + str(path))
        if private and (before.st_uid != os.geteuid() or before.st_mode & 0o022):
            raise BackupError("Unsichere Zieldateirechte: " + str(path))
        if before.st_size > limit:
            raise BackupError("Datei überschreitet das Größenlimit: " + str(path))
        digest, chunks = hashlib.sha256(), []
        remaining = before.st_size
        while remaining:
            chunk = stream.read(min(1024**2, remaining))
            if not chunk:
                raise BackupError("Datei wurde beim Lesen verändert: " + str(path))
            remaining -= len(chunk)
            digest.update(chunk)
            if collect:
                chunks.append(chunk)
        if _identity(before) != _identity(os.fstat(stream.fileno())):
            raise BackupError("Datei wurde beim Lesen verändert: " + str(path))
        return digest.hexdigest(), before, b"".join(chunks) if collect else None


def _skip(relative):
    parts = relative.parts
    if parts[0] in _EXCLUDED_ROOTS:
        return "Frühere Übernahme- und Wiederherstellungsberichte"
    if parts[0] == "projectM Visualizer" and ".netmon_projectm_flat_scan_v1" in parts:
        return "Erzeugter projectM-Suchordner"
    if parts[-1].endswith(".lock") or parts[-1] in {"lock", ".parentlock"}:
        return "Technische Prozesssperre"
    return ""


def _walk(root, *, selected=None, exclusions=False):
    directories, files, skipped = [], [], []
    count, total = 0, 0

    def visit(fd, parent):
        nonlocal count, total
        with os.scandir(fd) as scan:
            for item in scan:
                count += 1
                if count > MAX_ENTRIES:
                    raise BackupError("Zu viele Sicherungseinträge.")
                relative = parent / item.name
                _relative(str(relative))
                if selected is not None and relative.parts[0] not in selected:
                    continue
                if exclusions and (reason := _skip(relative)):
                    skipped.append({"path": str(relative), "reason": reason})
                    continue
                info = item.stat(follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    directories.append(str(relative))
                    child = os.open(
                        item.name,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=fd,
                    )
                    try:
                        if (info.st_dev, info.st_ino) != (
                            os.fstat(child).st_dev,
                            os.fstat(child).st_ino,
                        ):
                            raise BackupError("Ordner wurde beim Prüfen verändert.")
                        visit(child, relative)
                    finally:
                        os.close(child)
                elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                    total += info.st_size
                    if info.st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                        raise BackupError("Sicherung überschreitet das Größenlimit.")
                    files.append((str(relative), info))
                else:
                    raise BackupError(
                        "Verknüpfung oder Spezialdatei ist nicht sicherbar: "
                        + str(relative)
                    )

    with _directory(root) as fd:
        visit(fd, PurePosixPath())
    return sorted(directories), sorted(files), sorted(skipped, key=lambda x: x["path"])


def _write_new(path, payload, mode=0o600):
    """Publish complete private bytes without replacing any existing name."""
    with _private_directory(path.parent) as fd:
        temporary = ".netmon-backup-" + secrets.token_hex(12)
        out = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            mode,
            dir_fd=fd,
        )
        try:
            with os.fdopen(out, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fchmod(stream.fileno(), mode)
                os.fsync(stream.fileno())
            os.link(
                temporary,
                path.name,
                src_dir_fd=fd,
                dst_dir_fd=fd,
                follow_symlinks=False,
            )
        finally:
            os.unlink(temporary, dir_fd=fd)
            os.fsync(fd)


def _copy_new(source, destination, expected, mode=0o600, *, durable=True):
    """Stream to a temporary name, verify, then publish with create-only semantics."""
    with os.fdopen(_open_source(source), "rb") as incoming:
        before = os.fstat(incoming.fileno())
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > MAX_FILE_BYTES
        ):
            raise BackupError("Unsichere Quelldatei.")
        with _private_directory(destination.parent) as directory:
            name = ".netmon-backup-" + secrets.token_hex(12)
            fd = os.open(
                name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                mode,
                dir_fd=directory,
            )
            try:
                digest = hashlib.sha256()
                with os.fdopen(fd, "wb") as outgoing:
                    remaining = before.st_size
                    while remaining:
                        chunk = incoming.read(min(1024**2, remaining))
                        if not chunk:
                            raise BackupError("Quelldatei wurde verändert.")
                        outgoing.write(chunk)
                        digest.update(chunk)
                        remaining -= len(chunk)
                    outgoing.flush()
                    os.fchmod(outgoing.fileno(), mode)
                    if durable:
                        os.fsync(outgoing.fileno())
                if digest.hexdigest() != expected or _identity(before) != _identity(
                    os.fstat(incoming.fileno())
                ):
                    raise BackupError("Prüfsumme stimmt nicht; Quelle wurde verändert.")
                os.link(
                    name,
                    destination.name,
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                    follow_symlinks=False,
                )
            finally:
                os.unlink(name, dir_fd=directory)
                if durable:
                    os.fsync(directory)


def _json_bytes(value):
    return (
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def _stamp():
    return (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + secrets.token_hex(4)
    )


def _progress(callback, phase, count, total):
    if callback is not None and (count % 100 == 0 or count == total):
        callback(phase, count, total)


def export_backup(source_root, destination_parent, *, selected=None, progress=None):
    root, parent = _absolute(source_root), _absolute(destination_parent)
    if parent == root or root in parent.parents:
        raise BackupError(
            "Das Sicherungsziel muss außerhalb des NetMon-Ordners liegen."
        )
    if selected is not None:
        selected = tuple(sorted(set(selected)))
        if not selected or any(
            len(_relative(name).parts) != 1 or name in _EXCLUDED_ROOTS
            for name in selected
        ):
            raise BackupError("Ungültige Ordnerauswahl.")
        with _directory(root) as fd:
            for name in selected:
                info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                if not stat.S_ISDIR(info.st_mode):
                    raise BackupError("Ausgewählter Ordner fehlt: " + name)
    dirs, files, skipped = _walk(root, selected=selected, exclusions=True)
    backup = parent / ("netmon_documents_backup_" + _stamp())
    # Check the chosen parent by descriptors; only the new child is tightened.
    with _directory(parent) as fd:
        os.mkdir(backup.name, 0o700, dir_fd=fd)
    with _private_directory(backup):
        pass
    payload = backup / "NetMon"
    with _private_directory(payload):
        pass
    records = []
    for name in dirs:
        with _private_directory(payload / name):
            pass
    for name, scanned in files:
        checksum, info, _ = _read_file(root / name)
        if _identity(info) != _identity(scanned):
            raise BackupError("Quelle wurde während des Exports verändert: " + name)
        executable = bool(info.st_mode & 0o111)
        _copy_new(root / name, payload / name, checksum, 0o700 if executable else 0o600)
        records.append(
            {
                "path": name,
                "size": info.st_size,
                "sha256": checksum,
                "executable": executable,
            }
        )
        _progress(progress, "export", len(records), len(files))
    # A growing/changing selection must not be advertised as a complete snapshot.
    final_dirs, final_files, _ = _walk(root, selected=selected, exclusions=True)
    if dirs != final_dirs or [(n, _identity(i)) for n, i in files] != [
        (n, _identity(i)) for n, i in final_files
    ]:
        raise BackupError(
            "Quellordner wurde während des Exports verändert; bitte erneut sichern."
        )
    manifest = {
        "format": FORMAT,
        "format_version": FORMAT_VERSION,
        "data_version": DATA_VERSION,
        "app_version": NETMON_APP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(root),
        "kind": "full" if selected is None else "partial",
        "selection": list(selected) if selected is not None else [],
        "directories": dirs,
        "files": records,
        "excluded": skipped,
    }
    encoded = _json_bytes(manifest)
    if len(encoded) > MAX_MANIFEST_BYTES:
        raise BackupError("Sicherungsinventar ist zu groß.")
    _write_new(backup / MANIFEST, encoded)
    return backup


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError("Doppelter JSON-Eintrag.")
        result[key] = value
    return result


def _parse_json(payload):
    try:
        text = payload.decode("utf-8")
        skeleton = _JSON_STRING.sub("", text)
        if skeleton.count("[") + skeleton.count("{") > MAX_ENTRIES * 3:
            raise BackupError("Zu viele JSON-Strukturen.")
        return json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                BackupError("Ungültige JSON-Zahl.")
            ),
        )
    except (ValueError, RecursionError, UnicodeError) as exc:
        raise BackupError("Ungültige oder zu tief verschachtelte JSON-Datei.") from exc


def _inventory(backup):
    try:
        checksum, _, raw = _read_file(
            backup / MANIFEST, collect=True, limit=MAX_MANIFEST_BYTES
        )
    except FileNotFoundError as exc:
        raise BackupError(
            "Kein versioniertes Sicherungsinventar gefunden. Alte Sicherungen bitte mit der neuen Exportfunktion erneut erstellen."
        ) from exc
    manifest = _parse_json(raw)
    keys = {
        "format",
        "format_version",
        "data_version",
        "app_version",
        "created_at",
        "source_root",
        "kind",
        "selection",
        "directories",
        "files",
        "excluded",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != keys
        or manifest.get("format") != FORMAT
    ):
        raise BackupError(
            "Unbekanntes oder altes Sicherungsformat; eine nachträgliche Hashbestätigung ist nicht möglich."
        )
    if (
        type(manifest["format_version"]) is not int
        or manifest["format_version"] != FORMAT_VERSION
        or type(manifest["data_version"]) is not int
        or manifest["data_version"] != DATA_VERSION
    ):
        raise BackupError(
            "Diese Sicherungs-/Datenformatversion wird nicht unterstützt."
        )
    for key in ("app_version", "created_at", "source_root"):
        value = manifest[key]
        if (
            not isinstance(value, str)
            or not value
            or len(value) > 4096
            or any(ord(c) < 32 for c in value)
        ):
            raise BackupError("Ungültige Sicherungsmetadaten.")
    if (
        not Path(manifest["source_root"]).is_absolute()
        or ".." in Path(manifest["source_root"]).parts
        or Path(manifest["source_root"]) == Path("/")
    ):
        raise BackupError("Ungültiger Ursprungsordner.")
    if manifest["kind"] not in {"full", "partial"} or not isinstance(
        manifest["selection"], list
    ):
        raise BackupError("Ungültige Sicherungsauswahl.")
    selection = manifest["selection"]
    if (
        len(selection) > MAX_ENTRIES
        or any(
            not isinstance(s, str) or len(_relative(s).parts) != 1 for s in selection
        )
        or len(set(selection)) != len(selection)
    ):
        raise BackupError("Ungültige Sicherungsauswahl.")
    if (manifest["kind"] == "full" and selection) or (
        manifest["kind"] == "partial" and not selection
    ):
        raise BackupError("Unvollständige Sicherungsauswahl.")
    dirs, files = manifest["directories"], manifest["files"]
    if (
        not isinstance(dirs, list)
        or not isinstance(files, list)
        or len(dirs) + len(files) > MAX_ENTRIES
    ):
        raise BackupError("Ungültiges oder zu großes Sicherungsinventar.")
    names = set()
    for name in dirs:
        _relative(name)
        if name in names or _skip(PurePosixPath(name)):
            raise BackupError("Doppelter oder technischer Sicherungspfad.")
        names.add(name)
    file_names, total = set(), 0
    for record in files:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "size",
            "sha256",
            "executable",
        }:
            raise BackupError("Ungültiger Dateinachweis.")
        name = record["path"]
        _relative(name)
        if name in names or _skip(PurePosixPath(name)):
            raise BackupError("Doppelter oder technischer Sicherungspfad.")
        if (
            type(record["size"]) is not int
            or not 0 <= record["size"] <= MAX_FILE_BYTES
            or type(record["executable"]) is not bool
            or not isinstance(record["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", record["sha256"]) is None
        ):
            raise BackupError("Ungültige Dateigröße oder Prüfsumme.")
        total += record["size"]
        if total > MAX_TOTAL_BYTES:
            raise BackupError("Sicherung überschreitet das Größenlimit.")
        names.add(name)
        file_names.add(name)
    dir_names = set(dirs)
    for name in names:
        parts = PurePosixPath(name).parts
        if manifest["kind"] == "partial" and parts[0] not in selection:
            raise BackupError("Datei liegt außerhalb der ausgewählten Ordner.")
        if any(
            str(PurePosixPath(*parts[:i])) not in dir_names
            for i in range(1, len(parts))
        ):
            raise BackupError("Unvollständiges Ordnerinventar.")
    excluded = manifest["excluded"]
    if not isinstance(excluded, list) or len(excluded) > MAX_ENTRIES:
        raise BackupError("Ungültige Auslassungsliste.")
    for item in excluded:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "reason"}
            or not isinstance(item["reason"], str)
            or len(item["reason"]) > 200
        ):
            raise BackupError("Ungültige Auslassungsliste.")
        _relative(item["path"])
    actual_dirs, actual_files, _ = _walk(backup / "NetMon")
    if (
        set(actual_dirs) != set(dirs)
        or {name for name, _ in actual_files} != file_names
    ):
        raise BackupError(
            "Dateien fehlen oder liegen ohne Inventareintrag in der Sicherung."
        )
    return manifest, checksum


def _is_radio_playlist(relative):
    path = PurePosixPath(relative)
    return path.parts[0] == "Radio" and path.suffix.lower() in {".m3u", ".m3u8"}


def _transform_radio_playlist(raw, old_root, new_root):
    """Map only absolute internal file entries; preserve all other bytes."""
    if len(raw) > MAX_JSON_BYTES:
        raise BackupError("Playlistdatei ist zu groß für die Pfadanpassung.")
    source = os.fsencode(old_root.rstrip("/"))
    target = os.fsencode(str(new_root))
    lines = []
    for line in raw.splitlines(keepends=True):
        item = line.strip(b" \t\r\n")
        if item == source or item.startswith(source + b"/"):
            start = line.index(item)
            line = line[:start] + target + line[start + len(source) :]
        lines.append(line)
    updated = b"".join(lines)
    return updated, updated != raw


def _transform(relative, raw, old_root, new_root):
    if _is_radio_playlist(relative):
        return _transform_radio_playlist(raw, old_root, new_root)
    parts = PurePosixPath(relative).parts
    managed_json = relative.endswith(".json") and (
        parts[0] == "Config"
        or relative == "Radio/radio_settings.json"
        or relative == "LinuxHelp/reading.json"
        or parts[:2] == ("LinuxHelp", "meta")
    )
    if not managed_json:
        return raw, False
    if len(raw) > MAX_JSON_BYTES:
        raise BackupError("Einstellungsdatei ist zu groß: " + relative)
    value = _parse_json(raw)
    if relative == "LinuxHelp/reading.json" and (
        not isinstance(value, dict)
        or type(value.get("version")) is not int
        or value["version"] != 1
    ):
        raise BackupError("Unbekanntes Lesefortschritt-Format.")
    updated = _mapped(value, [(old_root.rstrip("/"), str(new_root))])
    return (_json_bytes(updated), True) if updated != value else (raw, False)


def _needs_transform(relative):
    parts = PurePosixPath(relative).parts
    return (
        _is_radio_playlist(relative)
        or relative.endswith(".json")
        and (
            parts[0] == "Config"
            or relative in {"Radio/radio_settings.json", "LinuxHelp/reading.json"}
            or parts[:2] == ("LinuxHelp", "meta")
        )
    )


def _target_snapshot(path):
    try:
        digest, info, _ = _read_file(path, private=True)
        return _identity(info), digest
    except FileNotFoundError:
        return None, None


@dataclass(frozen=True)
class RestoreEntry:
    path: str
    size: int
    sha256: str
    executable: bool
    output_sha256: str
    output_size: int
    adapted: bool
    action: str
    target_identity: tuple | None


@dataclass(frozen=True)
class RestorePlan:
    backup: Path
    target: Path
    manifest_sha256: str
    source_root: str
    app_version: str
    kind: str
    entries: tuple[RestoreEntry, ...]
    directories: tuple[str, ...]
    excluded: tuple[str, ...]


def preview_restore(backup, target, *, progress=None):
    """Read-only full inventory/hash validation, path adaptation and target comparison."""
    backup, target = _absolute(backup), _absolute(target)
    if backup == target or backup in target.parents or target in backup.parents:
        raise BackupError(
            "Sicherung und Wiederherstellungsziel müssen getrennt liegen."
        )
    manifest, manifest_hash = _inventory(backup)
    # Empty directories need validation too; preview never creates or chmods them.
    for name in manifest["directories"]:
        if PurePosixPath(name).parts[0] in ARCHIVE_AREAS:
            continue
        try:
            with _directory(target / name) as fd:
                info = os.fstat(fd)
                if info.st_uid != os.geteuid() or info.st_mode & 0o022:
                    raise BackupError("Unsichere Zielordnerrechte: " + name)
        except FileNotFoundError:
            pass
    entries = []
    for record in manifest["files"]:
        name = record["path"]
        collect = _needs_transform(name)
        digest, info, raw = _read_file(
            backup / "NetMon" / name,
            collect=collect,
            limit=MAX_JSON_BYTES if collect else MAX_FILE_BYTES,
        )
        if digest != record["sha256"] or info.st_size != record["size"]:
            raise BackupError("Datei fehlt oder Prüfsumme stimmt nicht: " + name)
        adapted = False
        out_digest, out_size = digest, info.st_size
        if collect:
            raw, adapted = _transform(name, raw, manifest["source_root"], target)
            out_digest, out_size = hashlib.sha256(raw).hexdigest(), len(raw)
        identity = None
        if PurePosixPath(name).parts[0] in ARCHIVE_AREAS:
            action = "archive"
        else:
            identity, current = _target_snapshot(target / name)
            action = (
                "new"
                if identity is None
                else "identical" if current == out_digest else "conflict"
            )
        entries.append(
            RestoreEntry(
                name,
                info.st_size,
                digest,
                record["executable"],
                out_digest,
                out_size,
                adapted,
                action,
                identity,
            )
        )
        _progress(progress, "verify", len(entries), len(manifest["files"]))
    return RestorePlan(
        backup,
        target,
        manifest_hash,
        manifest["source_root"],
        manifest["app_version"],
        manifest["kind"],
        tuple(entries),
        tuple(manifest["directories"]),
        tuple(item["path"] for item in manifest["excluded"]),
    )


def _check_current(entry, path):
    identity, _ = _target_snapshot(path)
    if identity != entry.target_identity:
        raise BackupError(
            "Zieldatei hat sich seit der Vorschau verändert: " + entry.path
        )


def _save_report(path, report):
    """Only replace our freshly created private report, never an imported user file."""
    with _private_directory(path.parent) as directory:
        name = ".netmon-report-" + secrets.token_hex(12)
        _write_new(path.parent / name, _json_bytes(report))
        os.replace(name, path.name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)


def restore_backup(plan, *, replace_conflicts=False, progress=None):
    """Revalidate preview, stage all bytes, then publish checked private files."""
    if not isinstance(plan, RestorePlan):
        raise BackupError("Eine geprüfte Vorschau ist erforderlich.")
    current = preview_restore(plan.backup, plan.target, progress=progress)
    if current != plan:
        raise BackupError(
            "Sicherung oder Ziel hat sich seit der Vorschau verändert. Bitte erneut prüfen."
        )
    with tempfile.TemporaryDirectory(prefix="netmon-restore-") as temporary:
        staged = Path(temporary)
        for index, entry in enumerate(plan.entries, start=1):
            path = staged / entry.path
            _copy_new(
                plan.backup / "NetMon" / entry.path, path, entry.sha256, durable=False
            )
            if _needs_transform(entry.path):
                _, _, raw = _read_file(path, collect=True, limit=MAX_JSON_BYTES)
                updated, _ = _transform(entry.path, raw, plan.source_root, plan.target)
                if hashlib.sha256(updated).hexdigest() != entry.output_sha256:
                    raise BackupError("Pfadanpassung hat sich verändert.")
                # Staging is a new owner-only temporary tree, never a user path.
                with path.open("wb") as stream:
                    stream.write(updated)
            _progress(progress, "stage", index, len(plan.entries))
        if (
            _read_file(plan.backup / MANIFEST, collect=True, limit=MAX_MANIFEST_BYTES)[
                0
            ]
            != plan.manifest_sha256
        ):
            raise BackupError("Sicherungsinventar wurde nach der Vorschau verändert.")
        # No canonical data has been touched before all incoming bytes were staged.
        for entry in plan.entries:
            if entry.action != "archive":
                _check_current(entry, plan.target / entry.path)
        with _private_directory(plan.target):
            pass
        with private_state_lock(plan.target / ".netmon-restore.lock"):
            run = plan.target / "Wiederherstellungen" / _stamp()
            with _private_directory(run.parent) as directory:
                os.mkdir(run.name, 0o700, dir_fd=directory)
            with _private_directory(run):
                pass
            report_path = run / "bericht.json"
            report = {
                "format_version": FORMAT_VERSION,
                "app_version": NETMON_APP_VERSION,
                "source_app_version": plan.app_version,
                "source": str(plan.backup),
                "target": str(plan.target),
                "complete": False,
                "files": [],
                "errors": [],
                "restart_required": True,
            }
            _save_report(report_path, report)
            try:
                # Empty folders remain useful even when the backup contains no files.
                for name in plan.directories:
                    folder = (
                        run / "Pruefreferenzen" / name
                        if PurePosixPath(name).parts[0] in ARCHIVE_AREAS
                        else plan.target / name
                    )
                    with _private_directory(folder):
                        pass
                for entry in plan.entries:
                    target = plan.target / entry.path
                    mode = 0o700 if entry.executable else 0o600
                    if entry.action != "archive":
                        _check_current(entry, target)
                    action = entry.action
                    if action == "archive":
                        target = run / "Pruefreferenzen" / entry.path
                    elif action == "conflict" and not replace_conflicts:
                        target = run / "Konflikte" / entry.path
                        action = "kept"
                    elif action == "conflict":
                        original = run / "Originale" / entry.path
                        digest, original_info, _ = _read_file(target, private=True)
                        _copy_new(
                            target,
                            original,
                            digest,
                            0o700 if original_info.st_mode & 0o111 else 0o600,
                        )
                        _check_current(entry, target)
                        with _private_directory(target.parent) as directory:
                            name = ".netmon-replace-" + secrets.token_hex(12)
                            replacement = target.parent / name
                            try:
                                _copy_new(
                                    staged / entry.path,
                                    replacement,
                                    entry.output_sha256,
                                    mode,
                                )
                                _check_current(entry, target)
                                os.replace(
                                    name,
                                    target.name,
                                    src_dir_fd=directory,
                                    dst_dir_fd=directory,
                                )
                                os.fsync(directory)
                            finally:
                                try:
                                    os.unlink(name, dir_fd=directory)
                                except FileNotFoundError:
                                    pass
                        action = "replaced"
                    if action not in {"identical", "replaced"}:
                        _copy_new(
                            staged / entry.path, target, entry.output_sha256, mode
                        )
                    report["files"].append(
                        {
                            "path": entry.path,
                            "action": action,
                            "destination": str(target.relative_to(plan.target)),
                            "sha256": entry.output_sha256,
                            "adapted": entry.adapted,
                        }
                    )
                    _progress(
                        progress, "restore", len(report["files"]), len(plan.entries)
                    )
                # Do not resurrect old split-folder data on the first app start after a restore.
                marker = plan.target / "Migration/uebernahme-v1.json"
                if not marker.exists():
                    _write_new(
                        marker,
                        _json_bytes(
                            {
                                "version": 1,
                                "target": str(plan.target),
                                "complete": True,
                                "copied": 0,
                                "identical": 0,
                                "files": [],
                                "conflicts": [],
                                "skipped": [],
                                "rewritten": [],
                                "errors": [],
                            }
                        ),
                    )
                report["complete"] = True
                _save_report(report_path, report)
            except Exception as exc:
                report["errors"].append(str(exc))
                _save_report(report_path, report)
                raise PartialRestoreError(
                    "Wiederherstellung nicht vollständig. Bereits übernommene Dateien und Originale sind im Bericht dokumentiert: "
                    + str(report_path)
                ) from exc
    return report_path, report
