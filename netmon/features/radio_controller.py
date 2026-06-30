"""Internetradio controller helpers for NetMon."""

# source marker: "tags": {"title": "Tags"

from __future__ import annotations

import concurrent.futures
import http.client
import json
import os
import re
import socket
import shutil
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from tkinter import filedialog, messagebox, simpledialog
from xml.etree import ElementTree

try:
    from netmon.core.tooling import has_cmd
except ModuleNotFoundError:
    from core.tooling import has_cmd

try:
    from netmon.core.utils import safe_write_json, call_in_ui_thread
except ModuleNotFoundError:
    from core.utils import safe_write_json, call_in_ui_thread


def default_radio_settings():
    return {
        "theme": "light",
        "volume": 50,
        "eq_bass": 0,
        "eq_mid": 0,
        "eq_treble": 0,
        "last_station_id": "",
        "last_search": "",
        "station_list_columns": ["name", "genre", "bitrate"],
        "recordings_dir": "",
        "playlist_entries": [],
        "playlist_path": "",
        "playlists_dir": "",
        "projectm_preset_import_dir": "",
        "projectm_preset_download_url": "",
    }


RADIO_THEME_NAMES = ("light", "dark", "beige", "pop")
RADIO_THEME_KEYS = (
    "bg",
    "panel_bg",
    "fg",
    "muted_fg",
    "accent",
    "border",
    "disabled_fg",
    "entry_bg",
    "entry_fg",
    "text_bg",
    "text_fg",
    "select_bg",
    "select_fg",
    "tree_bg",
    "tree_fg",
    "tab_bg",
    "tab_fg",
    "tab_selected_bg",
    "tab_selected_fg",
)
RADIO_THEME_ALIASES = {
    "pop (user)": "pop",
    "pop-user": "pop",
    "pop_user": "pop",
}


RADIO_DB_ENDPOINT = "https://de1.api.radio-browser.info/json/stations/search"
RADIO_DB_LIMIT = 5000
RADIO_RESULTS_PER_PAGE = 50
RADIO_DB_FIELDS = (
    "name",
    "url",
    "url_resolved",
    "homepage",
    "favicon",
    "tags",
    "country",
    "countrycode",
    "language",
    "codec",
    "bitrate",
    "lastcheckok",
    "votes",
    "clickcount",
)

ALLOWED_RADIO_STREAM_SCHEMES = {"http", "https", "rtsp", "rtmp"}
ALLOWED_RADIO_HOMEPAGE_SCHEMES = {"http", "https"}

RADIO_BROWSER_SOURCE_ENDPOINTS = {
    "radio_browser_api": "https://de1.api.radio-browser.info/json/stations",
    "radio_browser_all_api": "https://all.api.radio-browser.info/json/stations",
    "radio_browser_country_de_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/DE",
    "radio_browser_country_at_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AT",
    "radio_browser_country_ch_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CH",
    "radio_browser_country_fr_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/FR",
    "radio_browser_country_it_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/IT",
    "radio_browser_country_es_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/ES",
    "radio_browser_country_nl_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/NL",
    "radio_browser_country_be_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BE",
    "radio_browser_country_gb_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/GB",
    "radio_browser_country_us_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/US",
    "radio_browser_country_ca_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CA",
    "radio_browser_country_au_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AU",
    "radio_browser_country_jp_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/JP",
    "radio_browser_country_br_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BR",
    "radio_browser_search": "https://de1.api.radio-browser.info/json/stations/search",
    "community_radio_api": "https://api.radio-browser.info/json/stations",
    "radio_browser_top": "https://de1.api.radio-browser.info/json/stations/topvote/100",
}

ICECAST_SOURCE_ENDPOINTS = {
    "icecast_json": "https://dir.xiph.org/yp.xml",
}

RADIO_DATABASE_SOURCE_CHECK_ENDPOINTS = {
    "radio_browser_api": "https://de1.api.radio-browser.info/json/stations",
    "radio_browser_all_api": "https://all.api.radio-browser.info/json/stations",
    "radio_browser_country_de_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/DE",
    "radio_browser_country_at_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AT",
    "radio_browser_country_ch_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CH",
    "radio_browser_country_fr_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/FR",
    "radio_browser_country_it_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/IT",
    "radio_browser_country_es_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/ES",
    "radio_browser_country_nl_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/NL",
    "radio_browser_country_be_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BE",
    "radio_browser_country_gb_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/GB",
    "radio_browser_country_us_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/US",
    "radio_browser_country_ca_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/CA",
    "radio_browser_country_au_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/AU",
    "radio_browser_country_jp_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/JP",
    "radio_browser_country_br_exact": "https://de1.api.radio-browser.info/json/stations/bycountrycodeexact/BR",
    "radio_browser_country": "https://de1.api.radio-browser.info/json/stations/bycountry/",
    "radio_browser_tag": "https://de1.api.radio-browser.info/json/stations/bytag/",
    "radio_browser_top": "https://de1.api.radio-browser.info/json/stations/topvote/100",
    "radio_browser_search": "https://de1.api.radio-browser.info/json/stations/search",
    "shoutcast_api": "https://directory.shoutcast.com/",
    "icecast_directory": "https://dir.xiph.org/",
    "icecast_json": "https://dir.xiph.org/yp.xml",
    "fmstream": "https://fmstream.org/index.php",
    "streamurl_link": "https://streamurl.link/",
    "airable": "https://www.airablenow.com/",
    "community_radio_api": "https://api.radio-browser.info/",
    "radio_api": "https://radioapi.me/",
}

RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS = {
    "radio_browser_country_de_exact",
    "radio_browser_country_at_exact",
    "radio_browser_country_ch_exact",
    "radio_browser_country_fr_exact",
    "radio_browser_country_it_exact",
    "radio_browser_country_es_exact",
    "radio_browser_country_nl_exact",
    "radio_browser_country_be_exact",
    "radio_browser_country_gb_exact",
    "radio_browser_country_us_exact",
    "radio_browser_country_ca_exact",
    "radio_browser_country_au_exact",
    "radio_browser_country_jp_exact",
    "radio_browser_country_br_exact",
}

RADIO_STATION_LIST_COLUMN_DEFS = {
    "name": {"title_key": "radio_col_name", "title": "Station", "width": 260, "anchor": "w"},
    "genre": {"title_key": "radio_col_genre", "title": "Genre", "width": 180, "anchor": "w"},
    "tags": {"title_key": "radio_col_tags", "title": "Tags", "width": 260, "anchor": "w"},
    "bitrate": {"title_key": "radio_col_bitrate", "title": "Bitrate", "width": 80, "anchor": "e"},
    "url": {"title_key": "radio_col_url", "title": "URL", "width": 220, "anchor": "w"},
    "homepage": {"title_key": "radio_col_homepage", "title": "Homepage", "width": 220, "anchor": "w"},
    "country": {"title_key": "radio_col_country", "title": "Country", "width": 120, "anchor": "w"},
    "language": {"title_key": "radio_col_language", "title": "Language", "width": 100, "anchor": "w"},
    "codec": {"title_key": "radio_col_codec", "title": "Codec", "width": 80, "anchor": "w"},
}

RADIO_STATION_LIST_COLUMN_ORDER = (
    "name",
    "genre",
    "tags",
    "bitrate",
    "url",
    "homepage",
    "country",
    "language",
    "codec",
)

RADIO_AUDIO_EXTENSIONS = {
    ".mp3",
    ".m4a",
    ".aac",
    ".ogg",
    ".wav",
    ".flac",
    ".opus",
    ".wma",
    ".aiff",
    ".aif",
    ".mka",
}


def _tr(app, key, default):
    try:
        return app.tr(key, default)
    except Exception:
        return default


def _app_value(app, name, default=None):
    return getattr(app, name, default)


def _app_callback(app, name):
    callback = _app_value(app, name, None)
    return callback if callable(callback) else None


def _bool_var_value(var, default):
    try:
        return bool(var.get()) if var is not None else default
    except Exception:
        return default


def _slugify_station_id(text: str) -> str:
    raw = str(text or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
    return slug or "station"


def _default_recordings_dir(app) -> str:
    base = str(getattr(app, "netmon_state_dir", "") or "").strip()
    if not base:
        base = tempfile.gettempdir()
    return os.path.join(base, "radio_recordings")


def _default_playlist_path(app) -> str:
    return os.path.join(_default_playlists_dir(app), "radio_playlist.m3u")


def _default_playlists_dir(app) -> str:
    base = str(getattr(app, "netmon_state_dir", "") or "").strip()
    if not base:
        base = tempfile.gettempdir()
    return os.path.join(base, "radio_playlists")


def _radio_recordings_dir(app) -> str:
    return str(
        getattr(app, "radio_recordings_dir", "") or _default_recordings_dir(app)
    ).strip()


def _radio_playlists_dir(app) -> str:
    return str(
        getattr(app, "radio_playlists_dir", "") or _default_playlists_dir(app)
    ).strip()


def _radio_playlist_path(app) -> str:
    return str(
        getattr(app, "radio_playlist_path", "")
        or getattr(app, "radio_settings", {}).get("playlist_path", "")
        or _default_playlist_path(app)
    ).strip()


def _radio_folder_browser_root_dir(app, mode: str) -> str:
    normalized_mode = str(mode or "recordings").strip() or "recordings"
    if normalized_mode == "playlists":
        return _radio_playlists_dir(app)
    if normalized_mode == "system":
        return str(getattr(app, "radio_system_folder_path", "") or "").strip()
    return _radio_recordings_dir(app)


def _playlist_dialog_defaults(app) -> tuple[str, str]:
    return _radio_playlists_dir(app), _radio_playlist_path(app)


def _normalize_station_stream_url(value) -> str:
    url = str(value or "").strip()
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return ""
    scheme = str(parsed.scheme or "").strip().lower()
    if scheme not in ALLOWED_RADIO_STREAM_SCHEMES:
        return ""
    return url


def _normalize_station_homepage_url(value) -> str:
    url = str(value or "").strip()
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return ""
    scheme = str(parsed.scheme or "").strip().lower()
    if scheme not in ALLOWED_RADIO_HOMEPAGE_SCHEMES:
        return ""
    return url


def normalize_station_entry(entry, *, custom=False):
    if not isinstance(entry, dict):
        return None

    name = str(entry.get("name", "") or "").strip()
    url = _normalize_station_stream_url(
        entry.get("url", "") or entry.get("url_resolved", "") or ""
    )
    if not name or not url:
        return None

    station_id = str(entry.get("id", "") or "").strip()
    if not station_id:
        station_id = _slugify_station_id(name)

    category = str(entry.get("category", "") or "").strip()
    station = {
        "id": station_id,
        "name": name,
        "url": url,
        "category": category,
        "custom": bool(entry.get("custom", custom)),
    }
    for key in RADIO_DB_FIELDS:
        if key not in entry:
            continue
        value = entry.get(key)
        if key in {"url", "url_resolved"}:
            value = _normalize_station_stream_url(value)
        if key == "homepage":
            value = _normalize_station_homepage_url(value)
        if key == "tags" and isinstance(value, str):
            value = [tag.strip() for tag in value.split(",") if tag.strip()]
        station[key] = value
    if station.get("url_resolved") and not station.get("url"):
        station["url"] = _normalize_station_stream_url(
            station.get("url_resolved") or ""
        )
    if not station.get("url"):
        return None
    return station


def _load_json(path, fallback):
    try:
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
    except Exception:
        pass
    return fallback


def _read_m3u_playlist(path):
    try:
        if not os.path.isfile(path):
            return []
        entries = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                item = str(line or "").strip()
                if not item or item.startswith("#"):
                    continue
                entries.append(item)
        return entries
    except Exception:
        return []


def _write_m3u_playlist(path, entries):
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        lines = ["#EXTM3U"]
        lines.extend(str(item).strip() for item in entries if str(item).strip())
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        return True, ""
    except Exception as exc:
        return False, str(exc)


def _read_default_stations(app):
    return _load_json(_app_value(app, "radio_default_stations_path", ""), [])


def _schedule_ui(app, callback):
    after = _app_callback(app, "after")
    if callable(after):
        try:
            after(0, callback)
            return True
        except Exception:
            pass
    if threading.current_thread() is not threading.main_thread():
        return False
    try:
        callback()
        return True
    except Exception:
        return False


def _normalize_station_list_columns(columns):
    normalized = []
    seen = set()
    for column_id in list(columns or []):
        key = str(column_id or "").strip()
        if key not in RADIO_STATION_LIST_COLUMN_DEFS or key in seen:
            continue
        normalized.append(key)
        seen.add(key)
    if not normalized:
        normalized = list(default_radio_settings()["station_list_columns"])
    return normalized


def selected_radio_station_columns(app):
    settings = getattr(app, "radio_settings", {}) or {}
    return _normalize_station_list_columns(settings.get("station_list_columns", []))


def _station_genre_text(row):
    category = str(row.get("category", "") or "").strip()
    if category:
        return category
    tags = [
        str(tag or "").strip()
        for tag in (row.get("tags", []) or [])
        if str(tag or "").strip()
    ]
    ignored = {
        "fm",
        "am",
        "radio",
        "music",
        "musik",
        "online",
        "station",
        "stream",
        "live",
    }
    for tag in tags:
        normalized = tag.strip().lower()
        if normalized and normalized not in ignored and len(normalized) > 2:
            return tag
    return tags[0] if tags else ""


def _station_table_value(row, column_id):
    if column_id == "name":
        return str(row.get("name", "") or "").strip()
    if column_id == "genre":
        return _station_genre_text(row)
    if column_id == "tags":
        return ", ".join(row.get("tags", []) or [])
    if column_id == "bitrate":
        bitrate = row.get("bitrate", "")
        return f"{bitrate} kbps" if bitrate not in ("", None) else ""
    if column_id == "url":
        return str(row.get("url_resolved", "") or row.get("url", "") or "").strip()
    if column_id == "homepage":
        return str(row.get("homepage", "") or "").strip()
    if column_id == "country":
        return str(row.get("country", "") or "").strip()
    if column_id == "language":
        return str(row.get("language", "") or "").strip()
    if column_id == "codec":
        return str(row.get("codec", "") or "").strip()
    return ""


def _filter_radio_db_rows(raw_rows):
    if not isinstance(raw_rows, list):
        return []

    filtered_rows = []
    for item in raw_rows:
        if not isinstance(item, dict):
            continue
        station = {}
        for key in RADIO_DB_FIELDS:
            if key not in item:
                continue
            value = item.get(key)
            if key == "tags":
                if isinstance(value, str):
                    station[key] = [
                        tag.strip() for tag in value.split(",") if tag.strip()
                    ]
                elif isinstance(value, list):
                    station[key] = [
                        str(tag).strip() for tag in value if str(tag).strip()
                    ]
                else:
                    station[key] = []
                continue
            if value is None:
                station[key] = ""
                continue
            if key in {"bitrate", "votes", "clickcount"}:
                try:
                    station[key] = int(value)
                except Exception:
                    station[key] = 0
                continue
            if key == "lastcheckok":
                station[key] = bool(value)
                continue
            station[key] = str(value).strip()
        normalized = normalize_station_entry(station)
        if normalized is not None:
            filtered_rows.append(normalized)
    return filtered_rows


def _search_station_rows(stations, query, *, limit=None):
    q = str(query or "").strip().lower()
    if not q:
        return []

    results = []
    for station in stations:
        name = str(station.get("name", "") or "").lower()
        tags = " ".join(station.get("tags", []) or []).lower()
        category = str(station.get("category", "") or "").lower()
        url = str(station.get("url", "") or "").lower()
        if q in name or q in tags or q in category or q in url:
            results.append(station)
        if limit is not None and len(results) >= limit:
            break
    return results


def _radio_station_index(app):
    stations = getattr(app, "radio_stations", []) or []
    return {station.get("id", ""): station for station in stations if station.get("id")}


def _selected_station_id(app):
    context_station_id = str(getattr(app, "radio_context_station_id", "") or "").strip()
    if context_station_id:
        return context_station_id
    table = getattr(app, "radio_station_table", None)
    if table is None:
        return ""
    try:
        selected = table.selection()
    except Exception:
        return ""
    if selected:
        return str(selected[0] or "").strip()
    try:
        focused = table.focus()
    except Exception:
        focused = ""
    return str(focused or "").strip()



def save_radio_stations(app, stations=None):
    payload = []
    for station in list(
        stations if stations is not None else getattr(app, "radio_stations", [])
    ):
        normalized = normalize_station_entry(
            station,
            custom=(
                bool(station.get("custom", False))
                if isinstance(station, dict)
                else False
            ),
        )
        if normalized is not None:
            payload.append(normalized)

    ok, err = safe_write_json(
        app.radio_stations_path,
        payload,
        indent=2,
        ensure_ascii=False,
    )
    if ok:
        app.radio_stations = payload
        return True

    try:
        app.log(f"Radio-Senderliste konnte nicht gespeichert werden: {err}")
    except Exception:
        pass
    return False



def save_radio_settings(app):
    def _safe_var_value(var, default=""):
        if var is None:
            return default
        getter = getattr(var, "get", None)
        if not callable(getter):
            return default
        try:
            return getter()
        except Exception:
            return default

    payload = default_radio_settings()
    volume = 50
    volume_var = getattr(app, "radio_volume_var", None)
    if volume_var is not None:
        try:
            volume = int(volume_var.get() or 50)
        except Exception:
            volume = 50
    eq_bass = 0
    eq_mid = 0
    eq_treble = 0
    theme_name = _radio_theme_name_from_app(
        app,
        fallback=(getattr(app, "radio_settings", {}) or {}).get("theme", "light"),
    )
    for var_name, target in (
        ("radio_eq_bass_var", "eq_bass"),
        ("radio_eq_mid_var", "eq_mid"),
        ("radio_eq_treble_var", "eq_treble"),
    ):
        var = getattr(app, var_name, None)
        if var is None:
            continue
        try:
            value = int(var.get() or 0)
        except Exception:
            value = 0
        if target == "eq_bass":
            eq_bass = max(-12, min(12, value))
        elif target == "eq_mid":
            eq_mid = max(-12, min(12, value))
        else:
            eq_treble = max(-12, min(12, value))
    payload.update(
        {
            "theme": theme_name,
            "volume": max(0, min(100, volume)),
            "eq_bass": eq_bass,
            "eq_mid": eq_mid,
            "eq_treble": eq_treble,
            "last_station_id": str(
                getattr(app, "radio_current_station_id", "") or ""
            ).strip(),
            "last_search": str(
                _safe_var_value(getattr(app, "radio_search_var", None), "") or ""
            ).strip(),
            "station_list_columns": selected_radio_station_columns(app),
            "recordings_dir": str(
                getattr(app, "radio_recordings_dir", "")
                or getattr(app, "radio_settings", {}).get("recordings_dir", "")
                or _default_recordings_dir(app)
            ).strip(),
            "playlist_entries": [
                str(item).strip()
                for item in list(getattr(app, "radio_playlist_entries", []) or [])
                if str(item).strip()
            ],
            "playlist_path": str(
                getattr(app, "radio_playlist_path", "")
                or getattr(app, "radio_settings", {}).get("playlist_path", "")
                or _default_playlist_path(app)
            ).strip(),
            "playlists_dir": str(
                getattr(app, "radio_playlists_dir", "")
                or getattr(app, "radio_settings", {}).get("playlists_dir", "")
                or _default_playlists_dir(app)
            ).strip(),
            "projectm_preset_import_dir": str(
                getattr(app, "radio_settings", {}).get("projectm_preset_import_dir", "")
                or ""
            ).strip(),
            "projectm_preset_download_url": str(
                getattr(app, "radio_settings", {}).get("projectm_preset_download_url", "")
                or ""
            ).strip(),
        }
    )
    app.radio_settings = payload
    ok, err = safe_write_json(
        app.radio_settings_path,
        payload,
        indent=2,
        ensure_ascii=False,
    )
    if not ok:
        try:
            app.log(f"Radio-Einstellungen konnten nicht gespeichert werden: {err}")
        except Exception:
            pass
    return ok


def _normalize_radio_theme_name(theme_name, fallback="light"):
    fallback_name = str(fallback or "light").strip().lower() or "light"
    if fallback_name not in RADIO_THEME_NAMES:
        fallback_name = "light"
    normalized = str(theme_name or "").strip().lower()
    if not normalized:
        return fallback_name
    normalized = RADIO_THEME_ALIASES.get(normalized, normalized)
    return normalized if normalized in RADIO_THEME_NAMES else fallback_name


def _radio_theme_name_from_app(app, fallback="light"):
    current = getattr(app, "_app_theme", None)
    if isinstance(current, dict):
        return _normalize_radio_theme_name(current.get("name", fallback), fallback)
    settings = getattr(app, "radio_settings", {}) or {}
    return _normalize_radio_theme_name(settings.get("theme", fallback), fallback)


def _radio_theme_palette_from_app(app):
    current = getattr(app, "_app_theme", None)
    if not isinstance(current, dict):
        return {}
    palette = {
        key: str(current.get(key, "") or "").strip()
        for key in RADIO_THEME_KEYS
        if str(current.get(key, "") or "").strip()
    }
    if palette:
        palette["name"] = _normalize_radio_theme_name(current.get("name", "light"))
    return palette


def _apply_radio_theme_setting(app, theme_name, theme_palette=None):
    normalized = _normalize_radio_theme_name(theme_name)
    if isinstance(theme_palette, dict) and theme_palette:
        apply_theme_palette = getattr(app, "apply_theme_palette", None)
        if callable(apply_theme_palette):
            try:
                apply_theme_palette(normalized, dict(theme_palette))
                return normalized
            except Exception:
                pass
    apply_theme = getattr(app, "apply_theme", None)
    if callable(apply_theme):
        try:
            apply_theme(normalized)
            return normalized
        except Exception:
            pass
    settings = getattr(app, "radio_settings", None)
    if isinstance(settings, dict):
        settings["theme"] = normalized
    current = getattr(app, "_app_theme", None)
    updated = dict(current) if isinstance(current, dict) else {}
    if isinstance(theme_palette, dict) and theme_palette:
        updated.update(
            {
                key: value
                for key, value in dict(theme_palette).items()
                if key in RADIO_THEME_KEYS and str(value or "").strip()
            }
        )
    updated["name"] = normalized
    if updated:
        try:
            app._app_theme = updated
        except Exception:
            pass
    return normalized


def build_radio_handover_payload(app):
    save_radio_settings(app)
    station_id = str(getattr(app, "radio_current_station_id", "") or "").strip()
    current = getattr(app, "radio_current_station", None)
    if not isinstance(current, dict):
        current = _resolve_station_by_id(app, station_id)
    title_text = str(
        getattr(getattr(app, "radio_title_var", None), "get", lambda: "")() or ""
    ).strip()
    if title_text.lower() in {
        _tr(app, "radio_header_title_idle", "Titel: -").strip().lower(),
        _tr(app, "radio_header_title_connecting", "Titel: verbinde...").strip().lower(),
        _tr(app, "radio_header_title_error", "Titel: Fehler / keine Verbindung")
        .strip()
        .lower(),
    }:
        title_text = ""
    payload = {
        "current_station_id": station_id,
        "current_station": dict(current) if isinstance(current, dict) else {},
        "current_title": title_text,
        "was_playing": bool(getattr(app, "radio_proc", None)),
        "theme": _radio_theme_name_from_app(
            app,
            fallback=(getattr(app, "radio_settings", {}) or {}).get("theme", "light"),
        ),
        "theme_palette": _radio_theme_palette_from_app(app),
        "volume": int(
            getattr(getattr(app, "radio_volume_var", None), "get", lambda: 50)() or 50
        ),
        "eq_bass": int(
            getattr(getattr(app, "radio_eq_bass_var", None), "get", lambda: 0)() or 0
        ),
        "eq_mid": int(
            getattr(getattr(app, "radio_eq_mid_var", None), "get", lambda: 0)() or 0
        ),
        "eq_treble": int(
            getattr(getattr(app, "radio_eq_treble_var", None), "get", lambda: 0)() or 0
        ),
        "last_search": str(
            getattr(getattr(app, "radio_search_var", None), "get", lambda: "")() or ""
        ).strip(),
    }
    return payload


def apply_radio_handover_payload(app, payload, *, auto_play=False):
    if not isinstance(payload, dict):
        return False
    settings = default_radio_settings()
    settings.update(getattr(app, "radio_settings", {}) or {})
    station_id = str(payload.get("current_station_id", "") or "").strip()
    current_title = str(payload.get("current_title", "") or "").strip()
    settings.update(
        {
            "theme": _normalize_radio_theme_name(
                payload.get("theme", settings.get("theme", "light")),
                settings.get("theme", "light"),
            ),
            "volume": max(
                0,
                min(100, int(payload.get("volume", settings.get("volume", 50)) or 50)),
            ),
            "eq_bass": max(
                -12,
                min(12, int(payload.get("eq_bass", settings.get("eq_bass", 0)) or 0)),
            ),
            "eq_mid": max(
                -12, min(12, int(payload.get("eq_mid", settings.get("eq_mid", 0)) or 0))
            ),
            "eq_treble": max(
                -12,
                min(
                    12, int(payload.get("eq_treble", settings.get("eq_treble", 0)) or 0)
                ),
            ),
            "last_station_id": station_id,
            "last_search": str(
                payload.get("last_search", settings.get("last_search", "")) or ""
            ).strip(),
        }
    )
    app.radio_settings = settings
    settings["theme"] = _apply_radio_theme_setting(
        app,
        settings.get("theme", "light"),
        payload.get("theme_palette"),
    )
    app.radio_current_station_id = station_id
    station = payload.get("current_station")
    if isinstance(station, dict) and station.get("id"):
        app.radio_current_station = dict(station)
    else:
        app.radio_current_station = _resolve_station_by_id(app, station_id)
    for var_name, key_name, fallback in (
        ("radio_search_var", "last_search", ""),
        ("radio_volume_var", "volume", 50),
        ("radio_eq_bass_var", "eq_bass", 0),
        ("radio_eq_mid_var", "eq_mid", 0),
        ("radio_eq_treble_var", "eq_treble", 0),
    ):
        var = getattr(app, var_name, None)
        if var is None:
            continue
        try:
            var.set(settings.get(key_name, fallback))
        except Exception:
            pass
    on_radio_eq_preview(app)
    save_radio_settings(app)
    refresh_radio_ui(app)
    for target in _radio_targets(app):
        try:
            target.radio_handover_title = current_title
        except Exception:
            pass
    if current_title:
        _set_radio_title_text(app, current_title)
    if auto_play and bool(payload.get("was_playing")) and station_id:
        play_radio_station(app, station_id)
    return True


def radio_available(app):
    dep_status = getattr(app, "dep_status", {}) or {}
    if "mpv" in dep_status:
        return bool(dep_status.get("mpv"))
    return has_cmd("mpv")


def _radio_targets(app):
    targets = [app]
    host_app = getattr(app, "radio_host_app", None)
    if host_app is not None and host_app is not app:
        targets.append(host_app)
    return targets


def set_radio_status(app, message):
    text = str(message or "").strip() or _tr(app, "radio_status_ready", "Radio bereit.")
    for target in _radio_targets(app):
        for name in ("radio_header_status_var",):
            var = getattr(target, name, None)
            if var is not None:
                try:
                    var.set(text)
                except Exception:
                    pass


def _set_radio_light(app, color):
    for target in _radio_targets(app):
        indicator = getattr(target, "l_radio", None)
        if indicator is None:
            continue
        try:
            target.set_light(indicator, color)
            target.radio_light_state = color
        except Exception:
            pass


def _set_radio_station_text(app, station_name):
    name = str(station_name or "").strip()
    value = (
        _tr(app, "radio_header_off", "Radio: aus")
        if not name
        else _tr(app, "radio_header_station", "Radio: {name}").format(name=name)
    )
    for target in _radio_targets(app):
        for var_name in ("radio_status_var", "radio_now_playing_var"):
            var = getattr(target, var_name, None)
            if var is not None:
                try:
                    var.set(value)
                except Exception:
                    pass


def _set_radio_title_text(app, title):
    value = str(title or "").strip() or _tr(app, "radio_header_title_idle", "Titel: -")
    for target in _radio_targets(app):
        for var_name in ("radio_title_var", "radio_header_status_var"):
            var = getattr(target, var_name, None)
            if var is not None:
                try:
                    var.set(value)
                except Exception:
                    pass


def _set_radio_stream_url_text(app, url):
    value = str(url or "").strip() or "-"
    for target in _radio_targets(app):
        var = getattr(target, "radio_stream_url_var", None)
        if var is not None:
            try:
                var.set(f"Stream-URL: {value}")
            except Exception:
                pass


def _set_radio_bitrate_text(app, bitrate):
    value = str(bitrate or "").strip()
    if value:
        value = f"{value} kbps"
    else:
        value = "-"
    for target in _radio_targets(app):
        var = getattr(target, "radio_bitrate_var", None)
        if var is not None:
            try:
                var.set(f"Bitrate: {value}")
            except Exception:
                pass


def _radio_debug_log(app, message):
    text = str(message or "").strip()
    if not text:
        return
    for candidate in [app, *list(_radio_targets(app))]:
        log_fn = getattr(candidate, "log_safe", None)
        if callable(log_fn):
            try:
                log_fn(f"[RadioEditDebug] {text}")
                return
            except Exception:
                pass
        log_fn = getattr(candidate, "log", None)
        if callable(log_fn):
            try:
                log_fn(f"[RadioEditDebug] {text}")
                return
            except Exception:
                pass


def _set_custom_form_values(app, *, name="", url="", homepage="", category=""):
    for target in _radio_targets(app):
        for attr_name, value in (
            ("radio_custom_name_var", name),
            ("radio_custom_url_var", url),
            ("radio_custom_homepage_var", homepage),
            ("radio_custom_category_var", category),
        ):
            var = getattr(target, attr_name, None)
            if var is not None:
                try:
                    var.set(str(value or ""))
                except Exception:
                    pass


def _eq_value(app, var_name):
    try:
        return max(-12, min(12, int(getattr(app, var_name).get() or 0)))
    except Exception:
        return 0


def _eq_filter_spec_from_values(bass, mid, treble):
    values = [int(bass), int(mid), int(treble)]
    if not any(values):
        return ""
    return (
        "lavfi=["
        f"equalizer=f=100:t=q:w=1:g={values[0]},"
        f"equalizer=f=1000:t=q:w=1:g={values[1]},"
        f"equalizer=f=8000:t=q:w=1:g={values[2]}"
        "]"
    )


def radio_eq_filter_spec(app):
    return _eq_filter_spec_from_values(
        _eq_value(app, "radio_eq_bass_var"),
        _eq_value(app, "radio_eq_mid_var"),
        _eq_value(app, "radio_eq_treble_var"),
    )




def filtered_radio_stations(app, query=None):
    stations = list(getattr(app, "radio_stations", []) or [])
    if query is None:
        var = getattr(app, "radio_search_var", None)
        if var is not None:
            try:
                query = var.get()
            except Exception:
                query = ""
        else:
            query = ""
    text = str(query or "").strip().lower()
    if not text:
        return stations

    result = []
    for station in stations:
        haystack = " ".join(
            [
                str(station.get("name", "") or ""),
                str(station.get("category", "") or ""),
                str(station.get("url", "") or ""),
            ]
        ).lower()
        if text in haystack:
            result.append(station)
    return result




def update_radio_dependency_state(app):
    available = radio_available(app)
    hint = (
        ""
        if available
        else _tr(
            app, "radio_dependency_missing", "Radio deaktiviert: mpv nicht gefunden."
        )
    )
    label = getattr(app, "radio_dependency_var", None)
    if label is not None:
        try:
            label.set(hint or _tr(app, "radio_status_ready", "Radio bereit."))
        except Exception:
            pass

    if not available:
        set_radio_status(app, hint)
        _set_radio_light(app, "gray")
        _set_radio_station_text(app, "")
        _set_radio_title_text(app, _tr(app, "radio_header_title_idle", "Titel: -"))
    elif not getattr(app, "radio_proc", None):
        set_radio_status(app, _tr(app, "radio_status_ready", "Radio bereit."))
        _set_radio_light(app, "gray")
        _set_radio_station_text(app, "")
        _set_radio_title_text(app, _tr(app, "radio_header_title_idle", "Titel: -"))


def open_radio_tab(app, _event=None):
    tab = getattr(app, "tab_radio", None)
    if tab is not None:
        try:
            app._select_tools_tab(tab)
        except Exception:
            pass
    return "break"


def _resolve_station_by_id(app, station_id):
    return _radio_station_index(app).get(str(station_id or "").strip())


def _resolve_target_station(app, station_id=""):
    station = _resolve_station_by_id(app, station_id)
    if station is not None:
        return station

    selected_id = _selected_station_id(app)
    station = _resolve_station_by_id(app, selected_id)
    if station is not None:
        return station

    current = _resolve_station_by_id(app, getattr(app, "radio_current_station_id", ""))
    if current is not None:
        return current

    favorites = getattr(app, "radio_favorites", []) or []
    for favorite_id in favorites:
        station = _resolve_station_by_id(app, favorite_id)
        if station is not None:
            return station

    stations = filtered_radio_stations(app)
    if stations:
        return stations[0]
    return None


def _radio_ipc_path(app):
    current = str(getattr(app, "radio_ipc_path", "") or "").strip()
    if current:
        return current
    state_dir = str(
        getattr(app, "netmon_state_dir", tempfile.gettempdir()) or tempfile.gettempdir()
    )
    return os.path.join(state_dir, f"netmon-radio-{os.getpid()}.sock")


def _radio_playback_lock(app):
    lock = getattr(app, "radio_playback_lock", None)
    if lock is None:
        lock = threading.RLock()
        try:
            app.radio_playback_lock = lock
        except Exception:
            pass
    return lock


def _cleanup_radio_ipc_path(app):
    path = str(getattr(app, "radio_ipc_path", "") or "").strip()
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def _force_kill_radio_process_by_ipc(ipc_path: str) -> bool:
    ipc_path = str(ipc_path or "").strip()
    if not ipc_path:
        return False
    pattern = f"mpv.*--input-ipc-server={re.escape(ipc_path)}"
    try:
        proc = subprocess.run(
            ["pkill", "-f", pattern],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode == 0
    except Exception:
        return False


def _send_mpv_command(app, command):
    path = _radio_ipc_path(app)
    if not path or not os.path.exists(path):
        return False

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        sock.connect(path)
        payload = json.dumps({"command": command}).encode("utf-8") + b"\n"
        sock.sendall(payload)
        try:
            sock.recv(4096)
        except Exception:
            pass
        return True
    except Exception:
        return False
    finally:
        try:
            sock.close()
        except Exception:
            pass


def _query_mpv_property(app, property_name):
    path = _radio_ipc_path(app)
    if not path or not os.path.exists(path):
        return None

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        sock.connect(path)
        payload = (
            json.dumps(
                {"command": ["get_property", str(property_name or "").strip()]}
            ).encode("utf-8")
            + b"\n"
        )
        sock.sendall(payload)
        data = sock.recv(65536)
        if not data:
            return None
        response = json.loads(data.decode("utf-8", errors="replace").strip())
        if isinstance(response, dict) and response.get("error") == "success":
            return response.get("data")
    except Exception:
        return None
    finally:
        try:
            sock.close()
        except Exception:
            pass
    return None


def radio_recording_available(app):
    return has_cmd("ffmpeg")


def _recording_status_text(app, text):
    value = str(text or "").strip() or _tr(app, "radio_record_status_off", "Recording off.")
    for target in _radio_targets(app):
        var = getattr(target, "radio_record_status_var", None)
        if var is not None:
            try:
                var.set(value)
            except Exception:
                pass


def _recording_dir_text(app):
    target_dir = _radio_recordings_dir(app)
    return _tr(app, "radio_record_dir_value", "Aufnahmeordner: {path}").format(
        path=target_dir or "-"
    )


def _recording_file_text(app):
    path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    return _tr(app, "radio_record_file_value", "Letzte Aufnahme: {name}").format(
        name=os.path.basename(path) if path else "-"
    )


def _record_button_colors(active, blink_on):
    if not active:
        return {
            "bg": "#b32020",
            "fg": "#ffffff",
            "activebackground": "#d83a3a",
            "activeforeground": "#ffffff",
        }
    if blink_on:
        return {
            "bg": "#ff4d4d",
            "fg": "#ffffff",
            "activebackground": "#ff6b6b",
            "activeforeground": "#ffffff",
        }
    return {
        "bg": "#6d1010",
        "fg": "#ffffff",
        "activebackground": "#962020",
        "activeforeground": "#ffffff",
    }


def _stop_record_button_blink(target):
    after_id = getattr(target, "radio_record_blink_after_id", None)
    if after_id is not None:
        try:
            target.after_cancel(after_id)
        except Exception:
            pass
    try:
        target.radio_record_blink_after_id = None
        target.radio_record_blink_on = False
    except Exception:
        pass


def _schedule_record_button_blink(target):
    button = getattr(target, "radio_record_transport_button", None)
    if button is None:
        return
    _stop_record_button_blink(target)

    def tick():
        try:
            proc = getattr(target, "radio_record_proc", None)
            active = proc is not None and proc.poll() is None
        except Exception:
            active = getattr(target, "radio_record_proc", None) is not None
        if not active:
            _stop_record_button_blink(target)
            try:
                button.configure(
                    text="⏺", state="normal", **_record_button_colors(False, False)
                )
            except Exception:
                pass
            return
        blink_on = not bool(getattr(target, "radio_record_blink_on", False))
        try:
            target.radio_record_blink_on = blink_on
        except Exception:
            pass
        try:
            button.configure(
                text="⏺",
                state="normal",
                **_record_button_colors(True, blink_on),
            )
        except Exception:
            pass
        try:
            target.radio_record_blink_after_id = target.after(500, tick)
        except Exception:
            target.radio_record_blink_after_id = None

    tick()


def _radio_source_text(app):
    mode = str(getattr(app, "radio_playback_mode", "radio") or "radio").strip()
    if mode == "playlist":
        path = str(getattr(app, "radio_local_media_path", "") or "").strip()
        return f"Quelle: Playlist | {os.path.basename(path) if path else '-'}"
    if mode == "file":
        path = str(getattr(app, "radio_local_media_path", "") or "").strip()
        return f"Quelle: Datei | {os.path.basename(path) if path else '-'}"
    if mode == "recording":
        path = str(getattr(app, "radio_local_media_path", "") or "").strip()
        return f"Quelle: Mitschnitt | {os.path.basename(path) if path else '-'}"
    current = getattr(app, "radio_current_station", None)
    if not isinstance(current, dict):
        current = _resolve_station_by_id(
            app, getattr(app, "radio_current_station_id", "")
        )
    name = str((current or {}).get("name", "") or "").strip()
    return f"Quelle: Livestream | {name or '-'}"


def refresh_radio_source_ui(app):
    value = _radio_source_text(app)
    for target in _radio_targets(app):
        var = getattr(target, "radio_source_var", None)
        if var is not None:
            try:
                var.set(value)
            except Exception:
                pass


def _playlist_status_text(app):
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    count = len(entries)
    if count == 1:
        return _tr(app, "radio_playlist_status_single", "Playlist: 1 Datei")
    return _tr(app, "radio_playlist_status_many", "Playlist: {count} Dateien").format(
        count=count
    )


def _playlist_label_for_path(path):
    value = str(path or "").strip()
    if not value:
        return "-"
    if os.path.isdir(value):
        return f"[Ordner] {os.path.basename(value) or value}"
    return os.path.basename(value) or value


def _is_audio_file_path(path):
    suffix = os.path.splitext(str(path or "").strip())[1].lower()
    return suffix in RADIO_AUDIO_EXTENSIONS


def _recordings_status_text(app):
    entries = list(getattr(app, "radio_recordings_entries", []) or [])
    count = len(entries)
    if count == 1:
        return _tr(app, "radio_recordings_status_single", "Aufnahmeordner: 1 Datei")
    return _tr(
        app,
        "radio_recordings_status_many",
        "Aufnahmeordner: {count} Dateien",
    ).format(count=count)


def _playlist_folder_status_text(app):
    entries = list(getattr(app, "radio_playlist_files_entries", []) or [])
    count = len(entries)
    if count == 1:
        return _tr(app, "radio_playlist_folder_status_single", "Playlistordner: 1 Datei")
    return _tr(
        app,
        "radio_playlist_folder_status_many",
        "Playlistordner: {count} Dateien",
    ).format(count=count)


def _system_folder_status_text(app):
    entries = list(getattr(app, "radio_system_folder_entries", []) or [])
    count = len(entries)
    if count == 1:
        return _tr(app, "radio_system_folder_status_single", "Systemordner: 1 Datei")
    return _tr(
        app,
        "radio_system_folder_status_many",
        "Systemordner: {count} Dateien",
    ).format(count=count)


def _current_radio_folder_browser_path(app):
    current = str(getattr(app, "radio_folder_browser_current_path", "") or "").strip()
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    root_dir = _radio_folder_browser_root_dir(app, mode)
    if mode == "recordings":
        if current and _radio_folder_browser_path_within_root(current, root_dir):
            return current
        return root_dir
    if current:
        return current
    return root_dir


def _radio_folder_browser_path_within_root(path, root_dir):
    candidate = str(path or "").strip()
    root = str(root_dir or "").strip()
    if not candidate or not root:
        return False
    try:
        candidate_real = os.path.realpath(candidate)
        root_real = os.path.realpath(root)
        return os.path.commonpath([candidate_real, root_real]) == root_real
    except Exception:
        return False


def _set_current_radio_folder_browser_path(app, path):
    app.radio_folder_browser_current_path = str(path or "").strip()


def _radio_folder_browser_parent_path(app):
    current_path = _current_radio_folder_browser_path(app)
    if not current_path:
        return ""
    parent_path = os.path.dirname(current_path.rstrip(os.sep))
    if not parent_path or parent_path == current_path:
        return ""
    if not os.path.isdir(parent_path):
        return ""
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode == "recordings":
        root_dir = _radio_folder_browser_root_dir(app, mode)
        if not _radio_folder_browser_path_within_root(parent_path, root_dir):
            return ""
    return parent_path


def _current_radio_folder_browser_entry(app):
    return (
        str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings"),
        str(_current_radio_folder_browser_path(app) or "").strip(),
    )


def _push_radio_folder_browser_history(app, entry):
    try:
        stack = list(getattr(app, "radio_folder_browser_back_history", []) or [])
    except Exception:
        stack = []
    entry = (str(entry[0] or ""), str(entry[1] or "").strip())
    if stack and stack[-1] == entry:
        app.radio_folder_browser_back_history = stack
        return
    stack.append(entry)
    if len(stack) > 50:
        stack = stack[-50:]
    app.radio_folder_browser_back_history = stack


def _clear_radio_folder_browser_forward_history(app):
    app.radio_folder_browser_forward_history = []


def _set_radio_folder_browser_mode_and_path(app, mode, target_dir):
    mode = str(mode or "recordings").strip() or "recordings"
    target_dir = str(target_dir or "").strip()
    if mode == "recordings":
        root_dir = _radio_folder_browser_root_dir(app, mode)
        if not _radio_folder_browser_path_within_root(target_dir, root_dir):
            target_dir = root_dir
    app.radio_folder_browser_mode = mode
    if mode == "system":
        app.radio_system_folder_path = target_dir
    _set_current_radio_folder_browser_path(app, target_dir)


def _navigate_radio_folder_browser_to(
    app, mode, target_dir, *, announce_text="", push_history=True
):
    current_entry = _current_radio_folder_browser_entry(app)
    next_entry = (
        str(mode or "recordings").strip() or "recordings",
        str(target_dir or "").strip(),
    )
    if push_history and current_entry != next_entry:
        _push_radio_folder_browser_history(app, current_entry)
        _clear_radio_folder_browser_forward_history(app)
    _set_radio_folder_browser_mode_and_path(app, next_entry[0], next_entry[1])
    return _reload_radio_folder_browser(app, announce_text=announce_text)


def _folder_browser_entries_for_path(app, mode, target_dir):
    entries = []
    path = str(target_dir or "").strip()
    if not path or not os.path.isdir(path):
        return entries
    try:
        names = sorted(os.listdir(path), key=str.lower)
    except Exception:
        return entries
    dir_entries = []
    file_entries = []
    for name in names:
        entry_path = os.path.join(path, name)
        if os.path.isdir(entry_path):
            dir_entries.append(entry_path)
            continue
        if mode == "playlists":
            if os.path.isfile(entry_path) and str(name).lower().endswith(".m3u"):
                file_entries.append(entry_path)
        elif mode == "system":
            if os.path.isfile(entry_path) and _is_audio_file_path(entry_path):
                file_entries.append(entry_path)
        else:
            if os.path.isfile(entry_path):
                file_entries.append(entry_path)
    entries.extend(dir_entries)
    entries.extend(file_entries)
    return entries


def _set_folder_browser_entries(app, mode, entries):
    if mode == "playlists":
        app.radio_playlist_files_entries = list(entries)
    elif mode == "system":
        app.radio_system_folder_entries = list(entries)
    else:
        app.radio_recordings_entries = list(entries)


def _current_folder_browser_entries(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode == "playlists":
        return list(getattr(app, "radio_playlist_files_entries", []) or [])
    if mode == "system":
        return list(getattr(app, "radio_system_folder_entries", []) or [])
    return list(getattr(app, "radio_recordings_entries", []) or [])


def _reload_radio_folder_browser(app, *, announce_text=""):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    target_dir = _current_radio_folder_browser_path(app)
    if not target_dir:
        target_dir = _radio_folder_browser_root_dir(app, mode)
    entries = _folder_browser_entries_for_path(app, mode, target_dir)
    _set_current_radio_folder_browser_path(app, target_dir)
    _set_folder_browser_entries(app, mode, entries)
    refresh_radio_recordings_browser_ui(app)
    if announce_text:
        _recording_status_text(app, announce_text)
    return True


def _selected_radio_folder_browser_path(app):
    entries = _current_folder_browser_entries(app)
    idx = _selected_radio_folder_browser_index(app)
    if idx is None or idx < 0 or idx >= len(entries):
        return ""
    return str(entries[idx] or "").strip()


def _radio_folder_browser_index_from_event(app, event):
    listbox = getattr(app, "radio_recordings_listbox", None)
    if listbox is None:
        return -1
    try:
        idx = int(listbox.nearest(event.y))
    except Exception:
        idx = -1
    entries = _current_folder_browser_entries(app)
    if idx < 0 or idx >= len(entries):
        return -1
    return idx


def _select_radio_folder_browser_index(app, idx):
    listbox = getattr(app, "radio_recordings_listbox", None)
    if listbox is None or idx < 0:
        return
    try:
        listbox.selection_clear(0, "end")
    except Exception:
        pass
    try:
        listbox.selection_set(idx)
        listbox.activate(idx)
        listbox.focus_set()
    except Exception:
        pass


def refresh_radio_recordings_browser_ui(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode == "playlists":
        entries = list(getattr(app, "radio_playlist_files_entries", []) or [])
        title = "Playlistordner"
        status_text = _playlist_folder_status_text(app)
    elif mode == "system":
        entries = list(getattr(app, "radio_system_folder_entries", []) or [])
        folder_path = str(getattr(app, "radio_system_folder_path", "") or "").strip()
        folder_name = os.path.basename(folder_path) or folder_path or "-"
        title = f"System - {folder_name}"
        status_text = _system_folder_status_text(app)
    else:
        entries = list(getattr(app, "radio_recordings_entries", []) or [])
        title = "Aufnahmeordner"
        status_text = _recordings_status_text(app)
    for target in _radio_targets(app):
        listbox = getattr(target, "radio_recordings_listbox", None)
        status_var = getattr(target, "radio_recordings_status_var", None)
        title_var = getattr(target, "radio_folder_browser_title_var", None)
        path_var = getattr(target, "radio_folder_browser_path_var", None)
        back_button = getattr(target, "radio_folder_browser_back_button", None)
        forward_button = getattr(target, "radio_folder_browser_forward_button", None)
        up_button = getattr(target, "radio_folder_browser_up_button", None)
        open_path_button = getattr(
            target, "radio_folder_browser_open_path_button", None
        )
        if title_var is not None:
            try:
                title_var.set(title)
            except Exception:
                pass
        if path_var is not None:
            try:
                path_var.set(_current_radio_folder_browser_path(app))
            except Exception:
                pass
        if status_var is not None:
            try:
                status_var.set(status_text)
            except Exception:
                pass
        try:
            if back_button is not None:
                back_button.configure(
                    state=(
                        "normal"
                        if bool(
                            getattr(app, "radio_folder_browser_back_history", []) or []
                        )
                        else "disabled"
                    )
                )
        except Exception:
            pass
        try:
            if forward_button is not None:
                forward_button.configure(
                    state=(
                        "normal"
                        if bool(
                            getattr(app, "radio_folder_browser_forward_history", [])
                            or []
                        )
                        else "disabled"
                    )
                )
        except Exception:
            pass
        try:
            if up_button is not None:
                up_button.configure(
                    state=(
                        "normal"
                        if _radio_folder_browser_parent_path(app)
                        else "disabled"
                    )
                )
        except Exception:
            pass
        try:
            if open_path_button is not None:
                open_path_button.configure(
                    state=(
                        "normal"
                        if os.path.isdir(_current_radio_folder_browser_path(app))
                        and has_cmd("xdg-open")
                        else "disabled"
                    )
                )
        except Exception:
            pass
        if listbox is not None:
            try:
                listbox.delete(0, "end")
                for path in entries:
                    listbox.insert("end", _playlist_label_for_path(path))
            except Exception:
                pass


def open_current_radio_folder_browser_path(app):
    path = _current_radio_folder_browser_path(app)
    if not path or not os.path.isdir(path):
        _recording_status_text(app, "Ordnerpfad nicht verfügbar.")
        return False
    if not has_cmd("xdg-open"):
        _recording_status_text(app, "Systemlink öffnen nicht verfügbar.")
        return False
    try:
        subprocess.Popen(
            ["xdg-open", path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _recording_status_text(
            app,
            f"Ordnerpfad geöffnet: {os.path.basename(path) or path}",
        )
        return True
    except Exception:
        return False


def navigate_radio_folder_browser_back(app):
    history = list(getattr(app, "radio_folder_browser_back_history", []) or [])
    if not history:
        _recording_status_text(app, "Kein vorheriger Ordner vorhanden.")
        refresh_radio_recordings_browser_ui(app)
        return False
    current_entry = _current_radio_folder_browser_entry(app)
    target_mode, target_dir = history.pop()
    forward = list(getattr(app, "radio_folder_browser_forward_history", []) or [])
    if current_entry != (target_mode, target_dir):
        forward.append(current_entry)
    app.radio_folder_browser_back_history = history
    app.radio_folder_browser_forward_history = forward
    return _navigate_radio_folder_browser_to(
        app,
        target_mode,
        target_dir,
        announce_text=f"Zurück: {os.path.basename(target_dir) or target_dir or '-'}",
        push_history=False,
    )


def navigate_radio_folder_browser_forward(app):
    history = list(getattr(app, "radio_folder_browser_forward_history", []) or [])
    if not history:
        _recording_status_text(app, "Kein nächster Ordner vorhanden.")
        refresh_radio_recordings_browser_ui(app)
        return False
    current_entry = _current_radio_folder_browser_entry(app)
    target_mode, target_dir = history.pop()
    back = list(getattr(app, "radio_folder_browser_back_history", []) or [])
    if current_entry != (target_mode, target_dir):
        back.append(current_entry)
    app.radio_folder_browser_back_history = back
    app.radio_folder_browser_forward_history = history
    return _navigate_radio_folder_browser_to(
        app,
        target_mode,
        target_dir,
        announce_text=f"Weiter: {os.path.basename(target_dir) or target_dir or '-'}",
        push_history=False,
    )


def navigate_radio_folder_browser_up(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    parent_path = _radio_folder_browser_parent_path(app)
    if not parent_path:
        _recording_status_text(app, "Kein übergeordneter Ordner vorhanden.")
        refresh_radio_recordings_browser_ui(app)
        return False
    title = {
        "recordings": "Ordner höher",
        "playlists": "Playlistordner höher",
        "system": "Systemordner höher",
    }.get(mode, "Ordner höher")
    return _navigate_radio_folder_browser_to(
        app,
        mode,
        parent_path,
        announce_text=f"{title}: {os.path.basename(parent_path) or parent_path}",
    )


def start_radio_folder_browser_drag(app, event):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    app.radio_folder_browser_drag_source_index = -1
    app.radio_folder_browser_drag_source_path = ""
    if mode != "recordings":
        return None
    idx = _radio_folder_browser_index_from_event(app, event)
    if idx < 0:
        return None
    entries = _current_folder_browser_entries(app)
    path = str(entries[idx] or "").strip()
    if not path or not os.path.isfile(path):
        return None
    app.radio_folder_browser_drag_source_index = idx
    app.radio_folder_browser_drag_source_path = path
    _select_radio_folder_browser_index(app, idx)
    return None


def track_radio_folder_browser_drag(app, event):
    source_path = str(
        getattr(app, "radio_folder_browser_drag_source_path", "") or ""
    ).strip()
    if not source_path:
        return None
    idx = _radio_folder_browser_index_from_event(app, event)
    if idx >= 0:
        _select_radio_folder_browser_index(app, idx)
    return None


def cancel_radio_folder_browser_drag(app, _event=None):
    app.radio_folder_browser_drag_source_index = -1
    app.radio_folder_browser_drag_source_path = ""
    return None


def finish_radio_folder_browser_drag(app, event):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    source_path = str(
        getattr(app, "radio_folder_browser_drag_source_path", "") or ""
    ).strip()
    source_index = int(getattr(app, "radio_folder_browser_drag_source_index", -1) or -1)
    try:
        app.radio_folder_browser_drag_source_index = -1
        app.radio_folder_browser_drag_source_path = ""
    except Exception:
        pass
    if mode != "recordings" or not source_path or not os.path.isfile(source_path):
        return None
    target_index = _radio_folder_browser_index_from_event(app, event)
    if target_index < 0 or target_index == source_index:
        return None
    entries = _current_folder_browser_entries(app)
    if target_index >= len(entries):
        return None
    target_path = str(entries[target_index] or "").strip()
    if not target_path or not os.path.isdir(target_path):
        return None
    destination_path = os.path.join(target_path, os.path.basename(source_path))
    if os.path.abspath(destination_path) == os.path.abspath(source_path):
        return None
    if os.path.exists(destination_path):
        _recording_status_text(app, "Zieldatei existiert bereits.")
        return None
    try:
        shutil.move(source_path, destination_path)
    except Exception:
        _recording_status_text(app, "Datei konnte nicht verschoben werden.")
        return None
    last_record_path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    if last_record_path == source_path:
        app.radio_last_record_path = destination_path
    _reload_radio_folder_browser(
        app,
        announce_text=(
            f"Verschoben: {os.path.basename(source_path)} -> "
            f"{os.path.basename(target_path) or target_path}"
        ),
    )
    refresh_radio_recording_ui(app)
    return "break"


def refresh_radio_playlist_ui(app):
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    for target in _radio_targets(app):
        listbox = getattr(target, "radio_playlist_listbox", None)
        status_var = getattr(target, "radio_playlist_status_var", None)
        add_button = getattr(target, "radio_playlist_add_button", None)
        play_selected_button = getattr(
            target, "radio_playlist_play_selected_button", None
        )
        remove_button = getattr(target, "radio_playlist_remove_button", None)
        clear_button = getattr(target, "radio_playlist_clear_button", None)
        save_button = getattr(target, "radio_playlist_save_button", None)
        load_button = getattr(target, "radio_playlist_load_button", None)
        folder_button = getattr(target, "radio_playlist_folder_button", None)
        system_button = getattr(target, "radio_system_folder_button", None)
        if status_var is not None:
            try:
                status_var.set(_playlist_status_text(app))
            except Exception:
                pass
        if listbox is not None:
            try:
                current = listbox.curselection()
                selected_idx = int(current[0]) if current else None
            except Exception:
                selected_idx = None
            try:
                listbox.delete(0, "end")
                for path in entries:
                    listbox.insert("end", _playlist_label_for_path(path))
                if (
                    selected_idx is not None
                    and 0 <= selected_idx < len(entries)
                    and len(entries) > 0
                ):
                    listbox.selection_set(selected_idx)
                    listbox.activate(selected_idx)
            except Exception:
                pass
        has_entries = bool(entries)
        try:
            if add_button is not None:
                add_button.configure(state="normal")
        except Exception:
            pass
        try:
            if play_selected_button is not None:
                play_selected_button.configure(
                    state="normal" if has_entries and has_cmd("mpv") else "disabled"
                )
        except Exception:
            pass
        try:
            if remove_button is not None:
                remove_button.configure(state="normal" if has_entries else "disabled")
        except Exception:
            pass
        try:
            if clear_button is not None:
                clear_button.configure(state="normal" if has_entries else "disabled")
        except Exception:
            pass
        try:
            if save_button is not None:
                save_button.configure(state="normal" if has_entries else "disabled")
        except Exception:
            pass
        try:
            if load_button is not None:
                load_button.configure(state="normal")
        except Exception:
            pass
        try:
            if folder_button is not None:
                folder_button.configure(state="normal")
        except Exception:
            pass
        try:
            if system_button is not None:
                system_button.configure(state="normal")
        except Exception:
            pass
    refresh_radio_source_ui(app)


def refresh_radio_recording_ui(app):
    active = False
    proc = getattr(app, "radio_record_proc", None)
    try:
        active = proc is not None and proc.poll() is None
    except Exception:
        active = proc is not None
    for target in _radio_targets(app):
        start_button = getattr(target, "radio_record_start_button", None)
        stop_button = getattr(target, "radio_record_stop_button", None)
        transport_button = getattr(target, "radio_record_transport_button", None)
        panel_button = getattr(target, "radio_record_panel_button", None)
        choose_button = getattr(target, "radio_record_folder_button", None)
        open_button = getattr(target, "radio_record_open_folder_button", None)
        open_last_button = getattr(target, "radio_record_open_last_button", None)
        play_last_button = getattr(target, "radio_record_play_last_button", None)
        dir_var = getattr(target, "radio_record_dir_var", None)
        file_var = getattr(target, "radio_record_file_var", None)
        last_record_path = str(getattr(app, "radio_last_record_path", "") or "").strip()
        last_record_exists = bool(last_record_path and os.path.isfile(last_record_path))
        recordings_dir = _radio_recordings_dir(app)
        if dir_var is not None:
            try:
                dir_var.set(_recording_dir_text(app))
            except Exception:
                pass
        if file_var is not None:
            try:
                file_var.set(_recording_file_text(app))
            except Exception:
                pass
        try:
            if start_button is not None:
                start_button.configure(
                    state=(
                        "normal"
                        if (not active and radio_recording_available(app))
                        else "disabled"
                    )
                )
        except Exception:
            pass
        try:
            if stop_button is not None:
                stop_button.configure(state="normal" if active else "disabled")
        except Exception:
            pass
        try:
            if transport_button is not None:
                if radio_recording_available(app) or active:
                    transport_button.configure(state="normal", text="⏺")
                    if active:
                        _schedule_record_button_blink(target)
                    else:
                        _stop_record_button_blink(target)
                        transport_button.configure(
                            **_record_button_colors(False, False)
                        )
                else:
                    _stop_record_button_blink(target)
                    transport_button.configure(
                        state="disabled",
                        text="⏺",
                        **_record_button_colors(False, False),
                    )
        except Exception:
            pass
        try:
            if panel_button is not None:
                panel_button.configure(
                    text=("Aufnahme stoppen" if active else "Aufnahme starten"),
                    state=(
                        "normal"
                        if (radio_recording_available(app) or active)
                        else "disabled"
                    ),
                )
        except Exception:
            pass
        try:
            if choose_button is not None:
                choose_button.configure(state="normal")
        except Exception:
            pass
        try:
            if open_button is not None:
                open_button.configure(
                    state="normal" if os.path.isdir(recordings_dir) else "disabled"
                )
        except Exception:
            pass
        try:
            if open_last_button is not None:
                open_last_button.configure(
                    state="normal" if last_record_exists else "disabled"
                )
        except Exception:
            pass
        try:
            if play_last_button is not None:
                play_last_button.configure(
                    state="normal" if last_record_exists else "disabled"
                )
        except Exception:
            pass


def _recording_file_path(app, station):
    name = str((station or {}).get("name", "") or "radio").strip()
    raw_title = str(
        getattr(getattr(app, "radio_title_var", None), "get", lambda: "")() or ""
    ).strip()
    title = raw_title
    if title.lower().startswith("titel:"):
        title = title.split(":", 1)[1].strip()
    invalid_titles = {
        "",
        "-",
        _tr(app, "radio_header_title_idle", "Titel: -")
        .replace("Titel:", "", 1)
        .strip()
        .lower(),
        _tr(app, "radio_header_title_connecting", "Titel: verbinde...")
        .replace("Titel:", "", 1)
        .strip()
        .lower(),
        _tr(app, "radio_header_title_error", "Titel: Fehler / keine Verbindung")
        .replace("Titel:", "", 1)
        .strip()
        .lower(),
    }
    cleaned_title = title.strip()
    if cleaned_title.lower() in invalid_titles:
        cleaned_title = ""
    filename_parts = [_slugify_station_id(name)]
    if cleaned_title:
        title_part = cleaned_title
        artist_part = ""
        if " - " in cleaned_title:
            artist_candidate, title_candidate = cleaned_title.split(" - ", 1)
            artist_candidate = artist_candidate.strip()
            title_candidate = title_candidate.strip()
            if artist_candidate and title_candidate:
                artist_part = artist_candidate
                title_part = title_candidate
        filename_parts.append(_slugify_station_id(title_part))
        if artist_part:
            filename_parts.append(_slugify_station_id(artist_part))
    filename = "_".join(filename_parts) + ".mp3"
    target_dir = _radio_recordings_dir(app)
    return os.path.join(target_dir, filename)


def _recording_command(stream_url, output_path):
    return [
        "ffmpeg",
        "-y",
        "-i",
        str(stream_url or "").strip(),
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "192k",
        output_path,
    ]


def choose_radio_recordings_dir(app):
    initial_dir = _radio_recordings_dir(app)
    folder = filedialog.askdirectory(
        title=app.tr("radio_recordings_dir_dialog_title", "Aufnahmeordner wählen"),
        initialdir=initial_dir,
    )
    if not folder:
        return False
    app.radio_recordings_dir = str(folder).strip()
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["recordings_dir"] = app.radio_recordings_dir
    app.radio_settings = settings
    save_radio_settings(app)
    _recording_status_text(app, "Aufnahmeordner aktualisiert.")
    refresh_radio_recording_ui(app)
    open_radio_recordings_dir(app)
    return True


def open_radio_recordings_dir(app):
    target_dir = _radio_recordings_dir(app)
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception:
        return False
    return _navigate_radio_folder_browser_to(
        app,
        "recordings",
        target_dir,
        announce_text=f"Aufnahmeordner geladen: {os.path.basename(target_dir) or target_dir}",
    )


def open_radio_playlists_dir(app):
    target_dir = _radio_playlists_dir(app)
    try:
        os.makedirs(target_dir, exist_ok=True)
    except Exception:
        return False
    app.radio_playlists_dir = target_dir
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlists_dir"] = target_dir
    current_playlist_path = str(getattr(app, "radio_playlist_path", "") or "").strip()
    old_default_path = os.path.join(_default_recordings_dir(app), "radio_playlist.json")
    if not current_playlist_path or current_playlist_path == old_default_path:
        app.radio_playlist_path = os.path.join(target_dir, "radio_playlist.m3u")
        settings["playlist_path"] = app.radio_playlist_path
    app.radio_settings = settings
    save_radio_settings(app)
    return _navigate_radio_folder_browser_to(
        app,
        "playlists",
        target_dir,
        announce_text=f"Playlistordner geladen: {os.path.basename(target_dir) or target_dir}",
    )


def open_radio_system_dir(app):
    initial_dir = str(getattr(app, "radio_system_folder_path", "") or "").strip()
    if not initial_dir:
        initial_dir = os.path.expanduser("~")
    folder = filedialog.askdirectory(
        title=_tr(app, "radio_system_dir_dialog_title", "Systemordner wählen"),
        initialdir=initial_dir,
    )
    if not folder:
        return False
    target_dir = str(folder).strip()
    app.radio_system_folder_path = target_dir
    return _navigate_radio_folder_browser_to(
        app,
        "system",
        target_dir,
        announce_text=f"Systemordner geladen: {os.path.basename(target_dir) or target_dir}",
    )


def _selected_radio_folder_browser_index(app):
    try:
        context_idx = int(getattr(app, "radio_folder_browser_context_index", -1))
    except Exception:
        context_idx = -1
    if context_idx >= 0:
        return context_idx
    selected = _selected_radio_recording_index(app)
    if selected is None:
        return -1
    return int(selected)


def _load_radio_playlist_path(app, path):
    entries = _read_m3u_playlist(path)
    if not entries:
        _recording_status_text(app, "Playlist-Datei ist ungültig.")
        return False
    app.radio_playlist_entries = entries
    app.radio_playlist_path = str(path).strip()
    app.radio_playlists_dir = os.path.dirname(
        app.radio_playlist_path
    ) or _radio_playlists_dir(app)
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlist_entries"] = list(entries)
    settings["playlist_path"] = app.radio_playlist_path
    settings["playlists_dir"] = app.radio_playlists_dir
    app.radio_settings = settings
    save_radio_settings(app)
    refresh_radio_playlist_ui(app)
    _recording_status_text(app, f"Playlist geladen: {os.path.basename(path)}")
    return True


def _start_loaded_radio_playlist(app):
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    if not entries:
        return False
    listbox = getattr(app, "radio_playlist_listbox", None)
    if listbox is not None:
        try:
            listbox.selection_clear(0, "end")
        except Exception:
            pass
        try:
            listbox.selection_set(0)
            listbox.activate(0)
        except Exception:
            pass
    app.radio_playlist_index = 0
    app.radio_playback_mode = "playlist"
    app.radio_local_media_path = str(entries[0]).strip()
    return play_selected_radio_playlist_entry(app)


def open_last_radio_recording(app):
    path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    if not path or not os.path.isfile(path):
        _recording_status_text(app, "Keine letzte Aufnahme vorhanden.")
        refresh_radio_recording_ui(app)
        return False
    if has_cmd("xdg-open"):
        try:
            subprocess.Popen(
                ["xdg-open", path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            _recording_status_text(
                app, f"Letzte Aufnahme geöffnet: {os.path.basename(path)}"
            )
            return True
        except Exception:
            return False
    return False


def _selected_radio_recording_index(app):
    listbox = getattr(app, "radio_recordings_listbox", None)
    if listbox is None:
        return None
    try:
        selected = listbox.curselection()
    except Exception:
        return None
    if not selected:
        return None
    try:
        return int(selected[0])
    except Exception:
        return None


def play_selected_radio_recording_file(app, _event=None):
    entries = list(getattr(app, "radio_recordings_entries", []) or [])
    idx = _selected_radio_recording_index(app)
    if idx is None or idx < 0 or idx >= len(entries):
        _recording_status_text(app, "Keine Aufnahme-Datei ausgewählt.")
        return False
    path = str(entries[idx] or "").strip()
    if not path or not os.path.isfile(path):
        _recording_status_text(app, "Aufnahme-Datei nicht gefunden.")
        return False
    app.radio_playback_mode = "recording"
    app.radio_local_media_path = path
    return _play_local_audio_file(
        app,
        path,
        station_name="Aufnahmeordner",
        title_text=f"Datei: {os.path.basename(path)}",
    )


def open_selected_radio_folder_browser_entry(app, _event=None):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode == "playlists":
        entries = list(getattr(app, "radio_playlist_files_entries", []) or [])
        idx = _selected_radio_folder_browser_index(app)
        if idx is None or idx < 0 or idx >= len(entries):
            _recording_status_text(app, "Keine Playlist-Datei ausgewählt.")
            return False
        path = str(entries[idx] or "").strip()
        if os.path.isdir(path):
            return _navigate_radio_folder_browser_to(
                app,
                "playlists",
                path,
                announce_text=f"Playlistordner geöffnet: {os.path.basename(path) or path}",
            )
        if not path or not os.path.isfile(path):
            _recording_status_text(app, "Playlist-Datei nicht gefunden.")
            return False
        if not _load_radio_playlist_path(app, path):
            return False
        return _start_loaded_radio_playlist(app)
    if mode == "system":
        entries = list(getattr(app, "radio_system_folder_entries", []) or [])
        idx = _selected_radio_folder_browser_index(app)
        if idx is None or idx < 0 or idx >= len(entries):
            _recording_status_text(app, "Keine System-Datei ausgewählt.")
            return False
        path = str(entries[idx] or "").strip()
        if os.path.isdir(path):
            return _navigate_radio_folder_browser_to(
                app,
                "system",
                path,
                announce_text=f"Systemordner geöffnet: {os.path.basename(path) or path}",
            )
        if not path or not os.path.isfile(path):
            _recording_status_text(app, "System-Datei nicht gefunden.")
            return False
        app.radio_playback_mode = "file"
        app.radio_local_media_path = path
        return _play_local_audio_file(
            app,
            path,
            station_name="Systemordner",
            title_text=f"Datei: {os.path.basename(path)}",
        )
    path = _selected_radio_folder_browser_path(app)
    if os.path.isdir(path):
        return _navigate_radio_folder_browser_to(
            app,
            "recordings",
            path,
            announce_text=f"Ordner geöffnet: {os.path.basename(path) or path}",
        )
    return play_selected_radio_recording_file(app, _event)


def show_radio_folder_browser_context_menu(app, event):
    menu = getattr(app, "radio_folder_browser_menu", None)
    listbox = getattr(app, "radio_recordings_listbox", None)
    if menu is None or listbox is None:
        return None
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    try:
        idx = int(listbox.nearest(event.y))
    except Exception:
        idx = -1
    entries = (
        list(getattr(app, "radio_recordings_entries", []) or [])
        if mode == "recordings"
        else (
            list(getattr(app, "radio_playlist_files_entries", []) or [])
            if mode == "playlists"
            else list(getattr(app, "radio_system_folder_entries", []) or [])
        )
    )
    if idx >= 0 and idx < len(entries):
        try:
            listbox.selection_clear(0, "end")
        except Exception:
            pass
        try:
            listbox.selection_set(idx)
            listbox.activate(idx)
            listbox.focus_set()
        except Exception:
            pass
        app.radio_folder_browser_context_index = idx
    else:
        app.radio_folder_browser_context_index = -1
    try:
        menu.delete(0, "end")
    except Exception:
        pass
    selected_path = _selected_radio_folder_browser_path(app)
    selected_is_dir = bool(selected_path and os.path.isdir(selected_path))
    selected_is_file = bool(selected_path and os.path.isfile(selected_path))
    try:
        if mode == "recordings":
            if selected_is_file:
                menu.add_command(
                    label="Zur Playlist hinzufügen",
                    command=lambda: add_selected_radio_folder_browser_entry_to_playlist(
                        app
                    ),
                )
                menu.add_command(
                    label="Aufnahme löschen",
                    command=lambda: delete_selected_radio_folder_browser_entry(app),
                )
                menu.add_command(
                    label="Umbenennen",
                    command=lambda: rename_selected_radio_folder_browser_entry(app),
                )
            elif selected_is_dir:
                menu.add_command(
                    label="Ordner löschen",
                    command=lambda: delete_selected_radio_folder_browser_entry(app),
                )
                menu.add_command(
                    label="Umbenennen",
                    command=lambda: rename_selected_radio_folder_browser_entry(app),
                )
            if selected_is_file or selected_is_dir:
                menu.add_separator()
            menu.add_command(
                label="Ordner erstellen",
                command=lambda: create_radio_folder_browser_subfolder(app),
            )
            menu.add_command(
                label="Aufnahmeordner festlegen",
                command=lambda: choose_radio_recordings_dir(app),
            )
        elif mode == "playlists":
            if selected_is_file:
                menu.add_command(
                    label="Playlist starten",
                    command=lambda: start_selected_radio_folder_browser_playlist(app),
                )
        elif selected_is_file:
            menu.add_command(
                label="Zur Playlist hinzufügen",
                command=lambda: add_selected_radio_folder_browser_entry_to_playlist(
                    app
                ),
            )
    except Exception:
        pass
    try:
        if int(menu.index("end")) < 0:
            return None
    except Exception:
        pass
    show_fn = getattr(app, "_show_context_menu", None)
    if callable(show_fn):
        return show_fn(menu, event)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass
    return "break"


def add_selected_radio_folder_browser_entry_to_playlist(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode not in {"recordings", "system"}:
        _recording_status_text(
            app, "Nur Aufnahmen können zur Playlist hinzugefügt werden."
        )
        return False
    entries = (
        list(getattr(app, "radio_recordings_entries", []) or [])
        if mode == "recordings"
        else list(getattr(app, "radio_system_folder_entries", []) or [])
    )
    idx = _selected_radio_folder_browser_index(app)
    app.radio_folder_browser_context_index = -1
    if idx < 0 or idx >= len(entries):
        _recording_status_text(
            app,
            (
                "Keine Aufnahme-Datei ausgewählt."
                if mode == "recordings"
                else "Keine System-Datei ausgewählt."
            ),
        )
        return False
    path = str(entries[idx] or "").strip()
    if not path or not os.path.isfile(path):
        _recording_status_text(
            app,
            (
                "Aufnahme-Datei nicht gefunden."
                if mode == "recordings"
                else "System-Datei nicht gefunden."
            ),
        )
        return False
    playlist_entries = list(getattr(app, "radio_playlist_entries", []) or [])
    if path not in playlist_entries:
        playlist_entries.append(path)
        app.radio_playlist_entries = playlist_entries
        settings = dict(getattr(app, "radio_settings", {}) or {})
        settings["playlist_entries"] = list(playlist_entries)
        app.radio_settings = settings
        save_radio_settings(app)
        refresh_radio_playlist_ui(app)
    _recording_status_text(
        app,
        f"Zur Playlist hinzugefügt: {_playlist_label_for_path(path)}",
    )
    return True


def create_radio_folder_browser_subfolder(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode != "recordings":
        _recording_status_text(app, "Ordner können hier nicht erstellt werden.")
        return False
    base_path = _current_radio_folder_browser_path(app)
    if not base_path or not os.path.isdir(base_path):
        _recording_status_text(app, "Aufnahmeordner nicht verfügbar.")
        return False
    folder_name = simpledialog.askstring(
        "Ordner erstellen",
        "Ordnername:",
        parent=getattr(app, "winfo_toplevel", lambda: None)(),
    )
    folder_name = str(folder_name or "").strip()
    app.radio_folder_browser_context_index = -1
    if not folder_name:
        return False
    if folder_name in {".", ".."} or "/" in folder_name or "\\" in folder_name:
        _recording_status_text(app, "Ungültiger Ordnername.")
        return False
    target_path = os.path.join(base_path, folder_name)
    if os.path.exists(target_path):
        _recording_status_text(app, "Ordner existiert bereits.")
        return False
    try:
        os.makedirs(target_path, exist_ok=False)
    except Exception:
        _recording_status_text(app, "Ordner konnte nicht erstellt werden.")
        return False
    _reload_radio_folder_browser(
        app,
        announce_text=f"Ordner erstellt: {os.path.basename(target_path) or target_path}",
    )
    return True


def delete_selected_radio_folder_browser_entry(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode != "recordings":
        _recording_status_text(app, "Löschen ist hier nicht verfügbar.")
        return False
    path = _selected_radio_folder_browser_path(app)
    app.radio_folder_browser_context_index = -1
    if not path or not os.path.exists(path):
        _recording_status_text(app, "Kein Eintrag ausgewählt.")
        return False
    name = os.path.basename(path) or path
    if os.path.isdir(path):
        if not messagebox.askyesno(
            "Ordner löschen",
            f"Soll der Ordner '{name}' mit Inhalt gelöscht werden?",
            parent=getattr(app, "winfo_toplevel", lambda: None)(),
        ):
            return False
        try:
            shutil.rmtree(path)
        except Exception:
            _recording_status_text(app, "Ordner konnte nicht gelöscht werden.")
            return False
        _reload_radio_folder_browser(app, announce_text=f"Ordner gelöscht: {name}")
        return True
    if not messagebox.askyesno(
        "Aufnahme löschen",
        f"Soll die Aufnahme '{name}' gelöscht werden?",
        parent=getattr(app, "winfo_toplevel", lambda: None)(),
    ):
        return False
    try:
        os.remove(path)
    except Exception:
        _recording_status_text(app, "Aufnahme konnte nicht gelöscht werden.")
        return False
    last_record_path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    if last_record_path == path:
        app.radio_last_record_path = ""
    _reload_radio_folder_browser(app, announce_text=f"Aufnahme gelöscht: {name}")
    refresh_radio_recording_ui(app)
    return True


def rename_selected_radio_folder_browser_entry(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode != "recordings":
        _recording_status_text(app, "Umbenennen ist hier nicht verfügbar.")
        return False
    path = _selected_radio_folder_browser_path(app)
    app.radio_folder_browser_context_index = -1
    if not path or not os.path.exists(path):
        _recording_status_text(app, "Kein Eintrag ausgewählt.")
        return False
    current_name = os.path.basename(path) or path
    new_name = simpledialog.askstring(
        "Umbenennen",
        "Neuer Name:",
        initialvalue=current_name,
        parent=getattr(app, "winfo_toplevel", lambda: None)(),
    )
    new_name = str(new_name or "").strip()
    if not new_name or new_name == current_name:
        return False
    if new_name in {".", ".."} or "/" in new_name or "\\" in new_name:
        _recording_status_text(app, "Ungültiger Name.")
        return False
    target_path = os.path.join(os.path.dirname(path), new_name)
    if os.path.exists(target_path):
        _recording_status_text(app, "Zielname existiert bereits.")
        return False
    try:
        os.rename(path, target_path)
    except Exception:
        _recording_status_text(app, "Eintrag konnte nicht umbenannt werden.")
        return False
    last_record_path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    if last_record_path == path:
        app.radio_last_record_path = target_path
    _reload_radio_folder_browser(
        app,
        announce_text=f"Umbenannt: {current_name} -> {new_name}",
    )
    refresh_radio_recording_ui(app)
    return True


def start_selected_radio_folder_browser_playlist(app):
    mode = str(getattr(app, "radio_folder_browser_mode", "recordings") or "recordings")
    if mode != "playlists":
        _recording_status_text(app, "Keine Playlist-Datei ausgewählt.")
        return False
    app.radio_folder_browser_context_index = -1
    return open_selected_radio_folder_browser_entry(app)


def _play_local_audio_file(app, path, *, station_name, title_text):
    path = str(path or "").strip()
    if not path or not os.path.isfile(path):
        return False
    try:
        volume = int(getattr(app, "radio_volume_var").get() or 50)
    except Exception:
        volume = 50

    def worker():
        with _radio_playback_lock(app):
            stop_radio_playback(app, async_mode=False)
            ipc_path = _radio_ipc_path(app)
            app.radio_ipc_path = ipc_path
            _cleanup_radio_ipc_path(app)
            cmd = _mpv_command(
                volume,
                path,
                ipc_path,
                radio_eq_filter_spec(app),
            )
            _schedule_ui(app, lambda: _set_radio_light(app, "yellow"))
            _schedule_ui(app, lambda: _set_radio_station_text(app, station_name))
            _schedule_ui(app, lambda: _set_radio_title_text(app, title_text))
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:
                _schedule_ui(
                    app,
                    lambda err=str(exc): _recording_status_text(
                        app, f"Mitschnitt konnte nicht abgespielt werden: {err}"
                    ),
                )
                return

            def announce():
                app.radio_proc = proc
                app.radio_stop_requested = False
                app.radio_current_station = None
                app.radio_current_station_id = ""
                refresh_radio_source_ui(app)
                _set_radio_light(app, "green")
                set_radio_status(app, f"Spielt Mitschnitt: {os.path.basename(path)}")

            _schedule_ui(app, announce)

            threading.Thread(
                target=_wait_for_radio_process,
                args=(app, proc, os.path.basename(path)),
                daemon=True,
            ).start()
            threading.Thread(
                target=_poll_radio_metadata,
                args=(app, proc),
                daemon=True,
            ).start()

    threading.Thread(target=worker, daemon=True).start()
    return True


def play_last_radio_recording(app):
    path = str(getattr(app, "radio_last_record_path", "") or "").strip()
    if not path or not os.path.isfile(path):
        _recording_status_text(app, "Keine letzte Aufnahme vorhanden.")
        refresh_radio_recording_ui(app)
        return False
    app.radio_playback_mode = "recording"
    app.radio_local_media_path = path
    return _play_local_audio_file(
        app,
        path,
        station_name="Letzter Mitschnitt",
        title_text=f"Datei: {os.path.basename(path)}",
    )


def play_radio_file(app):
    initial_dir = _radio_recordings_dir(app)
    path = filedialog.askopenfilename(
        title=app.tr("radio_audio_file_dialog_title", "Audiodatei auswählen"),
        initialdir=initial_dir,
        filetypes=(
            ("Audio-Dateien", "*.mp3 *.m4a *.aac *.ogg *.wav *.flac *.opus"),
            ("Alle Dateien", "*.*"),
        ),
    )
    if not path:
        return False
    app.radio_playback_mode = "file"
    app.radio_local_media_path = str(path).strip()
    app.radio_playlist_index = -1
    return _play_local_audio_file(
        app,
        path,
        station_name="Lokale Datei",
        title_text=f"Datei: {os.path.basename(path)}",
    )


def add_radio_playlist_files(app):
    initial_dir = _radio_recordings_dir(app)
    paths = filedialog.askopenfilenames(
        title=_tr(app, 
            "radio_playlist_add_files_dialog_title",
            "Dateien zur Playlist hinzufügen",
        ),
        initialdir=initial_dir,
        filetypes=(
            ("Audio-Dateien", "*.mp3 *.m4a *.aac *.ogg *.wav *.flac *.opus"),
            ("Alle Dateien", "*.*"),
        ),
    )
    if not paths:
        return False
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    known = {str(item).strip() for item in entries}
    added = 0
    for path in paths:
        value = str(path or "").strip()
        if not value or value in known:
            continue
        entries.append(value)
        known.add(value)
        added += 1
    app.radio_playlist_entries = entries
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlist_entries"] = list(entries)
    app.radio_settings = settings
    save_radio_settings(app)
    refresh_radio_playlist_ui(app)
    if added:
        _recording_status_text(app, f"Playlist erweitert: {added} Datei(en).")
        return True
    _recording_status_text(app, "Keine neuen Dateien zur Playlist hinzugefügt.")
    return False


def _selected_radio_playlist_index(app):
    listbox = getattr(app, "radio_playlist_listbox", None)
    if listbox is None:
        return None
    try:
        selected = listbox.curselection()
    except Exception:
        return None
    if not selected:
        return None
    try:
        return int(selected[0])
    except Exception:
        return None


def play_selected_radio_playlist_entry(app, _event=None):
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    idx = _selected_radio_playlist_index(app)
    if idx is None or idx < 0 or idx >= len(entries):
        _recording_status_text(app, "Kein Playlist-Eintrag ausgewählt.")
        refresh_radio_playlist_ui(app)
        return False
    path = str(entries[idx] or "").strip()
    if not path or not os.path.isfile(path):
        _recording_status_text(app, "Playlist-Datei nicht gefunden.")
        return False
    app.radio_playback_mode = "playlist"
    app.radio_local_media_path = path
    app.radio_playlist_index = idx
    return _play_local_audio_file(
        app,
        path,
        station_name="Playlist",
        title_text=f"Datei: {_playlist_label_for_path(path)}",
    )


def remove_selected_radio_playlist_entry(app):
    entries = list(getattr(app, "radio_playlist_entries", []) or [])
    idx = _selected_radio_playlist_index(app)
    if idx is None or idx < 0 or idx >= len(entries):
        _recording_status_text(app, "Kein Playlist-Eintrag ausgewählt.")
        refresh_radio_playlist_ui(app)
        return False
    removed = entries.pop(idx)
    app.radio_playlist_entries = entries
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlist_entries"] = list(entries)
    app.radio_settings = settings
    save_radio_settings(app)
    refresh_radio_playlist_ui(app)
    _recording_status_text(
        app, f"Playlist-Eintrag entfernt: {_playlist_label_for_path(removed)}"
    )
    return True


def clear_radio_playlist(app):
    if not list(getattr(app, "radio_playlist_entries", []) or []):
        refresh_radio_playlist_ui(app)
        return False
    app.radio_playlist_entries = []
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlist_entries"] = []
    app.radio_settings = settings
    save_radio_settings(app)
    refresh_radio_playlist_ui(app)
    _recording_status_text(app, "Playlist geleert.")
    return True


def save_radio_playlist_to_file(app):
    entries = [
        str(item).strip()
        for item in list(getattr(app, "radio_playlist_entries", []) or [])
        if str(item).strip()
    ]
    if not entries:
        _recording_status_text(app, "Playlist ist leer.")
        refresh_radio_playlist_ui(app)
        return False
    initial_dir, initial_file = _playlist_dialog_defaults(app)
    path = filedialog.asksaveasfilename(
        title=_tr(app, "radio_playlist_save_dialog_title", "Playlist speichern"),
        initialdir=os.path.dirname(initial_file) or initial_dir,
        initialfile=os.path.basename(initial_file) or "radio_playlist.m3u",
        defaultextension=".m3u",
        filetypes=(("M3U-Playlisten", "*.m3u"), ("Alle Dateien", "*.*")),
    )
    if not path:
        return False
    ok, err = _write_m3u_playlist(path, entries)
    if not ok:
        _recording_status_text(app, f"Playlist konnte nicht gespeichert werden: {err}")
        return False
    app.radio_playlist_path = str(path).strip()
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["playlist_path"] = app.radio_playlist_path
    settings["playlists_dir"] = os.path.dirname(app.radio_playlist_path) or initial_dir
    settings["playlist_entries"] = list(entries)
    app.radio_settings = settings
    app.radio_playlists_dir = str(settings["playlists_dir"]).strip()
    save_radio_settings(app)
    refresh_radio_playlist_ui(app)
    _recording_status_text(app, f"Playlist gespeichert: {os.path.basename(path)}")
    return True


def load_radio_playlist_from_file(app):
    initial_dir, initial_file = _playlist_dialog_defaults(app)
    path = filedialog.askopenfilename(
        title=_tr(app, "radio_playlist_load_dialog_title", "Playlist laden"),
        initialdir=os.path.dirname(initial_file) or initial_dir,
        initialfile=os.path.basename(initial_file) or "radio_playlist.m3u",
        filetypes=(("M3U-Playlisten", "*.m3u"), ("Alle Dateien", "*.*")),
    )
    if not path:
        return False
    return _load_radio_playlist_path(app, path)


def start_radio_recording(app):
    if not radio_recording_available(app):
        _recording_status_text(app, "Aufnahme nicht verfügbar: ffmpeg fehlt.")
        refresh_radio_recording_ui(app)
        return False
    proc = getattr(app, "radio_record_proc", None)
    try:
        if proc is not None and proc.poll() is None:
            _recording_status_text(app, "Aufnahme läuft bereits.")
            refresh_radio_recording_ui(app)
            return False
    except Exception:
        if proc is not None:
            return False
    station = _resolve_target_station(app, getattr(app, "radio_context_station_id", ""))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    stream_url = str(
        station.get("url_resolved", "") or station.get("url", "") or ""
    ).strip()
    if not stream_url:
        _recording_status_text(app, "Aufnahme fehlgeschlagen: keine Stream-URL.")
        return False
    target_path = _recording_file_path(app, station)
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
    except Exception:
        _recording_status_text(app, "Aufnahmeordner konnte nicht erstellt werden.")
        return False
    try:
        record_proc = subprocess.Popen(
            _recording_command(stream_url, target_path),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        _recording_status_text(app, f"Aufnahme fehlgeschlagen: {exc}")
        refresh_radio_recording_ui(app)
        return False
    app.radio_record_proc = record_proc
    app.radio_last_record_path = target_path
    _recording_status_text(
        app,
        f"Aufnahme läuft: {os.path.basename(target_path)}",
    )
    refresh_radio_recording_ui(app)

    def _wait_for_recording():
        rc = None
        try:
            rc = record_proc.wait()
        except Exception:
            rc = None
        if getattr(app, "radio_record_proc", None) is record_proc:
            app.radio_record_proc = None
        status_text = (
            f"Aufnahme gespeichert: {os.path.basename(target_path)}"
            if rc == 0
            else f"Aufnahme beendet (rc={rc if rc is not None else '-'})"
        )
        _schedule_ui(app, lambda: _recording_status_text(app, status_text))
        _schedule_ui(app, lambda: refresh_radio_recording_ui(app))

    threading.Thread(target=_wait_for_recording, daemon=True).start()
    return True


def stop_radio_recording(app):
    proc = getattr(app, "radio_record_proc", None)
    if proc is None:
        _recording_status_text(app, "Aufnahme aus.")
        refresh_radio_recording_ui(app)
        return False
    try:
        proc.terminate()
        proc.wait(timeout=3)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    app.radio_record_proc = None
    _recording_status_text(app, "Aufnahme gestoppt.")
    refresh_radio_recording_ui(app)
    return True


def _mpv_command(volume, url, ipc_path, eq_filter=""):
    command = [
        "mpv",
        "--no-video",
        "--audio-display=no",
        "--force-window=no",
        "--input-terminal=no",
        f"--input-ipc-server={ipc_path}",
        "--quiet",
        f"--volume={max(0, min(100, int(volume)))}",
        url,
    ]
    if str(eq_filter or "").strip():
        command.insert(-1, f"--af={eq_filter}")
    return command


def _extract_stream_title(metadata):
    if not isinstance(metadata, dict):
        return ""
    for key in ("icy-title", "title"):
        value = str(metadata.get(key, "") or "").strip()
        if value:
            return value
    artist = str(metadata.get("artist", "") or "").strip()
    title = str(metadata.get("title", "") or "").strip()
    if artist and title:
        return f"{artist} - {title}"
    return ""


def _normalize_title_candidate(value):
    text = str(value or "").strip()
    if not text:
        return ""
    lowered = text.lower()
    if lowered in {"-", "n/a", "unknown"}:
        return ""
    return text


def _parse_icy_stream_title(metadata_text):
    text = str(metadata_text or "")
    if not text:
        return ""
    match = re.search(r"StreamTitle='([^']*)';", text, flags=re.IGNORECASE)
    if not match:
        match = re.search(r'StreamTitle="([^"]*)";', text, flags=re.IGNORECASE)
    if not match:
        return ""
    return _normalize_title_candidate(match.group(1))


def _fetch_icy_stream_title(stream_url, timeout=4):
    url = str(stream_url or "").strip()
    if not url:
        return ""
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "NetMon/1.1",
            "Icy-MetaData": "1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            metaint = response.headers.get("icy-metaint", "")
            try:
                interval = int(str(metaint or "").strip() or "0")
            except Exception:
                interval = 0
            if interval <= 0:
                return ""
            skipped = 0
            while skipped < interval:
                chunk = response.read(min(4096, interval - skipped))
                if not chunk:
                    return ""
                skipped += len(chunk)
            length_byte = response.read(1)
            if not length_byte:
                return ""
            metadata_length = length_byte[0] * 16
            if metadata_length <= 0:
                return ""
            metadata_block = response.read(metadata_length)
            if not metadata_block:
                return ""
            metadata_text = metadata_block.decode("utf-8", errors="ignore").strip(
                "\x00"
            )
            return _parse_icy_stream_title(metadata_text)
    except Exception:
        return ""


def _read_radio_stream_title(app):
    debug_payload = {}

    metadata = _query_mpv_property(app, "metadata")
    debug_payload["metadata"] = metadata
    title = _extract_stream_title(metadata)
    if title:
        return title, debug_payload

    filtered_metadata = _query_mpv_property(app, "filtered-metadata")
    debug_payload["filtered-metadata"] = filtered_metadata
    title = _extract_stream_title(filtered_metadata)
    if title:
        return title, debug_payload

    for property_name in (
        "media-title",
        "stream-title",
        "media-title/raw",
        "chapter-metadata/by-key/title",
        "metadata/by-key/icy-title",
        "metadata/by-key/title",
    ):
        value = _query_mpv_property(app, property_name)
        debug_payload[property_name] = value
        title = _normalize_title_candidate(value)
        if title:
            return title, debug_payload
    station = getattr(app, "radio_current_station", None)
    if not isinstance(station, dict):
        station = _resolve_station_by_id(
            app, getattr(app, "radio_current_station_id", "")
        )
    stream_url = ""
    if isinstance(station, dict):
        stream_url = str(
            station.get("url_resolved", "") or station.get("url", "") or ""
        ).strip()
    icy_title = _fetch_icy_stream_title(stream_url)
    debug_payload["icy-fetch"] = icy_title
    if icy_title:
        return icy_title, debug_payload
    return "", debug_payload


def _poll_radio_metadata(app, proc):
    last_title = ""
    debug_counter = 0
    while getattr(app, "radio_proc", None) is proc:
        title, debug_payload = _read_radio_stream_title(app)
        if title and title != last_title:
            last_title = title
            _schedule_ui(
                app,
                lambda text=title: _set_radio_title_text(
                    app,
                    _tr(app, "radio_header_title", "Titel: {title}").format(title=text),
                ),
            )
        elif not title:
            debug_counter += 1
            if debug_counter <= 3 or debug_counter % 6 == 0:
                try:
                    debug_text = ", ".join(
                        f"{key}={str(value or '-').strip() or '-'}"
                        for key, value in debug_payload.items()
                    )
                except Exception:
                    debug_text = "payload-unavailable"
                _radio_debug_log(app, f"title_poll no_title | {debug_text}")
        time.sleep(5)


def _wait_for_radio_process(app, proc, station_name):
    rc = None
    try:
        rc = proc.wait()
    except Exception:
        rc = None

    def finalize():
        if getattr(app, "radio_proc", None) is proc:
            app.radio_proc = None
            if getattr(app, "radio_stop_requested", False):
                set_radio_status(
                    app, _tr(app, "radio_status_stopped", "Radio gestoppt.")
                )
                _set_radio_light(app, "gray")
                _set_radio_station_text(app, "")
                _set_radio_title_text(
                    app, _tr(app, "radio_header_title_idle", "Titel: -")
                )
            elif rc == 0:
                set_radio_status(
                    app,
                    _tr(
                        app, "radio_status_stream_ended", "Stream beendet: {name}"
                    ).format(name=station_name),
                )
                _set_radio_light(app, "gray")
                _set_radio_title_text(
                    app, _tr(app, "radio_header_title_idle", "Titel: -")
                )
            else:
                set_radio_status(
                    app,
                    _tr(
                        app, "radio_status_ended_rc", "Radio beendet (rc={rc})."
                    ).format(rc=rc),
                )
                _set_radio_light(app, "red")
                _set_radio_title_text(
                    app,
                    _tr(
                        app,
                        "radio_header_title_error",
                        "Titel: Fehler / keine Verbindung",
                    ),
                )
            app.radio_stop_requested = False
            _cleanup_radio_ipc_path(app)
            refresh_radio_source_ui(app)
            update_radio_header(app)

    try:
        call_in_ui_thread(app, finalize)
    except Exception:
        finalize()


def stop_radio_playback(app, *, async_mode=True, clear_current=False):
    proc = getattr(app, "radio_proc", None)
    if proc is None:
        if clear_current:
            app.radio_current_station_id = ""
        if not async_mode:
            set_radio_status(app, _tr(app, "radio_status_stopped", "Radio gestoppt."))
            _set_radio_light(app, "gray")
            _set_radio_station_text(app, "")
            _set_radio_title_text(app, _tr(app, "radio_header_title_idle", "Titel: -"))
        return True

    def worker():
        with _radio_playback_lock(app):
            app.radio_stop_requested = True
            ipc_path = str(getattr(app, "radio_ipc_path", "") or "").strip()
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                try:
                    proc.kill()
                    try:
                        proc.wait(timeout=1)
                    except Exception:
                        pass
                except Exception:
                    pass
            if proc.poll() is None and ipc_path:
                _force_kill_radio_process_by_ipc(ipc_path)
                try:
                    proc.wait(timeout=1)
                except Exception:
                    pass
            if clear_current:
                app.radio_current_station_id = ""
            if getattr(app, "radio_proc", None) is proc:
                app.radio_proc = None
            _cleanup_radio_ipc_path(app)
            app.radio_ipc_path = ""
            try:
                call_in_ui_thread(app, lambda: update_radio_header(app))
                call_in_ui_thread(app, lambda: refresh_radio_source_ui(app))
                app.after(
                    0,
                    lambda: set_radio_status(
                        app, _tr(app, "radio_status_stopped", "Radio gestoppt.")
                    ),
                )
                call_in_ui_thread(app, lambda: _set_radio_light(app, "gray"))
                call_in_ui_thread(app, lambda: _set_radio_station_text(app, ""))
                app.after(
                    0,
                    lambda: _set_radio_title_text(
                        app, _tr(app, "radio_header_title_idle", "Titel: -")
                    ),
                )
            except Exception:
                update_radio_header(app)
                refresh_radio_source_ui(app)
                set_radio_status(
                    app, _tr(app, "radio_status_stopped", "Radio gestoppt.")
                )
                _set_radio_light(app, "gray")
                _set_radio_station_text(app, "")
                _set_radio_title_text(
                    app, _tr(app, "radio_header_title_idle", "Titel: -")
                )

    if async_mode:
        threading.Thread(target=worker, daemon=True).start()
        return True

    worker()
    return True



def play_selected_station(app):
    return play_radio_station(app, _selected_station_id(app))


def play_station_from_click(app, event):
    table = getattr(app, "radio_station_table", None)
    if table is None:
        return None
    try:
        region = table.identify("region", event.x, event.y)
    except Exception:
        region = ""
    if region not in {"tree", "cell"}:
        return None
    try:
        row_id = table.identify_row(event.y)
    except Exception:
        row_id = ""
    if not row_id:
        return None
    try:
        table.selection_set(row_id)
        table.focus(row_id)
    except Exception:
        pass
    play_radio_station(app, row_id)
    return "break"


def _station_cycle(app):
    rows = list(getattr(app, "radio_filtered_station_ids", []) or [])
    if not rows:
        rows = [
            station.get("id", "")
            for station in getattr(app, "radio_stations", []) or []
        ]
    return [station_id for station_id in rows if station_id]


def play_previous_station(app):
    if str(getattr(app, "radio_playback_mode", "radio") or "radio") == "playlist":
        entries = list(getattr(app, "radio_playlist_entries", []) or [])
        if entries:
            current_idx = int(getattr(app, "radio_playlist_index", -1) or -1)
            if current_idx < 0:
                current_path = str(
                    getattr(app, "radio_local_media_path", "") or ""
                ).strip()
                if current_path in entries:
                    current_idx = entries.index(current_path)
            next_idx = (
                (current_idx - 1) % len(entries)
                if current_idx >= 0
                else len(entries) - 1
            )
            listbox = getattr(app, "radio_playlist_listbox", None)
            if listbox is not None:
                try:
                    listbox.selection_set(next_idx)
                    listbox.activate(next_idx)
                except Exception:
                    pass
            return play_selected_radio_playlist_entry(app)
    cycle = _station_cycle(app)
    if not cycle:
        set_radio_status(
            app, _tr(app, "radio_status_no_stations", "Keine Radiosender vorhanden.")
        )
        return False
    current = getattr(app, "radio_current_station_id", "")
    if current in cycle:
        next_id = cycle[(cycle.index(current) - 1) % len(cycle)]
    else:
        next_id = cycle[-1]
    return play_radio_station(app, next_id)


def play_next_station(app):
    if str(getattr(app, "radio_playback_mode", "radio") or "radio") == "playlist":
        entries = list(getattr(app, "radio_playlist_entries", []) or [])
        if entries:
            current_idx = int(getattr(app, "radio_playlist_index", -1) or -1)
            if current_idx < 0:
                current_path = str(
                    getattr(app, "radio_local_media_path", "") or ""
                ).strip()
                if current_path in entries:
                    current_idx = entries.index(current_path)
            next_idx = (current_idx + 1) % len(entries) if current_idx >= 0 else 0
            listbox = getattr(app, "radio_playlist_listbox", None)
            if listbox is not None:
                try:
                    listbox.selection_set(next_idx)
                    listbox.activate(next_idx)
                except Exception:
                    pass
            return play_selected_radio_playlist_entry(app)
    cycle = _station_cycle(app)
    if not cycle:
        set_radio_status(
            app, _tr(app, "radio_status_no_stations", "Keine Radiosender vorhanden.")
        )
        return False
    current = getattr(app, "radio_current_station_id", "")
    if current in cycle:
        next_id = cycle[(cycle.index(current) + 1) % len(cycle)]
    else:
        next_id = cycle[0]
    return play_radio_station(app, next_id)


def on_radio_search_changed(app, *_args):
    refresh_radio_station_table(app, reset_page=True)
    save_radio_settings(app)


def on_radio_volume_preview(app, _value=None):
    value = 50
    try:
        value = int(getattr(app, "radio_volume_var").get() or 50)
    except Exception:
        value = 50
    for target in _radio_targets(app):
        target_volume_var = getattr(target, "radio_volume_var", None)
        if target_volume_var is not None and target_volume_var is not getattr(
            app, "radio_volume_var", None
        ):
            try:
                target_volume_var.set(value)
            except Exception:
                pass
        volume_var = getattr(target, "radio_volume_text_var", None)
        if volume_var is not None:
            try:
                volume_var.set(f"Vol.: {value}%")
                volume_var.set(
                    _tr(app, "radio_volume_label", "Vol.: {value}%").format(value=value)
                )
            except Exception:
                pass
        header_volume_var = getattr(target, "radio_volume_label_var", None)
        if header_volume_var is not None:
            try:
                header_volume_var.set(f"{value}%")
            except Exception:
                pass


def apply_radio_volume(app, volume=None):
    if getattr(app, "radio_proc", None) is None:
        return False
    if volume is None:
        try:
            volume = int(getattr(app, "radio_volume_var").get() or 50)
        except Exception:
            volume = 50
    value = max(0, min(100, int(volume)))
    return _send_mpv_command(app, ["set_property", "volume", value])


def on_radio_eq_preview(app, _value=None):
    for var_name, label_name in (
        ("radio_eq_bass_var", "radio_eq_bass_label_var"),
        ("radio_eq_mid_var", "radio_eq_mid_label_var"),
        ("radio_eq_treble_var", "radio_eq_treble_label_var"),
    ):
        label_var = getattr(app, label_name, None)
        if label_var is None:
            continue
        try:
            label_var.set(str(_eq_value(app, var_name)))
        except Exception:
            pass


def apply_radio_equalizer(app):
    if getattr(app, "radio_proc", None) is None:
        return False
    filter_spec = radio_eq_filter_spec(app)
    return _send_mpv_command(app, ["set_property", "af", filter_spec])


def commit_radio_eq_change(app, _event=None):
    on_radio_eq_preview(app)
    save_radio_settings(app)
    if getattr(app, "radio_proc", None) is None:
        return False
    applied = apply_radio_equalizer(app)
    if applied:
        return True
    station_id = getattr(app, "radio_current_station_id", "")
    if station_id:
        return play_radio_station(app, station_id)
    return False


def commit_radio_volume_change(app, _event=None):
    on_radio_volume_preview(app)
    save_radio_settings(app)
    if getattr(app, "radio_proc", None) is not None:
        applied = apply_radio_volume(app)
        if not applied:
            station_id = getattr(app, "radio_current_station_id", "")
            if station_id:
                play_radio_station(app, station_id)






# Hidden radio database workflow overrides


def load_radio_db(app):
    raw = _load_json(getattr(app, "radio_db_path", ""), [])
    if not isinstance(raw, list):
        return []

    stations = []
    seen_ids = set()
    for item in raw:
        station = normalize_station_entry(item, custom=bool(item.get("custom", False)))
        if station is None:
            continue
        station_id = station["id"]
        if station_id in seen_ids:
            station["id"] = f"{station_id}-{len(seen_ids) + 1}"
        seen_ids.add(station["id"])
        stations.append(station)
    return stations


def save_radio_db(app, stations=None):
    payload = []
    for station in list(
        stations if stations is not None else getattr(app, "radio_db", [])
    ):
        normalized = normalize_station_entry(
            station,
            custom=(
                bool(station.get("custom", False))
                if isinstance(station, dict)
                else False
            ),
        )
        if normalized is not None:
            payload.append(normalized)

    ok, err = safe_write_json(
        app.radio_db_path,
        payload,
        indent=2,
        ensure_ascii=False,
    )
    if ok:
        app.radio_db = payload
        return True

    try:
        app.log(f"Radio-Datenbank konnte nicht gespeichert werden: {err}")
    except Exception:
        pass
    return False


def _download_radio_db_payload():
    payload = json.dumps(
        {
            "hidebroken": True,
            "limit": RADIO_DB_LIMIT,
            "offset": 0,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        RADIO_DB_ENDPOINT,
        data=payload,
        headers={
            "User-Agent": "NetMon/1.1",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset("utf-8")
        body = response.read().decode(charset, errors="replace")
    raw_rows = json.loads(body)
    return _filter_radio_db_rows(raw_rows)


def _radio_database_source_ids_for_download(app):
    selected = []
    exclusive_mode_enabled = _bool_var_value(
        _app_value(app, "radio_database_exclusive_mode_var", None),
        True,
    )
    source_vars = _app_value(app, "radio_database_source_vars", {}) or {}
    source_ids = list(source_vars.keys())
    for source_id in (
        *RADIO_BROWSER_SOURCE_ENDPOINTS.keys(),
        *ICECAST_SOURCE_ENDPOINTS.keys(),
    ):
        if source_id not in source_ids:
            source_ids.append(source_id)
    for source_id in source_ids:
        var = source_vars.get(source_id)
        if var is None:
            if source_id != "icecast_json":
                continue
            selected.append(source_id)
            continue
        try:
            if bool(var.get()):
                selected.append(source_id)
        except Exception:
            if source_id == "icecast_json":
                selected.append(source_id)
    if exclusive_mode_enabled:
        for exclusive_id in RADIO_DATABASE_EXCLUSIVE_COUNTRY_SOURCE_IDS:
            if exclusive_id in selected:
                return [exclusive_id]
    return selected


def _xml_text(node, *names):
    for name in names:
        child = node.find(name)
        if child is not None and str(child.text or "").strip():
            return str(child.text or "").strip()
    return ""


def _parse_icecast_entries_from_xml(text):
    root = ElementTree.fromstring(text)
    rows = []
    for node in root.findall(".//entry"):
        rows.append(
            {
                "name": _xml_text(node, "server_name", "listen_name", "title"),
                "url": _xml_text(node, "listen_url", "url"),
                "homepage": _xml_text(node, "server_url", "homepage"),
                "tags": _xml_text(node, "genre", "tags"),
                "category": _xml_text(node, "genre"),
                "language": _xml_text(node, "language"),
                "country": _xml_text(node, "country"),
                "codec": _xml_text(node, "server_type", "type"),
                "bitrate": _xml_text(node, "bitrate"),
            }
        )
    return _filter_radio_db_rows(rows)


def _download_radio_source_payload(source_id):
    source_key = str(source_id or "").strip()
    endpoint = RADIO_BROWSER_SOURCE_ENDPOINTS.get(source_key, "")
    if endpoint:
        if endpoint.endswith("/search") or endpoint.endswith("/stations"):
            payload = json.dumps(
                {
                    "hidebroken": True,
                    "limit": RADIO_DB_LIMIT,
                    "offset": 0,
                }
            ).encode("utf-8")
            request = urllib.request.Request(
                endpoint,
                data=payload,
                headers={
                    "User-Agent": "NetMon/1.1",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
        else:
            request = urllib.request.Request(
                endpoint,
                headers={"User-Agent": "NetMon/1.1"},
            )
        with urllib.request.urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset("utf-8")
            body = response.read().decode(charset, errors="replace")
        raw_rows = json.loads(body)
        return _filter_radio_db_rows(raw_rows)

    endpoint = ICECAST_SOURCE_ENDPOINTS.get(source_key, "")
    if endpoint:
        request = urllib.request.Request(
            endpoint,
            headers={"User-Agent": "NetMon/1.1"},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            charset = response.headers.get_content_charset("utf-8")
            body = response.read().decode(charset, errors="replace")
        return _parse_icecast_entries_from_xml(body)

    if not endpoint:
        raise ValueError(f"quelle nicht unterstützt: {source_id}")
    raise ValueError(f"quelle nicht unterstützt: {source_id}")


def _set_radio_database_source_indicator(app, source_id, status):
    state = str(status or "unknown").strip().lower() or "unknown"
    if state not in {"online", "offline", "unknown"}:
        state = "unknown"

    cache = _app_value(app, "radio_database_source_status_by_id", None)
    if not isinstance(cache, dict):
        cache = {}
        app.radio_database_source_status_by_id = cache
    cache[str(source_id or "").strip()] = state

    labels = _app_value(app, "radio_database_source_status_labels", {}) or {}
    label = labels.get(str(source_id or "").strip())
    if label is None:
        return
    images = _app_value(app, "radio_status_indicator_images", {}) or {}
    try:
        label.configure(image=images.get(state))
    except Exception:
        pass


def _probe_radio_database_source_reachability(source_id, timeout=6.0):
    url = RADIO_DATABASE_SOURCE_CHECK_ENDPOINTS.get(str(source_id or "").strip(), "")
    url = str(url or "").strip()
    if not url:
        return None

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "NetMon/1.1",
            "Accept": "*/*",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            code = int(getattr(response, "status", 0) or response.getcode() or 0)
            if code and code >= 400:
                return False
            try:
                response.read(1)
            except Exception:
                pass
            return True
    except urllib.error.HTTPError as exc:
        code = int(getattr(exc, "code", 0) or 0)
        if code in {401, 403, 405, 406}:
            return True
        return False
    except (
        urllib.error.URLError,
        ValueError,
        socket.timeout,
        TimeoutError,
        ConnectionError,
        http.client.IncompleteRead,
        http.client.RemoteDisconnected,
        OSError,
    ):
        return False
    except Exception:
        return None


def _merge_radio_source_rows(sources_payloads):
    merged = []
    seen_keys = set()
    for rows in list(sources_payloads or []):
        for item in list(rows or []):
            station = normalize_station_entry(
                item,
                custom=(
                    bool(item.get("custom", False)) if isinstance(item, dict) else False
                ),
            )
            if station is None:
                continue
            key = (
                str(station.get("url", "") or "").strip().lower(),
                str(station.get("name", "") or "").strip().lower(),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            merged.append(station)
    return merged


def _persist_radio_db_meta(app, *, count):
    meta_path = getattr(app, "radio_db_meta_path", "") or ""
    if not meta_path:
        return False
    meta = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": int(count),
        "endpoint": RADIO_DB_ENDPOINT,
    }
    ok, err = safe_write_json(
        meta_path,
        meta,
        indent=2,
        ensure_ascii=False,
    )
    if ok:
        return True
    try:
        app.log(f"Radio-Metadaten konnten nicht gespeichert werden: {err}")
    except Exception:
        pass
    return False


def _set_radio_database_import_progress(
    app, current, total, message="", *, running=False
):
    callback = _app_callback(app, "set_radio_database_import_progress")
    if callable(callback):
        try:
            callback(current, total, message, running=running)
            return
        except Exception:
            pass


def _show_radio_database_import_summary(app, summary):
    callback = _app_callback(app, "show_radio_database_import_summary")
    if callable(callback):
        try:
            callback(summary)
            return True
        except Exception:
            return False
    return False


def _summarize_radio_database_import_results(
    selected_source_ids, source_results, merged_count
):
    raw_total = sum(
        int(item.get("count", 0) or 0)
        for item in list(source_results or [])
        if str(item.get("status", "") or "").strip() == "ok"
    )
    merged_total = max(0, int(merged_count or 0))
    duplicates_removed = max(0, raw_total - merged_total)
    return {
        "total_sources": len(list(selected_source_ids or [])),
        "raw_total": raw_total,
        "merged_total": merged_total,
        "duplicates_removed": duplicates_removed,
        "source_results": list(source_results or []),
        "errors": [
            str(item.get("label", "") or item.get("source_id", "") or "").strip()
            + ": "
            + str(item.get("error", "") or "").strip()
            for item in list(source_results or [])
            if str(item.get("status", "") or "").strip() == "error"
        ],
    }


def download_radio_db(app):
    def worker():
        try:
            db_path = _app_value(app, "radio_db_path", "") or ""
            if not db_path:
                raise ValueError("radio_db_path fehlt")

            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            app.log("Radio-Datenbank: Download gestartet...")
            selected_source_ids = _radio_database_source_ids_for_download(app)
            if not selected_source_ids:
                raise ValueError("keine unterstützte Datenbank ausgewählt")
            payloads = []
            source_results = []
            total_sources = len(selected_source_ids)
            _schedule_ui(
                app,
                lambda: _set_radio_database_import_progress(
                    app,
                    0,
                    total_sources,
                    "Import wird vorbereitet...",
                    running=True,
                ),
            )
            for index, source_id in enumerate(selected_source_ids, start=1):
                source_label = str(source_id or "").strip()
                _schedule_ui(
                    app,
                    lambda idx=index, total=total_sources, label=source_label: _set_radio_database_import_progress(
                        app,
                        idx - 1,
                        total,
                        f"Lade {label} ({idx}/{total})...",
                        running=True,
                    ),
                )
                try:
                    rows_for_source = _download_radio_source_payload(source_id)
                    payloads.append(rows_for_source)
                    source_results.append(
                        {
                            "source_id": source_id,
                            "label": source_label,
                            "status": "ok",
                            "count": len(rows_for_source),
                        }
                    )
                except Exception as exc:
                    source_results.append(
                        {
                            "source_id": source_id,
                            "label": source_label,
                            "status": "error",
                            "count": 0,
                            "error": str(exc),
                        }
                    )
                _schedule_ui(
                    app,
                    lambda idx=index, total=total_sources, label=source_label: _set_radio_database_import_progress(
                        app,
                        idx,
                        total,
                        f"Verarbeitet {label} ({idx}/{total})",
                        running=True,
                    ),
                )
            rows = _merge_radio_source_rows(payloads)
            if not rows:
                raise ValueError("keine gueltigen Senderdaten empfangen")
            summary = _summarize_radio_database_import_results(
                selected_source_ids,
                source_results,
                len(rows),
            )

            if not save_radio_db(app, stations=rows):
                raise RuntimeError("radio_db konnte nicht gespeichert werden")
            _persist_radio_db_meta(app, count=len(rows))

            def on_success():
                app.radio_db = rows
                try:
                    refresh_radio_ui(app)
                except Exception:
                    pass
                _set_radio_database_import_progress(
                    app,
                    total_sources,
                    total_sources,
                    f"Import abgeschlossen: {len(rows)} Sender gespeichert.",
                    running=False,
                )
                try:
                    app.log(
                        f"Radio-Datenbank aktualisiert: {len(rows)} Sender gespeichert."
                    )
                except Exception:
                    pass
                for item in list(summary.get("errors", []) or []):
                    try:
                        app.log(f"Radio-Datenbank Quelle übersprungen: {item}")
                    except Exception:
                        pass
                _show_radio_database_import_summary(app, summary)

            _schedule_ui(app, on_success)
        except Exception as exc:
            _schedule_ui(
                app,
                lambda error=str(exc): _set_radio_database_import_progress(
                    app,
                    0,
                    1,
                    f"Import fehlgeschlagen: {error}",
                    running=False,
                ),
            )
            try:
                app.log(f"Radio-Datenbank Download fehlgeschlagen: {exc}")
            except Exception:
                pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def load_favorites(app):
    raw = _load_json(getattr(app, "radio_favorites_path", ""), [])
    if not isinstance(raw, list):
        return []

    favorites = []
    seen_ids = set()
    for item in raw:
        station = normalize_station_entry(item, custom=bool(item.get("custom", False)))
        if station is None or station["id"] in seen_ids:
            continue
        seen_ids.add(station["id"])
        favorites.append(station)
    return favorites


def save_radio_favorites(app, favorites=None):
    payload = []
    for station in list(
        favorites if favorites is not None else getattr(app, "radio_favorites", [])
    ):
        normalized = normalize_station_entry(
            station,
            custom=(
                bool(station.get("custom", False))
                if isinstance(station, dict)
                else False
            ),
        )
        if normalized is not None:
            payload.append(normalized)

    ok, err = safe_write_json(
        app.radio_favorites_path,
        payload,
        indent=2,
        ensure_ascii=False,
    )
    if ok:
        app.radio_favorites = payload
        return True

    try:
        app.log(f"Radio-Favoriten konnten nicht gespeichert werden: {err}")
    except Exception:
        pass
    return False


def _radio_db_index(app):
    radio_db = getattr(app, "radio_db", []) or []
    return {station.get("id", ""): station for station in radio_db if station.get("id")}


def _favorite_index(app):
    favorites = getattr(app, "radio_favorites", []) or []
    return {
        station.get("id", ""): station for station in favorites if station.get("id")
    }


def _result_index(app):
    results = getattr(app, "radio_search_results", []) or []
    return {station.get("id", ""): station for station in results if station.get("id")}


def _favorites_view_enabled(app):
    toggle_var = getattr(app, "radio_show_favorites_var", None)
    if toggle_var is None:
        return False
    try:
        return bool(toggle_var.get())
    except Exception:
        return False


def _resolve_station_by_id(app, station_id):
    station_key = str(station_id or "").strip()
    if not station_key:
        return None
    for index in (_result_index(app), _favorite_index(app), _radio_db_index(app)):
        station = index.get(station_key)
        if station is not None:
            return station
    return None


def load_radio_runtime(app):
    radio_db = load_radio_db(app)
    if not radio_db:
        radio_db = []
        for item in _read_default_stations(app):
            station = normalize_station_entry(
                item, custom=bool(item.get("custom", False))
            )
            if station is not None:
                radio_db.append(station)
        save_radio_db(app, stations=radio_db)

    settings = default_radio_settings()
    raw_settings = _load_json(app.radio_settings_path, default_radio_settings())
    if isinstance(raw_settings, dict):
        settings.update(raw_settings)

    app.radio_db = radio_db
    app.radio_favorites = load_favorites(app)
    app.radio_search_results = []
    app.radio_current_station_id = str(
        settings.get("last_station_id", "") or ""
    ).strip()
    app.radio_current_station = None
    app.radio_search_page = 0
    app.radio_filtered_station_ids = []
    app.radio_settings = settings
    app.radio_recordings_dir = str(
        settings.get("recordings_dir", "") or _default_recordings_dir(app)
    ).strip()
    app.radio_playlist_entries = [
        str(item).strip()
        for item in list(settings.get("playlist_entries", []) or [])
        if str(item).strip()
    ]
    app.radio_playlist_path = str(
        settings.get("playlist_path", "") or _default_playlist_path(app)
    ).strip()
    app.radio_playlists_dir = str(
        settings.get("playlists_dir", "") or _default_playlists_dir(app)
    ).strip()
    settings["station_list_columns"] = _normalize_station_list_columns(
        settings.get("station_list_columns", [])
    )
    if "radio_search_var" in app.__dict__:
        try:
            app.radio_search_var.set(str(settings.get("last_search", "") or ""))
        except Exception:
            pass
    if "radio_volume_var" in app.__dict__:
        try:
            app.radio_volume_var.set(int(settings.get("volume", 50) or 50))
        except Exception:
            app.radio_volume_var.set(50)
    for var_name, key_name in (
        ("radio_eq_bass_var", "eq_bass"),
        ("radio_eq_mid_var", "eq_mid"),
        ("radio_eq_treble_var", "eq_treble"),
    ):
        if var_name in app.__dict__:
            try:
                getattr(app, var_name).set(int(settings.get(key_name, 0) or 0))
            except Exception:
                getattr(app, var_name).set(0)
    on_radio_eq_preview(app)
    configure_radio_station_table_columns(app)
    toggle_text_var = getattr(app, "radio_toggle_favorites_text_var", None)
    if toggle_text_var is not None:
        try:
            toggle_text_var.set(_tr(app, "radio_show_favorites", "Favoriten anzeigen"))
        except Exception:
            pass

    save_radio_favorites(app)
    save_radio_settings(app)


def search_radio(app, query):
    db = list(getattr(app, "radio_db", []) or load_radio_db(app))
    return _search_station_rows(db, query)


def refresh_radio_favorites_list(app):
    listbox = getattr(app, "radio_favorites_list", None)
    if listbox is None:
        return

    try:
        selected = listbox.curselection()
    except Exception:
        selected = ()

    try:
        listbox.delete(0, "end")
    except Exception:
        return

    for station in getattr(app, "radio_favorites", []) or []:
        label = str(station.get("name", "") or "").strip()
        if not label:
            continue
        try:
            listbox.insert("end", label)
        except Exception:
            pass

    if selected:
        try:
            idx = int(selected[0])
            listbox.selection_set(idx)
        except Exception:
            pass


def _page_status_text(app, total_count, page_count, current_page):
    if total_count <= 0:
        if _favorites_view_enabled(app):
            return _tr(app, "radio_result_count", "Treffer: {count}").format(count=0)
        return _tr(app, "radio_search_idle", "Suche starten.")
    return _tr(
        app,
        "radio_result_page_count",
        "Treffer: {count} | Seite {page}/{pages}",
    ).format(count=total_count, page=current_page + 1, pages=page_count)


def _station_online_indicator(app, row):
    cache = getattr(app, "radio_live_status_by_station_id", {}) or {}
    status = cache.get(str(row.get("id", "") or "").strip(), None)
    if status is True:
        return "online"
    if status is False:
        return "offline"
    return "unknown"


def _station_online_indicator_image(app, row):
    images = getattr(app, "radio_status_indicator_images", {}) or {}
    return images.get(_station_online_indicator(app, row))


def _station_online_indicator_text(_app, row):
    status = _station_online_indicator(_app, row)
    if status == "online":
        return "●"
    if status == "offline":
        return "●"
    return "●"


def _visible_radio_page_rows(app):
    rows = list(getattr(app, "radio_search_results", []) or [])
    current_page = max(0, int(getattr(app, "radio_search_page", 0) or 0))
    start = current_page * RADIO_RESULTS_PER_PAGE
    end = start + RADIO_RESULTS_PER_PAGE
    return rows[start:end]


def _set_radio_reachability_button_state(app, *, running=False):
    button = getattr(app, "radio_reachability_button", None)
    if button is None:
        return
    try:
        button.configure(
            state="disabled" if running else "normal",
            text="Prüfe..." if running else "Erreichbarkeit prüfen",
        )
    except Exception:
        pass


def _probe_radio_station_reachability(row, timeout=4.0):
    urls = []
    for candidate in (row.get("url_resolved", ""), row.get("url", "")):
        value = str(candidate or "").strip()
        if value and value not in urls:
            urls.append(value)
    if not urls:
        return None

    saw_inconclusive = False
    for url in urls:
        for headers in (
            {
                "User-Agent": "NetMonRadio/1.0",
                "Icy-MetaData": "1",
                "Range": "bytes=0-0",
            },
            {
                "User-Agent": "NetMonRadio/1.0",
            },
        ):
            request = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    code = int(
                        getattr(response, "status", 0) or response.getcode() or 0
                    )
                    if code and code >= 400:
                        continue
                    try:
                        response.read(1)
                    except Exception:
                        pass
                    return True
            except urllib.error.HTTPError as exc:
                code = int(getattr(exc, "code", 0) or 0)
                if code in {401, 403, 405, 406, 416}:
                    return True
            except http.client.BadStatusLine as exc:
                line = str(exc or "").strip().upper()
                if line.startswith("ICY ") or line.startswith("HTTP/"):
                    return True
                saw_inconclusive = True
            except (
                urllib.error.URLError,
                ValueError,
                socket.timeout,
                TimeoutError,
                ConnectionError,
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                OSError,
            ):
                continue
            except Exception:
                saw_inconclusive = True
    return None if saw_inconclusive else False


def check_visible_radio_station_reachability(app):
    if bool(getattr(app, "radio_reachability_check_running", False)):
        return False

    page_rows = _visible_radio_page_rows(app)
    if not page_rows:
        set_radio_status(
            app, _tr(app, "radio_status_no_stations", "Keine Radiosender vorhanden.")
        )
        return False

    cache = getattr(app, "radio_live_status_by_station_id", None)
    if not isinstance(cache, dict):
        cache = {}
        app.radio_live_status_by_station_id = cache
    for row in page_rows:
        station_id = str(row.get("id", "") or "").strip()
        if station_id:
            cache.pop(station_id, None)

    app.radio_reachability_check_running = True
    _set_radio_reachability_button_state(app, running=True)
    update_radio_results_table(app)

    def worker():
        results = {}
        try:
            max_workers = min(6, max(1, len(page_rows)))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_map = {
                    pool.submit(_probe_radio_station_reachability, row): row
                    for row in page_rows
                }
                for future in concurrent.futures.as_completed(future_map):
                    row = future_map[future]
                    station_id = str(row.get("id", "") or "").strip()
                    if not station_id:
                        continue
                    try:
                        reachable = future.result()
                    except Exception:
                        reachable = None
                    if reachable is None:
                        fallback = row.get("lastcheckok")
                        if isinstance(fallback, bool):
                            reachable = fallback
                    if reachable is None:
                        reachable = False
                    results[station_id] = reachable
                    cache[station_id] = reachable
                    _schedule_ui(app, lambda: update_radio_results_table(app))
        finally:

            def finalize():
                app.radio_reachability_check_running = False
                _set_radio_reachability_button_state(app, running=False)
                if results:
                    online_count = sum(1 for value in results.values() if value)
                    set_radio_status(
                        app,
                        f"Erreichbarkeit geprüft: {online_count}/{len(results)} Sender online.",
                    )
                else:
                    set_radio_status(app, "Erreichbarkeit konnte nicht geprüft werden.")

            _schedule_ui(app, finalize)

    threading.Thread(target=worker, daemon=True).start()
    return True


def check_radio_database_source_reachability(app):
    if bool(_app_value(app, "radio_database_source_check_running", False)):
        return False

    labels = _app_value(app, "radio_database_source_status_labels", {}) or {}
    source_ids = list(labels.keys())
    if not source_ids:
        return False

    app.radio_database_source_check_running = True
    for source_id in source_ids:
        _set_radio_database_source_indicator(app, source_id, "unknown")

    def worker():
        results = {}
        try:
            max_workers = min(6, max(1, len(source_ids)))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
                future_map = {
                    pool.submit(
                        _probe_radio_database_source_reachability, source_id
                    ): source_id
                    for source_id in source_ids
                }
                for future in concurrent.futures.as_completed(future_map):
                    source_id = future_map[future]
                    try:
                        reachable = future.result()
                    except Exception:
                        reachable = None
                    status = "unknown"
                    if reachable is True:
                        status = "online"
                    elif reachable is False:
                        status = "offline"
                    results[source_id] = status
                    _schedule_ui(
                        app,
                        lambda sid=source_id, current_status=status: _set_radio_database_source_indicator(
                            app, sid, current_status
                        ),
                    )
        finally:

            def finalize():
                app.radio_database_source_check_running = False
                online_count = sum(1 for value in results.values() if value == "online")
                offline_count = sum(
                    1 for value in results.values() if value == "offline"
                )
                if results:
                    set_radio_status(
                        app,
                        f"Datenbanken geprüft: {online_count} erreichbar, {offline_count} nicht erreichbar.",
                    )

            _schedule_ui(app, finalize)

    threading.Thread(target=worker, daemon=True).start()
    return True


def toggle_radio_station_list_column(app, column_id, enabled):
    key = str(column_id or "").strip()
    if key not in RADIO_STATION_LIST_COLUMN_DEFS:
        return False
    current = selected_radio_station_columns(app)
    if enabled:
        if key in current:
            return True
        current.append(key)
    else:
        if key not in current:
            return True
        if len(current) <= 1:
            return False
        current = [item for item in current if item != key]
    settings = dict(getattr(app, "radio_settings", {}) or {})
    settings["station_list_columns"] = _normalize_station_list_columns(current)
    app.radio_settings = settings
    configure_radio_station_table_columns(app)
    update_radio_results_table(app)
    save_radio_settings(app)
    return True


def _radio_page_count(total):
    if total <= 0:
        return 1
    return max(1, (int(total) + RADIO_RESULTS_PER_PAGE - 1) // RADIO_RESULTS_PER_PAGE)


def update_radio_page_controls(app):
    total = len(getattr(app, "radio_search_results", []) or [])
    pages = _radio_page_count(total)
    current_page = int(getattr(app, "radio_search_page", 0) or 0)
    indicator = getattr(app, "radio_page_indicator_var", None)
    if indicator is not None:
        try:
            indicator.set(f"{current_page + 1}/{pages}")
        except Exception:
            pass
    prev_button = getattr(app, "radio_page_prev_button", None)
    if prev_button is not None:
        try:
            prev_button.configure(state="normal" if current_page > 0 else "disabled")
        except Exception:
            pass
    next_button = getattr(app, "radio_page_next_button", None)
    if next_button is not None:
        try:
            next_button.configure(
                state="normal" if current_page < pages - 1 else "disabled"
            )
        except Exception:
            pass


def configure_radio_station_table_columns(app):
    table = getattr(app, "radio_station_table", None)
    if table is None:
        return False
    columns = selected_radio_station_columns(app)
    try:
        table.configure(columns=tuple(columns), show=("tree", "headings"))
        table.heading("#0", text=_tr(app, "radio_col_indicator", "Status"))
        table.column("#0", width=44, minwidth=44, stretch=False, anchor="center")
        table.tag_configure("ampel_online", foreground="#2fb344")
        table.tag_configure("ampel_offline", foreground="#d9485f")
        table.tag_configure("ampel_unknown", foreground="#8a8f98")
        for column_id in columns:
            meta = RADIO_STATION_LIST_COLUMN_DEFS.get(column_id, {})
            title_key = str(meta.get("title_key", "") or "").strip()
            title_default = str(meta.get("title", column_id))
            table.heading(column_id, text=_tr(app, title_key, title_default))
            table.column(
                column_id,
                width=int(meta.get("width", 120) or 120),
                anchor=str(meta.get("anchor", "w") or "w"),
                stretch=False,
            )
    except Exception:
        return False
    return True


def update_radio_results_table(app):
    table = getattr(app, "radio_station_table", None)
    if table is None:
        return
    columns = selected_radio_station_columns(app)
    rows = list(getattr(app, "radio_search_results", []) or [])
    current_page = max(0, int(getattr(app, "radio_search_page", 0) or 0))
    total_count = len(rows)
    page_count = _radio_page_count(total_count)
    if current_page >= page_count:
        current_page = max(0, page_count - 1)
        app.radio_search_page = current_page
    start = current_page * RADIO_RESULTS_PER_PAGE
    end = start + RADIO_RESULTS_PER_PAGE
    page_rows = rows[start:end]
    app.radio_filtered_station_ids = [
        row.get("id", "") for row in page_rows if row.get("id")
    ]
    current_selection = getattr(app, "radio_current_station_id", "")

    try:
        for item in table.get_children():
            table.delete(item)
    except Exception:
        return

    for row in page_rows:
        station_id = row.get("id", "")
        status = _station_online_indicator(app, row)
        try:
            table.insert(
                "",
                "end",
                iid=station_id,
                text=_station_online_indicator_text(app, row),
                values=tuple(
                    _station_table_value(row, column_id) for column_id in columns
                ),
                tags=(f"ampel_{status}",),
            )
        except Exception:
            pass

    if current_selection:
        try:
            table.selection_set(current_selection)
            table.see(current_selection)
        except Exception:
            pass

    count_var = getattr(app, "radio_list_status_var", None)
    if count_var is not None:
        try:
            count_var.set(_page_status_text(app, total_count, page_count, current_page))
        except Exception:
            pass
    update_radio_page_controls(app)


def refresh_radio_station_table(app, *, reset_page=False):
    query = ""
    search_var = getattr(app, "radio_search_var", None)
    if search_var is not None:
        try:
            query = search_var.get()
        except Exception:
            query = ""

    if _favorites_view_enabled(app):
        favorites = list(getattr(app, "radio_favorites", []) or [])
        rows = (
            _search_station_rows(favorites, query)
            if str(query or "").strip()
            else favorites
        )
    else:
        rows = search_radio(app, query)
    app.radio_search_results = rows
    if reset_page:
        app.radio_search_page = 0
    update_radio_results_table(app)


def update_radio_header(app):
    current = getattr(app, "radio_current_station", None)
    if current is None:
        current = _resolve_station_by_id(
            app, getattr(app, "radio_current_station_id", "")
        )
    refresh_logo = getattr(app, "refresh_radio_station_logo", None)
    if isinstance(current, dict):
        _set_radio_station_text(app, current.get("name", ""))
        _set_radio_stream_url_text(
            app, current.get("url_resolved", "") or current.get("url", "")
        )
        _set_radio_bitrate_text(app, current.get("bitrate", ""))
        if callable(refresh_logo):
            refresh_logo(current)
    elif not getattr(app, "radio_proc", None):
        _set_radio_station_text(app, "")
        _set_radio_stream_url_text(app, "")
        _set_radio_bitrate_text(app, "")
        if callable(refresh_logo):
            refresh_logo(None)


def refresh_radio_ui(app):
    update_radio_database_count_label(app)
    refresh_radio_station_table(app)
    refresh_radio_favorites_list(app)
    update_radio_header(app)
    update_radio_dependency_state(app)


def update_radio_database_count_label(app):
    count_var = _app_value(app, "radio_database_count_var", None)
    if count_var is None:
        return
    count = len(_app_value(app, "radio_db", []) or [])
    try:
        count_var.set(
            _tr(app, "radio_database_count", "DB: {count} Sender").format(count=count)
        )
    except Exception:
        pass


def set_radio_search_page(app, page):
    total = len(getattr(app, "radio_search_results", []) or [])
    max_page = max(0, _radio_page_count(total) - 1)
    try:
        app.radio_search_page = max(0, min(int(page), max_page))
    except Exception:
        app.radio_search_page = 0
    update_radio_results_table(app)
    return app.radio_search_page


def step_radio_search_page(app, delta):
    current = int(getattr(app, "radio_search_page", 0) or 0)
    return set_radio_search_page(app, current + int(delta))


def toggle_radio_favorites_view(app):
    toggle_var = getattr(app, "radio_show_favorites_var", None)
    enabled = False
    if toggle_var is not None:
        try:
            enabled = not bool(toggle_var.get())
            toggle_var.set(enabled)
        except Exception:
            enabled = False
    toggle_text_var = getattr(app, "radio_toggle_favorites_text_var", None)
    if toggle_text_var is not None:
        try:
            toggle_text_var.set(
                _tr(app, "radio_show_all_stations", "Alle Sender anzeigen")
                if enabled
                else _tr(app, "radio_show_favorites", "Favoriten anzeigen")
            )
        except Exception:
            pass
    refresh_radio_station_table(app, reset_page=True)
    return enabled


def _resolve_target_station(app, station_id=""):
    station = _resolve_station_by_id(app, station_id)
    if station is not None:
        return station

    selected_id = _selected_station_id(app)
    station = _resolve_station_by_id(app, selected_id)
    if station is not None:
        return station

    current = getattr(app, "radio_current_station", None)
    if isinstance(current, dict) and current.get("url"):
        return current

    current = _resolve_station_by_id(app, getattr(app, "radio_current_station_id", ""))
    if current is not None:
        return current

    favorites = list(getattr(app, "radio_favorites", []) or [])
    if favorites:
        return favorites[0]

    results = list(getattr(app, "radio_search_results", []) or [])
    if results:
        return results[0]
    return None


def play_radio_station(app, station_id=""):
    if not radio_available(app):
        update_radio_dependency_state(app)
        return False

    station = _resolve_target_station(app, station_id=station_id)
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False

    def worker():
        with _radio_playback_lock(app):
            preserved_title = str(
                getattr(app, "radio_handover_title", "") or ""
            ).strip()
            stop_radio_playback(app, async_mode=False)
            _schedule_ui(app, lambda: _set_radio_light(app, "yellow"))
            _schedule_ui(
                app,
                lambda: _set_radio_station_text(app, station.get("name", "")),
            )
            _schedule_ui(
                app,
                lambda: _set_radio_title_text(
                    app, _tr(app, "radio_header_title_connecting", "Titel: verbinde...")
                ),
            )
            volume = 50
            try:
                volume = int(getattr(app, "radio_volume_var").get() or 50)
            except Exception:
                volume = 50
            ipc_path = _radio_ipc_path(app)
            app.radio_ipc_path = ipc_path
            _cleanup_radio_ipc_path(app)
            cmd = _mpv_command(
                volume, station["url"], ipc_path, radio_eq_filter_spec(app)
            )
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as exc:
                try:
                    app.after(
                        0,
                        lambda err=str(exc): (
                            set_radio_status(
                                app,
                                _tr(
                                    app,
                                    "radio_status_start_failed",
                                    "Radio-Start fehlgeschlagen: {error}",
                                ).format(error=err),
                            ),
                            _set_radio_light(app, "red"),
                            _set_radio_title_text(
                                app,
                                _tr(
                                    app,
                                    "radio_header_title_error",
                                    "Titel: Fehler / keine Verbindung",
                                ),
                            ),
                        ),
                    )
                except Exception:
                    set_radio_status(
                        app,
                        _tr(
                            app,
                            "radio_status_start_failed",
                            "Radio-Start fehlgeschlagen: {error}",
                        ).format(error=exc),
                    )
                    _set_radio_light(app, "red")
                    _set_radio_title_text(
                        app,
                        _tr(
                            app,
                            "radio_header_title_error",
                            "Titel: Fehler / keine Verbindung",
                        ),
                    )
                return

            def announce():
                app.radio_proc = proc
                app.radio_stop_requested = False
                app.radio_current_station_id = station["id"]
                app.radio_current_station = dict(station)
                app.radio_playback_mode = "radio"
                app.radio_local_media_path = ""
                app.radio_playlist_index = -1
                save_radio_settings(app)
                update_radio_header(app)
                refresh_radio_station_table(app)
                refresh_radio_favorites_list(app)
                refresh_radio_source_ui(app)
                _set_radio_light(app, "green")
                set_radio_status(
                    app,
                    _tr(app, "radio_status_playing", "Spielt: {name}").format(
                        name=station["name"]
                    ),
                )
                _set_radio_title_text(
                    app,
                    preserved_title or _tr(app, "radio_header_title_idle", "Titel: -"),
                )

            try:
                call_in_ui_thread(app, announce)
            except Exception:
                announce()

            monitor = threading.Thread(
                target=_wait_for_radio_process,
                args=(app, proc, station["name"]),
                daemon=True,
            )
            monitor.start()
        threading.Thread(
            target=_poll_radio_metadata, args=(app, proc), daemon=True
        ).start()

    threading.Thread(target=worker, daemon=True).start()
    return True


def _station_cycle(app):
    rows = list(getattr(app, "radio_filtered_station_ids", []) or [])
    if rows:
        return [station_id for station_id in rows if station_id]
    return [
        station.get("id", "")
        for station in list(getattr(app, "radio_favorites", []) or [])
        if station.get("id")
    ]


def play_current_radio_source(app):
    mode = str(getattr(app, "radio_playback_mode", "radio") or "radio").strip()
    if mode == "playlist":
        entries = list(getattr(app, "radio_playlist_entries", []) or [])
        current_idx = int(getattr(app, "radio_playlist_index", -1) or -1)
        current_path = str(getattr(app, "radio_local_media_path", "") or "").strip()
        if current_idx < 0 and current_path in entries:
            current_idx = entries.index(current_path)
        if 0 <= current_idx < len(entries):
            path = str(entries[current_idx] or "").strip()
            if path and os.path.isfile(path):
                app.radio_playlist_index = current_idx
                app.radio_local_media_path = path
                return _play_local_audio_file(
                    app,
                    path,
                    station_name="Playlist",
                    title_text=f"Datei: {_playlist_label_for_path(path)}",
                )
        return play_selected_radio_playlist_entry(app)
    if mode in {"file", "recording"}:
        path = str(getattr(app, "radio_local_media_path", "") or "").strip()
        if path and os.path.isfile(path):
            station_name = (
                "Letzter Mitschnitt" if mode == "recording" else "Lokale Datei"
            )
            return _play_local_audio_file(
                app,
                path,
                station_name=station_name,
                title_text=f"Datei: {os.path.basename(path)}",
            )
    return play_radio_station(app)


def add_to_favorites(app, station):
    normalized = normalize_station_entry(
        station,
        custom=(
            bool(station.get("custom", False)) if isinstance(station, dict) else False
        ),
    )
    if normalized is None:
        return False

    favorites = list(getattr(app, "radio_favorites", []) or [])
    if normalized["id"] not in {item.get("id", "") for item in favorites}:
        favorites.append(normalized)
    save_radio_favorites(app, favorites=favorites)
    app.radio_favorites = favorites
    refresh_radio_favorites_list(app)
    return True


def add_selected_station_to_favorites(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    favorites = list(getattr(app, "radio_favorites", []) or [])
    if station["id"] in {item.get("id", "") for item in favorites}:
        set_radio_status(
            app,
            _tr(app, "radio_status_favorite_exists", "Favorit bereits vorhanden."),
        )
        return True
    add_to_favorites(app, station)
    refresh_radio_ui(app)
    set_radio_status(
        app,
        _tr(app, "radio_status_favorite_added", "Favorit hinzugefügt: {name}").format(
            name=station.get("name", "")
        ),
    )
    return True


def toggle_selected_favorite(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False

    favorites = list(getattr(app, "radio_favorites", []) or [])
    favorite_ids = {item.get("id", "") for item in favorites}
    if station["id"] in favorite_ids:
        favorites = [item for item in favorites if item.get("id") != station["id"]]
        state = "entfernt"
    else:
        favorites.append(dict(station))
        state = "gespeichert"

    save_radio_favorites(app, favorites=favorites)
    app.radio_favorites = favorites
    refresh_radio_ui(app)
    set_radio_status(
        app,
        _tr(app, "radio_status_favorite_toggled", "Favorit {state}.").format(
            state=_tr(app, f"radio_favorite_state_{state}", state)
        ),
    )
    return True


def delete_selected_station(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    if not bool(station.get("custom")):
        set_radio_status(
            app,
            _tr(
                app,
                "radio_status_preset_delete_blocked",
                "Preset-Sender können nicht gelöscht werden.",
            ),
        )
        return False

    if not messagebox.askyesno(
        _tr(app, "radio_delete_title", "Radio-Sender löschen"),
        _tr(
            app,
            "radio_delete_prompt",
            "Soll '{name}' wirklich gelöscht werden?",
        ).format(name=station.get("name", "")),
        parent=app,
    ):
        return False

    station_id = str(station.get("id", "") or "").strip()
    app.radio_db = [
        item
        for item in list(getattr(app, "radio_db", []) or [])
        if item.get("id") != station_id
    ]
    app.radio_favorites = [
        item
        for item in list(getattr(app, "radio_favorites", []) or [])
        if item.get("id") != station_id
    ]

    if getattr(app, "radio_current_station_id", "") == station_id:
        stop_radio_playback(app, async_mode=False, clear_current=True)
    if (
        str(getattr(app, "radio_custom_edit_station_id", "") or "").strip()
        == station_id
    ):
        clear_custom_station_form(app)

    save_radio_db(app)
    save_radio_favorites(app)
    refresh_radio_ui(app)
    set_radio_status(
        app,
        _tr(app, "radio_status_station_deleted", "Sender gelöscht: {name}").format(
            name=station.get("name", "")
        ),
    )
    return True


def remove_selected_station_from_favorites(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    favorites = list(getattr(app, "radio_favorites", []) or [])
    if station["id"] not in {item.get("id", "") for item in favorites}:
        set_radio_status(
            app,
            _tr(app, "radio_status_favorite_missing", "Sender ist kein Favorit."),
        )
        return False
    favorites = [item for item in favorites if item.get("id") != station["id"]]
    save_radio_favorites(app, favorites=favorites)
    app.radio_favorites = favorites
    refresh_radio_ui(app)
    set_radio_status(
        app,
        _tr(app, "radio_status_favorite_removed", "Favorit entfernt: {name}").format(
            name=station.get("name", "")
        ),
    )
    return True


def copy_selected_station_url(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    url = str(station.get("url_resolved", "") or station.get("url", "") or "").strip()
    if not url:
        return False
    try:
        app.clipboard_clear()
        app.clipboard_append(url)
    except Exception:
        return False
    set_radio_status(
        app,
        _tr(app, "radio_status_url_copied", "Stream-URL kopiert."),
    )
    return True


def open_selected_station_homepage(app):
    station = _resolve_target_station(app, _selected_station_id(app))
    if station is None:
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False
    url = _normalize_station_homepage_url(station.get("homepage", "") or "")
    if not url:
        url = _normalize_station_homepage_url(station.get("url", "") or "")
    if not url:
        set_radio_status(
            app,
            _tr(app, "radio_status_homepage_missing", "Keine Homepage vorhanden."),
        )
        return False
    try:
        webbrowser.open(url, new=2)
    except Exception as exc:
        set_radio_status(
            app,
            _tr(
                app,
                "radio_status_homepage_open_failed",
                "Homepage konnte nicht geöffnet werden: {error}",
            ).format(error=exc),
        )
        return False
    set_radio_status(
        app,
        _tr(app, "radio_status_homepage_opened", "Homepage geöffnet."),
    )
    return True


def show_station_context_menu(app, event):
    table = getattr(app, "radio_station_table", None)
    menu = getattr(app, "radio_station_menu", None)
    if table is None or menu is None:
        return
    try:
        row_id = table.identify_row(event.y)
    except Exception:
        row_id = ""
    if row_id:
        try:
            table.selection_set(row_id)
            table.focus(row_id)
        except Exception:
            pass
    try:
        app.radio_context_station_id = str(row_id or "").strip()
    except Exception:
        pass
    _radio_debug_log(
        app,
        f"context_menu row_id={str(row_id or '').strip() or '-'} "
        f"selection={getattr(table, 'selection', lambda: ())()}",
    )
    try:
        table.focus_set()
    except Exception:
        pass
    show_fn = getattr(app, "_show_context_menu", None)
    if callable(show_fn):
        return show_fn(menu, event)
    try:
        menu.tk_popup(event.x_root, event.y_root)
    finally:
        try:
            menu.grab_release()
        except Exception:
            pass


def _set_custom_form_state(app, *, edit_station_id="", status_message=""):
    station_id = str(edit_station_id or "").strip()
    app.radio_custom_edit_station_id = station_id
    for target in _radio_targets(app):
        try:
            target.radio_custom_edit_station_id = station_id
        except Exception:
            pass

        submit_var = getattr(target, "radio_custom_submit_text_var", None)
        if submit_var is not None:
            try:
                submit_var.set(
                    _tr(app, "radio_custom_save_button", "Sender speichern")
                    if station_id
                    else _tr(app, "radio_custom_add_button", "Sender hinzufügen")
                )
            except Exception:
                pass

        status_var = getattr(target, "radio_custom_form_status_var", None)
        if status_var is not None:
            try:
                status_var.set(str(status_message or ""))
            except Exception:
                pass

        delete_button = getattr(target, "radio_custom_editor_delete_button", None)
        if delete_button is not None:
            try:
                delete_button.configure(state="normal" if station_id else "disabled")
            except Exception:
                pass


def clear_custom_station_form(app):
    _set_custom_form_values(app, name="", url="", homepage="", category="")
    _set_custom_form_state(app, edit_station_id="", status_message="")
    _radio_debug_log(app, "clear_custom_form")
    return True


def edit_selected_station_data(app):
    station_id = _selected_station_id(app)
    station = _resolve_target_station(app, station_id)
    if station is None:
        _radio_debug_log(
            app, f"edit_selected_station_data unresolved station_id={station_id or '-'}"
        )
        set_radio_status(
            app,
            _tr(
                app, "radio_status_no_station_selected", "Kein Radiosender ausgewählt."
            ),
        )
        return False

    station_name = str(station.get("name", "") or "").strip()
    station_url = str(
        station.get("url_resolved", "") or station.get("url", "") or ""
    ).strip()
    station_homepage = str(station.get("homepage", "") or "").strip()
    station_category = str(station.get("category", "") or "").strip()
    _set_custom_form_values(
        app,
        name=station_name,
        url=station_url,
        homepage=station_homepage,
        category=station_category,
    )

    if bool(station.get("custom")):
        _set_custom_form_state(
            app,
            edit_station_id=station.get("id", ""),
            status_message=_tr(
                app,
                "radio_custom_editing_status",
                "Bearbeite eigenen Sender: {name}",
            ).format(name=station.get("name", "")),
        )
    else:
        _set_custom_form_state(
            app,
            edit_station_id="",
            status_message=_tr(
                app,
                "radio_custom_prefill_status",
                "Preset ins Formular übernommen. Beim Speichern wird ein eigener Sender angelegt.",
            ),
        )
    try:
        app.radio_context_station_id = str(station.get("id", "") or "").strip()
    except Exception:
        pass
    _radio_debug_log(
        app,
        "edit_selected_station_data "
        f"station_id={station.get('id', '') or '-'} "
        f"name={station_name or '-'} "
        f"url={station_url or '-'} "
        f"homepage={station_homepage or '-'} "
        f"targets={len(list(_radio_targets(app)))}",
    )
    try:
        update_idletasks = getattr(app, "update_idletasks", None)
        if callable(update_idletasks):
            update_idletasks()
    except Exception:
        pass
    try:
        open_editor = getattr(app, "open_custom_radio_station_editor", None)
        if callable(open_editor):
            open_editor()
    except Exception:
        pass
    return True


def add_custom_station(app):
    name_var = getattr(app, "radio_custom_name_var", None)
    url_var = getattr(app, "radio_custom_url_var", None)
    homepage_var = getattr(app, "radio_custom_homepage_var", None)
    category_var = getattr(app, "radio_custom_category_var", None)
    edit_station_id = str(
        getattr(app, "radio_custom_edit_station_id", "") or ""
    ).strip()

    name = str(name_var.get() if name_var is not None else "" or "").strip()
    url = str(url_var.get() if url_var is not None else "" or "").strip()
    homepage = str(homepage_var.get() if homepage_var is not None else "" or "").strip()
    category = str(category_var.get() if category_var is not None else "" or "").strip()
    if not name or not url:
        set_radio_status(
            app,
            _tr(
                app,
                "radio_status_name_url_required",
                "Name und URL werden für eigene Sender benötigt.",
            ),
        )
        return False

    station = normalize_station_entry(
        {
            "id": edit_station_id or _slugify_station_id(name),
            "name": name,
            "url": url,
            "homepage": homepage,
            "category": category,
            "custom": True,
        },
        custom=True,
    )
    if station is None:
        set_radio_status(
            app,
            _tr(
                app,
                "radio_status_custom_create_failed",
                "Eigenen Radiosender konnte nicht angelegt werden.",
            ),
        )
        return False

    db = list(getattr(app, "radio_db", []) or [])
    existing_ids = {item.get("id", "") for item in db if isinstance(item, dict)}
    if not edit_station_id and station["id"] in existing_ids:
        station["id"] = f"{station['id']}-{int(time.time())}"

    updated_existing = False
    for idx, item in enumerate(db):
        if item.get("id") == station["id"]:
            db[idx] = station
            updated_existing = True
            break
    if not updated_existing:
        db.append(station)

    if not save_radio_db(app, stations=db):
        set_radio_status(
            app,
            _tr(
                app,
                "radio_status_custom_create_failed",
                "Eigenen Radiosender konnte nicht angelegt werden.",
            ),
        )
        return False

    app.radio_db = db
    favorites = list(getattr(app, "radio_favorites", []) or [])
    favorite_updated = False
    for idx, item in enumerate(favorites):
        if item.get("id") == station["id"]:
            favorites[idx] = dict(station)
            favorite_updated = True
    if favorite_updated:
        save_radio_favorites(app, favorites=favorites)
        app.radio_favorites = favorites
    if getattr(app, "radio_current_station_id", "") == station["id"]:
        app.radio_current_station = dict(station)

    search_var = getattr(app, "radio_search_var", None)
    if search_var is not None:
        try:
            search_var.set(station["name"])
        except Exception:
            pass

    toggle_var = getattr(app, "radio_show_favorites_var", None)
    if toggle_var is not None:
        try:
            toggle_var.set(False)
        except Exception:
            pass
    toggle_text_var = getattr(app, "radio_toggle_favorites_text_var", None)
    if toggle_text_var is not None:
        try:
            toggle_text_var.set(_tr(app, "radio_show_favorites", "Favoriten anzeigen"))
        except Exception:
            pass

    save_radio_settings(app)
    refresh_radio_station_table(app, reset_page=True)
    refresh_radio_favorites_list(app)

    table = getattr(app, "radio_station_table", None)
    if table is not None:
        try:
            table.selection_set(station["id"])
            table.focus(station["id"])
            table.see(station["id"])
        except Exception:
            pass

    set_radio_status(
        app,
        (
            _tr(app, "radio_status_station_updated", "Sender aktualisiert: {name}")
            if edit_station_id
            else _tr(app, "radio_status_station_added", "Sender hinzugefügt: {name}")
        ).format(name=station["name"]),
    )
    if edit_station_id:
        _set_custom_form_state(
            app,
            edit_station_id=station["id"],
            status_message=_tr(
                app,
                "radio_custom_editing_status",
                "Bearbeite eigenen Sender: {name}",
            ).format(name=station["name"]),
        )
    else:
        clear_custom_station_form(app)
    return True


def play_favorite_selection(app, _event=None):
    listbox = getattr(app, "radio_favorites_list", None)
    if listbox is None:
        return False

    try:
        selection = listbox.curselection()
    except Exception:
        selection = ()
    if not selection:
        return False

    idx = int(selection[0])
    favorites = list(getattr(app, "radio_favorites", []) or [])
    if idx < 0 or idx >= len(favorites):
        return False
    station = favorites[idx]
    return play_radio_station(app, station.get("id", ""))
