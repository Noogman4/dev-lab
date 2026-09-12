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


def guided_tour_button_text(app, _tour_name, _base_label) -> str:
    """Return the compact command label used by guided-tour launchers."""
    return app.tr("guided_tour_btn_start_short", "Start")


def guided_tour_status_symbol(completed: bool) -> str:
    """Return the compact completion marker for a guided tour."""
    return "[x]" if completed else "[ ]"


def guided_tour_title_text(app, tour_name, base_label) -> str:
    """Return a launcher title, marking completed tours when applicable."""
    label = str(base_label or "").strip()
    if not label:
        return ""
    if app.is_guided_tour_completed(tour_name):
        return app.tr("tour_status_title_completed", "{label} abgeschlossen").format(
            label=label
        )
    return label


def build_guided_tour_full_sequence(app) -> list[str]:
    """Return eligible launcher tour IDs in their configured order."""
    sequence = []
    for _group_title, tours in app._guided_tour_launcher_specs():
        for tour_id, _label in tours:
            normalized = str(tour_id or "").strip().lower()
            if normalized in {"", "full-tour", "quickstart"}:
                continue
            sequence.append(normalized)
    return sequence


def build_full_tour_steps(app, definitions: dict) -> list[dict]:
    """Build the full-tour frame around steps from eligible tour definitions."""
    steps = [
        {
            "title": app.tr("tour_full_step_intro_title", "NetMon Volle Tour"),
            "body": app.tr(
                "tour_full_step_intro_body",
                "Diese Führung arbeitet die im Tour-Tab erfassten Bereiche der Reihe nach ab. Sie ist deutlich ausführlicher als der schnelle Einstieg und eignet sich für einen kompletten Rundgang.",
            ),
            "prepare": lambda: app.nb.select(app.tab_settings),
        }
    ]
    for tour_id in build_guided_tour_full_sequence(app):
        selected = definitions.get(tour_id)
        if not isinstance(selected, dict):
            continue
        steps.extend(list(selected.get("steps") or []))
    steps.append(
        {
            "title": app.tr("tour_full_step_done_title", "Volle Tour abgeschlossen"),
            "body": app.tr(
                "tour_full_step_done_body",
                "Du hast jetzt alle aktuell erfassten Tour-Bereiche einmal der Reihe nach durchlaufen. Für einzelne Themen kannst du später gezielt in die Spezial- oder Tab-Touren zurückspringen.",
            ),
            "prepare": lambda: app.nb.select(app.tab_settings),
        }
    )
    return steps


def build_guided_tour_tab_prepare_callable(app, selector: str, tab_attr: str):
    """Build a callback that selects the requested top-level or nested tab."""

    def _prepare():
        tab = getattr(app, "__dict__", {}).get(tab_attr)
        if tab is None:
            return
        if selector == "system":
            app._select_system_tab(tab)
            return
        if selector == "tools":
            app._select_tools_tab(tab)
            return
        if selector == "security":
            app._select_security_tab(tab)
            return
        app.nb.select(tab)

    return _prepare


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
    prepare = build_guided_tour_tab_prepare_callable(
        app,
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
