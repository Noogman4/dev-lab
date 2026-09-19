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
