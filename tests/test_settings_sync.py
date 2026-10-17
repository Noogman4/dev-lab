from types import SimpleNamespace

from netmon.ui.settings_sync import (
    app_var_value,
    sync_app_vars_from_mapping,
    update_backup_and_download_scan_settings_from_app,
    update_base_network_settings_from_app,
    update_chad_runtime_options_from_app,
    update_chad_settings_from_app,
    update_clamav_quickscan_settings_from_app,
    update_guided_tour_and_donation_settings_from_app,
    update_security_tool_settings_from_app,
    update_systemcheck_settings_from_app,
    update_theme_logging_settings_from_app,
)


class DummyVar:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class BrokenVar:
    def get(self):
        raise RuntimeError("cannot read")

    def set(self, _value):
        raise RuntimeError("cannot write")


def test_app_var_value_returns_default_for_missing_or_broken_vars():
    app = SimpleNamespace(present=DummyVar("configured"), broken=BrokenVar())

    assert app_var_value(app, "present", "fallback") == "configured"
    assert app_var_value(app, "missing", "fallback") == "fallback"
    assert app_var_value(app, "broken", "fallback") == "fallback"


def test_sync_app_vars_from_mapping_updates_existing_vars_only():
    app = SimpleNamespace(first=DummyVar("old"), broken=BrokenVar())

    sync_app_vars_from_mapping(
        app,
        {
            "first": "new",
            "missing": "ignored",
            "broken": "ignored",
        },
    )

    assert app.first.get() == "new"


def test_update_backup_and_download_scan_settings_from_app_uses_vars_and_defaults():
    app = SimpleNamespace(
        settings={
            "backup_include_documents": True,
            "backup_include_pictures": True,
            "backup_include_desktop": True,
            "backup_include_music": True,
            "backup_include_videos": True,
            "backup_include_downloads": True,
            "backup_include_netmon_documents": True,
            "backup_netmon_full": False,
            "download_scan_prequarantine_startup": False,
            "download_scan_auto_move": False,
            "download_scan_ask_before_move": True,
            "download_scan_keep_original": True,
            "download_scan_save_report": True,
        },
        download_scan_temp_dir_var=DummyVar("  /tmp/custom-prequarantine  "),
        download_scan_target_dir_var=DummyVar(""),
        backup_target_dir_var=DummyVar("  /backup/data  "),
        backup_include_documents_var=DummyVar(False),
        backup_include_pictures_var=DummyVar(True),
        backup_include_desktop_var=DummyVar(False),
        backup_include_music_var=DummyVar(True),
        backup_include_videos_var=DummyVar(False),
        backup_include_downloads_var=DummyVar(True),
        backup_include_netmon_documents_var=DummyVar(False),
        backup_netmon_full_var=DummyVar(True),
        backup_netmon_dir_vars={
            "logs": DummyVar(True),
            "cache": DummyVar(False),
            "config": DummyVar(True),
        },
        download_scan_prequarantine_startup_var=DummyVar(True),
        download_scan_auto_move_var=DummyVar(True),
        download_scan_ask_before_move_var=DummyVar(False),
        download_scan_keep_original_var=DummyVar(False),
        download_scan_save_report_var=DummyVar(True),
        _default_download_scan_temp_dir=lambda: "/tmp/default-prequarantine",
        _default_download_scan_target_dir=lambda: "/downloads/default",
        _default_backup_data_target_dir=lambda: "/backup/default",
    )

    update_backup_and_download_scan_settings_from_app(app)

    assert app.settings["download_scan_temp_dir"] == "/tmp/custom-prequarantine"
    assert app.settings["download_scan_target_dir"] == "/downloads/default"
    assert app.settings["backup_data_target_dir"] == "/backup/data"
    assert app.settings["backup_include_documents"] is False
    assert app.settings["backup_include_pictures"] is True
    assert app.settings["backup_include_desktop"] is False
    assert app.settings["backup_include_music"] is True
    assert app.settings["backup_include_videos"] is False
    assert app.settings["backup_include_downloads"] is True
    assert app.settings["backup_include_netmon_documents"] is False
    assert app.settings["backup_netmon_full"] is True
    assert app.settings["backup_netmon_selected_dirs"] == ["config", "logs"]
    assert app.settings["download_scan_prequarantine_startup"] is True
    assert app.settings["download_scan_auto_move"] is True
    assert app.settings["download_scan_ask_before_move"] is False
    assert app.settings["download_scan_keep_original"] is False
    assert app.settings["download_scan_save_report"] is True


def test_update_guided_tour_and_donation_settings_allows_disable(monkeypatch):
    app = SimpleNamespace(
        settings={
            "guided_tour_offer_on_startup": True,
            "guided_tour_startup_mode": "quickstart",
            "guided_tour_completed": {},
            "donation_popup_enabled": True,
            "donation_popup_disabled_at": 0,
        },
        var_guided_tour_offer_on_startup=DummyVar(False),
        var_guided_tour_full_on_startup=DummyVar(True),
        var_donation_popup_enabled=DummyVar(False),
        _guided_tour_startup_mode=lambda: "quickstart",
        _guided_tour_completed_settings=lambda: {"quickstart": True},
        donation_popup_disable_allowed=lambda: True,
    )
    monkeypatch.setattr("netmon.ui.settings_sync.time.time", lambda: 12345)

    update_guided_tour_and_donation_settings_from_app(app)

    assert app.settings["guided_tour_offer_on_startup"] is False
    assert app.settings["guided_tour_startup_mode"] == "full-tour"
    assert app.settings["guided_tour_completed"] == {"quickstart": True}
    assert app.settings["donation_popup_enabled"] is False
    assert app.settings["donation_popup_disabled_at"] == 12345


def test_update_guided_tour_and_donation_settings_blocks_early_disable():
    app = SimpleNamespace(
        settings={
            "guided_tour_offer_on_startup": True,
            "guided_tour_startup_mode": "full-tour",
            "guided_tour_completed": {"old": True},
            "donation_popup_enabled": True,
            "donation_popup_disabled_at": 0,
        },
        var_guided_tour_offer_on_startup=DummyVar(True),
        var_guided_tour_full_on_startup=DummyVar(False),
        var_donation_popup_enabled=DummyVar(False),
        _guided_tour_startup_mode=lambda: "full-tour",
        _guided_tour_completed_settings=lambda: {"dns": True},
        donation_popup_disable_allowed=lambda: False,
    )

    update_guided_tour_and_donation_settings_from_app(app)

    assert app.settings["guided_tour_offer_on_startup"] is True
    assert app.settings["guided_tour_startup_mode"] == "quickstart"
    assert app.settings["guided_tour_completed"] == {"dns": True}
    assert app.settings["donation_popup_enabled"] is True
    assert app.settings["donation_popup_disabled_at"] == 0


def test_update_clamav_quickscan_settings_from_app_uses_controller_normalizers():
    calls = []

    class DummyClamavController:
        @staticmethod
        def clamav_normalize_quick_target_ids(target_ids):
            calls.append(("targets", list(target_ids)))
            return ["downloads"]

        @staticmethod
        def clamav_normalize_custom_quick_paths(paths):
            calls.append(("paths", list(paths)))
            return ["/custom"]

    app = SimpleNamespace(
        settings={},
        clamav_quickscan_target_ids=["downloads", "unknown"],
        clamav_quickscan_custom_paths=[" /custom "],
    )

    update_clamav_quickscan_settings_from_app(app, DummyClamavController)

    assert app.settings["clamav_quickscan_targets"] == ["downloads"]
    assert app.settings["clamav_quickscan_custom_paths"] == ["/custom"]
    assert calls == [
        ("targets", ["downloads", "unknown"]),
        ("paths", [" /custom "]),
    ]


def test_update_chad_settings_from_app_copies_profile_filters_focus_and_answers():
    app = SimpleNamespace(
        settings={
            "chad_filter_relevant": True,
            "chad_filter_critical": False,
            "chad_filter_recommendations": True,
            "chad_filter_beginner": False,
            "chad_filter_rawdata": False,
            "chad_filter_technical": True,
            "chad_filter_hide_normal_services": True,
            "chad_filter_ignore_harmless_processes": True,
            "chad_filter_ignore_dev_environment": True,
            "chad_focus_security": True,
            "chad_focus_dns": True,
            "chad_focus_network": True,
            "chad_focus_process": True,
            "chad_focus_firewall": True,
            "chad_focus_performance": False,
            "chad_focus_optimization": False,
            "chad_focus_rootkit": False,
            "chad_answer_short": False,
            "chad_answer_detailed": True,
            "chad_answer_step": True,
            "chad_answer_linux_help": True,
            "chad_answer_risk": True,
            "chad_answer_recommendations": True,
        },
        chad_profile_var=DummyVar(" Security "),
        chad_analysis_mode_var=DummyVar(" Expert "),
        chad_systemcheck_profile_var=DummyVar(" Network "),
        chad_filter_relevant_var=DummyVar(False),
        chad_filter_critical_var=DummyVar(True),
        chad_filter_recommendations_var=DummyVar(False),
        chad_filter_beginner_var=DummyVar(True),
        chad_filter_rawdata_var=DummyVar(True),
        chad_filter_technical_var=DummyVar(False),
        chad_filter_hide_normal_services_var=DummyVar(False),
        chad_filter_ignore_harmless_processes_var=DummyVar(False),
        chad_filter_ignore_dev_environment_var=DummyVar(False),
        chad_focus_security_var=DummyVar(False),
        chad_focus_dns_var=DummyVar(False),
        chad_focus_network_var=DummyVar(False),
        chad_focus_process_var=DummyVar(False),
        chad_focus_firewall_var=DummyVar(False),
        chad_focus_performance_var=DummyVar(True),
        chad_focus_optimization_var=DummyVar(True),
        chad_focus_rootkit_var=DummyVar(True),
        chad_answer_short_var=DummyVar(True),
        chad_answer_detailed_var=DummyVar(False),
        chad_answer_step_var=DummyVar(False),
        chad_answer_linux_help_var=DummyVar(False),
        chad_answer_risk_var=DummyVar(False),
        chad_answer_recommendations_var=DummyVar(False),
    )

    update_chad_settings_from_app(app)

    assert app.settings["chad_profile"] == "security"
    assert app.settings["chad_analysis_mode"] == "expert"
    assert app.settings["chad_systemcheck_profile"] == "network"
    assert app.settings["chad_filter_relevant"] is False
    assert app.settings["chad_filter_critical"] is True
    assert app.settings["chad_filter_recommendations"] is False
    assert app.settings["chad_filter_beginner"] is True
    assert app.settings["chad_filter_rawdata"] is True
    assert app.settings["chad_filter_technical"] is False
    assert app.settings["chad_filter_hide_normal_services"] is False
    assert app.settings["chad_filter_ignore_harmless_processes"] is False
    assert app.settings["chad_filter_ignore_dev_environment"] is False
    assert app.settings["chad_focus_security"] is False
    assert app.settings["chad_focus_dns"] is False
    assert app.settings["chad_focus_network"] is False
    assert app.settings["chad_focus_process"] is False
    assert app.settings["chad_focus_firewall"] is False
    assert app.settings["chad_focus_performance"] is True
    assert app.settings["chad_focus_optimization"] is True
    assert app.settings["chad_focus_rootkit"] is True
    assert app.settings["chad_answer_short"] is True
    assert app.settings["chad_answer_detailed"] is False
    assert app.settings["chad_answer_step"] is False
    assert app.settings["chad_answer_linux_help"] is False
    assert app.settings["chad_answer_risk"] is False
    assert app.settings["chad_answer_recommendations"] is False


def test_update_chad_runtime_options_from_app_copies_model_and_popup_flags():
    app = SimpleNamespace(
        settings={
            "auto_switch_to_chad": True,
            "chad_preview_popup": False,
            "chad_model": "old-model",
        },
        var_auto_switch_to_chad=DummyVar(False),
        var_chad_preview_popup=DummyVar(True),
        chad_model_var=DummyVar(" gpt-4.1 "),
    )

    update_chad_runtime_options_from_app(app)

    assert app.settings["auto_switch_to_chad"] is False
    assert app.settings["chad_preview_popup"] is True
    assert app.settings["chad_model"] == "gpt-4.1"


def test_update_security_tool_settings_from_app_normalizes_fields():
    calls = []

    class DummySpeedtestController:
        @staticmethod
        def normalize_speedtest_server_id(value):
            calls.append(("speedtest", value))
            return "44081"

    app = SimpleNamespace(
        settings={
            "security_baseline_profile_id": "zorin_desktop_development",
            "security_game_mode_preset": "online",
            "wireshark_launch_blocked": False,
            "speedtest_server_id": "",
        },
        security_baseline_profile_id="  desktop_safe_v1  ",
        security_game_mode_preset_var=DummyVar(" Steam "),
        var_wireshark_launch_blocked=DummyVar(True),
        speedtest_server_id_var=DummyVar("ID 44081"),
        _normalize_game_mode_preset=lambda value: str(value).strip().lower(),
    )

    update_security_tool_settings_from_app(app, DummySpeedtestController)

    assert app.settings["security_baseline_profile_id"] == "desktop_safe_v1"
    assert app.settings["security_game_mode_preset"] == "steam"
    assert app.settings["wireshark_launch_blocked"] is True
    assert app.settings["speedtest_server_id"] == "44081"
    assert calls == [("speedtest", "ID 44081")]


def test_update_systemcheck_settings_from_app_copies_flags():
    app = SimpleNamespace(
        settings={
            "systemcheck_security_summary": True,
            "systemcheck_startup_guard": True,
            "systemcheck_path_guard": True,
            "systemcheck_process_guard": True,
            "systemcheck_lynis": True,
            "systemcheck_rkhunter": False,
            "systemcheck_clamav": False,
        },
        var_systemcheck_security_summary=DummyVar(False),
        var_systemcheck_startup_guard=DummyVar(True),
        var_systemcheck_path_guard=DummyVar(False),
        var_systemcheck_process_guard=DummyVar(True),
        var_systemcheck_lynis=DummyVar(False),
        var_systemcheck_rkhunter=DummyVar(True),
        var_systemcheck_clamav=DummyVar(True),
    )

    update_systemcheck_settings_from_app(app)

    assert app.settings["systemcheck_security_summary"] is False
    assert app.settings["systemcheck_startup_guard"] is True
    assert app.settings["systemcheck_path_guard"] is False
    assert app.settings["systemcheck_process_guard"] is True
    assert app.settings["systemcheck_lynis"] is False
    assert app.settings["systemcheck_rkhunter"] is True
    assert app.settings["systemcheck_clamav"] is True


def test_update_theme_logging_settings_from_app_normalizes_values():
    app = SimpleNamespace(
        settings={
            "theme": "dark",
            "theme_custom_accent": "",
            "theme_custom_panel_bg": "",
            "theme_custom_style": "dezent",
            "theme_custom_profile_name": "Old",
            "tooltips_enabled": True,
            "auto_log_clear": False,
            "debug_network_logging": False,
            "strict_protection": True,
            "ufw_logging_default": "keep",
        },
        var_theme_studio_accent=DummyVar("FF3366"),
        var_theme_studio_panel=DummyVar("#FFF1F6"),
        var_theme_studio_style=DummyVar(" KRAEFTIG "),
        var_theme_studio_profile_name=DummyVar("  Pop Theme  "),
        tooltips_enabled=DummyVar(False),
        var_auto_log_clear=DummyVar(True),
        var_debug_network_logging=DummyVar(True),
        strict_protection_var=DummyVar(False),
        var_ufw_logging_default=DummyVar("medium"),
        _normalize_theme_name=lambda value: str(value).strip().lower(),
        tr=lambda _key, default=None: default,
    )

    def normalize_hex_color(value):
        text = str(value or "").strip()
        if not text:
            return ""
        if not text.startswith("#"):
            text = f"#{text}"
        return text.lower() if len(text) == 7 else ""

    update_theme_logging_settings_from_app(
        app,
        new_theme=" Pop ",
        normalize_hex_color=normalize_hex_color,
    )

    assert app.settings["theme"] == "pop"
    assert app.settings["theme_custom_accent"] == "#ff3366"
    assert app.settings["theme_custom_panel_bg"] == "#fff1f6"
    assert app.settings["theme_custom_style"] == "kraeftig"
    assert app.settings["theme_custom_profile_name"] == "Pop Theme"
    assert app.settings["tooltips_enabled"] is False
    assert app.settings["auto_log_clear"] is True
    assert app.settings["debug_network_logging"] is True
    assert app.settings["strict_protection"] is False
    assert app.settings["ufw_logging_default"] == "keep"


def test_update_base_network_settings_from_app_normalizes_startup_and_dns():
    app = SimpleNamespace(
        settings={
            "language": "de",
            "process_guard_autorun": False,
            "dnssec_mode": "standard",
            "isp_dns_fallback_profile": "Cloudflare (1.1.1.1)",
            "start_security_monitoring": False,
        },
        var_startup_guard_autorun=DummyVar(False),
        var_process_guard_autorun=DummyVar(True),
        var_path_guard_autorun=DummyVar(True),
        var_dns_guard_enabled=DummyVar(False),
        var_dnssec_mode=DummyVar(" STRICT "),
        var_isp_dns_fallback_profile=DummyVar(" Quad9 "),
        var_start_security_monitoring=DummyVar(True),
        _normalize_isp_dns_fallback_profile=lambda value: str(value).strip().lower(),
    )

    update_base_network_settings_from_app(app, new_language="en")

    assert app.settings["language"] == "en"
    assert app.settings["startup_guard_autorun"] is False
    assert app.settings["process_guard_autorun"] is True
    assert app.settings["path_guard_autorun"] is True
    assert app.settings["start_network_mode"] == "system"
    assert app.settings["start_vpn_profile"] == ""
    assert app.settings["dns_guard_enabled"] is False
    assert app.settings["dnssec_mode"] == "strict"
    assert app.settings["isp_dns_fallback_profile"] == "quad9"
    assert app.settings["start_killswitch"] is False
    assert app.settings["start_security_monitoring"] is True
    assert app.settings["start_dot"] is False
