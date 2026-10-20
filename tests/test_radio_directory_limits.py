"""Bounded downloads and parser regressions without external network access."""

import io
import json
from email.message import Message

import pytest

from netmon.core import radio_directory as directory
from netmon.features import radio_controller as radio


class Response(io.BytesIO):
    def __init__(self, body, headers=(), short_reads=False, status=200):
        super().__init__(body)
        self.status = self.code = status
        self.msg = "test response"
        self.headers = Message()
        for key, value in headers:
            self.headers[key] = value
        self.short_reads = short_reads
        self.bytes_read = 0

    def info(self):
        return self.headers

    def read(self, size=-1):
        assert self.status not in directory.REDIRECT_CODES, "Redirect body drained"
        assert size > 0, "Unbounded read"
        return super().read(size)

    def read1(self, size=-1):
        assert self.status not in directory.REDIRECT_CODES, "Redirect body drained"
        assert 0 < size <= directory.CHUNK_BYTES
        result = super().read(min(size, 7) if self.short_reads else size)
        self.bytes_read += len(result)
        return result


@pytest.fixture
def transport(monkeypatch):
    """Keep the real urllib opener/response processors; replace only network I/O."""
    calls = []
    responses = []

    def open_response(handler, request):
        calls.append(request)
        assert responses, "Unexpected follow-up connection"
        return responses.pop(0)

    monkeypatch.setattr(
        directory.urllib.request.HTTPHandler, "http_open", open_response
    )
    monkeypatch.setattr(
        directory.urllib.request.HTTPSHandler, "https_open", open_response
    )
    return responses, calls


@pytest.fixture
def serve(transport):
    def install(body, headers=(), short_reads=False):
        response = Response(body, headers, short_reads)
        transport[0].append(response)
        return response

    return install


DOWNLOADS = [
    radio._download_radio_db_payload,
    lambda: radio._download_radio_source_payload("radio_browser_api"),
    lambda: radio._download_radio_source_payload("radio_browser_top"),
    lambda: radio._download_radio_source_payload("icecast_json"),
]


@pytest.mark.parametrize("download", DOWNLOADS)
@pytest.mark.parametrize("length", [None, "129", "1", "invalid"])
def test_all_download_paths_reject_oversize(download, length, monkeypatch, serve):
    monkeypatch.setattr(directory, "MAX_RESPONSE_BYTES", 128)
    headers = [] if length is None else [("Content-Length", length)]
    response = serve(b"x" * 1000, headers, short_reads=True)
    with pytest.raises(ValueError, match="Größenlimit"):
        download()
    assert response.closed
    assert response.bytes_read == (0 if length == "129" else 129)


def test_exact_limit_and_short_reads_succeed(monkeypatch, serve):
    monkeypatch.setattr(directory, "MAX_RESPONSE_BYTES", 128)
    response = serve(b" " * 126 + b"[]", [("Content-Length", "128")], True)
    assert radio._download_radio_db_payload() == []
    assert response.bytes_read == 128
    assert response.closed


@pytest.mark.parametrize("download", DOWNLOADS[:3])
def test_normal_json_downloads_keep_station_fields(download, serve):
    serve(json.dumps([{"name": "Radio", "url": "https://example.com/live"}]).encode())
    rows = download()
    assert rows[0]["name"] == "Radio"
    assert rows[0]["url"] == "https://example.com/live"


def test_normal_xml_download_keeps_station_fields(serve):
    serve(
        b"<directory><entry><server_name>Radio</server_name>"
        b"<listen_url>https://example.com/live</listen_url></entry></directory>"
    )
    rows = radio._download_radio_source_payload("icecast_json")
    assert rows[0]["name"] == "Radio"
    assert rows[0]["url"] == "https://example.com/live"


@pytest.mark.parametrize("download", DOWNLOADS[:3])
def test_json_nesting_rejected_before_decoder(download, monkeypatch, serve):
    serve(b"[" * (directory.MAX_DEPTH + 1) + b"]" * (directory.MAX_DEPTH + 1))

    def forbidden(*args):
        pytest.fail("JSON decoder must not receive excessively nested input")

    monkeypatch.setattr(directory.json, "loads", forbidden)
    with pytest.raises(ValueError, match="verschachtelt"):
        download()


def test_json_strings_do_not_count_as_structure():
    value = ["[{:," * 100, 'a"b\\c', {"nested": [1]}]
    assert directory.parse_directory_json(json.dumps(value)) == value


@pytest.mark.parametrize("kind", ["json", "xml"])
def test_parser_item_budget(kind, monkeypatch):
    monkeypatch.setattr(directory, "MAX_ITEMS", 3)
    parse, text = (
        (directory.parse_directory_json, "[1,2,3,4]")
        if kind == "json"
        else (directory.parse_directory_xml, "<d><e/><e/><e/></d>")
    )
    with pytest.raises(ValueError):
        parse(text)


def test_xml_nesting_rejected(serve):
    serve(b"<d>" * (directory.MAX_DEPTH + 1) + b"</d>" * (directory.MAX_DEPTH + 1))
    with pytest.raises(ValueError, match="Strukturlimit"):
        radio._download_radio_source_payload("icecast_json")


def test_xml_entity_declarations_rejected(serve):
    serve(b'<!DOCTYPE d [<!ENTITY x "expanded">]><d>&x;</d>')
    with pytest.raises(ValueError, match="DTD"):
        radio._download_radio_source_payload("icecast_json")


def test_decoded_text_budget(monkeypatch, serve):
    monkeypatch.setattr(directory, "MAX_RESPONSE_BYTES", 128)
    serve(b"\xff" * 64, [("Content-Type", "text/plain; charset=iso-8859-1")])
    assert directory.fetch_directory_text("https://example.com") == "ÿ" * 64
    serve(b"\xff" * 65, [("Content-Type", "text/plain; charset=iso-8859-1")])
    with pytest.raises(ValueError, match="Dekodierte"):
        directory.fetch_directory_text("https://example.com")


@pytest.mark.parametrize("encoding", ["gzip", "deflate", "br"])
def test_compression_rejected_without_reading(encoding, serve):
    response = serve(b"compressed", [("Content-Encoding", encoding)])
    with pytest.raises(ValueError, match="Komprimierte"):
        radio._download_radio_db_payload()
    assert response.bytes_read == 0
    assert response.closed


def test_total_download_deadline(monkeypatch, serve):
    response = serve(b"[]")
    ticks = iter([0, 0, directory.DOWNLOAD_SECONDS + 1])
    monkeypatch.setattr(directory.time, "monotonic", lambda: next(ticks))
    with pytest.raises(ValueError, match="Zeitlimit"):
        radio._download_radio_db_payload()
    assert response.closed


@pytest.mark.parametrize("download", DOWNLOADS)
@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_redirect_body_is_never_read(download, status, transport):
    responses, calls = transport
    redirect = Response(
        b"unbounded intermediate body",
        [("Location", "/next"), ("Content-Length", str(10**12))],
        status=status,
    )
    final = Response(b"<directory/>" if download is DOWNLOADS[3] else b"[]")
    responses.extend([redirect, final])
    assert download() == []
    assert redirect.closed and final.closed
    assert redirect.bytes_read == 0
    assert len(calls) == 2
    initial_method = calls[0].get_method()
    expected = "POST" if initial_method == "POST" and status in {307, 308} else "GET"
    assert calls[1].get_method() == expected
    assert calls[1].data == (calls[0].data if expected == "POST" else None)


@pytest.mark.parametrize("download", DOWNLOADS)
def test_expired_budget_after_close_prevents_followup_connect(
    download, transport, monkeypatch
):
    responses, calls = transport
    clock = [0]

    class SlowClose(Response):
        def close(self):
            clock[0] = directory.DOWNLOAD_SECONDS + 1
            super().close()

    response = SlowClose(b"ignored", [("Location", "/next")], status=302)
    responses.append(response)
    monkeypatch.setattr(directory.time, "monotonic", lambda: clock[0])
    with pytest.raises(ValueError, match="Zeitlimit"):
        download()
    assert response.closed
    assert len(calls) == 1


def test_redirect_uses_remaining_timeout(transport, monkeypatch):
    responses, calls = transport
    clock = [0]

    class SlowClose(Response):
        def close(self):
            clock[0] = 12
            super().close()

    responses.extend(
        [SlowClose(b"", [("Location", "/next")], status=302), Response(b"[]")]
    )
    monkeypatch.setattr(directory.time, "monotonic", lambda: clock[0])
    assert radio._download_radio_db_payload() == []
    assert [request.timeout for request in calls] == [30, 18]


def test_redirect_count_is_bounded(transport):
    responses, calls = transport
    redirects = [
        Response(b"", [("Location", f"/hop/{i}")], status=302)
        for i in range(directory.MAX_REDIRECTS + 1)
    ]
    responses.extend(redirects)
    with pytest.raises(ValueError, match="Zu viele"):
        radio._download_radio_db_payload()
    assert len(calls) == directory.MAX_REDIRECTS + 1
    assert all(response.closed for response in redirects)


@pytest.mark.parametrize(
    "headers",
    [
        [],
        [("Location", "")],
        [("Location", "/one"), ("Location", "/two")],
        [("Location", "file:///etc/passwd")],
        [("Location", "https://user:password@example.com/")],
        [("Location", "http://example.com/")],
        [("Location", "/next\r\ninjected")],
    ],
)
def test_invalid_redirect_closes_without_followup(headers, transport):
    responses, calls = transport
    response = Response(b"ignored", headers, status=302)
    responses.append(response)
    with pytest.raises(ValueError):
        radio._download_radio_db_payload()
    assert response.closed
    assert len(calls) == 1


def test_redirect_loop_closes_without_followup(transport):
    responses, calls = transport
    response = Response(b"", [("Location", radio.RADIO_DB_ENDPOINT)], status=302)
    responses.append(response)
    with pytest.raises(ValueError, match="Schleife"):
        radio._download_radio_db_payload()
    assert response.closed
    assert len(calls) == 1


def test_error_body_is_not_read(transport):
    responses, calls = transport
    response = Response(b"oversized error body", status=500)
    responses.append(response)
    with pytest.raises(ValueError, match="HTTP 500"):
        radio._download_radio_db_payload()
    assert response.closed and response.bytes_read == 0
    assert len(calls) == 1
