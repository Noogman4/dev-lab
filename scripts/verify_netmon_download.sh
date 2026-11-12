#!/usr/bin/env bash
set -euo pipefail

# Self-contained for publication under /verify; Python 3 is required.
# This helper checks integrity only. Verify the pinned signature separately.
exec /usr/bin/python3 -I - "$@" <<'PYTHON'
"""Verify only explicitly supplied regular files; never open manifest paths."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import re
import stat
import sys

MAX_MANIFEST_BYTES = 64 * 1024
MAX_FILES = 64
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,254}\Z")
ENTRY = re.compile(rb"([0-9a-fA-F]{64}) [ *]([^\r\n]+)\Z")


class VerificationError(ValueError):
    pass


def member_name(name):
    parts = name.split("/")
    if len(parts) == 2 and parts[0] == "docs":
        parts = parts[1:]
    if len(parts) != 1 or not NAME.fullmatch(parts[0]):
        raise VerificationError("Unsicherer Dateiname im Manifest oder in der Auswahl.")
    return name


def supplied_name(path):
    path = Path(os.path.abspath(path))
    name = path.name
    if path.parent.name == "docs":
        name = "docs/" + name
    return member_name(name)


def identity(info):
    return tuple(
        getattr(info, "st_" + key)
        for key in ("dev", "ino", "mode", "nlink", "size", "mtime_ns", "ctime_ns")
    )


@contextmanager
def regular_file(path):
    if len(os.fsencode(path)) > 4096 or any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise VerificationError("Ungueltiger Eingabepfad.")
    parts = Path(os.path.abspath(path)).parts
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
    directory = os.open(parts[0], os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    fd = None
    try:
        for part in parts[1:-1]:
            child = os.open(
                part, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            os.close(directory)
            directory = child
        fd = os.open(parts[-1], flags, dir_fd=directory)
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise VerificationError("Nur regulaere, einfach verlinkte Dateien erlaubt.")
        yield fd, before
        after = os.fstat(fd)
        named = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
        if identity(before) != identity(after) or identity(after) != identity(named):
            raise VerificationError(
                "Eingabedatei wurde waehrend der Pruefung veraendert."
            )
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


def manifest_entries(path):
    with regular_file(path) as (fd, info):
        if not 0 < info.st_size <= MAX_MANIFEST_BYTES:
            raise VerificationError("Manifest-Groessenlimit oder leeres Manifest.")
        content = bytearray()
        while len(content) <= MAX_MANIFEST_BYTES:
            chunk = os.read(fd, min(8192, MAX_MANIFEST_BYTES + 1 - len(content)))
            if not chunk:
                break
            content.extend(chunk)
        if len(content) != info.st_size:
            raise VerificationError(
                "Manifest-Groessenlimit oder veraendertes Manifest."
            )
    lines = bytes(content).split(b"\n")
    if lines[-1] == b"":
        lines.pop()
    if not 1 <= len(lines) <= MAX_FILES:
        raise VerificationError("Ungueltige Anzahl von Manifest-Eintraegen.")
    entries = {}
    for line in lines:
        match = ENTRY.fullmatch(line)
        if not match:
            raise VerificationError("Ungueltiger SHA256SUMS-Eintrag.")
        try:
            name = member_name(match[2].decode("ascii"))
        except UnicodeError as exc:
            raise VerificationError("Ungueltiger Manifest-Dateiname.") from exc
        if name in entries:
            raise VerificationError("Doppelter Manifest-Eintrag.")
        entries[name] = match[1].decode("ascii").lower()
    return entries


def verify(arguments):
    if not 2 <= len(arguments) <= MAX_FILES + 1:
        raise VerificationError(
            "Verwendung: verify_netmon_download.sh <SHA256SUMS> <datei> [weitere_dateien...]"
        )
    # Validate the entire manifest and exact membership before any payload open.
    entries = manifest_entries(arguments[0])
    selected = {}
    for path in arguments[1:]:
        name = supplied_name(path)
        if name in selected:
            raise VerificationError("Doppelter Dateiname in der Auswahl.")
        selected[name] = path
    if entries.keys() != selected.keys():
        raise VerificationError(
            "Manifest und ausgewaehlte Dateien stimmen nicht exakt ueberein."
        )
    total = 0
    for name, path in selected.items():
        with regular_file(path) as (fd, info):
            total += info.st_size
            if info.st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                raise VerificationError(
                    "Datei- oder Gesamtgroessenlimit ueberschritten."
                )
            digest = hashlib.sha256()
            remaining = info.st_size
            while remaining:
                chunk = os.read(fd, min(128 * 1024, remaining))
                if not chunk:
                    raise VerificationError(
                        "Unvollstaendige oder veraenderte Eingabedatei."
                    )
                digest.update(chunk)
                remaining -= len(chunk)
        if digest.hexdigest() != entries[name]:
            raise VerificationError("SHA-256 stimmt nicht ueberein: " + name)
    # Report success only after every supplied descriptor passed its checks.
    for name in selected:
        print(name + ": OK")
    print(
        "Nur Integritaet geprueft; Herkunft erfordert eine separat gepruefte Signatur."
    )


if __name__ == "__main__":
    try:
        verify(sys.argv[1:])
    except VerificationError as exc:
        print("Pruefung abgelehnt: " + str(exc), file=sys.stderr)
        sys.exit(1)
    except (OSError, ValueError):
        print(
            "Pruefung abgelehnt: Eingabedatei fehlt, ist unsicher oder nicht lesbar.",
            file=sys.stderr,
        )
        sys.exit(1)
PYTHON
