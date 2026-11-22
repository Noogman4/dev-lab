"""Fixed, hash-verified glossary documents; personal entries cannot supply paths."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

try:
    from netmon.services import linux_help_markdown_service as markdown
except ModuleNotFoundError:
    from services import linux_help_markdown_service as markdown

ROOT = Path(__file__).resolve().parents[2]
DOCUMENT_DIR = ROOT / "docs/linux-glossar"
SOURCE_PATH = ROOT / "tools/it_lexikon_linux_hilfe.json"
SOURCE_SHA256 = "b3fb9bfe37d335ee6eaa89c89425f08c94e8efc6f698e7c520ffc81ed128fc24"


@lru_cache(maxsize=4)
def _catalog(directory, source_path):
    raw = markdown._read_regular(Path(source_path), markdown.MAX_CATALOG_BYTES)
    if hashlib.sha256(raw).hexdigest() != SOURCE_SHA256:
        raise ValueError("Glossarquelle stimmt nicht mit dem Katalog überein.")
    source = json.loads(raw.decode("utf-8"))
    entries = source.get("entries") if isinstance(source, dict) else None
    if (
        not isinstance(entries, list)
        or len(entries) != 302
        or any(not isinstance(item, dict) for item in entries)
    ):
        raise ValueError("Ungültige Glossarquelle.")
    if len({item.get("id") for item in entries}) != 302:
        raise ValueError("Mehrdeutige Glossarquelle.")
    catalog = json.loads(
        markdown._read_regular(
            Path(directory) / "index.json", markdown.MAX_CATALOG_BYTES
        ).decode("utf-8")
    )
    if (
        not isinstance(catalog, dict)
        or type(catalog.get("schema_version")) is not int
        or catalog.get("schema_version") != 1
        or catalog.get("kind") != "glossary"
        or catalog.get("source_sha256") != SOURCE_SHA256
        or catalog.get("source_catalog") != "tools/it_lexikon_linux_hilfe.json"
        or type(catalog.get("total_records")) is not int
        or catalog["total_records"] != 302
        or type(catalog.get("documented_records")) is not int
        or not 1 <= catalog["documented_records"] <= 302
        or not isinstance(catalog.get("records"), list)
        or len(catalog["records"]) != catalog["documented_records"]
    ):
        raise ValueError("Ungültiger Glossarkatalog.")
    records = {}
    urls = set()
    for number, record in enumerate(catalog["records"], 1):
        original = entries[number - 1]
        category = original.get("category") or (
            original["tags"][0].title() if original.get("tags") else "Glossary"
        )
        if (
            not isinstance(record, dict)
            or type(record.get("source_record")) is not int
            or record["source_record"] != number
            or record.get("source") != original
            or record.get("id") != original["id"]
            or record.get("term") != original["term"]
            or record.get("category") != category
            or record.get("document") != original["id"] + ".md"
            or not isinstance(record.get("sha256"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"])
            or record.get("status") not in ("review_pending", "reviewed")
        ):
            raise ValueError("Ungültige Glossarzuordnung.")
        sources = record.get("source_urls")
        if (
            not isinstance(sources, list)
            or len(sources) > 64
            or any(not markdown._https_url(url) for url in sources)
        ):
            raise ValueError("Ungültige Glossarquellen.")
        urls.update(sources)
        records[record["id"]] = record
    if catalog.get("source_urls") != sorted(urls):
        raise ValueError("Glossarquellen passen nicht zum Katalog.")
    return records, frozenset(urls)


def catalog():
    return _catalog(str(DOCUMENT_DIR), str(SOURCE_PATH))


def load_glossary_document(item):
    if (
        not isinstance(item, dict)
        or item.get("entry_type") != "glossary"
        or not all(isinstance(item.get(key), str) for key in ("id", "name"))
        or item.get("cmd", "") != ""
    ):
        return None
    try:
        records, _sources = catalog()
    except FileNotFoundError:
        return None
    record = records.get(item["id"])
    if record is None or item["name"] != record["term"]:
        return None
    try:
        raw = markdown._read_regular(
            DOCUMENT_DIR / record["document"], markdown.MAX_BYTES
        )
    except FileNotFoundError:
        return None
    if hashlib.sha256(raw).hexdigest() != record["sha256"]:
        raise ValueError("Glossardokument stimmt nicht mit dem Katalog überein.")
    document = markdown.parse_glossary_document(raw.decode("utf-8-sig"))
    expected = {
        "id": record["id"],
        "name": record["term"],
        "category": record["category"],
        "source_record": record["source_record"],
        "tags": record["source"]["tags"],
        "related": record["source"]["related"],
        "status": record["status"],
    }
    if any(document.metadata.get(key) != value for key, value in expected.items()):
        raise ValueError("Glossardokument passt nicht zum Begriff.")
    return document


def linked_glossary_id(url):
    if not isinstance(url, str) or not re.fullmatch(r"it_\d{4}\.md", url):
        return ""
    records, _sources = catalog()
    identifier = url[:-3]
    return identifier if identifier in records else ""
