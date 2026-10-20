"""Fail-closed HDD mount policy; persisted paths are never mount authority."""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass

SAFE_MOUNT_OPTIONS = "nodev,nosuid,noexec"
_DEVICE_TYPES = {"disk", "part", "lvm", "crypt"}
_SYSTEM_FSTAB = "/etc/fstab"
_FSTAB_BYTES = 1024 * 1024
_FSTAB_ENTRIES = 4096
_SYSTEM_TOOLS = {
    "findmnt": "/usr/bin/findmnt",
    "lsblk": "/usr/bin/lsblk",
    "udisksctl": "/usr/bin/udisksctl",
    "umount": "/usr/bin/umount",
    "sudo": "/usr/bin/sudo",
    "cryptsetup": "/usr/sbin/cryptsetup",
    "true": "/usr/bin/true",
}
_PSEUDO_FILESYSTEMS = {
    "tmpfs",
    "ramfs",
    "proc",
    "sysfs",
    "devtmpfs",
    "devpts",
    "cgroup",
    "cgroup2",
    "hugetlbfs",
    "mqueue",
    "debugfs",
    "tracefs",
    "securityfs",
    "configfs",
    "efivarfs",
    "pstore",
    "fusectl",
    "overlay",
    "binfmt_misc",
}


def run_hdd_command(args, timeout=15, input_text=None):
    """Run HDD tools with fixed system paths and no inherited process environment.

    UDisks uses the default system bus and the user's registered Polkit agent.
    No caller-controlled bus address, loader, blkid, locale or tool search path
    is passed through. The sudo child command is absolute as well.
    """
    argv = list(args)
    if not argv or argv[0] not in _SYSTEM_TOOLS:
        raise MountPolicyError("Unsupported HDD system tool.")
    if argv[0] == "sudo":
        if argv[1:] == ["-S", "-v"]:
            pass  # Refresh the existing sudo timestamp, without a child command.
        elif (
            len(argv) >= 3
            and argv[1] == "-n"
            and argv[2]
            in {
                "umount",
                "cryptsetup",
                "true",
            }
        ):
            argv[2] = _SYSTEM_TOOLS[argv[2]]
        else:
            raise MountPolicyError("Unsupported privileged HDD command.")
    argv[0] = _SYSTEM_TOOLS[argv[0]]
    try:
        result = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
            check=False,
            shell=False,
            input=input_text,
            env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired:
        return 124, "HDD command timed out"
    except OSError:
        return 1, "HDD system tool unavailable"
    return result.returncode, (result.stdout or "").strip()


def _file_stamp(info):
    return (
        info.st_dev,
        info.st_ino,
        info.st_mode,
        info.st_uid,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _read_system_fstab():
    """Read only the fixed, root-owned regular system table, with bounded work."""
    fd = os.open(_SYSTEM_FSTAB, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != 0
            or before.st_mode & 0o022
            or before.st_size > _FSTAB_BYTES
        ):
            raise MountPolicyError("Untrusted or oversized system fstab.")
        data = bytearray()
        while len(data) <= _FSTAB_BYTES:
            chunk = os.read(fd, min(65536, _FSTAB_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if (
            len(data) > _FSTAB_BYTES
            or len(data) != before.st_size
            or _file_stamp(before) != _file_stamp(os.fstat(fd))
            or _file_stamp(before)
            != _file_stamp(os.stat(_SYSTEM_FSTAB, follow_symlinks=False))
        ):
            raise MountPolicyError("System fstab changed while reading.")
    finally:
        os.close(fd)
    text = data.decode("utf-8", errors="strict")
    if any((ord(c) < 32 and c not in "\t\n") or ord(c) == 127 for c in text):
        raise MountPolicyError("Invalid control characters in system fstab.")
    entries = 0
    for line in text.splitlines():
        if len(line) > 4096:
            raise MountPolicyError("Oversized system fstab line.")
        fields = line.split()
        if not fields or fields[0].startswith("#"):
            continue
        # Inline comments are allowed only after the required four fields.
        for index, field in enumerate(fields):
            if field.startswith("#"):
                fields = fields[:index]
                break
        if (
            not 4 <= len(fields) <= 6
            or any(not field.isascii() or not field.isdecimal() for field in fields[4:])
            or "\\" in re.sub(r"\\(?:040|011|012|134|043)", "", " ".join(fields))
        ):
            raise MountPolicyError("Malformed system fstab entry.")
        entries += 1
        if entries > _FSTAB_ENTRIES:
            raise MountPolicyError("Too many system fstab entries.")
    return bytes(data), _file_stamp(before), entries


def _fstab_block_source(path, fstype, nodes):
    """Resolve raw fstab tags against live identities, never the blkid cache."""
    tag = re.fullmatch(r"(UUID|LABEL|PARTUUID|PARTLABEL)=(.+)", path)
    if tag:
        key, value = tag.groups()
        # Quoted and otherwise unusual tag forms fail closed.
        matches = [(n, parents) for n, parents in nodes if n.get(key.lower()) == value]
    elif path.startswith("/"):
        resolved = os.path.realpath(path)
        info = os.stat(resolved)
        if not stat.S_ISBLK(info.st_mode):
            raise MountPolicyError("System fstab source is not a block device.")
        matches = [
            (n, parents)
            for n, parents in nodes
            if os.path.realpath(n["path"]) == resolved
        ]
    else:
        raise MountPolicyError("Unresolved system fstab source.")
    if not matches or any(
        p.get("type") not in _DEVICE_TYPES for _, parents in matches for p in parents
    ):
        raise MountPolicyError("Unverified system fstab device or ancestry.")
    identities = {_block_identity(n) for n, _ in matches}
    if len(identities) != 1:
        raise MountPolicyError("Ambiguous system fstab device.")
    identity = identities.pop()
    if (
        not identity.uuid
        or not identity.fstype
        or fstype
        not in {
            "auto",
            identity.fstype,
        }
    ):
        raise MountPolicyError("Inconsistent system fstab filesystem identity.")
    # Detect duplicate UUIDs and contradictory descriptions of the same device.
    for node, _ in nodes:
        same_path = os.path.realpath(node["path"]) == identity.path
        same_uuid = node.get("uuid") == identity.uuid
        if (same_path or same_uuid) and _block_identity(node) != identity:
            raise MountPolicyError("Contradictory system fstab device identity.")
    if not tag and (
        os.path.realpath(path) != identity.path
        or info.st_rdev != identity.number
        or os.stat(path).st_rdev != identity.number
    ):
        raise MountPolicyError("System fstab device changed during verification.")
    if _block_identity(matches[0][0]) != identity:
        raise MountPolicyError("System fstab device changed during verification.")
    return identity


def _check_system_fstab(source, runner):
    """Inspect the fixed table without environment-sensitive tag evaluation."""
    try:
        snapshot = _read_system_fstab()
        if snapshot[2]:
            rc, out = runner(
                [
                    "findmnt",
                    "--fstab",
                    "--tab-file",
                    _SYSTEM_FSTAB,
                    "--list",
                    "--json",
                    "--output",
                    "SOURCE,FSTYPE",
                ],
                timeout=8,
            )
            if rc != 0:
                raise MountPolicyError("Cannot evaluate system fstab.")
            rows = json.loads(out)["filesystems"]
            if not isinstance(rows, list) or len(rows) != snapshot[2]:
                raise MountPolicyError("Incomplete system fstab evaluation.")
            nodes = _read_inventory(runner)
            for row in rows:
                path = row["source"]
                if not isinstance(path, str) or not path or row.get("children"):
                    raise MountPolicyError("Invalid system fstab source.")
                if row.get("fstype") in _PSEUDO_FILESYSTEMS and path in {
                    "none",
                    row["fstype"],
                }:
                    continue
                device = _fstab_block_source(path, row.get("fstype"), nodes)
                if device.number == source.number or device.uuid == source.uuid:
                    raise MountPolicyError("fstab-managed device; use system tools.")
        if _read_system_fstab() != snapshot:
            raise MountPolicyError("System fstab changed during evaluation.")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise MountPolicyError(
            "fstab-managed or unverifiable device; mount refused."
        ) from exc


class MountPolicyError(ValueError):
    """The selected device cannot be safely identified or mounted."""


@dataclass(frozen=True)
class DeviceIdentity:
    path: str
    uuid: str
    number: int
    kind: str
    fstype: str


@dataclass(frozen=True)
class MountIdentity:
    device: DeviceIdentity
    source: DeviceIdentity | None

    @property
    def is_luks(self):
        return self.device.fstype.lower() == "crypto_luks"


def _block_identity(node):
    path = node.get("path")
    kind = node.get("type")
    if not isinstance(path, str) or kind not in _DEVICE_TYPES:
        raise MountPolicyError("Unsupported block device type.")
    resolved = os.path.realpath(path)
    if not resolved.startswith("/dev/"):
        raise MountPolicyError("Device must be below /dev.")
    try:
        info = os.stat(resolved)
    except OSError as exc:
        raise MountPolicyError("Device is unavailable.") from exc
    number = f"{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}"
    if not stat.S_ISBLK(info.st_mode) or number != node.get("maj:min"):
        raise MountPolicyError("Block device identity mismatch.")
    return DeviceIdentity(
        resolved, node.get("uuid") or "", info.st_rdev, kind, node.get("fstype") or ""
    )


def _read_inventory(runner):
    rc, out = runner(
        [
            "lsblk",
            "--json",
            "--paths",
            "--tree",
            "--output",
            "NAME,PATH,TYPE,FSTYPE,UUID,LABEL,PARTUUID,PARTLABEL,MAJ:MIN",
        ],
        timeout=8,
    )
    if rc != 0:
        raise MountPolicyError("Cannot read live block device inventory.")
    try:
        nodes = []

        def walk(items, ancestors=()):
            if not isinstance(items, list):
                raise MountPolicyError("Invalid block device inventory list.")
            for node in items:
                if not isinstance(node, dict) or not isinstance(node.get("path"), str):
                    raise MountPolicyError("Invalid block device inventory node.")
                nodes.append((node, ancestors))
                walk(node.get("children") or [], (*ancestors, node))

        walk(json.loads(out)["blockdevices"])
        return nodes
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError) as exc:
        raise MountPolicyError("Invalid block device inventory.") from exc


def inspect_device(device, expected_uuid, runner):
    """Read a fresh kernel inventory and bind UUID, device number and ancestry."""
    if (
        not expected_uuid
        or not isinstance(device, str)
        or not device.startswith("/dev/")
    ):
        raise MountPolicyError(
            "Assign a detected device with a UUID to the slot first."
        )
    nodes = _read_inventory(runner)
    try:
        # UUID clones are ambiguous even if only one path was selected.
        matching = {
            os.path.realpath(n["path"])
            for n, _ in nodes
            if n.get("uuid") == expected_uuid
        }
        resolved = os.path.realpath(device)
        if matching != {resolved}:
            raise MountPolicyError("Missing, changed or ambiguous device UUID.")
        matches = [
            (n, parents)
            for n, parents in nodes
            if os.path.realpath(n["path"]) == resolved
        ]
        if not matches:
            raise MountPolicyError("Device is no longer detected.")
        node, _parents = matches[0]
        if any(
            p.get("type") not in _DEVICE_TYPES
            for _, parents in matches
            for p in parents
        ):
            raise MountPolicyError(
                "Unsupported device ancestry (for example loop image)."
            )
        identity = _block_identity(node)
        if identity.uuid != expected_uuid:
            raise MountPolicyError("Device UUID changed.")
        if any(_block_identity(n) != identity for n, _ in matches):
            raise MountPolicyError("Contradictory live device identities.")
        candidates = []

        def sources(current):
            item = _block_identity(current)
            if item.fstype and item.fstype.lower() not in {
                "crypto_luks",
                "lvm2_member",
                "linux_raid_member",
                "swap",
            }:
                candidates.append(item)
                return
            for child in current.get("children") or []:
                sources(child)

        sources(node)
        if len(candidates) > 1:
            raise MountPolicyError(
                "Multiple filesystems; assign the intended partition."
            )
        if candidates and candidates[0].uuid:
            source = candidates[0]
            source_paths = {
                os.path.realpath(n["path"])
                for n, _ in nodes
                if n.get("uuid") == candidates[0].uuid
            }
            if source_paths != {candidates[0].path}:
                raise MountPolicyError("Ambiguous filesystem UUID.")
            if any(
                _block_identity(n) != source
                for n, _ in nodes
                if os.path.realpath(n["path"]) == source.path
            ):
                raise MountPolicyError("Contradictory live filesystem identities.")
        return MountIdentity(identity, candidates[0] if candidates else None)
    except (
        KeyError,
        TypeError,
        AttributeError,
        RecursionError,
        json.JSONDecodeError,
    ) as exc:
        raise MountPolicyError("Invalid block device inventory.") from exc


def revalidate(identity, runner):
    current = inspect_device(identity.device.path, identity.device.uuid, runner)
    if current != identity:
        raise MountPolicyError("Device or filesystem changed; refresh and retry.")
    return current


def unlock_device(identity, passphrase, runner):
    """Unlock only through UDisks policy; no generic sudo/cryptsetup fallback."""
    if not identity.is_luks or identity.source is not None:
        raise MountPolicyError("Device is not a locked LUKS container.")
    # NamedTemporaryFile creates a private 0600 file. Never put the secret in argv.
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as key:
        key.write(passphrase)
        key.flush()
        revalidate(identity, runner)
        rc, _out = runner(
            [
                "udisksctl",
                "unlock",
                "--block-device",
                identity.device.path,
                "--key-file",
                key.name,
            ],
            timeout=25,
        )
    if rc != 0:
        raise MountPolicyError(
            "UDisks unlock failed; no privileged fallback attempted."
        )
    for attempt in range(10):
        current = inspect_device(identity.device.path, identity.device.uuid, runner)
        if current.device != identity.device:
            raise MountPolicyError("Device changed while unlocking.")
        if current.source is not None:
            return current
        if attempt < 9:
            time.sleep(0.2)
    raise MountPolicyError("Unlocked filesystem is not bound to the selected device.")


def mount_device(identity, runner):
    """UDisks owns authorization and target selection; options cannot come from JSON."""
    if identity.source is None or not identity.source.uuid:
        raise MountPolicyError("No unambiguous filesystem with UUID available.")
    revalidate(identity, runner)
    # UDisks may ignore caller options for fstab-managed devices. Fail closed.
    _check_system_fstab(identity.source, runner)
    revalidate(identity, runner)
    return runner(
        [
            "udisksctl",
            "mount",
            "--block-device",
            identity.source.path,
            "--options",
            SAFE_MOUNT_OPTIONS,
        ],
        timeout=20,
    )


def confirm_mapper_closed(identity, runner):
    """A successful close command alone is not evidence that plaintext is gone."""
    if (
        not identity.is_luks
        or identity.source is None
        or identity.source.kind != "crypt"
    ):
        raise MountPolicyError("No verified crypt mapper to confirm.")
    for attempt in range(5):
        current = inspect_device(identity.device.path, identity.device.uuid, runner)
        if current.device != identity.device:
            raise MountPolicyError("LUKS device changed while confirming close.")
        nodes = _read_inventory(runner)
        still_listed = any(
            os.path.realpath(node["path"]) == identity.source.path
            or node.get("maj:min")
            == f"{os.major(identity.source.number)}:{os.minor(identity.source.number)}"
            for node, _ in nodes
        )
        if current.source is None and not still_listed:
            try:
                os.stat(identity.source.path)
            except FileNotFoundError:
                return True
        if attempt < 4:
            time.sleep(0.1)
    return False


def verified_mount_target(identity, runner):
    """Bind one exact live mount to the selected slot's verified filesystem."""
    revalidate(identity, runner)
    source = identity.source
    if source is None or not source.uuid:
        raise MountPolicyError("No confirmed filesystem identity for unmount.")

    def query(selector, value):
        rc, out = runner(
            [
                "findmnt",
                "--kernel",
                "--tab-file",
                "/proc/self/mountinfo",
                "--list",
                "--json",
                "--output",
                "SOURCE,TARGET,UUID,MAJ:MIN",
                selector,
                value,
            ],
            timeout=8,
        )
        if rc != 0:
            raise MountPolicyError("Cannot confirm an exact live mount.")
        try:
            rows = json.loads(out)["filesystems"]
            if not isinstance(rows, list) or len(rows) != 1:
                raise MountPolicyError("Ambiguous live mount.")
            row = rows[0]
            target = row["target"]
            if (
                row.get("children")
                or os.path.realpath(row["source"]) != source.path
                or row["uuid"] != source.uuid
                or row["maj:min"]
                != f"{os.major(source.number)}:{os.minor(source.number)}"
                or not isinstance(target, str)
                or not target.startswith("/")
                or target == "/"
                or os.path.realpath(target) != target
                or os.path.normpath(target) != target
                or any(ord(c) < 32 or ord(c) == 127 for c in target)
            ):
                raise MountPolicyError("Mount source/target does not match the slot.")
            return target
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise MountPolicyError("Invalid live mount information.") from exc

    target = query("--source", source.path)
    if query("--mountpoint", target) != target:
        raise MountPolicyError("Live mount changed during verification.")
    revalidate(identity, runner)
    return target
