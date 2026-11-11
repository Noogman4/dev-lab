"""Offline ZIP worker and bounded raw-file protocol for preset installation."""

from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
import struct

PRESET_EXTENSIONS = {".milk", ".prjm"}
ASSET_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".tga",
    ".gif",
    ".dds",
    ".ppm",
    ".pgm",
}
MAGIC = b"NMPZ1\0"
END = b"NMPZ-END\0"
MAX_MANIFEST_BYTES = 32 * 1024 * 1024
MAX_ROW_BYTES = 8192
MAX_WIRE_BYTES = 1024 * 1024 * 1024 + MAX_MANIFEST_BYTES + len(END)


@dataclass(frozen=True)
class Member:
    index: int
    file_size: int
    compress_size: int
    compress_type: int


def _exact(handle, size):
    value = handle.read(size)
    if len(value) != size:
        raise ValueError("Truncated preset worker reply.")
    return value


def read_members(handle, archive_size):
    """Validate only small JSON records and raw bytes; never open ZIP here."""
    from netmon.core import projectm_archive as limits
    from netmon.core.archive_limits import ByteBudget
    from netmon.core.projectm_import_plan import ImportPlan

    if not 0 <= archive_size <= limits.MAX_DOWNLOAD_BYTES:
        raise ValueError("Preset archive exceeds compressed limit.")
    if _exact(handle, len(MAGIC)) != MAGIC:
        raise ValueError("Unknown preset worker protocol.")
    count = struct.unpack(">I", _exact(handle, 4))[0]
    if count > limits.MAX_MEMBERS:
        raise ValueError("Preset reply has too many members.")
    used = len(MAGIC) + 4
    declared = ByteBudget(limits.MAX_TOTAL_BYTES)
    rows = []
    for index in range(count):
        size = struct.unpack(">I", _exact(handle, 4))[0]
        used += 4 + size
        if not 0 < size <= MAX_ROW_BYTES or used > MAX_MANIFEST_BYTES:
            raise ValueError("Excessive preset worker metadata.")
        row = json.loads(_exact(handle, size))
        if not isinstance(row, dict) or set(row) != {
            "parts",
            "size",
            "compressed",
            "method",
        }:
            raise ValueError("Invalid preset worker member.")
        parts = row["parts"]
        if (
            not isinstance(parts, list)
            or not 1 <= len(parts) <= 32
            or any(
                not isinstance(part, str)
                or not part
                or part in {".", ".."}
                or any(c in part for c in "/\\:\0")
                or any(0xD800 <= ord(c) <= 0xDFFF for c in part)
                for part in parts
            )
            or len("/".join(parts)) > 1024
        ):
            raise ValueError("Unsafe preset worker path.")
        length, compressed, method = row["size"], row["compressed"], row["method"]
        if (
            any(type(value) is not int for value in (length, compressed, method))
            or not 0 <= length <= limits.MAX_FILE_BYTES
            or not 0 <= compressed <= archive_size
            or method not in {0, 8}
            or (length and not compressed)
            or length > compressed * limits.MAX_COMPRESSION_RATIO
            or (method == 0 and length != compressed)
        ):
            raise ValueError("Invalid preset worker size or method.")
        declared.consume(length)
        rows.append((Member(index, length, compressed, method), parts))
    if not any(
        os.path.splitext(parts[-1])[1].lower() in PRESET_EXTENSIONS for _, parts in rows
    ):
        raise ValueError("ZIP contains no presets.")
    # Recompute all naming and object budgets; child claims have no path authority.
    plan = ImportPlan(rows, PRESET_EXTENSIONS, PRESET_EXTENSIONS | ASSET_EXTENSIONS)
    offsets = {}
    offset = handle.tell()
    for item in plan.files:
        offsets[item.member.index] = offset
        offset += item.member.file_size
    if os.fstat(handle.fileno()).st_size != offset + len(END):
        raise ValueError("Preset payload size disagrees with manifest.")
    handle.seek(offset)
    if _exact(handle, len(END)) != END:
        raise ValueError("Incomplete preset worker reply.")
    return rows, offsets


class PreparedArchive:
    def __init__(self, handle, archive_size):
        self.handle = handle
        self.members, self.offsets = read_members(handle, archive_size)

    def copy_member(self, member, destination, budget):
        from netmon.core.archive_limits import copy_limited
        from netmon.core import projectm_archive as limits

        self.handle.seek(self.offsets[member.index])
        remaining = member.file_size
        handle = self.handle

        class Payload:
            def read(self, size):
                nonlocal remaining
                data = handle.read(min(size, remaining))
                remaining -= len(data)
                return data

        return copy_limited(
            Payload(),
            destination,
            min(limits.MAX_FILE_BYTES, member.file_size),
            expected_size=member.file_size,
            budget=budget,
        )


@contextmanager
def prepared_archive(path):
    from netmon.core import radio_sandbox

    with radio_sandbox.prepared_preset_bundle(path) as (handle, archive_size):
        yield PreparedArchive(handle, archive_size)


def encode_archive(path, destination):
    """All ZIP parsing, CRC verification and inflation stay inside this worker."""
    import zipfile
    from netmon.core import projectm_archive as limits
    from netmon.core.archive_limits import ByteBudget
    from netmon.core.projectm_import_plan import ImportPlan

    with open(path, "rb") as handle:
        size, count = limits.check_zip_envelope(handle)
        with zipfile.ZipFile(handle, "r") as archive:
            rows = limits.validate_members(archive, size, count)
            if not any(
                os.path.splitext(parts[-1])[1].lower() in PRESET_EXTENSIONS
                for _, parts in rows
            ):
                raise ValueError("ZIP contains no presets.")
            plan = ImportPlan(
                rows, PRESET_EXTENSIONS, PRESET_EXTENSIONS | ASSET_EXTENSIONS
            )
            # Finish the complete bounded metadata before sending any payload.
            metadata = bytearray(MAGIC + struct.pack(">I", len(rows)))
            for member, parts in rows:
                row = json.dumps(
                    {
                        "parts": parts,
                        "size": member.file_size,
                        "compressed": member.compress_size,
                        "method": member.compress_type,
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                ).encode("utf-8")
                if (
                    len(row) > MAX_ROW_BYTES
                    or len(metadata) + 4 + len(row) > MAX_MANIFEST_BYTES
                ):
                    raise ValueError("Excessive preset worker metadata.")
                metadata.extend(struct.pack(">I", len(row)))
                metadata.extend(row)
            destination.write(metadata)
            budget = ByteBudget(limits.MAX_TOTAL_BYTES)
            for item in plan.files:
                limits.copy_member(archive, item.member, destination, budget)
            destination.write(END)
            destination.flush()


def apply_process_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, 512 * 1024 * 1024),
        (resource.RLIMIT_CPU, 30),
        (resource.RLIMIT_NPROC, 0),
        (resource.RLIMIT_FSIZE, MAX_WIRE_BYTES),
    ):
        soft, hard = resource.getrlimit(name)
        limit = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (limit, limit))


def main():
    import sys

    try:
        apply_process_limits()
        sys.path.insert(0, "/run")
        if sys.argv[1:]:
            raise ValueError("Invalid ZIP worker arguments.")
        encode_archive("/media/archive.zip", sys.stdout.buffer)
        return 0
    except Exception:
        print("Protected preset archive failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
