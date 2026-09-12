"""Settings variable synchronization helpers."""

from __future__ import annotations

import time


def app_var_value(app, name: str, default):
    """Return a Tk variable value, falling back when the variable is absent or broken."""
    var = getattr(app, "__dict__", {}).get(name)
    if var is None:
        return default
    try:
        return var.get()
    except Exception:
        return default


def sync_app_vars_from_mapping(app, mapping: dict) -> None:
    """Apply values to existing Tk variables, ignoring absent or broken variables."""
    app_dict = getattr(app, "__dict__", {})
    for attr_name, value in mapping.items():
        var = app_dict.get(attr_name)
        if var is None:
            continue
        try:
            var.set(value)
        except Exception:
            pass


def _string_app_var_or_default(app, name: str, default) -> str:
    fallback = str(default() if callable(default) else default)
    return str(app_var_value(app, name, fallback) or fallback).strip() or fallback


def _lower_string_app_var_or_default(app, name: str, default: str) -> str:
    fallback = str(default or "").strip().lower()
    return (
        str(app_var_value(app, name, fallback) or fallback).strip().lower() or fallback
    )


def update_backup_and_download_scan_settings_from_app(app) -> None:
    """Copy backup and download-scan UI values into the settings payload."""
    settings = app.settings
    settings["download_scan_temp_dir"] = _string_app_var_or_default(
        app,
        "download_scan_temp_dir_var",
        app._default_download_scan_temp_dir,
    )
    settings["download_scan_target_dir"] = _string_app_var_or_default(
        app,
        "download_scan_target_dir_var",
        app._default_download_scan_target_dir,
    )
    settings["backup_data_target_dir"] = _string_app_var_or_default(
        app,
        "backup_target_dir_var",
        app._default_backup_data_target_dir,
    )

    for key, var_name in (
        ("backup_include_documents", "backup_include_documents_var"),
        ("backup_include_pictures", "backup_include_pictures_var"),
        ("backup_include_desktop", "backup_include_desktop_var"),
        ("backup_include_music", "backup_include_music_var"),
        ("backup_include_videos", "backup_include_videos_var"),
        ("backup_include_downloads", "backup_include_downloads_var"),
        ("backup_include_netmon_documents", "backup_include_netmon_documents_var"),
    ):
        settings[key] = bool(app_var_value(app, var_name, settings.get(key, True)))

    backup_netmon_dir_vars = getattr(app, "__dict__", {}).get("backup_netmon_dir_vars")
    backup_netmon_dir_vars = backup_netmon_dir_vars or {}
    settings["backup_netmon_full"] = bool(
        app_var_value(
            app,
            "backup_netmon_full_var",
            settings.get("backup_netmon_full", False),
        )
    )
    settings["backup_netmon_selected_dirs"] = [
        str(key)
        for key, var in sorted(backup_netmon_dir_vars.items())
        if bool(getattr(var, "get", lambda: False)())
    ]

    for key, var_name, default in (
        (
            "download_scan_prequarantine_startup",
            "download_scan_prequarantine_startup_var",
            False,
        ),
        ("download_scan_auto_move", "download_scan_auto_move_var", False),
        ("download_scan_ask_before_move", "download_scan_ask_before_move_var", True),
        ("download_scan_keep_original", "download_scan_keep_original_var", True),
        ("download_scan_save_report", "download_scan_save_report_var", True),
    ):
        settings[key] = bool(app_var_value(app, var_name, settings.get(key, default)))


def update_guided_tour_and_donation_settings_from_app(app) -> None:
    """Copy guided-tour and donation UI values into the settings payload."""
    settings = app.settings
    settings["guided_tour_offer_on_startup"] = bool(
        app_var_value(
            app,
            "var_guided_tour_offer_on_startup",
            settings.get("guided_tour_offer_on_startup", True),
        )
    )
    settings["guided_tour_startup_mode"] = (
        "full-tour"
        if bool(
            app_var_value(
                app,
                "var_guided_tour_full_on_startup",
                app._guided_tour_startup_mode() == "full-tour",
            )
        )
        else "quickstart"
    )
    settings["guided_tour_completed"] = app._guided_tour_completed_settings()

    donation_popup_requested = bool(
        app_var_value(
            app,
            "var_donation_popup_enabled",
            settings.get("donation_popup_enabled", True),
        )
    )
    if donation_popup_requested or app.donation_popup_disable_allowed():
        if not donation_popup_requested and bool(
            settings.get("donation_popup_enabled", True)
        ):
            settings["donation_popup_disabled_at"] = int(time.time())
        settings["donation_popup_enabled"] = donation_popup_requested
    else:
        settings["donation_popup_enabled"] = True


def update_clamav_quickscan_settings_from_app(app, clamav_controller) -> None:
    """Copy normalized ClamAV quickscan values into the settings payload."""
    app_dict = getattr(app, "__dict__", {})
    app.settings["clamav_quickscan_targets"] = (
        clamav_controller.clamav_normalize_quick_target_ids(
            app_dict.get("clamav_quickscan_target_ids", [])
        )
    )
    app.settings["clamav_quickscan_custom_paths"] = (
        clamav_controller.clamav_normalize_custom_quick_paths(
            app_dict.get("clamav_quickscan_custom_paths", [])
        )
    )


def update_security_tool_settings_from_app(app, speedtest_controller) -> None:
    """Copy security adjunct and speedtest values into the settings payload."""
    settings = app.settings
    settings["security_baseline_profile_id"] = (
        str(
            getattr(app, "__dict__", {}).get(
                "security_baseline_profile_id",
                settings.get(
                    "security_baseline_profile_id",
                    "zorin_desktop_development",
                ),
            )
            or "zorin_desktop_development"
        ).strip()
        or "zorin_desktop_development"
    )
    settings["security_game_mode_preset"] = app._normalize_game_mode_preset(
        app_var_value(
            app,
            "security_game_mode_preset_var",
            settings.get("security_game_mode_preset", "online"),
        )
    )
    settings["wireshark_launch_blocked"] = bool(
        app_var_value(
            app,
            "var_wireshark_launch_blocked",
            settings.get("wireshark_launch_blocked", False),
        )
    )
    settings["speedtest_server_id"] = (
        speedtest_controller.normalize_speedtest_server_id(
            app_var_value(
                app,
                "speedtest_server_id_var",
                settings.get("speedtest_server_id", ""),
            )
        )
    )


def update_systemcheck_settings_from_app(app) -> None:
    """Copy systemcheck selection flags into the settings payload."""
    settings = app.settings
    for key, var_name in (
        ("systemcheck_security_summary", "var_systemcheck_security_summary"),
        ("systemcheck_startup_guard", "var_systemcheck_startup_guard"),
        ("systemcheck_path_guard", "var_systemcheck_path_guard"),
        ("systemcheck_process_guard", "var_systemcheck_process_guard"),
        ("systemcheck_lynis", "var_systemcheck_lynis"),
        ("systemcheck_rkhunter", "var_systemcheck_rkhunter"),
        ("systemcheck_clamav", "var_systemcheck_clamav"),
    ):
        settings[key] = bool(app_var_value(app, var_name, settings.get(key, False)))


def update_theme_logging_settings_from_app(
    app,
    *,
    new_theme: str,
    normalize_hex_color,
) -> None:
    """Copy theme, tooltip, logging and protection values into settings."""
    settings = app.settings
    settings["theme"] = app._normalize_theme_name(new_theme)
    settings["theme_custom_accent"] = normalize_hex_color(
        app_var_value(
            app,
            "var_theme_studio_accent",
            settings.get("theme_custom_accent", ""),
        )
    )
    settings["theme_custom_panel_bg"] = normalize_hex_color(
        app_var_value(
            app,
            "var_theme_studio_panel",
            settings.get("theme_custom_panel_bg", ""),
        )
    )
    settings["theme_custom_style"] = _lower_string_app_var_or_default(
        app,
        "var_theme_studio_style",
        str(settings.get("theme_custom_style", "dezent") or "dezent"),
    )
    default_profile_name = app.tr("theme_studio_default_profile_name", "My Theme")
    settings["theme_custom_profile_name"] = (
        str(
            app_var_value(
                app,
                "var_theme_studio_profile_name",
                settings.get("theme_custom_profile_name", default_profile_name),
            )
        ).strip()
        or default_profile_name
    )
    for key, var_name, default in (
        ("tooltips_enabled", "tooltips_enabled", True),
        ("auto_log_clear", "var_auto_log_clear", False),
        ("debug_network_logging", "var_debug_network_logging", False),
        ("strict_protection", "strict_protection_var", True),
    ):
        settings[key] = bool(app_var_value(app, var_name, settings.get(key, default)))

    ufw_logging_default = _lower_string_app_var_or_default(
        app,
        "var_ufw_logging_default",
        str(settings.get("ufw_logging_default", "keep") or "keep"),
    )
    settings["ufw_logging_default"] = (
        ufw_logging_default
        if ufw_logging_default in {"keep", "off", "low", "high"}
        else "keep"
    )


def update_base_network_settings_from_app(app, *, new_language: str) -> None:
    """Copy language, startup guard, DNS and startup network values into settings."""
    settings = app.settings
    settings["language"] = new_language
    settings["startup_guard_autorun"] = bool(
        app_var_value(app, "var_startup_guard_autorun", True)
    )
    settings["process_guard_autorun"] = bool(
        app_var_value(
            app,
            "var_process_guard_autorun",
            settings.get("process_guard_autorun", True),
        )
    )
    settings["path_guard_autorun"] = bool(
        app_var_value(app, "var_path_guard_autorun", False)
    )
    settings["start_network_mode"] = "system"
    settings["start_vpn_profile"] = ""
    settings["dns_guard_enabled"] = bool(
        app_var_value(app, "var_dns_guard_enabled", True)
    )

    dnssec_mode = _lower_string_app_var_or_default(
        app,
        "var_dnssec_mode",
        str(settings.get("dnssec_mode", "standard") or "standard"),
    )
    settings["dnssec_mode"] = "strict" if dnssec_mode == "strict" else "standard"
    settings["isp_dns_fallback_profile"] = app._normalize_isp_dns_fallback_profile(
        app_var_value(
            app,
            "var_isp_dns_fallback_profile",
            settings.get("isp_dns_fallback_profile"),
        )
    )
    settings["start_killswitch"] = False
    settings["start_security_monitoring"] = bool(
        app_var_value(
            app,
            "var_start_security_monitoring",
            settings.get("start_security_monitoring", False),
        )
    )
    settings["start_dot"] = False


def update_chad_settings_from_app(app) -> None:
    """Copy Chad analysis UI values into the settings payload."""
    settings = app.settings
    for key, var_name, default in (
        ("chad_profile", "chad_profile_var", "custom"),
        ("chad_analysis_mode", "chad_analysis_mode_var", "standard"),
        ("chad_systemcheck_profile", "chad_systemcheck_profile_var", "custom"),
    ):
        settings[key] = _lower_string_app_var_or_default(app, var_name, default)

    for key, var_name in (
        ("chad_filter_relevant", "chad_filter_relevant_var"),
        ("chad_filter_critical", "chad_filter_critical_var"),
        ("chad_filter_recommendations", "chad_filter_recommendations_var"),
        ("chad_filter_beginner", "chad_filter_beginner_var"),
        ("chad_filter_rawdata", "chad_filter_rawdata_var"),
        ("chad_filter_technical", "chad_filter_technical_var"),
        ("chad_filter_hide_normal_services", "chad_filter_hide_normal_services_var"),
        (
            "chad_filter_ignore_harmless_processes",
            "chad_filter_ignore_harmless_processes_var",
        ),
        (
            "chad_filter_ignore_dev_environment",
            "chad_filter_ignore_dev_environment_var",
        ),
        ("chad_focus_security", "chad_focus_security_var"),
        ("chad_focus_dns", "chad_focus_dns_var"),
        ("chad_focus_network", "chad_focus_network_var"),
        ("chad_focus_process", "chad_focus_process_var"),
        ("chad_focus_firewall", "chad_focus_firewall_var"),
        ("chad_focus_performance", "chad_focus_performance_var"),
        ("chad_focus_optimization", "chad_focus_optimization_var"),
        ("chad_focus_rootkit", "chad_focus_rootkit_var"),
        ("chad_answer_short", "chad_answer_short_var"),
        ("chad_answer_detailed", "chad_answer_detailed_var"),
        ("chad_answer_step", "chad_answer_step_var"),
        ("chad_answer_linux_help", "chad_answer_linux_help_var"),
        ("chad_answer_risk", "chad_answer_risk_var"),
        ("chad_answer_recommendations", "chad_answer_recommendations_var"),
    ):
        settings[key] = bool(app_var_value(app, var_name, settings.get(key, False)))
