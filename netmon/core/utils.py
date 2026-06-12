"""Small pure utility helpers shared by the NetMon app."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime


def safe_write_json(path, payload, *, indent=2, ensure_ascii=False):
    """Atomically write JSON data to disk."""
    tmp_path = ""
    try:
        abs_path = os.path.abspath(path)
        dir_path = os.path.dirname(abs_path) or "."
        os.makedirs(dir_path, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=dir_path,
            prefix=".netmon-tmp-",
            suffix=".json",
            delete=False,
        ) as fh:
            json.dump(payload, fh, indent=indent, ensure_ascii=ensure_ascii)
            fh.flush()
            os.fsync(fh.fileno())
            tmp_path = fh.name

        os.replace(tmp_path, abs_path)
        return True, ""
    except Exception as exc:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        return False, str(exc)


def format_table(headers, rows):
    headers = [str(h) for h in (headers or [])]
    rows = [list(r) for r in (rows or [])]
    if not headers:
        return ""

    col_count = len(headers)
    normalized_rows = []
    for row in rows:
        row_vals = [str(row[i]) if i < len(row) else "" for i in range(col_count)]
        normalized_rows.append(row_vals)

    widths = [len(h) for h in headers]
    for row in normalized_rows:
        for idx, value in enumerate(row):
            widths[idx] = max(widths[idx], len(value))

    header_line = " | ".join(
        headers[idx].ljust(widths[idx]) for idx in range(col_count)
    )
    separator = "-+-".join("-" * widths[idx] for idx in range(col_count))
    body_lines = [
        " | ".join(row[idx].ljust(widths[idx]) for idx in range(col_count))
        for row in normalized_rows
    ]

    lines = [header_line, separator]
    lines.extend(body_lines or ["(keine Regeln)"])
    return "\n".join(lines)


def ts():
    return datetime.now().strftime("%H:%M:%S")


def human_rate(bytes_per_sec: float) -> str:
    if bytes_per_sec < 0:
        bytes_per_sec = 0
    units = ["B/s", "KiB/s", "MiB/s", "GiB/s"]
    value = float(bytes_per_sec)
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} {units[idx]}"
    return f"{value:.1f} {units[idx]}"


def human_size(num_bytes):
    if num_bytes is None:
        return "–"
    try:
        value = float(num_bytes)
    except (TypeError, ValueError):
        return "–"
    if value < 0:
        value = 0
    units = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]
    idx = 0
    while value >= 1024 and idx < len(units) - 1:
        value /= 1024.0
        idx += 1
    if idx == 0:
        return f"{int(value)} {units[idx]}"
    return f"{value:.1f} {units[idx]}"


def call_in_ui_thread(app, fn) -> None:
    """Run fn() on the Tk main thread.

    If already on the main thread, calls fn() directly.
    Otherwise schedules it via app.after(0, fn).
    """
    import threading

    if threading.current_thread() is threading.main_thread():
        fn()
    else:
        app.after(0, fn)


__all__ = [
    "call_in_ui_thread",
    "format_table",
    "human_rate",
    "human_size",
    "safe_write_json",
    "ts",
]
