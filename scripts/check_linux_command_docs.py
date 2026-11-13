"""Check document structure and frozen mapping, never execute shell examples."""

from __future__ import annotations

import argparse
import csv
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from netmon.services.linux_help_markdown_service import parse_document  # noqa: E402

BASE = Path("docs/linux-befehlsdatenbank")
CATALOG = BASE / "browser-codex/KATALOG-201-300.json"
HEADINGS = (
    "1. Kurzbeschreibung",
    "2. Was macht der Befehl?",
    "3. Syntax",
    "4. Wichtige Optionen",
    "5. Beispiel erklärt Schritt für Schritt",
    "6. Typische Anwendungsfälle",
    "7. Risiken, Nebenwirkungen und Vorsicht",
    "8. Häufige Fehler",
    "9. Sichere Varianten oder Tipps für Einsteiger",
    "10. Verwandte Befehle",
)


def load_catalog(root=ROOT):
    """Verify the frozen 201–300 mapping against the byte-identical source CSV."""
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    raw = (root / catalog["source_catalog"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != catalog["source_sha256"]:
        raise ValueError("Die Original-CSV hat sich gegenüber der Übergabe geändert.")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    records = catalog["records"]
    if len(rows) != catalog["total_records"] or [
        item["source_record"] for item in records
    ] != list(range(201, 301)):
        raise ValueError("Unvollständiger oder abweichender Katalogbereich.")
    for item in records:
        if rows[item["source_record"] - 1] != item["source"]:
            raise ValueError(f"Originaldatensatz weicht ab: {item['source_record']}")
        if Path(item["document"]).name != item["document"] or not item[
            "document"
        ].endswith(".md"):
            raise ValueError("Ungültiger Dokumentdateiname im Katalog.")
    if len({item["document"] for item in records}) != len(records):
        raise ValueError("Doppelte Dokumentdateinamen im Katalog.")
    return catalog


def check_document(path, record, catalog):
    """Return format evidence; this does not verify meaning, links or examples."""
    with path.open("rb") as handle:
        raw = handle.read(256 * 1024 + 1)
    document = parse_document(raw.decode("utf-8-sig"))
    metadata = document.metadata
    for key in ("id", "name", "category", "source_record"):
        if metadata.get(key) != record[key]:
            raise ValueError(f"Falsche Zuordnung für {key}: {path.name}")
    if metadata.get("source_catalog") != catalog["source_catalog"]:
        raise ValueError("Abweichende Originalquelle im Dokumentkopf.")
    if metadata.get("language") != "de":
        raise ValueError("Dokumentsprache muss de sein.")
    if not isinstance(metadata.get("tags"), list) or not all(
        isinstance(tag, str) and tag.strip() for tag in metadata["tags"]
    ):
        raise ValueError("Tags müssen eine Liste nichtleerer Zeichenketten sein.")
    for key in ("status", "locally_checked_version", "reviewed_at"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError(f"Prüfstand fehlt: {key}")
    if (
        date.fromisoformat(metadata["reviewed_at"]).isoformat()
        != metadata["reviewed_at"]
    ):
        raise ValueError("reviewed_at benötigt YYYY-MM-DD.")
    headings = tuple(
        block.text
        for block in document.blocks
        if block.kind == "heading" and block.level == 2
    )
    if headings != HEADINGS:
        raise ValueError("Die zehn Hauptabschnitte fehlen oder weichen ab.")
    return {"source_record": record["source_record"], "file": path.name, "format": "ok"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--documents",
        type=Path,
        default=BASE / "browser-codex/entwuerfe-201-210",
    )
    parser.add_argument("--first", type=int, default=201)
    parser.add_argument("--last", type=int, default=210)
    args = parser.parse_args()
    if not 201 <= args.first <= args.last <= 300:
        parser.error("Prüfbereich muss innerhalb 201–300 liegen.")
    results = []
    try:
        catalog = load_catalog()
        directory = ROOT / args.documents
        for record in catalog["records"]:
            if args.first <= record["source_record"] <= args.last:
                results.append(
                    check_document(directory / record["document"], record, catalog)
                )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"format": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    print(
        json.dumps(
            {
                "format": "ok",
                "documents": results,
                "limitation": "Keine fachliche, Quellen-, GUI- oder Beispielprüfung.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
