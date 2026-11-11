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
        b"<svg width='1' height='1'/>",
        b"GIF89a" + struct.pack("<HH", 65535, 65535),
        b"X" * (logo.INPUT_BYTES + 1),
    ],
)
def test_image_policy_still_rejects_unsupported_or_excessive_data(raw):
    with pytest.raises(ValueError):
        logo.decode_image(raw)


def test_animation_is_rejected():
    output = io.BytesIO()
    Image.new("RGB", (2, 2), "red").save(
        output,
        format="GIF",
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
