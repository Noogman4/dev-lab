"""Bounded public-web GETs for automatic icon metadata, without ambient proxies."""

from dataclasses import dataclass, field
import http.client
import io
import ipaddress
import queue
import re
import socket
import ssl
import threading
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

HTML_BYTES = 256 * 1024
MANIFEST_BYTES = 128 * 1024
ICON_BYTES = 1024 * 1024
CHUNK_BYTES = 64 * 1024
MAX_REDIRECTS = 3
MAX_CANDIDATES = 8
MAX_MANIFESTS = 2
MAX_METADATA_LINKS = 32
MAX_CONTROL_BYTES = 32 * 1024
_DNS_SLOTS = threading.BoundedSemaphore(2)
_V4_DENIED = tuple(
    ipaddress.ip_network(value)
    for value in (
        "0.0.0.0/8",
        "100.64.0.0/10",
        "192.0.0.0/24",
        "192.88.99.0/24",
    )
)
_V6_DENIED = tuple(
    ipaddress.ip_network(value)
    for value in (
        "2001::/23",
        "2001:db8::/32",
        "2002::/16",
        "3fff::/20",
    )
)


@dataclass(frozen=True)
class WebURL:
    url: str
    scheme: str
    host: str
    port: int
    path: str

    @property
    def origin(self):
        return self.scheme, self.host, self.port


def parse_url(value):
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 4096
        or any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in value)
    ):
        raise ValueError("Invalid icon URL")
    parts = urlsplit(value)
    if (
        parts.scheme not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or "%" in parts.netloc
        or parts.netloc.endswith(":")
    ):
        raise ValueError("Only HTTP(S) URLs without user information are allowed")
    port = (
        parts.port
        if parts.port is not None
        else (443 if parts.scheme == "https" else 80)
    )
    if parts.port is not None and parts.netloc.rsplit(":", 1)[1] != str(parts.port):
        raise ValueError("Noncanonical icon port")
    if port != (443 if parts.scheme == "https" else 80):
        raise ValueError("Automatic icons require the default HTTP(S) port")
    host = parts.hostname.encode("idna").decode("ascii").lower()
    if host.endswith("."):
        raise ValueError("Ambiguous trailing-dot host")
    try:
        address = ipaddress.ip_address(host)
        host = address.compressed
    except ValueError:
        try:
            socket.inet_aton(host)
        except OSError:
            pass
        else:
            raise ValueError("Noncanonical numeric host")
        if len(host) > 253 or any(
            not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
            for label in host.split(".")
        ):
            raise ValueError("Invalid icon hostname")
        if "." not in host or host.endswith(
            (".localhost", ".local", ".internal", ".home", ".test", ".invalid")
        ):
            raise ValueError("Nonpublic icon hostname")
    netloc = f"[{host}]" if ":" in host else host
    path = parts.path or "/"
    path.encode("ascii")
    parts.query.encode("ascii")
    return WebURL(
        urlunsplit((parts.scheme, netloc, path, parts.query, "")),
        parts.scheme,
        host,
        port,
        path + ("?" + parts.query if parts.query else ""),
    )


def public_address(value):
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        public_address(str(address.ipv4_mapped))
        return address
    if (
        not address.is_global
        or address.is_reserved
        or address.is_multicast
        or address.is_loopback
        or address.is_link_local
        or address.is_unspecified
    ):
        raise ValueError("Forbidden icon network address")
    if isinstance(address, ipaddress.IPv4Address):
        if any(address in network for network in _V4_DENIED):
            raise ValueError("Special-purpose IPv4 address")
    elif address not in ipaddress.ip_network("2000::/3") or any(
        address in network for network in _V6_DENIED
    ):
        raise ValueError("Special-purpose IPv6 address")
    return address


@dataclass
class DownloadBudget:
    seconds: float = 20
    max_requests: int = 10
    max_bytes: int = 3 * 1024 * 1024
    deadline: float = field(init=False)
    requests: int = 0
    received: int = 0

    def __post_init__(self):
        self.deadline = time.monotonic() + self.seconds

    def remaining(self):
        value = self.deadline - time.monotonic()
        if value <= 0:
            raise TimeoutError("Icon operation deadline exceeded")
        return value

    def request(self):
        self.remaining()
        if self.received >= self.max_bytes:
            raise ValueError("Icon operation byte budget exhausted")
        self.requests += 1
        if self.requests > self.max_requests:
            raise ValueError("Icon request budget exceeded")

    def consume(self, size):
        self.received += size
        if self.received > self.max_bytes:
            raise ValueError("Icon operation byte budget exceeded")


def _resolve(target, budget):
    # Numeric addresses need no DNS. Check them before any socket is created.
    try:
        address = public_address(target.host)
    except ValueError:
        try:
            ipaddress.ip_address(target.host)
        except ValueError:
            pass
        else:
            raise
    else:
        family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
        return [
            (
                family,
                (
                    (str(address), target.port, 0, 0)
                    if address.version == 6
                    else (str(address), target.port)
                ),
            )
        ]
    if not _DNS_SLOTS.acquire(blocking=False):
        raise TimeoutError("Icon DNS workers busy")
    answer = queue.Queue(maxsize=1)

    def worker():
        try:
            result = socket.getaddrinfo(
                target.host,
                target.port,
                socket.AF_UNSPEC,
                socket.SOCK_STREAM,
                socket.IPPROTO_TCP,
            )
            answer.put((result, None))
        except Exception as exc:
            answer.put((None, exc))
        finally:
            _DNS_SLOTS.release()

    try:
        threading.Thread(target=worker, daemon=True, name="netmon-icon-dns").start()
    except BaseException:
        _DNS_SLOTS.release()
        raise
    try:
        result, error = answer.get(timeout=budget.remaining())
    except queue.Empty as exc:
        raise TimeoutError("Icon DNS deadline exceeded") from exc
    if error:
        raise OSError("Icon DNS failed") from error
    budget.remaining()
    if not result or len(result) > 32:
        raise ValueError("Invalid icon DNS answer count")
    approved = []
    for family, socktype, protocol, _, endpoint in result:
        if (
            family not in {socket.AF_INET, socket.AF_INET6}
            or socktype != socket.SOCK_STREAM
            or protocol != socket.IPPROTO_TCP
            or endpoint[1] != target.port
            or (family == socket.AF_INET6 and endpoint[3])
        ):
            raise ValueError("Invalid icon DNS answer")
        public_address(endpoint[0])
        if (family, endpoint) not in approved:
            approved.append((family, endpoint))
    return approved


def _connect(approved, budget, timeout):
    for family, endpoint in approved:
        connection = socket.socket(family, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        try:
            connection.settimeout(min(timeout, budget.remaining()))
            # endpoint is the validated numeric sockaddr. No create_connection(),
            # getaddrinfo(), proxy, or second hostname resolution is involved.
            connection.connect(endpoint)
            if ipaddress.ip_address(
                connection.getpeername()[0]
            ) != ipaddress.ip_address(endpoint[0]):
                raise ValueError("Icon peer differs from the approved IP")
            return connection
        except OSError:
            connection.close()
        except BaseException:
            connection.close()
            raise
    raise OSError("No approved icon address reachable")


class _DeadlineRaw(io.RawIOBase):
    def __init__(self, connection, budget, timeout):
        super().__init__()
        self.connection, self.budget, self.timeout = connection, budget, timeout
        self.reader = connection.makefile("rb", buffering=0)

    def readable(self):
        return True

    def readinto(self, buffer):
        self.connection.settimeout(min(self.timeout, self.budget.remaining()))
        size = self.reader.readinto(buffer)
        self.budget.remaining()
        return size

    def close(self):
        self.reader.close()
        super().close()


class _ResponseFile(io.BufferedReader):
    def __init__(self, raw):
        super().__init__(raw, buffer_size=16 * 1024)
        self.control_bytes = 0

    def readline(self, size=-1):
        line = super().readline(
            min(size if size >= 0 else MAX_CONTROL_BYTES + 1, MAX_CONTROL_BYTES + 1)
        )
        self.control_bytes += len(line)
        if self.control_bytes > MAX_CONTROL_BYTES:
            raise ValueError("Excessive HTTP headers/chunk framing")
        return line


class _ResponseSocket:
    def __init__(self, connection, budget, timeout):
        self.connection, self.budget, self.timeout = connection, budget, timeout

    def makefile(self, *_args, **_kwargs):
        return _ResponseFile(_DeadlineRaw(self.connection, self.budget, self.timeout))


class _PinnedConnection(http.client.HTTPConnection):
    def __init__(self, target, approved, budget, timeout):
        super().__init__(target.host, target.port, timeout=timeout)
        self.target, self.approved, self.budget = target, approved, budget
        self.response_class = lambda sock, **kwargs: http.client.HTTPResponse(
            _ResponseSocket(sock, budget, timeout), **kwargs
        )

    def connect(self):
        connection = _connect(self.approved, self.budget, self.timeout)
        try:
            if self.target.scheme == "https":
                connection.settimeout(min(self.timeout, self.budget.remaining()))
                connection = ssl.create_default_context().wrap_socket(
                    connection, server_hostname=self.target.host
                )
                self.budget.remaining()
            self.sock = connection
        except BaseException:
            connection.close()
            raise

    def send(self, data):
        if self.sock is None:
            self.connect()
        self.sock.settimeout(min(self.timeout, self.budget.remaining()))
        super().send(data)


@dataclass(frozen=True)
class Download:
    data: bytes
    content_type: str
    url: str


def fetch(
    url,
    *,
    limit=ICON_BYTES,
    budget=None,
    timeout=10,
    origin=None,
    origins=None,
    headers=None,
):
    budget = budget if budget is not None else DownloadBudget()
    current, visited = parse_url(url), set()
    safe_headers = {
        "User-Agent": "NetMon/icon",
        "Accept": "*/*",
        "Accept-Encoding": "identity",
        "Connection": "close",
    }
    for key, value in (headers or {}).items():
        if (
            key.lower() not in {"user-agent", "accept", "accept-language"}
            or len(value) > 512
            or "\r" in value
            or "\n" in value
        ):
            raise ValueError("Forbidden icon request header")
        safe_headers[key] = value
    for hop in range(MAX_REDIRECTS + 1):
        budget.request()
        if (
            current.url in visited
            or (origin is not None and current.origin != origin)
            or (origins is not None and current.origin not in origins)
        ):
            raise ValueError("Icon redirect loop or cross-origin metadata")
        visited.add(current.url)
        approved = _resolve(current, budget)
        connection = _PinnedConnection(current, approved, budget, timeout)
        response = None
        try:
            connection.request("GET", current.path, headers=safe_headers)
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                locations = response.headers.get_all("Location", [])
                if hop == MAX_REDIRECTS or len(locations) != 1:
                    raise ValueError("Excessive or ambiguous icon redirects")
                location = locations[0]
                if not location or any(
                    ord(char) <= 32 or char == "\\" for char in location
                ):
                    raise ValueError("Invalid icon redirect target")
                parsed = urlsplit(location)
                if location.startswith("//") and not parsed.netloc:
                    raise ValueError("Invalid icon redirect authority")
                candidate = parse_url(
                    location if parsed.scheme else urljoin(current.url, location)
                )
                if current.scheme == "https" and candidate.scheme != "https":
                    raise ValueError("HTTPS icon downgrade rejected")
                current = candidate
                continue  # close without reading the redirect body
            if response.status != 200:
                raise ValueError("Icon HTTP status rejected")
            encoding = response.headers.get("Content-Encoding", "identity").lower()
            lengths = response.headers.get_all("Content-Length", [])
            transfers = response.headers.get_all("Transfer-Encoding", [])
            if (
                encoding != "identity"
                or len(lengths) > 1
                or (lengths and transfers)
                or (transfers and transfers != ["chunked"])
            ):
                raise ValueError("Ambiguous or compressed HTTP icon response")
            expected = None
            if lengths:
                if not re.fullmatch(r"[0-9]{1,10}", lengths[0]):
                    raise ValueError("Invalid icon Content-Length")
                expected = int(lengths[0])
                if expected > limit:
                    raise ValueError("Icon Content-Length exceeds limit")
            chunks, count = [], 0
            while True:
                chunk = response.read1(
                    min(
                        CHUNK_BYTES,
                        limit - count + 1,
                        budget.max_bytes - budget.received + 1,
                    )
                )
                budget.remaining()
                if not chunk:
                    break
                count += len(chunk)
                budget.consume(len(chunk))
                if count > limit:
                    raise ValueError("Icon body exceeds limit")
                chunks.append(chunk)
            if expected is not None and expected != count:
                raise ValueError("Truncated icon response")
            return Download(
                b"".join(chunks), response.headers.get_content_type(), current.url
            )
        finally:
            if response is not None:
                response.close()
            connection.close()
    raise ValueError("Too many icon redirects")
