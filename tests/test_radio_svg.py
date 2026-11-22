"""Static SVGs, raw RGBA output and the offline renderer's grant boundary."""

from pathlib import Path
import sysconfig

from PIL import Image
import pytest

from netmon.core import radio_logo as logo, radio_sandbox as sandbox, radio_svg as svg


def document(content, viewport='viewBox="0 0 100 50"'):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" {viewport}>{content}</svg>'.encode()
    )


@pytest.fixture
def native_renderer(monkeypatch):
    directory = Path("/usr/lib") / str(sysconfig.get_config_var("MULTIARCH") or "")
    if not all((directory / name).is_file() for name in svg.LIBRARY_NAMES):
        pytest.skip("System SVG renderer unavailable")
    monkeypatch.setattr(svg, "LIBRARY_DIR", directory)


def test_svg_colors_transparency_and_aspect_ratio_become_raw_pixels(
    native_renderer, monkeypatch
):
    monkeypatch.setattr(
        Image, "open", lambda *a, **kw: pytest.fail("Encoded image codec on SVG path")
    )
    raw = document('<rect width="100" height="50" fill="red" opacity="0.5"/>')
    frames = logo.validate_pixels(logo.decode_image(raw))
    for limit, (width, height, data) in zip(logo.SIZES, frames):
        assert width == limit and abs(height * 2 - width) <= 1
        image = Image.frombytes("RGBA", (width, height), data)
        assert image.getpixel((width // 2, height // 2)) == (255, 0, 0, 128)


@pytest.mark.parametrize(
    "viewport",
    [
        'viewBox="0 0 100 50"',
        'width="100px" height="50px"',
        'width="100%" height="100%" viewBox="0 0 100 50"',
    ],
)
def test_svg_viewports_are_rendered_inside_fixed_icon_bounds(native_renderer, viewport):
    width, height, raw = svg.render_svg(
        document('<rect width="100" height="50" fill="blue"/>', viewport), 170
    )
    assert (width, height) == (170, 85)
    assert len(raw) == width * height * 4
    assert raw[(height // 2 * width + width // 2) * 4 :][:4] == b"\0\0\xff\xff"


def test_svg_gradients_and_local_clipping_render_without_external_resources(
    native_renderer,
):
    raw = document("""<defs>
      <linearGradient id="g"><stop stop-color="red"/><stop offset="1" stop-color="blue"/></linearGradient>
      <clipPath id="c"><rect width="50" height="50"/></clipPath>
      </defs><rect width="100" height="50" fill="url(#g)" clip-path="url(#c)"/>""")
    width, height, data = svg.render_svg(raw, 170)
    image = Image.frombytes("RGBA", (width, height), data)
    assert image.getpixel((10, height // 2))[0] > image.getpixel((10, height // 2))[2]
    assert image.getpixel((width - 10, height // 2))[3] == 0


@pytest.mark.parametrize(
    "raw",
    [
        document("<script/>"),
        document('<animate attributeName="x"/>'),
        document('<set attributeName="fill" to="red"/>'),
        document('<image href="file:///etc/passwd"/>'),
        document('<image href="http://127.0.0.1/a"/>'),
        document('<image href="data:image/png;base64,aA=="/>'),
        document('<path onload="alert(1)"/>'),
        document('<path style="fill:url(http://127.0.0.1/a)"/>'),
        document('<path style="fill:u\\72l(file:/etc/passwd)"/>'),
        document('<style>@import "http://127.0.0.1/a";</style>'),
        document("<foreignObject/>"),
        document('<use id="cycle" href="#cycle"/>'),
        document('<path xml:base="file:///etc/"/>'),
        document("<text>Needs a Pango worker</text>"),
        document("<tspan>Text</tspan>"),
        document("<rect/>", 'width="2049" height="1"'),
        document("<g>" * 34 + "</g>" * 34),
        b'<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg width="1" height="1">&x;</svg>',
        document("<desc>" + "x" * (128 * 1024) + "</desc>"),
    ],
)
def test_disallowed_svg_is_rejected_before_loading_any_native_renderer(
    monkeypatch, raw
):
    monkeypatch.setattr(
        svg.c, "CDLL", lambda *a, **kw: pytest.fail("Unfiltered SVG reached renderer")
    )
    with pytest.raises(ValueError):
        logo.decode_image(raw)


def test_missing_svg_libraries_do_not_affect_existing_png_support(monkeypatch):
    import io

    monkeypatch.setattr(
        svg.c,
        "CDLL",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("missing renderer")),
    )
    with pytest.raises(OSError):
        logo.decode_image(document('<rect width="100" height="50"/>'))
    output = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(output, format="PNG")
    assert logo.validate_pixels(logo.decode_image(output.getvalue()))[0][:2] == (16, 16)


def test_svg_libraries_are_granted_only_to_the_offline_image_capsule(
    monkeypatch, tmp_path
):
    libraries = []
    for name in svg.LIBRARY_NAMES:
        library = tmp_path / name
        library.write_bytes(b"fixture ELF, never executed")
        libraries.append(library)
    monkeypatch.setattr(
        sandbox, "_svg_runtime", lambda: (tuple(libraries), tuple(libraries))
    )
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    sandbox._prepare_directory(tmp_path)
    for fetch in (True, False):
        command = sandbox._logo_command(tmp_path, tmp_path, (), fetch=fetch)
        assert ("--unshare-net" not in command) is fetch
        assert ("/run/netmon/core/radio_svg.py" in command) is not fetch
        for name in svg.LIBRARY_NAMES:
            assert ("/run/svg/" + name in command) is not fetch
        assert "/usr/share/fonts" not in command
        assert "/run/control" not in command and "/run/audio/pulse" not in command
        assert "--cap-drop" in command and "--clearenv" in command


def test_broken_svg_can_still_use_an_alternative_raster_icon(monkeypatch):
    calls = []
    expected = logo.MAGIC + b"".join(
        b"\x00\x01\x00\x01\xff\0\0\xff" for _ in logo.SIZES
    )

    def run(**options):
        calls.append(options["url"])
        if options["url"].endswith(".svg"):
            raise sandbox.LogoError("image_format")
        return expected

    monkeypatch.setattr(sandbox, "_run_logo", run)
    monkeypatch.setattr(
        sandbox,
        "_discover_logo_urls",
        lambda *a, **kw: ["https://radio.example/good.png"],
    )
    assert (
        sandbox.fetch_logo(
            "https://radio.example/text.svg", homepage="https://radio.example/"
        )
        == expected
    )
    assert len(calls) == 2
