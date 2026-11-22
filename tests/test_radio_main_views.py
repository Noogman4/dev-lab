"""Actual radio pages with private fixtures and no playback or network actions."""

import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace

import pytest

from netmon import netmon_radio_app as ui
from netmon.features import radio_controller as radio
from netmon.ui.tabs import radio_tab


@pytest.fixture(params=["standalone", "embedded"])
def radio_pages(request, monkeypatch, tmp_path):
    monkeypatch.setattr(ui, "prepare_user_files", lambda: None)
    monkeypatch.setattr(
        ui.netmon_projectm_sidecar, "ensure_projectm_preset_dir", lambda app: None
    )
    for name in (
        "_refresh_projectm_status",
        "refresh_radio_attach_state",
        "stop_radio_recording",
        "stop_radio_playback",
        "close_projectm_visualizer_test",
        "_configure_compact_standalone_window",
    ):
        monkeypatch.setattr(ui.NetMonRadioApp, name, lambda *args, **kwargs: None)
    for name in (
        "current_radio_transition_id",
        "consume_radio_handover",
        "complete_radio_transition",
        "set_radio_detached_state",
    ):
        monkeypatch.setattr(ui.netmon_radio_core, name, lambda *args, **kwargs: None)
    monkeypatch.setattr(radio, "save_radio_settings", lambda app: True)
    monkeypatch.setattr(radio, "update_radio_dependency_state", lambda app: None)
    monkeypatch.setattr(radio, "load_radio_runtime", lambda app: None)
    actions = []
    monkeypatch.setattr(
        radio, "play_radio_station", lambda *args, **kwargs: actions.append("radio")
    )
    monkeypatch.setattr(
        radio, "_play_local_audio_file", lambda *args, **kwargs: actions.append("file")
    )
    root = None
    if request.param == "standalone":
        app = ui.NetMonRadioApp()
        app.geometry("1100x900")
    else:
        root = tk.Tk()
        root.geometry("1100x900")
        app = ui.NetMonRadioPanel(root)
        app.pack(fill="both", expand=True)
    media, recordings = tmp_path / "media", tmp_path / "recordings"
    media.mkdir()
    recordings.mkdir()
    (media / "test.mp3").write_bytes(b"synthetic fixture")
    (recordings / "recording.mp3").write_bytes(b"synthetic fixture")
    app.radio_recordings_dir = str(recordings)
    app.radio_system_folder_path = str(media)
    app.update()
    yield app, actions, media, recordings
    app.destroy()
    if root is not None:
        root.destroy()


def test_one_main_area_and_navigation_without_sashes_or_playback(radio_pages):
    app, actions, media, recordings = radio_pages
    assert app.radio_main_pane is None and app.radio_media_pane is None

    def descendants(widget):
        return [
            child
            for parent in widget.winfo_children()
            for child in [parent, *descendants(parent)]
        ]

    assert not any(child.winfo_class() == "TPanedwindow" for child in descendants(app))
    assert set(app.radio_main_view_buttons) == {
        "radio",
        "media",
        "recordings",
        "playlist",
    }
    for view, directory in (
        ("media", media),
        ("recordings", recordings),
        ("playlist", None),
        ("radio", None),
    ):
        app.radio_main_view_buttons[view].invoke()
        app.update()
        assert app.radio_main_view == view
        page = app.radio_main_views[view]
        assert page.winfo_ismapped()
        assert len(page.master.grid_slaves()) == 1
        assert page.winfo_height() == page.master.winfo_height()
        assert "selected" in app.radio_main_view_buttons[view].state()
        if directory:
            assert app.radio_folder_browser_current_path == str(directory)
            assert app.radio_recordings_listbox.size() == 1
            assert app.radio_playlist_add_button is None
            assert app.radio_playlist_folder_button is None
            button = app.radio_system_folder_button
            assert bool(button.winfo_ismapped()) == (view == "media")
            if view == "media":
                assert (
                    button.winfo_rootx()
                    == app.radio_folder_source_buttons.winfo_rootx()
                )
            assert app.radio_folder_browser_header.winfo_ismapped()
    if app._scroll_canvas is not None:
        assert app._scroll_canvas.bbox("all")[3] <= app._scroll_canvas.winfo_height()
    assert actions == []


def test_recordings_hide_metadata_but_preserve_audio_and_subfolder_navigation(
    radio_pages,
):
    app, actions, _, recordings = radio_pages
    metadata = recordings / "recording.json"
    original = '{"titles": [{"title": "Künstler – Titel"}]}'
    metadata.write_text(original)
    (recordings / "another.JSON").write_text("{}")
    (recordings / "notes.txt").write_text("private notes")
    audio = recordings / "another.ogg"
    audio.write_bytes(b"synthetic audio")
    folder = recordings / "album"
    folder.mkdir()
    nested_audio = folder / "inside.MP3"
    nested_audio.write_bytes(b"synthetic audio")
    (folder / "inside.json").write_text("{}")
    app.show_radio_main_view("recordings")
    app.update()
    assert set(app.radio_recordings_entries) == {
        str(folder),
        str(audio),
        str(recordings / "recording.mp3"),
    }
    assert app.radio_recordings_listbox.size() == 3
    app.radio_recordings_listbox.selection_set(0)
    app.open_selected_radio_folder_browser_entry()
    app.update()
    assert app.radio_folder_browser_current_path == str(folder)
    assert app.radio_recordings_entries == [str(nested_audio)]
    app.navigate_radio_folder_browser_back()
    assert len(app.radio_recordings_entries) == 3
    assert metadata.read_text() == original
    assert (folder / "inside.json").read_text() == "{}"
    assert actions == []


def test_cancel_media_folder_selection_preserves_current_view(radio_pages, monkeypatch):
    app, actions, _, _ = radio_pages
    app.radio_system_folder_path = ""
    monkeypatch.setattr(radio.filedialog, "askdirectory", lambda **kwargs: "")
    app.show_radio_main_view("playlist")
    app.radio_main_view_buttons["media"].invoke()
    app.update()
    assert app.radio_main_view == "playlist"
    assert app.radio_main_views["playlist"].winfo_ismapped()
    assert "selected" in app.radio_main_view_buttons["playlist"].state()
    assert actions == []


def test_subfolders_and_back_navigation_remember_the_matching_main_view(radio_pages):
    app, actions, media, recordings = radio_pages
    album = media / "album"
    album.mkdir()
    app.show_radio_main_view("media")
    app.radio_recordings_listbox.selection_set(0)
    app.open_selected_radio_folder_browser_entry()
    assert app.radio_folder_browser_current_path == str(album)
    app.show_radio_main_view("recordings")
    assert app.radio_folder_browser_current_path == str(recordings)
    app.show_radio_main_view("media")
    assert app.radio_folder_browser_current_path == str(album)
    app.navigate_radio_folder_browser_back()
    assert app.radio_main_view == "recordings"
    app.navigate_radio_folder_browser_forward()
    assert app.radio_main_view == "media"
    assert actions == []


def test_hidden_favorite_logos_stay_inactive_until_return_to_radio(radio_pages):
    app, actions, _, _ = radio_pages
    app.radio_favorites = [{"id": "favorite", "name": "Mein Sender", "favicon": ""}]
    app.toggle_radio_favorites_view()
    app.show_radio_main_view("playlist")
    radio.refresh_radio_station_table(app)
    assert app.radio_favorite_tiles.stop.is_set()
    app.show_radio_main_view("radio")
    app.update()
    assert not app.radio_show_favorites_var.get()
    assert app.radio_station_table.winfo_ismapped()
    assert not app.radio_favorite_tiles.winfo_ismapped()
    app.radio_favorite_selectors[True].invoke()
    app.update()
    assert app.radio_favorite_tiles.winfo_ismapped()
    assert list(app.radio_favorite_tiles.cards) == ["favorite"]
    assert actions == []


def test_radio_host_scaffold_has_no_bottom_pane():
    root = tk.Tk()
    try:
        root.geometry("900x700")
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)
        app = SimpleNamespace(tools_nb=notebook, tr=lambda key, fallback: fallback)
        host, show_bottom = radio_tab._build_radio_tab_scaffold(app)
        root.update()
        assert app.radio_tab_pane is None
        assert app.radio_tab_pane_marker is None
        assert host.winfo_height() > 600
        assert app.radio_tab_bottom_section is host
        show_bottom()
        assert host.winfo_children() == []
    finally:
        root.destroy()


def test_settings_database_button_closes_settings_before_opening_database(
    radio_pages, monkeypatch
):
    app, actions, _, _ = radio_pages
    settings = app.open_radio_record_settings_popup()
    app.update()
    calls = []

    def check_sources():
        assert not settings.winfo_exists()
        assert app.radio_record_settings_window is None
        assert app.radio_output_setup_button is None
        calls.append("sources")

    monkeypatch.setattr(app, "check_radio_database_source_reachability", check_sources)
    monkeypatch.setattr(
        app, "download_radio_db", lambda: pytest.fail("Unexpected database download")
    )
    button = next(
        child
        for child in app.radio_output_setup_button.master.winfo_children()
        if isinstance(child, ttk.Button)
        and child.cget("text")
        == app.tr("radio_settings_station_database", "Station database")
    )
    button.invoke()
    app.update()
    database = app.radio_database_sources_window
    assert database.winfo_exists() and database.winfo_ismapped()
    assert str(database.transient()) == str(app.winfo_toplevel())
    assert calls == ["sources"]
    # Opening settings again still reuses the existing database window.
    settings = app.open_radio_record_settings_popup()
    app.update()
    button = next(
        child
        for child in app.radio_output_setup_button.master.winfo_children()
        if isinstance(child, ttk.Button)
        and child.cget("text")
        == app.tr("radio_settings_station_database", "Station database")
    )
    button.invoke()
    app.update()
    assert not settings.winfo_exists()
    assert app.radio_record_settings_window is None
    assert app.radio_output_setup_button is None
    assert app.radio_database_sources_window is database
    assert calls == ["sources"]
    database.tk.call(database.protocol("WM_DELETE_WINDOW"))
    app.update()
    assert app.radio_database_sources_window is None
    assert actions == []


@pytest.mark.parametrize(
    "view,opener", [("table", "right"), ("favorites", "right"), ("favorites", "dots")]
)
def test_native_context_menu_stays_open_after_opening_click_at_screen_bottom(
    radio_pages, view, opener
):
    app, actions, _, _ = radio_pages
    app.winfo_toplevel().geometry("1100x1000+0+0")
    stations = [
        {
            "id": f"row-{i:02}",
            "name": f"Sender {i:02}",
            "url": "https://example.invalid/live",
            "favicon": "",
        }
        for i in range(50)
    ]
    app.radio_db = stations
    app.radio_favorites = stations
    app.radio_search_var.set("Sender")
    app.set_radio_favorites_view(view == "favorites")
    radio.refresh_radio_station_table(app, reset_page=True)
    app.update()
    if view == "table":
        target = app.radio_station_table
        target.see("row-49")
        app.update()
        _, y, _, height = target.bbox("row-49")
        x, y = 100, y + height // 2
    else:
        tiles = app.radio_favorite_tiles
        tiles.canvas.yview_moveto(1)
        app.update()
        target = tiles.cards["row-49"]
        x = target.winfo_width() - 15 if opener == "dots" else 35
        y = 14
    menu = app.radio_station_menu
    invoked = []
    for index in range(menu.index("end") + 1):
        if menu.type(index) == "command":
            menu.entryconfigure(index, command=lambda i=index: invoked.append(i))
    button = 1 if opener == "dots" else 3
    target.event_generate("<Motion>", x=x, y=y, warp=True)
    target.event_generate(f"<ButtonPress-{button}>", x=x, y=y)
    app.update()
    assert not menu.winfo_ismapped()
    # Small pointer movement is normal between pressing and releasing a button.
    target.event_generate(
        "<Motion>", x=x + 5, y=y, state=256 if button == 1 else 1024, warp=True
    )
    target.event_generate(f"<ButtonRelease-{button}>", x=x + 5, y=y)
    app.update()
    assert menu.winfo_ismapped()
    assert menu.winfo_rooty() < target.winfo_rooty() + y
    assert app.radio_context_station_id == "row-49"
    assert invoked == [] and actions == []
    # A deliberate menu click still works normally.
    choice = next(
        i
        for i in range(menu.index("end") + 1)
        if menu.type(i) == "command"
        and menu.entrycget(i, "label")
        == app.tr("radio_menu_copy_url", "Copy stream URL")
    )
    item_y = menu.yposition(choice) + 5
    menu.event_generate("<Motion>", x=15, y=item_y, warp=True)
    menu.event_generate("<ButtonPress-1>", x=15, y=item_y)
    menu.event_generate("<ButtonRelease-1>", x=15, y=item_y)
    app.update()
    assert invoked == [choice] and not menu.winfo_ismapped()
    for dismiss in ("escape", "outside"):
        target.event_generate("<Motion>", x=x, y=y, warp=True)
        target.event_generate(f"<ButtonPress-{button}>", x=x, y=y)
        target.event_generate(f"<ButtonRelease-{button}>", x=x, y=y)
        app.update()
        assert menu.winfo_ismapped()
        if dismiss == "escape":
            menu.event_generate("<Escape>")
        else:
            app.radio_title_label.event_generate("<ButtonPress-1>", x=3, y=3)
        app.update()
        assert not menu.winfo_ismapped()
        assert invoked == [choice]
    assert actions == []
