"""Read-only access to the most useful Linux logs, plus anonymisation for Chad.

Fixed whitelist: no user-supplied commands, paths or journalctl filters. The
desktop user is expected to be in the `adm` group (journal and /var/log are
readable without sudo); missing permissions are reported, never escalated.
No Tk here: the UI calls read_source() from a worker thread.
"""

from __future__ import annotations

from dataclasses import dataclass
import getpass
import ipaddress
import os
import re
import selectors
import socket
import stat
import subprocess
import time

try:
    from netmon.core.diagnostics import redact_sensitive_text
except ModuleNotFoundError:  # pragma: no cover - legacy flat layout
    from core.diagnostics import redact_sensitive_text

LINE_CHOICES = (200, 500, 2000)
DEFAULT_LINES = 500
FILE_TAIL_BYTES = 1 << 20
# Byte limit (UTF-8), enforced while reading the journalctl pipe.
MAX_OUTPUT_BYTES = 2 << 20
MAX_OUTPUT_CHARS = MAX_OUTPUT_BYTES  # historic name; the unit is bytes
JOURNAL_TIMEOUT = 8
JOURNAL_ENV = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "SYSTEMD_COLORS": "0"}
RANGES = {
    "boot": ("-b",),
    "previous": ("-b", "-1"),
    "hour": ("--since", "-1h"),
    "today": ("--since", "today"),
}
DEFAULT_RANGE = "boot"
JOURNAL_BASE = ("journalctl", "--no-pager", "-q", "-o", "short-iso")


@dataclass(frozen=True)
class Source:
    key: str
    label: str
    journal: tuple = ()
    files: tuple = ()


SOURCES = (
    Source(
        "system",
        "Systemfehler & Warnungen",
        journal=("-p", "warning"),
    ),
    Source(
        "kernel",
        "Kernel & Hardware",
        journal=("-k", "-p", "warning"),
    ),
    Source(
        "network",
        "Netzwerk, VPN & DNS",
        journal=(
            "-u",
            "NetworkManager",
            "-u",
            "systemd-resolved",
            "-u",
            "wg-quick@*",
        ),
    ),
    Source(
        "firewall",
        "Firewall (UFW)",
        journal=("-k", "--grep", r"\[UFW "),
    ),
    Source("auth", "Anmeldungen (auth.log)", files=("/var/log/auth.log",)),
    Source(
        "packages",
        "Pakete (apt/dpkg)",
        files=("/var/log/apt/history.log", "/var/log/dpkg.log"),
    ),
)
_BY_KEY = {source.key: source for source in SOURCES}


def resolve_source(key):
    if type(key) is str and key in _BY_KEY:
        return _BY_KEY[key]
    raise ValueError("Unbekannte Log-Quelle.")


def _check_options(range_key, lines):
    if type(range_key) is not str or range_key not in RANGES:
        raise ValueError("Unbekannter Zeitraum.")
    if type(lines) is not int or lines not in LINE_CHOICES:
        raise ValueError("Unzulässige Zeilenzahl.")


def journal_argv(source, range_key=DEFAULT_RANGE, lines=DEFAULT_LINES):
    """The exact fixed argv for a journal source; never contains user text."""
    source = resolve_source(getattr(source, "key", source))
    _check_options(range_key, lines)
    if not source.journal:
        raise ValueError("Quelle ist kein Journal.")
    return [
        *JOURNAL_BASE,
        *source.journal,
        *RANGES[range_key],
        "-n",
        str(lines),
    ]


def read_file_tail(path, lines=DEFAULT_LINES, max_bytes=FILE_TAIL_BYTES):
    """Last `lines` lines of a regular file; no links, bounded read."""
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise PermissionError("keine reguläre Datei")
        start = max(0, info.st_size - max_bytes)
        os.lseek(fd, start, os.SEEK_SET)
        chunks, remaining = [], min(info.st_size, max_bytes)
        while remaining > 0:
            data = os.read(fd, min(65536, remaining))
            if not data:
                break
            chunks.append(data)
            remaining -= len(data)
    finally:
        os.close(fd)
    text = b"".join(chunks).decode("utf-8", errors="replace")
    rows = text.splitlines()
    if start > 0 and rows:
        rows = rows[1:]  # first row is probably cut
    return "\n".join(rows[-lines:])


def _cap(text, limit=None):
    """Keep the newest part within `limit` UTF-8 bytes, starting at a full line."""
    limit = MAX_OUTPUT_BYTES if limit is None else limit
    data = str(text).encode("utf-8")
    if len(data) <= limit:
        return str(text)
    tail = data[-limit:].decode("utf-8", errors="ignore")
    return tail.split("\n", 1)[-1] if "\n" in tail else tail


def _run_bounded(argv, timeout=JOURNAL_TIMEOUT, limit=None):
    """Run a fixed argv; keep only the newest `limit` bytes while reading.

    Memory stays bounded however much the process writes; the process is ended
    after `timeout` seconds and always reaped.
    """
    limit = MAX_OUTPUT_BYTES if limit is None else limit
    process = subprocess.Popen(
        list(argv),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True,
        env=dict(JOURNAL_ENV),
    )
    buffer, dropped = bytearray(), False
    deadline = time.monotonic() + timeout
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("journalctl Zeitüberschreitung")
                if not selector.select(min(remaining, 0.5)):
                    continue
                chunk = os.read(process.stdout.fileno(), 65536)
                if not chunk:
                    break
                buffer += chunk
                if len(buffer) > limit:
                    del buffer[: len(buffer) - limit]
                    dropped = True
        rc = process.wait(timeout=2)
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        process.stdout.close()
    text = bytes(buffer).decode("utf-8", errors="replace")
    if dropped and "\n" in text:
        text = text.split("\n", 1)[1]
    return rc, text


def is_file_source(key):
    return bool(resolve_source(key).files)


def read_source(key, range_key=DEFAULT_RANGE, lines=DEFAULT_LINES, *, run=None):
    """Return (ok, text). Never raises for unreadable/missing sources.

    File sources show the end of the file; the time range applies only to
    journal sources (the UI disables it for files).
    """
    source = resolve_source(key)
    _check_options(range_key, lines)
    if source.journal:
        runner = run or _run_bounded
        try:
            rc, out = runner(
                journal_argv(source, range_key, lines), timeout=JOURNAL_TIMEOUT
            )
        except Exception as exc:  # timeout or missing journalctl
            return False, f"journalctl nicht verfügbar: {type(exc).__name__}"
        out = _cap(str(out or ""))
        if not out.strip():
            # journalctl --grep exits 1 when nothing matches; errors go to the
            # (merged) output, so an empty result is "no entries", not a failure.
            return True, "Keine Einträge im gewählten Zeitraum."
        return rc == 0, out
    parts, ok = [], True
    for path in source.files:
        try:
            body = read_file_tail(path, lines)
        except FileNotFoundError:
            body = "(Datei nicht vorhanden)"
        except PermissionError:
            body, ok = "(Keine Leseberechtigung – Gruppe „adm“ fehlt?)", False
        except OSError as exc:
            body, ok = f"(Nicht lesbar: {type(exc).__name__})", False
        parts.append(f"===== {path} =====\n{body}" if len(source.files) > 1 else body)
    return ok, _cap("\n\n".join(parts))


# ── Anonymisation for Chad ───────────────────────────────────────────────────

_WG_KEY = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{42}[AEIMQUYcgkosw048]=")
_MAC_FIELD = re.compile(r"\bMAC=((?:[0-9A-Fa-f]{2}:){5,}[0-9A-Fa-f]{2})\b")
_MAC = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_UUID = re.compile(
    r"\b[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}\b"
)
_IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
# Optional dotted tail: IPv6 with embedded IPv4 (::ffff:203.0.113.42) is one token.
_IPV6 = re.compile(
    r"(?<![0-9A-Fa-f:])[0-9A-Fa-f]{0,4}(?::[0-9A-Fa-f]{0,4}){2,7}"
    r"(?:(?:\.\d{1,3}){3})?(?![0-9A-Fa-f:]|\.\d)"
)
# NetworkManager: Config: added 'ssid' value 'X'  (field name quoted, then value)
_NAMED_VALUE = re.compile(
    r"(?i)(['\"])(ssid|connection(?:\.id)?)\1(\s+value\s+)(['\"])(.*?)\4"
)
# SSID 'X' / ssid: "X" / connection 'X' (keyword itself not quoted)
_QUOTED_AFTER = re.compile(
    r"(?i)(?<![\w'\"])(ssid|access point|connection)\b(\s*[=:]?\s*)(['\"])(.*?)\3"
)
# ssid=X / ssid: X (unquoted value)
_UNQUOTED_SSID = re.compile(r"(?i)(?<![\w'\"])(ssid)\b(\s*[=:]\s*)(?!['\"])([^\s,;]+)")
CHAD_MAX_LINES = 400
CHAD_MAX_BYTES = 60_000


# Placeholders are written as private-use tokens and only resolved at the very
# end, so no later rule (IPv4, MAC, host/user names) can re-read a placeholder
# or its index as data. Tokens contain no digits, letters, dots or colons.
_TOKEN_OPEN = "\ue000"
_TOKEN_CLOSE = "\ue001"
_TOKEN_DIGIT0 = 0xE010
_TOKEN_CHARS = re.compile("[\ue000-\ue01f]")
_TOKEN = re.compile("\ue000([\ue010-\ue019]+)\ue001")


class _Labels:
    def __init__(self):
        self.maps = {}
        self.counts = {}
        self.names = []

    def token(self, name):
        self.names.append(name)
        digits = str(len(self.names) - 1)
        return (
            _TOKEN_OPEN
            + "".join(chr(_TOKEN_DIGIT0 + int(d)) for d in digits)
            + _TOKEN_CLOSE
        )

    def get(self, kind, value):
        mapping = self.maps.setdefault(kind, {})
        if value not in mapping:
            mapping[value] = self.token(f"{kind}-{len(mapping) + 1}")
        self.counts[kind] = self.counts.get(kind, 0) + 1
        return mapping[value]

    def resolve(self, text):
        def name(match):
            index = "".join(str(ord(c) - _TOKEN_DIGIT0) for c in match.group(1))
            return self.names[int(index)]

        return _TOKEN.sub(name, text)


def _mac_key(value):
    return value.lower().replace("-", ":")


def _mac_field(match, labels):
    """UFW MAC= value: 6 bytes, or dst(6):src(6):ethertype(2) as in iptables logs."""
    groups = match.group(1).lower().split(":")
    if len(groups) == 14:
        dst = labels.get("MAC", ":".join(groups[:6]))
        src = labels.get("MAC", ":".join(groups[6:12]))
        return f"MAC={dst}:{src}:{':'.join(groups[12:])}"
    return "MAC=" + labels.get("MAC", ":".join(groups))


def _name_kind(keyword):
    return "CONN" if keyword.lower().startswith("connection") else "SSID"


def _ipv4(match, labels):
    text = match.group(0)
    try:
        address = ipaddress.IPv4Address(text)
    except ValueError:
        return text
    if address.is_loopback or address.is_unspecified:
        return text
    return labels.get("LAN-IP" if address.is_private else "IP", text)


def _ipv6(match, labels):
    text = match.group(0)
    if text.count(":") < 2:
        return text
    try:
        address = ipaddress.IPv6Address(text)
    except ValueError:
        return text  # e.g. a plain MAC or a clock time; handled elsewhere
    # IPv4-mapped (::ffff:a.b.c.d): judge by the IPv4 address (Python < 3.12.4
    # does not do that itself, e.g. ::ffff:127.0.0.1 is_loopback False).
    judged = address.ipv4_mapped or address
    if judged.is_loopback or judged.is_unspecified:
        return text
    private = judged.is_private or getattr(judged, "is_link_local", False)
    return labels.get("LAN-IP6" if private else "IP6", address.compressed)


def anonymize_for_ai(text, *, hostname=None, username=None):
    """Replace identifying log data consistently. Returns (text, counts).

    Counts only increase for values that were actually replaced.
    """
    labels = _Labels()
    result = redact_sensitive_text(str(text or ""))
    result = _TOKEN_CHARS.sub("\ufffd", result)  # input cannot forge tokens
    result = _WG_KEY.sub(lambda m: labels.get("WG-KEY", m.group(0)), result)
    result = _NAMED_VALUE.sub(
        lambda m: m.group(1)
        + m.group(2)
        + m.group(1)
        + m.group(3)
        + m.group(4)
        + labels.get(_name_kind(m.group(2)), m.group(5))
        + m.group(4),
        result,
    )
    result = _QUOTED_AFTER.sub(
        lambda m: m.group(1)
        + m.group(2)
        + m.group(3)
        + labels.get(_name_kind(m.group(1)), m.group(4))
        + m.group(3),
        result,
    )
    result = _UNQUOTED_SSID.sub(
        lambda m: m.group(1) + m.group(2) + labels.get("SSID", m.group(3)), result
    )
    # IPv6 before plain MACs: a valid IPv6 made of 2-digit groups must not be
    # cut into a MAC. Plain 6-group MACs are not valid IPv6 and stay for _MAC.
    result = _MAC_FIELD.sub(lambda m: _mac_field(m, labels), result)
    result = _IPV6.sub(lambda m: _ipv6(m, labels), result)
    result = _MAC.sub(lambda m: labels.get("MAC", _mac_key(m.group(0))), result)
    result = _UUID.sub(lambda m: labels.get("UUID", m.group(0).lower()), result)
    result = _IPV4.sub(lambda m: _ipv4(m, labels), result)
    for kind, value in (
        ("HOST", hostname if hostname is not None else socket.gethostname()),
        ("USER", username if username is not None else getpass.getuser()),
    ):
        value = str(value or "").strip()
        if len(value) >= 3:
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_.-]){re.escape(value)}(?![A-Za-z0-9_-])"
            )
            result, count = pattern.subn(labels.token(f"[{kind}]"), result)
            if count:
                labels.counts[kind] = labels.counts.get(kind, 0) + count
    return labels.resolve(result), dict(labels.counts)


def truncate_for_ai(text, max_lines=CHAD_MAX_LINES, max_bytes=CHAD_MAX_BYTES):
    """Keep the newest part within lines and UTF-8 bytes; returns (text, truncated)."""
    rows = str(text or "").splitlines()
    truncated = len(rows) > max_lines
    rows = rows[-max_lines:]
    result = "\n".join(rows)
    if len(result.encode("utf-8")) > max_bytes:
        result = _cap(result, max_bytes)
        truncated = True
    return result, truncated
