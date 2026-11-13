"""Shared best-effort redaction for diagnostic objects and raw log records."""

import json
import re
import unicodedata

MAX_LOG_MESSAGE_CHARS = 64 * 1024
TRUNCATED_LOG_MESSAGE = "[NetMon log record truncated]"


def escape_log_controls(text):
    """Keep untrusted text in one physical record without altering Unicode text."""
    short = {"\n": "\\n", "\r": "\\r", "\t": "\\t"}
    return "".join(
        (
            short.get(char, f"\\u{ord(char):04x}")
            if unicodedata.category(char) in {"Cc", "Zl", "Zp"}
            else char
        )
        for char in text
    )


def encode_log_record(text, *, limit=MAX_LOG_MESSAGE_CHARS):
    """Frame already-redacted text; valid structured records remain valid JSON."""
    if len(text) > limit:
        return TRUNCATED_LOG_MESSAGE
    if text.lstrip().startswith(("{", "[")):
        try:
            value = json.loads(text)
            if isinstance(value, (dict, list)):
                text = json.dumps(value, ensure_ascii=False)
        except (ValueError, RecursionError):
            pass
    text = escape_log_controls(text)
    return text if len(text) <= limit else TRUNCATED_LOG_MESSAGE


def format_log_message(value):
    """Redact complete, bounded input before encoding any record separators."""
    text = str(value or "")
    if len(text) > MAX_LOG_MESSAGE_CHARS:
        return TRUNCATED_LOG_MESSAGE
    return encode_log_record(redact_sensitive_text(text))


_KEY = (
    r"(?:private[-_]?key|preshared[-_]?key|client[-_]?secret|access[-_]?token|"
    r"refresh[-_]?token|api[-_]?key|passphrase|password|passwd|secret|token|pwd|psk)"
)
_VALUE = r"""(?:"(?:[^"\\]|\\.)*(?:"|$)|'(?:[^'\\]|\\.)*(?:'|$)|[^\r\n]+)"""
_ASSIGNMENT = re.compile(
    rf"""(?P<prefix>\b{_KEY}\b["']?\s*[:=]\s*)(?P<value>{_VALUE})""", re.I
)
# An option token starts the word ("--auth-token x", "'--token', 'x'"); prose
# such as "API-Token erlaubt Zugriff" is not an option and stays readable.
_OPTION = re.compile(
    rf"""(?P<prefix>(?<![\w-])--?(?:[A-Za-z0-9]{{1,32}}[-_]){{0,4}}{_KEY}\b"""
    rf"""(?:["']\s*,\s*|["']?[ \t]+))(?P<value>{_VALUE})""",
    re.I,
)
_SENSITIVE_KEY = re.compile(rf"(?:{_KEY}|authorization|cookie|set[-_]?cookie)\Z", re.I)
_ARG = r"""(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s"']+)"""
# Short password options are only unambiguous for specific programs; "-p" is
# a port elsewhere (ssh -p 2222, mysql -P 3306). The option must follow the
# program name within 256 characters, which keeps scans linear on long lines.
_PROGRAM_PATTERNS = (
    # sshpass -p PASSWORD / -pPASSWORD, only among sshpass's own leading options.
    (
        re.compile(rf"(\bsshpass(?:[ \t]+-(?!p)\S+)*[ \t]+-p)[ \t]*{_ARG}"),
        r"\1 [REDACTED]",
    ),
    # docker login -p PASSWORD
    (
        re.compile(rf"(\bdocker[ \t]+login\b[^\r\n]{{0,256}}?[ \t]-p)[ \t]*{_ARG}"),
        r"\1 [REDACTED]",
    ),
    # mysql -pPASSWORD (attached only; "-p value" prompts and names a database)
    (
        re.compile(
            r"(\b(?:mysql|mysqldump|mysqladmin|mysqlimport|mysqlcheck|mysqlshow|"
            r"mariadb|mariadb-dump|mariadb-admin)\b[^\r\n]{0,256}?[ \t]-p)"
            r"""(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s"'-][^\s"']*)"""
        ),
        r"\1[REDACTED]",
    ),
    # curl -u USER:PASSWORD / --user USER:PASSWORD keeps the user name.
    (
        re.compile(
            r"""(\bcurl\b[^\r\n]{0,256}?[ \t](?:-u|--user(?![\w-]))(?:=|[ \t]*)"""
            r"""["']?[^\s:"']+:)[^\s"']+"""
        ),
        r"\1[REDACTED]",
    ),
)
_PATTERNS = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z0-9 ]*PRIVATE KEY-----|$)"
        ),
        "[PRIVATE_KEY_REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(authorization\s*:\s*(?:bearer|basic))\s+[^\s'\"]+"),
        r"\1 [REDACTED]",
    ),
    (re.compile(r"(?im)\b((?:set-cookie|cookie)\s*:)\s*[^\r\n]+"), r"\1 [REDACTED]"),
    (re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{16,}\b"), "[API_KEY_REDACTED]"),
    (re.compile(r"(?i)\b(https?://)[^\s/@]+@"), r"\1[REDACTED]@"),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL_REDACTED]",
    ),
    (
        re.compile(r"(?<![A-Za-z0-9])/(home|Users)/[A-Za-z0-9._-]+"),
        r"/\1/[USER_REDACTED]",
    ),
)


def _replace_value(match):
    value = match["value"]
    quote = value[0] if value.startswith(('"', "'")) else ""
    return match["prefix"] + quote + "[REDACTED]" + quote


def redact_sensitive_text(value):
    text = str(value or "")
    # Preserve JSON escaping when a raw log record contains structured text.
    # Regex-only replacement inside escaped command strings could corrupt it.
    if len(text) <= 64 * 1024 and text.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(text)
            redacted = redact_diagnostic_value(parsed)
            if parsed == redacted:
                return text
            return json.dumps(redacted, ensure_ascii=False)
        except (ValueError, RecursionError):
            pass
    pattern, replacement = _PATTERNS[0]
    text = pattern.sub(replacement, text)
    text = _ASSIGNMENT.sub(_replace_value, text)
    text = _OPTION.sub(_replace_value, text)
    for pattern, replacement in _PROGRAM_PATTERNS + _PATTERNS[1:]:
        text = pattern.sub(replacement, text)
    return text


def redact_diagnostic_value(value):
    if isinstance(value, dict):
        return {
            redact_sensitive_text(str(key)): (
                "[REDACTED]"
                if _SENSITIVE_KEY.fullmatch(str(key))
                else redact_diagnostic_value(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        result = []
        redact_next = False
        for item in value:
            result.append(
                "[REDACTED]" if redact_next else redact_diagnostic_value(item)
            )
            redact_next = (
                isinstance(item, str)
                and item.startswith("-")
                and _SENSITIVE_KEY.fullmatch(item.lstrip("-")) is not None
            )
        return result
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value
