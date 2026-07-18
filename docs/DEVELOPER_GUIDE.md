# Entwicklerleitfaden NetMon

## Projektstruktur

### Tatsaechliche Verzeichnisstruktur

- Root-Dateien: `.codi-hints`, `.gitignore`, `AGENTS.md`, `Makefile`, `README.md`, `dev-lab-backup-2026-03-07.tar.gz`, `index.html`, `netmon_radio_app.py`, `pyproject.toml`, `requirements.txt`, `test_agent.txt`
- Laufzeit-Paket `netmon/` mit den Unterbereichen `config`, `core`, `features`, `lang`, `modules`, `services`, `ui`.
- Test-Suite unter `tests/`.
- Hilfswerkzeuge unter `tools/`.
- Shell-Skripte unter `scripts/`.
- Agent-/CLI-Code unter `agent/`.
- Bestehende Projektdokumente unter `docs/`.

### Einordnung der vom Auftrag geforderten Ordner

| Ordner | Im Repository gefunden? | Befund |
| --- | --- | --- |
| `src/` | Nein | Stattdessen liegt der eigentliche Code in `netmon/`. |
| `assets/` | Nein | Es gibt Bild-/JSON-Dateien in `tools/` und `netmon/config/`, aber kein Root-`assets/`. |
| `config/` | Teilweise | Vorhanden als Paket `netmon/config/`. |
| `logs/` | Nicht als Repo-Ordner | Laufzeitlogs werden im State-Verzeichnis unter `~/.local/state/netmon` angelegt. |
| `docs/` | Ja | Enthielt bereits projektspezifische Markdown-Dateien. |

## Hauptmodule

### Start- und Laufzeitpfad

- `netmon/__main__.py`: startet `netmon.main` via `run_module`.
- `netmon/main.py`: CLI-Argumente, Headless-Modi, `DISPLAY`-/`tkinter`-Checks, Splash, Instanz-Lock, Start-Error-Logging, `App`-Start.
- `netmon/app.py`: zentrale `App`-Klasse, GUI-Aufbau, Theme-System, Widget-Attribute, Delegation an Controller und Services.

### Paketuebersicht nach Codebasis

### Paket `netmon`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/__init__.py` | NetMon package. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/__main__.py` | Nicht dokumentiert. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/app.py` | Nicht dokumentiert. | Keine internen Imports erfasst | find_code_the_classics_zip, strip_ansi_codes, normalize_hex_color, hex_to_rgb, rgb_to_hex, blend_hex_colors, ideal_text_color, normalize_lynis_output, run_headless_snapshot, App.attach_local_mousewheel_binding, App.attach_all_local_mousewheel_bindings, App.on_close, App.report_callback_exception, App.select_theme, App.toggle_theme, App.apply_theme, App.make_light, App.set_light, App.on_light_click, App.show_firewall_menu | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/dark_test.py` | NetMon Darkmode Test Launcher (separate from stable main app). | Keine internen Imports erfasst | main | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/main.py` | NetMon startup entrypoint. | Keine internen Imports erfasst | get_startup_error_log_path, run_headless_smoke, main | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_network_service.py` | NetMon network/firewall/vpn command service layer. | Keine internen Imports erfasst | NetmonNetworkService.run, NetmonNetworkService.file_exists, NetmonNetworkService.wg_quick_up, NetmonNetworkService.wg_quick_down, NetmonNetworkService.ufw_enable_force, NetmonNetworkService.ufw_status, NetmonNetworkService.ufw_default, NetmonNetworkService.ufw_allow_on_iface, NetmonNetworkService.ufw_delete_allow_on_iface, NetmonNetworkService.ufw_allow_udp_endpoint, NetmonNetworkService.ufw_delete_allow_udp_endpoint | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_ops.py` | NetMon service helpers for operation coordination. | Keine internen Imports erfasst | NetworkOperationCoordinator.try_begin, NetworkOperationCoordinator.end, RollbackTransaction.add_rollback, RollbackTransaction.commit, RollbackTransaction.rollback | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_projectm_sidecar.py` | Optional external projectM sidecar integration for the standalone radio app. | Keine internen Imports erfasst | get_projectm_preset_dir, ensure_projectm_preset_dir, probe_projectm_package_candidates, build_projectm_install_command, get_projectm_sidecar_status, launch_projectm_sidecar, stop_projectm_sidecar, describe_projectm_sidecar_runtime | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_radio_app.py` | Standalone Tk app for NetMon Radio. | Keine internen Imports erfasst | main, NetMonRadioApp.tr, NetMonRadioApp.register_feature_button, NetMonRadioApp.attach_text_context_menu, NetMonRadioApp.refresh_radio_attach_state, NetMonRadioApp.attach_radio_to_netmon, NetMonRadioApp.detach_radio_from_netmon, NetMonRadioApp.log, NetMonRadioApp.log_safe, NetMonRadioApp.toggle_theme, NetMonRadioApp.apply_theme, NetMonRadioApp.apply_theme_palette, NetMonRadioApp.refresh_radio_station_logo, NetMonRadioApp.open_projectm_preset_folder, NetMonRadioApp.import_projectm_preset_files, NetMonRadioApp.refresh_radio_ui, NetMonRadioApp.update_radio_dependency_state, NetMonRadioApp.download_radio_db, NetMonRadioApp.radio_play, NetMonRadioApp.play_selected_radio_station | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_radio_core.py` | Helpers for launching and sharing state with the standalone NetMon Radio app. | Keine internen Imports erfasst | repo_root, radio_entrypoint_path, radio_wrapper_path, project_venv_python_executable, project_python_executable, radio_desktop_entry_dir, radio_desktop_entry_path, build_radio_paths, write_netmon_host_state, clear_netmon_host_state, read_netmon_host_state, read_radio_host_state, write_radio_launcher_state, write_radio_host_state, set_radio_mode, netmon_host_is_available, radio_host_is_running, standalone_radio_is_running, radio_transition_in_progress, begin_radio_transition | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_security_parser.py` | Security parser helpers for NetMon. | Keine internen Imports erfasst | NetmonSecurityParser.parse_ufw_block_line | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_security_store.py` | Security event store/analyzer helpers for NetMon. | Keine internen Imports erfasst | NetmonSecurityStore.filtered_events, NetmonSecurityStore.compute_stats, NetmonSecurityStore.detect_portscan | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/netmon_state_coordinator.py` | NetMon state coordination helpers. | Keine internen Imports erfasst | NetmonStateCoordinator.default_internet_suspend_state, NetmonStateCoordinator.normalize_internet_suspend_state, NetmonStateCoordinator.capture_internet_suspend_state, NetmonStateCoordinator.finalize_internet_restore_state, NetmonStateCoordinator.capture_stealth_runtime_state | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |

### Paket `netmon/config`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/config/__init__.py` | Configuration package for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/config/constants.py` | Pure constants shared across NetMon modules. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |

### Paket `netmon/core`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/core/__init__.py` | Core helpers for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/command.py` | Command helpers shared across NetMon modules. | Keine internen Imports erfasst | run_cmd, run_cmd_with_input, check_sudo_nopasswd, renew_sudo_timestamp | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/coordinator.py` | Compatibility wrapper for the NetMon state coordinator. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/crash.py` | Crash logging helpers for NetMon startup and runtime hooks. | netmon.config.constants | Keine oeffentlichen Namen erfasst | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/lock.py` | Single-instance lock helpers for NetMon. | Keine internen Imports erfasst | read_netmon_instance_lock_info, format_netmon_instance_lock_info, acquire_netmon_instance_lock, release_netmon_instance_lock | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/rkhunter_manager.py` | Nicht dokumentiert. | Keine internen Imports erfasst | is_rkhunter_installed, run_rkhunter_update, update_after_repair, detect_update_failure, backup_config, repair_config | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/state.py` | State and configuration path helpers for NetMon. | Keine internen Imports erfasst | get_netmon_config_dir, get_netmon_state_dir | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/tooling.py` | Tool discovery and small loader helpers for NetMon. | Keine internen Imports erfasst | has_cmd, get_cmd_path, get_user_pictures_dir, load_speedtest_module_from_file, check_speedtest_module_available | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |
| `netmon/core/utils.py` | Small pure utility helpers shared by the NetMon app. | Keine internen Imports erfasst | safe_write_json, format_table, ts, human_rate, human_size | Stellt generische Hilfsfunktionen für Kommandos, Pfade, Crash-Handling, Locking oder Formatierung bereit. |

### Paket `netmon/features`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/features/__init__.py` | Feature controllers for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/chad_controller.py` | Chad controller helpers for NetMon. | Keine internen Imports erfasst | log_chad_error, refresh_chad_runtime_status, mark_chad_status_event, update_chad_summary_from_result, ensure_chad_inline_prompt, get_chad_inline_input, clear_chad_inline_input, get_chad_transcript_text, guard_chad_inline_input, guard_chad_inline_delete, refresh_chad_output_view, append_to_chad_output, scroll_chad_output_to_top, scroll_chad_output_to_bottom, is_chad_enabled, ensure_chad_enabled, show_chad_activation_required_popup, update_chad_controls_state, filter_chad_analysis_input, build_chad_analysis_prompt | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/clamav_controller.py` | ClamAV controller helpers for NetMon. | Keine internen Imports erfasst | update_clamav_panel, update_clamav_panel_safe, clamav_findings_open, clamav_findings_quarantined, update_clamav_findings_buttons_state, update_clamav_findings_buttons_state_safe, clamav_is_excluded_root, clamav_system_targets, clamav_system_excluded_roots, clamav_count_files, clamav_select_items_dialog, set_clamav_abort_button_state, run_clamscan_with_progress, run_clamscan_with_cancel, write_clamav_output, format_runtime_hms, clamav_progress_apply, clamav_progress_tick, clamav_progress_start, clamav_progress_update_safe | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/dns_controller.py` | DNS controller helpers for NetMon. | Keine internen Imports erfasst | use_vpn_dns, normalize_dns_profile_choice, apply_dns_profile_choice_via_control, format_dns_profile_control_result, use_user_dns, enforce_dns_policy, refresh_dns_policy_status, evaluate_dns_policy, show_dns_policy_result, apply_dns | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/dot_controller.py` | DoT controller helpers for NetMon. | Keine internen Imports erfasst | set_dot_profile_choice_safe, update_dot_light, update_dot_light_safe, set_dot_state, set_dot_state_safe, dot_profile_config, build_dot_dropin_content, parse_dot_dropin, read_dot_dropin, is_vpn_dns_active, detect_netmon_dot_dropin_conflict, dot_leak_conflict_warning_text, infer_dot_profile_name, parse_dot_resolvectl_status, parse_dot_status_from_resolvectl, dot_preflight, dot_tls_probe, collect_dot_status, show_dot_status_result, startup_dot_status_check | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/firewall_controller.py` | Firewall controller helpers for NetMon. | Keine internen Imports erfasst | parse_ufw_action, extract_ip_port_proto_from_ufw_to, is_ufw_non_rule_line, parse_ufw_structured_rule, parse_ufw_numbered_rule, ip_sort_key, ufw_rule_sort_key, update_firewall_rule_remove_button_state, on_firewall_rule_select, format_ufw_rule_lines, format_ufw_status_grouped, get_killswitch_vpn_profiles, get_killswitch_vpn_endpoints, verify_killswitch_rules, killswitch_is_on, recover_firewall_after_killswitch_failure, killswitch_on_sync, killswitch_on, killswitch_off_sync, killswitch_off | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/fun_controller.py` | Fun tab launcher helpers for NetMon. | Keine internen Imports erfasst | module_available, discover_fun_games, update_fun_games_table, update_fun_dependency_state, refresh_fun_games, open_fun_games_folder, start_selected_game, stop_running_game | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/hdd_controller.py` | HDD controller helpers for NetMon. | Keine internen Imports erfasst | default_hdd_slots, load_hdd_slots_config, save_hdd_slots_config, save_hdd_config, hdd_slot_configured, hdd_find_device_by_uuid, hdd_resolve_slot_device, slot_for_device, refresh_hdd_table, slot_display_name, update_hdd_slot_button_labels, update_hdd_buttons, on_hdd_name_focus_in, on_hdd_name_focus_out, on_hdd_name_changed, set_hdd_name_from_model, on_hdd_table_select, assign_selected_disk_to_slot, clear_slot_assignment, hdd_sanitize_mapper_name | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/links_controller.py` | Links and desktop-app controller helpers for NetMon. | Keine internen Imports erfasst | desktop_exec_command, desktop_search_dirs, desktop_language_keys, parse_desktop_entry, load_desktop_app_entries, refresh_desktop_app_entries, default_link_slots, load_link_slots_config, save_link_slots_config, link_slot_configured, link_slot_display_name, update_link_slot_buttons, link_slot_summary, refresh_link_table, load_link_slot_into_form, on_link_slot_select, on_link_table_select, on_link_type_change, on_systemlink_app_select, sync_link_target_widgets | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/linux_help_controller.py` | Linux command database controller helpers for NetMon. | Keine internen Imports erfasst | set_linux_help_dirty, linux_help_csv_candidates, linux_help_csv_path, linux_help_slugify, linux_help_make_id, linux_help_get_risk_level, linux_help_requires_root, linux_help_tag_text, build_linux_help_chad_prompt, normalize_linux_help_entry, rebuild_linux_help_indexes, import_linux_help_csv, export_linux_help_csv, load_linux_help_data, save_linux_help_data, get_linux_help_categories, get_linux_help_commands_for_category, get_linux_help_command_by_id, sync_linux_help_form_categories, set_linux_help_form_from_entry | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/packet_capture_controller.py` | Packet capture controller helpers for NetMon. | Keine internen Imports erfasst | packet_capture_set_running_state, append_packet_capture_output, clear_packet_capture_output, packet_capture_generate_default_path, choose_packet_capture_file, refresh_packet_capture_interfaces, packet_capture_update_runtime, packet_capture_show_file_info, packet_capture_start_async, packet_capture_stop, open_packet_capture_in_wireshark, open_packet_capture_file_location | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/process_guard_controller.py` | Process Guard controller helpers for NetMon. | Keine internen Imports erfasst | format_process_guard_result, format_process_guard_details, set_process_guard_filter, update_process_guard_status_line, show_process_guard_trustlist, mark_selected_process_guard_trusted, remove_selected_process_guard_trusted, reset_process_guard_trustlist, refresh_process_guard_tree, on_process_guard_select, set_process_guard_light, run_process_guard_check, analyze_process_guard_with_chad, analyze_selected_process_guard_with_chad, apply_process_guard_monitoring_snapshot, start_process_guard_monitoring, stop_process_guard_monitoring | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/radio_controller.py` | Internetradio controller helpers for NetMon. | Keine internen Imports erfasst | default_radio_settings, normalize_station_entry, selected_radio_station_columns, legacy_load_radio_runtime, save_radio_stations, legacy_save_radio_favorites, save_radio_settings, build_radio_handover_payload, apply_radio_handover_payload, radio_available, set_radio_status, radio_eq_filter_spec, legacy_update_radio_header, legacy_refresh_radio_favorites_list, filtered_radio_stations, legacy_refresh_radio_station_table, legacy_refresh_radio_ui, update_radio_dependency_state, open_radio_tab, radio_recording_available | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/repository_guard_controller.py` | Repository Guard controller helpers for NetMon. | Keine internen Imports erfasst | run_repository_guard_scan, show_repository_guard_result, refresh_repository_guard_sources_tree, refresh_repository_guard_findings_tree, on_repository_guard_source_select, on_repository_guard_finding_select, format_repository_guard_result, format_repository_guard_source_details, format_repository_guard_finding_details, get_repository_guard_finding_recommendations, is_repository_guard_keyring_finding, is_repository_guard_review_finding, set_repository_guard_source_filter, set_repository_guard_finding_filter, copy_repository_guard_report, run_repository_guard_primary_action, copy_repository_guard_quick_action_snippet, copy_repository_guard_selected_uri, copy_repository_guard_selected_file_path, get_repository_guard_primary_action | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/roots_baseline_guard_controller.py` | Manual baseline helpers for the Roots Baseline Guard tab. | Keine internen Imports erfasst | roots_baseline_guard_supported_area_paths, refresh_roots_baseline_guard_root_mode_status, refresh_roots_baseline_guard_status, clear_roots_baseline_guard_view, read_roots_baseline_guard_current_state, create_roots_baseline_guard_baseline, check_roots_baseline_guard_baseline, update_roots_baseline_guard_baseline, show_last_roots_baseline_guard_comparison, on_roots_baseline_guard_result_select, on_roots_baseline_guard_whitelist_select, open_selected_roots_baseline_guard_whitelist_entry, selected_roots_baseline_guard_result_path, open_roots_baseline_guard_info_path, get_roots_baseline_guard_analysis_text, open_selected_roots_baseline_guard_parent_folder, load_roots_baseline_guard_demo_cases, analyze_roots_baseline_guard_with_chad, explain_selected_roots_baseline_guard_change, add_selected_roots_baseline_guard_change_to_whitelist | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/security_audit_controller.py` | Security audit controller helpers for NetMon. | Keine internen Imports erfasst | open_lynis_tab, clear_lynis_output, update_lynis_output, extract_lynis_issues_and_recommendations, show_lynis_issues_only, show_lynis_full_output, analyze_lynis_issues_with_chad, update_lynis_summary_from_output, set_lynis_buttons_state, finish_lynis_audit, lynis_scan_worker, start_lynis_scan, run_lynis_quick, run_lynis_full, lynis_audit_async, set_rkhunter_repair_available, open_rkhunter_tab, update_rkhunter_output, clear_rkhunter_output, update_rkhunter_summary_from_output | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/security_monitoring_controller.py` | Security monitoring controller helpers for NetMon. | Keine internen Imports erfasst | security_update_status, security_open_tab, prepare_security_chad_analysis, prepare_security_chad_curated_analysis, prepare_security_chad_technical_analysis, build_security_chad_curated_summary, build_security_chad_summary, read_ufw_log_tail, parse_ufw_block_line, detect_portscan, get_ufw_logging_level, security_query_log_level, refresh_security_log_level, security_filtered_events, security_compute_stats, security_update_stats_view, refresh_security_table, on_security_event_select, security_refresh_table_action, security_filter_portscan | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/speedtest_controller.py` | Speedtest controller helpers for NetMon. | Keine internen Imports erfasst | speedtest_logs_dir, speedtest_history_path, load_speedtest_history, persist_speedtest_history, append_speedtest_history, speedtest_warn_messages, update_speedtest_panel, show_speedtest_history, speedtest_async | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |
| `netmon/features/vpn_controller.py` | VPN controller helpers for NetMon. | Keine internen Imports erfasst | load_primary_vpn_slots_config, get_privacy_vpn_options, base_wg_profile_name, internal_ipv4_profile_candidates, internal_ipv4_profile_name, is_internal_ipv4_profile, privacy_vpn_label_profile_maps, update_privacy_vpn_combo, privacy_vpn_profile_from_value, privacy_vpn_label_for_profile, save_primary_vpn_slots_config, load_vpn_slots_config, save_vpn_slots_config, update_primary_vpn_buttons, update_primary_vpn_form_controls, refresh_vpn_slots_table, sync_primary_vpn_form_selection, open_primary_vpn_slot, save_primary_vpn_slot, load_vpn_slot_into_form | Liest Status, Widgets und Pfade vom `app`-Objekt, delegiert Detailarbeit an Services/Core-Helfer und schreibt Ergebnisse zurück in Variablen, Text-Widgets oder Dateien. |

### Paket `netmon/modules`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/modules/__init__.py` | NetMon modules package. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Verarbeitet Analyse- oder Parser-Eingaben und gibt strukturierte Ergebnisobjekte zurück. |
| `netmon/modules/port_analysis.py` | Port analysis helpers for detecting pseudo-open behavior. | Keine internen Imports erfasst | check_port_real_service | Verarbeitet Analyse- oder Parser-Eingaben und gibt strukturierte Ergebnisobjekte zurück. |
| `netmon/modules/speedtest.py` | Native speedtest helpers for NetMon. | Keine internen Imports erfasst | run_speedtest, format_speedtest_summary, format_speedtest_table | Verarbeitet Analyse- oder Parser-Eingaben und gibt strukturierte Ergebnisobjekte zurück. |

### Paket `netmon/services`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/services/__init__.py` | Service layer exports for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/ai_analysis_service.py` | Local prompt builder for optional NetMon analysis workflows. | Keine internen Imports erfasst | AiAnalysisService.sanitize_content, AiAnalysisService.build_prompt | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/ai_online_service.py` | Optional OpenAI API client for NetMon's Chad analysis tab. | Keine internen Imports erfasst | AiOnlineService.is_available, AiOnlineService.image_to_data_url, AiOnlineService.analyze, AiOnlineService.chat | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/dns_control_service.py` | Central DNS evaluation and repair helpers for NetMon. | Keine internen Imports erfasst | DNSControlService.read_resolvectl_status, DNSControlService.parse_active_dns_servers, DNSControlService.detect_vpn_active, DNSControlService.get_wireguard_interfaces, DNSControlService.normalize_dns_server, DNSControlService.detect_dnssec_mode, DNSControlService.dns_server_is_private_or_local, DNSControlService.is_vpn_dns_server, DNSControlService.parse_link_sections, DNSControlService.find_vpn_dns_servers, DNSControlService.dns_sources_for_sections, DNSControlService.is_physical_dns_candidate, DNSControlService.nm_active_connections_detailed, DNSControlService.active_nm_dns_targets, DNSControlService.filter_physical_nm_targets, DNSControlService.detect_netmon_dot_dropin_conflict, DNSControlService.evaluate_dns_policy, DNSControlService.build_dns_health_report, DNSControlService.build_dns_leak_check_result, DNSControlService.apply_nm_dns_policy_to_targets | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/lang_service.py` | Nicht dokumentiert. | Keine internen Imports erfasst | LangService.load | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/network_helpers.py` | Pure network helper functions used by the NetMon UI layer. | Keine internen Imports erfasst | is_local_or_lan_ip, is_safe_trace_target, is_safe_nmap_target, normalize_external_url_target, parse_traceroute_hops, format_traceroute_table, parse_cf_trace, parse_nmap_open_tcp_ports, parse_ss_lines | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/network_service.py` | Compatibility wrapper for the NetMon network service. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/path_guard_service.py` | Nicht dokumentiert. | Keine internen Imports erfasst | PathGuardService.get_current_path_entries, PathGuardService.get_shell_profile_paths, PathGuardService.analyze_path_entries, PathGuardService.analyze_shell_profiles, PathGuardService.run_check | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/process_guard_service.py` | Nicht dokumentiert. | Keine internen Imports erfasst | ProcessGuardService.is_available, ProcessGuardService.snapshot_processes, ProcessGuardService.process_signature, ProcessGuardService.trust_signature, ProcessGuardService.load_trustlist, ProcessGuardService.save_trustlist, ProcessGuardService.is_trusted, ProcessGuardService.mark_trusted, ProcessGuardService.remove_trusted, ProcessGuardService.reset_trustlist, ProcessGuardService.evaluate_process, ProcessGuardService.run_check, ProcessGuardService.detect_new_findings | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/rkhunter_analysis_service.py` | Deterministische Klassifizierung von RKHunter- und `dpkg -V`-Ausgaben. | Keine internen Imports erfasst | extract_replaced_script_paths, extract_warning_command_paths, analyze_rkhunter_output | Liefert kategorisierte Befunde, Gesamtrisiko und konservative Evidenz fuer das manuelle `rkhunter --propupd`-Gate; keine eigene GUI. |
| `netmon/services/repository_guard_service.py` | Nicht dokumentiert. | Keine internen Imports erfasst | RepositoryGuardService.scan, RepositoryGuardService.load_trustlist, RepositoryGuardService.save_trustlist, RepositoryGuardService.mark_host_trusted, RepositoryGuardService.remove_host_trusted, RepositoryGuardService.reset_trustlist, RepositoryGuardService.apply_trustlist, RepositoryGuardService.collect_sources, RepositoryGuardService.build_findings, RepositoryGuardService.build_summary, RepositoryGuardService.load_baseline, RepositoryGuardService.save_baseline, RepositoryGuardService.compare_to_baseline | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |
| `netmon/services/startup_guard_service.py` | Nicht dokumentiert. | Keine internen Imports erfasst | StartupGuardService.sha256_file, StartupGuardService.collect_entries, StartupGuardService.load_baseline, StartupGuardService.save_baseline, StartupGuardService.load_trustlist, StartupGuardService.save_trustlist, StartupGuardService.is_trusted, StartupGuardService.mark_trusted, StartupGuardService.remove_trusted, StartupGuardService.reset_trustlist, StartupGuardService.compare_to_baseline | Nimmt Eingabedaten bzw. Runner-Funktionen entgegen und liefert strukturierte Dict-/Tuple-Ergebnisse zurück; keine eigene GUI. |

### Paket `netmon/ui`

| Datei | Aufgabe | Interne Abhaengigkeiten | Oeffentliche Funktionen / Methoden | Datenfluss |
| --- | --- | --- | --- | --- |
| `netmon/ui/__init__.py` | UI package for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/ui/tabs/__init__.py` | Notebook tab builders for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/chad_settings_tab.py` | Chad settings tab builder for NetMon. | Keine internen Imports erfasst | build_chad_settings_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/chad_tab.py` | Chad tab builder for NetMon. | Keine internen Imports erfasst | build_chad_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/cleanup_assistant_tab.py` | Cleanup Assistant tab UI for NetMon. | Keine internen Imports erfasst | build_cleanup_assistant_tab, CleanupAssistantTab.apply_theme, CleanupAssistantTab.analyze_system, CleanupAssistantTab.analyze_module, CleanupAssistantTab.request_cleanup, CleanupAssistantTab.open_module_targets, CleanupAssistantTab.show_module_details, CleanupAssistantTab.analyze_user_cache, CleanupAssistantTab.analyze_thumbnail_cache, CleanupAssistantTab.analyze_apt_cache, CleanupAssistantTab.analyze_temporary_files, CleanupAssistantTab.analyze_log_files, CleanupAssistantTab.analyze_trash, CleanupAssistantTab.cleanup_user_cache, CleanupAssistantTab.cleanup_thumbnail_cache, CleanupAssistantTab.cleanup_apt_cache, CleanupAssistantTab.cleanup_temporary_files, CleanupAssistantTab.cleanup_log_files, CleanupAssistantTab.cleanup_trash | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/connections_tab.py` | Connections tab builder for NetMon. | Keine internen Imports erfasst | build_connections_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/dns_tab.py` | DNS tab builder for NetMon. | Keine internen Imports erfasst | build_dns_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/download_scan_tab.py` | Download scan tab builder for NetMon. | Keine internen Imports erfasst | build_download_scan_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/fun_tab.py` | Fun tab builder for NetMon. | Keine internen Imports erfasst | build_fun_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/hdd_tab.py` | HDD subtab builder for NetMon. | Keine internen Imports erfasst | build_hdd_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/links_tab.py` | Links subtab builder for NetMon. | Keine internen Imports erfasst | build_links_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/linux_help_tab.py` | Linux command database tab builder for NetMon. | Keine internen Imports erfasst | build_linux_help_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/log_tab.py` | Log tab builder for NetMon. | Keine internen Imports erfasst | build_log_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/radio_tab.py` | Radio tab launcher for NetMon. | Keine internen Imports erfasst | build_radio_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/security_tabs.py` | Security notebook tab builders for NetMon. | Keine internen Imports erfasst | build_startup_guard_tab, build_repository_guard_tab, build_roots_baseline_guard_tab, build_firewall_tab, build_security_tabs | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/settings_tab.py` | Settings tab builder for NetMon. | Keine internen Imports erfasst | build_settings_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/system_tab.py` | System subtab builder for NetMon. | Keine internen Imports erfasst | build_system_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/tools_tabs.py` | Tool notebook tab builders for NetMon. | Keine internen Imports erfasst | build_basic_tools_tabs | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/trace_tab.py` | Trace tab builder for NetMon. | Keine internen Imports erfasst | build_trace_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/tabs/vpn_slots_tab.py` | VPN slots subtab builder for NetMon. | Keine internen Imports erfasst | build_vpn_slots_tab | Erzeugt Tk-/ttk-Widgets, bindet sie an `app`-Attribute und delegiert Aktionen an Methoden des `App`-Objekts bzw. Controller. |
| `netmon/ui/widgets/__init__.py` | Reusable UI widgets for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/ui/widgets/lights.py` | Light indicator helpers for NetMon. | Keine internen Imports erfasst | make_light, set_light | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |
| `netmon/ui/widgets/tooltip.py` | Tooltip widget helpers for NetMon. | Keine internen Imports erfasst | Keine oeffentlichen Namen erfasst | Zentraler Anwendungs- oder Integrationspfad; verbindet GUI, Services, Controller und Laufzeitstatus. |


## Programmstart

1. `python -m netmon` landet in `netmon/__main__.py`.
2. `netmon/main.py` parst `--headless`, `--headless-smoke` und `--theme`.
3. Vor GUI-Start prueft der Code `tkinter` und `DISPLAY`.
4. Danach werden globale Crash-Hooks installiert und ein Instanz-Lock gesetzt.
5. Optional wird ein Start-Splash gezeigt.
6. Anschliessend wird `App(start_theme=...)` erstellt und `mainloop()` aufgerufen.

## Initialisierung in `App`

- Aufbau von Locks und Koordinatoren fuer Netzwerkoperationen.
- Instanziierung optionaler Services: Netzwerk, State Coordinator, Security Parser/Store, AI, Startup Guard, Path Guard, Process Guard, Repository Guard.
- Initialisierung zahlreicher `tk.StringVar`-/`BooleanVar`-Statusvariablen fuer DNS, DoT, Chad, Linux-Hilfe, Radio, Speedtest, Security usw.
- Ermittlung von Config- und State-Pfaden ueber `get_netmon_config_dir()` und `get_netmon_state_dir()`.
- Laden von Einstellungen und Initialisierung von Pfaden fuer Slots, Radio-Dateien, Security-Baselines, Trustlists, Captures und Logs.

## GUI-Aufbau

- Das Hauptnotebook `self.nb` entsteht in `netmon/app.py`.
- Darin liegen direkte Haupttabs wie `Log`, `Trace`, `Verbindungen`, `DNS`, `Chad`, `Download Scan`, `Settings` sowie die drei Sammelbereiche `System`, `Tools` und `Security`.
- `System`, `Tools` und `Security` enthalten jeweils ein eigenes `ttk.Notebook` (`system_nb`, `tools_nb`, `security_nb`).
- Die Untertabs werden ueber Builder in `netmon/ui/tabs/*.py` aufgebaut.

## Netzwerkpruefung

- Der allgemeine Command-Runner liegt in `netmon/core/command.py` (`run_cmd`, `run_cmd_with_input`, `renew_sudo_timestamp`).
- `netmon/netmon_network_service.py` kapselt `wg-quick`-, `ufw`- und Datei-Pruefkommandos.
- Netzwerk-Werkzeuge wie `MTR`, `Nmap`, `iftop`, `htop`, `Trace` und Verbindungen werden in eigenen Tab-/Controller-Pfaden aufgebaut.

## DNS-Pruefung

- `DNSControlService` in `netmon/services/dns_control_service.py` kapselt Resolver-Lesen, DNS-Parser, DNSSEC-/VPN-/Leak-Bewertung und Reparaturoperationen.
- `dns_controller.py` und die DNS-App-Methoden binden diese Bewertungen an Variablen, Buttons, Logging und DNS Guard.
- DoT-Profile und DNS-Providerkataloge liegen in `netmon/config/constants.py`.

## Logging

- Startfehler werden in `startup_error.log` im State-Verzeichnis geschrieben.
- Laufende App-Logs werden im Log-Tab angezeigt.
- Hilfsfunktionen wie `safe_write_json()` und mehrere Controller schreiben JSON-Dateien atomar oder defensiv in Config-/State-Pfade.
- Einzelne Bereiche fuehren eigene History-/Export-Dateien, z. B. Speedtest-History oder Radio-Handover-Dateien.

## Erweiterungen und Einbau neuer Elemente

### Neue Module erstellen

1. Fachlogik je nach Typ in `netmon/features/`, `netmon/services/`, `netmon/core/` oder `netmon/ui/tabs/` anlegen.
2. Falls das Modul GUI-Logik braucht, dem bestehenden Muster folgen: UI-Builder in `ui/tabs`, Aktionslogik in `features`, Hilfslogik in `services` oder `core`.
3. In `netmon/app.py` importieren und an geeigneter Stelle als Methode, Service oder Builder verdrahten.
4. Zuordnung zu Config-/State-Pfaden zentral in `App.__init__` vornehmen, wenn Dateien benoetigt werden.

### Neue Buttons integrieren

1. Ziel-Tab bzw. Ziel-Frame in `netmon/ui/tabs/*.py` oder in einem Builder in `app.py` bestimmen.
2. Button als `ttk.Button` anlegen und auf eine App-Methode oder Controller-Funktion verdrahten.
3. Falls der Button Statusvariablen braucht, die zugehoerigen `StringVar`/`BooleanVar` in `App.__init__` anlegen.
4. Fuer Lokalisierung bevorzugt `app.tr(key, fallback)` nutzen.

### Neue Tabs integrieren

1. Neues UI-Modul in `netmon/ui/tabs/` anlegen oder bestehenden Builder erweitern.
2. `app.tab_* = ttk.Frame(...)` und `*.add(...)` nach dem vorhandenen Muster definieren.
3. Den Builder in `netmon/app.py` importieren und beim Notebook-Aufbau aufrufen.
4. Optional Tooltip-/Navigationseintraege in `setup_all_tab_tooltips()` und Hilfsnavigation ergaenzen.

## Unklar / Nicht dokumentiert

- Es gibt kein separates `src/`-Verzeichnis; der Auftrag spricht dafuer, aber der Code lebt in `netmon/`.
- Nicht jeder Modulpfad dokumentiert seinen Datenfluss per Docstring; fuer viele Dateien ist der Datenfluss nur aus der Aufrufstruktur ersichtlich.
- Einige UI-Texte in `app.py` und `lang/*.json` sind noch Platzhalter oder konservative Vorbereitungstexte, obwohl Teile der Funktion bereits existieren.
