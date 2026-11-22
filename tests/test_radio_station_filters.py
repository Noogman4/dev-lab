"""Shared genre/bitrate semantics, including mixed catalog representations."""

import pytest

from netmon.core import radio_station_filters as filters


@pytest.mark.parametrize(
    "field,value,category",
    [
        ("category", "Classic Rock", "rock"),
        ("genre", "ELECTRONIC", "electronic"),
        ("tags", ["chill-out", "lounge"], "chillout"),
        ("tags", "house,techno", "electronic"),
        ("category", "Klassik", "classical"),
        ("tags", "hip-hop; rap", "hiphop"),
        ("genre", "heavy metal", "metal"),
        ("tags", "soul|jazz", "jazz"),
    ],
)
def test_categories_match_real_metadata_forms(field, value, category):
    criteria = filters.normalize_filter({"categories": [category]})
    assert filters.matches_station({field: value}, criteria)


def test_category_or_and_minimum_bitrate_are_combined():
    stations = [
        {"id": "rock128", "tags": ["rock"], "bitrate": 128},
        {"id": "electro192", "genre": "electronic", "bitrate": "192 kbps"},
        {"id": "chill64", "category": "chillout", "bitrate": 64},
        {"id": "jazz256", "tags": ["jazz"], "bitrate": 256},
        {"id": "unknown", "genre": "rock", "bitrate": 0},
    ]
    criteria = {
        "categories": ["rock", "electronic", "chillout"],
        "minimum_bitrate": 128,
    }
    assert [row["id"] for row in filters.filter_stations(stations, criteria)] == [
        "rock128",
        "electro192",
    ]
    criteria["include_unknown"] = True
    assert [row["id"] for row in filters.filter_stations(stations, criteria)] == [
        "rock128",
        "electro192",
        "unknown",
    ]
    assert len(filters.filter_stations(stations, {})) == 5


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "-",
        "n/a",
        0,
        -1,
        True,
        float("nan"),
        float("inf"),
        [],
        {},
        10**1000,
        "128.5",
        "128000",
    ],
)
def test_unknown_bitrate_is_not_a_known_rate(value):
    assert filters.bitrate_kbps(value) is None
    assert not filters.matches_station(
        {"bitrate": value}, filters.normalize_filter({"minimum_bitrate": 128})
    )
    assert filters.matches_station(
        {"bitrate": value},
        filters.normalize_filter({"minimum_bitrate": 128, "include_unknown": True}),
    )


@pytest.mark.parametrize(
    "value", [128, 128.0, "128", "128 kbps", "128 kbit/s", "128 KB/S"]
)
def test_known_bitrate_forms(value):
    assert filters.bitrate_kbps(value) == 128


def test_category_names_are_not_inferred_from_station_names_or_substrings():
    criteria = filters.normalize_filter({"categories": ["rock", "pop"]})
    for row in [
        {"name": "Rock Radio", "tags": ["jazz"]},
        {"genre": "popular science"},
        {"category": "bedrock"},
        None,
    ]:
        assert not filters.matches_station(row, criteria)


@pytest.mark.parametrize(
    "value",
    [
        None,
        [],
        "rock",
        {"categories": [[], {}, "unknown"], "minimum_bitrate": True},
        {"categories": "rock", "minimum_bitrate": 999},
    ],
)
def test_malformed_settings_normalize_to_defaults(value):
    assert filters.normalize_filter(value) == filters.normalize_filter()


def test_country_options_are_alphabetical_unique_and_bounded():
    assert filters.country_names(
        [
            {"country": "Germany"},
            {"country": " germany "},
            {"country": "Ghana"},
            {"country": "France"},
            {"country": "unknown"},
            {"country": ""},
            {"country": "Bad\nName"},
            {"country": "x" * 129},
            {"country": []},
            None,
        ]
    ) == ["France", "Germany", "Ghana"]


def test_country_is_exact_case_insensitive_and_combined_with_existing_filters():
    criteria = {"country": "Germany", "categories": ["rock"], "minimum_bitrate": 128}
    rows = [
        {"id": "ok", "country": "germany", "tags": ["rock"], "bitrate": 192},
        {"id": "low", "country": "Germany", "tags": ["rock"], "bitrate": 64},
        {"id": "genre", "country": "Germany", "tags": ["jazz"], "bitrate": 192},
        {"id": "foreign", "country": "France", "tags": ["rock"], "bitrate": 192},
        {"id": "missing", "tags": ["rock"], "bitrate": 192},
    ]
    assert [row["id"] for row in filters.filter_stations(rows, criteria)] == ["ok"]
    assert len(filters.filter_stations(rows, {})) == 5
    assert filters.normalize_filter({"country": " Germany "})["country"] == "Germany"
    assert "country" not in filters.normalize_filter({"country": []})
