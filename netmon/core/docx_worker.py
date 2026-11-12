"""Disposable DOCX parser. Limits are applied before importing document parsers."""

import io
import json
import sys
import zipfile

MAX_INPUT_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 120_000
MAX_REPLY_BYTES = 1024 * 1024
MAX_XML_NODES = 100_000
MAX_XML_DEPTH = 64
MAX_MEMORY_BYTES = 512 * 1024 * 1024
MAX_CPU_SECONDS = 4
MAX_WALL_SECONDS = 8
_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def apply_process_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, MAX_MEMORY_BYTES),
        (resource.RLIMIT_CPU, MAX_CPU_SECONDS),
        (resource.RLIMIT_NOFILE, 32),
        (resource.RLIMIT_NPROC, 0),
        (resource.RLIMIT_FSIZE, MAX_REPLY_BYTES),
        (resource.RLIMIT_CORE, 0),
    ):
        soft, hard = resource.getrlimit(name)
        bound = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (bound, bound))


def check_xml_structure(snapshot):
    from lxml import etree

    nodes = 0
    with zipfile.ZipFile(snapshot) as archive:
        for member in archive.infolist():
            if not member.filename.endswith((".xml", ".rels")):
                continue
            parser = etree.XMLPullParser(
                events=("start", "end"),
                resolve_entities=False,
                load_dtd=False,
                no_network=True,
                huge_tree=False,
            )
            depth = 0
            with archive.open(member) as source:
                while chunk := source.read(4096):
                    parser.feed(chunk)
                    for event, element in parser.read_events():
                        if event == "start":
                            nodes += 1
                            depth += 1
                            if nodes > MAX_XML_NODES or depth > MAX_XML_DEPTH:
                                raise ValueError("DOCX XML structure exceeds limits.")
                            if element.tag == _W + "gridSpan":
                                span = element.get(_W + "val", "1")
                                if (
                                    not span.isascii()
                                    or not span.isdecimal()
                                    or not 1 <= int(span) <= 128
                                ):
                                    raise ValueError("DOCX table span exceeds limits.")
                        else:
                            depth -= 1
                            element.clear()
            root = parser.close()
            if root.getroottree().docinfo.doctype:
                raise ValueError("DOCX document types/entities are not allowed.")
    snapshot.seek(0)


def extract_bounded_text(document):
    """Append only remaining characters; never materialize row.cells/grid spans."""
    parts = []
    length = 0
    truncated = False

    def append(text):
        nonlocal length, truncated
        available = MAX_TEXT_CHARS - length
        parts.append(text[:available])
        length += min(available, len(text))
        if len(text) > available:
            truncated = True
        return length < MAX_TEXT_CHARS

    def paragraph_text(paragraph):
        available = MAX_TEXT_CHARS - length
        fragments = []
        for node in paragraph.iter():
            text = (
                (node.text or "")
                if node.tag == _W + "t"
                else (
                    "\t"
                    if node.tag == _W + "tab"
                    else "\n" if node.tag in {_W + "br", _W + "cr"} else ""
                )
            )
            if len(text) > available:
                fragments.append(text[:available])
                return "".join(fragments), True
            fragments.append(text)
            available -= len(text)
        return "".join(fragments).strip(), False

    body = document.element.body
    for paragraph in body.iterchildren(_W + "p"):
        text, clipped = paragraph_text(paragraph)
        if text:
            if parts and not append("\n"):
                return "".join(parts), True
            if not append(text) or clipped:
                return "".join(parts), True
    for table in body.iterchildren(_W + "tbl"):
        for row in table.iterchildren(_W + "tr"):
            if not any((node.text or "").strip() for node in row.iter(_W + "t")):
                continue
            if parts and not append("\n"):
                return "".join(parts), True
            first_cell = True
            for cell in row.iterchildren(_W + "tc"):
                if not first_cell and not append(" | "):
                    return "".join(parts), True
                first_cell = False
                first_paragraph = True
                for paragraph in cell.iterchildren(_W + "p"):
                    if not first_paragraph and not append("\n"):
                        return "".join(parts), True
                    first_paragraph = False
                    text, clipped = paragraph_text(paragraph)
                    if not append(text) or clipped:
                        return "".join(parts), True
    return "".join(parts).strip(), truncated


def parse_snapshot(payload):
    if not 0 < len(payload) <= MAX_INPUT_BYTES:
        raise ValueError("DOCX compressed size exceeds limit.")
    snapshot = io.BytesIO(payload)
    check_xml_structure(snapshot)
    import docx

    document = docx.Document(snapshot)
    text, truncated = extract_bounded_text(document)
    return {"text": text, "truncated": truncated}


def main():
    try:
        apply_process_limits()
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        result = parse_snapshot(payload)
        reply = json.dumps(result, ensure_ascii=True).encode("ascii")
        if len(reply) > MAX_REPLY_BYTES:
            raise ValueError("DOCX parser reply exceeds limit.")
        sys.stdout.buffer.write(reply)
        return 0
    except Exception:
        # Errors are intentionally short and contain no imported document text.
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
