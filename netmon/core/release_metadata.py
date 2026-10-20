"""Small, bounded About-version requests; redirects never drain response bodies."""

from contextlib import contextmanager
import http.client
import json
import queue
import socket
import threading
import time
from urllib import error, request
from urllib.parse import urljoin, urlsplit

MAX_BYTES = 64 * 1024
MAX_SECONDS = 15
MAX_REDIRECTS = 4
MAX_JSON_DEPTH = 16
MAX_JSON_TOKENS = 1024
_REDIRECTS = {301, 302, 303, 307, 308}


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Returning None prevents urllib's unbounded fp.read() before a hop.
        return None


def _remaining(deadline, cancelled):
    remaining = deadline - time.monotonic()
    if cancelled.is_set() or remaining <= 0:
        raise TimeoutError("Versionsdownload: Gesamtzeitlimit überschritten.")
    return remaining


def _validate_url(url):
    parsed = urlsplit(url)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(ord(c) < 33 or ord(c) == 127 for c in url)
    ):
        raise ValueError("Ungültige URL für Versionsdownload.")


def _read_payload(response, deadline, cancelled):
    encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
    if encoding not in {"", "identity"}:
        raise ValueError("Komprimierte Versionsantwort nicht erlaubt.")
    declared = response.headers.get("Content-Length")
    if declared is not None and not 0 <= int(declared) <= MAX_BYTES:
        raise ValueError("Versionsantwort überschreitet das Größenlimit.")
    data = bytearray()
    while True:
        remaining = _remaining(deadline, cancelled)
        # HTTPResponse.read1 performs at most one underlying buffered read.
        # Update its socket timeout too; the public wrapper bounds DNS/headers.
        raw = getattr(getattr(response, "fp", None), "raw", None)
        sock = getattr(raw, "_sock", None)
        if sock is not None:
            sock.settimeout(min(8, remaining))
        read = getattr(response, "read1", response.read)
        chunk = read(min(4096, MAX_BYTES - len(data) + 1))
        _remaining(deadline, cancelled)
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > MAX_BYTES:
            raise ValueError("Versionsantwort überschreitet das Größenlimit.")


def _decode_payload(payload):
    text = payload.decode("utf-8", errors="strict")
    depth = tokens = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
            tokens += 1
        elif char in "[{":
            depth += 1
            tokens += 1
        elif char in "]}":
            depth -= 1
        elif char in ",:":
            tokens += 1
        if depth > MAX_JSON_DEPTH or tokens > MAX_JSON_TOKENS:
            raise ValueError("Versions-JSON überschreitet das Strukturlimit.")
    result = json.loads(text)
    if not isinstance(result, dict):
        raise ValueError("Versionsdatei ist kein JSON-Objekt.")
    return result


@contextmanager
def _deadline_opener(deadline, cancelled):
    """Bound live sockets and reject late DNS/connect results before HTTP."""
    done = threading.Event()
    lock = threading.Lock()
    state = [None, None, None]  # Connection, response, connecting socket.

    def remaining():
        return min(8, _remaining(deadline, cancelled))

    def watch():
        while not done.wait(0.025):
            try:
                remaining()
            except TimeoutError:
                cancelled.set()
                with lock:
                    connection, response, connecting = state
                    raw = getattr(getattr(response, "fp", None), "raw", None)
                    sockets = [
                        connecting,
                        getattr(connection, "sock", None),
                        getattr(raw, "_sock", None),
                    ]
                    for sock in sockets:
                        if sock is not None:
                            try:
                                sock.shutdown(socket.SHUT_RDWR)
                            except OSError:
                                pass
                # A system call may publish a socket later. Keep cancellation
                # latched and continue shutting down late sockets until exit.

    def connect_with_budget(address, timeout=None, source_address=None):
        remaining()
        host, port = address
        addresses = socket.getaddrinfo(host, port, 0, socket.SOCK_STREAM)
        remaining()  # A running system resolver is not reliably cancellable.
        last_error = None
        for family, kind, proto, _name, target in addresses:
            remaining()
            sock = socket.socket(family, kind, proto)
            connected = False
            try:
                with lock:
                    remaining()
                    state[2] = sock
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
                    with lock:
                        if state[2] is sock:
                            state[2] = None
            remaining()  # No next address after cancellation or expiry.
        if last_error is not None:
            raise last_error
        raise OSError("Keine Adresse für Versionsdownload verfügbar.")

    def factory(cls):
        def create(*args, **kwargs):
            connection = cls(*args, **kwargs)
            connection._create_connection = connect_with_budget
            original_connect = connection.connect

            def connect():
                remaining()
                original_connect()
                remaining()  # Also covers TLS and proxy tunnelling.
                connection.sock.settimeout(remaining())

            connection.connect = connect
            with lock:
                remaining()
                state[:] = [connection, None, None]
            return connection

        return create

    class HTTPHandler(request.HTTPHandler):
        def http_open(self, req):
            return self.do_open(factory(http.client.HTTPConnection), req)

    class HTTPSHandler(request.HTTPSHandler):
        def https_open(self, req):
            return self.do_open(
                factory(http.client.HTTPSConnection), req, context=self._context
            )

    def remember(response):
        with lock:
            state[1] = response

    remaining()
    opener = request.build_opener(_NoRedirect(), HTTPHandler(), HTTPSHandler())
    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    try:
        yield opener, remember
    finally:
        done.set()
        watcher.join()
        with lock:
            connection, _response, connecting = state
            if connection is not None:
                connection.close()
            if connecting is not None:
                connecting.close()


def _download(url, deadline, cancelled):
    with _deadline_opener(deadline, cancelled) as (opener, remember):
        seen = set()
        for hop in range(MAX_REDIRECTS + 1):
            _validate_url(url)
            if url in seen:
                raise ValueError("Redirect-Schleife beim Versionsdownload.")
            seen.add(url)
            timeout = min(8, _remaining(deadline, cancelled))
            req = request.Request(url, headers={"Accept-Encoding": "identity"})
            try:
                response = opener.open(req, timeout=timeout)
            except error.HTTPError as exc:
                if exc.code not in _REDIRECTS:
                    exc.close()
                    raise
                response = exc
            remember(response)
            try:
                _remaining(deadline, cancelled)
                status = response.getcode()
                if status in _REDIRECTS:
                    location = response.headers.get("Location")
                    if not location or hop == MAX_REDIRECTS:
                        raise ValueError(
                            "Ungültiger oder zu häufiger Versions-Redirect."
                        )
                    target = urljoin(url, location)
                    _validate_url(target)
                    if (
                        urlsplit(url).scheme == "https"
                        and urlsplit(target).scheme != "https"
                    ):
                        raise ValueError("Unsicherer Versions-Redirect.")
                    url = target
                    continue
                if status != 200:
                    raise ValueError("Versionsdownload ohne erfolgreiche HTTP-Antwort.")
                result = _decode_payload(_read_payload(response, deadline, cancelled))
                _remaining(deadline, cancelled)
                return result
            finally:
                response.close()
        raise ValueError("Zu viele Versions-Redirects.")


def fetch_release_metadata(url):
    """Enforce a caller deadline even when DNS or HTTP headers stall.

    Live sockets are interrupted on expiry. A running system DNS call cannot
    reliably be cancelled; its late result is rejected before connecting.
    The App keeps one request in flight until that transport actually exits.
    """
    deadline = time.monotonic() + MAX_SECONDS
    cancelled = threading.Event()
    results = queue.Queue(maxsize=1)
    finished = threading.Event()

    def download():
        try:
            results.put((True, _download(url, deadline, cancelled)))
        except (
            OSError,
            ValueError,
            error.URLError,
            http.client.HTTPException,
            RecursionError,
        ) as exc:
            results.put((False, exc))
        except Exception as exc:
            results.put((False, exc))
            raise
        finally:
            finished.set()

    worker = threading.Thread(target=download, daemon=True)
    worker.start()
    try:
        success, result = results.get(timeout=_remaining(deadline, cancelled))
        _remaining(deadline, cancelled)
    except (queue.Empty, TimeoutError) as exc:
        cancelled.set()
        timeout = TimeoutError("Versionsdownload: Gesamtzeitlimit überschritten.")
        # Let the UI refuse repeated requests while a system call is unwinding.
        timeout.transport_finished = finished
        raise timeout from exc
    if not success:
        raise result
    return result
