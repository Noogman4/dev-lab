"""Full bundled documentation coverage and catalog trust boundaries."""

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tkinter as tk

import pytest

from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_markdown_service as markdown
from netmon.ui.linux_help_reader import LinuxHelpReader

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ROOT / "docs/linux-befehlsdatenbank"
CATALOG = json.loads((DOCUMENTS / "index.json").read_text())


def entry(record):
    return {"id": record["id"], "name": record["name"], "cmd": record["name"]}


def test_every_real_database_entry_loads_its_own_bundled_document():
    commands = controller._load_linux_help_commands(
        controller.linux_help_csv_path(), isolated=False
    )
    assert len(commands) == len(CATALOG["records"]) == 713
    records = {record["id"]: record for record in CATALOG["records"]}
    assert {command["id"] for command in commands} == set(records)
    for command in commands:
        record = records[command["id"]]
        document = markdown.load_command_document(command)
        assert document is not None, command["name"]
        assert document.metadata["source_record"] == record["source_record"]
        assert document.metadata["id"] == record["id"]
        assert document.metadata["command"] == record["command"]
        assert (
            len([b for b in document.blocks if b.kind == "heading" and b.level == 2])
            == 10
        )


@pytest.fixture
def local_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(markdown, "DOCUMENT_DIR", tmp_path)
    markdown._catalog.cache_clear()
    (tmp_path / "index.json").write_text(json.dumps(CATALOG))
    for filename in ("ls.md", "7z.md"):
        (tmp_path / filename).write_bytes((DOCUMENTS / filename).read_bytes())
    yield tmp_path
    markdown._catalog.cache_clear()


@pytest.mark.parametrize("field", ["id", "name", "cmd", "entry_type"])
def test_edited_or_imported_identity_cannot_select_another_document(field):
    item = {"id": "ls", "name": "ls", "cmd": "ls", "entry_type": "command"}
    item[field] = "glossary" if field == "entry_type" else "ls; unrelated"
    item["document"] = "../../unrelated.md"
    assert markdown.load_command_document(item) is None


def test_user_supplied_document_path_is_ignored(local_catalog):
    item = {"id": "ls", "name": "ls", "cmd": "ls", "document": "../../other.md"}
    assert markdown.load_command_document(item).metadata["id"] == "ls"
    (local_catalog / "ls.md").unlink()
    assert markdown.load_command_document(item) is None


def test_changed_document_is_rejected_before_display(local_catalog):
    path = local_catalog / "ls.md"
    path.write_text(path.read_text() + "\nChanged content\n")
    with pytest.raises(ValueError, match="Katalog"):
        markdown.load_command_document({"id": "ls", "name": "ls", "cmd": "ls"})


def test_metadata_identity_is_checked_even_with_matching_digest(local_catalog):
    path = local_catalog / "ls.md"
    path.write_text(path.read_text().replace('id: "ls"', 'id: "different"'))
    catalog = copy.deepcopy(CATALOG)
    record = next(r for r in catalog["records"] if r["id"] == "ls")
    record["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (local_catalog / "index.json").write_text(json.dumps(catalog))
    with pytest.raises(ValueError, match="passt nicht"):
        markdown.load_command_document(entry(record))


@pytest.mark.parametrize("problem", ["path", "duplicate", "number", "digest"])
def test_invalid_catalog_cannot_supply_a_path(local_catalog, problem):
    catalog = copy.deepcopy(CATALOG)
    first = catalog["records"][0]
    if problem == "path":
        first["document"] = "../elsewhere.md"
    elif problem == "duplicate":
        first["id"] = catalog["records"][1]["id"]
    elif problem == "number":
        first["source_record"] = True
    else:
        first["sha256"] = "not a digest"
    (local_catalog / "index.json").write_text(json.dumps(catalog))
    with pytest.raises(ValueError):
        markdown.load_command_document(entry(first))


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversized"])
def test_catalog_read_is_regular_and_bounded(local_catalog, monkeypatch, kind):
    path = local_catalog / "index.json"
    if kind == "oversized":
        monkeypatch.setattr(markdown, "MAX_CATALOG_BYTES", 8)
    else:
        path.unlink()
        if kind == "symlink":
            path.symlink_to(DOCUMENTS / "index.json")
        else:
            os.mkfifo(path)
    with pytest.raises((OSError, ValueError)):
        markdown.load_command_document({"id": "ls", "name": "ls", "cmd": "ls"})


def test_only_exact_additional_bundled_source_addresses_are_clickable():
    url = "https://man7.org/linux/man-pages/man1/find.1.html"
    assert markdown.source_url(url) == url
    assert markdown.source_url("https://man7.org/unlisted-target") == ""
    assert markdown.source_url(url + "?unlisted=1") == ""
    assert markdown.source_url("https://127.0.0.1/") == ""
    for url in CATALOG["source_urls"]:
        assert markdown.source_url(url) == url


def test_package_copy_block_contains_the_complete_independent_catalog(
    tmp_path, monkeypatch
):
    source = (ROOT / "scripts/build_netmon_deb.sh").read_text()
    code = re.search(r"<<'LINUX_HELP_DOCS'\n(.*?)\nLINUX_HELP_DOCS", source, re.S)[1]
    code = "import os\nos.umask(0o077)\n" + code
    subprocess.run(
        [sys.executable, "-I", "-c", code, str(ROOT), str(tmp_path)], check=True
    )
    packaged = tmp_path / "docs/linux-befehlsdatenbank"
    assert packaged.stat().st_mode & 0o777 == 0o755
    assert packaged.parent.stat().st_mode & 0o777 == 0o755
    assert all(p.stat().st_mode & 0o777 == 0o644 for p in packaged.iterdir())
    assert {p.name for p in packaged.iterdir()} == {
        "index.json",
        *(r["document"] for r in CATALOG["records"]),
    }
    monkeypatch.setattr(markdown, "DOCUMENT_DIR", packaged)
    for record in CATALOG["records"]:
        assert markdown.load_command_document(entry(record)) is not None


@pytest.mark.parametrize("number", [14, 101, 180, 256, 301, 401, 525, 672, 713])
def test_non_pilot_documents_render_passively(number, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Opening documentation executed a process")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    root = tk.Tk()
    try:
        root.geometry("900x700")
        record = CATALOG["records"][number - 1]
        reader = LinuxHelpReader(root)
        reader.pack(fill="both", expand=True)
        document = markdown.load_command_document(entry(record))
        reader.set_document(document, entry(record))
        root.update()
        assert len(reader.headings) == 10
        assert reader.text.cget("state") == "disabled"
        assert len(reader.code_buttons) == len(
            [b for b in document.blocks if b.kind == "code"]
        )
    finally:
        root.destroy()
