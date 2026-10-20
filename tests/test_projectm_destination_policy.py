"""Destination policy exercises the real opener without external network access."""

import io
import socket
import ssl

import pytest

from netmon.core import projectm_transport as transport


def answer(ip, port=80):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    sockaddr = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
    return (family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)


class WireSocket:
    def __init__(self, payload, connections, fail=False):
        self.payload = payload
        self.connections = connections
        self.fail = fail
        self.closed = False
        self.sent = b""

    def settimeout(self, timeout):
        self.timeout = timeout

    def setsockopt(self, *_):
        pass

    def connect(self, address):
        self.connections.append(address)
        if self.fail:
            raise OSError("connection failed")

    def sendall(self, data):
        self.sent += data

    def makefile(self, *_):
        return io.BytesIO(self.payload)

    def close(self):
        self.closed = True


@pytest.fixture
def wire(monkeypatch):
    connections = []
    sockets = []
    payloads = []

    def create(*_):
        sock = WireSocket(payloads.pop(0), connections)
        sockets.append(sock)
        return sock

    monkeypatch.setattr(transport.socket, "socket", create)
    return connections, sockets, payloads


BLOCKED = [
    "127.0.0.1",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.1",
    "169.254.169.254",
    "0.0.0.0",
    "224.0.0.1",
    "240.0.0.1",
    "100.64.0.1",
    "::1",
    "::",
    "fc00::1",
    "fe80::1",
    "ff02::1",
    "2001:db8::1",
    "::ffff:127.0.0.1",
    "::ffff:192.168.1.1",
    "2002:7f00:1::1",
]


@pytest.mark.parametrize("ip", BLOCKED)
@pytest.mark.parametrize("scheme", ["http", "https"])
def test_initial_destination_rejected_before_socket_creation(
    monkeypatch, wire, ip, scheme
):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *_a, **_k: [answer(ip)])
    host = f"[{ip}]" if ":" in ip else ip
    with (
        pytest.raises(ValueError, match="public network"),
        transport.open_preset_response(f"{scheme}://{host}/pack", timeout=1),
    ):
        pytest.fail("Non-public destination accepted")
    assert wire[0] == []
    assert wire[1] == []


@pytest.mark.parametrize("ip", BLOCKED)
def test_redirect_rechecks_destination(monkeypatch, wire, ip):
    host = f"[{ip}]" if ":" in ip else ip
    wire[2].append(
        f"HTTP/1.1 302 Found\r\nLocation: http://{host}/pack\r\nContent-Length: 0\r\n\r\n".encode()
    )
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda host, port, **_k: [
            answer("8.8.8.8" if host == "packs.example" else ip, port)
        ],
    )
    with (
        pytest.raises(ValueError, match="public network"),
        transport.open_preset_response("http://packs.example/", timeout=1),
    ):
        pytest.fail("Non-public redirect accepted")
    assert wire[0] == [("8.8.8.8", 80)]
    assert wire[1][0].closed


def test_mixed_dns_answer_fails_before_any_connection(monkeypatch, wire):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *_a, **_k: [answer("8.8.8.8"), answer("10.0.0.1")]
    )
    with pytest.raises(ValueError, match="public network"):
        transport._connect_public(("packs.example", 80), 1)
    assert wire[0] == []


@pytest.mark.parametrize("scheme,port", [("http", 80), ("https", 443)])
def test_pinned_connection_preserves_host_and_tls(monkeypatch, wire, scheme, port):
    lookups = []
    tls_hosts = []

    def resolve(host, port, **_):
        lookups.append(host)
        # A second resolution would return an internal address.
        return [answer("8.8.8.8" if len(lookups) == 1 else "127.0.0.1", port)]

    def wrap(context, sock, *, server_hostname, **_):
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname
        tls_hosts.append(server_hostname)
        return sock

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    monkeypatch.setattr(ssl.SSLContext, "wrap_socket", wrap)
    monkeypatch.setenv("http_proxy", "http://proxy.internal:8080")
    monkeypatch.setenv("https_proxy", "http://proxy.internal:8080")
    monkeypatch.setenv("no_proxy", "")
    wire[2].append(b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\npack")
    with transport.open_preset_response(
        f"{scheme}://packs.example/pack", timeout=1
    ) as response:
        assert response.read(4) == b"pack"
    assert lookups == ["packs.example"]
    assert wire[0] == [("8.8.8.8", port)]
    assert b"Host: packs.example\r\n" in wire[1][0].sent
    assert tls_hosts == (["packs.example"] if scheme == "https" else [])


def test_same_host_redirect_resolves_again_and_rejects_rebinding(monkeypatch, wire):
    calls = []

    def resolve(host, port, **_):
        calls.append(host)
        return [answer("8.8.8.8" if len(calls) == 1 else "127.0.0.1", port)]

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    wire[2].append(
        b"HTTP/1.1 302 Found\r\nLocation: /next\r\nContent-Length: 0\r\n\r\n"
    )
    with (
        pytest.raises(ValueError, match="public network"),
        transport.open_preset_response("http://packs.example/", timeout=1),
    ):
        pytest.fail("Rebinding accepted")
    assert calls == ["packs.example", "packs.example"]
    assert wire[0] == [("8.8.8.8", 80)]


def test_public_ipv6_is_accepted(monkeypatch, wire):
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *_a, **_k: [answer("2606:4700:4700::1111")]
    )
    wire[2].append(b"HTTP/1.1 200 OK\r\nContent-Length: 0\r\n\r\n")
    with transport.open_preset_response("http://packs.example/", timeout=1):
        pass
    assert wire[0] == [("2606:4700:4700::1111", 80, 0, 0)]


def test_connection_fallback_uses_only_checked_addresses(monkeypatch):
    connections = []
    first = WireSocket(b"", connections, fail=True)
    second = WireSocket(b"", connections)
    sockets = iter([first, second])
    monkeypatch.setattr(socket, "socket", lambda *_: next(sockets))
    monkeypatch.setattr(
        socket, "getaddrinfo", lambda *_a, **_k: [answer("8.8.8.8"), answer("1.1.1.1")]
    )
    assert transport._connect_public(("packs.example", 80), 1) is second
    assert connections == [("8.8.8.8", 80), ("1.1.1.1", 80)]
    assert first.closed


@pytest.mark.parametrize("result", [[], socket.gaierror("DNS failed")])
def test_dns_failure_fails_closed(monkeypatch, wire, result):
    def resolve(*_a, **_k):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    with pytest.raises((ValueError, socket.gaierror)):
        transport._connect_public(("packs.example", 80), 1)
    assert wire[0] == []
