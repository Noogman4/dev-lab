"""Chad settings tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_chad_settings_tab(app):
    app.tab_chad_settings = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_chad_settings,
        text=app.tr("tab_chad_settings", "Chad Einstellungen"),
    )
    app.build_chad_settings_tab()
