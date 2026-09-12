from types import SimpleNamespace

from netmon.ui.tour_specs import (
    build_full_tour_steps,
    build_guided_tab_tour_steps,
    build_guided_tour_full_sequence,
    build_guided_tour_primary_definitions,
    build_guided_tour_tab_prepare_callable,
    build_guided_tour_tab_definitions,
    guided_tour_button_text,
    guided_tour_status_symbol,
    guided_tour_status_text,
    guided_tour_title_text,
)


def test_build_guided_tour_primary_definitions_uses_app_translations_and_steps():
    calls = []

    def tr(key, default=None):
        return f"{key}:{default}"

    def steps(name):
        def _builder():
            calls.append(name)
            return [{"step": name}]

        return _builder

    app = SimpleNamespace(
        tr=tr,
        _build_quickstart_tour_steps=steps("quickstart"),
        _build_dns_tour_steps=steps("dns"),
        _build_security_tour_steps=steps("security"),
        _build_download_scan_tour_steps=steps("download-scan"),
        _build_radio_tour_steps=steps("radio"),
    )

    definitions = build_guided_tour_primary_definitions(app)

    assert list(definitions) == [
        "quickstart",
        "dns",
        "security",
        "download-scan",
        "radio",
    ]
    assert definitions["quickstart"]["id"] == "quickstart"
    assert (
        definitions["quickstart"]["title"]
        == "tour_def_quickstart_title:NetMon Schnellstart"
    )
    assert definitions["radio"]["title"] == "tour_def_radio_title:NetMon Radio Tour"
    assert definitions["download-scan"]["steps"] == [{"step": "download-scan"}]
    assert calls == ["quickstart", "dns", "security", "download-scan", "radio"]


def test_guided_tour_launcher_presentation_helpers_mark_completed_tours():
    app = SimpleNamespace(
        tr=lambda _key, default=None: default,
        is_guided_tour_completed=lambda tour_name: tour_name == "completed",
    )

    assert guided_tour_button_text(app, "completed", "Long label") == "Start"
    assert guided_tour_status_symbol(True) == "[x]"
    assert guided_tour_status_symbol(False) == "[ ]"
    assert guided_tour_title_text(app, "completed", " Tour ") == "Tour abgeschlossen"
    assert guided_tour_title_text(app, "open", " Tour ") == "Tour"
    assert guided_tour_title_text(app, "open", " ") == ""


def test_guided_tour_status_text_covers_mixed_all_and_no_completion():
    def build_app(completed):
        return SimpleNamespace(
            tr=lambda _key, default=None: default,
            is_guided_tour_completed=lambda tour_name: tour_name in completed,
        )

    assert guided_tour_status_text(build_app({"dns"})) == (
        "Tourstatus: abgeschlossen: DNS | offen: Volle Tour, Schnellstart, "
        "Security, D-Scan, Radio"
    )
    assert (
        guided_tour_status_text(
            build_app(
                {"full-tour", "quickstart", "dns", "security", "download-scan", "radio"}
            )
        )
        == "Tourstatus: alle verfügbaren Touren abgeschlossen."
    )
    assert (
        guided_tour_status_text(build_app(set()))
        == "Tourstatus: noch keine Tour abgeschlossen."
    )


def test_full_tour_helpers_keep_launcher_order_and_surround_selected_steps():
    selections = []
    app = SimpleNamespace(
        tr=lambda _key, default=None: default,
        _guided_tour_launcher_specs=lambda: [
            ("Primary", [("quickstart", "Quick"), (" DNS ", "DNS")]),
            ("Other", [("full-tour", "Full"), ("radio", "Radio"), ("", "")]),
        ],
        nb=SimpleNamespace(select=selections.append),
        tab_settings="settings-tab",
    )
    definitions = {
        "dns": {"steps": [{"title": "DNS step"}]},
        "radio": "invalid",
    }

    sequence = build_guided_tour_full_sequence(app)
    steps = build_full_tour_steps(app, definitions)

    assert sequence == ["dns", "radio"]
    assert [step["title"] for step in steps] == [
        "NetMon Volle Tour",
        "DNS step",
        "Volle Tour abgeschlossen",
    ]
    steps[0]["prepare"]()
    steps[-1]["prepare"]()
    assert selections == ["settings-tab", "settings-tab"]


def test_build_guided_tour_tab_definitions_skips_blank_ids_and_builds_steps():
    calls = []
    specs = [
        {"id": " System ", "tour_title": "System Tour"},
        {"id": "", "tour_title": "Ignored"},
        {"tour_title": "Also ignored"},
        {"id": "dns"},
    ]
    app = SimpleNamespace(
        _guided_tour_tab_specs=lambda: specs,
        _build_guided_tab_tour_steps=lambda spec: calls.append(spec["id"])
        or [{"step": spec["id"]}],
    )

    definitions = build_guided_tour_tab_definitions(app)

    assert definitions == {
        "system": {
            "id": "system",
            "title": "System Tour",
            "steps": [{"step": " System "}],
        },
        "dns": {
            "id": "dns",
            "title": "NetMon Tab Tour",
            "steps": [{"step": "dns"}],
        },
    }
    assert calls == [" System ", "dns"]


def test_build_guided_tab_tour_steps_builds_actions_and_detail_steps():
    selections = []

    def action():
        return None

    app = SimpleNamespace(
        tr=lambda _key, default=None: default,
        tab_security="security-tab",
        _select_security_tab=lambda tab: selections.append(("security", tab)),
    )
    spec = {
        "tab_title": " Security ",
        "description": " Overview ",
        "hint": "Hint",
        "target": "target-widget",
        "tab_attr": "tab_security",
        "selector": " SECURITY ",
        "action": action,
        "action_label": "Run",
        "action_success": "Done",
        "action_failure": "Failed",
        "detail_steps": [
            {"title": "Detail"},
            "ignored",
            {"title": "Custom", "prepare": "custom-prepare"},
        ],
    }

    steps = build_guided_tab_tour_steps(app, spec)

    expected_prepare = steps[0]["prepare"]
    assert [step["title"] for step in steps] == [
        "Security im Überblick",
        "Security",
        "Detail",
        "Custom",
        "Security abgeschlossen",
    ]
    assert steps[0]["prepare"] == expected_prepare
    assert steps[1]["target"] == "target-widget"
    assert steps[1]["body"] == "Overview"
    assert steps[1]["action"] is action
    assert steps[1]["action_label"] == "Run"
    assert steps[1]["action_success"] == "Done"
    assert steps[1]["action_failure"] == "Failed"
    assert steps[2]["prepare"] == expected_prepare
    assert steps[3]["prepare"] == "custom-prepare"
    expected_prepare()
    assert selections == [("security", "security-tab")]


def test_build_guided_tour_tab_prepare_callable_selects_expected_tab_area():
    calls = []
    app = SimpleNamespace(
        tab_top="top-tab",
        tab_system="system-tab",
        tab_tools="tools-tab",
        tab_security="security-tab",
        nb=SimpleNamespace(select=lambda tab: calls.append(("top", tab))),
        _select_system_tab=lambda tab: calls.append(("system", tab)),
        _select_tools_tab=lambda tab: calls.append(("tools", tab)),
        _select_security_tab=lambda tab: calls.append(("security", tab)),
    )

    build_guided_tour_tab_prepare_callable(app, "", "tab_top")()
    build_guided_tour_tab_prepare_callable(app, "system", "tab_system")()
    build_guided_tour_tab_prepare_callable(app, "tools", "tab_tools")()
    build_guided_tour_tab_prepare_callable(app, "security", "tab_security")()
    build_guided_tour_tab_prepare_callable(app, "tools", "missing")()

    assert calls == [
        ("top", "top-tab"),
        ("system", "system-tab"),
        ("tools", "tools-tab"),
        ("security", "security-tab"),
    ]
