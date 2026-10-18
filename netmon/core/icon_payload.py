"""Small non-active icon formats and bounded raster decoder inputs."""

import binascii
import io
import math
import re
import struct
import xml.etree.ElementTree as ET

from netmon.core.icon_http import ICON_BYTES

MAX_DIMENSION = 2048
MAX_PIXELS = 4 * 1024 * 1024
MAX_ICO_IMAGES = 64
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
ET.register_namespace("", "http://www.w3.org/2000/svg")


def check_dimensions(width, height):
    if (
        not 0 < width <= MAX_DIMENSION
        or not 0 < height <= MAX_DIMENSION
        or width * height > MAX_PIXELS
    ):
        raise ValueError("Excessive icon dimensions")


def _png(payload):
    if len(payload) < 33 or payload[12:16] != b"IHDR":
        raise ValueError("Invalid PNG header")
    width, height, depth, color, compression, filtering, interlace = struct.unpack(
        ">2L5B", payload[16:29]
    )
    check_dimensions(width, height)
    if (
        compression
        or filtering
        or interlace not in {0, 1}
        or color not in {0, 2, 3, 4, 6}
        or depth not in {1, 2, 4, 8, 16}
    ):
        raise ValueError("Unsupported PNG header")
    offset, chunks, saw_data = 8, [PNG_MAGIC], False
    for _ in range(512):
        if offset + 12 > len(payload):
            break
        size, kind = struct.unpack(">L4s", payload[offset : offset + 8])
        end = offset + size + 12
        if end > len(payload):
            raise ValueError("Truncated PNG")
        content = payload[offset + 8 : end - 4]
        if binascii.crc32(kind + content) & 0xFFFFFFFF != int.from_bytes(
            payload[end - 4 : end], "big"
        ):
            raise ValueError("Invalid PNG checksum")
        if kind == b"acTL" or (kind == b"IHDR" and (offset != 8 or size != 13)):
            raise ValueError("Animated or ambiguous PNG")
        if kind in {
            b"IHDR",
            b"PLTE",
            b"IDAT",
            b"IEND",
            b"tRNS",
            b"gAMA",
            b"sRGB",
            b"cHRM",
        }:
            chunks.append(payload[offset:end])
        elif not kind[0] & 32:
            raise ValueError("Unknown critical PNG chunk")
        # Drop comments, compressed text, EXIF and other non-render metadata.
        if kind == b"IDAT":
            saw_data = True
        if kind == b"IEND":
            if size or not saw_data or end != len(payload):
                raise ValueError("Invalid PNG end")
            return b"".join(chunks)
        offset = end
    raise ValueError("Incomplete or excessive PNG chunks")


def _svg(payload):
    if b"<!" in payload or len(payload) > 128 * 1024:
        raise ValueError("SVG declarations/entities are not allowed")
    root = ET.fromstring(payload)
    if root.tag.split("}")[-1] != "svg":
        raise ValueError("Not SVG")
    allowed = {
        "svg",
        "g",
        "path",
        "rect",
        "circle",
        "ellipse",
        "line",
        "polyline",
        "polygon",
        "defs",
        "linearGradient",
        "radialGradient",
        "stop",
        "clipPath",
        "mask",
        "title",
        "desc",
        "text",
        "tspan",
    }
    view = root.get("viewBox", "").replace(",", " ").split()
    if len(view) == 4:
        values = [float(item) for item in view]
        if not all(math.isfinite(item) for item in values):
            raise ValueError("Invalid SVG viewBox")
        check_dimensions(values[2], values[3])
    for name in ("width", "height"):
        value = root.get(name)
        if value and value != "100%":
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)(?:px)?", value)
            if not match or not 0 < float(match[1]) <= MAX_DIMENSION:
                raise ValueError("Excessive SVG viewport")
    if len(view) != 4 and not all(
        root.get(name) and root.get(name) != "100%" for name in ("width", "height")
    ):
        raise ValueError("Missing SVG viewport")
    pending, count = [(root, 0)], 0
    while pending:
        element, depth = pending.pop()
        count += 1
        if (
            count > 2048
            or depth > 32
            or len(element.attrib) > 32
            or element.tag.split("}")[-1] not in allowed
            or (
                element.tag.startswith("{")
                and not element.tag.startswith("{http://www.w3.org/2000/svg}")
            )
        ):
            raise ValueError("Active or excessive SVG")
        for key, value in element.attrib.items():
            name = key.split("}")[-1].lower()
            lowered = value.lower()
            if (
                name.startswith("on")
                or name == "base"
                or "\\" in value
                or len(value) > 8192
                or any(
                    token in lowered
                    for token in (
                        "@import",
                        "javascript:",
                        "data:",
                        "http:",
                        "https:",
                        "//",
                        "expression(",
                    )
                )
            ):
                raise ValueError("Active SVG attribute")
            if name == "href" and not value.startswith("#"):
                raise ValueError("External SVG reference")
            if name == "style":
                for declaration in value.split(";"):
                    if not declaration.strip():
                        continue
                    property_name, separator, _ = declaration.partition(":")
                    if not separator or property_name.strip().lower() not in {
                        "fill",
                        "fill-opacity",
                        "fill-rule",
                        "stroke",
                        "stroke-opacity",
                        "stroke-width",
                        "stroke-linecap",
                        "stroke-linejoin",
                        "stroke-miterlimit",
                        "stroke-dasharray",
                        "stroke-dashoffset",
                        "opacity",
                        "stop-color",
                        "stop-opacity",
                        "color",
                        "display",
                        "visibility",
                    }:
                        raise ValueError("Unsupported SVG style property")
            if "url" in lowered and not re.fullmatch(
                r"[^u]*url\(#[a-zA-Z0-9_.-]+\)[^u]*", value
            ):
                raise ValueError("External SVG style")
        pending.extend((child, depth + 1) for child in element)
    return ET.tostring(root, encoding="utf-8")


def _raster_dimensions(payload):
    """Inspect dimensions before invoking optional native JPEG/GIF/WebP decoders."""
    if payload.startswith((b"GIF87a", b"GIF89a")) and len(payload) >= 10:
        check_dimensions(*struct.unpack_from("<2H", payload, 6))
        return
    if payload.startswith(b"\xff\xd8\xff"):
        offset = 2
        for _ in range(512):
            if offset + 4 > len(payload) or payload[offset] != 0xFF:
                break
            marker = payload[offset + 1]
            if marker == 0xFF:
                offset += 1
                continue
            size = int.from_bytes(payload[offset + 2 : offset + 4], "big")
            if size < 2 or offset + size + 2 > len(payload):
                break
            if marker in {0xC0, 0xC1, 0xC2} and size >= 8:
                height, width = struct.unpack_from(">2H", payload, offset + 5)
                check_dimensions(width, height)
                return
            offset += size + 2
        raise ValueError("Missing or excessive JPEG dimensions")
    if payload.startswith(b"RIFF") and payload[8:12] == b"WEBP":
        if int.from_bytes(payload[4:8], "little") + 8 != len(payload):
            raise ValueError("Invalid WebP length")
        offset, found = 12, False
        for _ in range(512):
            if offset == len(payload):
                if found:
                    return
                break
            if offset + 8 > len(payload):
                break
            kind = payload[offset : offset + 4]
            size = int.from_bytes(payload[offset + 4 : offset + 8], "little")
            data = payload[offset + 8 : offset + 8 + size]
            if len(data) != size or kind in {b"ANIM", b"ANMF"}:
                break
            if kind == b"VP8X" and len(data) == 10:
                check_dimensions(
                    1 + int.from_bytes(data[4:7], "little"),
                    1 + int.from_bytes(data[7:10], "little"),
                )
            elif kind == b"VP8 " and len(data) >= 10 and data[3:6] == b"\x9d\x01\x2a":
                width, height = struct.unpack_from("<2H", data, 6)
                check_dimensions(width & 0x3FFF, height & 0x3FFF)
                found = True
            elif kind == b"VP8L" and len(data) >= 5 and data[0] == 0x2F:
                bits = int.from_bytes(data[1:5], "little")
                check_dimensions(1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF))
                found = True
            offset += 8 + size + size % 2
        raise ValueError("Missing, animated or excessive WebP dimensions")
    raise ValueError("Unsupported icon signature")


def sanitize_icon(payload, *, allow_svg=True):
    if not payload or len(payload) > ICON_BYTES:
        raise ValueError("Invalid icon byte size")
    if payload.startswith(PNG_MAGIC):
        return ".png", _png(payload)
    if payload.startswith(b"\x00\x00\x01\x00"):
        count = int.from_bytes(payload[4:6], "little")
        if not 0 < count <= MAX_ICO_IMAGES or len(payload) < 6 + count * 16:
            raise ValueError("Invalid ICO directory")
        pngs, ranges = [], []
        for index in range(count):
            entry = payload[6 + index * 16 : 22 + index * 16]
            width, height = entry[0] or 256, entry[1] or 256
            check_dimensions(width, height)
            size, offset = struct.unpack_from("<2L", entry, 8)
            if not size or offset < 6 + count * 16 or offset + size > len(payload):
                raise ValueError("Invalid ICO member")
            if any(offset < end and offset + size > start for start, end in ranges):
                raise ValueError("Overlapping ICO members")
            ranges.append((offset, offset + size))
            data = payload[offset : offset + size]
            if data.startswith(PNG_MAGIC):
                clean = _png(data)
                if struct.unpack_from(">2L", clean, 16) != (width, height):
                    raise ValueError("ICO PNG dimensions mismatch")
                pngs.append(clean)
            else:
                if len(data) < 40 or int.from_bytes(data[:4], "little") < 40:
                    raise ValueError("Unsupported ICO bitmap")
                dib_width, dib_height = struct.unpack_from("<2l", data, 4)
                if dib_width != width or dib_height != height * 2:
                    raise ValueError("ICO bitmap dimensions mismatch")
        if pngs:
            return ".png", pngs[0]
        return ".ico", payload
    if allow_svg and b"<svg" in payload[:512].lower():
        return ".svg", _svg(payload)
    # Static JPEG/GIF/WebP radio logos require Pillow, not an unchecked Tk decode.
    _raster_dimensions(payload)
    from PIL import Image

    with Image.open(io.BytesIO(payload)) as image:
        check_dimensions(*image.size)
        if (
            image.format not in {"JPEG", "GIF", "WEBP"}
            or getattr(image, "n_frames", 1) != 1
        ):
            raise ValueError("Unsupported or animated icon")
        image.load()
        output = io.BytesIO()
        image.convert("RGBA").save(output, format="PNG")
        normalized = output.getvalue()
        if len(normalized) > ICON_BYTES:
            raise ValueError("Converted icon exceeds byte budget")
        return ".png", _png(normalized)
