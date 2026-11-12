#!/usr/bin/env python3
"""Run a signed production bundle build from one committed snapshot.

Production bundle scripts used to read site files, assets, documentation,
their own release tooling and a separately built DEB with a JSON "receipt"
from the working tree. Anyone able to write ``dist/`` could place their own
DEB next to a matching hand-written receipt, and uncommitted content could be
signed as an official release. This launcher:

* pins the current HEAD commit,
* refuses to start while any signed input, package source or release tool
  differs from that commit (modified, staged, deleted or untracked),
* exports exactly that commit with ``git archive`` into a private directory,
* adds the few large git-ignored package assets only if their SHA-256 matches
  the committed pin list ``packaging/release-assets.sha256``,
* runs the bundle script from that snapshot. The bundle builds the
  documentation and the DEB itself inside the snapshot and signs only those;
  nothing from the workspace ``dist/`` directory is trusted, it only receives
  the outputs.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import shutil
import stat
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
    # Built inside the snapshot: documentation sources and the DEB builder.
    "scripts/build_docs_pdf.py",
    "docs/USER_GUIDE.md",
    "docs/SECURITY.md",
    "docs/ARCHITECTURE.md",
)
ASSET_MANIFEST = "packaging/release-assets.sha256"
ASSET_LINE = re.compile(r"([0-9a-f]{64})  ([A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)*)")
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _package_inputs():
    # Single source of truth for what build_netmon_deb.sh reads.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from netmon_release_deb_receipt import PACKAGE_INPUTS
    finally:
        sys.path.pop(0)
    return tuple(PACKAGE_INPUTS)


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
        *_package_inputs(),
    )
    if changes:
        paths = [e[3:].decode(errors="replace") for e in changes.split(b"\0") if e]
        raise ReleaseSourceError(
            "Produktions-Bundle nur aus committetem Stand: Release-Eingaben "
            "geaendert oder unversioniert (" + ", ".join(paths[:5]) + ")"
        )


def export_commit(commit, destination):
    """Extract every tracked file of exactly this commit, nothing else."""
    with tempfile.TemporaryFile(dir=destination.parent) as archive:
        _git("archive", "--format=tar", commit, stdout=archive)
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode="r:") as packed:
            packed.extractall(destination, filter="data")


def _open_workspace_file(relative):
    """Open ROOT/relative without following any link below ROOT."""
    parts = relative.split("/")
    descriptor = os.open(ROOT, DIRECTORY_FLAGS)
    try:
        for part in parts[:-1]:
            child = os.open(part, DIRECTORY_FLAGS, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return os.open(
            parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=descriptor
        )
    finally:
        os.close(descriptor)


def import_pinned_assets(snapshot):
    """Copy git-ignored package assets into the snapshot only if pinned."""
    manifest = snapshot / ASSET_MANIFEST
    if not manifest.is_file():
        return []
    imported = []
    for line in manifest.read_text(encoding="ascii").splitlines():
        if not line or line.startswith("#"):
            continue
        match = ASSET_LINE.fullmatch(line)
        if not match or any(p in {".", ".."} for p in match[2].split("/")):
            raise ReleaseSourceError(f"Ungueltige Zeile in {ASSET_MANIFEST}")
        expected, relative = match[1], match[2]
        target = snapshot / relative
        if os.path.lexists(target):
            raise ReleaseSourceError(f"Gepinnte Datei ist versioniert: {relative}")
        try:
            source = _open_workspace_file(relative)
        except OSError as exc:
            raise ReleaseSourceError(
                f"Gepinnte Release-Datei fehlt oder ist unsicher: {relative}"
            ) from exc
        digest = hashlib.sha256()
        with os.fdopen(source, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ReleaseSourceError(f"Keine regulaere Datei: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as output:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                    output.write(chunk)
        if digest.hexdigest() != expected:
            target.unlink()
            raise ReleaseSourceError(
                f"Gepinnte Release-Datei weicht vom committeten SHA-256 ab: {relative}"
            )
        imported.append(relative)
    return imported


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
        for relative in import_pinned_assets(snapshot):
            print(f"Gepinnte Release-Datei geprueft: {relative}", file=sys.stderr)
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
