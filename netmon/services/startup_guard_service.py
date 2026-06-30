import glob
import hashlib
import json
import os
from datetime import datetime, UTC

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    try:
        from core.utils import safe_write_json
    except ModuleNotFoundError:

        def safe_write_json(path, data):
            try:
                parent = os.path.dirname(os.path.abspath(path))
                if parent:
                    os.makedirs(parent, exist_ok=True)
                tmp_path = f"{path}.tmp"
                with open(tmp_path, "w", encoding="utf-8") as handle:
                    json.dump(
                        data, handle, ensure_ascii=False, indent=2, sort_keys=True
                    )
                    handle.write("\n")
                os.replace(tmp_path, path)
                return True, ""
            except Exception as exc:
                return False, str(exc)


class StartupGuardService:
    def __init__(self, sources=None):
        self.sources = sources or [
            ("user_autostart", os.path.expanduser("~/.config/autostart/*.desktop")),
            ("system_autostart", "/etc/xdg/autostart/*.desktop"),
            (
                "systemd_user",
                os.path.expanduser("~/.config/systemd/user/*.service"),
            ),
            ("systemd_system", "/etc/systemd/system/*.service"),
        ]

    def sha256_file(self, path: str) -> str:
        digest = hashlib.sha256()
        try:
            with open(path, "rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        except Exception:
            return ""
        return digest.hexdigest()

    def _build_entry(self, source: str, path: str) -> dict:
        entry = {
            "source": source,
            "path": path,
            "name": os.path.basename(path),
            "exists": os.path.exists(path),
            "sha256": "",
            "mtime": 0,
            "size": 0,
        }
        if not entry["exists"]:
            return entry

        try:
            stat_info = os.stat(path)
            entry["mtime"] = int(stat_info.st_mtime)
            entry["size"] = int(stat_info.st_size)
        except Exception:
            pass
        entry["sha256"] = self.sha256_file(path)
        return entry

    def collect_entries(self) -> list[dict]:
        entries = []
        seen_paths = set()
        for source, pattern in self.sources:
            for path in sorted(glob.glob(pattern)):
                normalized = os.path.abspath(path)
                if normalized in seen_paths:
                    continue
                seen_paths.add(normalized)
                entries.append(self._build_entry(source, normalized))
        entries.sort(key=lambda item: (item.get("source", ""), item.get("path", "")))
        return entries

    def load_baseline(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {}
        except Exception:
            return {}
        if isinstance(data, dict):
            data.setdefault("entries", [])
            return data
        if isinstance(data, list):
            return {"entries": data}
        return {}

    def save_baseline(self, path: str, entries: list[dict]) -> tuple[bool, str]:
        payload = {
            "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "entries": list(entries or []),
        }
        return safe_write_json(path, payload)

    def load_trustlist(self, path: str) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except FileNotFoundError:
            return {"trusted": {}}
        except Exception:
            return {"trusted": {}}
        if isinstance(data, dict):
            trusted = data.get("trusted")
            data["trusted"] = trusted if isinstance(trusted, dict) else {}
            return data
        return {"trusted": {}}

    def save_trustlist(self, path: str, trustlist: dict) -> tuple[bool, str]:
        payload = dict(trustlist or {})
        trusted = payload.get("trusted")
        payload["trusted"] = trusted if isinstance(trusted, dict) else {}
        return safe_write_json(path, payload)

    def is_trusted(self, entry: dict, trustlist: dict) -> bool:
        trusted = ((trustlist or {}).get("trusted") or {}).get(entry.get("path"))
        return bool(trusted and trusted.get("sha256") == entry.get("sha256"))

    def mark_trusted(
        self, path: str, entry: dict, trustlist_path: str
    ) -> tuple[bool, str]:
        normalized_path = str(path or "").strip()
        if not normalized_path:
            return False, "Pfad fehlt"

        item = dict(entry or {})
        sha256 = str(item.get("sha256") or "").strip()
        if not sha256:
            return False, "SHA256 fehlt"

        trustlist = self.load_trustlist(trustlist_path)
        trusted = dict(trustlist.get("trusted") or {})
        trusted[normalized_path] = {
            "name": item.get("name") or os.path.basename(normalized_path),
            "source": item.get("source") or "",
            "sha256": sha256,
            "trusted_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "note": "vom Nutzer als bekannt markiert",
        }
        trustlist["trusted"] = trusted
        return self.save_trustlist(trustlist_path, trustlist)

    def remove_trusted(self, path: str, trustlist_path: str) -> tuple[bool, str]:
        normalized_path = str(path or "").strip()
        if not normalized_path:
            return False, "Pfad fehlt"

        trustlist = self.load_trustlist(trustlist_path)
        trusted = dict(trustlist.get("trusted") or {})
        trusted.pop(normalized_path, None)
        trustlist["trusted"] = trusted
        return self.save_trustlist(trustlist_path, trustlist)

    def reset_trustlist(self, trustlist_path: str) -> tuple[bool, str]:
        return self.save_trustlist(trustlist_path, {"trusted": {}})

    def compare_to_baseline(
        self, baseline: dict, current: list[dict], trustlist: dict | None = None
    ) -> dict:
        baseline_entries = list((baseline or {}).get("entries") or [])
        current_entries = list(current or [])
        trustlist_data = trustlist or {"trusted": {}}

        baseline_map = {
            str(item.get("path") or ""): item
            for item in baseline_entries
            if str(item.get("path") or "")
        }
        current_map = {
            str(item.get("path") or ""): item
            for item in current_entries
            if str(item.get("path") or "")
        }

        new_entries = []
        removed_entries = []
        changed_entries = []
        trusted_entries = []
        unchanged_entries = []

        for path, current_entry in current_map.items():
            baseline_entry = baseline_map.get(path)
            if baseline_entry is None:
                if self.is_trusted(current_entry, trustlist_data):
                    trusted_entries.append(current_entry)
                else:
                    new_entries.append(current_entry)
                continue
            changed = any(
                baseline_entry.get(field) != current_entry.get(field)
                for field in ("sha256", "size", "mtime")
            )
            if changed:
                changed_item = {
                    "before": baseline_entry,
                    "after": current_entry,
                }
                if self.is_trusted(current_entry, trustlist_data):
                    trusted_entries.append(changed_item)
                else:
                    changed_entries.append(changed_item)
            else:
                unchanged_entries.append(current_entry)

        for path, baseline_entry in baseline_map.items():
            if path not in current_map:
                removed_entries.append(baseline_entry)

        new_entries.sort(key=lambda item: item.get("path", ""))
        removed_entries.sort(key=lambda item: item.get("path", ""))
        changed_entries.sort(
            key=lambda item: item.get("after", {}).get("path")
            or item.get("before", {}).get("path", "")
        )
        trusted_entries.sort(
            key=lambda item: item.get("path")
            or item.get("after", {}).get("path")
            or item.get("before", {}).get("path", "")
        )
        unchanged_entries.sort(key=lambda item: item.get("path", ""))

        return {
            "new": new_entries,
            "removed": removed_entries,
            "changed": changed_entries,
            "trusted": trusted_entries,
            "unchanged": unchanged_entries,
        }
