"""Catalog parsing in the source process and strict validation of its reply."""

import io
import json
import re
import shlex
from urllib.parse import unquote, urlsplit

MAX_BODY_BYTES = 16 * 1024 * 1024
MAX_REPLY_BYTES = 16 * 1024 * 1024
MAX_ROWS = 50_000
# Each source stays small; combined imports count duplicates before merging.
MAX_IMPORT_ROWS = 250_000
MAX_IMPORT_BYTES = 128 * 1024 * 1024
MAX_M3U_BYTES = 1024 * 1024
MAX_M3U_ROWS = 5000
MAX_M3U_LINE_CHARS = 8192
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


def _direct_stream_url(value, *, https_only=False):
    if not isinstance(value, str) or not value or len(value) > TEXT_LIMITS["url"]:
        return False
    if any(char.isspace() or not char.isprintable() for char in value) or "\\" in value:
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme in ({"https"} if https_only else {"http", "https"})
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.fragment
            and not parsed.netloc.endswith(":")
            and parsed.port != 0
            and not unquote(parsed.path)
            .lower()
            .endswith((".m3u", ".m3u8", ".pls", ".mpd"))
        )
    except ValueError:
        return False


def _verified_rows(data):
    """Map the provider's country envelopes without treating a website as audio."""
    if not isinstance(data, dict) or not isinstance(data.get("countries"), list):
        raise ValueError("Invalid Verified Radio country envelope")
    if len(data["countries"]) > 512:
        raise ValueError("Verified Radio country count exceeds limit")
    entries = 0
    for country in data["countries"]:
        if not isinstance(country, dict) or not isinstance(
            country.get("stations"), list
        ):
            raise ValueError("Invalid Verified Radio station envelope")
        for item in country["stations"]:
            entries += 1
            if entries > MAX_ROWS:
                raise ValueError("Verified Radio station count exceeds limit")
            if not isinstance(item, dict) or not _direct_stream_url(
                item.get("stream"), https_only=True
            ):
                continue
            languages = item.get("langs", [])
            if (
                isinstance(languages, list)
                and len(languages) <= 32
                and all(
                    isinstance(value, str) and len(value) <= 128 for value in languages
                )
            ):
                languages = ", ".join(languages)
            yield {
                "name": item.get("name", ""),
                "url": item["stream"],
                "homepage": item.get("url", ""),
                "country": country.get("country", ""),
                "countrycode": country.get("countryCode", ""),
                "tags": item.get("genre", []),
                "language": languages,
                "codec": item.get("codec", ""),
                "bitrate": item.get("bitrate", 0),
                "votes": item.get("votes", 0),
                "clickcount": item.get("clicks", 0),
            }


def _m3u_rows(text, *, provider="72fm"):
    """Read named station entries only; never follow playlists or directives.

    The registered 72FM Top 500 feed uses group-title for the country.
    IPRD uses group-title for semicolon-separated genres, not the country.
    Provider comments are ignored rather than treated as station websites.
    """
    header = False
    pending = None
    entries = 0
    for raw_line in re.split(r"\r\n|\r|\n", text):
        if len(raw_line) > MAX_M3U_LINE_CHARS:
            raise ValueError("M3U line exceeds limit")
        line = raw_line.strip()
        if not line:
            continue
        if not header:
            if line != "#EXTM3U":
                raise ValueError("Extended M3U header required")
            header = True
            continue
        if line.startswith("#EXT-X-"):
            raise ValueError("HLS is not a station catalog")
        if line.startswith("#EXTINF:"):
            if pending is not None:
                raise ValueError("M3U station has no stream")
            quoted = False
            separator = None
            for index, char in enumerate(line):
                if char == '"':
                    quoted = not quoted
                elif char == "," and not quoted:
                    separator = index
                    break
            if separator is None:
                raise ValueError("Invalid M3U station metadata")
            tokens = shlex.split(line[8:separator])
            if not tokens or not re.fullmatch(r"-?\d+(?:\.\d+)?", tokens[0]):
                raise ValueError("Invalid M3U duration")
            attributes = dict(
                token.split("=", 1) for token in tokens[1:] if "=" in token
            )
            pending = {
                "name": line[separator + 1 :].strip(),
                "favicon": attributes.get("tvg-logo", ""),
            }
            group = attributes.get("group-title", "")
            if provider == "iprd":
                pending["tags"] = [
                    tag.strip() for tag in group.split(";") if tag.strip()
                ]
            else:
                pending["country"] = group
            if not pending["name"]:
                raise ValueError("M3U station name required")
            continue
        if line.startswith("#"):
            continue
        entries += 1
        if entries > MAX_ROWS or (provider != "iprd" and entries > MAX_M3U_ROWS):
            raise ValueError("M3U station count exceeds limit")
        if pending is None:
            raise ValueError("M3U station metadata required")
        row, pending = pending, None
        if not _direct_stream_url(line):
            continue
        yield {**row, "url": line}
    if not header or pending is not None:
        raise ValueError("Incomplete M3U station catalog")


def encode_catalog(raw, kind):
    if len(raw) > MAX_BODY_BYTES:
        raise ValueError("Catalog body exceeds limit")
    if kind == "m3u" and len(raw) > MAX_M3U_BYTES:
        raise ValueError("M3U body exceeds limit")
    text = raw.decode("utf-8-sig")
    if kind in {"json", "verified"}:

        def invalid_constant(_value):
            raise ValueError("Non-finite catalog number")

        data = json.loads(text, parse_constant=invalid_constant)
        if kind == "verified":
            rows = _verified_rows(data)
        else:
            rows = data
            if not isinstance(rows, list) or len(rows) > MAX_ROWS:
                raise ValueError("Invalid catalog row count")
    elif kind == "xml":
        rows = _xml_rows(text)
    elif kind == "m3u":
        rows = _m3u_rows(text)
    elif kind == "iprd":
        rows = _m3u_rows(text, provider="iprd")
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
        if sys.argv[1:] not in (
            ["--json"],
            ["--xml"],
            ["--m3u"],
            ["--iprd"],
            ["--verified"],
        ):
            raise ValueError("Invalid catalog parser mode")
        apply_process_limits()
        limit = MAX_M3U_BYTES if sys.argv[1:] == ["--m3u"] else MAX_BODY_BYTES
        raw = sys.stdin.buffer.read(limit + 1)
        reply = encode_catalog(raw, sys.argv[1][2:])
        sys.stdout.buffer.write(reply)
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        print("Protected catalog parser failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
