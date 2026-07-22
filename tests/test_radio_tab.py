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


def test_schedule_initial_radio_pane_marker_update_uses_after_zero():
    calls = []
    callback = object()

    class DummyContainer:
        def after(self, delay, scheduled_callback):
            calls.append((delay, scheduled_callback))

    radio_tab._schedule_initial_radio_pane_marker_update(
        DummyContainer(),
        callback,
    )

    assert calls == [(0, callback)]


def test_schedule_initial_radio_pane_marker_update_ignores_after_failures():
    class DummyContainer:
        def after(self, delay, scheduled_callback):
            raise RuntimeError("after failed")

    radio_tab._schedule_initial_radio_pane_marker_update(
        DummyContainer(),
        object(),
    )


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
