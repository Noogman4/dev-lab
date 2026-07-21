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
