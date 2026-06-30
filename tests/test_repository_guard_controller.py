from netmon.features import repository_guard_controller


def test_keyring_filter_matches_expected_codes():
    assert repository_guard_controller.is_repository_guard_keyring_finding(
        {"code": "repo_no_signed_by"}
    )
    assert repository_guard_controller.is_repository_guard_keyring_finding(
        {"code": "repo_signed_by_missing_file"}
    )
    assert not repository_guard_controller.is_repository_guard_keyring_finding(
        {"code": "repo_unknown_origin"}
    )


def test_review_filter_requires_active_untrusted_third_party_source():
    source_map = {
        "src-1": {
            "id": "src-1",
            "enabled": True,
            "origin_class": "unknown",
            "trusted_host": False,
        },
        "src-2": {
            "id": "src-2",
            "enabled": True,
            "origin_class": "unknown",
            "trusted_host": True,
        },
        "src-3": {
            "id": "src-3",
            "enabled": False,
            "origin_class": "unknown",
            "trusted_host": False,
        },
    }

    assert repository_guard_controller.is_repository_guard_review_finding(
        {"severity": "warning", "source_id": "src-1"},
        source_map,
    )
    assert not repository_guard_controller.is_repository_guard_review_finding(
        {"severity": "warning", "source_id": "src-2"},
        source_map,
    )
    assert not repository_guard_controller.is_repository_guard_review_finding(
        {"severity": "warning", "source_id": "src-3"},
        source_map,
    )
    assert not repository_guard_controller.is_repository_guard_review_finding(
        {"severity": "notice", "source_id": "src-1"},
        source_map,
    )


def test_recommendations_include_signed_by_guidance():
    recommendations = (
        repository_guard_controller.get_repository_guard_finding_recommendations(
            {"code": "repo_no_signed_by"},
            source={
                "host": "example.invalid",
                "uri": "https://example.invalid/repo",
            },
        )
    )

    assert any("signed-by" in item for item in recommendations)
    assert any("/etc/apt/keyrings/" in item for item in recommendations)


def test_recommendations_include_baseline_guidance():
    recommendations = (
        repository_guard_controller.get_repository_guard_finding_recommendations(
            {"code": "repo_baseline_changed"},
            source={
                "uri": "https://example.invalid/repo",
            },
        )
    )

    assert any("Baseline" in item for item in recommendations)


def test_finding_details_render_recommendations():
    class DummyApp:
        repository_guard_last_result = {
            "sources": [
                {
                    "id": "src-1",
                    "repo_type": "deb",
                    "uri": "https://example.invalid/repo",
                    "file_path": "/tmp/demo.list",
                    "line_no": 1,
                }
            ]
        }

    text = repository_guard_controller.format_repository_guard_finding_details(
        DummyApp(),
        {
            "severity": "warning",
            "code": "repo_no_signed_by",
            "title": "Quelle ohne signed-by-Hinweis",
            "summary": "Drittquelle nutzt keinen expliziten Keyring-Hinweis.",
            "source_id": "src-1",
            "details": {},
        },
    )

    assert "Empfohlene Prüfung:" in text
    assert "signed-by" in text


def test_primary_action_prefers_baseline_for_baseline_findings():
    action = repository_guard_controller.get_repository_guard_primary_action(
        {"code": "repo_baseline_changed"},
        source={"origin_class": "unknown", "trusted_host": False},
    )

    assert action["type"] == "save_baseline"


def test_primary_action_prefers_trust_for_untrusted_third_party_source():
    action = repository_guard_controller.get_repository_guard_primary_action(
        {"code": "repo_unknown_origin"},
        source={"origin_class": "unknown", "trusted_host": False},
    )

    assert action["type"] == "mark_trusted"


def test_quick_action_snippet_for_missing_keyring_file():
    snippet = repository_guard_controller.get_repository_guard_quick_action_snippet(
        {
            "code": "repo_signed_by_missing_file",
            "details": {"keyring_path": "/usr/share/keyrings/demo.gpg"},
        },
        source={},
    )

    assert snippet == "ls -l /usr/share/keyrings/demo.gpg"


def test_quick_action_snippet_shell_quotes_special_characters():
    snippet = repository_guard_controller.get_repository_guard_quick_action_snippet(
        {
            "code": "repo_no_signed_by",
            "details": {"file_path": "/tmp/demo repo's.list"},
        },
        source={},
    )

    assert snippet == "grep -n 'signed-by\\|^deb' '/tmp/demo repo'\"'\"'s.list'"


def test_reset_repository_guard_baseline_removes_file(tmp_path):
    baseline_path = tmp_path / "repository_guard_baseline.json"
    baseline_path.write_text("{}", encoding="utf-8")

    class DummyService:
        def load_trustlist(self, _path):
            return {}

        def scan(self, trustlist=None):
            return {
                "status": "ok",
                "checked_at": "2026-05-31T00:00:00Z",
                "summary": {
                    "repositories_total": 0,
                    "findings_total": 0,
                    "warning": 0,
                    "notice": 0,
                    "info": 0,
                    "critical": 0,
                    "errors": 0,
                },
                "sources": [],
                "findings": [],
                "errors": [],
            }

    class DummyApp:
        repository_guard_baseline_path = str(baseline_path)
        repository_guard_trustlist_path = ""
        repository_guard_service = DummyService()
        repository_guard_last_result = {}
        repository_guard_selected_source = None
        repository_guard_selected_finding = None

        def log(self, _message):
            pass

    app = DummyApp()
    repository_guard_controller.reset_repository_guard_baseline(app)

    assert not baseline_path.exists()


def test_copy_repository_guard_selected_uri_uses_selected_finding_source_lookup():
    class DummyApp:
        repository_guard_last_result = {
            "sources": [
                {
                    "id": "src-1",
                    "uri": "https://example.invalid/repo",
                    "file_path": "/tmp/demo.list",
                }
            ]
        }
        repository_guard_selected_source = None
        repository_guard_selected_finding = {"source_id": "src-1", "details": {}}

        def __init__(self):
            self.clipboard = None
            self.logs = []

        def clipboard_clear(self):
            self.clipboard = ""

        def clipboard_append(self, value):
            self.clipboard = value

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()

    repository_guard_controller.copy_repository_guard_selected_uri(app)

    assert app.clipboard == "https://example.invalid/repo"
    assert app.logs == ["Repository Guard: URI kopiert: https://example.invalid/repo"]


def test_mark_selected_repository_guard_trusted_uses_trimmed_trustlist_path(
    monkeypatch,
):
    calls = []
    scan_calls = []

    class DummyService:
        def mark_host_trusted(self, source, trustlist_path):
            calls.append((source, trustlist_path))
            return True, ""

    class DummyApp:
        repository_guard_selected_source = {
            "id": "src-1",
            "host": "example.invalid",
        }
        repository_guard_service = DummyService()
        repository_guard_trustlist_path = " /tmp/repository_guard_trust.json "

        def __init__(self):
            self.logs = []

        def log(self, message):
            self.logs.append(message)

    monkeypatch.setattr(
        repository_guard_controller,
        "run_repository_guard_scan",
        lambda app: scan_calls.append(app),
    )

    app = DummyApp()
    repository_guard_controller.mark_selected_repository_guard_trusted(app)

    assert calls == [
        (
            {"id": "src-1", "host": "example.invalid"},
            "/tmp/repository_guard_trust.json",
        )
    ]
    assert app.logs == ["Repository Guard: Host als vertraut markiert: example.invalid"]
    assert scan_calls == [app]


def test_repository_guard_trustlist_returns_safe_default_without_service():
    app = type("DummyApp", (), {})()

    assert repository_guard_controller._repository_guard_trustlist(app) == {
        "trusted_hosts": {}
    }


def test_finish_repository_guard_trustlist_action_logs_success_and_rescans(
    monkeypatch,
):
    app = type("DummyApp", (), {})()
    logs = []
    scan_calls = []
    app.log = logs.append

    monkeypatch.setattr(
        repository_guard_controller,
        "run_repository_guard_scan",
        lambda current_app: scan_calls.append(current_app),
    )

    repository_guard_controller._finish_repository_guard_trustlist_action(
        app,
        ok=True,
        err="",
        success_message="Repository Guard: Erfolg.",
    )

    assert logs == ["Repository Guard: Erfolg."]
    assert scan_calls == [app]


def test_finish_repository_guard_trustlist_action_logs_error_without_rescan(
    monkeypatch,
):
    app = type("DummyApp", (), {})()
    logs = []
    scan_calls = []
    app.log = logs.append

    monkeypatch.setattr(
        repository_guard_controller,
        "run_repository_guard_scan",
        lambda current_app: scan_calls.append(current_app),
    )

    repository_guard_controller._finish_repository_guard_trustlist_action(
        app,
        ok=False,
        err="kaputt",
        success_message="Repository Guard: Erfolg.",
    )

    assert logs == ["Repository Guard: Trustlist Fehler: kaputt"]
    assert scan_calls == []


def test_repository_guard_last_result_returns_detached_dict():
    app = type("DummyApp", (), {})()
    app.repository_guard_last_result = {"status": "ok", "sources": []}

    result = repository_guard_controller._repository_guard_last_result(app)
    result["status"] = "changed"

    assert app.repository_guard_last_result["status"] == "ok"


def test_repository_guard_selection_context_prefers_selected_source():
    app = type("DummyApp", (), {})()
    app.repository_guard_selected_finding = {"source_id": "src-1"}
    app.repository_guard_selected_source = {"id": "src-direct", "uri": "https://direct"}
    app.repository_guard_last_result = {
        "sources": [{"id": "src-1", "uri": "https://fallback"}]
    }

    finding, source = repository_guard_controller._repository_guard_selection_context(
        app
    )

    assert finding == {"source_id": "src-1"}
    assert source == {"id": "src-direct", "uri": "https://direct"}


def test_repository_guard_selection_context_falls_back_to_finding_source_id():
    app = type("DummyApp", (), {})()
    app.repository_guard_selected_finding = {"source_id": "src-1"}
    app.repository_guard_selected_source = None
    app.repository_guard_last_result = {
        "sources": [{"id": "src-1", "uri": "https://example.invalid/repo"}]
    }

    finding, source = repository_guard_controller._repository_guard_selection_context(
        app
    )

    assert finding == {"source_id": "src-1"}
    assert source == {"id": "src-1", "uri": "https://example.invalid/repo"}


def test_repository_guard_selection_context_returns_none_source_without_selection():
    app = type("DummyApp", (), {})()
    app.repository_guard_selected_finding = None
    app.repository_guard_selected_source = None
    app.repository_guard_last_result = {"sources": []}

    finding, source = repository_guard_controller._repository_guard_selection_context(
        app
    )

    assert finding is None
    assert source is None


def test_selected_repository_guard_tree_index_parses_expected_suffix():
    assert (
        repository_guard_controller._selected_repository_guard_tree_index("repo-src-7")
        == 7
    )
    assert (
        repository_guard_controller._selected_repository_guard_tree_index("repo-find-0")
        == 0
    )


def test_selected_repository_guard_tree_index_returns_none_for_invalid_values():
    assert repository_guard_controller._selected_repository_guard_tree_index("") is None
    assert (
        repository_guard_controller._selected_repository_guard_tree_index("broken")
        is None
    )


def test_selected_repository_guard_tree_item_returns_selected_visible_item():
    class DummyTree:
        def selection(self):
            return ("src-1",)

    assert repository_guard_controller._selected_repository_guard_tree_item(
        DummyTree(),
        [{"id": "src-0"}, {"id": "src-1"}],
    ) == {"id": "src-1"}


def test_selected_repository_guard_tree_item_returns_none_for_invalid_selection():
    class DummyTree:
        def selection(self):
            return ("src-9",)

    assert (
        repository_guard_controller._selected_repository_guard_tree_item(
            DummyTree(),
            [{"id": "src-0"}],
        )
        is None
    )


def test_repository_guard_source_id_returns_trimmed_source_id():
    assert (
        repository_guard_controller._repository_guard_source_id(
            {"source_id": " src-1 "}
        )
        == "src-1"
    )


def test_repository_guard_source_id_returns_empty_for_missing_value():
    assert repository_guard_controller._repository_guard_source_id({}) == ""
    assert repository_guard_controller._repository_guard_source_id(None) == ""


def test_repository_guard_selected_source_or_log_returns_selection():
    app = type("DummyApp", (), {})()
    source = {"host": "example.invalid"}
    app.repository_guard_selected_source = source
    app.log = lambda _message: None

    assert (
        repository_guard_controller._repository_guard_selected_source_or_log(app)
        is source
    )


def test_repository_guard_selected_source_or_log_logs_when_missing():
    logs = []
    app = type("DummyApp", (), {})()
    app.repository_guard_selected_source = None
    app.log = logs.append

    assert (
        repository_guard_controller._repository_guard_selected_source_or_log(app)
        is None
    )
    assert logs == ["Repository Guard: Keine Quelle ausgewählt."]


def test_repository_guard_service_unavailable_message_matches_expected_text():
    assert (
        repository_guard_controller._repository_guard_service_unavailable_message()
        == "Repository Guard: Service nicht verfügbar."
    )


def test_repository_guard_service_unavailable_message_is_stable_string():
    message = (
        repository_guard_controller._repository_guard_service_unavailable_message()
    )

    assert isinstance(message, str)
    assert "Service nicht verfügbar" in message


def test_repository_guard_missing_baseline_path_message_matches_expected_text():
    assert (
        repository_guard_controller._repository_guard_missing_baseline_path_message()
        == "Repository Guard: Baseline-Pfad fehlt."
    )


def test_repository_guard_missing_baseline_path_message_is_stable_string():
    message = (
        repository_guard_controller._repository_guard_missing_baseline_path_message()
    )

    assert isinstance(message, str)
    assert "Baseline-Pfad fehlt" in message


def test_repository_guard_selected_detail_value_prefers_trimmed_source_field():
    assert (
        repository_guard_controller._repository_guard_selected_detail_value(
            {"details": {"uri": "https://detail.invalid/repo"}},
            source={"uri": " https://source.invalid/repo "},
            source_key="uri",
            detail_keys=("uri", "uri_after", "uri_before"),
        )
        == "https://source.invalid/repo"
    )


def test_repository_guard_selected_detail_value_uses_detail_fallback_keys():
    assert (
        repository_guard_controller._repository_guard_selected_detail_value(
            {"details": {"file_path_after": " /tmp/demo.list "}},
            source={},
            source_key="file_path",
            detail_keys=("file_path", "file_path_after", "file_path_before"),
        )
        == "/tmp/demo.list"
    )


def test_set_repository_guard_source_filter_normalizes_refreshes_and_logs(monkeypatch):
    app = type("DummyApp", (), {})()
    app.repository_guard_source_filter_mode = "all"
    logs = []
    refresh_calls = []
    app.log = logs.append

    monkeypatch.setattr(
        repository_guard_controller,
        "refresh_repository_guard_sources_tree",
        lambda current_app: refresh_calls.append(current_app),
    )

    repository_guard_controller.set_repository_guard_source_filter(app, " trusted ")

    assert app.repository_guard_source_filter_mode == "trusted"
    assert refresh_calls == [app]
    assert logs == ["Repository Guard: Quellenfilter aktiv - trusted."]


def test_set_repository_guard_finding_filter_normalizes_refreshes_and_logs(
    monkeypatch,
):
    app = type("DummyApp", (), {})()
    app.repository_guard_finding_filter_mode = "all"
    logs = []
    refresh_calls = []
    app.log = logs.append

    monkeypatch.setattr(
        repository_guard_controller,
        "refresh_repository_guard_findings_tree",
        lambda current_app: refresh_calls.append(current_app),
    )

    repository_guard_controller.set_repository_guard_finding_filter(app, " baseline ")

    assert app.repository_guard_finding_filter_mode == "baseline"
    assert refresh_calls == [app]
    assert logs == ["Repository Guard: Finding-Filter aktiv - baseline."]


def test_repository_guard_source_filter_mode_normalizes_known_and_unknown_values():
    assert repository_guard_controller._repository_guard_source_filter_mode(
        " trusted "
    ) == ("trusted")
    assert repository_guard_controller._repository_guard_source_filter_mode(
        "mystery"
    ) == ("all")


def test_repository_guard_trust_state_label_maps_known_values():
    assert (
        repository_guard_controller._repository_guard_trust_state_label(" review ")
        == "prüfen"
    )
    assert (
        repository_guard_controller._repository_guard_trust_state_label("known")
        == "bekannt"
    )


def test_repository_guard_trust_state_label_falls_back_for_unknown_values():
    assert repository_guard_controller._repository_guard_trust_state_label("") == "-"
    assert (
        repository_guard_controller._repository_guard_trust_state_label("mystery")
        == "-"
    )


def test_repository_guard_finding_filter_mode_normalizes_known_and_unknown_values():
    assert (
        repository_guard_controller._repository_guard_finding_filter_mode(" baseline ")
        == "baseline"
    )
    assert (
        repository_guard_controller._repository_guard_finding_filter_mode("mystery")
        == "all"
    )


def test_repository_guard_report_payload_appends_details_section():
    payload = repository_guard_controller._repository_guard_report_payload(
        {"status": "ok", "summary": {}, "sources": [], "findings": [], "errors": []},
        "Detailzeile",
    )

    assert "=== Details ===" in payload
    assert payload.endswith("Detailzeile")


def test_repository_guard_report_payload_skips_empty_details():
    payload = repository_guard_controller._repository_guard_report_payload(
        {"status": "ok", "summary": {}, "sources": [], "findings": [], "errors": []},
        "   ",
    )

    assert "=== Details ===" not in payload


def test_repository_guard_details_header_matches_expected_text():
    assert (
        repository_guard_controller._repository_guard_details_header()
        == "=== Details ==="
    )


def test_repository_guard_details_header_mentions_details():
    header = repository_guard_controller._repository_guard_details_header()

    assert "Details" in header


def test_repository_guard_text_export_payload_formats_expected_text():
    payload = repository_guard_controller._repository_guard_text_export_payload(
        {"status": "ok", "summary": {}, "sources": [], "findings": [], "errors": []}
    )

    assert payload.endswith("\n")
    assert payload.startswith("=== Repository Guard ===")


def test_repository_guard_text_export_payload_ends_with_single_newline():
    payload = repository_guard_controller._repository_guard_text_export_payload(
        {"status": "ok", "summary": {}, "sources": [], "findings": [], "errors": []}
    )

    assert not payload.endswith("\n\n")


def test_repository_guard_json_export_payload_formats_expected_json():
    payload = repository_guard_controller._repository_guard_json_export_payload(
        {"status": "ok", "summary": {"warning": 1}}
    )

    assert payload.endswith("\n")
    assert '"status": "ok"' in payload
    assert '"warning": 1' in payload


def test_repository_guard_json_export_payload_ends_with_single_newline():
    payload = repository_guard_controller._repository_guard_json_export_payload(
        {"status": "ok"}
    )

    assert not payload.endswith("\n\n")


def test_repository_guard_export_payload_formats_text_exports():
    payload = repository_guard_controller._repository_guard_export_payload(
        "/tmp/repository_guard.txt",
        {"status": "ok", "summary": {}, "sources": [], "findings": [], "errors": []},
    )

    assert payload.endswith("\n")
    assert payload.startswith("=== Repository Guard ===")


def test_repository_guard_export_payload_formats_json_exports():
    payload = repository_guard_controller._repository_guard_export_payload(
        "/tmp/repository_guard.json",
        {"status": "ok", "summary": {"warning": 1}},
    )

    assert payload.endswith("\n")
    assert '"status": "ok"' in payload
    assert '"warning": 1' in payload


def test_repository_guard_source_filter_status_text_maps_known_modes():
    assert (
        repository_guard_controller._repository_guard_source_filter_status_text(
            "trusted"
        )
        == "Quellenfilter: nur Trusted Hosts"
    )
    assert (
        repository_guard_controller._repository_guard_source_filter_status_text(
            "unknown"
        )
        == "Quellenfilter: alle"
    )


def test_repository_guard_finding_filter_status_text_maps_known_modes():
    assert (
        repository_guard_controller._repository_guard_finding_filter_status_text(
            "baseline"
        )
        == "Finding-Filter: Baseline-Änderungen"
    )
    assert (
        repository_guard_controller._repository_guard_finding_filter_status_text(
            "unknown"
        )
        == "Finding-Filter: alle"
    )


def test_repository_guard_filter_choice_text_prefers_matching_label():
    assert (
        repository_guard_controller._repository_guard_filter_choice_text(
            {"all": "Alle", "trusted": "Trusted Hosts"},
            " trusted ",
            default_key="all",
            default_label="Alle",
        )
        == "Trusted Hosts"
    )


def test_repository_guard_filter_choice_text_falls_back_to_default_label():
    assert (
        repository_guard_controller._repository_guard_filter_choice_text(
            {},
            "unknown",
            default_key="all",
            default_label="Alle",
        )
        == "Alle"
    )


def test_repository_guard_empty_trustlist_message_matches_expected_text():
    assert (
        repository_guard_controller._repository_guard_empty_trustlist_message()
        == "Keine Trusted Hosts gespeichert."
    )


def test_repository_guard_empty_trustlist_message_mentions_trusted_hosts():
    message = repository_guard_controller._repository_guard_empty_trustlist_message()

    assert "Trusted Hosts" in message


def test_repository_guard_status_light_color_maps_known_states():
    assert (
        repository_guard_controller._repository_guard_status_light_color("ok")
        == "#2fbf71"
    )
    assert (
        repository_guard_controller._repository_guard_status_light_color("critical")
        == "#d92d20"
    )
    assert (
        repository_guard_controller._repository_guard_status_light_color("mystery")
        == "#7a7f87"
    )


def test_apply_repository_guard_filter_status_sets_source_vars():
    app = type("DummyApp", (), {})()
    app.repository_guard_source_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.repository_guard_source_filter_choice_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    repository_guard_controller._apply_repository_guard_filter_status(
        app,
        labels={"all": "Alle", "trusted": "Trusted Hosts"},
        mode="trusted",
        status_var_name="repository_guard_source_filter_status_var",
        choice_var_name="repository_guard_source_filter_choice_var",
        status_text_fn=repository_guard_controller._repository_guard_source_filter_status_text,
        default_key="all",
        default_label="Alle",
    )

    assert (
        app.repository_guard_source_filter_status_var.value
        == "Quellenfilter: nur Trusted Hosts"
    )
    assert app.repository_guard_source_filter_choice_var.value == "Trusted Hosts"


def test_apply_repository_guard_filter_status_sets_finding_defaults():
    app = type("DummyApp", (), {})()
    app.repository_guard_finding_filter_status_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()
    app.repository_guard_finding_filter_choice_var = type(
        "DummyVar",
        (),
        {"set": lambda self, value: setattr(self, "value", value), "value": ""},
    )()

    repository_guard_controller._apply_repository_guard_filter_status(
        app,
        labels={},
        mode="unknown",
        status_var_name="repository_guard_finding_filter_status_var",
        choice_var_name="repository_guard_finding_filter_choice_var",
        status_text_fn=repository_guard_controller._repository_guard_finding_filter_status_text,
        default_key="relevant",
        default_label="Relevant",
    )

    assert (
        app.repository_guard_finding_filter_status_var.value == "Finding-Filter: alle"
    )
    assert app.repository_guard_finding_filter_choice_var.value == "Relevant"


def test_repository_guard_trustlist_host_lines_format_expected_fields():
    assert repository_guard_controller._repository_guard_trustlist_host_lines(
        "example.invalid",
        {
            "uri": "https://example.invalid/repo",
            "repo_type": "deb",
            "trusted_at": "2026-06-06T12:00:00",
        },
    ) == [
        "- Host: example.invalid",
        "  URI: https://example.invalid/repo",
        "  Typ: deb",
        "  Markiert: 2026-06-06T12:00:00",
        "",
    ]


def test_repository_guard_trustlist_host_lines_use_safe_defaults():
    assert repository_guard_controller._repository_guard_trustlist_host_lines(
        "example.invalid",
        {},
    ) == [
        "- Host: example.invalid",
        "  URI: -",
        "  Typ: -",
        "  Markiert: -",
        "",
    ]


def test_show_repository_guard_trustlist_uses_configured_trustlist_path():
    calls = []

    class DummyService:
        def load_trustlist(self, path):
            calls.append(path)
            return {
                "trusted_hosts": {
                    "example.invalid": {
                        "uri": "https://example.invalid/repo",
                        "repo_type": "deb",
                        "trusted_at": "2026-06-06T12:00:00",
                    }
                }
            }

    class DummyApp:
        repository_guard_service = DummyService()
        repository_guard_trustlist_path = " /tmp/repository_guard_trust.json "

        def __init__(self):
            self.logs = []
            self.repository_guard_detail_text = None

        def log(self, message):
            self.logs.append(message)

    app = DummyApp()
    captured = {}

    original_set_detail_text = repository_guard_controller._set_detail_text
    try:
        repository_guard_controller._set_detail_text = (
            lambda _app, text: captured.setdefault("text", text)
        )
        repository_guard_controller.show_repository_guard_trustlist(app)
    finally:
        repository_guard_controller._set_detail_text = original_set_detail_text

    assert calls == ["/tmp/repository_guard_trust.json"]
    assert "Repository Guard Vertrauensliste" in captured["text"]
    assert "example.invalid" in captured["text"]
