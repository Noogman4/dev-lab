"""Lightweight runtime measurement helpers for NetMon."""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime

try:
    from netmon.config.constants import NETMON_APP_VERSION
    from netmon.core.state import get_netmon_state_dir
except ModuleNotFoundError:
    from config.constants import NETMON_APP_VERSION
    from core.state import get_netmon_state_dir

_SENSITIVE_KEY_PARTS = (
    "api_key",
    "authorization",
    "client_secret",
    "keyring",
    "password",
    "passphrase",
    "private_key",
    "secret",
    "token",
)

_VALID_MODES = {"basic", "detailed"}
_DEFAULT_MAX_BYTES = 5_000_000
_DEFAULT_BACKUPS = 3


def performance_mode() -> str:
    raw = str(os.environ.get("NETMON_PERFORMANCE_MONITORING", "off") or "off")
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return "basic"
    if value in _VALID_MODES:
        return value
    return "off"


def is_enabled(*, required_mode: str = "basic") -> bool:
    mode = performance_mode()
    if mode == "off":
        return False
    if required_mode == "detailed":
        return mode == "detailed"
    return True


def performance_log_path() -> str:
    override = str(os.environ.get("NETMON_PERFORMANCE_LOG_PATH", "") or "").strip()
    if override:
        return os.path.abspath(os.path.expanduser(override))
    return os.path.join(
        get_netmon_state_dir(),
        "logs",
        "performance_measurements.jsonl",
    )


def _configured_int(env_name: str, default: int) -> int:
    try:
        value = int(str(os.environ.get(env_name, "") or "").strip())
    except ValueError:
        return default
    return value if value >= 0 else default


def _rotation_settings() -> tuple[int, int]:
    return (
        _configured_int("NETMON_PERFORMANCE_MAX_BYTES", _DEFAULT_MAX_BYTES),
        _configured_int("NETMON_PERFORMANCE_BACKUPS", _DEFAULT_BACKUPS),
    )


def _safe_scalar(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return str(value)[:200]


def _safe_metadata(metadata: dict | None) -> dict:
    safe = {}
    for key, value in dict(metadata or {}).items():
        safe_key = str(key or "").strip()[:80]
        if not safe_key:
            continue
        lowered = safe_key.lower()
        if any(part in lowered for part in _SENSITIVE_KEY_PARTS):
            safe[safe_key] = "[REDACTED]"
            continue
        if isinstance(value, (list, tuple)):
            safe[safe_key] = [_safe_scalar(item) for item in list(value)[:20]]
        elif isinstance(value, dict):
            safe[safe_key] = {
                str(item_key)[:80]: _safe_scalar(item_value)
                for item_key, item_value in list(value.items())[:20]
            }
        else:
            safe[safe_key] = _safe_scalar(value)
    return safe


def classify_duration(duration_ms: float, *, gui_thread: bool = False) -> str:
    if duration_ms < 50:
        return "FAST"
    if duration_ms < 250:
        return "NOTICE"
    if duration_ms < 1000:
        return "SLOW"
    return "CRITICAL" if gui_thread else "SLOW"


def _timestamp() -> str:
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def _rotate_log(path: str) -> None:
    max_bytes, backups = _rotation_settings()
    if max_bytes <= 0 or backups <= 0:
        return
    try:
        if not os.path.exists(path) or os.path.getsize(path) < max_bytes:
            return
        oldest = f"{path}.{backups}"
        if os.path.exists(oldest):
            os.remove(oldest)
        for index in range(backups - 1, 0, -1):
            src = f"{path}.{index}"
            dst = f"{path}.{index + 1}"
            if os.path.exists(src):
                os.replace(src, dst)
        os.replace(path, f"{path}.1")
    except Exception:
        pass


def write_measurement(record: dict, *, log_path: str | None = None) -> bool:
    path = log_path or performance_log_path()
    try:
        directory = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(directory, exist_ok=True)
        _rotate_log(path)
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")
        return True
    except Exception:
        return False


class RuntimeMeasurement:
    def __init__(
        self,
        *,
        area: str,
        operation: str,
        command_name: str | None = None,
        metadata: dict | None = None,
        mode: str = "basic",
        log_path: str | None = None,
        enabled: bool | None = None,
    ):
        self.area = str(area or "unknown").strip() or "unknown"
        self.operation = str(operation or "unknown").strip() or "unknown"
        self.command_name = str(command_name or "").strip()
        self.metadata = _safe_metadata(metadata)
        self.mode = mode
        self.log_path = log_path
        self.enabled = (
            is_enabled(required_mode=mode) if enabled is None else bool(enabled)
        )
        self.status = "success"
        self.error = ""
        self.return_code = None
        self._start = 0.0
        self._gui_thread = False

    def __enter__(self):
        self._gui_thread = threading.current_thread() is threading.main_thread()
        self._start = time.perf_counter()
        return self

    def set_status(
        self,
        status: str = "success",
        *,
        return_code: int | None = None,
        error: str = "",
    ) -> None:
        self.status = str(status or "success").strip() or "success"
        if return_code is not None:
            self.return_code = int(return_code)
        if error:
            self.error = str(error)[:200]

    def add_metadata(self, **metadata) -> None:
        self.metadata.update(_safe_metadata(metadata))

    def __exit__(self, exc_type, exc, _tb):
        duration_ms = (time.perf_counter() - self._start) * 1000.0
        if exc is not None:
            self.status = "error"
            self.error = type(exc).__name__
        if self.enabled:
            record = {
                "timestamp": _timestamp(),
                "area": self.area,
                "operation": self.operation,
                "duration_ms": round(duration_ms, 3),
                "status": self.status,
                "gui_thread": self._gui_thread,
                "severity": classify_duration(duration_ms, gui_thread=self._gui_thread),
                "netmon_version": NETMON_APP_VERSION,
            }
            if self.command_name:
                record["command_name"] = self.command_name
            if self.return_code is not None:
                record["return_code"] = self.return_code
            if self.error:
                record["error"] = self.error
            if self.metadata:
                record["metadata"] = self.metadata
            write_measurement(record, log_path=self.log_path)
        return False


def measure(**kwargs) -> RuntimeMeasurement:
    return RuntimeMeasurement(**kwargs)


def measure_runtime(**measure_kwargs):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            with measure(**measure_kwargs):
                return fn(*args, **kwargs)

        wrapper.__name__ = getattr(fn, "__name__", "wrapper")
        wrapper.__doc__ = getattr(fn, "__doc__", None)
        wrapper.__module__ = getattr(fn, "__module__", None)
        return wrapper

    return decorator


def safe_command_name(args) -> str:
    tokens = [str(part or "").strip() for part in list(args or [])]
    if not tokens:
        return "unknown"
    filtered = [
        token for token in tokens if token and token not in {"sudo", "-n", "-S"}
    ]
    command = filtered[0] if filtered else tokens[0]
    return os.path.basename(command)[:80] or "unknown"


__all__ = [
    "RuntimeMeasurement",
    "classify_duration",
    "is_enabled",
    "measure",
    "measure_runtime",
    "performance_log_path",
    "performance_mode",
    "safe_command_name",
    "write_measurement",
]
