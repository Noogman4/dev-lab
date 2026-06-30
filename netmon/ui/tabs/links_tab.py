"""Links subtab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.config.constants import LINK_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import LINK_SLOT_COUNT


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _list_value(value):
    return list(value or [])


def build_links_tab(app):
    app.tab_links = ttk.Frame(app.system_nb, padding=10)
    app.system_nb.add(app.tab_links, text=app.tr("system_tab_links", "Links"))

    link_manage = ttk.LabelFrame(
        app.tab_links,
        text=app.tr("links_group_manage", "Link Verwaltung"),
        padding=8,
    )
    link_manage.pack(fill="x", pady=(0, 8))
    link_form = ttk.Frame(link_manage)
    link_form.pack(fill="x")
    for col, weight in [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 1),
        (4, 0),
        (5, 0),
        (6, 0),
        (7, 1),
    ]:
        link_form.columnconfigure(col, weight=weight)

    app.link_slot_choice = tk.StringVar(value="1")
    ttk.Label(link_form, text=app.tr("label_slot", "Slot:")).grid(
        row=0, column=0, sticky="w"
    )
    app.link_slot_combo = ttk.Combobox(
        link_form,
        textvariable=app.link_slot_choice,
        values=[str(i) for i in range(1, LINK_SLOT_COUNT + 1)],
        state="readonly",
        width=4,
    )
    app.link_slot_combo.grid(row=0, column=1, sticky="w", padx=(4, 10))
    app.link_slot_combo.bind("<<ComboboxSelected>>", app.on_link_slot_select)

    ttk.Label(
        link_form,
        text=app.tr("label_display_name", "Anzeigename:"),
    ).grid(row=0, column=2, sticky="w")
    app.link_custom_name_var = tk.StringVar(value="")
    ttk.Entry(link_form, textvariable=app.link_custom_name_var).grid(
        row=0, column=3, sticky="ew", padx=(4, 10)
    )

    ttk.Label(link_form, text=app.tr("label_type", "Typ:")).grid(
        row=0, column=4, sticky="w"
    )
    app.link_type_var = tk.StringVar(value="Systemlink")
    app.link_type_combo = ttk.Combobox(
        link_form,
        textvariable=app.link_type_var,
        values=["Systemlink", "Externer Link"],
        state="readonly",
        width=14,
    )
    app.link_type_combo.grid(row=0, column=5, sticky="w", padx=(4, 10))
    app.link_type_combo.bind("<<ComboboxSelected>>", app.on_link_type_change)

    app.link_target_label = ttk.Label(
        link_form,
        text=app.tr("links_label_target", "Ziel / Pfad / URL:"),
    )
    app.link_target_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
    app.link_target_var = tk.StringVar(value="")
    app.link_system_app_var = tk.StringVar(value="")

    app.link_target_entry = ttk.Entry(link_form, textvariable=app.link_target_var)
    app.link_target_entry.grid(
        row=1, column=2, columnspan=6, sticky="ew", padx=(4, 0), pady=(8, 0)
    )

    app.link_system_frame = ttk.Frame(link_form)
    app.link_system_frame.grid(
        row=1, column=2, columnspan=6, sticky="ew", padx=(4, 0), pady=(8, 0)
    )
    app.link_system_frame.columnconfigure(0, weight=1)

    app.link_system_combo = ttk.Combobox(
        app.link_system_frame,
        textvariable=app.link_system_app_var,
        values=_list_value(_app_value(app, "desktop_app_labels", [])),
        state="readonly",
    )
    app.link_system_combo.grid(row=0, column=0, sticky="ew")
    app.link_system_combo.bind("<<ComboboxSelected>>", app.on_systemlink_app_select)

    app.btn_link_refresh_programs = ttk.Button(
        app.link_system_frame,
        text=app.tr("btn_refresh", "Aktualisieren"),
        command=app.refresh_desktop_app_entries,
    )
    app.btn_link_refresh_programs.grid(row=0, column=1, sticky="w", padx=(8, 0))
    app.add_tooltip(
        app.btn_link_refresh_programs,
        app.tr(
            "tooltip_links_refresh_programs",
            "Liest installierte Programme (.desktop) neu ein und aktualisiert die Auswahlliste.",
        ),
    )

    link_btns = ttk.Frame(link_manage)
    link_btns.pack(fill="x", pady=(8, 0))
    app.btn_link_apply = ttk.Button(
        link_btns,
        text=app.tr("btn_apply_assignment", "Zuordnung übernehmen"),
        command=app.assign_link_slot,
    )
    app.btn_link_apply.pack(side="left")
    app.add_tooltip(
        app.btn_link_apply,
        app.tr(
            "tooltip_links_apply",
            "Speichert die aktuelle Link-Zuordnung für den gewählten Slot.",
        ),
    )
    app.btn_link_clear = ttk.Button(
        link_btns,
        text=app.tr("btn_clear_assignment", "Zuordnung aufheben"),
        command=lambda: app.clear_link_slot(confirm=True),
    )
    app.btn_link_clear.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_link_clear,
        app.tr(
            "tooltip_links_clear",
            "Entfernt die Konfiguration des gewählten Link-Slots.",
        ),
    )
    app.btn_link_test = ttk.Button(
        link_btns,
        text=app.tr("links_btn_test", "Link testen"),
        command=app.test_link_slot,
    )
    app.btn_link_test.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_link_test,
        app.tr(
            "tooltip_links_test",
            "Testet den aktuell eingestellten Link mit den Formulardaten.",
        ),
    )

    link_table_wrap = ttk.Frame(app.tab_links)
    link_table_wrap.pack(fill="both", expand=True)
    link_table_wrap.columnconfigure(0, weight=1)
    link_table_wrap.rowconfigure(0, weight=1)

    app.link_table = ttk.Treeview(
        link_table_wrap,
        columns=("slot", "name", "type", "target"),
        show="headings",
        height=15,
    )
    for col, title, width, anchor in [
        ("slot", "Slot", 60, "center"),
        ("name", "Anzeigename", 180, "w"),
        ("type", "Typ", 120, "center"),
        ("target", "Ziel", 420, "w"),
    ]:
        app.link_table.heading(col, text=title)
        app.link_table.column(col, width=width, anchor=anchor)

    link_table_scroll = ttk.Scrollbar(
        link_table_wrap, orient="vertical", command=app.link_table.yview
    )
    app.link_table.configure(yscrollcommand=link_table_scroll.set)

    app.link_table.grid(row=0, column=0, sticky="nsew")
    link_table_scroll.grid(row=0, column=1, sticky="ns")
    app.link_table.bind("<<TreeviewSelect>>", app.on_link_table_select)

    app.load_link_slot_into_form(1)
    app.sync_link_target_widgets()
    app.refresh_link_table()
    app.update_link_slot_buttons()
