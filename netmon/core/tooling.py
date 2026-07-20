"""Tool discovery and small loader helpers for NetMon."""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess


def has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def get_cmd_path(name: str) -> str:
    return shutil.which(name) or ""


def _existing_dir(path: str) -> str:
    return path if path and os.path.isdir(path) else ""


def _picture_fallback_dirs() -> list[str]:
    return [
        os.path.expanduser("~/Bilder"),
        os.path.expanduser("~/Pictures"),
    ]


def get_user_pictures_dir() -> str:
    if has_cmd("xdg-user-dir"):
        try:
            proc = subprocess.run(
                ["xdg-user-dir", "PICTURES"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=3,
                check=False,
            )
            pic_dir = (proc.stdout or "").strip()
            if proc.returncode == 0 and _existing_dir(pic_dir):
                return pic_dir
        except Exception:
            pass

    for candidate in _picture_fallback_dirs():
        if _existing_dir(candidate):
            return candidate

    return os.path.expanduser("~")


def _speedtest_module_candidates(
    *, app_file: str, repo_root: str, search_paths
) -> list[str]:
    base_dir = os.path.dirname(os.path.abspath(app_file))
    candidates = [
        os.path.join(base_dir, "modules", "speedtest.py"),
        os.path.join(repo_root, "netmon", "modules", "speedtest.py"),
        os.path.join(repo_root, "modules", "speedtest.py"),
        "/usr/lib/netmon/netmon/modules/speedtest.py",
        "/opt/netmon/netmon/modules/speedtest.py",
    ]

    for path_entry in search_paths:
        if not path_entry:
            continue
        candidates.append(os.path.join(path_entry, "netmon", "modules", "speedtest.py"))
        candidates.append(os.path.join(path_entry, "modules", "speedtest.py"))
    return candidates


def _unique_absolute_paths(paths) -> tuple[list[str], list[str]]:
    checked = []
    seen = set()
    unique = []
    for path in paths:
        abs_path = os.path.abspath(path)
        if abs_path in seen:
            continue
        seen.add(abs_path)
        checked.append(abs_path)
        unique.append(abs_path)
    return unique, checked


def load_speedtest_module_from_file(*, app_file: str, repo_root: str, search_paths):
    candidates, checked = _unique_absolute_paths(
        _speedtest_module_candidates(
            app_file=app_file,
            repo_root=repo_root,
            search_paths=search_paths,
        )
    )
    for module_file in candidates:
        if not os.path.isfile(module_file):
            continue

        spec = importlib.util.spec_from_file_location(
            "netmon_speedtest_module", module_file
        )
        if spec is None or spec.loader is None:
            continue

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod, module_file

    raise ModuleNotFoundError(
        "Datei fehlt oder nicht ladbar. Geprüft: " + ", ".join(checked)
    )


def check_speedtest_module_available(*, app_file: str, repo_root: str, search_paths):
    try:
        mod, module_file = load_speedtest_module_from_file(
            app_file=app_file,
            repo_root=repo_root,
            search_paths=search_paths,
        )
    except Exception as exc:
        return False, f"Import fehlgeschlagen: {exc}"

    required = ("run_speedtest", "format_speedtest_summary", "format_speedtest_table")
    missing = [name for name in required if not callable(getattr(mod, name, None))]
    if missing:
        return False, "Fehlende Funktionen: " + ", ".join(missing)
    return True, module_file


__all__ = [
    "check_speedtest_module_available",
    "get_cmd_path",
    "get_user_pictures_dir",
    "has_cmd",
    "load_speedtest_module_from_file",
]
