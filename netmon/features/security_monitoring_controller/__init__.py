"""Security monitoring controller package.

Imports all public functions from sub-modules for backward-compatible access:
    import netmon.features.security_monitoring_controller as smc
    smc.security_open_tab(app)
"""

from ._core import (
    build_security_chad_curated_summary, build_security_chad_summary, connected_device_inventory, current_input_access_inventory,
    detect_portscan, format_connected_device_inventory, get_ufw_logging_level, on_connected_device_select,
    on_security_event_select, parse_ufw_block_line, prepare_security_chad_analysis, prepare_security_chad_curated_analysis,
    prepare_security_chad_technical_analysis, read_ufw_log_tail, refresh_connected_device_table, refresh_input_access_table,
    refresh_security_table, security_clear_events, security_clear_views, security_compute_stats,
    security_filter_all, security_filter_external, security_filter_portscan, security_filter_relevant,
    security_filtered_events, security_integrity_ignore_path, security_open_tab, security_refresh_table_action,
    security_show_connected_devices, security_update_stats_view, security_update_status,
)
from ._scanning import (
    build_device_baseline, build_input_access_baseline, build_integrity_baseline, device_type_from_path,
    device_watch_paths, export_security_logs, hash_file_sha256, integrity_watch_files,
    load_security_baseline, sanitize_integrity_baseline, save_security_baseline, scan_device_changes,
    scan_input_access_changes, scan_input_access_state, scan_integrity_changes, security_build_baseline,
    security_create_device_event, security_create_file_event, security_create_input_access_event, security_export_dir,
    security_input_access_scan, security_input_access_whitelisted, security_poll_async, security_scan_now,
    security_start_monitoring, security_stop_monitoring,
)

__all__ = [
    build_device_baseline, build_input_access_baseline, build_integrity_baseline, build_security_chad_curated_summary,
    build_security_chad_summary, connected_device_inventory, current_input_access_inventory, detect_portscan,
    device_type_from_path, device_watch_paths, export_security_logs, format_connected_device_inventory,
    get_ufw_logging_level, hash_file_sha256, integrity_watch_files, load_security_baseline,
    on_connected_device_select, on_security_event_select, parse_ufw_block_line, prepare_security_chad_analysis,
    prepare_security_chad_curated_analysis, prepare_security_chad_technical_analysis, read_ufw_log_tail, refresh_connected_device_table,
    refresh_input_access_table, refresh_security_table, sanitize_integrity_baseline, save_security_baseline,
    scan_device_changes, scan_input_access_changes, scan_input_access_state, scan_integrity_changes,
    security_build_baseline, security_clear_events, security_clear_views, security_compute_stats,
    security_create_device_event, security_create_file_event, security_create_input_access_event, security_export_dir,
    security_filter_all, security_filter_external, security_filter_portscan, security_filter_relevant,
    security_filtered_events, security_input_access_scan, security_input_access_whitelisted, security_integrity_ignore_path,
    security_open_tab, security_poll_async, security_refresh_table_action, security_scan_now,
    security_show_connected_devices, security_start_monitoring, security_stop_monitoring, security_update_stats_view,
    security_update_status,
]
