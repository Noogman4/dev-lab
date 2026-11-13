"""M3U station catalogs use the existing bounded import and playback boundary."""

import json

import pytest

from netmon.core import radio_catalog as catalog
from netmon.features import radio_controller as radio


def rows(text, kind="m3u"):
    return catalog.validate_rows(
        json.loads(catalog.encode_catalog(text.encode("utf-8"), kind))["rows"]
    )


def test_72fm_metadata_becomes_station_rows_without_provider_web_navigation():
    result = rows(
        '\ufeff#EXTM3U\n# 72FM: https://72fm.com/station/id?source=m3u\n#EXTINF:-1 tvg-logo="https://example.com/logo,a.png" group-title="Germany" radio="true",Ä Radio, live\nhttps://example.com:8000/live.mp3\n'
    )
    assert result == [
        {
            "name": "Ä Radio, live",
            "url": "https://example.com:8000/live.mp3",
            "country": "Germany",
            "favicon": "https://example.com/logo,a.png",
        }
    ]
    assert "homepage" not in result[0]
    assert radio._filter_radio_db_rows(result)[0]["name"] == "Ä Radio, live"


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/list.m3u",
        "https://example.com/live.m3u8",
        "https://example.com/live.%6d3u8",
        "https://example.com/list.pls",
        "https://example.com/list.mpd",
        "file:///etc/passwd",
        "--script=/tmp/payload.lua",
        "rtsp://example.com/live",
        "https://u:p@example.com/live",
        "https://example.com:65536/live",
        "https://example.com:0/live",
        "https://example.com/a b",
        "https://example.com/live#fragment",
        "https://attacker.example\\@example.com/live",
    ],
)
def test_unsupported_entries_are_not_passed_to_player_or_catalog(url):
    assert rows(
        "#EXTM3U\n#EXTINF:-1,Unsupported\n"
        + url
        + "\n#EXTINF:-1,Direct\nhttps://example.com/audio.mp3\n"
    ) == [
        {
            "name": "Direct",
            "url": "https://example.com/audio.mp3",
            "country": "",
            "favicon": "",
        }
    ]


@pytest.mark.parametrize(
    "text",
    [
        "https://example.com/live",
        "#EXTM3U\nhttps://example.com/live",
        '#EXTM3U\n#EXTINF:-1 tvg-logo="unterminated,Name\nhttps://example.com/live',
        "#EXTM3U\n#EXTINF:-1,Name",
        "#EXTM3U\n#EXTINF:-1,One\n#EXTINF:-1,Two\nhttps://example.com/live",
        "#EXTM3U\n#EXT-X-TARGETDURATION:8\n#EXTINF:8,segment\nhttps://example.com/segment.ts",
        "#EXTM3U\n#EXTINF:invalid,Name\nhttps://example.com/live",
    ],
)
def test_malformed_or_hls_catalogs_fail_without_partial_reply(text):
    with pytest.raises(ValueError):
        rows(text)


def test_m3u_limits_do_not_silently_truncate(monkeypatch):
    text = "#EXTM3U\n#EXTINF:-1,One\nhttps://example.com/one\n#EXTINF:-1,Two\nhttps://example.com/two\n"
    monkeypatch.setattr(catalog, "MAX_M3U_ROWS", 1)
    with pytest.raises(ValueError, match="count exceeds"):
        rows(text)
    monkeypatch.setattr(catalog, "MAX_M3U_BYTES", 8)
    with pytest.raises(ValueError, match="body exceeds"):
        rows(text)


def test_m3u_line_limit_applies_to_comments_too(monkeypatch):
    monkeypatch.setattr(catalog, "MAX_M3U_LINE_CHARS", 16)
    with pytest.raises(ValueError, match="line exceeds"):
        rows("#EXTM3U\n#" + "x" * 16)


def test_provider_directives_are_data_and_are_not_executed():
    result = rows(
        "#EXTM3U\n#EXTVLCOPT:input-slave=file:///etc/passwd\n#EXTINF:-1,Radio\nhttps://example.com/live\n"
    )
    assert result[0]["url"] == "https://example.com/live"


def test_same_stream_alias_is_merged_once_without_losing_first_source_metadata():
    first = {
        "name": "Original",
        "url": "https://example.com/redirect",
        "url_resolved": "https://example.com/Live?key=A",
        "tags": ["Jazz"],
    }
    second = {"name": "Other provider name", "url": "https://example.com/Live?key=A"}
    different = {"name": "Different stream", "url": "https://example.com/live?key=A"}
    merged = radio._merge_radio_source_rows([[first], [second, different]])
    assert [station["name"] for station in merged] == ["Original", "Different stream"]
    assert merged[0]["tags"] == ["Jazz"]


def test_iprd_groups_are_genres_and_do_not_invent_a_country():
    result = rows(
        '#EXTM3U\n#EXTINF:-1 tvg-logo="https://example.com/logo.png" group-title="pop;world;schlager",Ä Radio\nhttps://example.com/live.mp3\n',
        "iprd",
    )
    assert result == [
        {
            "name": "Ä Radio",
            "url": "https://example.com/live.mp3",
            "favicon": "https://example.com/logo.png",
            "tags": ["pop", "world", "schlager"],
        }
    ]
    assert "country" not in result[0]


def test_iprd_uses_existing_catalog_limits_without_raising_72fm_limits(monkeypatch):
    text = "#EXTM3U\n#EXTINF:-1,One\nhttps://example.com/one\n#EXTINF:-1,Two\nhttps://example.com/two\n"
    monkeypatch.setattr(catalog, "MAX_M3U_ROWS", 1)
    monkeypatch.setattr(catalog, "MAX_M3U_BYTES", 8)
    assert len(rows(text, "iprd")) == 2
    with pytest.raises(ValueError):
        rows(text, "m3u")
    monkeypatch.setattr(catalog, "MAX_ROWS", 1)
    with pytest.raises(ValueError, match="count exceeds"):
        rows(text, "iprd")
    monkeypatch.setattr(catalog, "MAX_BODY_BYTES", 8)
    with pytest.raises(ValueError, match="body exceeds"):
        rows(text, "iprd")


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "--script=/tmp/payload.lua",
        "https://example.com/list.m3u8",
        "https://u:p@example.com/live",
    ],
)
def test_iprd_keeps_the_direct_stream_policy(url):
    assert rows("#EXTM3U\n#EXTINF:-1,Unsupported\n" + url + "\n", "iprd") == []


@pytest.mark.parametrize(
    "source_id", ["72fm_top_500", "iprd_all", "verified_radio_streams"]
)
def test_new_catalog_ids_are_stable_and_keep_equal_station_names_distinct(
    monkeypatch, source_id
):
    payload = [
        {"name": "Same name", "url": "https://example.com/one"},
        {"name": "Same name", "url": "https://example.com/two"},
    ]
    monkeypatch.setattr(radio.radio_sandbox, "fetch_catalog", lambda *a, **kw: payload)
    imported = radio._download_radio_source_payload(source_id)
    ids = [station["id"] for station in imported]
    assert len(set(ids)) == 2
    payload[0]["name"] = "New display name"
    assert radio._download_radio_source_payload(source_id)[0]["id"] == ids[0]
