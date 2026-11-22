"""Slow player replies must not stall Tk or replay obsolete slider values."""

import threading
import time
from tkinter import ttk

import test_radio_main_views as view_tests
from netmon.features import radio_controller as radio

radio_pages = view_tests.radio_pages


def pump_until(app, condition):
    deadline = time.monotonic() + 2
    while not condition():
        assert time.monotonic() < deadline, "radio control queue did not drain"
        app.update()
        time.sleep(0.005)


def test_wheel_and_equalizer_keep_ui_alive_and_coalesce_slow_updates(
    radio_pages, monkeypatch, tmp_path
):
    app, actions, _, _ = radio_pages
    entered, release = threading.Event(), threading.Event()
    calls, ticks = [], []
    ui_thread = threading.get_ident()

    def send(snapshot, command):
        assert threading.get_ident() != ui_thread
        assert vars(snapshot) == {"radio_ipc_path": str(tmp_path / "fixture.sock")}
        calls.append(command)
        entered.set()
        assert release.wait(3)
        return True

    monkeypatch.setattr(radio, "_send_mpv_command", send)
    app.radio_proc = object()
    app.radio_ipc_path = str(tmp_path / "fixture.sock")
    app.radio_volume_var.set(40)
    try:
        app.radio_compact_volume.event_generate("<Button-4>")
        pump_until(app, entered.is_set)
        assert app.radio_volume_var.get() == 42
        assert app.radio_volume_label_var.get() == "42%"
        app.after(0, lambda: ticks.append(True))
        for _ in range(3):
            app.radio_compact_volume.event_generate("<Button-4>")
        app.radio_compact_volume.event_generate("<Button-5>")
        assert app.radio_volume_var.get() == 46
        app.radio_compact_volume.event_generate("<MouseWheel>", delta=120)
        bass = next(
            child
            for child in app.radio_inline_equalizer.winfo_children()
            if isinstance(child, ttk.Scale) and child is not app.radio_compact_volume
        )
        bass.set(3)
        bass.event_generate("<ButtonRelease-1>")
        pump_until(app, lambda: bool(ticks))
        assert not release.is_set()
        assert calls == [["set_property", "volume", 42]]
        assert app.radio_volume_var.get() == 48
        release.set()
        pump_until(app, lambda: not app._radio_control_updates["scheduled"])
        assert calls == [
            ["set_property", "volume", 42],
            ["set_property", "volume", 48],
            ["set_property", "af", radio.radio_eq_filter_spec(app)],
        ]
        assert actions == []
    finally:
        release.set()
        app.radio_proc = None


def test_failed_old_player_update_cannot_restart_replacement(
    radio_pages, monkeypatch, tmp_path
):
    app, actions, _, _ = radio_pages
    entered, release = threading.Event(), threading.Event()
    calls = []

    def send(_snapshot, command):
        calls.append(command)
        if len(calls) == 1:
            entered.set()
            assert release.wait(3)
            return False
        return True

    monkeypatch.setattr(radio, "_send_mpv_command", send)
    app.radio_proc = object()
    app.radio_current_station_id = "old-station"
    app.radio_ipc_path = str(tmp_path / "fixture.sock")
    try:
        app.radio_volume_var.set(10)
        app.commit_radio_volume_change()
        pump_until(app, entered.is_set)
        app.radio_proc = object()
        app.radio_current_station_id = "new-station"
        app.radio_volume_var.set(80)
        app.commit_radio_volume_change()
        release.set()
        pump_until(app, lambda: not app._radio_control_updates["scheduled"])
        assert calls == [
            ["set_property", "volume", 10],
            ["set_property", "volume", 80],
        ]
        assert actions == []
    finally:
        release.set()
        app.radio_proc = None
