"""Support package helpers for NetMon diagnostics and user reports."""

from __future__ import annotations

import json
import os
import shutil
import stat
import zipfile
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone

from netmon.config.constants import NETMON_APP_VERSION
from netmon.core.diagnostics import (
    current_os_label,
    diagnostic_reports_dir,
    diagnostic_system_info,
    latest_diagnostic_report_path,
    redact_diagnostic_value,
)
from netmon.core.state import (
    get_netmon_documents_dir,
    get_netmon_documents_subdir,
    get_netmon_state_dir,
)

try:
    from netmon.core.performance_monitor import measure
except ModuleNotFoundError:
    from core.performance_monitor import measure


def support_packages_dir() -> str:
    path = os.path.join(get_netmon_documents_dir(), "support")
    try:
        os.makedirs(path, mode=0o700, exist_ok=True)
    except Exception:
        pass
    return path


def support_package_path(*, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return os.path.join(
        support_packages_dir(),
        f"netmon-support-{stamp}.zip",
    )


def _support_bundle_candidate_paths() -> list[str]:
    diagnostics_dir = diagnostic_reports_dir()
    runtime_logs_dir = get_netmon_documents_subdir("Logs")
    state_logs_dir = os.path.join(get_netmon_state_dir(), "logs")
    return [
        latest_diagnostic_report_path(),
        os.path.join(diagnostics_dir, "startup_error.log"),
        os.path.join(diagnostics_dir, "crash.log"),
        os.path.join(runtime_logs_dir, "runtime.log"),
        os.path.join(state_logs_dir, "runtime.log"),
        os.path.join(state_logs_dir, "network_debug.log"),
    ]


def _approved_input(path: str) -> bool:
    parent, name = os.path.split(path)
    approved = {
        os.path.abspath(diagnostic_reports_dir()): (
            name in {"startup_error.log", "crash.log"}
            or (name.startswith("netmon-") and name.endswith(".json"))
        ),
        os.path.abspath(get_netmon_documents_subdir("Logs")): name == "runtime.log",
        os.path.abspath(os.path.join(get_netmon_state_dir(), "logs")): name
        in {"runtime.log", "network_debug.log"},
    }
    return approved.get(parent, False)


@contextmanager
def _open_directory(path: str):
    """Walk every component without following directory symlinks (Linux)."""
    if not all(hasattr(os, flag) for flag in ("O_NOFOLLOW", "O_DIRECTORY")):
        raise OSError("Secure support export requires no-follow directory opens")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(os.path.sep, flags)
    try:
        for component in os.path.abspath(path).split(os.path.sep):
            if not component:
                continue
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or info.st_mode & 0o022:
            raise OSError("Support directory has unsafe ownership or permissions")
        yield fd
    finally:
        os.close(fd)


def _trusted_input(info) -> bool:
    return (
        stat.S_ISREG(info.st_mode)
        and info.st_nlink == 1
        and info.st_uid == os.geteuid()
        and not info.st_mode & 0o022
    )


@contextmanager
def _open_support_input(path: str):
    if not _approved_input(path):
        raise OSError("Unapproved support input")
    with _open_directory(os.path.dirname(path)) as directory_fd:
        name = os.path.basename(path)
        before = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        if not _trusted_input(before):
            raise OSError("Unsafe support input")
        # O_NONBLOCK prevents a raced-in FIFO from blocking before fstat.
        fd = os.open(
            name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd
        )
        with os.fdopen(fd, "rb") as source:
            after = os.fstat(source.fileno())
            if not _trusted_input(after) or (before.st_dev, before.st_ino) != (
                after.st_dev,
                after.st_ino,
            ):
                raise OSError("Support input changed during open")
            yield source


def _existing_unique_files(paths) -> list[str]:
    seen = set()
    files = []
    for path in paths:
        if not path:
            continue
        normalized = os.path.abspath(os.path.expanduser(str(path).strip()))
        if normalized in seen:
            continue
        try:
            with _open_support_input(normalized):
                pass
        except OSError:
            continue
        seen.add(normalized)
        files.append(normalized)
    return files


def support_bundle_inputs() -> list[str]:
    with measure(
        area="diagnostics",
        operation="support_bundle_inputs",
        mode="detailed",
    ) as measurement:
        files = _existing_unique_files(_support_bundle_candidate_paths())
        measurement.add_metadata(file_count=len(files))
        return files


def build_support_manifest(*, metadata: dict | None = None, files=None) -> dict:
    normalized_files = [str(path) for path in (files or [])]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "netmon_version": NETMON_APP_VERSION,
        "os": current_os_label(),
        "system": redact_diagnostic_value(diagnostic_system_info()),
        "metadata": redact_diagnostic_value(dict(metadata or {})),
        "files": normalized_files,
    }


def create_support_package(*, metadata: dict | None = None) -> str:
    with measure(
        area="diagnostics",
        operation="create_support_package",
        mode="basic",
    ) as measurement:
        package_path = support_package_path()
        files = support_bundle_inputs()
        with ExitStack() as stack:
            sources = []
            for path in files:
                try:
                    source = stack.enter_context(_open_support_input(path))
                except OSError:
                    continue
                sources.append((path, source))
            measurement.add_metadata(file_count=len(sources))
            manifest = build_support_manifest(
                metadata=metadata, files=[path for path, _source in sources]
            )
            # Exclusive, private output: never follow or overwrite a preexisting ZIP.
            with _open_directory(os.path.dirname(package_path)) as directory_fd:
                output_fd = os.open(
                    os.path.basename(package_path),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o600,
                    dir_fd=directory_fd,
                )
            with (
                os.fdopen(output_fd, "wb") as output,
                zipfile.ZipFile(
                    output, mode="w", compression=zipfile.ZIP_DEFLATED
                ) as archive,
            ):
                archive.writestr(
                    "manifest.json",
                    json.dumps(manifest, indent=2, ensure_ascii=False),
                )
                for path, source in sources:
                    with archive.open(
                        "files/" + os.path.basename(path), "w"
                    ) as destination:
                        shutil.copyfileobj(source, destination, length=64 * 1024)
        return package_path


__all__ = [
    "build_support_manifest",
    "create_support_package",
    "support_bundle_inputs",
    "support_package_path",
    "support_packages_dir",
]
