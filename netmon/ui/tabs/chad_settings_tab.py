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
