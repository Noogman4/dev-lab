"""The host owns embedded colors; detached Radio cannot replace NetMon's theme."""

from copy import deepcopy
import json
import os
import types
from types import SimpleNamespace
import tkinter as tk
from tkinter import ttk

import pytest

from netmon import app as main, netmon_radio_app as ui
from netmon.features import radio_controller as radio


@pytest.fixture
def isolated_radio(monkeypatch):
    monkeypatch.setattr(ui, "prepare_user_files", lambda: None)
    monkeypatch.setattr(
        ui.netmon_projectm_sidecar, "ensure_projectm_preset_dir", lambda _app: None
    )
    for name in (
        "_refresh_projectm_status",
        "refresh_radio_attach_state",
        "stop_radio_recording",
        "stop_radio_playback",
        "close_projectm_visualizer_test",
        "_configure_compact_standalone_window",
    ):
        monkeypatch.setattr(ui.NetMonRadioApp, name, lambda *_a, **_k: None)
    for name in (
        "current_radio_transition_id",
        "consume_radio_handover",
        "complete_radio_transition",
        "set_radio_detached_state",
    ):
        monkeypatch.setattr(ui.netmon_radio_core, name, lambda *_a, **_k: None)
    monkeypatch.setattr(radio, "save_radio_settings", lambda _app: True)
    monkeypatch.setattr(radio, "load_radio_runtime", lambda _app: None)
    monkeypatch.setattr(radio, "update_radio_dependency_state", lambda _app: None)
    monkeypatch.setattr(
        radio,
        "play_radio_station",
        lambda *_a, **_k: pytest.fail("Playback is outside the theme test"),
    )


def incoming():
    return {
        "theme": "dark",
        "theme_palette": dict(ui.DARK_THEME),
        "volume": 37,
        "eq_bass": 3,
        "current_station_id": "test",
        "current_station": {
            "id": "test",
            "name": "Test Station",
            "url": "https://example.invalid/live",
        },
        "was_playing": False,
        "last_search": "Jazz",
    }


@pytest.mark.parametrize(
    "palette",
    [
        ui.LIGHT_THEME,
        ui.BEIGE_THEME,
        {**ui.POP_THEME, "panel_bg": "#f0e0f1", "accent": "#123456"},
    ],
)
@pytest.mark.parametrize("has_payload", [False, True])
@pytest.mark.parametrize("has_panel", [False, True])
def test_real_reattach_keeps_main_settings_and_palette(
    monkeypatch, tmp_path, palette, has_payload, has_panel
):
    palette = deepcopy(palette)
    persisted = tmp_path / "config.json"
    settings = {"theme": palette["name"], "unrelated": "keep"}
    persisted.write_text(json.dumps(settings))
    radio_path = tmp_path / "radio_settings.json"
    radio_path.write_text(json.dumps({"theme": "dark", "volume": 37}))
    main_theme_calls = []
    panel_calls = []
    panel = (
        SimpleNamespace(radio_settings=radio.default_radio_settings())
        if has_panel
        else None
    )
    if panel is not None:
        panel.apply_theme_palette = lambda name, colors: panel_calls.append(
            (name, colors)
        )
    host = SimpleNamespace(
        _app_theme=deepcopy(palette),
        settings=deepcopy(settings),
        radio_settings={},
        radio_settings_path=str(radio_path),
        radio_embedded_panel=panel,
        _record_diagnostic_action=lambda *_a, **_k: None,
        _log_radio_theme_diagnostic=lambda *_a: None,
        _normalize_theme_name=lambda name: name,
        _get_theme_display_name=lambda name: name,
        apply_theme=lambda *a, **k: main_theme_calls.append(a),
        save_settings=lambda: persisted.write_text(json.dumps(host.settings)),
        tr=lambda _key, fallback: fallback,
    )
    host._sync_radio_theme_to_current_theme = (
        lambda: main.App._sync_radio_theme_to_current_theme(host)
    )
    monkeypatch.setattr(
        main.netmon_radio_core, "standalone_radio_is_running", lambda: False
    )
    monkeypatch.setattr(
        main.netmon_radio_core, "complete_radio_transition", lambda **_k: None
    )
    monkeypatch.setattr(
        main.netmon_radio_core, "set_radio_detached_state", lambda *_a: None
    )
    monkeypatch.setattr(radio, "open_radio_tab", lambda _app: None)
    monkeypatch.setattr(radio, "save_radio_settings", lambda _app: True)
    monkeypatch.setattr(radio, "refresh_radio_ui", lambda _app: None)
    monkeypatch.setattr(radio, "on_radio_volume_preview", lambda _app: None)
    monkeypatch.setattr(radio, "on_radio_eq_preview", lambda _app: None)
    payload = incoming() if has_payload else None
    original_payload = deepcopy(payload)
    assert main.App.reattach_radio_app(host, handover_payload=payload)
    assert host._app_theme == palette
    assert host.settings == settings
    assert json.loads(persisted.read_text()) == settings
    assert main_theme_calls == []
    assert host.radio_settings["theme"] == palette["name"]
    if panel is not None:
        assert panel.radio_settings["theme"] == palette["name"]
        assert panel_calls and all(
            name == palette["name"] and colors == palette
            for name, colors in panel_calls
        )
    assert payload == original_payload
    if has_payload:
        target = panel or host
        assert target.radio_current_station_id == "test"
        assert target.radio_settings["volume"] == 37
        assert target.radio_settings["eq_bass"] == 3
        assert target.radio_settings["last_search"] == "Jazz"


@pytest.mark.parametrize(
    "palette",
    [
        ui.LIGHT_THEME,
        ui.BEIGE_THEME,
        {**ui.POP_THEME, "panel_bg": "#f0e0f1", "accent": "#123456"},
    ],
)
def test_panel_creation_and_dark_handover_keep_host_custom_colors(
    isolated_radio, palette
):
    root = tk.Tk()
    palette = deepcopy(palette)
    host = SimpleNamespace(
        _app_theme=deepcopy(palette), settings={"theme": palette["name"]}
    )
    try:
        root.geometry("1100x900")
        panel = ui.NetMonRadioPanel(root, host_app=host)
        panel.pack(fill="both", expand=True)
        outside_label = ttk.Label(root, text="NetMon behält sein Theme")
        outside_label.pack()
        root.update()
        assert panel._app_theme == palette
        assert panel.style.lookup("TFrame", "background") == palette["panel_bg"]
        assert radio.apply_radio_handover_payload(panel, incoming())
        root.update()
        assert panel._app_theme == palette
        assert host._app_theme == palette
        assert host.settings == {"theme": palette["name"]}
        assert panel.style.lookup("TLabel", "background") == palette["panel_bg"]
        assert panel.style.lookup("TButton", "background") == palette["tab_bg"]
        assert panel.radio_volume_var.get() == 37
        if os.environ.get("NETMON_TEST_ISOLATED") == "1":
            from PIL import ImageGrab

            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
                f"/work/embedded-theme-{palette['name']}.png"
            )
        panel.destroy()
    finally:
        root.destroy()


def test_standalone_stays_dark_despite_host_light_handover(isolated_radio, monkeypatch):
    monkeypatch.setattr(
        ui.netmon_radio_core,
        "consume_radio_handover",
        lambda *_a, **_k: {
            **incoming(),
            "theme": "light",
            "theme_palette": dict(ui.LIGHT_THEME),
        },
    )
    app = ui.NetMonRadioApp(start_theme="light")
    try:
        app.update()
        assert app._app_theme == ui.DARK_THEME
        assert app.radio_settings["theme"] == "dark"
    finally:
        app.destroy()


def theme_host():
    """Use real host theme methods, without starting host integrations."""
    root = tk.Tk()
    root.style = ttk.Style(root)
    root._app_theme = None
    root._theme_toggle_btn = None
    root.settings = {
        "theme": "pop",
        "theme_custom_panel_bg": "#201a29",
        "theme_custom_accent": "#5691bd",
    }
    root.radio_settings = {}
    for name in (
        "apply_theme",
        "_get_theme",
        "_compose_theme",
        "_normalize_theme_name",
        "_normalize_theme_studio_style",
        "_apply_ttk_theme",
        "_ensure_colorable_ttk_theme",
        "_apply_tk_widget_theme",
        "_sync_radio_theme_to_current_theme",
    ):
        setattr(root, name, types.MethodType(getattr(main.App, name), root))
    for name in (
        "_apply_log_theme",
        "_apply_chad_chat_theme",
        "refresh_theme_studio_preview",
        "_apply_dependency_installer_theme",
        "_log_radio_theme_diagnostic",
    ):
        setattr(root, name, lambda *_a, **_k: None)
    return root


@pytest.mark.parametrize("initial", [None, "light", "pop"])
@pytest.mark.parametrize("target", ["light", "dark", "beige", "pop"])
def test_final_host_theme_recolors_existing_panel_at_startup_and_on_theme_change(
    isolated_radio,
    initial,
    target,
):
    root = theme_host()
    try:
        root.geometry("1100x900")
        if initial:
            root.apply_theme(initial, log_change=False, persist=False)
        panel = ui.NetMonRadioPanel(root, host_app=root)
        root.radio_embedded_panel = panel
        panel.pack(fill="both", expand=True)
        outside = ttk.Button(root, text="NetMon")
        outside.pack()
        root.apply_theme(target, log_change=False, persist=False)
        root.update()
        palette = root._app_theme
        for key in ui.RADIO_THEME_PALETTE_KEYS:
            assert panel._app_theme[key] == palette[key], key
        assert (
            panel.style.lookup("RadioView.TButton", "background") == palette["tab_bg"]
        )
        assert (
            panel.style.lookup("RadioView.TButton", "background", ("selected",))
            == palette["select_bg"]
        )
        assert (
            panel.style.lookup("RadioManage.TMenubutton", "background")
            == palette["tab_bg"]
        )
        assert (
            panel.style.lookup("RadioPanel.TLabelframe", "background")
            == palette["panel_bg"]
        )
        assert (
            panel.style.lookup("RadioMuted.TLabel", "background") == palette["panel_bg"]
        )
        assert panel.style.lookup("TButton", "background") == palette["tab_bg"]
        assert panel.radio_settings["theme"] == target
        # Handover must continue to follow the now-final host theme.
        assert radio.apply_radio_handover_payload(panel, incoming())
        assert root._app_theme == palette
        for key in ui.RADIO_THEME_PALETTE_KEYS:
            assert panel._app_theme[key] == palette[key], key
        if os.environ.get("NETMON_TEST_ISOLATED") == "1" and initial is None:
            from PIL import ImageGrab

            ImageGrab.grab(xdisplay=os.environ["DISPLAY"]).save(
                f"/work/startup-host-{target}.png"
            )
    finally:
        root.destroy()
