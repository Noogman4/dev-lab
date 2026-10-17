"""Bounded stream copying shared by external archive importers."""

from dataclasses import dataclass

COPY_CHUNK_BYTES = 64 * 1024


@dataclass
class ByteBudget:
    limit: int
    used: int = 0

    def consume(self, size):
        if size < 0 or size > self.limit - self.used:
            raise ValueError("Archive exceeds total uncompressed byte limit.")
        self.used += size


def copy_limited(
    source,
    destination,
    max_bytes,
    *,
    expected_size=None,
    budget=None,
    limit_error="Archive exceeds file byte limit.",
):
    """Count real bytes before writing; handle short writes and exact sizes."""
    copied = 0
    while True:
        chunk = source.read(min(COPY_CHUNK_BYTES, max_bytes - copied + 1))
        if not chunk:
            break
        copied += len(chunk)
        if copied > max_bytes:
            raise ValueError(limit_error)
        if budget is not None:
            budget.consume(len(chunk))
        remaining = memoryview(chunk)
        while remaining:
            written = destination.write(remaining)
            if written is None or written <= 0 or written > len(remaining):
                raise OSError("Incomplete archive write.")
            remaining = remaining[written:]
    if expected_size is not None and copied != expected_size:
        raise ValueError("Archive member size does not match its metadata.")
    return copied


def copy_response_limited(
    response, destination, max_bytes, *, limit_error=None, require_complete=False
):
    """Content-Length is an early check, never the streaming limit's source."""
    limit_error = limit_error or "Archive download exceeds compressed byte limit."
    content_length = response.headers.get("Content-Length")
    declared_size = None
    if content_length is not None:
        try:
            declared_size = int(content_length)
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid archive Content-Length.") from exc
        if declared_size < 0 or declared_size > max_bytes:
            raise ValueError(limit_error)
    copied = copy_limited(response, destination, max_bytes, limit_error=limit_error)
    if require_complete and declared_size is not None and copied < declared_size:
        raise ValueError("Incomplete archive download.")
    return copied
