"""Shared best-effort redaction for diagnostic objects and raw log records."""

import json
import re

_KEY = (
    r"(?:private[-_]?key|preshared[-_]?key|client[-_]?secret|access[-_]?token|"
    r"refresh[-_]?token|api[-_]?key|passphrase|password|passwd|secret|token|pwd|psk)"
)
_VALUE = r"""(?:"(?:[^"\\]|\\.)*(?:"|$)|'(?:[^'\\]|\\.)*(?:'|$)|[^\r\n]+)"""
_ASSIGNMENT = re.compile(
    rf"""(?P<prefix>\b{_KEY}\b["']?\s*[:=]\s*)(?P<value>{_VALUE})""", re.I
)
_OPTION = re.compile(
    rf"""(?P<prefix>--?{_KEY}\b(?:["']\s*,\s*|["']?[ \t]+))(?P<value>{_VALUE})""",
    re.I,
)
_SENSITIVE_KEY = re.compile(rf"(?:{_KEY}|authorization|cookie|set[-_]?cookie)\Z", re.I)
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
    for pattern, replacement in _PATTERNS[1:]:
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
