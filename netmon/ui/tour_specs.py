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
