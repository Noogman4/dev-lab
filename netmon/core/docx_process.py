"""Bound DOCX parser lifetime and output without preexec_fn in a GUI thread."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

from .docx_worker import (
    MAX_INPUT_BYTES,
    MAX_REPLY_BYTES,
    MAX_TEXT_CHARS,
    MAX_WALL_SECONDS,
)


def _worker_command():
    return [sys.executable, "-I", "-B", str(Path(__file__).with_name("docx_worker.py"))]


def _stop_worker(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    process.wait()


def parse_docx_snapshot(payload: bytes) -> tuple[str, bool]:
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise ValueError("DOCX compressed size exceeds limit.")
    # A descriptor-owned temporary output plus RLIMIT_FSIZE prevents unbounded
    # pipe buffering in the parent. No child stderr/document data is captured.
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
                raise ValueError("DOCX parser exceeded its time limit.") from exc
            if process.returncode != 0:
                raise ValueError("DOCX parser failed or exceeded its resource limits.")
        finally:
            _stop_worker(process)
        output.seek(0)
        reply = output.read(MAX_REPLY_BYTES + 1)
    if len(reply) > MAX_REPLY_BYTES:
        raise ValueError("DOCX parser reply exceeds limit.")
    try:
        result = json.loads(reply)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid DOCX parser reply.") from exc
    if (
        not isinstance(result, dict)
        or set(result) != {"text", "truncated"}
        or not isinstance(result["text"], str)
        or len(result["text"]) > MAX_TEXT_CHARS
        or type(result["truncated"]) is not bool
    ):
        raise ValueError("Invalid DOCX parser reply.")
    return result["text"], result["truncated"]
