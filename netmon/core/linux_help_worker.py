"""Disposable CSV/XLSX parser and command normalizer, with OS resource limits."""

import io
import json
from pathlib import Path
import re
import sys
import tempfile
import zipfile

MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_REPLY_BYTES = 16 * 1024 * 1024
MAX_MEMORY_BYTES = 512 * 1024 * 1024
MAX_CPU_SECONDS = 4
MAX_WALL_SECONDS = 8
MAX_XML_NODES = 500_000
MAX_XML_DEPTH = 64


def apply_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, MAX_MEMORY_BYTES),
        (resource.RLIMIT_CPU, MAX_CPU_SECONDS),
        (resource.RLIMIT_FSIZE, MAX_REPLY_BYTES),
        (resource.RLIMIT_NOFILE, 64),
        (resource.RLIMIT_NPROC, 0),
        (resource.RLIMIT_CORE, 0),
    ):
        soft, hard = resource.getrlimit(name)
        bound = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (bound, bound))


def check_xlsx_xml(payload, *, rows, columns):
    from lxml import etree

    def coordinate(value):
        match = re.fullmatch(r"([A-Z]{1,3})([1-9][0-9]{0,6})", value)
        if not match:
            raise ValueError("Invalid worksheet coordinate")
        column = 0
        for char in match[1]:
            column = column * 26 + ord(char) - ord("A") + 1
        if column > columns or int(match[2]) > rows + 1:
            raise ValueError("Import: XLSX-Zeilen-/Spaltengrenze ueberschritten.")

    nodes = 0
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
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
            worksheet = member.filename.startswith("xl/worksheets/")
            depth = 0
            worksheet_rows = column = cells_in_row = 0
            with archive.open(member) as source:
                while chunk := source.read(4096):
                    parser.feed(chunk)
                    for event, element in parser.read_events():
                        if event == "start":
                            nodes += 1
                            depth += 1
                            if nodes > MAX_XML_NODES or depth > MAX_XML_DEPTH:
                                raise ValueError(
                                    "Import: XML-Strukturgrenze ueberschritten."
                                )
                            if worksheet:
                                if element.tag.endswith("}row"):
                                    worksheet_rows += 1
                                    row = element.get("r", str(worksheet_rows))
                                    if (
                                        not re.fullmatch(r"[1-9][0-9]{0,6}", row)
                                        or int(row) > rows + 1
                                        or worksheet_rows > rows + 1
                                    ):
                                        raise ValueError(
                                            "Import: XLSX-Zeilengrenze ueberschritten."
                                        )
                                    column = cells_in_row = 0
                                elif element.tag.endswith("}c"):
                                    cells_in_row += 1
                                    reference = element.get("r")
                                    if reference:
                                        coordinate(reference)
                                        column = 0
                                        for char in re.match(r"[A-Z]+", reference)[0]:
                                            column = (
                                                column * 26 + ord(char) - ord("A") + 1
                                            )
                                    else:
                                        column += 1
                                    if column > columns or cells_in_row > columns:
                                        raise ValueError(
                                            "Import: XLSX-Spaltengrenze ueberschritten."
                                        )
                                elif element.tag.endswith("}dimension"):
                                    for value in element.get("ref", "").split(":"):
                                        coordinate(value)
                        else:
                            depth -= 1
                            element.clear()
            root = parser.close()
            if root.getroottree().docinfo.doctype:
                raise ValueError("Import: XML-Dokumenttypen sind nicht erlaubt.")


def parse(payload, kind, requested):
    # Fixed trusted source tree, never the selected file's directory/PYTHONPATH.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from netmon.features import linux_help_controller as controller

    expected = {
        "MAX_SOURCE_CSV_BYTES",
        "MAX_SOURCE_ROWS",
        "MAX_SOURCE_COLUMNS",
        "MAX_SOURCE_CELL_CHARS",
        "MAX_SOURCE_CELLS",
        "MAX_SOURCE_TEXT_CHARS",
    }
    if set(requested) != expected or kind not in {".csv", ".xlsx"}:
        raise ValueError("Invalid import request")
    for name, value in requested.items():
        if type(value) is not int or not 0 < value <= getattr(controller, name):
            raise ValueError("Invalid import limit")
        setattr(controller, name, value)
    if kind == ".xlsx":
        check_xlsx_xml(
            payload,
            rows=controller.MAX_SOURCE_ROWS,
            columns=controller.MAX_SOURCE_COLUMNS,
        )
    import csv

    csv.field_size_limit(controller.MAX_SOURCE_CELL_CHARS)
    with tempfile.NamedTemporaryFile(suffix=kind) as source:
        source.write(payload)
        source.flush()
        commands = controller._load_linux_help_commands(source.name, isolated=False)
    total = 0
    for command in commands:
        for value in command.values():
            if isinstance(value, str):
                if len(value) > controller.MAX_SOURCE_CELL_CHARS + 16:
                    raise ValueError("Import: Normalisierte Zelle ist zu gross.")
                total += len(value)
                if total > controller.MAX_SOURCE_TEXT_CHARS:
                    raise ValueError("Import: Normalisierte Textgrenze ueberschritten.")
    return commands


def main():
    try:
        apply_limits()
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not 0 < len(payload) <= MAX_INPUT_BYTES:
            raise ValueError("Import: Eingabegroessenlimit ueberschritten.")
        result = {"commands": parse(payload, sys.argv[1], json.loads(sys.argv[2]))}
    except Exception as exc:
        # Only fixed budget diagnostics can be returned; parser exceptions may
        # contain imported text. No tracebacks or document text reach stderr.
        detail = str(exc)
        result = {
            "error": (
                detail
                if detail.startswith("Import:")
                else "Import: Parserfehler oder Ressourcenlimit."
            )
        }
    reply = json.dumps(result, ensure_ascii=True).encode("ascii")
    if len(reply) > MAX_REPLY_BYTES:
        return 1
    sys.stdout.buffer.write(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
