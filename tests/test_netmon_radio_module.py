import inspect
import json
import os
import threading
import http.client
import zipfile
from types import SimpleNamespace

import pytest

from netmon.app import App
from netmon import netmon_projectm_sidecar
from netmon import netmon_radio_app
from netmon import netmon_radio_core
from netmon.features import radio_controller
from netmon.ui.tabs.radio_tab import build_radio_tab, _install_pane_drag_marker


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyTable:
    def __init__(self, selection=(), focus=""):
        self._selection = selection
        self._focus = focus

    def selection(self):
        return self._selection

    def focus(self):
        return self._focus


class DummyWidget:
    def __init__(self):
        self.calls = []

    def configure(self, **kwargs):
        self.calls.append(kwargs)


class DummyListbox:
    def __init__(self, selection=()):
        self.items = []
        self._selection = tuple(selection)
        self.activated = None
        self.focused = False

    def delete(self, start, end=None):
        self.items = []

    def insert(self, index, value):
        self.items.append(value)

    def curselection(self):
        return self._selection

    def selection_clear(self, start, end=None):
        self._selection = ()

    def selection_set(self, index):
        self._selection = (index,)

    def activate(self, index):
        self.activated = index

    def nearest(self, y):
        try:
            idx = int(y)
        except Exception:
            idx = 0
        if idx < 0:
            return 0
        return idx

    def focus_set(self):
        self.focused = True


class DummyEvent:
    def __init__(self, y=0):
        self.y = y


def test_normalize_station_entry_marks_custom_and_keeps_url():
    station = radio_controller.normalize_station_entry(
        {
            "name": "My Stream",
            "url": "https://example.com/live.mp3",
            "category": "Test",
        },
        custom=True,
    )

    assert station["id"] == "my-stream"
    assert station["name"] == "My Stream"
    assert station["url"] == "https://example.com/live.mp3"
    assert station["category"] == "Test"
    assert station["custom"] is True


def test_normalize_station_entry_rejects_disallowed_stream_scheme():
    station = radio_controller.normalize_station_entry(
        {
            "name": "Bad Stream",
            "url": "file:///etc/passwd",
            "category": "Test",
        }
    )

    assert station is None


def test_normalize_station_entry_keeps_allowed_resolved_url():
    station = radio_controller.normalize_station_entry(
        {
            "name": "Resolved Stream",
            "url": "https://example.com/live.m3u",
            "url_resolved": "rtsp://stream.example.com/live",
        }
    )

    assert station["url"] == "https://example.com/live.m3u"
    assert station["url_resolved"] == "rtsp://stream.example.com/live"


def test_normalize_station_entry_rejects_when_only_resolved_url_has_bad_scheme():
    station = radio_controller.normalize_station_entry(
        {
            "name": "Bad Resolved Stream",
            "url_resolved": "gopher://127.0.0.1:70/_secret",
        }
    )

    assert station is None


def test_normalize_station_entry_rejects_disallowed_homepage_scheme():
    station = radio_controller.normalize_station_entry(
        {
            "name": "Homepage Test",
            "url": "https://example.com/live.mp3",
            "homepage": "file:///etc/passwd",
        }
    )

    assert station["homepage"] == ""


def test_load_radio_runtime_bootstraps_defaults_into_user_config(tmp_path):
    default_path = tmp_path / "radio_stations.default.json"
    db_path = tmp_path / "radio_db.json"
    favorites_path = tmp_path / "radio_favorites.json"
    settings_path = tmp_path / "radio_settings.json"
    default_path.write_text(
        json.dumps(
            [
                {
                    "id": "seed-station",
                    "name": "Seed Station",
                    "url": "https://example.com/seed.mp3",
                    "category": "Seed",
                    "custom": False,
                }
            ]
        ),
        encoding="utf-8",
    )

    app = type("DummyApp", (), {})()
    app.radio_default_stations_path = str(default_path)
    app.radio_db_path = str(db_path)
    app.radio_favorites_path = str(favorites_path)
    app.radio_settings_path = str(settings_path)
    app.radio_search_var = DummyVar("")
    app.radio_volume_var = DummyVar(10)
    app.log = lambda _message: None

    radio_controller.load_radio_runtime(app)

    assert db_path.exists()
    assert favorites_path.exists()
    assert settings_path.exists()
    assert len(app.radio_db) == 1
    assert app.radio_db[0]["name"] == "Seed Station"
    assert app.radio_settings["volume"] == 50
    assert app.radio_settings["station_list_columns"] == ["name", "genre", "bitrate"]
    assert app.radio_volume_var.get() == 50
    assert app.radio_recordings_dir.endswith("radio_recordings")
    assert app.radio_playlist_entries == []
    assert app.radio_playlist_path.endswith("radio_playlist.m3u")
    assert app.radio_playlists_dir.endswith("radio_playlists")


def test_build_radio_paths_uses_documents_dir_for_radio_user_files(
    monkeypatch, tmp_path
):
    docs_dir = tmp_path / "Documents" / "NetMon"
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    config_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_documents_dir", lambda: str(docs_dir)
    )
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_config_dir", lambda: str(config_dir)
    )
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_state_dir", lambda: str(state_dir)
    )

    paths = netmon_radio_core.build_radio_paths()

    radio_dir = docs_dir / "Radio"
    assert paths.radio_db_path == str(radio_dir / "radio_db.json")
    assert paths.radio_db_meta_path == str(radio_dir / "radio_db_meta.json")
    assert paths.radio_stations_path == str(radio_dir / "radio_stations.json")
    assert paths.radio_favorites_path == str(radio_dir / "radio_favorites.json")
    assert paths.radio_settings_path == str(radio_dir / "radio_settings.json")
    assert paths.radio_host_state_path == str(state_dir / "radio_host_state.json")


def test_build_radio_paths_migrates_legacy_radio_user_files(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Documents" / "NetMon"
    config_dir = tmp_path / "config"
    state_dir = tmp_path / "state"
    config_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    (state_dir / "radio_db.json").write_text('{"hello": "db"}', encoding="utf-8")
    (state_dir / "radio_db_meta.json").write_text('{"hello": "meta"}', encoding="utf-8")
    (config_dir / "radio_stations.json").write_text(
        '{"hello": "stations"}', encoding="utf-8"
    )
    (config_dir / "radio_favorites.json").write_text(
        '{"hello": "favorites"}', encoding="utf-8"
    )
    (config_dir / "radio_settings.json").write_text(
        '{"hello": "settings"}', encoding="utf-8"
    )
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_documents_dir", lambda: str(docs_dir)
    )
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_config_dir", lambda: str(config_dir)
    )
    monkeypatch.setattr(
        netmon_radio_core, "get_netmon_state_dir", lambda: str(state_dir)
    )

    paths = netmon_radio_core.build_radio_paths()

    assert json.loads(
        (docs_dir / "Radio" / "radio_db.json").read_text(encoding="utf-8")
    ) == {"hello": "db"}
    assert json.loads(
        (docs_dir / "Radio" / "radio_db_meta.json").read_text(encoding="utf-8")
    ) == {"hello": "meta"}
    assert json.loads(
        (docs_dir / "Radio" / "radio_stations.json").read_text(encoding="utf-8")
    ) == {"hello": "stations"}
    assert json.loads(
        (docs_dir / "Radio" / "radio_favorites.json").read_text(encoding="utf-8")
    ) == {"hello": "favorites"}
    assert json.loads(
        (docs_dir / "Radio" / "radio_settings.json").read_text(encoding="utf-8")
    ) == {"hello": "settings"}
    assert paths.radio_settings_path == str(docs_dir / "Radio" / "radio_settings.json")


def test_radio_handover_payload_roundtrip_applies_runtime_state():
    app = type("DummyApp", (), {})()
    app.radio_settings_path = "/tmp/radio-settings.json"
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_current_station_id = "station-1"
    app.radio_current_station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/1.mp3",
    }
    app.radio_proc = object()
    app.radio_volume_var = DummyVar(67)
    app.radio_eq_bass_var = DummyVar(3)
    app.radio_eq_mid_var = DummyVar(-2)
    app.radio_eq_treble_var = DummyVar(4)
    app.radio_search_var = DummyVar("ambient")
    app.radio_title_var = DummyVar("Titel: Artist - Track")
    app._app_theme = {
        "name": "pop",
        "accent": "#ff3366",
        "panel_bg": "#fff1f6",
        "tab_bg": "#ffd4e3",
    }
    app.log = lambda _message: None
    app.tr = lambda _key, default=None: default

    save_calls = []
    refresh_calls = []
    play_calls = []
    original_save = radio_controller.save_radio_settings
    original_refresh = radio_controller.refresh_radio_ui
    original_play = radio_controller.play_radio_station
    original_preview = radio_controller.on_radio_eq_preview
    try:
        radio_controller.save_radio_settings = (
            lambda _app: save_calls.append("save") or True
        )
        radio_controller.refresh_radio_ui = lambda _app: refresh_calls.append("refresh")
        radio_controller.play_radio_station = (
            lambda _app, station_id="": play_calls.append(station_id) or True
        )
        radio_controller.on_radio_eq_preview = lambda _app: None

        payload = radio_controller.build_radio_handover_payload(app)
        assert payload["current_station_id"] == "station-1"
        assert payload["current_title"] == "Titel: Artist - Track"
        assert payload["was_playing"] is True
        assert payload["theme"] == "pop"
        assert payload["theme_palette"]["accent"] == "#ff3366"
        assert payload["theme_palette"]["panel_bg"] == "#fff1f6"

        target = type("DummyTarget", (), {})()
        target.radio_settings = radio_controller.default_radio_settings()
        target._app_theme = {"name": "light"}
        target.radio_current_station_id = ""
        target.radio_current_station = None
        target.radio_search_var = DummyVar("")
        target.radio_volume_var = DummyVar(0)
        target.radio_eq_bass_var = DummyVar(0)
        target.radio_eq_mid_var = DummyVar(0)
        target.radio_eq_treble_var = DummyVar(0)
        target.radio_title_var = DummyVar("")
        target.radio_header_status_var = DummyVar("")
        target.radio_handover_title = ""
        target_theme_palette_calls = []
        target.apply_theme_palette = (
            lambda theme_name, palette: target_theme_palette_calls.append(
                (theme_name, dict(palette))
            )
        )
        target.log = lambda _message: None
        target.tr = lambda _key, default=None: default

        assert (
            radio_controller.apply_radio_handover_payload(
                target,
                payload,
                auto_play=True,
            )
            is True
        )
    finally:
        radio_controller.save_radio_settings = original_save
        radio_controller.refresh_radio_ui = original_refresh
        radio_controller.play_radio_station = original_play
        radio_controller.on_radio_eq_preview = original_preview

    assert target.radio_current_station_id == "station-1"
    assert target.radio_current_station["name"] == "Station 1"
    assert target.radio_search_var.get() == "ambient"
    assert target.radio_volume_var.get() == 67
    assert target.radio_eq_bass_var.get() == 3
    assert target.radio_eq_mid_var.get() == -2
    assert target.radio_eq_treble_var.get() == 4
    assert target.radio_title_var.get() == "Titel: Artist - Track"
    assert target.radio_handover_title == "Titel: Artist - Track"
    assert target.radio_settings["theme"] == "pop"
    assert target_theme_palette_calls == [("pop", payload["theme_palette"])]
    assert refresh_calls == ["refresh"]
    assert play_calls == ["station-1"]
    assert save_calls == ["save", "save"]


def test_apply_radio_handover_payload_normalizes_pop_user_theme_name():
    target = type("DummyTarget", (), {})()
    target.radio_settings = radio_controller.default_radio_settings()
    target.radio_search_var = DummyVar("")
    target.radio_volume_var = DummyVar(0)
    target.radio_eq_bass_var = DummyVar(0)
    target.radio_eq_mid_var = DummyVar(0)
    target.radio_eq_treble_var = DummyVar(0)
    target.radio_title_var = DummyVar("")
    target.radio_header_status_var = DummyVar("")
    target.radio_handover_title = ""
    target.log = lambda _message: None
    target.tr = lambda _key, default=None: default

    theme_calls = []
    target.apply_theme = lambda theme_name: theme_calls.append(theme_name)

    original_save = radio_controller.save_radio_settings
    original_refresh = radio_controller.refresh_radio_ui
    original_preview = radio_controller.on_radio_eq_preview
    try:
        radio_controller.save_radio_settings = lambda _app: True
        radio_controller.refresh_radio_ui = lambda _app: None
        radio_controller.on_radio_eq_preview = lambda _app: None

        assert (
            radio_controller.apply_radio_handover_payload(
                target,
                {"theme": "Pop (User)"},
            )
            is True
        )
    finally:
        radio_controller.save_radio_settings = original_save
        radio_controller.refresh_radio_ui = original_refresh
        radio_controller.on_radio_eq_preview = original_preview

    assert target.radio_settings["theme"] == "pop"
    assert theme_calls == ["pop"]


def test_sync_radio_theme_to_current_theme_passes_custom_pop_palette_to_panel():
    panel_calls = []
    app = SimpleNamespace(
        _app_theme={
            "name": "pop",
            "accent": "#ff3366",
            "panel_bg": "#fff1f6",
            "tab_bg": "#ffd4e3",
        },
        radio_embedded_panel=SimpleNamespace(
            radio_settings={},
            apply_theme_palette=lambda theme_name, palette: panel_calls.append(
                (theme_name, dict(palette))
            ),
        ),
    )

    assert App._sync_radio_theme_to_current_theme(app) is True
    assert app.radio_embedded_panel.radio_settings["theme"] == "pop"
    assert panel_calls == [
        (
            "pop",
            {
                "name": "pop",
                "accent": "#ff3366",
                "panel_bg": "#fff1f6",
                "tab_bg": "#ffd4e3",
            },
        )
    ]


def test_search_radio_matches_name_tags_and_limits_results():
    app = type("DummyApp", (), {})()
    app.radio_settings = {"excluded_genres": []}
    app.radio_db = [
        {
            "id": "one",
            "name": "Drone Zone",
            "url": "https://example.com/drone.mp3",
            "category": "Ambient",
            "tags": ["ambient", "drone"],
            "custom": False,
        },
        {
            "id": "two",
            "name": "World Service",
            "url": "https://news.example.com/live",
            "category": "News",
            "tags": ["world", "news"],
            "custom": False,
        },
    ] + [
        {
            "id": f"bulk-{idx}",
            "name": f"Bulk {idx}",
            "url": f"https://example.com/{idx}.mp3",
            "category": "Bulk",
            "tags": ["bulk"],
            "custom": False,
        }
        for idx in range(280)
    ]

    assert [item["id"] for item in radio_controller.search_radio(app, "drone")] == [
        "one"
    ]
    assert [item["id"] for item in radio_controller.search_radio(app, "world")] == [
        "two"
    ]
    assert radio_controller.search_radio(app, "") == []
    assert len(radio_controller.search_radio(app, "bulk")) == 280


def test_filter_radio_db_rows_keeps_required_fields_only():
    rows = radio_controller._filter_radio_db_rows(
        [
            {
                "name": "Deep Radio",
                "url": "https://example.com/live.mp3",
                "url_resolved": "https://cdn.example.com/live.mp3",
                "homepage": "https://example.com",
                "favicon": "https://example.com/icon.png",
                "tags": "ambient, drone",
                "country": "Germany",
                "countrycode": "DE",
                "language": "de",
                "codec": "MP3",
                "bitrate": "192",
                "lastcheckok": 1,
                "votes": "77",
                "clickcount": "12",
                "stationuuid": "should-not-be-saved",
            }
        ]
    )

    assert len(rows) == 1
    assert rows[0]["name"] == "Deep Radio"
    assert rows[0]["tags"] == ["ambient", "drone"]
    assert rows[0]["bitrate"] == 192
    assert rows[0]["lastcheckok"] is True
    assert "stationuuid" not in rows[0]


def test_extract_stream_title_prefers_icy_title_then_title():
    assert (
        radio_controller._extract_stream_title(
            {"icy-title": "Artist - Track", "title": "Fallback"}
        )
        == "Artist - Track"
    )
    assert radio_controller._extract_stream_title({"title": "Fallback"}) == "Fallback"
    assert radio_controller._extract_stream_title({"artist": "A", "title": "B"}) == "B"


def test_read_radio_stream_title_falls_back_to_media_title():
    app = type("DummyApp", (), {})()

    original_query_property = radio_controller._query_mpv_property
    try:
        responses = {
            "metadata": {},
            "media-title": "Station Artist - Station Track",
            "stream-title": "",
        }
        radio_controller._query_mpv_property = (
            lambda _app, property_name: responses.get(property_name)
        )

        title, debug_payload = radio_controller._read_radio_stream_title(app)
        assert title == "Station Artist - Station Track"
        assert "metadata" in debug_payload
        assert "media-title" in debug_payload
    finally:
        radio_controller._query_mpv_property = original_query_property


def test_parse_icy_stream_title_extracts_streamtitle_field():
    assert (
        radio_controller._parse_icy_stream_title(
            "StreamTitle='Artist - Track';StreamUrl='';"
        )
        == "Artist - Track"
    )


def test_read_radio_stream_title_falls_back_to_icy_fetch():
    app = type("DummyApp", (), {})()
    app.radio_current_station_id = "station-1"
    app.radio_current_station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/live.mp3",
    }

    original_query_property = radio_controller._query_mpv_property
    original_fetch_icy_title = radio_controller._fetch_icy_stream_title
    try:
        radio_controller._query_mpv_property = lambda _app, _property_name: ""
        radio_controller._fetch_icy_stream_title = (
            lambda stream_url, timeout=4: "ICY Artist - ICY Track"
        )

        title, debug_payload = radio_controller._read_radio_stream_title(app)

        assert title == "ICY Artist - ICY Track"
        assert debug_payload["icy-fetch"] == "ICY Artist - ICY Track"
    finally:
        radio_controller._query_mpv_property = original_query_property
        radio_controller._fetch_icy_stream_title = original_fetch_icy_title


def test_add_to_favorites_saves_full_station_payload():
    app = type("DummyApp", (), {})()
    app.radio_favorites = []
    app.radio_favorites_path = "/tmp/radio-favorites.json"
    calls = []
    app.log = lambda _message: None
    radio_controller.refresh_radio_favorites_list = lambda _app: calls.append("refresh")
    radio_controller.save_radio_favorites = (
        lambda _app, favorites=None: calls.append(list(favorites or [])) or True
    )

    station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/1.mp3",
        "category": "Test",
        "tags": ["alpha"],
    }

    assert radio_controller.add_to_favorites(app, station) is True
    assert calls[-2][0]["name"] == "Station 1"
    assert calls[-1] == "refresh"


def test_play_radio_station_clears_connecting_title_once_process_starts():
    app = type("DummyApp", (), {})()
    app.radio_volume_var = DummyVar(50)
    app.radio_title_var = DummyVar("")
    app.radio_header_status_var = DummyVar("")
    app.radio_status_var = DummyVar("")
    app.radio_now_playing_var = DummyVar("")
    app.radio_stream_url_var = DummyVar("")
    app.radio_bitrate_var = DummyVar("")
    app.radio_search_results = []
    app.radio_favorites = []
    app.radio_current_station_id = ""
    app.radio_current_station = None
    app.radio_proc = None
    app.radio_stop_requested = False
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_station_table = None
    app.after = lambda _delay, callback, *args: callback(*args)
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/live.mp3",
    }

    class FakeProc:
        def terminate(self):
            return None

        def wait(self, timeout=None):
            return 0

    class ImmediateThread:
        def __init__(self, target=None, args=(), kwargs=None, daemon=None):
            self.target = target
            self.args = args
            self.kwargs = kwargs or {}

        def start(self):
            if self.target is not None:
                self.target(*self.args, **self.kwargs)

    original_radio_available = radio_controller.radio_available
    original_resolve_target_station = radio_controller._resolve_target_station
    original_stop_radio_playback = radio_controller.stop_radio_playback
    original_schedule_ui = radio_controller._schedule_ui
    original_radio_ipc_path = radio_controller._radio_ipc_path
    original_cleanup_radio_ipc_path = radio_controller._cleanup_radio_ipc_path
    original_eq_filter = radio_controller.radio_eq_filter_spec
    original_popen = radio_controller.subprocess.Popen
    original_thread = threading.Thread
    original_wait_process = radio_controller._wait_for_radio_process
    original_poll_metadata = radio_controller._poll_radio_metadata
    original_save_settings = radio_controller.save_radio_settings
    original_update_header = radio_controller.update_radio_header
    original_refresh_table = radio_controller.refresh_radio_station_table
    original_refresh_favorites = radio_controller.refresh_radio_favorites_list
    try:
        radio_controller.radio_available = lambda _app: True
        radio_controller._resolve_target_station = lambda _app, station_id="": station
        radio_controller.stop_radio_playback = lambda _app, **_kwargs: True
        radio_controller._schedule_ui = lambda _app, callback: callback()
        radio_controller._radio_ipc_path = lambda _app: "/tmp/netmon-radio-test.sock"
        radio_controller._cleanup_radio_ipc_path = lambda _app: None
        radio_controller.radio_eq_filter_spec = lambda _app: ""
        radio_controller.subprocess.Popen = lambda *args, **kwargs: FakeProc()
        threading.Thread = ImmediateThread
        radio_controller._wait_for_radio_process = lambda *_args, **_kwargs: None
        radio_controller._poll_radio_metadata = lambda *_args, **_kwargs: None
        radio_controller.save_radio_settings = lambda _app: True
        radio_controller.update_radio_header = lambda _app: None
        radio_controller.refresh_radio_station_table = lambda _app: None
        radio_controller.refresh_radio_favorites_list = lambda _app: None

        assert radio_controller.play_radio_station(app, "station-1") is True
    finally:
        radio_controller.radio_available = original_radio_available
        radio_controller._resolve_target_station = original_resolve_target_station
        radio_controller.stop_radio_playback = original_stop_radio_playback
        radio_controller._schedule_ui = original_schedule_ui
        radio_controller._radio_ipc_path = original_radio_ipc_path
        radio_controller._cleanup_radio_ipc_path = original_cleanup_radio_ipc_path
        radio_controller.radio_eq_filter_spec = original_eq_filter
        radio_controller.subprocess.Popen = original_popen
        threading.Thread = original_thread
        radio_controller._wait_for_radio_process = original_wait_process
        radio_controller._poll_radio_metadata = original_poll_metadata
        radio_controller.save_radio_settings = original_save_settings
        radio_controller.update_radio_header = original_update_header
        radio_controller.refresh_radio_station_table = original_refresh_table
        radio_controller.refresh_radio_favorites_list = original_refresh_favorites

    assert app.radio_current_station_id == "station-1"
    assert app.radio_title_var.get() == "Titel: -"


def test_stop_radio_playback_uses_targeted_pkill_fallback(monkeypatch):
    app = type("DummyApp", (), {})()
    app.radio_proc = None
    app.radio_stop_requested = False
    app.radio_current_station_id = "station-1"
    app.radio_ipc_path = "/tmp/netmon-radio-test.sock"
    app.radio_title_var = DummyVar("")
    app.radio_header_status_var = DummyVar("")
    app.radio_status_var = DummyVar("")
    app.radio_now_playing_var = DummyVar("")
    app.radio_stream_url_var = DummyVar("")
    app.radio_bitrate_var = DummyVar("")
    app.after = lambda _delay, callback, *args: callback(*args)
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    class FakeProc:
        def terminate(self):
            raise RuntimeError("terminate failed")

        def wait(self, timeout=None):
            raise RuntimeError("wait failed")

        def kill(self):
            raise RuntimeError("kill failed")

        def poll(self):
            return None

    app.radio_proc = FakeProc()
    calls = []

    monkeypatch.setattr(
        radio_controller,
        "_cleanup_radio_ipc_path",
        lambda _app: calls.append("cleanup"),
    )
    monkeypatch.setattr(
        radio_controller,
        "_force_kill_radio_process_by_ipc",
        lambda ipc_path: calls.append(("pkill", ipc_path)) or True,
    )

    assert radio_controller.stop_radio_playback(app, async_mode=False) is True
    assert ("pkill", "/tmp/netmon-radio-test.sock") in calls


def test_radio_source_includes_playback_lock_and_targeted_kill_fallback():
    source = inspect.getsource(radio_controller)

    assert "def _radio_playback_lock(app):" in source
    assert "with _radio_playback_lock(app):" in source
    assert "def _force_kill_radio_process_by_ipc(ipc_path: str) -> bool:" in source


def test_start_radio_recording_uses_ffmpeg_and_updates_status(tmp_path):
    app = type("DummyApp", (), {})()
    app.netmon_state_dir = str(tmp_path)
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_recordings_dir = str(tmp_path / "records")
    app.radio_record_status_var = DummyVar("")
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_record_proc = None
    app.radio_current_station_id = "station-1"
    app.radio_current_station = {
        "id": "station-1",
        "name": "Station 1",
        "url": "https://example.com/live.mp3",
    }
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    class FakeProc:
        def __init__(self):
            self.pid = 1

        def poll(self):
            return None

    calls = []
    original_has_cmd = radio_controller.has_cmd
    original_popen = radio_controller.subprocess.Popen
    original_thread = threading.Thread
    try:
        radio_controller.has_cmd = lambda name: name == "ffmpeg"
        radio_controller.subprocess.Popen = (
            lambda cmd, **kwargs: calls.append(cmd) or FakeProc()
        )

        class IgnoreThread:
            def __init__(self, target=None, args=(), kwargs=None, daemon=None):
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}

            def start(self):
                return None

        threading.Thread = IgnoreThread

        assert radio_controller.start_radio_recording(app) is True
    finally:
        radio_controller.has_cmd = original_has_cmd
        radio_controller.subprocess.Popen = original_popen
        threading.Thread = original_thread

    assert calls
    assert calls[0][0] == "ffmpeg"
    assert "libmp3lame" in calls[0]
    assert app.radio_record_proc is not None
    assert "Aufnahme läuft:" in app.radio_record_status_var.get()
    assert "Aufnahmeordner:" in app.radio_record_dir_var.get()
    assert "Letzte Aufnahme:" in app.radio_record_file_var.get()


def test_start_radio_recording_prefers_context_menu_station(tmp_path):
    app = type("DummyApp", (), {})()
    app.netmon_state_dir = str(tmp_path)
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_recordings_dir = str(tmp_path / "records")
    app.radio_record_status_var = DummyVar("")
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_record_proc = None
    app.radio_current_station_id = "station-1"
    app.radio_context_station_id = "station-2"
    app.radio_stations = [
        {
            "id": "station-1",
            "name": "Station 1",
            "url": "https://example.com/live-1.mp3",
        },
        {
            "id": "station-2",
            "name": "Station 2",
            "url": "https://example.com/live-2.mp3",
        },
    ]
    app.radio_search_results = list(app.radio_stations)
    app.radio_current_station = app.radio_stations[0]
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    class FakeProc:
        def __init__(self):
            self.pid = 1

        def poll(self):
            return None

    calls = []
    original_has_cmd = radio_controller.has_cmd
    original_popen = radio_controller.subprocess.Popen
    original_thread = threading.Thread
    try:
        radio_controller.has_cmd = lambda name: name == "ffmpeg"
        radio_controller.subprocess.Popen = (
            lambda cmd, **kwargs: calls.append(cmd) or FakeProc()
        )

        class IgnoreThread:
            def __init__(self, target=None, args=(), kwargs=None, daemon=None):
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}

            def start(self):
                return None

        threading.Thread = IgnoreThread

        assert radio_controller.start_radio_recording(app) is True
    finally:
        radio_controller.has_cmd = original_has_cmd
        radio_controller.subprocess.Popen = original_popen
        threading.Thread = original_thread

    assert calls
    assert any("live-2.mp3" in str(part) for part in calls[0])


def test_recording_file_path_includes_station_title_and_date(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(tmp_path)
    app.radio_title_var = DummyVar("Titel: Artist - Track")
    app.tr = lambda _key, default=None: default

    path = radio_controller._recording_file_path(
        app,
        {
            "name": "1.FM - Ambient & Chill",
        },
    )

    basename = os.path.basename(path)
    assert basename == "1-fm-ambient-chill_track_artist.mp3"
    assert basename.endswith(".mp3")


def test_refresh_radio_recording_ui_updates_dir_and_last_file_text(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_record_proc = None
    app.radio_recordings_dir = str(tmp_path / "records")
    app.radio_last_record_path = str(tmp_path / "records" / "demo.mp3")
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_record_transport_button = DummyWidget()
    app.radio_record_start_button = DummyWidget()
    app.radio_record_stop_button = DummyWidget()
    app.radio_record_folder_button = DummyWidget()
    app.radio_record_open_folder_button = DummyWidget()
    app.radio_record_open_last_button = DummyWidget()
    app.radio_record_play_last_button = DummyWidget()

    os.makedirs(tmp_path / "records", exist_ok=True)
    (tmp_path / "records" / "demo.mp3").write_text("demo", encoding="utf-8")

    original_has_cmd = radio_controller.has_cmd
    try:
        radio_controller.has_cmd = lambda name: name == "ffmpeg"
        radio_controller.refresh_radio_recording_ui(app)
    finally:
        radio_controller.has_cmd = original_has_cmd

    assert app.radio_record_dir_var.get().endswith(str(tmp_path / "records"))
    assert app.radio_record_file_var.get() == "Letzte Aufnahme: demo.mp3"
    assert any(
        call.get("state") == "normal"
        for call in app.radio_record_transport_button.calls
    )
    assert app.radio_record_open_last_button.calls[-1]["state"] == "normal"
    assert app.radio_record_play_last_button.calls[-1]["state"] == "normal"


def test_play_last_radio_recording_uses_mpv(tmp_path):
    record_path = tmp_path / "demo.mp3"
    record_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_last_record_path = str(record_path)
    app.radio_record_status_var = DummyVar("")
    app.radio_title_var = DummyVar("")
    app.radio_header_status_var = DummyVar("")
    app.radio_status_var = DummyVar("")
    app.radio_now_playing_var = DummyVar("")
    app.radio_stream_url_var = DummyVar("")
    app.radio_bitrate_var = DummyVar("")
    app.radio_proc = None
    app.radio_stop_requested = False
    app.after = lambda _delay, callback, *args: callback(*args)
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    calls = []

    class FakeProc:
        def wait(self):
            return 0

    original_popen = radio_controller.subprocess.Popen
    original_thread = threading.Thread
    original_stop = radio_controller.stop_radio_playback
    original_wait = radio_controller._wait_for_radio_process
    original_poll = radio_controller._poll_radio_metadata
    try:
        radio_controller.subprocess.Popen = (
            lambda cmd, **kwargs: calls.append(cmd) or FakeProc()
        )
        radio_controller.stop_radio_playback = lambda _app, **_kwargs: True
        radio_controller._wait_for_radio_process = lambda *_args, **_kwargs: None
        radio_controller._poll_radio_metadata = lambda *_args, **_kwargs: None

        class ImmediateThread:
            def __init__(self, target=None, args=(), kwargs=None, daemon=None):
                self.target = target
                self.args = args
                self.kwargs = kwargs or {}

            def start(self):
                if self.target is not None:
                    self.target(*self.args, **self.kwargs)

        threading.Thread = ImmediateThread

        assert radio_controller.play_last_radio_recording(app) is True
    finally:
        radio_controller.subprocess.Popen = original_popen
        radio_controller.stop_radio_playback = original_stop
        radio_controller._wait_for_radio_process = original_wait
        radio_controller._poll_radio_metadata = original_poll
        threading.Thread = original_thread

    assert calls
    assert calls[0][0] == "mpv"
    assert calls[0][-1] == str(record_path)


def test_open_selected_station_homepage_rejects_disallowed_scheme():
    app = type("DummyApp", (), {})()
    statuses = []
    opened = []

    original_resolve_target_station = radio_controller._resolve_target_station
    original_selected_station_id = radio_controller._selected_station_id
    original_webbrowser_open = radio_controller.webbrowser.open
    original_set_radio_status = radio_controller.set_radio_status
    try:
        radio_controller._resolve_target_station = lambda _app, station_id="": {
            "homepage": "file:///etc/passwd",
            "url": "rtsp://stream.example.com/live",
        }
        radio_controller._selected_station_id = lambda _app: "station-1"
        radio_controller.webbrowser.open = lambda url, new=0: opened.append((url, new))
        radio_controller.set_radio_status = lambda _app, message: statuses.append(
            message
        )

        assert radio_controller.open_selected_station_homepage(app) is False
    finally:
        radio_controller._resolve_target_station = original_resolve_target_station
        radio_controller._selected_station_id = original_selected_station_id
        radio_controller.webbrowser.open = original_webbrowser_open
        radio_controller.set_radio_status = original_set_radio_status

    assert opened == []
    assert statuses[-1] == "Keine Homepage vorhanden."


def test_open_selected_station_homepage_opens_https():
    app = type("DummyApp", (), {})()
    statuses = []
    opened = []

    original_resolve_target_station = radio_controller._resolve_target_station
    original_selected_station_id = radio_controller._selected_station_id
    original_webbrowser_open = radio_controller.webbrowser.open
    original_set_radio_status = radio_controller.set_radio_status
    try:
        radio_controller._resolve_target_station = lambda _app, station_id="": {
            "homepage": "https://example.com",
            "url": "https://example.com/live.mp3",
        }
        radio_controller._selected_station_id = lambda _app: "station-1"
        radio_controller.webbrowser.open = lambda url, new=0: opened.append((url, new))
        radio_controller.set_radio_status = lambda _app, message: statuses.append(
            message
        )

        assert radio_controller.open_selected_station_homepage(app) is True
    finally:
        radio_controller._resolve_target_station = original_resolve_target_station
        radio_controller._selected_station_id = original_selected_station_id
        radio_controller.webbrowser.open = original_webbrowser_open
        radio_controller.set_radio_status = original_set_radio_status

    assert opened == [("https://example.com", 2)]
    assert statuses[-1] == "Homepage geöffnet."


def test_add_custom_station_persists_into_radio_db_and_updates_search():
    app = type("DummyApp", (), {})()
    app.radio_db = []
    app.radio_custom_name_var = DummyVar("My Custom Radio")
    app.radio_custom_url_var = DummyVar("https://example.com/live.mp3")
    app.radio_custom_homepage_var = DummyVar("https://example.com")
    app.radio_custom_category_var = DummyVar("Community")
    app.radio_custom_submit_text_var = DummyVar("Sender hinzufügen")
    app.radio_custom_form_status_var = DummyVar("")
    app.radio_custom_edit_station_id = ""
    app.radio_search_var = DummyVar("")
    app.radio_show_favorites_var = DummyVar(True)
    app.radio_toggle_favorites_text_var = DummyVar("")
    app.radio_station_table = None
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    saved = []
    refresh_calls = []
    statuses = []
    original_save_db = radio_controller.save_radio_db
    original_refresh_table = radio_controller.refresh_radio_station_table
    original_refresh_favorites = radio_controller.refresh_radio_favorites_list
    original_set_status = radio_controller.set_radio_status
    original_save_settings = radio_controller.save_radio_settings
    try:
        radio_controller.save_radio_db = (
            lambda _app, stations=None: saved.append(list(stations or [])) or True
        )
        radio_controller.refresh_radio_station_table = (
            lambda _app, reset_page=False: refresh_calls.append(reset_page)
        )
        radio_controller.refresh_radio_favorites_list = (
            lambda _app: refresh_calls.append("favorites")
        )
        radio_controller.set_radio_status = lambda _app, message: statuses.append(
            message
        )
        radio_controller.save_radio_settings = lambda _app: True

        assert radio_controller.add_custom_station(app) is True
        assert saved[-1][0]["name"] == "My Custom Radio"
        assert saved[-1][0]["custom"] is True
        assert saved[-1][0]["homepage"] == "https://example.com"
        assert app.radio_search_var.get() == "My Custom Radio"
        assert app.radio_show_favorites_var.get() is False
        assert app.radio_custom_name_var.get() == ""
        assert app.radio_custom_url_var.get() == ""
        assert app.radio_custom_homepage_var.get() == ""
        assert app.radio_custom_category_var.get() == ""
        assert app.radio_custom_submit_text_var.get() == "Sender hinzufügen"
        assert app.radio_custom_form_status_var.get() == ""
        assert refresh_calls == [True, "favorites"]
        assert statuses[-1] == "Sender hinzugefügt: My Custom Radio"
    finally:
        radio_controller.save_radio_db = original_save_db
        radio_controller.refresh_radio_station_table = original_refresh_table
        radio_controller.refresh_radio_favorites_list = original_refresh_favorites
        radio_controller.set_radio_status = original_set_status
        radio_controller.save_radio_settings = original_save_settings


def test_delete_selected_station_removes_custom_station_from_db_and_favorites():
    app = type("DummyApp", (), {})()
    app.radio_current_station_id = ""
    app.radio_station_table = None
    app.radio_db = [
        {
            "id": "custom-1",
            "name": "Custom 1",
            "url": "https://example.com/custom.mp3",
            "custom": True,
        },
        {
            "id": "preset-1",
            "name": "Preset 1",
            "url": "https://example.com/preset.mp3",
            "custom": False,
        },
    ]
    app.radio_favorites = [
        {
            "id": "custom-1",
            "name": "Custom 1",
            "url": "https://example.com/custom.mp3",
            "custom": True,
        }
    ]
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    saved_db = []
    saved_favorites = []
    statuses = []
    original_selected_station_id = radio_controller._selected_station_id
    original_askyesno = radio_controller.messagebox.askyesno
    original_save_db = radio_controller.save_radio_db
    original_save_favorites = radio_controller.save_radio_favorites
    original_refresh_ui = radio_controller.refresh_radio_ui
    original_set_status = radio_controller.set_radio_status
    try:
        radio_controller._selected_station_id = lambda _app: "custom-1"
        radio_controller.messagebox.askyesno = lambda *_args, **_kwargs: True
        radio_controller.save_radio_db = (
            lambda _app, stations=None: saved_db.append(list(stations or _app.radio_db))
            or True
        )
        radio_controller.save_radio_favorites = (
            lambda _app, favorites=None: saved_favorites.append(
                list(favorites or _app.radio_favorites)
            )
            or True
        )
        radio_controller.refresh_radio_ui = lambda _app: None
        radio_controller.set_radio_status = lambda _app, message: statuses.append(
            message
        )

        assert radio_controller.delete_selected_station(app) is True
        assert [item["id"] for item in app.radio_db] == ["preset-1"]
        assert app.radio_favorites == []
        assert [item["id"] for item in saved_db[-1]] == ["preset-1"]
        assert saved_favorites[-1] == []
        assert statuses[-1] == "Sender gelöscht: Custom 1"
    finally:
        radio_controller._selected_station_id = original_selected_station_id
        radio_controller.messagebox.askyesno = original_askyesno
        radio_controller.save_radio_db = original_save_db
        radio_controller.save_radio_favorites = original_save_favorites
        radio_controller.refresh_radio_ui = original_refresh_ui
        radio_controller.set_radio_status = original_set_status


def test_edit_selected_station_data_prefills_form_for_custom_station():
    app = type("DummyApp", (), {})()
    app.radio_db = [
        {
            "id": "custom-1",
            "name": "Custom 1",
            "url": "https://example.com/custom.mp3",
            "homepage": "https://custom.example.com",
            "category": "Community",
            "custom": True,
        }
    ]
    app.radio_favorites = []
    app.radio_search_results = []
    app.radio_custom_name_var = DummyVar("")
    app.radio_custom_url_var = DummyVar("")
    app.radio_custom_homepage_var = DummyVar("")
    app.radio_custom_category_var = DummyVar("")
    app.radio_custom_submit_text_var = DummyVar("")
    app.radio_custom_form_status_var = DummyVar("")
    app.radio_custom_edit_station_id = ""
    app.tr = lambda _key, default=None: default

    original_selected_station_id = radio_controller._selected_station_id
    try:
        radio_controller._selected_station_id = lambda _app: "custom-1"
        assert radio_controller.edit_selected_station_data(app) is True
        assert app.radio_custom_name_var.get() == "Custom 1"
        assert app.radio_custom_url_var.get() == "https://example.com/custom.mp3"
        assert app.radio_custom_homepage_var.get() == "https://custom.example.com"
        assert app.radio_custom_category_var.get() == "Community"
        assert app.radio_custom_edit_station_id == "custom-1"
        assert app.radio_custom_submit_text_var.get() == "Sender speichern"
        assert (
            app.radio_custom_form_status_var.get()
            == "Bearbeite eigenen Sender: Custom 1"
        )
    finally:
        radio_controller._selected_station_id = original_selected_station_id


def test_edit_selected_station_data_opens_custom_editor_when_available():
    app = type("DummyApp", (), {})()
    app.radio_db = [
        {
            "id": "custom-1",
            "name": "Custom 1",
            "url": "https://example.com/custom.mp3",
            "homepage": "https://custom.example.com",
            "category": "Community",
            "custom": True,
        }
    ]
    app.radio_favorites = []
    app.radio_search_results = []
    app.radio_custom_name_var = DummyVar("")
    app.radio_custom_url_var = DummyVar("")
    app.radio_custom_homepage_var = DummyVar("")
    app.radio_custom_category_var = DummyVar("")
    app.radio_custom_submit_text_var = DummyVar("")
    app.radio_custom_form_status_var = DummyVar("")
    app.radio_custom_edit_station_id = ""
    app.tr = lambda _key, default=None: default
    opened = []
    app.open_custom_radio_station_editor = lambda: opened.append("open")

    original_selected_station_id = radio_controller._selected_station_id
    try:
        radio_controller._selected_station_id = lambda _app: "custom-1"
        assert radio_controller.edit_selected_station_data(app) is True
    finally:
        radio_controller._selected_station_id = original_selected_station_id

    assert opened == ["open"]


def test_selected_station_id_falls_back_to_tree_focus():
    app = type("DummyApp", (), {})()
    app.radio_station_table = DummyTable(selection=(), focus="focused-station")

    assert radio_controller._selected_station_id(app) == "focused-station"


def test_selected_station_id_prefers_context_menu_row():
    app = type("DummyApp", (), {})()
    app.radio_context_station_id = "context-station"
    app.radio_station_table = DummyTable(
        selection=("selected-station",), focus="focused"
    )

    assert radio_controller._selected_station_id(app) == "context-station"


def test_add_custom_station_updates_existing_custom_station_when_editing():
    app = type("DummyApp", (), {})()
    app.radio_db = [
        {
            "id": "custom-1",
            "name": "Old Name",
            "url": "https://example.com/old.mp3",
            "homepage": "https://old.example.com",
            "category": "Old",
            "custom": True,
        }
    ]
    app.radio_favorites = [
        {
            "id": "custom-1",
            "name": "Old Name",
            "url": "https://example.com/old.mp3",
            "homepage": "https://old.example.com",
            "category": "Old",
            "custom": True,
        }
    ]
    app.radio_current_station_id = "custom-1"
    app.radio_current_station = dict(app.radio_db[0])
    app.radio_custom_name_var = DummyVar("New Name")
    app.radio_custom_url_var = DummyVar("https://example.com/new.mp3")
    app.radio_custom_homepage_var = DummyVar("https://new.example.com")
    app.radio_custom_category_var = DummyVar("Fresh")
    app.radio_custom_submit_text_var = DummyVar("")
    app.radio_custom_form_status_var = DummyVar("")
    app.radio_custom_edit_station_id = "custom-1"
    app.radio_search_var = DummyVar("")
    app.radio_show_favorites_var = DummyVar(False)
    app.radio_toggle_favorites_text_var = DummyVar("")
    app.radio_station_table = None
    app.tr = lambda _key, default=None: default
    app.log = lambda _message: None

    saved_db = []
    saved_favorites = []
    refresh_calls = []
    statuses = []
    original_save_db = radio_controller.save_radio_db
    original_save_favorites = radio_controller.save_radio_favorites
    original_refresh_table = radio_controller.refresh_radio_station_table
    original_refresh_favorites = radio_controller.refresh_radio_favorites_list
    original_set_status = radio_controller.set_radio_status
    original_save_settings = radio_controller.save_radio_settings
    try:
        radio_controller.save_radio_db = (
            lambda _app, stations=None: saved_db.append(list(stations or [])) or True
        )
        radio_controller.save_radio_favorites = (
            lambda _app, favorites=None: saved_favorites.append(list(favorites or []))
            or True
        )
        radio_controller.refresh_radio_station_table = (
            lambda _app, reset_page=False: refresh_calls.append(reset_page)
        )
        radio_controller.refresh_radio_favorites_list = (
            lambda _app: refresh_calls.append("favorites")
        )
        radio_controller.set_radio_status = lambda _app, message: statuses.append(
            message
        )
        radio_controller.save_radio_settings = lambda _app: True

        assert radio_controller.add_custom_station(app) is True
        assert len(saved_db[-1]) == 1
        assert saved_db[-1][0]["id"] == "custom-1"
        assert saved_db[-1][0]["name"] == "New Name"
        assert saved_db[-1][0]["homepage"] == "https://new.example.com"
        assert saved_favorites[-1][0]["name"] == "New Name"
        assert saved_favorites[-1][0]["homepage"] == "https://new.example.com"
        assert app.radio_current_station["name"] == "New Name"
        assert app.radio_custom_edit_station_id == "custom-1"
        assert app.radio_custom_submit_text_var.get() == "Sender speichern"
        assert statuses[-1] == "Sender aktualisiert: New Name"
    finally:
        radio_controller.save_radio_db = original_save_db
        radio_controller.save_radio_favorites = original_save_favorites
        radio_controller.refresh_radio_station_table = original_refresh_table
        radio_controller.refresh_radio_favorites_list = original_refresh_favorites
        radio_controller.set_radio_status = original_set_status
        radio_controller.save_radio_settings = original_save_settings


def test_toggle_radio_favorites_view_updates_filter_state():
    app = type("DummyApp", (), {})()
    app.radio_show_favorites_var = DummyVar(False)
    app.radio_toggle_favorites_text_var = DummyVar("")
    app.tr = lambda _key, default=None: default

    calls = []
    radio_controller.refresh_radio_station_table = (
        lambda _app, reset_page=False: calls.append("refresh")
    )

    assert radio_controller.toggle_radio_favorites_view(app) is True
    assert app.radio_show_favorites_var.get() is True
    assert app.radio_toggle_favorites_text_var.get() == "Alle Sender anzeigen"
    assert calls == ["refresh"]


def test_set_radio_search_page_updates_table_and_stays_in_range():
    app = type("DummyApp", (), {})()
    app.radio_search_page = 0
    app.radio_search_results = list(range(280))

    calls = []
    original_update = radio_controller.update_radio_results_table

    try:
        radio_controller.update_radio_results_table = lambda _app: calls.append("table")

        assert radio_controller.set_radio_search_page(app, 3) == 3
        assert app.radio_search_page == 3
        assert calls == ["table"]

        assert radio_controller.set_radio_search_page(app, 99) == 5
        assert app.radio_search_page == 5
    finally:
        radio_controller.update_radio_results_table = original_update


def test_commit_radio_volume_change_prefers_live_mpv_update():
    app = type("DummyApp", (), {})()
    app.radio_volume_var = DummyVar(42)
    app.radio_proc = object()
    app.radio_current_station_id = "station-1"
    app.radio_volume_text_var = DummyVar("")
    app.radio_volume_label_var = DummyVar("")
    app.radio_search_var = DummyVar("")
    app.tr = lambda _key, default=None: default

    calls = []
    radio_controller.save_radio_settings = lambda _app: calls.append("save")
    radio_controller.apply_radio_volume = lambda _app: calls.append("apply") or True
    radio_controller.play_radio_station = lambda _app, station_id: calls.append(
        ("restart", station_id)
    )

    radio_controller.commit_radio_volume_change(app)

    assert "save" in calls
    assert "apply" in calls
    assert ("restart", "station-1") not in calls
    assert app.radio_volume_text_var.get() == "Vol.: 42%"
    assert app.radio_volume_label_var.get() == "42%"


def test_on_radio_volume_preview_syncs_host_and_panel_slider_vars():
    app = type("DummyApp", (), {})()
    host = type("DummyHost", (), {})()
    app.radio_volume_var = DummyVar(58)
    app.radio_volume_text_var = DummyVar("")
    app.radio_volume_label_var = DummyVar("")
    app.radio_host_app = host
    app.tr = lambda _key, default=None: default
    host.radio_volume_var = DummyVar(0)
    host.radio_volume_text_var = DummyVar("")
    host.radio_volume_label_var = DummyVar("")

    radio_controller.on_radio_volume_preview(app)

    assert app.radio_volume_var.get() == 58
    assert host.radio_volume_var.get() == 58
    assert app.radio_volume_text_var.get() == "Vol.: 58%"
    assert host.radio_volume_text_var.get() == "Vol.: 58%"
    assert app.radio_volume_label_var.get() == "58%"
    assert host.radio_volume_label_var.get() == "58%"


def test_commit_radio_volume_change_restarts_stream_when_live_update_fails():
    app = type("DummyApp", (), {})()
    app.radio_volume_var = DummyVar(64)
    app.radio_proc = object()
    app.radio_current_station_id = "station-2"
    app.radio_volume_text_var = DummyVar("")
    app.radio_volume_label_var = DummyVar("")
    app.radio_search_var = DummyVar("")
    app.tr = lambda _key, default=None: default

    calls = []
    radio_controller.save_radio_settings = lambda _app: calls.append("save")
    radio_controller.apply_radio_volume = lambda _app: calls.append("apply") or False
    radio_controller.play_radio_station = lambda _app, station_id: calls.append(
        ("restart", station_id)
    )

    radio_controller.commit_radio_volume_change(app)

    assert "save" in calls
    assert "apply" in calls
    assert ("restart", "station-2") in calls


def test_radio_integration_hooks_are_present():
    init_source = inspect.getsource(App.__init__)
    close_source = inspect.getsource(App.on_close)
    preflight_source = inspect.getsource(App.preflight_dependencies)
    manual_summary_source = inspect.getsource(App._log_preflight_manual_summary)
    download_source = inspect.getsource(App.download_radio_db)

    assert "build_radio_tab(self)" in init_source
    assert "self.refresh_radio_ui()" in init_source
    assert 'self.radio_ipc_path = ""' in init_source
    assert "self.radio_search_page = 0" in init_source
    assert "self.radio_page_prev_button = None" in init_source
    assert "self.radio_page_next_button = None" in init_source
    assert "self.radio_title_var = tk.StringVar(" in init_source
    assert 'self.radio_light_state = "gray"' in init_source
    assert "radio_paths = (" in init_source
    assert "netmon_radio_core.build_radio_paths()" in init_source
    assert "self.radio_db_path = radio_paths.radio_db_path" in init_source
    assert "self.radio_settings_path = radio_paths.radio_settings_path" in init_source
    assert "self.stop_radio()" in close_source
    assert '"mpv": has_cmd("mpv")' in preflight_source
    assert '"pactl": has_cmd("pactl")' in preflight_source
    assert '"mpv (Radio)", "mpv"' in manual_summary_source
    assert '"projectM Visualizer", "projectm_visualizer"' in manual_summary_source
    assert '"timeshift": has_cmd("timeshift")' in preflight_source
    assert '("Timeshift", "timeshift")' in manual_summary_source
    assert "return radio_controller.download_radio_db(self)" in download_source
    assert (
        'self.set_feature_enabled("radio", checks.get("mpv", False))'
        in preflight_source
    )
    assert (
        "self.missing_dependencies = list(self.dep_installer_missing_keys)"
        in preflight_source
    )
    assert "self._log_dependency_installer_summary()" in preflight_source
    assert "self.update_radio_dependency_state()" in preflight_source
    assert "def set_radio_search_page(self, page):" in inspect.getsource(App)
    assert "if netmon_radio_core.standalone_radio_is_running():" in init_source
    assert "netmon_radio_core.set_radio_detached_state(True)" in init_source


def test_radio_tab_source_contains_external_radio_launcher():
    source = inspect.getsource(build_radio_tab)
    marker_source = inspect.getsource(_install_pane_drag_marker)

    assert 'text=app.tr("tools_tab_radio", "Radio")' in source
    assert 'text="⛶"' not in marker_source
    assert "top_expand" not in marker_source
    assert "bottom_expand" not in marker_source
    assert "marker_width = min(66, max(width - 24, 42))" in marker_source
    assert 'app.tr("radio_launcher_title", "NetMon Radio als externe App")' in source
    assert "NetMonRadioPanel(host, on_detach=_detach_from_tab, host_app=app)" in source
    assert 'app.tr("radio_launcher_reattach", "Radio anheften")' in source
    assert 'app.tr("radio_launcher_reopen", "Radio-App erneut öffnen")' not in source
    assert "app.refresh_radio_launcher_state = refresh_radio_launcher_state" in source
    assert "netmon_radio_core.write_radio_host_state(" not in source
    assert "_show_embedded_panel()" in source
    assert "_show_detached_placeholder()" in source
    assert "app.start_radio_visualizer" not in source
    assert "app.open_radio_visualizer_fullscreen" not in source


def test_app_header_source_contains_compact_radio_player():
    source = inspect.getsource(App.__init__)

    assert "header_left = ttk.Frame(header)" in source
    assert "header.columnconfigure(0, weight=0, minsize=260)" in source
    assert "header.columnconfigure(1, weight=1)" in source
    assert "header_right = ttk.Frame(header, width=620, height=120)" in source
    assert "self.l_radio_canvas = tk.Canvas(" in source
    assert "textvariable=self.radio_status_var" in source
    assert "textvariable=self.radio_title_var" in source
    assert "textvariable=self.radio_volume_label_var" in source
    assert "self.radio_header_frame.grid_propagate(False)" in source
    assert "self.radio_header_frame.pack_propagate(False)" in source
    assert "self.radio_header_frame.configure(width=300, height=138)" in source
    assert 'self.radio_header_frame.place(relx=0.5, y=8, anchor="n")' in source
    assert "self.radio_header_volume = ttk.Scale(" in source
    assert "length=160" in source
    assert "textvariable=self.radio_volume_label_var" in source
    assert "self.copyright_label = tk.Label(\n            header_right," in source


def test_standalone_radio_app_ui_contains_player_and_projectm():
    source = inspect.getsource(netmon_radio_app.NetMonRadioApp._build_ui)
    marker_source = inspect.getsource(netmon_radio_app._install_pane_drag_marker)
    menu_source = inspect.getsource(netmon_radio_app.NetMonRadioApp.__init__)
    theme_source = inspect.getsource(
        netmon_radio_app.NetMonRadioApp._apply_tk_widget_theme
    )
    init_source = inspect.getsource(netmon_radio_app.NetMonRadioApp.__init__)
    window_source = inspect.getsource(
        netmon_radio_app.NetMonRadioApp._configure_compact_standalone_window
    )
    app_source = inspect.getsource(netmon_radio_app.NetMonRadioApp)

    assert 'self.title("NetMon Radio")' in init_source
    assert "self._radio_compact_layout = True" in init_source
    assert "self._configure_compact_standalone_window()" in init_source
    assert 'self.state("zoomed")' not in init_source
    assert 'if self._started_from == "netmon_detach":' in init_source
    assert "self.after(120, self._ensure_standalone_window_visible)" in init_source
    assert "compact_layout = embedded or bool(" in source
    assert "station_table_height = 18 if compact_layout else 28" in source
    assert (
        "screen_height = max(int(self.winfo_screenheight() or 900), 900)"
        in window_source
    )
    assert "int(screen_height * 0.86)" in window_source
    assert 'self.geometry(f"{width}x{height}+{x}+{y}")' in window_source
    assert "self.maxsize(width, max_height)" in window_source
    assert "self.resizable(False, True)" in window_source
    assert 'text="⛶"' not in marker_source
    assert "top_expand" not in marker_source
    assert "bottom_expand" not in marker_source
    assert "marker_width = min(66, max(width - 24, 42))" in marker_source
    assert "y_offset=12" in source
    assert "self._scroll_canvas = None" in source
    assert "content_parent = self" in source
    assert "canvas = tk.Canvas(self, highlightthickness=0, bd=0)" in source
    assert (
        'scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)'
        in source
    )
    assert "content_parent = ttk.Frame(canvas)" in source
    assert 'widget.bind("<MouseWheel>", self._on_mousewheel, add="+")' in source
    assert 'text=("Start" if embedded else "projectM starten")' in source
    assert 'text=("Stop" if embedded else "projectM stoppen")' in source
    assert 'text="projectM installieren"' in source
    assert 'text="Radio anheften"' in source
    assert 'text="Miniplayer"' in source
    assert 'text="Datenbanken"' in source
    assert "textvariable=self.radio_database_count_var" in source
    assert 'text="Erreichbarkeit prüfen"' in source
    assert 'text="Sender hinzufügen"' in source
    assert "command=self.open_new_custom_radio_station_editor" in source
    assert "ttk.Progressbar(" in app_source
    assert "textvariable=self.radio_database_progress_status_var" in app_source
    assert "details_frame.columnconfigure(2, weight=0)" in source
    assert 'sticky="ne"' in source
    assert 'text="Steuerung & EQ"' in source
    assert 'text="EQ"' in source
    assert "action_row = ttk.Frame(station_frame)" in source
    assert "search_row = ttk.Frame(station_frame, padding=search_pad)" in source
    assert (
        "search = ttk.Entry(search_row, textvariable=self.radio_search_var, width=48)"
        in source
    )
    assert "textvariable=self.radio_toggle_favorites_text_var" in source
    assert 'sticky="w"' in source
    assert ').grid(row=0, column=2, sticky="w", padx=(12, 0))' in source
    assert "top = ttk.Frame(content_parent, padding=search_pad)" not in source
    assert ').pack(side="left", padx=(14, 0))' not in source
    assert 'main_pane = ttk.Panedwindow(main, orient="vertical")' in source
    assert (
        "self.radio_main_pane_marker = _install_pane_drag_marker(main, main_pane)"
        in source
    )
    assert "main_pane.add(station_frame, weight=3)" in source
    assert "main_pane.add(playlist_frame, weight=2)" in source
    assert (
        "playlist_parent = main_pane if main_pane is not None else (main if not embedded else controls)"
        in source
    )
    assert '"row": 1 if not embedded else 2,' in source
    assert "status_row.columnconfigure(0, weight=1)" in source
    assert "radio_page_frame = ttk.Frame(status_row)" in source
    assert 'radio_page_frame.place(relx=0.5, rely=0.5, anchor="center")' in source
    assert 'text="←"' in source
    assert "textvariable=self.radio_page_indicator_var" in source
    assert 'text="→"' in source
    assert 'label="Bass"' in source
    assert 'label="Mitten"' in source
    assert 'label="Höhen"' in source
    assert "self.radio_station_table = ttk.Treeview(" in source
    assert 'columns=("name", "genre", "bitrate")' in source
    assert 'show=("tree", "headings")' in source
    assert 'self.radio_station_table.heading("#0", text="Ampel")' in source
    assert 'self.radio_station_table.grid(row=2, column=0, sticky="nsew")' in source
    assert 'text="Beliebige Felder an- oder abwählen."' in app_source
    assert '"tags": {"title": "Tags"' in inspect.getsource(radio_controller)
    assert "radio_controller.configure_radio_station_table_columns(self)" in source
    assert "stretch=False," in inspect.getsource(
        radio_controller.configure_radio_station_table_columns
    )
    assert (
        'table.tag_configure("ampel_online", foreground="#2fb344")'
        in inspect.getsource(radio_controller.configure_radio_station_table_columns)
    )
    assert '("url", "URL", 520)' not in source
    assert (
        'label="Aufnahme starten"' in source
        or 'label="Aufnahme starten"' in menu_source
    )
    assert (
        'label="Aufnahme stoppen"' in source
        or 'label="Aufnahme stoppen"' in menu_source
    )
    assert "height=9" in source
    assert 'elif klass == "Listbox":' in theme_source
    assert 'bg=theme["tree_bg"]' in theme_source
    assert 'fg=theme["tree_fg"]' in theme_source
    assert "def open_radio_miniplayer(self):" in app_source
    assert "def _start_standalone_resize(self, event):" in app_source
    assert "def _resize_standalone_height(self, event):" in app_source
    assert "def _ensure_standalone_window_visible(self):" in app_source
    assert "owner = self.winfo_toplevel() if embedded else self" in app_source
    assert "mini = tk.Toplevel(owner)" in app_source
    assert "mini.resizable(True, True)" in app_source
    assert "mini.minsize(mini_width, mini_height)" in app_source
    assert "mini.maxsize(mini_width * 2, mini_height * 2)" in app_source
    assert "owner.withdraw()" in app_source
    assert 'window.wm_state("normal")' in app_source
    assert "window.after(80, _finalize_restore)" in app_source
    assert 'window.attributes("-topmost", True)' in app_source
    assert "self.withdraw()" in app_source
    assert 'fallback = getattr(host_app, "open_radio_external_app", None)' in app_source
    assert "_restore_window(owner)" in app_source
    assert "_restore_window(self)" in app_source
    assert "def check_visible_radio_station_reachability(self):" in app_source
    assert "def open_radio_database_sources_popup(self):" in app_source
    assert "RADIO_DATABASE_SOURCES" in inspect.getsource(netmon_radio_app)
    assert "radio_browser_country_de_exact" in inspect.getsource(netmon_radio_app)
    assert "radio_browser_country_at_exact" in inspect.getsource(netmon_radio_app)
    assert "radio_browser_country_us_exact" in inspect.getsource(netmon_radio_app)
    assert 'popup.title("Datenbanken")' in app_source
    assert 'popup.geometry("980x760")' in app_source
    assert 'text="Exklusive Länderdatenbanken"' in app_source
    assert 'text="Alle auswählen"' in app_source
    assert 'text="Exklusivmodus"' in app_source
    assert 'text="Andere Datenbanken"' in app_source
    assert (
        "source_canvas = tk.Canvas(source_wrap, highlightthickness=0, bd=0)"
        in app_source
    )
    assert 'orient="vertical"' in app_source
    assert "command=source_canvas.yview" in app_source
    assert 'ttk.Separator(source_frame, orient="horizontal")' in app_source
    assert 'text="Datenbank aktualisieren"' in app_source
    assert "action_row = ttk.Frame(body)" in app_source
    assert "self.radio_database_progressbar.grid(" in app_source
    assert 'image=self.radio_status_indicator_images.get("unknown")' in app_source
    assert "self.check_radio_database_source_reachability()" in app_source
    assert "def check_radio_database_source_reachability(self):" in app_source
    assert "def on_radio_database_select_all_changed(self):" in app_source
    assert "def on_radio_database_exclusive_mode_changed(self):" in app_source
    assert "def on_radio_database_source_toggle(self, source_id):" in app_source
    assert "def _sync_radio_database_select_all_state(self):" in app_source
    assert "def open_new_custom_radio_station_editor(self):" in app_source
    assert "def set_radio_database_import_progress(" in app_source
    assert "def show_radio_database_import_summary(self, summary):" in app_source
    assert "radio_controller.clear_custom_station_form(self)" in app_source
    assert "return self.download_radio_db()" in app_source
    assert "radio_controller.open_radio_tab(host_app)" in app_source
    assert (
        'widget.bind("<Double-Button-1>", self.restore_from_radio_miniplayer, add="+")'
        in app_source
    )
    assert (
        'widget.bind("<B1-Motion>", self._drag_radio_miniplayer, add="+")' in app_source
    )
    assert 'orient="horizontal",' in source
    assert "command=self.radio_station_table.xview," in source
    assert "xscrollcommand=station_scroll_x.set," in source
    assert 'self.radio_station_table.bind(\n            "<ButtonRelease-1>",' in source
    assert "self.radio_logo_label = ttk.Label(" in source
    assert 'text="Aktueller Sender"' in source
    assert "textvariable=self.radio_source_var" in source
    assert "textvariable=self.radio_title_var" in source
    assert "textvariable=self.radio_bitrate_var" in source
    assert (
        "self.radio_detach_button = ttk.Button(\n                details_frame,"
        in source
    )
    assert "self.radio_detach_button.grid(\n                row=1," in source
    assert (
        "self.radio_attach_button = ttk.Button(\n                details_frame,"
        in source
    )
    assert "self.radio_attach_button.grid(\n                row=1," in source
    assert (
        "self.radio_database_button = ttk.Button(\n            projectm_actions,"
        in source
    )
    assert "self.radio_database_button.grid(\n            row=1," in source
    assert (
        'details_row.grid(row=0, column=0, sticky="ew", pady=(0, outer_pad))' in source
    )
    assert 'player_top.grid(row=1, column=0, sticky="ew")' in source
    assert 'playback_eq_frame.grid(row=0, column=0, sticky="ew")' in source
    assert (
        'projectm_frame.grid(row=1, column=0, sticky="ew", pady=(outer_pad, 0))'
        in source
    )
    assert "projectm_actions.columnconfigure(2, weight=1)" in source
    assert 'projectm_frame.grid(row=0, column=2, sticky="nsew")' not in source
    assert "self._append_log_file(text)" in inspect.getsource(
        netmon_radio_app.NetMonRadioApp.log
    )


def test_standalone_radio_pane_drag_state_uses_initial_values():
    state = netmon_radio_app._standalone_radio_pane_drag_state()
    other_state = netmon_radio_app._standalone_radio_pane_drag_state()

    assert state == {
        "root_y": 0,
        "sash_y": 0,
        "update_pending": False,
    }
    assert other_state == state
    assert other_state is not state


def test_standalone_radio_pane_bind_marker_events_binds_all_with_add():
    calls = []
    first_callback = object()
    second_callback = object()

    class DummyWidget:
        def bind(self, event_name, callback, add=None):
            calls.append((event_name, callback, add))

    netmon_radio_app._standalone_radio_pane_bind_marker_events(
        DummyWidget(),
        (
            ("<Configure>", first_callback),
            ("<B1-Motion>", second_callback),
        ),
    )

    assert calls == [
        ("<Configure>", first_callback, "+"),
        ("<B1-Motion>", second_callback, "+"),
    ]


def test_standalone_radio_pane_bind_marker_events_stops_and_ignores_failures():
    calls = []

    class DummyWidget:
        def bind(self, event_name, _callback, add=None):
            calls.append((event_name, add))
            raise RuntimeError("bind failed")

    netmon_radio_app._standalone_radio_pane_bind_marker_events(
        DummyWidget(),
        (
            ("<Configure>", object()),
            ("<B1-Motion>", object()),
        ),
    )

    assert calls == [("<Configure>", "+")]


def test_standalone_radio_pane_update_bindings_use_update_callback_for_all_events():
    update_marker = object()

    assert netmon_radio_app._standalone_radio_pane_update_bindings(update_marker) == (
        ("<Configure>", update_marker),
        ("<ButtonRelease-1>", update_marker),
        ("<B1-Motion>", update_marker),
    )


def test_standalone_radio_pane_grip_bindings_use_drag_callbacks():
    start_drag = object()
    drag = object()
    end_drag = object()

    assert netmon_radio_app._standalone_radio_pane_grip_bindings(
        start_drag,
        drag,
        end_drag,
    ) == (
        ("<Button-1>", start_drag),
        ("<B1-Motion>", drag),
        ("<ButtonRelease-1>", end_drag),
    )


def test_standalone_radio_pane_marker_binding_plan_maps_widgets_to_bindings():
    container = object()
    pane = object()
    grip = object()
    update_bindings = object()
    grip_bindings = object()

    assert netmon_radio_app._standalone_radio_pane_marker_binding_plan(
        container,
        pane,
        grip,
        update_bindings=update_bindings,
        grip_bindings=grip_bindings,
    ) == (
        (container, update_bindings),
        (pane, update_bindings),
        (grip, grip_bindings),
    )


def test_standalone_radio_pane_bind_marker_callbacks_binds_plan_in_order():
    calls = []
    first_widget = object()
    first_bindings = object()
    second_widget = object()
    second_bindings = object()

    netmon_radio_app._standalone_radio_pane_bind_marker_callbacks(
        (
            (first_widget, first_bindings),
            (second_widget, second_bindings),
        ),
        bind_events=lambda widget, bindings: calls.append((widget, bindings)),
    )

    assert calls == [
        (first_widget, first_bindings),
        (second_widget, second_bindings),
    ]


def test_standalone_radio_pane_bind_marker_callbacks_propagates_binder_failure():
    calls = []

    def fail_bind(widget, bindings):
        calls.append((widget, bindings))
        raise RuntimeError("bind failed")

    with pytest.raises(RuntimeError, match="bind failed"):
        netmon_radio_app._standalone_radio_pane_bind_marker_callbacks(
            (("widget", "bindings"),),
            bind_events=fail_bind,
        )

    assert calls == [("widget", "bindings")]


def test_standalone_radio_pane_request_initial_marker_update_uses_after_zero():
    calls = []
    callback = object()

    class DummyContainer:
        def after(self, delay, scheduled_callback):
            calls.append((delay, scheduled_callback))

    netmon_radio_app._standalone_radio_pane_request_initial_marker_update(
        DummyContainer(),
        callback,
    )

    assert calls == [(0, callback)]


def test_standalone_radio_pane_request_initial_marker_update_ignores_after_failure():
    calls = []

    class DummyContainer:
        def after(self, _delay, _scheduled_callback):
            calls.append("after")
            raise RuntimeError("after failed")

    netmon_radio_app._standalone_radio_pane_request_initial_marker_update(
        DummyContainer(),
        object(),
    )

    assert calls == ["after"]


def test_standalone_radio_pane_schedule_initial_marker_update_delegates_request():
    calls = []
    container = object()
    callback = object()

    netmon_radio_app._standalone_radio_pane_schedule_initial_marker_update(
        container,
        callback,
        request_update=lambda container_arg, callback_arg: calls.append(
            (container_arg, callback_arg)
        ),
    )

    assert calls == [(container, callback)]


def test_standalone_radio_pane_schedule_active_marker_initial_update_forwards_dependencies():
    calls = []
    container = object()
    callback = object()

    netmon_radio_app._standalone_radio_pane_schedule_active_marker_initial_update(
        container,
        callback,
        lambda container_arg, callback_arg: calls.append((container_arg, callback_arg)),
    )

    assert calls == [(container, callback)]


def test_standalone_radio_pane_activate_marker_callbacks_binds_then_schedules():
    events = []
    container = object()
    binding_plan = object()
    update_marker = object()

    netmon_radio_app._standalone_radio_pane_activate_marker_callbacks(
        container,
        binding_plan,
        update_marker,
        callback_binder=lambda plan: events.append(("bind", plan)),
        initial_update_scheduler=lambda container_arg, update_arg: events.append(
            ("schedule", container_arg, update_arg)
        ),
    )

    assert events == [
        ("bind", binding_plan),
        (
            "schedule",
            container,
            update_marker,
        ),
    ]


def test_standalone_radio_pane_activate_marker_callbacks_propagates_binding_failure():
    def fail_bind(_binding_plan):
        raise RuntimeError("bind failed")

    with pytest.raises(RuntimeError, match="bind failed"):
        netmon_radio_app._standalone_radio_pane_activate_marker_callbacks(
            object(),
            object(),
            object(),
            callback_binder=fail_bind,
            initial_update_scheduler=lambda *_args: None,
        )


def test_standalone_radio_pane_activate_marker_bindings_builds_and_activates():
    events = []
    container = object()
    pane = object()
    grip = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()
    update_bindings = object()
    grip_bindings = object()
    binding_plan = object()

    netmon_radio_app._standalone_radio_pane_activate_marker_bindings(
        container,
        pane,
        grip,
        update_marker,
        start_drag,
        drag,
        end_drag,
        update_bindings_builder=lambda update_arg: events.append(
            ("update_bindings", update_arg)
        )
        or update_bindings,
        grip_bindings_builder=lambda *args: events.append(("grip_bindings", args))
        or grip_bindings,
        binding_plan_builder=lambda *args, **kwargs: events.append(
            ("binding_plan", args, kwargs)
        )
        or binding_plan,
        activate_marker_callbacks=lambda *args: events.append(("activate", args)),
    )

    assert events == [
        ("update_bindings", update_marker),
        ("grip_bindings", (start_drag, drag, end_drag)),
        (
            "binding_plan",
            (container, pane, grip),
            {"update_bindings": update_bindings, "grip_bindings": grip_bindings},
        ),
        ("activate", (container, binding_plan, update_marker)),
    ]


def test_standalone_radio_pane_activate_marker_bindings_propagates_activation_failure():
    def fail_activate(_container, _binding_plan, _update_marker):
        raise RuntimeError("activate failed")

    with pytest.raises(RuntimeError, match="activate failed"):
        netmon_radio_app._standalone_radio_pane_activate_marker_bindings(
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
            object(),
            update_bindings_builder=lambda _update_marker: object(),
            grip_bindings_builder=lambda _start, _drag, _end: object(),
            binding_plan_builder=lambda *_args, **_kwargs: object(),
            activate_marker_callbacks=fail_activate,
        )


def test_standalone_radio_pane_marker_geometry_centers_and_offsets_marker():
    assert netmon_radio_app._standalone_radio_pane_marker_geometry(
        120,
        80,
        y_offset=12,
    ) == {"x": 27, "y": 87, "width": 66, "height": 12}
    assert netmon_radio_app._standalone_radio_pane_marker_geometry(
        20,
        1,
    ) == {"x": 8, "y": 2, "width": 42, "height": 12}


def test_standalone_radio_pane_place_marker_places_and_lifts():
    calls = []
    geometry = {"x": 27, "y": 87, "width": 66, "height": 12}

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lift(self):
            calls.append("lift")

    netmon_radio_app._standalone_radio_pane_place_marker(DummyMarker(), geometry)

    assert calls == [
        ("place", geometry),
        "lift",
    ]


def test_standalone_radio_pane_forget_marker_forgets_place():
    calls = []

    class DummyMarker:
        def place_forget(self):
            calls.append("place_forget")

    netmon_radio_app._standalone_radio_pane_forget_marker(DummyMarker())

    assert calls == ["place_forget"]


def test_standalone_radio_pane_set_sash_pos_prefers_sashpos():
    calls = []

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    netmon_radio_app._standalone_radio_pane_set_sash_pos(DummyPane(), "120")

    assert calls == [("sashpos", 0, 120)]


def test_standalone_radio_pane_set_sash_pos_falls_back_to_sash_place():
    calls = []

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))
            raise RuntimeError("unsupported")

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    netmon_radio_app._standalone_radio_pane_set_sash_pos(DummyPane(), "120")

    assert calls == [
        ("sashpos", 0, 120),
        ("sash_place", 0, 0, 120),
    ]


def test_standalone_radio_pane_sash_callback_binds_pane():
    calls = []
    pane = object()

    callback = netmon_radio_app._standalone_radio_pane_sash_callback(
        pane,
        set_sash_pos=lambda pane_arg, new_y: calls.append((pane_arg, new_y)),
    )

    callback("240")

    assert calls == [(pane, "240")]


def test_standalone_radio_pane_sash_callback_propagates_set_failures():
    def fail_set(_pane, _new_y):
        raise RuntimeError("set failed")

    callback = netmon_radio_app._standalone_radio_pane_sash_callback(
        object(),
        set_sash_pos=fail_set,
    )

    with pytest.raises(RuntimeError, match="set failed"):
        callback(240)


def test_standalone_radio_pane_place_marker_for_sash_builds_geometry_then_places():
    events = []
    marker = object()
    geometry = object()

    class DummyContainer:
        def winfo_width(self):
            events.append("width")
            return 120

    netmon_radio_app._standalone_radio_pane_place_marker_for_sash(
        DummyContainer(),
        marker,
        80,
        12,
        geometry_builder=lambda width, sash_y, y_offset: events.append(
            ("geometry", width, sash_y, y_offset)
        )
        or geometry,
        marker_placer=lambda marker_arg, geometry_arg: events.append(
            ("place", marker_arg, geometry_arg)
        ),
    )

    assert events == [
        "width",
        ("geometry", 120, 80, 12),
        ("place", marker, geometry),
    ]


def test_standalone_radio_pane_place_marker_for_sash_safe_places_marker():
    events = []
    container = object()
    marker = object()

    netmon_radio_app._standalone_radio_pane_place_marker_for_sash_safe(
        container,
        marker,
        80,
        12,
        place_marker_for_sash=lambda *args: events.append(("place", args)),
        forget_marker=lambda marker_arg: events.append(("forget", marker_arg)),
    )

    assert events == [
        ("place", (container, marker, 80, 12)),
    ]


def test_standalone_radio_pane_place_marker_for_sash_safe_forgets_on_place_failure():
    events = []
    marker = object()

    def fail_place(*_args):
        events.append("place")
        raise RuntimeError("place failed")

    netmon_radio_app._standalone_radio_pane_place_marker_for_sash_safe(
        object(),
        marker,
        80,
        place_marker_for_sash=fail_place,
        forget_marker=lambda marker_arg: events.append(("forget", marker_arg)),
    )

    assert events == [
        "place",
        ("forget", marker),
    ]


def test_standalone_radio_pane_place_marker_for_sash_safe_ignores_forget_failure():
    events = []

    def fail_place(*_args):
        events.append("place")
        raise RuntimeError("place failed")

    def fail_forget(_marker):
        events.append("forget")
        raise RuntimeError("forget failed")

    netmon_radio_app._standalone_radio_pane_place_marker_for_sash_safe(
        object(),
        object(),
        80,
        place_marker_for_sash=fail_place,
        forget_marker=fail_forget,
    )

    assert events == ["place", "forget"]


def test_standalone_radio_pane_place_callback_binds_marker_context():
    calls = []
    container = object()
    marker = object()

    callback = netmon_radio_app._standalone_radio_pane_place_callback(
        container,
        marker,
        7,
        place_marker_for_sash_safe=lambda *args: calls.append(args),
    )

    callback("240")

    assert calls == [(container, marker, "240", 7)]


def test_standalone_radio_pane_place_callback_propagates_place_failures():
    def fail_place(_container, _marker, _sash_y, _y_offset):
        raise RuntimeError("place failed")

    callback = netmon_radio_app._standalone_radio_pane_place_callback(
        object(),
        object(),
        7,
        place_marker_for_sash_safe=fail_place,
    )

    with pytest.raises(RuntimeError, match="place failed"):
        callback(240)


def test_standalone_radio_pane_update_marker_places_current_sash():
    events = []

    class DummyPane:
        def sashpos(self, index):
            events.append(("sashpos", index))
            return "80"

    netmon_radio_app._standalone_radio_pane_update_marker(
        DummyPane(),
        lambda sash_y: events.append(("place", sash_y)),
    )

    assert events == [
        ("sashpos", 0),
        ("place", 80),
    ]


def test_standalone_radio_pane_update_marker_safe_updates_marker():
    events = []
    pane = object()
    marker = object()
    place_marker = object()

    netmon_radio_app._standalone_radio_pane_update_marker_safe(
        pane,
        place_marker,
        marker,
        update_marker=lambda pane_arg, place_arg: events.append(
            ("update", pane_arg, place_arg)
        ),
        forget_marker=lambda marker_arg: events.append(("forget", marker_arg)),
    )

    assert events == [
        ("update", pane, place_marker),
    ]


def test_standalone_radio_pane_update_marker_safe_forgets_on_update_failure():
    events = []
    marker = object()

    def fail_update(*_args):
        events.append("update")
        raise RuntimeError("update failed")

    netmon_radio_app._standalone_radio_pane_update_marker_safe(
        object(),
        object(),
        marker,
        update_marker=fail_update,
        forget_marker=lambda marker_arg: events.append(("forget", marker_arg)),
    )

    assert events == [
        "update",
        ("forget", marker),
    ]


def test_standalone_radio_pane_update_marker_safe_ignores_forget_failure():
    events = []

    def fail_update(*_args):
        events.append("update")
        raise RuntimeError("update failed")

    def fail_forget(_marker):
        events.append("forget")
        raise RuntimeError("forget failed")

    netmon_radio_app._standalone_radio_pane_update_marker_safe(
        object(),
        object(),
        object(),
        update_marker=fail_update,
        forget_marker=fail_forget,
    )

    assert events == ["update", "forget"]


def test_standalone_radio_pane_update_callback_binds_marker_context_and_event():
    calls = []
    pane = object()
    place_marker = object()
    marker = object()

    callback = netmon_radio_app._standalone_radio_pane_update_callback(
        pane,
        place_marker,
        marker,
        update_marker_safe=lambda *args: calls.append(args),
    )

    callback(object())

    assert calls == [(pane, place_marker, marker)]


def test_standalone_radio_pane_update_callback_propagates_update_failures():
    def fail_update(_pane, _place_marker, _marker):
        raise RuntimeError("update failed")

    callback = netmon_radio_app._standalone_radio_pane_update_callback(
        object(),
        object(),
        object(),
        update_marker_safe=fail_update,
    )

    with pytest.raises(RuntimeError, match="update failed"):
        callback()


def test_standalone_radio_pane_schedule_marker_update_skips_pending_state():
    calls = []

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    state = {"update_pending": True}

    netmon_radio_app._standalone_radio_pane_schedule_marker_update(
        DummyContainer(),
        state,
        lambda: calls.append("update"),
    )

    assert state["update_pending"] is True
    assert calls == []


def test_standalone_radio_pane_schedule_marker_update_uses_after_idle_runner():
    calls = []
    runners = []

    class DummyContainer:
        def after_idle(self, callback):
            calls.append("after_idle")
            runners.append(callback)

    state = {"update_pending": False}

    netmon_radio_app._standalone_radio_pane_schedule_marker_update(
        DummyContainer(),
        state,
        lambda: calls.append("update"),
    )

    assert state["update_pending"] is True
    assert calls == ["after_idle"]

    runners[0]()

    assert state["update_pending"] is False
    assert calls == ["after_idle", "update"]


def test_standalone_radio_pane_schedule_marker_update_runs_on_after_idle_failure():
    calls = []

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))
            raise RuntimeError("after idle failed")

    state = {"update_pending": False}

    netmon_radio_app._standalone_radio_pane_schedule_marker_update(
        DummyContainer(),
        state,
        lambda: calls.append("update"),
    )

    assert state["update_pending"] is False
    assert calls[0][0] == "after_idle"
    assert calls[1:] == ["update"]


def test_standalone_radio_pane_schedule_callback_binds_update_context():
    calls = []
    container = object()
    state = {"update_pending": False}
    update_marker = object()

    callback = netmon_radio_app._standalone_radio_pane_schedule_callback(
        container,
        state,
        update_marker,
        schedule_marker_update=lambda *args: calls.append(args),
    )

    callback()

    assert calls == [(container, state, update_marker)]


def test_standalone_radio_pane_schedule_callback_propagates_schedule_failures():
    def fail_schedule(_container, _state, _update_marker):
        raise RuntimeError("schedule failed")

    callback = netmon_radio_app._standalone_radio_pane_schedule_callback(
        object(),
        {"update_pending": False},
        object(),
        schedule_marker_update=fail_schedule,
    )

    with pytest.raises(RuntimeError, match="schedule failed"):
        callback()


def test_standalone_radio_pane_start_drag_records_event_and_sash():
    state = {}

    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            assert index == 0
            return "240"

    netmon_radio_app._standalone_radio_pane_start_drag(
        state,
        DummyEvent(),
        DummyPane(),
    )

    assert state == {"root_y": 310, "sash_y": 240}


def test_standalone_radio_pane_start_drag_uses_zeroes_on_failure():
    state = {"root_y": 5, "sash_y": 6}

    class DummyEvent:
        y_root = "bad"

    class DummyPane:
        def sashpos(self, index):
            return "240"

    netmon_radio_app._standalone_radio_pane_start_drag(
        state,
        DummyEvent(),
        DummyPane(),
    )

    assert state == {"root_y": 0, "sash_y": 0}


def test_standalone_radio_pane_start_drag_event_records_state_and_breaks():
    state = {}

    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            assert index == 0
            return "240"

    result = netmon_radio_app._standalone_radio_pane_start_drag_event(
        state,
        DummyEvent(),
        DummyPane(),
    )

    assert result == "break"
    assert state == {"root_y": 310, "sash_y": 240}


def test_standalone_radio_pane_start_drag_event_propagates_start_failures():
    calls = []

    def fail_start(*_args):
        calls.append("start")
        raise RuntimeError("start failed")

    with pytest.raises(RuntimeError, match="start failed"):
        netmon_radio_app._standalone_radio_pane_start_drag_event(
            object(),
            object(),
            object(),
            start_drag=fail_start,
        )

    assert calls == ["start"]


def test_standalone_radio_pane_start_callback_binds_drag_context():
    calls = []
    state = {}
    pane = object()
    event = object()

    callback = netmon_radio_app._standalone_radio_pane_start_callback(
        state,
        pane,
        start_drag_event=lambda *args: calls.append(args) or "break",
    )

    assert callback(event) == "break"
    assert calls == [(state, event, pane)]


def test_standalone_radio_pane_start_callback_propagates_start_failures():
    def fail_start_event(_state, _event, _pane):
        raise RuntimeError("start failed")

    callback = netmon_radio_app._standalone_radio_pane_start_callback(
        {},
        object(),
        start_drag_event=fail_start_event,
    )

    with pytest.raises(RuntimeError, match="start failed"):
        callback(object())


def test_standalone_radio_pane_drag_motion_moves_places_and_schedules():
    calls = []
    state = {"root_y": "310", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    netmon_radio_app._standalone_radio_pane_drag_motion(
        state,
        DummyEvent(),
        lambda sash_y: calls.append(("set_sash", sash_y)),
        lambda sash_y: calls.append(("place", sash_y)),
        lambda: calls.append("schedule"),
    )

    assert calls == [
        ("set_sash", 260),
        ("place", 260),
        "schedule",
    ]


def test_standalone_radio_pane_drag_event_handles_motion_and_breaks():
    calls = []
    state = {"root_y": "310", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    result = netmon_radio_app._standalone_radio_pane_drag_event(
        state,
        DummyEvent(),
        lambda sash_y: calls.append(("set_sash", sash_y)),
        lambda sash_y: calls.append(("place", sash_y)),
        lambda: calls.append("schedule"),
    )

    assert result == "break"
    assert calls == [
        ("set_sash", 260),
        ("place", 260),
        "schedule",
    ]


def test_standalone_radio_pane_drag_event_breaks_after_ignored_motion_failure():
    calls = []

    def fail_motion(*_args):
        calls.append("motion")
        raise RuntimeError("motion failed")

    result = netmon_radio_app._standalone_radio_pane_drag_event(
        object(),
        object(),
        lambda sash_y: calls.append(("set_sash", sash_y)),
        lambda sash_y: calls.append(("place", sash_y)),
        lambda: calls.append("schedule"),
        drag_motion=fail_motion,
    )

    assert result == "break"
    assert calls == ["motion"]


def test_standalone_radio_pane_drag_callback_binds_drag_context():
    calls = []
    state = {}
    event = object()
    set_sash = object()
    place_marker = object()
    schedule_marker = object()

    callback = netmon_radio_app._standalone_radio_pane_drag_callback(
        state,
        set_sash,
        place_marker,
        schedule_marker,
        drag_event=lambda *args: calls.append(args) or "break",
    )

    assert callback(event) == "break"
    assert calls == [(state, event, set_sash, place_marker, schedule_marker)]


def test_standalone_radio_pane_drag_callback_propagates_drag_failures():
    def fail_drag_event(_state, _event, _set_sash, _place_marker, _schedule):
        raise RuntimeError("drag failed")

    callback = netmon_radio_app._standalone_radio_pane_drag_callback(
        {},
        object(),
        object(),
        object(),
        drag_event=fail_drag_event,
    )

    with pytest.raises(RuntimeError, match="drag failed"):
        callback(object())


def test_standalone_radio_pane_end_drag_updates_marker_and_breaks():
    calls = []

    result = netmon_radio_app._standalone_radio_pane_end_drag(
        lambda: calls.append("update")
    )

    assert result == "break"
    assert calls == ["update"]


def test_standalone_radio_pane_end_drag_propagates_update_failures():
    def fail_update():
        raise RuntimeError("update failed")

    with pytest.raises(RuntimeError, match="update failed"):
        netmon_radio_app._standalone_radio_pane_end_drag(fail_update)


def test_standalone_radio_pane_end_callback_binds_update_and_event():
    calls = []
    update_marker = object()

    callback = netmon_radio_app._standalone_radio_pane_end_callback(
        update_marker,
        end_drag=lambda marker_arg: calls.append(marker_arg) or "break",
    )

    assert callback(object()) == "break"
    assert calls == [update_marker]


def test_standalone_radio_pane_end_callback_propagates_end_failures():
    def fail_end(_update_marker):
        raise RuntimeError("end failed")

    callback = netmon_radio_app._standalone_radio_pane_end_callback(
        object(),
        end_drag=fail_end,
    )

    with pytest.raises(RuntimeError, match="end failed"):
        callback()


def test_standalone_radio_pane_marker_frame_options_use_marker_style():
    assert netmon_radio_app._standalone_radio_pane_marker_frame_options("#123456") == {
        "bg": "#123456",
        "bd": 1,
        "relief": "solid",
    }


def test_standalone_radio_pane_marker_grip_options_use_marker_style():
    assert netmon_radio_app._standalone_radio_pane_marker_grip_options("#123456") == {
        "text": "≡",
        "bg": "#123456",
        "fg": "#ffffff",
        "font": ("TkDefaultFont", 9, "bold"),
        "cursor": "sb_v_double_arrow",
        "padx": 0,
        "pady": 0,
        "anchor": "center",
    }


def test_standalone_radio_pane_configure_marker_widgets_applies_layout():
    calls = []

    class DummyMarker:
        def columnconfigure(self, column, weight):
            calls.append(("columnconfigure", column, weight))

    class DummyGrip:
        def grid(self, **kwargs):
            calls.append(("grid", kwargs))

    netmon_radio_app._standalone_radio_pane_configure_marker_widgets(
        DummyMarker(),
        DummyGrip(),
    )

    assert calls == [
        ("columnconfigure", 0, 1),
        ("grid", {"row": 0, "column": 0, "sticky": "ew"}),
    ]


def test_standalone_radio_pane_configure_marker_widgets_propagates_layout_failures():
    class FailingMarker:
        def columnconfigure(self, _column, weight):
            raise RuntimeError("column failed")

    with pytest.raises(RuntimeError, match="column failed"):
        netmon_radio_app._standalone_radio_pane_configure_marker_widgets(
            FailingMarker(),
            object(),
        )


def test_standalone_radio_pane_marker_frame_builds_with_options():
    calls = []
    container = object()
    marker = object()

    result = netmon_radio_app._standalone_radio_pane_marker_frame(
        container,
        "#123456",
        frame_builder=lambda *args, **kwargs: calls.append(("frame", args, kwargs))
        or marker,
        frame_options_builder=lambda color: calls.append(("frame_options", color))
        or {"bg": color, "bd": 1, "relief": "solid"},
    )

    assert result is marker
    assert calls == [
        ("frame_options", "#123456"),
        (
            "frame",
            (container,),
            {"bg": "#123456", "bd": 1, "relief": "solid"},
        ),
    ]


def test_standalone_radio_pane_marker_frame_propagates_builder_failures():
    def fail_frame(*_args, **_kwargs):
        raise RuntimeError("frame failed")

    with pytest.raises(RuntimeError, match="frame failed"):
        netmon_radio_app._standalone_radio_pane_marker_frame(
            object(),
            "#123456",
            frame_builder=fail_frame,
        )


def test_standalone_radio_pane_marker_grip_builds_with_options():
    calls = []
    marker = object()
    grip = object()

    result = netmon_radio_app._standalone_radio_pane_marker_grip(
        marker,
        "#123456",
        label_builder=lambda *args, **kwargs: calls.append(("label", args, kwargs))
        or grip,
        grip_options_builder=lambda color: calls.append(("grip_options", color))
        or {
            "text": "≡",
            "bg": color,
            "fg": "#ffffff",
            "font": ("TkDefaultFont", 9, "bold"),
            "cursor": "sb_v_double_arrow",
            "padx": 0,
            "pady": 0,
            "anchor": "center",
        },
    )

    assert result is grip
    assert calls == [
        ("grip_options", "#123456"),
        (
            "label",
            (marker,),
            {
                "text": "≡",
                "bg": "#123456",
                "fg": "#ffffff",
                "font": ("TkDefaultFont", 9, "bold"),
                "cursor": "sb_v_double_arrow",
                "padx": 0,
                "pady": 0,
                "anchor": "center",
            },
        ),
    ]


def test_standalone_radio_pane_marker_grip_propagates_builder_failures():
    def fail_label(*_args, **_kwargs):
        raise RuntimeError("label failed")

    with pytest.raises(RuntimeError, match="label failed"):
        netmon_radio_app._standalone_radio_pane_marker_grip(
            object(),
            "#123456",
            label_builder=fail_label,
        )


def test_standalone_radio_pane_marker_widget_pair_builds_frame_then_grip():
    calls = []
    container = object()

    marker = object()
    grip = object()

    result = netmon_radio_app._standalone_radio_pane_marker_widget_pair(
        container,
        "#123456",
        marker_frame_builder=lambda *args: calls.append(("frame", args)) or marker,
        marker_grip_builder=lambda *args: calls.append(("grip", args)) or grip,
    )

    assert result == (marker, grip)
    assert calls == [
        ("frame", (container, "#123456")),
        ("grip", (marker, "#123456")),
    ]


def test_standalone_radio_pane_marker_widget_pair_propagates_grip_failures():
    marker = object()

    def fail_grip(*_args):
        raise RuntimeError("grip failed")

    with pytest.raises(RuntimeError, match="grip failed"):
        netmon_radio_app._standalone_radio_pane_marker_widget_pair(
            object(),
            "#123456",
            marker_frame_builder=lambda *_args: marker,
            marker_grip_builder=fail_grip,
        )


def test_standalone_radio_pane_marker_widgets_builds_pair_and_configures_layout():
    calls = []
    container = object()

    marker = object()
    grip = object()

    result = netmon_radio_app._standalone_radio_pane_marker_widgets(
        container,
        "#123456",
        marker_pair_builder=lambda *args: calls.append(("pair", args))
        or (marker, grip),
        configure_widgets=lambda marker_arg, grip_arg: calls.append(
            ("configure", marker_arg, grip_arg)
        ),
    )

    assert result == (marker, grip)
    assert calls == [
        ("pair", (container, "#123456")),
        ("configure", marker, grip),
    ]


def test_standalone_radio_pane_marker_widgets_propagates_frame_failures():
    def fail_pair(*_args):
        raise RuntimeError("pair failed")

    with pytest.raises(RuntimeError, match="pair failed"):
        netmon_radio_app._standalone_radio_pane_marker_widgets(
            object(),
            "#123456",
            marker_pair_builder=fail_pair,
        )


def test_standalone_radio_pane_marker_drag_callbacks_builds_callbacks_in_order():
    events = []
    pane = object()
    drag_state = {"update_pending": False}
    set_sash = object()
    place_marker = object()
    update_marker = object()
    schedule_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    result = netmon_radio_app._standalone_radio_pane_marker_drag_callbacks(
        drag_state,
        pane,
        set_sash,
        place_marker,
        schedule_marker,
        update_marker,
        start_callback_builder=lambda *args: events.append(("start", args))
        or start_drag,
        drag_callback_builder=lambda *args: events.append(("drag", args)) or drag,
        end_callback_builder=lambda update_arg: events.append(("end", update_arg))
        or end_drag,
    )

    assert result == (start_drag, drag, end_drag)
    assert events == [
        ("start", (drag_state, pane)),
        ("drag", (drag_state, set_sash, place_marker, schedule_marker)),
        ("end", update_marker),
    ]


def test_standalone_radio_pane_marker_drag_callbacks_propagates_builder_failures():
    def fail_end(_update_marker):
        raise RuntimeError("end failed")

    with pytest.raises(RuntimeError, match="end failed"):
        netmon_radio_app._standalone_radio_pane_marker_drag_callbacks(
            {},
            object(),
            object(),
            object(),
            object(),
            object(),
            start_callback_builder=lambda *_args: object(),
            drag_callback_builder=lambda *_args: object(),
            end_callback_builder=fail_end,
        )


def test_standalone_radio_pane_marker_base_callbacks_builds_callbacks_in_order():
    events = []
    container = object()
    pane = object()
    marker = object()
    drag_state = {"update_pending": False}
    set_sash = object()
    place_marker = object()
    update_marker = object()
    schedule_marker = object()

    result = netmon_radio_app._standalone_radio_pane_marker_base_callbacks(
        container,
        pane,
        marker,
        12,
        drag_state_builder=lambda: events.append("drag_state") or drag_state,
        sash_callback_builder=lambda pane_arg: events.append(("sash", pane_arg))
        or set_sash,
        place_callback_builder=lambda *args: events.append(("place", args))
        or place_marker,
        update_callback_builder=lambda *args: events.append(("update", args))
        or update_marker,
        schedule_callback_builder=lambda *args: events.append(("schedule", args))
        or schedule_marker,
    )

    assert result == (
        drag_state,
        set_sash,
        place_marker,
        update_marker,
        schedule_marker,
    )
    assert events == [
        "drag_state",
        ("sash", pane),
        ("place", (container, marker, 12)),
        ("update", (pane, place_marker, marker)),
        ("schedule", (container, drag_state, update_marker)),
    ]


def test_standalone_radio_pane_marker_base_callbacks_propagates_builder_failures():
    def fail_schedule(*_args):
        raise RuntimeError("schedule failed")

    with pytest.raises(RuntimeError, match="schedule failed"):
        netmon_radio_app._standalone_radio_pane_marker_base_callbacks(
            object(),
            object(),
            object(),
            drag_state_builder=lambda: {},
            sash_callback_builder=lambda _pane: object(),
            place_callback_builder=lambda *_args: object(),
            update_callback_builder=lambda *_args: object(),
            schedule_callback_builder=fail_schedule,
        )


def test_standalone_radio_pane_marker_callbacks_builds_callbacks_in_order():
    events = []
    container = object()
    pane = object()
    marker = object()
    drag_state = {"update_pending": False}
    set_sash = object()
    place_marker = object()
    update_marker = object()
    schedule_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    result = netmon_radio_app._standalone_radio_pane_marker_callbacks(
        container,
        pane,
        marker,
        12,
        base_callbacks_builder=lambda *args: events.append(("base", args))
        or (drag_state, set_sash, place_marker, update_marker, schedule_marker),
        drag_callbacks_builder=lambda *args: events.append(("drag_callbacks", args))
        or (start_drag, drag, end_drag),
    )

    assert result == (update_marker, start_drag, drag, end_drag)
    assert events == [
        ("base", (container, pane, marker, 12)),
        (
            "drag_callbacks",
            (drag_state, pane, set_sash, place_marker, schedule_marker, update_marker),
        ),
    ]


def test_standalone_radio_pane_marker_callbacks_propagates_builder_failures():
    def fail_drag_callbacks(*_args):
        raise RuntimeError("drag callbacks failed")

    with pytest.raises(RuntimeError, match="drag callbacks failed"):
        netmon_radio_app._standalone_radio_pane_marker_callbacks(
            object(),
            object(),
            object(),
            base_callbacks_builder=lambda *_args: (
                {},
                object(),
                object(),
                object(),
                object(),
            ),
            drag_callbacks_builder=fail_drag_callbacks,
        )


def test_standalone_radio_pane_activate_marker_parts_activates_bindings():
    events = []
    container = object()
    pane = object()
    grip = object()
    callbacks = (object(), object(), object(), object())

    netmon_radio_app._standalone_radio_pane_activate_marker_parts(
        container,
        pane,
        grip,
        callbacks,
        bindings_activator=lambda *args: events.append(("activate", args)),
    )

    assert events == [
        ("activate", (container, pane, grip, *callbacks)),
    ]


def test_standalone_radio_pane_activate_marker_parts_propagates_activation_failure():
    def fail_activate(*_args):
        raise RuntimeError("activate failed")

    with pytest.raises(RuntimeError, match="activate failed"):
        netmon_radio_app._standalone_radio_pane_activate_marker_parts(
            object(),
            object(),
            object(),
            (object(), object(), object(), object()),
            bindings_activator=fail_activate,
        )


def test_standalone_radio_pane_install_marker_parts_builds_callbacks_and_activates():
    events = []
    container = object()
    pane = object()
    marker = object()
    grip = object()
    callbacks = (object(), object(), object(), object())

    result = netmon_radio_app._standalone_radio_pane_install_marker_parts(
        container,
        pane,
        marker,
        grip,
        12,
        callbacks_builder=lambda *args: events.append(("callbacks", args)) or callbacks,
        marker_parts_activator=lambda *args: events.append(("activate_parts", args)),
    )

    assert result is marker
    assert events == [
        ("callbacks", (container, pane, marker, 12)),
        ("activate_parts", (container, pane, grip, callbacks)),
    ]


def test_standalone_radio_pane_install_marker_parts_propagates_activation_failure():
    def fail_activate_parts(*_args):
        raise RuntimeError("activate parts failed")

    with pytest.raises(RuntimeError, match="activate parts failed"):
        netmon_radio_app._standalone_radio_pane_install_marker_parts(
            object(),
            object(),
            object(),
            object(),
            callbacks_builder=lambda *_args: (
                object(),
                object(),
                object(),
                object(),
            ),
            marker_parts_activator=fail_activate_parts,
        )


def test_standalone_radio_pane_install_marker_builds_widgets_and_installs_parts():
    events = []
    container = object()
    pane = object()
    marker = object()
    grip = object()
    installed_marker = object()

    result = netmon_radio_app._standalone_radio_pane_install_marker(
        container,
        pane,
        color="#123456",
        y_offset=12,
        widgets_builder=lambda *args: events.append(("widgets", args))
        or (marker, grip),
        install_parts=lambda *args: events.append(("install", args))
        or installed_marker,
    )

    assert result is installed_marker
    assert events == [
        ("widgets", (container, "#123456")),
        ("install", (container, pane, marker, grip, 12)),
    ]


def test_standalone_radio_pane_install_marker_propagates_widget_failures():
    def fail_widgets(*_args):
        raise RuntimeError("widgets failed")

    with pytest.raises(RuntimeError, match="widgets failed"):
        netmon_radio_app._standalone_radio_pane_install_marker(
            object(),
            object(),
            widgets_builder=fail_widgets,
        )


def test_station_online_indicator_uses_lastcheckok():
    app = SimpleNamespace(radio_live_status_by_station_id={"on": True, "off": False})
    assert radio_controller._station_online_indicator(app, {"id": "on"}) == "online"
    assert radio_controller._station_online_indicator(app, {"id": "off"}) == "offline"
    assert (
        radio_controller._station_online_indicator(app, {"id": "unknown"}) == "unknown"
    )


def test_station_logo_url_allows_only_web_schemes():
    app = SimpleNamespace()

    assert (
        netmon_radio_app.NetMonRadioApp._station_logo_url(
            app, {"favicon": "https://example.com/logo.png"}
        )
        == "https://example.com/logo.png"
    )
    assert (
        netmon_radio_app.NetMonRadioApp._station_logo_url(
            app, {"favicon": "http://example.com/logo.png"}
        )
        == "http://example.com/logo.png"
    )
    for blocked in (
        "file:///etc/passwd",
        "ftp://example.com/logo.png",
        "data:image/png;base64,AAAA",
        "javascript:alert(1)",
        "//example.com/logo.png",
        "example.com/logo.png",
    ):
        assert (
            netmon_radio_app.NetMonRadioApp._station_logo_url(app, {"favicon": blocked})
            == ""
        )


def test_radio_logo_size_uses_larger_embedded_main_logo():
    app = SimpleNamespace(radio_embedded_mode=True)

    assert netmon_radio_app.NetMonRadioApp._radio_logo_size(app, "main") == (110, 110)


def test_radio_logo_size_uses_larger_standalone_main_logo():
    app = SimpleNamespace(radio_embedded_mode=False)

    assert netmon_radio_app.NetMonRadioApp._radio_logo_size(app, "main") == (170, 170)
    assert radio_controller._station_online_indicator_text(app, {"id": "on"}) == "●"


def test_update_radio_database_count_label_uses_real_loaded_count():
    app = SimpleNamespace(
        radio_db=[
            {"id": "one", "name": "One", "url": "https://example.com/one"},
            {"id": "two", "name": "Two", "url": "https://example.com/two"},
            {"id": "three", "name": "Three", "url": "https://example.com/three"},
        ],
        radio_database_count_var=DummyVar(""),
        tr=lambda _key, default=None: default,
    )

    radio_controller.update_radio_database_count_label(app)

    assert app.radio_database_count_var.get() == "DB: 3 Sender"


def test_detach_radio_from_netmon_falls_back_to_host_app():
    calls = []

    class HostApp:
        def open_radio_external_app(self):
            calls.append("fallback")
            return True

    panel = SimpleNamespace(
        radio_detach_callback=lambda: False,
        radio_host_app=HostApp(),
    )

    assert netmon_radio_app.NetMonRadioApp.detach_radio_from_netmon(panel) is True
    assert calls == ["fallback"]


def test_radio_database_source_ids_for_download_use_enabled_flags():
    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    app = SimpleNamespace(
        radio_database_source_vars={
            "radio_browser_api": DummyVar(True),
            "radio_browser_search": DummyVar(False),
            "radio_browser_mirror_1": DummyVar(True),
            "radio_browser_mirror_2": DummyVar(False),
            "community_radio_api": DummyVar(True),
            "radio_browser_top": DummyVar(False),
        },
        radio_database_exclusive_mode_var=DummyVar(True),
    )

    assert radio_controller._radio_database_source_ids_for_download(app) == [
        "radio_browser_api",
        "radio_browser_mirror_1",
        "community_radio_api",
        "icecast_json",
    ]


def test_radio_database_source_ids_for_download_prefers_de_exact_exclusive():
    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    app = SimpleNamespace(
        radio_database_source_vars={
            "radio_browser_api": DummyVar(True),
            "radio_browser_country_de_exact": DummyVar(True),
            "radio_browser_search": DummyVar(True),
            "icecast_json": DummyVar(True),
        },
        radio_database_exclusive_mode_var=DummyVar(True),
    )

    assert radio_controller._radio_database_source_ids_for_download(app) == [
        "radio_browser_country_de_exact"
    ]


def test_radio_database_source_ids_for_download_prefers_any_exact_country_exclusive():
    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    app = SimpleNamespace(
        radio_database_source_vars={
            "radio_browser_api": DummyVar(True),
            "radio_browser_country_at_exact": DummyVar(True),
            "radio_browser_country_us_exact": DummyVar(False),
            "radio_browser_search": DummyVar(True),
            "icecast_json": DummyVar(True),
        },
        radio_database_exclusive_mode_var=DummyVar(True),
    )

    assert radio_controller._radio_database_source_ids_for_download(app) == [
        "radio_browser_country_at_exact"
    ]


def test_radio_database_source_ids_for_download_allows_multiple_country_lists_when_exclusive_mode_off():
    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    app = SimpleNamespace(
        radio_database_source_vars={
            "radio_browser_country_de_exact": DummyVar(True),
            "radio_browser_country_at_exact": DummyVar(True),
            "radio_browser_country_ch_exact": DummyVar(False),
            "radio_browser_country_fr_exact": DummyVar(False),
            "radio_browser_country_it_exact": DummyVar(False),
            "radio_browser_country_es_exact": DummyVar(False),
            "radio_browser_country_nl_exact": DummyVar(False),
            "radio_browser_country_be_exact": DummyVar(False),
            "radio_browser_country_gb_exact": DummyVar(False),
            "radio_browser_country_us_exact": DummyVar(False),
            "radio_browser_country_ca_exact": DummyVar(False),
            "radio_browser_country_au_exact": DummyVar(False),
            "radio_browser_country_jp_exact": DummyVar(False),
            "radio_browser_country_br_exact": DummyVar(False),
            "radio_browser_api": DummyVar(False),
            "radio_browser_search": DummyVar(False),
            "radio_browser_mirror_1": DummyVar(False),
            "radio_browser_mirror_2": DummyVar(False),
            "community_radio_api": DummyVar(False),
            "radio_browser_top": DummyVar(False),
            "icecast_json": DummyVar(True),
        },
        radio_database_exclusive_mode_var=DummyVar(False),
    )

    assert radio_controller._radio_database_source_ids_for_download(app) == [
        "radio_browser_country_de_exact",
        "radio_browser_country_at_exact",
        "icecast_json",
    ]


def test_merge_radio_source_rows_deduplicates_by_url_and_name():
    merged = radio_controller._merge_radio_source_rows(
        [
            [
                {"name": "Station A", "url": "https://example.com/a.mp3"},
                {"name": "Station B", "url": "https://example.com/b.mp3"},
            ],
            [
                {"name": "Station A", "url": "https://example.com/a.mp3"},
                {"name": "Station C", "url": "https://example.com/c.mp3"},
            ],
        ]
    )
    assert [item["name"] for item in merged] == ["Station A", "Station B", "Station C"]


def test_set_radio_database_source_indicator_updates_cache_and_label():
    label = DummyWidget()
    app = SimpleNamespace(
        radio_database_source_status_by_id={},
        radio_database_source_status_labels={"radio_browser_api": label},
        radio_status_indicator_images={"online": "green-dot"},
    )

    radio_controller._set_radio_database_source_indicator(
        app, "radio_browser_api", "online"
    )

    assert app.radio_database_source_status_by_id["radio_browser_api"] == "online"
    assert label.calls[-1] == {"image": "green-dot"}


def test_summarize_radio_database_import_results_counts_duplicates_and_errors():
    summary = radio_controller._summarize_radio_database_import_results(
        ["radio_browser_api", "icecast_json", "radio_browser_top"],
        [
            {"source_id": "radio_browser_api", "status": "ok", "count": 5000},
            {"source_id": "icecast_json", "status": "ok", "count": 1200},
            {
                "source_id": "radio_browser_top",
                "status": "error",
                "count": 0,
                "error": "timeout",
            },
        ],
        5300,
    )

    assert summary["total_sources"] == 3
    assert summary["raw_total"] == 6200
    assert summary["merged_total"] == 5300
    assert summary["duplicates_removed"] == 900
    assert summary["errors"] == ["radio_browser_top: timeout"]


def test_probe_radio_database_source_reachability_accepts_403(monkeypatch):
    class Http403Error(radio_controller.urllib.error.HTTPError):
        def __init__(self):
            super().__init__(
                "https://example.com",
                403,
                "forbidden",
                hdrs=None,
                fp=None,
            )

    def fake_urlopen(request, timeout=0):
        raise Http403Error()

    monkeypatch.setattr(radio_controller.urllib.request, "urlopen", fake_urlopen)

    assert (
        radio_controller._probe_radio_database_source_reachability(
            "radio_browser_api", timeout=0.1
        )
        is True
    )


def test_parse_icecast_entries_from_xml_maps_station_fields():
    rows = radio_controller._parse_icecast_entries_from_xml("""
        <directory>
          <entry>
            <server_name>Ice Station</server_name>
            <listen_url>https://ice.example.com/live</listen_url>
            <server_url>https://ice.example.com</server_url>
            <genre>Jazz, Smooth Jazz</genre>
            <bitrate>128</bitrate>
            <server_type>audio/mpeg</server_type>
            <country>DE</country>
            <language>de</language>
          </entry>
        </directory>
        """)

    assert len(rows) == 1
    assert rows[0]["name"] == "Ice Station"
    assert rows[0]["url"] == "https://ice.example.com/live"
    assert rows[0]["homepage"] == "https://ice.example.com"
    assert rows[0]["tags"] == ["Jazz", "Smooth Jazz"]
    assert rows[0]["bitrate"] == 128


def test_normalize_station_list_columns_keeps_valid_unique_order():
    assert radio_controller._normalize_station_list_columns(
        ["url", "name", "tags", "bitrate", "homepage", "name"]
    ) == ["url", "name", "tags", "bitrate", "homepage"]


def test_station_genre_text_prefers_category_then_first_tag():
    assert (
        radio_controller._station_genre_text(
            {"category": "Ambient", "tags": ["drone", "chill"]}
        )
        == "Ambient"
    )
    assert (
        radio_controller._station_genre_text(
            {"category": "", "tags": ["rock", "guitar"]}
        )
        == "rock"
    )
    assert (
        radio_controller._station_genre_text(
            {"category": "", "tags": ["fm", "rock", "guitar"]}
        )
        == "rock"
    )


def test_toggle_radio_station_list_column_updates_selection(monkeypatch):
    calls = []
    app = SimpleNamespace(
        radio_settings={"station_list_columns": ["name", "genre", "bitrate", "url"]},
        radio_station_table=object(),
        radio_search_results=[],
    )
    monkeypatch.setattr(
        radio_controller,
        "configure_radio_station_table_columns",
        lambda _app: calls.append("configure") or True,
    )
    monkeypatch.setattr(
        radio_controller,
        "update_radio_results_table",
        lambda _app: calls.append("refresh"),
    )
    monkeypatch.setattr(
        radio_controller,
        "save_radio_settings",
        lambda _app: calls.append("save") or True,
    )

    assert (
        radio_controller.toggle_radio_station_list_column(app, "homepage", True) is True
    )
    assert radio_controller.toggle_radio_station_list_column(app, "url", False) is True
    assert (
        radio_controller.toggle_radio_station_list_column(app, "homepage", True) is True
    )
    assert app.radio_settings["station_list_columns"] == [
        "name",
        "genre",
        "bitrate",
        "homepage",
    ]
    assert calls.count("configure") == 2


def test_probe_radio_station_reachability_uses_urlopen(monkeypatch):
    calls = []

    class DummyResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def getcode(self):
            return 200

    def fake_urlopen(request, timeout=0):
        calls.append((request.full_url, timeout, dict(request.headers)))
        return DummyResponse()

    monkeypatch.setattr(radio_controller.urllib.request, "urlopen", fake_urlopen)

    assert (
        radio_controller._probe_radio_station_reachability(
            {"url": "https://example.com/stream"}
        )
        is True
    )
    assert calls


def test_probe_radio_station_reachability_accepts_icy_response(monkeypatch):
    def fake_urlopen(request, timeout=0):
        raise http.client.BadStatusLine("ICY 200 OK")

    monkeypatch.setattr(radio_controller.urllib.request, "urlopen", fake_urlopen)

    assert (
        radio_controller._probe_radio_station_reachability(
            {"url": "https://example.com/stream"}
        )
        is True
    )


def test_check_visible_radio_station_reachability_resets_current_page_statuses(
    monkeypatch,
):
    scheduled = []
    app = SimpleNamespace(
        radio_reachability_check_running=False,
        radio_search_results=[
            {"id": "one", "url": "https://a"},
            {"id": "two", "url": "https://b"},
        ],
        radio_search_page=0,
        radio_live_status_by_station_id={"one": True, "two": False, "other": True},
        radio_reachability_button=None,
    )

    monkeypatch.setattr(radio_controller, "RADIO_RESULTS_PER_PAGE", 50)
    monkeypatch.setattr(
        radio_controller,
        "update_radio_results_table",
        lambda _app: scheduled.append("refresh"),
    )
    monkeypatch.setattr(
        radio_controller,
        "set_radio_status",
        lambda _app, message: scheduled.append(message),
    )
    monkeypatch.setattr(
        radio_controller,
        "_schedule_ui",
        lambda _app, callback: callback(),
    )

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target is not None:
                self._target()

    monkeypatch.setattr(radio_controller.threading, "Thread", ImmediateThread)

    class ImmediatePool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, row):
            class DoneFuture:
                def result(self_inner):
                    return fn(row)

            return DoneFuture()

    monkeypatch.setattr(
        radio_controller.concurrent.futures,
        "ThreadPoolExecutor",
        ImmediatePool,
    )
    monkeypatch.setattr(
        radio_controller.concurrent.futures,
        "as_completed",
        lambda futures: list(futures),
    )
    monkeypatch.setattr(
        radio_controller,
        "_probe_radio_station_reachability",
        lambda row, timeout=4.0: row["id"] == "one",
    )

    assert radio_controller.check_visible_radio_station_reachability(app) is True
    assert app.radio_live_status_by_station_id["one"] is True
    assert app.radio_live_status_by_station_id["two"] is False
    assert app.radio_live_status_by_station_id["other"] is True
    assert app.radio_reachability_check_running is False


def test_check_visible_radio_station_reachability_falls_back_to_lastcheckok(
    monkeypatch,
):
    app = SimpleNamespace(
        radio_reachability_check_running=False,
        radio_search_results=[
            {"id": "one", "url": "https://a", "lastcheckok": True},
        ],
        radio_search_page=0,
        radio_live_status_by_station_id={},
        radio_reachability_button=None,
    )

    monkeypatch.setattr(
        radio_controller, "update_radio_results_table", lambda _app: None
    )
    monkeypatch.setattr(
        radio_controller, "set_radio_status", lambda _app, message: None
    )
    monkeypatch.setattr(
        radio_controller, "_schedule_ui", lambda _app, callback: callback()
    )

    class ImmediateThread:
        def __init__(self, target=None, daemon=None):
            self._target = target

        def start(self):
            if self._target is not None:
                self._target()

    monkeypatch.setattr(radio_controller.threading, "Thread", ImmediateThread)

    class ImmediatePool:
        def __init__(self, max_workers=None):
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def submit(self, fn, row):
            class DoneFuture:
                def result(self_inner):
                    return fn(row)

            return DoneFuture()

    monkeypatch.setattr(
        radio_controller.concurrent.futures,
        "ThreadPoolExecutor",
        ImmediatePool,
    )
    monkeypatch.setattr(
        radio_controller.concurrent.futures,
        "as_completed",
        lambda futures: list(futures),
    )
    monkeypatch.setattr(
        radio_controller,
        "_probe_radio_station_reachability",
        lambda row, timeout=4.0: None,
    )

    assert radio_controller.check_visible_radio_station_reachability(app) is True
    assert app.radio_live_status_by_station_id["one"] is True


def test_radio_core_builds_external_app_command():
    command = netmon_radio_core.build_radio_app_command(
        "/usr/bin/python3", started_from="desktop"
    )

    assert command[0] == "/usr/bin/python3"
    assert command[1:3] == ["-m", "netmon.netmon_radio_app"]
    assert command[-2:] == ["--started-from", "desktop"]


def test_radio_core_builds_desktop_exec_command_with_wrapper_path(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.project_python_executable",
        lambda: "/usr/bin/python3",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_wrapper_path",
        lambda: "/workspaces/dev-lab/netmon_radio_app.py",
    )

    command = netmon_radio_core.build_radio_desktop_exec_command(theme_name="dark")

    assert command == (
        "/usr/bin/python3 /workspaces/dev-lab/netmon_radio_app.py "
        "--theme dark --started-from desktop"
    )


def test_radio_core_builds_wrapper_command(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.project_python_executable",
        lambda: "/usr/bin/python3",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_wrapper_path",
        lambda: "/workspaces/dev-lab/netmon_radio_app.py",
    )

    command = netmon_radio_core.build_radio_wrapper_command(
        theme_name="dark",
        started_from="netmon_detach",
    )

    assert command == [
        "/usr/bin/python3",
        "/workspaces/dev-lab/netmon_radio_app.py",
        "--theme",
        "dark",
        "--started-from",
        "netmon_detach",
    ]


def test_radio_core_builds_desktop_entry_with_repo_path(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.repo_root",
        lambda: "/workspaces/dev-lab",
    )

    entry = netmon_radio_core.build_radio_desktop_entry("/usr/bin/python3 app.py")

    assert "Exec=/usr/bin/python3 app.py\n" in entry
    assert "Path=/workspaces/dev-lab\n" in entry
    assert "StartupWMClass=NetMonRadio\n" in entry


def test_radio_core_runtime_desktop_entry_is_hidden_and_uses_radio_icon(
    tmp_path, monkeypatch
):
    runtime_path = tmp_path / "state" / "netmon-radio-runtime.desktop"
    icon_path = tmp_path / "tools" / "netmon2.png"
    icon_path.parent.mkdir(parents=True)
    icon_path.write_text("png", encoding="utf-8")

    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_runtime_desktop_entry_path",
        lambda: str(runtime_path),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_icon_path",
        lambda: str(icon_path),
    )

    path = netmon_radio_core.ensure_radio_runtime_desktop_entry(theme_name="dark")

    assert path == str(runtime_path)
    content = runtime_path.read_text(encoding="utf-8")
    assert "NoDisplay=true\n" in content
    assert "StartupWMClass=NetMonRadio\n" in content
    assert f"Icon={icon_path}\n" in content


def test_radio_core_launch_radio_app_returns_none_on_early_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.project_python_executable",
        lambda: "/usr/bin/python3",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_wrapper_path",
        lambda: "/workspaces/dev-lab/netmon_radio_app.py",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.repo_root", lambda: "/workspaces/dev-lab"
    )
    monkeypatch.setattr("netmon.netmon_radio_core.time.sleep", lambda _seconds: None)
    monkeypatch.setattr("netmon.netmon_radio_core.shutil.which", lambda cmd: "")

    class DummyProc:
        pid = 4321

        def poll(self):
            return 2

    monkeypatch.setattr(
        "netmon.netmon_radio_core.subprocess.Popen",
        lambda *args, **kwargs: DummyProc(),
    )

    logs = []
    proc = netmon_radio_core.launch_radio_app(
        logger=logs.append, started_from="netmon_detach"
    )

    assert proc is None
    assert logs
    assert "sofort wieder beendet" in logs[-1]


def test_radio_core_launch_radio_app_sets_desktop_file_hints(tmp_path, monkeypatch):
    captured = {}
    logs = []

    class DummyProc:
        pid = 12345

        def poll(self):
            return None

    monkeypatch.setattr(
        "netmon.netmon_radio_core.ensure_radio_runtime_desktop_entry",
        lambda theme_name=None, started_from=None: "/tmp/netmon-radio-runtime.desktop",
    )
    # Auf Hosts mit installiertem NetMon existiert die installierte
    # netmon-radio.desktop und wird bevorzugt. Fuer den Test auf einen nicht
    # vorhandenen Pfad zeigen, damit zuverlaessig der Runtime-Desktop-Zweig greift.
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_desktop_entry_path",
        lambda: str(tmp_path / "applications" / "netmon-radio.desktop"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )

    def fake_popen(*args, **kwargs):
        captured.update(kwargs)
        return DummyProc()

    monkeypatch.setattr("netmon.netmon_radio_core.subprocess.Popen", fake_popen)
    monkeypatch.setattr("netmon.netmon_radio_core.time.sleep", lambda _seconds: None)
    monkeypatch.setattr("netmon.netmon_radio_core.shutil.which", lambda cmd: "")

    proc = netmon_radio_core.launch_radio_app(
        logger=logs.append,
        started_from="netmon_detach",
    )

    assert proc is not None
    assert (
        captured["env"]["BAMF_DESKTOP_FILE_HINT"] == "/tmp/netmon-radio-runtime.desktop"
    )
    assert (
        captured["env"]["GIO_LAUNCHED_DESKTOP_FILE"]
        == "/tmp/netmon-radio-runtime.desktop"
    )
    assert any(
        "desktop_hint=/tmp/netmon-radio-runtime.desktop" in item for item in logs
    )


def test_radio_core_launch_radio_app_uses_runtime_desktop_id_for_gtk_launch(
    tmp_path, monkeypatch
):
    captured = {}

    class DummyProc:
        pid = 45678

        def poll(self):
            return None

    monkeypatch.setattr(
        "netmon.netmon_radio_core.ensure_radio_runtime_desktop_entry",
        lambda theme_name=None, started_from=None: "/tmp/netmon-radio-runtime.desktop",
    )
    # Auf Hosts mit installiertem NetMon existiert die installierte
    # netmon-radio.desktop und wird bevorzugt. Fuer den Test auf einen nicht
    # vorhandenen Pfad zeigen, damit zuverlaessig der Runtime-Desktop-Zweig greift.
    monkeypatch.setattr(
        "netmon.netmon_radio_core.radio_desktop_entry_path",
        lambda: str(tmp_path / "applications" / "netmon-radio.desktop"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.shutil.which", lambda cmd: "/usr/bin/gtk-launch"
    )
    monkeypatch.setattr("netmon.netmon_radio_core.time.sleep", lambda _seconds: None)

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs.get("env")
        return DummyProc()

    monkeypatch.setattr("netmon.netmon_radio_core.subprocess.Popen", fake_popen)

    proc = netmon_radio_core.launch_radio_app(started_from="netmon_detach")

    assert proc is not None
    assert captured["command"] == ["gtk-launch", "netmon-radio-runtime"]
    assert (
        captured["env"]["BAMF_DESKTOP_FILE_HINT"] == "/tmp/netmon-radio-runtime.desktop"
    )


def test_radio_core_host_and_attach_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )
    monkeypatch.setattr("netmon.netmon_radio_core.os.kill", lambda pid, sig: None)

    assert netmon_radio_core.write_netmon_host_state(12345) is True
    state = netmon_radio_core.read_radio_host_state()
    assert state["owner_pid"] == 12345
    assert state["mode"] == "embedded"
    assert state["attached"] is True
    assert state["launcher_state"] == "embedded_active"
    assert netmon_radio_core.netmon_host_is_available() is True
    assert (
        netmon_radio_core.write_radio_host_state(
            mode="standalone",
            owner_pid=9876,
            current_station_id="station-7",
            started_from="desktop",
        )
        is True
    )
    state = netmon_radio_core.read_radio_host_state()
    assert state["owner_pid"] == 9876
    assert state["mode"] == "standalone"
    assert state["launcher_state"] == "standalone_active"
    assert state["current_station_id"] == "station-7"
    assert state["started_from"] == "desktop"
    assert netmon_radio_core.set_radio_detached_state(True) is True
    assert netmon_radio_core.radio_is_detached() is True
    state = netmon_radio_core.read_radio_host_state()
    assert state["attached"] is False
    assert state["mode"] == "standalone"
    assert state["launcher_state"] == "standalone_active"
    assert netmon_radio_core.current_radio_transition_id() == ""
    assert netmon_radio_core.begin_radio_transition(
        from_mode="standalone",
        target_mode="embedded",
        owner_pid=9876,
        current_station_id="station-7",
        started_from="desktop",
    )
    transition_id = netmon_radio_core.current_radio_transition_id()
    assert transition_id
    assert (
        netmon_radio_core.request_radio_handover(
            target_mode="standalone",
            payload={"current_station_id": "station-7", "was_playing": True},
            action="detach",
            transition_id=transition_id,
        )
        is True
    )
    assert netmon_radio_core.consume_radio_handover("embedded") is None
    assert (
        netmon_radio_core.consume_radio_handover(
            "standalone", transition_id="stale-transition"
        )
        is None
    )
    handover = netmon_radio_core.consume_radio_handover("standalone")
    assert handover["current_station_id"] == "station-7"
    assert handover["was_playing"] is True
    assert (
        netmon_radio_core.request_radio_handover_ack(
            target_mode="embedded",
            payload={"action": "detach_ready"},
            transition_id=transition_id,
        )
        is True
    )
    assert (
        netmon_radio_core.consume_radio_handover_ack(
            "embedded", transition_id="stale-transition"
        )
        is None
    )
    ack_payload = netmon_radio_core.consume_radio_handover_ack("embedded")
    assert ack_payload["action"] == "detach_ready"
    assert netmon_radio_core.request_radio_attach(transition_id=transition_id) is True
    assert (
        netmon_radio_core.consume_radio_attach_request(transition_id="stale-transition")
        is False
    )
    assert netmon_radio_core.consume_radio_attach_request() is True
    assert netmon_radio_core.consume_radio_attach_request() is False
    assert (
        netmon_radio_core.request_standalone_radio_attach(transition_id=transition_id)
        is True
    )
    assert (
        netmon_radio_core.consume_standalone_radio_attach_request(
            transition_id="stale-transition"
        )
        is False
    )
    assert netmon_radio_core.consume_standalone_radio_attach_request() is True
    assert netmon_radio_core.consume_standalone_radio_attach_request() is False
    assert netmon_radio_core.request_standalone_radio_attach() is True
    assert netmon_radio_core.clear_standalone_radio_attach_request() is True
    assert netmon_radio_core.consume_standalone_radio_attach_request() is False
    assert (
        netmon_radio_core.request_standalone_radio_show(transition_id=transition_id)
        is True
    )
    assert (
        netmon_radio_core.consume_standalone_radio_show_request(
            transition_id="stale-transition"
        )
        is False
    )
    assert netmon_radio_core.consume_standalone_radio_show_request() is True
    assert netmon_radio_core.consume_standalone_radio_show_request() is False
    assert netmon_radio_core.request_radio_attach() is True
    assert netmon_radio_core.clear_radio_attach_request() is True
    assert netmon_radio_core.consume_radio_attach_request() is False
    assert netmon_radio_core.clear_netmon_host_state(9876) is True


def test_radio_core_set_radio_mode_updates_host_state(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )

    assert (
        netmon_radio_core.set_radio_mode(
            "embedded",
            owner_pid=55,
            current_station_id="station-a",
            started_from="netmon_tab",
        )
        is True
    )

    state = netmon_radio_core.read_radio_host_state()
    assert state["owner_pid"] == 55
    assert state["mode"] == "embedded"
    assert state["attached"] is True
    assert state["launcher_state"] == "embedded_active"
    assert state["current_station_id"] == "station-a"
    assert state["started_from"] == "netmon_tab"


def test_radio_core_write_launcher_state_derives_legacy_fields(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )

    assert (
        netmon_radio_core.write_radio_launcher_state(
            launcher_state="attaching",
            owner_pid=777,
            current_station_id="station-z",
            started_from="test",
            session_id="session-777",
            transition_id="transition-777",
        )
        is True
    )

    state = netmon_radio_core.read_radio_host_state()
    assert state["launcher_state"] == "attaching"
    assert state["mode"] == "standalone"
    assert state["attached"] is False
    assert state["transition_state"] == "pending"
    assert state["transition_target"] == "embedded"
    assert state["current_station_id"] == "station-z"
    assert state["session_id"] == "session-777"
    assert state["transition_id"] == "transition-777"


def test_radio_core_transition_helpers_track_pending_and_complete(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_config_dir",
        lambda: str(tmp_path / "config"),
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.get_netmon_state_dir",
        lambda: str(tmp_path / "state"),
    )

    assert (
        netmon_radio_core.begin_radio_transition(
            from_mode="embedded",
            target_mode="standalone",
            owner_pid=111,
            current_station_id="station-x",
            started_from="netmon_detach",
        )
        is True
    )
    state = netmon_radio_core.read_radio_host_state()
    assert state["launcher_state"] == "detaching"
    assert netmon_radio_core.radio_transition_in_progress("standalone") is True
    assert netmon_radio_core.cancel_radio_transition(111) is True
    assert netmon_radio_core.radio_transition_in_progress("standalone") is False

    assert (
        netmon_radio_core.complete_radio_transition(
            mode="standalone",
            owner_pid=222,
            current_station_id="station-y",
            started_from="desktop",
            attached=False,
        )
        is True
    )
    state = netmon_radio_core.read_radio_host_state()
    assert state["mode"] == "standalone"
    assert state["launcher_state"] == "standalone_active"
    assert state["owner_pid"] == 222


def test_radio_core_prefers_project_venv_python(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_radio_core.project_venv_python_executable",
        lambda: "/tmp/netmon-venv/bin/python",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.os.path.isfile",
        lambda path: path == "/tmp/netmon-venv/bin/python",
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_core.os.access",
        lambda path, mode: path == "/tmp/netmon-venv/bin/python",
    )

    assert (
        netmon_radio_core.project_python_executable() == "/tmp/netmon-venv/bin/python"
    )


def test_standalone_radio_app_supports_headless_smoke_flag():
    source = inspect.getsource(netmon_radio_app.main)

    assert "--headless-smoke" in source
    assert "--started-from" in source
    assert "standalone_radio_is_running()" in source
    assert "app.update_idletasks()" in source
    assert "app._on_close()" in source


def test_app_and_standalone_sources_include_radio_handover_flow():
    app_source = inspect.getsource(App.open_radio_external_app)
    reattach_source = inspect.getsource(App.reattach_radio_app)
    poll_source = inspect.getsource(App._poll_radio_attach_request)
    startup_source = inspect.getsource(netmon_radio_app.NetMonRadioApp.__init__)
    app_init_source = inspect.getsource(App.__init__)
    standalone_poll_source = inspect.getsource(
        netmon_radio_app.NetMonRadioApp._poll_radio_attach_state
    )
    standalone_attach_source = inspect.getsource(
        netmon_radio_app.NetMonRadioApp.attach_radio_to_netmon
    )

    assert "build_radio_handover_payload" in app_source
    assert "clear_radio_attach_request" in app_source
    assert "clear_standalone_radio_attach_request" in app_source
    assert "begin_radio_transition" in app_source
    assert "set_radio_detached_state(True)" in app_source
    assert "request_standalone_radio_show()" in app_source
    assert "cancel_radio_transition" in app_source
    assert (
        'request_radio_handover(\n                target_mode="standalone"'
        in app_source
    )
    assert "apply_radio_handover_payload" in reattach_source
    assert 'consume_radio_handover(\n                        "embedded"' in poll_source
    assert "source_app.stop_radio_playback(async_mode=False)" in poll_source
    assert "radio_controller.play_radio_station(" in startup_source
    assert "build_radio_handover_payload" in standalone_attach_source
    assert "begin_radio_transition" in standalone_attach_source
    assert (
        'request_radio_handover(\n                target_mode="embedded"'
        in standalone_attach_source
    )
    assert "request_standalone_radio_attach()" in reattach_source
    assert "consume_standalone_radio_attach_request(" in standalone_poll_source
    assert "consume_standalone_radio_show_request(" in standalone_poll_source
    assert "standalone_radio_is_running()" in app_init_source


def test_phase5_sources_include_transition_status_messages():
    app_source = inspect.getsource(App.open_radio_external_app)
    reattach_source = inspect.getsource(App.reattach_radio_app)
    close_source = inspect.getsource(App.on_close)
    radio_tab_source = inspect.getsource(build_radio_tab)
    standalone_source = inspect.getsource(
        netmon_radio_app.NetMonRadioApp.refresh_radio_attach_state
    )

    assert "Radio wird bereits als Standalone-App gestartet." in app_source
    assert "Radio wird als Standalone-App gestartet." in app_source
    assert "Radio wird wieder an NetMon angeheftet." in reattach_source
    assert "detached_radio or standalone_transition" in close_source
    assert "Radio wird gerade als Standalone-App gestartet." in radio_tab_source
    assert "Radio wird gerade wieder an NetMon angeheftet." in radio_tab_source
    assert "Radio wird gerade an NetMon angeheftet." in standalone_source


def test_on_close_keeps_detached_radio_running(monkeypatch):
    app = App.__new__(App)
    calls = []

    class DummyPanel:
        def close_projectm_visualizer_test(self):
            calls.append("panel-close-projectm")

        def stop_radio_playback(self, async_mode=False):
            calls.append(("panel-stop-radio", async_mode))

    app.system_monitor_active = True
    app.process_guard_monitoring = True
    app.radio_embedded_panel = DummyPanel()
    app.stop_radio = lambda: calls.append("stop-radio")
    app.stop_running_fun_game = lambda: calls.append("stop-fun")
    app.destroy = lambda: calls.append("destroy")

    monkeypatch.setattr(
        "netmon.app.netmon_radio_core.radio_is_detached",
        lambda: True,
    )
    monkeypatch.setattr(
        "netmon.app.netmon_radio_core.radio_transition_in_progress",
        lambda _target=None: False,
    )
    monkeypatch.setattr(
        "netmon.app.netmon_radio_core.clear_netmon_host_state",
        lambda _pid: calls.append("clear-host"),
    )

    app.on_close()

    assert "stop-radio" not in calls
    assert "panel-close-projectm" not in calls
    assert ("panel-stop-radio", False) not in calls
    assert "clear-host" in calls
    assert "stop-fun" in calls
    assert "destroy" in calls


def test_standalone_close_auto_reattaches_when_netmon_is_available(monkeypatch):
    app = netmon_radio_app.NetMonRadioApp.__new__(netmon_radio_app.NetMonRadioApp)
    calls = []

    app.log_safe = lambda message: calls.append(("log", message))
    app.attach_radio_to_netmon = lambda: calls.append("attach") or True
    app.close_projectm_visualizer_test = lambda: calls.append("close-projectm")
    app.stop_radio_playback = lambda async_mode=False: calls.append(
        ("stop-radio", async_mode)
    )
    app.destroy = lambda: calls.append("destroy")

    monkeypatch.setattr(
        "netmon.netmon_radio_app.netmon_radio_core.read_radio_host_state",
        lambda: {"mode": "standalone", "owner_pid": 12345},
    )
    monkeypatch.setattr(
        "netmon.netmon_radio_app.netmon_radio_core.netmon_host_is_available",
        lambda: True,
    )
    monkeypatch.setattr("netmon.netmon_radio_app.os.getpid", lambda: 12345)

    app._on_close()

    assert "attach" in calls
    assert "destroy" not in calls


def test_refresh_projectm_status_disables_install_button_when_installed(monkeypatch):
    app = netmon_radio_app.NetMonRadioApp.__new__(netmon_radio_app.NetMonRadioApp)
    app.radio_projectm_proc = None
    app.radio_projectm_log_path = ""
    app.radio_projectm_command = []
    app.radio_projectm_last_started_at = ""
    app.radio_projectm_last_stopped_at = ""
    app.radio_projectm_status_var = DummyVar("")
    app.radio_projectm_meta_var = DummyVar("")
    app.radio_projectm_history_var = DummyVar("")
    app.radio_projectm_install_var = DummyVar("")
    app.radio_projectm_install_button = DummyWidget()

    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.describe_projectm_sidecar_runtime",
        lambda _app: {
            "running": False,
            "installed": True,
            "installable": True,
            "pid": 0,
            "command": "",
            "log_path": "/tmp/projectm.log",
            "status_text": "projectM: gestoppt",
            "install_text": "projectM Backend: Binary",
            "install_command": "",
            "backend_label": "Binary",
        },
    )

    netmon_radio_app.NetMonRadioApp._refresh_projectm_status(app)

    assert app.radio_projectm_install_var.get() == "projectM Backend: Binary"
    assert app.radio_projectm_install_button.calls[-1]["state"] == "disabled"


def test_standalone_radio_app_has_projectm_hooks_only():
    app_source = inspect.getsource(netmon_radio_app.NetMonRadioApp)
    init_source = inspect.getsource(netmon_radio_app._init_radio_runtime_state)
    ui_init_source = inspect.getsource(netmon_radio_app._init_radio_ui_state)
    main_app_source = inspect.getsource(App)
    sidecar_source = inspect.getsource(
        netmon_projectm_sidecar.describe_projectm_sidecar_runtime
    )

    assert "def _timestamp_text(self):" in app_source
    assert "def _on_scroll_content_configure(self, _event=None):" in app_source
    assert "def _on_scroll_canvas_configure(self, event):" in app_source
    assert "def _on_mousewheel(self, event):" in app_source
    assert "def _on_shift_mousewheel(self, event):" in app_source
    assert "def _on_page_down(self, _event=None):" in app_source
    assert "def _on_page_up(self, _event=None):" in app_source
    assert "def _on_home_scroll(self, _event=None):" in app_source
    assert "def _on_end_scroll(self, _event=None):" in app_source
    assert "def _refresh_projectm_status(self):" in app_source
    assert "def open_projectm_visualizer_test(self):" in app_source
    assert "def close_projectm_visualizer_test(self):" in app_source
    assert "def install_projectm_visualizer(self):" in app_source
    assert "radio_projectm_last_started_at" in app_source
    assert "radio_projectm_last_stopped_at" in app_source
    assert "netmon_projectm_sidecar.ensure_projectm_preset_dir(app)" in init_source
    assert "netmon_projectm_sidecar.ensure_projectm_preset_dir(self)" in main_app_source
    assert '"radio_projectm_btn_open_presets"' in app_source
    assert '"radio_projectm_btn_manage_presets"' in app_source
    assert "projectM preset folder: preparing Documents/NetMon" in ui_init_source
    assert "checking downloaded packs and custom imports" in ui_init_source
    assert "heruntergeladenen Preset-Packs und eigenen Imports" in sidecar_source


def test_netmon_windows_apply_custom_taskbar_icons():
    app_init_source = inspect.getsource(App.__init__)
    app_source = inspect.getsource(App)
    radio_source = inspect.getsource(netmon_radio_app.NetMonRadioApp)

    assert 'super().__init__(className="NetMon")' in app_init_source
    assert "self._apply_window_icon()" in app_init_source
    assert (
        'self.after(1200, lambda: self._log_window_integration_diagnostic("startup"))'
        in app_init_source
    )
    assert "def _window_icon_asset_path(self) -> str:" in app_source
    assert "def _apply_window_icon(self) -> None:" in app_source
    assert "def _window_integration_context(self) -> dict[str, str]:" in app_source
    assert (
        "def _log_window_integration_diagnostic(self, stage: str) -> None:"
        in app_source
    )
    assert 'super().__init__(className="NetMonRadio")' in radio_source
    assert "def _window_icon_asset_path(self):" in radio_source
    assert "def _apply_window_icon(self):" in radio_source
    assert (
        'self.after(600, lambda: self._log_window_integration_diagnostic("startup"))'
        in radio_source
    )
    assert "def _window_integration_context(self):" in radio_source
    assert "def _log_window_integration_diagnostic(self, stage):" in radio_source
    assert 'os.path.join(repo_root, "tools", "netmon2.png")' in radio_source


def test_projectm_sidecar_prefers_pulseaudio_command_variants(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.shutil.which",
        lambda name: {
            "projectM-pulseaudio": "/usr/bin/projectM-pulseaudio",
            "projectm": "/usr/bin/projectm",
        }.get(name),
    )

    assert netmon_projectm_sidecar._detect_projectm_command() == [
        "/usr/bin/projectM-pulseaudio"
    ]


def test_projectm_sidecar_parses_optional_apt_candidates():
    result = netmon_projectm_sidecar._parse_apt_policy_output("""
projectm-pulseaudio:
  Installed: (none)
  Candidate: 3.1.12-3
  Version table:
     3.1.12-3 500
        500 http://deb.debian.org/debian bookworm/main amd64 Packages
""")

    assert result["installable"] is True
    assert result["available_packages"] == ["projectm-pulseaudio"]
    assert (
        netmon_projectm_sidecar.build_projectm_install_command(result)
        == "sudo apt install -y projectm-pulseaudio"
    )


def test_projectm_sidecar_detects_flatpak_install(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.shutil.which",
        lambda name: "/usr/bin/flatpak" if name == "flatpak" else None,
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar._read_flatpak_list_output",
        lambda _path: "projectM\tnet.sourceforge.projectM\tstable",
    )

    status = netmon_projectm_sidecar.get_projectm_sidecar_status()

    assert status.installed is True
    assert status.backend_label == "Flatpak"
    assert status.command == ["/usr/bin/flatpak", "run", "net.sourceforge.projectM"]


def test_projectm_sidecar_prefers_flatpak_install_when_apt_missing(monkeypatch):
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.subprocess.run",
        lambda *args, **kwargs: type("Completed", (), {"stdout": "", "stderr": ""})(),
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.shutil.which",
        lambda name: "/usr/bin/flatpak" if name == "flatpak" else None,
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar._read_flatpak_list_output",
        lambda _path: "",
    )

    probe = netmon_projectm_sidecar.probe_projectm_package_candidates(refresh=True)

    assert probe["install_strategy"] == "flatpak"
    assert (
        netmon_projectm_sidecar.build_projectm_install_command(probe)
        == "flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo && flatpak install -y flathub net.sourceforge.projectM"
    )


def test_projectm_preset_dir_uses_netmon_documents_dir(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Documents" / "NetMon"
    docs_dir.mkdir(parents=True)
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_netmon_documents_dir",
        lambda: str(docs_dir),
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_projectm_sidecar_status",
        lambda app=None: netmon_projectm_sidecar.ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=True,
            backend_id="projectm_external",
            message="ok",
            command=["/usr/bin/projectm"],
            backend_label="Binary",
        ),
    )

    path = netmon_projectm_sidecar.get_projectm_preset_dir()

    assert path == os.path.join(
        str(docs_dir),
        "projectM Visualizer",
        "Presets",
    )


def test_projectm_log_path_uses_documents_logs_and_migrates_state_log(
    monkeypatch, tmp_path
):
    docs_logs_dir = tmp_path / "Documents" / "NetMon" / "Logs"
    state_logs_dir = tmp_path / "state" / "logs"
    state_logs_dir.mkdir(parents=True)
    legacy_log = state_logs_dir / "projectm_visualizer.log"
    legacy_log.write_text("legacy projectm log\n", encoding="utf-8")

    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_netmon_documents_subdir",
        lambda *parts: str(docs_logs_dir),
    )
    app = SimpleNamespace(netmon_state_dir=str(tmp_path / "state"))

    path = netmon_projectm_sidecar._log_path(app)

    assert path == str(docs_logs_dir / "projectm_visualizer.log")
    assert (docs_logs_dir / "projectm_visualizer.log").read_text(
        encoding="utf-8"
    ) == "legacy projectm log\n"


def test_ensure_projectm_preset_dir_migrates_legacy_presets_without_bundled_sync(
    monkeypatch, tmp_path
):
    docs_dir = tmp_path / "Documents" / "NetMon"
    docs_dir.mkdir(parents=True)
    legacy_dir = tmp_path / "state" / "projectm_presets"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "legacy.milk").write_text("legacy", encoding="utf-8")

    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_netmon_documents_dir",
        lambda: str(docs_dir),
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar._sync_projectm_flatpak_playlist_file",
        lambda app, preset_dir: None,
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_projectm_sidecar_status",
        lambda app=None: netmon_projectm_sidecar.ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=True,
            backend_id="projectm_external",
            message="ok",
            command=["/usr/bin/projectm"],
            backend_label="Binary",
        ),
    )
    app = SimpleNamespace(
        netmon_state_dir=str(tmp_path / "state"), log_safe=lambda *_: None
    )

    preset_dir = netmon_projectm_sidecar.ensure_projectm_preset_dir(app)

    assert preset_dir == os.path.join(
        str(docs_dir),
        "projectM Visualizer",
        "Presets",
    )
    assert os.path.isfile(os.path.join(preset_dir, "legacy.milk"))
    assert not os.path.exists(os.path.join(preset_dir, "NetMon Presets"))


def test_install_projectm_preset_archive_extracts_zip_pack(monkeypatch, tmp_path):
    docs_dir = tmp_path / "Documents" / "NetMon"
    docs_dir.mkdir(parents=True)
    archive_path = tmp_path / "preset-pack.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("cool-pack/visuals/alpha.milk", "preset")
        archive.writestr("cool-pack/assets/cover.png", "png")
        archive.writestr("cool-pack/readme.txt", "ignored")

    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_netmon_documents_dir",
        lambda: str(docs_dir),
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar._sync_projectm_flatpak_playlist_file",
        lambda app, preset_dir: None,
    )
    monkeypatch.setattr(
        "netmon.netmon_projectm_sidecar.get_projectm_sidecar_status",
        lambda app=None: netmon_projectm_sidecar.ProjectMSidecarStatus(
            available=True,
            installed=True,
            installable=True,
            backend_id="projectm_external",
            message="ok",
            command=["/usr/bin/projectm"],
            backend_label="Binary",
        ),
    )

    result = netmon_projectm_sidecar.install_projectm_preset_archive(
        SimpleNamespace(netmon_state_dir=str(tmp_path / "state")),
        str(archive_path),
        pack_name="Cool Pack",
    )

    assert result["imported_presets"] == 1
    assert result["imported_assets"] == 1
    assert os.path.isfile(
        os.path.join(
            result["target_dir"],
            "visuals",
            "alpha.milk",
        )
    )
    assert os.path.isfile(
        os.path.join(
            result["target_dir"],
            "assets",
            "cover.png",
        )
    )


def test_refresh_radio_playlist_ui_updates_list_and_buttons(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_playlist_entries = [
        str(tmp_path / "first.mp3"),
        str(tmp_path / "second.mp3"),
    ]
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_listbox = DummyListbox(selection=(1,))
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_host_app = None

    original_has_cmd = radio_controller.has_cmd
    try:
        radio_controller.has_cmd = lambda name: name == "mpv"
        radio_controller.refresh_radio_playlist_ui(app)
    finally:
        radio_controller.has_cmd = original_has_cmd

    assert app.radio_playlist_status_var.get() == "Playlist: 2 Dateien"
    assert app.radio_playlist_listbox.items == ["first.mp3", "second.mp3"]
    assert app.radio_playlist_play_selected_button.calls[-1]["state"] == "normal"
    assert app.radio_playlist_remove_button.calls[-1]["state"] == "normal"
    assert app.radio_playlist_clear_button.calls[-1]["state"] == "normal"


def test_add_radio_playlist_files_appends_unique_paths(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(tmp_path)
    app.radio_playlist_entries = [str(tmp_path / "kept.mp3")]
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_listbox = DummyListbox()
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    original_dialog = radio_controller.filedialog.askopenfilenames
    try:
        radio_controller.filedialog.askopenfilenames = lambda **_kwargs: (
            str(tmp_path / "kept.mp3"),
            str(tmp_path / "new.mp3"),
        )
        assert radio_controller.add_radio_playlist_files(app) is True
    finally:
        radio_controller.filedialog.askopenfilenames = original_dialog

    assert app.radio_playlist_entries == [
        str(tmp_path / "kept.mp3"),
        str(tmp_path / "new.mp3"),
    ]
    assert app.radio_playlist_status_var.get() == "Playlist: 2 Dateien"
    assert app.radio_record_status_var.get() == "Playlist erweitert: 1 Datei(en)."


def test_play_selected_radio_playlist_entry_uses_local_playback(tmp_path):
    audio_path = tmp_path / "mix.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_playlist_entries = [str(audio_path)]
    app.radio_playlist_listbox = DummyListbox(selection=(0,))
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    play_calls = []
    original_play = radio_controller._play_local_audio_file
    try:
        radio_controller._play_local_audio_file = (
            lambda current_app, path, **kwargs: play_calls.append(
                (current_app, path, kwargs)
            )
            or True
        )
        assert radio_controller.play_selected_radio_playlist_entry(app) is True
    finally:
        radio_controller._play_local_audio_file = original_play

    assert play_calls == [
        (
            app,
            str(audio_path),
            {
                "station_name": "Playlist",
                "title_text": "Datei: mix.mp3",
            },
        )
    ]


def test_remove_selected_radio_playlist_entry_updates_state(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_playlist_entries = [str(tmp_path / "a.mp3"), str(tmp_path / "b.mp3")]
    app.radio_playlist_listbox = DummyListbox(selection=(0,))
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.remove_selected_radio_playlist_entry(app) is True

    assert app.radio_playlist_entries == [str(tmp_path / "b.mp3")]
    assert app.radio_playlist_status_var.get() == "Playlist: 1 Datei"
    assert app.radio_record_status_var.get() == "Playlist-Eintrag entfernt: a.mp3"


def test_play_current_radio_source_replays_local_file_mode(tmp_path):
    audio_path = tmp_path / "local.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_playback_mode = "file"
    app.radio_local_media_path = str(audio_path)

    play_calls = []
    original_play = radio_controller._play_local_audio_file
    try:
        radio_controller._play_local_audio_file = (
            lambda current_app, path, **kwargs: play_calls.append(
                (current_app, path, kwargs)
            )
            or True
        )
        assert radio_controller.play_current_radio_source(app) is True
    finally:
        radio_controller._play_local_audio_file = original_play

    assert play_calls == [
        (
            app,
            str(audio_path),
            {
                "station_name": "Lokale Datei",
                "title_text": "Datei: local.mp3",
            },
        )
    ]


def test_play_next_station_cycles_playlist_mode(tmp_path):
    first = tmp_path / "one.mp3"
    second = tmp_path / "two.mp3"
    first.write_text("one", encoding="utf-8")
    second.write_text("two", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_playback_mode = "playlist"
    app.radio_playlist_entries = [str(first), str(second)]
    app.radio_playlist_index = 0
    app.radio_local_media_path = str(first)
    app.radio_playlist_listbox = DummyListbox(selection=(0,))

    calls = []
    original_play = radio_controller.play_selected_radio_playlist_entry
    try:
        radio_controller.play_selected_radio_playlist_entry = (
            lambda current_app, _event=None: calls.append(
                (
                    current_app.radio_playlist_index,
                    current_app.radio_playlist_listbox.curselection(),
                )
            )
            or True
        )
        assert radio_controller.play_next_station(app) is True
    finally:
        radio_controller.play_selected_radio_playlist_entry = original_play

    assert calls == [(0, (1,))]


def test_save_radio_playlist_to_file_writes_m3u_and_updates_settings(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_playlist_entries = [str(tmp_path / "one.mp3"), str(tmp_path / "two.mp3")]
    app.radio_playlist_path = ""
    app.radio_playlists_dir = str(tmp_path)
    app.radio_record_status_var = DummyVar("")
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_host_app = None

    playlist_path = tmp_path / "custom-playlist.m3u"
    original_dialog = radio_controller.filedialog.asksaveasfilename
    original_save = radio_controller.save_radio_settings
    try:
        radio_controller.filedialog.asksaveasfilename = lambda **_kwargs: str(
            playlist_path
        )
        radio_controller.save_radio_settings = lambda current_app: (
            current_app.radio_settings.update(
                {
                    "playlist_entries": list(current_app.radio_playlist_entries),
                    "playlist_path": current_app.radio_playlist_path,
                    "playlists_dir": current_app.radio_playlists_dir,
                }
            )
            or True
        )
        assert radio_controller.save_radio_playlist_to_file(app) is True
    finally:
        radio_controller.filedialog.asksaveasfilename = original_dialog
        radio_controller.save_radio_settings = original_save

    assert playlist_path.read_text(encoding="utf-8") == (
        "#EXTM3U\n" f"{tmp_path / 'one.mp3'}\n" f"{tmp_path / 'two.mp3'}\n"
    )
    assert app.radio_playlist_path == str(playlist_path)
    assert app.radio_settings["playlist_path"] == str(playlist_path)
    assert app.radio_settings["playlists_dir"] == str(tmp_path)
    assert (
        app.radio_record_status_var.get() == "Playlist gespeichert: custom-playlist.m3u"
    )


def test_load_radio_playlist_from_file_reads_entries_and_persists(tmp_path):
    playlist_path = tmp_path / "loaded-playlist.m3u"
    playlist_path.write_text(
        "#EXTM3U\n"
        f"{tmp_path / 'a.mp3'}\n"
        "\n"
        "#EXTINF:-1,Station B\n"
        f"{tmp_path / 'b.mp3'}\n",
        encoding="utf-8",
    )

    app = type("DummyApp", (), {})()
    app.radio_playlist_entries = []
    app.radio_playlist_path = ""
    app.radio_playlists_dir = str(tmp_path)
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_listbox = DummyListbox()
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_playlist_save_button = DummyWidget()
    app.radio_playlist_load_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_host_app = None

    original_dialog = radio_controller.filedialog.askopenfilename
    original_save = radio_controller.save_radio_settings
    try:
        radio_controller.filedialog.askopenfilename = lambda **_kwargs: str(
            playlist_path
        )
        radio_controller.save_radio_settings = lambda current_app: (
            current_app.radio_settings.update(
                {
                    "playlist_entries": list(current_app.radio_playlist_entries),
                    "playlist_path": current_app.radio_playlist_path,
                    "playlists_dir": current_app.radio_playlists_dir,
                }
            )
            or True
        )
        assert radio_controller.load_radio_playlist_from_file(app) is True
    finally:
        radio_controller.filedialog.askopenfilename = original_dialog
        radio_controller.save_radio_settings = original_save

    assert app.radio_playlist_entries == [
        str(tmp_path / "a.mp3"),
        str(tmp_path / "b.mp3"),
    ]
    assert app.radio_playlist_path == str(playlist_path)
    assert app.radio_playlists_dir == str(tmp_path)
    assert app.radio_playlist_status_var.get() == "Playlist: 2 Dateien"
    assert app.radio_record_status_var.get() == "Playlist geladen: loaded-playlist.m3u"


def test_open_radio_playlists_dir_creates_folder_and_updates_defaults(tmp_path):
    app = type("DummyApp", (), {})()
    app.radio_playlists_dir = str(tmp_path / "playlists")
    app.radio_playlist_path = ""
    app.radio_playlist_files_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_record_status_var = DummyVar("")
    app.radio_settings = radio_controller.default_radio_settings()
    app.log = lambda _message: None

    original_has_cmd = radio_controller.has_cmd
    original_save = radio_controller.save_radio_settings
    try:
        radio_controller.has_cmd = lambda _cmd: False
        radio_controller.save_radio_settings = lambda current_app: True
        assert radio_controller.open_radio_playlists_dir(app) is True
    finally:
        radio_controller.has_cmd = original_has_cmd
        radio_controller.save_radio_settings = original_save

    assert os.path.isdir(app.radio_playlists_dir)
    assert app.radio_playlist_path == os.path.join(
        app.radio_playlists_dir, "radio_playlist.m3u"
    )
    assert app.radio_settings["playlists_dir"] == app.radio_playlists_dir
    assert app.radio_settings["playlist_path"] == app.radio_playlist_path
    assert app.radio_folder_browser_mode == "playlists"
    assert app.radio_playlist_files_entries == []
    assert app.radio_folder_browser_title_var.get() == "Playlistordner"
    assert app.radio_recordings_status_var.get() == "Playlistordner: 0 Dateien"
    assert app.radio_record_status_var.get() == "Playlistordner geladen: playlists"


def test_open_radio_recordings_dir_populates_embedded_browser(tmp_path):
    record_dir = tmp_path / "records"
    record_dir.mkdir()
    (record_dir / "a.mp3").write_text("a", encoding="utf-8")
    (record_dir / "b.mp3").write_text("b", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    original_has_cmd = radio_controller.has_cmd
    radio_controller.has_cmd = lambda _cmd: True
    try:
        assert radio_controller.open_radio_recordings_dir(app) is True
    finally:
        radio_controller.has_cmd = original_has_cmd

    assert app.radio_recordings_entries == [
        str(record_dir / "a.mp3"),
        str(record_dir / "b.mp3"),
    ]
    assert app.radio_recordings_listbox.items == ["a.mp3", "b.mp3"]
    assert app.radio_folder_browser_mode == "recordings"
    assert app.radio_folder_browser_title_var.get() == "Aufnahmeordner"
    assert app.radio_folder_browser_path_var.get() == str(record_dir)
    assert app.radio_folder_browser_open_path_button.calls[-1]["state"] == "normal"
    assert app.radio_recordings_status_var.get() == "Aufnahmeordner: 2 Dateien"


def test_open_radio_system_dir_populates_browser_with_system_title(tmp_path):
    system_dir = tmp_path / "eigener ordner"
    system_dir.mkdir()
    (system_dir / "one.mp3").write_text("1", encoding="utf-8")
    (system_dir / "two.ogg").write_text("2", encoding="utf-8")
    (system_dir / "ignore.txt").write_text("x", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_system_folder_entries = []
    app.radio_system_folder_path = ""
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    original_dialog = radio_controller.filedialog.askdirectory
    try:
        radio_controller.filedialog.askdirectory = lambda **_kwargs: str(system_dir)
        assert radio_controller.open_radio_system_dir(app) is True
    finally:
        radio_controller.filedialog.askdirectory = original_dialog

    assert app.radio_folder_browser_mode == "system"
    assert app.radio_system_folder_path == str(system_dir)
    assert app.radio_system_folder_entries == [
        str(system_dir / "one.mp3"),
        str(system_dir / "two.ogg"),
    ]
    assert app.radio_folder_browser_title_var.get() == "System - eigener ordner"
    assert app.radio_recordings_status_var.get() == "Systemordner: 2 Dateien"
    assert app.radio_record_status_var.get() == "Systemordner geladen: eigener ordner"


def test_play_selected_radio_recording_file_uses_local_playback(tmp_path):
    audio_path = tmp_path / "rec.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_entries = [str(audio_path)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    calls = []
    original_play = radio_controller._play_local_audio_file
    try:
        radio_controller._play_local_audio_file = (
            lambda current_app, path, **kwargs: calls.append(
                (current_app, path, kwargs)
            )
            or True
        )
        assert radio_controller.play_selected_radio_recording_file(app) is True
    finally:
        radio_controller._play_local_audio_file = original_play

    assert calls == [
        (
            app,
            str(audio_path),
            {
                "station_name": "Aufnahmeordner",
                "title_text": "Datei: rec.mp3",
            },
        )
    ]


def test_add_selected_radio_folder_browser_entry_to_playlist_appends_recording(
    tmp_path,
):
    audio_path = tmp_path / "rec.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_context_index = 0
    app.radio_recordings_entries = [str(audio_path)]
    app.radio_playlist_entries = []
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_listbox = DummyListbox()
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_playlist_save_button = DummyWidget()
    app.radio_playlist_load_button = DummyWidget()
    app.radio_playlist_folder_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_host_app = None

    original_save = radio_controller.save_radio_settings
    try:
        radio_controller.save_radio_settings = lambda current_app: True
        assert (
            radio_controller.add_selected_radio_folder_browser_entry_to_playlist(app)
            is True
        )
    finally:
        radio_controller.save_radio_settings = original_save

    assert app.radio_playlist_entries == [str(audio_path)]
    assert app.radio_folder_browser_context_index == -1
    assert app.radio_playlist_status_var.get() == "Playlist: 1 Datei"
    assert app.radio_playlist_listbox.items == ["rec.mp3"]
    assert app.radio_record_status_var.get() == "Zur Playlist hinzugefügt: rec.mp3"


def test_open_selected_radio_folder_browser_entry_loads_and_starts_playlist(tmp_path):
    playlist_path = tmp_path / "demo.m3u"
    playlist_path.write_text(
        "#EXTM3U\n" f"{tmp_path / 'one.mp3'}\n" f"{tmp_path / 'two.mp3'}\n",
        encoding="utf-8",
    )

    app = type("DummyApp", (), {})()
    app.radio_folder_browser_mode = "playlists"
    app.radio_playlist_files_entries = [str(playlist_path)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_playlist_entries = []
    app.radio_playlist_path = ""
    app.radio_playlists_dir = ""
    app.radio_playlist_status_var = DummyVar("")
    app.radio_playlist_listbox = DummyListbox()
    app.radio_playlist_add_button = DummyWidget()
    app.radio_playlist_play_file_button = DummyWidget()
    app.radio_playlist_play_selected_button = DummyWidget()
    app.radio_playlist_remove_button = DummyWidget()
    app.radio_playlist_clear_button = DummyWidget()
    app.radio_playlist_save_button = DummyWidget()
    app.radio_playlist_load_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_settings = radio_controller.default_radio_settings()
    app.radio_host_app = None

    original_save = radio_controller.save_radio_settings
    original_play = radio_controller.play_selected_radio_playlist_entry
    try:
        radio_controller.save_radio_settings = lambda current_app: True
        radio_controller.play_selected_radio_playlist_entry = (
            lambda current_app, _event=None: (
                setattr(current_app, "_playlist_started", True) or True
            )
        )
        assert radio_controller.open_selected_radio_folder_browser_entry(app) is True
    finally:
        radio_controller.save_radio_settings = original_save
        radio_controller.play_selected_radio_playlist_entry = original_play

    assert app.radio_playlist_entries == [
        str(tmp_path / "one.mp3"),
        str(tmp_path / "two.mp3"),
    ]
    assert app.radio_playlist_path == str(playlist_path)
    assert app.radio_playlist_index == 0
    assert app.radio_playback_mode == "playlist"
    assert app.radio_local_media_path == str(tmp_path / "one.mp3")
    assert app.radio_playlist_listbox.curselection() == (0,)
    assert getattr(app, "_playlist_started", False) is True
    assert app.radio_record_status_var.get() == "Playlist geladen: demo.m3u"


def test_open_radio_recordings_dir_lists_subfolders_and_files(tmp_path):
    record_dir = tmp_path / "records"
    child_dir = record_dir / "clips"
    child_dir.mkdir(parents=True)
    audio_path = record_dir / "demo.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.open_radio_recordings_dir(app) is True

    assert app.radio_recordings_entries == [str(child_dir), str(audio_path)]
    assert app.radio_recordings_listbox.items == ["[Ordner] clips", "demo.mp3"]


def test_create_radio_folder_browser_subfolder_creates_directory(tmp_path):
    record_dir = tmp_path / "records"
    record_dir.mkdir()

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None
    app.winfo_toplevel = lambda: None

    original_askstring = radio_controller.simpledialog.askstring
    try:
        radio_controller.simpledialog.askstring = lambda *args, **kwargs: "neu"
        assert radio_controller.create_radio_folder_browser_subfolder(app) is True
    finally:
        radio_controller.simpledialog.askstring = original_askstring

    assert (record_dir / "neu").is_dir()
    assert app.radio_recordings_entries == [str(record_dir / "neu")]
    assert app.radio_record_status_var.get() == "Ordner erstellt: neu"


def test_delete_selected_radio_folder_browser_entry_removes_file(tmp_path):
    record_dir = tmp_path / "records"
    record_dir.mkdir()
    audio_path = record_dir / "demo.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_context_index = 0
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = [str(audio_path)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_last_record_path = str(audio_path)
    app.radio_record_proc = None
    app.radio_record_start_button = DummyWidget()
    app.radio_record_stop_button = DummyWidget()
    app.radio_record_transport_button = DummyWidget()
    app.radio_record_panel_button = DummyWidget()
    app.radio_record_choose_dir_button = DummyWidget()
    app.radio_record_open_dir_button = DummyWidget()
    app.radio_record_open_last_button = DummyWidget()
    app.radio_record_play_last_button = DummyWidget()
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_host_app = None
    app.winfo_toplevel = lambda: None

    original_askyesno = radio_controller.messagebox.askyesno
    try:
        radio_controller.messagebox.askyesno = lambda *args, **kwargs: True
        assert radio_controller.delete_selected_radio_folder_browser_entry(app) is True
    finally:
        radio_controller.messagebox.askyesno = original_askyesno

    assert not audio_path.exists()
    assert app.radio_recordings_entries == []
    assert app.radio_last_record_path == ""
    assert app.radio_record_status_var.get() == "Aufnahme gelöscht: demo.mp3"


def test_radio_folder_browser_back_and_forward_in_recordings(tmp_path):
    record_dir = tmp_path / "records"
    child_dir = record_dir / "clips"
    child_dir.mkdir(parents=True)
    (record_dir / "demo.mp3").write_text("demo", encoding="utf-8")
    (child_dir / "inside.mp3").write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_folder_browser_back_history = []
    app.radio_folder_browser_forward_history = []
    app.radio_recordings_entries = [str(child_dir), str(record_dir / "demo.mp3")]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.open_selected_radio_folder_browser_entry(app) is True
    assert app.radio_folder_browser_current_path == str(child_dir)

    assert radio_controller.navigate_radio_folder_browser_back(app) is True
    assert app.radio_folder_browser_current_path == str(record_dir)
    assert app.radio_recordings_entries == [
        str(child_dir),
        str(record_dir / "demo.mp3"),
    ]

    assert radio_controller.navigate_radio_folder_browser_forward(app) is True
    assert app.radio_folder_browser_current_path == str(child_dir)
    assert app.radio_recordings_entries == [str(child_dir / "inside.mp3")]


def test_radio_folder_browser_back_and_forward_across_modes(tmp_path):
    record_dir = tmp_path / "records"
    playlist_dir = tmp_path / "playlists"
    record_dir.mkdir()
    playlist_dir.mkdir()
    (record_dir / "demo.mp3").write_text("demo", encoding="utf-8")
    (playlist_dir / "mix.m3u").write_text("#EXTM3U\n", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_playlists_dir = str(playlist_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_folder_browser_back_history = []
    app.radio_folder_browser_forward_history = []
    app.radio_recordings_entries = []
    app.radio_playlist_files_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.open_radio_playlists_dir(app) is True
    assert app.radio_folder_browser_mode == "playlists"

    assert radio_controller.navigate_radio_folder_browser_back(app) is True
    assert app.radio_folder_browser_mode == "recordings"
    assert app.radio_folder_browser_current_path == str(record_dir)

    assert radio_controller.navigate_radio_folder_browser_forward(app) is True
    assert app.radio_folder_browser_mode == "playlists"
    assert app.radio_folder_browser_current_path == str(playlist_dir)


def test_navigate_radio_folder_browser_up_in_recordings(tmp_path):
    record_dir = tmp_path / "records"
    child_dir = record_dir / "clips"
    child_dir.mkdir(parents=True)
    (record_dir / "demo.mp3").write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(child_dir)
    app.radio_folder_browser_back_history = []
    app.radio_folder_browser_forward_history = []
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_up_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.navigate_radio_folder_browser_up(app) is True
    assert app.radio_folder_browser_current_path == str(record_dir)
    assert app.radio_recordings_entries == [
        str(child_dir),
        str(record_dir / "demo.mp3"),
    ]


def test_navigate_radio_folder_browser_up_stops_at_recordings_root(tmp_path):
    record_dir = tmp_path / "records"
    record_dir.mkdir()

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_up_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.navigate_radio_folder_browser_up(app) is False
    assert app.radio_folder_browser_current_path == str(record_dir)
    assert app.radio_record_status_var.get() == "Kein übergeordneter Ordner vorhanden."


def test_recordings_browser_path_is_clamped_to_configured_root(tmp_path):
    record_dir = tmp_path / "records"
    outside_dir = tmp_path / "outside"
    record_dir.mkdir()
    outside_dir.mkdir()
    (record_dir / "demo.mp3").write_text("demo", encoding="utf-8")
    (outside_dir / "other.mp3").write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(outside_dir)
    app.radio_recordings_entries = []
    app.radio_recordings_listbox = DummyListbox()
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_up_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    assert radio_controller.open_radio_recordings_dir(app) is True
    assert app.radio_folder_browser_current_path == str(record_dir)
    assert app.radio_recordings_entries == [str(record_dir / "demo.mp3")]


def test_rename_selected_radio_folder_browser_entry_renames_file(tmp_path):
    record_dir = tmp_path / "records"
    record_dir.mkdir()
    audio_path = record_dir / "demo.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_context_index = 0
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = [str(audio_path)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_last_record_path = str(audio_path)
    app.radio_record_proc = None
    app.radio_record_start_button = DummyWidget()
    app.radio_record_stop_button = DummyWidget()
    app.radio_record_transport_button = DummyWidget()
    app.radio_record_panel_button = DummyWidget()
    app.radio_record_choose_dir_button = DummyWidget()
    app.radio_record_open_dir_button = DummyWidget()
    app.radio_record_open_last_button = DummyWidget()
    app.radio_record_play_last_button = DummyWidget()
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_host_app = None
    app.winfo_toplevel = lambda: None

    original_askstring = radio_controller.simpledialog.askstring
    try:
        radio_controller.simpledialog.askstring = lambda *args, **kwargs: "neu.mp3"
        assert radio_controller.rename_selected_radio_folder_browser_entry(app) is True
    finally:
        radio_controller.simpledialog.askstring = original_askstring

    renamed_path = record_dir / "neu.mp3"
    assert renamed_path.exists()
    assert app.radio_recordings_entries == [str(renamed_path)]
    assert app.radio_last_record_path == str(renamed_path)
    assert app.radio_record_status_var.get() == "Umbenannt: demo.mp3 -> neu.mp3"


def test_rename_selected_radio_folder_browser_entry_renames_directory(tmp_path):
    record_dir = tmp_path / "records"
    child_dir = record_dir / "clips"
    child_dir.mkdir(parents=True)

    app = type("DummyApp", (), {})()
    app.radio_recordings_dir = str(record_dir)
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_context_index = 0
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = [str(child_dir)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_last_record_path = ""
    app.radio_record_proc = None
    app.radio_record_start_button = DummyWidget()
    app.radio_record_stop_button = DummyWidget()
    app.radio_record_transport_button = DummyWidget()
    app.radio_record_panel_button = DummyWidget()
    app.radio_record_choose_dir_button = DummyWidget()
    app.radio_record_open_dir_button = DummyWidget()
    app.radio_record_open_last_button = DummyWidget()
    app.radio_record_play_last_button = DummyWidget()
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_host_app = None
    app.winfo_toplevel = lambda: None

    original_askstring = radio_controller.simpledialog.askstring
    try:
        radio_controller.simpledialog.askstring = lambda *args, **kwargs: "neuordner"
        assert radio_controller.rename_selected_radio_folder_browser_entry(app) is True
    finally:
        radio_controller.simpledialog.askstring = original_askstring

    renamed_dir = record_dir / "neuordner"
    assert renamed_dir.is_dir()
    assert app.radio_recordings_entries == [str(renamed_dir)]
    assert app.radio_record_status_var.get() == "Umbenannt: clips -> neuordner"


def test_drag_and_drop_moves_recording_file_into_folder(tmp_path):
    record_dir = tmp_path / "records"
    target_dir = record_dir / "clips"
    target_dir.mkdir(parents=True)
    audio_path = record_dir / "demo.mp3"
    audio_path.write_text("demo", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = [str(audio_path), str(target_dir)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_up_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_last_record_path = str(audio_path)
    app.radio_record_proc = None
    app.radio_record_start_button = DummyWidget()
    app.radio_record_stop_button = DummyWidget()
    app.radio_record_transport_button = DummyWidget()
    app.radio_record_panel_button = DummyWidget()
    app.radio_record_choose_dir_button = DummyWidget()
    app.radio_record_open_dir_button = DummyWidget()
    app.radio_record_open_last_button = DummyWidget()
    app.radio_record_play_last_button = DummyWidget()
    app.radio_record_dir_var = DummyVar("")
    app.radio_record_file_var = DummyVar("")
    app.radio_host_app = None

    radio_controller.start_radio_folder_browser_drag(app, DummyEvent(y=0))
    result = radio_controller.finish_radio_folder_browser_drag(app, DummyEvent(y=1))

    moved_path = target_dir / "demo.mp3"
    assert result == "break"
    assert moved_path.exists()
    assert not audio_path.exists()
    assert app.radio_last_record_path == str(moved_path)
    assert app.radio_record_status_var.get() == "Verschoben: demo.mp3 -> clips"


def test_drag_and_drop_does_not_overwrite_existing_target(tmp_path):
    record_dir = tmp_path / "records"
    target_dir = record_dir / "clips"
    target_dir.mkdir(parents=True)
    audio_path = record_dir / "demo.mp3"
    audio_path.write_text("demo", encoding="utf-8")
    (target_dir / "demo.mp3").write_text("existing", encoding="utf-8")

    app = type("DummyApp", (), {})()
    app.radio_folder_browser_mode = "recordings"
    app.radio_folder_browser_current_path = str(record_dir)
    app.radio_recordings_entries = [str(audio_path), str(target_dir)]
    app.radio_recordings_listbox = DummyListbox(selection=(0,))
    app.radio_recordings_status_var = DummyVar("")
    app.radio_folder_browser_title_var = DummyVar("")
    app.radio_folder_browser_path_var = DummyVar("")
    app.radio_folder_browser_back_button = DummyWidget()
    app.radio_folder_browser_forward_button = DummyWidget()
    app.radio_folder_browser_up_button = DummyWidget()
    app.radio_folder_browser_open_path_button = DummyWidget()
    app.radio_record_status_var = DummyVar("")
    app.radio_host_app = None

    radio_controller.start_radio_folder_browser_drag(app, DummyEvent(y=0))
    result = radio_controller.finish_radio_folder_browser_drag(app, DummyEvent(y=1))

    assert result is None
    assert audio_path.exists()
    assert app.radio_record_status_var.get() == "Zieldatei existiert bereits."
