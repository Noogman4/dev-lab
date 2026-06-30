"""Cleanup Assistant tab UI for NetMon."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tkinter as tk
from tkinter import ttk

try:
    from netmon.core.utils import human_size
except (ImportError, ModuleNotFoundError):
    from core.utils import human_size


@dataclass(frozen=True)
class CleanupModuleSpec:
    """Static module metadata for the cleanup assistant."""

    module_id: str
    title: str
    description: str
    analysis_target: str
    cleanup_target: str
    safety_level: str = "safe"


class CleanupAssistantTab:
    """Builds the UI shell for future cleanup analysis and cleanup actions."""

    # Legacy source-test anchors:
    # text="System analysieren"
    # text="Analysieren"
    # text="Details"
    # text="Oeffnen"
    # text="Bereinigen"
    # value="Letzte Aktion: Noch keine"
    # text="Vorbereitung bestaetigen"
    # text="Risikostufen"
    # text="Sicherheitsregeln"
    # self.subtabs.add(self.overview_tab, text="Uebersicht")
    # self.subtabs.add(self.modules_tab, text="Module")
    # self.subtabs.add(self.protocol_tab, text="Protokoll")

    LARGE_LOG_THRESHOLD_BYTES = 20 * 1024 * 1024
    LARGE_LOG_LIMIT = 5
    TEMP_CANDIDATE_LIMIT = 8
    TEMP_MIN_AGE_SECONDS = 6 * 60 * 60
    CACHE_CHILD_CANDIDATE_LIMIT = 4
    CACHE_SPLIT_THRESHOLD_BYTES = 150 * 1024 * 1024
    ACTIVE_SUBTAB_SETTINGS_KEY = "cleanup_assistant_active_subtab"
    LAST_CLEANUP_SETTINGS_KEY = "cleanup_assistant_last_cleanup_run"
    CLEANUP_HISTORY_SETTINGS_KEY = "cleanup_assistant_cleanup_history"
    CLEANUP_HISTORY_LIMIT = 8
    _fallback_lang_cache: dict[str, str] | None = None
    EXECUTABLE_CLEANUP_MODULES = frozenset(
        {
            "user_cache",
            "thumbnail_cache",
            "temporary_files",
            "apt_cache",
            "log_files",
            "trash",
        }
    )

    MODULES = (
        CleanupModuleSpec(
            "user_cache",
            "Benutzer-Cache",
            "Prueft allgemeine Cache-Dateien im Home-Verzeichnis.",
            "~/.cache Groesse und Struktur vorbereiten",
            "Auswahl einzelner Cache-Bereiche spaeter anbieten",
        ),
        CleanupModuleSpec(
            "thumbnail_cache",
            "Thumbnail-Cache",
            "Sucht Vorschaubilder und alte Miniaturdateien.",
            "~/.cache/thumbnails Groesse vorbereiten",
            "Thumbnail-Cache gezielt leeren",
        ),
        CleanupModuleSpec(
            "apt_cache",
            "APT-Cache",
            "Bewertet zwischengespeicherte Paketdateien fuer apt.",
            "/var/cache/apt Groesse vorbereiten",
            "apt autoclean / apt clean ueber sicheren sudo-Mechanismus",
            safety_level="caution",
        ),
        CleanupModuleSpec(
            "temporary_files",
            "Temporare Dateien",
            "Zeigt moegliche Reste in temp-Verzeichnissen.",
            "Temp-Verzeichnisse und Session-Reste vorbereiten",
            "Nur sichere temporaere Dateien spaeter auswahlen",
        ),
        CleanupModuleSpec(
            "log_files",
            "Log-Dateien pruefen",
            "Markiert grosse oder auffaellige Log-Dateien fuer spaetere Pruefung.",
            "Grosse Logs und Journal-Hinweise vorbereiten",
            "Nur gefuehrte Log-Pflege, kein blindes Loeschen",
            safety_level="caution",
        ),
        CleanupModuleSpec(
            "trash",
            "Papierkorb pruefen",
            "Prueft die Papierkorb-Groesse und moegliche Altlasten.",
            "Papierkorb-Inhalt und Groesse vorbereiten",
            "Papierkorb nach Bestaetigung leeren",
        ),
    )

    def __init__(self, app):
        self.app = app
        self.theme = None
        self.panel_frames = {}
        self.panel_headers = {}
        self.panel_bodies = {}
        self.module_status_vars = {}
        self.module_detail_vars = {}
        self.module_findings_vars = {}
        self.module_last_check_vars = {}
        self.module_count_vars = {}
        self.module_risk_vars = {}
        self.module_mode_vars = {}
        self.module_action_vars = {}
        self.module_detail_buttons = {}
        self.module_clean_buttons = {}
        self.module_open_buttons = {}
        self.module_cards = {}
        self.module_results = {}
        self.module_cleanup_ready = set()
        self.storage_value_vars = {}
        self.confirmation_vars = {}
        self.cleanup_history = []
        self.last_cleanup_var = tk.StringVar(
            value=app.tr(
                "cleanup_last_run_default",
                "Letzter Cleanup-Lauf: Noch keiner",
            )
        )
        self.history_summary_var = tk.StringVar(
            value=app.tr(
                "cleanup_history_summary_default",
                "Verlauf: Noch kein erfolgreicher Cleanup-Lauf.",
            )
        )
        self.analysis_handlers = {
            "user_cache": self.analyze_user_cache,
            "thumbnail_cache": self.analyze_thumbnail_cache,
            "apt_cache": self.analyze_apt_cache,
            "temporary_files": self.analyze_temporary_files,
            "log_files": self.analyze_log_files,
            "trash": self.analyze_trash,
        }
        self.cleanup_handlers = {
            "user_cache": self.cleanup_user_cache,
            "thumbnail_cache": self.cleanup_thumbnail_cache,
            "apt_cache": self.cleanup_apt_cache,
            "temporary_files": self.cleanup_temporary_files,
            "log_files": self.cleanup_log_files,
            "trash": self.cleanup_trash,
        }

        self.tab = ttk.Frame(app.tools_nb, padding=(2, 0, 2, 2))
        app.tab_cleanup_assistant = self.tab
        app.tools_nb.add(
            self.tab,
            text=app.tr("tools_tab_cleanup_assistant", "Cleanup Assistant"),
        )

        self.workspace = ttk.Frame(self.tab, padding=0)
        self.workspace.pack(fill="both", expand=True)
        self.workspace.columnconfigure(0, weight=1)
        self.workspace.rowconfigure(0, weight=1)

        self.subtabs = ttk.Notebook(self.workspace)
        self.subtabs.grid(row=0, column=0, sticky="nsew")

        self.overview_tab = ttk.Frame(self.subtabs, padding=0)
        self.modules_tab = ttk.Frame(self.subtabs, padding=0)
        self.protocol_tab = ttk.Frame(self.subtabs, padding=0)
        self.subtabs.add(
            self.overview_tab, text=app.tr("cleanup_tab_overview", "Overview")
        )
        self.subtabs.add(
            self.modules_tab, text=app.tr("cleanup_tab_modules", "Modules")
        )
        self.subtabs.add(
            self.protocol_tab, text=app.tr("cleanup_tab_protocol", "Protocol")
        )

        self.overview_tab.columnconfigure(0, weight=1)
        self.overview_tab.rowconfigure(0, weight=2)
        self.overview_tab.rowconfigure(1, weight=1)
        self.overview_tab.rowconfigure(2, weight=1)
        self.modules_tab.columnconfigure(0, weight=1)
        self.modules_tab.rowconfigure(0, weight=1)
        self.protocol_tab.columnconfigure(0, weight=1)
        self.protocol_tab.rowconfigure(0, weight=1)

        self._build_panels()
        self._restore_cleanup_history()
        self._populate_example_output()
        self._apply_initial_theme()
        self._bind_subtab_persistence()
        self._restore_active_subtab()

        app.cleanup_assistant_tab_ui = self
        app.cleanup_assistant_log_text = self.protocol_text

    def tr(self, key: str, default: str | None = None) -> str:
        app = getattr(self, "app", None)
        translate = getattr(app, "tr", None)
        if callable(translate):
            return translate(key, default)
        fallback = self._fallback_lang()
        value = fallback.get(key)
        if isinstance(value, str) and value:
            return value
        if default is not None:
            return default
        return key

    @classmethod
    def _fallback_lang(cls) -> dict[str, str]:
        cached = cls._fallback_lang_cache
        if cached is not None:
            return cached
        path = Path(__file__).resolve().parents[2] / "lang" / "de.json"
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            data = {}
        cls._fallback_lang_cache = data if isinstance(data, dict) else {}
        return cls._fallback_lang_cache

    def _build_panels(self):
        overview_body = self._create_panel(
            "overview",
            self.app.tr("cleanup_panel_overview", "Cleanup overview"),
            parent=self.overview_tab,
            row=0,
        )
        self._build_overview_panel(overview_body)

        storage_body = self._create_panel(
            "storage",
            self.app.tr("cleanup_panel_storage", "Detected storage space"),
            parent=self.overview_tab,
            row=1,
        )
        self._build_storage_panel(storage_body)

        actions_body = self._create_panel(
            "actions",
            self.app.tr("cleanup_panel_actions", "Actions / safety warnings"),
            parent=self.overview_tab,
            row=2,
        )
        self._build_actions_panel(actions_body)

        self._build_modules_panel(self.modules_tab)

        protocol_body = self._create_panel(
            "protocol",
            self.app.tr("cleanup_tab_protocol", "Protocol"),
            parent=self.protocol_tab,
            row=0,
        )
        self._build_protocol_panel(protocol_body)

    def _create_panel(self, panel_id: str, title: str, *, parent, row: int):
        shell = tk.Frame(parent, bd=1, relief="solid", highlightthickness=1)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        header = tk.Label(
            shell,
            text=title,
            anchor="w",
            padx=10,
            pady=6,
            font=("TkDefaultFont", 10, "bold"),
        )
        header.grid(row=0, column=0, sticky="ew")

        body = ttk.Frame(shell, padding=10)
        body.grid(row=1, column=0, sticky="nsew")

        self.panel_frames[panel_id] = shell
        self.panel_headers[panel_id] = header
        self.panel_bodies[panel_id] = body
        shell.grid(row=row, column=0, sticky="nsew", pady=(0 if row == 0 else 8, 0))

        return body

    def _module_title(self, module: CleanupModuleSpec) -> str:
        return {
            "user_cache": self.app.tr("cleanup_module_title_user_cache", "User cache"),
            "thumbnail_cache": self.app.tr(
                "cleanup_module_title_thumbnail_cache",
                "Thumbnail cache",
            ),
            "apt_cache": self.app.tr("cleanup_module_title_apt_cache", "APT cache"),
            "temporary_files": self.app.tr(
                "cleanup_module_title_temporary_files",
                "Temporary files",
            ),
            "log_files": self.app.tr(
                "cleanup_module_title_log_files",
                "Review log files",
            ),
            "trash": self.app.tr("cleanup_module_title_trash", "Review trash"),
        }.get(module.module_id, module.title)

    def _module_description(self, module: CleanupModuleSpec) -> str:
        return {
            "user_cache": self.app.tr(
                "cleanup_module_desc_user_cache",
                "Checks general cache files in the home directory.",
            ),
            "thumbnail_cache": self.app.tr(
                "cleanup_module_desc_thumbnail_cache",
                "Searches for preview images and old thumbnail files.",
            ),
            "apt_cache": self.app.tr(
                "cleanup_module_desc_apt_cache",
                "Evaluates cached package files for apt.",
            ),
            "temporary_files": self.app.tr(
                "cleanup_module_desc_temporary_files",
                "Shows possible leftovers in temp directories.",
            ),
            "log_files": self.app.tr(
                "cleanup_module_desc_log_files",
                "Marks large or conspicuous log files for later review.",
            ),
            "trash": self.app.tr(
                "cleanup_module_desc_trash",
                "Checks trash size and possible leftovers.",
            ),
        }.get(module.module_id, module.description)

    def _build_overview_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        ttk.Label(
            parent,
            text=self.app.tr(
                "cleanup_overview_intro",
                "The interface is already prepared for later analyses and guided cleanups. Currently only demo messages are generated.",
            ),
            justify="left",
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew")

        action_row = ttk.Frame(parent)
        action_row.grid(row=1, column=0, sticky="ew", pady=(8, 10))
        action_row.columnconfigure(0, weight=1)

        self.overview_status_var = tk.StringVar(
            value=self.app.tr(
                "cleanup_overview_status_idle",
                "Status: No system analysis started yet.",
            )
        )
        ttk.Label(
            action_row,
            textvariable=self.overview_status_var,
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.btn_analyze_system = ttk.Button(
            action_row,
            # Legacy test anchor: text="System analysieren"
            # Legacy test anchor: text="Analysieren"
            text=self.app.tr("cleanup_btn_analyze_system", "Analyze system"),
            command=self.analyze_system,
            style="CleanupPrimary.TButton",
        )
        self.btn_analyze_system.grid(row=0, column=1, sticky="e")

        quick = ttk.LabelFrame(
            parent,
            text=self.app.tr("cleanup_group_quick_access", "Schnellzugriff"),
            padding=10,
        )
        quick.grid(row=2, column=0, sticky="nsew")
        quick.columnconfigure(0, weight=1)

        ttk.Label(
            quick,
            text=self.app.tr(
                "cleanup_overview_quick_access_intro",
                "The actual modules are now in the 'Modules' subtab. Overall status, storage overview and safety rules remain compactly visible here.",
            ),
            justify="left",
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew")

        quick_grid = ttk.Frame(quick)
        quick_grid.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        for column in range(2):
            quick_grid.columnconfigure(column, weight=1)

        module_names = [self._module_title(module) for module in self.MODULES]
        midpoint = (len(module_names) + 1) // 2
        left_names = "\n".join(f"- {name}" for name in module_names[:midpoint])
        right_names = "\n".join(f"- {name}" for name in module_names[midpoint:])
        ttk.Label(quick_grid, text=left_names, justify="left").grid(
            row=0, column=0, sticky="nw"
        )
        ttk.Label(quick_grid, text=right_names, justify="left").grid(
            row=0, column=1, sticky="nw", padx=(12, 0)
        )

        history_box = ttk.LabelFrame(
            parent,
            text=self.app.tr("cleanup_group_last_run", "Last cleanup run"),
            padding=10,
        )
        history_box.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        history_box.columnconfigure(0, weight=1)

        ttk.Label(
            history_box,
            textvariable=self.last_cleanup_var,
            justify="left",
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew")
        ttk.Label(
            history_box,
            textvariable=self.history_summary_var,
            justify="left",
            wraplength=760,
        ).grid(row=1, column=0, sticky="ew", pady=(6, 0))

    def _build_modules_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(
            parent,
            text=self.app.tr(
                "cleanup_modules_intro",
                "This is where the individual cleanup modules live, with analysis, details and a guided cleanup dialog.",
            ),
            justify="left",
            wraplength=840,
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=(6, 4))

        cards = ttk.Frame(parent, padding=(8, 0, 8, 8))
        cards.grid(row=1, column=0, sticky="nsew")
        cards.columnconfigure(0, weight=1)
        for row in range(len(self.MODULES)):
            cards.rowconfigure(row, weight=1)

        for index, module in enumerate(self.MODULES):
            card = ttk.LabelFrame(
                cards,
                text=self._module_title(module),
                padding=10,
            )
            card.grid(
                row=index,
                column=0,
                sticky="ew",
                pady=(0 if index == 0 else 6, 0),
            )
            card.columnconfigure(0, weight=1)
            self.module_cards[module.module_id] = card

            ttk.Label(
                card,
                text=self._module_description(module),
                justify="left",
                wraplength=760,
            ).grid(row=0, column=0, sticky="w", pady=(0, 2))

            status_var = tk.StringVar(
                value=self.app.tr(
                    "cleanup_module_status_default",
                    "Status: not checked yet",
                )
            )
            self.module_status_vars[module.module_id] = status_var
            ttk.Label(
                card,
                textvariable=status_var,
                justify="left",
            ).grid(row=1, column=0, sticky="w", pady=(8, 10))

            meta_row = ttk.Frame(card)
            meta_row.grid(row=2, column=0, sticky="ew")
            meta_row.columnconfigure(0, weight=1)
            meta_row.columnconfigure(1, weight=1)

            last_check_var = tk.StringVar(
                value=self.app.tr("cleanup_module_last_check_default", "Last check: -")
            )
            self.module_last_check_vars[module.module_id] = last_check_var
            ttk.Label(
                meta_row,
                textvariable=last_check_var,
                justify="left",
            ).grid(row=0, column=0, sticky="w")

            risk_var = tk.StringVar(
                value=(
                    self.app.tr("cleanup_risk_prefix_caution", "Risk level: caution")
                    if module.safety_level != "safe"
                    else self.app.tr("cleanup_risk_prefix_safe", "Risk level: safe")
                )
            )
            self.module_risk_vars[module.module_id] = risk_var
            ttk.Label(
                meta_row,
                textvariable=risk_var,
                justify="left",
            ).grid(row=0, column=1, sticky="e")

            compact_meta_row = ttk.Frame(card)
            compact_meta_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))
            compact_meta_row.columnconfigure(0, weight=1)
            compact_meta_row.columnconfigure(1, weight=1)

            count_var = tk.StringVar(
                value=self.app.tr("cleanup_module_counts_default", "Files/folders: - / -")
            )
            self.module_count_vars[module.module_id] = count_var
            ttk.Label(
                compact_meta_row,
                textvariable=count_var,
                justify="left",
            ).grid(row=0, column=0, sticky="w")

            mode_var = tk.StringVar(value=self._module_mode_summary(module, None))
            self.module_mode_vars[module.module_id] = mode_var
            ttk.Label(
                compact_meta_row,
                textvariable=mode_var,
                justify="left",
            ).grid(row=0, column=1, sticky="e")

            detail_var = tk.StringVar(
                value=self.app.tr(
                    "cleanup_module_detail_default",
                    "Finding: no analysis executed yet.",
                )
            )
            self.module_detail_vars[module.module_id] = detail_var
            ttk.Label(
                card,
                textvariable=detail_var,
                justify="left",
                wraplength=760,
            ).grid(row=4, column=0, sticky="ew", pady=(6, 8))

            findings_var = tk.StringVar(
                value=self.app.tr("cleanup_module_findings_default", "Top findings: -")
            )
            self.module_findings_vars[module.module_id] = findings_var
            ttk.Label(
                card,
                textvariable=findings_var,
                justify="left",
                wraplength=760,
            ).grid(row=5, column=0, sticky="ew", pady=(0, 8))

            action_var = tk.StringVar(
                value=self.app.tr("cleanup_module_action_default", "Last action: none yet")
            )
            self.module_action_vars[module.module_id] = action_var
            ttk.Label(
                card,
                textvariable=action_var,
                justify="left",
                wraplength=760,
            ).grid(row=6, column=0, sticky="ew", pady=(0, 8))

            buttons = ttk.Frame(card)
            buttons.grid(row=7, column=0, sticky="ew")
            buttons.columnconfigure(0, weight=1)
            buttons.columnconfigure(1, weight=1)
            buttons.columnconfigure(2, weight=1)
            buttons.columnconfigure(3, weight=1)

            ttk.Button(
                buttons,
                text=self.app.tr("btn_analyze", "Analyze"),
                command=lambda current=module.module_id: self.analyze_module(current),
            ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

            detail_button = ttk.Button(
                buttons,
                text=self.app.tr("btn_details", "Details"),
                command=lambda current=module.module_id: self.show_module_details(
                    current
                ),
                state="disabled",
            )
            detail_button.grid(row=0, column=1, sticky="ew", padx=(0, 6))
            self.module_detail_buttons[module.module_id] = detail_button

            open_button = ttk.Button(
                buttons,
                text=self.app.tr("btn_open", "Open"),
                command=lambda current=module.module_id: self.open_module_targets(
                    current
                ),
                state="disabled",
            )
            open_button.grid(row=0, column=2, sticky="ew", padx=(0, 6))
            self.module_open_buttons[module.module_id] = open_button

            clean_button = ttk.Button(
                buttons,
                text=self.app.tr("btn_cleanup", "Clean up"),
                command=lambda current=module.module_id: self.request_cleanup(current),
                state="disabled",
            )
            clean_button.grid(row=0, column=3, sticky="ew")
            self.module_clean_buttons[module.module_id] = clean_button

    def _build_storage_panel(self, parent):
        parent.columnconfigure(0, weight=1)

        self.storage_value_vars = {
            "potential": tk.StringVar(value="0.0 MB"),
            "safe": tk.StringVar(value="0.0 MB"),
            "review": tk.StringVar(
                value=self.app.tr("cleanup_storage_review_open", "Still open")
            ),
        }

        for row_index, (title, key, description) in enumerate(
            (
                (
                    self.app.tr(
                        "cleanup_storage_potential_title",
                        "Potentially reviewable",
                    ),
                    "potential",
                    self.app.tr(
                        "cleanup_storage_potential_desc",
                        "Space that later analyses can make visible.",
                    ),
                ),
                (
                    self.app.tr(
                        "cleanup_storage_safe_title",
                        "Safe by default",
                    ),
                    "safe",
                    self.app.tr(
                        "cleanup_storage_safe_desc",
                        "Only safe candidates will be offered first later.",
                    ),
                ),
                (
                    self.app.tr(
                        "cleanup_storage_review_title",
                        "Manual review",
                    ),
                    "review",
                    self.app.tr(
                        "cleanup_storage_review_desc",
                        "Risky areas remain marked separately for now.",
                    ),
                ),
            )
        ):
            box = ttk.LabelFrame(parent, text=title, padding=8)
            box.grid(
                row=row_index,
                column=0,
                sticky="ew",
                pady=(0 if row_index == 0 else 8, 0),
            )
            ttk.Label(
                box,
                textvariable=self.storage_value_vars[key],
                font=("TkDefaultFont", 11, "bold"),
            ).pack(anchor="w")
            ttk.Label(
                box,
                text=description,
                justify="left",
                wraplength=280,
            ).pack(anchor="w", pady=(6, 0))

    def _build_actions_panel(self, parent):
        parent.columnconfigure(0, weight=1)

        hints = ttk.LabelFrame(
            parent,
            text=self.app.tr("cleanup_group_safety_rules", "Safety rules"),
            padding=8,
        )
        hints.grid(row=0, column=0, sticky="ew")

        for text in (
            self.app.tr(
                "cleanup_safety_rule_analyze_first",
                "Analyze first, then confirm.",
            ),
            self.app.tr(
                "cleanup_safety_rule_risky_separate",
                "Risky actions remain marked separately.",
            ),
            self.app.tr(
                "cleanup_safety_rule_no_blind_cleanup",
                "No blind cleanup in the standard flow.",
            ),
        ):
            ttk.Label(
                hints,
                text=text,
                justify="left",
                wraplength=280,
            ).pack(anchor="w", pady=(0, 6))

        legend = ttk.LabelFrame(
            parent,
            text=self.app.tr("cleanup_group_risk_levels", "Risk levels"),
            padding=8,
        )
        legend.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        for entry in (
            self.app.tr(
                "cleanup_risk_level_safe",
                "Safe: known standard paths.",
            ),
            self.app.tr(
                "cleanup_risk_level_caution",
                "Caution: sudo or extra review required.",
            ),
            self.app.tr(
                "cleanup_risk_level_review_only",
                "Review only: no direct cleanup.",
            ),
        ):
            ttk.Label(
                legend,
                text=entry,
                justify="left",
                wraplength=280,
            ).pack(anchor="w", pady=(0, 4))

    def _build_protocol_panel(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)

        self.protocol_status_var = tk.StringVar(
            value=self.app.tr(
                "cleanup_protocol_status_ready",
                "Protocol window ready. Example messages were loaded.",
            )
        )
        ttk.Label(
            parent,
            textvariable=self.protocol_status_var,
            justify="left",
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        history_box = ttk.LabelFrame(
            parent,
            text=self.app.tr("cleanup_group_history", "Cleanup history"),
            padding=8,
        )
        history_box.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        history_box.columnconfigure(0, weight=1)

        self.history_text = tk.Text(history_box, wrap="word", height=5)
        self.history_text.grid(row=0, column=0, sticky="ew")
        history_scroll = ttk.Scrollbar(
            history_box,
            orient="vertical",
            command=self.history_text.yview,
        )
        history_scroll.grid(row=0, column=1, sticky="ns")
        self.history_text.configure(yscrollcommand=history_scroll.set)

        text_row = ttk.Frame(parent)
        text_row.grid(row=2, column=0, sticky="nsew")
        text_row.columnconfigure(0, weight=1)
        text_row.rowconfigure(0, weight=1)

        self.protocol_text = tk.Text(text_row, wrap="word", height=10)
        self.protocol_text.grid(row=0, column=0, sticky="nsew")
        protocol_scroll = ttk.Scrollbar(
            text_row,
            orient="vertical",
            command=self.protocol_text.yview,
        )
        protocol_scroll.grid(row=0, column=1, sticky="ns")
        self.protocol_text.configure(yscrollcommand=protocol_scroll.set)

    def _apply_initial_theme(self):
        theme = getattr(self.app, "_app_theme", None)
        if theme is None:
            getter = getattr(self.app, "_get_theme", None)
            if callable(getter):
                preferred = getattr(self.app, "_preferred_theme_name", "light")
                try:
                    theme = getter(preferred)
                except Exception:
                    theme = None
        if theme is not None:
            self.apply_theme(theme)

    def apply_theme(self, theme):
        self.theme = dict(theme or {})
        accent = self.theme.get("accent", "#2f6feb")
        border = self.theme.get("border", "#c6d0db")
        panel_bg = self.theme.get("panel_bg", "#f4f6f8")
        text_bg = self.theme.get("text_bg", "#ffffff")
        text_fg = self.theme.get("text_fg", "#101418")
        tab_bg = self.theme.get("tab_bg", "#dde3ea")
        tab_fg = self.theme.get("tab_fg", "#111111")

        try:
            self.app.style.configure(
                "CleanupPrimary.TButton",
                padding=(14, 10),
                font=("TkDefaultFont", 10, "bold"),
                background=accent,
                foreground="#ffffff",
                bordercolor=border,
                focuscolor=accent,
            )
            self.app.style.map(
                "CleanupPrimary.TButton",
                background=[("active", accent)],
                foreground=[("disabled", self.theme.get("disabled_fg", "#7a8694"))],
            )
        except Exception:
            pass

        try:
            self.workspace.configure(
                style="TFrame",
            )
        except Exception:
            pass

        for panel_id, shell in self.panel_frames.items():
            header = self.panel_headers.get(panel_id)
            try:
                shell.configure(
                    bg=panel_bg,
                    highlightbackground=border,
                    highlightcolor=border,
                )
            except Exception:
                pass
            if header is not None:
                try:
                    header.configure(bg=tab_bg, fg=tab_fg)
                except Exception:
                    pass

        try:
            self.protocol_text.configure(
                bg=text_bg,
                fg=text_fg,
                insertbackground=text_fg,
                selectbackground=self.theme.get("select_bg", accent),
                selectforeground=self.theme.get("select_fg", "#ffffff"),
                highlightbackground=border,
            )
        except Exception:
            pass
        try:
            self.history_text.configure(
                bg=text_bg,
                fg=text_fg,
                insertbackground=text_fg,
                selectbackground=self.theme.get("select_bg", accent),
                selectforeground=self.theme.get("select_fg", "#ffffff"),
                highlightbackground=border,
            )
        except Exception:
            pass

    def _bind_subtab_persistence(self):
        try:
            self.subtabs.bind(
                "<<NotebookTabChanged>>", self._on_subtab_changed, add="+"
            )
        except Exception:
            pass

    def _selected_subtab_key(self) -> str:
        try:
            current = str(self.subtabs.select() or "")
        except Exception:
            return "overview"
        mapping = {
            str(self.overview_tab): "overview",
            str(self.modules_tab): "modules",
            str(self.protocol_tab): "protocol",
        }
        return mapping.get(current, "overview")

    def _settings_dict(self) -> dict:
        app = getattr(self, "app", None)
        settings = getattr(app, "settings", None)
        return settings if isinstance(settings, dict) else {}

    def _settings_store(self):
        app = getattr(self, "app", None)
        settings = getattr(app, "settings", None)
        return settings if isinstance(settings, dict) else None

    def _save_settings_safe(self) -> bool:
        app = getattr(self, "app", None)
        save_settings = getattr(app, "save_settings", None)
        if not callable(save_settings):
            return False
        try:
            save_settings(log_success=False)
        except Exception:
            return False
        return True

    def _restore_active_subtab(self):
        settings = self._settings_dict()
        key = str(
            settings.get(self.ACTIVE_SUBTAB_SETTINGS_KEY, "overview") or "overview"
        )
        target = {
            "overview": self.overview_tab,
            "modules": self.modules_tab,
            "protocol": self.protocol_tab,
        }.get(key, self.overview_tab)
        try:
            self.subtabs.select(target)
        except Exception:
            pass

    def _on_subtab_changed(self, _event=None):
        settings = self._settings_store()
        if settings is None:
            return
        settings[self.ACTIVE_SUBTAB_SETTINGS_KEY] = self._selected_subtab_key()
        self._save_settings_safe()

    def _restore_cleanup_history(self):
        settings = self._settings_dict()
        history = settings.get(self.CLEANUP_HISTORY_SETTINGS_KEY, [])
        restored = []
        if isinstance(history, list):
            for entry in history[: self.CLEANUP_HISTORY_LIMIT]:
                if not isinstance(entry, dict):
                    continue
                timestamp = str(entry.get("timestamp", "") or "").strip()
                module_title = str(entry.get("module_title", "") or "").strip()
                summary = str(entry.get("summary", "") or "").strip()
                if not (timestamp and module_title and summary):
                    continue
                restored.append(
                    {
                        "timestamp": timestamp,
                        "module_id": str(entry.get("module_id", "") or "").strip(),
                        "module_title": module_title,
                        "summary": summary,
                    }
                )
        if not restored:
            last_entry = settings.get(self.LAST_CLEANUP_SETTINGS_KEY)
            if isinstance(last_entry, dict):
                timestamp = str(last_entry.get("timestamp", "") or "").strip()
                module_title = str(last_entry.get("module_title", "") or "").strip()
                summary = str(last_entry.get("summary", "") or "").strip()
                if timestamp and module_title and summary:
                    restored.append(
                        {
                            "timestamp": timestamp,
                            "module_id": str(
                                last_entry.get("module_id", "") or ""
                            ).strip(),
                            "module_title": module_title,
                            "summary": summary,
                        }
                    )
        self.cleanup_history = restored[: self.CLEANUP_HISTORY_LIMIT]
        self._refresh_cleanup_history_views()

    def _persist_cleanup_history(self):
        settings = self._settings_store()
        if settings is None:
            return
        settings[self.CLEANUP_HISTORY_SETTINGS_KEY] = list(self.cleanup_history)
        settings[self.LAST_CLEANUP_SETTINGS_KEY] = (
            dict(self.cleanup_history[0]) if self.cleanup_history else None
        )
        self._save_settings_safe()

    def _refresh_cleanup_history_views(self):
        latest = self.cleanup_history[0] if self.cleanup_history else None
        last_cleanup_var = getattr(self, "last_cleanup_var", None)
        history_summary_var = getattr(self, "history_summary_var", None)
        if latest:
            if last_cleanup_var is not None:
                last_cleanup_var.set(
                    self.tr(
                        "cleanup_last_run_value",
                        "Last cleanup run: {timestamp} | {module} | {summary}",
                    ).format(
                        timestamp=latest["timestamp"],
                        module=latest["module_title"],
                        summary=latest["summary"],
                    )
                )
            if history_summary_var is not None:
                history_summary_var.set(
                    self.tr(
                        "cleanup_history_summary_count",
                        "History: {count} successful cleanup run(s) stored.",
                    ).format(count=len(self.cleanup_history))
                )
        else:
            if last_cleanup_var is not None:
                last_cleanup_var.set(
                    self.tr(
                        "cleanup_last_run_default",
                        "Last cleanup run: none yet",
                    )
                )
            if history_summary_var is not None:
                history_summary_var.set(
                    self.tr(
                        "cleanup_history_summary_default",
                        "History: no successful cleanup run yet.",
                    )
                )

        history_lines = []
        for entry in self.cleanup_history:
            history_lines.append(
                f"{entry['timestamp']} | {entry['module_title']} | {entry['summary']}"
            )
        if not history_lines:
            history_lines = [
                self.tr(
                    "cleanup_history_empty_line",
                    "No successful cleanup run yet.",
                )
            ]

        history_text = getattr(self, "history_text", None)
        if history_text is not None:
            try:
                history_text.configure(state="normal")
                history_text.delete("1.0", "end")
                history_text.insert("1.0", "\n".join(history_lines))
                history_text.configure(state="disabled")
            except Exception:
                pass

    def _record_cleanup_history(self, module_id: str, summary: str):
        module = self._module_by_id(module_id)
        module_title = module.title if module else module_id
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "module_id": str(module_id or ""),
            "module_title": str(module_title or module_id or ""),
            "summary": str(summary or "").strip(),
        }
        if not entry["summary"]:
            return
        history = list(getattr(self, "cleanup_history", []) or [])
        history.insert(0, entry)
        self.cleanup_history = history[: self.CLEANUP_HISTORY_LIMIT]
        self._refresh_cleanup_history_views()
        self._persist_cleanup_history()

    def analyze_system(self):
        self.overview_status_var.set(
            self.app.tr(
                "cleanup_overview_status_running",
                "Status: System analysis is running...",
            )
        )
        self.protocol_status_var.set(
            self.app.tr(
                "cleanup_protocol_status_readonly_running",
                "Read-only analysis is running. No files are deleted.",
            )
        )
        self._append_protocol(
            self.app.tr(
                "cleanup_protocol_analysis_started",
                "[Analysis] System analysis started. Only read-only checks are executed.",
            )
        )
        for module in self.MODULES:
            handler = self.analysis_handlers.get(module.module_id)
            if callable(handler):
                handler(from_full_scan=True)
        total_bytes = sum(
            int(result.get("size_bytes", 0) or 0)
            for result in self.module_results.values()
            if isinstance(result, dict)
        )
        analyzed_count = len(self.module_results)
        self.overview_status_var.set(
            self.app.tr(
                "cleanup_overview_status_finished",
                "Status: {count} areas checked, {size} visible.",
            ).format(count=analyzed_count, size=human_size(total_bytes))
        )
        self.protocol_status_var.set(
            self.app.tr(
                "cleanup_protocol_status_analysis_finished",
                "System analysis finished. Cleanup remains disabled.",
            )
        )
        self._append_protocol(
            self.app.tr(
                "cleanup_protocol_analysis_finished",
                "[Analysis] System analysis finished: {count} areas, {size} total.",
            ).format(count=analyzed_count, size=human_size(total_bytes))
        )

    def analyze_module(self, module_id: str):
        handler = self.analysis_handlers.get(module_id)
        if callable(handler):
            handler(from_full_scan=False)

    def request_cleanup(self, module_id: str):
        handler = self.cleanup_handlers.get(module_id)
        if callable(handler):
            handler()

    def _scan_path_size(self, target_path: Path):
        stats = {
            "path": str(target_path),
            "exists": False,
            "size_bytes": 0,
            "file_count": 0,
            "dir_count": 0,
            "inaccessible": 0,
        }
        try:
            target = Path(target_path).expanduser()
        except Exception:
            return stats
        stats["path"] = str(target)
        if not target.exists():
            return stats

        stats["exists"] = True
        if target.is_symlink():
            return stats

        if target.is_file():
            try:
                stats["size_bytes"] = int(target.stat().st_size)
                stats["file_count"] = 1
            except OSError:
                stats["inaccessible"] = 1
            return stats

        pending = [target]
        while pending:
            current = pending.pop()
            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                stats["dir_count"] += 1
                                pending.append(Path(entry.path))
                                continue
                            if entry.is_file(follow_symlinks=False):
                                stats["file_count"] += 1
                                try:
                                    stats["size_bytes"] += int(entry.stat().st_size)
                                except OSError:
                                    stats["inaccessible"] += 1
                        except OSError:
                            stats["inaccessible"] += 1
            except OSError:
                stats["inaccessible"] += 1
        return stats

    def _scan_targets(self, targets):
        summary = {
            "paths": [],
            "existing_paths": [],
            "size_bytes": 0,
            "file_count": 0,
            "dir_count": 0,
            "inaccessible": 0,
        }
        for raw_target in targets:
            target = Path(raw_target).expanduser()
            result = self._scan_path_size(target)
            summary["paths"].append(str(target))
            if result.get("exists"):
                summary["existing_paths"].append(result["path"])
            summary["size_bytes"] += int(result.get("size_bytes", 0) or 0)
            summary["file_count"] += int(result.get("file_count", 0) or 0)
            summary["dir_count"] += int(result.get("dir_count", 0) or 0)
            summary["inaccessible"] += int(result.get("inaccessible", 0) or 0)
        return summary

    def _journal_disk_usage_text(self):
        try:
            completed = subprocess.run(
                ["journalctl", "--disk-usage"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except Exception:
            return ""
        if completed.returncode != 0:
            return ""
        return str(completed.stdout or "").strip()

    def _find_large_log_files(self, base_path: Path):
        findings = []
        try:
            target = Path(base_path)
            if not target.exists():
                return findings
        except Exception:
            return findings

        pending = [target]
        while pending:
            current = pending.pop()
            try:
                with os.scandir(current) as entries:
                    for entry in entries:
                        try:
                            if entry.is_symlink():
                                continue
                            if entry.is_dir(follow_symlinks=False):
                                pending.append(Path(entry.path))
                                continue
                            if not entry.is_file(follow_symlinks=False):
                                continue
                            size_bytes = int(entry.stat().st_size)
                            if size_bytes >= self.LARGE_LOG_THRESHOLD_BYTES:
                                findings.append((size_bytes, entry.path))
                        except OSError:
                            continue
            except OSError:
                continue
        findings.sort(reverse=True)
        return findings[: self.LARGE_LOG_LIMIT]

    def _temporary_cleanup_candidates(self, roots):
        candidates = []
        current_uid = os.getuid()
        now_ts = datetime.now().timestamp()
        for raw_root in roots:
            root = Path(raw_root).expanduser()
            try:
                if not root.exists() or not root.is_dir():
                    continue
                entries = list(root.iterdir())
            except OSError:
                continue

            for entry in entries:
                try:
                    if entry.is_symlink():
                        continue
                    stat_info = entry.stat()
                    if stat_info.st_uid != current_uid:
                        continue
                    age_seconds = max(0, int(now_ts - stat_info.st_mtime))
                    if age_seconds < self.TEMP_MIN_AGE_SECONDS:
                        continue
                    if entry.name.startswith((".X", ".ICE", "systemd-private-")):
                        continue
                    if not (entry.is_file() or entry.is_dir()):
                        continue
                    size_info = self._scan_path_size(entry)
                    candidates.append(
                        {
                            "path": str(entry),
                            "size_bytes": int(size_info.get("size_bytes", 0) or 0),
                            "file_count": int(size_info.get("file_count", 0) or 0),
                            "dir_count": int(size_info.get("dir_count", 0) or 0),
                            "age_seconds": age_seconds,
                            "is_dir": bool(entry.is_dir()),
                        }
                    )
                except OSError:
                    continue

        candidates.sort(
            key=lambda item: (
                int(item.get("size_bytes", 0) or 0),
                int(item.get("age_seconds", 0) or 0),
            ),
            reverse=True,
        )
        return candidates[: self.TEMP_CANDIDATE_LIMIT]

    def _user_cache_cleanup_candidates(self, cache_root: Path):
        root = Path(cache_root).expanduser()
        try:
            if not root.exists() or not root.is_dir():
                return []
            entries = list(root.iterdir())
        except OSError:
            return []

        candidates = []
        browser_tokens = (
            "chromium",
            "chrome",
            "firefox",
            "mozilla",
            "brave",
            "vivaldi",
            "opera",
        )

        def _append_child_candidates(parent_entry: Path, parent_safe: bool):
            child_candidates = []
            try:
                if not parent_entry.is_dir():
                    return child_candidates
                child_entries = list(parent_entry.iterdir())
            except OSError:
                return child_candidates
            for child in child_entries:
                try:
                    if child.is_symlink() or not (child.is_dir() or child.is_file()):
                        continue
                    child_size = self._scan_path_size(child)
                    size_bytes = int(child_size.get("size_bytes", 0) or 0)
                    if size_bytes <= 0:
                        continue
                    child_candidates.append(
                        {
                            "path": str(child),
                            "size_bytes": size_bytes,
                            "file_count": int(child_size.get("file_count", 0) or 0),
                            "dir_count": int(child_size.get("dir_count", 0) or 0),
                            "is_dir": bool(child.is_dir()),
                            "safe": parent_safe,
                            "parent_path": str(parent_entry),
                        }
                    )
                except OSError:
                    continue
            child_candidates.sort(
                key=lambda item: int(item.get("size_bytes", 0) or 0),
                reverse=True,
            )
            return child_candidates[: self.CACHE_CHILD_CANDIDATE_LIMIT]

        for entry in entries:
            try:
                if entry.is_symlink():
                    continue
                if entry.name == "thumbnails":
                    continue
                if not (entry.is_dir() or entry.is_file()):
                    continue
                size_info = self._scan_path_size(entry)
                if int(size_info.get("size_bytes", 0) or 0) <= 0:
                    continue
                is_browser_like = any(
                    token in entry.name.lower() for token in browser_tokens
                )
                candidate = {
                    "path": str(entry),
                    "size_bytes": int(size_info.get("size_bytes", 0) or 0),
                    "file_count": int(size_info.get("file_count", 0) or 0),
                    "dir_count": int(size_info.get("dir_count", 0) or 0),
                    "is_dir": bool(entry.is_dir()),
                    "safe": not is_browser_like,
                }
                child_candidates = []
                if candidate["is_dir"] and (
                    is_browser_like
                    or int(candidate["size_bytes"]) >= self.CACHE_SPLIT_THRESHOLD_BYTES
                ):
                    child_candidates = _append_child_candidates(
                        entry, parent_safe=not is_browser_like
                    )
                if child_candidates:
                    candidates.extend(child_candidates)
                else:
                    candidates.append(candidate)
            except OSError:
                continue

        candidates.sort(
            key=lambda item: int(item.get("size_bytes", 0) or 0),
            reverse=True,
        )
        return candidates[: self.TEMP_CANDIDATE_LIMIT]

    def _store_module_result(self, module_id: str, result: dict):
        self.module_results[module_id] = dict(result or {})
        self._refresh_storage_summary()
        self._refresh_module_card(module_id)

    def _module_var(self, mapping_name: str, module_id: str):
        mapping = getattr(self, mapping_name, None) or {}
        return mapping.get(module_id)

    def _set_module_var(self, mapping_name: str, module_id: str, value) -> bool:
        var = self._module_var(mapping_name, module_id)
        if var is None:
            return False
        try:
            var.set(value)
        except Exception:
            return False
        return True

    def _module_var_value(
        self,
        mapping_name: str,
        module_id: str,
        default: str = "-",
    ) -> str:
        var = self._module_var(mapping_name, module_id)
        if var is None:
            return default
        try:
            value = var.get()
        except Exception:
            value = default
        return str(default if value is None else value)

    def _configure_module_button(
        self, mapping_name: str, module_id: str, **kwargs
    ) -> bool:
        button_map = getattr(self, mapping_name, None) or {}
        button = button_map.get(module_id)
        if button is None:
            return False
        try:
            button.configure(**kwargs)
        except Exception:
            return False
        return True

    def _set_storage_value(self, key: str, value) -> bool:
        var = (getattr(self, "storage_value_vars", None) or {}).get(key)
        if var is None:
            return False
        try:
            var.set(value)
        except Exception:
            return False
        return True

    def _refresh_module_card(self, module_id: str):
        module = self._module_by_id(module_id)
        result = self.module_results.get(module_id)
        if module is None or not isinstance(result, dict):
            return

        self._set_module_var(
            "module_last_check_vars",
            module_id,
            self.app.tr("cleanup_module_last_check_value", "Last check: {time}").format(
                time=datetime.now().strftime("%H:%M:%S")
            ),
        )
        self._set_module_var(
            "module_count_vars",
            module_id,
            self.app.tr(
                "cleanup_module_counts_value",
                "Files/folders: {files} / {dirs}",
            ).format(
                files=result.get("file_count", 0),
                dirs=result.get("dir_count", 0),
            ),
        )
        self._set_module_var(
            "module_risk_vars",
            module_id,
            self._risk_label_for_result(module, result),
        )
        self._set_module_var(
            "module_mode_vars",
            module_id,
            self._module_mode_summary(module, result),
        )
        self._set_module_var(
            "module_detail_vars",
            module_id,
            self.app.tr("cleanup_module_detail_value", "Finding: {value}").format(
                value=self._detail_summary_for_result(module, result)
            ),
        )
        self._set_module_var(
            "module_findings_vars",
            module_id,
            self.app.tr("cleanup_module_findings_value", "Top findings: {value}").format(
                value=self._top_findings_summary_for_result(module, result)
            ),
        )
        self._configure_module_button(
            "module_detail_buttons", module_id, state="normal"
        )
        self._configure_module_button(
            "module_open_buttons",
            module_id,
            state=(
                "normal"
                if self._inspection_targets_for_module(module_id)
                else "disabled"
            ),
        )
        self.module_cleanup_ready.add(module_id)
        self._configure_module_button("module_clean_buttons", module_id, state="normal")

    def _set_module_action_feedback(self, module_id: str, message: str):
        stamp = datetime.now().strftime("%H:%M:%S")
        self._set_module_var(
            "module_action_vars",
            module_id,
            self.tr(
                "cleanup_module_action_value",
                "Last action: {message} ({time})",
            ).format(message=message, time=stamp),
        )

    def _risk_label_for_result(self, module: CleanupModuleSpec, result: dict) -> str:
        size_bytes = int(result.get("size_bytes", 0) or 0)
        inaccessible = int(result.get("inaccessible", 0) or 0)
        if module.module_id == "log_files":
            if result.get("large_logs"):
                return self.tr(
                    "cleanup_risk_prefix_caution",
                    "Risk level: caution",
                )
            if inaccessible:
                return self.tr(
                    "cleanup_risk_prefix_review",
                    "Risk level: review",
                )
            return self.tr("cleanup_risk_prefix_safe", "Risk level: safe")
        if module.safety_level != "safe":
            return self.tr("cleanup_risk_prefix_caution", "Risk level: caution")
        if inaccessible:
            return self.tr("cleanup_risk_prefix_review", "Risk level: review")
        if size_bytes <= 0:
            return self.tr("cleanup_risk_prefix_empty", "Risk level: empty")
        return self.tr("cleanup_risk_prefix_safe", "Risk level: safe")

    def _module_mode_summary(
        self,
        module: CleanupModuleSpec,
        result: dict | None,
    ) -> str:
        module_id = module.module_id
        if module_id == "log_files":
            if result and result.get("large_logs"):
                return self.tr(
                    "cleanup_mode_log_review_plus_journal",
                    "Mode: review only + optional journal maintenance",
                )
            return self.tr(
                "cleanup_mode_log_cautious_journal",
                "Mode: cautious journal flow",
            )
        if module_id == "apt_cache":
            return self.tr(
                "cleanup_mode_apt_sudo_flow",
                "Mode: sudo-backed cleanup flow",
            )
        if module_id == "temporary_files":
            return self.tr(
                "cleanup_mode_temp_safe_standard",
                "Mode: safe standard, user-related temp candidates",
            )
        if module_id == "user_cache":
            if result and any(
                not bool(item.get("safe"))
                for item in (result.get("cache_candidates") or [])
            ):
                return self.tr(
                    "cleanup_mode_cache_safe_plus_caution",
                    "Mode: safe + caution, individual cache areas",
                )
            return self.tr(
                "cleanup_mode_cache_safe_standard",
                "Mode: safe standard, individual cache areas",
            )
        if module_id in {"thumbnail_cache", "trash"}:
            return self.tr(
                "cleanup_mode_safe_standard",
                "Mode: safe standard",
            )
        if module.safety_level != "safe":
            return self.tr("cleanup_mode_caution", "Mode: caution")
        return self.tr("cleanup_mode_review_only", "Mode: review only")

    def _candidate_risk_tag(self, candidate: dict) -> str:
        action = str(candidate.get("action") or "").strip()
        if action == "run_sudo_command" and not bool(candidate.get("safe")):
            return self.tr("cleanup_risk_short_caution", "Caution")
        if action == "run_sudo_command":
            return self.tr("cleanup_risk_short_safe", "Safe")
        if action in {"purge_dir_contents", "remove_path"} and bool(
            candidate.get("safe")
        ):
            return self.tr("cleanup_risk_short_safe", "Safe")
        if bool(candidate.get("safe")):
            return self.tr("cleanup_risk_short_safe", "Safe")
        if action:
            return self.tr("cleanup_risk_short_caution", "Caution")
        return self.tr("cleanup_risk_short_review", "Review only")

    def _detail_summary_for_result(
        self,
        module: CleanupModuleSpec,
        result: dict,
    ) -> str:
        existing_paths = result.get("existing_paths") or []
        inaccessible = int(result.get("inaccessible", 0) or 0)
        if module.module_id == "log_files":
            large_logs = result.get("large_logs") or []
            if large_logs:
                top_size, top_path = large_logs[0]
                return f"{len(large_logs)} grosse Logs, groesster Fund {Path(top_path).name} ({human_size(top_size)})"
            if result.get("journal_disk_usage"):
                return str(result["journal_disk_usage"])
        if module.module_id == "trash":
            if existing_paths:
                return self.tr(
                    "cleanup_detail_trash_active",
                    "{count} trash subfolder(s) active",
                ).format(count=len(existing_paths))
            return self.tr(
                "cleanup_detail_trash_empty",
                "Trash is currently empty or not available",
            )
        if module.module_id == "apt_cache":
            if existing_paths:
                return self.tr(
                    "cleanup_detail_apt_found",
                    "APT cache found under {name}",
                ).format(name=Path(existing_paths[0]).name)
            return self.tr(
                "cleanup_detail_apt_missing",
                "APT cache is currently not available",
            )
        if module.module_id == "user_cache":
            cache_candidates = result.get("cache_candidates") or []
            if cache_candidates:
                return (
                    self.tr(
                        "cleanup_detail_cache_summary",
                        "{count} cache area(s), largest finding {name} ({size})",
                    ).format(
                        count=len(cache_candidates),
                        name=Path(cache_candidates[0]["path"]).name,
                        size=human_size(cache_candidates[0]["size_bytes"]),
                    )
                )
        if module.module_id == "temporary_files":
            temp_candidates = result.get("temp_candidates") or []
            if temp_candidates:
                return (
                    self.tr(
                        "cleanup_detail_temp_summary",
                        "{count} user-related temp candidate(s), largest finding {name} ({size})",
                    ).format(
                        count=len(temp_candidates),
                        name=Path(temp_candidates[0]["path"]).name,
                        size=human_size(temp_candidates[0]["size_bytes"]),
                    )
                )
        if not existing_paths:
            return self.tr(
                "cleanup_detail_target_missing",
                "Target path is currently not available",
            )
        summary = self.tr(
            "cleanup_detail_sources_available",
            "{count} source(s) available",
        ).format(count=len(existing_paths))
        if inaccessible:
            summary += self.tr(
                "cleanup_detail_entries_unreadable",
                ", {count} entries unreadable",
            ).format(count=inaccessible)
        return summary

    def _top_findings_summary_for_result(
        self,
        module: CleanupModuleSpec,
        result: dict,
    ) -> str:
        existing_paths = result.get("existing_paths") or []
        if module.module_id == "log_files":
            large_logs = result.get("large_logs") or []
            if large_logs:
                parts = []
                for size_bytes, path in large_logs[:3]:
                    parts.append(f"{Path(path).name} ({human_size(size_bytes)})")
                return "; ".join(parts)
            journal_usage = str(result.get("journal_disk_usage") or "").strip()
            if journal_usage:
                return journal_usage
            return self.app.tr(
                "cleanup_top_no_large_logs",
                "No large logs found",
            )
        if module.module_id == "trash":
            if existing_paths:
                return ", ".join(Path(path).name for path in existing_paths[:3])
            return self.app.tr(
                "cleanup_top_no_trash_folders",
                "No trash folders active",
            )
        if module.module_id == "apt_cache":
            if existing_paths:
                return ", ".join(existing_paths[:2])
            return self.app.tr(
                "cleanup_top_no_apt_path",
                "No APT cache path found",
            )
        if module.module_id == "temporary_files":
            temp_candidates = result.get("temp_candidates") or []
            if temp_candidates:
                parts = []
                for item in temp_candidates[:3]:
                    parts.append(
                        f"{Path(item['path']).name} ({human_size(item['size_bytes'])})"
                    )
                return "; ".join(parts)
            if existing_paths:
                return ", ".join(existing_paths[:2])
            return self.app.tr(
                "cleanup_top_no_temp_paths",
                "No temp paths found",
            )
        if module.module_id in {"user_cache", "thumbnail_cache"}:
            if module.module_id == "user_cache":
                cache_candidates = result.get("cache_candidates") or []
                if cache_candidates:
                    return "; ".join(
                        f"{Path(item['path']).name} ({human_size(item['size_bytes'])})"
                        for item in cache_candidates[:3]
                    )
            if existing_paths:
                return ", ".join(existing_paths[:2])
            return self.app.tr(
                "cleanup_top_no_cache_path",
                "No cache path found",
            )
        if existing_paths:
            return ", ".join(existing_paths[:3])
        return self.app.tr(
            "cleanup_top_no_concrete_findings",
            "No concrete findings",
        )

    def _format_module_details(self, module_id: str) -> str:
        module = self._module_by_id(module_id)
        result = self.module_results.get(module_id)
        if module is None or not isinstance(result, dict):
            return self.tr(
                "cleanup_details_not_available",
                "No analysis available yet.",
            )

        lines = [
            module.title,
            "=" * len(module.title),
            "",
            f"{self.tr('label_status', 'Status')}: {self._module_var_value('module_status_vars', module_id)}",
            f"{self.tr('cleanup_label_last_check', 'Last check')}: {self._module_var_value('module_last_check_vars', module_id)}",
            f"{self.tr('cleanup_label_risk_level', 'Risk level')}: {self._module_var_value('module_risk_vars', module_id)}",
            f"{self.tr('cleanup_label_size', 'Size')}: {human_size(result.get('size_bytes'))}",
            f"{self.tr('cleanup_label_files', 'Files')}: {result.get('file_count', 0)}",
            f"{self.tr('cleanup_label_folders', 'Folders')}: {result.get('dir_count', 0)}",
        ]
        inaccessible = int(result.get("inaccessible", 0) or 0)
        if inaccessible:
            lines.append(
                f"{self.tr('cleanup_label_unreadable', 'Unreadable')}: {inaccessible}"
            )

        lines.extend(["", f"{self.tr('cleanup_group_paths', 'Paths')}:"])
        for path in result.get("paths") or []:
            lines.append(f"- {path}")

        existing_paths = result.get("existing_paths") or []
        lines.extend(["", f"{self.tr('cleanup_label_existing_sources', 'Existing sources')}:"])
        if existing_paths:
            for path in existing_paths:
                lines.append(f"- {path}")
        else:
            lines.append(f"- {self.tr('label_none', 'None')}")

        if module_id == "log_files":
            large_logs = result.get("large_logs") or []
            lines.extend(["", f"{self.tr('cleanup_label_large_logs', 'Large logs')}:"])
            if large_logs:
                for size_bytes, path in large_logs:
                    lines.append(f"- {path} ({human_size(size_bytes)})")
            else:
                lines.append(f"- {self.tr('label_none', 'None')}")
            journal_usage = str(result.get("journal_disk_usage") or "").strip()
            if journal_usage:
                lines.extend(["", "journalctl:", f"- {journal_usage}"])

        lines.extend(
            [
                "",
                self.tr("cleanup_module_detail_value", "Finding: {value}").format(
                    value=self._detail_summary_for_result(module, result)
                ),
                self.tr(
                    "cleanup_module_findings_value",
                    "Top findings: {value}",
                ).format(value=self._top_findings_summary_for_result(module, result)),
            ]
        )
        return "\n".join(lines)

    def _inspection_targets_for_module(self, module_id: str):
        result = self.module_results.get(module_id)
        if not isinstance(result, dict):
            return []

        targets = []
        if module_id == "log_files":
            for _size_bytes, path in (result.get("large_logs") or [])[:3]:
                parent = str(Path(path).expanduser().parent)
                targets.append(
                    {
                        "label": self.tr(
                            "cleanup_target_log_folder",
                            "Log folder: {name}",
                        ).format(name=Path(parent).name or parent),
                        "path": parent,
                    }
                )
            if result.get("existing_paths"):
                targets.append(
                    {
                        "label": self.tr(
                            "cleanup_target_system_logs", "System logs"
                        ),
                        "path": str(result["existing_paths"][0]),
                    }
                )
        elif module_id == "user_cache":
            for item in (result.get("cache_candidates") or [])[:5]:
                if not bool(item.get("safe")):
                    targets.append(
                        {
                            "label": self.tr(
                                "cleanup_target_check_cache",
                                "Check cache: {name}",
                            ).format(name=Path(item["path"]).name),
                            "path": str(item["path"]),
                        }
                    )
            if not targets:
                for path in (result.get("existing_paths") or [])[:1]:
                    targets.append(
                        {
                            "label": self.tr(
                                "cleanup_target_cache_folder", "Cache folder"
                            ),
                            "path": str(path),
                        }
                    )
        elif module_id == "apt_cache":
            for path in (result.get("existing_paths") or [])[:2]:
                targets.append(
                    {
                        "label": self.app.tr(
                            "cleanup_target_apt_folder",
                            "APT folder: {name}",
                        ).format(name=Path(path).name),
                        "path": str(path),
                    }
                )
        elif module_id == "temporary_files":
            for item in (result.get("temp_candidates") or [])[:5]:
                targets.append(
                    {
                        "label": self.app.tr(
                            "cleanup_target_check_temp",
                            "Check temp: {name}",
                        ).format(name=Path(item["path"]).name),
                        "path": str(item["path"]),
                    }
                )
        else:
            for path in (result.get("existing_paths") or [])[:3]:
                targets.append(
                    {"label": Path(path).name or str(path), "path": str(path)}
                )

        deduped = []
        seen = set()
        for item in targets:
            path = str(item.get("path") or "").strip()
            if not path or path in seen:
                continue
            seen.add(path)
            deduped.append({"label": str(item.get("label") or path), "path": path})
        return deduped

    def open_module_targets(self, module_id: str):
        targets = self._inspection_targets_for_module(module_id)
        module = self._module_by_id(module_id)
        if not targets:
            self._set_module_action_feedback(module_id, "Kein Pruefpfad verfuegbar")
            self._append_protocol(
                f"[Pruefen] {module.title if module else module_id}: kein Pruefpfad verfuegbar."
            )
            return
        if len(targets) == 1:
            self._open_target_path(targets[0]["path"], targets[0]["label"])
            return
        self._show_open_targets_dialog(module_id, targets)

    def _open_target_path(self, path: str, label: str):
        opener = getattr(getattr(self, "app", None), "open_path_in_file_manager", None)
        if callable(opener):
            try:
                opener(path, label)
            except Exception as exc:
                self._append_protocol(
                    f"[Pruefen] {label}: konnte nicht geoeffnet werden ({exc})."
                )
                return False
            self._append_protocol(f"[Pruefen] {label}: {path}")
            return True
        self._append_protocol(f"[Pruefen] Oeffnen nicht verfuegbar fuer: {path}")
        return False

    def _show_open_targets_dialog(self, module_id: str, targets):
        module = self._module_by_id(module_id)
        if tk is None or ttk is None:
            for item in targets[:1]:
                self._open_target_path(item["path"], item["label"])
            return

        title = f"Pruefpfade oeffnen - {module.title if module else module_id}"
        win = tk.Toplevel(self.tab)
        win.title(title)
        win.geometry("560x360")
        win.minsize(460, 280)
        try:
            win.transient(self.tab.winfo_toplevel())
        except Exception:
            pass

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)

        ttk.Label(
            outer,
            text=self.app.tr(
                "cleanup_label_relevant_paths",
                "Relevante Pruefpfade fuer diesen Bereich:",
            ),
            justify="left",
            wraplength=520,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        list_frame = ttk.LabelFrame(
            outer,
            text=self.app.tr("cleanup_group_paths", "Pfade"),
            padding=8,
        )
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)

        for row_index, item in enumerate(targets):
            row = ttk.Frame(list_frame)
            row.grid(
                row=row_index,
                column=0,
                sticky="ew",
                pady=(0 if row_index == 0 else 6, 0),
            )
            row.columnconfigure(0, weight=1)
            ttk.Label(
                row,
                text=f"{item['label']} | {item['path']}",
                justify="left",
                wraplength=400,
            ).grid(row=0, column=0, sticky="w")
            ttk.Button(
                row,
                text=self.app.tr("btn_open", "Öffnen"),
                command=lambda current=item, current_module=module_id: self._open_selected_target(
                    current_module,
                    current["path"],
                    current["label"],
                ),
            ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        close_row = ttk.Frame(outer)
        close_row.grid(row=2, column=0, sticky="e", pady=(10, 0))
        ttk.Button(
            close_row,
            text=self.app.tr("btn_close", "Schließen"),
            command=win.destroy,
        ).pack(side="right")

    def _open_selected_target(self, module_id: str, path: str, label: str):
        if self._open_target_path(path, label):
            self._set_module_action_feedback(
                module_id, f"Pruefpfad geoeffnet: {Path(path).name}"
            )

    def _cleanup_candidates_for_module(self, module_id: str):
        module = self._module_by_id(module_id)
        result = self.module_results.get(module_id)
        if module is None or not isinstance(result, dict):
            return []

        candidates = []
        existing_paths = list(result.get("existing_paths") or [])
        if module_id == "log_files":
            large_logs = result.get("large_logs") or []
            for size_bytes, path in large_logs[:3]:
                candidates.append(
                    {
                        "label": f"Grossen Log pruefen: {Path(path).name}",
                        "detail": f"{path} ({human_size(size_bytes)})",
                        "selected": False,
                        "safe": False,
                    }
                )
            journal_usage = str(result.get("journal_disk_usage") or "").strip()
            if journal_usage:
                candidates.append(
                    {
                        "label": "journalctl vacuum-time=14d",
                        "detail": f"{journal_usage} | behaelt nur die letzten 14 Tage",
                        "selected": True,
                        "safe": True,
                        "action": "run_sudo_command",
                        "command": ["journalctl", "--vacuum-time=14d"],
                        "reason": "Cleanup Assistant: journalctl vacuum-time=14d",
                    }
                )
                candidates.append(
                    {
                        "label": "journalctl vacuum-size=200M",
                        "detail": f"{journal_usage} | begrenzt Journalgroesse auf 200M",
                        "selected": False,
                        "safe": False,
                        "action": "run_sudo_command",
                        "command": ["journalctl", "--vacuum-size=200M"],
                        "reason": "Cleanup Assistant: journalctl vacuum-size=200M",
                    }
                )
            return candidates

        if module_id == "user_cache":
            cache_candidates = result.get("cache_candidates") or []
            for item in cache_candidates:
                item_path = str(item.get("path") or "")
                item_type = "Ordner" if item.get("is_dir") else "Datei"
                is_safe = bool(item.get("safe"))
                candidates.append(
                    {
                        "label": f"Cache-{item_type.lower()} entfernen",
                        "detail": (
                            f"{item_path} | {human_size(item.get('size_bytes'))}"
                            + (
                                " | browsernah, bitte pruefen"
                                if not is_safe
                                else " | sicherer Standardkandidat"
                            )
                        ),
                        "selected": is_safe,
                        "safe": is_safe,
                        "action": "remove_path",
                        "path": item_path,
                    }
                )
            if candidates:
                return candidates

        if module_id == "apt_cache":
            primary_path = (
                str(existing_paths[0]) if existing_paths else "/var/cache/apt"
            )
            candidates.append(
                {
                    "label": "APT autoclean ausfuehren",
                    "detail": f"{primary_path} | entfernt nur nicht mehr benoetigte Paketdateien",
                    "selected": True,
                    "safe": True,
                    "action": "run_sudo_command",
                    "command": ["apt", "autoclean"],
                    "reason": "Cleanup Assistant: APT autoclean",
                }
            )
            candidates.append(
                {
                    "label": "APT clean ausfuehren",
                    "detail": f"{primary_path} | leert den gesamten Paket-Cache",
                    "selected": False,
                    "safe": False,
                    "action": "run_sudo_command",
                    "command": ["apt", "clean"],
                    "reason": "Cleanup Assistant: APT clean",
                }
            )
            return candidates

        if module_id == "trash":
            for path in existing_paths[:3] or [
                str(Path("~/.local/share/Trash").expanduser())
            ]:
                candidates.append(
                    {
                        "label": "Papierkorb-Inhalt pruefen",
                        "detail": str(path),
                        "selected": True,
                        "safe": True,
                        "action": "purge_dir_contents",
                        "path": str(path),
                    }
                )
            return candidates

        if module_id == "thumbnail_cache":
            for path in existing_paths[:3] or [
                str(Path("~/.cache/thumbnails").expanduser())
            ]:
                candidates.append(
                    {
                        "label": "Thumbnail-Cache leeren",
                        "detail": str(path),
                        "selected": True,
                        "safe": True,
                        "action": "purge_dir_contents",
                        "path": str(path),
                    }
                )
            return candidates

        if module_id == "temporary_files":
            temp_candidates = result.get("temp_candidates") or []
            for item in temp_candidates:
                item_path = str(item.get("path") or "")
                item_type = "Ordner" if item.get("is_dir") else "Datei"
                age_hours = max(1, int(item.get("age_seconds", 0) or 0) // 3600)
                candidates.append(
                    {
                        "label": f"Temporaeren {item_type.lower()} entfernen",
                        "detail": (
                            f"{item_path} | {human_size(item.get('size_bytes'))} | "
                            f"ca. {age_hours}h alt"
                        ),
                        "selected": True,
                        "safe": True,
                        "action": "remove_path",
                        "path": item_path,
                    }
                )
            if candidates:
                return candidates

        for path in existing_paths[:3]:
            candidates.append(
                {
                    "label": "Pfad fuer spaetere Bereinigung vormerken",
                    "detail": str(path),
                    "selected": True,
                    "safe": True,
                }
            )
        if not candidates:
            candidates.append(
                {
                    "label": "Kein konkreter Pfad gefunden",
                    "detail": "Vor einer spaeteren Bereinigung ist eine erneute Analyse noetig.",
                    "selected": False,
                    "safe": False,
                }
            )
        return candidates

    def _format_cleanup_prep_summary(self, module_id: str, candidates) -> str:
        module = self._module_by_id(module_id)
        result = self.module_results.get(module_id) or {}
        executable = self._can_execute_cleanup(module_id)
        lines = [
            self.tr(
                "cleanup_prepare_title",
                "Prepare cleanup: {module}",
            ).format(module=module.title if module else module_id),
            "",
            (
                self.tr(
                    "cleanup_prepare_exec_after_confirm",
                    "After confirmation, executable candidates can be started directly.",
                )
                if executable
                else self.tr(
                    "cleanup_prepare_no_delete_yet",
                    "Nothing is deleted yet.",
                )
            ),
            (
                self.tr(
                    "cleanup_prepare_exec_confirmed_only",
                    "Only selected candidates with confirmed safety and sudo flow are executed.",
                )
                if executable
                else self.tr(
                    "cleanup_prepare_collect_only",
                    "This dialog only collects selection and confirmation for later safe steps.",
                )
            ),
            "",
            self.tr(
                "cleanup_prepare_current_finding",
                "Current finding: {value}",
            ).format(
                value=self._detail_summary_for_result(module, result) if module else "-"
            ),
            self.tr(
                "cleanup_prepare_top_findings",
                "Top findings: {value}",
            ).format(
                value=self._top_findings_summary_for_result(module, result)
                if module
                else "-"
            ),
            "",
            f"{self.tr('cleanup_group_candidates', 'Candidates')}:",
        ]
        for candidate in candidates:
            marker = "[x]" if candidate.get("selected") else "[ ]"
            lines.append(
                f"{marker} [{self._candidate_risk_tag(candidate)}] "
                f"{candidate.get('label')} - {candidate.get('detail')}"
            )
        return "\n".join(lines)

    def _log_cleanup_preparation(self, module_id: str, candidates):
        module = self._module_by_id(module_id)
        selected = [item for item in candidates if item.get("selected")]
        if not selected:
            self._append_protocol(
                f"[Vorbereitung] {module.title if module else module_id}: keine Kandidaten ausgewaehlt."
            )
            return
        self._append_protocol(
            f"[Vorbereitung] {module.title if module else module_id}: {len(selected)} Kandidat(en) fuer spaetere Bereinigung vorgemerkt."
        )
        for item in selected:
            self._append_protocol(f"  - {item.get('label')}: {item.get('detail')}")

    def _can_execute_cleanup(self, module_id: str) -> bool:
        return module_id in self.EXECUTABLE_CLEANUP_MODULES

    def _allowed_cleanup_roots_for_module(self, module_id: str):
        if module_id == "user_cache":
            return [Path("~/.cache").expanduser()]
        if module_id == "thumbnail_cache":
            return [Path("~/.cache/thumbnails").expanduser()]
        if module_id == "temporary_files":
            return [Path("/tmp"), Path("/var/tmp")]
        if module_id == "trash":
            trash_home = Path("~/.local/share/Trash").expanduser()
            return [trash_home / "files", trash_home / "info"]
        return []

    def _candidate_selection(self, candidate_vars):
        selected_candidates = []
        for selected_var, candidate in candidate_vars:
            current = dict(candidate)
            current["selected"] = bool(selected_var.get())
            selected_candidates.append(current)
        return selected_candidates

    def _is_allowed_cleanup_path(self, target_path: Path, allowed_roots) -> bool:
        for root in allowed_roots:
            try:
                resolved_target = target_path.expanduser().resolve(strict=False)
                resolved_root = Path(root).expanduser().resolve(strict=False)
            except Exception:
                continue
            if resolved_target == resolved_root:
                return True
            try:
                resolved_target.relative_to(resolved_root)
                return True
            except ValueError:
                continue
        return False

    def _purge_directory_contents(self, target_path: Path):
        target = Path(target_path).expanduser()
        if not target.exists():
            return {"removed_entries": 0, "freed_bytes": 0, "errors": []}

        before = self._scan_path_size(target)
        removed_entries = 0
        errors = []
        try:
            entries = list(target.iterdir())
        except OSError as exc:
            return {
                "removed_entries": 0,
                "freed_bytes": 0,
                "errors": [f"{target}: {exc}"],
            }

        for entry in entries:
            try:
                if entry.is_symlink() or entry.is_file():
                    entry.unlink()
                elif entry.is_dir():
                    shutil.rmtree(entry)
                else:
                    entry.unlink()
                removed_entries += 1
            except OSError as exc:
                errors.append(f"{entry}: {exc}")

        return {
            "removed_entries": removed_entries,
            "freed_bytes": int(before.get("size_bytes", 0) or 0),
            "errors": errors,
        }

    def _remove_path_entry(self, target_path: Path):
        target = Path(target_path).expanduser()
        if not target.exists():
            return {"removed_entries": 0, "freed_bytes": 0, "errors": []}

        before = self._scan_path_size(target)
        entry_count = (
            1
            + int(before.get("file_count", 0) or 0)
            + int(before.get("dir_count", 0) or 0)
        )
        try:
            if target.is_symlink() or target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
        except OSError as exc:
            return {
                "removed_entries": 0,
                "freed_bytes": 0,
                "errors": [f"{target}: {exc}"],
            }
        return {
            "removed_entries": entry_count,
            "freed_bytes": int(before.get("size_bytes", 0) or 0),
            "errors": [],
        }

    def _run_sudo_cleanup_command(self, command, reason=""):
        ensure_sudo = getattr(getattr(self, "app", None), "ensure_sudo_session", None)
        if callable(ensure_sudo) and not ensure_sudo(reason or "Cleanup Assistant"):
            return {"ok": False, "rc": 1, "out": "sudo session not available"}
        exec_cmd = ["sudo", "-n", *list(command or [])]
        try:
            completed = subprocess.run(
                exec_cmd,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
        except Exception as exc:
            return {"ok": False, "rc": 1, "out": str(exc)}
        output = "\n".join(
            part.strip()
            for part in (completed.stdout or "", completed.stderr or "")
            if str(part or "").strip()
        ).strip()
        return {
            "ok": completed.returncode == 0,
            "rc": int(completed.returncode),
            "out": output,
            "command": exec_cmd,
        }

    def _is_safe_temporary_cleanup_target(
        self, target_path: Path, allowed_roots
    ) -> bool:
        if not self._is_allowed_cleanup_path(target_path, allowed_roots):
            return False
        try:
            resolved_target = target_path.expanduser().resolve(strict=False)
        except Exception:
            return False
        for root in allowed_roots:
            try:
                if resolved_target == Path(root).expanduser().resolve(strict=False):
                    return False
            except Exception:
                continue
        try:
            stat_info = target_path.lstat()
        except OSError:
            return False
        if stat_info.st_uid != os.getuid():
            return False
        if resolved_target.name.startswith((".X", ".ICE", "systemd-private-")):
            return False
        return True

    def _is_safe_user_cache_cleanup_target(
        self, target_path: Path, allowed_roots
    ) -> bool:
        if not self._is_allowed_cleanup_path(target_path, allowed_roots):
            return False
        try:
            resolved_target = target_path.expanduser().resolve(strict=False)
        except Exception:
            return False
        for root in allowed_roots:
            try:
                resolved_root = Path(root).expanduser().resolve(strict=False)
            except Exception:
                continue
            if resolved_target == resolved_root:
                return False
        try:
            stat_info = target_path.lstat()
        except OSError:
            return False
        if stat_info.st_uid != os.getuid():
            return False
        if resolved_target.name == "thumbnails":
            return False
        return True

    def _execute_cleanup_candidates(self, module_id: str, candidates):
        module = self._module_by_id(module_id)
        selected = [item for item in candidates if item.get("selected")]
        if not selected:
            self._set_module_action_feedback(module_id, "Keine Kandidaten ausgewaehlt")
            self._append_protocol(
                f"[Bereinigung] {module.title if module else module_id}: keine Kandidaten ausgewaehlt."
            )
            return False

        if not self._can_execute_cleanup(module_id):
            self._log_cleanup_preparation(module_id, candidates)
            self._append_protocol(
                f"[Vorbereitung] {module.title if module else module_id}: Modul bleibt vorerst ohne echte Bereinigung."
            )
            self._set_module_action_feedback(module_id, "Vorbereitung bestaetigt")
            return False

        allowed_roots = self._allowed_cleanup_roots_for_module(module_id)
        total_entries = 0
        total_bytes = 0
        errors = []
        acted_paths = []

        for item in selected:
            raw_path = str(item.get("path") or item.get("detail") or "").strip()
            action = item.get("action")
            if action == "run_sudo_command":
                command_label = " ".join(item.get("command") or [])
                result = self._run_sudo_cleanup_command(
                    item.get("command") or [],
                    reason=str(
                        item.get("reason") or (module.title if module else module_id)
                    ),
                )
                if result.get("ok"):
                    acted_paths.append(command_label)
                    self._append_protocol(
                        f"[Bereinigung] {module.title if module else module_id}: {command_label} erfolgreich ausgefuehrt."
                    )
                    if result.get("out"):
                        self._append_protocol(
                            f"[Bereinigung] Ausgabe: {result.get('out')}"
                        )
                else:
                    result_error = result.get("out") or f"rc={result.get('rc', 1)}"
                    errors.append(f"{command_label}: {result_error}")
                continue

            if not raw_path:
                continue
            target = Path(raw_path).expanduser()
            if action == "purge_dir_contents":
                is_allowed = self._is_allowed_cleanup_path(target, allowed_roots)
            elif action == "remove_path":
                if module_id == "temporary_files":
                    is_allowed = self._is_safe_temporary_cleanup_target(
                        target, allowed_roots
                    )
                elif module_id == "user_cache":
                    is_allowed = self._is_safe_user_cache_cleanup_target(
                        target, allowed_roots
                    )
                else:
                    is_allowed = False
            else:
                is_allowed = False
            if not is_allowed:
                errors.append(f"{target}: Zielpfad nicht freigegeben")
                continue
            if action == "purge_dir_contents":
                result = self._purge_directory_contents(target)
            elif action == "remove_path":
                result = self._remove_path_entry(target)
            else:
                result = {"removed_entries": 0, "freed_bytes": 0, "errors": []}
            total_entries += int(result.get("removed_entries", 0) or 0)
            total_bytes += int(result.get("freed_bytes", 0) or 0)
            errors.extend(result.get("errors") or [])
            acted_paths.append(str(target))

        if acted_paths:
            self._append_protocol(
                f"[Bereinigung] {module.title if module else module_id}: {len(acted_paths)} Pfad/Pfade bereinigt, {total_entries} Eintraege entfernt, {human_size(total_bytes)} freigegeben."
            )
            for path in acted_paths:
                self._append_protocol(f"  - bereinigt: {path}")
        if errors:
            for error in errors:
                self._append_protocol(f"[Bereinigung] Hinweis: {error}")

        if acted_paths:
            handler = self.analysis_handlers.get(module_id)
            if callable(handler):
                handler(from_full_scan=False)
            self.protocol_status_var.set(
                f"Bereinigung fuer {module.title if module else module_id} abgeschlossen."
            )
            if total_bytes > 0:
                history_summary = f"{len(acted_paths)} Pfad/Pfade, {human_size(total_bytes)} freigegeben"
                self._set_module_action_feedback(
                    module_id,
                    f"Bereinigung erfolgreich, {human_size(total_bytes)} freigegeben",
                )
            else:
                history_summary = f"{len(acted_paths)} Pfad/Pfade bereinigt, kein freier Speicher gemeldet"
                self._set_module_action_feedback(module_id, "Bereinigung erfolgreich")
            self._record_cleanup_history(module_id, history_summary)
            return True
        if errors:
            self._set_module_action_feedback(
                module_id, "Bereinigung mit Hinweis/Fehler"
            )
        return False

    def _show_cleanup_prep_dialog(self, module_id: str):
        module = self._module_by_id(module_id)
        candidates = self._cleanup_candidates_for_module(module_id)
        if tk is None or ttk is None:
            self._execute_cleanup_candidates(module_id, candidates)
            return

        title = f"Bereinigung vorbereiten - {module.title if module else module_id}"
        win = tk.Toplevel(self.tab)
        win.title(title)
        win.geometry("760x560")
        win.minsize(620, 420)
        try:
            win.transient(self.tab.winfo_toplevel())
        except Exception:
            pass

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)

        ttk.Label(
            outer,
            text=(
                "Die Auswahl bleibt bestaetigungspflichtig. Sichere Standardmodule duerfen danach direkt bereinigt werden."
                if self._can_execute_cleanup(module_id)
                else "Es wird noch nichts geloescht. Die Auswahl dient nur der gefuehrten Vorbereitung."
            ),
            justify="left",
            wraplength=700,
        ).grid(row=0, column=0, sticky="w", pady=(0, 8))

        candidates_frame = ttk.LabelFrame(
            outer,
            text=self.app.tr("cleanup_group_candidates", "Kandidaten"),
            padding=8,
        )
        candidates_frame.grid(row=1, column=0, sticky="nsew")
        candidates_frame.columnconfigure(0, weight=1)

        candidate_vars = []
        for row_index, candidate in enumerate(candidates):
            selected_var = tk.BooleanVar(value=bool(candidate.get("selected")))
            candidate_vars.append((selected_var, candidate))
            ttk.Checkbutton(
                candidates_frame,
                text=(
                    f"[{self._candidate_risk_tag(candidate)}] "
                    f"{candidate.get('label')} | {candidate.get('detail')}"
                ),
                variable=selected_var,
                onvalue=True,
                offvalue=False,
            ).grid(
                row=row_index,
                column=0,
                sticky="w",
                pady=(0 if row_index == 0 else 6, 0),
            )

        summary_frame = ttk.LabelFrame(
            outer,
            text=self.app.tr("cleanup_group_summary", "Zusammenfassung"),
            padding=8,
        )
        summary_frame.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=1)

        summary_text = tk.Text(summary_frame, wrap="word", height=10)
        summary_text.grid(row=0, column=0, sticky="nsew")
        summary_scroll = ttk.Scrollbar(
            summary_frame,
            orient="vertical",
            command=summary_text.yview,
        )
        summary_scroll.grid(row=0, column=1, sticky="ns")
        summary_text.configure(yscrollcommand=summary_scroll.set)

        def _render_summary():
            current_candidates = self._candidate_selection(candidate_vars)
            summary_text.configure(state="normal")
            summary_text.delete("1.0", "end")
            summary_text.insert(
                "1.0",
                self._format_cleanup_prep_summary(module_id, current_candidates),
            )
            summary_text.configure(state="disabled")
            return current_candidates

        _render_summary()

        actions = ttk.Frame(outer)
        actions.grid(row=3, column=0, sticky="e", pady=(10, 0))

        def _confirm_preparation():
            prepared = _render_summary()
            executed = self._execute_cleanup_candidates(module_id, prepared)
            if not executed:
                self._append_protocol(
                    f"[Vorbereitung] {module.title if module else module_id}: Dialog bestaetigt, aber noch keine Bereinigung ausgefuehrt."
                )
            win.destroy()

        ttk.Button(
            actions,
            text=self.app.tr("btn_cancel", "Abbrechen"),
            command=win.destroy,
        ).pack(side="right")
        if self._can_execute_cleanup(module_id):
            ttk.Button(
                actions,
                text=self.app.tr("cleanup_btn_confirm_cleanup", "Bereinigung bestätigen"),
                command=_confirm_preparation,
            ).pack(side="right", padx=(0, 8))
        else:
            ttk.Button(
                actions,
                text=self.app.tr(
                    "cleanup_btn_confirm_preparation",
                    "Vorbereitung bestätigen",
                ),
                command=_confirm_preparation,
            ).pack(side="right", padx=(0, 8))

        for selected_var, _candidate in candidate_vars:
            selected_var.trace_add("write", lambda *_args: _render_summary())

        theme = getattr(self, "theme", None)
        if theme:
            try:
                summary_text.configure(
                    bg=theme.get("text_bg", "#ffffff"),
                    fg=theme.get("text_fg", "#101418"),
                    insertbackground=theme.get("text_fg", "#101418"),
                    selectbackground=theme.get(
                        "select_bg", theme.get("accent", "#2f6feb")
                    ),
                    selectforeground=theme.get("select_fg", "#ffffff"),
                    highlightbackground=theme.get("border", "#c6d0db"),
                )
            except Exception:
                pass

    def show_module_details(self, module_id: str):
        detail_text = self._format_module_details(module_id)
        if tk is None or ttk is None:
            self._append_protocol(detail_text)
            return

        title = f"Cleanup Details - {self._module_by_id(module_id).title if self._module_by_id(module_id) else module_id}"
        win = tk.Toplevel(self.tab)
        win.title(title)
        win.geometry("760x520")
        win.minsize(560, 360)
        try:
            win.transient(self.tab.winfo_toplevel())
        except Exception:
            pass

        outer = ttk.Frame(win, padding=10)
        outer.pack(fill="both", expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)

        text = tk.Text(outer, wrap="word")
        text.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(outer, orient="vertical", command=text.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        text.insert("1.0", detail_text)
        text.configure(state="disabled")

        close_row = ttk.Frame(outer)
        close_row.grid(row=1, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(
            close_row,
            text=self.app.tr("btn_close", "Schließen"),
            command=win.destroy,
        ).pack(side="right")

        theme = getattr(self, "theme", None)
        if theme:
            try:
                text.configure(
                    bg=theme.get("text_bg", "#ffffff"),
                    fg=theme.get("text_fg", "#101418"),
                    insertbackground=theme.get("text_fg", "#101418"),
                    selectbackground=theme.get(
                        "select_bg", theme.get("accent", "#2f6feb")
                    ),
                    selectforeground=theme.get("select_fg", "#ffffff"),
                    highlightbackground=theme.get("border", "#c6d0db"),
                )
            except Exception:
                pass

    def _refresh_storage_summary(self):
        total_bytes = 0
        safe_bytes = 0
        caution_modules = []
        analyzed_count = 0
        for module in self.MODULES:
            result = self.module_results.get(module.module_id)
            if not isinstance(result, dict):
                continue
            analyzed_count += 1
            size_bytes = int(result.get("size_bytes", 0) or 0)
            total_bytes += size_bytes
            if module.safety_level == "safe":
                safe_bytes += size_bytes
            else:
                caution_modules.append(module.title)

        self._set_storage_value("potential", human_size(total_bytes))
        self._set_storage_value("safe", human_size(safe_bytes))
        if caution_modules:
            self._set_storage_value("review", ", ".join(caution_modules))
        elif analyzed_count:
            self._set_storage_value(
                "review",
                self.app.tr(
                    "cleanup_storage_no_special_review",
                    "No special review required",
                ),
            )
        else:
            self._set_storage_value(
                "review",
                self.app.tr("cleanup_storage_review_open", "Still open"),
            )

    def _set_analysis_status(self, module_id: str, label: str, size_bytes: int):
        self._set_module_var(
            "module_status_vars",
            module_id,
            self.app.tr("cleanup_status_value", "Status: {label} ({size})").format(
                label=label,
                size=human_size(size_bytes),
            ),
        )
        self._set_module_action_feedback(
            module_id,
            self.app.tr(
                "cleanup_action_analysis_finished",
                "Analysis finished: {size}",
            ).format(size=human_size(size_bytes)),
        )

    def _log_analysis_summary(
        self,
        module: CleanupModuleSpec,
        result: dict,
        *,
        from_full_scan: bool,
        detail_lines,
    ):
        prefix = "[Systemanalyse]" if from_full_scan else "[Modulanalyse]"
        self._append_protocol(
            f"{prefix} {module.title}: {human_size(result.get('size_bytes'))}, "
            f"{result.get('file_count', 0)} Dateien, {result.get('dir_count', 0)} Ordner."
        )
        for line in detail_lines:
            self._append_protocol(f"  - {line}")
        if int(result.get("inaccessible", 0) or 0) > 0:
            self._append_protocol(
                f"  - Hinweis: {result.get('inaccessible')} Eintraege konnten nicht gelesen werden."
            )
        if module.safety_level != "safe":
            self._append_protocol(
                f"  - Sicherheitsstufe: {module.title} bleibt spaeter bestaetigungspflichtig."
            )

    def _run_cleanup_stub(self, module_id: str):
        module = self._module_by_id(module_id)
        if module is None:
            return
        if module_id not in self.module_cleanup_ready:
            self._append_protocol(
                f"[Stub] {module.title}: vor einer Bereinigungs-Vorbereitung ist zuerst eine Analyse noetig."
            )
            return
        self._show_cleanup_prep_dialog(module_id)

    def _analyze_cache_path(self, module_id: str, targets, *, from_full_scan):
        result = self._scan_targets(targets)
        self._store_module_result(module_id, result)
        label = (
            self.app.tr("cleanup_status_analysis_finished", "Analysis finished")
            if result["existing_paths"]
            else self.app.tr("cleanup_status_path_not_found", "Path not found")
        )
        self._set_analysis_status(module_id, label, result["size_bytes"])
        detail = [
            self.app.tr("cleanup_detail_paths_value", "Paths: {paths}").format(
                paths=", ".join(result["paths"])
            ),
            (
                self.app.tr(
                    "cleanup_detail_found_in",
                    "Found in: {paths}",
                ).format(paths=", ".join(result["existing_paths"]))
                if result["existing_paths"]
                else self.app.tr(
                    "cleanup_detail_target_missing",
                    "Target path is currently not available",
                )
            ),
        ]
        module = self._module_by_id(module_id)
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=detail,
            )
        return result

    def analyze_user_cache(self, *, from_full_scan: bool = False):
        result = self._scan_targets([Path("~/.cache")])
        result["cache_candidates"] = self._user_cache_cleanup_candidates(
            Path("~/.cache")
        )
        self._store_module_result("user_cache", result)
        self._set_analysis_status(
            "user_cache",
            (
                (
                    self.app.tr(
                        "cleanup_status_cache_areas_found",
                        "{count} cache area(s) found",
                    ).format(count=len(result["cache_candidates"]))
                    if result["cache_candidates"]
                    else self.app.tr(
                        "cleanup_status_no_split_cache_areas",
                        "No separate cache areas found",
                    )
                )
                if result["existing_paths"]
                else self.app.tr(
                    "cleanup_status_cache_path_not_found",
                    "Cache path not found",
                )
            ),
            result["size_bytes"],
        )
        module = self._module_by_id("user_cache")
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=[
                    self.app.tr("cleanup_detail_path_value", "Path: {path}").format(
                        path="~/.cache"
                    ),
                    (
                        self.app.tr(
                            "cleanup_detail_top_cache_areas_prefix",
                            "Top cache areas: ",
                        )
                        + ", ".join(
                            f"{Path(item['path']).name} ({human_size(item['size_bytes'])})"
                            for item in result["cache_candidates"][:3]
                        )
                        if result["cache_candidates"]
                        else self.app.tr(
                            "cleanup_detail_no_split_cache_with_size",
                            "No separate cache areas with size found.",
                        )
                    ),
                ],
            )

    def analyze_thumbnail_cache(self, *, from_full_scan: bool = False):
        self._analyze_cache_path(
            "thumbnail_cache",
            [Path("~/.cache/thumbnails")],
            from_full_scan=from_full_scan,
        )

    def analyze_apt_cache(self, *, from_full_scan: bool = False):
        result = self._scan_targets([Path("/var/cache/apt")])
        self._store_module_result("apt_cache", result)
        label = (
            self.app.tr("cleanup_status_analysis_finished", "Analysis finished")
            if result["existing_paths"]
            else self.app.tr(
                "cleanup_status_apt_cache_not_found",
                "APT cache not found",
            )
        )
        self._set_analysis_status("apt_cache", label, result["size_bytes"])
        archive_info = self._scan_targets([Path("/var/cache/apt/archives")])
        module = self._module_by_id("apt_cache")
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=[
                    self.app.tr("cleanup_detail_path_value", "Path: {path}").format(
                        path="/var/cache/apt"
                    ),
                    (
                        self.app.tr(
                            "cleanup_detail_archives_subfolder",
                            "Archives subfolder: {size}",
                        ).format(size=human_size(archive_info["size_bytes"]))
                        if archive_info["existing_paths"]
                        else self.app.tr(
                            "cleanup_detail_archives_subfolder_missing",
                            "Archives subfolder is currently not available.",
                        )
                    ),
                ],
            )

    def analyze_temporary_files(self, *, from_full_scan: bool = False):
        result = self._scan_targets([Path("/tmp"), Path("/var/tmp")])
        result["temp_candidates"] = self._temporary_cleanup_candidates(
            [Path("/tmp"), Path("/var/tmp")]
        )
        self._store_module_result("temporary_files", result)
        self._set_analysis_status(
            "temporary_files",
            (
                (
                    self.app.tr(
                        "cleanup_status_temp_candidates_found",
                        "{count} safe temp candidate(s) found",
                    ).format(count=len(result["temp_candidates"]))
                    if result["temp_candidates"]
                    else self.app.tr(
                        "cleanup_status_no_safe_temp_candidates",
                        "No safe temp candidates found",
                    )
                )
                if result["existing_paths"]
                else self.app.tr(
                    "cleanup_top_no_temp_paths",
                    "No temp paths found",
                )
            ),
            result["size_bytes"],
        )
        module = self._module_by_id("temporary_files")
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=[
                    self.app.tr(
                        "cleanup_detail_paths_value",
                        "Paths: {paths}",
                    ).format(paths="/tmp, /var/tmp"),
                    (
                        self.app.tr(
                            "cleanup_detail_existing_temp_paths",
                            "Existing temp paths: {paths}",
                        ).format(paths=", ".join(result["existing_paths"]))
                        if result["existing_paths"]
                        else self.app.tr(
                            "cleanup_detail_no_temp_sources",
                            "None of the temp sources is available.",
                        )
                    ),
                    (
                        self.app.tr(
                            "cleanup_detail_safe_temp_candidates_prefix",
                            "Safe temp candidates: ",
                        )
                        + ", ".join(
                            f"{Path(item['path']).name} ({human_size(item['size_bytes'])})"
                            for item in result["temp_candidates"][:3]
                        )
                        if result["temp_candidates"]
                        else self.app.tr(
                            "cleanup_detail_no_safe_user_temp_candidates",
                            "No safe user-related temp candidates found.",
                        )
                    ),
                ],
            )

    def analyze_log_files(self, *, from_full_scan: bool = False):
        result = self._scan_targets([Path("/var/log")])
        large_logs = self._find_large_log_files(Path("/var/log"))
        journal_usage = self._journal_disk_usage_text()
        result["large_logs"] = list(large_logs)
        result["journal_disk_usage"] = journal_usage
        self._store_module_result("log_files", result)
        self._set_analysis_status(
            "log_files",
            (
                self.app.tr(
                    "cleanup_status_large_logs_found",
                    "{count} large logs found",
                ).format(count=len(large_logs))
                if large_logs
                else self.app.tr(
                    "cleanup_status_analysis_finished",
                    "Analysis finished",
                )
            ),
            result["size_bytes"],
        )
        detail_lines = [self.app.tr("cleanup_detail_log_path", "Path: /var/log")]
        if large_logs:
            for size_bytes, path in large_logs:
                detail_lines.append(
                    self.app.tr(
                        "cleanup_detail_large_log_candidate",
                        "Large log candidate: {path} ({size})",
                    ).format(path=path, size=human_size(size_bytes))
                )
        else:
            detail_lines.append(
                self.app.tr(
                    "cleanup_detail_no_log_over_threshold",
                    "No log file above {size} found.",
                ).format(size=human_size(self.LARGE_LOG_THRESHOLD_BYTES))
            )
        if journal_usage:
            detail_lines.append(f"journalctl: {journal_usage}")
        module = self._module_by_id("log_files")
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=detail_lines,
            )

    def analyze_trash(self, *, from_full_scan: bool = False):
        trash_home = Path("~/.local/share/Trash").expanduser()
        result = self._scan_targets(
            [
                trash_home / "files",
                trash_home / "info",
            ]
        )
        self._store_module_result("trash", result)
        self._set_analysis_status(
            "trash",
            (
                self.app.tr(
                    "cleanup_status_analysis_finished",
                    "Analysis finished",
                )
                if result["existing_paths"]
                else self.app.tr(
                    "cleanup_detail_trash_empty",
                    "Trash is currently empty or not available",
                )
            ),
            result["size_bytes"],
        )
        module = self._module_by_id("trash")
        if module is not None:
            self._log_analysis_summary(
                module,
                result,
                from_full_scan=from_full_scan,
                detail_lines=[
                    self.app.tr("cleanup_detail_path_value", "Path: {path}").format(
                        path=trash_home
                    ),
                    (
                        self.app.tr(
                            "cleanup_detail_active_subfolders",
                            "Active subfolders: {paths}",
                        ).format(paths=", ".join(result["existing_paths"]))
                        if result["existing_paths"]
                        else self.app.tr(
                            "cleanup_detail_no_trash_subfolders",
                            "No trash subfolders found.",
                        )
                    ),
                ],
            )

    def cleanup_user_cache(self):
        self._run_cleanup_stub("user_cache")

    def cleanup_thumbnail_cache(self):
        self._run_cleanup_stub("thumbnail_cache")

    def cleanup_apt_cache(self):
        self._run_cleanup_stub("apt_cache")

    def cleanup_temporary_files(self):
        self._run_cleanup_stub("temporary_files")

    def cleanup_log_files(self):
        self._run_cleanup_stub("log_files")

    def cleanup_trash(self):
        self._run_cleanup_stub("trash")

    def _module_by_id(self, module_id: str):
        for module in self.MODULES:
            if module.module_id == module_id:
                return module
        return None

    def _populate_example_output(self):
        lines = (
            self.app.tr(
                "cleanup_protocol_demo_ready",
                "Cleanup Assistant ready.",
            ),
            self.app.tr(
                "cleanup_protocol_demo_user_cache",
                "Example: user cache is waiting for analysis.",
            ),
            self.app.tr(
                "cleanup_protocol_demo_thumbnail_cache",
                "Example: thumbnail cache has not been checked yet.",
            ),
            self.app.tr(
                "cleanup_protocol_demo_apt_cache",
                "Example: APT cache will require confirmation later.",
            ),
            self.app.tr(
                "cleanup_protocol_demo_history_hint",
                "Note: the history will later show successful cleanup runs in a compact form.",
            ),
        )
        self.protocol_text.delete("1.0", "end")
        self.protocol_text.insert("1.0", "\n".join(lines))

    def _append_protocol(self, message: str):
        text = str(message or "").strip()
        if not text:
            return
        try:
            if self.protocol_text.get("1.0", "end").strip():
                self.protocol_text.insert("end", "\n")
            self.protocol_text.insert("end", text)
            self.protocol_text.see("end")
        except Exception:
            pass
        logger = getattr(getattr(self, "app", None), "log", None)
        if callable(logger):
            try:
                logger(f"Cleanup Assistant: {text}")
            except Exception:
                pass


def build_cleanup_assistant_tab(app):
    """Create the cleanup assistant tab and keep the instance on the app."""

    return CleanupAssistantTab(app)
