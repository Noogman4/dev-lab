"""System subtab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_system_tab(app):
    app.tab_system = ttk.Frame(app.system_nb, padding=10)
    app.system_nb.add(
        app.tab_system,
        text=app.tr("system_tab_system", "System"),
    )
    app._build_system_tab()
