"""Support package helpers for NetMon diagnostics and user reports."""

from __future__ import annotations

import json
import os
import zipfile
from datetime import datetime, timezone

from netmon.config.constants import NETMON_APP_VERSION
from netmon.core.diagnostics import (
    current_os_label,
    diagnostic_reports_dir,
    diagnostic_system_info,
    latest_diagnostic_report_path,
    redact_diagnostic_value,
)
from netmon.core.state import get_netmon_documents_dir, get_netmon_documents_subdir, get_netmon_state_dir


def support_packages_dir() -> str:
    path = os.path.join(get_netmon_documents_dir(), "support")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def support_package_path(*, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now(timezone.utc)).strftime("%Y%m%d-%H%M%S")
    return os.path.join(
        support_packages_dir(),
        f"netmon-support-{stamp}.zip",
    )


def support_bundle_inputs() -> list[str]:
    diagnostics_dir = diagnostic_reports_dir()
    runtime_logs_dir = get_netmon_documents_subdir("Logs")
    state_logs_dir = os.path.join(get_netmon_state_dir(), "logs")
    candidates = [
        latest_diagnostic_report_path(),
        os.path.join(diagnostics_dir, "startup_error.log"),
        os.path.join(diagnostics_dir, "crash.log"),
        os.path.join(runtime_logs_dir, "runtime.log"),
        os.path.join(state_logs_dir, "runtime.log"),
        os.path.join(state_logs_dir, "network_debug.log"),
    ]
    seen = set()
    files = []
    for path in candidates:
        normalized = os.path.abspath(os.path.expanduser(str(path or "").strip()))
        if not normalized or normalized in seen or not os.path.isfile(normalized):
            continue
        seen.add(normalized)
        files.append(normalized)
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
    package_path = support_package_path()
    files = support_bundle_inputs()
    manifest = build_support_manifest(metadata=metadata, files=files)

    try:
        os.makedirs(os.path.dirname(package_path), exist_ok=True)
    except Exception:
        pass

    with zipfile.ZipFile(
        package_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            "manifest.json",
            json.dumps(manifest, indent=2, ensure_ascii=False),
        )
        for path in files:
            archive.write(path, arcname=os.path.join("files", os.path.basename(path)))
    return package_path


__all__ = [
    "build_support_manifest",
    "create_support_package",
    "support_bundle_inputs",
    "support_package_path",
    "support_packages_dir",
]
