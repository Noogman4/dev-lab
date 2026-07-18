"""Linux command database tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.ui.tabs.security_tabs import _install_vertical_pane_drag_markers
except (ImportError, ModuleNotFoundError):
    from ui.tabs.security_tabs import _install_vertical_pane_drag_markers


def _bind_if_callable(widget, sequence: str, callback, *, add=None):
    if not callable(callback):
        return False
    widget.bind(sequence, callback, add=add)
    return True


def _bind_refresh_linux_help(widget, app, sequence: str):
    return _bind_if_callable(
        widget,
        sequence,
        lambda _event: app.refresh_linux_help_list(),
    )


def build_linux_help_tab(app):
    app.tab_linux_help = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(
        app.tab_linux_help,
        text=app.tr("tools_tab_linux", "Linux"),
    )
    app.tab_linux_help.columnconfigure(0, weight=1)
    app.tab_linux_help.rowconfigure(2, weight=1)

    status_frame = ttk.LabelFrame(
        app.tab_linux_help,
        text=app.tr("linux_help_group_status", "NetMon Linux command database"),
        padding=8,
    )
    status_frame.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    status_frame.columnconfigure(0, weight=1)
    ttk.Label(
        status_frame,
        textvariable=app.linux_help_status_var,
        justify="left",
        wraplength=1040,
    ).grid(row=0, column=0, sticky="w")

    filter_frame = ttk.LabelFrame(
        app.tab_linux_help,
        text=app.tr("linux_help_group_filters", "Search, filters and actions"),
        padding=8,
    )
    filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    filter_frame.columnconfigure(0, weight=1)

    search_row = ttk.Frame(filter_frame)
    search_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
    search_row.columnconfigure(1, weight=1)
    ttk.Label(
        search_row,
        text=app.tr("linux_help_label_search", "Search"),
    ).grid(row=0, column=0, sticky="w")
    app.linux_help_search_entry = ttk.Entry(
        search_row,
        textvariable=app.linux_help_search_var,
    )
    app.linux_help_search_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0))
    _bind_refresh_linux_help(app.linux_help_search_entry, app, "<KeyRelease>")

    filter_row = ttk.Frame(filter_frame)
    filter_row.grid(row=1, column=0, sticky="ew", pady=(0, 6))
    for column in range(7):
        filter_row.columnconfigure(column, weight=1 if column in {1, 3, 5} else 0)

    ttk.Label(
        filter_row,
        text=app.tr("linux_help_label_category", "Category"),
    ).grid(row=0, column=0, sticky="w")
    app.linux_help_category_combo = ttk.Combobox(
        filter_row,
        textvariable=app.linux_help_category_var,
        values=[],
        state="readonly",
    )
    app.linux_help_category_combo.grid(row=0, column=1, sticky="ew", padx=(6, 12))
    _bind_refresh_linux_help(
        app.linux_help_category_combo,
        app,
        "<<ComboboxSelected>>",
    )

    ttk.Label(
        filter_row,
        text=app.tr("linux_help_label_source", "Source"),
    ).grid(row=0, column=2, sticky="w")
    app.linux_help_source_combo = ttk.Combobox(
        filter_row,
        textvariable=app.linux_help_source_var,
        values=(
            app.tr("linux_help_source_commands", "Commands"),
            app.tr("linux_help_source_glossary", "Glossary"),
            app.tr("linux_help_source_both", "Both"),
        ),
        state="readonly",
    )
    app.linux_help_source_combo.grid(row=0, column=3, sticky="ew", padx=(6, 12))
    _bind_refresh_linux_help(
        app.linux_help_source_combo,
        app,
        "<<ComboboxSelected>>",
    )

    ttk.Label(
        filter_row,
        text=app.tr("linux_help_label_risk_filter", "Risk"),
    ).grid(row=0, column=4, sticky="w")
    app.linux_help_risk_combo = ttk.Combobox(
        filter_row,
        textvariable=app.linux_help_risk_filter_var,
        values=(
            app.tr("linux_help_all_risks", "All risks"),
            app.tr("linux_help_risk_safe", "🟢 Safe"),
            app.tr("linux_help_risk_caution", "🟡 Admin"),
            app.tr("linux_help_risk_danger", "🔴 Dangerous"),
        ),
        state="readonly",
    )
    app.linux_help_risk_combo.grid(row=0, column=5, sticky="ew", padx=(6, 12))
    _bind_refresh_linux_help(
        app.linux_help_risk_combo,
        app,
        "<<ComboboxSelected>>",
    )

    app.btn_linux_help_clear_filters = ttk.Button(
        filter_row,
        text=app.tr("btn_clear", "Clear"),
        command=app.clear_linux_help_filters,
    )
    app.btn_linux_help_clear_filters.grid(row=0, column=6, sticky="ew")

    actions_row = ttk.Frame(filter_frame)
    actions_row.grid(row=2, column=0, sticky="ew")
    for column in range(4):
        actions_row.columnconfigure(column, weight=1)

    app.btn_linux_help_reload = ttk.Button(
        actions_row,
        text=app.tr("btn_reload", "Reload"),
        command=app.reload_linux_help_data,
    )
    app.btn_linux_help_reload.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    app.btn_linux_help_import = ttk.Button(
        actions_row,
        text=app.tr("btn_import_csv", "Import CSV/XLSX"),
        command=app.linux_help_import_csv_dialog,
    )
    app.btn_linux_help_import.grid(row=0, column=1, sticky="ew", padx=(0, 8))
    app.btn_linux_help_export = ttk.Button(
        actions_row,
        text=app.tr("btn_export_csv", "Export CSV"),
        command=app.linux_help_export_csv_dialog,
    )
    app.btn_linux_help_export.grid(row=0, column=2, sticky="ew", padx=(0, 8))
    app.btn_linux_help_send_terminal = ttk.Button(
        actions_row,
        text=app.tr("linux_help_btn_send_terminal", "Send to terminal"),
        command=app.send_linux_help_command_to_terminal,
    )
    app.btn_linux_help_send_terminal.grid(row=0, column=3, sticky="ew")

    help_row = ttk.Frame(filter_frame)
    help_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))
    help_row.columnconfigure(0, weight=1)

    help_hint = ttk.Label(
        help_row,
        text=app.tr(
            "linux_help_hint_integrated",
            "Search by command, tags, description or syntax. The detail view below remains usable while scrolling.",
        ),
        justify="left",
        wraplength=980,
    )
    help_hint.grid(row=0, column=0, sticky="w")

    manage_row = ttk.Frame(filter_frame)
    manage_row.grid(row=4, column=0, sticky="ew", pady=(6, 0))
    for column in range(3):
        manage_row.columnconfigure(column, weight=1)

    app.btn_linux_help_new = ttk.Button(
        manage_row,
        text=app.tr("btn_new", "New"),
        command=app.linux_help_new_entry,
    )
    app.btn_linux_help_new.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    app.btn_linux_help_edit = ttk.Button(
        manage_row,
        text=app.tr("btn_edit", "Edit"),
        command=app.linux_help_edit_selected,
    )
    app.btn_linux_help_edit.grid(row=0, column=1, sticky="ew", padx=(0, 8))
    app.btn_linux_help_delete = ttk.Button(
        manage_row,
        text=app.tr("btn_delete", "Delete"),
        command=app.linux_help_delete_selected,
    )
    app.btn_linux_help_delete.grid(row=0, column=2, sticky="ew", padx=(0, 12))

    manage_hint_row = ttk.Frame(filter_frame)
    manage_hint_row.grid(row=5, column=0, sticky="ew", pady=(4, 0))
    manage_hint_row.columnconfigure(0, weight=1)

    ttk.Label(
        manage_hint_row,
        text=app.tr(
            "linux_help_manage_hint",
            "You can create your own additions via the popup and save them directly in the NetMon database.",
        ),
        justify="left",
        wraplength=900,
    ).grid(row=0, column=0, sticky="w")

    app.linux_help_main_pane = ttk.Panedwindow(
        app.tab_linux_help,
        orient="vertical",
    )
    app.linux_help_main_pane.grid(row=2, column=0, sticky="nsew")

    top_pane = ttk.Frame(app.linux_help_main_pane, padding=(0, 0, 0, 6))
    top_pane.columnconfigure(0, weight=1)
    top_pane.rowconfigure(0, weight=1)
    app.linux_help_main_pane.add(top_pane, weight=3)

    table_frame = ttk.LabelFrame(
        top_pane,
        text=app.tr("linux_help_group_commands", "Command overview"),
        padding=8,
    )
    table_frame.grid(row=0, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(0, weight=1)

    columns = ("category", "source", "risk", "root", "tags", "summary")
    app.linux_help_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="tree headings",
        selectmode="browse",
        height=14,
    )
    app.linux_help_tree.heading("#0", text=app.tr("linux_help_col_command", "Command"))
    app.linux_help_tree.heading(
        "category", text=app.tr("linux_help_col_category", "Category")
    )
    app.linux_help_tree.heading(
        "source", text=app.tr("linux_help_col_source", "Source")
    )
    app.linux_help_tree.heading("risk", text=app.tr("linux_help_col_risk", "Risk"))
    app.linux_help_tree.heading("root", text=app.tr("linux_help_col_root", "Root"))
    app.linux_help_tree.heading("tags", text=app.tr("linux_help_col_tags", "Tags"))
    app.linux_help_tree.heading(
        "summary", text=app.tr("linux_help_col_summary", "Summary")
    )
    app.linux_help_tree.column("#0", width=180, stretch=True, anchor="w")
    app.linux_help_tree.column("category", width=120, stretch=False, anchor="w")
    app.linux_help_tree.column("source", width=110, stretch=False, anchor="w")
    app.linux_help_tree.column("risk", width=110, stretch=False, anchor="w")
    app.linux_help_tree.column("root", width=80, stretch=False, anchor="center")
    app.linux_help_tree.column("tags", width=180, stretch=True, anchor="w")
    app.linux_help_tree.column("summary", width=300, stretch=True, anchor="w")
    app.linux_help_tree.grid(row=0, column=0, sticky="nsew")
    app.linux_help_tree.bind("<<TreeviewSelect>>", app.on_linux_help_select)
    app.linux_help_tree.bind(
        "<Double-1>",
        lambda _event: app.linux_help_edit_selected(),
    )
    app.linux_help_tree.bind("<Button-3>", app.show_linux_help_tree_menu)

    tree_scroll_y = ttk.Scrollbar(
        table_frame, orient="vertical", command=app.linux_help_tree.yview
    )
    tree_scroll_y.grid(row=0, column=1, sticky="ns")
    app.linux_help_tree.configure(yscrollcommand=tree_scroll_y.set)

    tree_scroll_x = ttk.Scrollbar(
        table_frame, orient="horizontal", command=app.linux_help_tree.xview
    )
    tree_scroll_x.grid(row=1, column=0, sticky="ew")
    app.linux_help_tree.configure(xscrollcommand=tree_scroll_x.set)

    bottom_pane = ttk.Frame(app.linux_help_main_pane, padding=(0, 6, 0, 0))
    bottom_pane.columnconfigure(0, weight=1)
    bottom_pane.rowconfigure(0, weight=1)
    bottom_pane.rowconfigure(1, weight=1)
    app.linux_help_main_pane.add(bottom_pane, weight=2)

    explanation_frame = ttk.LabelFrame(
        bottom_pane,
        text=app.tr("linux_help_group_explanation", "Explanation and notes"),
        padding=8,
    )
    explanation_frame.grid(row=0, column=0, sticky="nsew")
    explanation_frame.columnconfigure(0, weight=1)
    explanation_frame.rowconfigure(0, weight=1)

    app.linux_help_risk_canvas = None
    app.linux_help_risk_dot = None

    app.linux_help_text = tk.Text(
        explanation_frame,
        wrap="word",
        height=11,
        relief="flat",
        bd=0,
    )
    app.linux_help_text.grid(row=0, column=0, sticky="nsew")
    detail_scroll = ttk.Scrollbar(
        explanation_frame, orient="vertical", command=app.linux_help_text.yview
    )
    detail_scroll.grid(row=0, column=1, sticky="ns")
    app.linux_help_text.configure(yscrollcommand=detail_scroll.set)
    app.attach_chad_context_menu(app.linux_help_text, "Linux command database")

    documents_frame = ttk.LabelFrame(
        bottom_pane,
        text=app.tr("linux_help_group_documents", "PDF documentation library"),
        padding=8,
    )
    documents_frame.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
    documents_frame.columnconfigure(0, weight=0)
    documents_frame.columnconfigure(1, weight=1)
    documents_frame.rowconfigure(1, weight=1)

    documents_actions = ttk.Frame(documents_frame)
    documents_actions.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    for column in range(4):
        documents_actions.columnconfigure(column, weight=1)

    app.btn_linux_help_import_pdf = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_import_pdf", "PDF importieren"),
        command=app.import_linux_help_pdf_dialog,
    )
    app.btn_linux_help_import_pdf.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    app.btn_linux_help_reload_docs = ttk.Button(
        documents_actions,
        text=app.tr("btn_reload", "Reload"),
        command=app.reload_linux_help_documents,
    )
    app.btn_linux_help_reload_docs.grid(row=0, column=1, sticky="ew", padx=(0, 8))
    app.btn_linux_help_open_pdf = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_open_pdf", "PDF oeffnen"),
        command=app.open_selected_linux_help_pdf,
    )
    app.btn_linux_help_open_pdf.grid(row=0, column=2, sticky="ew", padx=(0, 8))
    app.btn_linux_help_open_docs_folder = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_open_docs_folder", "Ordner oeffnen"),
        command=app.open_linux_help_documents_folder,
    )
    app.btn_linux_help_open_docs_folder.grid(row=0, column=3, sticky="ew")

    documents_list_frame = ttk.Frame(documents_frame)
    documents_list_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
    documents_list_frame.columnconfigure(0, weight=1)
    documents_list_frame.rowconfigure(0, weight=1)

    app.linux_help_documents_listbox = tk.Listbox(
        documents_list_frame,
        exportselection=False,
        height=8,
    )
    app.linux_help_documents_listbox.grid(row=0, column=0, sticky="nsew")
    app.linux_help_documents_listbox.bind(
        "<<ListboxSelect>>",
        app.on_linux_help_document_select,
    )
    app.linux_help_documents_listbox.bind(
        "<Double-1>",
        lambda _event: app.open_selected_linux_help_pdf(),
    )
    app.linux_help_documents_listbox.bind(
        "<Button-3>",
        app.show_linux_help_document_menu,
    )
    documents_list_scroll = ttk.Scrollbar(
        documents_list_frame,
        orient="vertical",
        command=app.linux_help_documents_listbox.yview,
    )
    documents_list_scroll.grid(row=0, column=1, sticky="ns")
    app.linux_help_documents_listbox.configure(yscrollcommand=documents_list_scroll.set)

    documents_preview_frame = ttk.Frame(documents_frame)
    documents_preview_frame.grid(row=1, column=1, sticky="nsew")
    documents_preview_frame.columnconfigure(0, weight=1)
    documents_preview_frame.rowconfigure(0, weight=1)

    app.linux_help_documents_text = tk.Text(
        documents_preview_frame,
        wrap="word",
        height=8,
        relief="flat",
        bd=0,
    )
    app.linux_help_documents_text.grid(row=0, column=0, sticky="nsew")
    documents_preview_scroll = ttk.Scrollbar(
        documents_preview_frame,
        orient="vertical",
        command=app.linux_help_documents_text.yview,
    )
    documents_preview_scroll.grid(row=0, column=1, sticky="ns")
    app.linux_help_documents_text.configure(
        yscrollcommand=documents_preview_scroll.set,
        state="disabled",
    )

    _install_vertical_pane_drag_markers(
        app.tab_linux_help,
        app.linux_help_main_pane,
        min_pane_size=180,
    )
    app.reload_linux_help_data()
    app.reload_linux_help_documents()
