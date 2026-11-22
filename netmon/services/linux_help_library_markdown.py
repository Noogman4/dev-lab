"""Bounded passive Markdown for personal command and glossary entries."""

import json

try:
    from netmon.services import linux_help_markdown_service as markdown
except ModuleNotFoundError:
    from services import linux_help_markdown_service as markdown


def split_markdown(text):
    """Recognize only NetMon's JSON-valued header; ordinary YAML remains text."""
    if not isinstance(text, str) or len(text.encode("utf-8")) > markdown.MAX_BYTES:
        raise ValueError("Markdown-Dokument ist zu groß.")
    if not text.strip():
        raise ValueError("Markdown-Dokument ist leer.")
    if text.startswith(("---\n", "---\r\n")):
        try:
            meta, lines, start = markdown._document_parts(text)
        except (ValueError, TypeError, RecursionError):
            pass
        else:
            if all(
                isinstance(meta.get(key), str) and meta[key]
                for key in ("id", "name", "category")
            ):
                return meta, "\n".join(lines[start:]) + "\n"
    return {}, text


def entry_header(item):
    if not isinstance(item, dict):
        raise ValueError("Ungültige Markdown-Metadaten.")
    kind = "glossary" if item.get("entry_type") == "glossary" else "command"
    tags = item.get("tags") or []
    if isinstance(tags, str):
        tags = [value.strip() for value in tags.split(",") if value.strip()]
    meta = {
        "id": str(item.get("id") or "personal-document")[:256],
        "entry_type": kind,
        "name": str(
            item.get("name")
            or item.get("command_name")
            or item.get("title")
            or "Dokumentation"
        )[:256],
        "category": str(item.get("category") or "Eigene Dokumentationen")[:256],
        "language": "de",
        "tags": tags,
    }
    if kind == "glossary":
        related = item.get("related") or []
        if isinstance(related, str):
            related = [part.strip() for part in related.split(",") if part.strip()]
        meta["related"] = related
    else:
        risk = item.get("risk") or item.get("risk_level") or "caution"
        meta.update(
            command=str(item.get("cmd", item.get("command", ""))),
            root_required=item.get("root_required") is True,
            risk_level=risk if risk in ("safe", "caution", "danger") else "caution",
        )
    return meta


def format_entry_markdown(item, body):
    _old, body = split_markdown(body)
    header = entry_header(item)
    text = (
        "---\n"
        + "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in header.items()
        )
        + "\n---\n"
        + body
    )
    parse_library_markdown(text)
    return text


def parse_library_markdown(text, metadata=None):
    fields, body = split_markdown(text)
    # Private entry metadata is authoritative after edits to name/category.
    item = (metadata or {}).get("entry") or fields or metadata or {}
    meta = entry_header(item)
    # A personal entry may contain no executable command. Reuse the bounded
    # body parser without the bundled catalog's stricter identity contract.
    framed = format_header(meta) + body
    parsed, lines, start = markdown._document_parts(framed)
    return markdown.Document(parsed, markdown._parse_blocks(lines, start), text)


def format_header(meta):
    return (
        "---\n"
        + "\n".join(
            f"{key}: {json.dumps(value, ensure_ascii=False)}"
            for key, value in meta.items()
        )
        + "\n---\n"
    )
