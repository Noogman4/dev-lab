"""HTTP transport with explicit redirects; intermediate bodies are never read."""

import http.client
import ipaddress
import socket
import time
from contextlib import contextmanager
from urllib import request as urllib_request
from urllib.parse import urljoin, urlsplit, urlunsplit

from netmon.core.archive_limits import COPY_CHUNK_BYTES

MAX_REDIRECTS = 5
MAX_DOWNLOAD_SECONDS = 300
REDIRECT_CODES = {301, 302, 303, 307, 308}


def _public_addresses(host, port):
    """Resolve once and reject the entire answer if any address is not public."""
    addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not addresses:
        raise ValueError("Preset download host has no public addresses.")
    for family, _, _, _, sockaddr in addresses:
        address = ipaddress.ip_address(sockaddr[0])
        mapped = getattr(address, "ipv4_mapped", None)
        if (
            family not in {socket.AF_INET, socket.AF_INET6}
            or not address.is_global
            or address.is_multicast
            or address.is_reserved
            or address.is_loopback
            or address.is_link_local
            or address.is_unspecified
            or (mapped is not None and not mapped.is_global)
            or getattr(address, "sixtofour", None) is not None
            or getattr(address, "teredo", None) is not None
        ):
            raise ValueError("Preset downloads require public network addresses.")
    return addresses


def _connect_public(
    address, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, source_address=None
):
    # Connect to the checked sockaddr directly: never resolve the hostname again.
    addresses = _public_addresses(*address)
    error = None
    for family, socktype, proto, _, sockaddr in addresses:
        sock = socket.socket(family, socktype, proto)
        try:
            if timeout is not socket._GLOBAL_DEFAULT_TIMEOUT:
                sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            sock.connect(sockaddr)
            return sock
        except OSError as exc:
            sock.close()
            error = exc
    raise error


class _PublicHTTPConnection(http.client.HTTPConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._create_connection = _connect_public


class _PublicHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # HTTPSConnection still verifies certificates and sends SNI for self.host.
        self._create_connection = _connect_public


class _PublicHTTPHandler(urllib_request.HTTPHandler):
    def http_open(self, request):
        return self.do_open(_PublicHTTPConnection, request)


class _PublicHTTPSHandler(urllib_request.HTTPSHandler):
    def https_open(self, request):
        return self.do_open(
            _PublicHTTPSConnection,
            request,
            context=self._context,
        )


class _RawResponses(urllib_request.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response

    https_response = http_response


def _build_opener():
    # Replaces HTTPErrorProcessor, preventing urllib's automatic redirect drain.
    # Environment proxies could resolve the destination themselves, bypassing
    # address pinning. Downloads therefore use direct connections only.
    return urllib_request.build_opener(
        urllib_request.ProxyHandler({}),
        _PublicHTTPHandler(),
        _PublicHTTPSHandler(),
        _RawResponses(),
    )


def _validated_url(url):
    url = str(url or "").strip()
    if (
        len(url) > 8192
        or any(ord(char) <= 32 or ord(char) == 127 for char in url)
        or "\\" in url
    ):
        raise ValueError("Invalid preset download URL.")
    parts = urlsplit(url)
    if (
        parts.scheme.lower() not in {"http", "https"}
        or not parts.hostname
        or parts.username is not None
        or parts.password is not None
        or (parts.port is not None and not 0 < parts.port < 65536)
    ):
        raise ValueError("Preset downloads require an HTTP(S) URL without credentials.")
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, "")
    )


def _remaining(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Preset download exceeded its time budget.")
    return remaining


class _TimedResponse:
    def __init__(self, response, deadline):
        self.response = response
        self.deadline = deadline
        self.headers = response.headers

    def read(self, size):
        if not 0 < size <= COPY_CHUNK_BYTES:
            raise ValueError("Unbounded preset response read.")
        _remaining(self.deadline)
        # read1 returns available body data instead of filling a 64-KiB block,
        # allowing deadline checks between partial body reads.
        chunk = self.response.read1(size)
        _remaining(self.deadline)
        return chunk


@contextmanager
def open_preset_response(url, *, timeout):
    deadline = time.monotonic() + MAX_DOWNLOAD_SECONDS
    current = _validated_url(url)
    visited = set()
    opener = _build_opener()
    for hop in range(MAX_REDIRECTS + 1):
        if current in visited:
            raise ValueError("Preset redirect loop.")
        visited.add(current)
        remaining = _remaining(deadline)
        # Construct a fresh request on every hop. No Authorization, Cookie,
        # Referer or URL credentials can be inherited across origins.
        request = urllib_request.Request(
            current,
            headers={
                "Accept": "application/zip",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )
        with opener.open(request, timeout=min(timeout, remaining)) as response:
            _remaining(deadline)
            if response.status in REDIRECT_CODES:
                if hop == MAX_REDIRECTS:
                    raise ValueError("Too many preset redirects.")
                locations = response.headers.get_all("Location", [])
                if len(locations) != 1 or not locations[0].strip():
                    raise ValueError("Missing or ambiguous preset redirect target.")
                location = locations[0].strip()
                if any(ord(char) < 32 or ord(char) == 127 for char in location):
                    raise ValueError("Invalid preset redirect target.")
                target_parts = urlsplit(location)
                if location.startswith("//") and not target_parts.netloc:
                    raise ValueError("Invalid preset redirect target.")
                target = location if target_parts.scheme else urljoin(current, location)
                current = _validated_url(target)
                # Exiting the context closes the connection without reading.
                continue
            if response.status != 200:
                raise ValueError(f"Preset download returned HTTP {response.status}.")
            yield _TimedResponse(response, deadline)
            return
