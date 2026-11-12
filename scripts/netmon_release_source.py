#!/usr/bin/env python3
"""Run a signed production bundle build from one committed snapshot.

Production bundle scripts used to read site files, assets, documentation and
their own release tooling straight from the working tree, so a local edit or
an untracked file could be signed as an official release. This launcher:

* pins the current HEAD commit,
* refuses to start while any signed input or release tool differs from that
  commit (modified, staged, deleted or untracked),
* exports exactly that commit with ``git archive`` into a private directory,
* runs the bundle script from that snapshot. All web content and every tool
  then comes from the commit; only the receipt-bound DEB (and documentation
  that must match the copy inside that DEB) is taken from the workspace
  ``dist/`` directory, and outputs are written there.
"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
COMMIT = re.compile(r"^[0-9a-f]{40}$")
BUNDLE_SCRIPTS = (
    "build_netmon_site_bundle.sh",
    "build_netmon_release_update_bundle.sh",
)
# Everything a production bundle signs or executes, relative to the repo.
RELEASE_INPUTS = (
    "site",
    "tools/Favicon.png",
    "tools/bannericon.png",
    "tools/netmon.png",
    "tools/netmon-radio.png",
    "docs/CHANGELOG.md",
    "docs/security/netmonroots.minisign.pub",
    "netmon/config/constants.py",
    # Read by check_release_consistency.py for version consistency.
    "README.md",
    "SECURITY.md",
    "docs/README.md",
    "docs/CONFIGURATION.md",
    "docs/DEB_PACKAGING_PLAN.md",
    "scripts/build_netmon_site_bundle.sh",
    "scripts/build_netmon_release_update_bundle.sh",
    "scripts/netmon_release_common.sh",
    "scripts/netmon_release_source.py",
    "scripts/netmon_release_deb_receipt.py",
    "scripts/copy_netmon_release_input.py",
    "scripts/verify_netmon_release_bundle.py",
    "scripts/check_release_consistency.py",
    "scripts/read_netmon_version.py",
    "scripts/verify_netmon_signature.sh",
    "scripts/verify_netmon_download.sh",
)


class ReleaseSourceError(Exception):
    pass


def _git(*args, stdout=subprocess.PIPE):
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        stdout=stdout,
        stderr=subprocess.PIPE,
        env=env,
        check=False,
        timeout=300,
    )
    if result.returncode != 0:
        raise ReleaseSourceError("git query failed: " + " ".join(args[:2]))
    return result.stdout


def head_commit():
    commit = _git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    if not COMMIT.fullmatch(commit):
        raise ReleaseSourceError("Unexpected HEAD commit format")
    return commit


def require_clean_inputs():
    changes = _git(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=no",
        "--",
        *RELEASE_INPUTS,
    )
    if changes:
        paths = [e[3:].decode(errors="replace") for e in changes.split(b"\0") if e]
        raise ReleaseSourceError(
            "Produktions-Bundle nur aus committetem Stand: Release-Eingaben "
            "geaendert oder unversioniert (" + ", ".join(paths[:5]) + ")"
        )


def export_commit(commit, destination):
    """Extract the release inputs of exactly this commit, nothing else."""
    listed = _git("ls-tree", "-r", "-z", "--name-only", commit, "--", *RELEASE_INPUTS)
    files = [name.decode() for name in listed.split(b"\0") if name]
    if not files:
        raise ReleaseSourceError("Commit enthaelt keine Release-Eingaben")
    with tempfile.TemporaryFile(dir=destination.parent) as archive:
        _git("archive", "--format=tar", commit, "--", *files, stdout=archive)
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode="r:") as packed:
            packed.extractall(destination, filter="data")


def run(script, arguments):
    if script not in BUNDLE_SCRIPTS:
        raise ReleaseSourceError(f"Unbekanntes Bundle-Skript: {script}")
    commit = head_commit()
    require_clean_inputs()
    work = Path(tempfile.mkdtemp(prefix="netmon-release-source-"))
    try:
        snapshot = work / "source"
        snapshot.mkdir(mode=0o700)
        # Archive the pinned commit id, not "HEAD": a later checkout or
        # workspace edit cannot change what this build reads or runs.
        export_commit(commit, snapshot)
        env = {
            **os.environ,
            "NETMON_RELEASE_SOURCE_DIR": str(snapshot),
            "NETMON_RELEASE_WORKSPACE": str(ROOT),
            "NETMON_RELEASE_COMMIT": commit,
        }
        print(f"Release-Quelle: Commit {commit}", file=sys.stderr)
        return subprocess.run(
            ["bash", str(snapshot / "scripts" / script), *arguments],
            env=env,
            check=False,
        ).returncode
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 2 or argv[0] != "run":
        print(
            "Aufruf: netmon_release_source.py run <bundle-skript> [args]",
            file=sys.stderr,
        )
        return 2
    try:
        return run(argv[1], argv[2:])
    except (ReleaseSourceError, OSError, tarfile.TarError) as exc:
        print(f"Release-Abbruch: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
