import json
import inspect

from netmon.app import App
from netmon.features import chad_controller
from netmon.features import dns_controller
from netmon.features import dot_controller
from netmon.features import firewall_controller
from netmon.features import linux_help_controller
from netmon.features import security_audit_controller
from netmon.features import security_monitoring_controller
from netmon.services.lang_service import LangService
from netmon.ui.tabs.connections_tab import build_connections_tab
from netmon.ui.tabs.dns_tab import build_dns_tab
from netmon.ui.tabs.fun_tab import build_fun_tab
from netmon.ui.tabs.hdd_tab import build_hdd_tab
from netmon.ui.tabs.linux_help_tab import build_linux_help_tab
from netmon.ui.tabs.log_tab import build_log_tab
from netmon.ui.tabs.security_tabs import build_security_tabs, build_startup_guard_tab
from netmon.ui.tabs.tools_tabs import build_basic_tools_tabs


def test_lang_service_loads_existing_file(tmp_path):
    base_path = tmp_path / "lang"
    base_path.mkdir()
    with open(base_path / "de.json", "w", encoding="utf-8") as handle:
        json.dump({"tab_settings": "Einstellungen"}, handle)

    service = LangService(str(base_path))

    assert service.load("de") == {"tab_settings": "Einstellungen"}


def test_lang_service_returns_empty_dict_for_missing_file(tmp_path):
    service = LangService(str(tmp_path / "lang"))

    assert service.load("en") == {}


def test_tr_returns_translation_or_key_fallback():
    app = App.__new__(App)
    app.lang = {"tab_settings": "Settings"}

    assert app.tr("tab_settings") == "Settings"
    assert app.tr("missing_key") == "missing_key"
    assert app.tr("missing_key", "Default") == "Default"


def test_translate_tooltip_text_uses_source_mapping_and_falls_back():
    app = App.__new__(App)
    app.lang = {
        "tooltip_explicit": "Explicit tooltip",
        "tooltips": {
            "tooltip_auto_c32cd8817665": "Checks PATH entries and shell profiles for suspicious manipulation via key."
        },
        "tooltips_by_source": {
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen.": "Checks PATH entries and shell profiles for suspicious manipulation."
        },
    }

    assert app._translate_tooltip_text("tooltip_explicit") == "Explicit tooltip"
    assert (
        app._translate_tooltip_text(
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen."
        )
        == "Checks PATH entries and shell profiles for suspicious manipulation via key."
    )
    app.lang["tooltips"] = {}
    assert (
        app._translate_tooltip_text(
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen."
        )
        == "Checks PATH entries and shell profiles for suspicious manipulation."
    )
    assert app._translate_tooltip_text("tooltip_missing") == "tooltip_missing"


def test_tooltip_lang_key_is_stable():
    app = App.__new__(App)

    assert (
        app.tooltip_lang_key(
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen."
        )
        == "tooltip_auto_c32cd8817665"
    )


def test_main_tabs_and_security_sections_use_translation_keys():
    app_source = inspect.getsource(App)
    feature_source = "\n".join(
        [
            inspect.getsource(chad_controller),
            inspect.getsource(dns_controller),
            inspect.getsource(dot_controller),
            inspect.getsource(firewall_controller),
            inspect.getsource(linux_help_controller),
            inspect.getsource(security_audit_controller),
            inspect.getsource(security_monitoring_controller),
        ]
    )
    init_source = inspect.getsource(App.__init__)
    log_source = inspect.getsource(build_log_tab)
    connections_tab_source = inspect.getsource(build_connections_tab)
    dns_tab_source = inspect.getsource(build_dns_tab)
    tools_tab_source = inspect.getsource(build_basic_tools_tabs)
    linux_tab_source = inspect.getsource(build_linux_help_tab)
    fun_tab_source = inspect.getsource(build_fun_tab)
    security_tabs_source = inspect.getsource(build_security_tabs)
    hdd_tab_source = inspect.getsource(build_hdd_tab)
    startup_source = inspect.getsource(build_startup_guard_tab)
    chad_source = inspect.getsource(App.build_chad_analysis_tab)
    dnssec_source = inspect.getsource(App.run_dnssec_check)
    preflight_source = inspect.getsource(App.preflight_recheck)
    trace_source = inspect.getsource(App.trace_table_async)
    nmap_source = inspect.getsource(App.nmap_async)
    internet_off_source = inspect.getsource(App.internet_disable)

    assert 'app.nb.add(app.tab_log, text=app.tr("tab_log", "Log"))' in log_source
    assert "textvariable=app.dep_installer_button_var" in log_source
    assert (
        'app.nb.add(app.tab_conn, text=app.tr("tab_connections", "Verbindungen"))'
        in connections_tab_source
    )
    assert (
        'text=app.tr("connections_group_arp", "ARP Tabelle")' in connections_tab_source
    )
    assert (
        'value=app.tr("connections_arp_status_idle", "ARP: noch nicht geladen")'
        in connections_tab_source
    )
    assert (
        'text=app.tr("connections_group_route", "Routing Tabelle")'
        in connections_tab_source
    )
    assert (
        'value=app.tr("connections_route_status_idle", "Routing: noch nicht geladen")'
        in connections_tab_source
    )
    assert (
        'text=app.tr("dns_btn_refresh_status", "DNS Status aktualisieren")'
        in dns_tab_source
    )
    assert (
        'app.tools_nb.add(app.tab_mtr, text=app.tr("tools_tab_mtr", "MTR"))'
        in tools_tab_source
    )
    assert "nmap_output_frame = ttk.Frame(app.tab_nmap)" in tools_tab_source
    assert (
        'nmap_scroll_y = ttk.Scrollbar(nmap_output_frame, orient="vertical")'
        in tools_tab_source
    )
    assert "yscrollcommand=nmap_scroll_y.set," in tools_tab_source
    assert 'text=app.tr("tools_tab_theme_studio", "Theme Studio")' in tools_tab_source
    assert 'text=app.tr("tools_tab_fun", "Fun")' in fun_tab_source
    assert 'text=app.tr("tools_tab_linux", "Linux")' in linux_tab_source
    assert (
        'text=app.tr("privacy_check_enabled", "Stealthmodus aktiv")'
        in security_tabs_source
    )
    assert (
        'text=app.tr(\n            "privacy_check_strict",' not in security_tabs_source
    )
    assert 'text=self.tr("group_firewall", "Firewall")' in init_source
    assert 'text=app.tr("hdd_group_manage", "HDD Verwaltung")' in hdd_tab_source
    assert "app.hdd_info_auto_mount_check = ttk.Checkbutton(" in hdd_tab_source
    assert (
        'text=app.tr(\n            "hdd_check_auto_mount",\n            "Bei NetMon-Start automatisch mounten",\n        )'
        in hdd_tab_source
    )
    assert 'text=app.tr("security_group_actions", "Aktionen")' in security_tabs_source
    assert 'text=app.tr("path_guard_btn_check", "PATH prüfen")' in security_tabs_source
    assert (
        'text=self.tr(\n                "privacy_check_strict",'
        in inspect.getsource(App.build_settings_tab)
    )
    assert (
        'text=self.tr("settings_group_start_system", "Start & System")'
        in inspect.getsource(App.build_settings_tab)
    )
    assert (
        'text=app.tr("startup_guard_btn_baseline", "Baseline erstellen")'
        in startup_source
    )
    assert 'text=self.tr("chad_title", "Chad Analyse")' in chad_source
    assert 'text=self.tr("chad_check_enabled", "Chad-Anbindung aktiv")' in chad_source
    assert '"<Return>"' in chad_source
    assert (
        'text=self.tr("settings_group_chad_openai", "Chad Analyse / OpenAI")'
        in inspect.getsource(App.build_chad_settings_tab)
    )
    assert 'text="KI Status"' in inspect.getsource(App.build_chad_settings_tab)
    assert 'text="Analysemodus"' in inspect.getsource(App.build_chad_settings_tab)
    assert "VS Code-, Codex- und Docker-Hinweise minimieren" in inspect.getsource(
        App.build_chad_settings_tab
    )
    assert 'chat_input = app.__dict__.get("chad_chat_input")' in inspect.getsource(
        chad_controller.send_chad_chat_message
    )
    assert "chad_file_dialog_title" in feature_source
    assert "linux_help_confirm_send_title" in feature_source
    assert "dns_log_dnssec_started" in dnssec_source
    assert "startup_guard_status_check_running" in feature_source
    assert "security_log_filter_all" in feature_source
    assert "connections_status_copied" in app_source
    assert "firewall_confirm_enable_title" in feature_source
    assert "killswitch_confirm_enable_title" in feature_source
    assert "ssh_remove_confirm_title" in feature_source
    assert "preflight_log_started" in preflight_source
    assert "trace_log_enter_target" in trace_source
    assert "nmap_log_already_running" in nmap_source
    assert "dot_warning_blocked_title" in feature_source
    assert "internet_off_confirm_title" in internet_off_source
    assert "dns_warning_locked_title" in feature_source
    assert "dns_leak_repair_title" in app_source
    assert "dot_leak_fix_confirm_title" in app_source


def test_link_slot_and_vpn_slot_buttons_use_compact_per_button_size_override():
    init_source = inspect.getsource(App.__init__)

    assert 'style="LinkSlot.TButton"' in init_source
    assert "width=19," in init_source
    assert "padding=(8, 6)," in init_source
    assert "command=lambda i=idx: self.open_link_slot(i)," in init_source
    assert "command=lambda i=idx: self.open_vpn_slot(i)," in init_source


def test_mtr_summary_and_runtime_use_translation_keys():
    mtr_source = inspect.getsource(App.mtr_async)
    mtr_summary_source = inspect.getsource(App.summarize_mtr_output)

    assert "mtr_line_target" in mtr_source
    assert "mtr_assessment_running" in mtr_source
    assert "mtr_assessment_no_data" in mtr_source
    assert "mtr_status_no_issues" in mtr_summary_source
    assert "mtr_assessment_no_issues" in mtr_summary_source
    assert "mtr_note_average_latency" in mtr_summary_source


def test_nmap_summary_and_runtime_use_translation_keys():
    nmap_source = inspect.getsource(App.nmap_async)
    nmap_summary_source = inspect.getsource(App.summarize_nmap_output)

    assert "nmap_line_target" in nmap_source
    assert "nmap_assessment_running" in nmap_source
    assert "nmap_assessment_requires_root" in nmap_source
    assert "nmap_assessment_no_output" in nmap_summary_source
    assert "nmap_assessment_no_open_ports" in nmap_summary_source
    assert "nmap_note_filtered" in nmap_summary_source


def test_trace_iftop_and_htop_summaries_use_translation_keys():
    trace_source = inspect.getsource(App.trace_table_async)
    iftop_summary_source = inspect.getsource(App.summarize_iftop_output)
    htop_summary_source = inspect.getsource(App.summarize_htop_output)
    iftop_hint_source = inspect.getsource(App._iftop_timeout_hint)

    assert "trace_status_running" in trace_source
    assert "trace_assessment_running" in trace_source
    assert "iftop_line_status" in iftop_summary_source
    assert "iftop_assessment_activity" in iftop_summary_source
    assert "iftop_timeout_hint_general" in iftop_hint_source
    assert "htop_line_source" in htop_summary_source
    assert "htop_assessment_snapshot_available" in htop_summary_source
    assert "htop_line_top_cpu_process" in htop_summary_source


def test_firewall_transparency_uses_translation_keys():
    firewall_source = inspect.getsource(App._collect_firewall_transparency_snapshot)
    refresh_source = inspect.getsource(App.refresh_firewall_transparency_view)

    assert "firewall_transparency_active_rules" in firewall_source
    assert "firewall_transparency_no_rules_note" in firewall_source
    assert "firewall_tab_status_value" in refresh_source
    assert "firewall_tab_logging_menu_value" in refresh_source


def test_download_scan_and_chad_summary_use_translation_keys():
    download_scan_source = inspect.getsource(App._run_download_scan)
    chad_source = inspect.getsource(chad_controller.update_chad_summary_from_result)

    assert "download_scan_select_target_first" in download_scan_source
    assert "download_scan_report_findings_none" in download_scan_source
    assert "download_scan_result_report" in download_scan_source
    assert "chad_settings_summary_critical" in chad_source
    assert "chad_settings_summary_warnings_present" in chad_source
    assert "chad_analysis_label_default" in chad_source


def test_dns_and_dot_runtime_use_translation_keys():
    dns_source = inspect.getsource(dns_controller.apply_dns)
    vpn_dns_source = inspect.getsource(dns_controller.use_vpn_dns)
    dot_source = inspect.getsource(dot_controller._dot_status_text)
    dot_probe_source = inspect.getsource(dot_controller.dot_tls_probe)

    assert "dns_apply_cancelled_output" in dns_source
    assert "dns_apply_heading" in dns_source
    assert "dns_apply_action" in dns_source
    assert "dns_control_action_enforce_vpn_dns" in vpn_dns_source
    assert "dot_state_active_test_failed" in dot_source
    assert "dot_tls_probe_connection_failed" in dot_probe_source


def test_download_scan_workspace_and_systemcheck_use_translation_keys():
    update_text_source = inspect.getsource(App._update_download_scan_result_text)
    choose_file_source = inspect.getsource(App.choose_download_scan_file)
    disable_temp_source = inspect.getsource(App.disable_download_scan_temp_folder)
    missing_rkhunter_source = inspect.getsource(App._missing_rkhunter_for_chad_systemcheck_message)
    missing_clamav_source = inspect.getsource(App._missing_clamav_for_chad_systemcheck_message)

    assert "download_scan_result_text_default" in update_text_source
    assert "download_scan_import_failed" in choose_file_source
    assert "download_scan_result_selected_not_started" in choose_file_source
    assert "download_scan_result_prequarantine_disabled" in disable_temp_source
    assert "rkhunter_systemcheck_result_missing" in missing_rkhunter_source
    assert "clamav_systemcheck_result_missing" in missing_clamav_source


def test_language_files_contain_selected_ui_keys():
    with open("netmon/lang/de.json", "r", encoding="utf-8") as handle:
        de = json.load(handle)
    with open("netmon/lang/en.json", "r", encoding="utf-8") as handle:
        en = json.load(handle)

    for key in [
        "tab_connections",
        "btn_analyze_with_chad",
        "connections_group_arp",
        "connections_arp_status_idle",
        "connections_arp_status_count",
        "connections_arp_col_host",
        "connections_arp_col_ip",
        "connections_arp_col_mac",
        "connections_arp_col_iface",
        "connections_arp_col_type",
        "connections_group_route",
        "connections_route_status_idle",
        "connections_route_status_count",
        "connections_route_status_error",
        "connections_route_col_dst",
        "connections_route_col_gateway",
        "connections_route_col_iface",
        "connections_route_col_src",
        "connections_route_col_metric",
        "settings_group_start_system",
        "settings_start_network_label",
        "settings_start_network_isp",
        "settings_start_network_vpn",
        "settings_start_vpn_profile_label",
        "settings_start_activation_label",
        "settings_start_killswitch",
        "settings_start_security_monitoring",
        "settings_start_dot",
        "settings_start_ui_label",
        "settings_theme_label",
        "settings_auto_log_clear",
        "settings_start_security_label",
        "settings_ufw_logging_default_label",
        "dns_btn_refresh_status",
        "tools_tab_mtr",
        "tools_tab_theme_studio",
        "tools_tab_fun",
        "tools_tab_linux",
        "privacy_check_enabled",
        "group_firewall",
        "hdd_group_manage",
        "security_btn_export_logs",
        "path_guard_btn_check",
        "startup_guard_btn_baseline",
        "chad_btn_send",
        "chad_confirm_chat_title",
        "chad_status_file_imported",
        "chad_online_status_done",
        "linux_help_status_preparing",
        "linux_help_confirm_send_title",
        "dns_log_dnssec_started",
        "dns_log_leak_finished",
        "startup_guard_status_check_running",
        "startup_guard_log_check_done_counts",
        "security_log_filter_all",
        "security_log_export_failed",
        "connections_status_copied",
        "firewall_confirm_enable_title",
        "firewall_log_enabled",
        "vpn_log_started",
        "killswitch_confirm_enable_title",
        "killswitch_log_disabled",
        "ssh_remove_confirm_title",
        "preflight_log_started",
        "preflight_install_step_5",
        "trace_log_finished",
        "mtr_log_finished_rc",
        "mtr_line_target",
        "mtr_line_status",
        "mtr_line_assessment",
        "mtr_status_running",
        "mtr_status_no_data",
        "mtr_status_no_issues",
        "mtr_status_critical",
        "mtr_status_noticeable",
        "mtr_status_probably_harmless",
        "mtr_assessment_running",
        "mtr_assessment_no_data",
        "mtr_assessment_no_structure",
        "mtr_assessment_no_issues",
        "mtr_assessment_critical",
        "mtr_assessment_destination_loss",
        "mtr_assessment_route_break",
        "mtr_assessment_intermediate_loss",
        "mtr_note_target_loss_zero",
        "mtr_note_target_loss_value",
        "mtr_note_average_latency",
        "mtr_note_intermediate_full_loss",
        "mtr_note_icmp_filtering",
        "mtr_note_destination_loss_priority",
        "nmap_log_error_rc",
        "iftop_log_finished_rc",
        "htop_log_finished_rc",
        "dot_warning_blocked_title",
        "vpn_dns_enforce_confirm_title",
        "vpn_dns_enforce_status_cancelled",
        "internet_off_confirm_title",
        "internet_on_confirm_title",
        "networkmanager_missing_title",
        "internet_off_failed_title",
        "internet_on_failed_title",
        "dns_warning_locked_title",
        "dns_leak_repair_title",
        "dns_leak_repair_status_cancelled",
        "dot_leak_fix_confirm_title",
        "dot_leak_fix_status_cancelled",
        "radio_dependency_missing",
        "download_scan_select_target_first",
        "download_scan_report_findings_none",
        "download_scan_result_report",
        "chad_settings_summary_critical",
        "chad_settings_summary_warnings_present",
        "chad_analysis_label_default",
        "dns_control_action_enforce_vpn_dns",
        "dns_apply_cancelled_output",
        "dns_apply_heading",
        "dns_apply_action",
        "dot_state_active_test_failed",
        "dot_tls_probe_connection_failed",
        "download_scan_import_failed",
        "download_scan_result_selected_not_started",
        "download_scan_result_prequarantine_disabled",
        "rkhunter_systemcheck_result_missing",
        "clamav_systemcheck_result_missing",
    ]:
        assert key in de
        assert key in en
    assert "tooltips" in de
    assert "tooltip_auto_c32cd8817665" in de["tooltips"]
    assert "tooltip_auto_c32cd8817665" in en["tooltips"]


def test_language_files_have_matching_top_level_keys():
    with open("netmon/lang/de.json", "r", encoding="utf-8") as handle:
        de = json.load(handle)
    with open("netmon/lang/en.json", "r", encoding="utf-8") as handle:
        en = json.load(handle)

    assert sorted(set(de) - set(en)) == []
    assert sorted(set(en) - set(de)) == []


def test_german_repository_guard_and_lynis_strings_do_not_use_known_english_ui_labels():
    with open("netmon/lang/de.json", "r", encoding="utf-8") as handle:
        de = json.load(handle)

    assert de["lynis_btn_quick_scan"] == "Schnellaudit"
    assert de["lynis_btn_full_scan"] == "Vollständiger Sicherheitsscan (sudo)"
    assert de["settings_systemcheck_lynis"] == "Lynis Schnellaudit"
    assert de["repository_guard_btn_scan"] == "Repository-Scan"
    assert de["repository_guard_scan_unavailable"] == "Repository-Scan: Noch nicht verfügbar"
    assert de["repository_guard_findings_hint"] == "Bewertete Befunde erscheinen hier nach dem Scan."
    assert de["chad_status_repository_guard_findings_copied"] == "Repository-Guard-Befunde in Zwischenablage kopiert."
    assert de["dns_group_control"] == "DNS-Steuerung"
    assert de["dns_btn_health_check"] == "DNS-Health-Check"
    assert de["dns_btn_leak_check"] == "DNS-Leak-Check"
    assert de["dns_control_report_title"] == "=== DNS-Steuerung ==="
    assert de["dns_leak_repair_title"] == "DNS-Leak-Reparatur"
    assert de["theme_header_light"] == "Design: Hell"
    assert de["theme_studio_default_profile_name"] == "Mein Design"
    assert de["guided_tour_title_default"] == "NetMon-Tour"
    assert de["tour_def_dns_title"] == "NetMon DNS-Tour"
    assert de["tour_tab_title_dns"] == "NetMon DNS-Tab"
    assert de["tour_tab_title_packet_capture"] == "NetMon Packet-Capture-Tab"
    assert de["tour_tab_label_packet_capture"] == "Paketmitschnitt"
    assert de["tour_launcher_radio_tab"] == "Radio-Tab"
    assert de["tour_launcher_packet_capture"] == "Paketmitschnitt"
    assert de["tour_tab_lynis_quick_body"].startswith("Der Schnelllauf")
    assert de["dns_vpn_connected_skipped_no_sudo"].startswith("=== DNS-Steuerung ===")
    assert de["security_tab_firewall"] == "Firewall"
    assert de["security_tab_guards"] == "Devices"
    assert de["security_tab_path_guard"] == "Path"
    assert de["security_tab_startup_guard"] == "Autostart"
    assert de["security_tab_roots_baseline_guard"] == "Roots"
    assert de["security_tab_rkhunter"] == "Rootkithunter"
    assert de["security_tab_process_guard"] == "Prozesse"
    assert de["security_tab_repository_guard"] == "Repos"
    assert de["security_tab_packet_capture"] == "Capture"
