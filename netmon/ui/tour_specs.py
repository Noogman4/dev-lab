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


def build_guided_tab_tour_steps(app, spec: dict) -> list[dict]:
    """Build the common overview, target and completion steps for a tab tour."""
    tab_title = str(spec.get("tab_title") or "Tab").strip() or "Tab"
    description = str(spec.get("description") or "").strip()
    hint = spec.get("hint")
    target = spec.get("target") or spec.get("tab_attr")
    prepare = app._guided_tour_tab_prepare_callable(
        str(spec.get("selector") or "").strip().lower(),
        str(spec.get("tab_attr") or "").strip(),
    )
    steps = [
        {
            "title": app.tr(
                "tour_tab_overview_title",
                "{tab_title} im Überblick",
            ).format(tab_title=tab_title),
            "body": app.tr(
                "tour_tab_overview_body",
                "Diese Mini-Tour führt dich gezielt durch den Bereich {tab_title}. Sie erklärt kurz Zweck, Einordnung und den sinnvollsten Einstieg.",
            ).format(tab_title=tab_title),
            "prepare": prepare,
        },
        {
            "target": target,
            "title": tab_title,
            "body": description,
            "hint": hint,
            "prepare": prepare,
        },
        {
            "title": app.tr(
                "tour_tab_done_title",
                "{tab_title} abgeschlossen",
            ).format(tab_title=tab_title),
            "body": app.tr(
                "tour_tab_done_body",
                "Du hast jetzt den Bereich {tab_title} eingeordnet. Als nächster Schritt lohnt sich meist ein kurzer Praxistest oder der Wechsel in einen angrenzenden Fachbereich.",
            ).format(tab_title=tab_title),
            "hint": app.tr(
                "tour_tab_done_hint",
                "Diese Mini-Tour kannst du später erneut starten, wenn du den Bereich wieder einordnen willst.",
            ),
            "prepare": prepare,
        },
    ]
    action = spec.get("action")
    action_label = spec.get("action_label")
    if callable(action) and action_label:
        steps[1]["action"] = action
        steps[1]["action_label"] = action_label
        if spec.get("action_success"):
            steps[1]["action_success"] = spec.get("action_success")
        if spec.get("action_failure"):
            steps[1]["action_failure"] = spec.get("action_failure")
    detail_steps = spec.get("detail_steps") or []
    if detail_steps:
        normalized_steps = []
        for raw_step in detail_steps:
            if not isinstance(raw_step, dict):
                continue
            step = dict(raw_step)
            step.setdefault("prepare", prepare)
            normalized_steps.append(step)
        if normalized_steps:
            steps = steps[:-1] + normalized_steps + steps[-1:]
    return steps
