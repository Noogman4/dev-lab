"""Resource budgets for untrusted radio directory responses."""

import json
import time
import urllib.request
from contextlib import contextmanager
from urllib.parse import urljoin, urlsplit
from xml.etree import ElementTree

# Room for 5000 stations, including metadata; independent of provider row limits.
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_DEPTH = 64
MAX_ITEMS = 500_000
DOWNLOAD_SECONDS = 30
CHUNK_BYTES = 64 * 1024
MAX_REDIRECTS = 5
REDIRECT_CODES = {301, 302, 303, 307, 308}


class _RawResponses(urllib.request.HTTPErrorProcessor):
    def http_response(self, request, response):
        # Do not invoke urllib's redirect handler: it drains intermediate bodies.
        return response

    https_response = http_response


def _build_opener():
    return urllib.request.build_opener(_RawResponses())


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ValueError("Zeitlimit für Radio-Datenbank überschritten")
    return remaining


def _validate_url(url):
    if len(url) > 8192 or any(ord(c) <= 32 or ord(c) == 127 for c in url):
        raise ValueError("Ungültige Radio-Datenbank-URL")
    parts = urlsplit(url)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or "\\" in url
    ):
        raise ValueError("Ungültige Radio-Datenbank-URL")
    return parts


@contextmanager
def _open_directory_response(request, deadline):
    request = urllib.request.Request(request) if isinstance(request, str) else request
    _validate_url(request.full_url)
    opener = _build_opener()
    visited = set()
    for hop in range(MAX_REDIRECTS + 1):
        if request.full_url in visited:
            raise ValueError("Radio-Datenbank-Redirect-Schleife")
        visited.add(request.full_url)
        request.add_header("Accept-Encoding", "identity")
        # Recheck after closing the previous response and before every connect.
        with opener.open(request, timeout=_remaining(deadline)) as response:
            _remaining(deadline)
            if response.status in REDIRECT_CODES:
                if hop == MAX_REDIRECTS:
                    raise ValueError("Zu viele Radio-Datenbank-Redirects")
                locations = response.headers.get_all("Location", [])
                if len(locations) != 1 or not locations[0].strip():
                    raise ValueError("Fehlendes oder mehrdeutiges Redirect-Ziel")
                location = locations[0].strip()
                _validate_url(urljoin(request.full_url, location))
                # Validate the raw value too: urljoin strips some control bytes.
                if any(ord(c) < 32 or ord(c) == 127 for c in location):
                    raise ValueError("Ungültiges Redirect-Ziel")
                target = urljoin(request.full_url, location)
                if (
                    urlsplit(request.full_url).scheme == "https"
                    and urlsplit(target).scheme != "https"
                ):
                    raise ValueError("Unsicheres Redirect-Ziel")
                method = request.get_method()
                data = request.data
                if (
                    response.status == 303
                    and method != "HEAD"
                    or (response.status in {301, 302} and method == "POST")
                ):
                    method, data = "GET", None
                # Only directory request headers may cross an origin boundary.
                headers = {"User-Agent": "NetMon/1.1"}
                if data is not None:
                    headers["Content-Type"] = "application/json"
                request = urllib.request.Request(
                    target, data=data, headers=headers, method=method
                )
                # Context exit closes without reading the intermediate body.
                continue
            if response.status != 200:
                raise ValueError(f"Radio-Datenbank liefert HTTP {response.status}")
            yield response
            return


def fetch_directory_text(request):
    """Read at most the byte budget plus one overflow byte, even without headers."""
    deadline = time.monotonic() + DOWNLOAD_SECONDS
    with _open_directory_response(request, deadline) as response:
        encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
        # urllib does not decompress these bodies. Never add unbounded decompression.
        if encoding not in {"", "identity"}:
            raise ValueError("Komprimierte Radio-Datenbank wird nicht unterstützt")
        length = response.headers.get("Content-Length")
        if length is not None:
            try:
                length = int(length)
            except ValueError:
                length = None  # The actual read budget remains authoritative.
            if length is not None and (length < 0 or length > MAX_RESPONSE_BYTES):
                raise ValueError("Radio-Datenbank überschreitet das Größenlimit")
        data = bytearray()
        # read1 returns available data without waiting to fill an entire chunk.
        read = getattr(response, "read1", response.read)
        while True:
            _remaining(deadline)
            chunk = read(min(CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - len(data)))
            _remaining(deadline)
            data.extend(chunk)
            if len(data) > MAX_RESPONSE_BYTES:
                raise ValueError("Radio-Datenbank überschreitet das Größenlimit")
            if not chunk:
                break
        charset = response.headers.get_content_charset("utf-8")
        text = data.decode(charset, errors="replace")
        _check_text_size(text)
        return text


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
