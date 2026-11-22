"""Linux command database tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.ui.linux_help_components import open_linux_help_components
    from netmon.ui.linux_help_resources import open_linux_help_resources
except ModuleNotFoundError:
    from ui.linux_help_components import open_linux_help_components
    from ui.linux_help_resources import open_linux_help_resources

try:
    from netmon.features.linux_help_quiz_controller import (
        initialize_linux_help_quiz,
        open_linux_help_quiz,
    )
except ModuleNotFoundError:
    from features.linux_help_quiz_controller import (
        initialize_linux_help_quiz,
        open_linux_help_quiz,
    )

try:
    from netmon.features.linux_help_controller import (
        open_linux_help_reader,
        open_linux_help_prompt,
        import_linux_help_markdown_dialog,
        reset_linux_help_reading,
        style_linux_help_reading,
    )
except ModuleNotFoundError:
    from features.linux_help_controller import (
        open_linux_help_reader,
        open_linux_help_prompt,
        import_linux_help_markdown_dialog,
        reset_linux_help_reading,
        style_linux_help_reading,
    )


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

    help_row = ttk.Frame(filter_frame)
    help_row.grid(row=2, column=0, sticky="ew", pady=(6, 0))
    help_row.columnconfigure(0, weight=1)

    help_hint = ttk.Label(
        help_row,
        text=app.tr(
            "linux_help_hint_integrated",
            "Search by command, tags, description or syntax. Double-click a command to open the reader.",
        ),
        justify="left",
        wraplength=980,
    )
    help_hint.grid(row=0, column=0, sticky="w")

    top_pane = ttk.Frame(app.tab_linux_help)
    top_pane.grid(row=2, column=0, sticky="nsew")
    top_pane.columnconfigure(0, weight=1)
    top_pane.rowconfigure(0, weight=1)

    table_frame = ttk.LabelFrame(
        top_pane,
        text=app.tr("linux_help_group_commands", "Command overview"),
        padding=8,
    )
    table_frame.grid(row=0, column=0, sticky="nsew")
    table_frame.columnconfigure(0, weight=1)
    table_frame.rowconfigure(1, weight=1)

    reading_actions = ttk.Frame(table_frame)
    reading_actions.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
    for column in range(3):
        reading_actions.columnconfigure(column, weight=1, uniform="reading_actions")
    app.linux_help_bookmarks_only_var = tk.BooleanVar(master=app.tab_linux_help)
    app.linux_help_bookmarks_filter = ttk.Checkbutton(
        reading_actions,
        text=app.tr("linux_help_bookmarks_only", "Nur Lesezeichen"),
        variable=app.linux_help_bookmarks_only_var,
        command=app.refresh_linux_help_list,
    )
    app.linux_help_bookmarks_filter.grid(row=0, column=0, sticky="w")
    prompt_label = app.tr("linux_help_btn_md_prompt", "MD-Prompt erstellen …")
    resources_label = app.tr("linux_help_resources_button", "Benutzte Libraries")
    center_button_width = max(len(prompt_label), len(resources_label))
    app.btn_linux_help_prompt_top = ttk.Button(
        reading_actions,
        text=prompt_label,
        width=center_button_width,
        command=lambda: open_linux_help_prompt(app),
    )
    app.btn_linux_help_prompt_top.grid(row=0, column=1, padx=8)
    app.btn_linux_help_resources = ttk.Button(
        reading_actions,
        text=resources_label,
        width=center_button_width,
        command=lambda: open_linux_help_resources(app),
    )
    app.btn_linux_help_resources.grid(row=1, column=1, padx=8, pady=(6, 0))
    reset_label = app.tr("linux_help_reading_reset", "Lesestatus zurücksetzen…")
    components_label = app.tr("linux_help_components", "Linux Komponenten")
    right_button_width = max(len(reset_label), len(components_label))
    app.btn_linux_help_reset_reading = ttk.Button(
        reading_actions,
        text=reset_label,
        width=right_button_width,
        command=lambda: reset_linux_help_reading(app),
    )
    app.btn_linux_help_reset_reading.grid(row=0, column=2, sticky="e")
    app.btn_linux_help_components = ttk.Button(
        reading_actions,
        text=components_label,
        width=right_button_width,
        command=lambda: open_linux_help_components(app),
    )
    app.btn_linux_help_components.grid(row=1, column=2, sticky="e", pady=(6, 0))

    app.btn_linux_help_quiz = ttk.Button(
        reading_actions,
        text=app.tr("linux_help_quiz_open", "Lernquiz …"),
        command=lambda: open_linux_help_quiz(app),
    )
    app.btn_linux_help_quiz.grid(row=1, column=0, sticky="w", pady=(6, 0))

    columns = ("category", "source", "risk", "root", "tags", "summary", "reading")
    app.linux_help_tree = ttk.Treeview(
        table_frame,
        columns=columns,
        show="tree headings",
        selectmode="browse",
        height=14,
        displaycolumns=(
            "reading",
            "category",
            "source",
            "risk",
            "root",
            "tags",
            "summary",
        ),
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
    app.linux_help_tree.heading(
        "reading", text=app.tr("linux_help_reading_column", "Lesestatus")
    )
    app.linux_help_tree.column("#0", width=180, stretch=True, anchor="w")
    app.linux_help_tree.column("category", width=120, stretch=False, anchor="w")
    app.linux_help_tree.column("source", width=110, stretch=False, anchor="w")
    app.linux_help_tree.column("risk", width=110, stretch=False, anchor="w")
    app.linux_help_tree.column("root", width=80, stretch=False, anchor="center")
    app.linux_help_tree.column("tags", width=180, stretch=True, anchor="w")
    app.linux_help_tree.column("summary", width=300, stretch=True, anchor="w")
    app.linux_help_tree.column("reading", width=115, stretch=False, anchor="w")
    app.linux_help_tree.grid(row=1, column=0, sticky="nsew")
    app.linux_help_tree.bind(
        "<<ThemeChanged>>", lambda _event: style_linux_help_reading(app), add="+"
    )
    app.linux_help_tree.bind("<<TreeviewSelect>>", app.on_linux_help_select)
    app.linux_help_tree.bind(
        "<Double-1>",
        lambda event: open_linux_help_reader(app, event),
    )
    app.linux_help_tree.bind(
        "<Return>", lambda event: open_linux_help_reader(app, event)
    )
    app.linux_help_tree.bind("<Button-3>", app.show_linux_help_tree_menu)

    tree_scroll_y = ttk.Scrollbar(
        table_frame, orient="vertical", command=app.linux_help_tree.yview
    )
    tree_scroll_y.grid(row=1, column=1, sticky="ns")
    app.linux_help_tree.configure(yscrollcommand=tree_scroll_y.set)

    tree_scroll_x = ttk.Scrollbar(
        table_frame, orient="horizontal", command=app.linux_help_tree.xview
    )
    tree_scroll_x.grid(row=2, column=0, sticky="ew")
    app.linux_help_tree.configure(xscrollcommand=tree_scroll_x.set)

    bottom_pane = ttk.Frame(app.tab_linux_help, padding=(0, 8, 0, 0))
    bottom_pane.grid(row=3, column=0, sticky="ew")
    bottom_pane.columnconfigure(0, weight=1)
    app.linux_help_text = None
    app.linux_help_risk_canvas = None
    app.linux_help_risk_dot = None
    app.linux_help_reader_window = None

    documents_frame = ttk.LabelFrame(
        bottom_pane,
        text=app.tr("linux_help_document_management", "Dokumentationen verwalten"),
        padding=8,
    )
    documents_frame.grid(row=0, column=0, sticky="nsew")
    documents_frame.columnconfigure(0, weight=0)
    documents_frame.columnconfigure(1, weight=1)

    ttk.Label(
        documents_frame,
        text=app.tr(
            "linux_help_entry_actions_hint",
            "Actions for the selected entry above:",
        ),
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

    manage_row = ttk.Frame(documents_frame)
    manage_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    for column in range(3):
        manage_row.columnconfigure(column, weight=1, uniform="entry_actions")

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
    app.btn_linux_help_delete.grid(row=0, column=2, sticky="ew")

    documents_actions = ttk.Frame(documents_frame)
    documents_actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    for column in range(3):
        documents_actions.columnconfigure(column, weight=1, uniform="document_actions")

    app.btn_linux_help_import_markdown = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_import_markdown", "Markdown importieren (.md)"),
        command=lambda: import_linux_help_markdown_dialog(app),
    )
    app.btn_linux_help_import_markdown.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    app.btn_linux_help_prompt_bottom = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_md_prompt", "MD-Prompt erstellen …"),
        command=lambda: open_linux_help_prompt(app),
    )
    app.btn_linux_help_prompt_bottom.grid(row=0, column=1, sticky="ew", padx=(0, 8))
    app.btn_linux_help_reload = ttk.Button(
        documents_actions,
        text=app.tr("linux_help_btn_reload_all", "Reload all"),
        command=app.reload_linux_help_data,
    )
    app.btn_linux_help_reload.grid(row=0, column=2, sticky="ew")
    app.reload_linux_help_data()
    initialize_linux_help_quiz(app)
