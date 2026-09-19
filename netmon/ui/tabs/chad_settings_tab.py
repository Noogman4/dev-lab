"""Chad settings tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_chad_settings_tab(app):
    app.tab_chad_settings = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_chad_settings,
        text=app.tr("tab_chad_settings", "Chad Einstellungen"),
    )
    app.build_chad_settings_tab()


def build_chad_settings_summary(app, frame) -> None:
    """Build the Chad system summary and recent analysis history."""
    summary = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_system_summary", "Systembewertung"),
        padding=8,
    )
    summary.pack(fill="x", pady=(0, 6))
    summary_top = ttk.Frame(summary)
    summary_top.pack(fill="x")
    app.chad_settings_summary_indicator_label = tk.Label(
        summary_top,
        text="●",
        fg="#2e7d32",
        font=("TkDefaultFont", 12, "bold"),
    )
    app.chad_settings_summary_indicator_label.pack(side="left")
    ttk.Label(
        summary_top,
        textvariable=app.chad_settings_summary_state_var,
        font=("TkDefaultFont", 10, "bold"),
    ).pack(side="left", padx=(6, 0))

    summary_grid = ttk.Frame(summary)
    summary_grid.pack(fill="x", pady=(8, 0))
    summary_grid.columnconfigure(1, weight=1)
    summary_grid.columnconfigure(3, weight=1)
    for row, label_key, fallback, value_var, column in (
        (
            0,
            "chad_settings_label_critical",
            "Kritisch:",
            app.chad_settings_summary_critical_var,
            0,
        ),
        (
            0,
            "chad_settings_label_warnings",
            "Warnungen:",
            app.chad_settings_summary_warning_var,
            2,
        ),
        (
            1,
            "chad_settings_label_notices",
            "Hinweise:",
            app.chad_settings_summary_notice_var,
            0,
        ),
        (1, "chad_settings_label_info", "Info:", app.chad_settings_summary_info_var, 2),
    ):
        pady = (4, 0) if row else 0
        ttk.Label(summary_grid, text=app.tr(label_key, fallback)).grid(
            row=row, column=column, sticky="w", pady=pady
        )
        ttk.Label(summary_grid, textvariable=value_var).grid(
            row=row,
            column=column + 1,
            sticky="w",
            padx=(8, 18 if column == 0 else 0),
            pady=pady,
        )

    recent = ttk.LabelFrame(
        summary,
        text=app.tr("chad_settings_group_recent", "Letzte Analysen"),
        padding=8,
    )
    recent.pack(fill="x", pady=(6, 0))
    for column, weight in enumerate((2, 2, 1, 1, 1)):
        recent.columnconfigure(column, weight=weight)
    for column, key, fallback in (
        (0, "chad_settings_recent_header_timestamp", "Datum/Uhrzeit"),
        (1, "chad_settings_recent_header_type", "Analyseart"),
        (2, "chad_settings_recent_header_status", "Status"),
        (3, "chad_settings_recent_header_warnings", "Warn."),
        (4, "chad_settings_recent_header_critical", "Krit."),
    ):
        ttk.Label(
            recent,
            text=app.tr(key, fallback),
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=0, column=column, sticky="w", padx=(8, 0) if column else 0)
    for row_index, row_vars in enumerate(
        app.chad_settings_recent_analysis_rows, start=1
    ):
        for column, key in enumerate(
            ("timestamp_var", "type_var", "status_var", "warning_var", "critical_var")
        ):
            ttk.Label(recent, textvariable=row_vars[key]).grid(
                row=row_index,
                column=column,
                sticky="w",
                padx=(8, 0) if column else 0,
                pady=(4, 0),
            )


def build_chad_settings_connection(app, frame) -> None:
    """Build API key, model selection and Chad connection controls."""
    connection = ttk.LabelFrame(
        frame,
        text=app.tr("settings_group_chad_openai", "Chad Analyse / OpenAI"),
        padding=8,
    )
    connection.pack(fill="x", pady=(0, 6))
    for key, fallback, variable, padding in (
        (
            "settings_auto_switch_to_chad",
            "Beim Senden an Chad automatisch zum Chad-Tab wechseln",
            app.var_auto_switch_to_chad,
            None,
        ),
        (
            "settings_chad_preview_popup",
            "Vorschau-Popup bei Chad-Analyse anzeigen",
            app.var_chad_preview_popup,
            (4, 0),
        ),
    ):
        check = ttk.Checkbutton(
            connection, text=app.tr(key, fallback), variable=variable
        )
        if padding is None:
            check.pack(anchor="w")
        else:
            check.pack(anchor="w", pady=padding)

    api_row = ttk.Frame(connection)
    api_row.pack(fill="x", pady=(6, 0))
    ttk.Label(api_row, text=app.tr("chad_label_api_key", "API Key:")).pack(side="left")
    app.openai_api_key_entry = ttk.Entry(
        api_row,
        textvariable=app.openai_api_key_var,
        show="*",
        width=40,
    )
    app.openai_api_key_entry.pack(side="left", padx=(6, 6), fill="x", expand=True)
    for sequence in ("<Control-v>", "<Control-V>", "<Shift-Insert>"):
        app.openai_api_key_entry.bind(sequence, app.paste_api_key_from_clipboard)
    for attr_name, key, fallback, command in (
        ("btn_chad_api_save", "btn_save", "Speichern", app.save_ai_config),
        ("btn_chad_api_load", "btn_load", "Laden", app.load_ai_config),
        ("btn_chad_api_clear", "btn_clear", "Leeren", app.clear_api_key),
        ("btn_chad_api_delete", "btn_delete", "Delete", app.delete_saved_api_key),
    ):
        button = ttk.Button(
            api_row,
            text=app.tr(key, fallback),
            command=command,
            width=9,
        )
        button.pack(side="left", padx=(6, 0))
        setattr(app, attr_name, button)

    model_row = ttk.Frame(connection)
    model_row.pack(fill="x", pady=(8, 0))
    ttk.Label(
        model_row,
        text=app.tr("chad_settings_label_model", "Modell:"),
    ).pack(side="left")
    app.chad_model_combo = ttk.Combobox(
        model_row,
        textvariable=app.chad_model_var,
        values=app.chad_model_choices,
        state="readonly",
        width=18,
    )
    app.chad_model_combo.pack(side="left", padx=(6, 0))
    app.chad_model_combo.bind("<<ComboboxSelected>>", app.apply_chad_model_selection)
    ttk.Label(
        connection,
        textvariable=app.chad_analysis_status_var,
        justify="left",
    ).pack(anchor="w", pady=(8, 0))


def build_chad_settings_status(app, frame) -> None:
    """Build the current Chad API and analysis status panel."""
    status = ttk.LabelFrame(frame, text="KI Status", padding=8)
    status.pack(fill="x", pady=(0, 6))
    status.columnconfigure(1, weight=1)
    for row, key, fallback, value_var in (
        (
            0,
            "chad_settings_label_api_connected_status",
            "API verbunden Status:",
            app.chad_settings_api_status_var,
        ),
        (
            1,
            "chad_settings_label_model_name",
            "Modellname:",
            app.chad_settings_model_var,
        ),
        (
            2,
            "chad_settings_label_latency",
            "Antwortzeit:",
            app.chad_settings_latency_var,
        ),
        (
            3,
            "chad_settings_label_last_analysis",
            "Letzte Analyse:",
            app.chad_settings_last_analysis_var,
        ),
        (
            4,
            "chad_settings_label_token_usage",
            "Tokenverbrauch:",
            app.chad_settings_tokens_var,
        ),
    ):
        pady = (4, 0) if row else 0
        ttk.Label(status, text=app.tr(key, fallback)).grid(
            row=row, column=0, sticky="w", pady=pady
        )
        ttk.Label(status, textvariable=value_var).grid(
            row=row, column=1, sticky="w", padx=(8, 0), pady=pady
        )


def build_chad_settings_profiles(app, frame) -> None:
    """Build the Chad profile and analysis mode selectors."""
    chad_profile = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_profile", "Chad profile"),
        padding=8,
    )
    chad_profile.pack(fill="x", pady=(0, 6))
    app._build_two_col_toggle_grid(
        chad_profile,
        [
            (
                app.tr("chad_settings_profile_beginner", "Anfängerprofil"),
                "beginner",
                app.apply_chad_profile,
            ),
            (
                app.tr("chad_settings_profile_security", "Sicherheitsfokus"),
                "security",
                app.apply_chad_profile,
            ),
            (
                app.tr("chad_settings_profile_network", "Network focus"),
                "network",
                app.apply_chad_profile,
            ),
            (
                app.tr("chad_settings_profile_expert", "Expertenprofil"),
                "expert",
                app.apply_chad_profile,
            ),
            (
                app.tr("chad_settings_profile_custom", "Benutzerdefiniert"),
                "custom",
                app.apply_chad_profile,
            ),
        ],
        is_radio=True,
        variable=app.chad_profile_var,
    )
    analysis_mode = ttk.LabelFrame(frame, text="Analysemodus", padding=8)
    analysis_mode.pack(fill="x", pady=(0, 6))
    app._build_two_col_toggle_grid(
        analysis_mode,
        [
            (
                app.tr("chad_settings_mode_beginner", "Anfänger"),
                "beginner",
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_mode_standard", "Standard"),
                "standard",
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_mode_expert", "Experte"),
                "expert",
                app.mark_chad_profile_custom,
            ),
        ],
        is_radio=True,
        variable=app.chad_analysis_mode_var,
    )


def build_chad_settings_analysis_filter(app, frame) -> None:
    """Build the Chad analysis filter controls."""
    analysis_filter = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_analysis_filter", "Analyse Filter"),
        padding=8,
    )
    analysis_filter.pack(fill="x", pady=(0, 6))

    def mark_dev_environment_filter_custom() -> None:
        app._update_chad_controls_state()
        app.mark_chad_profile_custom()

    app._build_two_col_toggle_grid(
        analysis_filter,
        [
            (
                app.tr("chad_settings_filter_relevant", "Nur relevante Warnungen"),
                app.chad_filter_relevant_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_filter_critical", "Nur kritische Warnungen"),
                app.chad_filter_critical_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_filter_recommendations",
                    "Handlungsempfehlungen anzeigen",
                ),
                app.chad_filter_recommendations_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_filter_beginner", "Anfängerfreundliche Erklärungen"
                ),
                app.chad_filter_beginner_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_filter_rawdata", "Rohdaten anhängen"),
                app.chad_filter_rawdata_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_filter_technical", "Technische Details anzeigen"),
                app.chad_filter_technical_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_filter_hide_normal_services",
                    "Normale Systemdienste ausblenden",
                ),
                app.chad_filter_hide_normal_services_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_filter_ignore_harmless_processes",
                    "Bekannte harmlose Prozesse ignorieren",
                ),
                app.chad_filter_ignore_harmless_processes_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_filter_ignore_dev_environment",
                    "VS Code-, Codex- und Docker-Hinweise minimieren",
                ),
                app.chad_filter_ignore_dev_environment_var,
                mark_dev_environment_filter_custom,
            ),
        ],
    )


def build_chad_settings_focus(app, frame) -> None:
    """Build the Chad analysis focus controls."""
    focus = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_focus", "Analyse Schwerpunkte"),
        padding=8,
    )
    focus.pack(fill="x", pady=(0, 6))
    app._build_two_col_toggle_grid(
        focus,
        [
            (
                app.tr("chad_settings_focus_security", "Sicherheitsanalyse"),
                app.chad_focus_security_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_dns", "DNS Analyse"),
                app.chad_focus_dns_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_network", "Network analysis"),
                app.chad_focus_network_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_process", "Prozessanalyse"),
                app.chad_focus_process_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_firewall", "Firewall Analyse"),
                app.chad_focus_firewall_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_performance", "Performance Analyse"),
                app.chad_focus_performance_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_optimization", "Systemoptimierung"),
                app.chad_focus_optimization_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_focus_rootkit", "Rootkit Hinweise priorisieren"),
                app.chad_focus_rootkit_var,
                app.mark_chad_profile_custom,
            ),
        ],
    )


def build_chad_settings_systemcheck_profiles(app, frame) -> None:
    """Build the Chad systemcheck profile selector."""
    profile = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_systemcheck", "System check profiles"),
        padding=8,
    )
    profile.pack(fill="x", pady=(0, 6))
    app._build_two_col_toggle_grid(
        profile,
        [
            (
                app.tr("chad_settings_systemcheck_quick", "Schnellcheck"),
                "quick",
                app.apply_chad_systemcheck_profile,
            ),
            (
                app.tr("chad_settings_systemcheck_security", "Sicherheitscheck"),
                "security",
                app.apply_chad_systemcheck_profile,
            ),
            (
                app.tr("chad_settings_systemcheck_network", "Network check"),
                "network",
                app.apply_chad_systemcheck_profile,
            ),
            (
                app.tr("chad_settings_systemcheck_full", "Komplettanalyse"),
                "full",
                app.apply_chad_systemcheck_profile,
            ),
            (
                app.tr("chad_settings_systemcheck_custom", "Benutzerdefiniert"),
                "custom",
                app.apply_chad_systemcheck_profile,
            ),
        ],
        is_radio=True,
        variable=app.chad_systemcheck_profile_var,
    )


def build_chad_settings_answer_style(app, frame) -> None:
    """Build the Chad answer style controls."""
    answer = ttk.LabelFrame(
        frame,
        text=app.tr("chad_settings_group_answer_style", "KI Antwortverhalten"),
        padding=8,
    )
    answer.pack(fill="x", pady=(0, 6))
    app._build_two_col_toggle_grid(
        answer,
        [
            (
                app.tr("chad_settings_answer_short", "Kurze Antworten bevorzugen"),
                app.chad_answer_short_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_answer_detailed", "Ausführliche Analyse"),
                app.chad_answer_detailed_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_answer_step", "Schritt-für-Schritt-Erklärungen"),
                app.chad_answer_step_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_answer_linux_help", "Linux-Befehle erklären"),
                app.chad_answer_linux_help_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr("chad_settings_answer_risk", "Risiko-Einstufung anzeigen"),
                app.chad_answer_risk_var,
                app.mark_chad_profile_custom,
            ),
            (
                app.tr(
                    "chad_settings_answer_recommendations", "Empfehlungen priorisieren"
                ),
                app.chad_answer_recommendations_var,
                app.mark_chad_profile_custom,
            ),
        ],
    )


def build_chad_settings_content(app) -> None:
    """Build all Chad settings content inside the application's tab."""
    frame = ttk.Frame(app.tab_chad_settings, padding=12)
    frame.pack(fill="both", expand=True)
    build_chad_settings_summary(app, frame)
    build_chad_settings_connection(app, frame)
    build_chad_settings_status(app, frame)
    build_chad_settings_profiles(app, frame)
    build_chad_settings_analysis_filter(app, frame)
    build_chad_settings_focus(app, frame)
    build_chad_settings_systemcheck_profiles(app, frame)
    build_chad_settings_answer_style(app, frame)
