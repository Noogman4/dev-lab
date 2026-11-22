"""Unprivileged inventory of selected system configuration files."""

from collections import Counter
from dataclasses import dataclass
import ipaddress
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile
import time

from .log_redaction import redact_sensitive_text
from . import privileged_config
from .privileged_config import (
    APPARMOR_DIR,
    APT_SOURCE_LIST,
    APT_SOURCE_PARTS,
    CRYPTTAB,
    FIREWALL_RULE_FILES,
    HOSTS,
    MAX_CONTENT,
    NSSWITCH,
)
from .swap_resize import SwapResizeError, active_swap_files

FSTAB = "/etc/fstab"
RESOLV_CONF = "/etc/resolv.conf"
FSTAB_CHECK_TIMEOUT = 8
APPARMOR_CHECK_TIMEOUT = 8
APT_CHECK_TIMEOUT = 8
_SYSTEM_PATH = "/usr/bin:/bin"
_MOUNTINFO_LIMIT = 1024 * 1024
FIXED_FILES = {
    "mounts": (FSTAB,),
    "apparmor": (),
    "network": (HOSTS, RESOLV_CONF, NSSWITCH),
    "packages": (APT_SOURCE_LIST,),
    "firewall": (),
}
OPTIONAL_FILES = {"mounts": (CRYPTTAB,), "firewall": FIREWALL_RULE_FILES}
DISCOVERY = {
    "apparmor": ((APPARMOR_DIR, ()), (f"{APPARMOR_DIR}/local", ())),
    "packages": ((APT_SOURCE_PARTS, (".list", ".sources")),),
}
RESOLVER_TARGETS = frozenset(
    {
        "/run/systemd/resolve/stub-resolv.conf",
        "/run/systemd/resolve/resolv.conf",
        "/usr/lib/systemd/resolv.conf",
        "/run/NetworkManager/resolv.conf",
        "/run/resolvconf/resolv.conf",
    }
)
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


@dataclass(frozen=True)
class FileSnapshot:
    text: str | None
    link: str | None = None
    hosts_editable: bool = False
    apparmor_editable: bool = False


@dataclass(frozen=True)
class FileCheck:
    outcome: str
    detail: str = ""


@dataclass(frozen=True)
class AptSourceReview(FileCheck):
    draft: str = ""
    digest: str = ""


@dataclass(frozen=True)
class FstabCheck(FileCheck):
    syntax_errors: int | None = None
    optional_missing: tuple[str, ...] = ()
    type_unavailable: tuple[str, ...] = ()
    active_swaps: tuple[str, ...] = ()
    mounted_types: tuple[tuple[str, str], ...] = ()


def check_hosts(text):
    try:
        privileged_config.validate_hosts(text)
    except ValueError as exc:
        return FileCheck("errors", str(exc))
    return FileCheck("ok")


def check_resolv_nameservers(text):
    """Check nameserver IP literals in the displayed file without DNS queries."""
    invalid_lines = []
    found_nameserver = False
    for line_number, line in enumerate(text.split("\n"), 1):
        fields = line.split()
        if not fields or fields[0] != "nameserver":
            continue
        found_nameserver = True
        try:
            if not line.startswith("nameserver") or len(fields) < 2:
                raise ValueError("Expected one nameserver address")
            ipaddress.ip_address(fields[1])
        except ValueError:
            invalid_lines.append(str(line_number))
    if invalid_lines:
        return FileCheck("errors", ", ".join(invalid_lines))
    return FileCheck("ok" if found_nameserver else "warnings")


def _fstab_entries(text):
    entries = {}
    for line in text.splitlines():
        fields = []
        for field in line.split():
            if field.startswith("#"):
                break
            fields.append(field)
        if len(fields) >= 4:
            entries.setdefault(fields[1], []).append(fields)
    return entries


def _filesystem_uuid(source):
    tag = re.fullmatch(r'UUID=("?)([A-Za-z0-9-]+)\1', source)
    alias = re.fullmatch(r"/dev/disk/by-uuid/([A-Za-z0-9-]+)", source)
    return tag[2] if tag else alias[1] if alias else None


def _optional_uuid_source(target, fields):
    source, _, fstype, mount_options = fields[:4]
    options = set(mount_options.split(","))
    if (
        not 4 <= len(fields) <= 6
        or not target.startswith(("/mnt/", "/media/", "/run/media/"))
        or os.path.normpath(target) != target
        or fstype == "swap"
        or not {"noauto", "nofail"} <= options
        or {"auto", "fail", "x-initrd.mount"} & options
        or any(option.startswith("x-systemd.") for option in options)
    ):
        return None
    uuid = _filesystem_uuid(source)
    return f"/dev/disk/by-uuid/{uuid}" if uuid else None


def _read_mountinfo():
    mounts = {}
    try:
        with open("/proc/self/mountinfo", "r", encoding="utf-8") as stream:
            data = stream.read(_MOUNTINFO_LIMIT + 1)
    except (OSError, UnicodeError):
        return mounts
    if len(data) > _MOUNTINFO_LIMIT:
        return mounts
    for line in data.split("\n"):
        before, separator, after = line.partition(" - ")
        fields, filesystem = before.split(), after.split()
        if not separator or len(fields) < 6 or len(filesystem) < 3:
            continue
        target = re.sub(r"\\(040|011|012|134)", lambda m: chr(int(m[1], 8)), fields[4])
        mounts.setdefault(target, []).append((fields[2], filesystem[0]))
    return mounts


def _block_device_number(path):
    if not path.startswith("/dev/") or os.path.normpath(path) != path:
        return None
    try:
        info = os.stat(path)
    except OSError:
        return None
    if stat.S_ISBLK(info.st_mode):
        return f"{os.major(info.st_rdev)}:{os.minor(info.st_rdev)}"
    return None


def _udev_mount_matches(device, uuid, filesystem, deadline):
    udevadm = shutil.which("udevadm", path=_SYSTEM_PATH)
    timeout = deadline - time.monotonic()
    if not udevadm or timeout <= 0:
        return False
    try:
        result = subprocess.run(
            [udevadm, "info", "--query=property", f"--path=/sys/dev/block/{device}"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            check=False,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            env={"PATH": _SYSTEM_PATH, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    properties = set(result.stdout.splitlines())
    return (
        result.returncode == 0
        and {f"ID_FS_UUID={uuid}", f"ID_FS_TYPE={filesystem}"} <= properties
    )


def _confirmed_mounted_type(target, fields, mounts, deadline):
    source, _, fstype, options = fields[:4]
    rows = mounts.get(target, ())
    if (
        len(rows) != 1
        or any(len(mounts.get(str(parent), ())) > 1 for parent in Path(target).parents)
        or {"bind", "rbind", "move"} & set(options.split(","))
    ):
        return None
    device, filesystem = rows[0]
    if fstype not in ("auto", filesystem) or not re.fullmatch(
        r"[1-9][0-9]*:[0-9]+", device
    ):
        return None
    uuid = _filesystem_uuid(source)
    device_path = f"/dev/disk/by-uuid/{uuid}" if uuid else source
    configured_device = _block_device_number(device_path)
    if configured_device is not None:
        return filesystem if configured_device == device else None
    if uuid and _udev_mount_matches(device, uuid, filesystem, deadline):
        return filesystem
    return None


def _describe_fstab_check(text, outcome, detail):
    entries = _fstab_entries(text)
    reports = {}
    headings = Counter()
    target = None
    parse_errors = error_count = None
    for line in detail.splitlines():
        counts = re.fullmatch(
            r"(\d+) parse errors?, (\d+) errors?, \d+ warnings?", line
        )
        finding = re.fullmatch(r"\s*\[([WE])\] (.+)", line)
        if counts:
            parse_errors, error_count = map(int, counts.groups())
        elif finding:
            reports.setdefault(target, []).append(finding.groups())
        elif line and not line[0].isspace():
            target = line if line in entries else None
            headings[target] += 1
    if outcome == "ok" and detail == "Success, no errors or warnings detected":
        parse_errors = 0

    optional_missing = []
    type_unavailable = []
    mounted_types = []
    mounts = None
    probe_deadline = time.monotonic() + 2
    shown_errors = explained_errors = 0
    missing_type = "cannot detect on-disk filesystem type (No such file or directory)"
    unreadable_type = "cannot detect on-disk filesystem type (Permission denied)"
    for target, findings in reports.items():
        errors = [message for level, message in findings if level == "E"]
        shown_errors += len(errors)
        rows = entries.get(target, ())
        if len(rows) != 1 or headings[target] != 1:
            continue
        if target.startswith("/") and (
            ("W", unreadable_type) in findings or unreadable_type in errors
        ):
            if mounts is None:
                mounts = _read_mountinfo()
            filesystem = _confirmed_mounted_type(
                target, rows[0], mounts, probe_deadline
            )
            display_target = redact_sensitive_text(target)
            if filesystem:
                mounted_types.append((display_target, filesystem))
                if all(message == unreadable_type for _, message in findings):
                    explained_errors += errors.count(unreadable_type)
            else:
                type_unavailable.append(display_target)
        source = _optional_uuid_source(target, rows[0])
        if (
            source
            and ("W", f"unreachable source: {source}: No such file or directory")
            in findings
        ):
            optional_missing.append(redact_sensitive_text(target))
            explained_errors += errors.count(missing_type)

    # Only change the headline if the native report accounts for every error.
    if (
        outcome == "errors"
        and parse_errors == 0
        and error_count == shown_errors == explained_errors
        and explained_errors
    ):
        outcome = "warnings"

    configured_swap_files = {
        row[0]
        for rows in entries.values()
        for row in rows
        if row[2] == "swap" and row[0].startswith("/")
    }
    active_swaps = ()
    if configured_swap_files:
        try:
            active_swaps = tuple(
                map(
                    redact_sensitive_text,
                    sorted(configured_swap_files & active_swap_files()),
                )
            )
        except (OSError, ValueError, SwapResizeError):
            pass  # An unreadable kernel table cannot confirm active swap.
    return FstabCheck(
        outcome,
        redact_sensitive_text(detail),
        parse_errors,
        tuple(optional_missing),
        tuple(type_unavailable),
        active_swaps,
        tuple(mounted_types),
    )


def check_fstab(text):
    """Ask findmnt to verify the supplied snapshot without mounting anything."""
    data = text.encode("utf-8")
    if len(data) > MAX_CONTENT or b"\0" in data:
        raise ValueError("Invalid fstab snapshot")
    findmnt = shutil.which("findmnt", path=_SYSTEM_PATH)
    if findmnt is None:
        return FstabCheck("missing")

    with tempfile.NamedTemporaryFile(prefix="netmon-fstab-") as snapshot:
        snapshot.write(data)
        snapshot.flush()
        try:
            result = subprocess.run(
                [findmnt, "--verify", "--tab-file", snapshot.name],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
                timeout=FSTAB_CHECK_TIMEOUT,
                encoding="utf-8",
                errors="replace",
                env={"PATH": _SYSTEM_PATH, "LC_ALL": "C"},
            )
        except FileNotFoundError:
            return FstabCheck("missing")
        except subprocess.TimeoutExpired:
            return FstabCheck("timeout")
        detail = "\n".join(
            output.strip()
            for output in (result.stdout, result.stderr)
            if output.strip()
        ).replace(snapshot.name, FSTAB)

    if result.returncode != 0:
        outcome = "errors"
    elif result.stderr.strip() or "[W]" in result.stdout:
        # findmnt can report warnings with exit status zero.
        outcome = "warnings"
    else:
        outcome = "ok"
    return _describe_fstab_check(text, outcome, detail)


def is_apparmor_profile(path):
    return bool(path) and os.path.dirname(path) == APPARMOR_DIR


def check_apparmor_profile(text):
    """Compile the displayed snapshot with neither a kernel load nor caching."""
    if len(text.encode("utf-8")) > MAX_CONTENT or "\0" in text:
        raise ValueError("Invalid AppArmor profile snapshot")
    system_path = f"/usr/sbin:/sbin:{_SYSTEM_PATH}"
    parser = shutil.which("apparmor_parser", path=system_path)
    if parser is None:
        return FileCheck("missing")

    try:
        result = subprocess.run(
            [
                parser,
                "--config-file=/dev/null",
                "--skip-kernel-load",
                "--skip-cache",
                "--jobs=0",
                f"--base={APPARMOR_DIR}",
                f"--Include={APPARMOR_DIR}",
            ],
            input=text,
            capture_output=True,
            check=False,
            timeout=APPARMOR_CHECK_TIMEOUT,
            encoding="utf-8",
            errors="replace",
            env={"PATH": system_path, "LC_ALL": "C"},
        )
    except FileNotFoundError:
        return FileCheck("missing")
    except subprocess.TimeoutExpired:
        return FileCheck("timeout")

    detail = "\n".join(
        output.strip() for output in (result.stdout, result.stderr) if output.strip()
    )
    if result.returncode != 0:
        outcome = "errors"
    elif detail:
        outcome = "warnings"
    else:
        outcome = "ok"
    return FileCheck(outcome, redact_sensitive_text(detail))


def is_apt_sources_file(path):
    if not path:
        return False
    directory, filename = os.path.split(path)
    return path == APT_SOURCE_LIST or (
        directory == APT_SOURCE_PARTS
        and re.fullmatch(r"[A-Za-z0-9._-]+\.(?:list|sources)", filename) is not None
    )


def check_apt_sources(path, text):
    """Ask APT to parse one displayed sources file using private paths."""
    data = text.encode("utf-8")
    if not is_apt_sources_file(path) or len(data) > MAX_CONTENT or b"\0" in data:
        raise ValueError("Invalid APT sources snapshot")
    return _check_apt_source_set({path: data})


def review_apt_source_change(path, original, enabled):
    privileged_config.require_local_apt_source(path)
    sources = privileged_config.read_apt_source_set()
    if sources.get(path) != original.encode("utf-8"):
        raise ValueError("APT-Datei wurde inzwischen geändert. Bitte neu laden.")
    draft = privileged_config.apt_enabled_draft(original, enabled)
    if draft == original:
        return AptSourceReview("ok", draft=draft)
    digest = privileged_config.apt_source_set_digest(sources)
    sources[path] = draft.encode("utf-8")
    if len(sources[path]) > MAX_CONTENT:
        raise ValueError("APT-Entwurf überschreitet das Größenlimit.")
    result = _check_apt_source_set(sources)
    return AptSourceReview(result.outcome, result.detail, draft, digest)


def _check_apt_source_set(sources):
    apt_get = shutil.which("apt-get", path=_SYSTEM_PATH)
    if apt_get is None:
        return FileCheck("missing")

    with tempfile.TemporaryDirectory(prefix="netmon-apt-") as temp:
        directory = Path(temp)
        empty = directory / "empty"
        empty.mkdir()
        config = directory / "apt.conf"
        # APT_CONFIG is read before APT opens its usual configuration files.
        config.write_text(
            'Dir::Etc::Parts "";\nDir::Etc::main "/dev/null";\n', encoding="utf-8"
        )
        parts = directory / "sources.list.d"
        parts.mkdir()
        main = directory / "sources.list"
        main.touch()
        snapshots = {}
        for path, data in sources.items():
            snapshot = (
                main if path == APT_SOURCE_LIST else parts / os.path.basename(path)
            )
            snapshot.write_bytes(data)
            snapshots[str(snapshot)] = path
        try:
            result = subprocess.run(
                [
                    apt_get,
                    "-o",
                    f"Dir::Etc::sourcelist={main}",
                    "-o",
                    f"Dir::Etc::sourceparts={parts}",
                    "-o",
                    f"Dir::State::lists={empty}",
                    "-o",
                    "Dir::Cache::pkgcache=",
                    "-o",
                    "Dir::Cache::srcpkgcache=",
                    "indextargets",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
                timeout=APT_CHECK_TIMEOUT,
                encoding="utf-8",
                errors="replace",
                env={"PATH": _SYSTEM_PATH, "LC_ALL": "C", "APT_CONFIG": str(config)},
            )
        except FileNotFoundError:
            return FileCheck("missing")
        except subprocess.TimeoutExpired:
            return FileCheck("timeout")
        detail = result.stderr.strip()
        for snapshot_path, path in snapshots.items():
            detail = detail.replace(snapshot_path, path)

    if result.returncode != 0:
        outcome = "errors"
    elif detail:
        outcome = "warnings"
    else:
        outcome = "ok"
    return FileCheck(outcome, redact_sensitive_text(detail))


def _open_directory(root, path):
    fd = os.open(root, _DIR_FLAGS)
    try:
        for part in Path(path).parts[1:]:
            child = os.open(part, _DIR_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def discover_files(*, root="/"):
    """Discover real files within the known directories, across distro variants."""
    catalog = {group: list(paths) for group, paths in FIXED_FILES.items()}
    for group, paths in OPTIONAL_FILES.items():
        catalog[group].extend(path for path in paths if _known_file_exists(root, path))
    for group, directories in DISCOVERY.items():
        for path, suffixes in directories:
            try:
                fd = _open_directory(root, path)
                try:
                    with os.scandir(fd) as entries:
                        names = [
                            entry.name
                            for entry in entries
                            if not entry.name.startswith(".")
                            and entry.is_file(follow_symlinks=False)
                            and (not suffixes or entry.name.endswith(suffixes))
                            and not entry.name.endswith(
                                ("~", ".dpkg-old", ".dpkg-dist")
                            )
                        ]
                finally:
                    os.close(fd)
            except OSError:
                continue
            catalog[group].extend(f"{path}/{name}" for name in sorted(names))
    return catalog


def _known_file_exists(root, path):
    parts = Path(path)
    try:
        fd = _open_directory(root, str(parts.parent))
        try:
            info = os.stat(parts.name, dir_fd=fd, follow_symlinks=False)
        finally:
            os.close(fd)
    except PermissionError:
        # Keep a known path visible if inspecting the directory requires elevation.
        return True
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode)


def read_file(path, *, root="/"):
    """Read a bounded regular text file. Follow only recognised resolver links."""
    parts = Path(path)
    fd = _open_directory(root, str(parts.parent))
    target = None
    try:
        info = os.stat(parts.name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISLNK(info.st_mode):
            target = os.readlink(parts.name, dir_fd=fd)
        else:
            if not stat.S_ISREG(info.st_mode):
                raise ValueError("expected a regular text file")
            handle_fd = os.open(
                parts.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd
            )
            with os.fdopen(handle_fd, "rb") as handle:
                info = os.fstat(handle_fd)
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError("expected a regular text file")
                data = handle.read(MAX_CONTENT + 1)
            if len(data) > MAX_CONTENT or b"\0" in data:
                raise ValueError("not a text file within the size limit")
            protected = privileged_config.is_protected_regular_file(info)
            return FileSnapshot(
                data.decode("utf-8"),
                hosts_editable=protected and path == HOSTS,
                apparmor_editable=protected
                and privileged_config.is_apparmor_profile_path(path),
            )
    finally:
        os.close(fd)

    resolved = os.path.normpath(os.path.join(str(parts.parent), target))
    if path == RESOLV_CONF and resolved in RESOLVER_TARGETS:
        try:
            return FileSnapshot(read_file(resolved, root=root).text, target)
        except (OSError, ValueError):
            pass
    return FileSnapshot(None, target)
