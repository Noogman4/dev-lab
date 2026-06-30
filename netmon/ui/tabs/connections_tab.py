"""Connections tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.ui.tabs.security_tabs import _install_vertical_pane_drag_markers
except (ImportError, ModuleNotFoundError):
    from ui.tabs.security_tabs import _install_vertical_pane_drag_markers


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _bind_filter_refresh(widget, app):
    widget.bind("<KeyRelease>", lambda _event: app.apply_conn_filter())


def build_connections_tab(app):
    app.tab_conn = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_conn, text=app.tr("tab_connections", "Verbindungen"))

    conn_actions = ttk.LabelFrame(
        app.tab_conn,
        text=app.tr("connections_group_actions", "Connections actions"),
        padding=6,
    )
    conn_actions.pack(fill="x", pady=(0, 6))
    for col in range(3):
        conn_actions.columnconfigure(col, weight=1)

    conn_filter_grid = ttk.Frame(conn_actions)
    conn_filter_grid.grid(row=0, column=0, columnspan=3, sticky="ew")
    for col in range(6):
        if col in {1, 3, 5}:
            conn_filter_grid.columnconfigure(col, weight=1)

    ttk.Label(
        conn_filter_grid,
        text=app.tr("connections_label_freetext", "Free text:"),
    ).grid(
        row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 6)
    )
    app.conn_filter = tk.StringVar(value="")
    app.conn_filter_entry = ttk.Entry(conn_filter_grid, textvariable=app.conn_filter)
    app.conn_filter_entry.grid(row=0, column=1, sticky="ew", padx=(0, 12), pady=(0, 6))

    ttk.Label(
        conn_filter_grid,
        text=app.tr("connections_label_process", "Process:"),
    ).grid(
        row=0, column=2, sticky="w", padx=(0, 6), pady=(0, 6)
    )
    app.conn_process_filter_entry = ttk.Entry(
        conn_filter_grid,
        textvariable=app.conn_process_filter_var,
    )
    app.conn_process_filter_entry.grid(
        row=0, column=3, sticky="ew", padx=(0, 12), pady=(0, 6)
    )

    ttk.Label(conn_filter_grid, text=app.tr("connections_label_pid", "PID:")).grid(
        row=0, column=4, sticky="w", padx=(0, 6), pady=(0, 6)
    )
    app.conn_pid_filter_entry = ttk.Entry(
        conn_filter_grid,
        textvariable=app.conn_pid_filter_var,
        width=10,
    )
    app.conn_pid_filter_entry.grid(
        row=0, column=5, sticky="ew", padx=(0, 12), pady=(0, 6)
    )

    ttk.Label(
        conn_filter_grid,
        text=app.tr("connections_label_state", "State:"),
    ).grid(
        row=1, column=0, sticky="w", padx=(0, 6), pady=(0, 6)
    )
    app.conn_state_filter_entry = ttk.Entry(
        conn_filter_grid,
        textvariable=app.conn_state_filter_var,
        width=12,
    )
    app.conn_state_filter_entry.grid(
        row=1, column=1, sticky="ew", padx=(0, 12), pady=(0, 6)
    )

    for widget in (
        app.conn_filter_entry,
        app.conn_process_filter_entry,
        app.conn_pid_filter_entry,
        app.conn_state_filter_entry,
    ):
        _bind_filter_refresh(widget, app)

    app.conn_only_external_check = ttk.Checkbutton(
        conn_actions,
        text=app.tr("conn_check_only_external", "External only"),
        variable=app.conn_only_external_var,
        command=app.apply_conn_filter,
        onvalue=True,
        offvalue=False,
    )
    app.conn_only_external_check.grid(row=1, column=1, sticky="w", pady=(0, 6))
    app.conn_only_established_check = ttk.Checkbutton(
        conn_actions,
        text=app.tr("conn_check_only_established", "ESTABLISHED only"),
        variable=app.conn_only_established_var,
        command=app.apply_conn_filter,
        onvalue=True,
        offvalue=False,
    )
    app.conn_only_established_check.grid(row=1, column=2, sticky="w", pady=(0, 6))

    app.btn_conn_tab_refresh = ttk.Button(
        conn_actions,
        text=app.tr("btn_refresh_connections", "Refresh connections"),
        command=app.connections_async,
    )
    app.btn_conn_tab_refresh.grid(row=2, column=0, sticky="ew", padx=(0, 8), pady=(0, 6))
    app.btn_conn_tab_arp = ttk.Button(
        conn_actions,
        text=app.tr("btn_arp_table", "ARP table (arp -a)"),
        command=app.arp_async,
    )
    app.btn_conn_tab_arp.grid(row=2, column=1, sticky="ew", padx=(0, 8), pady=(0, 6))
    app.btn_conn_tab_route = ttk.Button(
        conn_actions,
        text=app.tr("btn_route_table", "Routing table (ip route)"),
        command=app.route_async,
    )
    app.btn_conn_tab_route.grid(row=2, column=2, sticky="ew", pady=(0, 6))

    app.btn_conn_tab_refresh_all = ttk.Button(
        conn_actions,
        text=app.tr("btn_refresh_all", "Refresh all"),
        command=app.refresh_all_connections_views,
    )
    app.btn_conn_tab_refresh_all.grid(row=3, column=0, sticky="ew", padx=(0, 8))
    app.btn_conn_tab_apply_filter = ttk.Button(
        conn_actions,
        text=app.tr("btn_apply_filter", "Apply filter"),
        command=app.apply_conn_filter,
    )
    app.btn_conn_tab_apply_filter.grid(row=3, column=1, sticky="ew", padx=(0, 8))
    app.btn_conn_tab_clear_filters = ttk.Button(
        conn_actions,
        text=app.tr("btn_clear_filters", "Clear filters"),
        command=app.clear_conn_filters,
    )
    app.btn_conn_tab_clear_filters.grid(row=3, column=2, sticky="ew")

    conn_bottom_row = ttk.Frame(conn_actions)
    conn_bottom_row.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))
    app.btn_conn_tab_chad = ttk.Button(
        conn_bottom_row,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=app.analyze_connections_with_chad,
    )
    app.btn_conn_tab_chad.pack(side="left", padx=(0, 8))
    app.btn_conn_tab_clear_view = ttk.Button(
        conn_bottom_row,
        text=app.tr("btn_clear_display", "Clear display"),
        command=app.clear_connections_view,
    )
    app.btn_conn_tab_clear_view.pack(side="left")

    conn_summary = ttk.LabelFrame(
        app.tab_conn,
        text=app.tr("connections_group_summary", "Connections summary"),
        padding=6,
    )
    conn_summary.pack(fill="x", pady=(0, 6))
    ttk.Label(
        conn_summary,
        textvariable=app.connections_summary_var,
        justify="left",
        wraplength=900,
    ).pack(anchor="w", fill="x")

    conn_body = ttk.Frame(app.tab_conn)
    conn_body.pack(fill="both", expand=True)
    conn_body.columnconfigure(0, weight=1)
    conn_body.rowconfigure(0, weight=1)

    app.conn_pane = ttk.Panedwindow(conn_body, orient="vertical")
    app.conn_pane.grid(row=0, column=0, sticky="nsew")
    app.conn_pane_marker = _install_vertical_pane_drag_markers(
        conn_body,
        app.conn_pane,
        min_pane_size=160,
    )

    conn_main_frame = ttk.Frame(app.conn_pane)
    conn_main_frame.columnconfigure(0, weight=1)
    conn_main_frame.rowconfigure(0, weight=1)

    conn_table_frame = ttk.Frame(conn_main_frame)
    conn_table_frame.grid(row=0, column=0, sticky="nsew")
    conn_table_frame.columnconfigure(0, weight=1)
    conn_table_frame.rowconfigure(0, weight=1)

    app.conn_table = ttk.Treeview(
        conn_table_frame,
        columns=("proto", "state", "local", "remote", "pid", "proc"),
        show="headings",
        height=18,
    )
    for col, title, width in [
        ("proto", app.tr("connections_col_proto", "Proto"), 70),
        ("state", app.tr("connections_col_state", "State"), 90),
        ("local", app.tr("connections_col_local", "Local"), 220),
        ("remote", app.tr("connections_col_remote", "Remote"), 220),
        ("pid", app.tr("connections_col_pid", "PID"), 70),
        ("proc", app.tr("connections_col_process", "Process"), 160),
    ]:
        app.conn_table.heading(col, text=title)
        app.conn_table.column(col, width=width, anchor="w")
    app.conn_table.column("pid", anchor="center")
    app.conn_table.grid(row=0, column=0, sticky="nsew")
    app.conn_table.bind("<<TreeviewSelect>>", app.on_connection_select)
    app.attach_connections_context_menu()
    conn_table_scroll = ttk.Scrollbar(
        conn_table_frame,
        orient="vertical",
        command=app.conn_table.yview,
    )
    conn_table_scroll.grid(row=0, column=1, sticky="ns")
    app.conn_table.configure(yscrollcommand=conn_table_scroll.set)

    conn_detail_frame = ttk.LabelFrame(
        conn_main_frame,
        text=app.tr("connections_group_details", "Connection details"),
        padding=6,
    )
    conn_detail_frame.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    for idx in range(3):
        conn_detail_frame.columnconfigure(idx, weight=1)

    for col, title, var_name in [
        (0, app.tr("connections_col_proto", "Proto"), "conn_detail_proto_var"),
        (1, app.tr("connections_col_state", "State"), "conn_detail_state_var"),
        (2, app.tr("connections_col_pid", "PID"), "conn_detail_pid_var"),
        (0, app.tr("connections_col_local", "Local"), "conn_detail_local_var"),
        (1, app.tr("connections_col_remote", "Remote"), "conn_detail_remote_var"),
        (2, app.tr("connections_col_process", "Process"), "conn_detail_proc_var"),
    ]:
        row = (
            0
            if title
            in {
                app.tr("connections_col_proto", "Proto"),
                app.tr("connections_col_state", "State"),
                app.tr("connections_col_pid", "PID"),
            }
            else 1
        )
        box = ttk.LabelFrame(conn_detail_frame, text=title, padding=5)
        box.grid(
            row=row,
            column=col,
            sticky="ew",
            padx=(0, 8) if col < 2 else (0, 0),
            pady=(0, 6) if row == 0 else (0, 0),
        )
        ttk.Label(
            box,
            textvariable=_app_value(app, var_name),
            justify="left",
            wraplength=260,
        ).pack(anchor="w", fill="x")

    conn_lower_frame = ttk.Frame(app.conn_pane)
    conn_lower_frame.columnconfigure(0, weight=1)
    conn_lower_frame.rowconfigure(0, weight=1)
    conn_lower_frame.rowconfigure(1, weight=1)

    arp_frame = ttk.LabelFrame(
        conn_lower_frame,
        text=app.tr("connections_group_arp", "ARP Tabelle"),
        padding=8,
    )
    arp_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
    arp_frame.columnconfigure(0, weight=1)
    arp_frame.rowconfigure(1, weight=1)

    app.arp_status_var = tk.StringVar(
        value=app.tr("connections_arp_status_idle", "ARP: noch nicht geladen")
    )
    ttk.Label(
        arp_frame,
        textvariable=app.arp_status_var,
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    app.arp_table = ttk.Treeview(
        arp_frame,
        columns=("host", "ip", "mac", "iface", "type"),
        show="headings",
        height=6,
    )
    for col, title, width in [
        ("host", app.tr("connections_arp_col_host", "Host"), 180),
        ("ip", app.tr("connections_arp_col_ip", "IP"), 140),
        ("mac", app.tr("connections_arp_col_mac", "MAC"), 160),
        ("iface", app.tr("connections_arp_col_iface", "Interface"), 100),
        ("type", app.tr("connections_arp_col_type", "Type"), 90),
    ]:
        app.arp_table.heading(col, text=title)
        app.arp_table.column(col, width=width, anchor="w")
    app.arp_table.grid(row=1, column=0, sticky="nsew")
    arp_scroll = ttk.Scrollbar(
        arp_frame,
        orient="vertical",
        command=app.arp_table.yview,
    )
    arp_scroll.grid(row=1, column=1, sticky="ns")
    app.arp_table.configure(yscrollcommand=arp_scroll.set)

    route_frame = ttk.LabelFrame(
        conn_lower_frame,
        text=app.tr("connections_group_route", "Routing Tabelle"),
        padding=8,
    )
    route_frame.grid(row=1, column=0, sticky="nsew")
    route_frame.columnconfigure(0, weight=1)
    route_frame.rowconfigure(1, weight=1)

    app.route_status_var = tk.StringVar(
        value=app.tr("connections_route_status_idle", "Routing: noch nicht geladen")
    )
    ttk.Label(
        route_frame,
        textvariable=app.route_status_var,
    ).grid(row=0, column=0, sticky="w", pady=(0, 6))

    app.route_table = ttk.Treeview(
        route_frame,
        columns=("dst", "gateway", "iface", "src", "metric"),
        show="headings",
        height=6,
    )
    for col, title, width in [
        ("dst", app.tr("connections_route_col_dst", "Destination"), 160),
        ("gateway", app.tr("connections_route_col_gateway", "Gateway"), 140),
        ("iface", app.tr("connections_route_col_iface", "Interface"), 100),
        ("src", app.tr("connections_route_col_src", "Source"), 140),
        ("metric", app.tr("connections_route_col_metric", "Metric"), 80),
    ]:
        app.route_table.heading(col, text=title)
        app.route_table.column(col, width=width, anchor="w")
    app.route_table.grid(row=1, column=0, sticky="nsew")
    route_scroll = ttk.Scrollbar(
        route_frame,
        orient="vertical",
        command=app.route_table.yview,
    )
    route_scroll.grid(row=1, column=1, sticky="ns")
    app.route_table.configure(yscrollcommand=route_scroll.set)

    app.conn_pane.add(conn_main_frame, weight=3)
    app.conn_pane.add(conn_lower_frame, weight=2)

    app._conn_rows_cache = []
    app._arp_rows_cache = []
    app._route_rows_cache = []
