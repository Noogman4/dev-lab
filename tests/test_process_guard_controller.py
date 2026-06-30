from netmon.features import process_guard_controller
from netmon.app import App


class DummyTreeview:
    def __init__(self):
        self.rows = []
        self._selection = []

    def get_children(self):
        return [row["iid"] for row in self.rows]

    def delete(self, item_id):
        self.rows = [row for row in self.rows if row["iid"] != item_id]

    def insert(self, _parent, _index, iid=None, values=()):
        self.rows.append({"iid": iid, "values": values})

    def selection(self):
        return list(self._selection)

    def index(self, item_id):
        for index, row in enumerate(self.rows):
            if row["iid"] == item_id:
                return index
        return -1


class DummyText:
    def __init__(self):
        self.value = ""
        self.states = []

    def configure(self, state=None, **_kwargs):
        if state is not None:
            self.states.append(state)

    def delete(self, *_args):
        self.value = ""

    def insert(self, *_args):
        self.value += _args[-1]

    def see(self, *_args):
        return None

    def index(self, _value):
        return "1.0" if not self.value else "2.0"


def test_refresh_process_guard_tree_populates_rows():
    app = type("DummyApp", (), {})()
    app.process_guard_tree = DummyTreeview()
    app.process_guard_filter_mode = "all"
    app.process_guard_selected_finding = {"pid": 1}
    app.process_guard_last_result = {
        "findings": [
            {
                "risk_level": "high",
                "pid": 42,
                "name": "bash",
                "user": "sven",
                "exe": "/usr/bin/bash",
            }
        ]
    }
    app.process_guard_visible_findings = []

    process_guard_controller.refresh_process_guard_tree(app)

    assert len(app.process_guard_tree.rows) == 1
    assert app.process_guard_tree.rows[0]["values"][0] == "HIGH"
    assert app.process_guard_visible_findings[0]["pid"] == 42
    assert app.process_guard_selected_finding is None


def test_on_process_guard_select_writes_details():
    app = type("DummyApp", (), {})()
    app.process_guard_tree = DummyTreeview()
    app.process_guard_tree.rows = [{"iid": "pg-0", "values": ()}]
    app.process_guard_tree._selection = ["pg-0"]
    app.process_guard_visible_findings = [
        {
            "pid": 42,
            "ppid": 1,
            "name": "bash",
            "user": "sven",
            "risk_level": "high",
            "risk_score": 9,
            "exe": "/usr/bin/bash",
            "cwd": "/tmp",
            "parent_name": "firefox",
            "cmdline": ["bash", "/tmp/run.sh"],
            "reasons": ["Ausführung aus temporärem Pfad: /tmp/run.sh"],
        }
    ]
    app.security_detail = DummyText()
    app.process_guard_selected_finding = None

    process_guard_controller.on_process_guard_select(app)

    assert app.process_guard_selected_finding["pid"] == 42
    assert "=== Process Guard Fund ===" in app.security_detail.value
    assert "firefox" in app.security_detail.value


def test_refresh_process_guard_tree_respects_filter_mode():
    app = type("DummyApp", (), {})()
    app.process_guard_tree = DummyTreeview()
    app.process_guard_filter_mode = "high"
    app.process_guard_selected_finding = None
    app.process_guard_last_result = {
        "findings": [
            {"risk_level": "high", "pid": 1, "name": "bash", "user": "a", "exe": "/a"},
            {
                "risk_level": "medium",
                "pid": 2,
                "name": "python3",
                "user": "b",
                "exe": "/b",
            },
        ]
    }

    process_guard_controller.refresh_process_guard_tree(app)

    assert len(app.process_guard_tree.rows) == 1
    assert app.process_guard_tree.rows[0]["values"][1] == 1


def test_set_process_guard_filter_updates_mode_and_logs():
    app = type("DummyApp", (), {})()
    logs = []
    app.process_guard_filter_mode = "all"
    app.process_guard_monitoring = False
    app.log = logs.append
    app.process_guard_tree = DummyTreeview()
    app.process_guard_selected_finding = None
    app.process_guard_last_result = {"findings": []}
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    process_guard_controller.set_process_guard_filter(app, "high")

    assert app.process_guard_filter_mode == "high"
    assert logs == ["Process Guard: Filter aktiv - nur hohe Risiken."]
    assert app.process_guard_filter_status_var.value == "Filter: nur hoch"


def test_update_process_guard_status_line_sets_all_fields():
    app = type("DummyApp", (), {})()
    app.process_guard_monitoring = True
    app.process_guard_filter_mode = "high_medium"
    app.process_guard_visible_findings = [{"pid": 1}, {"pid": 2}]
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    process_guard_controller.update_process_guard_status_line(app)

    assert app.process_guard_monitoring_status_var.value == "Monitoring: aktiv"
    assert app.process_guard_filter_status_var.value == "Filter: hoch + mittel"
    assert app.process_guard_visible_count_var.value == "Sichtbare Funde: 2"


def test_analyze_selected_process_guard_with_chad_uses_selected_finding():
    app = type("DummyApp", (), {})()
    calls = []
    app.process_guard_selected_finding = {
        "pid": 42,
        "ppid": 1,
        "name": "bash",
        "user": "sven",
        "risk_level": "high",
        "risk_score": 9,
        "exe": "/usr/bin/bash",
        "cwd": "/tmp",
        "parent_name": "firefox",
        "cmdline": ["bash", "/tmp/run.sh"],
        "reasons": ["Ausführung aus temporärem Pfad: /tmp/run.sh"],
    }
    app.prepare_chad_analysis = lambda title, text: calls.append((title, text))

    process_guard_controller.analyze_selected_process_guard_with_chad(app)

    assert calls[0][0] == "Process Guard Fund Analyse"
    assert "=== Process Guard Fund ===" in calls[0][1]


def test_analyze_selected_process_guard_with_chad_logs_without_selection():
    app = type("DummyApp", (), {})()
    logs = []
    app.process_guard_selected_finding = None
    app.log = logs.append

    process_guard_controller.analyze_selected_process_guard_with_chad(app)

    assert logs == ["Process Guard: Kein Fund ausgewählt."]


def test_process_guard_trustlist_returns_safe_default_without_service():
    app = type("DummyApp", (), {})()

    assert process_guard_controller._process_guard_trustlist(app) == {"trusted": {}}


def test_process_guard_counts_group_findings_by_risk_level():
    counts = process_guard_controller._process_guard_counts(
        [
            {"risk_level": "high"},
            {"risk_level": "medium"},
            {"risk_level": "medium"},
            {"risk_level": "low"},
        ]
    )

    assert counts == {"high": 1, "medium": 2, "low": 1}


def test_process_guard_light_state_for_risk_maps_known_levels():
    assert process_guard_controller._process_guard_light_state_for_risk("hoch") == (
        "error",
        "Process Guard: verdächtige Prozesse erkannt",
    )
    assert process_guard_controller._process_guard_light_state_for_risk("mittel") == (
        "warning",
        "Process Guard: Prüfbedarf",
    )
    assert process_guard_controller._process_guard_light_state_for_risk("niedrig") == (
        "ok",
        "Process Guard: keine Auffälligkeiten",
    )


def test_process_guard_light_values_map_known_state_defaults():
    assert process_guard_controller._process_guard_light_values("warning") == (
        "yellow",
        "Process Guard: Prüfbedarf",
    )


def test_process_guard_light_values_use_gray_and_custom_message_for_unknown():
    assert process_guard_controller._process_guard_light_values(
        "mystery",
        "Eigene Meldung",
    ) == ("gray", "Eigene Meldung")


def test_process_guard_monitoring_status_message_returns_active_text():
    assert (
        process_guard_controller._process_guard_monitoring_status_message("active")
        == "Process Guard: Monitoring aktiv"
    )


def test_process_guard_monitoring_status_message_returns_stopped_text():
    assert (
        process_guard_controller._process_guard_monitoring_status_message("stopped")
        == "Process Guard: Monitoring gestoppt"
    )


def test_process_guard_monitoring_state_for_findings_covers_all_paths():
    assert process_guard_controller._process_guard_monitoring_state_for_findings(
        []
    ) == (
        "ok",
        "Process Guard: Monitoring aktiv, keine neuen Auffälligkeiten",
        "",
    )
    assert process_guard_controller._process_guard_monitoring_state_for_findings(
        [{"risk_level": "medium"}]
    ) == (
        "warning",
        "Process Guard: neue Prozesse mit Prüfbedarf",
        "Process Guard: 1 neuer Fund/Funde erkannt.",
    )
    assert process_guard_controller._process_guard_monitoring_state_for_findings(
        [{"risk_level": "high"}, {"risk_level": "low"}]
    ) == (
        "error",
        "Process Guard: neue verdächtige Prozesse erkannt",
        "Process Guard: 2 neuer Fund/Funde erkannt.",
    )


def test_process_guard_monitoring_status_text_maps_both_states():
    assert (
        process_guard_controller._process_guard_monitoring_status_text(True)
        == "Monitoring: aktiv"
    )
    assert (
        process_guard_controller._process_guard_monitoring_status_text(False)
        == "Monitoring: aus"
    )


def test_process_guard_filter_label_maps_status_and_log_variants():
    assert (
        process_guard_controller._process_guard_filter_label(
            "high_medium",
            context="status",
        )
        == "Filter: hoch + mittel"
    )
    assert (
        process_guard_controller._process_guard_filter_label(
            "high",
            context="log",
        )
        == "nur hohe Risiken"
    )


def test_process_guard_filter_label_falls_back_to_all_label():
    assert (
        process_guard_controller._process_guard_filter_label("unknown")
        == "Filter: alle"
    )
    assert (
        process_guard_controller._process_guard_filter_label("unknown", context="log")
        == "alle Funde"
    )


def test_process_guard_visible_findings_filters_high_and_medium():
    result = {
        "findings": [
            {"risk_level": "high", "pid": 1},
            {"risk_level": "medium", "pid": 2},
            {"risk_level": "low", "pid": 3},
        ]
    }

    assert process_guard_controller._process_guard_visible_findings(
        result,
        "high",
    ) == [{"risk_level": "high", "pid": 1}]
    assert process_guard_controller._process_guard_visible_findings(
        result,
        "high_medium",
    ) == [{"risk_level": "high", "pid": 1}, {"risk_level": "medium", "pid": 2}]


def test_process_guard_visible_findings_falls_back_to_all_findings():
    result = {"findings": [{"risk_level": "low", "pid": 3}]}

    assert process_guard_controller._process_guard_visible_findings(
        result,
        "unknown",
    ) == [{"risk_level": "low", "pid": 3}]
    assert process_guard_controller._process_guard_visible_findings({}, "all") == []


def test_process_guard_tree_row_values_formats_expected_columns():
    assert process_guard_controller._process_guard_tree_row_values(
        {
            "risk_level": "high",
            "pid": 42,
            "name": "bash",
            "user": "sven",
            "exe": "/usr/bin/bash",
        }
    ) == ("HIGH", 42, "bash", "sven", "/usr/bin/bash")


def test_process_guard_tree_row_values_use_safe_defaults():
    assert process_guard_controller._process_guard_tree_row_values({}) == (
        "-",
        "-",
        "-",
        "-",
        "-",
    )


def test_process_guard_visible_count_text_formats_list_length():
    assert (
        process_guard_controller._process_guard_visible_count_text(
            [{"pid": 1}, {"pid": 2}]
        )
        == "Sichtbare Funde: 2"
    )


def test_process_guard_visible_count_text_uses_zero_for_empty_values():
    assert process_guard_controller._process_guard_visible_count_text([]) == (
        "Sichtbare Funde: 0"
    )
    assert process_guard_controller._process_guard_visible_count_text(None) == (
        "Sichtbare Funde: 0"
    )


def test_normalized_process_guard_filter_mode_accepts_known_values():
    assert (
        process_guard_controller._normalized_process_guard_filter_mode(" high ")
        == "high"
    )
    assert (
        process_guard_controller._normalized_process_guard_filter_mode("high_medium")
        == "high_medium"
    )


def test_normalized_process_guard_filter_mode_falls_back_to_all():
    assert (
        process_guard_controller._normalized_process_guard_filter_mode("mystery")
        == "all"
    )
    assert process_guard_controller._normalized_process_guard_filter_mode("") == "all"


def test_process_guard_status_values_collect_all_status_fields():
    app = type("DummyApp", (), {})()
    app.process_guard_monitoring = True
    app.process_guard_filter_mode = "high_medium"
    app.process_guard_visible_findings = [{"pid": 1}, {"pid": 2}]

    assert process_guard_controller._process_guard_status_values(app) == {
        "monitoring": "Monitoring: aktiv",
        "filter": "Filter: hoch + mittel",
        "visible_count": "Sichtbare Funde: 2",
    }


def test_process_guard_status_values_use_safe_defaults():
    app = type("DummyApp", (), {})()

    assert process_guard_controller._process_guard_status_values(app) == {
        "monitoring": "Monitoring: aus",
        "filter": "Filter: alle",
        "visible_count": "Sichtbare Funde: 0",
    }


def test_apply_process_guard_status_values_sets_all_status_vars():
    app = type("DummyApp", (), {})()
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    process_guard_controller._apply_process_guard_status_values(
        app,
        {
            "monitoring": "Monitoring: aktiv",
            "filter": "Filter: hoch + mittel",
            "visible_count": "Sichtbare Funde: 2",
        },
    )

    assert app.process_guard_monitoring_status_var.value == "Monitoring: aktiv"
    assert app.process_guard_filter_status_var.value == "Filter: hoch + mittel"
    assert app.process_guard_visible_count_var.value == "Sichtbare Funde: 2"


def test_apply_process_guard_status_values_uses_safe_defaults():
    app = type("DummyApp", (), {})()
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    process_guard_controller._apply_process_guard_status_values(app, {})

    assert app.process_guard_monitoring_status_var.value == "Monitoring: aus"
    assert app.process_guard_filter_status_var.value == "Filter: alle"
    assert app.process_guard_visible_count_var.value == "Sichtbare Funde: 0"


def test_process_guard_app_wrappers_log_when_controller_is_unavailable(monkeypatch):
    import netmon.app as app_module

    app = App.__new__(App)
    logs = []
    app.log = logs.append

    monkeypatch.setattr(app_module, "process_guard_controller", None)

    app.run_process_guard_check()
    app.start_process_guard_monitoring()
    app.stop_process_guard_monitoring()

    assert logs == [
        "Process Guard: Controller nicht verfügbar.",
        "Process Guard: Controller nicht verfügbar.",
        "Process Guard: Controller nicht verfügbar.",
    ]


def test_process_guard_service_or_log_returns_service_when_present():
    app = type("DummyApp", (), {})()
    service = object()
    app.process_guard_service = service
    app.log = lambda _message: None

    assert process_guard_controller._process_guard_service_or_log(app) is service


def test_process_guard_service_or_log_logs_when_missing():
    logs = []
    app = type("DummyApp", (), {})()
    app.log = logs.append

    assert process_guard_controller._process_guard_service_or_log(app) is None
    assert logs == ["Process Guard: Service nicht verfügbar."]


def test_process_guard_available_service_or_log_returns_available_service():
    logs = []
    service = type("DummyService", (), {"is_available": lambda self: True})()
    app = type("DummyApp", (), {})()
    app.process_guard_service = service
    app.log = logs.append

    assert (
        process_guard_controller._process_guard_available_service_or_log(app) is service
    )
    assert logs == []


def test_process_guard_available_service_or_log_logs_when_unavailable():
    logs = []
    service = type("DummyService", (), {"is_available": lambda self: False})()
    app = type("DummyApp", (), {})()
    app.process_guard_service = service
    app.log = logs.append

    assert process_guard_controller._process_guard_available_service_or_log(app) is None
    assert logs == ["Process Guard: Service nicht verfügbar."]


def test_process_guard_service_unavailable_message_matches_expected_text():
    assert (
        process_guard_controller._process_guard_service_unavailable_message()
        == "Process Guard: Service nicht verfügbar."
    )


def test_process_guard_service_unavailable_message_is_stable_string():
    message = process_guard_controller._process_guard_service_unavailable_message()

    assert isinstance(message, str)
    assert "Service nicht verfügbar" in message


def test_finish_process_guard_trustlist_action_logs_success_and_rechecks(monkeypatch):
    app = type("DummyApp", (), {})()
    logs = []
    rechecks = []
    app.log = logs.append

    monkeypatch.setattr(
        process_guard_controller,
        "run_process_guard_check",
        lambda current_app: rechecks.append(current_app),
    )

    process_guard_controller._finish_process_guard_trustlist_action(
        app,
        ok=True,
        err="",
        success_message="Process Guard: Erfolg.",
    )

    assert logs == ["Process Guard: Erfolg."]
    assert rechecks == [app]


def test_finish_process_guard_trustlist_action_logs_error_without_recheck(monkeypatch):
    app = type("DummyApp", (), {})()
    logs = []
    rechecks = []
    app.log = logs.append

    monkeypatch.setattr(
        process_guard_controller,
        "run_process_guard_check",
        lambda current_app: rechecks.append(current_app),
    )

    process_guard_controller._finish_process_guard_trustlist_action(
        app,
        ok=False,
        err="kaputt",
        success_message="Process Guard: Erfolg.",
    )

    assert logs == ["Process Guard: Trustlist Fehler: kaputt"]
    assert rechecks == []


def test_process_guard_finding_name_returns_safe_name():
    assert (
        process_guard_controller._process_guard_finding_name({"name": "bash"}) == "bash"
    )


def test_process_guard_finding_name_uses_default_for_missing_values():
    assert process_guard_controller._process_guard_finding_name({}) == "-"
    assert (
        process_guard_controller._process_guard_finding_name(None, default="unbekannt")
        == "unbekannt"
    )


def test_selected_process_guard_finding_or_log_returns_selection():
    app = type("DummyApp", (), {})()
    finding = {"name": "bash"}
    app.process_guard_selected_finding = finding
    app.log = lambda _message: None

    assert (
        process_guard_controller._selected_process_guard_finding_or_log(app) is finding
    )


def test_selected_process_guard_finding_or_log_logs_when_missing():
    logs = []
    app = type("DummyApp", (), {})()
    app.process_guard_selected_finding = None
    app.log = logs.append

    assert process_guard_controller._selected_process_guard_finding_or_log(app) is None
    assert logs == ["Process Guard: Kein Fund ausgewählt."]


def test_selected_process_guard_tree_index_returns_selected_row_index():
    tree = DummyTreeview()
    tree.rows = [{"iid": "pg-0", "values": ()}, {"iid": "pg-1", "values": ()}]
    tree._selection = ["pg-1"]

    assert process_guard_controller._selected_process_guard_tree_index(tree) == 1


def test_selected_process_guard_tree_index_returns_none_without_valid_selection():
    tree = DummyTreeview()
    tree.rows = [{"iid": "pg-0", "values": ()}]
    tree._selection = ["pg-9"]

    assert process_guard_controller._selected_process_guard_tree_index(tree) is None
    assert process_guard_controller._selected_process_guard_tree_index(None) is None


def test_selected_process_guard_visible_finding_returns_selected_item():
    app = type("DummyApp", (), {})()
    tree = DummyTreeview()
    tree.rows = [{"iid": "pg-0", "values": ()}]
    tree._selection = ["pg-0"]
    app.process_guard_visible_findings = [{"pid": 42}]

    assert process_guard_controller._selected_process_guard_visible_finding(
        app, tree
    ) == {"pid": 42}


def test_selected_process_guard_visible_finding_returns_none_for_invalid_index():
    app = type("DummyApp", (), {})()
    tree = DummyTreeview()
    tree.rows = [{"iid": "pg-0", "values": ()}]
    tree._selection = ["pg-0"]
    app.process_guard_visible_findings = []

    assert (
        process_guard_controller._selected_process_guard_visible_finding(app, tree)
        is None
    )


def test_replace_process_guard_text_overwrites_widget_content():
    widget = DummyText()
    widget.value = "old text"

    assert (
        process_guard_controller._replace_process_guard_text(widget, "new text") is True
    )
    assert widget.value == "new text"
    assert widget.states == ["normal", "normal"]


def test_replace_process_guard_text_returns_false_without_widget():
    assert (
        process_guard_controller._replace_process_guard_text(None, "new text") is False
    )


def test_write_process_guard_text_appends_with_separator():
    widget = DummyText()
    widget.value = "existing text"

    assert (
        process_guard_controller._write_process_guard_text(
            widget,
            "next text",
            replace=False,
            see_target="end",
        )
        is True
    )
    assert widget.value == "existing text\n\nnext text"
    assert widget.states == ["normal", "normal"]


def test_write_process_guard_text_replaces_and_resets_view():
    widget = DummyText()
    widget.value = "existing text"

    assert (
        process_guard_controller._write_process_guard_text(
            widget,
            "fresh text",
            replace=True,
            see_target="1.0",
        )
        is True
    )
    assert widget.value == "fresh text"
    assert widget.states == ["normal", "normal"]


def test_process_guard_trustlist_lines_use_empty_state_message():
    assert process_guard_controller._process_guard_trustlist_lines({}) == [
        "=== Process Guard Vertrauensliste ===",
        "",
        "- Keine bekannten Process-Guard-Ausnahmen gespeichert.",
    ]


def test_process_guard_empty_trustlist_message_matches_expected_text():
    assert (
        process_guard_controller._process_guard_empty_trustlist_message()
        == "- Keine bekannten Process-Guard-Ausnahmen gespeichert."
    )


def test_process_guard_empty_trustlist_message_mentions_ausnahmen():
    message = process_guard_controller._process_guard_empty_trustlist_message()

    assert "Ausnahmen" in message


def test_process_guard_trustlist_header_matches_expected_text():
    assert (
        process_guard_controller._process_guard_trustlist_header()
        == "=== Process Guard Vertrauensliste ==="
    )


def test_process_guard_trustlist_header_mentions_vertrauensliste():
    header = process_guard_controller._process_guard_trustlist_header()

    assert "Vertrauensliste" in header


def test_process_guard_monitoring_log_message_maps_known_states():
    assert (
        process_guard_controller._process_guard_monitoring_log_message("active")
        == "Process Guard: Monitoring gestartet."
    )
    assert (
        process_guard_controller._process_guard_monitoring_log_message("stopped")
        == "Process Guard: Monitoring gestoppt."
    )


def test_process_guard_monitoring_log_message_uses_unknown_fallback():
    assert (
        process_guard_controller._process_guard_monitoring_log_message("mystery")
        == "Process Guard: Monitoring unbekannt."
    )


def test_process_guard_trustlist_lines_render_sorted_entries():
    lines = process_guard_controller._process_guard_trustlist_lines(
        {
            "sig-b": {
                "name": "python3",
                "exe": "/usr/bin/python3",
                "user": "sven",
                "parent_name": "bash",
            },
            "sig-a": {
                "name": "bash",
                "exe": "/usr/bin/bash",
                "user": "root",
                "parent_name": "systemd",
            },
        }
    )

    assert lines[2] == "- bash | /usr/bin/bash | User: root"
    assert lines[3] == "  Parent: systemd"
    assert lines[4] == "  Signatur: sig-a"


def test_show_process_guard_trustlist_uses_configured_trustlist_path():
    calls = []
    app = type("DummyApp", (), {})()
    app.process_guard_trustlist_path = "/tmp/process_guard_trust.json"
    app.log = lambda _message: None
    app._select_security_tab = lambda _tab: None
    app.tab_process_guard = "process-guard"
    app.security_detail = DummyText()
    app.process_guard_service = type(
        "DummyService",
        (),
        {
            "load_trustlist": lambda self, path: calls.append(path)
            or {"trusted": {"sig": {"name": "bash", "exe": "/usr/bin/bash"}}}
        },
    )()

    process_guard_controller.show_process_guard_trustlist(app)

    assert calls == ["/tmp/process_guard_trust.json"]
    assert "Process Guard Vertrauensliste" in app.security_detail.value


def test_apply_process_guard_monitoring_snapshot_sets_green_when_clean():
    app = type("DummyApp", (), {})()
    app.process_guard_tree = DummyTreeview()
    app.process_guard_filter_mode = "all"
    app.process_guard_selected_finding = None
    app.process_guard_visible_findings = [{"pid": 99}]
    app.process_guard_detail = DummyText()
    app.process_guard_monitoring = True
    app.process_guard_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.l_process_guard = object()
    app.light_calls = []
    app.set_light = lambda _light, color: app.light_calls.append(color)
    app.log_messages = []
    app.log = app.log_messages.append

    process_guard_controller.apply_process_guard_monitoring_snapshot(
        app,
        processes=[{"pid": 1}],
        findings=[],
    )

    assert app.light_calls[-1] == "green"
    assert app.process_guard_status_var.value == (
        "Process Guard: Monitoring aktiv, keine neuen Auffälligkeiten"
    )
    assert app.process_guard_last_result["findings"] == []
    assert app.process_guard_visible_findings == []


def test_mark_selected_process_guard_trusted_rechecks():
    app = type("DummyApp", (), {})()
    calls = []
    app.process_guard_selected_finding = {
        "name": "bash",
        "exe": "/usr/bin/bash",
        "user": "sven",
        "parent_name": "firefox",
    }
    app.process_guard_trustlist_path = "/tmp/process_guard_trustlist.json"
    app.process_guard_service = type(
        "DummyService",
        (),
        {
            "mark_trusted": lambda self, finding, path: calls.append((finding, path))
            or (True, "")
        },
    )()
    app.log = calls.append
    app.run_process_guard_check = lambda: calls.append("recheck")

    original = process_guard_controller.run_process_guard_check
    process_guard_controller.run_process_guard_check = lambda _app: calls.append(
        "recheck"
    )
    try:
        process_guard_controller.mark_selected_process_guard_trusted(app)
    finally:
        process_guard_controller.run_process_guard_check = original

    assert calls[1] == "Process Guard: Fund als bekannt markiert: bash"
    assert calls[2] == "recheck"


def test_show_process_guard_trustlist_writes_output():
    app = type("DummyApp", (), {})()
    app.process_guard_trustlist_path = "/tmp/process_guard_trustlist.json"
    app.process_guard_service = type(
        "DummyService",
        (),
        {
            "load_trustlist": lambda self, _path: {
                "trusted": {
                    "bash|/usr/bin/bash|sven": {
                        "name": "bash",
                        "exe": "/usr/bin/bash",
                        "user": "sven",
                        "parent_name": "firefox",
                    }
                }
            }
        },
    )()
    app.security_detail = DummyText()

    process_guard_controller.show_process_guard_trustlist(app)

    assert "=== Process Guard Vertrauensliste ===" in app.security_detail.value
    assert "/usr/bin/bash" in app.security_detail.value


def test_reset_process_guard_trustlist_rechecks():
    app = type("DummyApp", (), {})()
    calls = []
    app.process_guard_trustlist_path = "/tmp/process_guard_trustlist.json"
    app.process_guard_service = type(
        "DummyService",
        (),
        {"reset_trustlist": lambda self, path: calls.append(path) or (True, "")},
    )()
    app.log = calls.append

    original = process_guard_controller.run_process_guard_check
    process_guard_controller.run_process_guard_check = lambda _app: calls.append(
        "recheck"
    )
    try:
        process_guard_controller.reset_process_guard_trustlist(app)
    finally:
        process_guard_controller.run_process_guard_check = original

    assert calls[0] == "/tmp/process_guard_trustlist.json"
    assert calls[1] == "Process Guard: Vertrauensliste wurde zurückgesetzt."
    assert calls[2] == "recheck"


def test_remove_selected_process_guard_trusted_rechecks():
    app = type("DummyApp", (), {})()
    calls = []
    app.process_guard_selected_finding = {
        "name": "bash",
        "exe": "/usr/bin/bash",
        "user": "sven",
        "parent_name": "firefox",
    }
    app.process_guard_trustlist_path = " /tmp/process_guard_trustlist.json "
    app.process_guard_service = type(
        "DummyService",
        (),
        {
            "remove_trusted": lambda self, finding, path: calls.append((finding, path))
            or (True, "")
        },
    )()
    app.log = calls.append

    original = process_guard_controller.run_process_guard_check
    process_guard_controller.run_process_guard_check = lambda _app: calls.append(
        "recheck"
    )
    try:
        process_guard_controller.remove_selected_process_guard_trusted(app)
    finally:
        process_guard_controller.run_process_guard_check = original

    assert calls[0][1] == "/tmp/process_guard_trustlist.json"
    assert calls[1] == "Process Guard: Fund aus Vertrauensliste entfernt: bash"
    assert calls[2] == "recheck"


def test_run_process_guard_check_uses_trimmed_trustlist_path():
    app = type("DummyApp", (), {})()
    calls = []
    app.process_guard_service = type(
        "DummyService",
        (),
        {
            "is_available": lambda self: True,
            "load_trustlist": lambda self, path: calls.append(("trustlist", path))
            or {},
            "run_check": lambda self, trustlist=None: {
                "available": True,
                "processes_count": 0,
                "findings": [],
                "risk": "niedrig",
                "counts": {"high": 0, "medium": 0, "low": 0},
            },
        },
    )()
    app.process_guard_trustlist_path = " /tmp/process_guard_trustlist.json "
    app.process_guard_tree = DummyTreeview()
    app.process_guard_detail = DummyText()
    app.process_guard_visible_findings = []
    app.process_guard_filter_mode = "all"
    app.process_guard_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_monitoring_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.process_guard_visible_count_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.l_process_guard = object()
    app.set_light = lambda _light, _color: None
    app.log_messages = []
    app.log = app.log_messages.append

    process_guard_controller.run_process_guard_check(app)

    assert calls == [("trustlist", "/tmp/process_guard_trustlist.json")]
    assert (
        app.log_messages[-1]
        == "Process Guard: Prüfung abgeschlossen (Risiko: niedrig)."
    )
