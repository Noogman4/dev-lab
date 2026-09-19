"""Chad tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.features import chad_controller
except ModuleNotFoundError:
    from features import chad_controller


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


def build_chad_analysis_output(app, chat_layout, light_theme) -> None:
    """Build the Chad output controls, analysis text and chat tags."""
    output_frame = ttk.Frame(chat_layout)
    output_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 2))
    output_frame.columnconfigure(0, weight=1)
    output_frame.rowconfigure(1, weight=1)
    output_head = ttk.Frame(output_frame)
    output_head.grid(row=0, column=0, sticky="ew", pady=(0, 3))
    output_head.columnconfigure(1, weight=1)
    ttk.Label(
        output_head,
        text=app.tr("chad_group_output", "Ausgabe / Analyse / Chatverlauf"),
    ).grid(row=0, column=0, sticky="w")

    output_controls = ttk.Frame(output_head)
    output_controls.grid(row=0, column=2, sticky="e")
    for attr_name, key, fallback, command, width, padding in (
        (
            "btn_chad_clear",
            "chad_btn_clear_analysis",
            "Analyse leeren",
            app.clear_chad_analysis,
            14,
            (0, 18),
        ),
        (
            "btn_chad_save_analysis",
            "chad_btn_save_analysis",
            "Analyse sichern",
            app.save_chad_analysis_to_file,
            13,
            (0, 6),
        ),
        (
            "btn_chad_load_analysis",
            "chad_btn_load_analysis",
            "Analyse einlesen",
            app.load_chad_analysis_from_file,
            14,
            (0, 6),
        ),
    ):
        button = ttk.Button(
            output_controls,
            text=app.tr(key, fallback),
            command=command,
            width=width,
        )
        button.pack(side="right", padx=padding)
        setattr(app, attr_name, button)

    app.chad_output_filter_combo = ttk.Combobox(
        output_controls,
        textvariable=app.chad_output_filter_var,
        state="readonly",
        width=18,
        values=[
            app.tr("chad_filter_all", "Alles"),
            app.tr("chad_filter_answers", "Nur Antworten"),
            app.tr("chad_filter_results", "Results only"),
        ],
    )
    app.chad_output_filter_combo.pack(side="right", padx=(0, 8))
    app.chad_output_filter_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: chad_controller.refresh_chad_output_view(app),
    )
    ttk.Label(
        output_controls,
        text=app.tr("chad_filter_label", "Filter:"),
    ).pack(side="right", padx=(0, 6))

    analysis_body = ttk.Frame(output_frame)
    analysis_body.grid(row=1, column=0, sticky="nsew")
    analysis_body.columnconfigure(0, weight=1)
    analysis_body.rowconfigure(0, weight=1)
    analysis_text_frame = ttk.Frame(analysis_body)
    analysis_text_frame.grid(row=0, column=0, sticky="nsew")
    analysis_text_frame.columnconfigure(0, weight=1)
    analysis_text_frame.rowconfigure(0, weight=1)
    analysis_scroll = ttk.Scrollbar(analysis_text_frame, orient="vertical")
    analysis_scroll.grid(row=0, column=1, sticky="ns")
    app.chad_analysis_text = tk.Text(
        analysis_text_frame,
        wrap="word",
        height=18,
        yscrollcommand=analysis_scroll.set,
    )
    app.chad_analysis_text.grid(row=0, column=0, sticky="nsew")
    analysis_scroll.configure(command=app.chad_analysis_text.yview)

    def activate_analysis_scroll(_event=None):
        try:
            app.chad_analysis_text.focus_force()
        except Exception:
            pass

    app.chad_analysis_text.bind("<Button-1>", activate_analysis_scroll, add="+")
    for tag_name in (
        "chat_user_header",
        "chat_assistant_header",
        "chat_system_header",
    ):
        app.chad_analysis_text.tag_configure(
            tag_name,
            font=("TkDefaultFont", 10, "bold"),
            spacing1=8,
            spacing3=2,
        )
    for tag_name in (
        "chat_user_body",
        "chat_assistant_body",
        "chat_system_body",
    ):
        app.chad_analysis_text.tag_configure(
            tag_name,
            lmargin1=14,
            lmargin2=14,
            spacing3=6,
        )
    app.chad_analysis_text.tag_configure("chat_spacer", spacing3=4)
    app._apply_chad_chat_theme(app._app_theme or light_theme)
    app.chad_analysis_text.configure(state="disabled")
