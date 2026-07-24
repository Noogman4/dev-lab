import pytest

from netmon.ui.tabs import radio_tab


def test_safe_translate_uses_fallback_without_translator():
    assert radio_tab._safe_translate(object(), "missing", "fallback") == "fallback"


def test_safe_translate_uses_translation_and_handles_failures():
    class DummyApp:
        def tr(self, key, fallback):
            if key == "broken":
                raise RuntimeError("boom")
            return f"translated:{key}"

    app = DummyApp()

    assert radio_tab._safe_translate(app, "ok", "fallback") == "translated:ok"
    assert radio_tab._safe_translate(app, "broken", "fallback") == "fallback"


def test_radio_launcher_status_var_reuses_existing_var():
    existing = object()
    app = type("DummyApp", (), {})()
    app.radio_launcher_status_var = existing

    assert radio_tab._radio_launcher_status_var(app) is existing


def test_radio_launcher_status_var_creates_empty_var_with_factory():
    created = []

    class DummyVar:
        def __init__(self, value=""):
            self.value = value
            created.append(self)

    app = type("DummyApp", (), {})()

    var = radio_tab._radio_launcher_status_var(app, var_factory=DummyVar)

    assert var is created[0]
    assert var.value == ""


def test_init_radio_tab_state_sets_host_sections_and_launcher_defaults():
    app = type("DummyApp", (), {})()
    app.radio_embedded_panel = object()
    app.radio_launcher_mode = "detached"
    host = object()
    top_section = object()
    bottom_section = object()

    radio_tab._init_radio_tab_state(
        app,
        host=host,
        top_section=top_section,
        bottom_section=bottom_section,
    )

    assert app.radio_tab_host is host
    assert app.radio_tab_top_section is top_section
    assert app.radio_tab_bottom_section is bottom_section
    assert app.radio_embedded_panel is None
    assert app.radio_launcher_mode == ""


def test_radio_launcher_status_text_covers_known_states():
    assert (
        radio_tab._radio_launcher_status_text(
            detached=False,
            launcher_state="detaching",
        )
        == "Radio wird gerade als Standalone-App gestartet."
    )
    assert (
        radio_tab._radio_launcher_status_text(
            detached=False,
            launcher_state="attaching",
        )
        == "Radio wird gerade wieder an NetMon angeheftet."
    )
    assert (
        radio_tab._radio_launcher_status_text(
            detached=True,
            launcher_state="",
        )
        == "Radio-App ist geloest und laeuft als Standalone weiter."
    )
    assert (
        radio_tab._radio_launcher_status_text(
            detached=False,
            launcher_state="",
        )
        == "Radio-App ist an NetMon angeheftet."
    )


def test_radio_detached_placeholder_texts_use_fallbacks():
    assert radio_tab._radio_detached_placeholder_texts() == (
        "NetMon Radio als externe App",
        "Radio laeuft gerade standalone. Zum Wieder-Anheften bitte in der externen Radio-App auf 'Radio anheften' klicken.",
        "Radio anheften",
    )


def test_radio_detached_placeholder_texts_use_translations_and_handle_failures():
    class DummyApp:
        def tr(self, key, fallback):
            if key == "radio_launcher_detached_hint":
                raise RuntimeError("boom")
            return f"translated:{key}"

    assert radio_tab._radio_detached_placeholder_texts(DummyApp()) == (
        "translated:radio_launcher_title",
        "Radio laeuft gerade standalone. Zum Wieder-Anheften bitte in der externen Radio-App auf 'Radio anheften' klicken.",
        "translated:radio_launcher_reattach",
    )


def test_radio_bottom_placeholder_text_uses_app_translation():
    calls = []

    class DummyApp:
        def tr(self, key, fallback):
            calls.append((key, fallback))
            return f"translated:{key}"

    assert (
        radio_tab._radio_bottom_placeholder_text(DummyApp())
        == "translated:radio_bottom_media_hint"
    )
    assert calls == [
        (
            "radio_bottom_media_hint",
            "This lower area is reserved for playlists and files.",
        )
    ]


def test_radio_bottom_section_title_uses_app_translation():
    calls = []

    class DummyApp:
        def tr(self, key, fallback):
            calls.append((key, fallback))
            return f"translated:{key}"

    assert (
        radio_tab._radio_bottom_section_title(DummyApp())
        == "translated:radio_bottom_media_title"
    )
    assert calls == [("radio_bottom_media_title", "Playlists and files")]


def test_detach_radio_from_tab_delegates_to_app():
    calls = []

    class DummyApp:
        def open_radio_external_app(self):
            calls.append("open")
            return "opened"

    assert radio_tab._detach_radio_from_tab(DummyApp()) == "opened"
    assert calls == ["open"]


def test_attach_embedded_radio_panel_grids_panel_and_sets_app_state():
    events = []

    class DummyPanel:
        def grid(self, **kwargs):
            events.append(("grid", kwargs))

    class DummyHost:
        def rowconfigure(self, row, weight=0):
            events.append(("rowconfigure", row, weight))

    app = type("DummyApp", (), {})()
    host = DummyHost()
    panel = DummyPanel()

    radio_tab._attach_embedded_radio_panel(app, host, panel)

    assert events == [
        ("grid", {"row": 0, "column": 0, "sticky": "nsew"}),
        ("rowconfigure", 0, 1),
    ]
    assert app.radio_embedded_panel is panel
    assert app.radio_launcher_mode == "embedded"


def test_set_detached_radio_placeholder_state_registers_button_and_mode():
    calls = []

    class DummyApp:
        def register_feature_button(self, feature, button):
            calls.append((feature, button))

    app = DummyApp()
    button = object()

    radio_tab._set_detached_radio_placeholder_state(app, button)

    assert calls == [("radio", button)]
    assert app.radio_launcher_mode == "detached"


def test_configure_single_cell_expand_sets_column_and_row_weight():
    calls = []

    class DummyWidget:
        def columnconfigure(self, column, weight=0):
            calls.append(("column", column, weight))

        def rowconfigure(self, row, weight=0):
            calls.append(("row", row, weight))

    radio_tab._configure_single_cell_expand(DummyWidget())

    assert calls == [("column", 0, 1), ("row", 0, 1)]


def test_build_radio_tab_body_creates_tab_adds_notebook_and_body():
    events = []

    class DummyNotebook:
        def add(self, tab, text=None):
            events.append(("add", tab, text))

    class DummyApp:
        def __init__(self):
            self.tools_nb = DummyNotebook()

        def tr(self, key, fallback):
            events.append(("tr", key, fallback))
            return "translated tab"

    class DummyFrame:
        def __init__(self, parent, **kwargs):
            self.parent = parent
            self.kwargs = kwargs
            events.append(("frame", parent, kwargs, self))

        def pack(self, **kwargs):
            events.append(("pack", self, kwargs))

        def columnconfigure(self, column, weight=0):
            events.append(("column", self, column, weight))

        def rowconfigure(self, row, weight=0):
            events.append(("row", self, row, weight))

    app = DummyApp()

    body = radio_tab._build_radio_tab_body(app, frame_factory=DummyFrame)

    assert app.tab_radio is events[0][3]
    assert body is events[3][3]
    assert events == [
        ("frame", app.tools_nb, {"padding": (2, 0, 2, 2)}, app.tab_radio),
        ("tr", "tools_tab_radio", "Radio"),
        ("add", app.tab_radio, "translated tab"),
        ("frame", app.tab_radio, {"padding": 0}, body),
        ("pack", body, {"fill": "both", "expand": True}),
        ("column", body, 0, 1),
        ("row", body, 0, 1),
    ]


def test_build_radio_tab_body_returns_body_frame():
    class DummyNotebook:
        def add(self, tab, text=None):
            pass

    class DummyApp:
        def __init__(self):
            self.tools_nb = DummyNotebook()

        def tr(self, key, fallback):
            return fallback

    class DummyFrame:
        def __init__(self, parent, **kwargs):
            pass

        def pack(self, **kwargs):
            pass

        def columnconfigure(self, column, weight=0):
            pass

        def rowconfigure(self, row, weight=0):
            pass

    app = DummyApp()

    body = radio_tab._build_radio_tab_body(app, frame_factory=DummyFrame)

    assert isinstance(body, DummyFrame)


def test_build_radio_pane_sections_creates_top_host_and_bottom():
    events = []
    pane = object()

    class DummyApp:
        def tr(self, key, fallback):
            events.append(("tr", key, fallback))
            return "translated title"

    class DummyWidget:
        def __init__(self, parent, **kwargs):
            self.parent = parent
            self.kwargs = kwargs

        def columnconfigure(self, column, weight=0):
            events.append(("column", self, column, weight))

        def rowconfigure(self, row, weight=0):
            events.append(("row", self, row, weight))

        def grid(self, **kwargs):
            events.append(("grid", self, kwargs))

    class DummyFrame(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("frame", parent, kwargs, self))

    class DummyLabelFrame(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("label_frame", parent, kwargs, self))

    top_section, host, bottom_section = radio_tab._build_radio_pane_sections(
        pane,
        DummyApp(),
        frame_factory=DummyFrame,
        label_frame_factory=DummyLabelFrame,
    )

    assert events == [
        ("frame", pane, {"padding": 0}, top_section),
        ("column", top_section, 0, 1),
        ("row", top_section, 0, 1),
        ("frame", top_section, {}, host),
        ("grid", host, {"row": 0, "column": 0, "sticky": "nsew"}),
        ("column", host, 0, 1),
        ("row", host, 0, 1),
        ("tr", "radio_bottom_media_title", "Playlists and files"),
        (
            "label_frame",
            pane,
            {"text": "translated title", "padding": 10},
            bottom_section,
        ),
        ("column", bottom_section, 0, 1),
        ("row", bottom_section, 0, 1),
    ]


def test_build_radio_pane_sections_returns_distinct_widgets():
    class DummyApp:
        def tr(self, key, fallback):
            return fallback

    class DummyWidget:
        def __init__(self, parent, **kwargs):
            pass

        def columnconfigure(self, column, weight=0):
            pass

        def rowconfigure(self, row, weight=0):
            pass

        def grid(self, **kwargs):
            pass

    top_section, host, bottom_section = radio_tab._build_radio_pane_sections(
        object(),
        DummyApp(),
        frame_factory=DummyWidget,
        label_frame_factory=DummyWidget,
    )

    assert top_section is not host
    assert top_section is not bottom_section
    assert host is not bottom_section


def test_add_radio_pane_sections_adds_top_and_bottom_with_weights():
    calls = []
    top_section = object()
    bottom_section = object()

    class DummyPane:
        def add(self, section, weight=0):
            calls.append((section, weight))

    radio_tab._add_radio_pane_sections(DummyPane(), top_section, bottom_section)

    assert calls == [
        (top_section, 3),
        (bottom_section, 2),
    ]


def test_build_radio_tab_pane_creates_pane_marker_and_app_state():
    calls = []
    body = object()
    marker = object()

    class DummyPane:
        def __init__(self, parent, **kwargs):
            calls.append(("pane", parent, kwargs))

        def grid(self, **kwargs):
            calls.append(("grid", self, kwargs))

    def marker_installer(marker_body, pane):
        calls.append(("marker", marker_body, pane))
        return marker

    app = type("DummyApp", (), {})()

    pane = radio_tab._build_radio_tab_pane(
        app,
        body,
        panedwindow_factory=DummyPane,
        marker_installer=marker_installer,
    )

    assert app.radio_tab_pane is pane
    assert app.radio_tab_pane_marker is marker
    assert calls == [
        ("pane", body, {"orient": "vertical"}),
        ("grid", pane, {"row": 0, "column": 0, "sticky": "nsew"}),
        ("marker", body, pane),
    ]


def test_build_radio_tab_pane_returns_created_pane():
    class DummyPane:
        def __init__(self, parent, **kwargs):
            pass

        def grid(self, **kwargs):
            pass

    app = type("DummyApp", (), {})()

    pane = radio_tab._build_radio_tab_pane(
        app,
        object(),
        panedwindow_factory=DummyPane,
        marker_installer=lambda body, pane: object(),
    )

    assert pane is app.radio_tab_pane


def test_radio_pane_marker_geometry_centers_and_clamps_marker():
    assert radio_tab._radio_pane_marker_geometry(800, 240) == {
        "x": 367,
        "y": 235,
        "width": 66,
        "height": 12,
    }
    assert radio_tab._radio_pane_marker_geometry(40, 4) == {
        "x": 8,
        "y": 2,
        "width": 42,
        "height": 12,
    }


def test_radio_pane_marker_width_clamps_between_min_and_max():
    assert radio_tab._radio_pane_marker_width(800) == 66
    assert radio_tab._radio_pane_marker_width(90) == 66
    assert radio_tab._radio_pane_marker_width(40) == 42
    assert radio_tab._radio_pane_marker_width(None) == 42


def test_radio_pane_marker_x_centers_and_clamps_left_padding():
    assert radio_tab._radio_pane_marker_x(800, 66) == 367
    assert radio_tab._radio_pane_marker_x(40, 42) == 8


def test_radio_pane_marker_y_offsets_and_clamps_top_padding():
    assert radio_tab._radio_pane_marker_y(240) == 235
    assert radio_tab._radio_pane_marker_y(4) == 2


def test_radio_pane_marker_height_returns_fixed_drag_target_height():
    assert radio_tab._radio_pane_marker_height() == 12


def test_radio_pane_marker_place_geometry_builds_int_place_kwargs():
    assert radio_tab._radio_pane_marker_place_geometry("1", 2, "3", 4) == {
        "x": 1,
        "y": 2,
        "width": 3,
        "height": 4,
    }


def test_set_radio_pane_sash_position_uses_sashpos():
    calls = []

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    radio_tab._set_radio_pane_sash_position(DummyPane(), "240")

    assert calls == [("sashpos", 0, 240)]


def test_set_radio_pane_sash_position_falls_back_to_sash_place():
    calls = []

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))
            raise RuntimeError("sashpos failed")

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    radio_tab._set_radio_pane_sash_position(DummyPane(), 240)

    assert calls == [
        ("sashpos", 0, 240),
        ("sash_place", 0, 0, 240),
    ]


def test_set_radio_pane_sash_position_ignores_failures():
    class DummyPane:
        def sashpos(self, index, value):
            raise RuntimeError("sashpos failed")

        def sash_place(self, index, x, y):
            raise RuntimeError("sash_place failed")

    radio_tab._set_radio_pane_sash_position(DummyPane(), 240)


def test_radio_pane_drag_start_state_reads_event_and_sash():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            assert index == 0
            return "240"

    assert radio_tab._radio_pane_drag_start_state(DummyEvent(), DummyPane()) == (
        310,
        240,
    )


def test_radio_pane_drag_start_state_returns_zeroes_on_failure():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            raise RuntimeError("sashpos failed")

    assert radio_tab._radio_pane_drag_start_state(DummyEvent(), DummyPane()) == (0, 0)


def test_record_radio_pane_drag_start_updates_drag_state():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            assert index == 0
            return "240"

    drag_state = {"root_y": 0, "sash_y": 0}

    radio_tab._record_radio_pane_drag_start(drag_state, DummyEvent(), DummyPane())

    assert drag_state == {"root_y": 310, "sash_y": 240}


def test_record_radio_pane_drag_start_uses_zeroes_on_failure():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            raise RuntimeError("sashpos failed")

    drag_state = {"root_y": 99, "sash_y": 88}

    radio_tab._record_radio_pane_drag_start(drag_state, DummyEvent(), DummyPane())

    assert drag_state == {"root_y": 0, "sash_y": 0}


def test_handle_radio_pane_marker_drag_start_updates_state_and_breaks():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            assert index == 0
            return "240"

    drag_state = {"root_y": 0, "sash_y": 0}

    result = radio_tab._handle_radio_pane_marker_drag_start(
        drag_state,
        DummyEvent(),
        DummyPane(),
    )

    assert result == "break"
    assert drag_state == {"root_y": 310, "sash_y": 240}


def test_handle_radio_pane_marker_drag_start_uses_zeroes_and_breaks_on_failure():
    class DummyEvent:
        y_root = "310"

    class DummyPane:
        def sashpos(self, index):
            raise RuntimeError("sashpos failed")

    drag_state = {"root_y": 99, "sash_y": 88}

    result = radio_tab._handle_radio_pane_marker_drag_start(
        drag_state,
        DummyEvent(),
        DummyPane(),
    )

    assert result == "break"
    assert drag_state == {"root_y": 0, "sash_y": 0}


def test_invoke_radio_pane_marker_drag_start_handler_forwards_dependencies():
    calls = []
    drag_state = object()
    event = object()
    pane = object()

    result = radio_tab._invoke_radio_pane_marker_drag_start_handler(
        drag_state,
        event,
        pane,
        lambda state_arg, event_arg, pane_arg: calls.append(
            (state_arg, event_arg, pane_arg)
        )
        or "break",
    )

    assert result == "break"
    assert calls == [(drag_state, event, pane)]


def test_make_radio_pane_marker_drag_start_callback_binds_state_event_and_pane():
    calls = []
    drag_state = object()
    pane = object()
    event = object()

    callback = radio_tab._make_radio_pane_marker_drag_start_callback(
        drag_state,
        pane,
        drag_start_handler=lambda state_arg, event_arg, pane_arg: calls.append(
            (state_arg, event_arg, pane_arg)
        )
        or "break",
    )

    assert callback(event) == "break"
    assert calls == [(drag_state, event, pane)]


def test_make_radio_pane_marker_drag_start_callback_returns_handler_result():
    callback = radio_tab._make_radio_pane_marker_drag_start_callback(
        object(),
        object(),
        drag_start_handler=lambda _state, _event, _pane: "handled",
    )

    assert callback(object()) == "handled"


def test_radio_pane_drag_target_sash_adds_positive_delta():
    class DummyEvent:
        y_root = "330"

    drag_state = {"root_y": "310", "sash_y": "240"}

    assert radio_tab._radio_pane_drag_target_sash(DummyEvent(), drag_state) == 260


def test_radio_pane_drag_target_sash_adds_negative_delta():
    class DummyEvent:
        y_root = "290"

    drag_state = {"root_y": "310", "sash_y": "240"}

    assert radio_tab._radio_pane_drag_target_sash(DummyEvent(), drag_state) == 220


def test_forget_radio_pane_marker_calls_place_forget():
    calls = []

    class DummyMarker:
        def place_forget(self):
            calls.append("place_forget")

    radio_tab._forget_radio_pane_marker(DummyMarker())

    assert calls == ["place_forget"]


def test_forget_radio_pane_marker_ignores_failures():
    class DummyMarker:
        def place_forget(self):
            raise RuntimeError("place_forget failed")

    radio_tab._forget_radio_pane_marker(DummyMarker())


def test_radio_pane_drag_state_returns_defaults_and_new_dict():
    first = radio_tab._radio_pane_drag_state()
    second = radio_tab._radio_pane_drag_state()

    assert first == {"root_y": 0, "sash_y": 0, "update_pending": False}
    assert second == {"root_y": 0, "sash_y": 0, "update_pending": False}
    assert first is not second


def test_bind_radio_pane_marker_event_binds_with_add():
    calls = []
    callback = object()

    class DummyWidget:
        def bind(self, event_name, callback_arg, add=None):
            calls.append((event_name, callback_arg, add))

    radio_tab._bind_radio_pane_marker_event(
        DummyWidget(),
        "<Configure>",
        callback,
    )

    assert calls == [("<Configure>", callback, "+")]


def test_bind_radio_pane_marker_events_binds_all_events_with_add():
    calls = []
    first_callback = object()
    second_callback = object()

    class DummyWidget:
        def bind(self, event_name, callback, add=None):
            calls.append((event_name, callback, add))

    radio_tab._bind_radio_pane_marker_events(
        DummyWidget(),
        (
            ("<Configure>", first_callback),
            ("<B1-Motion>", second_callback),
        ),
    )

    assert calls == [
        ("<Configure>", first_callback, "+"),
        ("<B1-Motion>", second_callback, "+"),
    ]


def test_bind_radio_pane_marker_events_stops_and_ignores_failures():
    calls = []

    class DummyWidget:
        def bind(self, event_name, callback, add=None):
            calls.append((event_name, add))
            raise RuntimeError("bind failed")

    radio_tab._bind_radio_pane_marker_events(
        DummyWidget(),
        (
            ("<Configure>", object()),
            ("<B1-Motion>", object()),
        ),
    )

    assert calls == [("<Configure>", "+")]


def test_run_radio_pane_marker_update_clears_pending_before_update():
    calls = []
    drag_state = {"update_pending": True}

    radio_tab._run_radio_pane_marker_update(
        drag_state,
        lambda: calls.append(("update", drag_state["update_pending"])),
    )

    assert calls == [("update", False)]
    assert drag_state["update_pending"] is False


def test_make_radio_pane_marker_update_runner_binds_update_dependencies():
    calls = []
    drag_state = object()
    update_marker = object()

    runner = radio_tab._make_radio_pane_marker_update_runner(
        drag_state,
        update_marker,
        update_runner=lambda state_arg, update_arg: calls.append(
            (state_arg, update_arg)
        ),
    )

    runner()

    assert calls == [(drag_state, update_marker)]


def test_request_radio_pane_marker_after_idle_schedules_runner():
    calls = []
    run_update = object()

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    radio_tab._request_radio_pane_marker_after_idle(
        DummyContainer(),
        run_update,
    )

    assert calls == [("after_idle", run_update)]


def test_request_radio_pane_marker_after_idle_runs_on_failure():
    calls = []

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))
            raise RuntimeError("after_idle failed")

    radio_tab._request_radio_pane_marker_after_idle(
        DummyContainer(),
        lambda: calls.append("run"),
    )

    assert calls[0][0] == "after_idle"
    assert calls[1:] == ["run"]


def test_claim_radio_pane_marker_update_skips_pending_state():
    drag_state = {"update_pending": True}

    assert radio_tab._claim_radio_pane_marker_update(drag_state) is False
    assert drag_state["update_pending"] is True


def test_claim_radio_pane_marker_update_marks_available_state():
    drag_state = {"update_pending": False}

    assert radio_tab._claim_radio_pane_marker_update(drag_state) is True
    assert drag_state["update_pending"] is True


def test_schedule_radio_pane_marker_update_skips_pending_update():
    calls = []
    drag_state = {"update_pending": True}

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    radio_tab._schedule_radio_pane_marker_update(
        DummyContainer(),
        drag_state,
        lambda: calls.append("update"),
    )

    assert calls == []
    assert drag_state["update_pending"] is True


def test_schedule_radio_pane_marker_update_uses_after_idle_callback():
    calls = []
    drag_state = {"update_pending": False}

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    radio_tab._schedule_radio_pane_marker_update(
        DummyContainer(),
        drag_state,
        lambda: calls.append("update"),
    )

    callback = calls[0][1]
    assert drag_state["update_pending"] is True

    callback()

    assert calls == [("after_idle", callback), "update"]
    assert drag_state["update_pending"] is False


def test_schedule_radio_pane_marker_update_runs_immediately_on_after_idle_failure():
    calls = []
    drag_state = {"update_pending": False}

    class DummyContainer:
        def after_idle(self, callback):
            calls.append("after_idle")
            raise RuntimeError("after_idle failed")

    radio_tab._schedule_radio_pane_marker_update(
        DummyContainer(),
        drag_state,
        lambda: calls.append("update"),
    )

    assert calls == ["after_idle", "update"]
    assert drag_state["update_pending"] is False


def test_request_radio_pane_marker_update_schedules_update():
    calls = []
    drag_state = {"update_pending": False}

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    radio_tab._request_radio_pane_marker_update(
        DummyContainer(),
        drag_state,
        lambda: calls.append("update"),
    )

    callback = calls[0][1]

    assert drag_state["update_pending"] is True

    callback()

    assert calls == [("after_idle", callback), "update"]
    assert drag_state["update_pending"] is False


def test_request_radio_pane_marker_update_keeps_pending_update():
    calls = []
    drag_state = {"update_pending": True}

    class DummyContainer:
        def after_idle(self, callback):
            calls.append(("after_idle", callback))

    radio_tab._request_radio_pane_marker_update(
        DummyContainer(),
        drag_state,
        lambda: calls.append("update"),
    )

    assert calls == []
    assert drag_state["update_pending"] is True


def test_invoke_radio_pane_marker_update_requester_forwards_dependencies():
    calls = []
    container = object()
    drag_state = object()
    update_marker = object()

    radio_tab._invoke_radio_pane_marker_update_requester(
        container,
        drag_state,
        update_marker,
        lambda container_arg, state_arg, update_arg: calls.append(
            (container_arg, state_arg, update_arg)
        ),
    )

    assert calls == [(container, drag_state, update_marker)]


def test_make_radio_pane_marker_schedule_callback_binds_update_dependencies():
    calls = []
    container = object()
    drag_state = object()
    update_marker = object()

    callback = radio_tab._make_radio_pane_marker_schedule_callback(
        container,
        drag_state,
        update_marker,
        update_requester=lambda container_arg, state_arg, update_arg: calls.append(
            (container_arg, state_arg, update_arg)
        ),
    )

    callback()

    assert calls == [(container, drag_state, update_marker)]


def test_make_radio_pane_marker_schedule_callback_invokes_requester_each_time():
    calls = []

    callback = radio_tab._make_radio_pane_marker_schedule_callback(
        object(),
        object(),
        object(),
        update_requester=lambda _container, _state, _update: calls.append("request"),
    )

    callback()
    callback()

    assert calls == ["request", "request"]


def test_request_initial_radio_pane_marker_update_uses_after_zero():
    calls = []
    callback = object()

    class DummyContainer:
        def after(self, delay, scheduled_callback):
            calls.append((delay, scheduled_callback))

    radio_tab._request_initial_radio_pane_marker_update(
        DummyContainer(),
        callback,
    )

    assert calls == [(0, callback)]


def test_request_initial_radio_pane_marker_update_ignores_after_failures():
    class DummyContainer:
        def after(self, delay, scheduled_callback):
            raise RuntimeError("after failed")

    radio_tab._request_initial_radio_pane_marker_update(
        DummyContainer(),
        object(),
    )


def test_schedule_initial_radio_pane_marker_update_delegates_request(monkeypatch):
    calls = []
    container = object()
    callback = object()

    monkeypatch.setattr(
        radio_tab,
        "_request_initial_radio_pane_marker_update",
        lambda container_arg, callback_arg: calls.append((container_arg, callback_arg)),
    )

    radio_tab._schedule_initial_radio_pane_marker_update(container, callback)

    assert calls == [(container, callback)]


def test_build_radio_pane_marker_widgets_creates_marker_and_grip():
    events = []
    container = object()

    class DummyWidget:
        def __init__(self, parent, **kwargs):
            self.parent = parent
            self.kwargs = kwargs

        def columnconfigure(self, column, weight=0):
            events.append(("columnconfigure", self, column, weight))

        def grid(self, **kwargs):
            events.append(("grid", self, kwargs))

    class DummyFrame(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("frame", parent, kwargs, self))

    class DummyLabel(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("label", parent, kwargs, self))

    marker, grip = radio_tab._build_radio_pane_marker_widgets(
        container,
        color="#123456",
        frame_factory=DummyFrame,
        label_factory=DummyLabel,
    )

    assert events[0] == (
        "frame",
        container,
        {"bg": "#123456", "bd": 1, "relief": "solid"},
        marker,
    )
    assert events[1] == ("columnconfigure", marker, 0, 1)
    assert events[2] == (
        "label",
        marker,
        {
            "text": "\u2261",
            "bg": "#123456",
            "fg": "#ffffff",
            "font": ("TkDefaultFont", 9, "bold"),
            "cursor": "sb_v_double_arrow",
            "padx": 0,
            "pady": 0,
            "anchor": "center",
        },
        grip,
    )
    assert events[3] == ("grid", grip, {"row": 0, "column": 0, "sticky": "ew"})


def test_update_radio_pane_marker_from_sash_places_current_sash():
    calls = []
    marker = object()

    class DummyPane:
        def sashpos(self, index):
            calls.append(("sashpos", index))
            return "240"

    radio_tab._update_radio_pane_marker_from_sash(
        DummyPane(),
        lambda sash_y: calls.append(("place", sash_y)),
        marker,
    )

    assert calls == [("sashpos", 0), ("place", 240)]


def test_update_radio_pane_marker_from_sash_forgets_marker_on_sash_failure():
    calls = []

    class DummyPane:
        def sashpos(self, index):
            calls.append(("sashpos", index))
            raise RuntimeError("sashpos failed")

    class DummyMarker:
        def place_forget(self):
            calls.append("place_forget")

    radio_tab._update_radio_pane_marker_from_sash(
        DummyPane(),
        lambda sash_y: calls.append(("place", sash_y)),
        DummyMarker(),
    )

    assert calls == [("sashpos", 0), "place_forget"]


def test_update_radio_pane_marker_from_sash_forgets_marker_on_place_failure():
    calls = []

    class DummyPane:
        def sashpos(self, index):
            calls.append(("sashpos", index))
            return 240

    class DummyMarker:
        def place_forget(self):
            calls.append("place_forget")

    def place_marker(sash_y):
        calls.append(("place", sash_y))
        raise RuntimeError("place failed")

    radio_tab._update_radio_pane_marker_from_sash(
        DummyPane(),
        place_marker,
        DummyMarker(),
    )

    assert calls == [("sashpos", 0), ("place", 240), "place_forget"]


def test_handle_radio_pane_marker_update_event_ignores_event_and_places_sash():
    calls = []
    marker = object()
    event = object()

    class DummyPane:
        def sashpos(self, index):
            calls.append(("sashpos", index))
            return "240"

    radio_tab._handle_radio_pane_marker_update_event(
        DummyPane(),
        lambda sash_y: calls.append(("place", sash_y)),
        marker,
        event,
    )

    assert calls == [("sashpos", 0), ("place", 240)]


def test_handle_radio_pane_marker_update_event_forgets_marker_on_failure():
    calls = []

    class DummyPane:
        def sashpos(self, index):
            calls.append(("sashpos", index))
            raise RuntimeError("sash failed")

    class DummyMarker:
        def place_forget(self):
            calls.append("place_forget")

    radio_tab._handle_radio_pane_marker_update_event(
        DummyPane(),
        lambda sash_y: calls.append(("place", sash_y)),
        DummyMarker(),
    )

    assert calls == [("sashpos", 0), "place_forget"]


def test_invoke_radio_pane_marker_update_handler_forwards_dependencies():
    calls = []
    pane = object()
    place_marker = object()
    marker = object()
    event = object()

    radio_tab._invoke_radio_pane_marker_update_handler(
        pane,
        place_marker,
        marker,
        event,
        lambda pane_arg, place_arg, marker_arg, event_arg: calls.append(
            (pane_arg, place_arg, marker_arg, event_arg)
        ),
    )

    assert calls == [(pane, place_marker, marker, event)]


def test_make_radio_pane_marker_update_callback_binds_update_dependencies():
    calls = []
    pane = object()
    place_marker = object()
    marker = object()
    event = object()

    callback = radio_tab._make_radio_pane_marker_update_callback(
        pane,
        place_marker,
        marker,
        update_handler=lambda pane_arg, place_arg, marker_arg, event_arg: calls.append(
            (pane_arg, place_arg, marker_arg, event_arg)
        ),
    )

    callback(event)

    assert calls == [(pane, place_marker, marker, event)]


def test_make_radio_pane_marker_update_callback_defaults_event_to_none():
    calls = []

    callback = radio_tab._make_radio_pane_marker_update_callback(
        object(),
        object(),
        object(),
        update_handler=lambda _pane, _place, _marker, event_arg: calls.append(
            event_arg
        ),
    )

    callback()

    assert calls == [None]


def test_show_radio_pane_marker_places_and_lifts_marker():
    calls = []
    geometry = {"x": 1, "y": 2, "width": 3, "height": 4}

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lift(self):
            calls.append("lift")

    radio_tab._show_radio_pane_marker(DummyMarker(), geometry)

    assert calls == [("place", geometry), "lift"]


def test_place_radio_pane_marker_places_and_lifts_marker():
    calls = []
    geometry = {"x": 1, "y": 2, "width": 3, "height": 4}

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lift(self):
            calls.append("lift")

        def place_forget(self):
            calls.append("place_forget")

    radio_tab._place_radio_pane_marker(DummyMarker(), geometry)

    assert calls == [("place", geometry), "lift"]


def test_place_radio_pane_marker_forgets_marker_on_place_failure():
    calls = []

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))
            raise RuntimeError("place failed")

        def lift(self):
            calls.append("lift")

        def place_forget(self):
            calls.append("place_forget")

    radio_tab._place_radio_pane_marker(DummyMarker(), {"x": 1})

    assert calls == [("place", {"x": 1}), "place_forget"]


def test_place_radio_pane_marker_forgets_marker_on_lift_failure():
    calls = []

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lift(self):
            calls.append("lift")
            raise RuntimeError("lift failed")

        def place_forget(self):
            calls.append("place_forget")

    radio_tab._place_radio_pane_marker(DummyMarker(), {"x": 1})

    assert calls == [("place", {"x": 1}), "lift", "place_forget"]


def test_radio_pane_container_width_reads_widget_width_as_int():
    class DummyContainer:
        def winfo_width(self):
            return "320"

    assert radio_tab._radio_pane_container_width(DummyContainer()) == 320


def test_radio_pane_marker_geometry_for_container_uses_width_and_sash():
    class DummyContainer:
        def winfo_width(self):
            return 320

    assert radio_tab._radio_pane_marker_geometry_for_container(
        DummyContainer(),
        240,
    ) == {
        "x": 127,
        "y": 235,
        "width": 66,
        "height": 12,
    }


def test_place_radio_pane_marker_for_sash_uses_container_width_and_sash():
    calls = []

    class DummyContainer:
        def winfo_width(self):
            calls.append("winfo_width")
            return 320

    class DummyMarker:
        def place(self, **kwargs):
            calls.append(("place", kwargs))

        def lift(self):
            calls.append("lift")

        def place_forget(self):
            calls.append("place_forget")

    radio_tab._place_radio_pane_marker_for_sash(
        DummyContainer(),
        DummyMarker(),
        240,
    )

    assert calls == [
        "winfo_width",
        ("place", {"x": 127, "y": 235, "width": 66, "height": 12}),
        "lift",
    ]


def test_place_radio_pane_marker_for_sash_propagates_width_failures():
    class DummyContainer:
        def winfo_width(self):
            raise RuntimeError("width failed")

    class DummyMarker:
        def place(self, **kwargs):
            raise AssertionError("place should not be called")

    with pytest.raises(RuntimeError, match="width failed"):
        radio_tab._place_radio_pane_marker_for_sash(
            DummyContainer(),
            DummyMarker(),
            240,
        )


def test_invoke_radio_pane_marker_placer_forwards_dependencies():
    calls = []
    container = object()
    marker = object()

    radio_tab._invoke_radio_pane_marker_placer(
        container,
        marker,
        240,
        lambda container_arg, marker_arg, sash_y: calls.append(
            (container_arg, marker_arg, sash_y)
        ),
    )

    assert calls == [(container, marker, 240)]


def test_make_radio_pane_marker_place_callback_binds_container_and_marker():
    calls = []
    container = object()
    marker = object()

    callback = radio_tab._make_radio_pane_marker_place_callback(
        container,
        marker,
        marker_placer=lambda container_arg, marker_arg, sash_y: calls.append(
            (container_arg, marker_arg, sash_y)
        ),
    )

    callback(240)

    assert calls == [(container, marker, 240)]


def test_make_radio_pane_marker_place_callback_invokes_placer_each_time():
    calls = []

    callback = radio_tab._make_radio_pane_marker_place_callback(
        object(),
        object(),
        marker_placer=lambda _container, _marker, sash_y: calls.append(sash_y),
    )

    callback(120)
    callback(240)

    assert calls == [120, 240]


def test_radio_pane_update_bindings_use_update_callback_for_all_events():
    update_marker = object()

    assert radio_tab._radio_pane_update_bindings(update_marker) == (
        ("<Configure>", update_marker),
        ("<ButtonRelease-1>", update_marker),
        ("<B1-Motion>", update_marker),
    )


def test_radio_pane_grip_bindings_use_drag_callbacks():
    start_drag = object()
    drag = object()
    end_drag = object()

    assert radio_tab._radio_pane_grip_bindings(start_drag, drag, end_drag) == (
        ("<Button-1>", start_drag),
        ("<B1-Motion>", drag),
        ("<ButtonRelease-1>", end_drag),
    )


def test_radio_pane_marker_binding_plan_maps_widgets_to_bindings():
    container = object()
    pane = object()
    grip = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    assert radio_tab._radio_pane_marker_binding_plan(
        container,
        pane,
        grip,
        update_marker=update_marker,
        start_drag=start_drag,
        drag=drag,
        end_drag=end_drag,
    ) == (
        (container, radio_tab._radio_pane_update_bindings(update_marker)),
        (pane, radio_tab._radio_pane_update_bindings(update_marker)),
        (grip, radio_tab._radio_pane_grip_bindings(start_drag, drag, end_drag)),
    )


def test_bind_radio_pane_marker_callbacks_binds_update_and_grip_events():
    calls = []

    class DummyWidget:
        def __init__(self, name):
            self.name = name

        def bind(self, event_name, callback, add=None):
            calls.append((self.name, event_name, callback, add))

    container = DummyWidget("container")
    pane = DummyWidget("pane")
    grip = DummyWidget("grip")
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    radio_tab._bind_radio_pane_marker_callbacks(
        container,
        pane,
        grip,
        update_marker=update_marker,
        start_drag=start_drag,
        drag=drag,
        end_drag=end_drag,
    )

    assert calls == [
        ("container", "<Configure>", update_marker, "+"),
        ("container", "<ButtonRelease-1>", update_marker, "+"),
        ("container", "<B1-Motion>", update_marker, "+"),
        ("pane", "<Configure>", update_marker, "+"),
        ("pane", "<ButtonRelease-1>", update_marker, "+"),
        ("pane", "<B1-Motion>", update_marker, "+"),
        ("grip", "<Button-1>", start_drag, "+"),
        ("grip", "<B1-Motion>", drag, "+"),
        ("grip", "<ButtonRelease-1>", end_drag, "+"),
    ]


def test_bind_radio_pane_marker_callbacks_ignores_widget_bind_failures():
    calls = []

    class FailingWidget:
        def __init__(self, name):
            self.name = name

        def bind(self, event_name, callback, add=None):
            calls.append((self.name, event_name, add))
            raise RuntimeError("bind failed")

    radio_tab._bind_radio_pane_marker_callbacks(
        FailingWidget("container"),
        FailingWidget("pane"),
        FailingWidget("grip"),
        update_marker=object(),
        start_drag=object(),
        drag=object(),
        end_drag=object(),
    )

    assert calls == [
        ("container", "<Configure>", "+"),
        ("pane", "<Configure>", "+"),
        ("grip", "<Button-1>", "+"),
    ]


def test_activate_radio_pane_marker_callbacks_binds_then_schedules_initial_update():
    events = []
    container = object()
    pane = object()
    grip = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    radio_tab._activate_radio_pane_marker_callbacks(
        container,
        pane,
        grip,
        update_marker=update_marker,
        start_drag=start_drag,
        drag=drag,
        end_drag=end_drag,
        callback_binder=lambda *args, **kwargs: events.append(("bind", args, kwargs)),
        initial_update_scheduler=lambda *args: events.append(("schedule", args)),
    )

    assert events == [
        (
            "bind",
            (container, pane, grip),
            {
                "update_marker": update_marker,
                "start_drag": start_drag,
                "drag": drag,
                "end_drag": end_drag,
            },
        ),
        ("schedule", (container, update_marker)),
    ]


def test_activate_radio_pane_marker_callbacks_propagates_binding_failures():
    def failing_binder(*_args, **_kwargs):
        raise RuntimeError("bind failed")

    with pytest.raises(RuntimeError, match="bind failed"):
        radio_tab._activate_radio_pane_marker_callbacks(
            object(),
            object(),
            object(),
            update_marker=object(),
            start_drag=object(),
            drag=object(),
            end_drag=object(),
            callback_binder=failing_binder,
            initial_update_scheduler=lambda *_args: None,
        )


def test_build_radio_pane_marker_callbacks_builds_callbacks_in_dependency_order():
    events = []
    container = object()
    pane = object()
    marker = object()
    drag_state = object()
    place_marker = object()
    update_marker = object()
    schedule_marker_update = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    result = radio_tab._build_radio_pane_marker_callbacks(
        container,
        pane,
        marker,
        drag_state,
        place_callback_factory=lambda container_arg, marker_arg: events.append(
            ("place_factory", container_arg, marker_arg)
        )
        or place_marker,
        update_callback_factory=lambda pane_arg, place_arg, marker_arg: events.append(
            ("update_factory", pane_arg, place_arg, marker_arg)
        )
        or update_marker,
        schedule_callback_factory=lambda container_arg, state_arg, update_arg: events.append(
            ("schedule_factory", container_arg, state_arg, update_arg)
        )
        or schedule_marker_update,
        drag_start_callback_factory=lambda state_arg, pane_arg: events.append(
            ("start_factory", state_arg, pane_arg)
        )
        or start_drag,
        drag_event_callback_factory=lambda state_arg, pane_arg, place_arg, schedule_arg: events.append(
            ("drag_factory", state_arg, pane_arg, place_arg, schedule_arg)
        )
        or drag,
        drag_end_callback_factory=lambda update_arg: events.append(
            ("end_factory", update_arg)
        )
        or end_drag,
    )

    assert isinstance(result, radio_tab._RadioPaneMarkerCallbacks)
    assert result.update_marker is update_marker
    assert result.start_drag is start_drag
    assert result.drag is drag
    assert result.end_drag is end_drag
    assert events == [
        ("place_factory", container, marker),
        ("update_factory", pane, place_marker, marker),
        ("schedule_factory", container, drag_state, update_marker),
        ("start_factory", drag_state, pane),
        ("drag_factory", drag_state, pane, place_marker, schedule_marker_update),
        ("end_factory", update_marker),
    ]


def test_build_radio_pane_marker_callbacks_returns_activation_callbacks():
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    result = radio_tab._build_radio_pane_marker_callbacks(
        object(),
        object(),
        object(),
        object(),
        place_callback_factory=lambda _container, _marker: "place",
        update_callback_factory=lambda _pane, _place, _marker: update_marker,
        schedule_callback_factory=lambda _container, _state, _update: "schedule",
        drag_start_callback_factory=lambda _state, _pane: start_drag,
        drag_event_callback_factory=lambda _state, _pane, _place, _schedule: drag,
        drag_end_callback_factory=lambda _update: end_drag,
    )

    assert isinstance(result, radio_tab._RadioPaneMarkerCallbacks)
    assert result.update_marker is update_marker
    assert result.start_drag is start_drag
    assert result.drag is drag
    assert result.end_drag is end_drag


def test_build_radio_pane_marker_base_builds_widgets_then_drag_state():
    events = []
    container = object()
    marker = object()
    grip = object()
    drag_state = object()

    result = radio_tab._build_radio_pane_marker_base(
        container,
        color="#123456",
        widget_builder=lambda container_arg, color="#0a84ff": events.append(
            ("widgets", container_arg, color)
        )
        or (marker, grip),
        drag_state_factory=lambda: events.append("drag_state") or drag_state,
    )

    assert isinstance(result, radio_tab._RadioPaneMarkerBase)
    assert result.marker is marker
    assert result.grip is grip
    assert result.drag_state is drag_state
    assert events == [("widgets", container, "#123456"), "drag_state"]


def test_build_radio_pane_marker_base_uses_default_color_for_widgets():
    calls = []

    radio_tab._build_radio_pane_marker_base(
        object(),
        widget_builder=lambda _container, color="#0a84ff": calls.append(color)
        or (object(), object()),
        drag_state_factory=lambda: object(),
    )

    assert calls == ["#0a84ff"]


def test_build_radio_pane_marker_installation_builds_base_then_callbacks():
    events = []
    container = object()
    pane = object()
    marker = object()
    grip = object()
    drag_state = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()

    def marker_base_builder(container_arg, color="#0a84ff"):
        events.append(("base", container_arg, color))
        return radio_tab._RadioPaneMarkerBase(marker, grip, drag_state)

    def callback_builder(container_arg, pane_arg, marker_arg, state_arg):
        events.append(("callbacks", container_arg, pane_arg, marker_arg, state_arg))
        return radio_tab._RadioPaneMarkerCallbacks(
            update_marker,
            start_drag,
            drag,
            end_drag,
        )

    result = radio_tab._build_radio_pane_marker_installation(
        container,
        pane,
        color="#123456",
        marker_base_builder=marker_base_builder,
        callback_builder=callback_builder,
    )

    assert isinstance(result, radio_tab._RadioPaneMarkerInstallation)
    assert result.marker is marker
    assert result.grip is grip
    assert result.update_marker is update_marker
    assert result.start_drag is start_drag
    assert result.drag is drag
    assert result.end_drag is end_drag
    assert events == [
        ("base", container, "#123456"),
        ("callbacks", container, pane, marker, drag_state),
    ]


def test_build_radio_pane_marker_installation_uses_default_color_for_base():
    calls = []

    radio_tab._build_radio_pane_marker_installation(
        object(),
        object(),
        marker_base_builder=lambda _container, color="#0a84ff": calls.append(color)
        or radio_tab._RadioPaneMarkerBase(object(), object(), object()),
        callback_builder=lambda *_args: radio_tab._RadioPaneMarkerCallbacks(
            object(),
            object(),
            object(),
            object(),
        ),
    )

    assert calls == ["#0a84ff"]


def test_activate_radio_pane_marker_installation_passes_named_fields():
    events = []
    container = object()
    pane = object()
    marker = object()
    grip = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()
    installation = radio_tab._RadioPaneMarkerInstallation(
        marker,
        grip,
        update_marker,
        start_drag,
        drag,
        end_drag,
    )

    radio_tab._activate_radio_pane_marker_installation(
        container,
        pane,
        installation,
        callback_activator=lambda *args, **kwargs: events.append((args, kwargs)),
    )

    assert events == [
        (
            (container, pane, grip),
            {
                "update_marker": update_marker,
                "start_drag": start_drag,
                "drag": drag,
                "end_drag": end_drag,
            },
        )
    ]


def test_install_pane_drag_marker_activates_callbacks_without_direct_reschedule(
    monkeypatch,
):
    events = []
    container = object()
    pane = object()
    marker = object()
    grip = object()
    update_marker = object()
    start_drag = object()
    drag = object()
    end_drag = object()
    installation = radio_tab._RadioPaneMarkerInstallation(
        marker,
        grip,
        update_marker,
        start_drag,
        drag,
        end_drag,
    )

    monkeypatch.setattr(
        radio_tab,
        "_build_radio_pane_marker_installation",
        lambda container_arg, pane_arg, color="#0a84ff": events.append(
            ("installation", container_arg, pane_arg, color)
        )
        or installation,
    )
    monkeypatch.setattr(
        radio_tab,
        "_activate_radio_pane_marker_installation",
        lambda *args, **kwargs: events.append(("activate", args, kwargs)),
    )
    monkeypatch.setattr(
        radio_tab,
        "_schedule_initial_radio_pane_marker_update",
        lambda *_args: events.append("direct_schedule"),
    )

    result = radio_tab._install_pane_drag_marker(container, pane)

    assert result is marker
    assert "direct_schedule" not in events
    assert events == [
        ("installation", container, pane, "#0a84ff"),
        (
            "activate",
            (container, pane, installation),
            {},
        ),
    ]


def test_handle_radio_pane_marker_drag_sets_sash_places_marker_and_schedules():
    calls = []
    drag_state = {"root_y": "310", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    radio_tab._handle_radio_pane_marker_drag(
        DummyEvent(),
        drag_state=drag_state,
        pane=DummyPane(),
        place_marker=lambda sash_y: calls.append(("place", sash_y)),
        schedule_marker_update=lambda: calls.append("schedule"),
    )

    assert calls == [
        ("sashpos", 0, 260),
        ("place", 260),
        "schedule",
    ]


def test_handle_radio_pane_marker_drag_ignores_target_failures():
    calls = []
    drag_state = {"root_y": "bad", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    radio_tab._handle_radio_pane_marker_drag(
        DummyEvent(),
        drag_state=drag_state,
        pane=DummyPane(),
        place_marker=lambda sash_y: calls.append(("place", sash_y)),
        schedule_marker_update=lambda: calls.append("schedule"),
    )

    assert calls == []


def test_handle_radio_pane_marker_drag_ignores_place_failures():
    calls = []
    drag_state = {"root_y": "310", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    def place_marker(sash_y):
        calls.append(("place", sash_y))
        raise RuntimeError("place failed")

    radio_tab._handle_radio_pane_marker_drag(
        DummyEvent(),
        drag_state=drag_state,
        pane=DummyPane(),
        place_marker=place_marker,
        schedule_marker_update=lambda: calls.append("schedule"),
    )

    assert calls == [
        ("sashpos", 0, 260),
        ("place", 260),
    ]


def test_handle_radio_pane_marker_drag_event_handles_motion_and_breaks():
    calls = []
    drag_state = {"root_y": "310", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    class DummyPane:
        def sashpos(self, index, value):
            calls.append(("sashpos", index, value))

        def sash_place(self, index, x, y):
            calls.append(("sash_place", index, x, y))

    result = radio_tab._handle_radio_pane_marker_drag_event(
        DummyEvent(),
        drag_state=drag_state,
        pane=DummyPane(),
        place_marker=lambda sash_y: calls.append(("place", sash_y)),
        schedule_marker_update=lambda: calls.append("schedule"),
    )

    assert result == "break"
    assert calls == [
        ("sashpos", 0, 260),
        ("place", 260),
        "schedule",
    ]


def test_handle_radio_pane_marker_drag_event_breaks_after_ignored_motion_failure():
    calls = []
    drag_state = {"root_y": "bad", "sash_y": "240"}

    class DummyEvent:
        y_root = "330"

    result = radio_tab._handle_radio_pane_marker_drag_event(
        DummyEvent(),
        drag_state=drag_state,
        pane=object(),
        place_marker=lambda sash_y: calls.append(("place", sash_y)),
        schedule_marker_update=lambda: calls.append("schedule"),
    )

    assert result == "break"
    assert calls == []


def test_invoke_radio_pane_marker_drag_event_handler_forwards_dependencies():
    calls = []
    event = object()
    drag_state = object()
    pane = object()
    place_marker = object()
    schedule_marker_update = object()

    result = radio_tab._invoke_radio_pane_marker_drag_event_handler(
        event,
        drag_state=drag_state,
        pane=pane,
        place_marker=place_marker,
        schedule_marker_update=schedule_marker_update,
        drag_event_handler=lambda event_arg, **kwargs: calls.append((event_arg, kwargs))
        or "break",
    )

    assert result == "break"
    assert calls == [
        (
            event,
            {
                "drag_state": drag_state,
                "pane": pane,
                "place_marker": place_marker,
                "schedule_marker_update": schedule_marker_update,
            },
        )
    ]


def test_make_radio_pane_marker_drag_event_callback_binds_drag_dependencies():
    calls = []
    drag_state = object()
    pane = object()
    place_marker = object()
    schedule_marker_update = object()
    event = object()

    callback = radio_tab._make_radio_pane_marker_drag_event_callback(
        drag_state,
        pane,
        place_marker,
        schedule_marker_update,
        drag_event_handler=lambda event_arg, **kwargs: calls.append((event_arg, kwargs))
        or "break",
    )

    assert callback(event) == "break"
    assert calls == [
        (
            event,
            {
                "drag_state": drag_state,
                "pane": pane,
                "place_marker": place_marker,
                "schedule_marker_update": schedule_marker_update,
            },
        )
    ]


def test_make_radio_pane_marker_drag_event_callback_returns_handler_result():
    callback = radio_tab._make_radio_pane_marker_drag_event_callback(
        object(),
        object(),
        object(),
        object(),
        drag_event_handler=lambda _event, **_kwargs: "handled",
    )

    assert callback(object()) == "handled"


def test_handle_radio_pane_marker_drag_end_updates_marker_and_breaks():
    calls = []

    result = radio_tab._handle_radio_pane_marker_drag_end(
        lambda: calls.append("update"),
    )

    assert result == "break"
    assert calls == ["update"]


def test_handle_radio_pane_marker_drag_end_propagates_update_failures():
    def update_marker():
        raise RuntimeError("update failed")

    with pytest.raises(RuntimeError, match="update failed"):
        radio_tab._handle_radio_pane_marker_drag_end(update_marker)


def test_invoke_radio_pane_marker_drag_end_handler_forwards_update_marker():
    calls = []
    update_marker = object()

    result = radio_tab._invoke_radio_pane_marker_drag_end_handler(
        update_marker,
        lambda update_arg: calls.append(update_arg) or "break",
    )

    assert result == "break"
    assert calls == [update_marker]


def test_make_radio_pane_marker_drag_end_callback_binds_update_marker():
    calls = []
    update_marker = object()
    event = object()

    callback = radio_tab._make_radio_pane_marker_drag_end_callback(
        update_marker,
        drag_end_handler=lambda update_arg: calls.append(update_arg) or "break",
    )

    assert callback(event) == "break"
    assert calls == [update_marker]


def test_make_radio_pane_marker_drag_end_callback_defaults_event_to_none():
    calls = []

    callback = radio_tab._make_radio_pane_marker_drag_end_callback(
        object(),
        drag_end_handler=lambda update_arg: calls.append(update_arg) or "break",
    )

    assert callback() == "break"
    assert len(calls) == 1


def test_build_detached_radio_placeholder_creates_expected_widgets():
    events = []
    host = object()
    status_var = object()
    command = object()

    class DummyWidget:
        def __init__(self, parent, **kwargs):
            self.parent = parent
            self.kwargs = kwargs

        def grid(self, **kwargs):
            events.append(("grid", self, kwargs))

    class DummyFrame(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("frame", parent, kwargs, self))

    class DummyLabel(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("label", parent, kwargs, self))

    class DummyButton(DummyWidget):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            events.append(("button", parent, kwargs, self))

    reattach = radio_tab._build_detached_radio_placeholder(
        host,
        title_text="title",
        hint_text="hint",
        status_var=status_var,
        reattach_text="reattach",
        reattach_command=command,
        frame_factory=DummyFrame,
        label_factory=DummyLabel,
        button_factory=DummyButton,
    )

    box = events[0][3]
    button = events[8][3]
    assert reattach is button
    assert events[0] == ("frame", host, {"padding": 18}, box)
    assert events[1] == ("grid", box, {"row": 0, "column": 0, "sticky": "nw"})
    assert events[2][0:3] == (
        "label",
        box,
        {"text": "title", "font": ("TkDefaultFont", 12, "bold")},
    )
    assert events[4][0:3] == (
        "label",
        box,
        {"text": "hint", "justify": "left", "wraplength": 760},
    )
    assert events[6][0:3] == (
        "label",
        box,
        {"textvariable": status_var, "justify": "left"},
    )
    assert events[8][0:3] == (
        "button",
        box,
        {"text": "reattach", "command": command},
    )
    assert events[9] == (
        "grid",
        button,
        {"row": 3, "column": 0, "sticky": "w", "pady": (8, 0)},
    )


def test_show_radio_detached_placeholder_skips_when_already_detached():
    events = []
    app = type("DummyApp", (), {})()
    app.radio_launcher_mode = "detached"

    radio_tab._show_radio_detached_placeholder(
        app,
        object(),
        lambda: events.append("clear"),
        placeholder_builder=lambda host, **kwargs: events.append("placeholder"),
        state_setter=lambda app, reattach: events.append("state"),
    )

    assert events == []


def test_show_radio_detached_placeholder_clears_builds_and_sets_state():
    events = []
    host = object()
    status_var = object()
    reattach_command = object()
    reattach_button = object()

    class DummyApp:
        radio_launcher_mode = ""
        radio_launcher_status_var = status_var
        reattach_radio_app = reattach_command

        def tr(self, key, fallback):
            events.append(("tr", key, fallback))
            return f"translated:{key}"

    app = DummyApp()

    def placeholder_builder(built_host, **kwargs):
        events.append(("placeholder", built_host, kwargs))
        return reattach_button

    def state_setter(state_app, button):
        events.append(("state", state_app, button))

    radio_tab._show_radio_detached_placeholder(
        app,
        host,
        lambda: events.append("clear"),
        placeholder_builder=placeholder_builder,
        state_setter=state_setter,
    )

    assert events == [
        "clear",
        (
            "tr",
            "radio_launcher_title",
            "NetMon Radio als externe App",
        ),
        (
            "tr",
            "radio_launcher_detached_hint",
            "Radio laeuft gerade standalone. Zum Wieder-Anheften bitte in der externen Radio-App auf 'Radio anheften' klicken.",
        ),
        (
            "tr",
            "radio_launcher_reattach",
            "Radio anheften",
        ),
        (
            "placeholder",
            host,
            {
                "title_text": "translated:radio_launcher_title",
                "hint_text": "translated:radio_launcher_detached_hint",
                "status_var": status_var,
                "reattach_text": "translated:radio_launcher_reattach",
                "reattach_command": reattach_command,
            },
        ),
        ("state", app, reattach_button),
    ]


def test_make_radio_detached_placeholder_callback_binds_app_host_and_clearer():
    calls = []
    app = object()
    host = object()
    clear_host = object()

    callback = radio_tab._make_radio_detached_placeholder_callback(
        app,
        host,
        clear_host,
        placeholder_shower=lambda app_arg, host_arg, clear_arg: calls.append(
            (app_arg, host_arg, clear_arg)
        ),
    )

    callback()

    assert calls == [(app, host, clear_host)]


def test_make_radio_detached_placeholder_callback_invokes_shower_each_time():
    calls = []

    callback = radio_tab._make_radio_detached_placeholder_callback(
        object(),
        object(),
        object(),
        placeholder_shower=lambda _app, _host, _clear: calls.append("show"),
    )

    callback()
    callback()

    assert calls == ["show", "show"]


def test_show_radio_embedded_panel_skips_when_already_embedded():
    events = []
    app = type("DummyApp", (), {})()
    app.radio_launcher_mode = "embedded"

    radio_tab._show_radio_embedded_panel(
        app,
        object(),
        lambda: events.append("clear"),
        panel_factory=lambda host, **kwargs: events.append("panel"),
        attach_panel=lambda app, host, panel: events.append("attach"),
    )

    assert events == []


def test_show_radio_embedded_panel_clears_builds_attaches_and_detaches():
    events = []
    host = object()
    panel = object()

    class DummyApp:
        radio_launcher_mode = ""

        def open_radio_external_app(self):
            events.append("open")
            return "opened"

    app = DummyApp()
    detach_callbacks = []

    def panel_factory(built_host, **kwargs):
        events.append(("panel", built_host, kwargs["host_app"]))
        detach_callbacks.append(kwargs["on_detach"])
        return panel

    def attach_panel(attach_app, attach_host, attach_panel_obj):
        events.append(("attach", attach_app, attach_host, attach_panel_obj))

    radio_tab._show_radio_embedded_panel(
        app,
        host,
        lambda: events.append("clear"),
        panel_factory=panel_factory,
        attach_panel=attach_panel,
    )

    assert detach_callbacks[0]() == "opened"
    assert events == [
        "clear",
        ("panel", host, app),
        ("attach", app, host, panel),
        "open",
    ]


def test_make_radio_embedded_panel_callback_binds_app_host_and_clearer():
    calls = []
    app = object()
    host = object()
    clear_host = object()

    callback = radio_tab._make_radio_embedded_panel_callback(
        app,
        host,
        clear_host,
        panel_shower=lambda app_arg, host_arg, clear_arg: calls.append(
            (app_arg, host_arg, clear_arg)
        ),
    )

    callback()

    assert calls == [(app, host, clear_host)]


def test_make_radio_embedded_panel_callback_invokes_shower_each_time():
    calls = []

    callback = radio_tab._make_radio_embedded_panel_callback(
        object(),
        object(),
        object(),
        panel_shower=lambda _app, _host, _clear: calls.append("show"),
    )

    callback()
    callback()

    assert calls == ["show", "show"]


def test_radio_launcher_runtime_state_reads_radio_core():
    class DummyCore:
        def radio_is_detached(self):
            return True

        def read_radio_host_state(self):
            return {"launcher_state": "detaching"}

    app = type("DummyApp", (), {"netmon_radio_core": DummyCore()})()

    assert radio_tab._radio_launcher_runtime_state(app) == (True, "detaching")


def test_radio_launcher_runtime_state_handles_core_failures():
    class DummyCore:
        def radio_is_detached(self):
            raise RuntimeError("boom")

        def read_radio_host_state(self):
            raise RuntimeError("boom")

    app = type("DummyApp", (), {"netmon_radio_core": DummyCore()})()

    assert radio_tab._radio_launcher_runtime_state(app) == (False, "")


def test_radio_launcher_target_mode_selects_detached_for_detached_state():
    assert radio_tab._radio_launcher_target_mode(True, "") == "detached"
    assert radio_tab._radio_launcher_target_mode(False, "detaching") == "detached"


def test_radio_launcher_target_mode_selects_embedded_for_attached_states():
    assert radio_tab._radio_launcher_target_mode(False, "") == "embedded"
    assert radio_tab._radio_launcher_target_mode(False, "attaching") == "embedded"


def test_refresh_radio_launcher_state_sets_status_and_shows_detached():
    events = []

    class DummyVar:
        def set(self, value):
            events.append(("set", value))

    class DummyCore:
        def radio_is_detached(self):
            events.append("detached")
            return True

        def read_radio_host_state(self):
            events.append("state")
            return {"launcher_state": ""}

    class DummyApp:
        def __init__(self):
            self.radio_launcher_status_var = DummyVar()
            self.netmon_radio_core = DummyCore()

        def tr(self, key, fallback):
            events.append(("tr", key, fallback))
            return f"translated:{key}"

    radio_tab._refresh_radio_launcher_state(
        DummyApp(),
        lambda: events.append("show_detached"),
        lambda: events.append("show_embedded"),
    )

    assert events == [
        "detached",
        "state",
        (
            "tr",
            "radio_status_detached",
            "Radio-App ist geloest und laeuft als Standalone weiter.",
        ),
        ("set", "translated:radio_status_detached"),
        "show_detached",
    ]


def test_refresh_radio_launcher_state_sets_status_and_shows_embedded():
    events = []

    class DummyVar:
        def set(self, value):
            events.append(("set", value))

    class DummyCore:
        def radio_is_detached(self):
            events.append("detached")
            return False

        def read_radio_host_state(self):
            events.append("state")
            return {"launcher_state": ""}

    app = type("DummyApp", (), {})()
    app.radio_launcher_status_var = DummyVar()
    app.netmon_radio_core = DummyCore()

    radio_tab._refresh_radio_launcher_state(
        app,
        lambda: events.append("show_detached"),
        lambda: events.append("show_embedded"),
    )

    assert events == [
        "detached",
        "state",
        ("set", "Radio-App ist an NetMon angeheftet."),
        "show_embedded",
    ]


def test_make_radio_launcher_refresh_callback_binds_refresh_dependencies():
    calls = []
    app = object()
    show_detached = object()
    show_embedded = object()

    callback = radio_tab._make_radio_launcher_refresh_callback(
        app,
        show_detached,
        show_embedded,
        launcher_refresher=lambda app_arg, detached_arg, embedded_arg: calls.append(
            (app_arg, detached_arg, embedded_arg)
        ),
    )

    callback()

    assert calls == [(app, show_detached, show_embedded)]


def test_make_radio_launcher_refresh_callback_invokes_refresher_each_time():
    calls = []

    callback = radio_tab._make_radio_launcher_refresh_callback(
        object(),
        object(),
        object(),
        launcher_refresher=lambda _app, _detached, _embedded: calls.append("refresh"),
    )

    callback()
    callback()

    assert calls == ["refresh", "refresh"]


def test_build_radio_tab_scaffold_builds_sections_initializes_and_shows_bottom():
    events = []
    app = type("DummyApp", (), {})()
    body = object()
    status_var = object()
    pane = object()
    top_section = object()
    host = object()
    bottom_section = object()

    def show_bottom_placeholder():
        events.append("show_bottom")

    result = radio_tab._build_radio_tab_scaffold(
        app,
        body_builder=lambda app_arg: events.append(("body", app_arg)) or body,
        status_var_factory=lambda app_arg: events.append(("status", app_arg))
        or status_var,
        pane_builder=lambda app_arg, body_arg: events.append(
            ("pane", app_arg, body_arg)
        )
        or pane,
        sections_builder=lambda pane_arg, app_arg: events.append(
            ("sections", pane_arg, app_arg)
        )
        or (top_section, host, bottom_section),
        bottom_callback_factory=lambda app_arg, bottom_arg: events.append(
            ("bottom_callback", app_arg, bottom_arg)
        )
        or show_bottom_placeholder,
        pane_sections_adder=lambda pane_arg, top_arg, bottom_arg: events.append(
            ("add", pane_arg, top_arg, bottom_arg)
        ),
        state_initializer=lambda app_arg, **kwargs: events.append(
            ("state", app_arg, kwargs)
        ),
    )

    assert result == (host, show_bottom_placeholder)
    assert app.radio_launcher_status_var is status_var
    assert events == [
        ("body", app),
        ("status", app),
        ("pane", app, body),
        ("sections", pane, app),
        ("bottom_callback", app, bottom_section),
        ("add", pane, top_section, bottom_section),
        (
            "state",
            app,
            {
                "host": host,
                "top_section": top_section,
                "bottom_section": bottom_section,
            },
        ),
        "show_bottom",
    ]


def test_build_radio_tab_scaffold_returns_host_and_bottom_callback():
    app = type("DummyApp", (), {})()
    host = object()

    def show_bottom_placeholder():
        pass

    result = radio_tab._build_radio_tab_scaffold(
        app,
        body_builder=lambda _app: "body",
        status_var_factory=lambda _app: "status",
        pane_builder=lambda _app, _body: "pane",
        sections_builder=lambda _pane, _app: ("top", host, "bottom"),
        bottom_callback_factory=lambda _app, _bottom: show_bottom_placeholder,
        pane_sections_adder=lambda _pane, _top, _bottom: None,
        state_initializer=lambda _app, **_kwargs: None,
    )

    assert result == (host, show_bottom_placeholder)


def test_install_radio_launcher_refresh_wires_assigns_and_runs_refresh():
    events = []
    app = type("DummyApp", (), {})()
    host = object()
    show_bottom = object()
    clear_host = object()
    show_detached = object()
    show_embedded = object()

    def refresh_radio_launcher_state():
        events.append("refresh")

    result = radio_tab._install_radio_launcher_refresh(
        app,
        host,
        show_bottom,
        host_clear_callback_factory=lambda app_arg, host_arg, bottom_arg: events.append(
            ("clear_factory", app_arg, host_arg, bottom_arg)
        )
        or clear_host,
        detached_callback_factory=lambda app_arg, host_arg, clear_arg: events.append(
            ("detached_factory", app_arg, host_arg, clear_arg)
        )
        or show_detached,
        embedded_callback_factory=lambda app_arg, host_arg, clear_arg: events.append(
            ("embedded_factory", app_arg, host_arg, clear_arg)
        )
        or show_embedded,
        refresh_callback_factory=lambda app_arg, detached_arg, embedded_arg: events.append(
            ("refresh_factory", app_arg, detached_arg, embedded_arg)
        )
        or refresh_radio_launcher_state,
    )

    assert result is refresh_radio_launcher_state
    assert app.refresh_radio_launcher_state is refresh_radio_launcher_state
    assert events == [
        ("clear_factory", app, host, show_bottom),
        ("detached_factory", app, host, clear_host),
        ("embedded_factory", app, host, clear_host),
        ("refresh_factory", app, show_detached, show_embedded),
        "refresh",
    ]


def test_install_radio_launcher_refresh_returns_assigned_callback():
    app = type("DummyApp", (), {})()

    def refresh_radio_launcher_state():
        pass

    result = radio_tab._install_radio_launcher_refresh(
        app,
        object(),
        object(),
        host_clear_callback_factory=lambda _app, _host, _bottom: "clear",
        detached_callback_factory=lambda _app, _host, _clear: "detached",
        embedded_callback_factory=lambda _app, _host, _clear: "embedded",
        refresh_callback_factory=lambda _app, _detached, _embedded: refresh_radio_launcher_state,
    )

    assert result is refresh_radio_launcher_state
    assert app.refresh_radio_launcher_state is refresh_radio_launcher_state


def test_clear_radio_host_stops_panel_and_destroys_children():
    events = []

    class DummyPanel:
        def stop_radio_playback(self, async_mode=False):
            events.append(("stop", async_mode))

    class DummyChild:
        def __init__(self, name):
            self.name = name

        def destroy(self):
            events.append(("destroy", self.name))

    class DummyHost:
        def winfo_children(self):
            return [DummyChild("one"), DummyChild("two")]

    radio_tab._clear_radio_host(DummyHost(), DummyPanel())

    assert events == [
        ("stop", False),
        ("destroy", "one"),
        ("destroy", "two"),
    ]


def test_clear_radio_host_ignores_stop_and_destroy_failures():
    class FailingPanel:
        def stop_radio_playback(self, async_mode=False):
            raise RuntimeError("stop failed")

    class FailingChild:
        def destroy(self):
            raise RuntimeError("destroy failed")

    class DummyHost:
        def winfo_children(self):
            return [FailingChild()]

    radio_tab._clear_radio_host(DummyHost(), FailingPanel())


def test_clear_radio_tab_host_stops_panel_resets_state_and_shows_placeholder():
    events = []

    class DummyPanel:
        def stop_radio_playback(self, async_mode=False):
            events.append(("stop", async_mode))

    class DummyChild:
        def destroy(self):
            events.append("destroy")

    class DummyHost:
        def winfo_children(self):
            return [DummyChild()]

    app = type("DummyApp", (), {})()
    app.radio_embedded_panel = DummyPanel()

    radio_tab._clear_radio_tab_host(
        app,
        DummyHost(),
        lambda: events.append("placeholder"),
    )

    assert app.radio_embedded_panel is None
    assert events == [("stop", False), "destroy", "placeholder"]


def test_clear_radio_tab_host_handles_missing_panel_and_shows_placeholder():
    events = []

    class DummyChild:
        def destroy(self):
            events.append("destroy")

    class DummyHost:
        def winfo_children(self):
            return [DummyChild()]

    app = type("DummyApp", (), {})()

    radio_tab._clear_radio_tab_host(
        app,
        DummyHost(),
        lambda: events.append("placeholder"),
    )

    assert app.radio_embedded_panel is None
    assert events == ["destroy", "placeholder"]


def test_make_radio_tab_host_clear_callback_binds_app_host_and_placeholder():
    calls = []
    app = object()
    host = object()
    show_bottom_placeholder = object()

    callback = radio_tab._make_radio_tab_host_clear_callback(
        app,
        host,
        show_bottom_placeholder,
        host_clearer=lambda app_arg, host_arg, placeholder_arg: calls.append(
            (app_arg, host_arg, placeholder_arg)
        ),
    )

    callback()

    assert calls == [(app, host, show_bottom_placeholder)]


def test_make_radio_tab_host_clear_callback_invokes_clearer_each_time():
    calls = []

    callback = radio_tab._make_radio_tab_host_clear_callback(
        object(),
        object(),
        object(),
        host_clearer=lambda _app, _host, _placeholder: calls.append("clear"),
    )

    callback()
    callback()

    assert calls == ["clear", "clear"]


def test_show_radio_bottom_placeholder_replaces_children_with_label():
    events = []

    class DummyChild:
        def __init__(self, name):
            self.name = name

        def destroy(self):
            events.append(("destroy", self.name))

    class DummyContainer:
        def winfo_children(self):
            return [DummyChild("old")]

    class DummyLabel:
        def __init__(self, container, **kwargs):
            events.append(("label", container, kwargs))

        def grid(self, **kwargs):
            events.append(("grid", kwargs))

    container = DummyContainer()

    label = radio_tab._show_radio_bottom_placeholder(
        container,
        "reserved",
        label_factory=DummyLabel,
    )

    assert isinstance(label, DummyLabel)
    assert events == [
        ("destroy", "old"),
        (
            "label",
            container,
            {"text": "reserved", "justify": "left", "wraplength": 900},
        ),
        ("grid", {"row": 0, "column": 0, "sticky": "nw"}),
    ]


def test_show_radio_bottom_placeholder_ignores_destroy_failures():
    class FailingChild:
        def destroy(self):
            raise RuntimeError("destroy failed")

    class DummyContainer:
        def winfo_children(self):
            return [FailingChild()]

    class DummyLabel:
        def __init__(self, container, **kwargs):
            pass

        def grid(self, **kwargs):
            pass

    radio_tab._show_radio_bottom_placeholder(
        DummyContainer(),
        "reserved",
        label_factory=DummyLabel,
    )


def test_show_radio_bottom_placeholder_for_app_uses_translated_text():
    events = []

    class DummyApp:
        def tr(self, key, fallback):
            events.append(("tr", key, fallback))
            return "translated placeholder"

    class DummyContainer:
        def winfo_children(self):
            events.append("children")
            return []

    class DummyLabel:
        def __init__(self, container, **kwargs):
            events.append(("label", container, kwargs))

        def grid(self, **kwargs):
            events.append(("grid", kwargs))

    container = DummyContainer()

    label = radio_tab._show_radio_bottom_placeholder_for_app(
        container,
        DummyApp(),
        label_factory=DummyLabel,
    )

    assert isinstance(label, DummyLabel)
    assert events == [
        (
            "tr",
            "radio_bottom_media_hint",
            "This lower area is reserved for playlists and files.",
        ),
        "children",
        (
            "label",
            container,
            {"text": "translated placeholder", "justify": "left", "wraplength": 900},
        ),
        ("grid", {"row": 0, "column": 0, "sticky": "nw"}),
    ]


def test_show_radio_bottom_placeholder_for_app_replaces_existing_children():
    events = []

    class DummyApp:
        def tr(self, key, fallback):
            return fallback

    class DummyChild:
        def destroy(self):
            events.append("destroy")

    class DummyContainer:
        def winfo_children(self):
            return [DummyChild()]

    class DummyLabel:
        def __init__(self, container, **kwargs):
            events.append(("label", kwargs["text"]))

        def grid(self, **kwargs):
            events.append(("grid", kwargs))

    radio_tab._show_radio_bottom_placeholder_for_app(
        DummyContainer(),
        DummyApp(),
        label_factory=DummyLabel,
    )

    assert events == [
        "destroy",
        ("label", "This lower area is reserved for playlists and files."),
        ("grid", {"row": 0, "column": 0, "sticky": "nw"}),
    ]


def test_make_radio_bottom_placeholder_callback_binds_app_and_section():
    calls = []
    app = object()
    bottom_section = object()

    callback = radio_tab._make_radio_bottom_placeholder_callback(
        app,
        bottom_section,
        placeholder_shower=lambda container, app_arg: calls.append(
            (container, app_arg)
        ),
    )

    callback()

    assert calls == [(bottom_section, app)]


def test_make_radio_bottom_placeholder_callback_invokes_shower_each_time():
    calls = []

    callback = radio_tab._make_radio_bottom_placeholder_callback(
        object(),
        object(),
        placeholder_shower=lambda _container, _app: calls.append("show"),
    )

    callback()
    callback()

    assert calls == ["show", "show"]
