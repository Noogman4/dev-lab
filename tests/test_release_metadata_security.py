"""Production origin/DNS guards with synthetic sockets; no external traffic."""

import io
import socket
import ssl
from types import SimpleNamespace

import pytest

from netmon.core import release_metadata as metadata


def answer(ip="8.8.8.8", port=443):
    family = socket.AF_INET6 if ":" in ip else socket.AF_INET
    endpoint = (ip, port, 0, 0) if family == socket.AF_INET6 else (ip, port)
    return family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", endpoint


def response(*, location=None):
    if location is not None:
        return f"HTTP/1.1 302 Found\r\nLocation: {location}\r\nContent-Length: 0\r\n\r\n".encode()
    body = b'{"version":"1.2.3"}'
    return (
        b"HTTP/1.1 200 OK\r\nContent-Length: "
        + str(len(body)).encode()
        + b"\r\n\r\n"
        + body
    )


@pytest.fixture
def network(monkeypatch):
    state = SimpleNamespace(
        answers=[[answer()]],
        lookups=[],
        sockets=[],
        responses=[response()],
        peers=None,
        connect_error=None,
        tls_names=[],
    )

    def resolve(host, port, *_args, **_kwargs):
        state.lookups.append((host, port))
        assert host == "netmonroots.com" and port == 443
        return state.answers[min(len(state.lookups) - 1, len(state.answers) - 1)]

    class Socket:
        def __init__(self, family, kind, protocol):
            self.family = family
            self.target = None
            self.sent = []
            self.closed = False
            self.timeout = None
            self.index = len(state.sockets)
            state.sockets.append(self)

        def settimeout(self, value):
            self.timeout = value

        def setsockopt(self, *_args):
            pass

        def connect(self, target):
            self.target = target
            if state.connect_error and self.index == 0:
                raise state.connect_error

        def getpeername(self):
            return state.peers if state.peers is not None else self.target

        def sendall(self, data):
            self.sent.append(data)

        def makefile(self, *_args):
            return io.BytesIO(
                state.responses[min(self.index, len(state.responses) - 1)]
            )

        def shutdown(self, *_args):
            pass

        def close(self):
            self.closed = True

    context = ssl.create_default_context()

    def wrap(sock, server_hostname):
        state.tls_names.append(server_hostname)
        return sock

    # Fake TLS I/O only here. Existing deadline tests retain real certificate
    # and hostname checks against their owned loopback TLS servers.
    monkeypatch.setattr(context, "wrap_socket", wrap)
    monkeypatch.setattr(ssl, "_create_default_https_context", lambda: context)
    monkeypatch.setattr(metadata.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(metadata.socket, "socket", Socket)
    return state


FORBIDDEN_URLS = [
    "http://netmonroots.com/version",
    "https://evil.invalid/version",
    "https://www.netmonroots.com/version",
    "https://netmonroots.com.evil.invalid/version",
    "https://127.0.0.1/version",
    "https://[::1]/version",
    "https://netmonroots.com:444/version",
    "https://netmonroots.com:0443/version",
    "https://netmonroots.com:/version",
    "https://netmonroots.com./version",
    "https://user@netmonroots.com/version",
    "https://netmonroots.com@evil.invalid/version",
    "https://netmonroots%2ecom/version",
    "https://netmonroots.com\\@evil.invalid/version",
    "file:///tmp/version.json",
]


@pytest.mark.parametrize("url", FORBIDDEN_URLS)
@pytest.mark.parametrize("redirect", [False, True])
def test_origin_is_checked_before_initial_or_followup_dns(network, url, redirect):
    if redirect:
        network.responses = [response(location=url)]
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata(
            "https://netmonroots.com/start" if redirect else url
        )
    assert len(network.lookups) == int(redirect)
    assert len(network.sockets) == int(redirect)
    assert all(sock.closed for sock in network.sockets)


@pytest.mark.parametrize(
    "url",
    [
        "https://netmonroots.com/\nversion",
        "https://netmonroots.com/\0version",
        "https://netmonroots.com/" + "x" * 4096,
    ],
)
def test_malformed_initial_url_does_not_resolve(network, url):
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata(url)
    assert network.lookups == [] and network.sockets == []


FORBIDDEN_IPS = [
    "127.0.0.1",
    "10.0.0.1",
    "172.16.0.1",
    "192.168.1.1",
    "169.254.169.254",
    "0.0.0.0",
    "100.64.0.1",
    "192.0.0.8",
    "192.88.99.1",
    "224.0.0.1",
    "240.0.0.1",
    "192.0.2.1",
    "198.51.100.1",
    "203.0.113.1",
    "::1",
    "::",
    "fc00::1",
    "fe80::1",
    "ff02::1",
    "2001:db8::1",
    "2002:0808:0808::1",
    "2001::1",
    "64:ff9b::a00:1",
    "3fff::1",
    "::ffff:127.0.0.1",
    "::ffff:10.0.0.1",
]


@pytest.mark.parametrize("ip", FORBIDDEN_IPS)
@pytest.mark.parametrize("mixed", [False, True])
def test_nonpublic_or_mixed_dns_answer_opens_no_socket(network, ip, mixed):
    network.answers = [[*([answer()] if mixed else []), answer(ip)]]
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://netmonroots.com/version")
    assert network.sockets == []


def test_same_origin_redirect_rechecks_dns_and_rejects_rebinding(network):
    network.responses = [response(location="/next")]
    network.answers = [[answer()], [answer("127.0.0.1")]]
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://netmonroots.com/start")
    assert len(network.lookups) == 2
    assert len(network.sockets) == 1
    assert network.sockets[0].closed


@pytest.mark.parametrize(
    "location",
    ["/next", "https://netmonroots.com/next", "https://netmonroots.com:443/next"],
)
def test_approved_redirect_pins_numeric_addresses_and_preserves_tls_name(
    network, monkeypatch, location
):
    network.responses = [response(location=location), response()]
    network.answers = [[answer()], [answer("1.1.1.1")]]
    # An ambient proxy must never create an extra connection or DNS lookup.
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:8765")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:8765")
    monkeypatch.setenv("all_proxy", "socks5://127.0.0.1:8765")
    monkeypatch.setenv("no_proxy", "")
    assert metadata.fetch_release_metadata("https://netmonroots.com/start") == {
        "version": "1.2.3"
    }
    assert network.lookups == [("netmonroots.com", 443)] * 2
    assert [sock.target for sock in network.sockets] == [
        ("8.8.8.8", 443),
        ("1.1.1.1", 443),
    ]
    assert network.tls_names == ["netmonroots.com"] * 2
    assert all(sock.closed for sock in network.sockets)
    assert all(
        b"Host: netmonroots.com" in b"".join(sock.sent) for sock in network.sockets
    )


@pytest.mark.parametrize(
    "peer", [("127.0.0.1", 443), ("1.1.1.1", 443), ("8.8.8.8", 444)]
)
def test_unexpected_peer_is_closed_before_tls_or_http(network, peer):
    network.peers = peer
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://netmonroots.com/version")
    assert len(network.sockets) == 1
    assert network.sockets[0].closed and not network.sockets[0].sent
    assert network.tls_names == []


def test_public_ipv6_is_pinned(network):
    network.answers = [[answer("2606:4700:4700::1111")]]
    assert (
        metadata.fetch_release_metadata("https://netmonroots.com/version")["version"]
        == "1.2.3"
    )
    assert network.sockets[0].target == ("2606:4700:4700::1111", 443, 0, 0)


def test_connection_retry_uses_only_prevalidated_numeric_addresses(network):
    network.answers = [[answer(), answer("1.1.1.1")]]
    network.connect_error = ConnectionRefusedError("synthetic first-address failure")
    assert (
        metadata.fetch_release_metadata("https://netmonroots.com/version")["version"]
        == "1.2.3"
    )
    assert network.lookups == [("netmonroots.com", 443)]
    assert [sock.target for sock in network.sockets] == [
        ("8.8.8.8", 443),
        ("1.1.1.1", 443),
    ]
    assert all(sock.closed for sock in network.sockets)


@pytest.mark.parametrize(
    "case", ["empty", "too_many", "port", "family", "kind", "protocol", "scope", "name"]
)
def test_malformed_dns_answer_is_rejected_before_socket_creation(network, case):
    rows = [answer()]
    if case == "empty":
        rows = []
    elif case == "too_many":
        rows *= 33
    elif case == "port":
        rows = [answer(port=444)]
    elif case == "scope":
        rows = [
            (
                socket.AF_INET6,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
                "",
                ("2606:4700::1111", 443, 0, 2),
            )
        ]
    elif case == "name":
        rows = [answer("private.invalid")]
    else:
        row = list(rows[0])
        row[{"family": 0, "kind": 1, "protocol": 2}[case]] = -1
        rows = [tuple(row)]
    network.answers = [rows]
    with pytest.raises(ValueError):
        metadata.fetch_release_metadata("https://netmonroots.com/version")
    assert network.sockets == []
