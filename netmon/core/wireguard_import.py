"""Bounded, immutable snapshots for reviewed WireGuard import bytes.

No user-owned staging path crosses sudo. The installed root helper receives the
reviewed bytes on stdin and creates its own root-only staging file.
"""

from dataclasses import dataclass, field, replace
import hashlib
import os
from pathlib import Path
import re
import secrets
import stat

from netmon.core import nm_ownership as own

MAX_PROFILES = 64
MAX_BATCH_BYTES = 8 * own.MAX_CONFIG


class ProfilePermissionsError(ValueError):
    """Safe user-facing diagnostic; contains no profile contents."""

    def __init__(self, path, mode):
        name = " ".join(Path(path).name.split())
        super().__init__(
            f"Profil '{name}': Dateirechte {stat.S_IMODE(mode):04o}; "
            "die Datei ist für die Gruppe oder andere Benutzer schreibbar. "
            "Import aus Sicherheitsgründen abgelehnt. Bitte in den "
            "Dateieigenschaften die Zugriffsrechte auf nur Besitzer: Lesen/Schreiben "
            "(0600) setzen und die Datei erneut importieren. "
            "NetMon ändert die Originaldatei nicht automatisch."
        )


class ProfileCopyError(ValueError):
    """Copy diagnostics with fixed text and a validated profile name only."""


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


def _read(path, *, for_copy=False):
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
            or not 0 < before.st_size <= own.MAX_CONFIG
        ):
            raise ValueError("Unsichere WireGuard-Quelldatei oder Groessenlimit")
        if before.st_mode & 0o022 and (not for_copy or before.st_uid != os.geteuid()):
            raise ProfilePermissionsError(path, before.st_mode)
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
    for_copy: bool = field(default=False, repr=False)
    origin: "ProfileSnapshot | None" = field(default=None, repr=False, compare=False)
    # Digest of the existing /etc/wireguard profile the user explicitly
    # approved replacing; None means create-only (never overwrite).
    replace_sha256: str | None = field(default=None, compare=False)

    @classmethod
    def from_bytes(
        cls, source, name, data, *, identity=None, protected=False, for_copy=False
    ):
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
            for_copy,
        )

    @classmethod
    def read(cls, source, *, for_copy=False):
        name = profile_name(source)
        data, identity = _read(source, for_copy=for_copy)
        return cls.from_bytes(
            os.path.abspath(source), name, data, identity=identity, for_copy=for_copy
        )

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
        if self.origin is not None:
            self.origin.verify_source()
        if self.identity is not None:
            data, identity = _read(self.source, for_copy=self.for_copy)
            if (
                identity != self.identity
                or hashlib.sha256(data).hexdigest() != self.sha256
            ):
                raise ValueError("WireGuard-Quelle wurde nach der Pruefung veraendert")

    def copy_to(self, directory):
        """Publish one reviewed private copy without replacing an existing file."""
        self.verify_source()
        directory = os.path.abspath(os.fspath(directory))
        destination = os.path.join(directory, self.name + ".conf")
        if self.source == destination:
            # An existing library file is never silently chmodded/replaced.
            return type(self).read(destination)
        parent = _copy_directory(directory)
        temporary = ".netmon-import-" + secrets.token_hex(16)
        created = None
        try:
            try:
                existing = type(self).read(destination)
            except FileNotFoundError:
                existing = None
            if existing is not None:
                if (
                    existing.data != self.data
                    or existing.identity[2] != os.geteuid()
                    or stat.S_IMODE(existing.identity[4]) != 0o600
                ):
                    raise ProfileCopyError(
                        f"Profil '{self.name}': Im Zielordner liegt bereits eine andere "
                        "oder nicht private Datei. Sie wurde nicht überschrieben."
                    )
                return replace(existing, origin=self)
            fd = os.open(
                temporary,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            try:
                created = os.fstat(fd)
                os.fchmod(fd, 0o600)
                data = memoryview(self.data)
                while data:
                    written = os.write(fd, data)
                    if not written:
                        raise OSError("Incomplete private profile copy")
                    data = data[written:]
                os.fsync(fd)
            finally:
                os.close(fd)
            staged, _identity_after_write = _read(os.path.join(directory, temporary))
            if staged != self.data:
                raise ValueError("WireGuard-Kopie wurde nicht vollständig geschrieben")
            self.verify_source()
            os.link(
                temporary,
                self.name + ".conf",
                src_dir_fd=parent,
                dst_dir_fd=parent,
                follow_symlinks=False,
            )
            os.unlink(temporary, dir_fd=parent)
            os.fsync(parent)
            copied = type(self).read(destination)
            if copied.data != self.data or stat.S_IMODE(copied.identity[4]) != 0o600:
                raise ValueError("WireGuard-Kopie wurde beim Schreiben veraendert")
            return replace(copied, origin=self)
        finally:
            try:
                if created is not None:
                    info = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                    if (info.st_dev, info.st_ino) == (created.st_dev, created.st_ino):
                        os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            finally:
                os.close(parent)


def _copy_directory(path):
    """Open/create an anchored user-owned destination, following no symlinks."""
    if len(os.fsencode(path)) > 4096 or any(ord(c) < 32 for c in path):
        raise ValueError("Ungueltiger WireGuard-Zielpfad")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in Path(path).parts[1:]:
            try:
                os.mkdir(part, 0o700, dir_fd=fd)
            except FileExistsError:
                pass
            child = os.open(
                part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd
            )
            os.close(fd)
            fd = child
        # Shared Documents ancestors may exist. The anchored destination itself
        # must belong to this user and exclude all other writers; absolute-path
        # readback must still match the exact bytes before any privileged import.
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise ValueError("Unsicherer WireGuard-Zielordner")
        return fd
    except BaseException:
        os.close(fd)
        raise
