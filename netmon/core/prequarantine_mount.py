"""Fixed, root-protected mount point for the download-scan pre-quarantine.

The privileged tmpfs mount never targets a user-selected or shared-temporary
path. Every component of the mount point is created by root below the
root-owned ``/run``, so no unprivileged process (not even the same UID) can
swap a component for a symlink between validation and ``mount``.
"""

from __future__ import annotations

import os
import stat

RUN_DIR = "/run"
PREQUARANTINE_ROOT = "/run/netmon-prequarantine"
REQUIRED_MOUNT_OPTIONS = frozenset({"noexec", "nosuid", "nodev"})
_MOUNTINFO = "/proc/self/mountinfo"
_ROOT_UID = 0


def prequarantine_mount_point(uid: int | None = None) -> str:
    uid = os.getuid() if uid is None else int(uid)
    if uid < 0:
        raise ValueError("invalid uid")
    return f"{PREQUARANTINE_ROOT}/{uid}"


def mount_option_string(uid: int | None = None, gid: int | None = None) -> str:
    uid = os.getuid() if uid is None else int(uid)
    gid = os.getgid() if gid is None else int(gid)
    return f"rw,noexec,nosuid,nodev,mode=700,size=256m,uid={uid},gid={gid}"


def prepare_command(uid: int | None = None) -> list[str]:
    """Root creates both fixed components with an exact mode (umask-proof)."""
    return [
        "sudo",
        "-n",
        "install",
        "-d",
        "-o",
        "root",
        "-g",
        "root",
        "-m",
        "0755",
        PREQUARANTINE_ROOT,
        prequarantine_mount_point(uid),
    ]


def mount_command(uid: int | None = None, gid: int | None = None) -> list[str]:
    return [
        "sudo",
        "-n",
        "mount",
        "-t",
        "tmpfs",
        "-o",
        mount_option_string(uid, gid),
        "tmpfs",
        prequarantine_mount_point(uid),
    ]


def unmount_command(uid: int | None = None) -> list[str]:
    return ["sudo", "-n", "umount", prequarantine_mount_point(uid)]


def _unescape(field: str) -> str:
    out, i = [], 0
    while i < len(field):
        digits = field[i + 1 : i + 4]
        if field[i] == "\\" and len(digits) == 3 and set(digits) <= set("01234567"):
            out.append(chr(int(digits, 8)))
            i += 4
        else:
            out.append(field[i])
            i += 1
    return "".join(out)


def exact_mount_entry(path: str, mountinfo: str | None = None) -> dict | None:
    """Return the topmost mount whose mount point is exactly ``path``."""
    try:
        with open(mountinfo or _MOUNTINFO, "r", encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError:
        return None
    entry = None
    for line in lines:
        if " - " not in line:
            continue
        pre, post = line.rstrip("\n").split(" - ", 1)
        pre_fields, post_fields = pre.split(), post.split()
        if len(pre_fields) < 6 or len(post_fields) < 3:
            continue
        if _unescape(pre_fields[4]) != path:
            continue
        # Later lines are mounted on top of earlier ones at the same point.
        entry = {
            "fs_type": post_fields[0],
            "source": _unescape(post_fields[1]),
            "mount_options": set(filter(None, pre_fields[5].split(","))),
            "super_options": set(filter(None, post_fields[2].split(","))),
        }
    return entry


def _protected_directory(path: str) -> str:
    try:
        info = os.lstat(path)
    except OSError as exc:
        return f"{path}: {exc.strerror or exc}"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return f"{path}: kein echtes Verzeichnis"
    if info.st_uid != _ROOT_UID:
        return f"{path}: gehört nicht root"
    if info.st_mode & 0o022:
        return f"{path}: für Gruppe/andere beschreibbar"
    return ""


def unsafe_parent_reason() -> str:
    """Return why the parents are not root-protected, or an empty string."""
    for path in (RUN_DIR, PREQUARANTINE_ROOT):
        reason = _protected_directory(path)
        if reason:
            return reason
    return ""


def unsafe_unmounted_point_reason(uid: int | None = None) -> str:
    """Validate the root-created, not yet mounted mount point."""
    target = prequarantine_mount_point(uid)
    reason = unsafe_parent_reason()
    if reason:
        return reason
    if exact_mount_entry(target) is not None:
        return f"{target}: bereits ein Mountpunkt"
    return _protected_directory(target)


def unsafe_active_mount_reason(uid: int | None = None) -> str:
    """Verify the exact NetMon tmpfs at the fixed mount point."""
    uid = os.getuid() if uid is None else int(uid)
    target = prequarantine_mount_point(uid)
    reason = unsafe_parent_reason()
    if reason:
        return reason
    entry = exact_mount_entry(target)
    if entry is None:
        return f"{target}: nicht eingehängt"
    if entry["fs_type"] != "tmpfs" or entry["source"] != "tmpfs":
        return f"{target}: kein NetMon-tmpfs"
    options = entry["mount_options"] | entry["super_options"]
    if not REQUIRED_MOUNT_OPTIONS.issubset(options):
        return f"{target}: noexec/nosuid/nodev fehlen"
    try:
        info = os.lstat(target)
    except OSError as exc:
        return f"{target}: {exc.strerror or exc}"
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        return f"{target}: kein echtes Verzeichnis"
    if info.st_uid != uid or stat.S_IMODE(info.st_mode) != 0o700:
        return f"{target}: Besitzer oder Rechte stimmen nicht"
    return ""


def active_mount_ready(uid: int | None = None) -> bool:
    return not unsafe_active_mount_reason(uid)
