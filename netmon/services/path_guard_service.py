from __future__ import annotations

import os
import stat
from pathlib import Path


class PathGuardService:
    def _home_path_variants(self) -> tuple[str, ...]:
        home = str(Path.home())
        return (
            "$HOME/bin",
            "$HOME/.local/bin",
            "~/bin",
            "~/.local/bin",
            f"{home}/bin",
            f"{home}/.local/bin",
        )

    def _is_snap_bin_entry(self, entry: str) -> bool:
        normalized = os.path.normpath(str(entry or "").strip())
        return normalized == "/snap/bin"

    def _is_normal_user_bin_entry(self, entry: str) -> bool:
        normalized = os.path.normpath(str(entry or "").strip())
        home = os.path.normpath(str(Path.home()))
        return normalized in {
            os.path.normpath(os.path.join(home, "bin")),
            os.path.normpath(os.path.join(home, ".local", "bin")),
        }

    def _path_assignment_contains_only_normal_user_bins(self, line: str) -> bool:
        stripped = str(line or "").strip()
        if not stripped:
            return False

        normalized = stripped.replace("export ", "", 1).strip()
        if not normalized.lower().startswith("path="):
            return False

        for variant in self._home_path_variants():
            normalized = normalized.replace(variant, "")

        for token in ("PATH=", '"', "'", "$PATH", "${PATH}", ":", " "):
            normalized = normalized.replace(token, "")

        return normalized == ""

    def get_current_path_entries(self) -> list[str]:
        raw = os.environ.get("PATH", "")
        return [part.strip() for part in raw.split(":") if part.strip()]

    def get_shell_profile_paths(self) -> list[str]:
        home = Path.home()
        return [
            str(home / ".bashrc"),
            str(home / ".profile"),
            str(home / ".zshrc"),
        ]

    def analyze_path_entries(self, entries: list[str]) -> list[dict]:
        findings = []

        suspicious_tokens = ("/tmp", "/var/tmp", "/dev/shm")
        home = Path.home()
        safe_prefixes = (
            "/usr/local/sbin",
            "/usr/local/bin",
            "/usr/sbin",
            "/usr/bin",
            "/sbin",
            "/bin",
            str(home / ".local" / "bin"),
            str(home / "bin"),
        )

        for index, entry in enumerate(entries):
            item = {
                "entry": entry,
                "index": index,
                "exists": os.path.isdir(entry),
                "severity": "ok",
                "issues": [],
            }

            if entry == ".":
                item["severity"] = "high"
                item["issues"].append(
                    "Aktuelles Verzeichnis '.' im PATH ist gefährlich."
                )

            if any(entry.startswith(token) for token in suspicious_tokens):
                item["severity"] = "high"
                item["issues"].append("Temporäres oder RAM-Verzeichnis im PATH.")

            if not item["exists"]:
                if self._is_snap_bin_entry(entry):
                    if item["severity"] == "ok":
                        item["severity"] = "info"
                    item["issues"].append(
                        "/snap/bin steht im PATH, existiert aber nicht."
                    )
                else:
                    if item["severity"] != "high":
                        item["severity"] = "medium"
                    item["issues"].append("PATH-Verzeichnis existiert nicht.")

            if item["exists"]:
                try:
                    mode = os.stat(entry).st_mode
                    if mode & stat.S_IWOTH:
                        item["severity"] = "high"
                        item["issues"].append(
                            "PATH-Verzeichnis ist für alle beschreibbar."
                        )
                    elif mode & stat.S_IWGRP:
                        if item["severity"] == "ok":
                            item["severity"] = "medium"
                        item["issues"].append(
                            "PATH-Verzeichnis ist gruppenbeschreibbar."
                        )
                except Exception as exc:
                    if item["severity"] == "ok":
                        item["severity"] = "medium"
                    item["issues"].append(f"Rechte konnten nicht geprüft werden: {exc}")

            if (
                index <= 2
                and not self._is_normal_user_bin_entry(entry)
                and not any(
                    entry == prefix or entry.startswith(prefix + os.sep)
                    for prefix in safe_prefixes
                )
            ):
                if item["severity"] == "ok":
                    item["severity"] = "medium"
                item["issues"].append(
                    "Ungewöhnlicher PATH-Eintrag steht sehr weit vorne."
                )

            if self._is_normal_user_bin_entry(entry) and item["severity"] == "ok":
                item["severity"] = "info"
                item["issues"].append("Üblicher User-Bin-Pfad im PATH.")

            findings.append(item)

        return findings

    def analyze_shell_profiles(self) -> list[dict]:
        findings = []
        patterns = ("PATH=", "export PATH", "path+=", "typeset -U path")
        suspicious_tokens = (
            "/tmp",
            "/var/tmp",
            "/dev/shm",
            "$PWD",
            "`pwd`",
            "$(pwd)",
            ".:",
            ":.",
            "curl | bash",
            "wget | bash",
            "base64",
        )

        for path in self.get_shell_profile_paths():
            item = {
                "path": path,
                "exists": os.path.isfile(path),
                "matches": [],
                "severity": "ok",
            }

            if not item["exists"]:
                findings.append(item)
                continue

            try:
                with open(path, "r", encoding="utf-8", errors="replace") as handle:
                    for lineno, line in enumerate(handle, start=1):
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#"):
                            continue

                        low = stripped.lower()
                        if any(pattern.lower() in low for pattern in patterns):
                            match = {
                                "line": lineno,
                                "text": stripped[:500],
                                "severity": "info",
                                "issues": [],
                            }
                            if any(token.lower() in low for token in suspicious_tokens):
                                match["severity"] = "high"
                                match["issues"].append(
                                    "Verdächtige PATH-Manipulation im Shell-Profil."
                                )
                                item["severity"] = "high"
                            elif self._path_assignment_contains_only_normal_user_bins(
                                stripped
                            ):
                                match["severity"] = "info"
                                match["issues"].append(
                                    "Übliche User-Bin-Pfade werden eingebunden."
                                )
                                if item["severity"] == "ok":
                                    item["severity"] = "info"
                            elif item["severity"] == "ok":
                                item["severity"] = "info"

                            item["matches"].append(match)
            except Exception as exc:
                item["severity"] = "medium"
                item["matches"].append(
                    {
                        "line": "-",
                        "text": f"Datei konnte nicht gelesen werden: {exc}",
                        "severity": "medium",
                        "issues": [],
                    }
                )

            findings.append(item)

        return findings

    def run_check(self) -> dict:
        entries = self.get_current_path_entries()
        path_findings = self.analyze_path_entries(entries)
        profile_findings = self.analyze_shell_profiles()

        high = 0
        medium = 0
        for item in path_findings:
            if item.get("severity") == "high":
                high += 1
            elif item.get("severity") == "medium":
                medium += 1

        for profile in profile_findings:
            if profile.get("severity") == "high":
                high += 1
            elif profile.get("severity") == "medium":
                medium += 1

        if high:
            risk = "hoch"
        elif medium:
            risk = "mittel"
        else:
            risk = "niedrig"

        return {
            "path_entries": entries,
            "path_findings": path_findings,
            "profile_findings": profile_findings,
            "risk": risk,
            "counts": {"high": high, "medium": medium},
        }


__all__ = ["PathGuardService"]
