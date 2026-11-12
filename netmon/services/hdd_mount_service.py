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
from itertools import islice

try:
    from netmon.core import trusted_sudo
except ModuleNotFoundError:
    from core import trusted_sudo

SAFE_MOUNT_OPTIONS = "nodev,nosuid,noexec"
_DEVICE_TYPES = {"disk", "part", "lvm", "crypt"}
_SYSTEM_FSTAB = "/etc/fstab"
_PROC_SWAPS = "/proc/swaps"
_PROC_ROOT = "/proc"
_FSTAB_BYTES = 1024 * 1024
_FSTAB_ENTRIES = 4096
_UDISKS = "org.freedesktop.UDisks2"
_UDISKS_MANAGER = "/org/freedesktop/UDisks2/Manager"
_UDISKS_BLOCK = "org.freedesktop.UDisks2.Block"
_BUS_PREFIX = [
    "busctl",
    "--system",
    "--json=short",
    "--auto-start=no",
    "--allow-interactive-authorization=no",
    "--timeout=5",
    "call",
    _UDISKS,
]
_UUID_ALIAS = re.compile(
    r"/dev/disk/by-uuid/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)
_SYSTEM_TOOLS = {
    "findmnt": "/usr/bin/findmnt",
    "lsblk": "/usr/bin/lsblk",
    "udisksctl": "/usr/bin/udisksctl",
    "umount": "/usr/bin/umount",
    "sudo": "/usr/bin/sudo",
    "cryptsetup": "/usr/sbin/cryptsetup",
    "true": "/usr/bin/true",
    "busctl": "/usr/bin/busctl",
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
    if argv[0] == "busctl" and not _readonly_udisks_query(argv):
        raise MountPolicyError(
            "Unsupported HDD bus query; only read-only UDisks calls allowed."
        )
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
    try:
        # sudo receives the typed password: bind it to the protected system
        # binary (root-owned, link-free ancestry), not only to a fixed name.
        argv[0] = (
            trusted_sudo.trusted_sudo_path()
            if argv[0] == "sudo"
            else _SYSTEM_TOOLS[argv[0]]
        )
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


def _unescape_table_path(value):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m[1], 8)), value)


def _trusted_swap_file(path):
    """Inspect metadata without opening swap contents, even when mode is 0600.

    Every component is opened relative to its pinned parent, without following
    symlinks. Only root can replace the file or a parent. O_PATH cannot activate,
    read, or write swap and cannot block on a disguised FIFO/device.
    """
    parts = path.split("/")
    if (
        not path.startswith("/")
        or any(p in {"", ".", ".."} for p in parts[1:])
        or parts[1] == "dev"
        or any(ord(c) < 32 or ord(c) == 127 for c in path)
    ):
        raise MountPolicyError("Noncanonical system fstab swapfile path.")
    descriptors = []
    try:
        for index, component in enumerate(["/", *parts[1:]]):
            last = index == len(parts) - 1
            flags = os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC
            if not last:
                flags |= os.O_DIRECTORY
            fd = os.open(
                component, flags, **({"dir_fd": descriptors[-1]} if descriptors else {})
            )
            descriptors.append(fd)
            info = os.fstat(fd)
            if info.st_uid != 0 or info.st_mode & 0o022:
                raise MountPolicyError("Untrusted system fstab swapfile or ancestor.")
            if last:
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_mode & 0o077
                    or info.st_nlink != 1
                    or info.st_size < 4096
                ):
                    raise MountPolicyError("Untrusted regular system fstab swapfile.")
            elif not stat.S_ISDIR(info.st_mode):
                raise MountPolicyError("Untrusted system fstab swapfile ancestor.")
        return info
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _active_swap_files():
    """Read the kernel's active swap identities, excluding changing Used counts."""
    with open(_PROC_SWAPS, "rb") as stream:
        raw = stream.read(_FSTAB_BYTES + 1)
    if len(raw) > _FSTAB_BYTES:
        raise MountPolicyError("Oversized kernel swap table.")
    lines = raw.decode("utf-8", errors="strict").splitlines()
    if not lines or lines[0].split() != [
        "Filename",
        "Type",
        "Size",
        "Used",
        "Priority",
    ]:
        raise MountPolicyError("Invalid kernel swap table.")
    result = {}
    for line in lines[1:]:
        fields = line.split()
        if (
            len(fields) != 5
            or fields[1] not in {"file", "partition"}
            or not fields[2].isascii()
            or not fields[2].isdecimal()
            or not fields[3].isascii()
            or not fields[3].isdecimal()
            or not re.fullmatch(r"-?[0-9]+", fields[4])
        ):
            raise MountPolicyError("Invalid kernel swap entry.")
        path = _unescape_table_path(fields[0])
        if (
            path in result
            or not path.startswith("/")
            or int(fields[3]) > int(fields[2])
        ):
            raise MountPolicyError("Ambiguous kernel swap entry.")
        result[path] = (fields[1], int(fields[2]), int(fields[4]))
    return result


def _fstab_swap_file(path, fields, source, nodes):
    options = fields[3].split(",")
    option_keys = [option.split("=", 1)[0] for option in options]
    if (
        len(set(option_keys)) != len(option_keys)
        or _unescape_table_path(fields[0]) != path
        or fields[1:3] != ["none", "swap"]
        or any(value != "0" for value in fields[4:])
        or any(
            not re.fullmatch(
                r"sw|defaults|nofail|noauto|discard(?:=once|=pages)?|pri=-?[0-9]+",
                option,
            )
            for option in options
        )
    ):
        raise MountPolicyError("Inconsistent system fstab swapfile entry.")
    info = _trusted_swap_file(path)
    active = _active_swap_files().get(path)
    if not active or active[0] != "file" or not 0 < active[1] * 1024 <= info.st_size:
        raise MountPolicyError(
            "System fstab swapfile is not confirmed active by the kernel."
        )
    # A regular file can still live on the selected device. Bind its backing
    # filesystem against the same live, unambiguous block identities as before.
    backing = [
        n
        for n, _ in nodes
        if n.get("maj:min") == f"{os.major(info.st_dev)}:{os.minor(info.st_dev)}"
    ]
    if not backing:
        raise MountPolicyError("Unverifiable system fstab swapfile backing device.")
    device = _fstab_block_source(backing[0]["path"], backing[0].get("fstype"), nodes)
    if any(_block_identity(node) != device for node in backing):
        raise MountPolicyError("Contradictory system fstab swapfile backing device.")
    if device.number == source.number or device.uuid == source.uuid:
        raise MountPolicyError(
            "fstab swapfile belongs to selected device; mount refused."
        )
    return _file_stamp(info), active, device


def _readonly_udisks_query(argv):
    if argv[: len(_BUS_PREFIX)] != _BUS_PREFIX:
        return False
    tail = argv[len(_BUS_PREFIX) :]
    if len(tail) == 9:
        return (
            tail[:7]
            == [
                _UDISKS_MANAGER,
                _UDISKS + ".Manager",
                "ResolveDevice",
                "a{sv}a{sv}",
                "1",
                "path",
                "s",
            ]
            and isinstance(tail[7], str)
            and tail[7].startswith("/dev/")
            and not any(ord(c) < 32 for c in tail[7])
            and tail[8] == "0"
        )
    return (
        len(tail) == 5
        and isinstance(tail[0], str)
        and re.fullmatch(
            r"/org/freedesktop/UDisks2/block_devices/[A-Za-z0-9_]+", tail[0]
        )
        is not None
        and tail[1:]
        == ["org.freedesktop.DBus.Properties", "GetAll", "s", _UDISKS_BLOCK]
    )


def _missing_uuid_alias(path):
    """Pin trusted parents and prove the UUID directory entry itself is absent.

    A dangling symlink, inaccessible parent or caller-controlled namespace is
    not treated as an absent device. No device node is opened.
    """
    if not _UUID_ALIAS.fullmatch(path):
        raise MountPolicyError("Unsupported missing fstab source.")
    descriptors, binding = [], []
    try:
        for component in ("/", "dev", "disk", "by-uuid"):
            fd = os.open(
                component,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                **({"dir_fd": descriptors[-1]} if descriptors else {}),
            )
            descriptors.append(fd)
            info = os.fstat(fd)
            if (
                not stat.S_ISDIR(info.st_mode)
                or info.st_uid != 0
                or info.st_mode & 0o022
            ):
                raise MountPolicyError("Untrusted fstab UUID alias directory.")
            binding.append((info.st_dev, info.st_ino, info.st_mode, info.st_uid))
        try:
            os.stat(
                path.rsplit("/", 1)[1], dir_fd=descriptors[-1], follow_symlinks=False
            )
        except FileNotFoundError:
            return tuple(binding)
        raise MountPolicyError("fstab UUID alias exists or changed; cannot exclude it.")
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MountPolicyError("Duplicate UDisks JSON property.")
        result[key] = value
    return result


def _udisks_json(args, signature, runner):
    rc, out = runner(args, timeout=8)
    if rc != 0 or len(out.encode("utf-8")) > _FSTAB_BYTES:
        raise MountPolicyError("Read-only UDisks identity query failed.")
    result = json.loads(out, object_pairs_hook=_unique_json_object)
    if (
        not isinstance(result, dict)
        or set(result) != {"type", "data"}
        or result["type"] != signature
    ):
        raise MountPolicyError("Unexpected UDisks JSON signature.")
    data = result["data"]
    if not isinstance(data, list) or len(data) != 1:
        raise MountPolicyError("Incomplete UDisks JSON response.")
    return data[0]


def _udisks_byte_path(value):
    if (
        not isinstance(value, list)
        or not 2 <= len(value) <= 4096
        or type(value[-1]) is not int
        or value[-1] != 0
        or any(type(b) is not int or not 1 <= b <= 255 for b in value[:-1])
    ):
        raise MountPolicyError("Invalid UDisks byte path.")
    path = bytes(value[:-1]).decode("utf-8", errors="strict")
    if not path.startswith("/dev/") or any(ord(c) < 32 or ord(c) == 127 for c in path):
        raise MountPolicyError("Invalid UDisks device path.")
    return path


def _udisks_source_binding(source, runner, *, configuration=()):
    """Bind the mount server's exact path/alias view, never human CLI text."""
    objects = _udisks_json(
        _BUS_PREFIX
        + [
            _UDISKS_MANAGER,
            _UDISKS + ".Manager",
            "ResolveDevice",
            "a{sv}a{sv}",
            "1",
            "path",
            "s",
            source.path,
            "0",
        ],
        "ao",
        runner,
    )
    if (
        not isinstance(objects, list)
        or len(objects) != 1
        or not isinstance(objects[0], str)
    ):
        raise MountPolicyError("Missing or ambiguous UDisks block object.")
    args = _BUS_PREFIX + [
        objects[0],
        "org.freedesktop.DBus.Properties",
        "GetAll",
        "s",
        _UDISKS_BLOCK,
    ]
    if not _readonly_udisks_query(args):
        raise MountPolicyError("Unexpected UDisks block object path.")
    props = _udisks_json(args, "a{sv}", runner)
    if not isinstance(props, dict):
        raise MountPolicyError("Invalid UDisks property map.")

    def get(name, signature):
        prop = props[name]
        if (
            not isinstance(prop, dict)
            or set(prop) != {"type", "data"}
            or prop["type"] != signature
        ):
            raise MountPolicyError("Unexpected UDisks property type.")
        return prop["data"]

    device = _udisks_byte_path(get("Device", "ay"))
    number = get("DeviceNumber", "t")
    uuid, fstype = get("IdUUID", "s"), get("IdType", "s")
    links = get("Symlinks", "aay")
    if not isinstance(links, list) or len(links) > _FSTAB_ENTRIES:
        raise MountPolicyError("Invalid UDisks alias list.")
    aliases = frozenset(_udisks_byte_path(value) for value in links)
    if (
        device != source.path
        or type(number) is not int
        or number != source.number
        or uuid != source.uuid
        or fstype != source.fstype
        or get("IdUsage", "s") != "filesystem"
        or get("Configuration", "a(sa{sv})") != list(configuration)
        or "/dev/disk/by-uuid/" + source.uuid not in aliases
        or len(aliases) != len(links)
    ):
        raise MountPolicyError("UDisks identity differs or has system configuration.")
    return objects[0], device, number, uuid, fstype, aliases


def _independent_missing_uuid(path, fields, source, nodes, runner):
    match = _UUID_ALIAS.fullmatch(path)
    if not match or fields[0] != path or fields[2] != "auto":
        raise MountPolicyError("Unverifiable missing system fstab source.")
    uuid = match[1].casefold()

    def verify_inventory(current):
        if source.uuid.casefold() == uuid or any(
            isinstance(node.get("uuid"), str) and node["uuid"].casefold() == uuid
            for node, _ in current
        ):
            raise MountPolicyError(
                "Missing fstab UUID alias may refer to a live device."
            )
        if _fstab_block_source(source.path, source.fstype, current) != source:
            raise MountPolicyError(
                "Selected filesystem changed during fstab exclusion."
            )

    verify_inventory(nodes)
    parents = _missing_uuid_alias(path)
    server = _udisks_source_binding(source, runner)
    if path == server[1] or path in server[-1]:
        raise MountPolicyError(
            "fstab source is an alias of the selected UDisks device."
        )
    if _missing_uuid_alias(path) != parents:
        raise MountPolicyError(
            "fstab UUID alias directory changed during verification."
        )
    verify_inventory(_read_inventory(runner))
    return parents, server


def _check_system_fstab(source, runner, *, allow_system=False):
    """Inspect the fixed table without environment-sensitive tag evaluation."""
    try:
        snapshot = _read_system_fstab()
        selected = None
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
            raw_entries = [
                line.split()
                for line in snapshot[0].decode("utf-8").splitlines()
                if line.split() and not line.lstrip().startswith("#")
            ]
            swaps = {}
            missing = {}
            for row, fields in zip(rows, raw_entries):
                path = row["source"]
                if not isinstance(path, str) or not path or row.get("children"):
                    raise MountPolicyError("Invalid system fstab source.")
                if row.get("fstype") in _PSEUDO_FILESYSTEMS and path in {
                    "none",
                    row["fstype"],
                }:
                    continue
                if (
                    row.get("fstype") == "swap"
                    and path.startswith("/")
                    and stat.S_ISREG(os.stat(path, follow_symlinks=False).st_mode)
                ):
                    if path in swaps:
                        raise MountPolicyError("Duplicate system fstab swapfile entry.")
                    # Remove validated inline comments, as in the initial parser.
                    fields = fields[
                        : next(
                            (
                                i
                                for i, value in enumerate(fields)
                                if value.startswith("#")
                            ),
                            len(fields),
                        )
                    ]
                    swaps[path] = (
                        fields,
                        _fstab_swap_file(path, fields, source, nodes),
                    )
                    continue
                try:
                    device = _fstab_block_source(path, row.get("fstype"), nodes)
                except FileNotFoundError:
                    if row.get("fstype") != "auto" or path in missing:
                        raise MountPolicyError(
                            "Unverifiable missing system fstab source."
                        )
                    missing[path] = (
                        fields,
                        _independent_missing_uuid(path, fields, source, nodes, runner),
                    )
                    continue
                if device.number == source.number or device.uuid == source.uuid:
                    if not allow_system:
                        raise MountPolicyError(
                            "fstab-managed device; use system tools."
                        )
                    if (
                        device != source
                        or selected is not None
                        or fields[0] != path
                        or fields[2] != row.get("fstype")
                    ):
                        raise MountPolicyError("Ambiguous system fstab filesystem.")
                    selected = tuple(
                        fields[
                            : next(
                                (
                                    i
                                    for i, value in enumerate(fields)
                                    if value.startswith("#")
                                ),
                                len(fields),
                            )
                        ]
                    )
            for path, (fields, binding) in swaps.items():
                if (
                    _fstab_swap_file(path, fields, source, _read_inventory(runner))
                    != binding
                ):
                    raise MountPolicyError(
                        "System fstab swapfile changed during verification."
                    )
            for path, (fields, binding) in missing.items():
                if (
                    _independent_missing_uuid(
                        path, fields, source, _read_inventory(runner), runner
                    )
                    != binding
                ):
                    raise MountPolicyError(
                        "Missing fstab UUID exclusion changed during verification."
                    )
        if _read_system_fstab() != snapshot:
            raise MountPolicyError("System fstab changed during evaluation.")
        if allow_system:
            return snapshot, selected
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


@dataclass(frozen=True)
class SystemMountPlan:
    """One inspected native LUKS mount; never persisted in slot settings."""

    identity: MountIdentity
    snapshot: tuple
    fields: tuple
    server: tuple
    source_node: tuple
    target_nodes: tuple

    @property
    def target(self):
        return self.fields[1]

    @property
    def options(self):
        return self.fields[3]


def _system_target_binding(target):
    """Inspect existing root-owned directories without following symlinks."""
    descriptors, binding = [], []
    try:
        for component in ["/", *target.split("/")[1:]]:
            fd = os.open(
                component,
                os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                **({"dir_fd": descriptors[-1]} if descriptors else {}),
            )
            descriptors.append(fd)
            info = os.fstat(fd)
            if info.st_uid != 0 or info.st_mode & 0o022:
                raise MountPolicyError("Untrusted system fstab mount directory.")
            binding.append((info.st_dev, info.st_ino, info.st_mode, info.st_uid))
        return tuple(binding)
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def prepare_system_mount(identity, runner):
    try:
        return _prepare_system_mount(identity, runner)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise MountPolicyError(
            "Native LUKS system fstab verification refused."
        ) from exc


def _prepare_system_mount(identity, runner):
    """Inspect only a bound ext4 Crypt child with a narrow native fstab entry.

    This is a different mount contract: options come from the administrator's
    system table. The controller passes the immutable plan to mount_device()
    for revalidation before mounting. No options come from JSON.
    """
    if not identity.is_luks or identity.source is None:
        return None
    revalidate(identity, runner)
    source = identity.source
    snapshot, fields = _check_system_fstab(source, runner, allow_system=True)
    if fields is None:
        return None
    options = fields[3].split(",")
    if (
        source.kind != "crypt"
        or source.fstype != "ext4"
        or not _UUID_ALIAS.fullmatch("/dev/disk/by-uuid/" + source.uuid)
        or fields[0] not in {"UUID=" + source.uuid, "/dev/disk/by-uuid/" + source.uuid}
        or fields[1] != "/mnt/" + source.uuid
        or fields[2] not in {"auto", "ext4"}
        or not {"nosuid", "nodev", "noauto"} <= set(options)
        or len(set(options)) != len(options)
        or not set(options)
        <= {"nosuid", "nodev", "noexec", "noauto", "nofail", "x-gvfs-show", "ro", "rw"}
        or {"ro", "rw"} <= set(options)
        or len(fields) != 6
        or fields[4:] != ("0", "0")
    ):
        raise MountPolicyError("Unsupported native LUKS system fstab entry.")
    entries = [
        line.split()
        for line in snapshot[0].decode("utf-8").splitlines()
        if line.split() and not line.lstrip().startswith("#")
    ]
    if sum(_unescape_table_path(row[1]) == fields[1] for row in entries) != 1:
        raise MountPolicyError("Ambiguous system fstab target.")
    nodes = _read_inventory(runner)
    children = [(n, parents) for n, parents in nodes if n.get("uuid") == source.uuid]
    if (
        len(children) != 1
        or not children[0][1]
        or _block_identity(children[0][1][-1]) != identity.device
    ):
        raise MountPolicyError("System fstab source is not the selected LUKS child.")
    config = {}
    for key, value in zip(("fsname", "dir", "type", "opts"), fields[:4]):
        config[key] = {"type": "ay", "data": list(value.encode("utf-8")) + [0]}
    config.update(
        {"freq": {"type": "i", "data": 0}, "passno": {"type": "i", "data": 0}}
    )
    server = _udisks_source_binding(source, runner, configuration=[["fstab", config]])
    node = os.stat(source.path)
    source_node = (node.st_rdev, node.st_dev, node.st_ino)
    target_nodes = _system_target_binding(fields[1])
    revalidate(identity, runner)
    if _read_system_fstab() != snapshot:
        raise MountPolicyError("System fstab changed during native mount inspection.")
    return SystemMountPlan(
        identity, snapshot, fields, server, source_node, target_nodes
    )


def mount_device(identity, runner, *, system_mount=None):
    """UDisks owns authorization and target selection; options cannot come from JSON."""
    if identity.source is None or not identity.source.uuid:
        raise MountPolicyError("No unambiguous filesystem with UUID available.")
    revalidate(identity, runner)
    if system_mount is not None:
        if (
            not isinstance(system_mount, SystemMountPlan)
            or system_mount.identity != identity
            or prepare_system_mount(identity, runner) != system_mount
        ):
            raise MountPolicyError("Native system mount changed after inspection.")
        # UDisks applies the verified system entry, including its authorization.
        result = runner(
            ["udisksctl", "mount", "--block-device", identity.source.path], timeout=20
        )
        if (
            result[0] == 0
            and verified_mount_target(identity, runner) != system_mount.target
        ):
            raise MountPolicyError("Native system mount target was not confirmed.")
        return result
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


def _below_mount(path, target):
    return path == target or path.startswith(target.rstrip("/") + "/")


def _busy_process_references(target):
    """Bounded, unprivileged proc metadata only, never process control or cmdlines.

    Paths are comparable only in our mount namespace. Results are observations,
    not proof of all blockers: permissions, mappings, races and budgets limit us.
    """
    found = []
    deadline = time.monotonic() + 2
    namespace = os.stat(f"{_PROC_ROOT}/self/ns/mnt")
    with os.scandir(_PROC_ROOT) as processes:
        for item in islice((p for p in processes if p.name.isdecimal()), 2048):
            if time.monotonic() > deadline or len(found) >= 20:
                break
            try:
                other = os.stat(f"{item.path}/ns/mnt")
                if (other.st_dev, other.st_ino) != (namespace.st_dev, namespace.st_ino):
                    continue
                reasons = []
                try:
                    if _below_mount(os.readlink(f"{item.path}/cwd"), target):
                        reasons.append("cwd")
                except OSError:
                    pass
                try:
                    with os.scandir(f"{item.path}/fd") as descriptors:
                        for entry in islice(descriptors, 512):
                            if time.monotonic() > deadline:
                                break
                            try:
                                if _below_mount(os.readlink(entry.path), target):
                                    reasons.append("fd")
                                    break
                            except OSError:
                                continue
                except OSError:
                    pass
                if reasons:
                    with open(
                        f"{item.path}/comm", encoding="utf-8", errors="replace"
                    ) as stream:
                        name = stream.read(128).strip()
                    name = "".join(c if c.isprintable() else "?" for c in name)
                    found.append((int(item.name), name, ",".join(reasons)))
            except OSError:
                continue
    return tuple(found)


def _busy_child_mounts(target, number):
    with open(f"{_PROC_ROOT}/self/mountinfo", "rb") as stream:
        raw = stream.read(_FSTAB_BYTES + 1)
    if len(raw) > _FSTAB_BYTES:
        raise MountPolicyError("Mount dependency snapshot exceeds diagnostic budget.")
    rows = []
    for line in raw.decode("utf-8", errors="strict").splitlines():
        fields = line.split()
        if len(fields) < 10 or "-" not in fields[6:]:
            raise MountPolicyError("Invalid mount dependency snapshot.")
        rows.append((fields[0], fields[1], fields[2], _unescape_table_path(fields[4])))
    roots = [r for r in rows if r[3] == target]
    expected = f"{os.major(number)}:{os.minor(number)}"
    if len(roots) != 1 or roots[0][2] != expected:
        raise MountPolicyError("Mount changed during busy diagnostics.")
    by_parent = {}
    if len({r[0] for r in rows}) != len(rows):
        raise MountPolicyError("Ambiguous mount dependency snapshot.")
    for row in rows:
        by_parent.setdefault(row[1], []).append(row[0])
    descendants = set()
    pending = [roots[0][0]]
    while pending:
        current = pending.pop()
        if current in descendants:
            raise MountPolicyError("Cyclic mount dependency snapshot.")
        descendants.add(current)
        pending.extend(by_parent.get(current, []))
    return tuple(r[3] for r in rows if r[0] in descendants and r[0] != roots[0][0])[:64]


def busy_mount_diagnostics(identity, target, runner):
    """Read hints only while the previously bound device/mount still matches."""
    if verified_mount_target(identity, runner) != target:
        raise MountPolicyError("Mount target changed before busy diagnostics.")
    children = _busy_child_mounts(target, identity.source.number)
    processes = _busy_process_references(target)
    if verified_mount_target(identity, runner) != target:
        raise MountPolicyError("Mount target changed during busy diagnostics.")
    return processes, children


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
