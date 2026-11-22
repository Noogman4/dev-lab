"""Bounded SVG rasterization, used only by the offline logo capsule."""

import ctypes as c
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from netmon.core.icon_payload import sanitize_icon

LIBRARY_DIR = Path("/run/svg")
LIBRARY_NAMES = ("librsvg-2.so.2", "libcairo.so.2", "libgobject-2.0.so.0")


class Rectangle(c.Structure):
    _fields_ = [(name, c.c_double) for name in ("x", "y", "width", "height")]


def _function(library, name, result, *arguments):
    function = getattr(library, name)
    function.restype, function.argtypes = result, list(arguments)
    return function


def render_svg(payload, size):
    """Filter first, then render from memory without any base URL or file name.

    Rsvg's memory constructor denies external file references without a base URL:
    https://gnome.pages.gitlab.gnome.org/librsvg/Rsvg-2.0/class.Handle.html
    The capsule also has no network, user files, browser or audio grants.
    """
    if type(size) is not int or not 0 < size <= 170:
        raise ValueError("Invalid SVG target size")
    suffix, clean = sanitize_icon(payload, allow_svg=True)
    if suffix != ".svg":
        raise ValueError("Unsupported SVG input")
    root = ET.fromstring(clean)
    # Pango text rendering starts a background thread. Keep the capsule's
    # existing no-new-process/thread limit; outlined lettering is ordinary paths.
    if any(element.tag.split("}")[-1] in {"text", "tspan"} for element in root.iter()):
        raise ValueError("Unsupported SVG text; outlined paths are supported")
    dimensions = [root.get(name, "100%") for name in ("width", "height")]
    if "100%" in dimensions:
        dimensions = root.get("viewBox", "").replace(",", " ").split()[2:]
    width, height = (float(value.removesuffix("px")) for value in dimensions)
    scale = size / max(width, height)
    width, height = max(1, round(width * scale)), max(1, round(height * scale))

    rsvg, cairo, gobject = (c.CDLL(str(LIBRARY_DIR / name)) for name in LIBRARY_NAMES)
    create_handle = _function(
        rsvg,
        "rsvg_handle_new_from_data",
        c.c_void_p,
        c.c_char_p,
        c.c_size_t,
        c.c_void_p,
    )
    render = _function(
        rsvg,
        "rsvg_handle_render_document",
        c.c_int,
        c.c_void_p,
        c.c_void_p,
        c.POINTER(Rectangle),
        c.c_void_p,
    )
    unref = _function(gobject, "g_object_unref", None, c.c_void_p)
    create_surface = _function(
        cairo, "cairo_image_surface_create", c.c_void_p, c.c_int, c.c_int, c.c_int
    )
    surface_status = _function(cairo, "cairo_surface_status", c.c_int, c.c_void_p)
    flush = _function(cairo, "cairo_surface_flush", None, c.c_void_p)
    stride_of = _function(cairo, "cairo_image_surface_get_stride", c.c_int, c.c_void_p)
    data_of = _function(cairo, "cairo_image_surface_get_data", c.c_void_p, c.c_void_p)
    destroy_surface = _function(cairo, "cairo_surface_destroy", None, c.c_void_p)
    create_context = _function(cairo, "cairo_create", c.c_void_p, c.c_void_p)
    context_status = _function(cairo, "cairo_status", c.c_int, c.c_void_p)
    destroy_context = _function(cairo, "cairo_destroy", None, c.c_void_p)

    handle = create_handle(clean, len(clean), None)
    if not handle:
        raise ValueError("Invalid SVG render input")
    surface = context = None
    try:
        # Cairo ARGB32 is premultiplied and native-endian; never copy it as RGBA.
        surface = create_surface(0, width, height)
        if not surface or surface_status(surface):
            raise ValueError("SVG surface allocation failed")
        context = create_context(surface)
        if not context or context_status(context):
            raise ValueError("SVG context allocation failed")
        viewport = Rectangle(0, 0, width, height)
        if not render(handle, context, c.byref(viewport), None):
            raise ValueError("SVG rendering failed")
        flush(surface)
        pointer = data_of(surface)
        if surface_status(surface) or stride_of(surface) != width * 4 or not pointer:
            raise ValueError("Invalid SVG surface pixels")
        data = c.string_at(pointer, width * height * 4)
        pixels = bytearray(len(data))
        for offset in range(0, len(data), 4):
            argb = int.from_bytes(data[offset : offset + 4], sys.byteorder)
            alpha = argb >> 24
            channels = [(argb >> shift) & 255 for shift in (16, 8, 0)]
            if alpha:
                channels = [
                    min(255, (value * 255 + alpha // 2) // alpha) for value in channels
                ]
            else:
                channels = [0, 0, 0]
            pixels[offset : offset + 4] = bytes([*channels, alpha])
        return width, height, bytes(pixels)
    finally:
        if context:
            destroy_context(context)
        if surface:
            destroy_surface(surface)
        unref(handle)
