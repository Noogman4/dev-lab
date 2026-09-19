import inspect
import json
import os

import netmon.app as app_module
from netmon.app import App
from netmon.ui.tabs.settings_tab import (
    build_settings_donation,
    build_settings_general_system,
    build_settings_logging,
    build_settings_maintenance,
    build_settings_privacy,
    build_settings_security,
    build_settings_tab,
)
from netmon.ui.tabs.chad_settings_tab import (
    build_security_systemcheck_panel,
    build_chad_settings_summary,
    build_chad_settings_tab,
)
from netmon.ui.tabs.theme_studio_tab import (
    build_theme_studio_color_controls,
    build_theme_studio_layout,
    build_theme_studio_style_actions,
)
from netmon.ui.tabs.vpn_slots_tab import build_vpn_slots_tab


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_load_settings_updates_defaults_from_config(tmp_path):
    app = App.__new__(App)
    app.settings = App._default_settings_payload(app)
    app.netmon_config_path = str(tmp_path / "config.json")
    app.log = lambda _message: None

    with open(app.netmon_config_path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "language": "en",
                "path_guard_autorun": True,
                "chad_preview_popup": True,
                "start_network_mode": "vpn",
            },
            handle,
        )

    app.load_settings()

    assert app.settings["language"] == "en"
    assert app.settings["path_guard_autorun"] is True
    assert app.settings["chad_preview_popup"] is True
    assert app.settings["start_network_mode"] == "system"
    assert app.settings["startup_guard_autorun"] is True


def test_apply_settings_from_ui_updates_runtime_and_persists():
    app = App.__new__(App)
    app.settings = App._default_settings_payload(app)
    app.lang_service = type(
        "DummyLangService",
        (),
        {"load": lambda self, code: {"loaded_language": code}},
    )()
    app.lang = {}
    app.var_language = DummyVar("en")
    app.var_startup_guard_autorun = DummyVar(False)
    app.var_path_guard_autorun = DummyVar(True)
    app.autostart_var = DummyVar(False)
    app.var_start_network_mode = DummyVar("vpn")
    app.var_start_vpn_profile = DummyVar("proton")
    app.var_dns_guard_enabled = DummyVar(False)
    app.var_dnssec_mode = DummyVar("strict")
    app.var_start_killswitch = DummyVar(True)
    app.var_start_security_monitoring = DummyVar(True)
    app.var_start_dot = DummyVar(False)
    app.var_theme_choice = DummyVar("Dark")
    app.var_auto_log_clear = DummyVar(True)
    app.var_debug_network_logging = DummyVar(True)
    app.var_ufw_logging_default = DummyVar("low")
    app.var_auto_switch_to_chad = DummyVar(False)
    app.var_chad_preview_popup = DummyVar(True)
    app.chad_model_var = DummyVar("gpt-4.1")
    app.var_systemcheck_security_summary = DummyVar(True)
    app.var_systemcheck_startup_guard = DummyVar(True)
    app.var_systemcheck_path_guard = DummyVar(True)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(True)
    app.var_systemcheck_rkhunter = DummyVar(False)

    app.var_systemcheck_clamav = DummyVar(True)
    app.chad_profile_var = DummyVar("security")
    app.chad_profile_var = DummyVar("security")
    app.chad_analysis_mode_var = DummyVar("expert")
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(True)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_beginner_var = DummyVar(True)
    app.chad_filter_rawdata_var = DummyVar(True)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)
    app.chad_focus_security_var = DummyVar(True)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(True)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(True)
    app.chad_focus_performance_var = DummyVar(True)
    app.chad_focus_optimization_var = DummyVar(True)
    app.chad_focus_rootkit_var = DummyVar(True)
    app.chad_systemcheck_profile_var = DummyVar("network")
    app.chad_answer_short_var = DummyVar(True)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(False)
    app.chad_answer_risk_var = DummyVar(True)
    app.chad_answer_recommendations_var = DummyVar(False)
    app.dns_guard_enabled_var = DummyVar(True)
    app.strict_protection_var = DummyVar(False)
    app.privacy_config = {}
    calls = []
    app.save_settings = lambda log_success=True: calls.append(("settings", log_success))
    app.save_privacy_config = lambda: calls.append(("privacy", None))
    app.log = lambda message: calls.append(("log", message))
    app.tr = lambda key, default=None: default or key
    app._apply_settings_runtime_state = lambda: calls.append(("runtime", None))

    app.apply_settings_from_ui()

    assert app.settings["language"] == "en"
    assert app.settings["startup_guard_autorun"] is False
    assert app.settings["path_guard_autorun"] is True
    assert app.settings["start_network_mode"] == "system"
    assert app.settings["start_vpn_profile"] == ""
    assert app.settings["dns_guard_enabled"] is False
    assert app.settings["dnssec_mode"] == "strict"
    assert app.settings["start_killswitch"] is False
    assert app.settings["start_security_monitoring"] is True
    assert app.settings["start_dot"] is False
    assert app.settings["theme"] == "dark"
    assert app.settings["auto_log_clear"] is True
    assert app.settings["debug_network_logging"] is True
    assert app.settings["strict_protection"] is False
    assert app.settings["ufw_logging_default"] == "low"
    assert app.settings["auto_switch_to_chad"] is False
    assert app.settings["chad_preview_popup"] is True
    assert app.settings["chad_model"] == "gpt-4.1"
    assert app.settings["systemcheck_security_summary"] is True
    assert app.settings["systemcheck_startup_guard"] is True
    assert app.settings["systemcheck_path_guard"] is True
    assert app.settings["systemcheck_process_guard"] is False
    assert app.settings["systemcheck_lynis"] is True
    assert app.settings["systemcheck_rkhunter"] is False
    assert app.settings["systemcheck_clamav"] is True
    assert app.settings["chad_profile"] == "security"
    assert app.settings["chad_analysis_mode"] == "expert"
    assert app.settings["chad_filter_relevant"] is False
    assert app.settings["chad_filter_critical"] is True
    assert app.settings["chad_filter_recommendations"] is False
    assert app.settings["chad_filter_beginner"] is True
    assert app.settings["chad_filter_rawdata"] is True
    assert app.settings["chad_filter_technical"] is False
    assert app.settings["chad_filter_hide_normal_services"] is False
    assert app.settings["chad_filter_ignore_harmless_processes"] is False
    assert app.settings["chad_filter_ignore_dev_environment"] is True
    assert app.settings["chad_focus_security"] is True
    assert app.settings["chad_focus_dns"] is False
    assert app.settings["chad_focus_network"] is True
    assert app.settings["chad_focus_process"] is False
    assert app.settings["chad_focus_firewall"] is True
    assert app.settings["chad_focus_performance"] is True
    assert app.settings["chad_focus_optimization"] is True
    assert app.settings["chad_focus_rootkit"] is True
    assert app.settings["chad_systemcheck_profile"] == "network"
    assert app.settings["chad_answer_short"] is True
    assert app.settings["chad_answer_detailed"] is False
    assert app.settings["chad_answer_step"] is False
    assert app.settings["chad_answer_linux_help"] is False
    assert app.settings["chad_answer_risk"] is True
    assert app.settings["chad_answer_recommendations"] is False
    assert app.lang["loaded_language"] == "en"
    assert calls == [
        ("runtime", None),
        ("settings", True),
        ("privacy", None),
        ("log", "Sprache geändert – Neustart empfohlen."),
        ("log", "Einstellungen übernommen."),
    ]


def test_save_theme_studio_profile_writes_json_payload(tmp_path, monkeypatch):
    app = App.__new__(App)
    app.var_theme_studio_accent = DummyVar("#ff3366")
    app.var_theme_studio_panel = DummyVar("#fff1f6")
    app.var_theme_studio_style = DummyVar("kräftig")
    app.var_theme_studio_profile_name = DummyVar("Mein Pop Theme")
    app.theme_studio_status_var = DummyVar("")
    app.log = lambda _message: None

    target = tmp_path / "my-theme.json"

    class DummyDialog:
        @staticmethod
        def asksaveasfilename(**_kwargs):
            return str(target)

    monkeypatch.setattr(app_module, "filedialog", DummyDialog)
    app._ensure_theme_studio_profiles_dir = lambda: str(tmp_path)

    assert app.save_theme_studio_profile() is True

    with open(target, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    assert payload["kind"] == "netmon_theme_studio_profile"
    assert payload["theme"] == "pop"
    assert payload["profile_name"] == "Mein Pop Theme"
    assert payload["accent"] == "#ff3366"
    assert payload["panel"] == "#fff1f6"
    assert payload["style"] == "kräftig"
    assert "Theme gespeichert:" in app.theme_studio_status_var.get()


def test_load_theme_studio_profile_reads_json_and_applies_pop(tmp_path, monkeypatch):
    app = App.__new__(App)
    app.var_theme_studio_base_theme = DummyVar("")
    app.var_theme_studio_accent = DummyVar("")
    app.var_theme_studio_panel = DummyVar("")
    app.var_theme_studio_style = DummyVar("")
    app.var_theme_studio_profile_name = DummyVar("")
    app.theme_studio_status_var = DummyVar("")
    app.log = lambda _message: None
    app._get_theme_display_name = lambda name: {"pop": "Pop"}.get(name, name)

    calls = []
    app.refresh_theme_studio_preview = lambda: calls.append("preview")
    app.apply_theme_studio_settings = lambda: calls.append("apply")

    source = tmp_path / "loaded-theme.json"
    with open(source, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "kind": "netmon_theme_studio_profile",
                "theme": "pop",
                "profile_name": "Studio Load",
                "accent": "#ff3366",
                "panel": "#fff1f6",
                "style": "warm",
            },
            handle,
        )

    class DummyDialog:
        @staticmethod
        def askopenfilename(**_kwargs):
            return str(source)

    monkeypatch.setattr(app_module, "filedialog", DummyDialog)
    app._ensure_theme_studio_profiles_dir = lambda: str(tmp_path)

    assert app.load_theme_studio_profile() is True
    assert app.var_theme_studio_base_theme.get() == "Pop"
    assert app.var_theme_studio_profile_name.get() == "Studio Load"
    assert app.var_theme_studio_accent.get() == "#ff3366"
    assert app.var_theme_studio_panel.get() == "#fff1f6"
    assert app.var_theme_studio_style.get() == "warm"
    assert calls == ["preview", "apply"]
    assert "Theme geladen und in Pop eingespielt" in app.theme_studio_status_var.get()


def test_debug_log_system_cmd_suppresses_repeated_polling_noise(monkeypatch):
    app = App.__new__(App)
    logs = []
    app.log_network_debug = logs.append

    times = iter((100.0, 105.0))
    monkeypatch.setattr(app_module.time, "time", lambda: next(times))

    app._debug_log_system_cmd(["wg", "show", "interfaces"], 0, "")
    app._debug_log_system_cmd(["wg", "show", "interfaces"], 0, "")

    assert logs == [
        "[VPN][WG] cmd: wg show interfaces",
        "[VPN][WG] rc: 0",
        "[VPN][WG] out: -",
    ]


def test_debug_log_system_cmd_logs_polling_change_immediately(monkeypatch):
    app = App.__new__(App)
    logs = []
    app.log_network_debug = logs.append

    times = iter((100.0, 105.0))
    monkeypatch.setattr(app_module.time, "time", lambda: next(times))

    app._debug_log_system_cmd(["wg", "show", "interfaces"], 0, "")
    app._debug_log_system_cmd(["wg", "show", "interfaces"], 0, "proton0")

    assert logs == [
        "[VPN][WG] cmd: wg show interfaces",
        "[VPN][WG] rc: 0",
        "[VPN][WG] out: -",
        "[VPN][WG] cmd: wg show interfaces",
        "[VPN][WG] rc: 0",
        "[VPN][WG] out: proton0",
    ]


def test_debug_nm_state_logs_single_summary_line(monkeypatch):
    app = App.__new__(App)
    logs = []
    app.log_safe = logs.append
    app.wg_profiles = ["Irland", "NL", "USA"]
    app.get_current_vpn_profile = lambda: ""
    app.get_wg_iface = lambda: ""

    outputs = iter(
        (
            (0, "eth0:ethernet:enp4s0:activated\nlo:loopback:lo:activated\n"),
            (0, "eth0:ethernet:enp4s0:activated\n"),
        )
    )
    monkeypatch.setattr(app_module, "has_cmd", lambda _name: True)
    monkeypatch.setattr(app_module, "run_cmd", lambda _cmd, timeout=10: next(outputs))

    app.debug_nm_state("Start")

    assert logs == [
        "Netzwerkstatus (Start): VPN aus, kein WG-Interface, 3 Profile geladen, 1/2 NM-Verbindungen aktiv"
    ]


def test_debug_nm_state_reports_missing_nmcli_in_summary(monkeypatch):
    app = App.__new__(App)
    logs = []
    app.log_safe = logs.append
    app.wg_profiles = []
    app.get_current_vpn_profile = lambda: "proton"
    app.get_wg_iface = lambda: "proton0"

    monkeypatch.setattr(app_module, "has_cmd", lambda _name: False)

    app.debug_nm_state("Start")

    assert logs == [
        "Netzwerkstatus (Start): VPN proton, WG proton0, 0 Profile geladen, NetworkManager nicht verfügbar"
    ]


def test_apply_settings_from_ui_accepts_beige_theme():
    app = App.__new__(App)
    app.settings = App._default_settings_payload(app)
    app.lang_service = None
    app.var_language = DummyVar("de")
    app.var_startup_guard_autorun = DummyVar(True)
    app.var_path_guard_autorun = DummyVar(False)
    app.var_start_network_mode = DummyVar("system")
    app.var_start_vpn_profile = DummyVar("")
    app.var_dns_guard_enabled = DummyVar(True)
    app.var_dnssec_mode = DummyVar("standard")
    app.var_start_killswitch = DummyVar(False)
    app.var_start_security_monitoring = DummyVar(False)
    app.var_start_dot = DummyVar(False)
    app.var_theme_choice = DummyVar("Beige")
    app.var_auto_log_clear = DummyVar(False)
    app.var_debug_network_logging = DummyVar(False)
    app.var_ufw_logging_default = DummyVar("keep")
    app.var_auto_switch_to_chad = DummyVar(True)
    app.var_chad_preview_popup = DummyVar(False)
    app.chad_model_var = DummyVar("gpt-4.1-mini")
    app.var_systemcheck_security_summary = DummyVar(True)
    app.var_systemcheck_startup_guard = DummyVar(True)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(True)
    app.var_systemcheck_lynis = DummyVar(True)
    app.var_systemcheck_rkhunter = DummyVar(False)
    app.var_systemcheck_clamav = DummyVar(False)
    app.chad_profile_var = DummyVar("custom")
    app.chad_analysis_mode_var = DummyVar("standard")
    app.chad_filter_relevant_var = DummyVar(True)
    app.chad_filter_critical_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(True)
    app.chad_filter_beginner_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(True)
    app.chad_filter_hide_normal_services_var = DummyVar(True)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(True)
    app.chad_filter_ignore_dev_environment_var = DummyVar(True)
    app.chad_focus_security_var = DummyVar(True)
    app.chad_focus_dns_var = DummyVar(True)
    app.chad_focus_network_var = DummyVar(True)
    app.chad_focus_process_var = DummyVar(True)
    app.chad_focus_firewall_var = DummyVar(True)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(False)
    app.chad_focus_rootkit_var = DummyVar(False)
    app.chad_systemcheck_profile_var = DummyVar("custom")
    app.chad_answer_short_var = DummyVar(False)
    app.chad_answer_detailed_var = DummyVar(True)
    app.chad_answer_step_var = DummyVar(True)
    app.chad_answer_linux_help_var = DummyVar(True)
    app.chad_answer_risk_var = DummyVar(True)
    app.chad_answer_recommendations_var = DummyVar(True)
    app.strict_protection_var = DummyVar(True)
    app.save_settings = lambda log_success=True: None
    app.log = lambda _message: None
    app.tr = lambda key, default=None: default or key
    app._apply_settings_runtime_state = lambda: None

    app.apply_settings_from_ui()

    assert app.settings["theme"] == "beige"


def test_apply_chad_profile_sets_beginner_preset():
    app = App.__new__(App)
    app.chad_profile_var = DummyVar("beginner")
    app.chad_analysis_status_var = DummyVar("")
    app.security_systemcheck_status_var = DummyVar("")
    app.chad_settings_model_var = DummyVar("")
    app.chad_model_var = DummyVar("gpt-4.1-mini")
    app.ai_online_service = type(
        "DummyService", (), {"default_model": "gpt-4.1-mini"}
    )()
    app._update_chad_controls_state = lambda: None
    app.chad_analysis_mode_var = DummyVar("expert")
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(True)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_beginner_var = DummyVar(False)
    app.chad_filter_rawdata_var = DummyVar(True)
    app.chad_filter_technical_var = DummyVar(True)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(True)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(True)
    app.chad_focus_optimization_var = DummyVar(True)
    app.chad_focus_rootkit_var = DummyVar(True)
    app.chad_answer_short_var = DummyVar(True)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(False)
    app.chad_answer_risk_var = DummyVar(False)
    app.chad_answer_recommendations_var = DummyVar(False)
    app.chad_systemcheck_profile_var = DummyVar("custom")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(True)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(True)
    app.var_systemcheck_clamav = DummyVar(True)

    app.apply_chad_profile()

    assert app.chad_analysis_mode_var.get() == "beginner"
    assert app.chad_filter_beginner_var.get() is True
    assert app.chad_filter_technical_var.get() is False
    assert app.chad_focus_process_var.get() is False
    assert app.chad_answer_step_var.get() is True
    assert app.chad_model_var.get() == "gpt-4.1-mini"
    assert app.chad_systemcheck_profile_var.get() == "quick"
    assert "Anfängerprofil" in app.chad_analysis_status_var.get()


def test_apply_chad_profile_sets_security_preset():
    app = App.__new__(App)
    app.chad_profile_var = DummyVar("security")
    app.chad_analysis_status_var = DummyVar("")
    app.security_systemcheck_status_var = DummyVar("")
    app.chad_settings_model_var = DummyVar("")
    app.chad_model_var = DummyVar("gpt-4.1-mini")
    app.ai_online_service = type(
        "DummyService", (), {"default_model": "gpt-4.1-mini"}
    )()
    app._update_chad_controls_state = lambda: None
    app.chad_analysis_mode_var = DummyVar("standard")
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(False)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_beginner_var = DummyVar(True)
    app.chad_filter_rawdata_var = DummyVar(False)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(True)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(True)
    app.chad_focus_optimization_var = DummyVar(True)
    app.chad_focus_rootkit_var = DummyVar(False)
    app.chad_answer_short_var = DummyVar(False)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(True)
    app.chad_answer_risk_var = DummyVar(False)
    app.chad_answer_recommendations_var = DummyVar(False)
    app.chad_systemcheck_profile_var = DummyVar("custom")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(False)
    app.var_systemcheck_clamav = DummyVar(False)

    app.apply_chad_profile()

    assert app.chad_analysis_mode_var.get() == "expert"
    assert app.chad_filter_critical_var.get() is True
    assert app.chad_focus_process_var.get() is True
    assert app.chad_focus_rootkit_var.get() is True
    assert app.chad_answer_short_var.get() is True
    assert app.chad_model_var.get() == "gpt-4.1"
    assert app.chad_systemcheck_profile_var.get() == "security"
    assert "Sicherheitsfokus" in app.chad_analysis_status_var.get()


def test_apply_chad_model_selection_updates_service_and_status():
    app = App.__new__(App)
    app.chad_model_var = DummyVar("gpt-4.1")
    app.chad_settings_model_var = DummyVar("")
    app.ai_online_service = type(
        "DummyService", (), {"default_model": "gpt-4.1-mini"}
    )()

    app.apply_chad_model_selection()

    assert app.ai_online_service.default_model == "gpt-4.1"
    assert app.chad_settings_model_var.get() == "gpt-4.1"


def test_apply_chad_profile_sets_network_recommended_model():
    app = App.__new__(App)
    app.chad_profile_var = DummyVar("network")
    app.chad_analysis_status_var = DummyVar("")
    app.security_systemcheck_status_var = DummyVar("")
    app.chad_settings_model_var = DummyVar("")
    app.ai_online_service = type(
        "DummyService", (), {"default_model": "gpt-4.1-mini"}
    )()
    app._update_chad_controls_state = lambda: None
    app.chad_analysis_mode_var = DummyVar("expert")
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(True)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_beginner_var = DummyVar(True)
    app.chad_filter_rawdata_var = DummyVar(True)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(True)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(False)
    app.chad_focus_optimization_var = DummyVar(True)
    app.chad_focus_rootkit_var = DummyVar(True)
    app.chad_answer_short_var = DummyVar(True)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(False)
    app.chad_answer_risk_var = DummyVar(False)
    app.chad_answer_recommendations_var = DummyVar(False)
    app.chad_model_var = DummyVar("gpt-4.1-mini")
    app.chad_systemcheck_profile_var = DummyVar("custom")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(False)
    app.var_systemcheck_clamav = DummyVar(False)

    app.apply_chad_profile()

    assert app.chad_model_var.get() == "gpt-4o-mini"
    assert app.ai_online_service.default_model == "gpt-4o-mini"
    assert app.chad_systemcheck_profile_var.get() == "network"


def test_mark_chad_profile_custom_switches_profile_label():
    app = App.__new__(App)
    app._applying_chad_profile = False
    app.chad_profile_var = DummyVar("security")
    app.chad_analysis_status_var = DummyVar("")

    app.mark_chad_profile_custom()

    assert app.chad_profile_var.get() == "custom"
    assert app.chad_analysis_status_var.get() == "Chad-Profil aktiv: Benutzerdefiniert"


def test_apply_chad_systemcheck_profile_sets_quick_preset():
    app = App.__new__(App)
    app.chad_systemcheck_profile_var = DummyVar("quick")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(True)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(True)
    app.var_systemcheck_clamav = DummyVar(True)
    app.security_systemcheck_status_var = DummyVar("")

    app.apply_chad_systemcheck_profile()

    assert app.var_systemcheck_security_summary.get() is True
    assert app.var_systemcheck_startup_guard.get() is True
    assert app.var_systemcheck_path_guard.get() is True
    assert app.var_systemcheck_process_guard.get() is False
    assert app.var_systemcheck_lynis.get() is True
    assert app.var_systemcheck_rkhunter.get() is False
    assert app.var_systemcheck_clamav.get() is False
    assert "Schnellcheck" in app.security_systemcheck_status_var.get()


def test_apply_chad_systemcheck_profile_sets_network_preset():
    app = App.__new__(App)
    app.chad_systemcheck_profile_var = DummyVar("network")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(True)
    app.var_systemcheck_path_guard = DummyVar(False)
    app.var_systemcheck_process_guard = DummyVar(True)
    app.var_systemcheck_lynis = DummyVar(True)
    app.var_systemcheck_rkhunter = DummyVar(True)
    app.var_systemcheck_clamav = DummyVar(True)
    app.security_systemcheck_status_var = DummyVar("")

    app.apply_chad_systemcheck_profile()

    assert app.var_systemcheck_security_summary.get() is True
    assert app.var_systemcheck_startup_guard.get() is False
    assert app.var_systemcheck_path_guard.get() is True
    assert app.var_systemcheck_process_guard.get() is False
    assert app.var_systemcheck_lynis.get() is False
    assert app.var_systemcheck_rkhunter.get() is False
    assert app.var_systemcheck_clamav.get() is False
    assert "Netzwerkcheck" in app.security_systemcheck_status_var.get()


def test_mark_chad_systemcheck_profile_custom_switches_profile_label():
    app = App.__new__(App)
    app._applying_chad_systemcheck_profile = False
    app.chad_systemcheck_profile_var = DummyVar("quick")
    app.security_systemcheck_status_var = DummyVar("")

    app.mark_chad_systemcheck_profile_custom()

    assert app.chad_systemcheck_profile_var.get() == "custom"
    assert (
        app.security_systemcheck_status_var.get()
        == "Systemcheck-Profil aktiv: Benutzerdefiniert"
    )


def test_reset_settings_to_defaults_restores_defaults():
    app = App.__new__(App)
    app.settings = {
        "language": "en",
        "startup_guard_autorun": False,
        "path_guard_autorun": True,
        "start_network_mode": "vpn",
        "start_vpn_profile": "proton",
        "dns_guard_enabled": False,
        "dnssec_mode": "strict",
        "start_killswitch": True,
        "start_security_monitoring": True,
        "start_dot": True,
        "theme": "dark",
        "auto_log_clear": True,
        "debug_network_logging": True,
        "strict_protection": False,
        "ufw_logging_default": "high",
        "auto_switch_to_chad": False,
        "chad_preview_popup": True,
        "systemcheck_security_summary": False,
        "systemcheck_startup_guard": False,
        "systemcheck_path_guard": True,
        "systemcheck_process_guard": False,
        "systemcheck_lynis": False,
        "systemcheck_rkhunter": True,
        "systemcheck_clamav": True,
        "chad_profile": "security",
        "chad_analysis_mode": "expert",
        "chad_filter_relevant": False,
        "chad_filter_critical": True,
        "chad_filter_recommendations": False,
        "chad_filter_beginner": True,
        "chad_filter_rawdata": True,
        "chad_filter_technical": False,
        "chad_filter_hide_normal_services": False,
        "chad_filter_ignore_harmless_processes": False,
        "chad_filter_ignore_dev_environment": False,
        "chad_focus_security": False,
        "chad_focus_dns": False,
        "chad_focus_network": False,
        "chad_focus_process": False,
        "chad_focus_firewall": False,
        "chad_focus_performance": True,
        "chad_focus_optimization": True,
        "chad_focus_rootkit": True,
        "chad_systemcheck_profile": "network",
        "chad_answer_short": True,
        "chad_answer_detailed": False,
        "chad_answer_step": False,
        "chad_answer_linux_help": False,
        "chad_answer_risk": False,
        "chad_answer_recommendations": False,
    }
    app.var_language = DummyVar("en")
    app.var_startup_guard_autorun = DummyVar(False)
    app.var_path_guard_autorun = DummyVar(True)
    app.autostart_var = DummyVar(False)
    app.var_start_network_mode = DummyVar("vpn")
    app.var_start_vpn_profile = DummyVar("proton")
    app.var_dns_guard_enabled = DummyVar(False)
    app.var_dnssec_mode = DummyVar("strict")
    app.var_start_killswitch = DummyVar(True)
    app.var_start_security_monitoring = DummyVar(True)
    app.var_start_dot = DummyVar(True)
    app.var_theme_choice = DummyVar("Dark")
    app.var_auto_log_clear = DummyVar(True)
    app.var_debug_network_logging = DummyVar(True)
    app.var_ufw_logging_default = DummyVar("high")
    app.var_auto_switch_to_chad = DummyVar(False)
    app.var_chad_preview_popup = DummyVar(True)
    app.chad_model_var = DummyVar("gpt-4o-mini")
    app.var_systemcheck_security_summary = DummyVar(False)
    app.var_systemcheck_startup_guard = DummyVar(False)
    app.var_systemcheck_path_guard = DummyVar(True)
    app.var_systemcheck_process_guard = DummyVar(False)
    app.var_systemcheck_lynis = DummyVar(False)
    app.var_systemcheck_rkhunter = DummyVar(True)
    app.var_systemcheck_clamav = DummyVar(True)
    app.chad_profile_var = DummyVar("security")
    app.chad_analysis_mode_var = DummyVar("expert")
    app.chad_filter_relevant_var = DummyVar(False)
    app.chad_filter_critical_var = DummyVar(True)
    app.chad_filter_recommendations_var = DummyVar(False)
    app.chad_filter_beginner_var = DummyVar(True)
    app.chad_filter_rawdata_var = DummyVar(True)
    app.chad_filter_technical_var = DummyVar(False)
    app.chad_filter_hide_normal_services_var = DummyVar(False)
    app.chad_filter_ignore_harmless_processes_var = DummyVar(False)
    app.chad_filter_ignore_dev_environment_var = DummyVar(False)
    app.chad_focus_security_var = DummyVar(False)
    app.chad_focus_dns_var = DummyVar(False)
    app.chad_focus_network_var = DummyVar(False)
    app.chad_focus_process_var = DummyVar(False)
    app.chad_focus_firewall_var = DummyVar(False)
    app.chad_focus_performance_var = DummyVar(True)
    app.chad_focus_optimization_var = DummyVar(True)
    app.chad_focus_rootkit_var = DummyVar(True)
    app.chad_systemcheck_profile_var = DummyVar("network")
    app.chad_answer_short_var = DummyVar(True)
    app.chad_answer_detailed_var = DummyVar(False)
    app.chad_answer_step_var = DummyVar(False)
    app.chad_answer_linux_help_var = DummyVar(False)
    app.chad_answer_risk_var = DummyVar(False)
    app.chad_answer_recommendations_var = DummyVar(False)
    app.dns_guard_enabled_var = DummyVar(False)
    app.strict_protection_var = DummyVar(False)
    app.lang_service = type(
        "DummyLangService",
        (),
        {"load": lambda self, code: {"loaded_language": code}},
    )()
    app.save_settings = lambda log_success=True: None
    app.save_privacy_config = lambda: None
    app.is_autostart_enabled = lambda: True
    app.log = lambda _message: None
    app.tr = lambda key, default=None: default or key

    app.reset_settings_to_defaults()

    assert app.settings == App._default_settings_payload(app)
    assert app.lang["loaded_language"] == "de"
    assert app.var_language.get() == "de"
    assert app.var_startup_guard_autorun.get() is True
    assert app.var_path_guard_autorun.get() is False
    assert app.var_start_network_mode.get() == "system"
    assert app.var_start_vpn_profile.get() == ""
    assert app.autostart_var.get() is True
    assert app.var_dns_guard_enabled.get() is True
    assert app.var_dnssec_mode.get() == "standard"
    assert app.var_start_killswitch.get() is False
    assert app.var_start_security_monitoring.get() is False
    assert app.var_start_dot.get() is False
    assert app.var_theme_choice.get() == "Dark"
    assert app.var_auto_log_clear.get() is False
    assert app.var_debug_network_logging.get() is False
    assert app.var_ufw_logging_default.get() == "keep"
    assert app.strict_protection_var.get() is True
    assert app.var_auto_switch_to_chad.get() is True
    assert app.var_chad_preview_popup.get() is False
    assert app.chad_model_var.get() == "gpt-4.1-mini"
    assert app.var_systemcheck_security_summary.get() is True
    assert app.var_systemcheck_startup_guard.get() is True
    assert app.var_systemcheck_path_guard.get() is True
    assert app.var_systemcheck_process_guard.get() is True
    assert app.var_systemcheck_lynis.get() is True
    assert app.var_systemcheck_rkhunter.get() is False
    assert app.var_systemcheck_clamav.get() is False
    assert app.chad_profile_var.get() == "custom"
    assert app.chad_analysis_mode_var.get() == "standard"
    assert app.chad_filter_relevant_var.get() is True
    assert app.chad_filter_critical_var.get() is False
    assert app.chad_filter_recommendations_var.get() is True
    assert app.chad_filter_beginner_var.get() is False
    assert app.chad_filter_rawdata_var.get() is False
    assert app.chad_filter_technical_var.get() is True
    assert app.chad_filter_hide_normal_services_var.get() is True
    assert app.chad_filter_ignore_harmless_processes_var.get() is True
    assert app.chad_filter_ignore_dev_environment_var.get() is True
    assert app.chad_focus_security_var.get() is True
    assert app.chad_focus_dns_var.get() is True
    assert app.chad_focus_network_var.get() is True
    assert app.chad_focus_process_var.get() is True
    assert app.chad_focus_firewall_var.get() is True
    assert app.chad_focus_performance_var.get() is False
    assert app.chad_focus_optimization_var.get() is False
    assert app.chad_focus_rootkit_var.get() is False
    assert app.chad_systemcheck_profile_var.get() == "custom"
    assert app.chad_answer_short_var.get() is False
    assert app.chad_answer_detailed_var.get() is True
    assert app.chad_answer_step_var.get() is True
    assert app.chad_answer_linux_help_var.get() is True
    assert app.chad_answer_risk_var.get() is True
    assert app.chad_answer_recommendations_var.get() is True


def test_toggle_theme_cycles_through_all_four_modes():
    app = App.__new__(App)
    applied = []
    app._app_theme = app_module.LIGHT_THEME
    app.apply_theme = lambda theme_name: applied.append(theme_name)

    app.toggle_theme()
    app._app_theme = app_module.DARK_THEME
    app.toggle_theme()
    app._app_theme = app_module.BEIGE_THEME
    app.toggle_theme()
    app._app_theme = app_module.POP_THEME
    app.toggle_theme()

    assert applied == ["dark", "beige", "pop", "light"]


def test_enable_and_disable_autostart_manage_user_desktop_file(tmp_path, monkeypatch):
    autostart_dir = tmp_path / "autostart"
    autostart_file = autostart_dir / "netmon.desktop"
    launcher = tmp_path / "netmon_main.py"
    launcher.write_text("print('demo')\n", encoding="utf-8")

    monkeypatch.setattr(app_module, "AUTOSTART_DIR", str(autostart_dir))
    monkeypatch.setattr(app_module, "AUTOSTART_FILE", str(autostart_file))
    monkeypatch.setattr(app_module.shutil, "which", lambda name: None)
    monkeypatch.setattr(app_module.sys, "argv", [str(launcher)])

    app = App.__new__(App)

    assert app.enable_autostart() is True
    assert autostart_file.exists()
    content = autostart_file.read_text(encoding="utf-8")
    assert "Type=Application" in content
    assert "Name=NetMon" in content
    assert f"Exec=python3 {os.path.abspath(launcher)}" in content
    assert "StartupWMClass=NetMon" in content
    assert app.is_autostart_enabled() is True

    assert app.disable_autostart() is True
    assert not autostart_file.exists()
    assert app.is_autostart_enabled() is False


def test_enable_autostart_prefers_installed_netmon_launcher(tmp_path, monkeypatch):
    autostart_dir = tmp_path / "autostart"
    autostart_file = autostart_dir / "netmon.desktop"

    monkeypatch.setattr(app_module, "AUTOSTART_DIR", str(autostart_dir))
    monkeypatch.setattr(app_module, "AUTOSTART_FILE", str(autostart_file))
    monkeypatch.setattr(app_module.shutil, "which", lambda name: "/usr/bin/netmon")

    app = App.__new__(App)

    assert app.enable_autostart() is True
    content = autostart_file.read_text(encoding="utf-8")
    assert "Exec=netmon" in content
    assert "StartupWMClass=NetMon" in content


def test_enable_and_disable_radio_desktop_launcher_manage_user_entry(
    tmp_path, monkeypatch
):
    desktop_dir = tmp_path / "applications"
    desktop_file = desktop_dir / "netmon-radio.desktop"
    captured = {}

    def _ensure_radio_desktop_entry(theme_name=None, started_from=None):
        captured.update(
            {
                "theme_name": theme_name,
                "started_from": started_from,
            }
        )
        desktop_dir.mkdir(parents=True, exist_ok=True)
        desktop_file.write_text("[Desktop Entry]\n", encoding="utf-8")
        return str(desktop_file)

    monkeypatch.setattr(
        app_module.netmon_radio_core,
        "radio_desktop_entry_path",
        lambda: str(desktop_file),
    )
    monkeypatch.setattr(
        app_module.netmon_radio_core,
        "ensure_radio_desktop_entry",
        _ensure_radio_desktop_entry,
    )

    app = App.__new__(App)
    app._current_radio_theme_name = lambda: "dark"

    assert app.enable_radio_desktop_launcher() is True
    assert desktop_file.exists()
    assert captured == {
        "theme_name": "dark",
        "started_from": "desktop",
    }
    assert app.is_radio_desktop_launcher_enabled() is True

    assert app.disable_radio_desktop_launcher() is True
    assert not desktop_file.exists()
    assert app.is_radio_desktop_launcher_enabled() is False


def test_settings_tab_source_and_hooks_are_present():
    build_source = inspect.getsource(App.build_settings_tab)
    general_system_source = inspect.getsource(build_settings_general_system)
    donation_source = inspect.getsource(build_settings_donation)
    logging_source = inspect.getsource(build_settings_logging)
    maintenance_source = inspect.getsource(build_settings_maintenance)
    privacy_source = inspect.getsource(build_settings_privacy)
    security_source = inspect.getsource(build_settings_security)
    systemcheck_source = inspect.getsource(build_security_systemcheck_panel)
    chad_summary_source = inspect.getsource(build_chad_settings_summary)
    app_source = inspect.getsource(App)
    theme_layout_source = inspect.getsource(build_theme_studio_layout)
    theme_color_source = inspect.getsource(build_theme_studio_color_controls)
    theme_actions_source = inspect.getsource(build_theme_studio_style_actions)
    vpn_slots_source = inspect.getsource(build_vpn_slots_tab)
    wrapper_source = inspect.getsource(build_settings_tab)
    chad_wrapper_source = inspect.getsource(build_chad_settings_tab)

    assert '"settings_save_button"' in general_system_source
    save_button_pos = general_system_source.index('"settings_save_button"')
    restart_button_pos = general_system_source.index(
        '"settings_restart_netmon_only"', save_button_pos
    )
    reset_button_pos = general_system_source.index(
        '"settings_reset_button"', restart_button_pos
    )
    assert save_button_pos < restart_button_pos < reset_button_pos
    assert '"settings_autostart"' in general_system_source
    assert "app.autostart_var" in general_system_source
    assert "app.toggle_autostart" in general_system_source
    assert '"settings_radio_desktop_launcher"' in general_system_source
    assert "app.radio_desktop_launcher_var" in general_system_source
    assert "app.toggle_radio_desktop_launcher" in general_system_source
    assert '"settings_path_guard_autorun"' in security_source
    assert '"settings_group_system"' in maintenance_source
    assert "app.var_start_security_monitoring" in general_system_source
    assert "variable=self.var_start_network_mode" not in build_source
    assert "textvariable=self.var_start_vpn_profile" not in build_source
    assert "variable=self.var_start_killswitch" not in build_source
    assert "variable=self.var_start_dot" not in build_source
    assert "app.var_theme_choice" in general_system_source
    assert "list(theme_display_names.values())" in general_system_source
    assert 'app.tr("privacy_group_stealth", "ISP-Stealthmodus")' in privacy_source
    assert "app.isp_stealth_enabled" in privacy_source
    assert "app.isp_stealth_autostart" in privacy_source
    assert "app.isp_stealth_disable_ipv6" in privacy_source
    assert "app.isp_stealth_enable_killswitch" in privacy_source
    assert "textvariable=app.isp_stealth_vpn_choice" in privacy_source
    assert '"privacy_dns_profile_vpn_managed_hint"' in privacy_source
    assert "app.var_auto_log_clear" in logging_source
    assert "app.var_debug_network_logging" in logging_source
    assert "app.var_ufw_logging_default" in logging_source
    assert 'text=self.tr("settings_tab_backup", "Backup")' in build_source
    assert 'app.tr("settings_group_donation", "NetMon unterstützen")' in donation_source
    assert "app.var_donation_popup_enabled" in donation_source
    assert '"settings_donation_support_button"' in donation_source
    assert 'app.tr("settings_group_system", "System")' in maintenance_source
    assert "self._build_settings_backup_tab(settings_backup_tab)" in build_source
    assert "app.restart_netmon_only" in maintenance_source
    assert "def build_theme_studio_tab(self):" in app_source
    assert "def apply_theme_studio_settings(self):" in app_source
    assert "def save_theme_studio_profile(self):" in app_source
    assert "def load_theme_studio_profile(self):" in app_source
    assert '"Live-Vorschau"' in theme_layout_source
    assert '"Farbe wählen"' in theme_color_source
    assert '"theme_studio_btn_save_theme"' in theme_actions_source
    assert '"theme_studio_btn_load_theme"' in theme_actions_source
    assert '"Systembewertung"' in chad_summary_source
    assert "settings_security_systemcheck" in systemcheck_source
    assert "build_security_systemcheck_panel(" in app_source
    assert "vpn_side_panel" not in vpn_slots_source
    assert 'text=app.tr("tab_settings", "Einstellungen")' in wrapper_source
    assert (
        'text=app.tr("tab_chad_settings", "Chad Einstellungen")' in chad_wrapper_source
    )


def test_donation_popup_disable_waits_until_one_week():
    app = App.__new__(App)
    app.settings = {"donation_popup_first_seen_at": 1000}

    assert app.donation_popup_disable_allowed(now=1000 + 7 * 24 * 60 * 60 - 1) is False
    assert app.donation_popup_disable_allowed(now=1000 + 7 * 24 * 60 * 60) is True


def test_donation_popup_first_seen_is_persisted_once():
    app = App.__new__(App)
    app.settings = {"donation_popup_first_seen_at": 0}
    saved = []
    app.save_settings = lambda log_success=False: saved.append(log_success)

    first_seen = app._ensure_donation_popup_first_seen_at()
    second_seen = app._ensure_donation_popup_first_seen_at()

    assert first_seen > 0
    assert second_seen == first_seen
    assert saved == [False]


def test_apply_startup_settings_orchestrates_existing_actions(monkeypatch):
    app = App.__new__(App)
    actions = []

    app.settings = {
        "theme": "dark",
        "auto_log_clear": True,
        "dns_guard_enabled": True,
        "start_security_monitoring": True,
        "start_network_mode": "vpn",
        "start_vpn_profile": "proton",
        "start_killswitch": True,
        "start_dot": True,
        "ufw_logging_default": "low",
    }
    app._preferred_theme_name = "light"
    app.apply_theme = lambda theme, log_change=False, persist=False: actions.append(
        ("theme", theme, log_change, persist)
    )
    app.clear_log = lambda: actions.append(("clear_log",))
    app.set_dns_guard_enabled = lambda enabled: actions.append(("dns_guard", enabled))
    app.security_start_monitoring = lambda: actions.append(("security_monitoring",))
    app.run_async = lambda func, job_name="": (
        actions.append(("run_async", job_name)) or func()
    )
    app.vpn_switch = lambda profile, ensure_sudo=True: actions.append(
        ("vpn", profile, ensure_sudo)
    )
    app.killswitch_on = lambda **kwargs: actions.append(("killswitch", kwargs))
    app.enable_dot_async = lambda: actions.append(("dot",))
    app.set_ufw_logging = lambda level: actions.append(("ufw_logging", level))
    app.log_safe = lambda message: actions.append(("log", message))
    app.after = lambda _delay, callback: callback()

    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)

    app.apply_startup_settings()

    assert ("theme", "dark", False, False) in actions
    assert ("clear_log",) in actions
    assert ("dns_guard", True) in actions
    assert ("security_monitoring",) in actions
    assert not any(item[0] == "run_async" for item in actions)
    assert not any(item[0] == "vpn" for item in actions)
    assert not any(item[0] == "killswitch" for item in actions)
    assert ("dot",) not in actions
    assert ("ufw_logging", "low") in actions


def test_apply_startup_settings_accepts_beige_theme(monkeypatch):
    app = App.__new__(App)
    actions = []

    app.settings = {
        "theme": "beige",
        "auto_log_clear": False,
        "dns_guard_enabled": False,
        "start_security_monitoring": False,
        "start_network_mode": "system",
        "start_vpn_profile": "",
        "start_killswitch": False,
        "start_dot": False,
        "ufw_logging_default": "keep",
    }
    app._preferred_theme_name = "light"
    app.apply_theme = lambda theme, log_change=False, persist=False: actions.append(
        ("theme", theme, log_change, persist)
    )
    app.after = lambda _delay, callback: callback()
    app.set_dns_guard_enabled = lambda enabled: actions.append(("dns_guard", enabled))
    app.security_start_monitoring = lambda: actions.append(("security_monitoring",))
    app.run_async = lambda func, job_name="": None
    app.log_safe = lambda _message: None
    app.set_ufw_logging = lambda level: actions.append(("ufw_logging", level))

    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)

    app.apply_startup_settings()

    assert ("theme", "beige", False, False) in actions


def test_on_start_network_mode_changed_disables_only_killswitch_for_system():
    app = App.__new__(App)

    class WidgetStub:
        def __init__(self):
            self.state = None

        def configure(self, **kwargs):
            self.state = kwargs.get("state")

    app.var_start_network_mode = DummyVar("system")
    app.var_start_killswitch = DummyVar(True)
    app.var_start_dot = DummyVar(True)
    app.start_vpn_profile_combo = WidgetStub()
    app.cb_start_killswitch = WidgetStub()
    app.cb_start_dot = WidgetStub()

    app.on_start_network_mode_changed()

    assert app.var_start_killswitch.get() is False
    assert app.var_start_dot.get() is False
    assert app.start_vpn_profile_combo.state == "disabled"
    assert app.cb_start_killswitch.state == "disabled"
    assert app.cb_start_dot.state == "disabled"


def test_on_start_network_mode_changed_disables_dot_for_vpn():
    app = App.__new__(App)

    class WidgetStub:
        def __init__(self):
            self.state = None

        def configure(self, **kwargs):
            self.state = kwargs.get("state")

    app.var_start_network_mode = DummyVar("vpn")
    app.var_start_killswitch = DummyVar(False)
    app.var_start_dot = DummyVar(True)
    app.start_vpn_profile_combo = WidgetStub()
    app.cb_start_killswitch = WidgetStub()
    app.cb_start_dot = WidgetStub()

    app.on_start_network_mode_changed()

    assert app.var_start_killswitch.get() is False
    assert app.var_start_dot.get() is False
    assert app.start_vpn_profile_combo.state == "disabled"
    assert app.cb_start_killswitch.state == "disabled"
    assert app.cb_start_dot.state == "disabled"


def test_apply_startup_settings_uses_killswitch_off_for_isp(monkeypatch):
    app = App.__new__(App)
    actions = []

    app.settings = {
        "theme": "light",
        "auto_log_clear": False,
        "dns_guard_enabled": True,
        "start_security_monitoring": False,
        "start_network_mode": "system",
        "start_vpn_profile": "proton",
        "start_killswitch": True,
        "start_dot": True,
        "ufw_logging_default": "keep",
    }
    app._preferred_theme_name = "light"
    app.apply_theme = lambda theme, log_change=False, persist=False: actions.append(
        ("theme", theme, log_change, persist)
    )
    app.clear_log = lambda: actions.append(("clear_log",))
    app.set_dns_guard_enabled = lambda enabled: actions.append(("dns_guard", enabled))
    app.security_start_monitoring = lambda: actions.append(("security_monitoring",))
    app.run_async = lambda func, job_name="": (
        actions.append(("run_async", job_name)) or func()
    )
    app.vpn_switch = lambda profile, ensure_sudo=True: actions.append(
        ("vpn", profile, ensure_sudo)
    )
    app.killswitch_on = lambda **kwargs: actions.append(("killswitch_on", kwargs))
    app.killswitch_off = lambda **kwargs: actions.append(("killswitch_off", kwargs))
    app.enable_dot_async = lambda: actions.append(("dot",))
    app.set_ufw_logging = lambda level: actions.append(("ufw_logging", level))
    app.log_safe = lambda message: actions.append(("log", message))
    app.after = lambda _delay, callback: callback()

    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)

    app.apply_startup_settings()

    assert ("dns_guard", True) in actions
    assert not any(item[0] == "killswitch_off" for item in actions)
    assert not any(item[0] == "killswitch_on" for item in actions)
    assert not any(item[0] == "vpn" for item in actions)
    assert ("dot",) not in actions


def test_on_start_network_mode_changed_disables_killswitch_and_dot_for_offline():
    app = App.__new__(App)

    class WidgetStub:
        def __init__(self):
            self.state = None

        def configure(self, **kwargs):
            self.state = kwargs.get("state")

    app._normalize_start_network_mode = App._normalize_start_network_mode.__get__(
        app, App
    )
    app.var_start_network_mode = DummyVar("offline")
    app.var_start_killswitch = DummyVar(True)
    app.var_start_dot = DummyVar(True)
    app.start_vpn_profile_combo = WidgetStub()
    app.cb_start_killswitch = WidgetStub()
    app.cb_start_dot = WidgetStub()

    app.on_start_network_mode_changed()

    assert app.var_start_killswitch.get() is False
    assert app.var_start_dot.get() is False
    assert app.start_vpn_profile_combo.state == "disabled"
    assert app.cb_start_killswitch.state == "disabled"
    assert app.cb_start_dot.state == "disabled"


def test_apply_startup_settings_skips_general_network_mode_when_stealth_autostart_is_active(
    monkeypatch,
):
    app = App.__new__(App)
    actions = []

    app.settings = {
        "theme": "light",
        "auto_log_clear": False,
        "dns_guard_enabled": True,
        "start_security_monitoring": False,
        "start_network_mode": "vpn",
        "start_vpn_profile": "proton",
        "start_killswitch": True,
        "start_dot": False,
        "ufw_logging_default": "keep",
    }
    app.privacy_config = {"enabled": True, "autostart": True}
    app._preferred_theme_name = "light"
    app._normalize_start_network_mode = App._normalize_start_network_mode.__get__(
        app, App
    )
    app._stealth_startup_enabled = App._stealth_startup_enabled.__get__(app, App)
    app.apply_theme = lambda theme, log_change=False, persist=False: actions.append(
        ("theme", theme)
    )
    app.set_dns_guard_enabled = lambda enabled: actions.append(("dns_guard", enabled))
    app.security_start_monitoring = lambda: actions.append(("security_monitoring",))
    app.run_async = lambda func, job_name="": (
        actions.append(("run_async", job_name)) or func()
    )
    app.vpn_switch = lambda profile, ensure_sudo=True: actions.append(
        ("vpn", profile, ensure_sudo)
    )
    app.killswitch_on = lambda **kwargs: actions.append(("killswitch_on", kwargs))
    app.killswitch_off = lambda **kwargs: actions.append(("killswitch_off", kwargs))
    app.internet_disable = lambda interactive_guard=True: actions.append(
        ("offline", interactive_guard)
    )
    app.enable_dot_async = lambda: actions.append(("dot",))
    app.set_ufw_logging = lambda level: actions.append(("ufw_logging", level))
    app.log_safe = lambda message: actions.append(("log", message))
    app.after = lambda _delay, callback: callback()

    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)

    app.apply_startup_settings()

    assert not any(item[0] == "vpn" for item in actions)
    assert not any(item[0] == "killswitch_on" for item in actions)
    assert not any(item[0] == "killswitch_off" for item in actions)
    assert not any(item[0] == "offline" for item in actions)
    assert not any(item[0] == "log" for item in actions)


def test_apply_startup_settings_skips_dot_for_vpn(monkeypatch):
    app = App.__new__(App)
    actions = []

    app.settings = {
        "theme": "light",
        "auto_log_clear": False,
        "dns_guard_enabled": True,
        "start_security_monitoring": False,
        "start_network_mode": "vpn",
        "start_vpn_profile": "proton",
        "start_killswitch": False,
        "start_dot": True,
        "ufw_logging_default": "keep",
    }
    app._preferred_theme_name = "light"
    app.apply_theme = lambda theme, log_change=False, persist=False: actions.append(
        ("theme", theme, log_change, persist)
    )
    app.clear_log = lambda: actions.append(("clear_log",))
    app.set_dns_guard_enabled = lambda enabled: actions.append(("dns_guard", enabled))
    app.security_start_monitoring = lambda: actions.append(("security_monitoring",))
    app.run_async = lambda func, job_name="": (
        actions.append(("run_async", job_name)) or func()
    )
    app.vpn_switch = lambda profile, ensure_sudo=True: actions.append(
        ("vpn", profile, ensure_sudo)
    )
    app.killswitch_on = lambda **kwargs: actions.append(("killswitch_on", kwargs))
    app.killswitch_off = lambda **kwargs: actions.append(("killswitch_off", kwargs))
    app.enable_dot_async = lambda: actions.append(("dot",))
    app.set_ufw_logging = lambda level: actions.append(("ufw_logging", level))
    app.log_safe = lambda message: actions.append(("log", message))
    app.after = lambda _delay, callback: callback()

    monkeypatch.setattr(app_module, "check_sudo_nopasswd", lambda: True)

    app.apply_startup_settings()

    assert not any(item[0] == "vpn" for item in actions)
    assert ("dot",) not in actions
