"""Bounded raw logo pixels; HTTP and image codecs run only in child modes."""

import io
import struct
import sys

INPUT_BYTES = 1024 * 1024
SIZES = (110, 170, 88)
MAGIC = b"NMRL1\0"
MAX_REPLY_BYTES = len(MAGIC) + sum(4 + size * size * 4 for size in SIZES)
ERROR_MAGIC = b"NMRLE1:"
ERROR_CODES = frozenset(
    {
        "timeout",
        "blocked_url",
        "http",
        "network",
        "image_format",
        "image_limits",
        "image_data",
        "runtime",
    }
)
MAX_ICON_CANDIDATES = 3


def failure_code(error, *, decoder):
    """Return fixed diagnostics, never remote text or a possibly secret URL."""
    text = str(error).lower()
    if isinstance(error, TimeoutError) or "deadline" in text:
        return "timeout"
    if any(word in text for word in ("exceeds limit", "byte budget", "exceeds budget")):
        return "image_limits"
    if decoder:
        if isinstance(error, (ImportError, OSError, AttributeError)):
            return "runtime"
        if any(word in text for word in ("unsupported", "animated", "signature")):
            return "image_format"
        if any(word in text for word in ("excessive", "budget", "byte size")):
            return "image_limits"
        return "image_data"
    if "http status" in text:
        return "http"
    if any(
        word in text
        for word in (
            "forbidden",
            "nonpublic",
            "default http",
            "only http",
            "invalid icon url",
            "invalid icon hostname",
            "noncanonical",
            "trailing-dot",
            "special-purpose",
            "downgrade",
        )
    ):
        return "blocked_url"
    return "network"


def discover_icons(homepage):
    """Read bounded homepage metadata in the network child, without a browser."""
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlsplit
    from netmon.core import icon_http

    class Links(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.urls = []

        def handle_starttag(self, tag, attrs):
            if tag != "link" or len(self.urls) >= 8:
                return
            attrs = dict(attrs)
            rel = str(attrs.get("rel", "")).lower().split()
            href = attrs.get("href")
            if (
                not (
                    {"icon", "apple-touch-icon", "apple-touch-icon-precomposed"}
                    & set(rel)
                )
                or not href
            ):
                return
            try:
                parsed = icon_http.parse_url(urljoin(page.url, href))
                if urlsplit(page.url).scheme == "https" and parsed.scheme != "https":
                    return
                candidate = parsed.url
            except (ValueError, UnicodeError):
                return
            if candidate not in self.urls:
                self.urls.append(candidate)

    page = icon_http.fetch(
        homepage,
        limit=128 * 1024,
        timeout=4,
        budget=icon_http.DownloadBudget(
            seconds=4, max_requests=4, max_bytes=128 * 1024
        ),
    )
    parser = Links()
    if page.content_type in {"text/html", "application/xhtml+xml"}:
        parser.feed(page.data.decode("utf-8", errors="replace"))
    fallback = icon_http.parse_url(urljoin(page.url, "/favicon.ico")).url
    return list(dict.fromkeys([*parser.urls[: MAX_ICON_CANDIDATES - 1], fallback]))


def validate_pixels(payload):
    """Parse only our fixed dimensions and RGBA bytes, never image formats."""
    if (
        not isinstance(payload, bytes)
        or not payload.startswith(MAGIC)
        or len(payload) > MAX_REPLY_BYTES
    ):
        raise ValueError("Invalid raw logo")
    offset, images = len(MAGIC), []
    for size in SIZES:
        if offset + 4 > len(payload):
            raise ValueError("Truncated raw logo")
        width, height = struct.unpack_from(">HH", payload, offset)
        offset += 4
        if not 0 < width <= size or not 0 < height <= size:
            raise ValueError("Invalid raw logo dimensions")
        length = width * height * 4
        pixels = payload[offset : offset + length]
        if len(pixels) != length:
            raise ValueError("Truncated raw logo pixels")
        images.append((width, height, pixels))
        offset += length
    if offset != len(payload):
        raise ValueError("Trailing raw logo data")
    return tuple(images)


def decode_image(raw):
    import importlib
    from netmon.core.icon_payload import check_dimensions, sanitize_icon
    from PIL import Image

    for name in (
        "PngImagePlugin",
        "JpegImagePlugin",
        "GifImagePlugin",
        "WebPImagePlugin",
        "IcoImagePlugin",
    ):
        importlib.import_module("PIL." + name)

    suffix, clean = sanitize_icon(raw, allow_svg=True, raster_size=max(SIZES))
    if suffix == ".svg":
        from netmon.core.radio_svg import render_svg

        width, height, pixels = render_svg(clean, max(SIZES))
        image = Image.frombytes("RGBA", (width, height), pixels)
    else:
        with Image.open(
            io.BytesIO(clean), formats=["PNG", "JPEG", "GIF", "WEBP", "ICO"]
        ) as source:
            check_dimensions(*source.size)
            if getattr(source, "n_frames", 1) != 1:
                raise ValueError("Animated logo refused")
            source.load()
            image = source.convert("RGBA")
    image.thumbnail((max(SIZES), max(SIZES)))
    result = bytearray(MAGIC)
    for size in SIZES:
        thumbnail = image.copy()
        thumbnail.thumbnail((size, size))
        result.extend(struct.pack(">HH", *thumbnail.size))
        result.extend(thumbnail.tobytes())
    value = bytes(result)
    validate_pixels(value)
    return value


def apply_process_limits(*, decoder):
    import resource

    bounds = [(resource.RLIMIT_AS, 384 * 1024 * 1024), (resource.RLIMIT_CPU, 8)]
    if decoder:
        bounds.append((resource.RLIMIT_NPROC, 0))
    for name, maximum in bounds:
        soft, hard = resource.getrlimit(name)
        limit = min(
            [maximum]
            + [value for value in (soft, hard) if value != resource.RLIM_INFINITY]
        )
        resource.setrlimit(name, (limit, limit))


def main():
    decoder = sys.argv[1:] == ["--decode"]
    try:
        if sys.argv[1:] not in (["--fetch"], ["--decode"], ["--discover"]):
            raise ValueError("Invalid logo mode")
        decoder = sys.argv[1] == "--decode"
        apply_process_limits(decoder=decoder)
        # Only the individually mounted policy files form this namespace package.
        sys.path.insert(0, "/run")
        if decoder:
            sys.path.insert(0, "/usr/lib/python3/dist-packages")
            raw = sys.stdin.buffer.read(INPUT_BYTES + 1)
            if not raw or len(raw) > INPUT_BYTES:
                raise ValueError("Logo input exceeds budget")
            if (
                raw.startswith(ERROR_MAGIC)
                and raw[len(ERROR_MAGIC) :].decode("ascii") in ERROR_CODES
            ):
                sys.stdout.buffer.write(raw)
                return 2
            value = decode_image(raw)
        else:
            import json
            from netmon.core import icon_http

            with open("/run/request.json", "rb") as handle:
                raw = handle.read(16385)
            if len(raw) > 16384:
                raise ValueError("Invalid logo request")
            request = json.loads(raw)
            if sys.argv[1] == "--discover":
                value = json.dumps(discover_icons(request["url"])).encode("utf-8")
            else:
                value = icon_http.fetch(
                    request["url"],
                    limit=INPUT_BYTES,
                    timeout=8,
                    budget=icon_http.DownloadBudget(seconds=8),
                ).data
        sys.stdout.buffer.write(value)
        sys.stdout.buffer.flush()
        return 0
    except Exception as error:
        sys.stdout.buffer.write(
            ERROR_MAGIC + failure_code(error, decoder=decoder).encode("ascii")
        )
        sys.stdout.buffer.flush()
        print("Protected radio logo failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
