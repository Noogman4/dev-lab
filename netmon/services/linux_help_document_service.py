"""Document model helpers for Linux help PDFs."""

from __future__ import annotations

import textwrap


def _value(item: dict, key: str, default: str = "") -> str:
    return str((item or {}).get(key) or default).strip()


def _risk_title(risk_key: str) -> str:
    mapping = {
        "safe": "Sicher",
        "caution": "Mit Vorsicht",
        "danger": "Gefaehrlich",
    }
    return mapping.get(str(risk_key or "").strip().lower(), "Unbekannt")


def _risk_detail(item: dict) -> str:
    risk = str((item or {}).get("risk") or "").strip().lower()
    root_required = bool((item or {}).get("root_required"))
    if risk == "danger":
        return (
            "Dieser Befehl kann Systemzustand, Daten oder Berechtigungen deutlich "
            "veraendern. Vorher Ziel, Pfade und Parameter genau pruefen."
        )
    if risk == "safe":
        if root_required:
            return (
                "Der Befehl gilt in der Datenbank als eher sicher, benoetigt aber "
                "gegebenenfalls erhoehte Rechte."
            )
        return (
            "Der Befehl gilt in der Datenbank als eher sicher. Trotzdem sollten "
            "Dateiname, Zielpfad und freier Speicherplatz geprueft werden."
        )
    return (
        "Der Befehl kann je nach Parametern lesend oder veraendernd arbeiten. "
        "Optionen und Zielpfade deshalb bewusst waehlen."
    )


def _split_tags(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(",") if part.strip()]


def build_linux_help_document(item: dict, *, source_prompt: str = "") -> dict:
    """Create a normalized document model for one Linux help entry."""
    entry = dict(item or {})
    name = _value(entry, "name", "Unbekannter Befehl")
    command = _value(entry, "cmd", name)
    syntax = _value(entry, "syntax", command or "-")
    example = _value(entry, "example", command or "-")
    info = _value(entry, "info", "Keine Kurzbeschreibung vorhanden.")
    explanation = _value(entry, "explanation", info)
    warning_text = _value(entry, "warning_text")
    category = _value(entry, "category", "Allgemein")
    risk_key = _value(entry, "risk", "unknown")
    risk_title = _risk_title(risk_key)
    root_required = bool(entry.get("root_required"))
    tags = _split_tags(_value(entry, "tags"))

    safe_tips = [
        "Vor der Ausfuehrung Dateinamen, Pfade und Schreibrechte pruefen.",
        "Zuerst mit --help oder einer lesenden Variante arbeiten, wenn verfuegbar.",
        "Bei Archiven und Kompression freien Speicherplatz vorab kontrollieren.",
    ]

    related_commands = []
    if command:
        first = command.split()[0]
        if first in {"unlzma", "lzma"}:
            related_commands = ["xz", "unxz", "xzcat"]
        elif first in {"tar"}:
            related_commands = ["gzip", "xz", "cpio"]

    sections = [
        {
            "title": "Kurzbeschreibung",
            "body": info,
        },
        {
            "title": "Was macht der Befehl?",
            "body": explanation or info,
        },
        {
            "title": "Syntax",
            "body": syntax or command or "-",
        },
        {
            "title": "Beispiel",
            "body": example or command or "-",
        },
        {
            "title": "Risiken und Hinweise",
            "body": "\n".join(
                line
                for line in [
                    f"Risikostufe: {risk_title}",
                    f"Root erforderlich: {'Ja' if root_required else 'Nein'}",
                    _risk_detail(entry),
                    warning_text,
                ]
                if str(line or "").strip()
            ),
        },
        {
            "title": "Tipps fuer Einsteiger",
            "body": "\n".join(f"- {tip}" for tip in safe_tips),
        },
    ]

    if related_commands:
        sections.append(
            {
                "title": "Verwandte Befehle",
                "body": ", ".join(related_commands),
            }
        )

    if source_prompt:
        sections.append(
            {
                "title": "Anhang: Verwendeter Prompt",
                "body": source_prompt,
            }
        )

    return {
        "title": f"{name} – Linux-Hilfe",
        "command_name": name,
        "command": command,
        "category": category,
        "risk_level": risk_key,
        "root_required": root_required,
        "tags": tags,
        "summary": info,
        "source_prompt": source_prompt,
        "sections": sections,
    }


def build_linux_help_document_preview(document: dict) -> str:
    """Render a plain text preview from a document model."""
    payload = dict(document or {})
    lines = [
        payload.get("title") or "Linux-Hilfe-Dokument",
        "",
        f"Befehl: {payload.get('command') or '-'}",
        f"Kategorie: {payload.get('category') or '-'}",
        f"Risiko: {_risk_title(payload.get('risk_level') or '')}",
        f"Root: {'Ja' if payload.get('root_required') else 'Nein'}",
        f"Tags: {', '.join(payload.get('tags') or []) or '-'}",
    ]
    for section in payload.get("sections") or []:
        title = str(section.get("title") or "").strip()
        body = str(section.get("body") or "").strip()
        if not title and not body:
            continue
        lines.extend(["", title, "-" * len(title)])
        if body:
            lines.append(body)
    return "\n".join(lines).strip()


def build_linux_help_pdf_lines(document: dict, *, width: int = 96) -> list[str]:
    """Convert a document preview into wrapped text lines for the PDF builder."""
    preview = build_linux_help_document_preview(document)
    wrapped: list[str] = []
    for raw_line in str(preview or "").splitlines():
        if not raw_line.strip():
            wrapped.append("")
            continue
        chunks = textwrap.wrap(
            raw_line,
            width=max(30, int(width)),
            replace_whitespace=False,
            drop_whitespace=False,
        )
        wrapped.extend(chunks or [""])
    return wrapped
