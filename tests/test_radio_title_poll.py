"""T-2: protected pipe playback asks mpv only for in-band metadata, then ICY."""

from types import SimpleNamespace

import pytest

from netmon.features import radio_controller as radio


def pipe_app():
    return SimpleNamespace(
        radio_current_station={"url": "https://example.invalid/stream"},
        radio_proc=SimpleNamespace(_source_process=object()),
    )


def local_app():
    return SimpleNamespace(
        radio_current_station={"url": "file:///music/a.ogg"},
        radio_proc=SimpleNamespace(_source_process=None),
    )


def test_pipe_source_queries_only_metadata_then_icy(monkeypatch):
    asked = []
    monkeypatch.setattr(
        radio, "_query_mpv_property", lambda _app, name: asked.append(name) or {}
    )
    monkeypatch.setattr(radio, "_fetch_icy_stream_title", lambda _url: "Live title")
    title, payload = radio._read_radio_stream_title(pipe_app())
    assert title == "Live title"
    assert asked == ["metadata"]
    assert payload["mpv-properties"] == "skipped-pipe" and "icy-fetch" in payload


def test_pipe_source_keeps_in_band_container_title(monkeypatch):
    monkeypatch.setattr(
        radio,
        "_query_mpv_property",
        lambda _app, name: {"title": "Ogg title"} if name == "metadata" else None,
    )
    monkeypatch.setattr(
        radio, "_fetch_icy_stream_title", lambda _url: pytest.fail("ICY not needed")
    )
    assert radio._read_radio_stream_title(pipe_app())[0] == "Ogg title"


def test_pipe_source_without_any_title_returns_empty(monkeypatch):
    monkeypatch.setattr(radio, "_query_mpv_property", lambda _app, name: {})
    monkeypatch.setattr(radio, "_fetch_icy_stream_title", lambda _url: "")
    title, payload = radio._read_radio_stream_title(pipe_app())
    assert title == "" and payload["icy-fetch"] == ""


def test_local_file_still_uses_all_mpv_properties(monkeypatch):
    asked = []

    def query(_app, name):
        asked.append(name)
        return "Local Artist - Track" if name == "media-title" else {}

    monkeypatch.setattr(radio, "_query_mpv_property", query)
    monkeypatch.setattr(
        radio, "_fetch_icy_stream_title", lambda _url: pytest.fail("ICY for local")
    )
    assert radio._read_radio_stream_title(local_app())[0] == "Local Artist - Track"
    assert asked == ["metadata", "filtered-metadata", "media-title"]


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        self.slept += seconds


@pytest.mark.parametrize(
    "make_app,interval",
    [(pipe_app, radio.TITLE_POLL_PIPE_SECONDS), (local_app, radio.TITLE_POLL_SECONDS)],
)
def test_poll_interval_depends_on_source(monkeypatch, make_app, interval):
    app = make_app()
    proc = app.radio_proc
    clock = FakeClock()
    rounds = []

    def read(_app):
        rounds.append(clock.now)
        if len(rounds) == 3:
            app.radio_proc = None
        return "", {}

    monkeypatch.setattr(
        radio, "time", SimpleNamespace(monotonic=clock.monotonic, sleep=clock.sleep)
    )
    monkeypatch.setattr(radio, "_read_radio_stream_title", read)
    monkeypatch.setattr(radio, "_radio_debug_log", lambda *_: None)
    radio._poll_radio_metadata(app, proc)
    assert rounds == pytest.approx([0.0, interval, 2 * interval])
    assert radio.TITLE_POLL_PIPE_SECONDS == 15.0 and radio.TITLE_POLL_SECONDS == 5.0


def test_stopped_player_ends_long_pipe_wait_promptly(monkeypatch):
    app = pipe_app()
    proc = app.radio_proc
    clock = FakeClock()

    def sleep(seconds):
        clock.sleep(seconds)
        if clock.now >= 1.0:
            app.radio_proc = None  # radio stopped during the 15 s wait

    monkeypatch.setattr(
        radio, "time", SimpleNamespace(monotonic=clock.monotonic, sleep=sleep)
    )
    monkeypatch.setattr(radio, "_read_radio_stream_title", lambda _app: ("", {}))
    monkeypatch.setattr(radio, "_radio_debug_log", lambda *_: None)
    radio._poll_radio_metadata(app, proc)
    assert clock.now <= 1.0 + 1e-9
