from types import SimpleNamespace

from netmon.ui.settings_sync import (
    app_var_value,
    sync_app_vars_from_mapping,
    update_backup_and_download_scan_settings_from_app,
    update_chad_settings_from_app,
    update_clamav_quickscan_settings_from_app,
    update_guided_tour_and_donation_settings_from_app,
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
