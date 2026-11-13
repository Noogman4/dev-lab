#!/usr/bin/env python3
"""Generate the Round 13 (large) security audit PDF from its Markdown report."""

from __future__ import annotations

from build_docs_pdf import build_pdf, parse_markdown_blocks, slugify
from read_netmon_version import ROOT, read_netmon_version

REPORT_PATH = ROOT / "docs" / "SECURITY_AUDIT_2026_R13.md"
OUTPUT_PATH = ROOT / "site" / "netmon_security_audit_2026_r13.pdf"


def main() -> int:
    version = read_netmon_version()
    blocks, headings = parse_markdown_blocks(REPORT_PATH.read_text(encoding="utf-8"))
    file_title = "NetMon Security Audit 2026 - Runde 13"
    sections = [
        {
            "doc_name": REPORT_PATH.name,
            "file_title": file_title,
            "section_anchor": slugify(file_title),
            "headings": headings,
            "blocks": blocks,
        }
    ]
    build_pdf(
        version,
        sections,
        OUTPUT_PATH,
        document_title=file_title,
        document_subtitle=(
            "Großes Security-Audit: 85 Findings, Vorgehensweise, Fixes und "
            "Verifikation für NetMon Roots."
        ),
    )
    print(f"PDF: {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
