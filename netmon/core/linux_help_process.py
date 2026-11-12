"""Parse immutable command database snapshots with bounded worker resources."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile

from .docx_archive import open_validated_xlsx
from .import_limits import ImportLimitError, read_bounded_bytes
from .linux_help_worker import MAX_INPUT_BYTES, MAX_REPLY_BYTES, MAX_WALL_SECONDS


def _worker_command(kind, limits):
    return [
        sys.executable,
        "-I",
        "-B",
        str(Path(__file__).with_name("linux_help_worker.py")),
        kind,
        json.dumps(limits),
    ]


def _stop(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=1)


def parse_commands(path, *, limits):
    kind = ".xlsx" if Path(path).suffix.lower() == ".xlsx" else ".csv"
    if kind == ".xlsx":
        with open_validated_xlsx(path) as snapshot:
            payload = snapshot.read(MAX_INPUT_BYTES + 1)
    else:
        payload = read_bounded_bytes(
            path, limits["MAX_SOURCE_CSV_BYTES"], label="CSV-Import"
        )
    if not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise ImportLimitError("Import: Eingabegroessenlimit ueberschritten.")
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            _worker_command(kind, limits),
            stdin=subprocess.PIPE,
            stdout=output,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env={
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "OPENBLAS_NUM_THREADS": "1",
                "OMP_NUM_THREADS": "1",
            },
        )
        try:
            try:
                process.communicate(payload, timeout=MAX_WALL_SECONDS)
            except subprocess.TimeoutExpired as exc:
                raise ImportLimitError(
                    "Import: Parser-Zeitlimit ueberschritten."
                ) from exc
            if process.returncode:
                raise ImportLimitError("Import: Parserfehler oder Ressourcenlimit.")
        finally:
            _stop(process)
        output.seek(0)
        reply = output.read(MAX_REPLY_BYTES + 1)
    if len(reply) > MAX_REPLY_BYTES:
        raise ImportLimitError("Import: Parser-Ausgabegrenze ueberschritten.")
    try:
        result = json.loads(reply)
        if not isinstance(result, dict):
            raise ValueError
        if set(result) == {"error"}:
            if not isinstance(result["error"], str) or len(result["error"]) > 500:
                raise ValueError
            raise ImportLimitError(
                "Import: Datei abgelehnt. " + str(result["error"])[:250]
            )
        commands = result["commands"]
        if (
            set(result) != {"commands"}
            or not isinstance(commands, list)
            or len(commands) > limits["MAX_SOURCE_ROWS"]
        ):
            raise ValueError
        total = 0
        seen_ids = set()
        fields = {
            "id",
            "entry_type",
            "category",
            "name",
            "info",
            "cmd",
            "syntax",
            "example",
            "explanation",
            "warning_text",
            "tags",
            "risk",
            "root_required",
            "enabled",
        }
        for command in commands:
            if not isinstance(command, dict) or set(command) != fields:
                raise ValueError
            if command["entry_type"] != "command" or command["risk"] not in {
                "safe",
                "caution",
                "danger",
            }:
                raise ValueError
            if not isinstance(command["id"], str) or command["id"] in seen_ids:
                raise ValueError
            seen_ids.add(command["id"])
            for key, value in command.items():
                if (
                    not isinstance(key, str)
                    or len(key) > 100
                    or type(value)
                    is not (bool if key in {"enabled", "root_required"} else str)
                ):
                    raise ValueError
                if isinstance(value, str):
                    if len(value) > limits["MAX_SOURCE_CELL_CHARS"] + 16:
                        raise ValueError
                    total += len(value)
                    if total > limits["MAX_SOURCE_TEXT_CHARS"]:
                        raise ValueError
        return commands
    except (ValueError, TypeError, KeyError, RecursionError) as exc:
        if isinstance(exc, ImportLimitError):
            raise
        raise ImportLimitError("Import: Ungueltige Parser-Antwort.") from exc
