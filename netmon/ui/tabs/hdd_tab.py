"""HDD subtab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.config.constants import HDD_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import HDD_SLOT_COUNT


def build_hdd_tab(app):
    app.tab_hdd = ttk.Frame(app.system_nb, padding=10)
    app.system_nb.add(app.tab_hdd, text=app.tr("system_tab_hdd", "HDD"))

    hdd_manage = ttk.LabelFrame(
        app.tab_hdd,
        text=app.tr("hdd_group_manage", "HDD Verwaltung"),
        padding=8,
    )
    hdd_manage.pack(fill="x", pady=(0, 8))
    top_line = ttk.Frame(hdd_manage)
    top_line.pack(fill="x")
    for col, weight in [(0, 0), (1, 0), (2, 0), (3, 1), (4, 0)]:
        top_line.columnconfigure(col, weight=weight)
    app.btn_hdd_scan = ttk.Button(
        top_line,
        text=app.tr("hdd_btn_scan", "Festplatten einlesen"),
        command=app.scan_hdds_async,
    )
    app.btn_hdd_scan.grid(row=0, column=0, sticky="w")
    app.add_tooltip(
        app.btn_hdd_scan,
        app.tr(
            "tooltip_hdd_scan",
            "Liest erkannte Festplatten neu ein und aktualisiert die Liste.",
        ),
    )
    app.hdd_slot_choice = tk.StringVar(value="1")
    ttk.Label(top_line, text=app.tr("label_slot", "Slot:")).grid(
        row=0, column=1, sticky="w", padx=(10, 4)
    )
    app.hdd_slot_combo = ttk.Combobox(
        top_line,
        textvariable=app.hdd_slot_choice,
        values=[str(i) for i in range(1, HDD_SLOT_COUNT + 1)],
        state="readonly",
        width=4,
    )
    app.hdd_slot_combo.grid(row=0, column=2, sticky="w")
    ttk.Label(
        top_line,
        text=app.tr("label_display_name", "Anzeigename:"),
    ).grid(row=0, column=3, sticky="w", padx=(10, 4))
    app.hdd_custom_name_var = tk.StringVar(value="")
    app.hdd_name_entry = ttk.Entry(top_line, textvariable=app.hdd_custom_name_var)
    app.hdd_name_entry.grid(row=0, column=4, sticky="ew")
    app.hdd_name_entry.bind("<FocusIn>", app.on_hdd_name_focus_in)
    app.hdd_name_entry.bind("<FocusOut>", app.on_hdd_name_focus_out)
    app.hdd_custom_name_var.trace_add("write", app.on_hdd_name_changed)
    app.btn_hdd_assign = ttk.Button(
        top_line,
        text=app.tr("btn_apply_assignment", "Zuordnung übernehmen"),
        command=app.assign_selected_disk_to_slot,
    )
    app.btn_hdd_assign.grid(row=0, column=5, sticky="e", padx=(8, 0))
    app.add_tooltip(
        app.btn_hdd_assign,
        app.tr(
            "tooltip_hdd_assign",
            "Ordnet die ausgewählte Festplatte dem gewählten Slot zu.",
        ),
    )
    app.btn_hdd_clear_assign = ttk.Button(
        top_line,
        text=app.tr("btn_clear_assignment", "Zuordnung aufheben"),
        command=lambda: app.clear_slot_assignment(confirm=True),
    )
    app.btn_hdd_clear_assign.grid(
        row=1, column=5, sticky="e", padx=(8, 0), pady=(6, 0)
    )
    app.add_tooltip(
        app.btn_hdd_clear_assign,
        app.tr(
            "tooltip_hdd_clear_assign",
            "Entfernt die Zuordnung des gewählten Slots.",
        ),
    )

    app.hdd_table = ttk.Treeview(
        hdd_manage,
        columns=(
            "device",
            "label",
            "fstype",
            "size",
            "mounted",
            "mountpoint",
            "slot",
        ),
        show="headings",
        height=7,
    )
    for col, title, width, anchor in [
        ("device", "Device", 150, "w"),
        ("label", "Label/Model", 180, "w"),
        ("fstype", "FS", 70, "center"),
        ("size", "Size", 90, "e"),
        ("mounted", "Status", 100, "center"),
        ("mountpoint", "Mountpoint", 180, "w"),
        ("slot", "Slot", 60, "center"),
    ]:
        app.hdd_table.heading(col, text=title)
        app.hdd_table.column(col, width=width, anchor=anchor)
    app.hdd_table.pack(fill="x", pady=(8, 0))
    app.hdd_table.bind("<<TreeviewSelect>>", app.on_hdd_table_select)
    app.hdd_info_auto_mount_var = tk.BooleanVar(value=False)
    app.hdd_info_auto_mount_hint_var = tk.StringVar(value="")
    auto_mount_row = ttk.Frame(app.tab_hdd)
    auto_mount_row.pack(fill="x", pady=(8, 4))
    app.hdd_info_auto_mount_check = ttk.Checkbutton(
        auto_mount_row,
        text=app.tr(
            "hdd_check_auto_mount",
            "Bei NetMon-Start automatisch mounten",
        ),
        variable=app.hdd_info_auto_mount_var,
        command=app.on_hdd_auto_mount_toggle,
    )
    app.hdd_info_auto_mount_check.pack(side="left")
    app.hdd_info_auto_mount_hint_label = ttk.Label(
        auto_mount_row,
        textvariable=app.hdd_info_auto_mount_hint_var,
        foreground="#8a6d3b",
    )
    app.hdd_info_auto_mount_hint_label.pack(side="left", padx=(10, 0))
    app.hdd_info_text = tk.Text(app.tab_hdd, wrap="word", height=12)
    app.hdd_info_text.pack(fill="both", expand=True)
    app.hdd_usage_canvas = tk.Canvas(
        app.tab_hdd, height=34, highlightthickness=1, highlightbackground="#bbb"
    )
    app.hdd_usage_canvas.pack(fill="x", pady=(8, 0))
