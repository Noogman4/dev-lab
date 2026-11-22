#!/usr/bin/env python3
"""Read NetMon's canonical application version without importing the app."""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSTANTS_FILE = ROOT / "netmon" / "config" / "constants.py"

# Release version scheme, identical to netmon/core/release_version.py (the
# release tooling runs from a snapshot without importing the app):
# ``1.1.22`` final release, ``1.1.22~beta1`` "NetMon 1.1.22 Public Beta 1".
_VERSION = re.compile(
    r"(?P<base>(?:0|[1-9][0-9]{0,8})(?:\.(?:0|[1-9][0-9]{0,8})){1,3})"
    r"(?:~beta(?P<beta>[1-9][0-9]{0,3}))?"
)


def parse_release_version(value):
    """Return ``(base_tuple, beta_number_or_None)`` or ``None`` if invalid."""
    if not isinstance(value, str):
        return None
    match = _VERSION.fullmatch(value)
    if match is None:
        return None
    base = tuple(int(part) for part in match["base"].split("."))
    beta = int(match["beta"]) if match["beta"] else None
    return base, beta


def is_release_version(value):
    return parse_release_version(value) is not None


def is_prerelease(value):
    parsed = parse_release_version(value)
    return parsed is not None and parsed[1] is not None


def release_sort_key(value):
    """Sort key that matches ``dpkg --compare-versions`` for valid versions."""
    parsed = parse_release_version(value)
    if parsed is None:
        raise ValueError(f"Keine gueltige NetMon-Version: {value!r}")
    base, beta = parsed
    # A beta of X sorts below X itself (Debian ``~``), betas numerically.
    return base, (0, beta) if beta is not None else (1, 0)


def compare_release_versions(left, right):
    left_key, right_key = release_sort_key(left), release_sort_key(right)
    return (left_key > right_key) - (left_key < right_key)


def display_version(value):
    """``1.1.22~beta1`` -> ``1.1.22 Public Beta 1``; other strings unchanged."""
    parsed = parse_release_version(value)
    if parsed is None or parsed[1] is None:
        return str(value or "")
    base, beta = parsed
    return f"{'.'.join(map(str, base))} Public Beta {beta}"


def latest_metadata_error(latest, version):
    """Check that ``latest-version.json`` announces ``version``; else explain.

    Final release: top-level ``version`` names it (unchanged contract that
    every installed client reads). Public beta: either the same, or, to keep
    stable installations on the stable channel, an additional ``beta`` object
    names it while ``version`` stays on an older final release. Clients that
    run a beta consider both entries and update to the newer one, so a beta
    reaches later betas and the final release.
    """
    if not isinstance(latest, dict):
        return "latest-version.json ist kein Objekt"
    if latest.get("version") == version:
        beta = latest.get("beta")
        if beta is not None and not (
            isinstance(beta, dict) and is_prerelease(beta.get("version"))
        ):
            return "latest-version.json: ungueltiger beta-Eintrag"
        return None
    if not is_prerelease(version):
        return (
            f"latest-version.json: erwartet Version {version}, "
            f"gefunden {latest.get('version')!r}"
        )
    beta = latest.get("beta")
    if not isinstance(beta, dict) or beta.get("version") != version:
        return (
            f"latest-version.json: Beta {version} weder als version "
            "noch als beta.version eingetragen"
        )
    stable = latest.get("version")
    if (
        not is_release_version(stable)
        or is_prerelease(stable)
        or compare_release_versions(stable, version) >= 0
    ):
        return (
            "latest-version.json: version muss neben einer Beta eine aeltere "
            f"finale Version sein, gefunden {stable!r}"
        )
    return None


def read_netmon_version(path: Path = CONSTANTS_FILE) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "NETMON_APP_VERSION"
            for target in node.targets
        ):
            continue
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            version = node.value.value.strip()
            if version:
                return version
    raise ValueError(f"NETMON_APP_VERSION fehlt in {path}")


if __name__ == "__main__":
    print(read_netmon_version())
