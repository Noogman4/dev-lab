"""Settings tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_settings_tab(app):
    app.tab_settings = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_settings,
        text=app.tr("tab_settings", "Einstellungen"),
    )
    app.build_settings_tab()
