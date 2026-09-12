from types import SimpleNamespace

from netmon.ui.tour_specs import (
    build_guided_tab_tour_steps,
    build_guided_tour_primary_definitions,
    build_guided_tour_tab_definitions,
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
    prepare = object()

    def action():
        return None

    app = SimpleNamespace(
        tr=lambda _key, default=None: default,
        _guided_tour_tab_prepare_callable=lambda selector, tab_attr: (
            prepare,
            selector,
            tab_attr,
        ),
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

    expected_prepare = (prepare, "security", "tab_security")
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
