from netmon.app import App
from netmon.features import chad_controller


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class DummyWidget:
    def __init__(self):
        self.states = []
        self.configs = []

    def configure(self, **kwargs):
        self.states.append(kwargs.get("state"))
        self.configs.append(kwargs)


class DummyNotebook:
    def __init__(self):
        self.selected = []

    def select(self, tab):
        self.selected.append(tab)


def test_select_security_tab_keeps_chad_visible_during_systemcheck():
    app = App.__new__(App)
    app.nb = DummyNotebook()
    app.tab_chad_analysis = "chad"
    app.tab_security_main = "security-main"
    app.security_nb = DummyNotebook()
    app.security_systemcheck_lock_chad_tab = True

    app._select_security_tab("startup-guard")

    assert app.nb.selected == ["chad"]
    assert app.security_nb.selected == []


def test_format_chad_response_title_includes_analysis_source():
    app = App.__new__(App)
    app.tr = lambda _key, default: default

    title = chad_controller._format_chad_response_title(app, "Firewall Analyse")

    assert title == "Chad Antwort: Firewall Analyse"


def test_update_chad_summary_from_result_updates_counts_and_recent_rows():
    app = App.__new__(App)
    app.chad_settings_summary_state_var = DummyVar("Unauffällig")
    app.chad_settings_summary_critical_var = DummyVar("0")
    app.chad_settings_summary_warning_var = DummyVar("0")
    app.chad_settings_summary_notice_var = DummyVar("0")
    app.chad_settings_summary_info_var = DummyVar("0")
    app.chad_settings_recent_analysis_entries = []
    app.chad_settings_recent_analysis_rows = [
        {
            "timestamp_var": DummyVar("--"),
            "type_var": DummyVar("--"),
            "status_var": DummyVar("--"),
            "warning_var": DummyVar("0"),
            "critical_var": DummyVar("0"),
        }
        for _ in range(3)
    ]
    app.chad_settings_summary_indicator_label = DummyWidget()

    chad_controller.update_chad_summary_from_result(
        app,
        "Firewall Analyse",
        "\n".join(
            [
                "Kritisch: rootkit gefunden",
                "Warnung: verdächtige Verbindung",
                "Hinweis: bitte prüfen",
                "OK: Firewall aktiv",
            ]
        ),
    )

    assert app.chad_settings_summary_state_var.get() == "Kritisch"
    assert app.chad_settings_summary_critical_var.get() == "1"
    assert app.chad_settings_summary_warning_var.get() == "1"
    assert app.chad_settings_summary_notice_var.get() == "1"
    assert app.chad_settings_summary_info_var.get() == "1"
    assert (
        app.chad_settings_recent_analysis_rows[0]["type_var"].get()
        == "Firewall Analyse"
    )
    assert app.chad_settings_recent_analysis_rows[0]["status_var"].get() == "Kritisch"
    assert app.chad_settings_recent_analysis_rows[0]["warning_var"].get() == "1"
    assert app.chad_settings_recent_analysis_rows[0]["critical_var"].get() == "1"
    assert app.chad_settings_summary_indicator_label.configs[-1]["fg"] == "#b71c1c"


def test_classify_chad_result_lines_understands_typical_netmon_phrases():
    counts = chad_controller._classify_chad_result_lines(
        "\n".join(
            [
                "Risiko: mittel",
                "Warnings: 2",
                "Suggestions: 4",
                "Hinweis: ~/.local/bin wird eingebunden",
                "Keine Änderungen",
                "Funde: 0",
            ]
        )
    )

    assert counts["critical"] == 0
    assert counts["warnings"] >= 2
    assert counts["notices"] >= 1
    assert counts["info"] >= 2


def test_prefixed_chad_response_title_is_still_classified_as_answer():
    assert (
        chad_controller._get_chad_entry_kind("Chad Antwort: Firewall Analyse")
        == "answer"
    )


def test_refresh_chad_security_tools_status_reports_rkhunter_and_clamav(monkeypatch):
    import netmon.app as app_module

    app = App.__new__(App)
    app.chad_security_tools_status_var = DummyVar("")

    monkeypatch.setattr(app_module, "is_rkhunter_installed", lambda: False)
    monkeypatch.setattr(app_module, "has_cmd", lambda name: name != "clamscan")

    app.refresh_chad_security_tools_status()

    status = app.chad_security_tools_status_var.get()
    assert "Security-Tools:" in status
    assert "rkhunter fehlt" in status
    assert "ClamAV fehlt" in status


def test_run_next_security_systemcheck_step_sends_missing_tool_result_to_chad():
    app = App.__new__(App)
    app.security_systemcheck_queue = [
        {
            "title": "rkhunter Analyse",
            "availability": lambda: False,
            "unavailable_text": lambda: "rkhunter fehlt lokal",
        }
    ]
    app.security_systemcheck_running = True
    app.security_systemcheck_lock_chad_tab = True
    app.security_systemcheck_results = []
    app.security_systemcheck_status_var = DummyVar("")
    captured = {}

    def fake_send(title, raw_text, done_callback=None):
        captured["title"] = title
        captured["raw_text"] = raw_text
        captured["done_callback"] = done_callback

    app._send_security_systemcheck_result_to_chad = fake_send
    app.after = lambda _delay, callback: callback()
    app.append_to_chad_output = lambda *_args, **_kwargs: None

    app._run_next_security_systemcheck_step()

    assert captured["title"] == "rkhunter Analyse"
    assert captured["raw_text"] == "rkhunter fehlt lokal"
    assert captured["done_callback"] == app._run_next_security_systemcheck_step


def test_selected_security_systemcheck_specs_use_app_rkhunter_runner():
    app = App.__new__(App)
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(True)
    app.var_systemcheck_clamav = DummyVar(False)
    app.rkhunter_scan_async = lambda: None
    app._collect_rkhunter_for_systemcheck = lambda: "rkhunter"
    app._is_rkhunter_available_for_chad_systemcheck = lambda: True
    app._missing_rkhunter_for_chad_systemcheck_message = lambda: "rkhunter fehlt"

    specs = app._selected_security_systemcheck_specs()

    assert len(specs) == 1
    assert specs[0]["title"] == "rkhunter Analyse"
    assert specs[0]["runner"] == app.rkhunter_scan_async


def test_selected_security_systemcheck_specs_use_app_clamav_runner():
    app = App.__new__(App)
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(False)
    app.var_systemcheck_clamav = DummyVar(True)
    app.security_clamav_quickscan_async = lambda: None
    app._collect_clamav_for_systemcheck = lambda: "clamav"
    app._is_clamav_available_for_chad_systemcheck = lambda: True
    app._missing_clamav_for_chad_systemcheck_message = lambda: "clamav fehlt"

    specs = app._selected_security_systemcheck_specs()

    assert len(specs) == 1
    assert specs[0]["title"] == "ClamAV Analyse"
    assert specs[0]["runner"] == app.security_clamav_quickscan_async


def test_collect_clamav_for_systemcheck_prefers_stable_snapshot():
    app = App.__new__(App)
    app.security_clamav_last_systemcheck_text = "\n".join(
        [
            "=== ClamAV ===",
            "Status: abgeschlossen",
            "Funde: 0",
            "Ergebnis: Keine Bedrohungen gefunden",
        ]
    )
    app._read_text_widget_content = lambda _name: ""

    result = app._collect_clamav_for_systemcheck()

    assert "Funde: 0" in result
    assert "Keine Bedrohungen gefunden" in result


def test_save_and_load_chad_analysis_json_roundtrip(tmp_path):
    class SaveDialog:
        @staticmethod
        def asksaveasfilename(**_kwargs):
            return str(tmp_path / "saved_analysis.json")

        @staticmethod
        def askopenfilename(**_kwargs):
            return str(tmp_path / "saved_analysis.json")

    original_dialog = chad_controller.filedialog
    chad_controller.filedialog = SaveDialog
    try:
        app = App.__new__(App)
        app.chad_enabled_var = DummyVar(True)
        app.chad_analysis_source_var = DummyVar("Quelle: Firewall Analyse")
        app.chad_analysis_status_var = DummyVar("")
        app.chad_analysis_current_prompt = "PROMPT"
        app.chad_online_result = "ERGEBNIS"
        app.chad_output_entries = [
            {"title": "Firewall Analyse", "text": "PROMPT", "kind": "result"},
            {
                "title": "Chad Antwort: Firewall Analyse",
                "text": "ERGEBNIS",
                "kind": "answer",
            },
        ]
        app.chad_chat_history = [{"role": "user", "content": "frage"}]
        app.tr = lambda _key, default=None: default or _key
        app.nb = DummyNotebook()
        app.tab_chad_analysis = "chad"

        chad_controller.save_chad_analysis_to_file(app)

        assert (tmp_path / "saved_analysis.json").exists()

        loaded = App.__new__(App)
        loaded.chad_enabled_var = DummyVar(True)
        loaded.chad_analysis_source_var = DummyVar("")
        loaded.chad_analysis_status_var = DummyVar("")
        loaded.chad_output_entries = []
        loaded.chad_chat_history = []
        loaded.chad_analysis_current_prompt = ""
        loaded.chad_online_result = ""
        loaded.tr = lambda _key, default=None: default or _key
        loaded.nb = DummyNotebook()
        loaded.tab_chad_analysis = "chad"

        chad_controller.load_chad_analysis_from_file(loaded)

        assert loaded.chad_analysis_current_prompt == "PROMPT"
        assert loaded.chad_online_result == "ERGEBNIS"
        assert len(loaded.chad_output_entries) == 2
        assert (
            loaded.chad_output_entries[1]["title"] == "Chad Antwort: Firewall Analyse"
        )
        assert loaded.chad_analysis_source_var.get() == "Quelle: Firewall Analyse"
        assert loaded.nb.selected == ["chad"]
    finally:
        chad_controller.filedialog = original_dialog


def test_set_chad_direct_prompt_updates_state_and_selects_chad_tab(monkeypatch):
    app = App.__new__(App)
    app.settings = {"auto_switch_to_chad": True}
    app.tr = lambda _key, default=None: default or _key
    app.nb = DummyNotebook()
    app.tab_chad_analysis = "chad"
    app.chad_analysis_source_var = DummyVar("")
    app.chad_analysis_status_var = DummyVar("")
    app.chad_analysis_current_prompt = ""
    app.chad_online_result = "old"
    appended = []
    marked = []

    monkeypatch.setattr(
        chad_controller,
        "append_to_chad_output",
        lambda _app, title, text: appended.append((title, text)),
    )
    monkeypatch.setattr(
        chad_controller,
        "mark_chad_status_event",
        lambda _app, **kwargs: marked.append(kwargs),
    )

    chad_controller.set_chad_direct_prompt(app, "Firewall Analyse", "  PROMPT  ")

    assert app.chad_analysis_current_prompt == "PROMPT"
    assert app.chad_online_result == ""
    assert app.chad_analysis_source_var.get() == "Quelle: Firewall Analyse"
    assert app.chad_analysis_status_var.get() == "Analyse vorbereitet."
    assert appended == [("Firewall Analyse", "PROMPT")]
    assert marked == [{"analysis_title": "Vorbereitet: Firewall Analyse"}]
    assert app.nb.selected == ["chad"]


def test_set_chad_direct_prompt_respects_disabled_auto_switch(monkeypatch):
    app = App.__new__(App)
    app.settings = {"auto_switch_to_chad": False}
    app.tr = lambda _key, default=None: default or _key
    app.nb = DummyNotebook()
    app.tab_chad_analysis = "chad"
    app.chad_analysis_source_var = DummyVar("")
    app.chad_analysis_status_var = DummyVar("")

    monkeypatch.setattr(
        chad_controller,
        "append_to_chad_output",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        chad_controller,
        "mark_chad_status_event",
        lambda *_args, **_kwargs: None,
    )

    chad_controller.set_chad_direct_prompt(app, "PATH Guard Analyse", "demo")

    assert app.nb.selected == []


def test_prepare_chad_analysis_skips_preview_by_default():
    app = App.__new__(App)
    calls = []
    app.chad_enabled_var = DummyVar(True)
    app.chad_analysis_status_var = DummyVar("")

    app.set_chad_analysis = lambda title, raw_text: calls.append(
        ("set", title, raw_text)
    )
    app.open_ai_analysis_preview = lambda title, raw_text: calls.append(
        ("preview", title, raw_text)
    )

    app.prepare_chad_analysis("PATH Guard Analyse", "demo text")

    assert calls == [("set", "PATH Guard Analyse", "demo text")]


def test_prepare_chad_analysis_can_open_preview_explicitly():
    app = App.__new__(App)
    calls = []
    app.chad_enabled_var = DummyVar(True)
    app.chad_analysis_status_var = DummyVar("")

    app.set_chad_analysis = lambda title, raw_text: calls.append(
        ("set", title, raw_text)
    )
    app.open_ai_analysis_preview = lambda title, raw_text: calls.append(
        ("preview", title, raw_text)
    )

    app.prepare_chad_analysis("Startup Guard Analyse", "demo text", show_preview=True)

    assert calls == [
        ("set", "Startup Guard Analyse", "demo text"),
        ("preview", "Startup Guard Analyse", "demo text"),
    ]


def test_prepare_chad_analysis_is_blocked_when_chad_is_disabled():
    app = App.__new__(App)
    calls = []
    app.chad_enabled_var = DummyVar(False)
    app.chad_analysis_status_var = DummyVar("")
    app.set_chad_analysis = lambda title, raw_text: calls.append(
        ("set", title, raw_text)
    )

    app.prepare_chad_analysis("PATH Guard Analyse", "demo text")

    assert calls == []
    assert app.chad_analysis_status_var.get() == "Chad-Anbindung ist deaktiviert."


def test_build_chad_analysis_prompt_adds_dev_environment_filter_hint():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        "demo",
    )

    assert "PROMPT::Security Analyse::demo" in prompt
    assert "VS Code-, Codex-, Dev-Container- und Docker-bezogene Prozesse" in prompt


def test_build_chad_analysis_prompt_filters_dev_environment_noise_before_prompt_build():
    captured = {}
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {
            "build_prompt": lambda self, title, text: captured.update(
                {"title": title, "text": text}
            )
            or f"PROMPT::{title}::{text}"
        },
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)

    raw_text = "\n".join(
        [
            "Process: vscode-server helper",
            "Socket: /var/run/docker.sock",
            "Warnung: unbekannte externe Verbindung 203.0.113.5:443",
        ]
    )

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Process Guard Analyse",
        raw_text,
    )

    assert captured["title"] == "Process Guard Analyse"
    assert "vscode-server helper" not in captured["text"]
    assert "/var/run/docker.sock" not in captured["text"]
    assert "unbekannte externe Verbindung" in captured["text"]
    assert "vscode-server helper" not in prompt
    assert "unbekannte externe Verbindung" in prompt


def test_build_chad_analysis_prompt_keeps_dev_lines_with_risk_signals():
    captured = {}
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {
            "build_prompt": lambda self, title, text: captured.update(
                {"title": title, "text": text}
            )
            or f"PROMPT::{title}::{text}"
        },
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)

    raw_text = "Docker Prozess verdächtig: unknown binary mit reverse shell Verhalten"

    chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        raw_text,
    )

    assert captured["text"] == raw_text


def test_build_chad_analysis_prompt_adds_analysis_filter_instructions():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(True)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(True)
    app.chad_filter_relevant_var = DummyVar(True)
    app.chad_filter_critical_var = DummyVar(True)
    app.chad_filter_recommendations_var = DummyVar(True)
    app.chad_filter_beginner_var = DummyVar(True)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        "demo",
    )

    assert "nur kritische oder klar hochriskante Warnungen" in prompt
    assert "Handlungsempfehlungen" in prompt
    assert "anfängerfreundlich" in prompt
    assert "keine langen Rohdatenblöcke" in prompt
    assert "technische Details knapp" in prompt
    assert "Normale Systemdienste" in prompt
    assert "harmlose Desktop-, Audio- und Sitzungsprozesse" in prompt


def test_build_chad_analysis_prompt_filters_normal_services_and_harmless_processes():
    captured = {}
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {
            "build_prompt": lambda self, title, text: captured.update(
                {"title": title, "text": text}
            )
            or f"PROMPT::{title}::{text}"
        },
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(True)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(True)

    raw_text = "\n".join(
        [
            "Dienst: systemd-resolved läuft normal",
            "Prozess: pipewire aktiv für Audiositzung",
            "Warnung: verdächtige unbekannte Binary mit Rootkit Hinweis",
        ]
    )

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        raw_text,
    )

    assert "systemd-resolved läuft normal" not in captured["text"]
    assert "pipewire aktiv für Audiositzung" not in captured["text"]
    assert "verdächtige unbekannte Binary" in captured["text"]
    assert "verdächtige unbekannte Binary" in prompt


def test_build_chad_analysis_prompt_filters_low_signal_lines_when_relevant_mode_is_active():
    captured = {}
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {
            "build_prompt": lambda self, title, text: captured.update(
                {"title": title, "text": text}
            )
            or f"PROMPT::{title}::{text}"
        },
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(True)
    app.chad_filter_critical_var = DummyVar(False)

    raw_text = "\n".join(
        [
            "=== Security ===",
            "Gesamtzahl Events: 42",
            "Keine externen Events gefunden.",
            "Warnung: verdächtige externe Verbindung zu 203.0.113.5",
        ]
    )

    chad_controller.build_chad_analysis_prompt(app, "Security Analyse", raw_text)

    assert "=== Security ===" in captured["text"]
    assert "Gesamtzahl Events: 42" not in captured["text"]
    assert "Keine externen Events gefunden." not in captured["text"]
    assert "verdächtige externe Verbindung" in captured["text"]
    assert "lokale Info-/Rauschzeile" in captured["text"]


def test_build_chad_analysis_prompt_filters_noncritical_lines_when_critical_mode_is_active():
    captured = {}
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {
            "build_prompt": lambda self, title, text: captured.update(
                {"title": title, "text": text}
            )
            or f"PROMPT::{title}::{text}"
        },
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(True)

    raw_text = "\n".join(
        [
            "=== Process Guard ===",
            "Geprüfte Prozesse: 211",
            "Risiko: Mittel",
            "WARNUNG: verdächtige unbekannte Binary erkannt",
        ]
    )

    chad_controller.build_chad_analysis_prompt(app, "Process Guard Analyse", raw_text)

    assert "=== Process Guard ===" in captured["text"]
    assert "Geprüfte Prozesse: 211" not in captured["text"]
    assert "Risiko: Mittel" not in captured["text"]
    assert "WARNUNG: verdächtige unbekannte Binary erkannt" in captured["text"]


def test_build_chad_analysis_prompt_adds_focus_priorities():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(True)
    app.chad_focus_security_var = DummyVar(True)
    app.chad_focus_dns_var = DummyVar(True)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(True)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(True)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(True)

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        "demo",
    )

    assert "Analyse-Schwerpunkte:" in prompt
    assert "Sicherheitsanalyse: priorisiere Schwachstellen" in prompt
    assert "DNS Analyse: achte besonders auf Resolver-Konflikte" in prompt
    assert "Prozessanalyse: bewerte Prozesse" in prompt
    assert "Performance Analyse: nenne auch Leistungsengpässe" in prompt
    assert "Rootkit Hinweise priorisieren" in prompt
    assert "Firewall Analyse" not in prompt


def test_build_chad_analysis_prompt_skips_focus_block_when_all_focuses_off():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(
        app,
        "Security Analyse",
        "demo",
    )

    assert "Analyse-Schwerpunkte:" not in prompt


def test_build_chad_analysis_prompt_adds_beginner_mode_instruction():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_analysis_mode_var = DummyVar("beginner")
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(app, "Security Analyse", "demo")

    assert "Analysemodus Anfänger" in prompt
    assert "wenig Fachjargon" in prompt


def test_build_chad_analysis_prompt_adds_expert_mode_instruction():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_analysis_mode_var = DummyVar("expert")
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(app, "Security Analyse", "demo")

    assert "Analysemodus Experte" in prompt
    assert "technisch präziser" in prompt


def test_build_chad_analysis_prompt_uses_standard_mode_by_default():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(app, "Security Analyse", "demo")

    assert "Analysemodus Standard" in prompt
    assert "ausgewogen" in prompt


def test_build_chad_analysis_prompt_adds_answer_behavior_instructions():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)
    app.chad_answer_short_var = DummyVar(True)
    app.chad_answer_detailed_var = DummyVar(True)
    app.chad_answer_step_var = DummyVar(True)
    app.chad_answer_linux_help_var = DummyVar(True)
    app.chad_answer_risk_var = DummyVar(True)
    app.chad_answer_recommendations_var = DummyVar(True)

    prompt = chad_controller.build_chad_analysis_prompt(app, "Security Analyse", "demo")

    assert "Antwortverhalten:" in prompt
    assert "Kurze Antworten bevorzugen" in prompt
    assert "Ausführliche Analyse" in prompt
    assert "Schritt-für-Schritt-Erklärungen" in prompt
    assert "Linux-Befehle erklären" in prompt
    assert "Risiko-Einstufung anzeigen" in prompt
    assert "Empfehlungen priorisieren" in prompt


def test_build_chad_analysis_prompt_skips_answer_behavior_block_when_all_off():
    app = App.__new__(App)
    app.ai_service = type(
        "DummyService",
        (),
        {"build_prompt": lambda self, title, text: f"PROMPT::{title}::{text}"},
    )()
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)
    app.chad_answer_short_var = DummyVar(False)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(False)
    app.chad_answer_risk_var = DummyVar(False)
    app.chad_answer_recommendations_var = DummyVar(False)

    prompt = chad_controller.build_chad_analysis_prompt(app, "Security Analyse", "demo")

    assert "Antwortverhalten:" not in prompt


def test_update_chad_controls_state_disables_widgets_when_chad_is_off():
    app = App.__new__(App)
    app.chad_enabled_var = DummyVar(False)
    app.keyring_available = True
    app.chad_chat_status_var = DummyVar("")
    app.chad_online_status_var = DummyVar("")
    app.chad_analysis_status_var = DummyVar("")
    app.openai_api_key_entry = DummyWidget()
    app.chad_analysis_text = DummyWidget()
    app.btn_chad_api_paste = DummyWidget()
    app.btn_chad_api_apply = DummyWidget()
    app.btn_chad_api_save = DummyWidget()
    app.btn_chad_api_clear = DummyWidget()
    app.btn_chad_api_delete = DummyWidget()
    app.btn_chad_take_analysis = DummyWidget()
    app.btn_chad_import_file = DummyWidget()
    app.btn_chad_online = DummyWidget()
    app.btn_chad_copy = DummyWidget()
    app.btn_chad_clear = DummyWidget()
    app.btn_chad_top = DummyWidget()
    app.btn_chad_bottom = DummyWidget()
    app.chad_auto_scroll_check = DummyWidget()

    app._update_chad_controls_state()

    assert app.openai_api_key_entry.states[-1] == "disabled"
    assert app.chad_analysis_text.states[-1] == "disabled"
    assert app.chad_chat_status_var.get() == "Chad-Anbindung deaktiviert."
    assert app.chad_online_status_var.get() == "Online-Analyse: deaktiviert"


def test_update_chad_controls_state_updates_dev_filter_status_hint():
    app = App.__new__(App)
    app.chad_enabled_var = DummyVar(True)
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)
    app.chad_dev_filter_status_var = DummyVar("")
    app.chad_chat_status_var = DummyVar("")
    app.chad_online_status_var = DummyVar("")
    app.chad_analysis_status_var = DummyVar("")
    app.openai_api_key_entry = DummyWidget()
    app.chad_analysis_text = DummyWidget()
    app.btn_chad_api_paste = DummyWidget()
    app.btn_chad_api_apply = DummyWidget()
    app.btn_chad_api_save = DummyWidget()
    app.btn_chad_api_load = DummyWidget()
    app.btn_chad_api_clear = DummyWidget()
    app.btn_chad_api_delete = DummyWidget()
    app.btn_chad_take_analysis = DummyWidget()
    app.btn_chad_import_file = DummyWidget()
    app.btn_chad_online = DummyWidget()
    app.btn_chad_copy = DummyWidget()
    app.btn_chad_clear = DummyWidget()
    app.btn_chad_top = DummyWidget()
    app.btn_chad_bottom = DummyWidget()
    app.chad_auto_scroll_check = DummyWidget()

    app._update_chad_controls_state()

    assert "Dev-Umgebungsfilter aktiv" in app.chad_dev_filter_status_var.get()


def test_refresh_chad_runtime_status_marks_connected_model_and_tokens():
    app = App.__new__(App)
    app.ai_online_service = type(
        "DummyService",
        (),
        {"is_available": lambda self: True, "default_model": "gpt-4.1-mini"},
    )()
    app.chad_settings_api_status_var = DummyVar("")
    app.chad_settings_model_var = DummyVar("")
    app.chad_settings_latency_var = DummyVar("–")
    app.chad_settings_last_analysis_var = DummyVar("Noch keine Analyse")
    app.chad_settings_tokens_var = DummyVar("Platzhalter")

    chad_controller.refresh_chad_runtime_status(app)

    assert app.chad_settings_api_status_var.get() == "Verbunden"
    assert app.chad_settings_model_var.get() == "gpt-4.1-mini"
    assert app.chad_settings_tokens_var.get() == "Noch nicht verfügbar"


def test_run_chad_online_analysis_updates_ki_status_on_success():
    app = App.__new__(App)

    class DummyText:
        def __init__(self):
            self.content = ""

        def configure(self, **_kwargs):
            return None

        def delete(self, *_args):
            self.content = ""

        def insert(self, _index, text, *_tags):
            self.content += text

        def see(self, *_args):
            return None

    app.chad_enabled_var = DummyVar(True)
    app.chad_analysis_current_prompt = "demo"
    app.chad_analysis_status_var = DummyVar("")
    app.chad_online_status_var = DummyVar("")
    app.chad_analysis_source_var = DummyVar("Quelle: PATH Guard Analyse")
    app.chad_settings_api_status_var = DummyVar("")
    app.chad_settings_model_var = DummyVar("")
    app.chad_settings_latency_var = DummyVar("–")
    app.chad_settings_last_analysis_var = DummyVar("Noch keine Analyse")
    app.chad_settings_tokens_var = DummyVar("Platzhalter")
    app.chad_pending_files = []
    app.chad_online_result = ""
    app.chad_analysis_text = DummyText()
    app.chad_auto_scroll_var = DummyVar(False)
    app.chad_output_filter_var = DummyVar("Alles")
    app.chad_output_entries = []
    app.tr = lambda _key, default=None: default or _key
    app.confirm_chad_send = lambda *_args: True
    app.after = lambda _delay, callback: callback()
    app.ai_online_service = type(
        "DummyService",
        (),
        {
            "is_available": lambda self: True,
            "default_model": "gpt-4.1-mini",
            "last_usage_text": "Gesamt: 20 | Input: 12 | Output: 8",
            "analyze": lambda self, *_args, **_kwargs: (True, "ok"),
        },
    )()

    app.run_chad_online_analysis()

    assert app.chad_settings_api_status_var.get() == "Verbunden"
    assert app.chad_settings_model_var.get() == "gpt-4.1-mini"
    assert (
        app.chad_settings_last_analysis_var.get() == "Abgeschlossen: PATH Guard Analyse"
    )
    assert app.chad_settings_latency_var.get().endswith(" ms")
    assert app.chad_online_result == "ok"
    assert app.chad_settings_tokens_var.get() == "Gesamt: 20 | Input: 12 | Output: 8"
    assert app.chad_output_entries[-1]["text"] == "ok"


def test_send_chad_chat_message_returns_break_without_confirmation():
    app = App.__new__(App)

    class DummyText:
        def get(self, *_args):
            return "hello"

        def configure(self, **_kwargs):
            return None

        def delete(self, *_args):
            return None

        def insert(self, *_args):
            return None

        def mark_set(self, *_args):
            return None

        def mark_gravity(self, *_args):
            return None

        def see(self, *_args):
            return None

        def focus_force(self):
            return None

        def index(self, *_args):
            return "1.0"

    app.chad_enabled_var = DummyVar(True)
    app.chad_analysis_text = DummyText()
    app.chad_chat_status_var = DummyVar("")
    app.chad_pending_files = []
    app.chad_chat_history = []
    app.tr = lambda _key, default=None: default or _key
    app.append_to_chad_output = lambda *args: None
    app.after = lambda _delay, callback: callback()
    app.ai_online_service = type(
        "DummyService",
        (),
        {
            "is_available": lambda self: True,
            "chat": lambda self, *_args, **_kwargs: (True, "ok"),
        },
    )()
    app.confirm_chad_send = lambda *args: (_ for _ in ()).throw(
        AssertionError("should not be called")
    )

    result = app.send_chad_chat_message()

    assert result == "break"


def test_refresh_chad_output_view_filters_answers_and_results():
    class DummyText:
        def __init__(self):
            self.content = ""
            self.states = []

        def configure(self, **kwargs):
            state = kwargs.get("state")
            if state is not None:
                self.states.append(state)

        def delete(self, *_args):
            self.content = ""

        def insert(self, _index, text, *_tags):
            self.content += text

        def get(self, *_args):
            return self.content

        def see(self, *_args):
            return None

    app = App.__new__(App)
    app.chad_analysis_text = DummyText()
    app.chad_auto_scroll_var = DummyVar(False)
    app.chad_output_filter_var = DummyVar("Alles")
    app.chad_output_entries = [
        {"title": "PATH Guard Analyse", "text": "result text", "kind": "result"},
        {"title": "Chad", "text": "answer text", "kind": "answer"},
        {"title": "Du", "text": "user text", "kind": "user"},
    ]

    chad_controller.refresh_chad_output_view(app)
    assert "result text" in app.chad_analysis_text.content
    assert "answer text" in app.chad_analysis_text.content
    assert "user text" in app.chad_analysis_text.content

    app.chad_output_filter_var.set("Nur Antworten")
    chad_controller.refresh_chad_output_view(app)
    assert "answer text" in app.chad_analysis_text.content
    assert "result text" not in app.chad_analysis_text.content
    assert "user text" not in app.chad_analysis_text.content

    app.chad_output_filter_var.set("Nur Ergebnisse")
    chad_controller.refresh_chad_output_view(app)
    assert "result text" in app.chad_analysis_text.content
    assert "answer text" not in app.chad_analysis_text.content
    assert "user text" not in app.chad_analysis_text.content


def test_run_chad_online_analysis_uses_custom_confirmation():
    app = App.__new__(App)
    calls = []

    app.chad_enabled_var = DummyVar(True)
    app.chad_analysis_current_prompt = "demo"
    app.chad_analysis_status_var = DummyVar("")
    app.chad_online_status_var = DummyVar("")
    app.ai_online_service = type(
        "DummyService",
        (),
        {"is_available": lambda self: True},
    )()
    app.confirm_chad_send = lambda title, text: calls.append((title, text)) or False

    app.run_chad_online_analysis()

    assert calls[0][0] == "Online Analyse"
    assert "OpenAI API" in calls[0][1]
    assert app.chad_online_status_var.get() == "Online-Analyse: abgebrochen"
