"""Private Markdown storage for the single Linux-help entry list."""

from datetime import datetime
import json
import os
import re
import stat
import uuid

try:
    from netmon.core.state import get_netmon_documents_subdir
    from netmon.core.utils import safe_write_json, user_json_write_scope
    from netmon.services.linux_help_library_markdown import (
        parse_library_markdown,
        split_markdown,
    )
    from netmon.services.linux_help_markdown_service import MAX_BYTES
except ModuleNotFoundError:
    from core.state import get_netmon_documents_subdir
    from core.utils import safe_write_json, user_json_write_scope
    from services.linux_help_library_markdown import (
        parse_library_markdown,
        split_markdown,
    )
    from services.linux_help_markdown_service import MAX_BYTES


def linux_help_markdown_dir():
    return get_netmon_documents_subdir("LinuxHelp", "markdown")


def linux_help_meta_dir():
    return get_netmon_documents_subdir("LinuxHelp", "meta")


def _read_regular(path, limit):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("Keine reguläre Datei oder Datei zu groß.")
        raw = handle.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("Dokument ist zu groß.")
    return raw


def _document_path(metadata, kind):
    identifier = metadata.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"[\w-]{1,150}", identifier):
        raise ValueError("Ungültige Dokumentkennung.")
    directory, suffix = {
        "markdown": (linux_help_markdown_dir, ".md"),
        "json": (linux_help_meta_dir, ".json"),
    }[kind]
    path = os.path.join(directory(), identifier + suffix)
    if os.path.islink(path):
        raise ValueError("Dokumentverknüpfungen werden nicht unterstützt.")
    return path


def read_linux_help_markdown(metadata):
    return _read_regular(_document_path(metadata, "markdown"), MAX_BYTES).decode(
        "utf-8-sig"
    )


def load_linux_help_markdown(metadata):
    return parse_library_markdown(read_linux_help_markdown(metadata), metadata)


def inspect_markdown_import(path):
    if os.path.splitext(str(path))[1].lower() not in (".md", ".markdown"):
        raise ValueError("Bitte eine Markdown-Datei auswählen.")
    text = _read_regular(path, MAX_BYTES).decode("utf-8-sig")
    title = re.search(r"^#\s+(.+)$", text, re.M)
    fallback = (
        title[1].strip() if title else os.path.splitext(os.path.basename(path))[0]
    )
    document = parse_library_markdown(text, {"name": fallback})
    fields, _body = split_markdown(text)
    meta = document.metadata
    entry = {
        "id": fields.get("id", ""),
        "entry_type": meta["entry_type"],
        "name": meta["name"],
        "category": meta["category"],
        "cmd": meta.get("command", ""),
        "tags": meta.get("tags", []),
        "related": meta.get("related", []),
        "risk": meta.get("risk_level", "unknown"),
        "root_required": meta.get("root_required", False),
        "info": next(
            (block.text[:300] for block in document.blocks if block.kind == "text"),
            "",
        ),
        "explanation": "",
    }
    return text, entry


def save_linux_help_markdown(text, entry=None, *, title="", command_name=""):
    """Publish a new immutable revision; callers link it only after saving JSON."""
    parse_library_markdown(text)
    moment = datetime.now().isoformat(timespec="seconds")
    identifier = "md_" + uuid.uuid4().hex
    name = (entry or {}).get("name") or command_name or title or "Dokumentation"
    metadata = {
        "id": identifier,
        "title": title or name,
        "command_name": command_name or name,
        "created_at": moment,
        "format": "markdown",
    }
    if entry is not None:
        metadata["entry"] = {
            key: value for key, value in entry.items() if key != "markdown_id"
        }
    path = _document_path(metadata, "markdown")
    meta_path = _document_path(metadata, "json")
    metadata.update(markdown_path=path, json_path=meta_path)
    with user_json_write_scope(path):
        descriptor = os.open(
            path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(text.encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
            ok, error = safe_write_json(
                meta_path, metadata, indent=2, ensure_ascii=False
            )
            if not ok:
                raise RuntimeError(
                    "Markdown-Metadaten konnten nicht gespeichert werden: " + str(error)
                )
        except Exception:
            os.unlink(path)
            raise
    return metadata


def import_linux_help_markdown(path, *, title="", command_name=""):
    text, inferred = inspect_markdown_import(path)
    return save_linux_help_markdown(
        text,
        title=title or inferred["name"],
        command_name=command_name or inferred["name"],
    )


def get_linux_help_document_by_id(document_id):
    metadata = {"id": document_id}
    try:
        payload = json.loads(
            _read_regular(
                _document_path(metadata, "json"), 2 * MAX_BYTES + 16384
            ).decode("utf-8")
        )
    except FileNotFoundError:
        return None
    if not isinstance(payload, dict) or payload.get("id") != document_id:
        raise ValueError("Ungültige Markdown-Metadaten.")
    if not payload.get("markdown_path"):
        return None
    payload["markdown_path"] = _document_path(metadata, "markdown")
    payload["json_path"] = _document_path(metadata, "json")
    return payload


def list_linux_help_documents():
    entries = []
    for name in sorted(os.listdir(linux_help_meta_dir()))[:4096]:
        if not name.endswith(".json"):
            continue
        try:
            item = get_linux_help_document_by_id(name[:-5])
            if item is not None:
                _read_regular(_document_path(item, "markdown"), MAX_BYTES)
                entries.append(item)
        except (OSError, ValueError, RecursionError):
            continue
    return entries


def delete_linux_help_document(document_id):
    metadata = get_linux_help_document_by_id(document_id)
    if metadata is None:
        raise FileNotFoundError("Markdown-Dokument fehlt.")
    paths = [_document_path(metadata, kind) for kind in ("markdown", "json")]
    # Validate every existing target before removing either member of the bundle.
    for path in paths:
        try:
            _read_regular(path, 2 * MAX_BYTES + 16384)
        except FileNotFoundError:
            pass
    deleted, missing = [], []
    with user_json_write_scope(paths[0]):
        for path in paths:
            try:
                os.unlink(path)
                deleted.append(path)
            except FileNotFoundError:
                missing.append(path)
    return {"id": document_id, "deleted": deleted, "missing": missing}
