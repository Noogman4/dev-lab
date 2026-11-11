"""Pure bounded JSON/XML parsers; network access belongs to radio_sandbox."""

import json
from xml.etree import ElementTree

MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 64
MAX_ITEMS = 500_000


def _check_text_size(text):
    if len(text) > MAX_RESPONSE_BYTES or len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
        raise ValueError("Dekodierte Radio-Datenbank überschreitet das Größenlimit")


def parse_directory_json(text):
    """Check nesting and item budgets before the recursive JSON decoder runs."""
    _check_text_size(text)
    depth = items = 0
    in_string = escaped = False
    for char in text:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "[{":
            depth += 1
            items += 1
            if depth > MAX_DEPTH:
                raise ValueError("Radio-JSON ist zu tief verschachtelt")
        elif char in "]}":
            depth -= 1
        elif char in ",:":
            items += 1
        if items > MAX_ITEMS:
            raise ValueError("Radio-JSON enthält zu viele Elemente")
    return json.loads(text)


class _DirectoryTreeBuilder(ElementTree.TreeBuilder):
    def __init__(self):
        super().__init__()
        self.depth = self.items = 0

    def start(self, tag, attrs):
        self.depth += 1
        self.items += 1 + len(attrs)
        if self.depth > MAX_DEPTH or self.items > MAX_ITEMS:
            raise ValueError("Radio-XML überschreitet das Strukturlimit")
        return super().start(tag, attrs)

    def end(self, tag):
        self.depth -= 1
        return super().end(tag)

    def doctype(self, name, pubid, system):
        # No DTDs are needed for station lists; reject entity expansion upfront.
        raise ValueError("DTD in Radio-XML wird nicht unterstützt")


def parse_directory_xml(text):
    _check_text_size(text)
    parser = ElementTree.XMLParser(target=_DirectoryTreeBuilder())
    return ElementTree.fromstring(text, parser=parser)
