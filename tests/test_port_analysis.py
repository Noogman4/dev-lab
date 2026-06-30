import socket
import ssl

from netmon.modules.port_analysis import check_port_real_service
from tools.netmon import parse_nmap_open_tcp_ports


class _FakeSocket:
    def __init__(self, payload=b"", recv_raises_timeout=False):
        self._payload = payload
        self._recv_raises_timeout = recv_raises_timeout
        self.closed = False
        self.sent = []

    def settimeout(self, _timeout):
        return None

    def recv(self, _size):
        if self._recv_raises_timeout:
            raise socket.timeout()
        return self._payload

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        self.closed = True


class _FakeTlsSocket:
    def __init__(self):
        self.closed = False

    def settimeout(self, _timeout):
        return None

    def close(self):
        self.closed = True


class _FakeTlsContext:
    def __init__(self, tls_sock=None, exc=None):
        self.tls_sock = tls_sock or _FakeTlsSocket()
        self.exc = exc
        self.check_hostname = True
        self.verify_mode = ssl.CERT_REQUIRED

    def wrap_socket(self, _sock, server_hostname=None):
        if self.exc is not None:
            raise self.exc
        return self.tls_sock


def test_check_port_real_service_open_with_ssh_banner(monkeypatch):
    fake = _FakeSocket(payload=b"SSH-2.0-OpenSSH_9.0\r\n")

    monkeypatch.setattr(socket, "create_connection", lambda _addr, timeout=3: fake)

    result = check_port_real_service("1.1.1.1", 22, timeout=2)

    assert result["state"] == "open"
    assert result["reason"] == "ssh_banner_received"
    assert result["banner"].startswith("SSH-2.0")


def test_check_port_real_service_pseudo_open_on_22_without_banner(monkeypatch):
    fake = _FakeSocket(payload=b"")

    monkeypatch.setattr(socket, "create_connection", lambda _addr, timeout=3: fake)

    result = check_port_real_service("1.1.1.1", 22, timeout=2)

    assert result["state"] == "pseudo-open"
    assert result["reason"] == "no_ssh_banner_connection_closed"


def test_check_port_real_service_open_on_80_http_response(monkeypatch):
    fake = _FakeSocket(payload=b"HTTP/1.1 200 OK\r\nServer: test\r\n\r\n")

    monkeypatch.setattr(socket, "create_connection", lambda _addr, timeout=3: fake)

    result = check_port_real_service("1.1.1.1", 80, timeout=2)

    assert result["state"] == "open"
    assert result["reason"] == "http_response_received"
    assert fake.sent


def test_check_port_real_service_open_on_443_tls_success(monkeypatch):
    fake_sock = _FakeSocket()
    fake_ctx = _FakeTlsContext()

    monkeypatch.setattr(socket, "create_connection", lambda _addr, timeout=3: fake_sock)
    monkeypatch.setattr(ssl, "create_default_context", lambda: fake_ctx)

    result = check_port_real_service("1.1.1.1", 443, timeout=2)

    assert result["state"] == "open"
    assert result["reason"] == "tls_handshake_success"


def test_check_port_real_service_closed_on_connection_refused_error(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise ConnectionRefusedError("[Errno 111] Connection refused")

    monkeypatch.setattr(socket, "create_connection", _raise)

    result = check_port_real_service("127.0.0.1", 22, timeout=1)

    assert result["state"] == "closed"
    assert result["reason"] == "connection_refused"


def test_check_port_real_service_closed_on_errno_111_oserror(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise OSError(111, "Connection refused")

    monkeypatch.setattr(socket, "create_connection", _raise)

    result = check_port_real_service("127.0.0.1", 22, timeout=1)

    assert result["state"] == "closed"
    assert result["reason"] == "connection_refused"


def test_check_port_real_service_filtered_on_connect_timeout(monkeypatch):
    def _raise(*_args, **_kwargs):
        raise OSError("timed out")

    monkeypatch.setattr(socket, "create_connection", _raise)

    result = check_port_real_service("8.8.8.8", 22, timeout=1)

    assert result["state"] == "filtered"
    assert "timed out" in result["reason"]


def test_parse_nmap_open_tcp_ports_extracts_open_tcp_lines_only():
    sample = """
Starting Nmap
22/tcp   open  ssh
53/udp   open  domain
80/tcp   open  http
443/tcp  filtered  https
8443/tcp open  https-alt
"""

    assert parse_nmap_open_tcp_ports(sample) == [22, 80, 8443]
