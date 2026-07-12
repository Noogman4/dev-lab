import json
from pathlib import Path

from netmon.app import App

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _tour_app():
    app = App.__new__(App)
    app.tr = lambda _key, default=None: default or _key
    return app


def test_secure_browser_tour_is_available_in_setup_and_full_tour():
    app = _tour_app()

    launcher_ids = [
        tour_id
        for _group_title, items in app._guided_tour_launcher_specs()
        for tour_id, _label in items
    ]
    definitions = app._guided_tour_definitions()
    secure_steps = definitions["tab-secure-browser"]["steps"]
    full_tour_titles = [
        str(step.get("title") or "") for step in definitions["full-tour"]["steps"]
    ]

    assert "tab-secure-browser" in launcher_ids
    assert len(secure_steps) == 9
    assert "Privatsphäregewinn durch die Installation" in full_tour_titles
    assert "Wichtige Schutzgrenzen" in full_tour_titles


def test_secure_browser_tour_has_all_privacy_topics_in_both_languages():
    required_keys = {
        "tour_launcher_secure_browser",
        "tour_tab_title_secure_browser",
        "tour_tab_label_secure_browser",
        "tour_tab_desc_secure_browser",
        "tour_tab_hint_secure_browser",
        "tour_tab_secure_browser_gain_title",
        "tour_tab_secure_browser_gain_body",
        "tour_tab_secure_browser_hardening_title",
        "tour_tab_secure_browser_hardening_body",
        "tour_tab_secure_browser_filter_title",
        "tour_tab_secure_browser_filter_body",
        "tour_tab_secure_browser_persistence_title",
        "tour_tab_secure_browser_persistence_body",
        "tour_tab_secure_browser_dry_run_title",
        "tour_tab_secure_browser_dry_run_body",
        "tour_tab_secure_browser_limits_title",
        "tour_tab_secure_browser_limits_body",
    }

    for language in ("de", "en"):
        path = PROJECT_ROOT / "netmon" / "lang" / f"{language}.json"
        translations = json.loads(path.read_text(encoding="utf-8"))

        assert required_keys <= translations.keys()
        assert all(str(translations[key]).strip() for key in required_keys)

    de = json.loads(
        (PROJECT_ROOT / "netmon" / "lang" / "de.json").read_text(encoding="utf-8")
    )
    en = json.loads(
        (PROJECT_ROOT / "netmon" / "lang" / "en.json").read_text(encoding="utf-8")
    )
    assert "nicht anonym" in de["tour_tab_secure_browser_limits_body"]
    assert "does not make you anonymous" in en["tour_tab_secure_browser_limits_body"]
