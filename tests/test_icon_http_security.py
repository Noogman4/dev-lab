"""No external services: numeric public addresses are routed to owned test sockets."""

import http.client
import socket
import socketserver
import ssl
import subprocess
import threading
import time

import pytest

from netmon.core import icon_http as web

FORBIDDEN = [
    "127.0.0.1",
    "127.255.1.1",
    "::1",
    "10.1.2.3",
    "172.16.0.1",
    "192.168.1.1",
    "fc00::1",
    "fd12::1",
    "169.254.169.254",
    "169.254.170.2",
    "100.100.100.200",
    "100.64.0.1",
    "fe80::1",
    "224.0.0.1",
    "ff02::1",
    "0.0.0.0",
    "::",
    "192.0.2.1",
    "198.51.100.1",
    "203.0.113.1",
    "240.0.0.1",
    "255.255.255.255",
    "2001:db8::1",
    "2002:0808:0808::1",
    "64:ff9b::a00:1",
    "3fff::1",
    "::ffff:127.0.0.1",
    "::ffff:10.0.0.1",
]


def dns_answer(address="8.8.8.8", port=80):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    endpoint = (address, port, 0, 0) if family == socket.AF_INET6 else (address, port)
    return family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", endpoint


@pytest.mark.parametrize("address", FORBIDDEN)
def test_forbidden_addresses_never_connect(monkeypatch, address):
    def forbidden(*_args):
        pytest.fail("No connection may be opened")

    monkeypatch.setattr(web, "_connect", forbidden)
    host = f"[{address}]" if ":" in address else address
    with pytest.raises(ValueError):
        web.fetch(f"http://{host}/icon")


@pytest.mark.parametrize(
    "address", ["8.8.8.8", "1.1.1.1", "2606:4700:4700::1111", "::ffff:8.8.8.8"]
)
def test_public_addresses(address):
    assert web.public_address(address)


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/a",
        "http://user@example.com/",
        "https://user:secret@example.com/",
        "http://example.com:8080/",
        "https://example.com:80/",
        "http://example.com:0/",
        "http://example.com:080/",
        "http://example.com:/",
        "http://example.com:65536/",
        "http://127.1/",
        "http://2130706433/",
        "http://0177.0.0.1/",
        "http://0x7f000001/",
        "http://[fe80::1%25eth0]/",
        "http://example.com./",
        "http://localhost/",
        "http://printer.local/",
        "http://my_host.example.com/",
        "http://-bad.example.com/",
        "http://example.com/\r\nHost:bad",
        "http://example.com\\@127.0.0.1/",
        "http://example.com/a b",
        "http://%31%32%37.0.0.1/",
    ],
)
def test_invalid_urls_fail_before_dns(monkeypatch, url):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_a: pytest.fail("No DNS"))
    with pytest.raises(ValueError):
        web.fetch(url)


@pytest.mark.parametrize(
    "private", ["127.0.0.1", "10.0.0.1", "fd00::1", "169.254.169.254"]
)
def test_mixed_dns_rejected_as_a_whole(monkeypatch, private):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *_a: [dns_answer(), dns_answer(private)]
    )
    monkeypatch.setattr(web, "_connect", lambda *_a: pytest.fail("Mixed DNS connected"))
    with pytest.raises(ValueError):
        web.fetch("http://icons.example.com/")


@pytest.mark.parametrize("wrong_peer", [False, True])
def test_numeric_connect_prevents_rebinding(monkeypatch, wrong_peer):
    resolutions, sockets = [], []

    def resolve(*args):
        resolutions.append(args)
        return [dns_answer("8.8.8.8" if len(resolutions) == 1 else "127.0.0.1")]

    class Socket:
        closed = False

        def __init__(self, *_args):
            sockets.append(self)

        def settimeout(self, timeout):
            assert 0 < timeout <= 10

        def connect(self, endpoint):
            assert endpoint == ("8.8.8.8", 80)

        def getpeername(self):
            return ("127.0.0.1" if wrong_peer else "8.8.8.8", 80)

        def close(self):
            self.closed = True

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    budget = web.DownloadBudget()
    approved = web._resolve(web.parse_url("http://icons.example.com/"), budget)
    monkeypatch.setattr(socket, "socket", Socket)
    if wrong_peer:
        with pytest.raises(ValueError, match="peer"):
            web._connect(approved, budget, 10)
        assert sockets[0].closed
    else:
        assert web._connect(approved, budget, 10) is sockets[0]
    assert len(resolutions) == 1


def test_dns_deadline_and_worker_cap(monkeypatch):
    release, finished = threading.Event(), []

    def stuck(*_args):
        release.wait(2)
        finished.append(True)
        return [dns_answer()]

    monkeypatch.setattr(socket, "getaddrinfo", stuck)
    monkeypatch.setattr(web, "_DNS_SLOTS", threading.BoundedSemaphore(2))
    started = time.monotonic()
    try:
        for _ in range(2):
            with pytest.raises(TimeoutError, match="DNS deadline"):
                web._resolve(
                    web.parse_url("http://icons.example.com/"),
                    web.DownloadBudget(seconds=0.03),
                )
        with pytest.raises(TimeoutError, match="busy"):
            web._resolve(
                web.parse_url("http://icons.example.com/"), web.DownloadBudget()
            )
        assert time.monotonic() - started < 0.5
    finally:
        release.set()
        until = time.monotonic() + 1
        while len(finished) != 2 and time.monotonic() < until:
            time.sleep(0.005)
    assert len(finished) == 2


def test_dns_thread_start_failure_releases_budget_slot(monkeypatch):
    slots = threading.BoundedSemaphore(1)
    monkeypatch.setattr(web, "_DNS_SLOTS", slots)

    def fail(_self):
        raise RuntimeError("thread creation failed")

    monkeypatch.setattr(threading.Thread, "start", fail)
    with pytest.raises(RuntimeError, match="creation"):
        web._resolve(web.parse_url("http://icons.example.com/"), web.DownloadBudget())
    assert slots.acquire(blocking=False)


def response(body=b"icon", headers=b"", status=b"200 OK"):
    return (
        b"HTTP/1.1 " + status + b"\r\nConnection: close\r\n" + headers + b"\r\n" + body
    )


@pytest.fixture
def server_factory(monkeypatch):
    """The only policy bypass is this test-owned connector to loopback servers."""
    servers, connections, requests = [], [], []
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda host, port, *_a: [dns_answer(port=port)]
    )

    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            self.request.settimeout(1)
            first = self.rfile.readline(8192).decode("ascii").split()
            if len(first) < 2:
                return
            headers = []
            while True:
                line = self.rfile.readline(8192)
                if line in (b"\r\n", b"", b"\n"):
                    break
                headers.append(line)
            requests.append((first[1], b"".join(headers)))
            result = self.server.routes.get(first[1], response(status=b"404 Not Found"))
            try:
                if callable(result):
                    result(self.request)
                else:
                    self.request.sendall(result)
            except (OSError, ValueError):
                pass

    class Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    def start(routes, context=None):
        server = Server(("127.0.0.1", 0), Handler)
        server.routes = routes
        if context:
            server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(
            target=lambda: server.serve_forever(poll_interval=0.01), daemon=True
        )
        thread.start()
        servers.append((server, thread))

        def connect(approved, budget, timeout):
            assert approved[0][1][0] == "8.8.8.8"
            connections.append(approved)
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(min(timeout, budget.remaining()))
            client.connect(server.server_address)
            return client

        monkeypatch.setattr(web, "_connect", connect)
        return requests, connections

    yield start
    for server, thread in servers:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)


@pytest.mark.parametrize(
    "headers,body,expected",
    [
        (b"", b"icon", b"icon"),
        (b"Content-Length: 4\r\n", b"icon", b"icon"),
        (b"Transfer-Encoding: chunked\r\n", b"4\r\nicon\r\n0\r\n\r\n", b"icon"),
        # A smaller declared length defines the entire response; no reuse or trailing decoding.
        (b"Content-Length: 2\r\n", b"icon", b"ic"),
    ],
)
def test_real_http_public_icons(server_factory, monkeypatch, headers, body, expected):
    requests, _ = server_factory({"/": response(body, headers)})
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:9")
    result = web.fetch("http://icons.example.com/", limit=4)
    assert result.data == expected
    assert b"Host: icons.example.com\r\n" in requests[0][1]
    assert b"Accept-Encoding: identity\r\n" in requests[0][1]
    assert b"Authorization:" not in requests[0][1]


@pytest.mark.parametrize(
    "headers,body",
    [
        (b"", b"x" * 65),
        (b"Content-Length: 65\r\n", b""),
        (b"Content-Length: 10\r\n", b"tiny"),
        (b"Content-Length: -1\r\n", b"x"),
        (b"Content-Length: nope\r\n", b"x"),
        (b"Content-Length: 1\r\nContent-Length: 1\r\n", b"x"),
        (b"Content-Length: 1\r\nTransfer-Encoding: chunked\r\n", b"x"),
        (b"Content-Encoding: gzip\r\n", b"x"),
        (b"Transfer-Encoding: chunked\r\n", b"41\r\n" + b"x" * 65 + b"\r\n0\r\n\r\n"),
        (b"Transfer-Encoding: chunked\r\n", b"bad-chunk\r\n"),
        (b"X-Large: " + b"x" * web.MAX_CONTROL_BYTES + b"\r\n", b"x"),
    ],
)
def test_real_http_bad_framing_or_overflow(server_factory, headers, body):
    server_factory({"/": response(body, headers)})
    with pytest.raises((ValueError, OSError, http.client.HTTPException)):
        web.fetch("http://icons.example.com/", limit=64)


@pytest.mark.parametrize("limit", [web.HTML_BYTES, web.MANIFEST_BYTES, web.ICON_BYTES])
def test_each_streamed_byte_limit(server_factory, limit):
    server_factory({"/": response(b"x" * (limit + 1))})
    with pytest.raises(ValueError, match="limit"):
        web.fetch("http://icons.example.com/", limit=limit)


def test_bounded_read_calls_and_cumulative_budget(server_factory, monkeypatch):
    server_factory({"/": response(b"x" * 70000)})
    original, sizes = http.client.HTTPResponse.read1, []

    def read(self, size):
        sizes.append(size)
        return original(self, size)

    monkeypatch.setattr(http.client.HTTPResponse, "read1", read)
    budget = web.DownloadBudget(max_bytes=100000, max_requests=3)
    assert len(web.fetch("http://icons.example.com/", budget=budget).data) == 70000
    with pytest.raises(ValueError, match="byte budget"):
        web.fetch("http://icons.example.com/", budget=budget)
    assert max(sizes) <= 64 * 1024
    assert budget.received == 100001


@pytest.mark.parametrize(
    "target",
    [
        "http://127.0.0.1/",
        "http://[::1]/",
        "http://169.254.169.254/",
        "http://10.0.0.1/",
        "http://[fd00::1]/",
        "file:///etc/passwd",
        "http://user@example.com/",
        "http://example.com:8080/",
    ],
)
def test_redirect_private_or_invalid_never_connected(server_factory, target):
    requests, connections = server_factory(
        {"/": response(headers=f"Location: {target}\r\n".encode(), status=b"302 Found")}
    )
    with pytest.raises(ValueError):
        web.fetch("http://icons.example.com/")
    assert len(requests) == len(connections) == 1


def test_redirect_body_not_drained(server_factory):
    stopped = threading.Event()

    def huge_redirect(sock):
        sock.sendall(
            response(
                headers=b"Location: /final\r\nContent-Length: 999999999\r\n",
                status=b"302 Found",
            )
        )
        # Do not transmit the declared body; a draining implementation would block.
        sock.settimeout(0.5)
        try:
            assert sock.recv(1) == b""
            stopped.set()
        except OSError:
            pass

    requests, _ = server_factory({"/": huge_redirect, "/final": response()})
    assert (
        web.fetch(
            "http://icons.example.com/", budget=web.DownloadBudget(seconds=0.5)
        ).data
        == b"icon"
    )
    assert stopped.wait(0.5)
    assert len(requests) == 2


@pytest.mark.parametrize("loop", [False, True])
def test_redirect_budget_and_loops(server_factory, loop):
    routes = {
        f"/{i}": response(
            headers=f"Location: /{0 if loop else i + 1}\r\n".encode(),
            status=b"302 Found",
        )
        for i in range(5)
    }
    requests, _ = server_factory(routes)
    with pytest.raises(ValueError, match="redirect"):
        web.fetch("http://icons.example.com/0")
    assert len(requests) == (1 if loop else 4)


def test_origin_rechecked_on_redirect(server_factory):
    requests, _ = server_factory(
        {
            "/": response(
                headers=b"Location: http://other.example.com/\r\n", status=b"302 Found"
            )
        }
    )
    with pytest.raises(ValueError, match="cross-origin"):
        web.fetch("http://icons.example.com/", origin=("http", "icons.example.com", 80))
    assert len(requests) == 1


@pytest.mark.parametrize(
    "header", ["Authorization", "Cookie", "Proxy-Authorization", "Referer", "Host"]
)
def test_sensitive_headers_forbidden(header):
    with pytest.raises(ValueError, match="header"):
        web.fetch("https://icons.example.com/", headers={header: "secret"})


def test_request_budget_stops_before_another_connection(server_factory):
    requests, connections = server_factory({"/": response()})
    budget = web.DownloadBudget(max_requests=1)
    assert web.fetch("http://icons.example.com/", budget=budget).data == b"icon"
    with pytest.raises(ValueError, match="request budget"):
        web.fetch("http://icons.example.com/", budget=budget)
    assert len(requests) == len(connections) == 1


def test_exhausted_byte_budget_blocks_later_candidate_connections(server_factory):
    requests, connections = server_factory({"/": response(b"x" * 65)})
    budget = web.DownloadBudget(max_bytes=64)
    with pytest.raises(ValueError, match="byte budget"):
        web.fetch("http://icons.example.com/", budget=budget)
    with pytest.raises(ValueError, match="byte budget"):
        web.fetch("http://icons.example.com/next-candidate", budget=budget)
    assert budget.received == 65
    assert len(requests) == len(connections) == 1


@pytest.mark.parametrize(
    "locations",
    [
        b"Location: /a\r\nLocation: /b\r\n",
        b"Location: \r\n",
        b"Location: http://example.com/a b\r\n",
        b"Location: //\r\n",
    ],
)
def test_ambiguous_redirect_rejected(server_factory, locations):
    requests, _ = server_factory(
        {"/": response(headers=locations, status=b"302 Found")}
    )
    with pytest.raises(ValueError):
        web.fetch("http://icons.example.com/")
    assert len(requests) == 1


def test_allowed_service_redirect_and_forbidden_third_origin(server_factory):
    requests, _ = server_factory(
        {
            "/": response(
                headers=b"Location: http://cdn.example.com/ok\r\n", status=b"302 Found"
            ),
            "/ok": response(
                headers=b"Location: http://other.example.com/\r\n", status=b"302 Found"
            ),
        }
    )
    with pytest.raises(ValueError, match="cross-origin"):
        web.fetch(
            "http://icons.example.com/",
            origins=frozenset(
                {("http", "icons.example.com", 80), ("http", "cdn.example.com", 80)}
            ),
        )
    assert len(requests) == 2


def test_dns_and_connect_failures_no_transport_fallback(monkeypatch):
    def failure(*_args):
        raise socket.gaierror("not found")

    monkeypatch.setattr(socket, "getaddrinfo", failure)
    monkeypatch.setattr(
        web, "_connect", lambda *_a: pytest.fail("DNS failure connected")
    )
    with pytest.raises(OSError, match="DNS failed"):
        web.fetch("http://icons.example.com/")


@pytest.mark.parametrize("stage", ["headers", "body"])
def test_total_deadline_not_renewed_by_drip(server_factory, stage):
    def slow(sock):
        if stage == "body":
            sock.sendall(response(headers=b"Content-Length: 100\r\n"))
            data = b"x" * 100
        else:
            data = b"HTTP/1.1 200 OK\r\nX-Slow: " + b"x" * 100
        for byte in data:
            sock.sendall(bytes([byte]))
            time.sleep(0.015)

    server_factory({"/": slow})
    started = time.monotonic()
    with pytest.raises(TimeoutError):
        web.fetch(
            "http://icons.example.com/",
            timeout=1,
            budget=web.DownloadBudget(seconds=0.12),
        )
    assert time.monotonic() - started < 0.8


@pytest.fixture
def tls_contexts(tmp_path):
    cert, key = tmp_path / "cert.pem", tmp_path / "key.pem"
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
            "-keyout",
            str(key),
            "-out",
            str(cert),
            "-subj",
            "/CN=icons.example.com",
            "-addext",
            "subjectAltName=DNS:icons.example.com",
        ],
        check=True,
        capture_output=True,
    )
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    return context, cert


@pytest.mark.parametrize("hostname", ["icons.example.com", "wrong.example.com"])
def test_real_https_keeps_certificate_and_hostname_checks(
    server_factory, tls_contexts, monkeypatch, hostname
):
    context, cert = tls_contexts
    names = []
    context.set_servername_callback(lambda _socket, name, _context: names.append(name))
    server_factory({"/": response()}, context)
    original = ssl.create_default_context

    def client_context():
        result = original(cafile=str(cert))
        assert result.check_hostname and result.verify_mode == ssl.CERT_REQUIRED
        return result

    monkeypatch.setattr(ssl, "create_default_context", client_context)
    if hostname == "icons.example.com":
        assert web.fetch(f"https://{hostname}/").data == b"icon"
    else:
        with pytest.raises(ssl.SSLCertVerificationError):
            web.fetch(f"https://{hostname}/")
    assert names == [hostname]


def test_https_downgrade_rejected(server_factory, tls_contexts, monkeypatch):
    context, cert = tls_contexts
    requests, _ = server_factory(
        {
            "/": response(
                headers=b"Location: http://icons.example.com/\r\n", status=b"302 Found"
            )
        },
        context,
    )
    original = ssl.create_default_context
    monkeypatch.setattr(
        ssl, "create_default_context", lambda: original(cafile=str(cert))
    )
    with pytest.raises(ValueError, match="downgrade"):
        web.fetch("https://icons.example.com/")
    assert len(requests) == 1


def test_untrusted_https_certificate_rejected(server_factory, tls_contexts):
    context, _ = tls_contexts
    server_factory({"/": response()}, context)
    with pytest.raises(ssl.SSLCertVerificationError):
        web.fetch("https://icons.example.com/")
