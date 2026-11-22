"""Logo codecs, raw pixel schema and restricted process lifetime."""

import io
import struct
import time
from types import SimpleNamespace

from PIL import Image
import pytest

from netmon.core import radio_logo as logo
from netmon.core import radio_sandbox as sandbox
from netmon import netmon_radio_app as ui


def picture(kind="PNG", size=(240, 120)):
    output = io.BytesIO()
    Image.new("RGB", size, "red").save(output, format=kind)
    return output.getvalue()


def pixels():
    return logo.MAGIC + b"".join(
        struct.pack(">HH", 1, 1) + b"\xff\0\0\xff" for _ in logo.SIZES
    )


@pytest.mark.parametrize("kind", ["PNG", "JPEG", "GIF", "WEBP", "ICO"])
def test_static_codecs_return_bounded_raw_rgba(kind):
    result = logo.validate_pixels(logo.decode_image(picture(kind)))
    for limit, (width, height, data) in zip(logo.SIZES, result):
        assert 0 < width <= limit and 0 < height <= limit
        assert len(data) == width * height * 4
        assert width >= height


@pytest.mark.parametrize(
    "value",
    [
        b"",
        b"PNG?",
        pixels()[:-1],
        pixels() + b"extra",
        logo.MAGIC + struct.pack(">HH", 0, 1),
        logo.MAGIC + struct.pack(">HH", 2048, 2048),
        b"X" * (logo.MAX_REPLY_BYTES + 1),
    ],
)
def test_raw_schema_rejects_malformed_truncated_or_excessive_frames(value):
    with pytest.raises(ValueError):
        logo.validate_pixels(value)


@pytest.mark.parametrize(
    "raw",
    [
        b"not an image",
        b"<svg width='1' height='1'><script/></svg>",
        b"GIF89a" + struct.pack("<HH", 65535, 65535),
        b"X" * (logo.INPUT_BYTES + 1),
    ],
)
def test_image_policy_still_rejects_unsupported_or_excessive_data(raw):
    with pytest.raises(ValueError):
        logo.decode_image(raw)


@pytest.mark.parametrize("kind", ["GIF", "WEBP"])
def test_animation_is_rejected(kind):
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        output,
        format=kind,
        save_all=True,
        append_images=[Image.new("RGB", (2, 2), "blue")],
    )
    with pytest.raises(ValueError):
        logo.decode_image(output.getvalue())


def test_raw_validation_never_calls_a_codec(monkeypatch):
    monkeypatch.setattr(
        Image, "open", lambda *_a, **_k: pytest.fail("encoded image decoder")
    )
    assert logo.validate_pixels(pixels())[0] == (1, 1, b"\xff\0\0\xff")


def controlled_children(monkeypatch, tmp_path, *, decoder, source=None):
    children = []
    real = sandbox.subprocess.Popen
    monkeypatch.setattr(sandbox, "_logo_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))

    def command(directory, _stdlib, _runtime, *, fetch):
        if fetch:
            assert (directory / "request.json").stat().st_mode & 0o777 == 0o600
        return [
            str(sandbox.PYTHON),
            "-I",
            "-S",
            "-B",
            "-c",
            source if fetch else decoder,
        ]

    def spawn(args, **kwargs):
        assert kwargs["close_fds"] and "private-token" not in " ".join(args)
        child = real(args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(sandbox, "_logo_command", command)
    monkeypatch.setattr(sandbox.subprocess, "Popen", spawn)
    return children


def test_parent_passes_exact_bounded_bytes_without_codec(monkeypatch, tmp_path):
    expected = pixels()
    children = controlled_children(
        monkeypatch,
        tmp_path,
        decoder=f"import sys;assert sys.stdin.buffer.read()==b'encoded';sys.stdout.buffer.write({expected!r})",
    )
    monkeypatch.setattr(Image, "open", lambda *_a, **_k: pytest.fail("parent codec"))
    assert sandbox.decode_logo(b"encoded", work_root=tmp_path) == expected
    assert all(c.poll() == 0 for c in children)
    assert not list(tmp_path.glob("logo-*"))


@pytest.mark.parametrize(
    "failure", ["bad", "oversize", "hang", "source-exit", "decoder-exit"]
)
def test_pipeline_failure_reaps_both_children_and_cleans_request(
    monkeypatch, tmp_path, failure
):
    expected = pixels()
    source = "import sys;sys.stdout.buffer.write(b'encoded')"
    decoder = (
        f"import sys;sys.stdin.buffer.read();sys.stdout.buffer.write({expected!r})"
    )
    if failure == "bad":
        decoder = "import sys;sys.stdin.buffer.read();print('not raw')"
    elif failure == "oversize":
        decoder = f"import sys;sys.stdin.buffer.read();sys.stdout.buffer.write(b'X'*{logo.MAX_REPLY_BYTES+1})"
    elif failure == "hang":
        source = "import time;time.sleep(10)"
    elif failure == "source-exit":
        source += ";raise SystemExit(2)"
    elif failure == "decoder-exit":
        decoder += ";raise SystemExit(2)"
    children = controlled_children(
        monkeypatch, tmp_path, decoder=decoder, source=source
    )
    began = time.monotonic()
    with pytest.raises((sandbox.RadioSandboxError, ValueError)):
        sandbox.fetch_logo(
            "https://example.com/?private-token", timeout=0.3, work_root=tmp_path
        )
    assert time.monotonic() - began < 3
    assert len(children) == 2 and all(c.poll() is not None for c in children)
    assert not list(tmp_path.glob("logo-*"))


def test_fetcher_and_decoder_have_distinct_grants(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    sandbox._prepare_directory(tmp_path)
    for fetch in (True, False):
        command = sandbox._logo_command(
            tmp_path, sandbox.Path("/usr/lib/python3.12"), (), fetch=fetch
        )
        assert ("--unshare-net" not in command) is fetch
        assert "/run/control" not in command and "/run/audio/pulse" not in command
        assert ("/run/request.json" in command) is fetch
        assert (str(sandbox.PILLOW) in command) is not fetch
        assert "/usr/lib/python3/dist-packages" not in command
        assert "--clearenv" in command and "--cap-drop" in command


def test_legacy_cache_migrates_offline_without_parent_codec(tmp_path, monkeypatch):
    old = tmp_path / "old.png"
    old.write_bytes(picture())
    cache = tmp_path / "new.pixels"
    calls = []
    expected = pixels()

    def decode(raw):
        assert raw == old.read_bytes()
        calls.append("decode")
        return expected

    monkeypatch.setattr(sandbox, "decode_logo", decode)
    monkeypatch.setattr(
        sandbox, "fetch_logo", lambda *_: pytest.fail("legacy cache network")
    )
    monkeypatch.setattr(Image, "open", lambda *_: pytest.fail("parent codec"))
    app = SimpleNamespace(
        radio_logo_cache_dir=str(tmp_path),
        after=lambda _n, cb: cb(),
        _render_station_logo_file=lambda *args: calls.append(args),
    )
    ui.NetMonRadioApp._download_station_logo(
        app, "https://example.com/", str(cache), "current", cached_path=str(old)
    )
    assert cache.read_bytes() == expected and old.exists()
    assert calls == ["decode", (str(cache), "current")]


def test_homepage_discovery_reads_only_bounded_icon_metadata(monkeypatch):
    from netmon.core import icon_http

    calls = []
    html = b"""<script>fetch('https://evil.example/')</script>
    <base href="http://127.0.0.1/">
    <link rel="icon" href="javascript:alert(1)">
    <link rel="icon" href="data:image/png,xxx">
    <link rel="icon" href="http://radio.example/downgrade.png">
    <link rel="icon" type="image/svg+xml" href="/logo.svg">
    <link rel="icon" href="/icon.png?size=96&amp;type=radio">
    <link rel="apple-touch-icon" href="https://cdn.example/icon.jpg">
    <link rel="icon" href="/fourth.png">"""

    def fetch(url, **options):
        calls.append((url, options))
        return icon_http.Download(html, "text/html", "https://radio.example/start")

    monkeypatch.setattr(icon_http, "fetch", fetch)
    assert logo.discover_icons("https://radio.example/") == [
        "https://radio.example/logo.svg",
        "https://radio.example/icon.png?size=96&type=radio",
        "https://radio.example/favicon.ico",
    ]
    assert len(calls) == 1  # No scripts, base URLs, manifests or images fetched here.
    assert calls[0][1]["limit"] == 128 * 1024
    assert calls[0][1]["budget"].max_requests == 4


def test_fallback_keeps_a_successful_direct_icon_and_uses_no_homepage(monkeypatch):
    monkeypatch.setattr(sandbox, "_run_logo", lambda **kw: pixels())
    monkeypatch.setattr(
        sandbox,
        "_discover_logo_urls",
        lambda *a, **kw: pytest.fail("unnecessary homepage"),
    )
    assert (
        sandbox.fetch_logo(
            "https://radio.example/logo", homepage="https://radio.example/"
        )
        == pixels()
    )


def test_broken_or_missing_icon_uses_protected_homepage_candidates(monkeypatch):
    calls = []

    def run(**kw):
        calls.append(kw["url"])
        if kw["url"].endswith(".png"):
            return pixels()
        raise sandbox.LogoError("http")

    monkeypatch.setattr(sandbox, "_run_logo", run)
    monkeypatch.setattr(
        sandbox,
        "_discover_logo_urls",
        lambda *a, **kw: [
            "https://radio.example/old.ico",
            "https://radio.example/good.png",
        ],
    )
    for direct in ("https://radio.example/dead.ico", ""):
        calls.clear()
        assert sandbox.fetch_logo(direct, homepage="https://radio.example/") == pixels()
        assert calls[-1] == "https://radio.example/good.png"
        assert len(calls) == (3 if direct else 2)


def test_fallback_stops_when_the_shared_deadline_is_exhausted(monkeypatch):
    clock = [100.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])

    def timeout(**kw):
        # Even an overrun during preparation must not start later work.
        clock[0] += 2
        raise sandbox.LogoError("timeout")

    monkeypatch.setattr(sandbox, "_run_logo", timeout)
    monkeypatch.setattr(
        sandbox,
        "_discover_logo_urls",
        lambda *a, **kw: pytest.fail("deadline exhausted"),
    )
    with pytest.raises(sandbox.LogoError) as error:
        sandbox.fetch_logo(
            "https://radio.example/a", homepage="https://radio.example/", timeout=2
        )
    assert error.value.code == "timeout"


def test_homepage_has_reserved_budget_after_a_hanging_direct_icon(monkeypatch):
    clock, calls = [100.0], []
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])

    def run(**options):
        calls.append((options["url"], options["timeout"]))
        if options["url"].endswith("good.png"):
            return pixels()
        clock[0] += options["timeout"]
        raise sandbox.LogoError("timeout")

    def discover(homepage, **options):
        assert homepage == "https://radio.example/"
        assert 0 < options["timeout"] < 8 - (clock[0] - 100)
        clock[0] += options["timeout"]
        return ["https://radio.example/good.png"]

    monkeypatch.setattr(sandbox, "_run_logo", run)
    monkeypatch.setattr(sandbox, "_discover_logo_urls", discover)
    assert (
        sandbox.fetch_logo(
            "https://radio.example/hangs.ico", homepage="https://radio.example/"
        )
        == pixels()
    )
    assert len(calls) == 2
    assert 0 < calls[0][1] <= 3
    assert calls[-1][1] > 0
    assert clock[0] <= 108


def test_slow_candidates_cannot_starve_later_homepage_icons(monkeypatch):
    clock, calls = [100.0], []
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])

    def discover(_homepage, **options):
        clock[0] += options["timeout"]
        return [
            "https://radio.example/hangs.ico",
            "https://radio.example/hangs.png",
            "https://radio.example/good.png",
        ]

    def run(**options):
        calls.append(options["url"])
        if options["url"].endswith("good.png"):
            return pixels()
        clock[0] += options["timeout"]
        raise sandbox.LogoError("timeout")

    monkeypatch.setattr(sandbox, "_run_logo", run)
    monkeypatch.setattr(sandbox, "_discover_logo_urls", discover)
    assert sandbox.fetch_logo("", homepage="https://radio.example/") == pixels()
    assert len(calls) == 3 and calls[-1].endswith("good.png")
    assert clock[0] < 108


@pytest.mark.parametrize("phase", ["decode", "discover"])
def test_logo_preparation_counts_toward_the_phase_deadline(
    monkeypatch, tmp_path, phase
):
    clock = [100.0]
    monkeypatch.setattr(sandbox.time, "monotonic", lambda: clock[0])

    def prepare():
        clock[0] += 2
        return tmp_path, ()

    monkeypatch.setattr(
        sandbox, "_logo_runtime" if phase == "decode" else "_fetch_runtime", prepare
    )
    monkeypatch.setattr(
        sandbox.subprocess,
        "Popen",
        lambda *a, **kw: pytest.fail("Expired phase started a child"),
    )
    with pytest.raises(sandbox.LogoError) as error:
        if phase == "decode":
            sandbox.decode_logo(b"encoded", timeout=1, work_root=tmp_path)
        else:
            sandbox._discover_logo_urls(
                "https://radio.example/", timeout=1, work_root=tmp_path
            )
    assert error.value.code == "timeout"


@pytest.mark.parametrize("kind", ["JPEG", "WEBP"])
def test_detailed_static_image_is_resized_before_normalized_png_budget(kind):
    import random
    from netmon.core import icon_payload

    image = Image.frombytes(
        "RGB", (1024, 768), random.Random(42).randbytes(1024 * 768 * 3)
    )
    stream = io.BytesIO()
    image.save(stream, format=kind, quality=55)
    raw = stream.getvalue()
    assert len(raw) < logo.INPUT_BYTES
    # The generic icon path retains its original strict conversion limit.
    with pytest.raises(ValueError, match="Converted icon exceeds byte budget"):
        icon_payload.sanitize_icon(raw, allow_svg=False)
    decoded = logo.validate_pixels(logo.decode_image(raw))
    for bound, (width, height, data) in zip(logo.SIZES, decoded):
        assert 0 < width <= bound and 0 < height <= bound
        assert width > height
        assert len(data) == width * height * 4


def test_hanging_direct_capsule_is_reaped_before_successful_fallback(
    monkeypatch, tmp_path
):
    import json

    expected = pixels()
    children = controlled_children(
        monkeypatch,
        tmp_path,
        decoder=f"import sys;sys.stdin.buffer.read();sys.stdout.buffer.write({expected!r})",
        source="import sys;sys.stdout.buffer.write(b'encoded')",
    )
    original_command = sandbox._logo_command

    def command(directory, stdlib, runtime, *, fetch):
        if fetch and json.loads((directory / "request.json").read_text())[
            "url"
        ].endswith("/hang"):
            return [str(sandbox.PYTHON), "-I", "-B", "-c", "import time;time.sleep(10)"]
        return original_command(directory, stdlib, runtime, fetch=fetch)

    def discover(*_args, **_options):
        assert len(children) == 2 and all(
            child.poll() is not None for child in children
        )
        return ["https://radio.example/good.png"]

    monkeypatch.setattr(sandbox, "_logo_command", command)
    monkeypatch.setattr(sandbox, "_discover_logo_urls", discover)
    started = time.monotonic()
    assert (
        sandbox.fetch_logo(
            "https://radio.example/hang",
            homepage="https://radio.example/",
            timeout=2,
            work_root=tmp_path,
        )
        == expected
    )
    assert time.monotonic() - started < 2.5
    assert len(children) == 4 and all(child.poll() is not None for child in children)
    assert not list(tmp_path.glob("logo-*"))


@pytest.mark.parametrize(
    "raw",
    [
        b"GIF89a" + struct.pack("<HH", 65535, 65535),
        b"\xff\xd8\xff\xc0\x00\x08\x08\xff\xff\xff\xff\x01",
        b"RIFF"
        + (22).to_bytes(4, "little")
        + b"WEBPVP8X"
        + (10).to_bytes(4, "little")
        + b"\x00" * 4
        + b"\xff" * 6,
    ],
)
def test_radio_resize_rejects_excessive_dimensions_before_any_codec(monkeypatch, raw):
    monkeypatch.setattr(
        Image,
        "open",
        lambda *a, **kw: pytest.fail("Excessive dimensions reached a codec"),
    )
    with pytest.raises(ValueError, match="dimensions"):
        logo.decode_image(raw)


@pytest.mark.parametrize("code", sorted(logo.ERROR_CODES))
def test_worker_error_categories_survive_without_remote_error_text(code):
    with pytest.raises(sandbox.LogoError) as error:
        sandbox._check_logo_error(logo.ERROR_MAGIC + code.encode())
    assert error.value.code == code
    assert "https:" not in str(error.value)
    assert "secret" not in str(sandbox.LogoError("https://example.com/?secret=123"))


def test_discovery_has_only_the_existing_network_grant(tmp_path, monkeypatch):
    monkeypatch.setattr(sandbox, "_network_files", lambda: ())
    sandbox._prepare_directory(tmp_path)
    command = sandbox._logo_command(
        tmp_path, sandbox.Path("/usr/lib/python3.12"), (), fetch=True, discover=True
    )
    assert "--discover" in command
    assert "--unshare-net" not in command
    assert str(sandbox.PILLOW) not in command
    assert "/run/audio/pulse" not in command and "/run/control" not in command
    assert "--clearenv" in command and "--cap-drop" in command


def test_source_failure_category_is_forwarded_by_the_offline_decoder(
    monkeypatch, tmp_path
):
    from pathlib import Path

    root = str(Path(__file__).resolve().parents[1])
    decoder = f"import sys;sys.path.insert(0,{root!r});sys.argv=['logo','--decode'];from netmon.core import radio_logo;raise SystemExit(radio_logo.main())"
    children = controlled_children(
        monkeypatch,
        tmp_path,
        decoder=decoder,
        source=f"import sys;sys.stdout.buffer.write({logo.ERROR_MAGIC + b'blocked_url'!r});raise SystemExit(2)",
    )
    with pytest.raises(sandbox.LogoError) as error:
        sandbox.fetch_logo("https://radio.example/", work_root=tmp_path)
    assert error.value.code == "blocked_url"
    assert all(child.poll() is not None for child in children)


@pytest.mark.parametrize(
    "reply",
    [
        b"{}",
        b"[null]",
        b'["file:///etc/passwd"]',
        b'["https://a.example/","https://b.example/","https://c.example/","https://d.example/"]',
        b"not-json",
    ],
)
def test_discovery_reply_is_bounded_and_revalidated(monkeypatch, tmp_path, reply):
    monkeypatch.setattr(sandbox, "_fetch_runtime", lambda: (tmp_path, ()))
    monkeypatch.setattr(
        sandbox,
        "_logo_command",
        lambda *a, **kw: [
            str(sandbox.PYTHON),
            "-I",
            "-B",
            "-c",
            f"import sys;sys.stdout.buffer.write({reply!r})",
        ],
    )
    with pytest.raises(sandbox.LogoError) as error:
        sandbox._discover_logo_urls(
            "https://radio.example/", timeout=2, work_root=tmp_path
        )
    assert error.value.code == "invalid_reply"
    assert not list(tmp_path.glob("logo-page-*"))
