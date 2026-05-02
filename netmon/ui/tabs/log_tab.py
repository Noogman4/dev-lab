"""Log tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_log_tab(app):
    app.tab_log = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_log, text=app.tr("tab_log", "Log"))

    log_bar = ttk.Frame(app.tab_log)
    log_bar.pack(fill="x", pady=(0, 8))
    ttk.Button(
        log_bar,
        text=app.tr("btn_clear_log", "Log leeren"),
        command=app.clear_log,
    ).pack(side="right")
    btn_log_chad = ttk.Button(
        log_bar,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=app.prepare_log_selection_chad_analysis,
    )
    btn_log_chad.pack(side="left")
    app.add_tooltip(
        btn_log_chad,
        "Bereitet nur den aktuell markierten Log-Text lokal für den Chad Analyse-Tab vor.",
    )
    btn_preflight_recheck = ttk.Button(
        log_bar,
        text=app.tr("btn_preflight_recheck", "Preflight neu prüfen"),
        command=app.preflight_recheck,
    )
    btn_preflight_recheck.pack(side="right", padx=(0, 8))
    app.add_tooltip(
        btn_preflight_recheck,
        "Führt die Tool-Erkennung erneut aus und aktualisiert aktivierte Buttons sofort.",
    )

    app.log_view_frame = tk.Frame(app.tab_log, bg="#ffffff", highlightthickness=0)
    app.log_view_frame.pack(fill="both", expand=True)

    app.text = tk.Text(
        app.log_view_frame,
        wrap="none",
        font=("Courier", 11),
        foreground="#000000",
        background="#ffffff",
        insertbackground="#000000",
    )
    app.text.pack(fill="both", expand=True)
    app.text.configure(cursor="xterm")
    app.text.bind("<Key>", lambda _e: "break")
    app.text.bind("<<Paste>>", lambda _e: "break")
    app.text.bind("<<Cut>>", lambda _e: "break")
    app.attach_chad_context_menu(app.text, "Log Analyse")

    app.log_overlay_frame = tk.Frame(
        app.log_view_frame, bg="#111111", highlightthickness=0
    )
    app.log_overlay_label = tk.Label(
        app.log_overlay_frame,
        bg="#111111",
        anchor="center",
        justify="center",
    )
    app.log_overlay_label.pack(fill="both", expand=True)

    app.log_overlay_name_var = tk.StringVar(value="")
    app.log_overlay_name_badge = tk.Label(
        app.log_view_frame,
        textvariable=app.log_overlay_name_var,
        fg="#f5f5f5",
        bg="#151515",
        padx=10,
        pady=3,
        relief="flat",
        highlightthickness=1,
        highlightbackground="#333333",
        font=("TkDefaultFont", 10, "bold"),
    )

    app.log_overlay_controls = tk.Frame(app.log_view_frame, bg="#000000", bd=0)
    app.log_overlay_controls.place(relx=1.0, rely=1.0, x=-10, y=-10, anchor="se")

    app.btn_log_overlay_load = ttk.Button(
        app.log_overlay_controls,
        text="Bild auswählen",
        command=app.choose_log_overlay_image,
    )
    app.btn_log_overlay_load.pack(side="left")
    app.add_tooltip(
        app.btn_log_overlay_load,
        "Öffnet den Auswahlbereich für Overlay-Bilder und lässt ihn bis zum manuellen Schließen geöffnet.",
    )

    app.log_overlay_picker_frame = tk.Frame(
        app.log_view_frame,
        bg="#0f0f0f",
        highlightthickness=1,
        highlightbackground="#2a2a2a",
    )
    app.log_overlay_picker_title = tk.Label(
        app.log_overlay_picker_frame,
        text="Bild für Overlay auswählen",
        fg="#e6e6e6",
        bg="#0f0f0f",
        anchor="w",
    )
    app.log_overlay_picker_title.pack(fill="x", padx=8, pady=(6, 4))

    app.log_overlay_picker_list = tk.Listbox(
        app.log_overlay_picker_frame,
        height=8,
        exportselection=False,
        activestyle="none",
        bg="#1a1a1a",
        fg="#f0f0f0",
        selectbackground="#2d4f7c",
        selectforeground="#ffffff",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#3a3a3a",
    )
    app.log_overlay_picker_list.pack(fill="both", expand=True, padx=8)
    app.log_overlay_picker_list.bind(
        "<<ListboxSelect>>", app._on_log_overlay_picker_select
    )

    app.log_overlay_picker_actions = tk.Frame(
        app.log_overlay_picker_frame,
        bg="#0f0f0f",
        bd=0,
    )
    app.log_overlay_picker_actions.pack(fill="x", padx=8, pady=(6, 8))

    app.btn_log_overlay_picker_folder = ttk.Button(
        app.log_overlay_picker_actions,
        text="Ordner...",
        command=app._choose_log_overlay_folder,
    )
    app.btn_log_overlay_picker_folder.pack(side="left")

    app.btn_log_overlay_picker_prev = ttk.Button(
        app.log_overlay_picker_actions,
        text="◀",
        width=3,
        command=lambda: app._step_log_overlay_selection(-1),
    )
    app.btn_log_overlay_picker_prev.pack(side="left", padx=(6, 0))

    app.btn_log_overlay_picker_next = ttk.Button(
        app.log_overlay_picker_actions,
        text="▶",
        width=3,
        command=lambda: app._step_log_overlay_selection(1),
    )
    app.btn_log_overlay_picker_next.pack(side="left", padx=(4, 0))

    app.btn_log_overlay_picker_close = ttk.Button(
        app.log_overlay_picker_actions,
        text="Auswahl schließen",
        command=app.close_log_overlay_picker,
    )
    app.btn_log_overlay_picker_close.pack(side="right")

    app.log_overlay_toggle_text = tk.StringVar(value="Bild")
    app.btn_log_overlay_toggle = ttk.Button(
        app.log_overlay_controls,
        textvariable=app.log_overlay_toggle_text,
        command=app.toggle_log_overlay,
    )
    app.btn_log_overlay_toggle.pack(side="left", padx=(6, 0))
    app.add_tooltip(
        app.btn_log_overlay_toggle,
        "Schaltet zwischen normalem Log und vollständiger Bild-Überlagerung um.",
    )

    app.log_view_frame.bind("<Configure>", app._on_log_overlay_resize)
    app._restore_log_overlay_from_config()
