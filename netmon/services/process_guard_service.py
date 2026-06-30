from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime, UTC

try:
    import psutil
except ModuleNotFoundError:
    psutil = None

try:
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    try:
        from core.utils import safe_write_json
    except ModuleNotFoundError:

        def safe_write_json(path, data, **_kwargs):
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2, ensure_ascii=False)
            return True, ""


class ProcessGuardService:
    def __init__(self):
        home = str(Path.home())
        self.temp_prefixes = ("/tmp", "/var/tmp", "/dev/shm")
        self.user_suspicious_prefixes = (
            os.path.join(home, "Downloads"),
            os.path.join(home, ".cache"),
            os.path.join(home, ".local", "tmp"),
        )
        self.browser_parent_names = {
            "firefox",
            "chrome",
            "chromium",
            "brave",
            "opera",
            "microsoft-edge",
            "libreoffice",
            "soffice",
            "evince",
            "okular",
        }
        self.suspicious_cmd_tokens = (
            "curl",
            "wget",
            "bash -c",
            "sh -c",
            "python -c",
            "python3 -c",
            "base64 -d",
            "nc ",
            "netcat",
            "socat",
        )
        self.suspicious_cmd_patterns = (
            r"(^|\s)curl(\s|$)",
            r"(^|\s)wget(\s|$)",
            r"(^|\s)bash\s+-c(\s|$)",
            r"(^|\s)sh\s+-c(\s|$)",
            r"(^|\s)python\s+-c(\s|$)",
            r"(^|\s)python3\s+-c(\s|$)",
            r"(^|\s)base64\s+-d(\s|$)",
            r"(^|\s)nc(\s|$)",
            r"(^|\s)netcat(\s|$)",
            r"(^|\s)socat(\s|$)",
        )

    def is_available(self) -> bool:
        return psutil is not None or shutil.which("ps") is not None

    def availability_reason(self) -> str:
        if psutil is None and shutil.which("ps") is None:
            return "python3-psutil fehlt und `ps` ist nicht verfügbar."
        return ""

    def snapshot_processes(self) -> list[dict]:
        if psutil is None:
            return self._snapshot_processes_via_ps()

        processes = []
        for proc in psutil.process_iter(
            [
                "pid",
                "ppid",
                "name",
                "exe",
                "cmdline",
                "cwd",
                "username",
                "create_time",
                "status",
            ]
        ):
            try:
                info = proc.info or {}
                processes.append(
                    {
                        "pid": int(info.get("pid") or 0),
                        "ppid": int(info.get("ppid") or 0),
                        "name": str(info.get("name") or "").strip(),
                        "exe": str(info.get("exe") or "").strip(),
                        "cmdline": list(info.get("cmdline") or []),
                        "cwd": str(info.get("cwd") or "").strip(),
                        "username": str(info.get("username") or "").strip(),
                        "create_time": float(info.get("create_time") or 0.0),
                        "status": str(info.get("status") or "").strip(),
                    }
                )
            except (
                psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess,
                ValueError,
                TypeError,
            ):
                continue
        return processes

    def _snapshot_processes_via_ps(self) -> list[dict]:
        try:
            result = subprocess.run(
                [
                    "ps",
                    "-eo",
                    "pid=,ppid=,user=,comm=,etimes=,stat=,args=",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                timeout=8,
                check=False,
            )
        except Exception:
            return []

        processes = []
        now = time.time()
        for raw_line in str(result.stdout or "").splitlines():
            line = str(raw_line or "").rstrip()
            if not line:
                continue
            parts = re.split(r"\s+", line.strip(), maxsplit=6)
            if len(parts) < 7:
                continue
            pid_text, ppid_text, user, comm, etimes_text, status, args_text = parts
            try:
                pid = int(pid_text)
                ppid = int(ppid_text)
                etimes = int(etimes_text)
            except Exception:
                continue
            cmdline = [part for part in str(args_text or "").split() if part]
            exe = self._read_proc_link(pid, "exe")
            cwd = self._read_proc_link(pid, "cwd")
            create_time = max(0.0, now - max(etimes, 0))
            processes.append(
                {
                    "pid": pid,
                    "ppid": ppid,
                    "name": str(comm or "").strip(),
                    "exe": exe,
                    "cmdline": cmdline,
                    "cwd": cwd,
                    "username": str(user or "").strip(),
                    "create_time": create_time,
                    "status": str(status or "").strip(),
                }
            )
        return processes

    def _read_proc_link(self, pid: int, entry: str) -> str:
        try:
            return os.readlink(f"/proc/{int(pid)}/{entry}").strip()
        except Exception:
            return ""

    def process_signature(self, proc: dict) -> tuple[int, float]:
        return (int(proc.get("pid") or 0), float(proc.get("create_time") or 0.0))

    def trust_signature(self, finding: dict) -> str:
        name = str(finding.get("name") or "").strip().lower()
        exe = str(finding.get("exe") or "").strip().lower()
        user = str(finding.get("user") or "").strip().lower()
        return "|".join([name, exe, user])

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
        return safe_write_json(path, payload, indent=2, ensure_ascii=False)

    def is_trusted(self, finding: dict, trustlist: dict) -> bool:
        signature = self.trust_signature(finding)
        trusted = ((trustlist or {}).get("trusted") or {}).get(signature)
        return bool(trusted)

    def mark_trusted(self, finding: dict, trustlist_path: str) -> tuple[bool, str]:
        signature = self.trust_signature(finding)
        if not signature.strip("|"):
            return False, "Signatur fehlt"
        trustlist = self.load_trustlist(trustlist_path)
        trusted = dict(trustlist.get("trusted") or {})
        trusted[signature] = {
            "name": finding.get("name") or "-",
            "exe": finding.get("exe") or "-",
            "user": finding.get("user") or "-",
            "parent_name": finding.get("parent_name") or "-",
            "trusted_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "note": "vom Nutzer als bekannt markiert",
        }
        trustlist["trusted"] = trusted
        return self.save_trustlist(trustlist_path, trustlist)

    def remove_trusted(self, finding: dict, trustlist_path: str) -> tuple[bool, str]:
        signature = self.trust_signature(finding)
        if not signature.strip("|"):
            return False, "Signatur fehlt"
        trustlist = self.load_trustlist(trustlist_path)
        trusted = dict(trustlist.get("trusted") or {})
        trusted.pop(signature, None)
        trustlist["trusted"] = trusted
        return self.save_trustlist(trustlist_path, trustlist)

    def reset_trustlist(self, trustlist_path: str) -> tuple[bool, str]:
        return self.save_trustlist(trustlist_path, {"trusted": {}})

    def evaluate_process(self, proc: dict, parent: dict | None = None) -> dict | None:
        reasons = []
        score = 0

        exe = str(proc.get("exe") or "").strip()
        name = str(proc.get("name") or "").strip()
        cwd = str(proc.get("cwd") or "").strip()
        user = str(proc.get("username") or "").strip()
        cmdline = [str(part or "").strip() for part in list(proc.get("cmdline") or [])]
        cmdline_text = " ".join(part for part in cmdline if part).strip().lower()
        parent_name = str((parent or {}).get("name") or "").strip().lower()

        candidate_paths = [path for path in [exe, cwd, *cmdline[1:]] if path]

        temp_hit = self._first_matching_prefix(candidate_paths, self.temp_prefixes)
        if temp_hit:
            score += 5
            reasons.append(f"Ausführung aus temporärem Pfad: {temp_hit}")

        user_path_hit = self._first_matching_prefix(
            candidate_paths, self.user_suspicious_prefixes
        )
        if user_path_hit:
            score += 3
            reasons.append(f"Start aus Nutzerpfad mit erhöhtem Risiko: {user_path_hit}")

        if self._match_suspicious_cmdline(cmdline_text):
            score += 3
            reasons.append("Verdächtige Kommandozeilenmuster erkannt.")

        if (
            parent_name in self.browser_parent_names
            and self._looks_like_shell_or_script(name, exe, cmdline)
        ):
            score += 4
            reasons.append(f"Parent-Prozess ist {parent_name}, Child ist Shell/Script.")

        if user == "root" and (temp_hit or user_path_hit):
            score += 5
            reasons.append("Root-Prozess läuft aus ungewöhnlichem Pfad.")

        if exe.endswith(" (deleted)"):
            score += 5
            reasons.append("Executable wurde gelöscht, Prozess läuft aber weiter.")
        elif exe.startswith("/") and not os.path.exists(exe):
            score += 2
            reasons.append("Executable-Pfad ist nicht mehr vorhanden.")

        if self._looks_random_or_fake_name(name):
            score += 2
            reasons.append("Prozessname wirkt ungewöhnlich oder tarnt sich.")

        if score <= 0:
            return None

        if score >= 6:
            risk_level = "high"
        elif score >= 3:
            risk_level = "medium"
        else:
            risk_level = "low"

        display_exe = exe or "-"
        if not exe and not cwd and not any(cmdline):
            display_exe = "Kernel-Thread"

        return {
            "pid": int(proc.get("pid") or 0),
            "ppid": int(proc.get("ppid") or 0),
            "name": name or "-",
            "exe": display_exe,
            "cwd": cwd or "-",
            "cmdline": cmdline,
            "user": user or "-",
            "parent_name": parent_name or "-",
            "risk_score": score,
            "risk_level": risk_level,
            "reasons": reasons,
            "summary": self._build_summary(name or "-", risk_level, reasons),
        }

    def run_check(self, trustlist: dict | None = None) -> dict:
        if not self.is_available():
            return {
                "available": False,
                "reason": self.availability_reason(),
                "processes_count": 0,
                "findings": [],
                "risk": "unbekannt",
                "counts": {"high": 0, "medium": 0, "low": 0},
            }

        processes = self.snapshot_processes()
        parent_map = {int(item.get("pid") or 0): item for item in processes}
        findings = []
        counts = {"high": 0, "medium": 0, "low": 0}

        for proc in processes:
            parent = parent_map.get(int(proc.get("ppid") or 0))
            finding = self.evaluate_process(proc, parent=parent)
            if not finding:
                continue
            if self.is_trusted(finding, trustlist or {"trusted": {}}):
                continue
            findings.append(finding)
            counts[finding["risk_level"]] += 1

        findings.sort(
            key=lambda item: (
                {"high": 0, "medium": 1, "low": 2}.get(item.get("risk_level"), 3),
                -int(item.get("risk_score") or 0),
                str(item.get("name") or ""),
            )
        )

        if counts["high"]:
            risk = "hoch"
        elif counts["medium"]:
            risk = "mittel"
        elif findings:
            risk = "niedrig"
        else:
            risk = "niedrig"

        return {
            "available": True,
            "processes_count": len(processes),
            "findings": findings,
            "risk": risk,
            "counts": counts,
        }

    def detect_new_findings(
        self,
        processes: list[dict],
        known_processes: set[tuple[int, float]],
        trustlist: dict | None = None,
    ) -> tuple[list[dict], set[tuple[int, float]]]:
        parent_map = {int(item.get("pid") or 0): item for item in processes}
        updated_known = set(known_processes or set())
        new_findings = []

        for proc in processes:
            signature = self.process_signature(proc)
            if signature in updated_known:
                continue
            updated_known.add(signature)
            parent = parent_map.get(int(proc.get("ppid") or 0))
            finding = self.evaluate_process(proc, parent=parent)
            if finding and not self.is_trusted(finding, trustlist or {"trusted": {}}):
                new_findings.append(finding)

        new_findings.sort(
            key=lambda item: (
                {"high": 0, "medium": 1, "low": 2}.get(item.get("risk_level"), 3),
                -int(item.get("risk_score") or 0),
            )
        )
        return new_findings, updated_known

    def _first_matching_prefix(
        self, values: list[str], prefixes: tuple[str, ...]
    ) -> str:
        for raw_value in values:
            value = str(raw_value or "").strip()
            if not value:
                continue
            normalized = os.path.normpath(value)
            for prefix in prefixes:
                normalized_prefix = os.path.normpath(prefix)
                if normalized == normalized_prefix or normalized.startswith(
                    normalized_prefix + os.sep
                ):
                    return value
        return ""

    def _match_suspicious_cmdline(self, cmdline_text: str) -> bool:
        text = str(cmdline_text or "").strip().lower()
        if not text:
            return False
        return any(
            re.search(pattern, text, flags=re.IGNORECASE)
            for pattern in self.suspicious_cmd_patterns
        )

    def _looks_like_shell_or_script(
        self, name: str, exe: str, cmdline: list[str]
    ) -> bool:
        lowered_name = (name or "").lower()
        lowered_exe = (exe or "").lower()
        if lowered_name in {"bash", "sh", "dash", "zsh", "python", "python3"}:
            return True
        if lowered_exe.endswith(
            ("/bash", "/sh", "/dash", "/zsh", "/python", "/python3")
        ):
            return True
        for item in cmdline[1:]:
            lowered = item.lower()
            if lowered.endswith((".sh", ".py")):
                return True
        return False

    def _looks_random_or_fake_name(self, name: str) -> bool:
        lowered = (name or "").strip().lower()
        if not lowered:
            return False
        if re.fullmatch(r"[a-z0-9]{12,}", lowered):
            return True
        if lowered.count(".") >= 2:
            return True
        return lowered in {"systemd-update", "chrome-update", "firefox-update"}

    def _build_summary(self, name: str, risk_level: str, reasons: list[str]) -> str:
        if reasons:
            return f"{name}: {risk_level} ({reasons[0]})"
        return f"{name}: {risk_level}"
