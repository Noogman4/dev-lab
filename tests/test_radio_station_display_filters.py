"""Whole-database browsing, combined display filters and independent rotation."""

import test_radio_main_views as view_tests
from test_radio_filters_ui import wait_count
from netmon.features import radio_controller as radio
from netmon.core import radio_station_filters as filters

radio_pages = view_tests.radio_pages


def prepare(app, count=125):
    app.radio_db = [
        {
            "id": f"row-{i:03}",
            "name": f"{'Rock' if i % 2 == 0 else 'Jazz'} Sender {i:03}",
            "url": f"https://example.invalid/{i}",
            "tags": ["rock" if i % 2 == 0 else "jazz"],
            "bitrate": 192 if i % 3 else 64,
        }
        for i in range(count)
    ]
    app.radio_favorites = app.radio_db[:4]
    app.show_radio_main_view("radio")
    app.update()


def test_radio_and_all_stations_reset_search_filters_and_pages_without_playback(
    radio_pages,
):
    app, actions, _, _ = radio_pages
    prepare(app)
    assert len(app.radio_search_results) == 125
    assert len(app.radio_station_table.get_children()) == 50
    assert app.radio_page_indicator_var.get() == "1/3"
    app.radio_page_next_button.invoke()
    assert app.radio_search_page == 1
    app.radio_search_var.set("Rock")
    app.apply_radio_station_filter({"categories": ["rock"], "minimum_bitrate": 192})
    assert 0 < len(app.radio_search_results) < 125
    app.radio_favorite_selectors[False].invoke()
    assert app.radio_search_var.get() == ""
    assert app.radio_station_filter == filters.normalize_filter()
    assert len(app.radio_search_results) == 125 and app.radio_search_page == 0
    app.radio_favorite_selectors[True].invoke()
    assert len(app.radio_search_results) == 4
    app.radio_main_view_buttons["radio"].invoke()
    assert not app.radio_show_favorites_var.get()
    assert len(app.radio_search_results) == 125
    app.radio_search_var.set("Jazz")
    radio.on_radio_search_changed(app)
    app.show_radio_main_view("playlist")
    app.radio_main_view_buttons["radio"].invoke()
    assert app.radio_search_var.get() == "" and len(app.radio_search_results) == 125
    assert actions == []


def test_display_filter_combines_with_search_and_preview_matches(radio_pages):
    app, actions, _, _ = radio_pages
    prepare(app, 12)
    app.radio_search_var.set("Rock")
    radio.on_radio_search_changed(app)
    assert len(app.radio_search_results) == 6
    app.radio_station_filter_button.invoke()
    dialog = app.radio_station_filter_window
    assert app.open_radio_station_filter() is dialog
    wait_count(app, dialog, 6)
    dialog.categories["rock"].set(True)
    dialog.bitrate.current(3)  # 192 kbps
    dialog.preview()
    wait_count(app, dialog, 4)
    dialog.apply_button.invoke()
    assert len(app.radio_search_results) == 4
    assert all(
        "Rock" in row["name"] and row["bitrate"] >= 192
        for row in app.radio_search_results
    )
    assert (
        "Rock" in app.radio_station_filter_text.get()
        and "192" in app.radio_station_filter_text.get()
    )
    assert "selected" in app.radio_station_filter_button.state()
    app.radio_search_var.set("Jazz")
    radio.on_radio_search_changed(app)
    assert app.radio_search_results == []
    assert "0" in app.radio_list_status_var.get()
    assert len(app.radio_db) == 12 and actions == []


def test_favorite_scope_and_cancel_filter_draft_are_consistent(radio_pages):
    app, actions, _, _ = radio_pages
    prepare(app, 12)
    app.radio_favorite_selectors[True].invoke()
    app.radio_station_filter_button.invoke()
    dialog = app.radio_station_filter_window
    wait_count(app, dialog, 4)
    dialog.categories["jazz"].set(True)
    dialog.preview()
    wait_count(app, dialog, 2)
    dialog.close()
    assert (
        app.radio_station_filter == filters.normalize_filter()
        and len(app.radio_search_results) == 4
    )
    app.apply_radio_station_filter({"categories": ["jazz"]})
    assert [row["id"] for row in app.radio_search_results] == ["row-001", "row-003"]
    app.radio_favorite_selectors[False].invoke()
    assert len(app.radio_search_results) == 12
    assert actions == []


def test_station_filters_and_navigation_do_not_change_random_filter_or_timer(
    radio_pages,
):
    app, actions, _, _ = radio_pages
    prepare(app, 12)
    mode = radio.radio_random_mode(app)
    mode.set_filter({"categories": ["jazz"], "minimum_bitrate": 128})
    saved = mode.settings()
    app.apply_radio_station_filter({"categories": ["rock"], "minimum_bitrate": 192})
    app.radio_station_filter_button.invoke()
    window = app.radio_station_filter_window
    app.radio_main_view_buttons["radio"].invoke()
    assert not window.winfo_exists()
    assert mode.settings() == saved
    assert app.radio_station_filter == filters.normalize_filter()
    assert app.radio_search_var.get() == "" and actions == []


def prepare_countries(app):
    prepare(app, 8)
    for row, country in zip(
        app.radio_db,
        ["Germany", "France", "Ghana", "Gabon", "Gambia", "Germany", "", "Germany"],
    ):
        row["country"] = country
    app.radio_station_filter_button.invoke()
    dialog = app.radio_station_filter_window
    app.update()
    return dialog


def test_country_dropdown_letters_cycle_and_full_prefix_jumps_to_germany(radio_pages):
    app, actions, _, _ = radio_pages
    dialog = prepare_countries(app)
    combo = dialog.country
    assert list(combo.cget("values")) == [
        "Alle Länder",
        "France",
        "Gabon",
        "Gambia",
        "Germany",
        "Ghana",
    ]
    combo.focus_force()
    app.update()
    for expected in ["Gabon", "Gambia", "Germany"]:
        combo.event_generate("<KeyPress>", keysym="g")
        app.update()
        assert combo.get() == expected
    dialog._country_last_key = 0
    for letter in "ger":
        combo.event_generate("<KeyPress>", keysym=letter)
    wait_count(app, dialog, 3)
    assert combo.get() == "Germany"
    dialog.apply_button.invoke()
    assert [row["id"] for row in app.radio_search_results] == [
        "row-000",
        "row-005",
        "row-007",
    ]
    assert "Land: Germany" in app.radio_station_filter_text.get()
    assert "selected" in app.radio_station_filter_button.state()
    assert actions == []


def test_country_jump_also_works_in_open_native_dropdown_and_reset_clears_it(
    radio_pages,
):
    app, actions, _, _ = radio_pages
    dialog = prepare_countries(app)
    combo = dialog.country
    app.tk.call("ttk::combobox::Post", str(combo))
    app.update()
    listbox = dialog._country_listbox
    for letter in "ger":
        app.tk.call("event", "generate", listbox, "<KeyPress>", "-keysym", letter)
        app.update()
    assert combo.get() == "Germany"
    assert tuple(app.tk.call(listbox, "curselection")) == (4,)
    app.tk.call("event", "generate", listbox, "<KeyPress>", "-keysym", "Return")
    app.update()
    dialog.reset_button.invoke()
    wait_count(app, dialog, 8)
    assert combo.current() == 0
    combo.current(4)
    dialog.apply_button.invoke()
    assert len(app.radio_search_results) == 3
    app.radio_favorite_selectors[False].invoke()
    assert (
        len(app.radio_search_results) == 8 and "country" not in app.radio_station_filter
    )
    dialog = app.open_radio_station_filter()
    combo = dialog.country
    combo.current(4)
    dialog.apply_button.invoke()
    app.radio_main_view_buttons["radio"].invoke()
    assert len(app.radio_search_results) == 8
    random_popup = app.open_radio_random_popup()
    random_dialog = random_popup.open_filters()
    assert random_dialog.country is None
    assert "country" not in random_popup.mode.filters
    assert actions == []


def test_country_combines_with_search_category_and_bitrate_and_cancel_is_safe(
    radio_pages,
):
    app, actions, _, _ = radio_pages
    dialog = prepare_countries(app)
    dialog.country.current(4)
    dialog.close()
    assert (
        "country" not in app.radio_station_filter and len(app.radio_search_results) == 8
    )
    app.radio_search_var.set("Rock")
    radio.on_radio_search_changed(app)
    dialog = app.open_radio_station_filter()
    dialog.categories["rock"].set(True)
    dialog.bitrate.current(3)
    dialog.country.current(4)
    dialog.preview()
    wait_count(app, dialog, 0)  # The German rock fixture has only 64 kbps.
    dialog.apply_button.invoke()
    assert app.radio_search_results == [] and "0" in app.radio_list_status_var.get()
    assert len(app.radio_db) == 8 and actions == []
