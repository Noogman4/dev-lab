"""PDF generation helpers for Linux help documents."""

from __future__ import annotations

import os


def _pdf_escape(text: str) -> str:
    return (
        str(text or "")
        .replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
    )


def render_text_pdf(lines: list[str], output_path: str, *, title: str = "") -> str:
    """Render a simple multi-page text PDF without extra dependencies."""
    safe_lines = [str(line or "") for line in (lines or [""])]
    page_line_limit = 48
    pages = [
        safe_lines[idx : idx + page_line_limit]
        for idx in range(0, max(len(safe_lines), 1), page_line_limit)
    ]
    if not pages:
        pages = [[""]]

    objects: list[bytes] = []

    def add_object(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)

    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    page_ids: list[int] = []
    content_ids: list[int] = []
    pages_id_placeholder = len(objects) + 1

    for page_lines in pages:
        content_lines = ["BT", "/F1 10 Tf", "50 790 Td", "14 TL"]
        for line in page_lines:
            content_lines.append(f"({_pdf_escape(line)}) Tj")
            content_lines.append("T*")
        if title:
            content_lines.append("ET")
        else:
            content_lines.append("ET")
        stream = "\n".join(content_lines).encode("latin-1", errors="replace")
        content_id = add_object(
            b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n"
            + stream
            + b"\nendstream"
        )
        content_ids.append(content_id)
        page_id = add_object(
            (
                "<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            .encode("ascii")
        )
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids).encode("ascii")
    pages_payload = (
        b"<< /Type /Pages /Count "
        + str(len(page_ids)).encode("ascii")
        + b" /Kids [ "
        + kids
        + b" ] >>"
    )
    objects.insert(pages_id_placeholder - 1, pages_payload)
    pages_id = pages_id_placeholder

    for index, payload in enumerate(list(objects), start=1):
        if b"{pages_id}" not in payload:
            continue
        objects[index - 1] = payload.replace(b"{pages_id}", str(pages_id).encode("ascii"))

    info_parts = ["/Producer (NetMon Linux Help PDF)"]
    if title:
        info_parts.append(f"/Title ({_pdf_escape(title)})")
    info_id = add_object(
        ("<< " + " ".join(info_parts) + " >>").encode("latin-1", errors="replace")
    )
    catalog_id = add_object(
        f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii")
    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as handle:
        handle.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for index, payload in enumerate(objects, start=1):
            offsets.append(handle.tell())
            handle.write(f"{index} 0 obj\n".encode("ascii"))
            handle.write(payload)
            handle.write(b"\nendobj\n")
        xref_offset = handle.tell()
        handle.write(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        handle.write(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            handle.write(f"{offset:010d} 00000 n \n".encode("ascii"))
        trailer = (
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        )
        handle.write(trailer.encode("ascii"))
    return output_path
