"""Bounded, cancellable ICY title requests (independent of audio playback)."""

import http.client
import math
import socket
import threading
import time
import urllib.request
from urllib.parse import urljoin, urlsplit

MAX_INTERVAL = 256 * 1024
MAX_METADATA = 255 * 16
MAX_REDIRECTS = 5
_REQUEST_LOCK = threading.Lock()


def fetch_icy_metadata(url, timeout=4, cancelled=lambda: False):
    """Return one complete metadata block, or empty bytes on any failure.

    One request may run at a time. A watchdog shuts down sockets even while
    HTTP headers or chunk framing trickle in; read1 avoids fill-to-size reads.
    System DNS and in-flight system calls may return late. Their results are
    discarded after cancellation/expiry, before trying another address or HTTP.
    The request slot remains occupied until this worker actually finishes.
    """
    if not _REQUEST_LOCK.acquire(blocking=False):
        return b""
    done = threading.Event()
    aborted = threading.Event()
    state_lock = threading.Lock()
    state = [None, None, None]  # Connection, response, connecting socket.
    watcher = None
    try:
        timeout = float(timeout)
        if not math.isfinite(timeout) or timeout <= 0:
            return b""
        deadline = time.monotonic() + min(timeout, 4.0)

        def remaining():
            value = deadline - time.monotonic()
            if aborted.is_set() or value <= 0 or cancelled():
                aborted.set()
                raise TimeoutError("ICY request expired or cancelled")
            return value

        def abort_socket():
            with state_lock:
                connection, response, connecting = state
                sockets = [connecting, getattr(connection, "sock", None)]
                if response is not None:
                    raw = getattr(getattr(response, "fp", None), "raw", None)
                    sockets.append(getattr(raw, "_sock", None))
                for sock in sockets:
                    if sock is not None:
                        try:
                            sock.shutdown(socket.SHUT_RDWR)
                        except OSError:
                            pass

        def watch():
            while not done.wait(0.025):
                try:
                    remaining()
                except TimeoutError:
                    abort_socket()
                    # DNS/connect/TLS may publish a socket after this attempt.
                    # Keep the abort latched and shut down late sockets too.

        def connect_with_budget(address, timeout=None, source_address=None):
            remaining()
            host, port = address
            addresses = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
            remaining()  # System DNS itself is not reliably interruptible.
            last_error = None
            for family, kind, proto, _name, target in addresses:
                remaining()
                sock = socket.socket(family, kind, proto)
                connected = False
                try:
                    with state_lock:
                        remaining()
                        state[2] = sock  # Expose even a not-yet-connected socket.
                    sock.settimeout(remaining())
                    if source_address:
                        sock.bind(source_address)
                        remaining()
                    sock.connect(target)
                    remaining()
                    sock.settimeout(remaining())
                    connected = True
                    return sock
                except OSError as exc:
                    last_error = exc
                finally:
                    if not connected:
                        sock.close()
                        with state_lock:
                            if state[2] is sock:
                                state[2] = None
                remaining()  # Never retry an address after expiry/cancellation.
            if last_error is not None:
                raise last_error
            raise OSError("No ICY server addresses")

        def connection_factory(cls):
            def create(*args, **kwargs):
                connection = cls(*args, **kwargs)
                connection._create_connection = connect_with_budget
                original_connect = connection.connect

                def connect():
                    remaining()
                    original_connect()
                    # Also covers proxy tunnelling and TLS before HTTP starts.
                    remaining()
                    connection.sock.settimeout(remaining())

                connection.connect = connect
                with state_lock:
                    remaining()
                    state[:] = [connection, None, None]
                return connection

            return create

        class HTTPHandler(urllib.request.HTTPHandler):
            def http_open(self, request):
                return self.do_open(
                    connection_factory(http.client.HTTPConnection), request
                )

        class HTTPSHandler(urllib.request.HTTPSHandler):
            def https_open(self, request):
                return self.do_open(
                    connection_factory(http.client.HTTPSConnection),
                    request,
                    context=self._context,
                )

        class RawResponses(urllib.request.HTTPErrorProcessor):
            def http_response(self, request, response):
                return response

            https_response = http_response

        # Keep urllib's environment proxy and TLS behavior, but handle redirects
        # ourselves so no intermediate response body is drained.
        remaining()
        opener = urllib.request.build_opener(
            HTTPHandler(), HTTPSHandler(), RawResponses()
        )
        remaining()
        watcher = threading.Thread(target=watch, daemon=True)
        watcher.start()
        visited = set()
        for hop in range(MAX_REDIRECTS + 1):
            remaining()
            if (
                len(url) > 8192
                or any(ord(c) <= 32 or ord(c) == 127 for c in url)
                or "\\" in url
                or url in visited
            ):
                return b""
            visited.add(url)
            parts = urlsplit(url)
            if (
                parts.scheme not in {"http", "https"}
                or not parts.hostname
                or parts.username is not None
                or parts.password is not None
            ):
                return b""
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "NetMon/1.1",
                    "Icy-MetaData": "1",
                    "Accept-Encoding": "identity",
                },
            )
            response = None
            try:
                response = opener.open(request, timeout=remaining())
                with state_lock:
                    state[1] = response
                remaining()
                if response.status in {301, 302, 303, 307, 308}:
                    locations = response.headers.get_all("Location", [])
                    if hop == MAX_REDIRECTS or len(locations) != 1:
                        return b""
                    location = locations[0].strip()
                    if not location or any(
                        ord(c) < 32 or ord(c) == 127 for c in location
                    ):
                        return b""
                    target = urljoin(url, location)
                    if parts.scheme == "https" and urlsplit(target).scheme != "https":
                        return b""
                    url = target
                    continue  # Close, never drain intermediate bodies.
                if response.status != 200 or response.getheader(
                    "Content-Encoding", "identity"
                ).lower() not in {"", "identity"}:
                    return b""
                interval = int(response.getheader("icy-metaint", "0"))
                if not 0 < interval <= MAX_INTERVAL:
                    return b""
                consumed = 0

                def read_exact(size, response=response):
                    nonlocal consumed
                    data = bytearray()
                    while len(data) < size:
                        remaining()
                        chunk = response.read1(min(4096, size - len(data)))
                        remaining()
                        if not chunk:
                            raise EOFError("Incomplete ICY frame")
                        consumed += len(chunk)
                        if consumed > MAX_INTERVAL + 1 + MAX_METADATA:
                            raise ValueError("ICY byte budget exceeded")
                        data.extend(chunk)
                    return bytes(data)

                # Discard audio in bounded chunks rather than retaining it.
                skipped = 0
                while skipped < interval:
                    skipped += len(read_exact(min(4096, interval - skipped)))
                length = read_exact(1)[0] * 16
                return read_exact(length) if length else b""
            finally:
                if response is not None:
                    response.close()
                with state_lock:
                    connection = state[0]
                    if connection is not None:
                        connection.close()
                    state[:] = [None, None, None]
        return b""
    except (OSError, ValueError, EOFError, http.client.HTTPException):
        return b""
    finally:
        done.set()
        if watcher is not None:
            watcher.join()
        _REQUEST_LOCK.release()
