"""Private, bounded reading progress; catalog entries and commands stay unchanged."""

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re

try:
    from netmon.core.private_state import (
        private_state_lock,
        read_private_json,
        write_private_json,
    )
    from netmon.core.state import get_netmon_documents_subdir
    from netmon.core.utils import user_json_write_scope
except ModuleNotFoundError:
    from core.private_state import (
        private_state_lock,
        read_private_json,
        write_private_json,
    )
    from core.state import get_netmon_documents_subdir
    from core.utils import user_json_write_scope

UNCHANGED = object()
MAX_ENTRIES = 2000


def entry_key(entry):
    """Do not transfer progress to a different command reusing an imported ID."""
    identity = [
        entry.get("entry_type", "command"),
        entry.get("id", ""),
        entry.get("name", ""),
        entry.get("cmd", ""),
    ]
    return hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode()).hexdigest()


def _bookmark(value):
    if not isinstance(value, dict) or set(value) != {"tab", "position"}:
        raise ValueError("Invalid bookmark")
    position = value["position"]
    if (
        not isinstance(value["tab"], str)
        or value["tab"] not in {"documentation", "short_info"}
        or type(position) not in (int, float)
        or not math.isfinite(position)
        or not 0 <= position <= 1
    ):
        raise ValueError("Invalid bookmark position")
    return {"tab": value["tab"], "position": round(position, 6)}


class ReadingState:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else None
        self.entries = {}
        try:
            self.entries = self._load()
        except (OSError, ValueError, UnicodeError, RecursionError):
            # Reading remains available; a later save must still reject bad state.
            pass

    def _path(self):
        if self.path is None:
            self.path = Path(get_netmon_documents_subdir("LinuxHelp")) / "reading.json"
        return self.path

    def _load(self):
        try:
            payload = read_private_json(self._path())
        except FileNotFoundError:
            return {}
        entries = payload.get("entries")
        if (
            type(payload.get("version")) is not int
            or payload["version"] != 1
            or not isinstance(entries, dict)
            or len(entries) > MAX_ENTRIES
        ):
            raise ValueError("Invalid reading state")
        result = {}
        for key, value in entries.items():
            if (
                not re.fullmatch(r"[0-9a-f]{64}", key)
                or not isinstance(value, dict)
                or set(value) - {"read", "bookmark"}
                or type(value.get("read")) is not bool
            ):
                raise ValueError("Invalid reading entry")
            result[key] = {"read": value["read"]}
            if "bookmark" in value:
                result[key]["bookmark"] = _bookmark(value["bookmark"])
        return result

    def get(self, entry):
        return deepcopy(self.entries.get(entry_key(entry), {"read": False}))

    def change(self, entry=None, *, read=None, bookmark=UNCHANGED, reset_read=False):
        with user_json_write_scope(self._path()):
            return self._change(
                entry, read=read, bookmark=bookmark, reset_read=reset_read
            )

    def _change(self, entry=None, *, read=None, bookmark=UNCHANGED, reset_read=False):
        path = self._path()
        # Serialize the whole read/modify/write across NetMon instances.
        with private_state_lock(path.with_name(".linux_help_reading_update.lock")):
            entries = self._load()
            if reset_read:
                for value in entries.values():
                    value["read"] = False
            else:
                key = entry_key(entry)
                value = entries.setdefault(key, {"read": False})
                if read is not None:
                    if type(read) is not bool:
                        raise ValueError("Invalid read flag")
                    value["read"] = read
                if bookmark is None:
                    value.pop("bookmark", None)
                elif bookmark is not UNCHANGED:
                    value["bookmark"] = _bookmark(bookmark)
            entries = {
                key: value
                for key, value in entries.items()
                if value["read"] or "bookmark" in value
            }
            if len(entries) > MAX_ENTRIES:
                raise ValueError("Too many reading entries")
            write_private_json(path, {"version": 1, "entries": entries})
            self.entries = entries
        return self.get(entry) if entry is not None else None
