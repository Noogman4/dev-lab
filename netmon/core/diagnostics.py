"""Structured diagnostic report helpers for NetMon."""

from __future__ import annotations

import os
import platform
import re
import sys
import traceback
from datetime import datetime, timezone
from uuid import uuid4

from netmon.config.constants import NETMON_APP_VERSION
from netmon.core.state import get_netmon_documents_dir
from netmon.core.utils import safe_write_json

DIAGNOSTIC_SCHEMA_VERSION = 1

_REDACTION_PATTERNS = (
    (
        re.compile(r"(?i)\b(authorization\s*:\s*bearer)\s+[A-Za-z0-9._~+/=-]+"),
        r"\1 [REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|token|secret|password|passwd|pwd)\s*[:=]\s*"
            r"['\"]?[^'\"\s;]+"
        ),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(
            r"(?i)\b(private[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*"
            r"['\"]?[^'\"\s;]+"
        ),
        r"\1=[REDACTED]",
    ),
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[EMAIL_REDACTED]",
    ),
    (
        re.compile(r"(?<![A-Za-z0-9])/(home|Users)/[A-Za-z0-9._-]+"),
        r"/\1/[USER_REDACTED]",
    ),
    (
        re.compile(r"(?i)\b(passphrase|psk)\s*[:=]\s*['\"]?[^'\"\s;]+"),
        r"\1=[REDACTED]",
    ),
)


def redact_sensitive_text(value: str) -> str:
    text = str(value or "")
    for pattern, replacement in _REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_diagnostic_value(value):
    if isinstance(value, dict):
        return {str(key): redact_diagnostic_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_diagnostic_value(item) for item in value]
    if isinstance(value, tuple):
        return [redact_diagnostic_value(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


def diagnostic_reports_dir() -> str:
    path = os.path.join(get_netmon_documents_dir(), "diagnostics")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def diagnostic_report_path(kind: str, *, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    safe_kind = re.sub(r"[^a-z0-9_-]+", "-", str(kind or "report").strip().lower())
    safe_kind = safe_kind.strip("-") or "report"
    return os.path.join(
        diagnostic_reports_dir(),
        f"netmon-{safe_kind}-{stamp}-{uuid4().hex[:8]}.json",
    )


def _read_os_release() -> dict:
    path = "/etc/os-release"
    data = {}
    try:
        with open(path, encoding="utf-8") as handle:
            for raw_line in handle:
                line = str(raw_line or "").strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                value = value.strip().strip('"').strip("'")
                data[str(key).strip()] = value
    except Exception:
        return {}
    return data


def current_os_label() -> str:
    release_data = _read_os_release()
    for key in ("PRETTY_NAME", "NAME"):
        value = str(release_data.get(key, "") or "").strip()
        if value:
            return value
    platform_text = str(platform.platform() or "").strip()
    if platform_text:
        return platform_text
    return f"{platform.system()} {platform.release()}".strip()


def diagnostic_system_info() -> dict:
    release_data = _read_os_release()
    return {
        "os": current_os_label(),
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "distribution": {
            "id": str(release_data.get("ID", "") or ""),
            "version_id": str(release_data.get("VERSION_ID", "") or ""),
            "name": str(release_data.get("NAME", "") or ""),
            "pretty_name": str(release_data.get("PRETTY_NAME", "") or ""),
        },
    }


def latest_diagnostic_report_path() -> str:
    try:
        base_dir = diagnostic_reports_dir()
        candidates = []
        for name in os.listdir(base_dir):
            if not name.startswith("netmon-") or not name.endswith(".json"):
                continue
            path = os.path.join(base_dir, name)
            if os.path.isfile(path):
                candidates.append(path)
        if not candidates:
            return ""
        candidates.sort(key=lambda path: os.path.getmtime(path), reverse=True)
        return candidates[0]
    except Exception:
        return ""


def build_diagnostic_report(
    *,
    kind: str,
    title: str,
    detail: str = "",
    exc: BaseException | None = None,
    context: dict | None = None,
) -> dict:
    now = datetime.now(timezone.utc)
    exc_type = type(exc).__name__ if exc is not None else ""
    exc_message = str(exc or "")
    traceback_text = ""
    if exc is not None:
        traceback_text = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )

    return {
        "schema_version": DIAGNOSTIC_SCHEMA_VERSION,
        "kind": str(kind or "report"),
        "title": redact_sensitive_text(title),
        "created_at": now.isoformat(),
        "netmon_version": NETMON_APP_VERSION,
        "system": redact_diagnostic_value(diagnostic_system_info()),
        "runtime": {
            "pid": os.getpid(),
            "argv": redact_diagnostic_value(list(sys.argv)),
            "cwd": redact_sensitive_text(os.getcwd()),
        },
        "environment": {
            "DISPLAY": redact_sensitive_text(os.environ.get("DISPLAY", "")),
            "XDG_SESSION_TYPE": redact_sensitive_text(
                os.environ.get("XDG_SESSION_TYPE", "")
            ),
        },
        "detail": redact_sensitive_text(detail),
        "exception": {
            "type": exc_type,
            "message": redact_sensitive_text(exc_message),
            "traceback": redact_sensitive_text(traceback_text),
        },
        "context": redact_diagnostic_value(context or {}),
    }


def write_diagnostic_report(
    *,
    kind: str,
    title: str,
    detail: str = "",
    exc: BaseException | None = None,
    context: dict | None = None,
) -> str:
    payload = build_diagnostic_report(
        kind=kind,
        title=title,
        detail=detail,
        exc=exc,
        context=context,
    )
    path = diagnostic_report_path(kind)
    ok, _err = safe_write_json(path, payload, indent=2, ensure_ascii=False)
    return path if ok else ""


__all__ = [
    "DIAGNOSTIC_SCHEMA_VERSION",
    "build_diagnostic_report",
    "current_os_label",
    "diagnostic_system_info",
    "diagnostic_report_path",
    "diagnostic_reports_dir",
    "latest_diagnostic_report_path",
    "redact_diagnostic_value",
    "redact_sensitive_text",
    "write_diagnostic_report",
]
