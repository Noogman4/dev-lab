"""Bounded reading of user-selected import files before any parser sees them."""

import json
import os
import re
import stat

_JSON_STRING = re.compile(r'"(?:[^"\\]|\\.)*"', re.DOTALL)


class ImportLimitError(ValueError):
    """A selected import file exceeds a fixed resource limit."""


def _size_text(size):
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):g} MiB"
    if size >= 1024:
        return f"{size / 1024:g} KiB"
    return f"{size} Bytes"


def read_bounded_bytes(path, max_bytes, *, label="Import"):
    """Read one regular file with at most ``max_bytes``; never follow a symlink."""
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise ImportLimitError(f"{label}: Datei kann nicht geöffnet werden.") from exc
    too_large = f"{label}: Datei ist größer als {_size_text(max_bytes)}."
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ImportLimitError(f"{label}: keine reguläre Datei.")
    except BaseException:
        os.close(descriptor)
        raise
    with os.fdopen(descriptor, "rb") as source:
        if before.st_size > max_bytes:
            raise ImportLimitError(too_large)
        payload = source.read(max_bytes + 1)
        after = os.fstat(source.fileno())
    if len(payload) > max_bytes:
        raise ImportLimitError(too_large)
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    ):
        raise ImportLimitError(f"{label}: Datei hat sich beim Lesen geändert.")
    return payload


def read_bounded_text(path, max_bytes, *, label="Import", encoding="utf-8"):
    payload = read_bounded_bytes(path, max_bytes, label=label)
    try:
        return payload.decode(encoding)
    except UnicodeDecodeError as exc:
        raise ImportLimitError(f"{label}: Datei ist kein gültiges {encoding}.") from exc


def load_bounded_json(path, max_bytes, *, max_containers=100_000, label="Import"):
    """Parse JSON only after byte and container-count limits are met.

    Counting ``[``/``{`` outside string literals bounds the number of Python
    lists and dicts json.loads can allocate; nesting depth is additionally
    bounded by the interpreter's recursion limit (RecursionError is mapped).
    """
    text = read_bounded_text(path, max_bytes, label=label)
    skeleton = _JSON_STRING.sub("", text)
    if skeleton.count("[") + skeleton.count("{") > max_containers:
        raise ImportLimitError(f"{label}: zu viele JSON-Strukturen.")
    try:
        return json.loads(text)
    except RecursionError as exc:
        raise ImportLimitError(f"{label}: JSON ist zu tief verschachtelt.") from exc


def bounded_list(value, max_items, *, label="Import", field="Liste"):
    """Return ``value`` as list, refusing more than ``max_items`` entries."""
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ImportLimitError(f"{label}: {field} ist keine Liste.")
    if len(value) > max_items:
        raise ImportLimitError(f"{label}: {field} hat mehr als {max_items} Einträge.")
    return list(value)
