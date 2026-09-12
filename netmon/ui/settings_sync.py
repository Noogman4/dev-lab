"""Settings variable synchronization helpers."""

from __future__ import annotations


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
