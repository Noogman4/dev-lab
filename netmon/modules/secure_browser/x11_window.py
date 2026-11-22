"""Set Weston window metadata through a short-lived host X11 connection."""

import ctypes
import sys

from PIL import Image


def _set_metadata(window_id, title, icon_path):
    x11 = ctypes.CDLL("libX11.so.6")
    x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
    x11.XOpenDisplay.restype = ctypes.c_void_p
    x11.XInternAtom.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
    x11.XInternAtom.restype = ctypes.c_ulong
    x11.XChangeProperty.argtypes = [
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_ulong,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    x11.XCloseDisplay.argtypes = [ctypes.c_void_p]

    with Image.open(icon_path) as logo:
        image = logo.convert("RGBA").resize((48, 48), Image.Resampling.LANCZOS)
    pixels = [
        (alpha << 24) | (red << 16) | (green << 8) | blue
        for red, green, blue, alpha in image.getdata()
    ]
    # Xlib expects native longs even when the X11 property is 32-bit.
    icon = (ctypes.c_ulong * (2 + len(pixels)))(*image.size, *pixels)
    name = title.encode("utf-8")
    display = x11.XOpenDisplay(None)
    if not display:
        return 1

    try:
        window = int(window_id)
        for prop, kind, format_bits, data in (
            (b"_NET_WM_NAME", b"UTF8_STRING", 8, name),
            (b"_NET_WM_ICON", b"CARDINAL", 32, icon),
        ):
            x11.XChangeProperty(
                display,
                window,
                x11.XInternAtom(display, prop, 0),
                x11.XInternAtom(display, kind, 0),
                format_bits,
                0,  # PropModeReplace
                data,
                len(data),
            )
    finally:
        x11.XCloseDisplay(display)
    return 0


if __name__ == "__main__":
    sys.exit(_set_metadata(*sys.argv[1:]))
