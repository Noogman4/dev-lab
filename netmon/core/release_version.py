"""NetMon release version scheme: final releases and public betas.

Accepted forms (Debian package versions, no epoch, no revision):

* ``1.1.22``        final release
* ``1.1.22~beta1``  "NetMon 1.1.22 Public Beta 1"

The tilde makes every beta sort *before* its final release, exactly like
``dpkg --compare-versions`` and APT do, so the sequence
``1.1.21 < 1.1.22~beta1 < 1.1.22~beta2 < 1.1.22`` holds both for package
upgrades and for the in-app update hint.

``scripts/read_netmon_version.py`` carries an identical copy for the release
tooling, which runs from a git snapshot without importing the app;
``tests/test_netmon_beta_release.py`` keeps both copies in lockstep.
"""

from __future__ import annotations

import re

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
