"""Restricted HTTP(S) media, metadata, catalog and preset source, stdlib only.

Run as a separate restricted process. It receives one parent-selected URL,
never requests from the decoder. No proxies, cookies, credentials or retries.
"""

import http.client
import ipaddress
import json
import re
import socket
import ssl
import sys
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

REDIRECTS = {301, 302, 303, 307, 308}
PLAYLIST_TYPES = {
    "application/vnd.apple.mpegurl",
    "application/x-mpegurl",
    "audio/mpegurl",
    "audio/x-mpegurl",
    "audio/x-scpls",
    "application/dash+xml",
}
TRANSITION_NETS = tuple(
    ipaddress.ip_network(value)
    for value in (
        "64:ff9b::/96",
        "64:ff9b:1::/48",
        "2002::/16",
        "2001::/32",
    )
)
MAX_ICY_INTERVAL = 1024 * 1024
MAX_TITLE_CHARS = 512
MAX_CATALOG_BODY_BYTES = 16 * 1024 * 1024
MAX_PRESET_BODY_BYTES = 256 * 1024 * 1024


class SourceError(ValueError):
    """A bounded, URL-free failure suitable for the parent."""


class ConnectionFailure(SourceError):
    """A permitted destination could not be connected to."""


PROBE_MODES = {"probe-source", "probe-station", "probe-station-range"}


def parse_url(value, *, allow_playlist=False):
    if not isinstance(value, str) or not value or len(value) > 8192:
        raise SourceError("Invalid source URL")
    if any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value):
        raise SourceError("Invalid source URL")
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError
        if (
            parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
        ):
            raise ValueError
        host = parsed.hostname.encode("idna").decode("ascii")
        if "%" in host or "\\" in host:
            raise ValueError
        try:
            ipaddress.ip_address(host)
        except ValueError:
            if not re.fullmatch(r"[a-zA-Z0-9.-]+", host):
                raise ValueError
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if not 1 <= port <= 65535 or parsed.port == 0:
            raise ValueError
    except (ValueError, UnicodeError) as exc:
        raise SourceError("Invalid source URL") from exc
    if not allow_playlist and unquote(parsed.path).lower().endswith(
        (".m3u", ".m3u8", ".pls", ".mpd")
    ):
        raise SourceError(
            "Remote playlists are not supported by this playback boundary"
        )
    return parsed, host, port


def public_address(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    if not address.is_global or address.is_multicast or address.is_reserved:
        return False
    if isinstance(address, ipaddress.IPv4Address) and (
        address in ipaddress.ip_network("192.0.0.0/24")
        or address in ipaddress.ip_network("192.88.99.0/24")
    ):
        return False
    if isinstance(address, ipaddress.IPv6Address):
        if address.ipv4_mapped is not None:
            return False
        if any(address in network for network in TRANSITION_NETS):
            return False
    return True


def resolve_public(host, port):
    answers = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    if not answers or len(answers) > 32:
        raise SourceError("No bounded public address plan")
    plan = []
    for family, kind, protocol, _name, address in answers:
        if family not in {socket.AF_INET, socket.AF_INET6} or not public_address(
            address[0]
        ):
            raise SourceError("Non-public network destination refused")
        if (family, address) not in plan:
            plan.append((family, address))
    return plan


def connect_pinned(plan):
    # No second resolver call: the checked sockaddr itself is used by connect.
    # Cap attempts as well as per-attempt time; never fall back to other IPs.
    for family, address in plan[:2]:
        connection = socket.socket(family, socket.SOCK_STREAM)
        try:
            connection.settimeout(5)
            connection.connect(address)
            return connection
        except OSError:
            connection.close()
    raise ConnectionFailure("Source connection failed")


def open_connection(scheme, host, port, plan, *, idle_timeout=None):
    connection = http.client.HTTPConnection(host, port, timeout=idle_timeout or 10)

    def connect():
        transport = connect_pinned(plan)
        try:
            if idle_timeout is not None:
                transport.settimeout(idle_timeout)
            if scheme == "https":
                context = ssl.create_default_context(
                    cafile="/etc/ssl/certs/ca-certificates.crt"
                )
                transport = context.wrap_socket(transport, server_hostname=host)
            transport.settimeout(idle_timeout or 10)
            connection.sock = transport
        except Exception:
            transport.close()
            raise

    connection.connect = connect
    return connection


def _read_exact(response, size):
    result = bytearray()
    while len(result) < size:
        chunk = response.read1(min(4096, size - len(result)))
        if not chunk:
            raise SourceError("Incomplete ICY metadata")
        result.extend(chunk)
    return bytes(result)


def _icy_disabled(interval):
    # Plain playback only: "icy-metaint: 0" announces no interleaved metadata
    # (e.g. rautemusik). The title reader keeps refusing it (no title there).
    return interval is None or interval.strip() == "0"


def read_icy_title(response):
    interval = response.getheader("icy-metaint")
    if interval is None:
        return ""
    if (
        not re.fullmatch(r"[0-9]{1,7}", interval)
        or not 0 < int(interval) <= MAX_ICY_INTERVAL
    ):
        raise SourceError("Invalid ICY interval")
    remaining = int(interval)
    while remaining:
        amount = min(4096, remaining)
        _read_exact(response, amount)
        remaining -= amount
    length = _read_exact(response, 1)[0] * 16
    if length == 0:
        return ""
    text = _read_exact(response, length).decode("utf-8", errors="replace").strip("\0")
    match = re.search(r"StreamTitle='([^']*)';", text, flags=re.IGNORECASE)
    if match is None:
        match = re.search(r'StreamTitle="([^"]*)";', text, flags=re.IGNORECASE)
    if match is None:
        return ""
    title = "".join(char if char.isprintable() else " " for char in match[1])
    return " ".join(title.split())[:MAX_TITLE_CHARS]


def _preset_url(url):
    if (
        not isinstance(url, str)
        or not url
        or len(url) > 8192
        or any(ord(char) <= 32 or ord(char) == 127 or char == "\\" for char in url)
    ):
        raise SourceError("Invalid preset URL")
    parsed = urlsplit(url)
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


def transfer(url, destination, *, mode="stream", idle_timeout=None):
    catalog = mode in {"catalog-json", "catalog-post", "catalog-xml"}
    preset = mode == "preset"
    if preset:
        idle_timeout = float(idle_timeout if idle_timeout is not None else 30)
        if not 0 < idle_timeout <= 300:
            raise SourceError("Invalid preset timeout")
        url = _preset_url(url)
    probe = mode in PROBE_MODES
    station = mode in {"probe-station", "probe-station-range"}
    if not probe and mode not in {
        "stream",
        "icy",
        "catalog-json",
        "catalog-post",
        "catalog-xml",
        "preset",
    }:
        raise SourceError("Invalid source mode")
    # Bounds apply to untrusted response headers; the live body is streamed.
    http.client._MAXLINE = 8192
    http.client._MAXHEADERS = 64
    visited = set()
    for step in range(6):
        if preset:
            if url in visited:
                raise SourceError("Preset redirect loop")
            visited.add(url)
        parsed, host, port = parse_url(url, allow_playlist=probe or preset)
        plan = resolve_public(host, port)
        connection = (
            open_connection(parsed.scheme, host, port, plan, idle_timeout=idle_timeout)
            if preset
            else open_connection(parsed.scheme, host, port, plan)
        )
        response = None
        try:
            path = parsed.path or "/"
            if parsed.query:
                path += "?" + parsed.query
            headers = {
                "User-Agent": "NetMon-Radio/1",
                "Connection": "close",
                "Accept-Encoding": "identity",
                "Icy-MetaData": "1" if mode in {"icy", "probe-station-range"} else "0",
            }
            if probe:
                headers["Accept"] = "*/*"
            if preset:
                headers["Accept"] = "application/zip"
            if mode == "probe-station-range":
                headers["Range"] = "bytes=0-0"
            body = None
            method = "GET"
            if mode == "catalog-post":
                method = "POST"
                body = b'{"hidebroken":true,"limit":5000,"offset":0}'
                headers["Content-Type"] = "application/json"
            if catalog:
                headers["Accept"] = (
                    "application/xml" if mode == "catalog-xml" else "application/json"
                )
                connection.request(method, path, body=body, headers=headers)
            else:
                connection.request(method, path, headers=headers)
            try:
                response = connection.getresponse()
            except http.client.BadStatusLine as exc:
                if not probe:
                    raise
                if isinstance(exc, http.client.RemoteDisconnected):
                    return False
                # An ICY status proves a responding service, not playable media.
                # A bare ICY/HTTP prefix is insufficient evidence.
                match = re.fullmatch(
                    r"ICY ([1-5][0-9]{2})(?: [^\r\n]*)?\r?\n?",
                    exc.line,
                    flags=re.IGNORECASE,
                )
                return (
                    _reachable_status(int(match[1]), station=True)
                    if station and match
                    else None
                )
            if response.status in REDIRECTS:
                target = response.getheader("Location")
                if preset and len(response.headers.get_all("Location", [])) != 1:
                    raise SourceError("Ambiguous preset redirect")
                if (
                    step == 5
                    or not target
                    or len(target) > 8192
                    or any(
                        char.isspace() or ord(char) < 32 or ord(char) == 127
                        for char in target
                    )
                ):
                    raise SourceError("Source redirect refused")
                target = urljoin(url, target)
                if preset:
                    target = _preset_url(target)
                redirected, _host, _port = parse_url(
                    target, allow_playlist=probe or preset
                )
                if parsed.scheme == "https" and redirected.scheme != "https":
                    raise SourceError("TLS downgrade refused")
                if mode == "catalog-post" and response.status == 303:
                    raise SourceError("Catalog POST redirect method refused")
                url = target
                continue
            if probe:
                # Headers suffice. Never read or parse a remote response body.
                return _reachable_status(response.status, station=station)
            if response.status != 200:
                raise SourceError("Source HTTP status refused")
            content_type = (
                (response.getheader("Content-Type") or "")
                .split(";", 1)[0]
                .strip()
                .lower()
            )
            if content_type in PLAYLIST_TYPES:
                raise SourceError(
                    "Remote playlists are not supported by this playback boundary"
                )
            encoding = (
                (response.getheader("Content-Encoding") or "identity").strip().lower()
            )
            if encoding != "identity":
                raise SourceError("Encoded source body refused")
            if mode == "icy":
                destination.write(
                    json.dumps({"title": read_icy_title(response)}).encode("utf-8")
                )
                destination.flush()
                return
            interval = response.getheader("icy-metaint")
            if interval and not _icy_disabled(interval):
                raise SourceError("Unexpected interleaved metadata refused")
            if preset:
                lengths = response.headers.get_all("Content-Length", [])
                transfers = response.headers.get_all("Transfer-Encoding", [])
                if (
                    len(lengths) > 1
                    or (lengths and transfers)
                    or (transfers and transfers != ["chunked"])
                ):
                    raise SourceError("Ambiguous preset response")
                if lengths and (
                    not re.fullmatch(r"[0-9]{1,10}", lengths[0])
                    or int(lengths[0]) > MAX_PRESET_BODY_BYTES
                ):
                    raise SourceError("Preset length exceeds limit")
                count = 0
                while True:
                    chunk = response.read1(
                        min(16384, MAX_PRESET_BODY_BYTES + 1 - count)
                    )
                    if not chunk:
                        if response.length is not None and response.length > 0:
                            raise SourceError("Incomplete preset body")
                        return
                    count += len(chunk)
                    if count > MAX_PRESET_BODY_BYTES:
                        raise SourceError("Preset body exceeds limit")
                    destination.write(chunk)
                    destination.flush()
            if catalog:
                raw = bytearray()
                if (
                    response.length is not None
                    and response.length > MAX_CATALOG_BODY_BYTES
                ):
                    raise SourceError("Catalog body exceeds limit")
                while True:
                    chunk = response.read1(
                        min(16384, MAX_CATALOG_BODY_BYTES + 1 - len(raw))
                    )
                    if not chunk:
                        if response.length is not None and response.length > 0:
                            raise SourceError("Incomplete catalog body")
                        break
                    raw.extend(chunk)
                    if len(raw) > MAX_CATALOG_BODY_BYTES:
                        raise SourceError("Catalog body exceeds limit")
                destination.write(raw)
                destination.flush()
                return
            while True:
                chunk = response.read1(16384)
                if not chunk:
                    if response.length is not None and response.length > 0:
                        raise SourceError("Incomplete source body")
                    return
                destination.write(chunk)
                destination.flush()
        finally:
            if response is not None:
                response.close()
            connection.close()


def _reachable_status(status, *, station):
    return (
        200 <= status < 300
        or status in {401, 403, 405, 406}
        or (station and status == 416)
    )


def probe_reachability(url, *, mode):
    """Policy refusals stay unknown; ordinary transport failures are offline."""
    if mode not in PROBE_MODES:
        raise SourceError("Invalid probe mode")
    try:
        return transfer(url, None, mode=mode)
    except ConnectionFailure:
        return False
    except SourceError:
        return None
    except (OSError, http.client.HTTPException):
        return False


# CPU seconds per mode; live streams run for hours and are bounded by the
# playback/recording scope (CPUQuota) instead of a cumulative CPU limit.
CPU_SECONDS = {"stream": None, "preset": 120}
DEFAULT_CPU_SECONDS = 30


def apply_process_limits(mode):
    """Hard self-limits before any network I/O (helper runs without caps)."""
    import resource

    bounds = [
        (resource.RLIMIT_AS, 256 * 1024 * 1024),
        (resource.RLIMIT_NOFILE, 64),
        (resource.RLIMIT_FSIZE, 1024 * 1024),
        (resource.RLIMIT_CORE, 0),
        (resource.RLIMIT_NPROC, 0),  # no new processes or threads
    ]
    seconds = CPU_SECONDS.get(mode, DEFAULT_CPU_SECONDS)
    if seconds is not None:
        bounds.append((resource.RLIMIT_CPU, seconds))
    for name, maximum in bounds:
        soft, hard = resource.getrlimit(name)
        limit = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (limit, limit))


def main():
    try:
        with open("/run/request.json", "rb") as request:
            data = request.read(16385)
        if len(data) > 16384:
            raise SourceError("Invalid source request")
        request = json.loads(data)
        mode = request.get("mode", "stream")
        if not isinstance(mode, str):
            raise SourceError("Invalid source mode")
        # The request file is written by NetMon; limits precede any network.
        apply_process_limits(mode)
        if mode in PROBE_MODES:
            result = probe_reachability(request["url"], mode=mode)
            sys.stdout.buffer.write(json.dumps({"reachable": result}).encode("utf-8"))
            sys.stdout.buffer.flush()
        else:
            transfer(
                request["url"],
                sys.stdout.buffer,
                mode=mode,
                idle_timeout=request.get("timeout") if mode == "preset" else None,
            )
        return 0
    except Exception:
        # Neither the URL (which may include a token) nor response contents
        # belong in stderr, application logs or exception messages.
        print("Protected radio source failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
