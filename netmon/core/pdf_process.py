"""Run the disposable PDF worker with bounded lifetime, input and output."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile

from .docx_process import _stop_worker
from .pdf_worker import (
    MAX_INPUT_BYTES,
    MAX_PAGES,
    MAX_REPLY_BYTES,
    MAX_TEXT_CHARS,
    MAX_WALL_SECONDS,
)


def _worker_command():
    return [sys.executable, "-I", "-B", str(Path(__file__).with_name("pdf_worker.py"))]


def parse_pdf_snapshot(payload: bytes) -> tuple[list[tuple[int, str]], bool]:
    """Extract page texts from an in-memory PDF snapshot in a limited child."""
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise ValueError("PDF size exceeds limit.")
    # Output goes to a private temporary file capped by the child's
    # RLIMIT_FSIZE, so the parent never buffers an unbounded pipe.
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            _worker_command(),
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        )
        try:
            try:
                process.communicate(payload, timeout=MAX_WALL_SECONDS)
            except subprocess.TimeoutExpired as exc:
                raise ValueError("PDF parser exceeded its time limit.") from exc
            if process.returncode != 0:
                raise ValueError("PDF parser failed or exceeded its resource limits.")
        finally:
            _stop_worker(process)
        output.seek(0)
        reply = output.read(MAX_REPLY_BYTES + 1)
    if len(reply) > MAX_REPLY_BYTES:
        raise ValueError("PDF parser reply exceeds limit.")
    try:
        result = json.loads(reply)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid PDF parser reply.") from exc
    if (
        not isinstance(result, dict)
        or set(result) != {"pages", "truncated"}
        or not isinstance(result["pages"], list)
        or len(result["pages"]) > MAX_PAGES
        or type(result["truncated"]) is not bool
    ):
        raise ValueError("Invalid PDF parser reply.")
    pages = []
    total = 0
    for entry in result["pages"]:
        if (
            not isinstance(entry, list)
            or len(entry) != 2
            or type(entry[0]) is not int
            or not 1 <= entry[0] <= MAX_PAGES
            or not isinstance(entry[1], str)
        ):
            raise ValueError("Invalid PDF parser reply.")
        total += len(entry[1])
        pages.append((entry[0], entry[1]))
    if total > MAX_TEXT_CHARS:
        raise ValueError("Invalid PDF parser reply.")
    return pages, result["truncated"]
