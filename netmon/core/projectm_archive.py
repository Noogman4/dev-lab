"""Resource and path validation for untrusted projectM ZIP packs."""

import os
import stat
import struct
import tempfile
import zipfile
from contextlib import contextmanager
from urllib import request as urllib_request
from urllib.parse import urlparse

from netmon.core.archive_limits import ByteBudget, copy_limited, copy_response_limited

MAX_DOWNLOAD_BYTES = 256 * 1024 * 1024
MAX_MEMBERS = 50_000
MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200
MAX_DIRECTORY_BYTES = 16 * 1024 * 1024


@contextmanager
def download_preset_archive(url, *, timeout=30):
    """Both projectM URL entry points use the same budgets and private cleanup."""
    url = str(url or "").strip()
    if urlparse(url).scheme.lower() not in {"http", "https"}:
        raise ValueError("Preset downloads require HTTP or HTTPS.")
    with tempfile.TemporaryDirectory(prefix="netmon-projectm-pack-") as temp_dir:
        path = os.path.join(temp_dir, "pack.zip")
        with open(path, "xb") as destination:
            with urllib_request.urlopen(url, timeout=timeout) as response:
                copy_response_limited(
                    response, destination, MAX_DOWNLOAD_BYTES, require_complete=True
                )
        yield path


def check_zip_envelope(handle):
    """Bound central-directory parsing before ZipFile allocates its members.

    ZIP64 central directories / multi-disk archives are unnecessary within these
    limits and are rejected. ZIP64 local headers remain supported by ZipFile.
    """
    handle.seek(0, os.SEEK_END)
    size = handle.tell()
    if size > MAX_DOWNLOAD_BYTES:
        raise ValueError("ZIP exceeds compressed byte limit.")
    handle.seek(max(0, size - 65557))
    tail = handle.read(65557)
    # Match zipfile's no-comment fast path before its backwards signature search.
    if tail[-22:-18] == b"PK\x05\x06" and tail[-2:] == b"\x00\x00":
        offset = len(tail) - 22
    else:
        offset = tail.rfind(b"PK\x05\x06")
    if offset < 0 or len(tail) - offset < 22:
        raise ValueError("Invalid ZIP end record.")
    _, disk, cd_disk, disk_count, count, cd_size, cd_offset, comment = (
        struct.unpack_from("<4s4H2LH", tail, offset)
    )
    if (
        disk != 0
        or cd_disk != 0
        or disk_count != count
        or count == 65535
        or cd_size == 0xFFFFFFFF
        or cd_offset == 0xFFFFFFFF
        or len(tail) - offset != 22 + comment
        or cd_offset + cd_size != size - len(tail) + offset
    ):
        raise ValueError("Unsupported or inconsistent ZIP directory.")
    end_offset = size - len(tail) + offset
    # zipfile checks this exact location even WITHOUT ZIP64 sentinel fields.
    # A locator can be hidden in a regular central-directory file comment.
    # Reject the parser-switch position, not arbitrary signatures in payloads.
    if end_offset >= 20:
        handle.seek(end_offset - 20)
        if handle.read(4) == b"PK\x06\x07":
            raise ValueError("ZIP64 central directories are not supported.")
    # Reject competing complete end records, including ones embedded in an
    # archive comment. There must be one unambiguous directory/end boundary.
    candidate = tail.find(b"PK\x05\x06")
    while candidate >= 0:
        if candidate != offset and candidate + 22 <= len(tail):
            fields = struct.unpack_from("<4s4H2LH", tail, candidate)
            if (
                candidate + 22 + fields[-1] == len(tail)
                and fields[1] == fields[2] == 0
                and fields[3] == fields[4]
                and fields[5] + fields[6] == size - len(tail) + candidate
            ):
                raise ValueError("Ambiguous ZIP end records.")
        candidate = tail.find(b"PK\x05\x06", candidate + 1)
    if count > MAX_MEMBERS or cd_size > MAX_DIRECTORY_BYTES:
        raise ValueError("ZIP has too many members or excessive directory metadata.")
    # The EOCD count can lie. Count real directory records without allocating
    # ZipInfo objects or trusting that claimed count to bound parser memory.
    handle.seek(cd_offset)
    remaining = cd_size
    actual_count = 0
    while remaining:
        header = handle.read(min(46, remaining))
        if len(header) != 46 or header[:4] != b"PK\x01\x02":
            raise ValueError("Invalid ZIP central directory record.")
        name_size, extra_size, comment_size = struct.unpack_from("<3H", header, 28)
        record_size = 46 + name_size + extra_size + comment_size
        if record_size > remaining:
            raise ValueError("Truncated ZIP central directory record.")
        compressed, uncompressed = struct.unpack_from("<2L", header, 20)
        disk_start = struct.unpack_from("<H", header, 34)[0]
        local_offset = struct.unpack_from("<L", header, 42)[0]
        if (
            disk_start != 0
            or compressed == 0xFFFFFFFF
            or uncompressed == 0xFFFFFFFF
            or local_offset >= cd_offset
        ):
            raise ValueError("Unsupported ZIP64 or inconsistent ZIP member location.")
        handle.seek(name_size, os.SEEK_CUR)
        extra = handle.read(extra_size)
        extra_offset = 0
        while extra_offset < len(extra):
            if len(extra) - extra_offset < 4:
                raise ValueError("Truncated ZIP extra field.")
            kind, field_size = struct.unpack_from("<2H", extra, extra_offset)
            extra_offset += 4 + field_size
            if extra_offset > len(extra):
                raise ValueError("Truncated ZIP extra field.")
            if kind == 1:
                raise ValueError(
                    "ZIP64 central-directory extra fields are unsupported."
                )
        actual_count += 1
        if actual_count > MAX_MEMBERS:
            raise ValueError("ZIP has too many members.")
        handle.seek(comment_size, os.SEEK_CUR)
        remaining -= record_size
    if actual_count != count:
        raise ValueError("ZIP has an inconsistent member count.")
    handle.seek(0)
    return size, count


def validate_members(archive, archive_size, expected_count):
    members = archive.infolist()
    if len(members) > MAX_MEMBERS or len(members) != expected_count:
        raise ValueError("ZIP has too many members or inconsistent member count.")
    declared_budget = ByteBudget(MAX_TOTAL_BYTES)
    parsed = []
    for member in members:
        name = member.orig_filename.replace("\\", "/")
        parts = name.rstrip("/").split("/")
        if (
            not name
            or name.startswith("/")
            or "\x00" in name
            or ":" in name
            or len(name) > 1024
            or len(parts) > 32
            or any(part in {"", ".", ".."} for part in parts)
        ):
            raise ValueError("Unsafe ZIP member path.")
        file_type = stat.S_IFMT(member.external_attr >> 16)
        is_directory = member.is_dir()
        if (
            file_type not in {0, stat.S_IFREG, stat.S_IFDIR}
            or (file_type == stat.S_IFDIR and not is_directory)
            or (file_type == stat.S_IFREG and is_directory)
        ):
            raise ValueError("ZIP contains a link or special file.")
        if member.flag_bits & 1 or member.compress_type not in {
            zipfile.ZIP_STORED,
            zipfile.ZIP_DEFLATED,
        }:
            raise ValueError("Encrypted or unsupported ZIP member.")
        if (
            member.file_size < 0
            or member.compress_size < 0
            or member.file_size > MAX_FILE_BYTES
            or member.compress_size > archive_size
            or (is_directory and member.file_size != 0)
            or (member.file_size > 0 and member.compress_size == 0)
            or member.file_size > member.compress_size * MAX_COMPRESSION_RATIO
            or (
                member.compress_type == zipfile.ZIP_STORED
                and member.file_size != member.compress_size
            )
        ):
            raise ValueError("ZIP member exceeds size or compression ratio limits.")
        declared_budget.consume(member.file_size)
        # Account for every member, including directories and ignored extensions.
        if not is_directory:
            parsed.append((member, parts))
    return parsed


def copy_member(archive, member, destination, budget):
    with archive.open(member, "r") as source:
        return copy_limited(
            source,
            destination,
            min(
                MAX_FILE_BYTES,
                member.file_size,
                member.compress_size * MAX_COMPRESSION_RATIO,
            ),
            expected_size=member.file_size,
            budget=budget,
        )
