#!/usr/bin/env python3
"""Create authenticated dev-lab backups and restore only authorized regular files."""

from __future__ import annotations

import argparse
import base64
import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = {
    "project": "dev-lab-project",
    "vscode": "vscode-settings",
    "configs": "dev-configs",
}
FORMAT = "dev-lab-backup-v1"
MAX_MANIFEST = 64 * 1024 * 1024
MAX_MEMBERS = 200_000
MAX_FILE = 8 * 1024**3
MAX_TOTAL = 64 * 1024**3
NOFOLLOW = os.O_NOFOLLOW | os.O_CLOEXEC


class BackupError(Exception):
    """An input failed authentication, authorization, or safe filesystem handling."""


def absolute(path: Path) -> Path:
    return Path(os.path.abspath(path))


def policy(project: Path, home: Path) -> dict:
    project, home = absolute(project), absolute(home)
    if project == Path("/") or home == Path("/"):
        raise BackupError("Projekt- und Home-Pfad duerfen nicht / sein.")
    return {
        "project": [(project, True)],
        "vscode": [
            (project / ".vscode", True),
            (home / ".vscode-server/data/Machine", True),
            (home / ".vscode-server/data/User", True),
        ],
        "configs": [
            (project / "AGENTS.md", False),
            (home / ".codex", True),
            (home / ".bashrc", False),
            (home / ".profile", False),
        ],
    }


def member_path(name: str, kind: str) -> str:
    if kind == "directory" and name.endswith("/"):
        name = name[:-1]
    if (
        not name
        or len(name) > 4096
        or "\\" in name
        or any(ord(char) < 32 or ord(char) == 127 for char in name)
        or any(part in ("", ".", "..") for part in name.split("/"))
    ):
        raise BackupError(f"Nicht normalisierter Archivpfad: {name!r}")
    return name


def authorize(name: str, kind: str, category: str, rules: dict) -> None:
    if kind not in ("file", "directory"):
        raise BackupError(f"Verbotener Dateityp: {kind!r}")
    if member_path(name, kind) != name:
        raise BackupError(f"Nicht normalisierter Manifestpfad: {name!r}")
    for source, subtree in rules[category]:
        prefix = source.relative_to("/").as_posix()
        if subtree and (name == prefix or name.startswith(prefix + "/")):
            return
        if not subtree and kind == "file" and name == prefix:
            return
    raise BackupError(f"Pfad fuer Kategorie {category} nicht erlaubt: {name!r}")


@contextlib.contextmanager
def regular_file(path: Path):
    fd = os.open(path, os.O_RDONLY | NOFOLLOW | os.O_NONBLOCK)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise BackupError(f"Keine regulaere Datei: {path}")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            yield stream
    finally:
        os.close(fd)


def read_small(path: Path, limit: int) -> bytes:
    with regular_file(path) as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise BackupError(f"Datei zu gross: {path}")
    return data


def transfer(source, destination=None, *, limit=MAX_TOTAL) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    while data := source.read(1024 * 1024):
        size += len(data)
        if size > limit:
            raise BackupError("Groessenlimit ueberschritten.")
        digest.update(data)
        if destination is not None:
            destination.write(data)
    return size, digest.hexdigest()


def run_minisign(arguments: list[str]) -> None:
    # Keep signing prompts visible so encrypted personal backup keys remain usable.
    signing = "-S" in arguments
    result = subprocess.run(
        ["minisign", *arguments], check=False, capture_output=not signing, text=True
    )
    if result.returncode:
        raise BackupError(f"Minisign fehlgeschlagen: {(result.stderr or '').strip()}")


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise BackupError(f"Doppelter Manifest-Key: {key!r}")
        result[key] = value
    return result


def authenticate(backup: Path, key_file: Path, temporary: Path) -> dict:
    if key_file.resolve().is_relative_to(backup.resolve()):
        raise BackupError(
            "Der vertrauenswuerdige Public Key muss ausserhalb des Backups liegen."
        )
    lines = read_small(key_file, 4096).decode("ascii").splitlines()
    if len(lines) != 2 or not lines[0].startswith("untrusted comment: "):
        raise BackupError("Ungueltige Public-Key-Datei.")
    decoded = base64.b64decode(lines[1], validate=True)
    if len(decoded) != 42 or decoded[:2] != b"Ed":
        raise BackupError("Ungueltiger Minisign Public Key.")
    manifest = temporary / "manifest.json"
    signature = temporary / "manifest.json.minisig"
    # Verify private snapshots; never parse or re-read mutable originals afterward.
    manifest.write_bytes(read_small(backup / manifest.name, MAX_MANIFEST))
    signature.write_bytes(read_small(backup / signature.name, 16384))
    run_minisign(["-V", "-P", lines[1], "-m", str(manifest), "-x", str(signature)])
    return json.loads(manifest.read_bytes(), object_pairs_hook=no_duplicate_keys)


def valid_size(value, limit: int) -> bool:
    return type(value) is int and 0 <= value <= limit


def valid_digest(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value) is not None


def validate_manifest(manifest: dict, backup: Path, rules: dict) -> list[dict]:
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"format", "archives"}
        or manifest["format"] != FORMAT
        or not isinstance(manifest["archives"], list)
        or not 1 <= len(manifest["archives"]) <= len(PREFIXES)
    ):
        raise BackupError("Ungueltiges oder nicht unterstuetztes Backup-Manifest.")
    names, categories = set(), set()
    total_size = total_members = 0
    for archive in manifest["archives"]:
        if not isinstance(archive, dict) or set(archive) != {
            "name",
            "category",
            "size",
            "sha256",
            "members",
        }:
            raise BackupError("Ungueltiger Archiveintrag im Manifest.")
        category = archive["category"]
        if not isinstance(category, str) or category not in PREFIXES:
            raise BackupError("Unbekannte Archivkategorie.")
        name = archive["name"]
        pattern = re.escape(PREFIXES[category]) + r"-\d{4}-\d{2}-\d{2}-\d{6}\.tar\.gz"
        if (
            not isinstance(name, str)
            or re.fullmatch(pattern, name) is None
            or name in names
            or category in categories
            or not valid_size(archive["size"], MAX_TOTAL)
            or not valid_digest(archive["sha256"])
            or not isinstance(archive["members"], list)
            or not archive["members"]
        ):
            raise BackupError("Ungueltiger oder mehrdeutiger Archiveintrag.")
        names.add(name)
        categories.add(category)
        paths = set()
        for member in archive["members"]:
            if not isinstance(member, dict) or set(member) != {
                "path",
                "type",
                "size",
                "sha256",
                "mode",
            }:
                raise BackupError("Ungueltiger Mitgliedseintrag im Manifest.")
            path, kind = member["path"], member["type"]
            if not isinstance(path, str):
                raise BackupError("Ungueltiger Mitgliedspfad.")
            authorize(path, kind, category, rules)
            if (
                path in paths
                or not valid_size(member["size"], MAX_FILE)
                or type(member["mode"]) is not int
                or member["mode"] not in (0o600, 0o700)
                or (kind == "file" and not valid_digest(member["sha256"]))
                or (
                    kind == "directory"
                    and (
                        member["size"] != 0
                        or member["sha256"] is not None
                        or member["mode"] != 0o700
                    )
                )
            ):
                raise BackupError("Ungueltiges oder doppeltes Archivmitglied.")
            paths.add(path)
            total_size += member["size"]
            total_members += 1
            if total_size > MAX_TOTAL or total_members > MAX_MEMBERS:
                raise BackupError("Backup-Limit ueberschritten.")
    actual = {path.name for path in backup.iterdir() if path.name.endswith(".tar.gz")}
    if actual != names:
        raise BackupError(
            "Archivdateien stimmen nicht mit dem signierten Manifest ueberein."
        )
    return manifest["archives"]


def inspect_archive(path: Path, category: str, rules: dict, staging=None) -> list[dict]:
    records, seen = [], set()
    total_size = 0
    with tarfile.open(path, mode="r|gz") as archive:
        for item in archive:
            if (
                item.type not in (tarfile.REGTYPE, tarfile.AREGTYPE, tarfile.DIRTYPE)
                or item.sparse is not None
            ):
                raise BackupError(
                    f"Links, Spezialdateien und Sparse-Dateien sind verboten: {item.name!r}"
                )
            kind = "directory" if item.isdir() else "file"
            name = member_path(item.name, kind)
            authorize(name, kind, category, rules)
            if (
                name in seen
                or len(seen) >= MAX_MEMBERS
                or not valid_size(item.size, MAX_FILE)
            ):
                raise BackupError(
                    "Doppeltes Archivmitglied oder Groessenlimit ueberschritten."
                )
            if kind == "directory" and item.size != 0:
                raise BackupError("Verzeichnis mit Nutzdaten ist verboten.")
            seen.add(name)
            total_size += item.size
            if total_size > MAX_TOTAL:
                raise BackupError("Backup-Limit ueberschritten.")
            mode = 0o700 if kind == "directory" else 0o600 | (item.mode & 0o100)
            target = staging / name if staging is not None else None
            digest = None
            if kind == "directory":
                if target is not None:
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
            else:
                with archive.extractfile(item) as source:
                    if target is not None:
                        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                        with target.open("xb") as destination:
                            os.chmod(target, 0o600)
                            size, digest = transfer(
                                source, destination, limit=item.size
                            )
                    else:
                        size, digest = transfer(source, limit=item.size)
                if size != item.size:
                    raise BackupError("Unvollstaendiges Archivmitglied.")
            records.append(
                {
                    "path": name,
                    "type": kind,
                    "size": item.size,
                    "sha256": digest,
                    "mode": mode,
                }
            )
    if not records:
        raise BackupError("Leeres Archiv.")
    return records


@contextlib.contextmanager
def directory_fd(path: Path, *, create=False):
    """Walk every component with directory descriptors, refusing all symlinks."""
    # O_PATH requires search permission, not permission to list ancestor contents.
    flags = os.O_PATH | os.O_DIRECTORY | NOFOLLOW
    fd = os.open("/", flags)
    try:
        for part in absolute(path).parts[1:]:
            try:
                next_fd = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield fd
    finally:
        os.close(fd)


def check_leaf(parent_fd: int, name: str, kind: str) -> None:
    try:
        existing = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except FileNotFoundError:
        return
    if kind == "directory" and stat.S_ISDIR(existing.st_mode):
        return
    if kind == "file" and stat.S_ISREG(existing.st_mode) and existing.st_nlink == 1:
        return
    raise BackupError(f"Unsicheres vorhandenes Restore-Ziel: {name!r}")


def check_destinations(root: Path, files: dict) -> None:
    # Preflight the entire selection before creating any target files/directories.
    with contextlib.ExitStack() as stack:
        try:
            stack.enter_context(directory_fd(root))
        except FileNotFoundError:
            pass
        for name, (member, _) in files.items():
            destination = root / name
            try:
                with directory_fd(destination.parent) as parent_fd:
                    check_leaf(parent_fd, destination.name, member["type"])
            except FileNotFoundError:
                pass


def copy_approved(root: Path, files: dict) -> None:
    check_destinations(root, files)
    with directory_fd(root, create=True):
        pass
    for name, (member, source) in sorted(files.items()):
        destination = root / name
        if member["type"] == "directory":
            with directory_fd(destination, create=True):
                pass
            continue
        with directory_fd(destination.parent, create=True) as parent_fd:
            check_leaf(parent_fd, destination.name, "file")
            temporary_name = ".dev-lab-restore-" + secrets.token_hex(16)
            fd = os.open(
                temporary_name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW,
                0o600,
                dir_fd=parent_fd,
            )
            try:
                with (
                    os.fdopen(fd, "wb") as destination_file,
                    source.open("rb") as source_file,
                ):
                    shutil.copyfileobj(source_file, destination_file)
                    os.fchmod(destination_file.fileno(), member["mode"])
                os.replace(
                    temporary_name,
                    destination.name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                )
            finally:
                with contextlib.suppress(FileNotFoundError):
                    os.unlink(temporary_name, dir_fd=parent_fd)


def restore(args) -> None:
    rules = policy(args.project_root, args.home_root)
    if args.all and (args.project or args.vscode or args.configs):
        raise BackupError("--all kann nicht mit einer Kategorie kombiniert werden.")
    selected = (
        set(PREFIXES)
        if args.all
        else {name for name in PREFIXES if getattr(args, name)}
    )
    if not selected:
        raise BackupError(
            "Mindestens eine Auswahl ist erforderlich: --project, --vscode oder --configs."
        )
    root = absolute(args.restore_root) if args.restore_root else None
    if root == Path("/"):
        raise BackupError(
            "Fuer Originalpfade ist --restore-original-paths erforderlich."
        )
    if args.restore_original_paths:
        if os.geteuid() != 0:
            raise BackupError(
                "--restore-original-paths erfordert ausdruecklichen privilegierten Aufruf."
            )
        root = Path("/")
    backup = absolute(args.backup_dir)
    with tempfile.TemporaryDirectory(prefix="dev-lab-restore-validation-") as temporary:
        staging = Path(temporary)
        archives = validate_manifest(
            authenticate(backup, args.trusted_public_key, staging), backup, rules
        )
        available = {entry["category"] for entry in archives}
        if not args.all and not selected <= available:
            raise BackupError("Ausgewaehlte Kategorie fehlt im signierten Manifest.")
        approved = {}
        for index, entry in enumerate(archives):
            if entry["category"] not in selected:
                continue
            snapshot = staging / f"archive-{index}.tar.gz"
            with (
                regular_file(backup / entry["name"]) as source,
                snapshot.open("xb") as output,
            ):
                size, digest = transfer(source, output, limit=entry["size"])
            if size != entry["size"] or digest != entry["sha256"]:
                raise BackupError(
                    f"Archiv stimmt nicht mit signiertem Hash ueberein: {entry['name']}"
                )
            files_root = staging / f"files-{index}"
            members = inspect_archive(snapshot, entry["category"], rules, files_root)
            if members != entry["members"]:
                raise BackupError(
                    "Archiv-Inventar stimmt nicht mit signiertem Manifest ueberein."
                )
            for member in members:
                name = member["path"]
                if name in approved and approved[name][0] != member:
                    raise BackupError(f"Widerspruechliche Archivmitglieder: {name!r}")
                approved[name] = (member, files_root / name)
        if root is not None:
            check_destinations(root, approved)
        for name in sorted(approved):
            print(f"  {name}")
        if args.dry_run:
            print(
                "Dry-run abgeschlossen. Signatur und Inhalte geprueft; keine Zieldateien geschrieben."
            )
            return
        if root is None:
            root = Path(tempfile.mkdtemp(prefix="dev-lab-restore-"))
        copy_approved(root, approved)
        print(f"Restore abgeschlossen. Ziel: {root}")


def source_entries(source: Path):
    """Do not follow links or archive devices, FIFOs, or sockets."""

    def fail_read(error):
        raise error

    if source.is_symlink() or not source.exists():
        return
    if source.is_file():
        yield source
    elif source.is_dir():
        for folder, directories, filenames in os.walk(
            source, followlinks=False, onerror=fail_read
        ):
            directories[:] = sorted(
                name for name in directories if not (Path(folder) / name).is_symlink()
            )
            yield Path(folder)
            for name in sorted(filenames):
                path = Path(folder) / name
                if stat.S_ISREG(path.lstat().st_mode):
                    yield path


def create(args) -> None:
    rules = policy(args.project_root, args.home_root)
    if not shutil.which("minisign"):
        raise BackupError("minisign ist nicht installiert.")
    # Refuse a missing/non-regular key before creating any backup output.
    with regular_file(args.signing_key):
        pass
    output = absolute(args.output_dir)
    for sources in rules.values():
        for source, subtree in sources:
            if subtree and output.resolve().is_relative_to(source.resolve()):
                raise BackupError(
                    "Backup-Ziel darf nicht innerhalb einer gesicherten Quelle liegen."
                )
            if args.signing_key.resolve() == source.resolve() or (
                subtree and args.signing_key.resolve().is_relative_to(source.resolve())
            ):
                raise BackupError(
                    "Der Backup-Signaturschluessel darf nicht Teil der Sicherung sein."
                )
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    backup = output / f"backup-{timestamp}"
    backup.mkdir(mode=0o700)
    archives = []
    for category, sources in rules.items():
        paths = [path for source, _ in sources for path in source_entries(source)]
        if not paths:
            continue
        archive = backup / f"{PREFIXES[category]}-{timestamp}.tar.gz"
        with tarfile.open(
            archive, mode="w:gz", format=tarfile.PAX_FORMAT
        ) as destination:
            for path in paths:
                name = path.relative_to("/").as_posix()
                is_directory = path.is_dir()
                authorize(
                    name, "directory" if is_directory else "file", category, rules
                )
                if is_directory:
                    item = tarfile.TarInfo(name)
                    item.type, item.mode = tarfile.DIRTYPE, 0o700
                    destination.addfile(item)
                else:
                    with regular_file(path) as source:
                        info = os.fstat(source.fileno())
                        item = tarfile.TarInfo(name)
                        item.size = info.st_size
                        item.mode = 0o600 | (info.st_mode & 0o100)
                        destination.addfile(item, source)
        os.chmod(archive, 0o600)
        members = inspect_archive(archive, category, rules)
        with regular_file(archive) as source:
            size, digest = transfer(source)
        archives.append(
            {
                "name": archive.name,
                "category": category,
                "size": size,
                "sha256": digest,
                "members": members,
            }
        )
    manifest = {"format": FORMAT, "archives": archives}
    validate_manifest(manifest, backup, rules)
    manifest_path = backup / "manifest.json"
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    if len(manifest_text.encode("utf-8")) > MAX_MANIFEST:
        raise BackupError("Manifest-Groessenlimit ueberschritten.")
    manifest_path.write_text(manifest_text, encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    run_minisign(
        [
            "-S",
            "-s",
            str(args.signing_key),
            "-m",
            str(manifest_path),
            "-x",
            str(backup / "manifest.json.minisig"),
        ]
    )
    print(f"Signiertes Backup abgeschlossen. Ziel: {backup}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create_parser = commands.add_parser("create", help="Signiertes Backup erstellen")
    create_parser.add_argument(
        "--output-dir", type=Path, default=Path.home() / "backups/dev-lab"
    )
    create_parser.add_argument("--signing-key", type=Path, required=True)
    restore_parser = commands.add_parser(
        "restore", help="Authentifiziertes Backup sicher wiederherstellen"
    )
    restore_parser.add_argument("--backup-dir", type=Path, required=True)
    restore_parser.add_argument("--trusted-public-key", type=Path, required=True)
    target = restore_parser.add_mutually_exclusive_group()
    target.add_argument("--restore-root", type=Path)
    target.add_argument("--restore-original-paths", action="store_true")
    restore_parser.add_argument("--dry-run", action="store_true")
    restore_parser.add_argument("--all", action="store_true")
    for category in PREFIXES:
        restore_parser.add_argument(f"--{category}", action="store_true")
    for command in (create_parser, restore_parser):
        command.add_argument("--project-root", type=Path, default=ROOT)
        command.add_argument("--home-root", type=Path, default=Path.home())
    args = parser.parse_args(argv)
    try:
        (create if args.command == "create" else restore)(args)
    except (
        BackupError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
        tarfile.TarError,
        EOFError,
    ) as error:
        print(f"Fehler: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
