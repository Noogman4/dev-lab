"""Tool notebook tab builders for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.config.constants import TRACE_TARGETS
    from netmon.ui.tabs.security_tabs import _install_vertical_pane_drag_markers
except (ImportError, ModuleNotFoundError):
    from config.constants import TRACE_TARGETS
    from ui.tabs.security_tabs import _install_vertical_pane_drag_markers


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _text_widget_value(widget) -> str:
    if widget is None:
        return ""
    try:
        return str(widget.get("1.0", "end").strip())
    except Exception:
        return ""


def build_basic_tools_tabs(app):
    app.tab_mtr = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_mtr, text=app.tr("tools_tab_mtr", "MTR"))
    mtr_bar = ttk.LabelFrame(
        app.tab_mtr,
        text=app.tr("tools_group_mtr_actions", "MTR actions"),
        padding=6,
    )
    mtr_bar.pack(fill="x", pady=(0, 6))
    for col in range(3):
        mtr_bar.columnconfigure(col, weight=1)

    app.btn_mtr_start = ttk.Button(
        mtr_bar,
        text=app.tr("btn_start_mtr", "Start MTR"),
        command=app.mtr_async,
    )
    app.btn_mtr_start.grid(row=0, column=0, sticky="w", padx=(0, 8))

    app.mtr_target_combo = ttk.Combobox(
        mtr_bar,
        textvariable=app.mtr_target,
        values=TRACE_TARGETS,
        state="normal",
    )
    app.mtr_target_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8))

    app.btn_mtr_chad = ttk.Button(
        mtr_bar,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=lambda: app.prepare_chad_analysis(
            "MTR analysis",
            _text_widget_value(_app_value(app, "mtr_text")),
        ),
    )
    app.btn_mtr_chad.grid(row=0, column=2, sticky="e")

    app.mtr_summary_var = tk.StringVar(
        value=app.tr(
            "mtr_summary_default",
            "MTR summary will appear here once a run has completed.",
        )
    )
    mtr_summary = ttk.LabelFrame(
        app.tab_mtr,
        text=app.tr("tools_group_mtr_summary", "MTR summary"),
        padding=6,
    )
    mtr_summary.pack(fill="x", pady=(0, 6))
    mtr_summary_frame = ttk.Frame(mtr_summary)
    mtr_summary_frame.pack(fill="x", expand=True)
    mtr_summary_frame.columnconfigure(0, weight=1)
    mtr_summary_frame.rowconfigure(0, weight=1)
    mtr_summary_scroll_y = ttk.Scrollbar(mtr_summary_frame, orient="vertical")
    mtr_summary_scroll_x = ttk.Scrollbar(mtr_summary_frame, orient="horizontal")
    app.mtr_summary_text = tk.Text(
        mtr_summary_frame,
        wrap="none",
        height=6,
        relief="flat",
        bd=0,
        yscrollcommand=mtr_summary_scroll_y.set,
        xscrollcommand=mtr_summary_scroll_x.set,
    )
    app.mtr_summary_text.grid(row=0, column=0, sticky="nsew")
    mtr_summary_scroll_y.configure(command=app.mtr_summary_text.yview)
    mtr_summary_scroll_y.grid(row=0, column=1, sticky="ns")
    mtr_summary_scroll_x.configure(command=app.mtr_summary_text.xview)
    mtr_summary_scroll_x.grid(row=1, column=0, sticky="ew")
    try:
        app.mtr_summary_text.insert("1.0", app.mtr_summary_var.get())
        app.mtr_summary_text.configure(state="disabled")
    except Exception:
        pass

    def _sync_mtr_summary_text(*_args):
        widget = getattr(app, "mtr_summary_text", None)
        if widget is None:
            return
        try:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", app.mtr_summary_var.get())
            widget.configure(state="disabled")
            widget.see("1.0")
        except Exception:
            pass

    app.mtr_summary_var.trace_add("write", _sync_mtr_summary_text)

    mtr_output_frame = ttk.Frame(app.tab_mtr)
    mtr_output_frame.pack(fill="both", expand=True)
    mtr_output_frame.columnconfigure(0, weight=1)
    mtr_output_frame.rowconfigure(0, weight=1)
    mtr_scroll_y = ttk.Scrollbar(mtr_output_frame, orient="vertical")
    mtr_scroll_x = ttk.Scrollbar(mtr_output_frame, orient="horizontal")
    app.mtr_text = tk.Text(
        mtr_output_frame,
        wrap="none",
        yscrollcommand=mtr_scroll_y.set,
        xscrollcommand=mtr_scroll_x.set,
    )
    app.mtr_text.grid(row=0, column=0, sticky="nsew")
    mtr_scroll_y.configure(command=app.mtr_text.yview)
    mtr_scroll_y.grid(row=0, column=1, sticky="ns")
    mtr_scroll_x.configure(command=app.mtr_text.xview)
    mtr_scroll_x.grid(row=1, column=0, sticky="ew")
    app.attach_chad_context_menu(app.mtr_text, "MTR analysis")

    app.tab_nmap = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_nmap, text=app.tr("tools_tab_nmap", "Nmap"))
    nmap_bar = ttk.LabelFrame(
        app.tab_nmap,
        text=app.tr("tools_group_nmap_actions", "Nmap actions"),
        padding=6,
    )
    nmap_bar.pack(fill="x", pady=(0, 8))
    for col in range(5):
        nmap_bar.columnconfigure(col, weight=1 if col in {2, 4} else 0)

    app.btn_nmap_start = ttk.Button(
        nmap_bar,
        text=app.tr("btn_start_scan", "Start scan"),
        command=app.nmap_async,
    )
    app.btn_nmap_start.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
    app.register_feature_button("nmap", app.btn_nmap_start)

    ttk.Label(
        nmap_bar,
        text=app.tr("tools_label_target_selection", "Target selection:"),
    ).grid(row=0, column=1, sticky="w")
    app.nmap_target_combo = ttk.Combobox(
        nmap_bar,
        textvariable=app.nmap_target,
        values=("127.0.0.1", "localhost", *TRACE_TARGETS),
        state="normal",
    )
    app.nmap_target_combo.grid(row=0, column=2, sticky="ew", padx=(0, 8), pady=(0, 6))

    ttk.Label(
        nmap_bar,
        text=app.tr("tools_label_manual_target", "Custom target / IP:"),
    ).grid(
        row=1, column=1, sticky="w", padx=(0, 8)
    )
    app.nmap_target_entry = ttk.Entry(
        nmap_bar,
        textvariable=app.nmap_manual_target_var,
    )
    app.nmap_target_entry.grid(
        row=1, column=2, columnspan=2, sticky="ew", padx=(0, 8), pady=(0, 6)
    )

    ttk.Label(
        nmap_bar,
        text=app.tr("tools_label_profile", "Profil:"),
    ).grid(row=0, column=3, sticky="e", padx=(0, 6))
    app.nmap_preset_tab_combo = ttk.Combobox(
        nmap_bar,
        textvariable=app.nmap_preset,
        values=tuple(app._nmap_preset_options().values()),
        state="readonly",
    )
    app.nmap_preset_tab_combo.grid(row=0, column=4, sticky="ew", pady=(0, 6))

    app.btn_nmap_clear = ttk.Button(
        nmap_bar,
        text=app.tr("btn_clear", "Clear"),
        command=app.clear_nmap_output,
    )
    app.btn_nmap_clear.grid(row=2, column=4, sticky="e", pady=(0, 6))

    ttk.Label(
        nmap_bar,
        text=app.tr("label_status", "Status:"),
    ).grid(row=2, column=0, sticky="w")
    ttk.Label(nmap_bar, textvariable=app.nmap_status_var).grid(
        row=2, column=1, sticky="w", padx=(0, 8)
    )
    ttk.Label(
        nmap_bar,
        text=app.tr("label_error", "Error:"),
    ).grid(row=2, column=2, sticky="w")
    ttk.Label(nmap_bar, textvariable=app.nmap_error_var).grid(
        row=2, column=3, columnspan=2, sticky="w"
    )
    app.btn_nmap_chad = ttk.Button(
        nmap_bar,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=lambda: app.prepare_chad_analysis(
            "Nmap analysis",
            _text_widget_value(_app_value(app, "nmap_text")),
        ),
    )
    app.btn_nmap_chad.grid(row=1, column=4, sticky="e", pady=(0, 6))

    app.nmap_summary_var = tk.StringVar(
        value=app.tr(
            "nmap_summary_default",
            "Nmap summary will appear here once a scan has completed.",
        )
    )
    nmap_summary = ttk.LabelFrame(
        app.tab_nmap,
        text=app.tr("tools_group_nmap_summary", "Nmap summary"),
        padding=6,
    )
    nmap_summary.pack(fill="x", pady=(0, 6))
    nmap_summary_frame = ttk.Frame(nmap_summary)
    nmap_summary_frame.pack(fill="x", expand=True)
    nmap_summary_frame.columnconfigure(0, weight=1)
    nmap_summary_frame.rowconfigure(0, weight=1)
    nmap_summary_scroll_y = ttk.Scrollbar(nmap_summary_frame, orient="vertical")
    nmap_summary_scroll_x = ttk.Scrollbar(nmap_summary_frame, orient="horizontal")
    app.nmap_summary_text = tk.Text(
        nmap_summary_frame,
        wrap="none",
        height=6,
        relief="flat",
        bd=0,
        yscrollcommand=nmap_summary_scroll_y.set,
        xscrollcommand=nmap_summary_scroll_x.set,
    )
    app.nmap_summary_text.grid(row=0, column=0, sticky="nsew")
    nmap_summary_scroll_y.configure(command=app.nmap_summary_text.yview)
    nmap_summary_scroll_y.grid(row=0, column=1, sticky="ns")
    nmap_summary_scroll_x.configure(command=app.nmap_summary_text.xview)
    nmap_summary_scroll_x.grid(row=1, column=0, sticky="ew")
    try:
        app.nmap_summary_text.insert("1.0", app.nmap_summary_var.get())
        app.nmap_summary_text.configure(state="disabled")
    except Exception:
        pass

    def _sync_nmap_summary_text(*_args):
        widget = getattr(app, "nmap_summary_text", None)
        if widget is None:
            return
        try:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", app.nmap_summary_var.get())
            widget.configure(state="disabled")
            widget.see("1.0")
        except Exception:
            pass

    app.nmap_summary_var.trace_add("write", _sync_nmap_summary_text)

    nmap_output_frame = ttk.Frame(app.tab_nmap)
    nmap_output_frame.pack(fill="both", expand=True)
    nmap_output_frame.columnconfigure(0, weight=1)
    nmap_output_frame.rowconfigure(0, weight=1)
    nmap_scroll_y = ttk.Scrollbar(nmap_output_frame, orient="vertical")
    app.nmap_text = tk.Text(
        nmap_output_frame,
        wrap="word",
        yscrollcommand=nmap_scroll_y.set,
    )
    app.nmap_text.grid(row=0, column=0, sticky="nsew")
    nmap_scroll_y.configure(command=app.nmap_text.yview)
    nmap_scroll_y.grid(row=0, column=1, sticky="ns")
    app.attach_chad_context_menu(app.nmap_text, "Nmap analysis")

    app.tab_iftop = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_iftop, text=app.tr("tools_tab_iftop", "iftop"))
    iftop_bar = ttk.LabelFrame(
        app.tab_iftop,
        text=app.tr("tools_group_iftop_actions", "iftop actions"),
        padding=6,
    )
    iftop_bar.pack(fill="x", pady=(0, 6))
    iftop_bar.columnconfigure(1, weight=1)
    iftop_bar.columnconfigure(3, weight=0)
    ttk.Label(
        iftop_bar,
        text=app.tr("tools_label_interface", "Interface:"),
    ).grid(row=0, column=0, sticky="e", padx=(0, 6), pady=(0, 6))
    app.iftop_interface_combo = ttk.Combobox(
        iftop_bar,
        textvariable=app.iftop_interface_var,
        state="readonly",
        values=[],
        width=18,
    )
    app.iftop_interface_combo.grid(
        row=0, column=1, sticky="ew", padx=(0, 12), pady=(0, 6)
    )
    ttk.Label(
        iftop_bar,
        text=app.tr("tools_label_duration", "Dauer:"),
    ).grid(row=0, column=2, sticky="e", padx=(0, 6), pady=(0, 6))
    app.iftop_duration_combo = ttk.Combobox(
        iftop_bar,
        textvariable=app.iftop_duration_var,
        state="readonly",
        values=("10", "20", "30"),
        width=6,
    )
    app.iftop_duration_combo.grid(row=0, column=3, sticky="w", padx=(0, 8), pady=(0, 6))

    iftop_actions = ttk.Frame(iftop_bar)
    iftop_actions.grid(row=1, column=0, columnspan=4, sticky="w")

    app.btn_iftop_snapshot = ttk.Button(
        iftop_actions,
        text=app.tr("btn_live_snapshot", "Live Snapshot"),
        command=app.iftop_async,
    )
    app.btn_iftop_snapshot.pack(side="left", padx=(0, 8))
    app.register_feature_button("iftop", app.btn_iftop_snapshot)
    app.btn_iftop_refresh_interfaces = ttk.Button(
        iftop_actions,
        text=app.tr("btn_refresh_interfaces", "Refresh interfaces"),
        command=app.refresh_iftop_interfaces,
    )
    app.btn_iftop_refresh_interfaces.pack(side="left", padx=(0, 8))
    app.btn_iftop_clear = ttk.Button(
        iftop_actions,
        text=app.tr("btn_clear_display", "Clear display"),
        command=app.clear_iftop_output,
    )
    app.btn_iftop_clear.pack(side="left", padx=(0, 8))
    app.btn_iftop_chad = ttk.Button(
        iftop_actions,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=app.prepare_iftop_chad_analysis,
    )
    app.btn_iftop_chad.pack(side="left")

    app.iftop_summary_var = tk.StringVar(
        value=app.tr(
            "iftop_summary_default",
            "iftop summary will appear here once a snapshot has completed.",
        )
    )
    iftop_summary = ttk.LabelFrame(
        app.tab_iftop,
        text=app.tr("tools_group_iftop_summary", "iftop summary"),
        padding=6,
    )
    iftop_summary.pack(fill="x", pady=(0, 6))
    iftop_summary_frame = ttk.Frame(iftop_summary)
    iftop_summary_frame.pack(fill="x", expand=True)
    iftop_summary_frame.columnconfigure(0, weight=1)
    iftop_summary_frame.rowconfigure(0, weight=1)
    iftop_summary_scroll_y = ttk.Scrollbar(iftop_summary_frame, orient="vertical")
    iftop_summary_scroll_x = ttk.Scrollbar(iftop_summary_frame, orient="horizontal")
    app.iftop_summary_text = tk.Text(
        iftop_summary_frame,
        wrap="none",
        height=6,
        relief="flat",
        bd=0,
        yscrollcommand=iftop_summary_scroll_y.set,
        xscrollcommand=iftop_summary_scroll_x.set,
    )
    app.iftop_summary_text.grid(row=0, column=0, sticky="nsew")
    iftop_summary_scroll_y.configure(command=app.iftop_summary_text.yview)
    iftop_summary_scroll_y.grid(row=0, column=1, sticky="ns")
    iftop_summary_scroll_x.configure(command=app.iftop_summary_text.xview)
    iftop_summary_scroll_x.grid(row=1, column=0, sticky="ew")
    try:
        app.iftop_summary_text.insert("1.0", app.iftop_summary_var.get())
        app.iftop_summary_text.configure(state="disabled")
    except Exception:
        pass

    def _sync_iftop_summary_text(*_args):
        widget = getattr(app, "iftop_summary_text", None)
        if widget is None:
            return
        try:
            widget.configure(state="normal")
            widget.delete("1.0", "end")
            widget.insert("1.0", app.iftop_summary_var.get())
            widget.configure(state="disabled")
            widget.see("1.0")
        except Exception:
            pass

    app.iftop_summary_var.trace_add("write", _sync_iftop_summary_text)

    app.iftop_text = tk.Text(app.tab_iftop, wrap="word")
    app.iftop_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.iftop_text, "iftop analysis")
    app.refresh_iftop_interfaces()

    app.tab_htop = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_htop, text=app.tr("tools_tab_htop", "htop"))
    htop_bar = ttk.LabelFrame(
        app.tab_htop,
        text=app.tr("tools_group_htop_actions", "htop actions"),
        padding=6,
    )
    htop_bar.pack(fill="x", pady=(0, 6))
    htop_bar.columnconfigure(2, weight=1)
    app.btn_htop_snapshot = ttk.Button(
        htop_bar,
        text=app.tr("tools_btn_htop_snapshot", "htop Snapshot"),
        command=app.htop_async,
    )
    app.btn_htop_snapshot.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
    app.btn_htop_refresh = ttk.Button(
        htop_bar,
        text=app.tr("btn_refresh_view", "Refresh view"),
        command=app.htop_async,
    )
    app.btn_htop_refresh.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
    ttk.Label(
        htop_bar,
        text=app.tr("tools_label_source", "Source:"),
    ).grid(row=0, column=2, sticky="e", padx=(0, 6))
    app.htop_source_combo = ttk.Combobox(
        htop_bar,
        textvariable=app.htop_source_var,
        values=("auto", "htop", "top", "ps"),
        state="readonly",
        width=10,
    )
    app.htop_source_combo.grid(row=0, column=3, sticky="w", padx=(0, 8), pady=(0, 6))
    app.btn_htop_clear = ttk.Button(
        htop_bar,
        text=app.tr("btn_clear_display", "Clear display"),
        command=app.clear_htop_output,
    )
    app.btn_htop_clear.grid(row=1, column=0, sticky="w", padx=(0, 8))
    app.btn_htop_copy = ttk.Button(
        htop_bar,
        text=app.tr("btn_copy_selection", "Copy selection"),
        command=app.copy_htop_selection_to_clipboard,
    )
    app.btn_htop_copy.grid(row=1, column=1, sticky="w", padx=(0, 8))
    app.btn_htop_export = ttk.Button(
        htop_bar,
        text=app.tr("btn_export_snapshot", "Export snapshot"),
        command=app.export_htop_snapshot,
    )
    app.btn_htop_export.grid(row=1, column=2, sticky="w", padx=(0, 8))
    app.btn_htop_selected_chad = ttk.Button(
        htop_bar,
        text=app.tr("btn_send_selection_to_chad", "Send selection to Chad"),
        command=app.prepare_selected_htop_process_chad_analysis,
    )
    app.btn_htop_selected_chad.grid(row=1, column=3, sticky="w", padx=(0, 8))
    app.btn_htop_chad = ttk.Button(
        htop_bar,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=app.prepare_htop_chad_analysis,
    )
    app.btn_htop_chad.grid(row=1, column=4, sticky="e")

    app.htop_summary_var = tk.StringVar(
        value=app.tr(
            "htop_summary_default",
            "htop summary will appear here once a snapshot has completed.",
        )
    )
    htop_summary = ttk.LabelFrame(
        app.tab_htop,
        text=app.tr("tools_group_htop_summary", "htop summary"),
        padding=6,
    )
    htop_summary.pack(fill="x", pady=(0, 6))
    ttk.Label(
        htop_summary,
        textvariable=app.htop_summary_var,
        justify="left",
        wraplength=900,
    ).pack(anchor="w", fill="x")

    htop_body = ttk.Frame(app.tab_htop)
    htop_body.pack(fill="both", expand=True)
    htop_body.columnconfigure(0, weight=1)
    htop_body.rowconfigure(0, weight=1)

    app.htop_pane = ttk.Panedwindow(htop_body, orient="vertical")
    app.htop_pane.grid(row=0, column=0, sticky="nsew")
    app.htop_pane_marker = _install_vertical_pane_drag_markers(
        htop_body,
        app.htop_pane,
        min_pane_size=140,
    )

    htop_upper = ttk.Frame(app.htop_pane)
    htop_upper.columnconfigure(0, weight=1)
    htop_upper.rowconfigure(0, weight=1)

    htop_table_frame = ttk.LabelFrame(
        htop_upper,
        text=app.tr("tools_group_process_overview", "Process overview"),
        padding=6,
    )
    htop_table_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
    for col in range(3):
        htop_table_frame.columnconfigure(col, weight=1)
    htop_table_frame.rowconfigure(2, weight=1)
    name_filter_pair = ttk.Frame(htop_table_frame)
    name_filter_pair.grid(row=0, column=0, sticky="ew", padx=(0, 12), pady=(0, 6))
    name_filter_pair.columnconfigure(1, weight=1)
    ttk.Label(
        name_filter_pair,
        text=app.tr("tools_label_name", "Name:"),
    ).grid(
        row=0, column=0, sticky="w", padx=(0, 6)
    )
    app.htop_name_filter_entry = ttk.Entry(
        name_filter_pair,
        textvariable=app.htop_name_filter_var,
    )
    app.htop_name_filter_entry.grid(row=0, column=1, sticky="ew")
    app.htop_name_filter_entry.bind(
        "<KeyRelease>", lambda _event: app.apply_htop_filters()
    )

    user_filter_pair = ttk.Frame(htop_table_frame)
    user_filter_pair.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(0, 6))
    user_filter_pair.columnconfigure(1, weight=1)
    ttk.Label(
        user_filter_pair,
        text=app.tr("tools_label_user", "User:"),
    ).grid(
        row=0, column=0, sticky="w", padx=(0, 6)
    )
    app.htop_user_filter_entry = ttk.Entry(
        user_filter_pair,
        textvariable=app.htop_user_filter_var,
    )
    app.htop_user_filter_entry.grid(row=0, column=1, sticky="ew")
    app.htop_user_filter_entry.bind(
        "<KeyRelease>", lambda _event: app.apply_htop_filters()
    )

    pid_filter_pair = ttk.Frame(htop_table_frame)
    pid_filter_pair.grid(row=0, column=2, sticky="ew", pady=(0, 6))
    pid_filter_pair.columnconfigure(1, weight=1)
    ttk.Label(pid_filter_pair, text=app.tr("tools_label_pid", "PID:")).grid(
        row=0, column=0, sticky="w", padx=(0, 6)
    )
    app.htop_pid_filter_entry = ttk.Entry(
        pid_filter_pair,
        textvariable=app.htop_pid_filter_var,
        width=10,
    )
    app.htop_pid_filter_entry.grid(row=0, column=1, sticky="ew")
    app.htop_pid_filter_entry.bind(
        "<KeyRelease>", lambda _event: app.apply_htop_filters()
    )
    app.htop_only_active_check = ttk.Checkbutton(
        htop_table_frame,
        text=app.tr("htop_check_only_active", "Active only"),
        variable=app.htop_only_active_var,
        command=app.apply_htop_filters,
        onvalue=True,
        offvalue=False,
    )
    app.htop_only_active_check.grid(row=1, column=0, sticky="w", pady=(0, 6))
    app.btn_htop_apply_filters = ttk.Button(
        htop_table_frame,
        text=app.tr("btn_apply_filter", "Apply filter"),
        command=app.apply_htop_filters,
    )
    app.btn_htop_apply_filters.grid(row=1, column=1, sticky="e", padx=(0, 8), pady=(0, 6))
    app.btn_htop_clear_filters = ttk.Button(
        htop_table_frame,
        text=app.tr("btn_clear_filters", "Clear filters"),
        command=app.clear_htop_filters,
    )
    app.btn_htop_clear_filters.grid(row=1, column=2, sticky="e", pady=(0, 6))
    app.htop_table = ttk.Treeview(
        htop_table_frame,
        columns=("pid", "name", "user", "cpu", "mem", "status"),
        show="headings",
        height=10,
    )
    for col, title, width in [
        ("pid", app.tr("tools_label_pid_plain", "PID"), 90),
        ("name", app.tr("tools_label_name_plain", "Name"), 260),
        ("user", app.tr("tools_label_user_plain", "User"), 130),
        ("cpu", app.tr("tools_label_cpu_percent", "%CPU"), 80),
        ("mem", app.tr("tools_label_mem_percent", "%MEM"), 80),
        ("status", app.tr("tools_label_status_plain", "Status"), 100),
    ]:
        app.htop_table.heading(col, text=title)
        app.htop_table.column(col, width=width, anchor="w")
    app.htop_table.grid(row=2, column=0, columnspan=3, sticky="nsew")
    app.attach_htop_tree_context_menu()
    htop_table_scroll = ttk.Scrollbar(
        htop_table_frame,
        orient="vertical",
        command=app.htop_table.yview,
    )
    htop_table_scroll.grid(row=2, column=3, sticky="ns")
    app.htop_table.configure(yscrollcommand=htop_table_scroll.set)
    app.htop_table.bind("<<TreeviewSelect>>", app.on_htop_process_select)

    htop_detail_frame = ttk.LabelFrame(
        htop_upper,
        text=app.tr("tools_group_process_details", "Process details"),
        padding=6,
    )
    htop_detail_frame.grid(row=1, column=0, sticky="ew", pady=(0, 6))
    for idx in range(3):
        htop_detail_frame.columnconfigure(idx, weight=1)
    for idx, (label_text, var_name) in enumerate(
        (
            (app.tr("tools_label_pid_plain", "PID"), "htop_detail_pid_var"),
            (app.tr("tools_label_name_plain", "Name"), "htop_detail_name_var"),
            (app.tr("tools_label_user_plain", "User"), "htop_detail_user_var"),
            (app.tr("tools_label_cpu_percent", "%CPU"), "htop_detail_cpu_var"),
            (app.tr("tools_label_mem_percent", "%MEM"), "htop_detail_mem_var"),
            (app.tr("tools_label_status_plain", "Status"), "htop_detail_status_var"),
        )
    ):
        row = 0 if idx < 3 else 1
        col = idx % 3
        field = ttk.Frame(htop_detail_frame)
        field.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0, 8) if col < 2 else (0, 0),
            pady=(0, 6) if row == 0 else (0, 0),
        )
        field.columnconfigure(0, weight=1)
        ttk.Label(field, text=label_text).pack(anchor="w")
        ttk.Label(field, textvariable=_app_value(app, var_name)).pack(
            anchor="w", fill="x"
        )

    htop_raw_frame = ttk.LabelFrame(
        app.htop_pane,
        text=app.tr("tools_group_raw_data", "Raw data"),
        padding=6,
    )
    htop_raw_frame.columnconfigure(0, weight=1)
    htop_raw_frame.rowconfigure(0, weight=1)
    app.htop_text = tk.Text(htop_raw_frame, wrap="word")
    app.htop_text.grid(row=0, column=0, sticky="nsew")
    htop_raw_scroll = ttk.Scrollbar(
        htop_raw_frame,
        orient="vertical",
        command=app.htop_text.yview,
    )
    htop_raw_scroll.grid(row=0, column=1, sticky="ns")
    app.htop_text.configure(yscrollcommand=htop_raw_scroll.set)
    app.attach_chad_context_menu(app.htop_text, "htop analysis")

    app.htop_pane.add(htop_upper, weight=3)
    app.htop_pane.add(htop_raw_frame, weight=2)

    app.tab_theme_studio = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(
        app.tab_theme_studio,
        text=app.tr("tools_tab_theme_studio", "Theme Studio"),
    )
    app.build_theme_studio_tab()
