"""Bound the selected OOXML ZIP before handing an immutable snapshot to python-docx."""

from contextlib import contextmanager
import io
import os
import stat
import unicodedata
import zipfile

from netmon.core.archive_limits import ByteBudget, copy_limited
from netmon.core.projectm_archive import check_zip_envelope

MAX_ARCHIVE_BYTES = 5 * 1024 * 1024
MAX_MEMBERS = 1024
MAX_MEMBER_BYTES = 8 * 1024 * 1024
MAX_TOTAL_BYTES = 32 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


class _Discard:
    def write(self, data):
        return len(data)


def _members(archive, count, size):
    members = archive.infolist()
    if len(members) != count:
        raise ValueError("Inconsistent DOCX member count.")
    names = set()
    declared = ByteBudget(MAX_TOTAL_BYTES)
    for member in members:
        name = member.orig_filename
        normalized = name[:-1] if member.is_dir() else name
        parts = normalized.split("/")
        if (
            not name
            or len(name) > 512
            or len(parts) > 16
            or "\\" in name
            or ":" in name
            or any(unicodedata.category(char).startswith("C") for char in name)
            or any(part in {"", ".", ".."} for part in parts)
            or normalized in names
        ):
            raise ValueError("Unsafe or duplicate DOCX member path.")
        names.add(normalized)
        kind = stat.S_IFMT(member.external_attr >> 16)
        if (
            kind not in {0, stat.S_IFREG, stat.S_IFDIR}
            or (kind == stat.S_IFDIR and not member.is_dir())
            or (kind == stat.S_IFREG and member.is_dir())
            or member.flag_bits & (0x01 | 0x20 | 0x40 | 0x2000)
            or member.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
        ):
            raise ValueError("Unsupported DOCX member type or encryption.")
        if (
            not 0 <= member.file_size <= MAX_MEMBER_BYTES
            or not 0 <= member.compress_size <= size
            or (member.is_dir() and member.file_size != 0)
            or member.file_size > member.compress_size * MAX_COMPRESSION_RATIO
            or (
                member.compress_type == zipfile.ZIP_STORED
                and member.file_size != member.compress_size
            )
        ):
            raise ValueError("DOCX member exceeds decompression limits.")
        declared.consume(member.file_size)
    return members


@contextmanager
def open_validated_docx(path):
    """Never re-open the caller's pathname after checking the bounded snapshot.

    The shared envelope checker rejects forged counts and ZIP64/parser-switch
    records before ZipFile allocates members. DOCX's stricter count is checked
    before that allocation too. All entries, including ignored OOXML parts, are
    streamed to EOF to verify actual byte budgets and CRCs without extracting.
    """
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("DOCX must be a regular file of at most 5 MiB.")
        payload = source.read(MAX_ARCHIVE_BYTES + 1)
        after = os.fstat(source.fileno())
        if len(payload) > MAX_ARCHIVE_BYTES or (
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise ValueError("DOCX exceeds size limit or changed while reading.")
    with io.BytesIO(payload) as snapshot:
        size, count = check_zip_envelope(snapshot)
        if not 0 < count <= MAX_MEMBERS:
            raise ValueError("DOCX has too many or no members.")
        with zipfile.ZipFile(snapshot) as archive:
            members = _members(archive, count, size)
            budget = ByteBudget(MAX_TOTAL_BYTES)
            for member in members:
                with archive.open(member) as source:
                    copy_limited(
                        source,
                        _Discard(),
                        min(
                            MAX_MEMBER_BYTES,
                            member.file_size,
                            member.compress_size * MAX_COMPRESSION_RATIO,
                        ),
                        expected_size=member.file_size,
                        budget=budget,
                    )
        snapshot.seek(0)
        yield snapshot
