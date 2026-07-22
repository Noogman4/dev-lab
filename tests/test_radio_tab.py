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
