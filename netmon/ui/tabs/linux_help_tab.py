"""Linux help tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_linux_help_tab(app):
    app.tab_linux_help = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(
        app.tab_linux_help,
        text=app.tr("tools_tab_linux", "Linux"),
    )

    top_info = ttk.LabelFrame(
        app.tab_linux_help,
        text=app.tr("linux_help_group_status", "Status"),
        padding=8,
    )
    top_info.pack(fill="x", pady=(0, 8))
    ttk.Label(
        top_info,
        textvariable=app.linux_help_status_var,
        justify="left",
    ).pack(anchor="w")

    linux_help_main = ttk.Frame(app.tab_linux_help)
    linux_help_main.pack(fill="both", expand=True)
    linux_help_main.columnconfigure(0, weight=0, minsize=260)
    linux_help_main.columnconfigure(1, weight=1)
    linux_help_main.rowconfigure(0, weight=1)

    linux_help_left = ttk.LabelFrame(
        linux_help_main,
        text=app.tr("linux_help_group_commands", "Befehle"),
        padding=8,
    )
    linux_help_left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
    linux_help_left.columnconfigure(0, weight=1)
    linux_help_left.rowconfigure(1, weight=1)

    app.linux_help_category_combo = ttk.Combobox(
        linux_help_left,
        textvariable=app.linux_help_category_var,
        values=[],
        state="readonly",
    )
    app.linux_help_category_combo.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    app.linux_help_category_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: app.refresh_linux_help_list(),
    )

    app.linux_help_listbox = tk.Listbox(
        linux_help_left,
        exportselection=False,
        height=16,
    )
    app.linux_help_listbox.grid(row=1, column=0, sticky="nsew")
    app.linux_help_listbox.bind("<<ListboxSelect>>", app.on_linux_help_select)

    linux_help_right = ttk.Frame(linux_help_main)
    linux_help_right.grid(row=0, column=1, sticky="nsew")
    linux_help_right.columnconfigure(0, weight=1)
    linux_help_right.rowconfigure(4, weight=1)

    info_frame = ttk.LabelFrame(
        linux_help_right,
        text=app.tr("linux_help_group_description", "Beschreibung"),
        padding=8,
    )
    info_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    ttk.Label(
        info_frame,
        textvariable=app.linux_help_desc_var,
        justify="left",
        wraplength=500,
    ).pack(anchor="w")

    risk_frame = ttk.LabelFrame(
        linux_help_right,
        text=app.tr("linux_help_group_risk", "Sicherheitsstufe"),
        padding=8,
    )
    risk_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    risk_row = ttk.Frame(risk_frame)
    risk_row.pack(fill="x")
    app.linux_help_risk_canvas = tk.Canvas(
        risk_row, width=18, height=18, highlightthickness=0
    )
    app.linux_help_risk_canvas.pack(side="left")
    app.linux_help_risk_dot = app.linux_help_risk_canvas.create_oval(
        2, 2, 16, 16, fill="gray"
    )
    ttk.Label(risk_row, textvariable=app.linux_help_risk_var).pack(side="left", padx=8)

    cmd_frame = ttk.LabelFrame(
        linux_help_right,
        text=app.tr("linux_help_group_command", "Befehl"),
        padding=8,
    )
    cmd_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
    ttk.Label(
        cmd_frame,
        textvariable=app.linux_help_command_var,
        justify="left",
        wraplength=500,
    ).pack(anchor="w")

    edit_frame = ttk.LabelFrame(
        linux_help_right,
        text=app.tr("linux_help_group_edit", "Datenpflege vorbereiten"),
        padding=8,
    )
    edit_frame.grid(row=3, column=0, sticky="ew", pady=(0, 8))
    edit_frame.columnconfigure(1, weight=1)
    edit_frame.columnconfigure(3, weight=1)
    ttk.Label(
        edit_frame,
        text=app.tr("linux_help_label_category", "Kategorie"),
    ).grid(row=0, column=0, sticky="w")
    app.linux_help_form_category_combo = ttk.Combobox(
        edit_frame,
        textvariable=app.linux_help_form_category_var,
        values=[],
        state="normal",
    )
    app.linux_help_form_category_combo.grid(row=0, column=1, sticky="ew", padx=(6, 12))
    ttk.Label(
        edit_frame,
        text=app.tr("linux_help_label_name", "Name"),
    ).grid(row=0, column=2, sticky="w")
    ttk.Entry(edit_frame, textvariable=app.linux_help_form_name_var).grid(
        row=0, column=3, sticky="ew", padx=(6, 0)
    )
    ttk.Label(edit_frame, text=app.tr("linux_help_label_shortinfo", "Kurzinfo")).grid(
        row=1, column=0, sticky="w", pady=(6, 0)
    )
    ttk.Entry(edit_frame, textvariable=app.linux_help_form_info_var).grid(
        row=1, column=1, sticky="ew", padx=(6, 12), pady=(6, 0)
    )
    ttk.Label(edit_frame, text=app.tr("linux_help_label_risk", "Risiko")).grid(
        row=1, column=2, sticky="w", pady=(6, 0)
    )
    app.linux_help_form_risk_combo = ttk.Combobox(
        edit_frame,
        textvariable=app.linux_help_form_risk_var,
        values=["safe", "caution", "danger"],
        state="readonly",
    )
    app.linux_help_form_risk_combo.grid(
        row=1, column=3, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    ttk.Label(edit_frame, text=app.tr("linux_help_label_command", "Befehl")).grid(
        row=2, column=0, sticky="w", pady=(6, 0)
    )
    ttk.Entry(edit_frame, textvariable=app.linux_help_form_cmd_var).grid(
        row=2, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    ttk.Label(
        edit_frame,
        text=app.tr("linux_help_label_explanation", "Erklärung"),
    ).grid(row=3, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(edit_frame, textvariable=app.linux_help_form_explanation_var).grid(
        row=3, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    ttk.Label(edit_frame, text=app.tr("linux_help_label_warning", "Warntext")).grid(
        row=4, column=0, sticky="w", pady=(6, 0)
    )
    ttk.Entry(edit_frame, textvariable=app.linux_help_form_warning_var).grid(
        row=4, column=1, columnspan=3, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    ttk.Checkbutton(
        edit_frame,
        text=app.tr("linux_help_check_enabled", "Aktiv"),
        variable=app.linux_help_form_enabled_var,
        onvalue=True,
        offvalue=False,
    ).grid(row=5, column=0, sticky="w", pady=(6, 0))

    notes_frame = ttk.LabelFrame(
        linux_help_right,
        text=app.tr("linux_help_group_notes", "Hinweise"),
        padding=8,
    )
    notes_frame.grid(row=4, column=0, sticky="nsew")
    app.linux_help_text = tk.Text(notes_frame, wrap="word", height=12)
    app.linux_help_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.linux_help_text, "Linux Hilfe Analyse")
    app.linux_help_text.insert(
        "1.0",
        "Hier erscheinen später ausführliche Erklärungen, Hinweise und "
        "Sicherheitsinfos zu Linux-Befehlen.\n\n"
        "Die vollständige Integration des separaten Linux-Befehle-Programms "
        "erfolgt in einem späteren Schritt.",
    )

    btn_frame = ttk.Frame(linux_help_right)
    btn_frame.grid(row=5, column=0, sticky="ew", pady=(8, 0))
    btn_frame.columnconfigure(0, weight=3)
    btn_frame.columnconfigure(1, weight=2)

    manage_frame = ttk.LabelFrame(
        btn_frame,
        text=app.tr("linux_help_group_manage", "Verwaltung"),
        padding=8,
    )
    manage_frame.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    for idx in range(3):
        manage_frame.columnconfigure(idx, weight=1)

    app.btn_linux_help_new = ttk.Button(
        manage_frame,
        text=app.tr("btn_new", "Neu"),
        command=app.linux_help_new_entry,
    )
    app.btn_linux_help_new.grid(row=0, column=0, sticky="ew")
    app.btn_linux_help_edit = ttk.Button(
        manage_frame,
        text=app.tr("btn_edit", "Bearbeiten"),
        command=app.linux_help_edit_selected,
    )
    app.btn_linux_help_edit.grid(row=0, column=1, sticky="ew", padx=(8, 0))
    app.btn_linux_help_delete = ttk.Button(
        manage_frame,
        text=app.tr("btn_delete", "Löschen"),
        command=app.linux_help_delete_selected,
    )
    app.btn_linux_help_delete.grid(row=0, column=2, sticky="ew", padx=(8, 0))
    app.btn_linux_help_save = ttk.Button(
        manage_frame,
        text=app.tr("btn_save", "Speichern"),
        command=app.save_linux_help_data,
    )
    app.btn_linux_help_save.grid(
        row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0)
    )
    app.btn_linux_help_import = ttk.Button(
        manage_frame,
        text=app.tr("btn_import_csv", "CSV importieren"),
        command=app.linux_help_import_csv_dialog,
    )
    app.btn_linux_help_import.grid(row=2, column=0, sticky="ew", pady=(8, 0))
    app.btn_linux_help_export = ttk.Button(
        manage_frame,
        text=app.tr("btn_export_csv", "CSV exportieren"),
        command=app.linux_help_export_csv_dialog,
    )
    app.btn_linux_help_export.grid(
        row=2, column=1, columnspan=2, sticky="ew", padx=(8, 0), pady=(8, 0)
    )

    display_frame = ttk.LabelFrame(
        btn_frame,
        text=app.tr("linux_help_group_display", "Anzeige"),
        padding=8,
    )
    display_frame.grid(row=0, column=1, sticky="ew")
    display_frame.columnconfigure(0, weight=1)

    app.btn_linux_help_send = ttk.Button(
        display_frame,
        text=app.tr("linux_help_btn_send_terminal", "Ins Terminal senden"),
        command=app.send_linux_help_command_to_terminal,
    )
    app.btn_linux_help_send.grid(row=0, column=0, sticky="ew")
    app.btn_linux_help_show = ttk.Button(
        display_frame,
        text=app.tr("linux_help_btn_show_only", "Nur anzeigen"),
        command=app.linux_help_placeholder_action,
    )
    app.btn_linux_help_show.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    app.btn_linux_help_refresh = ttk.Button(
        btn_frame,
        text=app.tr("btn_reload", "Neu laden"),
        command=app.reload_linux_help_data,
    )
    app.btn_linux_help_refresh.grid(
        row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
    )
    app.reload_linux_help_data()
