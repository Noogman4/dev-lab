from types import SimpleNamespace

from netmon.ui.tour_specs import build_guided_tour_primary_definitions


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
