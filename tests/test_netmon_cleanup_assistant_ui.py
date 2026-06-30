import inspect
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from netmon.app import App
from netmon.ui.tabs.cleanup_assistant_tab import (
    CleanupAssistantTab,
    build_cleanup_assistant_tab,
)


def test_cleanup_assistant_tab_builder_source_is_present():
    source = inspect.getsource(build_cleanup_assistant_tab)
    class_source = inspect.getsource(CleanupAssistantTab)

    assert "return CleanupAssistantTab(app)" in source
    assert (
        'text=app.tr("tools_tab_cleanup_assistant", "Cleanup Assistant")'
        in class_source
    )
    assert '"Benutzer-Cache"' in class_source
    assert '"Thumbnail-Cache"' in class_source
    assert '"APT-Cache"' in class_source
    assert '"Temporare Dateien"' in class_source
    assert '"Log-Dateien pruefen"' in class_source
    assert '"Papierkorb pruefen"' in class_source
    assert 'text="System analysieren"' in class_source
    assert 'text="Analysieren"' in class_source
    assert 'text="Details"' in class_source
    assert 'text="Oeffnen"' in class_source
    assert 'text="Bereinigen"' in class_source
    assert 'value="Letzte Aktion: Noch keine"' in class_source
    assert 'text="Vorbereitung bestaetigen"' in class_source
    assert 'text="Risikostufen"' in class_source
    assert 'text="Sicherheitsregeln"' in class_source
    assert "self.subtabs = ttk.Notebook(self.workspace)" in class_source
    assert 'self.subtabs.add(self.overview_tab, text="Uebersicht")' in class_source
    assert 'self.subtabs.add(self.modules_tab, text="Module")' in class_source
    assert 'self.subtabs.add(self.protocol_tab, text="Protokoll")' in class_source
    assert "text=title" in class_source
    assert "cards.columnconfigure(0, weight=1)" in class_source
    assert "self.protocol_text = tk.Text(" in class_source
    assert 'state="disabled"' in class_source
    assert "def analyze_system(self):" in class_source
    assert "def cleanup_apt_cache(self):" in class_source


def test_cleanup_assistant_tab_is_wired_into_app_source():
    app_source = inspect.getsource(App)

    assert "build_cleanup_assistant_tab(self)" in app_source
    assert '"cleanup_assistant_log_text"' in app_source
    assert '"cleanup_assistant_active_subtab": "overview"' in app_source
    assert '"cleanup_assistant_last_cleanup_run": None' in app_source
    assert '"cleanup_assistant_cleanup_history": []' in app_source
    assert 'getattr(self, "tab_cleanup_assistant", None)' in app_source
    assert 'cleanup_ui = self.__dict__.get("cleanup_assistant_tab_ui")' in app_source


def test_cleanup_scan_path_size_counts_files_and_dirs():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "a.txt").write_text("abc", encoding="utf-8")
        (base / "nested").mkdir()
        (base / "nested" / "b.bin").write_bytes(b"12345")

        result = tab._scan_path_size(base)

    assert result["exists"] is True
    assert result["file_count"] == 2
    assert result["dir_count"] >= 1
    assert result["size_bytes"] == 8


def test_cleanup_refresh_storage_summary_sums_safe_and_caution_modules():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {
        "user_cache": {"size_bytes": 1024},
        "apt_cache": {"size_bytes": 2048},
    }

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.storage_value_vars = {
        "potential": DummyVar(),
        "safe": DummyVar(),
        "review": DummyVar(),
    }

    tab._refresh_storage_summary()

    assert tab.storage_value_vars["potential"].value == "3.0 KiB"
    assert tab.storage_value_vars["safe"].value == "1.0 KiB"
    assert "APT-Cache" in tab.storage_value_vars["review"].value


def test_cleanup_risk_label_marks_logs_with_large_findings_as_caution():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    module = next(
        item for item in CleanupAssistantTab.MODULES if item.module_id == "log_files"
    )

    label = tab._risk_label_for_result(
        module,
        {
            "size_bytes": 1024,
            "inaccessible": 0,
            "large_logs": [(25 * 1024 * 1024, "/var/log/big.log")],
        },
    )

    assert label == "Warnstufe: Vorsicht"


def test_cleanup_module_mode_summary_marks_user_cache_mixed_mode():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    module = next(
        item for item in CleanupAssistantTab.MODULES if item.module_id == "user_cache"
    )

    label = tab._module_mode_summary(
        module,
        {
            "cache_candidates": [
                {"path": "/home/test/.cache/pip", "safe": True},
                {"path": "/home/test/.cache/chromium", "safe": False},
            ]
        },
    )

    assert label == "Modus: Sicher + Vorsicht, einzelne Cache-Bereiche"


def test_cleanup_candidate_risk_tag_marks_review_only_items():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    assert tab._candidate_risk_tag({"safe": False}) == "Nur pruefen"
    assert (
        tab._candidate_risk_tag(
            {"safe": False, "action": "run_sudo_command", "command": ["apt", "clean"]}
        )
        == "Vorsicht"
    )


def test_cleanup_set_module_action_feedback_updates_label():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.module_action_vars = {"user_cache": DummyVar()}

    tab._set_module_action_feedback("user_cache", "Analyse abgeschlossen: 1.0 MiB")

    assert tab.module_action_vars["user_cache"].value.startswith(
        "Letzte Aktion: Analyse abgeschlossen: 1.0 MiB ("
    )


def test_cleanup_inspection_targets_for_user_cache_prefer_unsafe_candidates():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "user_cache": {
            "existing_paths": ["/home/test/.cache"],
            "cache_candidates": [
                {"path": "/home/test/.cache/pip", "safe": True},
                {"path": "/home/test/.cache/chromium", "safe": False},
            ],
        }
    }

    targets = tab._inspection_targets_for_module("user_cache")

    assert targets == [
        {
            "label": "Cache pruefen: chromium",
            "path": "/home/test/.cache/chromium",
        }
    ]


def test_cleanup_inspection_targets_for_logs_include_var_log():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "log_files": {
            "existing_paths": ["/var/log"],
            "large_logs": [(25 * 1024 * 1024, "/var/log/big.log")],
        }
    }

    targets = tab._inspection_targets_for_module("log_files")

    assert targets[0]["path"] == "/var/log"
    assert any(item["path"] == "/var/log" for item in targets)


def test_cleanup_selected_subtab_key_reports_modules_tab():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    class DummyNotebook:
        def select(self):
            return ".modules"

    tab.subtabs = DummyNotebook()
    tab.overview_tab = ".overview"
    tab.modules_tab = ".modules"
    tab.protocol_tab = ".protocol"

    assert tab._selected_subtab_key() == "modules"


def test_cleanup_on_subtab_changed_updates_settings_and_persists():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    saved = []

    class DummyApp:
        def __init__(self):
            self.settings = {}

        def save_settings(self, log_success=False):
            saved.append(log_success)

    tab.app = DummyApp()
    tab._selected_subtab_key = lambda: "protocol"

    tab._on_subtab_changed()

    assert tab.app.settings["cleanup_assistant_active_subtab"] == "protocol"
    assert saved == [False]


def test_cleanup_settings_helpers_return_safe_defaults():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.app = type("DummyApp", (), {"settings": "invalid"})()

    assert tab._settings_dict() == {}
    assert tab._settings_store() is None


def test_cleanup_save_settings_safe_uses_log_success_false():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    saved = []

    class DummyApp:
        def save_settings(self, log_success=False):
            saved.append(log_success)

    tab.app = DummyApp()

    assert tab._save_settings_safe() is True
    assert saved == [False]


def test_cleanup_record_history_updates_vars_and_persists():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    persisted = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class DummyText:
        def __init__(self):
            self.value = ""

        def configure(self, **_kwargs):
            return None

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, text):
            self.value = text

    class DummyApp:
        def __init__(self):
            self.settings = {}

        def save_settings(self, log_success=False):
            persisted.append(log_success)

    tab.app = DummyApp()
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.cleanup_history = []
    tab.last_cleanup_var = DummyVar()
    tab.history_summary_var = DummyVar()
    tab.history_text = DummyText()

    tab._record_cleanup_history("trash", "1 Pfad/Pfade, 2.0 MiB freigegeben")

    assert len(tab.cleanup_history) == 1
    assert "Papierkorb pruefen" in tab.last_cleanup_var.value
    assert "1 erfolgreiche Cleanup-Lauf/Laeufe" in tab.history_summary_var.value
    assert "Papierkorb pruefen" in tab.history_text.value
    assert (
        tab.app.settings["cleanup_assistant_last_cleanup_run"]["module_id"] == "trash"
    )
    assert len(tab.app.settings["cleanup_assistant_cleanup_history"]) == 1
    assert persisted == [False]


def test_cleanup_restore_history_falls_back_to_last_saved_entry():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class DummyText:
        def __init__(self):
            self.value = ""

        def configure(self, **_kwargs):
            return None

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, text):
            self.value = text

    class DummyApp:
        def __init__(self):
            self.settings = {
                "cleanup_assistant_last_cleanup_run": {
                    "timestamp": "2026-06-05 08:15:00",
                    "module_id": "trash",
                    "module_title": "Papierkorb pruefen",
                    "summary": "2 Pfad/Pfade, 10 MiB freigegeben",
                }
            }

    tab.app = DummyApp()
    tab.CLEANUP_HISTORY_LIMIT = CleanupAssistantTab.CLEANUP_HISTORY_LIMIT
    tab.CLEANUP_HISTORY_SETTINGS_KEY = CleanupAssistantTab.CLEANUP_HISTORY_SETTINGS_KEY
    tab.LAST_CLEANUP_SETTINGS_KEY = CleanupAssistantTab.LAST_CLEANUP_SETTINGS_KEY
    tab.cleanup_history = []
    tab.last_cleanup_var = DummyVar()
    tab.history_summary_var = DummyVar()
    tab.history_text = DummyText()

    tab._restore_cleanup_history()

    assert len(tab.cleanup_history) == 1
    assert tab.cleanup_history[0]["module_id"] == "trash"
    assert "Papierkorb pruefen" in tab.last_cleanup_var.value
    assert "2026-06-05 08:15:00" in tab.history_text.value


def test_cleanup_restore_history_uses_saved_entries():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    class DummyText:
        def __init__(self):
            self.value = ""

        def configure(self, **_kwargs):
            return None

        def delete(self, *_args):
            self.value = ""

        def insert(self, _index, text):
            self.value = text

    class DummyApp:
        def __init__(self):
            self.settings = {
                "cleanup_assistant_cleanup_history": [
                    {
                        "timestamp": "2026-06-04 16:10:00",
                        "module_id": "thumbnail_cache",
                        "module_title": "Thumbnail-Cache",
                        "summary": "1 Pfad/Pfade, 5 B freigegeben",
                    }
                ]
            }

    tab.app = DummyApp()
    tab.CLEANUP_HISTORY_LIMIT = CleanupAssistantTab.CLEANUP_HISTORY_LIMIT
    tab.CLEANUP_HISTORY_SETTINGS_KEY = CleanupAssistantTab.CLEANUP_HISTORY_SETTINGS_KEY
    tab.LAST_CLEANUP_SETTINGS_KEY = CleanupAssistantTab.LAST_CLEANUP_SETTINGS_KEY
    tab.cleanup_history = []
    tab.last_cleanup_var = DummyVar()
    tab.history_summary_var = DummyVar()
    tab.history_text = DummyText()

    tab._restore_cleanup_history()

    assert len(tab.cleanup_history) == 1
    assert "Thumbnail-Cache" in tab.last_cleanup_var.value
    assert "1 erfolgreiche Cleanup-Lauf/Laeufe" in tab.history_summary_var.value
    assert "2026-06-04 16:10:00" in tab.history_text.value


def test_cleanup_detail_summary_mentions_top_large_log():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    module = next(
        item for item in CleanupAssistantTab.MODULES if item.module_id == "log_files"
    )

    detail = tab._detail_summary_for_result(
        module,
        {
            "existing_paths": ["/var/log"],
            "inaccessible": 0,
            "large_logs": [(25 * 1024 * 1024, "/var/log/big.log")],
        },
    )

    assert "grosse Logs" in detail
    assert "big.log" in detail


def test_cleanup_top_findings_summary_lists_large_logs():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    module = next(
        item for item in CleanupAssistantTab.MODULES if item.module_id == "log_files"
    )

    summary = tab._top_findings_summary_for_result(
        module,
        {
            "large_logs": [
                (25 * 1024 * 1024, "/var/log/big.log"),
                (21 * 1024 * 1024, "/var/log/auth.log"),
            ]
        },
    )

    assert "big.log" in summary
    assert "auth.log" in summary


def test_cleanup_top_findings_summary_uses_existing_paths_for_cache():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    module = next(
        item for item in CleanupAssistantTab.MODULES if item.module_id == "user_cache"
    )

    summary = tab._top_findings_summary_for_result(
        module,
        {
            "existing_paths": ["/home/test/.cache", "/home/test/.cache/thumbnails"],
        },
    )

    assert "/home/test/.cache" in summary


def test_cleanup_format_module_details_includes_paths_and_findings():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    class DummyVar:
        def __init__(self, value):
            self._value = value

        def get(self):
            return self._value

    tab.module_results = {
        "log_files": {
            "size_bytes": 25 * 1024 * 1024,
            "file_count": 2,
            "dir_count": 1,
            "inaccessible": 0,
            "paths": ["/var/log"],
            "existing_paths": ["/var/log"],
            "large_logs": [(25 * 1024 * 1024, "/var/log/big.log")],
            "journal_disk_usage": "Archived and active journals take up 1.2G in the file system.",
        }
    }
    tab.module_status_vars = {
        "log_files": DummyVar("Status: 1 grosse Logs gefunden (25.0 MiB)")
    }
    tab.module_last_check_vars = {"log_files": DummyVar("Letzter Check: 12:00:00")}
    tab.module_risk_vars = {"log_files": DummyVar("Warnstufe: Vorsicht")}

    details = tab._format_module_details("log_files")

    assert "Log-Dateien pruefen" in details
    assert "/var/log" in details
    assert "big.log" in details
    assert "Warnstufe: Vorsicht" in details


def test_cleanup_candidates_for_cache_default_to_safe_selected_paths():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "user_cache": {
            "existing_paths": ["/home/test/.cache", "/home/test/.cache/thumbnails"],
            "cache_candidates": [
                {
                    "path": "/home/test/.cache/pip",
                    "size_bytes": 4096,
                    "is_dir": True,
                    "safe": True,
                },
                {
                    "path": "/home/test/.cache/chromium",
                    "size_bytes": 2048,
                    "is_dir": True,
                    "safe": False,
                },
            ],
        }
    }

    candidates = tab._cleanup_candidates_for_module("user_cache")

    assert candidates
    assert candidates[0]["selected"] is True
    assert candidates[0]["safe"] is True
    assert candidates[1]["selected"] is False
    assert candidates[1]["safe"] is False
    assert "browsernah" in candidates[1]["detail"]


def test_cleanup_candidates_for_logs_default_to_unselected_review_items():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "log_files": {
            "large_logs": [(25 * 1024 * 1024, "/var/log/big.log")],
            "journal_disk_usage": "Archived and active journals take up 1.2G in the file system.",
        }
    }

    candidates = tab._cleanup_candidates_for_module("log_files")

    assert len(candidates) == 3
    assert candidates[0]["selected"] is False
    assert candidates[0]["safe"] is False
    assert candidates[1]["label"] == "journalctl vacuum-time=14d"
    assert candidates[1]["selected"] is True
    assert candidates[1]["safe"] is True
    assert candidates[1]["command"] == ["journalctl", "--vacuum-time=14d"]
    assert candidates[2]["label"] == "journalctl vacuum-size=200M"
    assert candidates[2]["selected"] is False
    assert candidates[2]["safe"] is False


def test_cleanup_candidates_for_apt_include_autoclean_and_clean():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "apt_cache": {
            "existing_paths": ["/var/cache/apt", "/var/cache/apt/archives"],
        }
    }

    candidates = tab._cleanup_candidates_for_module("apt_cache")

    assert len(candidates) == 2
    assert candidates[0]["label"] == "APT autoclean ausfuehren"
    assert candidates[0]["selected"] is True
    assert candidates[0]["safe"] is True
    assert candidates[0]["command"] == ["apt", "autoclean"]
    assert candidates[1]["label"] == "APT clean ausfuehren"
    assert candidates[1]["selected"] is False
    assert candidates[1]["safe"] is False
    assert candidates[1]["command"] == ["apt", "clean"]


def test_cleanup_candidates_for_temporary_files_use_remove_path_action():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "temporary_files": {
            "existing_paths": ["/tmp"],
            "temp_candidates": [
                {
                    "path": "/tmp/tmp-123",
                    "size_bytes": 4096,
                    "age_seconds": 8 * 3600,
                    "is_dir": True,
                }
            ],
        }
    }

    candidates = tab._cleanup_candidates_for_module("temporary_files")

    assert candidates
    assert candidates[0]["action"] == "remove_path"
    assert candidates[0]["selected"] is True


def test_cleanup_prep_summary_mentions_no_delete_and_candidates():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {"user_cache": {"existing_paths": ["/home/test/.cache"]}}
    candidates = [
        {
            "label": "Pfad fuer spaetere Bereinigung vormerken",
            "detail": "/home/test/.cache",
            "selected": True,
            "safe": True,
        }
    ]

    summary = tab._format_cleanup_prep_summary("user_cache", candidates)

    assert "direkt gestartet" in summary
    assert "/home/test/.cache" in summary


def test_cleanup_prep_summary_for_safe_module_mentions_real_cleanup():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.module_results = {
        "thumbnail_cache": {"existing_paths": ["/home/test/.cache/thumbnails"]}
    }
    candidates = [
        {
            "label": "Thumbnail-Cache leeren",
            "detail": "/home/test/.cache/thumbnails",
            "selected": True,
            "safe": True,
            "action": "purge_dir_contents",
            "path": "/home/test/.cache/thumbnails",
        }
    ]

    summary = tab._format_cleanup_prep_summary("thumbnail_cache", candidates)

    assert "direkt gestartet" in summary
    assert "Sicherheits- und sudo-Flow" in summary


def test_temporary_cleanup_candidates_only_include_old_user_entries():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.TEMP_MIN_AGE_SECONDS = 60
    tab.TEMP_CANDIDATE_LIMIT = 8

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        old_file = base / "old.tmp"
        old_file.write_bytes(b"1234")
        recent_file = base / "recent.tmp"
        recent_file.write_bytes(b"56")

        old_ts = old_file.stat().st_mtime - 3600
        recent_ts = recent_file.stat().st_mtime
        old_file.touch()
        recent_file.touch()
        os.utime(old_file, (old_ts, old_ts))
        os.utime(recent_file, (recent_ts, recent_ts))

        candidates = tab._temporary_cleanup_candidates([base])

    assert len(candidates) == 1
    assert candidates[0]["path"].endswith("old.tmp")


def test_user_cache_cleanup_candidates_skip_thumbnails_and_mark_browser_like():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.TEMP_CANDIDATE_LIMIT = 8
    tab.CACHE_CHILD_CANDIDATE_LIMIT = 4
    tab.CACHE_SPLIT_THRESHOLD_BYTES = 1024 * 1024

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "thumbnails").mkdir()
        (base / "thumbnails" / "skip.png").write_bytes(b"1")
        (base / "pip").mkdir()
        (base / "pip" / "wheel.bin").write_bytes(b"12345")
        (base / "chromium").mkdir()
        (base / "chromium" / "cache.bin").write_bytes(b"123")

        candidates = tab._user_cache_cleanup_candidates(base)

    assert len(candidates) == 2
    assert candidates[0]["path"].endswith("pip")
    assert candidates[0]["safe"] is True
    assert candidates[1]["path"].endswith("cache.bin")
    assert candidates[1]["safe"] is False


def test_user_cache_cleanup_candidates_split_browser_like_children():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.TEMP_CANDIDATE_LIMIT = 8
    tab.CACHE_CHILD_CANDIDATE_LIMIT = 4
    tab.CACHE_SPLIT_THRESHOLD_BYTES = 1

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        browser = base / "chromium"
        browser.mkdir()
        (browser / "GPUCache").mkdir()
        (browser / "GPUCache" / "gpu.bin").write_bytes(b"12345")
        (browser / "Code Cache").mkdir()
        (browser / "Code Cache" / "code.bin").write_bytes(b"123")

        candidates = tab._user_cache_cleanup_candidates(base)

    assert len(candidates) == 2
    assert candidates[0]["path"].endswith("GPUCache")
    assert candidates[0]["safe"] is False
    assert candidates[0]["parent_path"].endswith("chromium")
    assert candidates[1]["path"].endswith("Code Cache")


def test_purge_directory_contents_removes_files_and_subdirs():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "thumb1.png").write_bytes(b"1234")
        (base / "nested").mkdir()
        (base / "nested" / "thumb2.png").write_bytes(b"56789")

        result = tab._purge_directory_contents(base)

        assert result["removed_entries"] == 2
        assert result["freed_bytes"] == 9
        assert result["errors"] == []
        assert list(base.iterdir()) == []


def test_remove_path_entry_removes_single_temp_candidate():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        target = base / "temp-dir"
        target.mkdir()
        (target / "leftover.txt").write_text("abc", encoding="utf-8")

        result = tab._remove_path_entry(target)

        assert result["removed_entries"] >= 2
        assert result["freed_bytes"] == 3
        assert result["errors"] == []
        assert not target.exists()


def test_execute_cleanup_candidates_removes_user_cache_candidate_and_reanalyses():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.EXECUTABLE_CLEANUP_MODULES = CleanupAssistantTab.EXECUTABLE_CLEANUP_MODULES
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {}
    protocol_messages = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.protocol_status_var = DummyVar()
    tab._append_protocol = protocol_messages.append
    reanalysed = []
    tab.analysis_handlers = {
        "user_cache": lambda from_full_scan=False: reanalysed.append(from_full_scan)
    }

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        target = base / "pip"
        target.mkdir()
        (target / "cache.bin").write_bytes(b"123456")

        original_allowed = tab._allowed_cleanup_roots_for_module
        tab._allowed_cleanup_roots_for_module = lambda module_id: (
            [base] if module_id == "user_cache" else original_allowed(module_id)
        )

        executed = tab._execute_cleanup_candidates(
            "user_cache",
            [
                {
                    "label": "Cache-ordner entfernen",
                    "detail": str(target),
                    "selected": True,
                    "safe": True,
                    "action": "remove_path",
                    "path": str(target),
                }
            ],
        )

        assert executed is True
        assert not target.exists()
        assert reanalysed == [False]
        assert "abgeschlossen" in tab.protocol_status_var.value
        assert any("bereinigt" in message for message in protocol_messages)


def test_execute_cleanup_candidates_cleans_thumbnail_cache_and_reanalyses():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.EXECUTABLE_CLEANUP_MODULES = CleanupAssistantTab.EXECUTABLE_CLEANUP_MODULES
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {}
    protocol_messages = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.protocol_status_var = DummyVar()
    tab._append_protocol = protocol_messages.append
    reanalysed = []
    tab.analysis_handlers = {
        "thumbnail_cache": lambda from_full_scan=False: reanalysed.append(
            from_full_scan
        )
    }

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "thumb.png").write_bytes(b"12345")

        original_allowed = tab._allowed_cleanup_roots_for_module
        tab._allowed_cleanup_roots_for_module = lambda module_id: (
            [base] if module_id == "thumbnail_cache" else original_allowed(module_id)
        )

        executed = tab._execute_cleanup_candidates(
            "thumbnail_cache",
            [
                {
                    "label": "Thumbnail-Cache leeren",
                    "detail": str(base),
                    "selected": True,
                    "safe": True,
                    "action": "purge_dir_contents",
                    "path": str(base),
                }
            ],
        )

        assert executed is True
        assert list(base.iterdir()) == []
        assert reanalysed == [False]
        assert "abgeschlossen" in tab.protocol_status_var.value
        assert any("bereinigt" in message for message in protocol_messages)


def test_execute_cleanup_candidates_removes_temp_candidate_and_reanalyses():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.EXECUTABLE_CLEANUP_MODULES = CleanupAssistantTab.EXECUTABLE_CLEANUP_MODULES
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {}
    protocol_messages = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.protocol_status_var = DummyVar()
    tab._append_protocol = protocol_messages.append
    reanalysed = []
    tab.analysis_handlers = {
        "temporary_files": lambda from_full_scan=False: reanalysed.append(
            from_full_scan
        )
    }

    with TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        target = base / "tmp-leftover"
        target.mkdir()
        (target / "cache.bin").write_bytes(b"123456")

        original_allowed = tab._allowed_cleanup_roots_for_module
        tab._allowed_cleanup_roots_for_module = lambda module_id: (
            [base] if module_id == "temporary_files" else original_allowed(module_id)
        )

        executed = tab._execute_cleanup_candidates(
            "temporary_files",
            [
                {
                    "label": "Temporaeren ordner entfernen",
                    "detail": str(target),
                    "selected": True,
                    "safe": True,
                    "action": "remove_path",
                    "path": str(target),
                }
            ],
        )

        assert executed is True
        assert not target.exists()
        assert reanalysed == [False]
        assert "abgeschlossen" in tab.protocol_status_var.value
        assert any("bereinigt" in message for message in protocol_messages)


def test_execute_cleanup_candidates_runs_apt_command_and_reanalyses():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.EXECUTABLE_CLEANUP_MODULES = CleanupAssistantTab.EXECUTABLE_CLEANUP_MODULES
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {}
    protocol_messages = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.protocol_status_var = DummyVar()
    tab._append_protocol = protocol_messages.append
    reanalysed = []
    tab.analysis_handlers = {
        "apt_cache": lambda from_full_scan=False: reanalysed.append(from_full_scan)
    }
    tab._run_sudo_cleanup_command = lambda command, reason="": {
        "ok": True,
        "rc": 0,
        "out": "Del obsolete archives",
        "command": ["sudo", "-n", *command],
    }

    executed = tab._execute_cleanup_candidates(
        "apt_cache",
        [
            {
                "label": "APT autoclean ausfuehren",
                "detail": "/var/cache/apt | entfernt nur nicht mehr benoetigte Paketdateien",
                "selected": True,
                "safe": True,
                "action": "run_sudo_command",
                "command": ["apt", "autoclean"],
                "reason": "Cleanup Assistant: APT autoclean",
            }
        ],
    )

    assert executed is True
    assert reanalysed == [False]
    assert "abgeschlossen" in tab.protocol_status_var.value
    assert any("apt autoclean erfolgreich" in message for message in protocol_messages)


def test_execute_cleanup_candidates_runs_journalctl_vacuum_and_reanalyses():
    tab = CleanupAssistantTab.__new__(CleanupAssistantTab)
    tab.EXECUTABLE_CLEANUP_MODULES = CleanupAssistantTab.EXECUTABLE_CLEANUP_MODULES
    tab.MODULES = CleanupAssistantTab.MODULES
    tab.module_results = {}
    protocol_messages = []

    class DummyVar:
        def __init__(self):
            self.value = ""

        def set(self, value):
            self.value = value

    tab.protocol_status_var = DummyVar()
    tab._append_protocol = protocol_messages.append
    reanalysed = []
    tab.analysis_handlers = {
        "log_files": lambda from_full_scan=False: reanalysed.append(from_full_scan)
    }
    tab._run_sudo_cleanup_command = lambda command, reason="": {
        "ok": True,
        "rc": 0,
        "out": "Vacuuming done, freed 120.0M of archived journals.",
        "command": ["sudo", "-n", *command],
    }

    executed = tab._execute_cleanup_candidates(
        "log_files",
        [
            {
                "label": "journalctl vacuum-time=14d",
                "detail": "Archived and active journals take up 1.2G in the file system. | behaelt nur die letzten 14 Tage",
                "selected": True,
                "safe": True,
                "action": "run_sudo_command",
                "command": ["journalctl", "--vacuum-time=14d"],
                "reason": "Cleanup Assistant: journalctl vacuum-time=14d",
            }
        ],
    )

    assert executed is True
    assert reanalysed == [False]
    assert "abgeschlossen" in tab.protocol_status_var.value
    assert any(
        "journalctl --vacuum-time=14d erfolgreich" in message
        for message in protocol_messages
    )
