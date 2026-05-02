"""Connections tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_connections_tab(app):
    app.tab_conn = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_conn, text=app.tr("tab_connections", "Verbindungen"))

    conn_top = ttk.Frame(app.tab_conn)
    conn_top.pack(fill="x", pady=(0, 8))
    ttk.Label(
        conn_top,
        text=app.tr("label_filter_optional", "Filter (optional):"),
    ).pack(side="left")
    app.conn_filter = tk.StringVar(value="")
    app.conn_filter_entry = ttk.Entry(conn_top, textvariable=app.conn_filter)
    app.conn_filter_entry.pack(side="left", fill="x", expand=True, padx=8)
    ttk.Button(
        conn_top,
        text=app.tr("btn_apply_filter", "Filter anwenden"),
        command=app.apply_conn_filter,
    ).pack(side="left")
    ttk.Button(
        conn_top,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=app.analyze_connections_with_chad,
    ).pack(side="left", padx=(8, 0))

    app.conn_table = ttk.Treeview(
        app.tab_conn,
        columns=("proto", "state", "local", "remote", "pid", "proc"),
        show="headings",
        height=18,
    )
    for col, title, width in [
        ("proto", "Proto", 70),
        ("state", "State", 90),
        ("local", "Local", 220),
        ("remote", "Remote", 220),
        ("pid", "PID", 70),
        ("proc", "Process", 160),
    ]:
        app.conn_table.heading(col, text=title)
        app.conn_table.column(col, width=width, anchor="w")
    app.conn_table.column("pid", anchor="center")
    app.conn_table.pack(fill="both", expand=True)
    app.attach_connections_context_menu()

    app._conn_rows_cache = []
