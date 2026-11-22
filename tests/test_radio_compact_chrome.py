"""Real compact radio controls, with all external actions intercepted."""

import io
from tkinter import font as tkfont, ttk

from PIL import Image, ImageTk
import pytest

import test_radio_main_views as view_tests
from netmon import netmon_radio_app as ui
from netmon.features import radio_controller as radio
from netmon.core import radio_logo

radio_pages = view_tests.radio_pages


@pytest.mark.parametrize(
    "source_size,bounds",
    [
        ((8, 8), (0, 0, 96, 96)),
        ((32, 16), (0, 24, 96, 72)),
        ((16, 32), (24, 0, 72, 96)),
        ((320, 160), (0, 24, 96, 72)),
    ],
)
def test_cached_small_and_large_logos_fill_fixed_player_boxes(
    radio_pages, monkeypatch, tmp_path, source_size, bounds
):
    app, actions, _, _ = radio_pages
    original = io.BytesIO()
    Image.new("RGBA", source_size, (255, 0, 0, 128)).save(original, format="PNG")
    payload = radio_logo.decode_image(original.getvalue())
    cache = tmp_path / "existing.pixels"
    cache.write_bytes(payload)
    app.update()
    positions = (
        app.radio_title_label.winfo_rooty(),
        app.radio_record_summary.winfo_rooty(),
        app.radio_main_navigation.winfo_rooty(),
    )
    monkeypatch.setattr(
        Image, "open", lambda *a, **kw: pytest.fail("Encoded image decoder in UI")
    )
    monkeypatch.setattr(
        ui.radio_sandbox,
        "fetch_logo",
        lambda *a, **kw: pytest.fail("Unnecessary download"),
    )
    app._radio_logo_request_key = "test"
    app._render_station_logo_file(str(cache), "test")
    app.update()
    image = ImageTk.getimage(app._radio_logo_photo)
    mini = ImageTk.getimage(app._radio_mini_logo_photo)
    assert image.size == (96, 96) and image.getbbox() == bounds
    assert mini.size == (88, 88)
    assert image.getpixel((48, 48)) == (255, 0, 0, 128)
    assert positions == (
        app.radio_title_label.winfo_rooty(),
        app.radio_record_summary.winfo_rooty(),
        app.radio_main_navigation.winfo_rooty(),
    )
    assert cache.read_bytes() == payload
    assert actions == []


def test_native_tk_logo_scaling_centers_small_images_without_parent_pillow(
    radio_pages, monkeypatch, tmp_path
):
    app, actions, _, _ = radio_pages
    original = io.BytesIO()
    Image.new("RGBA", (32, 16), (255, 0, 0, 255)).save(original, format="PNG")
    cache = tmp_path / "existing.pixels"
    cache.write_bytes(radio_logo.decode_image(original.getvalue()))
    monkeypatch.setattr(ui, "Image", None)
    monkeypatch.setattr(ui, "ImageTk", None)
    app._radio_logo_request_key = "test"
    app._render_station_logo_file(str(cache), "test")
    app.update()
    main, mini = app._radio_logo_photo, app._radio_mini_logo_photo
    assert (main.width(), main.height()) == (96, 96)
    assert (mini.width(), mini.height()) == (88, 88)
    assert main.get(48, 48) == mini.get(44, 44) == (255, 0, 0)
    assert main.transparency_get(0, 0) and mini.transparency_get(0, 0)
    assert not main.transparency_get(48, 48) and not mini.transparency_get(44, 44)
    assert actions == []


@pytest.fixture(autouse=True)
def menu_spies(monkeypatch):
    calls = []
    for method, name in (
        ("open_new_custom_radio_station_editor", "add"),
        ("open_radio_database_sources_popup", "databases"),
        ("check_visible_radio_station_reachability", "reachability"),
    ):
        monkeypatch.setattr(
            ui.NetMonRadioApp, method, lambda _app, key=name: calls.append(key)
        )
    monkeypatch.setattr(
        ui.radio_station_import_controller,
        "import_station_file_dialog",
        lambda _app: calls.append("import"),
    )
    monkeypatch.setattr(
        ui.radio_station_import_controller,
        "open_station_import_folder",
        lambda _app: calls.append("imports"),
    )
    return calls


def test_compact_header_reclaims_main_area_and_wraps_at_smaller_width(radio_pages):
    app, actions, _, _ = radio_pages
    assert app.radio_player_controls.winfo_height() <= 260
    assert app.radio_main_views["radio"].winfo_height() > 500
    assert app._radio_logo_size() == (96, 96)
    assert set(app.radio_player_tool_buttons) == {"visualizer"}
    assert vars(app).get("radio_toolbox_window") is None
    navigation_sizes = {
        key: (button.winfo_width(), button.winfo_height())
        for key, button in app.radio_main_view_buttons.items()
    }
    for width in (1100, 820, 720):
        app.winfo_toplevel().geometry(f"{width}x900")
        app.update()
        parent = app.radio_player_controls
        edge = parent.winfo_rootx() + parent.winfo_width()
        for control in [
            *app.radio_player_tool_buttons.values(),
            app.radio_miniplayer_button,
        ]:
            assert control.winfo_ismapped()
            assert control.winfo_rootx() + control.winfo_width() <= edge + 1
        mini = app.radio_miniplayer_button
        details = app.radio_player_details_button
        assert mini.winfo_rootx() == details.winfo_rootx()
        assert mini.winfo_width() == details.winfo_width()
        assert mini.winfo_height() == details.winfo_height()
        assert mini.cget("style") == details.cget("style")
        assert mini.winfo_rooty() >= details.winfo_rooty() + details.winfo_height()
        playlist = app.radio_main_view_buttons["playlist"]
        assert playlist.winfo_rooty() + playlist.winfo_height() == (
            mini.winfo_rooty() + mini.winfo_height()
        )
        left = app.radio_player_left_block
        for key, button in app.radio_main_view_buttons.items():
            assert (button.winfo_width(), button.winfo_height()) == navigation_sizes[
                key
            ]
            assert button.winfo_ismapped()
            assert button.winfo_rootx() + button.winfo_width() <= (
                left.winfo_rootx() + left.winfo_width()
            )
        visualizer = app.radio_player_tool_buttons["visualizer"]
        assert visualizer.winfo_rooty() == mini.winfo_rooty()
        assert visualizer.winfo_rootx() > mini.winfo_rootx() + mini.winfo_width()
        assert visualizer.winfo_width() == mini.winfo_width()
        assert visualizer.winfo_height() == mini.winfo_height()
        assert visualizer.cget("style") == mini.cget("style")
        assert app.radio_compact_volume.winfo_ismapped()
        next_button = app.radio_transport_buttons["next"]
        assert 0 <= edge - next_button.winfo_rootx() - next_button.winfo_width() <= 16
        volume_row = app.radio_compact_volume.master
        assert volume_row.winfo_rooty() >= (
            next_button.winfo_rooty() + next_button.winfo_height()
        )
        assert 0 <= edge - volume_row.winfo_rootx() - volume_row.winfo_width() <= 12
        transport = next_button.master
        volume = app.radio_compact_volume
        sound = app.radio_inline_equalizer
        bass = next(
            child
            for child in sound.winfo_children()
            if isinstance(child, ttk.Scale) and child is not volume
        )
        assert sound.winfo_width() == transport.winfo_width()
        assert volume.winfo_rootx() == bass.winfo_rootx()
        assert volume.winfo_width() == bass.winfo_width()
        assert (
            0 <= bass.winfo_rooty() - volume.winfo_rooty() - volume.winfo_height() <= 8
        )
        for button in app.radio_transport_buttons.values():
            assert button.winfo_width() >= 45
            assert button.winfo_height() >= 36
    assert actions == []


def test_station_name_wraps_into_three_lines_without_moving_controls(radio_pages):
    app, actions, _, _ = radio_pages
    label = app.radio_station_name_label
    font = tkfont.Font(root=label, font=label.cget("font"))
    long_name = "*CLUB CHARTS TOP 100 || IMMER AKTUELL || DJ CLUB RADIO " * 5
    for width in (1100, 820, 720, 1100):
        app.winfo_toplevel().geometry(f"{width}x900")
        radio._set_radio_station_text(app, "bibiza")
        app.update()
        controls_x = app.radio_player_control_block.winfo_rootx()
        title_y = app.radio_title_label.winfo_rooty()
        assert label.cget("text") == "Radio: bibiza"
        radio._set_radio_station_text(app, long_name)
        app.update()
        lines = label.cget("text").splitlines()
        assert len(lines) == 3
        assert lines[-1].endswith("…")
        assert all(font.measure(line) <= label.winfo_width() - 4 for line in lines)
        assert label.winfo_rootx() + label.winfo_width() < controls_x
        assert app.radio_player_control_block.winfo_rootx() == controls_x
        assert app.radio_title_label.winfo_rooty() == title_y
        assert label.winfo_rooty() + label.winfo_height() <= title_y
        assert app.radio_now_playing_var.get() == "Radio: " + long_name.strip()
        # Every complete line follows the source at a word boundary.
        remaining = app.radio_now_playing_var.get()
        for line in lines[:-1]:
            assert remaining.startswith(line + " ")
            remaining = remaining[len(line) :].lstrip()
        radio._set_radio_station_text(app, "SenderOhneLeerzeichen" * 15)
        app.update()
        lines = label.cget("text").splitlines()
        assert len(lines) == 3 and lines[-1].endswith("…")
        assert all(font.measure(line) <= label.winfo_width() - 4 for line in lines)
    radio._set_radio_station_text(app, "")
    app.update()
    assert label.cget("text") == "Radio: aus"
    assert actions == []


def test_recording_cannot_cover_details_in_the_right_control_block(radio_pages):
    app, actions, _, _ = radio_pages
    record = app.radio_record_summary
    details = app.radio_player_details_button
    for width in (820, 720, 1100):
        app.winfo_toplevel().geometry(f"{width}x900")
        app.radio_record_status_var.set("Aufnahme läuft: " + "langer_dateiname_" * 12)
        app.update()
        for expanded in (False, True):
            if expanded:
                details.invoke()
                app.update()
            assert details.winfo_ismapped()
            assert record.winfo_rootx() + record.winfo_width() < details.winfo_rootx()
            title = app.radio_title_label
            logo = app.radio_logo_label
            assert title.winfo_rootx() == logo.winfo_rootx() == record.winfo_rootx()
            assert title.winfo_width() == record.winfo_width()
            assert title.winfo_rooty() >= logo.winfo_rooty() + logo.winfo_height()
            assert record.winfo_rooty() >= title.winfo_rooty() + title.winfo_height()
            assert (
                app.winfo_containing(
                    details.winfo_rootx() + details.winfo_width() // 2,
                    details.winfo_rooty() + details.winfo_height() // 2,
                )
                is details
            )
        details.invoke()
        app.update()
    assert actions == []


def test_fixed_favorite_selectors_keep_search_and_do_not_toggle_twice(radio_pages):
    app, actions, _, _ = radio_pages
    app.radio_favorites = [{"id": "one", "name": "Electronic One", "favicon": ""}]
    app.radio_search_var.set("Electronic")
    app.radio_favorite_selectors[True].invoke()
    app.update()
    assert app.radio_show_favorites_var.get()
    assert list(app.radio_favorite_tiles.cards) == ["one"]
    assert "selected" in app.radio_favorite_selectors[True].state()
    app.radio_favorite_selectors[True].invoke()
    assert app.radio_show_favorites_var.get()
    app.radio_favorite_selectors[False].invoke()
    assert not app.radio_show_favorites_var.get()
    assert app.radio_search_var.get() == ""
    assert actions == []


def test_manage_menu_reaches_all_existing_commands_and_disables_busy_check(
    radio_pages, menu_spies
):
    app, actions, _, _ = radio_pages
    for key in ("add", "import", "imports", "databases", "reachability"):
        app.radio_manage_menu.invoke(app.radio_manage_actions[key])
    assert menu_spies == ["add", "import", "imports", "databases", "reachability"]
    radio._set_radio_reachability_button_state(app, running=True)
    assert (
        app.radio_manage_menu.entrycget(app.radio_reachability_menu_index, "state")
        == "disabled"
    )
    app.radio_manage_menu.invoke(app.radio_reachability_menu_index)
    assert menu_spies.count("reachability") == 1
    radio._set_radio_reachability_button_state(app, running=False)
    assert (
        app.radio_manage_menu.entrycget(app.radio_reachability_menu_index, "state")
        == "normal"
    )
    assert actions == []


def test_visible_tile_actions_and_selected_station_menu_do_not_play(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    app.radio_favorites = [{"id": "one", "name": "Mein Sender", "favicon": ""}]
    app.set_radio_favorites_view(True)
    app.update()
    contexts = []
    monkeypatch.setattr(
        app,
        "_show_context_menu",
        lambda menu, event: contexts.append(app.radio_context_station_id),
    )
    card = app.radio_favorite_tiles.cards["one"]
    assert card.find_withtag("actions")
    card.event_generate("<ButtonRelease-1>", x=card.winfo_width() - 15, y=14)
    app.update()
    assert contexts == ["one"]
    app.radio_context_station_id = "stale-context"
    app.radio_manage_menu.invoke(app.radio_manage_actions["station"])
    assert contexts == ["one", "one"]
    assert actions == []


def test_inline_equalizer_keeps_values_and_uses_existing_commit(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    writes = []
    monkeypatch.setattr(radio, "save_radio_settings", lambda _app: writes.append(True))
    scales = [
        child
        for child in app.radio_inline_equalizer.winfo_children()
        if isinstance(child, ttk.Scale) and child is not app.radio_compact_volume
    ]
    assert len(scales) == 3
    assert all(slider.winfo_ismapped() for slider in scales)
    scales[0].set(4)
    app.update()
    assert app.radio_eq_bass_var.get() == 4
    assert writes == [] and actions == []
    scales[0].event_generate("<ButtonRelease-1>")
    app.update()
    assert writes == [True]
    app.open_radio_toolbox("visualizer")
    app.close_radio_toolbox()
    assert all(slider.winfo_ismapped() for slider in scales)
    assert app.radio_eq_bass_var.get() == 4


def test_visualizer_actions_and_collapsed_details_preserve_existing_routes(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    calls = []
    for method, key in (
        ("open_projectm_visualizer_test", "start"),
        ("close_projectm_visualizer_test", "stop"),
        ("open_projectm_preset_manager", "presets"),
        ("open_projectm_preset_folder", "folder"),
        ("install_projectm_visualizer", "install"),
    ):
        monkeypatch.setattr(app, method, lambda value=key: calls.append(value))
    app.radio_player_tool_buttons["visualizer"].invoke()
    app.update()
    assert not app.radio_toolbox_details.winfo_ismapped()
    assert calls == [] and actions == []
    for key in ("start", "stop", "presets", "folder", "install"):
        app.radio_toolbox_actions[key].invoke()
    assert calls == ["start", "stop", "presets", "folder", "install"]
    app.radio_toolbox_details_button.invoke()
    app.update()
    assert app.radio_toolbox_details.winfo_ismapped()
    app.radio_toolbox_details_button.invoke()
    app.update()
    assert not app.radio_toolbox_details.winfo_ismapped()


def test_control_buttons_reach_existing_actions(radio_pages, monkeypatch):
    app, actions, _, _ = radio_pages
    calls = []
    for method, key in (
        ("attach_radio_to_netmon", "attach"),
        ("detach_radio_from_netmon", "attach"),
        ("open_radio_record_settings_popup", "settings"),
    ):
        monkeypatch.setattr(app, method, lambda value=key: calls.append(value))
    app.close_radio_toolbox()
    app.update()
    assert "more" not in app.radio_player_tool_buttons
    assert vars(app).get("radio_player_details") is None
    button = app.radio_player_details_button
    transport = app.radio_transport_buttons["next"].master
    assert button.winfo_rootx() == transport.winfo_rootx()
    scales = [
        child
        for child in app.radio_inline_equalizer.winfo_children()
        if isinstance(child, ttk.Scale)
    ]
    assert button.winfo_rooty() >= max(
        scale.winfo_rooty() + scale.winfo_height() for scale in scales
    )
    settings = app.radio_record_settings_button
    assert settings.winfo_rootx() == button.winfo_rootx()
    assert settings.winfo_rooty() >= max(
        scale.winfo_rooty() + scale.winfo_height() for scale in scales
    )
    assert settings.winfo_rooty() + settings.winfo_height() <= button.winfo_rooty()
    host_action = (
        app.radio_detach_button if app.radio_embedded_mode else app.radio_attach_button
    )
    assert host_action.winfo_rooty() == button.winfo_rooty()
    assert host_action.winfo_rootx() >= button.winfo_rootx() + button.winfo_width()
    assert calls == [] and actions == []
    host_action.invoke()
    settings.invoke()
    assert calls == ["attach", "settings"]
    app.open_radio_toolbox("visualizer")
    assert app.radio_toolbox_kind == "visualizer"
    assert app.radio_output_setup_button is None
    assert app.radio_record_settings_button is settings
    assert settings.winfo_ismapped()
    assert host_action.winfo_ismapped()
    assert (
        app.radio_detach_button if app.radio_embedded_mode else app.radio_attach_button
    ) is host_action


def test_settings_audio_setup_sits_below_database_and_tracks_readiness(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    ready = {"value": False}
    calls = []
    monkeypatch.setattr(radio, "_radio_output_ready", lambda _app: ready["value"])
    monkeypatch.setattr(
        app, "manage_protected_radio_output", lambda: calls.append("setup")
    )
    popup = app.open_radio_record_settings_popup()
    app.update()
    setup = app.radio_output_setup_button
    body = setup.master
    refresh = next(
        child
        for child in body.winfo_children()
        if isinstance(child, ttk.Button)
        and child.cget("text")
        == app.tr("radio_settings_station_database", "Station database")
    )
    assert setup.winfo_rootx() == refresh.winfo_rootx()
    assert setup.winfo_rooty() >= refresh.winfo_rooty() + refresh.winfo_height()
    assert setup.cget("text") == app.tr("radio_output_button_setup", "Set up audio…")
    setup.invoke()
    assert calls == ["setup"]
    ready["value"] = True
    assert app.open_radio_record_settings_popup() is popup
    app.update()
    assert setup.cget("text") == app.tr("radio_output_button_ready", "✓ Set up audio…")
    assert setup.cget("text").startswith("✓")
    app.open_radio_toolbox("details")
    app.close_radio_toolbox()
    assert app.radio_output_setup_button is setup
    assert setup.winfo_exists()
    popup.tk.call(popup.protocol("WM_DELETE_WINDOW"))
    app.update()
    assert app.radio_output_setup_button is None
    ready["value"] = False
    popup = app.open_radio_record_settings_popup()
    app.update()
    assert not app.radio_output_setup_button.cget("text").startswith("✓")
    popup.tk.call(popup.protocol("WM_DELETE_WINDOW"))
    app.update()
    assert actions == []


def test_details_popup_keeps_main_layout_and_live_values(radio_pages):
    app, actions, _, _ = radio_pages
    button = app.radio_player_details_button
    title = button.cget("text")

    def layout():
        return (
            app.winfo_toplevel().geometry(),
            app.radio_player_controls.winfo_height(),
            app.radio_main_views["radio"].winfo_height(),
            button.winfo_rooty(),
        )

    original = layout()
    button.invoke()
    app.update()
    window = app.radio_toolbox_window
    assert app.radio_toolbox_kind == "details"
    assert window.winfo_exists()
    assert str(window.transient()) == str(app.winfo_toplevel())
    assert button.cget("text") == title
    assert layout() == original
    labels = app.radio_player_details.winfo_children()
    assert {str(label.cget("textvariable")) for label in labels} == {
        str(variable)
        for variable in (
            app.radio_source_var,
            app.radio_stream_url_var,
            app.radio_bitrate_var,
            app.radio_database_count_var,
            app.radio_attach_status_var,
        )
    }
    app.radio_bitrate_var.set("Bitrate: 320 kbps")
    app.update()
    assert "Bitrate: 320 kbps" in [label.cget("text") for label in labels]
    assert layout() == original
    window.focus_force()
    app.update()
    window.event_generate("<Escape>")
    app.update()
    assert not window.winfo_exists()
    assert app.radio_toolbox_window is None
    assert app.radio_player_details is None
    assert button.cget("text") == title
    button.invoke()
    app.update()
    window = app.radio_toolbox_window
    window.tk.call(window.protocol("WM_DELETE_WINDOW"))
    app.update()
    assert not window.winfo_exists()
    assert layout() == original
    assert actions == []


def test_transport_and_volume_still_use_the_existing_callbacks(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    calls = []
    for function, key in (
        ("play_previous_station", "previous"),
        ("play_current_radio_source", "play"),
        ("play_next_station", "next"),
    ):
        monkeypatch.setattr(
            radio, function, lambda *a, value=key, **kw: calls.append(value)
        )
    monkeypatch.setattr(app, "stop_radio_playback", lambda **kw: calls.append("stop"))
    monkeypatch.setattr(app, "start_radio_recording", lambda: calls.append("record"))
    for key in ("previous", "play", "record", "stop", "next"):
        app.radio_transport_buttons[key].invoke()
    assert calls == ["previous", "play", "record", "stop", "next"]
    for value in (0, 63, 100):
        app.radio_volume_var.set(value)
        app.on_radio_volume_preview()
        assert app.radio_volume_label_var.get() == f"{value}%"
    assert actions == []


def test_two_reserved_notice_lines_track_audio_setup_without_layout_changes(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    ready = {"value": False}
    monkeypatch.setattr(radio, "_radio_output_ready", lambda _app: ready["value"])
    for width in (1100, 820, 720):
        app.winfo_toplevel().geometry(f"{width}x900")
        radio._radio_output_hint(app)
        app.update()
        area = app.radio_notice_area
        label = app.radio_notice_label
        record = app.radio_record_summary
        navigation = app.radio_main_navigation
        assert len(app.radio_notice_var.get().splitlines()) == 2
        assert (
            "Ton einrichten" in app.radio_notice_var.get()
            or "Set up audio" in app.radio_notice_var.get()
        )
        assert area.winfo_rootx() == record.winfo_rootx()
        assert area.winfo_width() == record.winfo_width()
        assert area.winfo_rooty() >= record.winfo_rooty() + record.winfo_height()
        assert area.winfo_rooty() + area.winfo_height() <= navigation.winfo_rooty()
        assert (
            label.winfo_rootx() + label.winfo_width()
            < app.radio_player_control_block.winfo_rootx()
        )
        layout = (
            area.winfo_height(),
            navigation.winfo_rooty(),
            app.radio_player_controls.winfo_height(),
        )
        # The settings popup refreshes readiness, as it does after setup.
        ready["value"] = True
        popup = app.open_radio_record_settings_popup()
        app.update()
        assert app.radio_notice_var.get() == ""
        assert (
            area.winfo_height(),
            navigation.winfo_rooty(),
            app.radio_player_controls.winfo_height(),
        ) == layout
        assert app.radio_output_button_var.get().startswith("✓")
        popup.tk.call(popup.protocol("WM_DELETE_WINDOW"))
        app.update()
        ready["value"] = False
    assert actions == []
