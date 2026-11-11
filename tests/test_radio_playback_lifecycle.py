"""Start/stop races from the independent review, using real controller code."""

from collections import deque
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from netmon.features import radio_controller as radio


class Player:
    def __init__(self, path):
        self.ipc_path = str(path)
        path.write_text("synthetic IPC marker")
        self.dead = threading.Event()
        self.rc = None

    def poll(self):
        return self.rc

    def wait(self, timeout=None):
        if not self.dead.wait(timeout):
            raise subprocess.TimeoutExpired("fixture-player", timeout)
        return self.rc

    def terminate(self):
        self.finish(-15)

    def finish(self, rc):
        self.rc = rc
        Path(self.ipc_path).unlink(missing_ok=True)
        self.dead.set()

    def kill(self):
        self.terminate()


def until(condition, pump=lambda: None):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        pump()
        if condition():
            return
        time.sleep(0.005)
    pytest.fail("controller did not reach the expected lifecycle state")


@pytest.fixture
def playback(monkeypatch, tmp_path):
    callbacks, created, statuses, metadata = deque(), [], [], []
    lights, titles = [], []
    entered, release = threading.Event(), threading.Event()
    app = SimpleNamespace(
        radio_proc=None,
        radio_ipc_path="",
        radio_current_station_id="",
        radio_volume_var=SimpleNamespace(get=lambda: 40),
        tr=lambda _key, default=None: default,
    )

    def start(*_a, **_k):
        proc = Player(tmp_path / f"player-{len(created)}.sock")
        created.append(proc)
        entered.set()
        assert release.wait(3), "test did not release startup"
        return proc

    def pump():
        while callbacks:
            callbacks.popleft()()

    def launch(local=False):
        if local:
            path = tmp_path / "selected.wav"
            path.write_bytes(b"fixture")
            return radio._play_local_audio_file(
                app, str(path), station_name="Local", title_text="Local title"
            )
        return radio.play_radio_station(app, "B")

    monkeypatch.setattr(radio, "_start_radio_playback", start)
    monkeypatch.setattr(radio, "radio_available", lambda _a: True)
    monkeypatch.setattr(
        radio,
        "_resolve_target_station",
        lambda *_a, **_k: {"id": "B", "name": "B", "url": "https://example.com/b"},
    )
    monkeypatch.setattr(
        radio, "_schedule_ui", lambda _, cb: callbacks.append(cb) or True
    )
    app.after = lambda _, cb: callbacks.append(cb)
    monkeypatch.setattr(
        radio, "set_radio_status", lambda _, text: statuses.append(text)
    )
    monkeypatch.setattr(radio, "_poll_radio_metadata", lambda _, p: metadata.append(p))
    for name in (
        "save_radio_settings",
        "update_radio_header",
        "refresh_radio_source_ui",
        "refresh_radio_station_table",
        "refresh_radio_favorites_list",
        "_set_radio_light",
        "_set_radio_station_text",
        "_set_radio_title_text",
    ):
        monkeypatch.setattr(radio, name, lambda *_a, **_k: None)
    monkeypatch.setattr(
        radio, "_set_radio_light", lambda _, value: lights.append(value)
    )
    monkeypatch.setattr(
        radio, "_set_radio_title_text", lambda _, value: titles.append(value)
    )
    state = SimpleNamespace(
        app=app,
        callbacks=callbacks,
        created=created,
        statuses=statuses,
        metadata=metadata,
        lights=lights,
        titles=titles,
        entered=entered,
        release=release,
        launch=launch,
        pump=pump,
    )
    yield state
    release.set()
    radio.stop_radio_playback(app)
    for proc in created:
        proc.terminate()
    request = vars(app).get("radio_playback_request")
    if request is not None:
        assert request.done.wait(3), "owner did not finish after fixture cleanup"


def _pending_handover(s):
    host = SimpleNamespace()
    s.app.radio_host_app = host
    for target in (s.app, host):
        target.radio_handover_title = "Titel: HANDOVER"
        target.radio_handover_station_id = "B"
    return host


def _finish_before_restart(s):
    radio.stop_radio_playback(s.app)
    assert s.app.radio_playback_request.done.wait(3)
    s.pump()


def test_handover_title_is_consumed_once_and_cleared_on_host(playback):
    s = playback
    host = _pending_handover(s)
    assert s.launch()
    s.release.set()
    until(lambda: s.app.radio_proc is not None, s.pump)
    assert s.titles[-1] == "Titel: HANDOVER"
    for target in (s.app, host):
        assert target.radio_handover_title == target.radio_handover_station_id == ""
    _finish_before_restart(s)
    assert s.launch()
    until(lambda: len(s.created) == 2 and s.app.radio_proc is s.created[-1], s.pump)
    assert s.titles[-1] == "Titel: -"


def test_handover_title_cannot_follow_changed_station_selection(playback, monkeypatch):
    s = playback
    _pending_handover(s)
    s.app.radio_current_station_id = "A"  # UI selection changed since handover B.
    monkeypatch.setattr(
        radio,
        "_resolve_target_station",
        lambda app, station_id: {
            "id": station_id,
            "name": station_id,
            "url": "https://example.invalid/" + station_id,
        },
    )
    assert radio.play_radio_station(s.app, "A")
    s.release.set()
    until(lambda: s.app.radio_proc is not None, s.pump)
    assert s.titles[-1] == "Titel: -"
    _finish_before_restart(s)
    assert s.launch()
    until(lambda: len(s.created) == 2 and s.app.radio_proc is s.created[-1], s.pump)
    assert s.titles[-1] == "Titel: -"


@pytest.mark.parametrize("intent", ["stop", "local", "cancel-start"])
def test_other_playback_intent_discards_pending_handover(playback, intent):
    s = playback
    host = _pending_handover(s)
    if intent == "stop":
        radio.stop_radio_playback(s.app)
        s.pump()
    else:
        assert s.launch(local=intent == "local")
        assert s.entered.wait(2)
        if intent == "cancel-start":
            radio.stop_radio_playback(s.app)
        s.release.set()
        if intent == "local":
            until(lambda: s.app.radio_proc is not None, s.pump)
        _finish_before_restart(s)
    for target in (s.app, host):
        assert target.radio_handover_title == target.radio_handover_station_id == ""
    s.release.set()
    count = len(s.created)
    assert s.launch()
    until(lambda: len(s.created) > count and s.app.radio_proc is s.created[-1], s.pump)
    assert s.titles[-1] == "Titel: -"


def test_failed_start_does_not_reuse_handover_title_on_retry(playback, monkeypatch):
    s = playback
    _pending_handover(s)
    original = radio._start_radio_playback
    monkeypatch.setattr(
        radio,
        "_start_radio_playback",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("synthetic")),
    )
    assert s.launch()
    assert s.app.radio_playback_request.done.wait(3)
    s.pump()
    assert s.titles[-1] == "Titel: Fehler / keine Verbindung"
    assert s.app.radio_handover_title == s.app.radio_handover_station_id == ""
    monkeypatch.setattr(radio, "_start_radio_playback", original)
    s.release.set()
    assert s.launch()
    until(lambda: s.app.radio_proc is not None, s.pump)
    assert s.titles[-1] == "Titel: -"


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("close", [False, True])
def test_stop_during_start_revokes_player_and_metadata(playback, local, close):
    s = playback
    assert s.launch(local)
    assert s.entered.wait(2)
    before = time.monotonic()
    assert radio.stop_radio_playback(s.app, async_mode=not close)
    assert time.monotonic() - before < 0.2
    if close:
        s.app._radio_panel_destroying = True
    s.release.set()
    until(lambda: s.created[0].poll() is not None, s.pump)
    assert s.app.radio_proc is None
    assert not s.metadata
    assert not any(text.startswith("Spielt") for text in s.statuses)


@pytest.mark.parametrize("local", [False, True])
def test_stop_after_preparation_rejects_queued_announcement(playback, local):
    s = playback
    s.release.set()
    assert s.launch(local)
    until(lambda: any(cb.__name__ == "announce" for cb in s.callbacks))
    assert s.app.radio_proc is None
    radio.stop_radio_playback(s.app)
    until(lambda: s.created[0].poll() is not None, s.pump)
    assert s.app.radio_proc is None
    assert not s.metadata
    assert not any(text.startswith("Spielt") for text in s.statuses)


def test_delayed_old_stop_cannot_clear_new_ipc_or_status(playback, monkeypatch):
    s = playback
    s.release.set()
    s.launch()
    until(lambda: s.app.radio_proc is not None, s.pump)
    old = s.app.radio_proc
    deferred = []
    real_thread = threading.Thread

    class DelayedStopThread:
        def __init__(self, target, args=(), **_):
            self.target, self.args = target, args

        def start(self):
            deferred.append(lambda: self.target(*self.args))

    with monkeypatch.context() as patch:
        patch.setattr(radio.threading, "Thread", DelayedStopThread)
        radio.stop_radio_playback(s.app)
    assert threading.Thread is real_thread
    s.launch()
    until(lambda: s.app.radio_proc not in (None, old), s.pump)
    new, path, last_status = s.app.radio_proc, s.app.radio_ipc_path, s.statuses[-1]
    for run in deferred:
        run()
    s.pump()
    assert s.app.radio_proc is new and new.poll() is None
    assert s.app.radio_ipc_path == path and Path(path).exists()
    assert s.statuses[-1] == last_status


def test_cancelled_intermediate_start_cannot_bypass_older_cleanup(playback):
    s = playback
    s.launch()
    assert s.entered.wait(2)
    first = s.created[0]
    s.launch()
    radio.stop_radio_playback(s.app)
    s.launch()
    # The first start is deliberately still preparing. Neither a cancelled
    # intermediate request nor the latest one may overtake its cleanup.
    assert len(s.created) == 1
    s.release.set()
    until(lambda: s.app.radio_proc not in (None, first), s.pump)
    assert len(s.created) == 2
    assert first.poll() is not None and not Path(first.ipc_path).exists()
    assert s.app.radio_proc is s.created[1]
    assert s.metadata == [s.created[1]]


def test_old_start_failure_cannot_replace_newer_success(
    playback, monkeypatch, tmp_path
):
    s = playback
    attempts = []

    def start(*_a, **_k):
        attempts.append(True)
        if len(attempts) == 1:
            s.entered.set()
            assert s.release.wait(3)
            raise RuntimeError("obsolete preparation failed")
        player = Player(tmp_path / "new-player.sock")
        s.created.append(player)
        return player

    monkeypatch.setattr(radio, "_start_radio_playback", start)
    s.launch()
    assert s.entered.wait(2)
    s.launch()
    s.release.set()
    until(lambda: s.app.radio_proc is not None, s.pump)
    assert s.app.radio_sandbox_state == "started"
    assert not any("fehlgeschlagen" in text for text in s.statuses)


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("rc", [0, 2])
@pytest.mark.parametrize("busy_ui", [False, True])
def test_natural_exit_has_terminal_status_even_before_publication(
    playback, local, rc, busy_ui
):
    s = playback
    s.release.set()
    s.launch(local)
    until(lambda: any(cb.__name__ == "announce" for cb in s.callbacks))
    request = s.app.radio_playback_request
    proc = s.created[0]
    if not busy_ui:
        s.pump()
        assert s.app.radio_proc is proc
    else:
        assert s.app.radio_proc is None
    proc.finish(rc)
    assert request.done.wait(2)
    s.pump()
    assert s.app.radio_proc is None and s.app.radio_ipc_path == ""
    assert s.app.radio_sandbox_state == "stopped"
    assert s.lights[-1] == ("gray" if rc == 0 else "red")
    assert s.titles[-1] == (
        "Titel: -" if rc == 0 else "Titel: Fehler / keine Verbindung"
    )
    assert s.statuses[-1].startswith(
        "Stream beendet:" if rc == 0 else "Radio beendet (rc=2)"
    )
    if busy_ui:
        assert not s.metadata, "a dead unpublished player must not query metadata"
        assert not any(text.startswith("Spielt") for text in s.statuses)


@pytest.mark.parametrize("action", ["stop", "new_start"])
def test_unpublished_exit_callback_cannot_override_later_intent(playback, action):
    s = playback
    s.release.set()
    s.launch()
    until(lambda: any(cb.__name__ == "announce" for cb in s.callbacks))
    s.created[0].finish(2)
    assert s.app.radio_playback_request.done.wait(2)
    if action == "stop":
        radio.stop_radio_playback(s.app)
        s.pump()
        assert s.app.radio_proc is None
        assert s.statuses[-1] == "Radio gestoppt."
        assert s.lights[-1] == "gray"
    else:
        s.launch()
        until(lambda: s.app.radio_proc is s.created[-1] and len(s.created) == 2, s.pump)
        assert s.app.radio_sandbox_state == "started"
        assert s.statuses[-1] == "Spielt: B"
        assert s.lights[-1] == "green"
    assert not any("rc=2" in text for text in s.statuses)


@pytest.mark.parametrize("mode", ["control", "stop-then-close", "switch-then-close"])
def test_real_tk_close_does_not_wait_on_worker_or_playback_lock(mode):
    command = [
        sys.executable,
        "-B",
        "-X",
        "pycache_prefix=/nonexistent",
        str(Path(__file__).with_name("radio_lifecycle_probe.py")),
        mode,
    ]
    run = subprocess.run(command, capture_output=True, text=True, timeout=4)
    assert run.returncode == 0, run.stdout + run.stderr
    result = json.loads(run.stdout)
    assert result["completed"] and result["tcl_threaded"]
    assert result["close_seconds"] < 0.2
