import contextlib
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from netmon.core import release_metadata as metadata


@contextlib.contextmanager
def local_server(*, trickle_headers=False):
    contacted = threading.Event()
    stop = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            contacted.set()
            try:
                if trickle_headers:
                    for byte in b"HTTP/1.1 200 OK\r\nX-Synthetic: " + b"x" * 80:
                        if stop.wait(0.02):
                            return
                        self.connection.sendall(bytes([byte]))
                else:
                    self.send_response(200)
                    self.send_header("Content-Length", "19")
                    self.end_headers()
                    self.wfile.write(b'{"version":"1.2.3"}')
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                self.close_connection = True

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}
    )
    worker.start()
    try:
        yield server.server_port, contacted, stop
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        worker.join(2)


def test_slow_headers_transport_ends_near_deadline(monkeypatch):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.12)
    with local_server(trickle_headers=True) as (port, contacted, stop):
        caught = None
        try:
            with pytest.raises(TimeoutError) as caught:
                metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/")
            assert contacted.is_set()
            assert caught.value.transport_finished.wait(
                0.35
            ), "Transport still reads trickling headers after caller deadline"
        finally:
            stop.set()
            if caught is not None:
                caught.value.transport_finished.wait(2)


def test_dns_return_after_deadline_makes_no_http_request(monkeypatch):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.12)
    release = threading.Event()
    entered = threading.Event()
    original = socket.getaddrinfo
    caught = None
    with local_server() as (port, contacted, _stop):

        def delayed(host, target_port, *args, **kwargs):
            if host == "metadata-review.invalid":
                entered.set()
                assert release.wait(2)
                return original("127.0.0.1", target_port, *args, **kwargs)
            return original(host, target_port, *args, **kwargs)

        monkeypatch.setattr(socket, "getaddrinfo", delayed)
        try:
            with pytest.raises(TimeoutError) as caught:
                metadata.fetch_release_metadata(
                    f"http://metadata-review.invalid:{port}/"
                )
            assert entered.is_set()
            release.set()
            assert caught.value.transport_finished.wait(2)
            assert (
                not contacted.is_set()
            ), "HTTP was sent after deadline while returning from DNS"
        finally:
            release.set()
            if caught is not None:
                caught.value.transport_finished.wait(2)


def test_connect_retry_after_deadline_makes_no_followup_connection(monkeypatch):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.12)
    release = threading.Event()
    entered = threading.Event()
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    caught = None
    with local_server() as (port, contacted, _stop):
        first_port = 1

        def addresses(host, target_port, *args, **kwargs):
            if host == "metadata-review.invalid":
                return [
                    (
                        socket.AF_INET,
                        socket.SOCK_STREAM,
                        6,
                        "",
                        ("127.0.0.1", first_port),
                    ),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
                ]
            return original_dns(host, target_port, *args, **kwargs)

        def delayed_connect(sock, address):
            if address == ("127.0.0.1", first_port):
                entered.set()
                assert release.wait(2)
                raise TimeoutError("synthetic delayed first connect")
            return original_connect(sock, address)

        monkeypatch.setattr(socket, "getaddrinfo", addresses)
        monkeypatch.setattr(socket.socket, "connect", delayed_connect)
        try:
            with pytest.raises(TimeoutError) as caught:
                metadata.fetch_release_metadata(
                    f"http://metadata-review.invalid:{port}/"
                )
            assert entered.is_set()
            release.set()
            assert caught.value.transport_finished.wait(2)
            assert (
                not contacted.is_set()
            ), "A second address was connected after deadline"
        finally:
            release.set()
            if caught is not None:
                caught.value.transport_finished.wait(2)


def test_explicit_cancellation_interrupts_header_read():
    cancelled = threading.Event()
    done = threading.Event()
    outcomes = []
    with local_server(trickle_headers=True) as (port, contacted, stop):

        def download():
            try:
                outcomes.append(
                    metadata._download(
                        f"http://127.0.0.1:{port}/", time.monotonic() + 2, cancelled
                    )
                )
            except Exception as exc:
                outcomes.append(exc)
            finally:
                done.set()

        worker = threading.Thread(target=download)
        worker.start()
        try:
            assert contacted.wait(1)
            cancelled.set()
            assert done.wait(0.35), "Cancellation does not stop live header read"
            assert len(outcomes) == 1 and isinstance(outcomes[0], Exception)
        finally:
            stop.set()
            worker.join(3)


@contextlib.contextmanager
def response_server(reply, tls_context=None):
    stop = threading.Event()
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.path, dict(self.headers)))
            try:
                reply(self, stop)
            except (OSError, ValueError):
                pass
            finally:
                self.close_connection = True

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    if tls_context is not None:
        server.socket = tls_context.wrap_socket(server.socket, server_side=True)
    worker = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.02}
    )
    worker.start()
    try:
        yield server.server_port, requests
    finally:
        stop.set()
        server.shutdown()
        server.server_close()
        worker.join(2)


def send_json(handler, payload=b'{"version":"1.2.3"}'):
    handler.send_response(200)
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


@pytest.mark.parametrize("mode", ["declared", "missing", "endless"])
def test_real_oversized_and_streaming_answers_are_bounded(monkeypatch, mode):
    import http.client

    monkeypatch.setattr(metadata, "MAX_BYTES", 128)
    original = http.client.HTTPResponse.read1
    consumed = []

    def read(response, size=-1):
        assert 0 < size <= 129
        result = original(response, size)
        consumed.append(len(result))
        return result

    monkeypatch.setattr(http.client.HTTPResponse, "read1", read)

    def reply(handler, stop):
        handler.send_response(200)
        if mode == "declared":
            handler.send_header("Content-Length", "512")
        handler.end_headers()
        if mode == "endless":
            while not stop.wait(0.002):
                handler.wfile.write(b"x" * 16)
                handler.wfile.flush()
        else:
            handler.wfile.write(b"x" * 512)

    with response_server(reply) as (port, _requests):
        with pytest.raises(ValueError, match="Größenlimit"):
            metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/")
    assert sum(consumed) <= 129
    if mode == "declared":
        assert not consumed


@pytest.mark.parametrize("mode", ["body", "chunk-header"])
def test_slow_body_and_chunk_framing_release_transport(monkeypatch, mode):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.12)

    def reply(handler, stop):
        handler.send_response(200)
        if mode == "chunk-header":
            handler.send_header("Transfer-Encoding", "chunked")
            data = b"1" * 100
        else:
            handler.send_header("Content-Length", "19")
            data = b'{"version":"1.2.3"}'
        handler.end_headers()
        for byte in data:
            if stop.wait(0.03):
                return
            handler.wfile.write(bytes([byte]))
            handler.wfile.flush()

    with response_server(reply) as (port, _requests):
        with pytest.raises(TimeoutError) as caught:
            metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/")
        assert caught.value.transport_finished.wait(0.5)


@pytest.mark.parametrize("code", [301, 302, 303, 307, 308])
def test_real_redirects_never_drain_slow_intermediate_body(monkeypatch, code):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.5)

    def reply(handler, stop):
        if handler.path == "/final":
            send_json(handler)
            return
        handler.send_response(code)
        handler.send_header("Location", "/final")
        handler.end_headers()
        while not stop.wait(0.03):
            handler.wfile.write(b"redirect-body-must-not-be-read")
            handler.wfile.flush()

    with response_server(reply) as (port, requests):
        assert metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/start") == {
            "version": "1.2.3"
        }
        assert [path for path, _headers in requests] == ["/start", "/final"]


@pytest.mark.parametrize("mode", ["loop", "hops", "time"])
def test_real_redirect_limits_share_one_deadline(monkeypatch, mode):
    monkeypatch.setattr(metadata, "MAX_SECONDS", 0.13 if mode == "time" else 1)

    def reply(handler, stop):
        if mode == "time" and stop.wait(0.06):
            return
        number = int(handler.path.rsplit("/", 1)[-1])
        handler.send_response(302)
        handler.send_header(
            "Location", f"/hop/{number if mode == 'loop' else number+1}"
        )
        handler.end_headers()
        handler.wfile.write(b"do not drain this")

    with response_server(reply) as (port, requests):
        with pytest.raises(TimeoutError if mode == "time" else ValueError) as caught:
            metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/hop/0")
        if mode == "time":
            assert caught.value.transport_finished.wait(0.5)
        assert len(requests) <= metadata.MAX_REDIRECTS + 1
        if mode == "loop":
            assert len(requests) == 1


@pytest.mark.parametrize("encoding", ["gzip", "deflate", "br"])
def test_real_compressed_metadata_is_rejected_before_read(monkeypatch, encoding):
    import http.client

    def forbidden(*args, **kwargs):
        pytest.fail("Compressed metadata reached body reader")

    monkeypatch.setattr(http.client.HTTPResponse, "read1", forbidden)

    def reply(handler, _stop):
        handler.send_response(200)
        handler.send_header("Content-Encoding", encoding)
        handler.send_header("Content-Length", "10")
        handler.end_headers()
        handler.wfile.write(b"compressed")

    with response_server(reply) as (port, _requests):
        with pytest.raises(ValueError, match="Komprimierte"):
            metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/")


def test_multiple_addresses_retry_successfully_before_deadline(monkeypatch):
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    attempts = []

    with response_server(lambda handler, stop: send_json(handler)) as (port, _requests):

        def addresses(host, target_port, *args, **kwargs):
            if host == "metadata-review.invalid":
                return [
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 1)),
                    (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port)),
                ]
            return original_dns(host, target_port, *args, **kwargs)

        def connect(sock, target):
            attempts.append(target)
            if target == ("127.0.0.1", 1):
                raise ConnectionRefusedError("synthetic first-address failure")
            return original_connect(sock, target)

        monkeypatch.setattr(socket, "getaddrinfo", addresses)
        monkeypatch.setattr(socket.socket, "connect", connect)
        assert (
            metadata.fetch_release_metadata(f"http://metadata-review.invalid:{port}/")[
                "version"
            ]
            == "1.2.3"
        )
    assert attempts == [("127.0.0.1", 1), ("127.0.0.1", port)]


@pytest.fixture
def tls_contexts(tmp_path):
    import ssl
    import subprocess

    certificate = tmp_path / "test.crt"
    key = tmp_path / "test.key"
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "1",
            "-subj",
            "/CN=localhost",
            "-addext",
            "subjectAltName=DNS:localhost",
            "-keyout",
            str(key),
            "-out",
            str(certificate),
        ],
        check=True,
        capture_output=True,
    )
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.load_cert_chain(certificate, key)
    client = ssl.create_default_context(cafile=str(certificate))
    assert client.check_hostname and client.verify_mode == ssl.CERT_REQUIRED
    return server, client


@pytest.mark.parametrize("kind", ["untrusted", "trusted", "wrong-host"])
def test_real_https_preserves_certificate_and_hostname_verification(
    monkeypatch, tls_contexts, kind
):
    from urllib import error

    server_context, client_context = tls_contexts
    if kind != "untrusted":
        original_builder = metadata.request.build_opener

        def opener(*handlers):
            for handler in handlers:
                if isinstance(handler, metadata.request.HTTPSHandler):
                    handler._context = client_context
            return original_builder(*handlers)

        monkeypatch.setattr(metadata.request, "build_opener", opener)
    with response_server(lambda handler, stop: send_json(handler), server_context) as (
        port,
        _requests,
    ):
        url = f"https://{'127.0.0.1' if kind == 'wrong-host' else 'localhost'}:{port}/"
        if kind == "trusted":
            assert metadata.fetch_release_metadata(url)["version"] == "1.2.3"
        else:
            with pytest.raises(error.URLError, match="CERTIFICATE_VERIFY_FAILED"):
                metadata.fetch_release_metadata(url)


def test_normal_http_proxy_configuration_still_works(monkeypatch):
    with response_server(lambda handler, stop: send_json(handler)) as (port, requests):
        monkeypatch.setenv("http_proxy", f"http://127.0.0.1:{port}")
        monkeypatch.setenv("no_proxy", "")
        assert (
            metadata.fetch_release_metadata(
                "http://metadata-proxy-review.invalid/version"
            )["version"]
            == "1.2.3"
        )
        assert requests[0][0] == "http://metadata-proxy-review.invalid/version"


def test_redirect_requests_do_not_copy_response_secrets():
    def reply(handler, _stop):
        if handler.path == "/final":
            send_json(handler)
            return
        handler.send_response(302)
        handler.send_header(
            "Location", f"http://localhost:{handler.server.server_port}/final"
        )
        handler.send_header("Set-Cookie", "private-test-token=value")
        handler.send_header("Authorization", "Bearer private-test-token")
        handler.end_headers()

    with response_server(reply) as (port, requests):
        assert (
            metadata.fetch_release_metadata(f"http://127.0.0.1:{port}/start")["version"]
            == "1.2.3"
        )
        assert len(requests) == 2
        for _path, headers in requests:
            assert not {key.lower() for key in headers} & {
                "authorization",
                "cookie",
                "proxy-authorization",
            }


@pytest.mark.parametrize("failure", ["json", "size", "timeout", "unreachable"])
def test_update_failures_reach_existing_ui_error_path(monkeypatch, failure):
    import json
    from urllib import error

    from netmon import app as app_module
    from netmon.app import App

    app = App.__new__(App)
    app.tr = lambda key, fallback: fallback
    statuses, logs = [], []
    app._set_about_version_status = statuses.append
    app.log_safe = logs.append
    app.after = lambda delay, callback: callback()
    app.netmon_roots_latest_version_url = "https://metadata.invalid/version"
    app._open_url_with_xdg_open = lambda *args, **kwargs: pytest.fail(
        "Failed metadata opened a download"
    )
    failures = {
        "json": json.JSONDecodeError("synthetic invalid JSON", "{", 1),
        "size": ValueError("Versionsantwort überschreitet das Größenlimit."),
        "timeout": TimeoutError("Versionsdownload: Gesamtzeitlimit überschritten."),
        "unreachable": error.URLError("synthetic endpoint unavailable"),
    }

    def fetch(url):
        raise failures[failure]

    class Immediate:
        def __init__(self, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(app_module, "fetch_release_metadata", fetch)
    monkeypatch.setattr(app_module.threading, "Thread", Immediate)
    app.check_about_latest_version(manual=True)
    assert "nicht verfügbar" in statuses[-1]
    assert logs and app._about_version_check_running is False


def test_missing_version_is_still_rejected_by_app(monkeypatch):
    from netmon import app as app_module
    from netmon.app import App

    app = App.__new__(App)
    app.netmon_roots_latest_version_url = "https://metadata.invalid/version"
    monkeypatch.setattr(app_module, "fetch_release_metadata", lambda url: {})
    with pytest.raises(ValueError, match="keine Version"):
        app._fetch_latest_release_info()
