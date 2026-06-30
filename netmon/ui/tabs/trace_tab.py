"""Trace tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.ui.tabs.security_tabs import _install_vertical_pane_drag_markers
except (ImportError, ModuleNotFoundError):
    from ui.tabs.security_tabs import _install_vertical_pane_drag_markers


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _combo_values(widget) -> tuple:
    if widget is None:
        return ()
    try:
        values = widget.cget("values")
    except Exception:
        values = ()
    return tuple(values or ())


def build_trace_tab(app):
    app.tab_trace = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_trace, text=app.tr("tab_trace", "Trace"))

    trace_bar = ttk.LabelFrame(
        app.tab_trace,
        text=app.tr("trace_group_actions", "Trace Aktionen"),
        padding=6,
    )
    trace_bar.pack(fill="x", pady=(0, 6))
    for col in range(3):
        trace_bar.columnconfigure(col, weight=1)

    trace_form = ttk.Frame(trace_bar)
    trace_form.grid(row=0, column=0, columnspan=3, sticky="w")
    trace_form.columnconfigure(1, weight=1)

    ttk.Label(
        trace_form,
        text=app.tr("trace_label_target_selection", "Zielauswahl:"),
    ).grid(
        row=0, column=0, sticky="e", padx=(0, 8), pady=(0, 6)
    )
    app.trace_tab_target_combo = ttk.Combobox(
        trace_form,
        textvariable=app.trace_target,
        values=_combo_values(_app_value(app, "trace_combo")),
        state="normal",
        width=32,
    )
    app.trace_tab_target_combo.grid(row=0, column=1, sticky="w", pady=(0, 6))

    ttk.Label(
        trace_form,
        text=app.tr("trace_label_manual_target", "Freies Ziel / IP:"),
    ).grid(
        row=1, column=0, sticky="e", padx=(0, 8)
    )
    app.trace_manual_target_entry = ttk.Entry(
        trace_form,
        textvariable=app.trace_manual_target_var,
        width=32,
    )
    app.trace_manual_target_entry.grid(row=1, column=1, sticky="w")

    actions_row = ttk.Frame(trace_bar)
    actions_row.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

    app.trace_hop_lookup_check = ttk.Checkbutton(
        actions_row,
        text=app.tr("check_hop_lookup", "Hop Lookup (Land/Provider)"),
        variable=app.hop_lookup_enabled,
        onvalue=True,
        offvalue=False,
    )
    app.trace_hop_lookup_check.pack(side="left")
    app.btn_trace_tab_start = ttk.Button(
        actions_row,
        text=app.tr("btn_start_trace", "Trace starten"),
        command=app.trace_table_async,
    )
    app.btn_trace_tab_start.pack(side="left", padx=(12, 8))

    app.btn_trace_tab_clear = ttk.Button(
        actions_row,
        text=app.tr("btn_clear_display", "Anzeige leeren"),
        command=app.clear_trace_output,
    )
    app.btn_trace_tab_clear.pack(side="left", padx=(0, 8))
    app.btn_trace_tab_chad = ttk.Button(
        actions_row,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=app.prepare_trace_chad_analysis,
    )
    app.btn_trace_tab_chad.pack(side="left")

    trace_summary = ttk.LabelFrame(
        app.tab_trace,
        text=app.tr("trace_group_summary", "Trace Bewertung"),
        padding=6,
    )
    trace_summary.pack(fill="x", pady=(0, 6))
    ttk.Label(
        trace_summary,
        textvariable=app.trace_summary_var,
        justify="left",
        wraplength=900,
    ).pack(anchor="w", fill="x")

    trace_body = ttk.Frame(app.tab_trace)
    trace_body.pack(fill="both", expand=True)
    trace_body.columnconfigure(0, weight=1)
    trace_body.rowconfigure(0, weight=1)

    app.trace_pane = ttk.Panedwindow(trace_body, orient="vertical")
    app.trace_pane.grid(row=0, column=0, sticky="nsew")
    app.trace_pane_marker = _install_vertical_pane_drag_markers(
        trace_body,
        app.trace_pane,
        min_pane_size=140,
    )

    trace_table_frame = ttk.LabelFrame(
        app.trace_pane,
        text=app.tr("trace_group_hops", "Trace Hops"),
        padding=6,
    )
    trace_table_frame.columnconfigure(0, weight=1)
    trace_table_frame.rowconfigure(0, weight=1)

    app.trace_table = ttk.Treeview(
        trace_table_frame,
        columns=("hop", "ip", "rtt", "cc", "org"),
        show="headings",
        height=18,
    )
    app.trace_table.heading("hop", text=app.tr("trace_col_hop", "Hop"))
    app.trace_table.heading("ip", text=app.tr("trace_col_ip", "IP"))
    app.trace_table.heading("rtt", text=app.tr("trace_col_rtt", "RTT (ms)"))
    app.trace_table.column("hop", width=60, anchor="center")
    app.trace_table.column("ip", width=260, anchor="w")
    app.trace_table.column("rtt", width=120, anchor="e")
    app.trace_table.column("cc", width=70, anchor="center")
    app.trace_table.column("org", width=220, anchor="w")
    app.trace_table.grid(row=0, column=0, sticky="nsew")
    app.trace_table.heading("cc", text=app.tr("trace_col_country", "Land"))
    app.trace_table.heading("org", text=app.tr("trace_col_provider", "Provider"))
    app.attach_simple_tree_context_menu(app.trace_table)
    trace_scroll = ttk.Scrollbar(
        trace_table_frame,
        orient="vertical",
        command=app.trace_table.yview,
    )
    trace_scroll.grid(row=0, column=1, sticky="ns")
    app.trace_table.configure(yscrollcommand=trace_scroll.set)

    trace_raw_frame = ttk.LabelFrame(
        app.trace_pane,
        text=app.tr("trace_group_raw", "Rohdaten / Hinweise"),
        padding=6,
    )
    trace_raw_frame.columnconfigure(0, weight=1)
    trace_raw_frame.rowconfigure(0, weight=1)
    app.trace_text = tk.Text(trace_raw_frame, wrap="word", height=10)
    app.trace_text.grid(row=0, column=0, sticky="nsew")
    app.attach_chad_context_menu(app.trace_text, "Trace Analyse")
    trace_raw_scroll = ttk.Scrollbar(
        trace_raw_frame,
        orient="vertical",
        command=app.trace_text.yview,
    )
    trace_raw_scroll.grid(row=0, column=1, sticky="ns")
    app.trace_text.configure(yscrollcommand=trace_raw_scroll.set)

    app.trace_pane.add(trace_table_frame, weight=3)
    app.trace_pane.add(trace_raw_frame, weight=2)
