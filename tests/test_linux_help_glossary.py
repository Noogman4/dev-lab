"""Glossary coverage, identity boundaries and real reader interactions."""

import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import pytest

from netmon.features import linux_help_controller as controller
from netmon.services import linux_help_glossary_service as glossary
from netmon.services import linux_help_markdown_service as markdown
from netmon.services.linux_help_reading_service import ReadingState
from netmon.ui import linux_help_reader as ui

ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = ROOT / "docs/linux-glossar"
CATALOG = json.loads((DOCUMENTS / "index.json").read_text())
SOURCE = json.loads(glossary.SOURCE_PATH.read_text())["entries"]
ENTRIES = [
    controller.normalize_linux_help_glossary_entry(SimpleNamespace(), source)
    for source in SOURCE
]


def test_all_glossary_documents_match_the_original_source():
    assert (
        len(CATALOG["records"]) == CATALOG["documented_records"] == len(SOURCE) == 302
    )
    for number, item in enumerate(ENTRIES, 1):
        document = glossary.load_glossary_document(item)
        record = CATALOG["records"][number - 1]
        assert record["source"] == SOURCE[number - 1]
        assert document.metadata["id"] == item["id"]
        assert document.metadata["source_record"] == number
        assert document.metadata["name"] == item["name"]
        assert not {"command", "root_required", "risk_level"} & document.metadata.keys()
        assert (
            len([b for b in document.blocks if b.kind == "heading" and b.level == 2])
            == 10
        )
        assert markdown.load_command_document(item) is None


@pytest.mark.parametrize(
    "number,expected",
    [
        *((number, None) for number in [*range(1, 11), 191, 268, 269]),
        (274, "Notizbeispiel 0.1.0"),
        (275, "py3 none any"),
        (285, "Verdoppelt eine Zahl."),
        (292, "8"),
        (297, "Haltepunkt erreicht"),
        (298, "Aufrufe: 3"),
        (299, "3 Messungen pro Variante"),
        (301, "Behalten: 3\nNach Freigabe: 0"),
        (302, "Zyklus freigegeben"),
    ],
)
def test_selected_python_example_has_the_documented_output(number, expected, tmp_path):
    text = (DOCUMENTS / CATALOG["records"][number - 1]["document"]).read_text()
    examples = re.findall(r"^```python\n(.*?)\n```", text, re.M | re.S)
    assert len(examples) == 1
    if expected is None:
        (expected,) = re.findall(r"^```text\n(.*?)\n```", text, re.M | re.S)
    # These examples were read before execution. They use in-memory data or
    # a self-created temporary database. The harness also removes networking.
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-c", examples[0]],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=5,
        check=True,
    )
    assert result.stdout == expected + "\n"
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []


@pytest.fixture
def local_catalog(tmp_path, monkeypatch):
    directory = tmp_path / "docs"
    directory.mkdir()
    for name in ("index.json", "it_0001.md"):
        shutil.copyfile(DOCUMENTS / name, directory / name)
    source = tmp_path / "source.json"
    shutil.copyfile(glossary.SOURCE_PATH, source)
    monkeypatch.setattr(glossary, "DOCUMENT_DIR", directory)
    monkeypatch.setattr(glossary, "SOURCE_PATH", source)
    glossary._catalog.cache_clear()
    yield directory
    glossary._catalog.cache_clear()


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", "../it_0001"),
        ("name", "Geändert"),
        ("cmd", "python evil.py"),
        ("entry_type", "command"),
    ],
)
def test_modified_identity_does_not_select_a_glossary_document(field, value):
    assert glossary.load_glossary_document(dict(ENTRIES[0], **{field: value})) is None


def test_personal_document_path_is_ignored_and_changed_bytes_are_rejected(
    local_catalog,
):
    item = dict(ENTRIES[0], document="../../elsewhere.md")
    assert glossary.load_glossary_document(item).metadata["id"] == "it_0001"
    document = local_catalog / "it_0001.md"
    document.write_text(document.read_text() + "\nChanged content\n")
    with pytest.raises(ValueError, match="Katalog"):
        glossary.load_glossary_document(item)


@pytest.mark.parametrize(
    "old,new",
    [
        ('name: "Algorithmus"', 'name: "Geändert"'),
        ("source_record: 1", "source_record: true"),
        ('status: "review_pending"', 'status: "reviewed"'),
        ('tags: ["grundlagen"]', 'tags: ["anders"]'),
        ('entry_type: "glossary"', 'entry_type: "command"'),
        ('language: "de"', 'language: "en"'),
        ("related: []", "related: []\nroot_required: false"),
    ],
)
def test_header_checked_even_if_hash_matches(local_catalog, old, new):
    path = local_catalog / "it_0001.md"
    text = path.read_text()
    assert old in text
    path.write_text(text.replace(old, new))
    catalog = copy.deepcopy(CATALOG)
    catalog["records"][0]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (local_catalog / "index.json").write_text(json.dumps(catalog))
    with pytest.raises(ValueError):
        glossary.load_glossary_document(ENTRIES[0])


@pytest.mark.parametrize(
    "problem", ["schema", "count", "path", "number", "duplicate", "source", "url"]
)
def test_invalid_index_is_rejected(local_catalog, problem):
    catalog = copy.deepcopy(CATALOG)
    record = catalog["records"][0]
    if problem == "schema":
        catalog["schema_version"] = True
    elif problem == "count":
        catalog["documented_records"] += 1
    elif problem == "path":
        record["document"] = "../elsewhere.md"
    elif problem == "number":
        record["source_record"] = True
    elif problem == "duplicate":
        catalog["records"][1] = record
    elif problem == "source":
        record["source"]["short"] = "Changed source"
    else:
        record["source_urls"] = ["file:///etc/passwd"]
    (local_catalog / "index.json").write_text(json.dumps(catalog))
    with pytest.raises(ValueError):
        glossary.load_glossary_document(ENTRIES[0])


@pytest.mark.parametrize("filename", ["index.json", "it_0001.md", "source.json"])
@pytest.mark.parametrize("problem", ["symlink", "fifo", "oversized"])
def test_files_are_regular_and_bounded(local_catalog, monkeypatch, filename, problem):
    path = (
        glossary.SOURCE_PATH if filename == "source.json" else local_catalog / filename
    )
    if problem == "oversized":
        monkeypatch.setattr(
            markdown,
            "MAX_BYTES" if filename.endswith(".md") else "MAX_CATALOG_BYTES",
            8,
        )
    else:
        path.unlink()
        if problem == "fifo":
            os.mkfifo(path)
        else:
            path.symlink_to(DOCUMENTS / "it_0001.md")
    with pytest.raises((OSError, ValueError)):
        glossary.load_glossary_document(ENTRIES[0])


def test_missing_files_fall_back_and_changed_original_source_is_rejected(local_catalog):
    (local_catalog / "it_0001.md").unlink()
    assert glossary.load_glossary_document(ENTRIES[0]) is None
    glossary.SOURCE_PATH.write_text('{"entries": []}')
    glossary._catalog.cache_clear()
    with pytest.raises(ValueError, match="Glossarquelle"):
        glossary.load_glossary_document(ENTRIES[0])


def test_exact_external_sources_and_internal_ids_only():
    for url in CATALOG["source_urls"]:
        assert markdown.source_url(url) == url
    for url in (
        "https://docs.python.org/private",
        "file:///etc/passwd",
        "http://docs.python.org/",
        CATALOG["source_urls"][0] + "?other=1",
    ):
        assert markdown.source_url(url) == ""
    assert glossary.linked_glossary_id("it_0002.md") == "it_0002"
    assert glossary.linked_glossary_id("it_0080.md") == "it_0080"
    assert glossary.linked_glossary_id("it_0140.md") == "it_0140"
    assert glossary.linked_glossary_id("it_0141.md") == "it_0141"
    assert glossary.linked_glossary_id("it_0190.md") == "it_0190"
    assert glossary.linked_glossary_id("it_0191.md") == "it_0191"
    assert glossary.linked_glossary_id("it_0270.md") == "it_0270"
    assert glossary.linked_glossary_id("it_0271.md") == "it_0271"
    assert glossary.linked_glossary_id("it_0302.md") == "it_0302"
    for url in (
        "../it_0002.md",
        "it_0303.md",
        "it_0002.md#x",
        "file:///it_0002.md",
        "it_0002.md?x=1",
    ):
        assert glossary.linked_glossary_id(url) == ""


def test_packaging_contains_only_index_and_catalog_documents(tmp_path, monkeypatch):
    source = (ROOT / "scripts/build_netmon_deb.sh").read_text()
    code = re.search(
        r"<<'LINUX_GLOSSARY_DOCS'\n(.*?)\nLINUX_GLOSSARY_DOCS", source, re.S
    )[1]
    subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import os\nos.umask(0o077)\n" + code,
            str(ROOT),
            str(tmp_path),
        ],
        check=True,
    )
    packaged = tmp_path / "docs/linux-glossar"
    assert {p.name for p in packaged.iterdir()} == {
        "index.json",
        *(r["document"] for r in CATALOG["records"]),
    }
    assert packaged.stat().st_mode & 0o777 == 0o755
    assert all(p.stat().st_mode & 0o777 == 0o644 for p in packaged.iterdir())
    tools = tmp_path / "tools"
    tools.mkdir()
    shutil.copyfile(glossary.SOURCE_PATH, tools / glossary.SOURCE_PATH.name)
    monkeypatch.setattr(glossary, "DOCUMENT_DIR", packaged)
    monkeypatch.setattr(glossary, "SOURCE_PATH", tools / glossary.SOURCE_PATH.name)
    for item in ENTRIES[: CATALOG["documented_records"]]:
        assert glossary.load_glossary_document(item) is not None


@pytest.fixture
def app(tmp_path):
    root = tk.Tk()
    root.geometry("1100x800")
    tree = ttk.Treeview(
        root,
        columns=("category", "source", "risk", "root", "tags", "summary", "reading"),
    )
    tree.pack(fill="both", expand=True)
    translations = json.loads((ROOT / "netmon/lang/de.json").read_text())
    app = SimpleNamespace(
        linux_help_tree=tree,
        linux_help_data=[],
        linux_help_glossary=copy.deepcopy(ENTRIES),
        linux_help_reading_state=ReadingState(tmp_path / "reading.json"),
        tr=lambda key, fallback: translations.get(key, fallback),
        linux_help_bookmarks_only_var=tk.BooleanVar(master=root),
        linux_help_status_var=tk.StringVar(master=root),
    )
    controller.rebuild_linux_help_indexes(app)
    controller.refresh_linux_help_list(app)
    yield app
    root.destroy()


def test_reader_navigation_search_copy_and_persistent_bookmark_are_passive(
    app, monkeypatch
):
    def forbidden(*args, **kwargs):
        pytest.fail("Reading started a process")

    monkeypatch.setattr(ui.subprocess, "Popen", forbidden)
    before = {
        path.name: path.read_bytes() for path in DOCUMENTS.iterdir() if path.is_file()
    }
    window = controller.open_linux_help_reader(app, command_id="it_0001")
    root = window.winfo_toplevel()
    root.update()
    reader = window.reader
    assert len(reader.headings) == 10
    assert reader.text.cget("state") == "disabled"
    assert reader.info.get() == "Algorithmus · Grundlagen · Glossarbegriff"
    assert "Root:" not in reader.info.get()
    reader.query.set("größte")
    reader.find()
    assert reader.matches
    reader.code_buttons[0].invoke()
    assert "zahlen = [7, 2, 9, 4]" in root.clipboard_get()
    assert reader.open_link("it_0002.md") is window
    root.update()
    assert reader.document.metadata["id"] == "it_0002"
    assert window.entry["id"] == "it_0002"
    assert not reader.open_link("../it_0001.md")
    window.bookmark_button.invoke()
    restored = ReadingState(app.linux_help_reading_state.path)
    assert restored.get(ENTRIES[0])["read"]
    assert restored.get(ENTRIES[1])["bookmark"]["tab"] == "documentation"
    assert "bookmark" not in restored.get(ENTRIES[0])
    assert not restored.get(dict(ENTRIES[1], entry_type="command"))["read"]
    assert {
        path.name: path.read_bytes() for path in DOCUMENTS.iterdir() if path.is_file()
    } == before


def test_reader_missing_and_broken_docs_keep_short_info(app, local_catalog):
    item = ENTRIES[-1]  # Indexed but not copied into the test fixture.
    window = controller.open_linux_help_reader(app, command_id=item["id"])
    assert window.reader.document is None
    assert window.notebook.select() == str(window.short_frame)
    assert item["name"] in window.short_info.get("1.0", "end")
    path = local_catalog / "it_0001.md"
    path.write_text("changed")
    assert controller.open_linux_help_reader(app, command_id="it_0001") is window
    assert window.reader.document is None
    assert "konnte nicht geladen" in window.reader.info.get()


def test_source_launch_occurs_only_after_explicit_click(app, monkeypatch):
    calls = []
    monkeypatch.setattr(ui.subprocess, "Popen", lambda argv, **kw: calls.append(argv))
    window = controller.open_linux_help_reader(app, command_id="it_0001")
    assert calls == []
    url = CATALOG["records"][0]["source_urls"][0]
    assert window.reader.open_link(url)
    assert calls == [["/usr/bin/xdg-open", url]]


def test_all_glossary_documents_render_and_fit_light_dark_and_narrow_windows(
    app, monkeypatch
):
    monkeypatch.setattr(
        ui.subprocess,
        "Popen",
        lambda *_a, **_k: pytest.fail("Rendering started a process"),
    )
    for item in ENTRIES[: CATALOG["documented_records"]]:
        window = controller.open_linux_help_reader(app, command_id=item["id"])
        window.update()
        document = window.reader.document
        assert document is not None, item["id"]
        assert len(window.reader.headings) == 10
        assert document.metadata["name"] == item["name"]
        assert len(window.reader.code_buttons) == sum(
            block.kind == "code" for block in document.blocks
        )
        assert window.reader.links, item["id"]
    assert window.entry["id"] == "it_0302"
    window.reader.query.set("Zyklus freigegeben")
    window.reader.find()
    assert window.reader.matches
    window.reader.code_buttons[0].invoke()
    assert "gc.collect()" in window.clipboard_get()
    assert window.reader.open_link("it_0301.md") is window
    assert window.entry["id"] == "it_0301"
    window.bookmark_button.invoke()
    restored = ReadingState(app.linux_help_reading_state.path)
    assert restored.get(ENTRIES[300])["bookmark"]["tab"] == "documentation"
    assert not restored.get(dict(ENTRIES[300], entry_type="command"))["read"]
    controller.open_linux_help_reader(app, command_id="it_0009")
    reader = window.reader
    for name, geometry, bg, fg, section in (
        ("light", "1100x850+0+0", "#f4f6f8", "#101418", 0),
        ("dark-example", "1100x850+0+0", "#111418", "#e6edf3", 5),
        ("narrow", "700x600+0+0", "#f4f6f8", "#101418", 0),
    ):
        style = ttk.Style(window)
        style.configure("TFrame", background=bg)
        style.configure("TLabel", background=bg, foreground=fg)
        window.geometry(geometry)
        window.update()
        reader.contents.current(section)
        reader.jump_to_section()
        window.update()
        assert reader.text.cget("background") == bg
        assert reader.text.winfo_width() < window.winfo_width()
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            from PIL import ImageGrab

            x, y = window.winfo_rootx(), window.winfo_rooty()
            ImageGrab.grab(
                bbox=(x, y, x + window.winfo_width(), y + window.winfo_height()),
                xdisplay=os.environ["DISPLAY"],
            ).save(f"/work/glossary-reader-{name}.png")
