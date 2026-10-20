"""Exercise real sockets, including trickling headers and chunk framing."""

import contextlib
import socket
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.core import radio_icy as icy
from netmon.features import radio_controller as radio


@pytest.fixture(autouse=True)
def isolated_loopback(monkeypatch):
    # Every synthetic listener and client in this module uses 127.0.0.1.
    monkeypatch.setenv("NETMON_TEST_ISOLATED", "1")


@contextlib.contextmanager
def server(handler):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    listener.settimeout(2)
    stopped = threading.Event()
    errors = []

    def run():
        try:
            conn, _ = listener.accept()
            with conn:
                conn.settimeout(2)
                conn.recv(8192)
                handler(conn, stopped)
        except (OSError, TimeoutError):
            pass  # Expected when the client cancels/closes a hostile stream.
        except Exception as exc:  # noqa: BLE001 - report all server-thread failures
            errors.append(exc)

    worker = threading.Thread(target=run, daemon=True)
    worker.start()
    try:
        yield f"http://127.0.0.1:{listener.getsockname()[1]}/live"
    finally:
        stopped.set()
        listener.close()
        worker.join(3)
        assert not worker.is_alive()
        assert not errors


def send(conn, value):
    conn.sendall(value)


def drip(conn, stopped, value=b"a"):
    while not stopped.wait(0.01):
        send(conn, value)


def response(body, interval="1", extra=b""):
    return (
        b"HTTP/1.1 200 OK\r\nicy-metaint: "
        + interval.encode()
        + b"\r\n"
        + extra
        + b"\r\n"
        + body
    )


@pytest.mark.parametrize(
    "interval", ["0", "-1", "bad", str(icy.MAX_INTERVAL + 1), "9" * 5000]
)
def test_invalid_interval_closes_before_body(interval):
    def handler(conn, stopped):
        send(conn, response(b"", interval))
        assert conn.recv(1) == b""

    with server(handler) as url:
        assert icy.fetch_icy_metadata(url, timeout=0.3) == b""


def test_fragmented_valid_title():
    metadata = b"StreamTitle='Artist - Track';".ljust(32, b"\0")

    def handler(conn, stopped):
        for byte in response(b"a\x02" + metadata):
            send(conn, bytes([byte]))
            time.sleep(0.0001)

    with server(handler) as url:
        assert radio._fetch_icy_stream_title(url) == "Artist - Track"


@pytest.mark.parametrize("payload", [b"a", b"a\x02StreamTitle='cut", b"a\x00"])
def test_incomplete_or_empty_metadata(payload):
    with server(lambda conn, _: send(conn, response(payload))) as url:
        assert icy.fetch_icy_metadata(url) == b""


@pytest.mark.parametrize("phase", ["audio", "metadata", "headers", "chunk"])
def test_absolute_deadline_stops_trickle(phase):
    def handler(conn, stopped):
        if phase == "headers":
            send(conn, b"HTTP/1.1 200 OK\r\nX-Slow: ")
        elif phase == "chunk":
            send(conn, response(b"", extra=b"Transfer-Encoding: chunked\r\n"))
            # Slow chunk extension never completes; read1 alone cannot bound it.
            send(conn, b"1;slow=")
        else:
            send(
                conn,
                response(
                    b"a\xff" if phase == "metadata" else b"",
                    "1" if phase == "metadata" else "262144",
                ),
            )
        drip(conn, stopped)

    with server(handler) as url:
        start = time.monotonic()
        assert icy.fetch_icy_metadata(url, timeout=0.2) == b""
        assert time.monotonic() - start < 1.0


def test_cancellation_closes_socket_and_excludes_parallel_request():
    ready = threading.Event()
    cancel = threading.Event()
    results = []

    def handler(conn, stopped):
        send(conn, response(b"", "262144"))
        ready.set()
        drip(conn, stopped)

    with server(handler) as url:
        worker = threading.Thread(
            target=lambda: results.append(
                icy.fetch_icy_metadata(url, cancelled=cancel.is_set)
            )
        )
        worker.start()
        assert ready.wait(1)
        assert icy.fetch_icy_metadata(url) == b""
        cancel.set()
        worker.join(1)
        assert not worker.is_alive()
        assert results == [b""]
    # The lock must be reusable after cancellation.
    with server(lambda conn, _: send(conn, response(b"a\x01" + b"x" * 16))) as url:
        assert icy.fetch_icy_metadata(url) == b"x" * 16


def test_redirect_body_is_never_drained():
    with server(lambda conn, _: send(conn, response(b"a\x01" + b"x" * 16))) as target:

        def handler(conn, stopped):
            send(conn, f"HTTP/1.1 302 Found\r\nLocation: {target}\r\n\r\n".encode())
            assert conn.recv(1) == b""

        with server(handler) as url:
            assert icy.fetch_icy_metadata(url, timeout=0.5) == b"x" * 16


def test_old_playback_title_is_not_scheduled(monkeypatch):
    proc = object()
    app = SimpleNamespace(radio_proc=proc)

    def read(app, proc):
        app.radio_proc = object()
        return "old title", {}

    monkeypatch.setattr(radio, "_read_radio_stream_title", read)
    monkeypatch.setattr(radio, "_schedule_ui", lambda *args: pytest.fail("stale title"))
    radio._poll_radio_metadata(app, proc)


def test_queued_title_checks_playback_again(monkeypatch):
    proc = object()
    app = SimpleNamespace(radio_proc=proc)
    queued = []
    monkeypatch.setattr(radio, "_read_radio_stream_title", lambda *args: ("old", {}))
    monkeypatch.setattr(radio, "_schedule_ui", lambda app, cb: queued.append(cb))
    monkeypatch.setattr(radio.time, "sleep", lambda _: setattr(app, "radio_proc", None))
    monkeypatch.setattr(
        radio, "_set_radio_title_text", lambda *args: pytest.fail("stale title")
    )
    radio._poll_radio_metadata(app, proc)
    queued[0]()


def test_maximum_frame_and_byte_budget():
    metadata = b"x" * icy.MAX_METADATA
    body = b"a" * icy.MAX_INTERVAL + b"\xff" + metadata
    with server(
        lambda conn, _: send(conn, response(body, str(icy.MAX_INTERVAL)))
    ) as url:
        assert icy.fetch_icy_metadata(url) == metadata


def test_cancelled_request_never_connects(monkeypatch):
    monkeypatch.setattr(
        icy.urllib.request,
        "build_opener",
        lambda *args: pytest.fail("already cancelled"),
    )
    assert (
        icy.fetch_icy_metadata("http://example.invalid/", cancelled=lambda: True) == b""
    )


def test_redirect_loop_closes_without_reading_body():
    def handler(conn, stopped):
        send(conn, b"HTTP/1.1 302 Found\r\nLocation: /live\r\n\r\n")
        assert conn.recv(1) == b""

    with server(handler) as url:
        assert icy.fetch_icy_metadata(url) == b""


def test_environment_http_proxy_is_preserved(monkeypatch):
    with server(lambda conn, _: send(conn, response(b"a\x01" + b"p" * 16))) as proxy:
        monkeypatch.setenv("http_proxy", proxy)
        monkeypatch.setenv("no_proxy", "")
        monkeypatch.setenv("NO_PROXY", "")
        assert icy.fetch_icy_metadata("http://station.invalid/live") == b"p" * 16


def test_https_handler_passes_verifying_context(monkeypatch):
    import http.client
    import ssl

    seen = []

    class SyntheticTLSConnection(http.client.HTTPSConnection):
        def __new__(cls, host, **kwargs):
            context = kwargs.pop("context")
            # None on older Python means HTTPSConnection creates its default context.
            if context is not None:
                assert context.verify_mode == ssl.CERT_REQUIRED
                assert context.check_hostname
            seen.append(host)
            return http.client.HTTPConnection(host, **kwargs)

    monkeypatch.setattr(icy.http.client, "HTTPSConnection", SyntheticTLSConnection)
    with server(lambda conn, _: send(conn, response(b"a\x01" + b"s" * 16))) as url:
        assert icy.fetch_icy_metadata(url.replace("http:", "https:")) == b"s" * 16
    assert len(seen) == 1


class AddressSocket:
    """Synthetic transport for deterministic DNS/address budget checks."""

    def __init__(self):
        import io

        self.reply = io.BytesIO(response(b"a\x01" + b"x" * 16))
        self.closed = False
        self.timeout = None
        self.sent = []
        self.shutdown_called = threading.Event()

    def settimeout(self, value):
        self.timeout = value

    def setsockopt(self, *args):
        pass

    def sendall(self, data):
        self.sent.append(data)

    def makefile(self, *args):
        return self.reply

    def shutdown(self, how):
        self.shutdown_called.set()

    def close(self):
        self.closed = True


def address_rows():
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.2", 80)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.3", 80)),
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 80)),
    ]


@pytest.mark.parametrize("phase", ["dns", "connect_failure", "connect_success"])
@pytest.mark.parametrize("reason", ["deadline", "station_change"])
def test_r01_abort_before_http_or_next_address(monkeypatch, phase, reason):
    clock = [0.0]
    cancelled = [False]
    created = []
    attempted = []

    def abort():
        if reason == "deadline":
            clock[0] = 0.2
        else:
            cancelled[0] = True

    def resolve(*args):
        if phase == "dns":
            abort()
        return address_rows()

    class Transport(AddressSocket):
        def __init__(self, *args):
            super().__init__()
            created.append(self)

        def connect(self, target):
            attempted.append(target)
            abort()
            if phase == "connect_failure":
                raise OSError("synthetic failed address")

    monkeypatch.setattr(icy.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(icy.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(icy.socket, "socket", Transport)
    assert (
        icy.fetch_icy_metadata(
            "http://synthetic.invalid/", timeout=0.12, cancelled=lambda: cancelled[0]
        )
        == b""
    )
    assert len(attempted) == (0 if phase == "dns" else 1)
    assert all(sock.closed and not sock.sent for sock in created)
    assert not icy._REQUEST_LOCK.locked()


@pytest.mark.parametrize("exhaust_budget", [False, True])
def test_r01_address_retries_share_remaining_budget(monkeypatch, exhaust_budget):
    clock = [0.0]
    created = []
    attempts = []

    class Transport(AddressSocket):
        def __init__(self, *args):
            super().__init__()
            created.append(self)

        def connect(self, target):
            attempts.append((target, self.timeout))
            if len(attempts) <= 2:
                clock[0] += 0.07 if exhaust_budget else 0.02
                raise OSError("synthetic failed address")

    monkeypatch.setattr(icy.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(icy.socket, "getaddrinfo", lambda *a: address_rows())
    monkeypatch.setattr(icy.socket, "socket", Transport)
    result = icy.fetch_icy_metadata("http://synthetic.invalid/", timeout=0.12)
    assert result == (b"" if exhaust_budget else b"x" * 16)
    assert len(attempts) == (2 if exhaust_budget else 3)
    assert attempts[0][1] == pytest.approx(0.12)
    assert attempts[1][1] == pytest.approx(0.05 if exhaust_budget else 0.10)
    if not exhaust_budget:
        assert attempts[2][1] == pytest.approx(0.08)
    assert all(sock.closed for sock in created)
    assert not icy._REQUEST_LOCK.locked()


@pytest.mark.parametrize("phase", ["dns", "tcp"])
def test_r01_real_blocking_phase_cancels_without_http(monkeypatch, phase):
    entered = threading.Event()
    release = threading.Event()
    cancel = threading.Event()
    sockets = []
    results = []
    attempts = []

    def resolve(*args):
        if phase == "dns":
            entered.set()
            assert release.wait(1)
        return address_rows()

    class Transport(AddressSocket):
        def __init__(self, *args):
            super().__init__()
            sockets.append(self)

        def connect(self, target):
            attempts.append(target)
            entered.set()
            assert release.wait(1)

    monkeypatch.setattr(icy.socket, "getaddrinfo", resolve)
    monkeypatch.setattr(icy.socket, "socket", Transport)
    worker = threading.Thread(
        target=lambda: results.append(
            icy.fetch_icy_metadata("http://synthetic.invalid/", cancelled=cancel.is_set)
        )
    )
    worker.start()
    try:
        assert entered.wait(1)
        cancel.set()
        # The slot must not be released while a blocking system call still lives.
        assert icy._REQUEST_LOCK.locked()
        assert icy.fetch_icy_metadata("http://parallel.invalid/") == b""
        if phase == "tcp":
            assert sockets[0].shutdown_called.wait(0.5)
        release.set()
        worker.join(1)
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert results == [b""]
    assert len(attempts) == (0 if phase == "dns" else 1)
    assert all(sock.closed and not sock.sent for sock in sockets)
    assert not icy._REQUEST_LOCK.locked()
    # Normal request succeeds after the aborted worker has actually ended.
    monkeypatch.setattr(icy.socket, "getaddrinfo", lambda *a: address_rows())
    assert icy.fetch_icy_metadata("http://synthetic.invalid/") == b"x" * 16


def test_r01_watchdog_latches_abort_and_revisits_late_socket(monkeypatch):
    entered = threading.Event()
    release = threading.Event()
    cancel = threading.Event()
    observed = threading.Event()
    late = AddressSocket()
    result = []
    original = icy.http.client.HTTPConnection

    class LateConnection(original):
        def connect(self):
            entered.set()
            assert release.wait(1)
            self.sock = late
            # The watchdog must not have exited after finding no socket.
            assert late.shutdown_called.wait(0.5)

    monkeypatch.setattr(icy.http.client, "HTTPConnection", LateConnection)

    def cancelled():
        value = cancel.is_set()
        if value:
            observed.set()
        return value

    worker = threading.Thread(
        target=lambda: result.append(
            icy.fetch_icy_metadata("http://synthetic.invalid/", cancelled=cancelled)
        )
    )
    worker.start()
    try:
        assert entered.wait(1)
        cancel.set()
        assert observed.wait(1)  # The watcher observes abort without a socket.
        cancel.clear()  # Observed cancellation must remain irreversible.
        release.set()
        worker.join(1)
    finally:
        release.set()
        worker.join(2)
    assert not worker.is_alive()
    assert result == [b""]
    assert late.closed
    assert not late.sent
    assert not icy._REQUEST_LOCK.locked()
