"""PLS is local station data: bounded numbered entries, shared archive and no IO."""

import pytest

from netmon.core import radio_station_import as source
from netmon.features import radio_station_import_controller as controller
from netmon.features import radio_controller as radio
from tests.test_radio_xspf_import import importer as importer


def pls(
    entries="File1=https://example.com/live\nTitle1=Test Radio\nLength1=-1", count=1
):
    return f"[playlist]\n{entries}\nNumberOfEntries={count}\nVersion=2\n".encode()


def test_standard_pls_becomes_named_custom_station():
    rows, summary = source.parse_pls(pls())
    assert rows == [
        {
            "name": "Test Radio",
            "url": "https://example.com/live",
            "category": "PLS-Import",
            "custom": True,
        }
    ]
    assert summary == {"tracks": 1, "skipped": 0, "duplicates": 0}


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "latin-1"])
@pytest.mark.parametrize("separator", ["\n", "\r\n", "\r"])
def test_names_encodings_whitespace_and_case_are_supported(encoding, separator):
    payload = separator.join(
        [
            "; radio export",
            " [PLAYLIST] ",
            "TITLE1 = Ä Radio",
            "fIlE1 = http://example.com:9012",
            "length1=-1",
            "numberofentries=1",
            "version=2",
        ]
    ).encode(encoding)
    rows, _ = source.parse_pls(payload)
    assert rows[0]["name"] == "Ä Radio" and rows[0]["url"] == "http://example.com:9012"


def test_file_numbers_are_ordered_and_missing_titles_fall_back_to_host():
    rows, _ = source.parse_pls(
        pls(
            "File2=https://second.example/live\nTitle2=Second\nTitle1=First\nFile1=https://first.example/live",
            2,
        )
    )
    assert [row["name"] for row in rows] == ["First", "Second"]
    assert (
        source.parse_pls(b"[playlist]\nFile1=https://example.com/live")[0][0]["name"]
        == "example.com"
    )


def test_equals_percent_and_player_directives_remain_literal_data():
    rows, _ = source.parse_pls(
        pls(
            "File1=https://example.com/live?one=a=b&two=%20\nTitle1=100% Radio; %(key)s ${HOME}\nX-VLC-OPTION=--script=file:///etc/passwd"
        )
    )
    assert rows[0]["url"] == "https://example.com/live?one=a=b&two=%20"
    assert rows[0]["name"] == "100% Radio; %(key)s ${HOME}"
    assert len(rows[0]) == 4


@pytest.mark.parametrize("version", ["1", "2"])
def test_declared_legacy_or_current_version(version):
    rows, _ = source.parse_pls(
        f"[playlist]\nFile1=https://example.com/live\nVersion={version}".encode()
    )
    assert len(rows) == 1


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "../song.mp3",
        "--script=/tmp/payload.lua",
        "rtsp://example.com/live",
        "https://u:p@example.com/live",
        "https://example.com/list.pls",
        "https://example.com/list.xspf",
        "https://example.com/live.m3u8",
        "https://example.com:65536/live",
    ],
)
def test_unsupported_locations_are_counted_not_opened(url):
    rows, counts = source.parse_pls(
        pls(f"File1={url}\nFile2=https://example.com/good\nTitle2=Good", 2)
    )
    assert len(rows) == 1 and rows[0]["name"] == "Good"
    assert counts == {"tracks": 2, "duplicates": 0, "skipped": 1}


@pytest.mark.parametrize(
    "text",
    [
        "",
        "File1=https://example.com/live",
        "[not-playlist]\nFile1=https://example.com/live",
        "[playlist]\n[other]\nFile1=https://example.com/live",
        "[playlist]\n[playlist]\nFile1=https://example.com/live",
        "[playlist]\nFile1=https://example.com/live\nFILE1=https://example.org/other",
        "[playlist]\nFile0=https://example.com/live",
        "[playlist]\nFile01=https://example.com/live",
        "[playlist]\nFile1001=https://example.com/live",
        "[playlist]\nFile1=https://example.com/live\nNumberOfEntries=2",
        "[playlist]\nFile1=https://example.com/live\nNumberOfEntries=-1",
        "[playlist]\nFile1=https://example.com/live\nNumberOfEntries=1001",
        "[playlist]\nFile1=https://example.com/live\nNumberOfEntries=abc",
        "[playlist]\nFile1=https://example.com/live\nVersion=999",
        "[playlist]\nFile1=https://example.com/live\nLength1=abc",
        "[playlist]\nFile1=https://example.com/live\nLength1=-2",
        "[playlist]\nFile1=https://example.com/live\nLength1=2147483648",
        "[playlist]\nFile1=https://example.com/live\n=empty",
        "[playlist]\nFile1=https://example.com/live\ninvalid continuation",
        "[playlist]\nFile1=https://example.com/live\x00",
        "[playlist]\nTitle1=Only a name",
    ],
)
def test_malformed_lists_reject_whole_input(text):
    with pytest.raises(ValueError):
        source.parse_pls(text.encode())


@pytest.mark.parametrize(
    "limit,value,payload",
    [
        ("MAX_BYTES", 8, pls()),
        ("MAX_FIELD_CHARS", 16, pls()),
        ("MAX_PLS_FIELDS", 1, pls()),
        (
            "MAX_TRACKS",
            1,
            pls("File1=https://example.com/a\nFile2=https://example.com/b", 2),
        ),
    ],
)
def test_limits_fail_before_any_import(monkeypatch, limit, value, payload):
    monkeypatch.setattr(source, limit, value)
    with pytest.raises(ValueError):
        source.parse_pls(payload)


def test_invalid_utf8_with_bom_is_not_silently_redecoded():
    with pytest.raises(ValueError, match="UTF-8"):
        source.parse_pls(
            b"\xef\xbb\xbf[playlist]\nTitle1=\xff\nFile1=https://example.com/live"
        )


@pytest.mark.parametrize("suffix", [".pls", ".PLS"])
def test_file_dispatch_archive_bytes_and_original_remain_intact(tmp_path, suffix):
    path = tmp_path / ("radio" + suffix)
    payload = pls()
    path.write_bytes(payload)
    content, rows, _ = source.read_station_file(path)
    archived = source.archive_station_file(content, path, tmp_path / "Senderimporte")
    assert rows[0]["name"] == "Test Radio" and archived.suffix == ".pls"
    assert archived.read_bytes() == path.read_bytes() == payload
    assert (
        source.archive_station_file(content, path, tmp_path / "Senderimporte")
        == archived
    )


def test_duplicates_within_pls_and_across_xspf_m3u_share_same_flow(importer):
    app, xspf, folder = importer
    assert controller.import_station_file_path(app, xspf)
    path = xspf.with_suffix(".pls")
    path.write_bytes(
        pls(
            "File1=http://STREAMS.example.com:9012/\nTitle1=Existing XSPF\nFile2=https://example.org/live\nTitle2=New\nFile3=https://EXAMPLE.org:443/live",
            3,
        )
    )
    assert controller.import_station_file_path(app, path)
    assert (
        len(app.radio_db) == 2
        and "2 doppelt" in radio.set_radio_status.call_args.args[1]
    )
    m3u = xspf.with_suffix(".m3u")
    m3u.write_text("https://example.org/live\nhttps://third.example/live")
    assert controller.import_station_file_path(app, m3u)
    assert (
        len(app.radio_db) == 3
        and "1 doppelt" in radio.set_radio_status.call_args.args[1]
    )
    assert {p.suffix for p in folder.iterdir()} == {".xspf", ".pls", ".m3u"}
    assert radio.load_radio_db(app) == app.radio_db
    radio.play_radio_station.assert_not_called()
    controller.subprocess.Popen.assert_not_called()


def test_cancelling_pls_preview_has_no_effect_on_sender_data_or_original(importer):
    app, xspf, folder = importer
    path = xspf.with_suffix(".pls")
    payload = pls()
    path.write_bytes(payload)
    controller.messagebox.askyesno.return_value = False
    assert not controller.import_station_file_path(app, path)
    assert app.radio_db == [] and not folder.exists() and path.read_bytes() == payload


def test_count_error_does_not_save_partial_sender_list_or_archive(importer):
    app, xspf, folder = importer
    path = xspf.with_suffix(".pls")
    path.write_bytes(pls(count=2))
    assert not controller.import_station_file_path(app, path)
    assert app.radio_db == [] and not folder.exists()
    controller.messagebox.askyesno.assert_not_called()
    assert "Senderanzahl" in radio.set_radio_status.call_args.args[1]
