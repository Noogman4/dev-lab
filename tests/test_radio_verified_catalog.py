"""Verified Radio's homepage must never be used as its audio address."""

import json

import pytest

from netmon.core import radio_catalog as catalog
from netmon.features import radio_controller as radio


def payload(stations):
    return {
        "generated": "2026-08-26",
        "stationCount": len(stations),
        "countries": [
            {"country": "Germany", "countryCode": "DE", "stations": stations}
        ],
    }


def rows(data):
    return catalog.validate_rows(
        json.loads(catalog.encode_catalog(json.dumps(data).encode(), "verified"))[
            "rows"
        ]
    )


def test_stream_homepage_and_metadata_are_mapped_to_the_right_fields():
    data = payload(
        [
            {
                "name": "Ä Radio",
                "stream": "https://audio.example.com:8443/live.mp3",
                "url": "https://www.example.com",
                "codec": "mp3",
                "bitrate": 128,
                "genre": ["jazz", "live"],
                "langs": ["German", "English"],
                "votes": 80,
                "clicks": 7,
                "verified": "2026-08-24",
            }
        ]
    )
    [row] = rows(data)
    assert row == {
        "name": "Ä Radio",
        "url": "https://audio.example.com:8443/live.mp3",
        "homepage": "https://www.example.com",
        "country": "Germany",
        "countrycode": "DE",
        "tags": ["jazz", "live"],
        "language": "German, English",
        "codec": "mp3",
        "bitrate": 128,
        "votes": 80,
        "clickcount": 7,
    }
    assert "lastcheckok" not in row
    [station] = radio._filter_radio_db_rows([row])
    assert station["url"] == row["url"]
    assert station["homepage"] == row["homepage"]


@pytest.mark.parametrize(
    "stream",
    [
        None,
        "",
        "http://example.com/live",
        "file:///etc/passwd",
        "--script=/tmp/payload.lua",
        "https://example.com/live.m3u8",
        "https://example.com/list.pls",
        "https://example.com/list.%6d3u",
        "https://user:pass@example.com/live",
        "https://example.com:0/live",
        "https://example.com:65536/live",
        "https://example.com:bad/live",
        "https://example.com/a b",
        "https://example.com/a\x85b",
        "https://example.com/live#part",
        "https://attacker.example\\@example.com/live",
    ],
)
def test_missing_or_unsupported_stream_never_falls_back_to_homepage(stream):
    assert (
        rows(
            payload(
                [
                    {
                        "name": "Do not play homepage",
                        "stream": stream,
                        "url": "https://www.example.com",
                    }
                ]
            )
        )
        == []
    )


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"countries": {}},
        {"countries": [None]},
        {"countries": [{"stations": {}}]},
        {"countries": [{"stations": None}]},
    ],
)
def test_wrong_country_envelopes_fail_closed(data):
    with pytest.raises(ValueError):
        rows(data)


def test_actual_station_count_is_bounded_across_country_groups(monkeypatch):
    data = {
        "stationCount": 0,
        "countries": [
            {"stations": [{"name": "One", "stream": "https://example.com/one"}]},
            {"stations": [{"name": "Two", "stream": "https://example.com/two"}]},
        ],
    }
    monkeypatch.setattr(catalog, "MAX_ROWS", 1)
    with pytest.raises(ValueError, match="count exceeds"):
        rows(data)


def test_country_group_count_is_bounded_even_if_every_group_is_empty():
    with pytest.raises(ValueError, match="country count"):
        rows({"countries": [{"stations": []}] * 513})


def test_verified_catalog_keeps_body_reply_and_field_limits(monkeypatch):
    data = payload([{"name": "Radio", "stream": "https://example.com/live"}])
    monkeypatch.setattr(catalog, "MAX_BODY_BYTES", 8)
    with pytest.raises(ValueError, match="body exceeds"):
        rows(data)
    monkeypatch.setattr(catalog, "MAX_BODY_BYTES", 16 * 1024 * 1024)
    monkeypatch.setattr(catalog, "MAX_REPLY_BYTES", 8)
    with pytest.raises(ValueError, match="reply exceeds"):
        rows(data)
    monkeypatch.setattr(catalog, "MAX_REPLY_BYTES", 16 * 1024 * 1024)
    data["countries"][0]["stations"][0]["genre"] = ["x"] * 65
    with pytest.raises(ValueError, match="Mostly invalid"):
        rows(data)


def test_display_controls_are_cleaned_and_unknown_executable_fields_ignored():
    [row] = rows(
        payload(
            [
                {
                    "name": "Radio\n[ERROR] forged",
                    "stream": "https://example.com/live",
                    "argv": ["--script=/tmp/payload.lua"],
                }
            ]
        )
    )
    assert row["name"] == "Radio [ERROR] forged"
    assert "argv" not in row


def test_nonfinite_json_is_rejected_for_the_verified_envelope():
    raw = json.dumps(
        payload(
            [
                {
                    "name": "Radio",
                    "stream": "https://example.com/live",
                    "bitrate": float("nan"),
                }
            ]
        )
    ).encode()
    with pytest.raises(ValueError, match="Non-finite"):
        catalog.encode_catalog(raw, "verified")
