"""Bounded metadata, safe image inputs and offline UI/cache compatibility."""

import binascii
import io
import json
import os
import struct
import threading
from types import SimpleNamespace

from PIL import Image
import pytest

from netmon.core import icon_http as web
from netmon.core import icon_payload as icons
from netmon import netmon_radio_app as radio
from tools.secure_browser_manager import browser_container_builder as builder


def png(width=1, height=1):
    output = io.BytesIO()
    Image.new("RGBA", (width, height), "red").save(output, format="PNG")
    return output.getvalue()


def chunk(kind, data):
    return (
        struct.pack(">L", len(data))
        + kind
        + data
        + struct.pack(">L", binascii.crc32(kind + data) & 0xFFFFFFFF)
    )


def spec(tmp_path):
    return builder.ContainerSpec(
        name="firefox-test",
        path=tmp_path / "container",
        allowed_domains=["icons.example.com"],
        source_firefox_dir=tmp_path / "source",
        homepage_url="https://icons.example.com/",
        icon_mode="favicon",
    )


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1/icon.png",
        "http://[::1]/icon.png",
        "https://10.0.0.1/icon.png",
        "https://other.example.com/icon.png",
        "http://icons.example.com/icon.png",
        "https://user@icons.example.com/icon.png",
        "https://icons.example.com:8080/icon.png",
    ],
)
def test_html_and_manifest_links_reject_other_origins(url):
    base = "https://icons.example.com/"
    assert builder.extract_icon_links(f'<link rel="icon" href="{url}">', base) == []
    assert (
        builder.extract_manifest_links(f'<link rel="manifest" href="{url}">', base)
        == []
    )
    assert (
        builder.extract_manifest_icon_links(json.dumps({"icons": [{"src": url}]}), base)
        == []
    )


def test_html_and_manifest_candidates_bounded():
    base = "https://icons.example.com/path/"
    html = "".join(
        f'<link rel="icon" href="{i}.png"><link rel="manifest" href="{i}.json">'
        for i in range(10000)
    )
    parser = builder.IconLinkParser()
    parser.feed(html)
    assert len(parser.links) == len(parser.manifests) == web.MAX_METADATA_LINKS
    assert len(builder.extract_icon_links(html, base)) == web.MAX_CANDIDATES
    assert len(builder.extract_manifest_links(html, base)) == web.MAX_MANIFESTS
    manifest = json.dumps(
        {"icons": [{"src": f"{i}.png", "sizes": "128x128"} for i in range(10000)]}
    )
    assert (
        len(builder.extract_manifest_icon_links(manifest, base)) == web.MAX_CANDIDATES
    )


@pytest.mark.parametrize(
    "manifest",
    ["{", "[]", "null", '{"icons":false}', '{"icons":[null,1,"x"]}', "[" * 2000],
)
def test_invalid_manifest_safe(manifest):
    assert (
        builder.extract_manifest_icon_links(manifest, "https://icons.example.com/")
        == []
    )


def test_resolver_attempts_and_shared_budget_bounded(tmp_path, monkeypatch):
    calls = []
    html = "".join(
        f'<link rel="icon" href="/{i}.png"><link rel="manifest" href="/{i}.json">'
        for i in range(1000)
    ).encode()

    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        if kwargs["kind"] == "html":
            return html, "text/html"
        if kwargs["kind"] == "manifest":
            return (
                json.dumps(
                    {"icons": [{"src": f"/{i}.png"} for i in range(1000)]}
                ).encode(),
                "application/json",
            )
        raise OSError("offline")

    monkeypatch.setattr(builder, "fetch_url", fetch)
    assert builder.resolve_favicon_download(spec(tmp_path)) == (None, None, None)
    assert len(calls) == 1 + web.MAX_MANIFESTS + web.MAX_CANDIDATES
    assert len({id(kwargs["budget"]) for _, kwargs in calls}) == 1
    assert calls[0][1]["budget"].max_requests == 12
    assert calls[0][1]["budget"].max_bytes == 3 * 1024 * 1024
    assert calls[0][1]["budget"].seconds == 20
    for _, kwargs in calls[1:-1]:
        assert kwargs["origin"] == ("https", "icons.example.com", 443)
    services = calls[-1][1]["origins"]
    assert services == frozenset(
        {
            ("https", "www.google.com", 443),
            *(("https", f"t{i}.gstatic.com", 443) for i in range(4)),
        }
    )


def test_rejected_metadata_never_reaches_fetch(tmp_path, monkeypatch):
    calls = []

    def fetch(url, **kwargs):
        calls.append(url)
        if kwargs["kind"] == "html":
            return (
                b'<link rel="icon" href="http://127.0.0.1/a"><link rel="manifest" href="http://169.254.169.254/a"><link rel="icon" href="https://other.example.com/a">',
                "text/html",
            )
        raise OSError("offline")

    monkeypatch.setattr(builder, "fetch_url", fetch)
    assert builder.resolve_favicon_download(spec(tmp_path)) == (None, None, None)
    assert len(calls) == 3
    assert not any(
        "127.0.0.1" in url or "169.254" in url or "other.example" in url
        for url in calls
    )


def test_manifest_relative_icon_success(tmp_path, monkeypatch):
    source = spec(tmp_path)
    calls = []

    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        if kwargs["kind"] == "html":
            kwargs["budget"].last_url = "https://www.example.com/home"
            return b'<link rel="manifest" href="/assets/app.json">', "text/html"
        if kwargs["kind"] == "manifest":
            kwargs["budget"].last_url = "https://www.example.com/assets/final.json"
            return (
                b'{"icons":[{"src":"logo.png","sizes":"128x128"}]}',
                "application/json",
            )
        assert url == "https://www.example.com/assets/logo.png"
        assert kwargs["origin"] == ("https", "www.example.com", 443)
        return png(), "image/png"

    monkeypatch.setattr(builder, "fetch_url", fetch)
    path, error = builder.prepare_container_icon(source)
    assert error is None
    assert open(path, "rb").read() == png()
    assert len(calls) == 3


def test_service_query_cannot_inject_parameters():
    url = builder.get_public_favicon_fallback_urls("example.com&domain=127.0.0.1")[0]
    assert "domain=example.com%26domain%3D127.0.0.1" in url


def test_png_discards_compressed_metadata():
    payload = png()
    payload = (
        payload[:-12]
        + chunk(b"zTXt", b"comment\x00\x00fake-compressed-bomb")
        + payload[-12:]
    )
    suffix, clean = icons.sanitize_icon(payload)
    assert suffix == ".png" and clean == png()


@pytest.mark.parametrize("dimension", [0, 2049, 100000, 0xFFFFFFFF])
def test_png_dimensions_rejected_before_decode(dimension):
    payload = (
        icons.PNG_MAGIC
        + chunk(b"IHDR", struct.pack(">2L5B", dimension, dimension, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", b"x")
        + chunk(b"IEND", b"")
    )
    with pytest.raises(ValueError, match="dimensions"):
        icons.sanitize_icon(payload)


def test_png_checksum_and_animation_rejected():
    with pytest.raises(ValueError, match="checksum"):
        icons.sanitize_icon(png()[:40] + b"bad" + png()[43:])
    animated = png()[:33] + chunk(b"acTL", b"12345678") + png()[33:]
    with pytest.raises(ValueError, match="Animated"):
        icons.sanitize_icon(animated)


@pytest.mark.parametrize("format", ["JPEG", "GIF", "WEBP"])
def test_static_raster_logos_normalized(format):
    output = io.BytesIO()
    Image.new("RGB", (32, 32), "red").save(output, format=format)
    suffix, data = icons.sanitize_icon(output.getvalue())
    assert suffix == ".png"
    with Image.open(io.BytesIO(data)) as image:
        assert image.size == (32, 32)


def test_animated_gif_rejected():
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        output,
        format="GIF",
        save_all=True,
        append_images=[Image.new("RGB", (2, 2), "blue")],
    )
    with pytest.raises(ValueError, match="animated"):
        icons.sanitize_icon(output.getvalue())


def test_ico_embedded_png_and_classic_bitmap():
    output = io.BytesIO()
    Image.new("RGBA", (16, 16), "red").save(output, format="ICO")
    assert icons.sanitize_icon(output.getvalue())[0] == ".png"
    output = io.BytesIO()
    Image.new("RGBA", (16, 16), "red").save(output, format="ICO", bitmap_format="bmp")
    assert icons.sanitize_icon(output.getvalue())[0] == ".ico"


def test_overlapping_ico_images_cannot_multiply_work():
    payload = png()
    entry = b"\x01\x01\x00\x00\x01\x00\x20\x00" + struct.pack("<2L", len(payload), 38)
    with pytest.raises(ValueError, match="Overlapping"):
        icons.sanitize_icon(b"\x00\x00\x01\x00\x02\x00" + entry * 2 + payload)


@pytest.mark.parametrize(
    "payload",
    [
        b'<svg width="2049" height="2"/>',
        b'<svg width="100%" height="100%"/>',
        b'<svg viewBox="0 0 nan 1"/>',
        b'<svg viewBox="0 0 1 1"><script/></svg>',
        b'<svg viewBox="0 0 1 1"><image href="http://127.0.0.1/a"/></svg>',
        b'<svg viewBox="0 0 1 1"><path onload="alert(1)"/></svg>',
        b'<svg viewBox="0 0 1 1"><path fill="url(http://127.0.0.1/a)"/></svg>',
        b'<svg viewBox="0 0 1 1"><style>@import "a";</style></svg>',
        b'<!DOCTYPE svg [<!ENTITY a SYSTEM "file:///etc/passwd">]><svg>&a;</svg>',
        b'<svg viewBox="0 0 1 1"><use href="#cycle" id="cycle"/></svg>',
        b'<svg viewBox="0 0 1 1"><g xmlns="urn:active"/></svg>',
        b'<svg viewBox="0 0 1 1">' + b"<g>" * 34 + b"</g>" * 34 + b"</svg>",
    ],
)
def test_active_or_excessive_svg_rejected(payload):
    with pytest.raises(ValueError):
        icons.sanitize_icon(payload)


@pytest.mark.parametrize(
    "attribute",
    [
        r'style="fill:u\72l(\68ttp://127.0.0.1/a)"',
        'xml:base="../private"',
        'href="relative-resource.svg"',
    ],
)
def test_svg_base_and_escaped_external_references_rejected(attribute):
    with pytest.raises(ValueError):
        icons.sanitize_icon(
            f'<svg viewBox="0 0 16 16"><path {attribute}/></svg>'.encode()
        )


@pytest.mark.parametrize(
    "style", ["width:999999999px", "height:999999999px", "filter:blur(999999px)"]
)
def test_svg_css_cannot_override_size_budget(style):
    with pytest.raises(ValueError, match="style property"):
        icons.sanitize_icon(f'<svg viewBox="0 0 16 16" style="{style}"/>'.encode())


def test_simple_svg_inline_colors_remain_compatible():
    suffix, clean = icons.sanitize_icon(
        b'<svg viewBox="0 0 16 16"><path style="fill:red;stroke:black;stroke-width:1"/></svg>'
    )
    assert suffix == ".svg" and b"fill:red" in clean


def test_valid_svg_repeatable_and_processing_instruction_removed():
    payload = b'<?xml-stylesheet href="http://127.0.0.1/a"?><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><path fill="red" d="M0 0h32v32z"/></svg>'
    suffix, clean = icons.sanitize_icon(payload)
    assert suffix == ".svg" and b"stylesheet" not in clean and b"127.0.0.1" not in clean
    assert icons.sanitize_icon(clean) == (suffix, clean)


def test_builder_invalid_image_does_not_modify_existing_icon(tmp_path, monkeypatch):
    source = spec(tmp_path)
    existing = source.path / "icons" / "favicon.png"
    existing.parent.mkdir(parents=True)
    existing.write_bytes(png())
    monkeypatch.setattr(
        builder,
        "resolve_favicon_download",
        lambda _s: ("https://icons.example.com/a", b"not a picture", "image/png"),
    )
    _, warning = builder.prepare_container_icon(source)
    assert warning
    assert existing.read_bytes() == png()
    assert list(existing.parent.iterdir()) == [existing]


def radio_stub(tmp_path):
    app = SimpleNamespace(
        radio_logo_cache_dir=str(tmp_path),
        _radio_logo_request_key="station",
        placeholders=[],
        rendered=[],
    )
    app.after = lambda _delay, callback: callback()
    app._set_radio_logo_placeholder = lambda *args: app.placeholders.append(args)
    app._render_station_logo_file = lambda *args: app.rendered.append(args)
    return app


@pytest.mark.parametrize("failure", ["network", "payload", "write", "replace"])
def test_radio_failure_preserves_cache_and_cleans_temporary(
    tmp_path, monkeypatch, failure
):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    cache.write_bytes(png())

    def fetch(*_a, **_kwargs):
        if failure == "network":
            raise OSError("offline")
        return web.Download(
            b"bad" if failure == "payload" else png(),
            "image/png",
            "https://icons.example.com/",
        )

    monkeypatch.setattr(web, "fetch", fetch)
    if failure == "write":
        monkeypatch.setattr(
            radio.tempfile,
            "NamedTemporaryFile",
            lambda **_kw: (_ for _ in ()).throw(OSError("disk full")),
        )
    if failure == "replace":
        monkeypatch.setattr(
            radio.os,
            "replace",
            lambda *_a: (_ for _ in ()).throw(OSError("rename failed")),
        )
    radio.NetMonRadioApp._download_station_logo(
        app, "https://icons.example.com/", str(cache), "station"
    )
    assert cache.read_bytes() == png()
    assert list(tmp_path.iterdir()) == [cache]
    assert app.placeholders and not app.rendered


def test_rejected_radio_address_never_decoded(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    monkeypatch.setattr(
        radio.Image, "open", lambda *_a: pytest.fail("Rejected response decoded")
    )
    monkeypatch.setattr(
        web, "_connect", lambda *_a: pytest.fail("Private target connected")
    )
    radio.NetMonRadioApp._download_station_logo(
        app, "http://127.0.0.1/", str(tmp_path / "cache.png"), "station"
    )
    assert app.placeholders and not list(tmp_path.iterdir())


def test_radio_download_atomically_caches_valid_image(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    calls = []

    def fetch(url, **kwargs):
        calls.append(kwargs)
        return web.Download(png(), "image/png", url)

    monkeypatch.setattr(web, "fetch", fetch)
    radio.NetMonRadioApp._download_station_logo(
        app, "https://icons.example.com/", str(cache), "station"
    )
    assert cache.read_bytes() == png() and not app.placeholders
    assert app.rendered == [(str(cache), "station")]
    assert cache.stat().st_mode & 0o777 == 0o600
    assert calls[0]["budget"].seconds == calls[0]["timeout"] == 8


@pytest.mark.parametrize("kind", ["symlink", "fifo", "oversized", "invalid"])
def test_unsafe_cached_radio_image_not_decoded(tmp_path, monkeypatch, kind):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    if kind == "symlink":
        target = tmp_path / "target"
        target.write_bytes(png())
        cache.symlink_to(target)
    elif kind == "fifo":
        os.mkfifo(cache)
    elif kind == "oversized":
        cache.write_bytes(b"x" * (web.ICON_BYTES + 1))
    else:
        cache.write_bytes(b"invalid")
    monkeypatch.setattr(
        radio.Image, "open", lambda *_a: pytest.fail("Unsafe cache decoded")
    )
    radio.NetMonRadioApp._render_station_logo_file(app, str(cache), "station")
    assert app.placeholders


def test_radio_cache_hit_needs_no_network(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    cache.write_bytes(png())
    app._station_logo_url = lambda _s: "https://icons.example.com/"
    app._station_logo_cache_path = lambda _url: str(cache)
    monkeypatch.setattr(
        web, "fetch", lambda *_a, **_kw: pytest.fail("Cached logo downloaded")
    )
    radio.NetMonRadioApp.refresh_radio_station_logo(app, {"id": "station"})
    assert app.rendered == [(str(cache), "station|https://icons.example.com/")]


def test_radio_refresh_bounds_background_workers(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    app._station_logo_url = lambda _s: "https://icons.example.com/"
    app._station_logo_cache_path = lambda _url: str(tmp_path / "absent.png")
    app._download_station_logo = lambda *_a: None
    jobs = []

    class Thread:
        def __init__(self, target, **_kwargs):
            self.target = target

        def start(self):
            jobs.append(self.target)

    monkeypatch.setattr(radio, "_LOGO_WORKERS", threading.BoundedSemaphore(2))
    monkeypatch.setattr(radio.threading, "Thread", Thread)
    for _ in range(100):
        radio.NetMonRadioApp.refresh_radio_station_logo(app, {"id": "station"})
    assert len(jobs) == 2
    for job in jobs:
        job()
    assert radio._LOGO_WORKERS.acquire(blocking=False)
    assert radio._LOGO_WORKERS.acquire(blocking=False)


def test_stale_network_failure_does_not_replace_current_logo(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    monkeypatch.setattr(
        web, "fetch", lambda *_a, **_kw: (_ for _ in ()).throw(OSError("offline"))
    )
    radio.NetMonRadioApp._download_station_logo(
        app, "https://icons.example.com/", str(tmp_path / "cache.png"), "old-request"
    )
    assert not app.placeholders


@pytest.mark.parametrize(
    "payload",
    [
        b"GIF89a" + struct.pack("<2H", 65535, 65535),
        b"\xff\xd8\xff\xc0\x00\x08\x08\xff\xff\xff\xff\x01",
        b"RIFF"
        + (22).to_bytes(4, "little")
        + b"WEBPVP8X"
        + (10).to_bytes(4, "little")
        + b"\x00" * 4
        + b"\xff" * 6,
    ],
)
def test_native_raster_decoder_not_called_for_excessive_headers(monkeypatch, payload):
    monkeypatch.setattr(
        Image, "open", lambda *_a: pytest.fail("Oversized header reached decoder")
    )
    with pytest.raises(ValueError, match="dimensions"):
        icons.sanitize_icon(payload)


def test_png_does_not_require_optional_pillow(monkeypatch):
    import sys

    payload = png()
    monkeypatch.setitem(sys.modules, "PIL", None)
    assert icons.sanitize_icon(payload) == (".png", payload)


def test_radio_cached_png_works_without_pillow(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    cache.write_bytes(png())
    monkeypatch.setattr(radio, "Image", None)
    monkeypatch.setattr(radio, "ImageTk", None)
    photos = []
    monkeypatch.setattr(
        radio.tk, "PhotoImage", lambda **kw: photos.append(kw) or "photo"
    )
    app._fit_tk_photoimage = lambda image, **_kw: image
    app._radio_logo_size = lambda _variant: (16, 16)
    radio.NetMonRadioApp._render_station_logo_file(app, str(cache), "station")
    assert app._radio_logo_loaded_key == "station" and not app.placeholders
    assert list(photos[0]) == ["data"]


def test_partial_cache_write_rolls_back(tmp_path, monkeypatch):
    app = radio_stub(tmp_path)
    cache = tmp_path / "cache.png"
    cache.write_bytes(png())
    monkeypatch.setattr(
        web, "fetch", lambda url, **_kw: web.Download(png(), "image/png", url)
    )
    original = radio.tempfile.NamedTemporaryFile

    class PartialFile:
        def __init__(self, **kwargs):
            self.handle = original(**kwargs)
            self.name = self.handle.name

        def __enter__(self):
            return self

        def write(self, payload):
            self.handle.write(payload[:5])
            return 5

        def __exit__(self, *_args):
            self.handle.close()

    monkeypatch.setattr(radio.tempfile, "NamedTemporaryFile", PartialFile)
    radio.NetMonRadioApp._download_station_logo(
        app, "https://icons.example.com/", str(cache), "station"
    )
    assert cache.read_bytes() == png() and list(tmp_path.iterdir()) == [cache]
    assert app.placeholders
