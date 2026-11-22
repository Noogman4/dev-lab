"""Bounded, passive Markdown documents selected through the bundled catalog."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

DOCUMENT_DIR = Path(__file__).resolve().parents[2] / "docs/linux-befehlsdatenbank"
MAX_CATALOG_BYTES = 2 * 1024 * 1024
SOURCE_SHA256 = "40c0b0c306636337f25276c1ffb58322bb2ae1f35225ac70dc33ef98e00ae887"
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
    source: str = ""


def _https_url(value):
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
            and parsed.hostname
            and parsed.username is None
            and parsed.password is None
            and parsed.port in {None, 443}
            and not parsed.netloc.endswith(":")
        ):
            return value
    except ValueError:
        pass
    return ""


def source_url(value):
    """Allow baseline sources and exact source URLs from the bundled catalog."""
    if not _https_url(value):
        return ""
    if urlsplit(value).hostname in SOURCE_HOSTS:
        return value
    try:
        _records, sources = _catalog(str(DOCUMENT_DIR))
    except (OSError, ValueError, RecursionError):
        sources = ()
    if value in sources:
        return value
    try:
        # Import lazily: the glossary shares this module's passive parser.
        from .linux_help_glossary_service import catalog

        _records, sources = catalog()
    except (OSError, ValueError, RecursionError):
        return ""
    return value if value in sources else ""


def _read_regular(path, maximum):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("Keine reguläre Dokumentdatei.")
        raw = handle.read(maximum + 1)
    if len(raw) > maximum:
        raise ValueError("Dokumentdatei überschreitet die Größenbegrenzung.")
    return raw


@lru_cache(maxsize=4)
def _catalog(directory):
    """Load only the installed manifest, never a path supplied by an entry."""
    catalog = json.loads(
        _read_regular(Path(directory) / "index.json", MAX_CATALOG_BYTES).decode("utf-8")
    )
    if (
        not isinstance(catalog, dict)
        or catalog.get("schema_version") != 1
        or catalog.get("source_sha256") != SOURCE_SHA256
        or catalog.get("total_records") != 713
        or not isinstance(catalog.get("records"), list)
        or len(catalog["records"]) != 713
    ):
        raise ValueError("Ungültiger Dokumentkatalog.")
    records = {}
    files = set()
    for number, record in enumerate(catalog["records"], 1):
        if (
            not isinstance(record, dict)
            or type(record.get("source_record")) is not int
            or record["source_record"] != number
        ):
            raise ValueError("Ungültige Dokumentzuordnung.")
        for key in ("id", "name", "command", "category", "document", "sha256"):
            if not isinstance(record.get(key), str) or not 0 < len(record[key]) <= 256:
                raise ValueError("Unvollständige Dokumentzuordnung.")
        if (
            not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*\.md", record["document"])
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
            or record["id"] in records
            or record["document"] in files
        ):
            raise ValueError("Mehrdeutige oder ungültige Dokumentzuordnung.")
        records[record["id"]] = record
        files.add(record["document"])
    sources = catalog.get("source_urls", [])
    if (
        not isinstance(sources, list)
        or len(sources) > 4096
        or any(not _https_url(url) for url in sources)
    ):
        raise ValueError("Ungültige Dokumentquellen.")
    return records, frozenset(sources)


def _cells(line):
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _document_parts(text):
    """Bound and parse the common JSON-valued header before any rendering."""
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
    return metadata, lines, index + 1


def parse_document(text):
    """Parse command documentation; glossary headers use their own contract."""
    metadata, lines, index = _document_parts(text)
    for key in ("id", "name", "command", "category", "language"):
        if not isinstance(metadata.get(key), str) or not 0 < len(metadata[key]) <= 256:
            raise ValueError("Erforderliche Markdown-Metadaten fehlen.")
    if type(metadata.get("root_required")) is not bool or metadata.get(
        "risk_level"
    ) not in {"safe", "caution", "danger"}:
        raise ValueError("Ungültige Rechte- oder Risikoangabe.")
    return Document(metadata, _parse_blocks(lines, index), text)


def parse_glossary_document(text):
    metadata, lines, index = _document_parts(text)
    for key in ("id", "name", "category", "language"):
        if not isinstance(metadata.get(key), str) or not 0 < len(metadata[key]) <= 256:
            raise ValueError("Erforderliche Glossar-Metadaten fehlen.")
    if (
        metadata.get("entry_type") != "glossary"
        or not re.fullmatch(r"it_\d{4}", metadata["id"])
        or metadata.get("language") != "de"
        or metadata.get("source_catalog") != "tools/it_lexikon_linux_hilfe.json"
        or type(metadata.get("source_record")) is not int
        or not 1 <= metadata["source_record"] <= 302
        or metadata.get("status") not in ("review_pending", "reviewed")
        or set(metadata) & {"command", "root_required", "risk_level"}
    ):
        raise ValueError("Ungültige Glossar-Metadaten.")
    for key in ("tags", "related"):
        values = metadata.get(key)
        if (
            not isinstance(values, list)
            or len(values) > 64
            or any(
                not isinstance(value, str) or not 0 < len(value) <= 256
                for value in values
            )
        ):
            raise ValueError("Ungültige Glossar-Verweise.")
    return Document(metadata, _parse_blocks(lines, index), text)


def _parse_blocks(lines, index):
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
    return tuple(blocks)


def load_command_document(item):
    """Match catalog identity and verify bytes before displaying documentation."""
    if (
        not isinstance(item, dict)
        or item.get("entry_type", "command") != "command"
        or not all(isinstance(item.get(k), str) for k in ("id", "name", "cmd"))
    ):
        return None
    try:
        records, _sources = _catalog(str(DOCUMENT_DIR))
    except FileNotFoundError:
        return None
    record = records.get(item["id"])
    if (
        record is None
        or item["name"] != record["name"]
        or item["cmd"].strip() != record["name"]
    ):
        return None
    try:
        raw = _read_regular(DOCUMENT_DIR / record["document"], MAX_BYTES)
    except FileNotFoundError:
        return None
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError("Dokument stimmt nicht mit dem Katalog überein.")
    document = parse_document(raw.decode("utf-8-sig"))
    for key in ("id", "name", "command", "category", "source_record"):
        if document.metadata.get(key) != record[key]:
            raise ValueError("Markdown-Dokument passt nicht zum Befehl.")
    return document
