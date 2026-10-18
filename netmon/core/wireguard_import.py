"""Bounded, immutable snapshots for reviewed WireGuard import bytes.

No user-owned staging path crosses sudo. The installed root helper receives the
reviewed bytes on stdin and creates its own root-only staging file.
"""

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import re
import stat

from netmon.core import nm_ownership as own

MAX_PROFILES = 64
MAX_BATCH_BYTES = 8 * own.MAX_CONFIG


def profile_name(path):
    name = Path(path).name
    if name.endswith(".conf"):
        name = name[:-5]
    if name in {".", ".."} or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name):
        raise ValueError("Ungueltiger WireGuard-Profilname")
    return name


def _identity(info):
    return tuple(
        getattr(info, "st_" + key)
        for key in (
            "dev",
            "ino",
            "uid",
            "gid",
            "mode",
            "nlink",
            "size",
            "mtime_ns",
            "ctime_ns",
        )
    )


def _read(path):
    path = os.path.abspath(os.fspath(path))
    if len(os.fsencode(path)) > 4096 or any(ord(c) < 32 for c in path):
        raise ValueError("Ungueltiger WireGuard-Quellpfad")
    # Anchor every component with a no-follow directory descriptor, not resolve().
    parts = Path(path).parts
    directory = os.open(
        parts[0], getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW
    )
    fd = None
    try:
        for part in parts[1:-1]:
            child = os.open(
                part,
                getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=directory,
            )
            os.close(directory)
            directory = child
        fd = os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
        )
        before = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_uid not in {0, os.geteuid()}
            or before.st_mode & 0o022
            or not 0 < before.st_size <= own.MAX_CONFIG
        ):
            raise ValueError("Unsichere WireGuard-Quelldatei oder Groessenlimit")
        with os.fdopen(fd, "rb", closefd=False) as handle:
            data = handle.read(own.MAX_CONFIG + 1)
        after = os.fstat(fd)
        named = os.stat(parts[-1], dir_fd=directory, follow_symlinks=False)
        if (
            _identity(before) != _identity(after)
            or _identity(after) != _identity(named)
            or len(data) != after.st_size
            or len(data) > own.MAX_CONFIG
        ):
            raise ValueError("WireGuard-Quelle wurde beim Lesen veraendert")
        return data, _identity(after)
    finally:
        if fd is not None:
            os.close(fd)
        os.close(directory)


@dataclass(frozen=True)
class ProfileSnapshot:
    source: str
    name: str
    data: bytes = field(repr=False)
    sha256: str
    hooks: tuple[str, ...]
    identity: tuple | None = field(default=None, repr=False)
    protected: bool = False

    @classmethod
    def from_bytes(cls, source, name, data, *, identity=None, protected=False):
        if (
            name in {".", ".."}
            or not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name)
            or not 0 < len(data) <= own.MAX_CONFIG
        ):
            raise ValueError("Ungueltiger WireGuard-Snapshot")
        data = bytes(data)
        data.decode("utf-8", errors="strict")
        if b"\0" in data:
            raise ValueError("WireGuard-Profil enthaelt NUL")
        return cls(
            str(source),
            name,
            data,
            hashlib.sha256(data).hexdigest(),
            own.wireguard_hooks(data),
            identity,
            protected,
        )

    @classmethod
    def read(cls, source):
        name = profile_name(source)
        data, identity = _read(source)
        return cls.from_bytes(os.path.abspath(source), name, data, identity=identity)

    def payload(self):
        if (
            hashlib.sha256(self.data).hexdigest() != self.sha256
            or own.wireguard_hooks(self.data) != self.hooks
        ):
            raise ValueError(
                "WireGuard-Pruefnachweis stimmt nicht mit den Bytes ueberein"
            )
        return {
            "name": self.name,
            "content": self.data.decode("utf-8"),
            "sha256": self.sha256,
            "hooks": list(self.hooks),
        }

    def verify_source(self):
        self.payload()
        if self.identity is not None:
            data, identity = _read(self.source)
            if (
                identity != self.identity
                or hashlib.sha256(data).hexdigest() != self.sha256
            ):
                raise ValueError("WireGuard-Quelle wurde nach der Pruefung veraendert")
