#!/usr/bin/env python3
"""Bind an official NetMon DEB to the clean commit it was built from.

Only ``build_netmon_deb.sh --release`` writes a receipt. Signed production
bundles accept a DEB only with a receipt for the current HEAD whose hash and
package identity match. Local or ``--test-version`` builds never get one, so
they cannot be signed as an official release, even under the official name.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tarfile
from pathlib import Path

from read_netmon_version import ROOT

SCHEMA = "netmon-release-deb/1"
PACKAGE = "netmon"
TEST_BUILD_DOC = "./usr/share/doc/netmon/TEST-BUILD.md"
RECEIPT_SUFFIX = ".release.json"
MAX_RECEIPT_BYTES = 4096
RECEIPT_KEYS = {"schema", "kind", "package", "version", "filename", "sha256", "commit"}
RELEASE_VERSION = re.compile(r"^[0-9]+(\.[0-9]+)+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
# Every repository path build_netmon_deb.sh reads tracked content from.
PACKAGE_INPUTS = (
    "netmon",
    "netmon_radio_app.py",
    "packaging",
    "scripts/build_netmon_deb.sh",
    "scripts/netmon_uninstall_menu.sh",
    "scripts/read_netmon_version.py",
    "tools/__init__.py",
    "tools/netmon.png",
    "tools/netmon-radio.png",
    "tools/it_lexikon_linux_hilfe.json",
    "tools/netmon_roots_banner.png",
    "tools/netmon_roots_splash.png",
    "tools/netmon_roots_startup.png",
    "tools/netmon-linux-befehlsdatenbank-v1.csv",
    "tools/secure_browser_manager",
    "tools/Log-Pics",
    "README-DNS-INTEGRATION.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/DNS-F1-F6-REPORT.md",
)


class ReceiptError(Exception):
    pass


def _git(*args):
    # No optional index refresh: verification must not write repository state.
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"}
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        capture_output=True,
        env=env,
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise ReceiptError("git query failed: " + " ".join(args[:2]))
    return result.stdout


def head_commit():
    commit = _git("rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    if not COMMIT.fullmatch(commit):
        raise ReceiptError("Unexpected HEAD commit format")
    return commit


def require_clean_inputs():
    changes = _git(
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        *PACKAGE_INPUTS,
    )
    if changes:
        paths = [entry[3:].decode(errors="replace") for entry in changes.split(b"\0")]
        listed = ", ".join(path for path in paths[:5] if path)
        raise ReceiptError(
            "Release-DEB nur aus committetem Stand: Paketquellen geaendert "
            f"oder unversioniert ({listed})"
        )


def _deb_identity(deb):
    fields = subprocess.run(
        ["dpkg-deb", "-f", str(deb), "Package", "Version"],
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )
    contents = subprocess.run(
        ["dpkg-deb", "-c", str(deb)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if fields.returncode != 0 or contents.returncode != 0:
        raise ReceiptError("DEB control data unreadable")
    values = {}
    for line in fields.stdout.splitlines():
        key, _, value = line.partition(":")
        values[key.strip()] = value.strip()
    test_doc = any(
        line.split()[-1] == TEST_BUILD_DOC
        for line in contents.stdout.splitlines()
        if line.split()
    )
    return values.get("Package"), values.get("Version"), test_doc


def _sha256(deb):
    descriptor = os.open(deb, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ReceiptError("DEB must be a regular file")
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _require_release_identity(deb, version):
    if not RELEASE_VERSION.fullmatch(version):
        raise ReceiptError(f"Keine offizielle Release-Version: {version!r}")
    if deb.name != f"{PACKAGE}_{version}_all.deb":
        raise ReceiptError("Unexpected release DEB filename")
    package, deb_version, test_doc = _deb_identity(deb)
    if package != PACKAGE or deb_version != version:
        raise ReceiptError(
            f"DEB-Identitaet {package!r} {deb_version!r} ist kein Release {version}"
        )
    if test_doc:
        raise ReceiptError("DEB enthaelt eine Testbuild-Kennzeichnung")


def write_receipt(deb, version, commit):
    deb = Path(deb)
    if head_commit() != commit:
        raise ReceiptError("HEAD changed during the release DEB build")
    require_clean_inputs()
    _require_release_identity(deb, version)
    receipt = {
        "schema": SCHEMA,
        "kind": "release",
        "package": PACKAGE,
        "version": version,
        "filename": deb.name,
        "sha256": _sha256(deb),
        "commit": commit,
    }
    path = deb.with_name(deb.name + RECEIPT_SUFFIX)
    descriptor = os.open(
        path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644
    )
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path


def _read_receipt(path):
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ReceiptError(
            f"Kein Release-Beleg {path.name}: DEB stammt nicht aus "
            "build_netmon_deb.sh --release"
        ) from exc
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ReceiptError("Release receipt must be a regular file")
        data = handle.read(MAX_RECEIPT_BYTES + 1)
    if len(data) > MAX_RECEIPT_BYTES:
        raise ReceiptError("Release receipt too large")
    try:
        receipt = json.loads(data)
    except ValueError as exc:
        raise ReceiptError("Release receipt is not valid JSON") from exc
    if not isinstance(receipt, dict) or set(receipt) != RECEIPT_KEYS:
        raise ReceiptError("Release receipt has unexpected fields")
    return receipt


def verify_receipt(source_deb, staged_deb, version, commit=None):
    """Check the staged copy that is signed against the source DEB's receipt.

    ``commit`` is the snapshot commit a production bundle is built from; it
    replaces the HEAD lookup, which a git-less snapshot cannot perform.
    """
    source_deb, staged_deb = Path(source_deb), Path(staged_deb)
    receipt = _read_receipt(source_deb.with_name(source_deb.name + RECEIPT_SUFFIX))
    expected = {
        "schema": SCHEMA,
        "kind": "release",
        "package": PACKAGE,
        "version": version,
        "filename": source_deb.name,
    }
    for key, value in expected.items():
        if receipt[key] != value:
            raise ReceiptError(f"Release receipt mismatch: {key}")
    if not COMMIT.fullmatch(str(receipt["commit"])):
        raise ReceiptError("Release receipt commit malformed")
    if commit is not None and not COMMIT.fullmatch(commit):
        raise ReceiptError("Expected release commit malformed")
    if receipt["commit"] != (commit if commit is not None else head_commit()):
        raise ReceiptError(
            "Release-DEB wurde nicht aus dem aktuellen Commit gebaut "
            f"(Beleg {receipt['commit'][:12]})"
        )
    if staged_deb.name != source_deb.name:
        raise ReceiptError("Staged DEB name differs from source")
    if _sha256(staged_deb) != receipt["sha256"]:
        raise ReceiptError("DEB-Hash stimmt nicht mit dem Release-Beleg ueberein")
    _require_release_identity(staged_deb, version)
    return receipt


def verify_docs(staged_deb, deb_sha256, documents):
    """Generated docs must equal the copies shipped in the approved DEB."""
    staged_deb = Path(staged_deb)
    if _sha256(staged_deb) != deb_sha256:
        raise ReceiptError("DEB differs from receipt-approved SHA-256")
    wanted = {}
    for document in map(Path, documents):
        wanted[f"./usr/share/doc/{PACKAGE}/{document.name}"] = _sha256(document)
    found = {}
    tar = subprocess.Popen(
        ["dpkg-deb", "--fsys-tarfile", str(staged_deb)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    try:
        with tarfile.open(fileobj=tar.stdout, mode="r|") as members:
            for member in members:
                name = (
                    member.name if member.name.startswith("./") else "./" + member.name
                )
                if name not in wanted:
                    continue
                if not member.isfile() or name in found:
                    raise ReceiptError(f"Mehrdeutige Doku im DEB: {name}")
                digest = hashlib.sha256()
                handle = members.extractfile(member)
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
                found[name] = digest.hexdigest()
    finally:
        tar.stdout.close()
        if tar.wait(timeout=300) != 0:
            raise ReceiptError("DEB-Inhalt nicht lesbar")
    for name, digest in wanted.items():
        if found.get(name) != digest:
            raise ReceiptError(
                f"Dokumentation {Path(name).name} stimmt nicht mit der Kopie im "
                "belegten Release-DEB ueberein"
            )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("preflight")
    write = commands.add_parser("write")
    write.add_argument("deb")
    write.add_argument("--version", required=True)
    write.add_argument("--commit", required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("source_deb")
    verify.add_argument("staged_deb")
    verify.add_argument("--version", required=True)
    verify.add_argument("--sha256-only", action="store_true")
    verify.add_argument("--commit")
    identity = commands.add_parser("identity")
    identity.add_argument("deb")
    identity.add_argument("--version", required=True)
    docs = commands.add_parser("docs")
    docs.add_argument("staged_deb")
    docs.add_argument("documents", nargs="+")
    docs.add_argument("--sha256", required=True)
    options = parser.parse_args(argv)
    try:
        if options.command == "preflight":
            require_clean_inputs()
            print(head_commit())
        elif options.command == "write":
            print(
                f"Release-Beleg: {write_receipt(options.deb, options.version, options.commit)}"
            )
        elif options.command == "identity":
            deb = Path(options.deb)
            _require_release_identity(deb, options.version)
            print(_sha256(deb))
        elif options.command == "docs":
            verify_docs(options.staged_deb, options.sha256, options.documents)
            print("Dokumentation an Release-DEB gebunden")
        else:
            receipt = verify_receipt(
                options.source_deb,
                options.staged_deb,
                options.version,
                options.commit,
            )
            if options.sha256_only:
                print(receipt["sha256"])
            else:
                print(f"Release-DEB belegt: Commit {receipt['commit']}")
    except ReceiptError as exc:
        print(f"Release-Abbruch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
