#!/usr/bin/env python3
"""Offline publication gate for NetMon's two production ZIP profiles."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import struct
import subprocess
import tempfile
import zipfile
from pathlib import Path

from read_netmon_version import ROOT, read_netmon_version

BUNDLE_NAMES = {
    "site": "netmonroots_public_html.zip",
    "update": "netmonroots_release_update.zip",
}
TEST_MARKER = b"UNSIGNED-TEST-ONLY"
MAX_ZIP_BYTES = 1024 * 1024 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_FILE_BYTES = 512 * 1024 * 1024
MAX_MEMBERS = 10_000
MAX_DIRECTORY_BYTES = 8 * 1024 * 1024
SMALL_FILE_BYTES = 256 * 1024
CHUNK_BYTES = 64 * 1024
RELEASE_MANIFEST = "verify/RELEASE-SHA256SUMS"
RELEASE_SIGNATURE = RELEASE_MANIFEST + ".minisig"
MANIFEST_FILES = {RELEASE_MANIFEST, RELEASE_SIGNATURE}


def check_envelope(handle):
    """Release ZIPs have no comments, prefixes, ZIP64 or multi-disk directory."""
    size = os.fstat(handle.fileno()).st_size
    if not 22 <= size <= MAX_ZIP_BYTES:
        raise ValueError("Invalid release ZIP size")
    handle.seek(0)
    if handle.read(4) != b"PK\x03\x04":
        raise ValueError("Release ZIP must not have a prefix")
    handle.seek(size - 22)
    fields = struct.unpack("<4s4H2LH", handle.read(22))
    signature, disk, directory_disk, disk_count, count, length, offset, comment = fields
    if (
        signature != b"PK\x05\x06"
        or disk
        or directory_disk
        or disk_count != count
        or comment
        or count == 65535
        or length == 0xFFFFFFFF
        or offset == 0xFFFFFFFF
        or offset + length != size - 22
        or count > MAX_MEMBERS
        or length > MAX_DIRECTORY_BYTES
    ):
        raise ValueError("Unsupported or excessive release ZIP directory")
    handle.seek(max(0, size - 42))
    if handle.read(4) == b"PK\x06\x07":
        raise ValueError("ZIP64 directory not supported")
    handle.seek(offset)
    remaining, actual = length, 0
    while remaining:
        header = handle.read(min(46, remaining))
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise ValueError("Invalid central directory")
        name, extra, note = struct.unpack_from("<3H", header, 28)
        record = 46 + name + extra + note
        compressed, uncompressed = struct.unpack_from("<2L", header, 20)
        if (
            record > remaining
            or struct.unpack_from("<H", header, 34)[0]
            or 0xFFFFFFFF in (compressed, uncompressed)
            or struct.unpack_from("<L", header, 42)[0] >= offset
        ):
            raise ValueError("Inconsistent release ZIP member")
        handle.seek(name, os.SEEK_CUR)
        extras = handle.read(extra)
        cursor = 0
        while cursor < len(extras):
            if cursor + 4 > len(extras):
                raise ValueError("Truncated ZIP extra field")
            kind, extra_length = struct.unpack_from("<2H", extras, cursor)
            cursor += 4 + extra_length
            if kind == 1 or cursor > len(extras):
                raise ValueError("Unsupported ZIP extra field")
        handle.seek(note, os.SEEK_CUR)
        remaining -= record
        actual += 1
        if actual > MAX_MEMBERS:
            raise ValueError("Too many release ZIP members")
    if actual != count:
        raise ValueError("Inconsistent release ZIP member count")
    handle.seek(0)
    return count


def expected_files(version, kind):
    payloads = {
        f"netmon_{version}_all.deb",
        f"docs/netmon_dokumentation_{version}.pdf",
        f"docs/netmon_dokumentation_{version}.html",
    }
    files = {
        "latest-version.json",
        "downloads.html",
        "docs.html",
        "download-config.php",
        "security-audit.html",
        "security-audit-r12.html",
        "security-audit-r10.html",
        "netmon_security_audit_2026.pdf",
        "netmon_security_audit_2026_r11.pdf",
        "netmon_security_audit_2026_r12.pdf",
        "en/downloads.html",
        "en/docs.html",
        "en/security-audit.html",
        "dist/SHA256SUMS",
        "dist/SHA256SUMS.minisig",
        "verify/netmonroots.minisign.pub",
        "verify/verify_netmon_signature.sh",
        "verify/verify_netmon_download.sh",
        *MANIFEST_FILES,
        *(f"dist/{name}" for name in payloads),
    }
    if kind == "site":
        files.update(
            {
                "index.html",
                "aktuelles.html",
                "changelog.html",
                "tour.html",
                "legal.html",
                "impressum.html",
                "styles.css",
                "theme-bright.css",
                "theme-dark.css",
                "app.js",
                "robots.txt",
                "sitemap.xml",
                "favicon.png",
                "bannericon.png",
                ".htaccess",
                "download.php",
                "download-lib.php",
                "download-stats.php",
                "data/.htaccess",
                "data/download-stats.json",
                "LICENSE.txt",
                "THIRD_PARTY_NOTICES.md",
                "en/index.html",
                "en/updates.html",
                "en/changelog.html",
                "en/tour.html",
                "en/legal.html",
                "en/impressum.html",
                "tools/netmon.png",
                "tools/netmon-radio.png",
                "docs/CHANGELOG.md",
                *(f"security-audit-r{number}.html" for number in range(2, 11)),
                *(
                    f"netmon_security_audit_2026_r{number}.pdf"
                    for number in range(2, 13)
                ),
                *(
                    f"screenshots/{name}.png"
                    for name in (
                        "netmon-status-header-tour",
                        "netmon-dns-selection-tour",
                        "netmon-security-firewall-tour",
                        "netmon-roots-baseline-guard-tour",
                        "netmon-linux-help-glossary-tour",
                        "netmon-download-scan-tour",
                        "netmon-radio-projectm-tour",
                        "netmon-system-monitor-insight",
                        "netmon-clamav-insight",
                        "netmon-logs-diagnostics-insight",
                        "netmon-theme-studio-insight",
                        "netmon-table-details-insight",
                        "netmon-guided-actions-insight",
                    )
                ),
            }
        )
    return files, payloads


def directory_hashes(directory, required):
    """Hash an exact upload tree; never accept links or special files."""
    directories = {""} | {
        "/".join(name.split("/")[:depth])
        for name in required
        for depth in range(1, len(name.split("/")))
    }
    hashes, total = {}, 0

    def visit(path, relative):
        nonlocal total
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            if relative not in directories:
                raise ValueError("Unexpected upload directory")
            for child in sorted(path.iterdir()):
                visit(child, f"{relative}/{child.name}".lstrip("/"))
        elif stat.S_ISREG(mode) and relative in required:
            descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as source:
                if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                    raise ValueError("Upload member must be a regular file")
                digest, actual = hashlib.sha256(), 0
                while chunk := source.read(CHUNK_BYTES):
                    actual += len(chunk)
                    total += len(chunk)
                    if actual > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                        raise ValueError("Upload content byte budget exceeded")
                    digest.update(chunk)
                hashes[relative] = digest.hexdigest()
        else:
            raise ValueError("Unexpected or unsafe upload member")

    visit(directory, "")
    if hashes.keys() != required:
        raise ValueError("Missing expected upload files")
    return hashes


def write_manifest(directory, kind):
    required, _ = expected_files(read_netmon_version(), kind)
    hashes = directory_hashes(directory, required - MANIFEST_FILES)
    message = "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes))
    if len(message.encode("ascii")) > SMALL_FILE_BYTES:
        raise ValueError("Release manifest byte budget exceeded")
    (directory / RELEASE_MANIFEST).write_text(message, encoding="ascii")


def check_sums(message, expected):
    sums = {}
    for line in message.decode("ascii").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or match[2] in sums:
            raise ValueError("Invalid or duplicate checksum entry")
        sums[match[2]] = match[1]
    if sums != expected:
        raise ValueError("Release checksums or member set mismatch")


def verify_bundle(path, kind, upload_directory=None):
    if path.name != BUNDLE_NAMES[kind]:
        raise ValueError("Not a production bundle filename")
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("Release ZIP must be a regular file")
        count = check_envelope(handle)
        version = read_netmon_version()
        required, payloads = expected_files(version, kind)
        directories = {""} | {
            "/".join(name.split("/")[:depth])
            for name in required
            for depth in range(1, len(name.split("/")))
        }
        contents, hashes, seen = {}, {}, set()
        total = 0
        with zipfile.ZipFile(handle) as archive:
            if len(archive.infolist()) != count:
                raise ValueError("ZIP parser directory mismatch")
            for member in archive.infolist():
                name = member.orig_filename
                parts = name.rstrip("/").split("/")
                if (
                    not name
                    or name != member.filename
                    or "\\" in name
                    or ":" in name
                    or len(name) > 1024
                    or len(parts) > 32
                    or parts[0] != "public_html"
                    or (len(parts) == 1 and not member.is_dir())
                    or any(part in {"", ".", ".."} for part in parts)
                    or TEST_MARKER.lower() in name.lower().encode("utf-8")
                    or TEST_MARKER in member.comment
                    or TEST_MARKER in member.extra
                ):
                    raise ValueError("Test identity or unsafe release path")
                key = name.rstrip("/").casefold()
                if key in seen:
                    raise ValueError("Duplicate release path")
                seen.add(key)
                mode = stat.S_IFMT(member.external_attr >> 16)
                if (
                    mode not in {0, stat.S_IFREG, stat.S_IFDIR}
                    or (mode == stat.S_IFDIR and not member.is_dir())
                    or (mode == stat.S_IFREG and member.is_dir())
                    or member.flag_bits & 1
                    or member.compress_type
                    not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or member.file_size > MAX_FILE_BYTES
                    or (member.is_dir() and member.file_size)
                ):
                    raise ValueError("Unsupported release member")
                relative = "/".join(parts[1:])
                if member.is_dir():
                    if relative not in directories:
                        raise ValueError("Unexpected release directory")
                    continue
                if relative not in required:
                    raise ValueError("Unexpected production file")
                digest, chunks, tail, actual = hashlib.sha256(), [], b"", 0
                small = relative in {
                    "dist/SHA256SUMS",
                    "dist/SHA256SUMS.minisig",
                    "verify/netmonroots.minisign.pub",
                    "latest-version.json",
                    *MANIFEST_FILES,
                }
                with archive.open(member) as source:
                    while chunk := source.read(CHUNK_BYTES):
                        actual += len(chunk)
                        total += len(chunk)
                        if (
                            actual > MAX_FILE_BYTES
                            or total > MAX_TOTAL_BYTES
                            or (small and actual > SMALL_FILE_BYTES)
                        ):
                            raise ValueError("Release content byte budget exceeded")
                        if TEST_MARKER in tail + chunk:
                            raise ValueError(
                                "Unsigned test marker inside production bundle"
                            )
                        tail = chunk[-(len(TEST_MARKER) - 1) :]
                        digest.update(chunk)
                        if small:
                            chunks.append(chunk)
                if actual != member.file_size:
                    raise ValueError("Release member size mismatch")
                hashes[relative] = digest.hexdigest()
                if small:
                    contents[relative] = b"".join(chunks)
        if not required <= hashes.keys():
            raise ValueError("Missing expected production files")
        for script in ("verify_netmon_signature.sh", "verify_netmon_download.sh"):
            trusted = hashlib.sha256(
                (ROOT / "scripts" / script).read_bytes()
            ).hexdigest()
            if hashes[f"verify/{script}"] != trusted:
                raise ValueError("Bundled verifier differs from the trusted checkout")
        if {name for name in hashes if name.startswith("dist/")} != {
            f"dist/{name}" for name in payloads
        } | {"dist/SHA256SUMS", "dist/SHA256SUMS.minisig"}:
            raise ValueError("Unexpected release payload identity")
        latest = json.loads(contents["latest-version.json"])
        if not isinstance(latest, dict) or latest.get("version") != version:
            raise ValueError("Release version mismatch")
        with tempfile.TemporaryDirectory(prefix="netmon-release-verify-") as temporary:
            target = Path(temporary)
            for relative, filename in [
                ("dist/SHA256SUMS", "SHA256SUMS"),
                ("dist/SHA256SUMS.minisig", "SHA256SUMS.minisig"),
                ("verify/netmonroots.minisign.pub", "key.pub"),
                (RELEASE_MANIFEST, "RELEASE-SHA256SUMS"),
                (RELEASE_SIGNATURE, "RELEASE-SHA256SUMS.minisig"),
            ]:
                (target / filename).write_bytes(contents[relative])
            for manifest in ("SHA256SUMS", "RELEASE-SHA256SUMS"):
                subprocess.run(
                    [
                        "bash",
                        str(ROOT / "scripts/verify_netmon_signature.sh"),
                        str(target / "key.pub"),
                        str(target / (manifest + ".minisig")),
                        str(target / manifest),
                    ],
                    check=True,
                    timeout=30,
                )
        check_sums(
            contents["dist/SHA256SUMS"],
            {name: hashes[f"dist/{name}"] for name in payloads},
        )
        # Only the manifest and its own signature are excluded (self-reference).
        # The pinned key authenticates the manifest; its exact set binds every
        # other deployable byte, including the original download signature.
        check_sums(
            contents[RELEASE_MANIFEST],
            {
                name: digest
                for name, digest in hashes.items()
                if name not in MANIFEST_FILES
            },
        )
        if (
            upload_directory is not None
            and directory_hashes(upload_directory, required) != hashes
        ):
            raise ValueError("Upload directory differs from authenticated ZIP")
        handle.seek(0)
        digest = hashlib.file_digest(handle, "sha256").hexdigest()
        after = os.fstat(handle.fileno())
        current = path.lstat()
        if (current.st_dev, current.st_ino) != (before.st_dev, before.st_ino):
            raise ValueError("Release ZIP path replaced during verification")
        if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise ValueError("Release ZIP changed during verification")
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--kind", choices=BUNDLE_NAMES, required=True)
    parser.add_argument(
        "--write-manifest",
        action="store_true",
        help="Generate the unsigned full-member manifest in the given staging directory",
    )
    parser.add_argument(
        "--upload-directory",
        type=Path,
        help="Also require this upload directory to match the authenticated ZIP",
    )
    args = parser.parse_args()
    try:
        if args.write_manifest:
            if args.upload_directory is not None:
                raise ValueError("Manifest creation cannot verify an upload directory")
            write_manifest(args.bundle, args.kind)
            return 0
        digest = verify_bundle(args.bundle, args.kind, args.upload_directory)
    except (
        OSError,
        ValueError,
        RuntimeError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as exc:
        parser.exit(1, f"Release rejected: {exc}\n")
    print(f"Production bundle verified (SHA-256): {digest}  {args.bundle.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
