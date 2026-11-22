"""Real radio toolbar and history window, with intercepted audio actions."""

import json
import pytest
import test_radio_main_views as view_tests
from test_radio_random import Timer
from netmon.features import radio_controller as radio

radio_pages = view_tests.radio_pages


def test_random_button_timer_popup_and_history_use_entire_database(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    timer, played = Timer(), []
    app.radio_db = [
        {"id": str(i), "name": f"Database {i}", "url": f"https://example.invalid/{i}"}
        for i in range(3)
    ]
    app.radio_favorites = [app.radio_db[0]]
    app.radio_search_var.set("Database 0")
    mode = radio.radio_random_mode(app)
    mode.schedule, mode.cancel, mode.clock = (
        timer.after,
        timer.cancel,
        lambda: timer.now,
    )

    def play(app, station_id, *, random_token=None):
        played.append(station_id)
        mode.started(random_token)
        return True

    monkeypatch.setattr(radio, "play_radio_station", play)
    app.radio_manage_button.invoke()
    app.update()
    app.radio_random_button.invoke()
    assert mode.active and "selected" in app.radio_random_button.state()
    app.radio_random_settings_button.invoke()
    popup = app.radio_random_window
    assert popup is app.open_radio_random_popup()
    app.update()
    assert popup.winfo_ismapped() and len(popup.history.get_children()) == 1
    popup.minutes.set("2")
    popup.apply_button.invoke()
    assert mode.minutes == 2
    for _ in range(2):
        timer.advance(120)
    assert set(played) == {"0", "1", "2"}
    assert len(popup.history.get_children()) == 3
    popup.minutes.set("0")
    popup.apply_button.invoke()
    assert mode.minutes == 2 and "1440" in popup.status.get()
    popup.close()
    assert app.radio_random_window is None and mode.active
    app.radio_manage_button.invoke()
    app.radio_random_button.invoke()
    timer.advance(10000)
    assert not mode.active and len(played) == 3 and not timer.pending
    assert "selected" not in app.radio_random_button.state()
    assert actions == []


def test_toolbar_gives_search_space_and_management_holds_inline_switch(radio_pages):
    app, actions, _, _ = radio_pages
    for width in (1100, 820, 720):
        app.winfo_toplevel().geometry(f"{width}x900")
        app.update()
        search, manage = app.radio_compact_search, app.radio_manage_button
        assert search.winfo_ismapped() and manage.winfo_ismapped()
        assert not app.radio_random_button.winfo_ismapped()
        assert search.winfo_width() >= 160
        assert search.winfo_rooty() + search.winfo_height() <= manage.winfo_rooty()
        edge = manage.master.winfo_rootx() + manage.master.winfo_width()
        assert search.winfo_rootx() + search.winfo_width() <= edge
        assert manage.winfo_rootx() + manage.winfo_width() <= edge
        manage.invoke()
        app.update()
        switch, options = app.radio_random_button, app.radio_random_settings_button
        assert switch.winfo_ismapped() and options.winfo_ismapped()
        assert (
            switch.winfo_rooty() == options.winfo_rooty()
            or abs(switch.winfo_rooty() - options.winfo_rooty()) <= 4
        )
        assert switch.winfo_rootx() + switch.winfo_width() < options.winfo_rootx()
        assert app.radio_manage_popup.winfo_rootx() >= 0
        assert (
            app.radio_manage_popup.winfo_rooty() + app.radio_manage_popup.winfo_height()
            <= app.winfo_screenheight()
        )
        app.radio_manage_popup.event_generate("<Escape>")
        app.update()
        assert not app.radio_manage_popup.winfo_ismapped()
    assert actions == []


def prepare_history(app, tmp_path):
    stations = [
        {
            "id": key,
            "name": name,
            "url": f"https://example.invalid/{key}",
            "custom": False,
        }
        for key, name in [("wanted", "Sender im Verlauf"), ("other", "Anderer Sender")]
    ]
    app.radio_db = stations
    app.radio_favorites = []
    app.radio_db_path = str(tmp_path / "database.json")
    app.radio_favorites_path = str(tmp_path / "favorites.json")
    radio.save_radio_db(app)
    radio.save_radio_favorites(app)
    app.radio_current_station_id = "other"
    app.radio_context_station_id = "other"
    mode = radio.radio_random_mode(app)
    mode.history = [
        {
            "selected_at": "2026-11-15T10:00:00+00:00",
            "station_id": "wanted",
            "name": "Sender im Verlauf",
            "status": "stopped",
        }
    ]
    popup = app.open_radio_random_popup()
    app.update()
    return popup


def right_click_history(app, popup):
    key = popup.history.get_children()[0]
    x, y, width, height = popup.history.bbox(key)
    popup.history.event_generate("<ButtonPress-3>", x=x + 30, y=y + height // 2)
    app.update()
    assert not popup.history_menu.winfo_ismapped()
    popup.history.event_generate("<ButtonRelease-3>", x=x + 30, y=y + height // 2)
    app.update()
    assert popup.history_menu.winfo_ismapped()


def test_history_favorite_targets_clicked_station_and_saves_it(radio_pages, tmp_path):
    app, actions, _, _ = radio_pages
    popup = prepare_history(app, tmp_path)
    right_click_history(app, popup)
    # The timer can refresh the list while the context menu is open.
    popup.mode.history.append(
        {**popup.mode.history[0], "station_id": "other", "name": "Anderer Sender"}
    )
    popup.refresh()
    popup.history_menu.invoke(2)
    assert [row["id"] for row in app.radio_favorites] == ["wanted"]
    assert json.loads((tmp_path / "favorites.json").read_text())[0]["id"] == "wanted"
    assert app.radio_current_station_id == app.radio_context_station_id == "other"
    assert actions == []


@pytest.mark.parametrize("confirm", [False, True])
def test_history_delete_confirms_and_removes_catalog_station_only(
    radio_pages, tmp_path, monkeypatch, confirm
):
    app, actions, _, _ = radio_pages
    popup = prepare_history(app, tmp_path)
    radio.add_to_favorites(app, app.radio_db[0])
    before = list(popup.mode.history)
    prompts = []
    monkeypatch.setattr(
        radio.messagebox,
        "askyesno",
        lambda title, text, **kw: prompts.append((text, kw["parent"])) or confirm,
    )
    right_click_history(app, popup)
    popup.history_menu.invoke(3)
    assert len(prompts) == 1 and prompts[0][1] is popup
    assert "Sender im Verlauf" in prompts[0][0]
    expected = ["other"] if confirm else ["wanted", "other"]
    assert [row["id"] for row in app.radio_db] == expected
    assert [
        row["id"] for row in json.loads((tmp_path / "database.json").read_text())
    ] == expected
    assert [row["id"] for row in app.radio_favorites] == ([] if confirm else ["wanted"])
    assert popup.mode.history == before and app.radio_current_station_id == "other"
    if confirm:
        right_click_history(app, popup)
        assert popup.history_menu.entrycget(2, "state") == "disabled"
        assert popup.history_menu.entrycget(3, "state") == "disabled"
    assert actions == []


@pytest.mark.parametrize(
    "fault", ["database_write", "favorite_write", "changed_station", "duplicate_id"]
)
def test_history_actions_preserve_unrelated_data_on_errors(
    radio_pages, tmp_path, monkeypatch, fault
):
    app, actions, _, _ = radio_pages
    popup = prepare_history(app, tmp_path)
    right_click_history(app, popup)
    monkeypatch.setattr(radio.messagebox, "askyesno", lambda *a, **kw: True)
    if fault == "database_write":
        monkeypatch.setattr(radio, "save_radio_db", lambda *a, **kw: False)
    elif fault == "favorite_write":
        monkeypatch.setattr(radio, "save_radio_favorites", lambda *a, **kw: False)
    elif fault == "changed_station":
        app.radio_db[0]["url"] = "https://example.invalid/changed"
    else:
        app.radio_db.append(dict(app.radio_db[0]))
    before = [dict(row) for row in app.radio_db]
    popup.history_menu.invoke(3)
    assert app.radio_db == before and app.radio_favorites == []
    if fault in {"database_write", "favorite_write"}:
        assert len(json.loads((tmp_path / "database.json").read_text())) == 2
    assert actions == []


def test_manage_popup_closes_on_outside_click_and_keeps_existing_actions(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    called = []
    app.radio_manage_menu.entryconfigure(
        app.radio_manage_actions["add"], command=lambda: called.append("add")
    )
    app.radio_manage_button.invoke()
    app.update()
    popup = app.radio_manage_popup
    assert popup.winfo_ismapped()
    app.radio_title_label.event_generate("<ButtonPress-1>", x=2, y=2)
    app.update()
    assert not popup.winfo_ismapped()
    app.radio_manage_button.invoke()
    app.update()
    popup.rows[app.radio_manage_actions["add"]].invoke()
    assert called == ["add"] and not popup.winfo_ismapped()
    assert actions == []


@pytest.mark.parametrize("confirm", [False, True])
@pytest.mark.parametrize("blank", [False, True])
def test_clear_list_context_menu_on_row_or_blank_space_confirms_entire_history(
    radio_pages, tmp_path, monkeypatch, confirm, blank
):
    app, actions, _, _ = radio_pages
    popup = prepare_history(app, tmp_path)
    popup.mode.history.append(
        {**popup.mode.history[0], "station_id": "other", "name": "Anderer Sender"}
    )
    popup.refresh()
    prompts = []
    monkeypatch.setattr(
        radio.messagebox,
        "askyesno",
        lambda title, text, **kw: prompts.append(kw["parent"]) or confirm,
    )
    before = list(popup.mode.history)
    if blank:
        popup.history.event_generate(
            "<ButtonRelease-3>", x=30, y=popup.history.winfo_height() - 6
        )
        app.update()
        assert popup.history_menu.winfo_ismapped()
        assert popup.history_menu.entrycget(2, "state") == "disabled"
    else:
        right_click_history(app, popup)
    assert popup.history_menu.entrycget(5, "label") == "Liste leeren"
    popup.history_menu.invoke(5)
    assert prompts == [popup]
    assert popup.mode.history == ([] if confirm else before)
    assert len(popup.history.get_children()) == (0 if confirm else 2)
    assert len(app.radio_db) == 2 and app.radio_favorites == []
    assert app.radio_current_station_id == "other" and actions == []
    if confirm:
        assert app.radio_settings["random_history"] == []
        assert popup.history_menu.entrycget(5, "state") == "disabled"
