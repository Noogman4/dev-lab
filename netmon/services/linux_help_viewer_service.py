"""Viewer helpers for Linux help document metadata."""

from __future__ import annotations


def build_linux_help_library_preview(metadata: dict) -> str:
    item = dict(metadata or {})
    lines = [
        item.get("title") or "Linux-Hilfe-Dokument",
        "",
        f"Befehl: {item.get('command_name') or item.get('command') or '-'}",
        f"Erstellt: {item.get('created_at') or '-'}",
        f"Generator: {item.get('generator') or '-'}",
        f"Sprache: {item.get('language') or '-'}",
        f"PDF: {item.get('pdf_path') or '-'}",
    ]
    summary = str(item.get("summary") or "").strip()
    if summary:
        lines.extend(["", "Kurzbeschreibung", "----------------", summary])
    preview = str(item.get("preview_text") or "").strip()
    if preview:
        lines.extend(["", "Vorschau", "--------", preview])
    prompt = str(item.get("source_prompt") or "").strip()
    if prompt:
        lines.extend(["", "Prompt", "------", prompt])
    return "\n".join(lines).strip()
