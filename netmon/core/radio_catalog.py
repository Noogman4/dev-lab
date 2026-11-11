"""Catalog parsing in the source process and strict validation of its reply."""

import io
import json

MAX_BODY_BYTES = 16 * 1024 * 1024
MAX_REPLY_BYTES = 16 * 1024 * 1024
MAX_ROWS = 50_000
MAX_IMPORT_BYTES = 32 * 1024 * 1024
# RC-01: one bad upstream row (e.g. 79 tags) must not discard 5000 good ones.
# Bounded tolerance: more skipped than kept, or more than this, still fails.
MAX_SKIPPED_ROWS = 100
FIELDS = (
    "name",
    "url",
    "url_resolved",
    "homepage",
    "favicon",
    "tags",
    "country",
    "countrycode",
    "language",
    "codec",
    "bitrate",
    "lastcheckok",
    "votes",
    "clickcount",
)
TEXT_LIMITS = {
    "name": 512,
    "url": 8192,
    "url_resolved": 8192,
    "homepage": 8192,
    "favicon": 8192,
    "country": 256,
    "countrycode": 16,
    "language": 512,
    "codec": 128,
}
NUMBER_FIELDS = {"bitrate", "votes", "clickcount"}


def _text(value, limit):
    if value is None:
        return ""
    if not isinstance(value, (str, int, float, bool)):
        raise ValueError("Invalid catalog field type")
    text = str(value).strip()
    if len(text) > limit:
        raise ValueError("Catalog field exceeds limit")
    return "".join(char if char.isprintable() else " " for char in text)


def clean_row(item):
    if not isinstance(item, dict):
        raise ValueError("Invalid catalog row")
    row = {}
    for key in FIELDS:
        if key not in item:
            continue
        value = item[key]
        if key == "tags":
            if value is None:
                value = []
            if isinstance(value, str):
                if len(value) > 4096:
                    raise ValueError("Catalog tags exceed limit")
                value = value.split(",")
            if not isinstance(value, list) or len(value) > 64:
                raise ValueError("Invalid catalog tags")
            row[key] = [
                _text(tag, 128) for tag in value if tag is not None and str(tag).strip()
            ]
        elif key in NUMBER_FIELDS:
            if value is None or value == "":
                value = 0
            if not isinstance(value, (str, int, float, bool)) or len(str(value)) > 32:
                raise ValueError("Invalid catalog number")
            number = int(value)
            if not 0 <= number <= 2**31 - 1:
                raise ValueError("Catalog number exceeds limit")
            row[key] = number
        elif key == "lastcheckok":
            if not isinstance(value, (bool, int)) or value not in (False, True, 0, 1):
                raise ValueError("Invalid catalog check flag")
            row[key] = bool(value)
        else:
            row[key] = _text(value, TEXT_LIMITS[key])
    if sum(len(str(value)) for value in row.values()) > 16384:
        raise ValueError("Catalog row exceeds limit")
    return row


def validate_rows(rows):
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("Invalid catalog row count")
    for row in rows:
        if not isinstance(row, dict) or not set(row) <= set(FIELDS):
            raise ValueError("Invalid catalog reply fields")
        for key, value in row.items():
            if key == "tags":
                if (
                    not isinstance(value, list)
                    or len(value) > 64
                    or any(
                        not isinstance(tag, str)
                        or len(tag) > 128
                        or not tag.isprintable()
                        for tag in value
                    )
                ):
                    raise ValueError("Invalid catalog reply tags")
            elif key in NUMBER_FIELDS:
                if type(value) is not int or not 0 <= value <= 2**31 - 1:
                    raise ValueError("Invalid catalog reply number")
            elif key == "lastcheckok":
                if type(value) is not bool:
                    raise ValueError("Invalid catalog reply flag")
            elif (
                not isinstance(value, str)
                or len(value) > TEXT_LIMITS[key]
                or any(not char.isprintable() for char in value)
            ):
                raise ValueError("Invalid catalog reply text")
        if sum(len(str(value)) for value in row.values()) > 16384:
            raise ValueError("Catalog reply row exceeds limit")
    return rows


def _xml_rows(text):
    from xml.etree import ElementTree

    upper = text.upper()
    if "<!DOCTYPE" in upper or "<!ENTITY" in upper or "\0" in text:
        raise ValueError("Catalog DTD/entities are not supported")
    depth = nodes = entries = 0
    for event, node in ElementTree.iterparse(
        io.StringIO(text), events=("start", "end")
    ):
        if event == "start":
            depth += 1
            nodes += 1
            if (
                depth > 32
                or nodes > 600_000
                or (nodes == 1 and node.tag != "directory")
            ):
                raise ValueError("Catalog XML structure exceeds limit")
            continue
        if node.tag == "entry":
            entries += 1
            if entries > MAX_ROWS:
                raise ValueError("Catalog row count exceeds limit")

            def field(*names):
                for name in names:
                    value = node.findtext(name)
                    if value and value.strip():
                        return value.strip()
                return ""

            yield {
                "name": field("server_name", "listen_name", "title"),
                "url": field("listen_url", "url"),
                "homepage": field("server_url", "homepage"),
                "tags": field("genre", "tags"),
                "country": field("country"),
                "language": field("language"),
                "codec": field("server_type", "type"),
                "bitrate": field("bitrate"),
            }
            node.clear()
        depth -= 1


def encode_catalog(raw, kind):
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("Catalog body exceeds limit")
    text = raw.decode("utf-8-sig")
    if kind == "json":

        def invalid_constant(_value):
            raise ValueError("Non-finite catalog number")

        rows = json.loads(text, parse_constant=invalid_constant)
        if not isinstance(rows, list) or len(rows) > MAX_ROWS:
            raise ValueError("Invalid catalog row count")
    elif kind == "xml":
        rows = _xml_rows(text)
    else:
        raise ValueError("Invalid catalog kind")
    # Build one bounded reply; no partial result is sent on parser failure.
    # Single invalid rows are skipped (bounded); body, structure, row-count and
    # reply limits still fail the whole catalog.
    result = bytearray(b'{"rows":[')
    count = skipped = 0
    for item in rows:
        try:
            cleaned = clean_row(item)
        except (ValueError, OverflowError):
            skipped += 1
            if skipped > MAX_SKIPPED_ROWS:
                raise ValueError("Too many invalid catalog rows") from None
            continue
        encoded = json.dumps(cleaned, separators=(",", ":")).encode("utf-8")
        if len(result) + len(encoded) + 4 > MAX_REPLY_BYTES:
            raise ValueError("Catalog reply exceeds limit")
        if count:
            result.extend(b",")
        result.extend(encoded)
        count += 1
    if skipped > count:
        raise ValueError("Mostly invalid catalog rows")
    result.extend(b"]}")
    return result


def apply_process_limits():
    import resource

    for name, maximum in (
        (resource.RLIMIT_AS, 384 * 1024 * 1024),
        (resource.RLIMIT_CPU, 8),
        (resource.RLIMIT_NPROC, 0),
    ):
        soft, hard = resource.getrlimit(name)
        limit = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (limit, limit))


def main():
    import sys

    try:
        if sys.argv[1:] not in (["--json"], ["--xml"]):
            raise ValueError("Invalid catalog parser mode")
        apply_process_limits()
        raw = sys.stdin.buffer.read(MAX_BODY_BYTES + 1)
        reply = encode_catalog(raw, sys.argv[1][2:])
        sys.stdout.buffer.write(reply)
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        print("Protected catalog parser failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
