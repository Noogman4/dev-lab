"""Real filter popup controls with private fixtures and offline station data."""

import time

import test_radio_main_views as view_tests
from netmon.core import radio_station_filters as filters

radio_pages = view_tests.radio_pages


def wait_count(app, dialog, number):
    deadline = time.monotonic() + 3
    while dialog.worker is not None:
        assert time.monotonic() < deadline
        app.update()
        time.sleep(0.005)
    assert dialog.count.get() == f"Passende Sender: {number}"


def prepare(app):
    app.radio_db = [
        {
            "id": "rock",
            "name": "Rock",
            "url": "https://example.invalid/r",
            "tags": ["rock"],
            "bitrate": 192,
        },
        {
            "id": "jazz",
            "name": "Jazz",
            "url": "https://example.invalid/j",
            "genre": "jazz",
            "bitrate": 128,
        },
        {
            "id": "unknown",
            "name": "Rock unknown",
            "url": "https://example.invalid/u",
            "category": "rock",
            "bitrate": 0,
        },
    ]
    popup = app.open_radio_random_popup()
    popup.filter_button.invoke()
    app.update()
    return popup, popup.filter_window


def test_filter_draft_preview_apply_summary_and_reset(radio_pages):
    app, actions, _, _ = radio_pages
    popup, dialog = prepare(app)
    wait_count(app, dialog, 3)
    assert popup.open_filters() is dialog
    assert (
        popup.filter_button.winfo_rootx()
        > popup.apply_button.winfo_rootx() + popup.apply_button.winfo_width()
    )
    dialog.categories["rock"].set(True)
    dialog.bitrate.current(2)
    dialog.preview()
    wait_count(app, dialog, 1)
    assert popup.mode.filters == filters.normalize_filter()
    dialog.unknown.set(True)
    dialog.preview()
    wait_count(app, dialog, 2)
    dialog.apply_button.invoke()
    assert not dialog.winfo_exists()
    assert popup.mode.filters == filters.normalize_filter(
        {"categories": ["rock"], "minimum_bitrate": 128, "include_unknown": True}
    )
    assert "Rock" in popup.filter_text.get() and "128" in popup.filter_text.get()
    assert app.radio_settings["random_filter"] == popup.mode.filters
    dialog = popup.open_filters()
    dialog.reset_button.invoke()
    wait_count(app, dialog, 3)
    dialog.apply_button.invoke()
    assert popup.mode.filters == filters.normalize_filter()
    assert actions == []


def test_cancel_and_failed_save_leave_existing_filters_intact(radio_pages):
    app, actions, _, _ = radio_pages
    popup, dialog = prepare(app)
    dialog.categories["rock"].set(True)
    dialog.close()
    assert popup.mode.filters == filters.normalize_filter()
    dialog = popup.open_filters()
    dialog.categories["rock"].set(True)
    popup.mode.save = lambda settings: False
    wait_count(app, dialog, 3)
    dialog.apply_button.invoke()
    assert dialog.winfo_exists()
    assert "nicht gespeichert" in dialog.count.get()
    assert popup.mode.filters == filters.normalize_filter()
    popup.close()
    assert dialog.stop.is_set() and not dialog.winfo_exists()
    assert actions == []


def test_no_matches_stops_random_without_starting_an_unfiltered_station(radio_pages):
    app, actions, _, _ = radio_pages
    popup, dialog = prepare(app)
    dialog.categories["country"].set(True)
    dialog.preview()
    wait_count(app, dialog, 0)
    dialog.apply_button.invoke()
    assert not app.toggle_radio_random()
    assert popup.mode.reason == "no_matches"
    assert "Keine Sender passen" in popup.status.get()
    assert actions == []
