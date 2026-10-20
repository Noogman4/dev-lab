"""Bounded release metadata, including real urllib redirect handling with fake IO."""

import io
import json
from email.message import Message
import threading
from types import SimpleNamespace
from urllib import request
from urllib.response import addinfourl

import pytest

from netmon.core import release_metadata as metadata
from netmon.app import App
from netmon import app as app_module


class Response(io.BytesIO):
    def __init__(self, payload=b'{"version":"1.2.3"}', *, code=200, headers=None):
        super().__init__(payload)
        self.code = code
        self.headers = headers or {}
        self.read_sizes = []

    def getcode(self):
        return self.code

    def read(self, size=-1):
        assert size > 0
        self.read_sizes.append(size)
        return super().read(size)

    read1 = read


def transport(monkeypatch, responses):
    calls = []

    def open_request(req, timeout):
        calls.append((req, timeout))
        return responses.pop(0)

    monkeypatch.setattr(
        metadata.request, "build_opener", lambda *_h: SimpleNamespace(open=open_request)
    )
    return calls


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_actual_urllib_redirect_does_not_read_intermediate_body(monkeypatch, code):
    real_builder = request.build_opener
    bodies = []
    urls = []

    class SyntheticHTTP(request.HTTPHandler):
        handler_order = 499  # Serve synthetic IO before the production handler.

        def http_open(self, req):
            urls.append(req.full_url)
            first = len(urls) == 1
            body = Response(b"x" * 512 if first else b'{"version":"1.2.3"}')
            bodies.append(body)
            headers = Message()
            if first:
                headers["Location"] = "/final"
            response = addinfourl(body, headers, req.full_url, code if first else 200)
            response.msg = "synthetic"
            return response

    monkeypatch.setattr(
        metadata.request,
        "build_opener",
        lambda *handlers: real_builder(*handlers, SyntheticHTTP()),
    )
    assert (
        metadata.fetch_release_metadata("http://metadata.invalid/start")["version"]
        == "1.2.3"
    )
    assert urls == ["http://metadata.invalid/start", "http://metadata.invalid/final"]
    assert bodies[0].read_sizes == [] and bodies[0].closed
    assert bodies[1].read_sizes and bodies[1].closed


@pytest.mark.parametrize("declared", [None, "1", "129", "-1", "nonsense"])
def test_size_limit_with_missing_or_dishonest_content_length(monkeypatch, declared):
    monkeypatch.setattr(metadata, "MAX_BYTES", 128)
    headers = {} if declared is None else {"Content-Length": declared}
    response = Response(b"x" * 512, headers=headers)
    transport(monkeypatch, [response])
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://metadata.invalid/version")
    assert sum(response.read_sizes) <= 129
    assert response.closed


def test_exact_size_limit_and_identity_encoding_work(monkeypatch):
    monkeypatch.setattr(metadata, "MAX_BYTES", 128)
    response = Response(
        b'{"version":"1.2.3"}'.ljust(128), headers={"Content-Length": "128"}
    )
    calls = transport(monkeypatch, [response])
    assert (
        metadata.fetch_release_metadata("https://metadata.invalid/version")["version"]
        == "1.2.3"
    )
    assert calls[0][0].get_header("Accept-encoding") == "identity"


@pytest.mark.parametrize("encoding", ["gzip", "br", "deflate"])
def test_compressed_reply_rejected_before_read(monkeypatch, encoding):
    response = Response(headers={"Content-Encoding": encoding})
    transport(monkeypatch, [response])
    with pytest.raises(ValueError, match="Komprimierte"):
        metadata.fetch_release_metadata("https://metadata.invalid/version")
    assert not response.read_sizes


@pytest.mark.parametrize(
    "payload",
    [
        b"[" * 17 + b"0" + b"]" * 17,
        b'{"version":"1","extra":[' + b"0," * 1100 + b"0]}",
        b"[]",
        b"{",
        b"\xff",
    ],
)
def test_json_limits_and_invalid_payloads(monkeypatch, payload):
    response = Response(payload)
    transport(monkeypatch, [response])
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://metadata.invalid/version")
    assert response.closed


def test_structure_characters_inside_json_strings_are_not_counted(monkeypatch):
    payload = {"version": "1.2.3", "note": '[{,:\\"' * 1200}
    transport(monkeypatch, [Response(json.dumps(payload).encode())])
    assert (
        metadata.fetch_release_metadata("https://metadata.invalid/version") == payload
    )


@pytest.mark.parametrize("kind", ["loop", "hops", "missing", "scheme", "downgrade"])
def test_redirect_bounds(monkeypatch, kind):
    if kind == "loop":
        locations = ["/start"]
    elif kind == "hops":
        locations = [f"/hop{i}" for i in range(6)]
    elif kind == "missing":
        locations = [None]
    elif kind == "scheme":
        locations = ["file:///synthetic/metadata"]
    else:
        locations = ["http://metadata.invalid/final"]
    responses = [
        Response(code=302, headers={} if location is None else {"Location": location})
        for location in locations
    ]
    all_responses = list(responses)
    calls = transport(monkeypatch, responses)
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://metadata.invalid/start")
    assert len(calls) <= metadata.MAX_REDIRECTS + 1
    assert not any(response.read_sizes for response in all_responses)
    assert all(response.closed for response in all_responses[: len(calls)])


def test_expired_redirect_never_opens_followup(monkeypatch):
    now = [0]
    monkeypatch.setattr(metadata.time, "monotonic", lambda: now[0])
    calls = []
    response = Response(code=302, headers={"Location": "/next"})

    def open_request(req, timeout):
        calls.append(req)
        now[0] = metadata.MAX_SECONDS + 1
        return response

    monkeypatch.setattr(
        metadata.request, "build_opener", lambda *_h: SimpleNamespace(open=open_request)
    )
    with pytest.raises(TimeoutError):
        metadata.fetch_release_metadata("https://metadata.invalid/start")
    assert len(calls) == 1 and response.closed and not response.read_sizes


def test_next_hop_uses_remaining_time(monkeypatch):
    now = [0]
    monkeypatch.setattr(metadata.time, "monotonic", lambda: now[0])
    calls = []

    def open_request(req, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            now[0] = 12
            return Response(code=302, headers={"Location": "/next"})
        return Response()

    monkeypatch.setattr(
        metadata.request, "build_opener", lambda *_h: SimpleNamespace(open=open_request)
    )
    assert (
        metadata.fetch_release_metadata("https://metadata.invalid/start")["version"]
        == "1.2.3"
    )
    assert calls == [8, 3]


def test_stalled_connect_has_caller_deadline_and_no_later_read(monkeypatch):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.1)
    entered = threading.Event()
    release = threading.Event()
    response = Response()

    def open_request(req, timeout):
        entered.set()
        assert release.wait(3)
        return response

    monkeypatch.setattr(
        metadata.request, "build_opener", lambda *_h: SimpleNamespace(open=open_request)
    )
    try:
        with pytest.raises(TimeoutError) as caught:
            metadata.fetch_release_metadata("https://metadata.invalid/start")
        assert entered.is_set()
        assert not caught.value.transport_finished.is_set()
    finally:
        release.set()
    assert caught.value.transport_finished.wait(3)
    assert response.closed and not response.read_sizes


@pytest.mark.parametrize(
    "download_url, expected",
    [
        ("https://netmonroots.com/downloads", "https://netmonroots.com/downloads"),
        ("https://evil.invalid/file", "https://netmonroots.com/fallback"),
        ("file:///tmp/payload", "https://netmonroots.com/fallback"),
    ],
)
def test_app_uses_bounded_transport_and_preserves_link_policy(
    monkeypatch, download_url, expected
):
    monkeypatch.setattr(
        app_module,
        "fetch_release_metadata",
        lambda _url: {"version": "1.2.3", "download_url": download_url},
    )
    app = SimpleNamespace(
        netmon_roots_latest_version_url="https://netmonroots.com/version",
        netmon_roots_downloads_url="https://netmonroots.com/fallback",
        _is_trusted_update_url=App._is_trusted_update_url,
    )
    assert App._fetch_latest_release_info(app) == {
        "version": "1.2.3",
        "download_url": expected,
    }


@pytest.mark.parametrize(
    "version, opens, status",
    [
        ("9999.0", True, "Neue Version"),
        (app_module.NETMON_APP_VERSION, False, "aktuell"),
        ("0.0.1", False, "Lokale Version"),
    ],
)
def test_about_version_check_retains_update_behaviour(
    monkeypatch, version, opens, status
):
    app = App.__new__(App)
    app.tr = lambda _key, fallback: fallback
    statuses, links = [], []
    app._about_update_redirect_done = False
    app._set_about_version_status = statuses.append
    app._fetch_latest_release_info = lambda: {
        "version": version,
        "download_url": "https://netmonroots.com/downloads",
    }
    app.after = lambda _delay, callback: callback()
    app._open_url_with_xdg_open = lambda url, **_kw: links.append(url)

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module.threading, "Thread", Immediate)
    app.check_about_latest_version()
    assert (len(links) == 1) is opens
    assert status in statuses[-1]
    assert app._about_version_check_running is False


def test_about_blocks_retries_until_timed_out_transport_finishes(monkeypatch):
    app = App.__new__(App)
    app.tr = lambda _key, fallback: fallback
    statuses, logs, requests = [], [], []
    app._set_about_version_status = statuses.append
    app.log_safe = logs.append
    app.after = lambda _delay, callback: callback()
    finished = threading.Event()

    def fetch():
        requests.append(True)
        error = TimeoutError("synthetic DNS timeout")
        error.transport_finished = finished
        raise error

    app._fetch_latest_release_info = fetch

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module.threading, "Thread", Immediate)
    app.check_about_latest_version(manual=True)
    assert app._about_version_check_running is False
    app.check_about_latest_version()
    assert len(requests) == 1
    assert "nicht verfügbar" in statuses[-1]
    assert logs
    finished.set()
    app.check_about_latest_version()
    assert len(requests) == 2


def test_about_thread_start_error_does_not_stick_running_flag(monkeypatch):
    app = App.__new__(App)
    app.tr = lambda _key, fallback: fallback
    statuses, logs = [], []
    app._set_about_version_status = statuses.append
    app.log_safe = logs.append

    class Unavailable:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise RuntimeError("synthetic thread limit")

    monkeypatch.setattr(app_module.threading, "Thread", Unavailable)
    app.check_about_latest_version()
    assert app._about_version_check_running is False
    assert "nicht verfügbar" in statuses[-1]
    assert logs


def test_read_deadline_is_checked_between_bounded_reads(monkeypatch):
    now = [0]
    monkeypatch.setattr(metadata.time, "monotonic", lambda: now[0])
    timeouts, reads = [], []
    response = Response()
    response.fp = SimpleNamespace(
        raw=SimpleNamespace(
            _sock=SimpleNamespace(
                settimeout=timeouts.append, shutdown=lambda _how: None
            )
        )
    )
    original_read = response.read1

    def slow_read(size):
        reads.append(size)
        now[0] += 8
        return original_read(min(size, 4))

    response.read1 = slow_read
    calls = transport(monkeypatch, [response])
    with pytest.raises(TimeoutError):
        metadata.fetch_release_metadata("https://metadata.invalid/version")
    assert len(calls) == 1 and response.closed
    assert timeouts == [8, 7]
    assert len(reads) == 2
