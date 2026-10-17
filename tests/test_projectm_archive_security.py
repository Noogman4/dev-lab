"""M-02 regressions: synthetic ZIPs, fake HTTP streams, temporary output only."""

import io
import os
from pathlib import Path
import stat
import struct
from types import SimpleNamespace
import zipfile

import pytest

from netmon import netmon_projectm_sidecar as sidecar
from netmon import netmon_radio_app as radio
from netmon.app import App
from netmon.core import projectm_archive as limits
from netmon.core import projectm_transport
from netmon.core.archive_limits import (
    ByteBudget,
    COPY_CHUNK_BYTES,
    copy_limited,
    copy_response_limited,
)


@pytest.fixture
def app(tmp_path, monkeypatch):
    presets = tmp_path / "Presets"
    old = presets / "Downloaded Packs" / "Pack"
    old.mkdir(parents=True)
    (old / "existing.milk").write_bytes(b"existing preset")
    monkeypatch.setattr(
        sidecar, "_sync_projectm_flatpak_playlist_file", lambda *_: None
    )
    return SimpleNamespace(
        radio_projectm_preset_dir=str(presets),
        netmon_state_dir=str(tmp_path / "state"),
    )


def write_zip(tmp_path, entries, compression=zipfile.ZIP_STORED):
    path = tmp_path / "pack.zip"
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
    return path


def install(app, path):
    return sidecar.install_projectm_preset_archive(app, str(path), pack_name="Pack")


def assert_preserved(app):
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert sorted(path.name for path in root.iterdir()) == ["Pack"]
    assert (root / "Pack" / "existing.milk").read_bytes() == b"existing preset"


class Response(io.BytesIO):
    status = 200

    def __init__(self, data, content_length=None):
        super().__init__(data)
        self.headers = (
            {} if content_length is None else {"Content-Length": content_length}
        )
        self.requests = []

    def read(self, size=-1):
        assert 0 < size <= COPY_CHUNK_BYTES
        self.requests.append(size)
        return super().read(size)

    def read1(self, size=-1):
        return self.read(size)


def fake_transport(monkeypatch, open_response):
    monkeypatch.setattr(
        projectm_transport, "_build_opener", lambda: SimpleNamespace(open=open_response)
    )


@pytest.mark.parametrize("header", [None, "1", "6"])
def test_stream_limit_independent_of_content_length(header):
    response = Response(b"abcdef", header)
    destination = io.BytesIO()
    with pytest.raises(ValueError, match="compressed byte limit"):
        copy_response_limited(response, destination, 5)
    assert len(destination.getvalue()) <= 5
    if header != "6":
        assert response.requests


@pytest.mark.parametrize("header", [None, "1", "6"])
def test_bounded_download_accepts_missing_or_understated_length(header):
    response = Response(b"abcdef", header)
    destination = io.BytesIO()
    assert copy_response_limited(response, destination, 6) == 6
    assert destination.getvalue() == b"abcdef"


@pytest.mark.parametrize("header", ["invalid", "-1", "7"])
def test_invalid_or_excessive_length_fails_before_read(header):
    response = Response(b"abcdef", header)
    with pytest.raises(ValueError):
        copy_response_limited(response, io.BytesIO(), 6)
    assert not response.requests


def test_large_stream_is_read_in_chunks():
    payload = b"x" * (COPY_CHUNK_BYTES * 2 + 13)
    response = Response(payload)
    destination = io.BytesIO()
    copy_response_limited(response, destination, len(payload))
    assert len(response.requests) >= 4
    assert destination.getvalue() == payload


@pytest.mark.parametrize("kind", ["directory", "ignored"])
def test_member_limit_includes_ignored_and_directory_entries(
    app, tmp_path, monkeypatch, kind
):
    entries = [("one.milk", b"preset")]
    entries += [
        (f"d{i}/" if kind == "directory" else f"f{i}.txt", b"") for i in range(3)
    ]
    path = write_zip(tmp_path, entries)
    monkeypatch.setattr(limits, "MAX_MEMBERS", 3)
    with pytest.raises(ValueError, match="too many members"):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize("extension", ["milk", "txt"])
def test_file_limit_applies_to_all_extensions(app, tmp_path, monkeypatch, extension):
    path = write_zip(tmp_path, [("one.milk", b"ok"), (f"large.{extension}", b"x" * 9)])
    monkeypatch.setattr(limits, "MAX_FILE_BYTES", 8)
    with pytest.raises(ValueError, match="size or compression"):
        install(app, path)
    assert_preserved(app)


def test_total_declared_size_includes_ignored_files(app, tmp_path, monkeypatch):
    path = write_zip(tmp_path, [("one.milk", b"123"), ("ignored.txt", b"456")])
    monkeypatch.setattr(limits, "MAX_TOTAL_BYTES", 5)
    with pytest.raises(ValueError, match="total uncompressed"):
        install(app, path)
    assert_preserved(app)


def test_zip_bomb_ratio_rejected(app, tmp_path):
    path = write_zip(tmp_path, [("bomb.milk", b"0" * 200_000)], zipfile.ZIP_DEFLATED)
    with pytest.raises(ValueError, match="compression ratio"):
        install(app, path)
    assert_preserved(app)


def mutate_central_size(path, *, compressed=None, uncompressed=None, count=None):
    payload = bytearray(path.read_bytes())
    central = payload.index(b"PK\x01\x02")
    if compressed is not None:
        struct.pack_into("<L", payload, central + 20, compressed)
    if uncompressed is not None:
        struct.pack_into("<L", payload, central + 24, uncompressed)
    if count is not None:
        end = payload.rindex(b"PK\x05\x06")
        struct.pack_into("<HH", payload, end + 8, count, count)
    path.write_bytes(payload)


@pytest.mark.parametrize("sizes", [(0, 10), (1, 1000), (10000, 10), (1, 1)])
def test_manipulated_sizes_rejected(app, tmp_path, sizes):
    path = write_zip(tmp_path, [("one.milk", b"the original preset")])
    mutate_central_size(path, compressed=sizes[0], uncompressed=sizes[1])
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        install(app, path)
    assert_preserved(app)


def test_forged_member_count_rejected(app, tmp_path):
    path = write_zip(tmp_path, [("one.milk", b"a"), ("two.milk", b"b")])
    mutate_central_size(path, count=1)
    with pytest.raises(ValueError, match="member count"):
        install(app, path)
    assert_preserved(app)


def test_forged_count_cannot_bypass_limit_before_parsing(app, tmp_path, monkeypatch):
    path = write_zip(tmp_path, [("one.milk", b"a"), ("two/", b""), ("three.txt", b"b")])
    mutate_central_size(path, count=1)
    monkeypatch.setattr(limits, "MAX_MEMBERS", 2)
    monkeypatch.setattr(
        sidecar.zipfile,
        "ZipFile",
        lambda *_: pytest.fail("Member limit must precede ZipFile allocation"),
    )
    with pytest.raises(ValueError, match="too many members"):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize("kind", ["empty", "no-presets", "not-zip", "truncated"])
def test_invalid_or_empty_archive_leaves_no_output(app, tmp_path, kind):
    entries = [] if kind == "empty" else [("readme.txt", b"documentation")]
    path = write_zip(tmp_path, entries)
    if kind == "not-zip":
        path.write_bytes(b"not a ZIP")
    elif kind == "truncated":
        path.write_bytes(path.read_bytes()[:-10])
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize(
    "kind", ["zip64", "multi-disk", "truncated-record", "encryption", "method"]
)
def test_unsupported_or_inconsistent_metadata_rejected(app, tmp_path, kind):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    payload = bytearray(path.read_bytes())
    end = payload.rindex(b"PK\x05\x06")
    central = payload.index(b"PK\x01\x02")
    if kind == "zip64":
        struct.pack_into("<HH", payload, end + 8, 65535, 65535)
    elif kind == "multi-disk":
        struct.pack_into("<H", payload, end + 4, 1)
    elif kind == "truncated-record":
        struct.pack_into("<H", payload, central + 28, 65535)
    elif kind == "encryption":
        struct.pack_into("<H", payload, central + 8, 1)
    else:
        struct.pack_into("<H", payload, central + 10, zipfile.ZIP_LZMA)
    path.write_bytes(payload)
    with pytest.raises((ValueError, zipfile.BadZipFile)):
        install(app, path)
    assert_preserved(app)


def test_metadata_budget_checked_before_zipfile_parsing(app, tmp_path, monkeypatch):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    monkeypatch.setattr(limits, "MAX_DIRECTORY_BYTES", 1)
    monkeypatch.setattr(
        sidecar.zipfile,
        "ZipFile",
        lambda *_: pytest.fail("ZipFile must not parse excessive metadata"),
    )
    with pytest.raises(ValueError, match="directory metadata"):
        install(app, path)
    assert_preserved(app)


def test_local_archive_also_has_compressed_limit(app, tmp_path, monkeypatch):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    monkeypatch.setattr(limits, "MAX_DOWNLOAD_BYTES", path.stat().st_size - 1)
    with pytest.raises(ValueError, match="compressed byte limit"):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize("payload", [b"too long", b"short"])
def test_real_extracted_size_checked_and_partial_output_removed(
    app, tmp_path, monkeypatch, payload
):
    path = write_zip(tmp_path, [("one.milk", b"123456")])
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *_: io.BytesIO(payload))
    with pytest.raises(ValueError, match="byte limit|does not match"):
        install(app, path)
    assert_preserved(app)


def test_real_total_budget_is_enforced_independently_of_metadata():
    budget = ByteBudget(5)
    copy_limited(io.BytesIO(b"123"), io.BytesIO(), 3, budget=budget)
    second = io.BytesIO()
    with pytest.raises(ValueError, match="total uncompressed"):
        copy_limited(io.BytesIO(b"456"), second, 3, budget=budget)
    assert second.getvalue() == b""


def test_real_ratio_budget_is_enforced(monkeypatch):
    member = zipfile.ZipInfo("one.milk")
    member.file_size = 20
    member.compress_size = 1
    monkeypatch.setattr(limits, "MAX_COMPRESSION_RATIO", 4)
    archive = SimpleNamespace(open=lambda *_: io.BytesIO(b"12345"))
    with pytest.raises(ValueError, match="byte limit"):
        limits.copy_member(archive, member, io.BytesIO(), ByteBudget(100))


@pytest.mark.parametrize(
    "name",
    [
        "../escape.milk",
        "pack/../../escape.milk",
        "/absolute.milk",
        "C:/drive.milk",
        "\\\\server\\share\\one.milk",
        "pack\\..\\escape.milk",
        "pack/./one.milk",
        "pack//one.milk",
        "../ignored.txt",
    ],
)
def test_unsafe_paths_rejected(app, tmp_path, name):
    path = write_zip(tmp_path, [(name, b"evil"), ("valid.milk", b"ok")])
    with pytest.raises(ValueError, match="Unsafe ZIP"):
        install(app, path)
    assert_preserved(app)
    assert not (tmp_path / "escape.milk").exists()


@pytest.mark.parametrize(
    "file_type", [stat.S_IFLNK, stat.S_IFIFO, stat.S_IFCHR, stat.S_IFSOCK]
)
@pytest.mark.parametrize("name", ["unsafe.milk", "ignored.txt"])
def test_links_and_special_files_rejected_even_when_ignored(
    app, tmp_path, file_type, name
):
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = (file_type | 0o777) << 16
    path = write_zip(tmp_path, [(info, b"target"), ("good.milk", b"ok")])
    with pytest.raises(ValueError, match="link or special"):
        install(app, path)
    assert_preserved(app)


def test_directory_payload_rejected(app, tmp_path):
    path = write_zip(tmp_path, [("directory/", b"not empty"), ("good.milk", b"ok")])
    with pytest.raises(ValueError, match="size or compression"):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize("failure", ["write", "close", "mkdir", "read"])
def test_io_failure_removes_new_pack_and_preserves_existing(
    app, tmp_path, monkeypatch, failure
):
    path = write_zip(tmp_path, [("one.milk", b"preset"), ("sub/two.milk", b"preset")])
    if failure in {"write", "close"}:
        original_open = open

        class FailingFile:
            def __init__(self, *args, **kwargs):
                self.file = original_open(*args, **kwargs)

            def __enter__(self):
                return self

            def write(self, chunk):
                self.file.write(chunk[:1])
                if failure == "write":
                    raise OSError("simulated write failure")
                return len(chunk)

            def __exit__(self, *_):
                self.file.close()
                raise OSError("simulated close failure")

        monkeypatch.setattr(
            sidecar,
            "open",
            lambda *a, **kw: (
                FailingFile(*a, **kw)
                if len(a) > 1 and a[1] == "xb"
                else original_open(*a, **kw)
            ),
            raising=False,
        )
    elif failure == "mkdir":
        original = os.mkdir

        def fail(path, *args, **kwargs):
            if "Pack_2" in str(path):
                raise OSError("simulated mkdir failure")
            return original(path, *args, **kwargs)

        monkeypatch.setattr(sidecar.os, "mkdir", fail)
    else:
        monkeypatch.setattr(
            zipfile.ZipFile,
            "open",
            lambda *_: (_ for _ in ()).throw(OSError("simulated read failure")),
        )
    with pytest.raises(OSError, match="simulated"):
        install(app, path)
    assert_preserved(app)


def test_short_writes_are_completed_and_zero_writes_fail():
    class ShortWriter(io.BytesIO):
        def write(self, data):
            return super().write(data[:2])

    destination = ShortWriter()
    copy_limited(io.BytesIO(b"abcdef"), destination, 6)
    assert destination.getvalue() == b"abcdef"
    with pytest.raises(OSError, match="Incomplete"):
        copy_limited(io.BytesIO(b"abc"), SimpleNamespace(write=lambda _: 0), 3)


def test_existing_pack_symlink_is_not_reused(app, tmp_path):
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    (root / "Pack_2").symlink_to(tmp_path / "missing", target_is_directory=True)
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    result = install(app, path)
    assert Path(result["target_dir"]).name == "Pack_3"
    assert not (tmp_path / "missing").exists()


def test_symlink_pack_root_rejected(app, tmp_path):
    root = Path(app.radio_projectm_preset_dir)
    outside = tmp_path / "outside"
    outside.mkdir()
    # A separate preset root avoids altering the fixture's existing valid pack.
    other = root / "Other"
    other.mkdir()
    (other / "Downloaded Packs").symlink_to(outside, target_is_directory=True)
    other_app = SimpleNamespace(radio_projectm_preset_dir=str(other))
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    with pytest.raises(ValueError, match="symlinks"):
        install(other_app, path)
    assert list(outside.iterdir()) == []
    assert_preserved(app)


def test_symlink_preset_root_rejected_before_creating_pack_root(app, tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "linked-presets"
    link.symlink_to(outside, target_is_directory=True)
    other_app = SimpleNamespace(radio_projectm_preset_dir=str(link))
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    with pytest.raises(ValueError, match="symlinks"):
        install(other_app, path)
    assert list(outside.iterdir()) == []
    assert_preserved(app)


def test_atomic_directory_creation_does_not_reuse_a_racing_existing_pack(
    app, tmp_path, monkeypatch
):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    original = sidecar.os.mkdir

    def race(target, *args, **kwargs):
        if str(target).endswith("/Pack_2"):
            original(target, *args, **kwargs)
            (Path(target) / "concurrent.milk").write_bytes(b"concurrent preset")
            raise FileExistsError("simulated concurrent import")
        return original(target, *args, **kwargs)

    monkeypatch.setattr(sidecar.os, "mkdir", race)
    result = install(app, path)
    assert Path(result["target_dir"]).name == "Pack_3"
    assert (
        Path(result["target_dir"]).parent / "Pack_2/concurrent.milk"
    ).read_bytes() == b"concurrent preset"


def test_valid_archive_preserves_hierarchy_assets_and_existing_pack(app, tmp_path):
    path = write_zip(
        tmp_path,
        [
            ("pack/", b""),
            ("pack/presets/one.MILK", b"preset"),
            ("pack/presets/two.prjm", b"second"),
            ("pack/assets/texture.png", b"image"),
            ("pack/ignored.exe", b"ignored"),
            ("pack/empty.png", b""),
        ],
        zipfile.ZIP_DEFLATED,
    )
    result = install(app, path)
    target = Path(result["target_dir"])
    assert target.name == "Pack_2"
    assert result["imported_presets"] == 2
    assert result["imported_assets"] == 2
    assert result["imported_files"] == 4
    assert (target / "presets/one.MILK").read_bytes() == b"preset"
    assert (target / "assets/texture.png").read_bytes() == b"image"
    assert (target / "empty.png").read_bytes() == b""
    assert not (target / "ignored.exe").exists()
    assert target.stat().st_mode & 0o777 == 0o700
    assert (target.parent / "Pack/existing.milk").read_bytes() == b"existing preset"
    flat = Path(app.radio_projectm_preset_dir) / sidecar.PROJECTM_FLAT_SCAN_SUBDIR
    assert len(list(flat.iterdir())) == 3


def test_success_retains_legacy_migration_without_overwriting_presets(app, tmp_path):
    legacy = Path(app.netmon_state_dir) / "projectm_presets"
    legacy.mkdir(parents=True)
    (legacy / "legacy.milk").write_bytes(b"legacy preset")
    (legacy / "keep.milk").write_bytes(b"old version")
    root = Path(app.radio_projectm_preset_dir)
    (root / "keep.milk").write_bytes(b"current version")
    path = write_zip(tmp_path, [("new.milk", b"new preset")])
    install(app, path)
    assert (root / "legacy.milk").read_bytes() == b"legacy preset"
    assert (root / "keep.milk").read_bytes() == b"current version"


@pytest.mark.parametrize(
    "failure", [None, "download", "limit", "invalid", "import", "write"]
)
def test_ui_download_streams_imports_and_always_removes_tempfile(
    app, tmp_path, monkeypatch, failure
):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    data = path.read_bytes() if failure != "invalid" else b"invalid ZIP"
    response = Response(data, "1")
    monkeypatch.setattr(
        radio.simpledialog,
        "askstring",
        lambda *_a, **_k: "https://example.invalid/Pack.zip",
    )
    monkeypatch.setattr(radio.radio_controller, "save_radio_settings", lambda *_: None)
    monkeypatch.setattr(limits.tempfile, "tempdir", str(tmp_path))
    if failure == "limit":
        monkeypatch.setattr(limits, "MAX_DOWNLOAD_BYTES", 10)
    elif failure == "write":

        def fail_write(_response, handle, _limit, **_kwargs):
            handle.write(b"partial ZIP")
            raise OSError("simulated download write failure")

        monkeypatch.setattr(limits, "copy_response_limited", fail_write)

    def urlopen(*_a, **_k):
        if failure == "download":
            raise OSError("simulated download failure")
        return response

    fake_transport(monkeypatch, urlopen)
    app.tr = lambda _key, default: default
    app.update_idletasks = lambda: None
    app.radio_projectm_preset_hint_var = SimpleNamespace(set=lambda _: None)

    def import_archive(path, **_):
        if failure == "import":
            raise OSError("simulated import failure")
        install(app, path)
        return True

    app._import_projectm_preset_archive_path = import_archive
    assert radio.NetMonRadioApp.download_projectm_preset_pack(app) is (failure is None)
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
    if failure is not None:
        assert_preserved(app)


def zip64_comment_bypass():
    """One declared directory record hides a second directory selected by ZIP64."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("first.milk", b"one")
        archive.writestr("second.milk", b"two")
        last = zipfile.ZipInfo("last.milk")
        last.comment = b"x" * 76
        archive.writestr(last, b"three")
    data = bytearray(buffer.getvalue())
    end = data.rindex(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<LL", data, end + 12)
    last_header = data.rindex(b"PK\x01\x02")
    zip64_offset = end - 76
    data[zip64_offset:end] = struct.pack(
        "<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, 3, 3, cd_size - 76, cd_offset
    ) + struct.pack("<4sLQL", b"PK\x06\x07", 0, zip64_offset, 1)
    struct.pack_into("<HHLL", data, end + 8, 1, 1, end - last_header, last_header)
    return bytes(data)


def test_zip64_comment_bypass_fails_before_parser_allocation(
    app, tmp_path, monkeypatch
):
    data = zip64_comment_bypass()
    # Reproduce the parser disagreement without allocating a large archive.
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert len(archive.infolist()) == 3
        assert sum(46 + len(info.filename) for info in archive.infolist()) == 168
    path = tmp_path / "bypass.zip"
    path.write_bytes(data)
    monkeypatch.setattr(limits, "MAX_MEMBERS", 1)
    monkeypatch.setattr(limits, "MAX_DIRECTORY_BYTES", 131)
    monkeypatch.setattr(
        sidecar.zipfile,
        "ZipFile",
        lambda *_: pytest.fail("ZIP64 must be rejected before ZipFile allocation"),
    )
    with pytest.raises(ValueError, match="ZIP64"):
        install(app, path)
    assert_preserved(app)


@pytest.mark.parametrize("content_length", [None, "1"])
def test_components_installer_enforces_real_download_limit(
    app, tmp_path, monkeypatch, content_length
):
    response = Response(b"123456789", content_length)
    monkeypatch.setattr(limits, "MAX_DOWNLOAD_BYTES", 8)
    monkeypatch.setattr(limits.tempfile, "tempdir", str(tmp_path))
    fake_transport(monkeypatch, lambda *_a, **_k: response)
    app._import_projectm_preset_pack_from_url = lambda url, name: (
        App._import_projectm_preset_pack_from_url(app, url, name)
    )
    with pytest.raises(ValueError, match="compressed byte limit"):
        App._install_selected_file_features(app, ["projectm_presets_cream_crop"])
    assert response.requests
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
    assert_preserved(app)


def run_components_import(app):
    app._import_projectm_preset_pack_from_url = lambda url, name: (
        App._import_projectm_preset_pack_from_url(app, url, name)
    )
    return App._install_selected_file_features(app, ["projectm_presets_cream_crop"])


@pytest.mark.parametrize("content_length", [None, "1", "correct"])
def test_components_installer_handles_short_reads_and_valid_archive(
    app, tmp_path, monkeypatch, content_length
):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    payload = path.read_bytes()

    class ShortResponse(Response):
        def read(self, size=-1):
            assert 0 < size <= COPY_CHUNK_BYTES
            return super().read(min(size, 7))

    header = str(len(payload)) if content_length == "correct" else content_length
    response = ShortResponse(payload, header)
    monkeypatch.setattr(limits.tempfile, "tempdir", str(tmp_path))
    fake_transport(monkeypatch, lambda *_a, **_k: response)
    assert run_components_import(app) == [("projectm_presets_cream_crop", 1)]
    assert len(response.requests) > 10
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
    root = Path(app.radio_projectm_preset_dir) / "Downloaded Packs"
    assert (root / "Cream of the Crop" / "one.milk").read_bytes() == b"preset"
    assert (root / "Pack" / "existing.milk").read_bytes() == b"existing preset"


@pytest.mark.parametrize(
    "failure", ["connect", "read", "truncated", "length", "write", "invalid"]
)
def test_components_download_errors_clean_up_and_preserve_presets(
    app, tmp_path, monkeypatch, failure
):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    payload = path.read_bytes()
    if failure == "truncated":
        payload = payload[:-12]
    elif failure == "invalid":
        payload = b"not a ZIP"

    class BrokenResponse(Response):
        def read(self, size=-1):
            if failure == "read" and self.requests:
                raise OSError("simulated interrupted download")
            return super().read(min(size, 7))

    header = str(len(payload) + 1) if failure == "length" else None
    response = BrokenResponse(payload, header)

    def urlopen(*_a, **_k):
        if failure == "connect":
            raise OSError("simulated connection failure")
        return response

    if failure == "write":

        def fail_write(_response, handle, _limit, **_kwargs):
            handle.write(b"partial")
            raise OSError("simulated write failure")

        monkeypatch.setattr(limits, "copy_response_limited", fail_write)
    monkeypatch.setattr(limits.tempfile, "tempdir", str(tmp_path))
    fake_transport(monkeypatch, urlopen)
    with pytest.raises((ValueError, OSError, zipfile.BadZipFile)):
        run_components_import(app)
    assert not list(tmp_path.glob("netmon-projectm-pack-*"))
    assert_preserved(app)


@pytest.mark.parametrize(
    "comment", [b"", b"archive comment", b"literal PK\x06\x06 / PK\x06\x07"]
)
@pytest.mark.parametrize("corrupt", [False, True])
def test_zip64_locator_without_sentinels_rejected_before_parser(
    tmp_path, monkeypatch, comment, corrupt
):
    data = bytearray(zip64_comment_bypass())
    end = data.rindex(b"PK\x05\x06")
    if corrupt:
        data[end - 76 : end - 72] = b"bad!"
    struct.pack_into("<H", data, end + 20, len(comment))
    data.extend(comment)
    monkeypatch.setattr(
        sidecar.zipfile, "ZipFile", lambda *_: pytest.fail("Parser must not run")
    )
    with pytest.raises(ValueError, match="ZIP64"):
        limits.check_zip_envelope(io.BytesIO(data))


@pytest.mark.parametrize(
    "kind",
    [
        "zip64-end-only",
        "trailing",
        "cd-size",
        "cd-offset",
        "cd-local-overlap",
        "member-sentinel",
        "member-disk",
        "comment-length",
    ],
)
def test_inconsistent_structures_rejected_before_zipfile(
    app, tmp_path, monkeypatch, kind
):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    data = bytearray(path.read_bytes())
    end = data.rindex(b"PK\x05\x06")
    central = data.index(b"PK\x01\x02")
    if kind == "zip64-end-only":
        data[end:end] = struct.pack(
            "<4sQ2H2L4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, 1, 1, end - central, central
        )
    elif kind == "trailing":
        data.extend(b"unexpected trailing bytes")
    elif kind == "cd-size":
        struct.pack_into("<L", data, end + 12, end - central + 1)
    elif kind == "cd-offset":
        struct.pack_into("<L", data, end + 16, central - 1)
    elif kind == "cd-local-overlap":
        struct.pack_into("<L", data, central + 42, central)
    elif kind == "member-sentinel":
        struct.pack_into("<L", data, central + 24, 0xFFFFFFFF)
    elif kind == "member-disk":
        struct.pack_into("<H", data, central + 34, 1)
    else:
        struct.pack_into("<H", data, end + 20, 1)
    path.write_bytes(data)
    monkeypatch.setattr(
        sidecar.zipfile, "ZipFile", lambda *_: pytest.fail("Parser must not run")
    )
    with pytest.raises(ValueError):
        install(app, path)
    assert_preserved(app)


def test_competing_complete_end_records_rejected_before_parser(tmp_path):
    path = write_zip(tmp_path, [("one.milk", b"preset")])
    data = bytearray(path.read_bytes())
    end = data.rindex(b"PK\x05\x06")
    cd_size, cd_offset = struct.unpack_from("<LL", data, end + 12)
    duplicate_directory = bytes(data[cd_offset:end])
    duplicate_end = bytearray(data[end:])
    struct.pack_into("<L", duplicate_end, 16, len(data))
    struct.pack_into("<H", data, end + 20, cd_size + 22)
    data.extend(duplicate_directory + duplicate_end)
    with pytest.raises(ValueError, match="Ambiguous"):
        limits.check_zip_envelope(io.BytesIO(data))


@pytest.mark.parametrize("extra", [struct.pack("<HH", 1, 0), b"\x01\x00\x10\x00short"])
def test_zip64_or_truncated_extra_fields_rejected_before_parser(
    app, tmp_path, monkeypatch, extra
):
    info = zipfile.ZipInfo("one.milk")
    info.extra = extra
    path = write_zip(tmp_path, [(info, b"preset")])
    monkeypatch.setattr(
        sidecar.zipfile, "ZipFile", lambda *_: pytest.fail("Parser must not run")
    )
    with pytest.raises(ValueError, match="ZIP64|Truncated"):
        install(app, path)
    assert_preserved(app)


def test_incidental_signatures_and_non_zip64_extra_remain_valid(app, tmp_path):
    literal = b"PK\x06\x06 and PK\x06\x07"
    info = zipfile.ZipInfo("one.milk")
    info.comment = literal + b" padding" * 4
    info.extra = struct.pack("<HH", 0xCAFE, len(literal)) + literal
    path = write_zip(tmp_path, [(info, b"preset " + literal + b" PK\x05\x06")])
    with zipfile.ZipFile(path, "a") as archive:
        archive.comment = literal + b" archive comment"
    result = install(app, path)
    assert (Path(result["target_dir"]) / "one.milk").read_bytes().startswith(b"preset")


def test_small_zip64_local_header_remains_compatible(app, tmp_path):
    path = tmp_path / "local-header.zip"
    with zipfile.ZipFile(path, "w") as archive:
        with archive.open("one.milk", "w", force_zip64=True) as member:
            member.write(b"preset")
    result = install(app, path)
    assert result["imported_presets"] == 1
