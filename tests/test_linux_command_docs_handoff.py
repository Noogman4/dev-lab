"""Frozen handoff and parser boundaries; no GUI, network or example execution."""

import json
import shutil

import pytest

from netmon.services import linux_help_markdown_service as markdown
from scripts import check_linux_command_docs as checks

CATALOG = checks.load_catalog()
DRAFTS = checks.ROOT / checks.BASE / "browser-codex/entwuerfe-201-210"


@pytest.mark.parametrize("record", CATALOG["records"][:10], ids=lambda r: r["id"])
def test_original_drafts_have_valid_structure_despite_known_content_errors(record):
    result = checks.check_document(DRAFTS / record["document"], record, CATALOG)
    assert result["format"] == "ok"


def test_original_return_files_match_provenance():
    import hashlib

    provenance = json.loads(
        (DRAFTS.parent / "HERKUNFT-201-210.json").read_text(encoding="utf-8")
    )
    for name, expected in provenance["files"].items():
        assert hashlib.sha256((DRAFTS / name).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("name", ["7z.md", "tar.md"])
def test_shared_style_examples_fit_actual_parser(name):
    document = markdown.parse_document(
        (checks.ROOT / checks.BASE / name).read_text(encoding="utf-8")
    )
    assert (
        tuple(b.text for b in document.blocks if b.kind == "heading" and b.level == 2)
        == checks.HEADINGS
    )


def test_changed_source_catalog_is_rejected(tmp_path):
    target = tmp_path / checks.CATALOG
    target.parent.mkdir(parents=True)
    shutil.copyfile(checks.ROOT / checks.CATALOG, target)
    source = tmp_path / CATALOG["source_catalog"]
    source.parent.mkdir(parents=True)
    source.write_text("different source", encoding="utf-8")
    with pytest.raises(ValueError, match="Original-CSV"):
        checks.load_catalog(tmp_path)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ('id: "touch"', 'id: "tree"'),
        ("source_record: 201", "source_record: 202"),
        ('language: "de"', 'language: "en"'),
        ('risk_level: "caution"', 'risk_level: "anything"'),
        ("## 3. Syntax", "## 3. Platzhalter"),
        ('reviewed_at: "2026-11-13"', 'reviewed_at: "2026-13-99"'),
    ],
)
def test_wrong_mapping_or_required_structure_is_rejected(tmp_path, before, after):
    text = (DRAFTS / "touch.md").read_text(encoding="utf-8")
    assert before in text
    candidate = tmp_path / "touch.md"
    candidate.write_text(text.replace(before, after), encoding="utf-8")
    with pytest.raises(ValueError):
        checks.check_document(candidate, CATALOG["records"][0], CATALOG)


@pytest.mark.parametrize("suffix", ["\x00", "\n```bash\nunclosed", "x" * 262145])
def test_invalid_or_oversized_document_is_rejected(suffix):
    text = (DRAFTS / "touch.md").read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        markdown.parse_document(text + suffix)


def test_unrecognized_markup_stays_passive():
    text = (DRAFTS / "touch.md").read_text(encoding="utf-8")
    payload = "<script>run()</script>"
    parsed = markdown.parse_document(text + "\n" + payload + "\n")
    assert parsed.blocks[-1] == markdown.Block("text", payload)


@pytest.mark.parametrize(
    "url",
    [
        "http://www.7-zip.org/",
        "https://127.0.0.1/",
        "https://evil.example\\@www.7-zip.org/",
        "https://www.7-zip.org:999/",
        "https://user@www.7-zip.org/",
        "https://www.7-zip.org:/",
        "https://www.7-zip.org/\n",
    ],
)
def test_handoff_does_not_expand_reader_browser_authority(url):
    assert markdown.source_url(url) == ""
