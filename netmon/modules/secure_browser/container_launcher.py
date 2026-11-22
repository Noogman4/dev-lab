"""Start one managed Secure Browser profile in NetMon's Firefox sandbox."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from netmon.core.browser_domains import validate_website_filter
from tools.secure_browser_manager.browser_container_builder import (
    MAX_SCAN_FILE_SIZE,
    SANDBOX_START_COMMAND,
    WEBSITE_FILTER_BLOCK_PATTERN,
    detect_start_command,
    maintenance_read,
)

from . import sandbox, session
from .sandbox import BrowserSandboxError


def _read_policies(path, *, allow_unfiltered=False):
    payload = json.loads(maintenance_read(path, limit=MAX_SCAN_FILE_SIZE))
    if not isinstance(payload, dict):
        raise BrowserSandboxError("Die Secure-Browser-Richtlinien sind ungültig.")
    validate_website_filter(payload)
    policies = payload.get("policies", {})
    metadata = payload.get("_builder_metadata")
    if (
        allow_unfiltered
        and policies
        and "WebsiteFilter" not in policies
        and isinstance(metadata, dict)
        and metadata.get("enable_website_filter") is False
    ):
        return policies
    website_filter = policies.get("WebsiteFilter", {})
    if website_filter.get("Block") != [WEBSITE_FILTER_BLOCK_PATTERN]:
        raise BrowserSandboxError(
            "Der Secure Browser benötigt einen aktiven Domainfilter."
        )
    return policies


def _container_policies(container):
    policies = _read_policies(container / "policies.json", allow_unfiltered=True)
    policies["DisableAppUpdate"] = True
    policies["DefaultDownloadDirectory"] = "${home}/Downloads"
    return {"policies": policies}


def run_container(container):
    if not container.is_absolute() or not (container / "profile").is_dir():
        raise BrowserSandboxError("Der eigene Secure-Browser-Profilordner fehlt.")
    if os.getuid() == 0:
        raise BrowserSandboxError("NetMon startet Firefox nur als regulärer Benutzer.")
    runtime = session._managed_runtime(session.FIREFOX_DIR)
    wayland = session._wayland_socket()
    with session._lock_profile(container):
        if detect_start_command(container / "start.sh") != SANDBOX_START_COMMAND:
            raise BrowserSandboxError(
                "Die Sandbox ist für diesen Browser nicht aktiviert."
            )
        policies = _container_policies(container)
        lock = container / "child-lock.json"
        if os.path.lexists(lock):
            subprocess.run(
                [sys.executable, "-EsB", str(container / "browser_lock.py"), str(lock)],
                check=True,
            )
        with (
            session._private_bus(wayland.parent) as (bus, daemon),
            sandbox._launch_link(
                runtime, container, wayland, bus, None, policies=policies
            ) as processes,
        ):
            while sandbox._browser_running(*processes):
                if daemon.poll() is not None:
                    raise BrowserSandboxError("Der private Browser-D-Bus ist beendet.")
                time.sleep(0.25)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("container", type=Path)
    args = parser.parse_args()
    try:
        run_container(args.container)
    except subprocess.CalledProcessError:
        return 1  # The child-lock dialog handled the error or was cancelled.
    except (BrowserSandboxError, OSError, ValueError) as exc:
        print(f"Secure Browser: {exc}", file=sys.stderr)
        if os.environ.get("MOZ_DESKTOP_FILE"):
            from tkinter import TclError, messagebox

            try:
                messagebox.showerror("Secure Browser", str(exc))
            except TclError:
                pass
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
