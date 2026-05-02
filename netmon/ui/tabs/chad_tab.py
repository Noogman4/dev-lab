"""Chad tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_chad_tab(app):
    app.tab_chad_analysis = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_chad_analysis, text=app.tr("tab_chad", "Chad"))
    app.build_chad_analysis_tab()
