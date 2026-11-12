"""Disposable PDF text extractor. Limits are applied before importing PyPDF2.

A small crafted PDF can expand to gigabytes (FlateDecode bombs), nest objects
deeply or carry enormous content streams. Parsing therefore never happens in
the NetMon desktop process: this worker runs with hard memory, CPU, file and
process limits, stops at a fixed page and character budget, and returns only
bounded JSON on stdout.
"""

import io
import json
import sys

MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_PAGES = 30
MAX_TEXT_CHARS = 120_000
MAX_REPLY_BYTES = 2 * 1024 * 1024
MAX_MEMORY_BYTES = 512 * 1024 * 1024
MAX_CPU_SECONDS = 8
MAX_WALL_SECONDS = 15


def apply_process_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, MAX_MEMORY_BYTES),
        (resource.RLIMIT_CPU, MAX_CPU_SECONDS),
        (resource.RLIMIT_NOFILE, 32),
        (resource.RLIMIT_NPROC, 0),
        (resource.RLIMIT_FSIZE, MAX_REPLY_BYTES),
        (resource.RLIMIT_CORE, 0),
    ):
        soft, hard = resource.getrlimit(name)
        bound = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (bound, bound))


def extract_pages(payload):
    """Return ([[page number, text], ...], truncated) within the text budget."""
    if not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise ValueError("PDF size exceeds limit.")
    import PyPDF2

    reader = PyPDF2.PdfReader(io.BytesIO(payload), strict=False)
    total = len(reader.pages)
    pages = []
    remaining = MAX_TEXT_CHARS
    truncated = total > MAX_PAGES
    for index in range(min(total, MAX_PAGES)):
        text = (reader.pages[index].extract_text() or "").strip()
        if not text:
            continue
        if len(text) > remaining:
            pages.append([index + 1, text[:remaining]])
            return pages, True
        pages.append([index + 1, text])
        remaining -= len(text)
        if remaining == 0:
            return pages, index + 1 < total
    return pages, truncated


def main():
    try:
        apply_process_limits()
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        pages, truncated = extract_pages(payload)
        reply = json.dumps(
            {"pages": pages, "truncated": truncated}, ensure_ascii=True
        ).encode("ascii")
        if len(reply) > MAX_REPLY_BYTES:
            raise ValueError("PDF parser reply exceeds limit.")
        sys.stdout.buffer.write(reply)
        return 0
    except BaseException:
        # Errors are intentionally silent and contain no document text.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
