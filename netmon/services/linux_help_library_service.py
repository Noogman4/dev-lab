"""Storage helpers for generated Linux help documents."""

from __future__ import annotations

from datetime import datetime
import json
import os
import shutil

try:
    from netmon.core.state import get_netmon_documents_subdir
    from netmon.core.utils import safe_write_json
except ModuleNotFoundError:
    from core.state import get_netmon_documents_subdir
    from core.utils import safe_write_json

try:
    from netmon.services.linux_help_document_service import (
        build_linux_help_document_preview,
        build_linux_help_pdf_lines,
    )
    from netmon.services.linux_help_pdf_service import render_text_pdf
except ModuleNotFoundError:
    from services.linux_help_document_service import (
        build_linux_help_document_preview,
        build_linux_help_pdf_lines,
    )
    from services.linux_help_pdf_service import render_text_pdf


def linux_help_documents_dir() -> str:
    return get_netmon_documents_subdir("LinuxHelp")


def linux_help_pdfs_dir() -> str:
    return get_netmon_documents_subdir("LinuxHelp", "pdfs")


def linux_help_meta_dir() -> str:
    return get_netmon_documents_subdir("LinuxHelp", "meta")


def _slugify(text: str) -> str:
    cleaned = "".join(
        char.lower() if char.isalnum() else "_" for char in str(text or "").strip()
    )
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_") or "linux_help"


def _document_id(command_name: str, moment: datetime | None = None) -> str:
    stamp = (moment or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
    return f"{_slugify(command_name)}_{stamp}"


def create_linux_help_document_bundle(
    document: dict,
    *,
    generator: str = "manual",
    language: str = "de",
    moment: datetime | None = None,
) -> dict:
    payload = dict(document or {})
    doc_id = _document_id(payload.get("command_name") or payload.get("title") or "", moment)
    pdf_path = os.path.join(linux_help_pdfs_dir(), f"{doc_id}.pdf")
    json_path = os.path.join(linux_help_meta_dir(), f"{doc_id}.json")

    preview_text = build_linux_help_document_preview(payload)
    pdf_lines = build_linux_help_pdf_lines(payload)
    render_text_pdf(pdf_lines, pdf_path, title=str(payload.get("title") or "").strip())

    metadata = {
        "id": doc_id,
        "title": str(payload.get("title") or "").strip(),
        "command_name": str(payload.get("command_name") or "").strip(),
        "command": str(payload.get("command") or "").strip(),
        "category": str(payload.get("category") or "").strip(),
        "risk_level": str(payload.get("risk_level") or "").strip(),
        "root_required": bool(payload.get("root_required")),
        "tags": list(payload.get("tags") or []),
        "summary": str(payload.get("summary") or "").strip(),
        "source_prompt": str(payload.get("source_prompt") or "").strip(),
        "preview_text": preview_text,
        "generator": str(generator or "manual").strip() or "manual",
        "language": str(language or "de").strip() or "de",
        "created_at": (moment or datetime.now()).isoformat(timespec="seconds"),
        "pdf_path": pdf_path,
        "json_path": json_path,
    }
    ok, err = safe_write_json(json_path, metadata, indent=2, ensure_ascii=False)
    if not ok:
        raise RuntimeError(f"LinuxHelp-Metadaten konnten nicht gespeichert werden: {err}")
    return metadata


def import_linux_help_pdf(path: str, *, title: str = "", command_name: str = "") -> dict:
    source = str(path or "").strip()
    if not source or not os.path.isfile(source):
        raise FileNotFoundError(source or "missing path")
    if not source.lower().endswith(".pdf"):
        raise ValueError("Nur PDF-Dateien werden unterstuetzt.")

    now = datetime.now()
    inferred_name = command_name or os.path.splitext(os.path.basename(source))[0]
    doc_id = _document_id(inferred_name, now)
    target_pdf = os.path.join(linux_help_pdfs_dir(), f"{doc_id}.pdf")
    json_path = os.path.join(linux_help_meta_dir(), f"{doc_id}.json")
    shutil.copy2(source, target_pdf)

    metadata = {
        "id": doc_id,
        "title": title or os.path.basename(source),
        "command_name": inferred_name,
        "command": "",
        "category": "",
        "risk_level": "unknown",
        "root_required": False,
        "tags": [],
        "summary": "Importierte PDF-Dokumentation.",
        "source_prompt": "",
        "preview_text": (
            "Importierte Linux-Hilfe-PDF.\n\n"
            f"Datei: {os.path.basename(target_pdf)}\n"
            "Fuer importierte PDFs ist keine interne Textvorschau vorhanden."
        ),
        "generator": "import",
        "language": "de",
        "created_at": now.isoformat(timespec="seconds"),
        "pdf_path": target_pdf,
        "json_path": json_path,
    }
    ok, err = safe_write_json(json_path, metadata, indent=2, ensure_ascii=False)
    if not ok:
        raise RuntimeError(f"LinuxHelp-Importmetadaten konnten nicht gespeichert werden: {err}")
    return metadata


def list_linux_help_documents() -> list[dict]:
    entries = []
    meta_dir = linux_help_meta_dir()
    for name in sorted(os.listdir(meta_dir), reverse=True):
        if not name.endswith(".json"):
            continue
        path = os.path.join(meta_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        payload.setdefault("json_path", path)
        entries.append(payload)
    entries.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return entries


def get_linux_help_document_by_id(document_id: str) -> dict | None:
    target = str(document_id or "").strip()
    if not target:
        return None
    for item in list_linux_help_documents():
        if str(item.get("id") or "").strip() == target:
            return item
    return None


def delete_linux_help_document(document_id: str) -> dict:
    """Delete one Linux help PDF bundle and return deletion details."""
    metadata = get_linux_help_document_by_id(document_id)
    if not metadata:
        raise FileNotFoundError(str(document_id or "").strip() or "missing document id")

    deleted = []
    missing = []
    errors = []
    for key in ("pdf_path", "json_path"):
        path = str(metadata.get(key) or "").strip()
        if not path:
            continue
        if not os.path.isfile(path):
            missing.append(path)
            continue
        try:
            os.remove(path)
            deleted.append(path)
        except OSError as exc:
            errors.append(f"{path}: {exc}")

    if errors:
        raise RuntimeError("; ".join(errors))
    return {
        "id": metadata.get("id") or "",
        "title": metadata.get("title") or metadata.get("command_name") or "",
        "deleted": deleted,
        "missing": missing,
    }
