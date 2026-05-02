"""Trace tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_trace_tab(app):
    app.tab_trace = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_trace, text=app.tr("tab_trace", "Trace"))

    app.trace_table = ttk.Treeview(
        app.tab_trace,
        columns=("hop", "ip", "rtt", "cc", "org"),
        show="headings",
        height=18,
    )
    app.trace_table.heading("hop", text="Hop")
    app.trace_table.heading("ip", text="IP")
    app.trace_table.heading("rtt", text="RTT (ms)")
    app.trace_table.column("hop", width=60, anchor="center")
    app.trace_table.column("ip", width=260, anchor="w")
    app.trace_table.column("rtt", width=120, anchor="e")
    app.trace_table.column("cc", width=70, anchor="center")
    app.trace_table.column("org", width=220, anchor="w")
    app.trace_table.pack(fill="both", expand=True)
    app.trace_table.heading("cc", text="Land")
    app.trace_table.heading("org", text="Provider")
