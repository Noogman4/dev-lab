"""Actual popup and both radio layouts; no network or playback actions."""

import json
import os
from pathlib import Path
from types import SimpleNamespace
import test_radio_main_views as views
import pytest
from netmon import app as main
from netmon.core import radio_multi_recording as multi
from netmon.features import radio_multi_recording_controller as controller
from netmon.features import radio_controller as radio
from netmon.services.lang_service import LangService

radio_pages = views.radio_pages


def add_station(app):
    station = radio.normalize_station_entry(
        {
            "id": "test-multi",
            "name": "Test Mehrfachaufnahme",
            "url": "https://example.invalid/live",
            "bitrate": 192,
        }
    )
    app.radio_db = [station]
    app.radio_favorites = [station]
    app.radio_context_station_id = station["id"]
    return station


def test_english_multi_recording_labels_and_status(radio_pages):
    app, actions, _media, _recordings = radio_pages
    catalogs = Path(__file__).resolve().parents[1] / "netmon" / "lang"
    app._translations = LangService(str(catalogs)).load("en")
    station = add_station(app)

    assert controller.add_selected(app)
    window = app.radio_multi_recording_window
    assert window.title() == "Multi-recording"
    assert window.start_button.cget("text") == "Check & start"
    assert window.tree.set(station["id"], "status") == "Ready"
    assert app.radio_multi_recording_button.cget("text") == "Multi-recording …"
    assert controller.manager(app).snapshot()[1].startswith("Right-click a station")
    assert actions == []


def test_right_click_action_adds_once_and_folder_button_reopens_popup(radio_pages):
    app, actions, _media, _recordings = radio_pages
    station = add_station(app)
    menu = app.radio_station_menu
    index = next(
        index
        for index in range(menu.index("end") + 1)
        if menu.type(index) == "command"
        and menu.entrycget(index, "label") == "Zur Mehrfachaufnahme hinzufügen"
    )
    menu.invoke(index)
    app.update()
    window = app.radio_multi_recording_window
    assert window.tree.get_children() == (station["id"],)
    menu.invoke(index)
    assert window.tree.get_children() == (station["id"],)
    assert app.radio_db == app.radio_favorites == [station]
    assert app.radio_current_station_id == ""
    window.withdraw()
    app.show_radio_main_view("recordings")
    app.update()
    assert app.radio_multi_recording_button.winfo_ismapped()
    app.radio_multi_recording_button.invoke()
    app.update()
    assert app.radio_multi_recording_window is window and window.winfo_ismapped()
    if os.environ.get("NETMON_TEST_ISOLATED") == "1":
        from PIL import ImageGrab

        ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
            "/work/multi-recording-"
            + ("embedded" if app.radio_embedded_mode else "standalone")
            + ".png"
        )
    window.withdraw()
    app.show_radio_main_view("media")
    app.update()
    assert not app.radio_multi_recording_button.winfo_ismapped()
    assert actions == []


def test_favorite_context_selection_is_the_added_station(radio_pages, monkeypatch):
    app, actions, _media, _recordings = radio_pages
    station = add_station(app)
    monkeypatch.setattr(app, "_show_context_menu", lambda *_a: None)
    app.radio_context_station_id = "wrong"
    app._show_radio_favorite_context_menu(station["id"], SimpleNamespace())
    assert controller.add_selected(app)
    assert controller.manager(app).snapshot()[0][0]["id"] == station["id"]
    assert actions == []


def test_popup_hidden_does_not_stop_and_all_handover_routes_block(
    radio_pages, monkeypatch
):
    app, _actions, _media, _recordings = radio_pages
    add_station(app)
    controller.add_selected(app)
    mode = controller.manager(app)
    mode._active = True
    try:
        window = app.radio_multi_recording_window
        window.refresh()
        window.withdraw()
        app.update()
        assert mode.busy and not mode._cancel.is_set()
        assert "disabled" in window.start_button.state()
        assert "disabled" in window.duration.state()
        monkeypatch.setattr(
            app, "refresh_radio_attach_state", lambda: pytest.fail("attach continued")
        )
        app.radio_detach_callback = lambda: pytest.fail("detach continued")
        assert app.attach_radio_to_netmon() is False
        assert app.detach_radio_from_netmon() is False
        host = SimpleNamespace(radio_embedded_panel=app)
        assert main.App.open_radio_external_app(host) is False
        assert main.App.reattach_radio_app(host, handover_payload={}) is False
        assert "An-/Abkoppeln" in app.radio_record_status_var.get()
        monkeypatch.setattr(controller.messagebox, "askyesno", lambda *_a, **_k: False)
        assert not controller.confirm_close(app) and not mode._cancel.is_set()
        monkeypatch.setattr(controller.messagebox, "askyesno", lambda *_a, **_k: True)
        assert controller.confirm_close(app) and mode._cancel.is_set()
    finally:
        mode._active = False


def test_single_recording_cannot_become_eleventh(radio_pages, monkeypatch):
    app, _actions, _media, _recordings = radio_pages
    add_station(app)
    mode = controller.manager(app)
    mode._active = True
    mode._session = {str(i): {} for i in range(10)}
    monkeypatch.setattr(radio, "radio_recording_available", lambda _app: True)
    monkeypatch.setattr(
        radio.radio_sandbox,
        "start_recording",
        lambda *_a, **_k: pytest.fail("eleventh pipeline"),
    )
    try:
        assert radio.start_radio_recording(app) is False
        assert "zehn" in app.radio_record_status_var.get()
    finally:
        mode._active = False


def test_popup_duration_persists_queue_and_load_never_starts(
    radio_pages, monkeypatch, tmp_path
):
    app, _actions, _media, recordings = radio_pages
    station = add_station(app)
    # The shared GUI fixture stubs persistence: restore the real writer here.
    # Exercise normalization and the actual settings JSON via the original
    # function retained at module collection, before the fixture patch.
    monkeypatch.setattr(radio, "save_radio_settings", REAL_SAVE)
    app.radio_settings_path = str(tmp_path / "radio_settings.json")
    controller.add_selected(app)
    assert controller.persist(app, 12)
    settings = json.loads(open(app.radio_settings_path).read())
    assert settings["multi_recording_station_ids"] == [station["id"]]
    assert settings["multi_recording_minutes"] == 12
    replacement = SimpleNamespace(
        radio_settings=settings,
        radio_db=[station],
        radio_favorites=[],
        radio_search_results=[],
    )
    mode = controller.manager(replacement)
    assert not mode.busy and mode.snapshot()[0][0]["id"] == station["id"]
    app.radio_multi_recording_window.minutes.set("0")
    app.radio_multi_recording_window.start()
    assert not controller.manager(app).busy
    assert "1 bis 1440" in app.radio_multi_recording_window.notice.get()
    assert multi.saved_settings(settings)["multi_recording_minutes"] == 12


REAL_SAVE = radio.save_radio_settings


def test_popup_start_and_hidden_running_status_remain_responsive(
    radio_pages, monkeypatch
):
    from test_radio_multi_recording import FakeRecording, wait_for

    app, actions, _, _ = radio_pages
    add_station(app)
    controller.add_selected(app)
    mode = controller.manager(app)
    mode.check_seconds = 0.7
    mode._start = lambda url, path, **_k: FakeRecording(url, path)
    monkeypatch.setattr(radio, "radio_recording_available", lambda _app: True)
    window = app.radio_multi_recording_window
    window.minutes.set("1")
    window.start_button.invoke()
    window.withdraw()
    try:
        wait_for(
            lambda: app.update()
            or all(row["status"] == "recording" for row in mode.snapshot()[0])
        )
        window.refresh()
        assert not window.winfo_ismapped() and mode.busy
        assert "1 Streams" in app.radio_record_status_var.get()
        assert (
            app.radio_multi_recording_button.cget("text") == "Mehrfachaufnahme (1/10)"
        )
        host_button = (
            app.radio_detach_button
            if app.radio_embedded_mode
            else app.radio_attach_button
        )
        assert "disabled" in host_button.state()
        window.deiconify()
        app.update()
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            from PIL import ImageGrab

            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
                "/work/multi-active-"
                + ("embedded" if app.radio_embedded_mode else "standalone")
                + ".png"
            )
        assert actions == []
    finally:
        mode.stop()
        wait_for(lambda: not mode.busy)
        window.refresh()
    assert "beendet" in app.radio_record_status_var.get()
    assert "disabled" not in host_button.state()
