"""Chad tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_chad_tab(app):
    app.tab_chad_analysis = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_chad_analysis, text=app.tr("tab_chad", "Chad"))
    app.build_chad_analysis_tab()


def build_chad_analysis_header_and_composer(app):
    """Build the Chad analysis header and message composer."""
    app.tab_chad_analysis.columnconfigure(0, weight=1)
    app.tab_chad_analysis.rowconfigure(2, weight=1)

    top = ttk.Frame(app.tab_chad_analysis)
    top.grid(row=0, column=0, sticky="ew", pady=(0, 3))
    top.columnconfigure(1, weight=1)
    ttk.Label(
        top,
        text=app.tr("chad_title", "Chad Analyse"),
        font=("TkDefaultFont", 12, "bold"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(top, textvariable=app.chad_analysis_status_var).grid(
        row=0, column=1, sticky="w", padx=(12, 0)
    )
    app.chad_enabled_check = ttk.Checkbutton(
        top,
        text=app.tr("chad_check_enabled", "Chad-Anbindung aktiv"),
        variable=app.chad_enabled_var,
        onvalue=True,
        offvalue=False,
        command=app._update_chad_controls_state,
    )
    app.chad_enabled_check.grid(row=0, column=2, sticky="e")

    ttk.Label(
        app.tab_chad_analysis,
        textvariable=app.chad_dev_filter_status_var,
    ).grid(row=1, column=0, sticky="ew", pady=(0, 3))

    chat_layout = ttk.Frame(app.tab_chad_analysis)
    chat_layout.grid(row=2, column=0, sticky="nsew")
    chat_layout.columnconfigure(0, weight=1)
    chat_layout.rowconfigure(1, weight=1)

    composer_frame = ttk.Frame(chat_layout)
    composer_frame.grid(row=0, column=0, sticky="ew", pady=(0, 3))
    composer_frame.columnconfigure(0, weight=1)
    app.btn_chad_import_file = ttk.Button(
        composer_frame,
        text=app.tr("chad_btn_import_file", "Insert file"),
        command=app.import_file_to_chad_chat,
    )
    app.btn_chad_import_file.grid(row=0, column=0, sticky="w", padx=(0, 3))
    app.btn_chad_online = ttk.Button(
        composer_frame,
        text=app.tr("chad_btn_online_analysis", "Online analysieren"),
        command=app.run_chad_online_analysis,
    )
    app.btn_chad_online.grid(row=0, column=1, sticky="w", padx=(0, 6))

    composer_input_frame = ttk.Frame(composer_frame)
    composer_input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
    composer_input_frame.columnconfigure(0, weight=1)
    composer_input_frame.rowconfigure(0, weight=1)
    composer_input_scroll = ttk.Scrollbar(composer_input_frame, orient="vertical")
    composer_input_scroll.grid(row=0, column=1, sticky="ns")
    app.chad_chat_input = tk.Text(
        composer_input_frame,
        wrap="word",
        height=6,
        yscrollcommand=composer_input_scroll.set,
    )
    app.chad_chat_input.grid(row=0, column=0, sticky="ew")
    composer_input_scroll.configure(command=app.chad_chat_input.yview)
    app.chad_chat_input.bind(
        "<Return>",
        lambda _event: app.send_chad_chat_message(),
    )
    app.chad_chat_input.bind(
        "<KP_Enter>",
        lambda _event: app.send_chad_chat_message(),
    )
    app.attach_copy_paste_context_menu(app.chad_chat_input)
    return chat_layout
