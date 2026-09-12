"""Guided tour definition helpers."""

from __future__ import annotations


def build_guided_tour_primary_definitions(app) -> dict:
    return {
        "quickstart": {
            "id": "quickstart",
            "title": app.tr("tour_def_quickstart_title", "NetMon Schnellstart"),
            "steps": app._build_quickstart_tour_steps(),
        },
        "dns": {
            "id": "dns",
            "title": app.tr("tour_def_dns_title", "NetMon DNS Tour"),
            "steps": app._build_dns_tour_steps(),
        },
        "security": {
            "id": "security",
            "title": app.tr("tour_def_security_title", "NetMon Security Tour"),
            "steps": app._build_security_tour_steps(),
        },
        "download-scan": {
            "id": "download-scan",
            "title": app.tr("tour_def_download_scan_title", "NetMon D-Scan Tour"),
            "steps": app._build_download_scan_tour_steps(),
        },
        "radio": {
            "id": "radio",
            "title": app.tr("tour_def_radio_title", "NetMon Radio Tour"),
            "steps": app._build_radio_tour_steps(),
        },
    }


def build_guided_tour_tab_definitions(app) -> dict:
    """Build guided-tour definitions from the app's tab tour specifications."""
    definitions = {}
    for spec in app._guided_tour_tab_specs():
        tour_id = str(spec.get("id") or "").strip().lower()
        if not tour_id:
            continue
        definitions[tour_id] = {
            "id": tour_id,
            "title": str(spec.get("tour_title") or "NetMon Tab Tour").strip(),
            "steps": app._build_guided_tab_tour_steps(spec),
        }
    return definitions
