"""Tool notebook tab builders for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_basic_tools_tabs(app):
    app.tab_mtr = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_mtr, text=app.tr("tools_tab_mtr", "MTR"))
    mtr_bar = ttk.Frame(app.tab_mtr)
    mtr_bar.pack(fill="x", pady=(0, 6))
    ttk.Button(
        mtr_bar,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=lambda: app.prepare_chad_analysis(
            "MTR Analyse",
            app.mtr_text.get("1.0", "end").strip(),
        ),
    ).pack(side="right")
    app.mtr_text = tk.Text(app.tab_mtr, wrap="word")
    app.mtr_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.mtr_text, "MTR Analyse")

    app.tab_nmap = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_nmap, text=app.tr("tools_tab_nmap", "Nmap"))
    nmap_bar = ttk.Frame(app.tab_nmap)
    nmap_bar.pack(fill="x", pady=(0, 8))
    ttk.Button(
        nmap_bar,
        text=app.tr("btn_clear", "Leeren"),
        command=app.clear_nmap_output,
    ).pack(side="left")
    ttk.Label(
        nmap_bar,
        text=app.tr("label_status", "Status:"),
    ).pack(side="left", padx=(12, 4))
    ttk.Label(nmap_bar, textvariable=app.nmap_status_var).pack(side="left")
    ttk.Label(
        nmap_bar,
        text=app.tr("label_error", "Fehler:"),
    ).pack(side="left", padx=(12, 4))
    ttk.Label(nmap_bar, textvariable=app.nmap_error_var).pack(side="left")
    ttk.Button(
        nmap_bar,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=lambda: app.prepare_chad_analysis(
            "Nmap Analyse",
            app.nmap_text.get("1.0", "end").strip(),
        ),
    ).pack(side="right")

    app.nmap_text = tk.Text(app.tab_nmap, wrap="word")
    app.nmap_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.nmap_text, "Nmap Analyse")

    app.tab_iftop = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_iftop, text=app.tr("tools_tab_iftop", "iftop"))
    iftop_bar = ttk.Frame(app.tab_iftop)
    iftop_bar.pack(fill="x", pady=(0, 6))
    ttk.Button(
        iftop_bar,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=lambda: app.prepare_chad_analysis(
            "iftop Analyse",
            app.iftop_text.get("1.0", "end").strip(),
        ),
    ).pack(side="right")
    app.iftop_text = tk.Text(app.tab_iftop, wrap="word")
    app.iftop_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.iftop_text, "iftop Analyse")

    app.tab_htop = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_htop, text=app.tr("tools_tab_htop", "htop"))
    htop_bar = ttk.Frame(app.tab_htop)
    htop_bar.pack(fill="x", pady=(0, 6))
    ttk.Button(
        htop_bar,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=lambda: app.prepare_chad_analysis(
            "htop Analyse",
            app.htop_text.get("1.0", "end").strip(),
        ),
    ).pack(side="right")
    app.htop_text = tk.Text(app.tab_htop, wrap="word")
    app.htop_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.htop_text, "htop Analyse")
