"""Independent loopback reproductions; never contact OpenAI or use credentials."""

import contextlib
import gzip
import http.client
import importlib
import importlib.util
import json
import os
import select
import socket
import socketserver
import ssl
import subprocess
import sys
import threading
import time
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest

from netmon.services import ai_online_service as online


@pytest.fixture(params=["requests", "urllib"])
def backend(request, monkeypatch):
    if request.param == "requests":
        pytest.importorskip("requests")
    else:
        monkeypatch.setattr(online, "requests", None)
    # Explicitly isolated loopback only; avoid the host's proxy configuration.
    monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")
    return request.param


@pytest.fixture
def endpoint(request, tmp_path, monkeypatch):
    state = {"requests": [], "closed": threading.Event()}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            self.protocol_version = state.get("version", "HTTP/1.0")
            self.close_connection = state.get("close_connection", True)
            state["requests"].append(
                (
                    self.path,
                    dict(self.headers),
                    self.rfile.read(int(self.headers["Content-Length"])),
                )
            )
            try:
                mode = state.get("mode", "normal")
                if mode == "slow_headers":
                    for byte in b"HTTP/1.1 200 OK\r\nX-Slow: " + b"x" * 100:
                        self.connection.sendall(bytes([byte]))
                        time.sleep(0.015)
                    return
                self.send_response(state.get("status", 200))
                if mode == "redirect":
                    self.send_header("Location", "/redirect-target")
                for key, value in state.get("headers", {}).items():
                    self.send_header(key, value)
                self.end_headers()
                if mode == "stall":
                    state["closed"].wait(1)
                elif mode == "trickle":
                    for _ in range(100):
                        self.wfile.write(b" ")
                        self.wfile.flush()
                        time.sleep(0.015)
                elif mode == "chunk_header":
                    for byte in b"1;extension=" + b"x" * 100:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.015)
                elif mode == "disconnect":
                    self.wfile.write(b'{"output_text":')
                    self.wfile.flush()
                    self.connection.shutdown(socket.SHUT_RDWR)
                else:
                    self.wfile.write(state.get("body", b'{"output_text":"ok"}'))
            except (OSError, ValueError):
                pass
            finally:
                state["closed"].set()

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    secure = getattr(request, "param", "http") == "https"
    if secure:
        certificate, key = tmp_path / "test.crt", tmp_path / "test.key"
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
                "/CN=127.0.0.1",
                "-addext",
                "subjectAltName=IP:127.0.0.1",
                "-keyout",
                str(key),
                "-out",
                str(certificate),
            ],
            check=True,
            capture_output=True,
        )
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certificate, key)
        state["tls_context"] = context
        server.socket = context.wrap_socket(server.socket, server_side=True)
        client_context = ssl.create_default_context(cafile=str(certificate))
        monkeypatch.setattr(
            ssl, "_create_default_https_context", lambda: client_context
        )
        monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(certificate))
    thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
    )
    thread.start()
    yield f"{'https' if secure else 'http'}://127.0.0.1:{server.server_port}/responses", state
    state["closed"].set()
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)


def response_errors():
    errors = (OSError, ValueError, http.client.HTTPException)
    if online.requests is not None:
        errors += (online.requests.packages.urllib3.exceptions.HTTPError,)
    return errors


def post(endpoint, timeout=2):
    url, _ = endpoint
    return online.AiOnlineService()._post_json(
        url, {"Content-Type": "application/json"}, {"input": "hello"}, timeout
    )


def test_normal_json(backend, endpoint):
    assert post(endpoint) == (200, '{"output_text":"ok"}')
    assert endpoint[1]["requests"][0][1]["Accept-Encoding"] == "identity"


@pytest.mark.parametrize("status", [400, 429, 500])
def test_normal_api_error(backend, endpoint, status):
    state = endpoint[1]
    state.update(status=status, body=b'{"error":{"message":"quota"}}')
    assert post(endpoint) == (status, '{"error":{"message":"quota"}}')


@pytest.mark.parametrize(
    "status,size", [(200, 2 * 1024 * 1024 + 1), (400, 65537), (500, 65537)]
)
@pytest.mark.parametrize("declared", [True, False])
def test_transport_limit(backend, endpoint, status, size, declared):
    state = endpoint[1]
    state.update(status=status, body=b" " * size)
    if declared:
        state["headers"] = {"Content-Length": str(size)}
    with pytest.raises(ValueError, match="transport byte limit"):
        post(endpoint)


@pytest.mark.parametrize("encoding", ["gzip", "deflate"])
def test_normal_compressed_json(backend, endpoint, encoding):
    raw = b'{"output_text":"ok"}'
    endpoint[1].update(
        body=gzip.compress(raw) if encoding == "gzip" else zlib.compress(raw),
        headers={"Content-Encoding": encoding},
    )
    assert post(endpoint) == (200, raw.decode())


def test_large_compressed_transport(backend, endpoint):
    body = gzip.compress(os.urandom(2 * 1024 * 1024 + 1000))
    endpoint[1].update(body=body, headers={"Content-Encoding": "gzip"})
    with pytest.raises(ValueError, match="transport byte limit"):
        post(endpoint)


@pytest.mark.parametrize("status,size", [(200, 4 * 1024 * 1024 + 1), (500, 65537)])
def test_decompression_bomb(backend, endpoint, status, size):
    endpoint[1].update(
        status=status,
        body=gzip.compress(b" " * size),
        headers={"Content-Encoding": "gzip"},
    )
    with pytest.raises(ValueError, match="decoded byte limit"):
        post(endpoint)


@pytest.mark.parametrize("mode", ["trickle", "stall", "chunk_header", "slow_headers"])
def test_total_deadline(backend, endpoint, mode):
    endpoint[1]["mode"] = mode
    if mode == "chunk_header":
        endpoint[1]["headers"] = {"Transfer-Encoding": "chunked"}
    start = time.monotonic()
    with pytest.raises(TimeoutError, match="deadline exceeded"):
        post(endpoint, timeout=0.18)
    assert time.monotonic() - start < 0.75


def test_interrupted_body(backend, endpoint):
    endpoint[1].update(mode="disconnect", headers={"Content-Length": "10000"})
    with pytest.raises(response_errors()):
        post(endpoint)


def test_redirect_body_is_bounded_and_not_followed(backend, endpoint):
    endpoint[1].update(mode="redirect", status=307, body=b" " * 65537)
    with pytest.raises(ValueError, match="transport byte limit"):
        post(endpoint)
    assert len(endpoint[1]["requests"]) == 1


@pytest.mark.parametrize("method", ["analyze", "chat"])
@pytest.mark.parametrize("status", [200, 429])
def test_public_functions_unchanged(backend, endpoint, monkeypatch, method, status):
    state = endpoint[1]
    raw = (
        {
            "output_text": "Hallo",
            "usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5},
        }
        if status == 200
        else {"error": {"message": "quota"}}
    )
    state.update(status=status, body=json.dumps(raw).encode())
    service = online.AiOnlineService()
    service.api_key = "test-placeholder"
    original = service._post_json
    monkeypatch.setattr(
        service,
        "_post_json",
        lambda _url, headers, payload, timeout: original(
            endpoint[0], headers, payload, timeout
        ),
    )
    value = "Hallo" if method == "analyze" else [{"role": "user", "content": "Hallo"}]
    assert getattr(service, method)(value) == (
        (True, "Hallo") if status == 200 else (False, "Fehler: quota")
    )
    _, headers, body = state["requests"][0]
    payload = json.loads(body)
    assert headers["Authorization"] == "Bearer test-placeholder"
    assert payload["model"] == "gpt-4.1-mini"
    assert payload["max_output_tokens"] == (1400 if method == "analyze" else 900)
    if status == 200:
        assert service.last_usage_text == "Gesamt: 5 | Input: 3 | Output: 2"


@pytest.mark.parametrize("failure", ["size", "encoding", "deadline", "disconnect"])
@pytest.mark.parametrize("status", [200, 500])
def test_response_resources_closed(backend, endpoint, monkeypatch, failure, status):
    closed = []
    cleanup_done = threading.Event()
    if backend == "requests":
        original = online.requests.Session.send

        def send(session, *args, **kwargs):
            response = original(session, *args, **kwargs)
            close = response.close

            def tracked_close():
                try:
                    return close()
                finally:
                    closed.append(True)
                    cleanup_done.set()

            response.close = tracked_close
            return response

        monkeypatch.setattr(online.requests.Session, "send", send)
    else:
        original = online.urllib.request.OpenerDirector.open

        def track(response):
            close = response.close

            def tracked_close():
                try:
                    return close()
                finally:
                    closed.append(True)
                    cleanup_done.set()

            response.close = tracked_close

        def open_response(opener, *args, **kwargs):
            try:
                response = original(opener, *args, **kwargs)
            except online.urllib.error.HTTPError as exc:
                track(exc)
                raise
            track(response)
            return response

        monkeypatch.setattr(online.urllib.request.OpenerDirector, "open", open_response)
    state = endpoint[1]
    state["status"] = status
    if failure == "size":
        state.update(headers={"Content-Length": "99999999"})
    elif failure == "encoding":
        state.update(headers={"Content-Encoding": "br"})
    elif failure == "deadline":
        state.update(mode="trickle")
    else:
        state.update(mode="disconnect", headers={"Content-Length": "10000"})
    with pytest.raises(response_errors()):
        post(endpoint, timeout=0.18)
    assert cleanup_done.wait(0.5)
    assert closed


@pytest.mark.parametrize("stage", ["dns", "connect"])
def test_late_connect_result_cannot_start_another_request(
    backend, endpoint, monkeypatch, stage
):
    service = online.AiOnlineService()
    release = threading.Event()
    finished = threading.Event()
    entered = threading.Event()
    original_transport = service._post_json_transport
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    attempts = []

    def transport(*args):
        try:
            return original_transport(*args)
        finally:
            finished.set()

    def dns(host, port, *args, **kwargs):
        if stage == "dns":
            entered.set()
            assert release.wait(1)
        addresses = original_dns(host, port, *args, **kwargs)
        return addresses + addresses if stage == "connect" else addresses

    def connect(sock, target):
        attempts.append(target)
        if stage == "connect":
            entered.set()
            assert release.wait(1)
            raise ConnectionRefusedError("synthetic delayed failure")
        return original_connect(sock, target)

    monkeypatch.setattr(service, "_post_json_transport", transport)
    monkeypatch.setattr(socket, "getaddrinfo", dns)
    monkeypatch.setattr(socket.socket, "connect", connect)
    start = time.monotonic()
    try:
        with pytest.raises(TimeoutError, match="deadline exceeded"):
            service._post_json(endpoint[0], {}, {}, 0.15)
        assert entered.is_set()
        assert time.monotonic() - start < 0.6
        with pytest.raises(TimeoutError, match="still finishing"):
            service._post_json(endpoint[0], {}, {}, 0.15)
    finally:
        release.set()
        assert finished.wait(0.5)
    assert not endpoint[1]["requests"]
    assert len(attempts) == (1 if stage == "connect" else 0)


@pytest.mark.parametrize(
    "mode", ["short_gzip", "trailing_gzip", "unsupported", "bad_length"]
)
def test_malformed_payload_rejected(backend, endpoint, mode):
    state = endpoint[1]
    if mode == "unsupported":
        state.update(headers={"Content-Encoding": "br"})
    elif mode == "bad_length":
        state.update(headers={"Content-Length": "-1"})
    else:
        body = gzip.compress(b"{}")
        state.update(
            body=body[:-3] if mode == "short_gzip" else body + b"junk",
            headers={"Content-Encoding": "gzip"},
        )
    with pytest.raises(response_errors()):
        post(endpoint)


@pytest.mark.parametrize("method", ["analyze", "chat"])
def test_image_attachment_preserved(backend, endpoint, monkeypatch, method):
    service = online.AiOnlineService()
    service.api_key = "test-placeholder"
    monkeypatch.setattr(
        service, "image_to_data_url", lambda path: "data:image/png;base64,AA=="
    )
    original = service._post_json
    monkeypatch.setattr(
        service,
        "_post_json",
        lambda _url, headers, payload, timeout: original(
            endpoint[0], headers, payload, timeout
        ),
    )
    value = "image" if method == "analyze" else [{"role": "user", "content": "image"}]
    assert getattr(service, method)(
        value, files=[{"type": "image", "path": "synthetic.png"}]
    ) == (True, "ok")
    payload = json.loads(endpoint[1]["requests"][0][2])
    assert payload["input"][-1]["content"][-1] == {
        "type": "input_image",
        "image_url": "data:image/png;base64,AA==",
        "detail": "auto",
    }


@pytest.mark.parametrize("endpoint", ["https"], indirect=True)
@pytest.mark.parametrize("mode", ["normal", "trickle"])
def test_verified_tls_transport(backend, endpoint, mode):
    if mode == "normal":
        assert post(endpoint) == (200, '{"output_text":"ok"}')
    else:
        endpoint[1]["mode"] = mode
        with pytest.raises(TimeoutError, match="deadline exceeded"):
            post(endpoint, timeout=0.25)


def test_socks_proxy_has_no_direct_fallback(endpoint, monkeypatch):
    requests = pytest.importorskip("requests")
    selected = []

    def unavailable(proxy, **kwargs):
        selected.append(proxy)
        raise requests.exceptions.InvalidSchema("Synthetic unavailable SOCKS provider")

    monkeypatch.setattr(requests.adapters, "SOCKSProxyManager", unavailable)
    monkeypatch.setenv("HTTP_PROXY", "socks5h://127.0.0.1:9")
    monkeypatch.setenv("http_proxy", "socks5h://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "")
    monkeypatch.setenv("no_proxy", "")
    with pytest.raises(requests.exceptions.InvalidSchema, match="Synthetic"):
        post(endpoint)
    assert selected == ["socks5h://127.0.0.1:9"]
    assert not endpoint[1]["requests"]


@pytest.mark.parametrize("endpoint", ["http", "https"], indirect=True)
@pytest.mark.parametrize("close", [False, True])
@pytest.mark.parametrize("status", [200, 429])
def test_v2_fixed_length_http11_response(backend, endpoint, close, status):
    body = (
        b'{"output_text":"ok"}' if status == 200 else b'{"error":{"message":"quota"}}'
    )
    endpoint[1].update(
        version="HTTP/1.1",
        close_connection=close,
        status=status,
        body=body,
        headers={
            "Content-Length": str(len(body)),
            "Connection": "close" if close else "keep-alive",
        },
    )
    assert post(endpoint) == (status, body.decode())


@pytest.mark.parametrize("method", ["chat", "analyze"])
@pytest.mark.parametrize("endpoint", ["http", "https"], indirect=True)
def test_v2_public_method_fixed_length(backend, endpoint, monkeypatch, method):
    body = json.dumps({"output_text": "ok", "usage": {"total_tokens": 3}}).encode()
    endpoint[1].update(body=body, headers={"Content-Length": str(len(body))})
    service = online.AiOnlineService()
    service.api_key = "synthetic-placeholder"
    original = service._post_json
    monkeypatch.setattr(
        service,
        "_post_json",
        lambda _url, headers, payload, timeout: original(
            endpoint[0], headers, payload, timeout
        ),
    )
    value = "hello" if method == "analyze" else [{"role": "user", "content": "hello"}]
    assert getattr(service, method)(value) == (True, "ok")
    assert service.last_usage_text == "Gesamt: 3 | Input: 0 | Output: 0"


@pytest.mark.parametrize("encoding", ["gzip", "deflate"])
def test_v2_compressed_content_length(backend, endpoint, encoding):
    body = b'{"output_text":"ok"}'
    wire = gzip.compress(body) if encoding == "gzip" else zlib.compress(body)
    endpoint[1].update(
        body=wire,
        headers={"Content-Encoding": encoding, "Content-Length": str(len(wire))},
    )
    assert post(endpoint) == (200, body.decode())


def _finish_watches(watches):
    for timer, guard in watches:
        timer.cancel()
        timer.join()
        guard.close()


def test_v2_watchdog_survives_original_socket_detach():
    left, right = socket.socketpair()
    watches = []
    try:
        online._arm_deadline(left, time.monotonic() + 0.04, watches)
        with socket.socket(fileno=left.detach()) as wrapped:
            right.settimeout(0.5)
            assert right.recv(1) == b""
            assert wrapped.fileno() >= 0
            assert not os.get_inheritable(watches[0][1].fileno())
    finally:
        left.close()
        right.close()
        _finish_watches(watches)
    assert all(guard.fileno() == -1 for _, guard in watches)


def test_v2_watch_registration_failure_closes_duplicate(monkeypatch):
    captured = []
    original = socket.fromfd

    def duplicate(*args):
        sock = original(*args)
        captured.append(sock)
        return sock

    def cannot_start(_timer):
        raise RuntimeError("Synthetic timer start failure")

    monkeypatch.setattr(socket, "fromfd", duplicate)
    monkeypatch.setattr(threading.Timer, "start", cannot_start)
    left, right = socket.socketpair()
    try:
        with pytest.raises(RuntimeError, match="Synthetic"):
            online._arm_deadline(left, time.monotonic() + 1, [])
    finally:
        left.close()
        right.close()
    assert len(captured) == 1 and captured[0].fileno() == -1


@pytest.mark.parametrize("mode", ["normal", "size", "deadline"])
def test_v2_service_closes_watch_descriptors(backend, endpoint, monkeypatch, mode):
    guards = []
    original = online._arm_deadline

    def watch(sock, deadline, watches):
        original(sock, deadline, watches)
        guards.append(watches[-1][1])

    monkeypatch.setattr(online, "_arm_deadline", watch)
    service = online.AiOnlineService()
    if mode == "size":
        endpoint[1]["headers"] = {"Content-Length": "9999999"}
    elif mode == "deadline":
        endpoint[1]["mode"] = "trickle"
    if mode == "normal":
        assert service._post_json(endpoint[0], {}, {}, 1)[0] == 200
    else:
        with pytest.raises(ValueError if mode == "size" else TimeoutError):
            service._post_json(endpoint[0], {}, {}, 0.15)
    end = time.monotonic() + 0.5
    while service._http_lock.locked() and time.monotonic() < end:
        time.sleep(0.005)
    assert not service._http_lock.locked()
    assert guards and all(guard.fileno() == -1 for guard in guards)


@contextlib.contextmanager
def _proxy_server(endpoint, *, tls=False, socks=False, stall=False):
    # Forward only to this fixture's own loopback origin, never arbitrary hosts.
    from urllib.parse import urlsplit

    target = urlsplit(endpoint[0])
    state = {"connections": 0, "targets": [], "closed": threading.Event()}

    class Handler(socketserver.BaseRequestHandler):
        def exact(self, size):
            data = bytearray()
            while len(data) < size:
                piece = self.request.recv(size - len(data))
                if not piece:
                    raise EOFError
                data.extend(piece)
            return bytes(data)

        def cstring(self):
            data = bytearray()
            while True:
                piece = self.exact(1)
                if piece == b"\0":
                    return bytes(data)
                data.extend(piece)
                if len(data) > 255:
                    raise ValueError("Long fixture handshake")

        def handle(self):
            incoming = self.request
            state["connections"] += 1
            try:
                if socks:
                    version = self.exact(1)
                    if version == b"\x05":
                        methods = self.exact(self.exact(1)[0])
                        assert 0 in methods
                        incoming.sendall(b"\x05\0")
                        request = self.exact(4)
                        assert request[:3] == b"\x05\x01\0"
                        kind = request[3]
                        if kind == 1:
                            host = socket.inet_ntop(socket.AF_INET, self.exact(4))
                        elif kind == 3:
                            host = self.exact(self.exact(1)[0]).decode()
                        elif kind == 4:
                            host = socket.inet_ntop(socket.AF_INET6, self.exact(16))
                        else:
                            raise ValueError("Unknown fixture SOCKS address")
                        port = int.from_bytes(self.exact(2), "big")
                        reply = b"\x05\0\0\x01\x7f\0\0\x01\0\0"
                    else:
                        assert version == b"\x04"
                        assert self.exact(1) == b"\x01"
                        port = int.from_bytes(self.exact(2), "big")
                        address = self.exact(4)
                        self.cstring()  # Synthetic SOCKS4 user ID.
                        host = (
                            self.cstring().decode()
                            if address[:3] == b"\0\0\0" and address[3] != 0
                            else socket.inet_ntop(socket.AF_INET, address)
                        )
                        reply = b"\0\x5a\0\0\0\0\0\0"
                else:
                    header = bytearray()
                    while not header.endswith(b"\r\n\r\n"):
                        header.extend(self.exact(1))
                        if len(header) > 4096:
                            raise ValueError("Long fixture CONNECT")
                    method, destination, _version = (
                        header.split(b"\r\n", 1)[0].decode().split()
                    )
                    assert method == "CONNECT"
                    host, port = destination.rsplit(":", 1)
                    port = int(port)
                    reply = b"HTTP/1.1 200 Connection established\r\n\r\n"
                assert (
                    host in {"127.0.0.1", "socks-target.invalid"}
                    and port == target.port
                )
                state["targets"].append(host)
                if stall:
                    for byte in reply:
                        incoming.sendall(bytes([byte]))
                        time.sleep(0.04)
                    return
                with socket.create_connection(
                    ("127.0.0.1", port), timeout=2
                ) as outgoing:
                    incoming.sendall(reply)
                    end = time.monotonic() + 3
                    while time.monotonic() < end:
                        ready, _, _ = select.select([incoming, outgoing], [], [], 0.025)
                        if (
                            isinstance(incoming, ssl.SSLSocket)
                            and incoming.pending()
                            and incoming not in ready
                        ):
                            ready.append(incoming)
                        for source in ready:
                            data = source.recv(65536)
                            if not data:
                                return
                            (outgoing if source is incoming else incoming).sendall(data)
            except (OSError, EOFError, ValueError):
                pass
            finally:
                state["closed"].set()

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    server = Server(("127.0.0.1", 0), Handler)
    if tls:
        server.socket = endpoint[1]["tls_context"].wrap_socket(
            server.socket, server_side=True
        )
    thread = threading.Thread(
        target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
    )
    thread.start()
    try:
        yield server.server_address[1], state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)


def _set_proxy(monkeypatch, proxy):
    monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")
    for name in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        monkeypatch.setenv(name, proxy)
    for name in ("NO_PROXY", "no_proxy"):
        monkeypatch.setenv(name, "")


@pytest.mark.parametrize("endpoint", ["https"], indirect=True)
@pytest.mark.parametrize("secure_proxy", [False, True])
@pytest.mark.parametrize("mode", ["normal", "slow_headers", "trickle"])
def test_v2_https_proxy_transport_and_cleanup(
    endpoint, monkeypatch, secure_proxy, mode
):
    pytest.importorskip("requests")
    errors = []
    monkeypatch.setattr(
        threading, "excepthook", lambda args: errors.append(str(args.exc_value))
    )
    endpoint[1]["mode"] = mode
    with _proxy_server(endpoint, tls=secure_proxy) as (port, state):
        _set_proxy(
            monkeypatch, f'{"https" if secure_proxy else "http"}://127.0.0.1:{port}'
        )
        service = online.AiOnlineService()
        if mode == "normal":
            assert service._post_json(endpoint[0], {}, {}, 2) == (
                200,
                '{"output_text":"ok"}',
            )
        else:
            with pytest.raises(TimeoutError):
                service._post_json(endpoint[0], {}, {}, 0.20)
        end = time.monotonic() + 0.5
        while service._http_lock.locked() and time.monotonic() < end:
            time.sleep(0.005)
        assert not service._http_lock.locked()
        assert state["closed"].wait(0.5)
        assert not errors
        # Reuse exactly this instance after abort; no stale timer may touch it.
        endpoint[1]["mode"] = "normal"
        assert service._post_json(endpoint[0], {}, {}, 2)[0] == 200
        assert len(endpoint[1]["requests"]) == 2


@pytest.fixture(params=["pysocks", "installed-protocol-adapter"])
def socks_provider(request, monkeypatch):
    requests = pytest.importorskip("requests")
    import urllib3

    if request.param == "pysocks":
        provider = pytest.importorskip(
            "socks",
            reason="Optional PySocks not installed; no installation during review",
        )
    else:
        # Exercise real SOCKS4/5 wire handshakes with existing distro code,
        # adapted only to the public PySocks constructor/set_proxy interface.
        # This does NOT claim to qualify an absent PySocks installation.
        if not os.path.isfile("/usr/lib/python3/dist-packages/yt_dlp/socks.py"):
            pytest.skip("Existing SOCKS protocol adapter unavailable")
        monkeypatch.syspath_prepend("/usr/lib/python3/dist-packages")
        legacy = importlib.import_module("yt_dlp.socks")

        class AdapterSocket(legacy.sockssocket):
            def set_proxy(self, version, host, port, rdns, username, password):
                kind = (
                    legacy.ProxyType.SOCKS5
                    if version == 2
                    else legacy.ProxyType.SOCKS4A if rdns else legacy.ProxyType.SOCKS4
                )
                self.setproxy(kind, host, port, rdns, username, password)

        provider = SimpleNamespace(
            socksocket=AdapterSocket,
            SOCKS4=1,
            SOCKS5=2,
            PROXY_TYPE_SOCKS4=1,
            PROXY_TYPE_SOCKS5=2,
            ProxyError=legacy.ProxyError,
        )
        monkeypatch.setitem(sys.modules, "socks", provider)
    # Scoped load: never replace global urllib3 pool classes or leave a cached
    # synthetic PySocks module in later tests.
    path = os.path.join(os.path.dirname(urllib3.__file__), "contrib", "socks.py")
    spec = importlib.util.spec_from_file_location(
        "urllib3.contrib._netmon_test_socks", path
    )
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    monkeypatch.setattr(
        requests.adapters, "SOCKSProxyManager", native.SOCKSProxyManager
    )
    return request.param


@pytest.mark.parametrize("scheme", ["socks4", "socks4a", "socks5", "socks5h"])
def test_v2_socks_protocol_and_dns_policy(
    socks_provider, endpoint, monkeypatch, scheme
):
    lookups = []
    original = socket.getaddrinfo

    def dns(host, *args, **kwargs):
        lookups.append(host)
        return original(
            "127.0.0.1" if host == "socks-target.invalid" else host, *args, **kwargs
        )

    monkeypatch.setattr(socket, "getaddrinfo", dns)
    with _proxy_server(endpoint, socks=True) as (port, state):
        _set_proxy(monkeypatch, f"{scheme}://127.0.0.1:{port}")
        service = online.AiOnlineService()
        url = endpoint[0].replace("127.0.0.1", "socks-target.invalid")
        assert service._post_json(url, {}, {}, 2) == (200, '{"output_text":"ok"}')
        remote = scheme in {"socks4a", "socks5h"}
        assert state["targets"] == ["socks-target.invalid" if remote else "127.0.0.1"]
        assert ("socks-target.invalid" in lookups) is not remote
        assert len(endpoint[1]["requests"]) == 1


@pytest.mark.parametrize("endpoint", ["https"], indirect=True)
@pytest.mark.parametrize("scheme", ["socks4a", "socks5h"])
def test_v2_verified_https_through_socks(socks_provider, endpoint, monkeypatch, scheme):
    with _proxy_server(endpoint, socks=True) as (port, state):
        _set_proxy(monkeypatch, f"{scheme}://127.0.0.1:{port}")
        assert post(endpoint) == (200, '{"output_text":"ok"}')
        assert state["targets"] == ["127.0.0.1"]


@pytest.mark.parametrize("scheme", ["socks4a", "socks5h"])
def test_v2_socks_handshake_trickle_deadline(
    socks_provider, endpoint, monkeypatch, scheme
):
    with _proxy_server(endpoint, socks=True, stall=True) as (port, state):
        _set_proxy(monkeypatch, f"{scheme}://127.0.0.1:{port}")
        service = online.AiOnlineService()
        with pytest.raises(TimeoutError):
            service._post_json(endpoint[0], {}, {}, 0.15)
        end = time.monotonic() + 0.5
        while service._http_lock.locked() and time.monotonic() < end:
            time.sleep(0.005)
        assert not service._http_lock.locked()
        assert not endpoint[1]["requests"]
        assert state["closed"].wait(0.5)


@pytest.mark.parametrize("stage", ["proxy-dns", "target-dns", "connect"])
def test_v2_socks_late_phase_cannot_send_request(
    socks_provider, endpoint, monkeypatch, stage
):
    original_dns = socket.getaddrinfo
    original_connect = socket.socket.connect
    released = threading.Event()
    entered = threading.Event()
    attempts = []

    with _proxy_server(endpoint, socks=True) as (port, state):
        _set_proxy(monkeypatch, f"socks5://127.0.0.1:{port}")

        def dns(host, *args, **kwargs):
            block = host == (
                "socks-target.invalid" if stage == "target-dns" else "127.0.0.1"
            )
            if stage != "connect" and block:
                entered.set()
                assert released.wait(1)
            result = original_dns(
                "127.0.0.1" if host == "socks-target.invalid" else host, *args, **kwargs
            )
            return result + result  # Must not try a second proxy after expiry.

        def connect(sock, target):
            attempts.append(target)
            result = original_connect(sock, target)
            if stage == "connect":
                entered.set()
                assert released.wait(1)
            return result

        monkeypatch.setattr(socket, "getaddrinfo", dns)
        monkeypatch.setattr(socket.socket, "connect", connect)
        service = online.AiOnlineService()
        url = endpoint[0].replace("127.0.0.1", "socks-target.invalid")
        try:
            with pytest.raises(TimeoutError):
                service._post_json(url, {}, {}, 0.15)
            assert entered.is_set()
        finally:
            released.set()
        end = time.monotonic() + 0.5
        while service._http_lock.locked() and time.monotonic() < end:
            time.sleep(0.005)
        assert not service._http_lock.locked()
        assert len(attempts) == (1 if stage == "connect" else 0)
        assert not state["targets"]
        assert not endpoint[1]["requests"]


@pytest.mark.parametrize("unknown_proxy", [None, "socks5h"])
def test_v2_unknown_socks_manager_is_rejected(endpoint, monkeypatch, unknown_proxy):
    requests = pytest.importorskip("requests")
    monkeypatch.setattr(
        requests.adapters,
        "SOCKSProxyManager",
        lambda *args, **kwargs: SimpleNamespace(
            proxy=SimpleNamespace(scheme=unknown_proxy), clear=lambda: None
        ),
    )
    _set_proxy(monkeypatch, "socks5h://127.0.0.1:9")
    with pytest.raises(ValueError, match="no fallback"):
        post(endpoint)
    assert not endpoint[1]["requests"]


def test_v2_missing_native_socks_contract_cannot_connect(monkeypatch):
    monkeypatch.setitem(sys.modules, "socks", SimpleNamespace(SOCKS4=1))
    attempted = []
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args: attempted.append(args))
    connection = online._budget_connection(
        http.client.HTTPConnection, time.monotonic() + 1, [], socks_proxy=True
    )("127.0.0.1", 80)
    with pytest.raises(AttributeError, match="_socks_options"):
        connection._new_conn()
    assert not attempted


@pytest.mark.parametrize("endpoint", ["https"], indirect=True)
def test_v2_stalled_tls_handshake_stops_transport(backend, endpoint, monkeypatch):
    # This local plaintext fixture intentionally never answers a TLS handshake.
    with _proxy_server(endpoint) as (port, state):
        monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        monkeypatch.setenv("no_proxy", "127.0.0.1")
        service = online.AiOnlineService()
        start = time.monotonic()
        with pytest.raises(TimeoutError):
            service._post_json(f"https://127.0.0.1:{port}/responses", {}, {}, 0.15)
        assert time.monotonic() - start < 0.7
        end = time.monotonic() + 0.5
        while service._http_lock.locked() and time.monotonic() < end:
            time.sleep(0.005)
        assert not service._http_lock.locked()
        assert state["closed"].wait(0.5)
        assert state["connections"] == 1 and not state["targets"]
        assert not endpoint[1]["requests"]


def test_v2_socks_ipv6_proxy_scope_and_provider_error_cleanup(monkeypatch):
    captured = []
    sockets = []

    class ProviderSocket(socket.socket):
        def __init__(self, *args):
            super().__init__(*args)
            sockets.append(self)

        def set_proxy(self, version, host, port, rdns, username, password):
            captured.append(host)

        def connect(self, target):
            raise ValueError("Synthetic provider failure")

    monkeypatch.setitem(
        sys.modules, "socks", SimpleNamespace(socksocket=ProviderSocket)
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args: [
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("fe80::1", 1080, 0, 7),
            )
        ],
    )
    connection = SimpleNamespace(
        host="synthetic.invalid",
        port=443,
        source_address=None,
        socket_options=[],
        _socks_options={
            "proxy_host": "synthetic-proxy.invalid",
            "proxy_port": 1080,
            "socks_version": 2,
            "rdns": True,
            "username": None,
            "password": None,
        },
    )
    watches = []
    try:
        with pytest.raises(ValueError, match="Synthetic provider"):
            online._connect_socks_with_budget(connection, time.monotonic() + 1, watches)
    finally:
        _finish_watches(watches)
    assert captured == ["fe80::1%7"]
    assert sockets and all(sock.fileno() == -1 for sock in sockets)
    assert all(guard.fileno() == -1 for _, guard in watches)


def test_v2_connect_watch_failure_releases_all_descriptors(monkeypatch):
    original = socket.socket
    owned = []

    def create(*args, **kwargs):
        sock = original(*args, **kwargs)
        owned.append(sock)
        return sock

    def cannot_start(timer):
        raise RuntimeError("Synthetic timer failure before connect")

    monkeypatch.setattr(socket, "socket", create)
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *args: [
            (
                socket.AF_INET,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("127.0.0.1", 9),
            )
        ],
    )
    monkeypatch.setattr(threading.Timer, "start", cannot_start)
    with pytest.raises(RuntimeError, match="Synthetic"):
        online._connect_with_budget(("synthetic.invalid", 80), time.monotonic() + 1, [])
    assert len(owned) == 2
    assert all(sock.fileno() == -1 for sock in owned)
