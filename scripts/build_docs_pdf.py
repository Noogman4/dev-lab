#!/usr/bin/env python3
"""Build a compact NetMon documentation bundle as HTML and PDF."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from read_netmon_version import read_netmon_version

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
DEFAULT_VERSION = read_netmon_version()
DEFAULT_DOCS = [
    "README.md",
    "USER_GUIDE.md",
    "CONFIGURATION.md",
    "SECURITY.md",
    "ARCHITECTURE.md",
    "DEB_PACKAGING_PLAN.md",
    "CHANGELOG.md",
]


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned or "section"


def inline_format_html(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)

    def replace_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)
        return f'<a href="{html.escape(target, quote=True)}">{label}</a>'

    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, escaped)


def strip_markdown(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text


def inline_format_pdf(text: str) -> str:
    escaped = html.escape(strip_markdown(text))

    def replace_link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1))
        target = html.escape(match.group(2), quote=True)
        return f'<link href="{target}">{label}</link>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, escaped)
    escaped = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)
    return escaped


def parse_markdown_tables(
    lines: list[str], start: int
) -> tuple[list[list[str]], int] | None:
    if start + 1 >= len(lines):
        return None
    header = lines[start].strip()
    separator = lines[start + 1].strip()
    if "|" not in header or "|" not in separator:
        return None
    normalized_separator = separator.replace("|", "").replace(":", "").replace("-", "")
    if normalized_separator.strip():
        return None

    rows = [header]
    index = start + 2
    while index < len(lines) and "|" in lines[index]:
        rows.append(lines[index].strip())
        index += 1

    def split_row(row: str) -> list[str]:
        return [part.strip() for part in row.strip().strip("|").split("|")]

    return [split_row(row) for row in rows], index


def parse_markdown_blocks(
    md_text: str,
) -> tuple[list[dict], list[tuple[int, str, str]]]:
    lines = md_text.splitlines()
    blocks: list[dict] = []
    headings: list[tuple[int, str, str]] = []
    paragraph: list[str] = []
    code_lines: list[str] = []
    code_lang = ""
    in_code = False
    index = 0

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = " ".join(item.strip() for item in paragraph if item.strip())
            if text:
                blocks.append({"type": "paragraph", "text": text})
            paragraph = []

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if in_code:
            if stripped.startswith("```"):
                blocks.append(
                    {"type": "code", "text": "\n".join(code_lines), "lang": code_lang}
                )
                in_code = False
                code_lines = []
                code_lang = ""
            else:
                code_lines.append(line)
            index += 1
            continue

        table_result = parse_markdown_tables(lines, index)
        if table_result is not None:
            flush_paragraph()
            rows, next_index = table_result
            blocks.append({"type": "table", "rows": rows})
            index = next_index
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            in_code = True
            code_lang = stripped[3:].strip()
            index += 1
            continue

        if not stripped:
            flush_paragraph()
            index += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            anchor = slugify(title)
            headings.append((level, title, anchor))
            blocks.append(
                {
                    "type": "heading",
                    "level": level,
                    "text": title,
                    "anchor": anchor,
                }
            )
            index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            blocks.append({"type": "quote", "text": stripped.lstrip(">").strip()})
            index += 1
            continue

        ordered_match = re.match(r"^\d+\.\s+(.*)$", stripped)
        unordered_match = re.match(r"^[-*]\s+(.*)$", stripped)
        if ordered_match or unordered_match:
            flush_paragraph()
            list_type = "ol" if ordered_match else "ul"
            items = []
            while index < len(lines):
                current = lines[index].strip()
                current_ordered = re.match(r"^\d+\.\s+(.*)$", current)
                current_unordered = re.match(r"^[-*]\s+(.*)$", current)
                if list_type == "ol" and current_ordered:
                    items.append(current_ordered.group(1).strip())
                    index += 1
                    continue
                if list_type == "ul" and current_unordered:
                    items.append(current_unordered.group(1).strip())
                    index += 1
                    continue
                break
            blocks.append({"type": "list", "list_type": list_type, "items": items})
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return blocks, headings


def blocks_to_html(blocks: list[dict]) -> str:
    parts: list[str] = []
    for block in blocks:
        block_type = block["type"]
        if block_type == "heading":
            level = block["level"]
            parts.append(
                f'<h{level} id="{block["anchor"]}">{inline_format_html(block["text"])}</h{level}>'
            )
        elif block_type == "paragraph":
            parts.append(f'<p>{inline_format_html(block["text"])}</p>')
        elif block_type == "quote":
            parts.append(
                f'<blockquote><p>{inline_format_html(block["text"])}</p></blockquote>'
            )
        elif block_type == "code":
            parts.append(f"<pre><code>{html.escape(block['text'])}</code></pre>")
        elif block_type == "list":
            tag = "ol" if block["list_type"] == "ol" else "ul"
            parts.append(f"<{tag}>")
            for item in block["items"]:
                parts.append(f"<li>{inline_format_html(item)}</li>")
            parts.append(f"</{tag}>")
        elif block_type == "table":
            rows = block["rows"]
            parts.append("<table><thead><tr>")
            for cell in rows[0]:
                parts.append(f"<th>{inline_format_html(cell)}</th>")
            parts.append("</tr></thead><tbody>")
            for row in rows[1:]:
                parts.append("<tr>")
                for cell in row:
                    parts.append(f"<td>{inline_format_html(cell)}</td>")
                parts.append("</tr>")
            parts.append("</tbody></table>")
    return "\n".join(parts)


def build_toc_html(
    document_sections: list[tuple[str, str, list[tuple[int, str, str]]]],
) -> str:
    parts = ['<div class="toc"><h1 id="inhaltsverzeichnis">Inhaltsverzeichnis</h1>']
    for file_title, section_anchor, headings in document_sections:
        parts.append('<div class="toc-section">')
        parts.append(
            f'<p class="toc-file"><a href="#{section_anchor}">{inline_format_html(file_title)}</a></p>'
        )
        if headings:
            parts.append("<ul>")
            for level, title, anchor in headings:
                parts.append(
                    f'<li class="toc-level-{level}"><a href="#{anchor}">{inline_format_html(title)}</a></li>'
                )
            parts.append("</ul>")
        parts.append("</div>")
    parts.append("</div>")
    return "\n".join(parts)


def html_document(title: str, toc_html: str, body_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)}</title>
  <style>
    @page {{ size: A4; margin: 18mm 16mm; }}
    body {{ font-family: Liberation Sans, Arial, sans-serif; font-size: 10.5pt; line-height: 1.45; color: #202124; }}
    h1, h2, h3, h4 {{ color: #16263a; page-break-after: avoid; }}
    h1 {{ font-size: 20pt; border-bottom: 1px solid #c8d3df; padding-bottom: 4px; margin-top: 24px; }}
    h2 {{ font-size: 15pt; margin-top: 18px; }}
    h3 {{ font-size: 12.5pt; margin-top: 14px; }}
    a {{ color: #0b57d0; text-decoration: none; }}
    code, pre {{ font-family: Liberation Mono, monospace; font-size: 9.5pt; }}
    pre {{ background: #f5f7f9; border: 1px solid #d9e1e7; padding: 10px; white-space: pre-wrap; }}
    table {{ width: 100%; border-collapse: collapse; margin: 10px 0 14px 0; }}
    th, td {{ border: 1px solid #d9e1e7; padding: 6px 8px; vertical-align: top; text-align: left; }}
    th {{ background: #eef3f7; }}
    blockquote {{ margin: 10px 0; padding: 2px 12px; border-left: 3px solid #9db5cc; background: #f8fbfd; }}
    .title-page {{ page-break-after: always; }}
    .toc {{ page-break-after: always; }}
    .toc ul {{ list-style: none; padding-left: 0; }}
    .toc-file {{ font-weight: bold; margin: 10px 0 4px; }}
    .toc-level-1 {{ margin-left: 0; }}
    .toc-level-2 {{ margin-left: 14px; }}
    .toc-level-3 {{ margin-left: 28px; }}
    .toc-level-4 {{ margin-left: 42px; }}
    .doc-section {{ page-break-before: always; }}
    .doc-meta {{ color: #5f6368; font-size: 9.5pt; margin-bottom: 16px; }}
  </style>
</head>
<body>
  <section class="title-page">
    <h1>NetMon Dokumentation</h1>
    <p>Version: {html.escape(title)}</p>
    <p>Kompakte Zusammenstellung der zentralen Projekt- und Nutzerdokumentation.</p>
  </section>
  {toc_html}
  {body_html}
</body>
</html>"""


def build_bundle(
    version: str, doc_names: list[str], output_dir: Path
) -> tuple[Path, Path, list[dict]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    title = f"NetMon Dokumentation {version}"
    sections = []
    toc_sections = []

    for doc_name in doc_names:
        path = DOCS_DIR / doc_name
        text = path.read_text(encoding="utf-8")
        blocks, headings = parse_markdown_blocks(text)
        file_title = doc_name.replace(".md", "").replace("_", " ")
        section_anchor = f"doc-{slugify(doc_name)}"
        toc_sections.append((file_title, section_anchor, headings))
        sections.append(
            {
                "doc_name": doc_name,
                "file_title": file_title,
                "section_anchor": section_anchor,
                "headings": headings,
                "blocks": blocks,
            }
        )

    toc_html = build_toc_html(toc_sections)
    body_html_parts = []
    for section in sections:
        body_html_parts.append(
            f'<section class="doc-section"><h1 id="{section["section_anchor"]}">{inline_format_html(section["file_title"])}</h1>'
            f'<p class="doc-meta">Quelle: docs/{html.escape(section["doc_name"])}</p>'
            f'{blocks_to_html(section["blocks"])}</section>'
        )
    html_text = html_document(title, toc_html, "\n".join(body_html_parts))

    html_path = output_dir / f"netmon_dokumentation_{version}.html"
    pdf_path = output_dir / f"netmon_dokumentation_{version}.pdf"
    html_path.write_text(html_text, encoding="utf-8")
    return html_path, pdf_path, sections


def build_pdf(
    version: str,
    sections: list[dict],
    pdf_path: Path,
    *,
    document_title: str = "NetMon Dokumentation",
    document_subtitle: str = (
        "Kompakte Zusammenstellung der zentralen Projekt- und Nutzerdokumentation."
    ),
) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            PageBreak,
            Paragraph,
            Preformatted,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "reportlab ist nicht installiert. Installiere es z. B. mit "
            "`python3 -m pip install --target /tmp/netmon_docs_pdf_tools reportlab` "
            "und setze PYTHONPATH entsprechend."
        ) from exc

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"{document_title} {version}",
        author="NetMon",
    )

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="NetMonBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            spaceAfter=8,
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#16263a"),
            spaceBefore=12,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#16263a"),
            spaceBefore=10,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonH3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#16263a"),
            spaceBefore=8,
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonCode",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=10.5,
            backColor=colors.HexColor("#f5f7f9"),
            borderColor=colors.HexColor("#d9e1e7"),
            borderWidth=0.5,
            borderPadding=6,
            borderRadius=1,
            spaceAfter=10,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonQuote",
            parent=styles["BodyText"],
            leftIndent=10,
            borderColor=colors.HexColor("#9db5cc"),
            borderWidth=0.5,
            borderPadding=6,
            backColor=colors.HexColor("#f8fbfd"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NetMonSmall",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=colors.HexColor("#5f6368"),
            spaceAfter=8,
        )
    )

    story = [
        Paragraph(html.escape(document_title), styles["NetMonH1"]),
        Spacer(1, 6),
        Paragraph(f"Version: {html.escape(version)}", styles["NetMonBody"]),
        Paragraph(
            html.escape(document_subtitle),
            styles["NetMonBody"],
        ),
        PageBreak(),
        Paragraph(
            '<a name="inhaltsverzeichnis"/>Inhaltsverzeichnis', styles["NetMonH1"]
        ),
    ]

    for section in sections:
        story.append(
            Paragraph(
                f'<link href="#{section["section_anchor"]}"><b>{html.escape(section["file_title"])}</b></link>',
                styles["NetMonBody"],
            )
        )
        for level, title, anchor in section["headings"]:
            indent = max(0, level - 1) * 12
            toc_style = ParagraphStyle(
                f"TOC_{anchor}",
                parent=styles["NetMonSmall"],
                leftIndent=indent,
            )
            story.append(
                Paragraph(
                    f'<link href="#{anchor}">{html.escape(title)}</link>',
                    toc_style,
                )
            )

    for section in sections:
        story.append(PageBreak())
        story.append(
            Paragraph(
                f'<a name="{section["section_anchor"]}"/>{html.escape(section["file_title"])}',
                styles["NetMonH1"],
            )
        )
        story.append(
            Paragraph(
                f"Quelle: docs/{html.escape(section['doc_name'])}",
                styles["NetMonSmall"],
            )
        )

        for block in section["blocks"]:
            block_type = block["type"]
            if block_type == "heading":
                heading_style = styles["NetMonH3"]
                if block["level"] == 1:
                    heading_style = styles["NetMonH1"]
                elif block["level"] == 2:
                    heading_style = styles["NetMonH2"]
                story.append(
                    Paragraph(
                        f'<a name="{block["anchor"]}"/>{inline_format_pdf(block["text"])}',
                        heading_style,
                    )
                )
            elif block_type == "paragraph":
                story.append(
                    Paragraph(inline_format_pdf(block["text"]), styles["NetMonBody"])
                )
            elif block_type == "quote":
                story.append(
                    Paragraph(inline_format_pdf(block["text"]), styles["NetMonQuote"])
                )
            elif block_type == "code":
                story.append(Preformatted(block["text"], styles["NetMonCode"]))
            elif block_type == "list":
                for idx, item in enumerate(block["items"], start=1):
                    prefix = f"{idx}. " if block["list_type"] == "ol" else "• "
                    story.append(
                        Paragraph(
                            f"{prefix}{inline_format_pdf(item)}",
                            ParagraphStyle(
                                f"List_{section['section_anchor']}_{idx}_{block['list_type']}",
                                parent=styles["NetMonBody"],
                                leftIndent=12,
                                firstLineIndent=-8,
                            ),
                        )
                    )
            elif block_type == "table":
                rows = [
                    [
                        Paragraph(inline_format_pdf(cell), styles["NetMonSmall"])
                        for cell in row
                    ]
                    for row in block["rows"]
                ]
                table = Table(rows, repeatRows=1)
                table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef3f7")),
                            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e1e7")),
                            (
                                "INNERGRID",
                                (0, 0),
                                (-1, -1),
                                0.5,
                                colors.HexColor("#d9e1e7"),
                            ),
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 6),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                story.append(table)
                story.append(Spacer(1, 8))

    doc.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=DEFAULT_VERSION)
    parser.add_argument("--docs", nargs="*", default=DEFAULT_DOCS)
    parser.add_argument("--output-dir", default=str(ROOT / "dist" / "docs"))
    args = parser.parse_args()

    output_dir = Path(args.output_dir).resolve()
    html_path, pdf_path, sections = build_bundle(args.version, args.docs, output_dir)
    build_pdf(args.version, sections, pdf_path)
    print(f"HTML: {html_path}")
    print(f"PDF: {pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
