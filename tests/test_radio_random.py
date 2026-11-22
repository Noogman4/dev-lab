"""Virtual time and real settings round-trips, without audio or network access."""

from datetime import datetime, timezone
import json
import random
from types import SimpleNamespace

import pytest

from netmon.core import radio_random as random_radio
from netmon.features import radio_controller as radio


class Timer:
    def __init__(self):
        self.now = 0
        self.serial = 0
        self.pending = {}

    def after(self, delay, callback):
        self.serial += 1
        self.pending[self.serial] = (self.now + delay / 1000, callback)
        return self.serial

    def cancel(self, key):
        self.pending.pop(key, None)

    def advance(self, seconds):
        target = self.now + seconds
        while self.pending:
            key = min(self.pending, key=lambda key: self.pending[key][0])
            stamp, callback = self.pending[key]
            if stamp > target:
                break
            self.pending.pop(key)
            self.now = stamp
            callback()
        self.now = target


@pytest.fixture
def rotation():
    timer, played, saved = Timer(), [], []
    stations = [
        {"id": str(i), "name": f"Sender {i}", "url": f"https://example.invalid/{i}"}
        for i in range(4)
    ]
    mode = random_radio.RandomRadio(
        {},
        stations=lambda: stations,
        normalize=radio.normalize_station_entry,
        play=lambda key, token: played.append((key, token)) or True,
        schedule=timer.after,
        cancel=timer.cancel,
        save=lambda payload: saved.append(payload) or True,
        rng=random.Random(5),
        clock=lambda: timer.now,
        now=lambda: datetime(2026, 11, 15, tzinfo=timezone.utc),
    )
    return mode, timer, played, saved, stations


def test_full_database_rounds_do_not_repeat_and_timer_starts_after_player(rotation):
    mode, timer, played, saved, _ = rotation
    assert mode.start()
    timer.advance(20)
    assert len(played) == 1  # Connecting time is not part of the interval.
    for i in range(12):
        mode.started(played[-1][1])
        timer.advance(299)
        assert len(played) == i + 1
        timer.advance(1)
        assert len(played) == i + 2
    ids = [key for key, _ in played]
    for offset in (0, 4, 8):
        assert len(set(ids[offset : offset + 4])) == 4
    assert all(left != right for left, right in zip(ids, ids[1:]))
    assert saved[-1]["random_history"][-2]["status"] == "switched"
    assert len(timer.pending) == 1


def test_stop_and_restart_invalidate_queued_timers_and_old_player_callbacks(rotation):
    mode, timer, played, _, _ = rotation
    mode.start()
    old_token = played[-1][1]
    old_callback = next(iter(timer.pending.values()))[1]
    mode.stop()
    mode.start()
    new_token = played[-1][1]
    old_callback()
    mode.started(old_token)
    mode.failed(old_token)
    assert mode.owns(new_token)
    assert len(played) == 2 and len(timer.pending) == 1
    mode.stop()
    mode.started(new_token)
    timer.advance(9999)
    assert not mode.active and len(played) == 2 and not timer.pending


def test_interval_change_uses_elapsed_time_and_is_persisted(rotation):
    mode, timer, played, saved, _ = rotation
    mode.start()
    mode.started(played[-1][1])
    timer.advance(90)
    assert mode.set_minutes("2")
    timer.advance(29)
    assert len(played) == 1
    timer.advance(1)
    assert len(played) == 2
    assert saved[-1]["random_interval_minutes"] == 2
    assert len(timer.pending) == 1


@pytest.mark.parametrize(
    "value", [0, -1, 1441, True, None, "nan", "0.1", "1e2", "", []]
)
def test_invalid_intervals_never_change_timer(rotation, value):
    mode, timer, _, saved, _ = rotation
    with pytest.raises(ValueError):
        mode.set_minutes(value)
    assert mode.minutes == 5 and not timer.pending and not saved


def test_unavailable_streams_retry_but_stop_after_three_failures(rotation):
    mode, timer, played, _, _ = rotation
    mode.start()
    for attempt in range(3):
        mode.started(played[-1][1])
        mode.failed(played[-1][1])
        assert mode.history[-1]["status"] == "failed"
        timer.advance(5)
        assert len(played) == min(attempt + 2, 3)
    assert not mode.active and mode.reason == "start_failed" and not timer.pending


def test_stalled_connection_is_bounded_and_late_start_cannot_reset_retry(rotation):
    mode, timer, played, _, _ = rotation
    mode.start()
    token = played[-1][1]
    timer.advance(30)
    assert mode.reason == "retrying"
    mode.started(token)
    timer.advance(5)
    assert len(played) == 2
    assert mode.history[0]["status"] == "failed"


@pytest.mark.parametrize("kind", ["missing_output", "write_failed", "no_database"])
def test_terminal_conditions_never_spin(rotation, kind):
    mode, timer, played, _, stations = rotation
    if kind == "write_failed":
        mode.save = lambda payload: False
    elif kind == "missing_output":
        mode.play = lambda key, token: False
    else:
        stations.clear()
    assert not mode.start()
    timer.advance(10000)
    assert not mode.active and not timer.pending and not played


def test_database_edits_singleton_and_invalid_entries(rotation):
    mode, timer, played, _, stations = rotation
    stations[:] = [None, {}, {"id": "bad", "name": "Bad", "url": "file:///etc/passwd"}]
    assert not mode.start()
    stations.append(
        {"id": "only", "name": "Only station", "url": "https://example.invalid/"}
    )
    assert mode.start()
    mode.started(played[-1][1])
    timer.advance(300)
    assert [key for key, _ in played] == ["only", "only"]
    stations.clear()
    mode.started(played[-1][1])
    timer.advance(300)
    assert not mode.active and not timer.pending


def test_output_loss_stops_random_without_retry(rotation):
    mode, timer, played, _, _ = rotation
    mode.start()
    mode.started(played[-1][1])
    mode.failed(played[-1][1], terminal=True)
    timer.advance(10000)
    assert not mode.active and len(played) == 1


def test_history_is_bounded_and_corrupt_entries_are_discarded(rotation):
    mode, _, played, saved, _ = rotation
    mode.save = lambda payload: saved.__setitem__(slice(None), [payload]) or True
    for _ in range(510):
        mode.start()
        mode.started(played[-1][1])
        mode.stop()
    assert len(mode.history) == len(saved[-1]["random_history"]) == 500
    malformed = [None, {}, {"status": []}, {"status": "started", "selected_at": "bad"}]
    settings = random_radio.saved_settings(
        {"random_interval_minutes": [], "random_history": malformed}
    )
    assert settings == {
        "random_interval_minutes": 5,
        "random_history": [],
        "random_filter": {
            "categories": [],
            "minimum_bitrate": 0,
            "include_unknown": False,
        },
    }
    restored = random_radio.saved_settings(saved[-1])
    assert restored == saved[-1]


def test_settings_survive_restart_and_mode_does_not_autostart(tmp_path):
    timer = Timer()
    app = SimpleNamespace(
        radio_settings_path=str(tmp_path / "radio_settings.json"),
        radio_settings=radio.default_radio_settings(),
        radio_db=[
            {"id": "db", "name": "DB station", "url": "https://example.invalid/live"}
        ],
        after=timer.after,
        after_cancel=timer.cancel,
    )
    mode = radio.radio_random_mode(app)
    mode.play = lambda key, token: True
    assert mode.set_minutes(7) and mode.start()
    mode.started(1)
    mode.stop()
    saved = json.loads((tmp_path / "radio_settings.json").read_text())
    assert saved["random_interval_minutes"] == 7
    assert saved["random_history"][0]["name"] == "DB station"
    app.radio_settings = saved
    del app._radio_random_mode
    restarted = radio.radio_random_mode(app)
    assert restarted.minutes == 7 and restarted.history == mode.history
    assert not restarted.active and not timer.pending
    assert restarted.clear_history()
    assert (
        json.loads((tmp_path / "radio_settings.json").read_text())["random_history"]
        == []
    )
    assert radio.radio_random_mode(app).history == []


def test_random_filter_is_saved_and_only_matching_stations_play(rotation):
    mode, timer, played, saved, stations = rotation
    stations[0].update(tags=["rock"], bitrate=192)
    stations[1].update(tags=["electronic"], bitrate=256)
    stations[2].update(tags=["rock"], bitrate=64)
    stations[3].update(tags=["jazz"], bitrate=256)
    criteria = {"categories": ["rock", "electronic"], "minimum_bitrate": 128}
    assert mode.set_filter(criteria)
    assert mode.start()
    for _ in range(5):
        mode.started(played[-1][1])
        timer.advance(300)
    assert {key for key, _ in played} == {"0", "1"}
    mode.stop()
    assert mode.clear_history()
    assert saved[-1]["random_filter"] == mode.filters
    restarted = random_radio.RandomRadio(
        saved[-1],
        stations=lambda: stations,
        normalize=radio.normalize_station_entry,
        play=lambda key, token: True,
        schedule=timer.after,
        cancel=timer.cancel,
        save=lambda settings: True,
    )
    assert restarted.filters == mode.filters and not restarted.active


def test_changing_filter_preserves_timer_and_applies_to_next_switch(rotation):
    mode, timer, played, _, stations = rotation
    for row in stations:
        row.update(tags=["rock"], bitrate=192)
    mode.start()
    mode.started(played[-1][1])
    timer.advance(100)
    current = played[-1][0]
    wanted = next(row for row in stations if row["id"] != current)
    wanted["tags"] = ["jazz"]
    pending = dict(timer.pending)
    assert mode.set_filter({"categories": ["jazz"]})
    assert timer.pending == pending and mode.active and len(played) == 1
    timer.advance(200)
    assert played[-1][0] == wanted["id"]


def test_empty_filter_result_never_falls_back_and_save_failure_preserves_filter(
    rotation,
):
    mode, timer, played, _, _ = rotation
    assert mode.set_filter({"categories": ["rock"]})
    mode.save = lambda settings: False
    assert not mode.set_filter({"categories": ["jazz"]})
    assert mode.filters["categories"] == ["rock"]
    assert not mode.start()
    assert mode.reason == "no_matches" and not played and not timer.pending


@pytest.mark.parametrize("stage", ["selected", "started", "retrying"])
def test_clear_history_preserves_live_timer_and_old_callbacks_do_not_restore_rows(
    rotation, stage
):
    mode, timer, played, saved, _ = rotation
    mode.start()
    token = played[-1][1]
    if stage != "selected":
        mode.started(token)
    if stage == "retrying":
        mode.failed(token)
    pending = dict(timer.pending)
    assert mode.clear_history()
    assert mode.active and mode.history == [] and timer.pending == pending
    assert saved[-1]["random_history"] == []
    if stage == "selected":
        mode.started(token)
        assert mode.history == [] and saved[-1]["random_history"] == []
    timer.advance(5 if stage == "retrying" else 300)
    assert len(mode.history) == 1 and len(played) == 2
    assert mode.history[0]["station_id"] == played[-1][0]


def test_clear_history_save_failure_preserves_history_playback_and_persisted_settings(
    tmp_path, monkeypatch
):
    timer = Timer()
    app = SimpleNamespace(
        radio_settings_path=str(tmp_path / "settings.json"),
        radio_settings=radio.default_radio_settings(),
        radio_db=[{"id": "one", "name": "One", "url": "https://example.invalid/live"}],
        after=timer.after,
        after_cancel=timer.cancel,
    )
    mode = radio.radio_random_mode(app)
    mode.play = lambda key, token: True
    mode.start()
    mode.started(1)
    old_history, pending = list(mode.history), dict(timer.pending)
    writer = radio.safe_write_json
    monkeypatch.setattr(
        radio, "safe_write_json", lambda *a, **kw: (False, "fixture failure")
    )
    assert not mode.clear_history()
    assert mode.history == old_history and mode.active and timer.pending == pending
    assert app.radio_settings["random_history"] == old_history
    monkeypatch.setattr(radio, "safe_write_json", writer)
    assert radio.save_radio_settings(app)
    assert (
        json.loads((tmp_path / "settings.json").read_text())["random_history"]
        == old_history
    )


@pytest.fixture
def protected_rotation(monkeypatch, tmp_path):
    timer, starts = Timer(), []
    app = SimpleNamespace(
        radio_settings=radio.default_radio_settings(),
        radio_settings_path=str(tmp_path / "settings.json"),
        radio_db=[
            {
                "id": "same",
                "name": "Database",
                "url": "https://example.invalid/database",
            }
        ],
        radio_favorites=[
            {
                "id": "same",
                "name": "Favorite",
                "url": "https://example.invalid/favorite",
            }
        ],
        after=timer.after,
        after_cancel=timer.cancel,
    )
    for name in (
        "update_radio_header",
        "refresh_radio_station_table",
        "refresh_radio_favorites_list",
        "refresh_radio_source_ui",
        "_set_radio_light",
        "_set_radio_station_text",
        "_set_radio_title_text",
        "set_radio_status",
        "_poll_radio_metadata",
    ):
        monkeypatch.setattr(radio, name, lambda *args, **kwargs: None)
    from netmon import netmon_projectm_sidecar

    monkeypatch.setattr(
        netmon_projectm_sidecar, "invalidate_projectm_playback", lambda *args: None
    )
    monkeypatch.setattr(radio, "radio_available", lambda app: True)
    monkeypatch.setattr(radio, "_schedule_ui", lambda app, callback: callback())

    class ImmediateThread:
        def __init__(self, target, args=(), **kwargs):
            self.target, self.args = target, args

        def start(self):
            self.target(*self.args)

    def start(app, volume, url):
        starts.append(url)
        return SimpleNamespace(ipc_path="", wait=lambda **kwargs: 1)

    def run(app, request, start, announce, failed, name):
        request.process = start()
        app.radio_proc = request.process
        announce(request.process)
        request.done.set()

    monkeypatch.setattr(radio.threading, "Thread", ImmediateThread)
    monkeypatch.setattr(radio, "_start_radio_playback", start)
    monkeypatch.setattr(radio, "_run_radio_playback_request", run)
    return app, timer, starts


def test_random_uses_existing_protected_start_and_database_over_same_id_favorite(
    protected_rotation,
):
    app, timer, starts = protected_rotation
    assert radio.toggle_radio_random(app)
    mode = radio.radio_random_mode(app)
    assert mode.active and starts == ["https://example.invalid/database"]
    assert mode.history[-1]["status"] == "started"
    assert len(timer.pending) == 1
    radio.stop_radio_playback(app)
    timer.advance(10000)
    assert not mode.active and not timer.pending
    assert starts == ["https://example.invalid/database"]


def test_manual_station_choice_cancels_automatic_switch(protected_rotation):
    app, timer, starts = protected_rotation
    radio.toggle_radio_random(app)
    assert radio.play_radio_station(app, "same")
    timer.advance(10000)
    assert starts == [
        "https://example.invalid/database",
        "https://example.invalid/favorite",
    ]
    assert not radio.radio_random_mode(app).active and not timer.pending


def test_connection_timeout_cancels_owned_request_before_trying_another(
    protected_rotation, monkeypatch
):
    app, timer, starts = protected_rotation
    requests = []

    def pending(app, request, *args):
        requests.append(request)
        request.done.set()

    monkeypatch.setattr(radio, "_run_radio_playback_request", pending)
    assert radio.toggle_radio_random(app)
    old = requests[-1]
    timer.advance(30)
    assert old.cancelled.is_set() and not radio._radio_request_current(app, old)
    mode = radio.radio_random_mode(app)
    assert mode.active and mode.reason == "retrying"
    timer.advance(5)
    assert len(requests) == 2
    assert radio._radio_request_current(app, requests[-1])
    # A stale random token must not stop a replacement player/request.
    assert not radio.stop_radio_playback(app, random_token=old.random_token)
    assert radio._radio_request_current(app, requests[-1])
    assert starts == []


@pytest.mark.parametrize("output_lost", [False, True])
def test_player_end_notifies_random_mode_and_lost_output_never_retries(
    protected_rotation, output_lost
):
    app, timer, starts = protected_rotation
    radio.toggle_radio_random(app)
    proc = app.radio_proc
    proc.output_lost = output_lost
    radio._wait_for_radio_process(app, proc, "Database", app.radio_playback_request)
    mode = radio.radio_random_mode(app)
    assert mode.history[-1]["status"] == "failed"
    if output_lost:
        assert not mode.active and not timer.pending
    else:
        assert mode.active and mode.reason == "retrying"
        timer.advance(5)
        assert len(starts) == 2


def test_recording_blocks_random_start_and_starting_recording_cancels_rotation(
    rotation, monkeypatch, tmp_path
):
    mode, timer, _, _, stations = rotation
    app = SimpleNamespace(_radio_random_mode=mode, radio_record_starting=True)
    assert not radio.toggle_radio_random(app)
    assert mode.reason == "recording" and not timer.pending
    app.radio_record_starting = False
    mode.start()
    monkeypatch.setattr(radio, "radio_recording_available", lambda app: True)
    monkeypatch.setattr(radio, "_resolve_target_station", lambda *a: stations[0])
    monkeypatch.setattr(
        radio, "_recording_file_path", lambda *a: str(tmp_path / "synthetic.mp3")
    )
    monkeypatch.setattr(radio, "_recording_status_text", lambda *a: None)
    monkeypatch.setattr(radio, "refresh_radio_recording_ui", lambda *a: None)
    monkeypatch.setattr(
        radio.threading, "Thread", lambda **kwargs: SimpleNamespace(start=lambda: None)
    )
    assert radio.start_radio_recording(app)
    assert not mode.active and not timer.pending and mode.reason == "recording"
