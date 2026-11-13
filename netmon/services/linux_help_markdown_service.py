"""Bounded, passive Markdown documents for the Linux-help pilot (7z only)."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

DOCUMENT_DIR = Path(__file__).resolve().parents[2] / "docs/linux-befehlsdatenbank"
DOCUMENT_FILES = {"7z": "7z.md"}
MAX_BYTES = 256 * 1024
MAX_LINES = 5000
MAX_BLOCKS = 500
MAX_CELLS = 1000
MAX_CODE_CHARS = 32 * 1024
SOURCE_HOSTS = {"www.7-zip.org", "manpages.debian.org", "sources.debian.org"}


@dataclass(frozen=True)
class Block:
    kind: str
    text: str = ""
    level: int = 0
    rows: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class Document:
    metadata: dict
    blocks: tuple[Block, ...]


def source_url(value):
    """Only the reviewed documentation hosts may be handed to a browser."""
    if (
        not isinstance(value, str)
        or len(value) > 4096
        or "\\" in value
        or any(char.isspace() or not char.isprintable() for char in value)
    ):
        return ""
    try:
        parsed = urlsplit(value)
        if (
            parsed.scheme == "https"
            and parsed.hostname in SOURCE_HOSTS
            and parsed.username is None
            and parsed.password is None
            and parsed.port in {None, 443}
            and not parsed.netloc.endswith(":")
        ):
            return value
    except ValueError:
        pass
    return ""


def _cells(line):
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def parse_document(text):
    """Parse the documented subset, never HTML, includes or executable directives."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Markdown-Dokument überschreitet die Größenbegrenzung.")
    if any(not char.isprintable() and char not in "\n\r\t" for char in text):
        raise ValueError("Unzulässige Steuerzeichen im Markdown-Dokument.")
    lines = text.splitlines()
    if len(lines) > MAX_LINES or not lines or lines[0] != "---":
        raise ValueError("Ungültiger Markdown-Dokumentkopf.")
    metadata = {}
    index = 1
    while index < len(lines) and lines[index] != "---":
        key, separator, value = lines[index].partition(":")
        if not separator or not re.fullmatch(r"[a-z_]+", key) or key in metadata:
            raise ValueError("Ungültige Markdown-Metadaten.")
        try:
            metadata[key] = json.loads(value.strip())
        except json.JSONDecodeError as error:
            raise ValueError("Metadaten benötigen JSON-kompatible Werte.") from error
        index += 1
        if index > 40:
            raise ValueError("Zu viele Markdown-Metadaten.")
    if index == len(lines):
        raise ValueError("Unvollständiger Markdown-Dokumentkopf.")
    for key in ("id", "name", "command", "category", "language"):
        if not isinstance(metadata.get(key), str) or not 0 < len(metadata[key]) <= 256:
            raise ValueError("Erforderliche Markdown-Metadaten fehlen.")
    if type(metadata.get("root_required")) is not bool or metadata.get(
        "risk_level"
    ) not in {"safe", "caution", "danger"}:
        raise ValueError("Ungültige Rechte- oder Risikoangabe.")
    index += 1
    blocks = []
    cells = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith("```"):
            code = []
            index += 1
            while index < len(lines) and lines[index] != "```":
                code.append(lines[index])
                index += 1
            if index == len(lines) or len("\n".join(code)) > MAX_CODE_CHARS:
                raise ValueError("Ungültiger oder zu großer Codeblock.")
            blocks.append(Block("code", "\n".join(code)))
            index += 1
        elif heading := re.match(r"^(#{1,6})\s+(.+)$", line):
            blocks.append(Block("heading", heading[2], len(heading[1])))
            index += 1
        elif (
            line.startswith("|")
            and index + 1 < len(lines)
            and all(
                re.fullmatch(r":?-{3,}:?", cell) for cell in _cells(lines[index + 1])
            )
        ):
            rows = [_cells(line)]
            index += 2
            while index < len(lines) and lines[index].startswith("|"):
                rows.append(_cells(lines[index]))
                index += 1
            width = len(rows[0])
            cells += sum(len(row) for row in rows)
            if width > 8 or cells > MAX_CELLS or any(len(row) != width for row in rows):
                raise ValueError("Ungültige oder zu große Markdown-Tabelle.")
            blocks.append(Block("table", rows=tuple(rows)))
        else:
            # Lines outside the supported block syntax stay plain text.
            blocks.append(Block("text", line))
            index += 1
        if len(blocks) > MAX_BLOCKS:
            raise ValueError("Zu viele Markdown-Abschnitte.")
    return Document(metadata, tuple(blocks))


def load_command_document(item):
    """Match an exact pilot entry; no file path is derived from imported fields."""
    if (
        not isinstance(item, dict)
        or item.get("entry_type") == "glossary"
        or item.get("name") != "7z"
        or str(item.get("cmd", "")).strip() != "7z"
    ):
        return None
    path = DOCUMENT_DIR / DOCUMENT_FILES["7z"]
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        return None
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BYTES:
            raise ValueError("Ungültige Markdown-Dokumentdatei.")
        raw = handle.read(MAX_BYTES + 1)
    document = parse_document(raw.decode("utf-8-sig"))
    if document.metadata["id"] != "7z" or document.metadata["command"] != "7z":
        raise ValueError("Markdown-Dokument passt nicht zum Befehl.")
    return document
