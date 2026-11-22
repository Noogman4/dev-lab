"""Shared, offline category/bitrate filtering for radio station dictionaries."""

import math
import re

CATEGORIES = (
    ("rock", "Rock"),
    ("electronic", "Electronic"),
    ("chillout", "Chillout"),
    ("pop", "Pop"),
    ("jazz", "Jazz"),
    ("classical", "Classical"),
    ("house", "House"),
    ("hiphop", "Hip-Hop"),
    ("techno", "Techno"),
    ("schlager", "Schlager"),
    ("ambient", "Ambient"),
    ("metal", "Metal"),
    ("blues", "Blues"),
    ("reggae", "Reggae"),
    ("soul", "Soul"),
    ("country", "Country"),
)
BITRATES = (0, 64, 128, 192, 256)
_ALIASES = {
    "rock": ("rock", "hardrock", "softrock", "punkrock", "rockabilly"),
    "electronic": (
        "electronic",
        "electronica",
        "elektronisch",
        "elektronische",
        "edm",
        "dance",
        "house",
        "techno",
        "trance",
        "dubstep",
        "drum and bass",
        "dnb",
    ),
    "chillout": ("chillout", "chill out", "chill", "downtempo", "lounge"),
    "classical": ("classical", "klassik", "klassische", "classic music"),
    "hiphop": ("hiphop", "hip hop", "rap"),
}
_PATTERNS = {
    key: re.compile(
        r"(?<!\w)(?:"
        + "|".join(re.escape(alias) for alias in _ALIASES.get(key, (key,)))
        + r")(?!\w)"
    )
    for key, _ in CATEGORIES
}


def country_name(value):
    if not isinstance(value, str) or len(value) > 128:
        return ""
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        return ""
    name = " ".join(value.split())
    return "" if name.casefold() in {"", "-", "unknown", "n/a", "none"} else name


def country_names(stations):
    names = {}
    for row in stations:
        if isinstance(row, dict):
            name = country_name(row.get("country"))
            if name:
                names.setdefault(name.casefold(), name)
    return sorted(names.values(), key=str.casefold)


def normalize_filter(value=None):
    raw = value if isinstance(value, dict) else {}
    selected = raw.get("categories", [])
    if not isinstance(selected, list):
        selected = []
    selected = selected[:64]
    minimum = raw.get("minimum_bitrate", 0)
    if type(minimum) is not int or minimum not in BITRATES:
        minimum = 0
    normalized = {
        "categories": [key for key, _ in CATEGORIES if key in selected],
        "minimum_bitrate": minimum,
        "include_unknown": raw.get("include_unknown") is True,
    }
    country = country_name(raw.get("country"))
    if country:
        normalized["country"] = country
    return normalized


def bitrate_kbps(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        if not 0 < value <= 10000:
            return None
        return int(value) if math.isfinite(value) and value == int(value) else None
    if isinstance(value, str):
        match = re.fullmatch(r"\s*([0-9]{1,4})\s*(?:kbps|kbit/s|kb/s)?\s*", value, re.I)
        if match and int(match[1]) > 0:
            return int(match[1])
    return None


def _metadata(station):
    parts = []
    for field in ("category", "genre", "tags"):
        value = station.get(field, "")
        if isinstance(value, str):
            parts.append(value[:4096])
        elif isinstance(value, list):
            parts.extend(item[:256] for item in value[:64] if isinstance(item, str))
    return re.sub(r"[-_/]+", " ", " ".join(parts).casefold())


def matches_station(station, criteria):
    """Categories are OR; bitrate is AND. Zero minimum includes unknown rates.

    Pass normalized criteria when filtering a collection. Names and URLs are
    deliberately not category metadata (e.g. 'Rock' in a town/station name).
    """
    if not isinstance(station, dict):
        return False
    country = criteria.get("country", "")
    if (
        country
        and country_name(station.get("country")).casefold() != country.casefold()
    ):
        return False
    minimum = criteria["minimum_bitrate"]
    if minimum:
        rate = bitrate_kbps(station.get("bitrate"))
        if rate is None:
            if not criteria["include_unknown"]:
                return False
        elif rate < minimum:
            return False
    selected = criteria["categories"]
    if selected:
        metadata = _metadata(station)
        return any(_PATTERNS[key].search(metadata) for key in selected)
    return True


def filter_stations(stations, criteria):
    normalized = normalize_filter(criteria)
    return [row for row in stations if matches_station(row, normalized)]
