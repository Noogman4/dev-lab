"""Atomic configuration writer; no user-owned source pathname crosses sudo.

The installed helper is executed in isolated Python mode after the bootstrap
checks its root-owned, non-writable ancestry. Source checkouts fail closed.
"""

import fcntl
import hashlib
import ipaddress
import json
import os
import re
import secrets
import stat
import subprocess
import sys
from pathlib import Path

HELPER = "/usr/lib/netmon/netmon/core/privileged_config.py"
HOSTS = "/etc/hosts"
CRYPTTAB = "/etc/crypttab"
NSSWITCH = "/etc/nsswitch.conf"
FIREWALL_RULE_FILES = (
    "/etc/nftables.conf",
    "/etc/iptables/rules.v4",
    "/etc/iptables/rules.v6",
    "/etc/ufw/user.rules",
    "/etc/ufw/user6.rules",
    "/etc/ufw/before.rules",
    "/etc/ufw/before6.rules",
    "/etc/ufw/after.rules",
    "/etc/ufw/after6.rules",
)
PROTECTED_READ_PATHS = frozenset((CRYPTTAB, NSSWITCH, *FIREWALL_RULE_FILES))
APPARMOR_DIR = "/etc/apparmor.d"
APT_SOURCE_LIST = "/etc/apt/sources.list"
APT_SOURCE_PARTS = "/etc/apt/sources.list.d"
MAX_CONTENT = 1024 * 1024
MAX_APT_SOURCES_BYTES = 8 * MAX_CONTENT
# 0: durable write; 1: rejected/failed before replace; 74: replaced, then failed.
# Timeouts and other process failures do not establish whether replace happened.
WRITE_COMMITTED_ERROR = 74
DESTINATIONS = frozenset(
    {
        "/etc/systemd/resolved.conf.d/netmon-dot.conf",
        "/etc/sysctl.d/99-zz-netmon-hardening.conf",
        "/etc/ufw/sysctl.conf",
        "/etc/rkhunter.conf",
    }
)


class CommittedWriteError(OSError):
    """The destination changed, but finalization could not be confirmed."""


# This code runs before importing any installed application code as root.
BOOTSTRAP = r"""
import os, stat, sys
path = "/usr/lib/netmon/netmon/core/privileged_config.py"
current = "/"
try:
    for part in [""] + path.strip("/").split("/"):
        current = os.path.join(current, part)
        info = os.lstat(current)
        if info.st_uid != 0 or info.st_mode & 0o022:
            raise ValueError("Unprotected configuration helper")
        if current == path:
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ValueError("Unsafe configuration helper")
        elif not stat.S_ISDIR(info.st_mode):
            raise ValueError("Unsafe configuration helper directory")
except (OSError, ValueError) as exc:
    sys.exit(str(exc))
os.execv("/usr/bin/python3", ["/usr/bin/python3", "-I", path] + sys.argv[1:])
"""


def write_privileged_config(path, content, *, run_cmd_fn=None, timeout=20):
    """Send the exact reviewed UTF-8 content, bound to its digest, over stdin."""
    if path not in DESTINATIONS:
        return 1, "Nicht erlaubter Konfigurationspfad."
    if not isinstance(content, str):
        return 1, "Ungueltiger Konfigurationsinhalt."
    data = content.encode("utf-8")
    if len(data) > MAX_CONTENT or b"\0" in data:
        return 1, "Ungueltiger Konfigurationsinhalt oder Groessenlimit."
    return _run_write([path], content, run_cmd_fn, timeout)


def validate_hosts(content):
    """Check hosts entries while preserving comments and the original formatting."""
    if "\0" in content or len(content.encode("utf-8")) > MAX_CONTENT:
        raise ValueError("Ungültiger Inhalt oder Größenlimit überschritten.")
    for number, line in enumerate(content.split("\n"), 1):
        fields = line.partition("#")[0].split()
        if not fields:
            continue
        address, *names = fields
        try:
            ipaddress.ip_address(address)
            if "%" in address:
                raise ValueError("Zone identifier")
        except ValueError:
            raise ValueError(f"Zeile {number}: ungültige IP-Adresse.") from None
        if not names or any(
            len(name.rstrip(".")) > 253
            or not all(
                re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
                for label in name.removesuffix(".").split(".")
            )
            for name in names
        ):
            raise ValueError(f"Zeile {number}: fehlender oder ungültiger Hostname.")


def hosts_save_available():
    return os.path.abspath(__file__) == HELPER


def save_hosts_config(content, original_digest, *, run_cmd_fn=None):
    validate_hosts(content)
    if not re.fullmatch(r"[0-9a-f]{64}", original_digest):
        raise ValueError("Ungültiger Prüfwert der Originaldatei.")
    if run_cmd_fn is None and not hosts_save_available():
        return 1, "Protected installed root helper required"
    return _run_write([HOSTS, original_digest], content, run_cmd_fn, 20)


def is_apparmor_profile_path(path):
    return bool(
        path
        and re.fullmatch(
            re.escape(APPARMOR_DIR) + r"/[A-Za-z0-9_-][A-Za-z0-9._-]*", path
        )
    )


def save_apparmor_profile(path, content, original_digest, *, run_cmd_fn=None):
    if not is_apparmor_profile_path(path) or not re.fullmatch(
        r"[0-9a-f]{64}", original_digest
    ):
        raise ValueError("Ungültiger AppArmor-Profilpfad oder Prüfwert.")
    if "\0" in content or len(content.encode("utf-8")) > MAX_CONTENT:
        raise ValueError("Ungültiger Inhalt oder Größenlimit überschritten.")
    if run_cmd_fn is None and not hosts_save_available():
        return 1, "Protected installed root helper required"
    return _run_write([path, original_digest], content, run_cmd_fn, 20)


def is_deb822_source(path):
    return bool(
        path
        and re.fullmatch(
            re.escape(APT_SOURCE_PARTS) + r"/[A-Za-z0-9_-][A-Za-z0-9._-]*\.sources",
            path,
        )
    )


def apt_enabled_draft(content, enabled):
    """Change only Enabled fields, retaining the rest of the Deb822 file."""
    value = "yes" if enabled else "no"
    blocks = re.split(r"(?m)(^[ \t]*\r?\n)", content)
    count = 0
    for index in range(0, len(blocks), 2):
        block = blocks[index]
        if not any(
            line.strip() and not line.startswith("#") for line in block.split("\n")
        ):
            continue
        count += 1
        fields = list(re.finditer(r"(?im)^(Enabled:[ \t]*)([^\r\n]*)(\r?)$", block))
        if not re.search(r"(?im)^Types:[ \t]*\S", block) or len(fields) > 1:
            raise ValueError(
                "APT-Abschnitt hat kein Types-Feld oder mehrere Enabled-Felder."
            )
        if fields:
            field = fields[0]
            if field[2].strip().lower() not in {"yes", "no"} or block[
                field.end() + 1 : field.end() + 2
            ] in {" ", "\t"}:
                raise ValueError(
                    "Enabled muss einzeilig sein und yes oder no enthalten."
                )
            if field[2].strip().lower() != value:
                blocks[index] = block[: field.start(2)] + value + block[field.end(2) :]
        elif not enabled:
            newline = "\r\n" if "\r\n" in block else "\n"
            blocks[index] = f"Enabled: no{newline}{block}"
    if not count:
        raise ValueError("Keine APT-Quellabschnitte gefunden.")
    return "".join(blocks)


def require_local_apt_source(path):
    """Check dpkg ownership before offering or performing a source change."""
    if not is_deb822_source(path):
        raise ValueError("Nur vorhandene .sources-Dateien sind bearbeitbar.")
    try:
        result = subprocess.run(
            ["/usr/bin/dpkg-query", "--admindir=/var/lib/dpkg", "--search", path],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=5,
            env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"},
        )
    except subprocess.TimeoutExpired:
        raise ValueError("Zeitlimit bei der Prüfung der Paketzuordnung.") from None
    if result.returncode == 0:
        raise ValueError("Die Datei wird von einem Paket verwaltet.")
    if (
        result.returncode != 1
        or result.stdout
        or result.stderr.strip() != f"dpkg-query: no path found matching pattern {path}"
    ):
        raise ValueError("Paketzuordnung konnte nicht zuverlässig geprüft werden.")


def read_apt_source_set():
    """Read the standard APT input set through protected directories."""
    parts = _destination_directory(f"{APT_SOURCE_PARTS}/sources.list")
    try:
        paths = sorted(
            name
            for name in os.listdir(parts)
            if re.fullmatch(r"[A-Za-z0-9._-]+\.(list|sources)", name)
        )
        sources = {}
        total = 0
        for name in paths:
            data = _read_protected_file(parts, name)[0]
            total += len(data)
            if total > MAX_APT_SOURCES_BYTES:
                raise ValueError(
                    "Die APT-Konfiguration überschreitet das Prüfgrößenlimit."
                )
            sources[f"{APT_SOURCE_PARTS}/{name}"] = data
    finally:
        os.close(parts)
    directory = _destination_directory(APT_SOURCE_LIST)
    try:
        try:
            sources[APT_SOURCE_LIST] = _read_protected_file(directory, "sources.list")[
                0
            ]
        except FileNotFoundError:
            pass  # APT also supports systems with only sources.list.d.
    finally:
        os.close(directory)
    return sources


def apt_source_set_digest(sources):
    entries = sorted(
        (path, hashlib.sha256(data).hexdigest()) for path, data in sources.items()
    )
    return hashlib.sha256(json.dumps(entries).encode("ascii")).hexdigest()


def save_apt_source_config(path, content, source_set_digest, *, run_cmd_fn=None):
    if not is_deb822_source(path) or not re.fullmatch(
        r"[0-9a-f]{64}", source_set_digest
    ):
        raise ValueError("Ungültige APT-Datei oder Prüfwert.")
    if "\0" in content or len(content.encode("utf-8")) > MAX_CONTENT:
        raise ValueError("Ungültiger Inhalt oder Größenlimit überschritten.")
    if run_cmd_fn is None and not hosts_save_available():
        return 1, "Protected installed root helper required"
    return _run_write([path, source_set_digest], content, run_cmd_fn, 20)


def _run_write(arguments, content, run_cmd_fn, timeout):
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return _run_helper([*arguments, digest], content, run_cmd_fn, timeout)


def read_system_config(path, *, run_cmd_fn=None):
    if path not in PROTECTED_READ_PATHS:
        raise ValueError("Destination not allowed")
    if run_cmd_fn is None and not hosts_save_available():
        raise OSError("Protected installed root helper required")
    rc, output = _run_helper(["--read", path], "", run_cmd_fn, 10)
    if rc:
        raise OSError(output)
    text = json.loads(output)
    if (
        not isinstance(text, str)
        or "\0" in text
        or len(text.encode("utf-8")) > MAX_CONTENT
    ):
        raise ValueError("Invalid configuration payload")
    return text


def _run_helper(arguments, content, run_cmd_fn, timeout):
    if run_cmd_fn is None:
        try:
            from netmon.core.command import run_cmd
        except ModuleNotFoundError:
            from core.command import run_cmd
        run_cmd_fn = run_cmd
    return run_cmd_fn(
        [
            "sudo",
            "-n",
            "/usr/bin/python3",
            "-I",
            "-c",
            BOOTSTRAP,
            *arguments,
        ],
        input_text=content,
        timeout=timeout,
    )


def _check_directory(fd):
    info = os.fstat(fd)
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
        raise ValueError("Unprotected destination directory")


def _destination_directory(path):
    """Anchor every component; never follow a directory link."""
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        _check_directory(directory)
        parts = Path(path).parts[1:-1]
        for index, part in enumerate(parts):
            try:
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
            except FileNotFoundError:
                # Only the dedicated resolved drop-in directory may be created.
                if (
                    path != "/etc/systemd/resolved.conf.d/netmon-dot.conf"
                    or index != len(parts) - 1
                ):
                    raise
                try:
                    os.mkdir(part, mode=0o755, dir_fd=directory)
                except FileExistsError:
                    pass
                child = os.open(
                    part,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=directory,
                )
            os.close(directory)
            directory = child
            _check_directory(directory)
        return directory
    except BaseException:
        os.close(directory)
        raise


def _atomic_write(path, data):
    directory = _destination_directory(path)
    staging = ".netmon-config-" + secrets.token_hex(16)
    created = False
    replaced = False
    try:
        try:
            name = Path(path).name
            try:
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
            except FileNotFoundError:
                pass
            else:
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != 0
                    or info.st_mode & 0o022
                    or info.st_nlink != 1
                ):
                    raise ValueError("Unsafe destination file")
            fd = os.open(
                staging,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            created = True
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fchown(handle.fileno(), 0, 0)
                os.fchmod(handle.fileno(), 0o644)
                os.fsync(handle.fileno())
            os.replace(staging, name, src_dir_fd=directory, dst_dir_fd=directory)
            replaced = True
            created = False
            os.fsync(directory)
        finally:
            try:
                if created:
                    os.unlink(staging, dir_fd=directory)
            finally:
                os.close(directory)
    except OSError as exc:
        if replaced:
            raise CommittedWriteError(
                f"Destination replaced; finalization failed: {exc}"
            ) from exc
        raise


def is_protected_regular_file(info):
    return (
        stat.S_ISREG(info.st_mode)
        and info.st_uid == 0
        and not info.st_mode & 0o7022
        and info.st_nlink == 1
    )


def _read_protected_file(directory, name):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(fd)
        if not is_protected_regular_file(info):
            raise ValueError(f"Ungeschützte oder ungewöhnliche Datei: {name}")
        original = handle.read(MAX_CONTENT + 1)
        if len(original) > MAX_CONTENT:
            raise ValueError(f"Datei überschreitet das Größenlimit: {name}")
        attrs = {name: os.getxattr(fd, name) for name in os.listxattr(fd)}
        return original, info, attrs


def _read_system_config(path):
    directory = _destination_directory(path)
    try:
        data, _, _ = _read_protected_file(directory, Path(path).name)
    finally:
        os.close(directory)
    if b"\0" in data:
        raise ValueError("Invalid configuration payload")
    return data.decode("utf-8")


def _write_reviewed_staging(directory, name, data, *, gid, mode, attrs):
    fd = os.open(
        name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
        0o600,
        dir_fd=directory,
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fchown(fd, 0, gid)
            os.fchmod(fd, mode)
            for attr, value in attrs.items():
                os.setxattr(fd, attr, value)
            if stat.S_IMODE(os.fstat(fd).st_mode) != mode:
                raise ValueError("Dateirechte konnten nicht erhalten werden.")
            os.fsync(fd)
    except BaseException:
        os.unlink(name, dir_fd=directory)
        raise


def _replace_hosts(data, original_digest):
    return _replace_reviewed_file(HOSTS, data, original_digest, backup_kind="hosts")


def _replace_apt_source(path, data, source_set_digest):
    require_local_apt_source(path)

    def verify(original):
        sources = read_apt_source_set()
        if (
            sources.get(path) != original
            or apt_source_set_digest(sources) != source_set_digest
        ):
            raise ValueError(
                "APT-Quellen wurden inzwischen geändert. Bitte neu prüfen."
            )

    def validate(original):
        content = original.decode("utf-8")
        if data == original or all(
            data != apt_enabled_draft(content, enabled).encode("utf-8")
            for enabled in (True, False)
        ):
            raise ValueError(
                "Nur das Aktivieren oder Deaktivieren vorhandener Quellen ist zulässig."
            )
        verify(original)

    return _replace_reviewed_file(
        path, data, backup_kind="apt", validate=validate, verify=verify
    )


def _replace_reviewed_file(
    path, data, original_digest=None, *, backup_kind, validate=None, verify=None
):
    directory = _destination_directory(path)
    name = Path(path).name
    nonce = secrets.token_hex(16)
    backup = f".netmon-{backup_kind}-{nonce}.bak"
    staging = f".netmon-{backup_kind}-{nonce}.tmp"
    try:
        # Serialize NetMon writers. Re-read again just before replacing to catch
        # changes made by editors which do not participate in this lock.
        fcntl.flock(directory, fcntl.LOCK_EX | fcntl.LOCK_NB)
        original, info, attrs = _read_protected_file(directory, name)
        if (
            original_digest is not None
            and hashlib.sha256(original).hexdigest() != original_digest
        ):
            raise ValueError("Datei wurde inzwischen geändert. Bitte neu laden.")
        if validate is not None:
            validate(original)
        _write_reviewed_staging(
            directory,
            staging,
            data,
            gid=info.st_gid,
            mode=stat.S_IMODE(info.st_mode),
            attrs=attrs,
        )
        try:
            _write_reviewed_staging(
                directory, backup, original, gid=0, mode=0o600, attrs={}
            )
            os.fsync(directory)
            if verify is not None:
                verify(original)
            current, latest, latest_attrs = _read_protected_file(directory, name)
            if (
                current != original
                or latest.st_ino != info.st_ino
                or latest.st_ctime_ns != info.st_ctime_ns
                or latest_attrs != attrs
            ):
                raise ValueError("Datei wurde inzwischen geändert. Bitte neu laden.")
            os.replace(staging, name, src_dir_fd=directory, dst_dir_fd=directory)
        except BaseException:
            os.unlink(staging, dir_fd=directory)
            raise
        try:
            os.fsync(directory)
        except OSError as exc:
            raise CommittedWriteError(f"{Path(path).parent / backup}: {exc}") from exc
        return str(Path(path).parent / backup)
    finally:
        os.close(directory)


def main(arguments=None):
    arguments = sys.argv[1:] if arguments is None else arguments
    try:
        if os.geteuid() != 0 or os.path.abspath(__file__) != HELPER:
            raise ValueError("Protected installed root helper required")
        if len(arguments) == 2 and arguments[0] == "--read":
            if arguments[1] not in PROTECTED_READ_PATHS:
                raise ValueError("Destination not allowed")
            print(json.dumps(_read_system_config(arguments[1])))
            return 0
        hosts_write = (
            len(arguments) == 3
            and arguments[0] == HOSTS
            and re.fullmatch(r"[0-9a-f]{64}", arguments[1])
        )
        apparmor_write = (
            len(arguments) == 3
            and is_apparmor_profile_path(arguments[0])
            and re.fullmatch(r"[0-9a-f]{64}", arguments[1])
        )
        apt_write = (
            len(arguments) == 3
            and is_deb822_source(arguments[0])
            and re.fullmatch(r"[0-9a-f]{64}", arguments[1])
        )
        if (
            not hosts_write
            and not apparmor_write
            and not apt_write
            and (len(arguments) != 2 or arguments[0] not in DESTINATIONS)
        ):
            raise ValueError("Destination not allowed")
        data = sys.stdin.buffer.read(MAX_CONTENT + 1)
        content = data.decode("utf-8", errors="strict")
        if (
            len(data) > MAX_CONTENT
            or b"\0" in data
            or hashlib.sha256(data).hexdigest() != arguments[-1]
        ):
            raise ValueError("Invalid configuration payload or digest")
        if hosts_write:
            validate_hosts(content)
            print(_replace_hosts(data, arguments[1]))
        elif apparmor_write:
            print(
                _replace_reviewed_file(
                    arguments[0], data, arguments[1], backup_kind="apparmor"
                )
            )
        elif apt_write:
            print(_replace_apt_source(arguments[0], data, arguments[1]))
        else:
            _atomic_write(arguments[0], data)
        return 0
    except CommittedWriteError as exc:
        print(str(exc), file=sys.stderr)
        return WRITE_COMMITTED_ERROR
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
