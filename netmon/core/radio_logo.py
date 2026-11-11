"""Bounded raw logo pixels; HTTP and image codecs run only in child modes."""

import io
import struct
import sys

INPUT_BYTES = 1024 * 1024
SIZES = (110, 170, 88)
MAGIC = b"NMRL1\0"
MAX_REPLY_BYTES = len(MAGIC) + sum(4 + size * size * 4 for size in SIZES)


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

    _, clean = sanitize_icon(raw, allow_svg=False)
    with Image.open(
        io.BytesIO(clean), formats=["PNG", "JPEG", "GIF", "WEBP", "ICO"]
    ) as source:
        check_dimensions(*source.size)
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("Animated logo refused")
        source.load()
        image = source.convert("RGBA")
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
    try:
        if sys.argv[1:] not in (["--fetch"], ["--decode"]):
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
            value = decode_image(raw)
        else:
            import json
            from netmon.core import icon_http

            with open("/run/request.json", "rb") as handle:
                raw = handle.read(16385)
            if len(raw) > 16384:
                raise ValueError("Invalid logo request")
            request = json.loads(raw)
            value = icon_http.fetch(
                request["url"],
                limit=INPUT_BYTES,
                timeout=8,
                budget=icon_http.DownloadBudget(seconds=8),
            ).data
        sys.stdout.buffer.write(value)
        sys.stdout.buffer.flush()
        return 0
    except Exception:
        print("Protected radio logo failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
