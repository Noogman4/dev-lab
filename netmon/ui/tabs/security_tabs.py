"""Security notebook tab builders for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


ROOTS_GUARD_INITIAL_ENABLED_AREAS = {
    "SSH Konfiguration",
    "SSH Schlüssel / authorized_keys",
    "DNS / Hosts",
    "Kritische Systemdateien",
    "Autostart / systemd / cron",
}


def _selected_filter_mode(choice_var, modes_by_label: dict, default: str) -> str:
    if choice_var is None:
        return default
    try:
        label = str(choice_var.get() or "")
    except Exception:
        label = ""
    return str(modes_by_label.get(label, default) or default)


def _install_vertical_pane_drag_markers(
    container,
    pane,
    *,
    color="#0a84ff",
    min_pane_size=110,
):
    markers = []
    drag_state = {
        "active": None,
        "root_y": 0,
        "sash_y": 0,
        "update_pending": False,
    }

    def _clamp_sash_pos(index, new_y):
        if int(min_pane_size) <= 0:
            return int(new_y)
        try:
            total_height = max(
                int(container.winfo_height() or 0),
                int(pane.winfo_height() or 0),
            )
        except Exception:
            total_height = 0
        if total_height <= 0:
            return int(new_y)

        sash_count = max(len(pane.panes()) - 1, 0)
        lower_bound = int(min_pane_size)
        upper_bound = max(total_height - int(min_pane_size), lower_bound)
        if index > 0:
            try:
                lower_bound = max(
                    lower_bound, int(pane.sashpos(index - 1)) + int(min_pane_size)
                )
            except Exception:
                pass
        if index < sash_count - 1:
            try:
                upper_bound = min(
                    upper_bound, int(pane.sashpos(index + 1)) - int(min_pane_size)
                )
            except Exception:
                pass
        if upper_bound < lower_bound:
            upper_bound = lower_bound
        return max(lower_bound, min(int(new_y), upper_bound))

    def _set_sash_pos(index, new_y):
        new_y = _clamp_sash_pos(index, new_y)
        try:
            pane.sashpos(index, int(new_y))
            return
        except Exception:
            pass
        try:
            pane.sash_place(index, 0, int(new_y))
        except Exception:
            pass

    def _ensure_marker(index):
        while len(markers) <= index:
            marker = tk.Frame(
                container,
                bg=color,
                bd=1,
                relief="solid",
            )
            marker.columnconfigure(0, weight=1)
            grip = tk.Label(
                marker,
                text="≡",
                bg=color,
                fg="#ffffff",
                font=("TkDefaultFont", 9, "bold"),
                cursor="sb_v_double_arrow",
                padx=0,
                pady=0,
                anchor="center",
            )
            grip.grid(row=0, column=0, sticky="ew")
            markers.append((marker, grip))
        return markers[index]

    def _place_marker(index, sash_y):
        marker, _grip = _ensure_marker(index)
        try:
            width = max(int(container.winfo_width() or 0), 0)
            marker_width = min(66, max(width - 24, 42))
            x = max((width - marker_width) // 2, 8)
            pane_offset_y = max(int(pane.winfo_y() or 0), 0)
            y = max(pane_offset_y + int(sash_y) - 9, 2)
            marker.place(x=x, y=y, width=marker_width, height=12)
            marker.lift()
        except Exception:
            try:
                marker.place_forget()
            except Exception:
                pass

    def _hide_unused_markers(start_index):
        for marker, _grip in markers[start_index:]:
            try:
                marker.place_forget()
            except Exception:
                pass

    def _update_markers(_event=None):
        sash_count = max(len(pane.panes()) - 1, 0)
        for index in range(sash_count):
            try:
                _place_marker(index, int(pane.sashpos(index)))
            except Exception:
                pass
        _hide_unused_markers(sash_count)

    def _schedule_marker_update():
        if drag_state["update_pending"]:
            return
        drag_state["update_pending"] = True

        def _run():
            drag_state["update_pending"] = False
            _update_markers()

        try:
            container.after_idle(_run)
        except Exception:
            _run()

    def _start_drag(event, index):
        drag_state["active"] = index
        try:
            drag_state["root_y"] = int(event.y_root)
            drag_state["sash_y"] = int(pane.sashpos(index))
        except Exception:
            drag_state["root_y"] = 0
            drag_state["sash_y"] = 0
        return "break"

    def _drag(event, index):
        if drag_state["active"] != index:
            return "break"
        try:
            delta = int(event.y_root) - int(drag_state["root_y"])
            new_sash = int(drag_state["sash_y"]) + delta
            _set_sash_pos(index, new_sash)
            _place_marker(index, new_sash)
            _schedule_marker_update()
        except Exception:
            pass
        return "break"

    def _end_drag(_event=None):
        drag_state["active"] = None
        _update_markers()
        return "break"

    for widget in (container, pane):
        try:
            widget.bind("<Configure>", _update_markers, add="+")
            widget.bind("<ButtonRelease-1>", _update_markers, add="+")
            widget.bind("<B1-Motion>", _update_markers, add="+")
        except Exception:
            pass

    for index in range(4):
        marker, grip = _ensure_marker(index)
        try:
            grip.bind(
                "<Button-1>",
                lambda event, sash_index=index: _start_drag(event, sash_index),
                add="+",
            )
            grip.bind(
                "<B1-Motion>",
                lambda event, sash_index=index: _drag(event, sash_index),
                add="+",
            )
            grip.bind("<ButtonRelease-1>", _end_drag, add="+")
        except Exception:
            pass
        try:
            marker.place_forget()
        except Exception:
            pass

    try:
        container.after(0, _update_markers)
    except Exception:
        pass
    return markers


def _build_security_stats_row(parent, app, *, top_padding=8):
    stats_frame = ttk.Frame(parent)
    stats_frame.pack(fill="x", pady=(top_padding, 0))
    for index in range(5):
        stats_frame.columnconfigure(index, weight=1)

    for col, title, var in [
        (0, "Gesamt-Events", app.security_stat_total_var),
        (1, "BLOCK-Events", app.security_stat_block_var),
        (2, "Portscan-Verdacht", app.security_stat_scan_var),
        (3, "Top Quelle-IP", app.security_stat_top_ip_var),
        (4, "Häufigster Ziel-Port", app.security_stat_top_port_var),
    ]:
        box = ttk.LabelFrame(stats_frame, text=title, padding=5)
        box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
        ttk.Label(box, textvariable=var).pack(anchor="center")

    return stats_frame


def build_startup_guard_tab(app):
    startup_top = ttk.Frame(app.tab_startup_guard)
    startup_top.pack(fill="x", pady=(0, 8))

    startup_row1 = ttk.LabelFrame(
        startup_top,
        text=app.tr("startup_guard_group_basic", "Basis"),
        padding=6,
    )
    startup_row1.pack(fill="x")
    startup_row2 = ttk.LabelFrame(
        startup_top,
        text=app.tr("startup_guard_group_analysis", "Analyse"),
        padding=6,
    )
    startup_row2.pack(fill="x", pady=(6, 0))
    startup_row3 = ttk.LabelFrame(
        startup_top,
        text=app.tr("startup_guard_group_trust", "Vertrauen"),
        padding=6,
    )
    startup_row3.pack(fill="x", pady=(6, 0))
    startup_status_row = ttk.Frame(startup_top)
    startup_status_row.pack(fill="x", pady=(6, 0))

    app.btn_startup_guard_baseline = ttk.Button(
        startup_row1,
        text=app.tr("startup_guard_btn_baseline", "Baseline erstellen"),
        command=app.startup_guard_create_baseline,
    )
    app.btn_startup_guard_baseline.pack(side="left")
    app.add_tooltip(
        app.btn_startup_guard_baseline,
        app.tr(
            "tooltip_startup_guard_baseline",
            "Sammelt aktuelle Startup-/Autostart-Einträge und speichert sie als Baseline.",
        ),
    )

    app.btn_startup_guard_check = ttk.Button(
        startup_row1,
        text=app.tr("startup_guard_btn_check", "Startup prüfen"),
        command=app.startup_guard_check,
    )
    app.btn_startup_guard_check.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_check,
        app.tr(
            "tooltip_startup_guard_check",
            "Vergleicht den aktuellen Startup-Zustand mit der gespeicherten Baseline.",
        ),
    )

    app.btn_startup_guard_clear = ttk.Button(
        startup_row1,
        text=app.tr("startup_guard_btn_clear", "Ergebnis leeren"),
        command=app.clear_startup_guard_output,
    )
    app.btn_startup_guard_clear.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_clear,
        app.tr(
            "tooltip_startup_guard_clear",
            "Leert die aktuelle Startup-Guard-Ausgabe im Tab.",
        ),
    )

    app.btn_startup_guard_chad_selected = ttk.Button(
        startup_row2,
        text=app.tr(
            "startup_guard_btn_chad_selected",
            "Eintrag mit Chad analysieren",
        ),
        command=app.analyze_selected_startup_entry_with_chad,
    )
    app.btn_startup_guard_chad_selected.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_chad_selected,
        app.tr(
            "tooltip_startup_guard_chad_selected",
            "Übergibt den aktuell ausgewählten Startup-Eintrag an den Chad Analyse-Bereich.",
        ),
    )

    app.btn_startup_guard_chad_changes = ttk.Button(
        startup_row2,
        text=app.tr(
            "startup_guard_btn_chad_changes",
            "Alle Änderungen mit Chad analysieren",
        ),
        command=app.analyze_startup_guard_changes_with_chad,
    )
    app.btn_startup_guard_chad_changes.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_chad_changes,
        app.tr(
            "tooltip_startup_guard_chad_changes",
            "Übergibt neue, entfernte und geänderte Startup-Einträge gesammelt an den Chad Analyse-Bereich.",
        ),
    )

    app.btn_startup_guard_mark_trusted = ttk.Button(
        startup_row3,
        text=app.tr("startup_guard_btn_mark_trusted", "Als bekannt markieren"),
        command=app.startup_guard_mark_selected_trusted,
    )
    app.btn_startup_guard_mark_trusted.pack(side="left")
    app.add_tooltip(
        app.btn_startup_guard_mark_trusted,
        app.tr(
            "tooltip_startup_guard_mark_trusted",
            "Markiert den ausgewählten Startup-Eintrag als bekannt, solange Pfad und Hash unverändert bleiben.",
        ),
    )

    app.btn_startup_guard_remove_trusted = ttk.Button(
        startup_row3,
        text=app.tr(
            "startup_guard_btn_remove_trusted",
            "Aus Vertrauensliste entfernen",
        ),
        command=app.startup_guard_remove_selected_trusted,
    )
    app.btn_startup_guard_remove_trusted.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_remove_trusted,
        app.tr(
            "tooltip_startup_guard_remove_trusted",
            "Entfernt den ausgewählten Startup-Eintrag aus der Vertrauensliste.",
        ),
    )

    app.btn_startup_guard_show_trustlist = ttk.Button(
        startup_row3,
        text=app.tr(
            "startup_guard_btn_show_trustlist",
            "Vertrauensliste anzeigen",
        ),
        command=app.startup_guard_show_trustlist,
    )
    app.btn_startup_guard_show_trustlist.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_show_trustlist,
        app.tr(
            "tooltip_startup_guard_show_trustlist",
            "Zeigt alle aktuell als bekannt markierten Startup-Einträge an.",
        ),
    )

    app.btn_startup_guard_reset_trustlist = ttk.Button(
        startup_row3,
        text=app.tr(
            "startup_guard_btn_reset_trustlist",
            "Vertrauensliste zurücksetzen",
        ),
        command=app.startup_guard_reset_trustlist,
    )
    app.btn_startup_guard_reset_trustlist.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_startup_guard_reset_trustlist,
        app.tr(
            "tooltip_startup_guard_reset_trustlist",
            "Leert alle bekannten Startup-Guard-Ausnahmen und prüft den Startup-Zustand erneut.",
        ),
    )

    ttk.Label(
        startup_status_row,
        text=app.tr("startup_guard_label_status", "Status:"),
    ).pack(side="left")
    ttk.Label(
        startup_status_row,
        textvariable=app.startup_guard_status_var,
    ).pack(side="left")
    ttk.Label(startup_status_row, text=" | ").pack(side="left")
    ttk.Label(
        startup_status_row,
        textvariable=app.startup_guard_run_status_var,
    ).pack(side="left")
    ttk.Label(startup_status_row, text=" | ").pack(side="left")
    ttk.Label(
        startup_status_row,
        textvariable=app.startup_guard_visible_count_var,
    ).pack(side="left")

    app.startup_guard_pane = ttk.Panedwindow(
        app.tab_startup_guard,
        orient="vertical",
    )
    app.startup_guard_pane.pack(fill="both", expand=True)

    tree_frame = ttk.Frame(app.startup_guard_pane)
    details_frame = ttk.LabelFrame(
        app.startup_guard_pane,
        text=app.tr("startup_guard_group_details", "Details"),
        padding=6,
    )
    app.startup_guard_pane.add(tree_frame, weight=3)
    app.startup_guard_pane.add(details_frame, weight=2)

    tree_scroll_y = ttk.Scrollbar(tree_frame, orient="vertical")
    tree_scroll_y.pack(side="right", fill="y")
    tree_scroll_x = ttk.Scrollbar(tree_frame, orient="horizontal")
    tree_scroll_x.pack(side="bottom", fill="x")

    app.startup_guard_tree = ttk.Treeview(
        tree_frame,
        columns=("status", "source", "name", "path"),
        show="headings",
        height=12,
        yscrollcommand=tree_scroll_y.set,
        xscrollcommand=tree_scroll_x.set,
    )
    app.startup_guard_tree.heading(
        "status", text=app.tr("startup_guard_col_status", "Status")
    )
    app.startup_guard_tree.heading(
        "source", text=app.tr("startup_guard_col_source", "Quelle")
    )
    app.startup_guard_tree.heading(
        "name", text=app.tr("startup_guard_col_name", "Name")
    )
    app.startup_guard_tree.heading(
        "path", text=app.tr("startup_guard_col_path", "Pfad")
    )
    app.startup_guard_tree.column("status", width=110, anchor="center")
    app.startup_guard_tree.column("source", width=150, anchor="w")
    app.startup_guard_tree.column("name", width=220, anchor="w")
    app.startup_guard_tree.column("path", width=520, anchor="w")
    app.startup_guard_tree.pack(fill="both", expand=True)
    tree_scroll_y.configure(command=app.startup_guard_tree.yview)
    tree_scroll_x.configure(command=app.startup_guard_tree.xview)
    app.startup_guard_tree.bind(
        "<<TreeviewSelect>>",
        app.on_startup_guard_select,
    )
    app.attach_startup_guard_tree_context_menu()

    app.startup_guard_details_text = tk.Text(
        details_frame,
        wrap="word",
        height=14,
    )
    app.startup_guard_details_text.pack(fill="both", expand=True)
    app.startup_guard_details_text.insert(
        "1.0",
        app.tr(
            "startup_guard_details_placeholder",
            "Startup Guard details will appear here.\n",
        ),
    )
    app.startup_guard_details_text.configure(state="disabled")
    app.attach_text_context_menu(app.startup_guard_details_text)


def build_repository_guard_tab(app):
    app.tab_repository_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_repository_guard,
        text=app.tr("security_tab_repository_guard", "Repo"),
    )

    app.repository_guard_status_var = tk.StringVar(
        value=app.tr("repository_guard_status_not_checked", "Status: Nicht geprüft")
    )
    app.repository_guard_scan_status_var = tk.StringVar(
        value=app.tr(
            "repository_guard_scan_unavailable",
            "Repository-Scan: Noch nicht verfügbar",
        )
    )
    app.repository_guard_summary_var = tk.StringVar(
        value=app.tr(
            "repository_guard_summary_empty",
            "Quellen: 0 | Befunde: 0 | Warnungen: 0 | Fehler: 0",
        )
    )
    app.repository_guard_source_filter_status_var = tk.StringVar(
        value=app.tr(
            "repository_guard_source_filter_all",
            "Quellenfilter: alle",
        )
    )
    app.repository_guard_finding_filter_status_var = tk.StringVar(
        value=app.tr(
            "repository_guard_finding_filter_relevant",
            "Befundfilter: relevant",
        )
    )
    app.repository_guard_source_filter_choice_var = tk.StringVar(
        value=app.tr("repository_guard_source_filter_btn_all", "All")
    )
    app.repository_guard_finding_filter_choice_var = tk.StringVar(
        value=app.tr("repository_guard_finding_filter_btn_relevant", "Relevant")
    )

    body = ttk.Frame(app.tab_repository_guard)
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)
    body.rowconfigure(0, weight=1)

    app.repository_guard_pane = ttk.Panedwindow(body, orient="vertical")
    app.repository_guard_pane.grid(row=0, column=0, sticky="nsew")
    app.repository_guard_pane_markers = _install_vertical_pane_drag_markers(
        body,
        app.repository_guard_pane,
    )

    status_frame = ttk.LabelFrame(
        app.repository_guard_pane,
        text=app.tr("repository_guard_group_status", "Status"),
        padding=6,
    )
    status_frame.columnconfigure(1, weight=1)
    info_frame = ttk.LabelFrame(
        app.repository_guard_pane,
        text=app.tr("repository_guard_group_info", "Information"),
        padding=8,
    )
    checks_frame = ttk.LabelFrame(
        app.repository_guard_pane,
        text=app.tr(
            "repository_guard_group_checks",
            "Geplante Analysebereiche",
        ),
        padding=8,
    )
    action_frame = ttk.LabelFrame(
        app.repository_guard_pane,
        text=app.tr("repository_guard_group_actions", "Preparation"),

        padding=8,
    )

    app.repository_guard_pane.add(status_frame, weight=0)
    app.repository_guard_pane.add(info_frame, weight=2)
    app.repository_guard_pane.add(checks_frame, weight=2)
    app.repository_guard_pane.add(action_frame, weight=5)

    app.repository_guard_status_light = tk.Canvas(
        status_frame,
        width=18,
        height=18,
        highlightthickness=0,
        bd=0,
    )
    app.repository_guard_status_light.pack(side="left", padx=(0, 8))
    app.repository_guard_status_light_item = (
        app.repository_guard_status_light.create_oval(
            2,
            2,
            16,
            16,
            fill="#7a7f87",
            outline="#7a7f87",
        )
    )

    status_text_wrap = ttk.Frame(status_frame)
    status_text_wrap.pack(side="left", fill="x", expand=True)
    ttk.Label(
        status_text_wrap,
        textvariable=app.repository_guard_scan_status_var,
    ).grid(row=0, column=0, sticky="w", padx=(0, 16))
    ttk.Label(
        status_text_wrap,
        textvariable=app.repository_guard_status_var,
    ).grid(row=0, column=1, sticky="w")
    ttk.Label(
        status_text_wrap,
        textvariable=app.repository_guard_summary_var,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))
    ttk.Label(
        status_text_wrap,
        textvariable=app.repository_guard_source_filter_status_var,
    ).grid(row=2, column=0, sticky="w", pady=(2, 0), padx=(0, 16))
    ttk.Label(
        status_text_wrap,
        textvariable=app.repository_guard_finding_filter_status_var,
    ).grid(row=2, column=1, sticky="w", pady=(2, 0))

    top_actions_row = ttk.Frame(info_frame)
    top_actions_row.pack(fill="x", pady=(0, 6))
    app.btn_repository_guard_scan = ttk.Button(
        top_actions_row,
        text=app.tr("repository_guard_btn_scan", "Repository scan"),

        command=app.run_repository_guard_scan,
    )
    app.btn_repository_guard_scan.pack(side="left")
    app.add_tooltip(
        app.btn_repository_guard_scan,
        app.tr(
            "repository_guard_btn_scan_tooltip",
            "Liest lokale APT-Paketquellen ein und bewertet erste Auffälligkeiten.",
        ),
    )

    action_buttons_row = ttk.Frame(top_actions_row)
    action_buttons_row.pack(side="right")
    app.btn_repository_guard_baseline = ttk.Button(
        action_buttons_row,
        text=app.tr("repository_guard_btn_baseline", "Save baseline"),
        command=app.create_repository_guard_baseline,
    )
    app.btn_repository_guard_baseline.pack(side="left", padx=(0, 8))
    app.add_tooltip(
        app.btn_repository_guard_baseline,
        app.tr(
            "repository_guard_btn_baseline_tooltip",
            "Speichert den aktuell erkannten Quellenzustand als neue Vergleichs-Baseline.",
        ),
    )
    app.btn_repository_guard_reset_baseline = ttk.Button(
        action_buttons_row,
        text=app.tr("repository_guard_btn_reset_baseline", "Reset baseline"),
        command=app.reset_repository_guard_baseline,
    )
    app.btn_repository_guard_reset_baseline.pack(side="left", padx=(0, 8))
    app.add_tooltip(
        app.btn_repository_guard_reset_baseline,
        app.tr(
            "repository_guard_btn_reset_baseline_tooltip",
            "Entfernt die gespeicherte Repository-Guard-Baseline und beendet Vergleiche mit dem alten Referenzstand.",
        ),
    )
    app.btn_repository_guard_clear = ttk.Button(
        action_buttons_row,
        text=app.tr("repository_guard_btn_clear", "Clear display"),
        command=app.clear_repository_guard_view,
    )
    app.btn_repository_guard_clear.pack(side="left", padx=(0, 8))
    app.add_tooltip(
        app.btn_repository_guard_clear,
        app.tr(
            "repository_guard_btn_clear_tooltip",
            "Leert die aktuelle Repository-Guard-Ansicht und setzt Auswahl, Filterstatus und Details zurück.",
        ),
    )
    app.btn_repository_guard_copy = ttk.Button(
        action_buttons_row,
        text=app.tr("repository_guard_btn_copy", "Copy result"),
        command=app.copy_repository_guard_report,
    )
    app.btn_repository_guard_copy.pack(side="left", padx=(0, 8))
    app.add_tooltip(
        app.btn_repository_guard_copy,
        app.tr(
            "repository_guard_btn_copy_tooltip",
            "Kopiert die aktuelle Repository-Guard-Zusammenfassung inklusive Detailansicht in die Zwischenablage.",
        ),
    )
    app.btn_repository_guard_export = ttk.Button(
        action_buttons_row,
        text=app.tr("repository_guard_btn_export", "Export result"),
        command=app.export_repository_guard_report,
    )
    app.btn_repository_guard_export.pack(side="left")
    app.add_tooltip(
        app.btn_repository_guard_export,
        app.tr(
            "repository_guard_btn_export_tooltip",
            "Exportiert das aktuelle Ergebnis als JSON oder Text.",
        ),
    )

    source_filter_row = ttk.Frame(info_frame)
    source_filter_row.pack(fill="x", pady=(0, 6))
    ttk.Label(
        source_filter_row,
        text=app.tr(
            "repository_guard_source_filter_label",
            "Quellen:",
        ),
    ).pack(side="left")
    source_filter_options = [
        ("all", app.tr("repository_guard_source_filter_btn_all", "All")),
        ("apt", app.tr("repository_guard_source_filter_btn_apt", "APT")),
        ("flatpak", app.tr("repository_guard_source_filter_btn_flatpak", "Flatpak")),
        ("active", app.tr("repository_guard_source_filter_btn_active", "Active")),
        (
            "third_party",
            app.tr("repository_guard_source_filter_btn_third_party", "Drittquellen"),
        ),
        ("trusted", app.tr("repository_guard_source_filter_btn_trusted", "Vertraut")),
        ("review", app.tr("repository_guard_source_filter_btn_review", "Prüfbedarf")),
    ]
    app.repository_guard_source_filter_labels = {
        mode: label for mode, label in source_filter_options
    }
    app.repository_guard_source_filter_modes_by_label = {
        label: mode for mode, label in source_filter_options
    }
    app.repository_guard_source_filter_combo = ttk.Combobox(
        source_filter_row,
        state="readonly",
        textvariable=app.repository_guard_source_filter_choice_var,
        values=[label for _mode, label in source_filter_options],
        width=18,
    )
    app.repository_guard_source_filter_combo.pack(side="left", padx=(8, 0))
    app.repository_guard_source_filter_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: app.set_repository_guard_source_filter(
            _selected_filter_mode(
                app.repository_guard_source_filter_choice_var,
                app.repository_guard_source_filter_modes_by_label,
                "all",
            )
        ),
    )
    app.add_tooltip(
        app.repository_guard_source_filter_combo,
        app.tr(
            "repository_guard_source_filter_combo_tooltip",
            "Wählt aus, welche Quellen in der oberen Ergebnisansicht angezeigt werden.",
        ),
    )
    ttk.Label(
        source_filter_row,
        text=app.tr(
            "repository_guard_finding_filter_label",
            "Befunde:",
        ),
    ).pack(side="left", padx=(16, 0))
    finding_filter_options = [
        ("all", app.tr("repository_guard_finding_filter_btn_all", "Alle")),
        (
            "relevant",
            app.tr("repository_guard_finding_filter_btn_relevant", "Relevant"),
        ),
        (
            "baseline",
            app.tr("repository_guard_finding_filter_btn_baseline", "Baseline"),
        ),
        ("keyring", app.tr("repository_guard_finding_filter_btn_keyring", "Schlüssel")),
        ("review", app.tr("repository_guard_finding_filter_btn_review", "Prüfbedarf")),
        ("notices", app.tr("repository_guard_finding_filter_btn_notices", "Hinweise")),
    ]
    app.repository_guard_finding_filter_labels = {
        mode: label for mode, label in finding_filter_options
    }
    app.repository_guard_finding_filter_modes_by_label = {
        label: mode for mode, label in finding_filter_options
    }
    app.repository_guard_finding_filter_combo = ttk.Combobox(
        source_filter_row,
        state="readonly",
        textvariable=app.repository_guard_finding_filter_choice_var,
        values=[label for _mode, label in finding_filter_options],
        width=18,
    )
    app.repository_guard_finding_filter_combo.pack(side="left", padx=(8, 0))
    app.repository_guard_finding_filter_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: app.set_repository_guard_finding_filter(
            _selected_filter_mode(
                app.repository_guard_finding_filter_choice_var,
                app.repository_guard_finding_filter_modes_by_label,
                "relevant",
            )
        ),
    )
    app.add_tooltip(
        app.repository_guard_finding_filter_combo,
        app.tr(
            "repository_guard_finding_filter_combo_tooltip",
            "Wählt aus, welche Befunde im mittleren Ergebnisfenster angezeigt werden.",
        ),
    )

    info_wrap = ttk.Frame(info_frame)
    info_wrap.pack(fill="both", expand=True)
    info_wrap.columnconfigure(0, weight=1)
    info_wrap.rowconfigure(0, weight=1)
    info_scroll_y = ttk.Scrollbar(info_wrap, orient="vertical")
    info_scroll_y.grid(row=0, column=1, sticky="ns")
    info_scroll_x = ttk.Scrollbar(info_wrap, orient="horizontal")
    info_scroll_x.grid(row=1, column=0, sticky="ew")
    app.repository_guard_sources_tree = ttk.Treeview(
        info_wrap,
        columns=(
            "state",
            "type",
            "trust",
            "host",
            "suite",
            "components",
            "uri",
            "file",
        ),
        show="headings",
        height=6,
        yscrollcommand=info_scroll_y.set,
        xscrollcommand=info_scroll_x.set,
    )
    for col, title, width, anchor in [
        ("state", app.tr("repository_guard_col_state", "Status"), 90, "center"),
        ("type", app.tr("repository_guard_col_type", "Typ"), 80, "center"),
        ("trust", app.tr("repository_guard_trust_label", "Vertrauen").rstrip(":"), 95, "center"),
        ("host", "Host", 180, "w"),
        ("suite", "Suite", 110, "w"),
        ("components", app.tr("repository_guard_col_components", "Komponenten"), 180, "w"),
        ("uri", "URI", 300, "w"),
        ("file", app.tr("repository_guard_col_file", "Datei"), 300, "w"),
    ]:
        app.repository_guard_sources_tree.heading(col, text=title)
        app.repository_guard_sources_tree.column(col, width=width, anchor=anchor)
    app.repository_guard_sources_tree.grid(row=0, column=0, sticky="nsew")
    info_scroll_y.configure(command=app.repository_guard_sources_tree.yview)
    info_scroll_x.configure(command=app.repository_guard_sources_tree.xview)
    app.repository_guard_sources_tree.bind(
        "<<TreeviewSelect>>",
        app.on_repository_guard_source_select,
    )
    app.attach_repository_guard_sources_context_menu()

    checks_wrap = ttk.Frame(checks_frame)
    checks_wrap.pack(fill="both", expand=True)
    checks_wrap.columnconfigure(0, weight=1)
    checks_wrap.rowconfigure(0, weight=1)
    checks_scroll_y = ttk.Scrollbar(checks_wrap, orient="vertical")
    checks_scroll_y.grid(row=0, column=1, sticky="ns")
    checks_scroll_x = ttk.Scrollbar(checks_wrap, orient="horizontal")
    checks_scroll_x.grid(row=1, column=0, sticky="ew")
    app.repository_guard_findings_tree = ttk.Treeview(
        checks_wrap,
        columns=("severity", "code", "summary"),
        show="headings",
        height=6,
        yscrollcommand=checks_scroll_y.set,
        xscrollcommand=checks_scroll_x.set,
    )
    for col, title, width, anchor in [
        ("severity", app.tr("repository_guard_col_severity", "Schwere"), 100, "center"),
        ("code", "Code", 220, "w"),
        ("summary", app.tr("repository_guard_col_summary", "Zusammenfassung"), 520, "w"),
    ]:
        app.repository_guard_findings_tree.heading(col, text=title)
        app.repository_guard_findings_tree.column(col, width=width, anchor=anchor)
    app.repository_guard_findings_tree.grid(row=0, column=0, sticky="nsew")
    checks_scroll_y.configure(command=app.repository_guard_findings_tree.yview)
    checks_scroll_x.configure(command=app.repository_guard_findings_tree.xview)
    app.repository_guard_findings_tree.bind(
        "<<TreeviewSelect>>",
        app.on_repository_guard_finding_select,
    )
    app.attach_repository_guard_findings_context_menu()

    ttk.Label(
        info_frame,
        text=app.tr(
            "repository_guard_sources_hint",
            "Erfasste Paketquellen erscheinen hier nach einem Repository-Scan.",
        ),
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    ttk.Label(
        checks_frame,
        text=app.tr(
            "repository_guard_findings_hint",
            "Bewertete Befunde erscheinen hier nach dem Scan.",
        ),
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    action_frame.columnconfigure(0, weight=1)
    action_frame.rowconfigure(2, weight=1)

    ttk.Label(
        action_frame,
        text=app.tr(
            "repository_guard_placeholder_intro",
            "V1 liest aktuell lokale APT-.list-Quellen ein und bewertet erste Signale.",
        ),
        justify="left",
    ).grid(row=0, column=0, sticky="w")

    trust_row = ttk.Frame(action_frame)
    trust_row.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    ttk.Label(
        trust_row,
        text=app.tr("repository_guard_trust_label", "Vertrauen:"),
    ).pack(side="left")
    app.btn_repository_guard_mark_trusted = ttk.Button(
        trust_row,
        text=app.tr("repository_guard_btn_mark_trusted", "Host vertrauen"),
        command=app.mark_selected_repository_guard_trusted,
    )
    app.btn_repository_guard_mark_trusted.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_repository_guard_mark_trusted,
        app.tr(
            "repository_guard_btn_mark_trusted_tooltip",
            "Markiert den Host der ausgewählten Quelle als bewusst vertraut und reduziert passende Herkunftshinweise.",
        ),
    )
    app.btn_repository_guard_remove_trusted = ttk.Button(
        trust_row,
        text=app.tr("repository_guard_btn_remove_trusted", "Vertrauen entfernen"),
        command=app.remove_selected_repository_guard_trusted,
    )
    app.btn_repository_guard_remove_trusted.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_repository_guard_remove_trusted,
        app.tr(
            "repository_guard_btn_remove_trusted_tooltip",
            "Entfernt den Host der ausgewählten Quelle wieder aus der Repository-Trustlist.",
        ),
    )
    app.btn_repository_guard_show_trustlist = ttk.Button(
        trust_row,
        text=app.tr("repository_guard_btn_show_trustlist", "Vertrauensliste anzeigen"),
        command=app.show_repository_guard_trustlist,
    )
    app.btn_repository_guard_show_trustlist.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_repository_guard_show_trustlist,
        app.tr(
            "repository_guard_btn_show_trustlist_tooltip",
            "Zeigt die aktuell gespeicherten vertrauenswürdigen Repository-Hosts im Detailbereich an.",
        ),
    )
    app.btn_repository_guard_reset_trustlist = ttk.Button(
        trust_row,
        text=app.tr("repository_guard_btn_reset_trustlist", "Vertrauensliste zurücksetzen"),
        command=app.reset_repository_guard_trustlist,
    )
    app.btn_repository_guard_reset_trustlist.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_repository_guard_reset_trustlist,
        app.tr(
            "repository_guard_btn_reset_trustlist_tooltip",
            "Leert die komplette Repository-Trustlist und bewertet Hosts danach wieder neutral.",
        ),
    )

    detail_frame = ttk.LabelFrame(
        action_frame,
        text=app.tr("repository_guard_details_title", "Details"),
        padding=6,
    )
    detail_frame.grid(row=2, column=0, sticky="nsew", pady=(10, 0))
    detail_frame.columnconfigure(0, weight=1)
    detail_frame.rowconfigure(0, weight=1)

    app.repository_guard_detail_text = tk.Text(
        detail_frame,
        wrap="word",
        height=18,
    )
    app.repository_guard_detail_text.grid(row=0, column=0, sticky="nsew")
    app.repository_guard_detail_text.insert(
        "1.0",
        app.tr(
            "repository_guard_detail_placeholder",
            "Repository Guard Details erscheinen hier.\n",
        ),
    )
    app.repository_guard_detail_text.configure(state="disabled")
    app.attach_repository_guard_detail_context_menu()

    future_host = ttk.Frame(action_frame)
    future_host.grid(row=3, column=0, sticky="nsew", pady=(12, 0))
    future_host.columnconfigure(0, weight=1)
    future_host.rowconfigure(0, weight=1)
    app.security_future_modules_host = future_host


def build_roots_baseline_guard_tab(app):
    # source markers:
    # text="System Integrity Status"
    # text="Überwachte Bereiche"
    # text="Baseline Verwaltung"
    # text="Mit Root lesen / prüfen"
    # text="Baseline Änderungen"
    # text="Chad Analyse"
    # text="Verlauf / History"
    # text="Vertrauenswürdige Änderungen"
    app.tab_roots_baseline_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_roots_baseline_guard,
        text=app.tr("security_tab_roots_baseline_guard", "Roots Baseline Guard"),
    )

    wrap = ttk.Frame(app.tab_roots_baseline_guard)
    wrap.pack(fill="both", expand=True)

    app.roots_baseline_guard_canvas = tk.Canvas(wrap, highlightthickness=0)
    app.roots_baseline_guard_canvas.pack(side="left", fill="both", expand=True)

    app.roots_baseline_guard_scrollbar = ttk.Scrollbar(
        wrap,
        orient="vertical",
        command=app.roots_baseline_guard_canvas.yview,
    )
    app.roots_baseline_guard_scrollbar.pack(side="right", fill="y")
    app.roots_baseline_guard_canvas.configure(
        yscrollcommand=app.roots_baseline_guard_scrollbar.set
    )

    app.roots_baseline_guard_scroll_frame = ttk.Frame(app.roots_baseline_guard_canvas)
    app.roots_baseline_guard_canvas_window = (
        app.roots_baseline_guard_canvas.create_window(
            (0, 0),
            window=app.roots_baseline_guard_scroll_frame,
            anchor="nw",
        )
    )

    def _on_roots_guard_frame_config(_event):
        app.roots_baseline_guard_canvas.configure(
            scrollregion=app.roots_baseline_guard_canvas.bbox("all")
        )
        try:
            canvas_height = int(app.roots_baseline_guard_canvas.winfo_height() or 0)
            frame_height = int(
                app.roots_baseline_guard_scroll_frame.winfo_reqheight() or 0
            )
            app.roots_baseline_guard_canvas.itemconfig(
                app.roots_baseline_guard_canvas_window,
                height=max(canvas_height, frame_height),
            )
        except Exception:
            pass

    def _on_roots_guard_canvas_config(event):
        app.roots_baseline_guard_canvas.itemconfig(
            app.roots_baseline_guard_canvas_window,
            width=event.width,
        )
        try:
            frame_height = int(
                app.roots_baseline_guard_scroll_frame.winfo_reqheight() or 0
            )
            app.roots_baseline_guard_canvas.itemconfig(
                app.roots_baseline_guard_canvas_window,
                height=max(int(event.height or 0), frame_height),
            )
        except Exception:
            pass

    app.roots_baseline_guard_scroll_frame.bind(
        "<Configure>", _on_roots_guard_frame_config
    )
    app.roots_baseline_guard_canvas.bind("<Configure>", _on_roots_guard_canvas_config)

    body = app.roots_baseline_guard_scroll_frame
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=1)
    body.rowconfigure(2, weight=1)

    app.roots_integrity_status_var = tk.StringVar(
        value=app.tr(
            "roots_status_no_critical_changes",
            "No critical changes detected",
        )
    )
    app.roots_integrity_counts_var = tk.StringVar(
        value=app.tr(
            "roots_status_counts_default",
            "Critical: 0 | Warnings: 0 | Notices: 0",
        )
    )
    app.roots_baseline_status_var = tk.StringVar(
        value=app.tr("roots_status_no_baseline", "No baseline created yet.")
    )
    app.roots_baseline_created_var = tk.StringVar(
        value=app.tr(
            "roots_status_created_default",
            "Baseline created: not created yet",
        )
    )
    app.roots_baseline_updated_var = tk.StringVar(
        value=app.tr(
            "roots_status_updated_default",
            "Baseline updated: not updated yet",
        )
    )
    app.roots_baseline_checked_var = tk.StringVar(
        value=app.tr(
            "roots_status_checked_default",
            "Last check: not performed yet",
        )
    )
    app.roots_last_root_action_var = tk.StringVar(
        value=app.tr("roots_status_last_root_action", "Last action with root: no")
    )
    app.roots_root_mode_status_var = tk.StringVar(
        value=app.tr("roots_status_root_mode_off", "Root mode: off")
    )
    app.roots_signal_summary_var = tk.StringVar(
        value=app.tr("roots_status_findings_default", "Findings: -")
    )

    status_frame = ttk.LabelFrame(
        body,
        text=app.tr("roots_group_integrity_status", "System Integrity Status"),
        padding=8,
    )
    status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
    status_frame.columnconfigure(1, weight=1)
    status_frame.columnconfigure(2, weight=0)

    app.roots_integrity_light = tk.Canvas(
        status_frame,
        width=18,
        height=18,
        highlightthickness=0,
        bd=0,
    )
    app.roots_integrity_light.grid(row=0, column=0, sticky="w", padx=(0, 8))
    app.roots_integrity_light_item = app.roots_integrity_light.create_oval(
        2,
        2,
        16,
        16,
        fill="#2fbf71",
        outline="#2fbf71",
    )
    ttk.Label(status_frame, textvariable=app.roots_integrity_status_var).grid(
        row=0, column=1, sticky="w"
    )
    roots_root_mode_label_kwargs = {
        "textvariable": app.roots_root_mode_status_var,
        "fg": "#7a7f87",
    }
    try:
        roots_root_mode_label_kwargs["bg"] = app.cget("bg")
    except Exception:
        pass
    app.roots_root_mode_status_label = tk.Label(
        status_frame,
        **roots_root_mode_label_kwargs,
    )
    app.roots_root_mode_status_label.grid(row=0, column=2, sticky="e", padx=(12, 0))
    ttk.Label(status_frame, textvariable=app.roots_integrity_counts_var).grid(
        row=1, column=1, sticky="w", pady=(6, 0)
    )
    ttk.Label(status_frame, textvariable=app.roots_signal_summary_var).grid(
        row=1, column=2, sticky="e", padx=(12, 0), pady=(6, 0)
    )

    monitored_frame = ttk.LabelFrame(
        body,
        text=app.tr("roots_group_monitored_areas", "Monitored areas"),
        padding=8,
    )
    monitored_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))
    monitored_frame.columnconfigure(0, weight=1)
    monitored_frame.columnconfigure(1, weight=1)
    monitored_frame.rowconfigure(1, weight=0)

    monitored_core_frame = ttk.LabelFrame(
        monitored_frame,
        text=app.tr("roots_group_core_config", "Core system and configuration"),
        padding=6,
    )
    monitored_core_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 0))
    monitored_runtime_frame = ttk.LabelFrame(
        monitored_frame,
        text=app.tr("roots_group_runtime_services", "Services and runtime environment"),
        padding=6,
    )
    monitored_runtime_frame.grid(
        row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 0)
    )

    monitored_groups = [
        (
            monitored_core_frame,
            [
                app.tr("roots_area_users_permissions", "Users / permissions"),
                app.tr("roots_area_ssh_config", "SSH configuration"),
                app.tr("roots_area_dns_hosts", "DNS / hosts"),
                app.tr("roots_area_package_sources", "Package sources"),
                app.tr("roots_area_firewall", "Firewall"),
                app.tr("roots_area_critical_system_files", "Critical system files"),
            ],
        ),
        (
            monitored_runtime_frame,
            [
                app.tr(
                    "roots_area_autostart_systemd_cron",
                    "Autostart / systemd / cron",
                ),
                app.tr("roots_area_shell_profiles", "Shell profiles"),
                app.tr("roots_area_network_configuration", "Network configuration"),
                app.tr(
                    "roots_area_security_relevant_services",
                    "Security-relevant services",
                ),
            ],
        ),
    ]
    app.roots_baseline_guard_scope_vars = {}
    for frame, labels in monitored_groups:
        frame.columnconfigure(0, weight=1)
        for index, label in enumerate(labels):
            var = tk.BooleanVar(value=label in ROOTS_GUARD_INITIAL_ENABLED_AREAS)
            app.roots_baseline_guard_scope_vars[label] = var
            ttk.Checkbutton(frame, text=label, variable=var).grid(
                row=index,
                column=0,
                sticky="w",
                pady=(3, 3),
            )

    baseline_hint_frame = ttk.LabelFrame(
        monitored_frame,
        text=app.tr("roots_group_status", "Status"),
        padding=6,
    )
    baseline_hint_frame.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(8, 0))
    ttk.Label(
        baseline_hint_frame,
        textvariable=app.roots_baseline_status_var,
        wraplength=280,
        justify="left",
    ).pack(anchor="w")
    ttk.Label(
        baseline_hint_frame,
        textvariable=app.roots_baseline_created_var,
        wraplength=280,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))
    ttk.Label(
        baseline_hint_frame,
        textvariable=app.roots_baseline_updated_var,
        wraplength=280,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))
    ttk.Label(
        baseline_hint_frame,
        textvariable=app.roots_baseline_checked_var,
        wraplength=280,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))
    ttk.Label(
        baseline_hint_frame,
        textvariable=app.roots_last_root_action_var,
        wraplength=280,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    baseline_frame = ttk.LabelFrame(
        body,
        text=app.tr("roots_group_baseline_management", "Baseline management"),
        padding=8,
    )
    baseline_frame.grid(row=1, column=1, sticky="nw", padx=(10, 12), pady=(0, 8))
    baseline_frame.columnconfigure(0, weight=1)

    baseline_actions_frame = ttk.LabelFrame(
        baseline_frame,
        text=app.tr("roots_group_actions", "Actions"),
        padding=6,
    )
    baseline_actions_frame.pack(fill="x")

    app.roots_baseline_guard_root_mode_var = tk.BooleanVar(value=False)
    ttk.Checkbutton(
        baseline_actions_frame,
        text=app.tr("roots_baseline_check_root_mode", "Read / check with root"),
        variable=app.roots_baseline_guard_root_mode_var,
    ).pack(anchor="w", pady=(0, 6))
    try:
        app.roots_baseline_guard_root_mode_var.trace_add(
            "write",
            lambda *_args: app.refresh_roots_baseline_guard_root_mode_status(),
        )
    except Exception:
        pass
    ttk.Label(
        baseline_actions_frame,
        text=app.tr(
            "roots_label_root_scope",
            "Root is requested only for this read/check operation, not for the entire GUI.",
        ),
        justify="left",
        wraplength=220,
    ).pack(anchor="w", pady=(0, 6))

    app.btn_roots_baseline_guard_read_current_state = ttk.Button(
        baseline_actions_frame,
        text=app.tr(
            "roots_baseline_btn_read_current_state",
            "Read current state",
        ),
        command=app.roots_baseline_guard_read_current_state,
    )
    app.btn_roots_baseline_guard_read_current_state.pack(fill="x")
    app.btn_roots_baseline_guard_create_baseline = ttk.Button(
        baseline_actions_frame,
        text=app.tr("roots_baseline_btn_create", "Create baseline"),
        command=app.roots_baseline_guard_create_baseline,
    )
    app.btn_roots_baseline_guard_create_baseline.pack(fill="x", pady=(6, 0))
    app.btn_roots_baseline_guard_check_baseline = ttk.Button(
        baseline_actions_frame,
        text=app.tr("roots_baseline_btn_check", "Check baseline"),
        command=app.roots_baseline_guard_check_baseline,
    )
    app.btn_roots_baseline_guard_check_baseline.pack(fill="x", pady=(6, 0))
    app.btn_roots_baseline_guard_update_baseline = ttk.Button(
        baseline_actions_frame,
        text=app.tr("roots_baseline_btn_update", "Update baseline"),
        command=app.roots_baseline_guard_update_baseline,
    )
    app.btn_roots_baseline_guard_update_baseline.pack(fill="x", pady=(6, 0))
    app.btn_roots_baseline_guard_show_last_comparison = ttk.Button(
        baseline_actions_frame,
        text=app.tr(
            "roots_baseline_btn_show_last_comparison",
            "Show last comparison",
        ),
        command=app.roots_baseline_guard_show_last_comparison,
    )
    app.btn_roots_baseline_guard_show_last_comparison.pack(fill="x", pady=(6, 0))
    app.btn_roots_baseline_guard_load_demo = ttk.Button(
        baseline_actions_frame,
        text=app.tr("roots_baseline_btn_load_demo", "Load demo cases"),
        command=app.load_roots_baseline_guard_demo_cases,
    )
    app.btn_roots_baseline_guard_load_demo.pack(fill="x", pady=(6, 0))
    app.btn_roots_baseline_guard_clear_view = ttk.Button(
        baseline_actions_frame,
        text=app.tr("roots_baseline_btn_clear_view", "Clear view"),
        command=app.clear_roots_baseline_guard_view,
    )
    app.btn_roots_baseline_guard_clear_view.pack(fill="x", pady=(6, 0))

    roots_results_pane_host = ttk.Frame(body)
    roots_results_pane_host.grid(
        row=2, column=0, columnspan=2, sticky="nsew", pady=(0, 8)
    )
    roots_results_pane_host.columnconfigure(0, weight=1)
    roots_results_pane_host.rowconfigure(0, weight=1)

    app.roots_baseline_guard_pane = ttk.Panedwindow(
        roots_results_pane_host,
        orient="vertical",
    )
    app.roots_baseline_guard_pane.grid(row=0, column=0, sticky="nsew")
    app.roots_baseline_guard_pane_markers = _install_vertical_pane_drag_markers(
        roots_results_pane_host,
        app.roots_baseline_guard_pane,
        min_pane_size=0,
    )

    results_frame = ttk.LabelFrame(
        app.roots_baseline_guard_pane,
        text=app.tr("roots_group_baseline_changes", "Baseline changes"),
        padding=8,
    )
    results_frame.columnconfigure(0, weight=1)
    results_frame.rowconfigure(0, weight=1)

    results_table_frame = ttk.Frame(results_frame)
    results_table_frame.grid(row=0, column=0, sticky="nsew")
    results_table_frame.columnconfigure(0, weight=1)
    results_table_frame.rowconfigure(0, weight=1)

    roots_results_scroll_y = ttk.Scrollbar(
        results_table_frame,
        orient="vertical",
    )
    roots_results_scroll_y.grid(row=0, column=1, sticky="ns")
    roots_results_scroll_x = ttk.Scrollbar(
        results_table_frame,
        orient="horizontal",
    )
    roots_results_scroll_x.grid(row=1, column=0, sticky="ew")

    app.roots_baseline_guard_results_table = ttk.Treeview(
        results_table_frame,
        columns=("area", "change", "risk", "time", "status"),
        show="headings",
        selectmode="extended",
        height=7,
        yscrollcommand=roots_results_scroll_y.set,
        xscrollcommand=roots_results_scroll_x.set,
    )
    for col, title, width, anchor in [
        ("area", app.tr("roots_col_area", "File / area"), 340, "w"),
        ("change", app.tr("roots_col_change", "Change"), 210, "w"),
        ("risk", app.tr("roots_col_risk", "Risk"), 100, "center"),
        ("time", app.tr("roots_col_time", "Time"), 150, "center"),
        ("status", app.tr("roots_col_status", "Status"), 120, "center"),
    ]:
        app.roots_baseline_guard_results_table.heading(col, text=title)
        app.roots_baseline_guard_results_table.column(col, width=width, anchor=anchor)
    app.roots_baseline_guard_results_table.grid(row=0, column=0, sticky="nsew")
    roots_results_scroll_y.configure(
        command=app.roots_baseline_guard_results_table.yview
    )
    roots_results_scroll_x.configure(
        command=app.roots_baseline_guard_results_table.xview
    )
    app.roots_baseline_guard_results_table.insert(
        "",
        "end",
        values=(
            app.tr("roots_results_no_changes", "No changes detected yet."),
            "-",
            "-",
            "-",
            app.tr("roots_results_placeholder_status", "Placeholder"),
        ),
    )
    app.roots_baseline_guard_results_table.bind(
        "<<TreeviewSelect>>",
        app.on_roots_baseline_guard_result_select,
    )
    app.attach_selection_copy_shortcuts(
        app.roots_baseline_guard_results_table, "treeview"
    )
    app.attach_roots_baseline_guard_tree_context_menu()

    roots_lower_frame = ttk.Frame(app.roots_baseline_guard_pane)
    roots_lower_frame.columnconfigure(0, weight=1)
    roots_lower_frame.rowconfigure(0, weight=1)

    app.roots_baseline_guard_pane.add(results_frame, weight=3)
    app.roots_baseline_guard_pane.add(roots_lower_frame, weight=2)

    roots_lower_pane_host = ttk.Frame(roots_lower_frame)
    roots_lower_pane_host.grid(row=0, column=0, sticky="nsew")
    roots_lower_pane_host.columnconfigure(0, weight=1)
    roots_lower_pane_host.rowconfigure(0, weight=1)

    app.roots_baseline_guard_lower_pane = ttk.Panedwindow(
        roots_lower_pane_host,
        orient="vertical",
    )
    app.roots_baseline_guard_lower_pane.grid(row=0, column=0, sticky="nsew")
    app.roots_baseline_guard_lower_pane_markers = _install_vertical_pane_drag_markers(
        roots_lower_pane_host,
        app.roots_baseline_guard_lower_pane,
        min_pane_size=0,
    )

    roots_lower_top = ttk.Frame(app.roots_baseline_guard_lower_pane)
    roots_lower_top.columnconfigure(0, weight=1)
    roots_lower_top.columnconfigure(1, weight=1)
    roots_lower_top.rowconfigure(0, weight=1)
    roots_lower_top.rowconfigure(1, weight=1)

    chad_frame = ttk.LabelFrame(
        roots_lower_top,
        text=app.tr("roots_group_chad_analysis", "Chad analysis"),
        padding=8,
    )
    chad_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 8))

    chad_options = [
        (
            "Nur kritische Änderungen analysieren",
            app.tr("roots_chad_option_critical_only", "Analyze critical changes only"),
        ),
        (
            "Anfängerfreundlich erklären",
            app.tr("roots_chad_option_beginner_friendly", "Explain in a beginner-friendly way"),
        ),
        (
            "Handlungsempfehlungen anzeigen",
            app.tr("roots_chad_option_show_recommendations", "Show recommendations"),
        ),
        (
            "Technische Details anzeigen",
            app.tr("roots_chad_option_show_technical", "Show technical details"),
        ),
        (
            "Reparaturvorschläge anzeigen",
            app.tr("roots_chad_option_show_repairs", "Show repair suggestions"),
        ),
    ]
    app.roots_baseline_guard_chad_vars = {}
    for index, (option_key, label) in enumerate(chad_options):
        var = tk.BooleanVar(value=index in {0, 1, 2})
        app.roots_baseline_guard_chad_vars[option_key] = var
        ttk.Checkbutton(chad_frame, text=label, variable=var).pack(
            anchor="w", pady=(2, 2)
        )

    chad_button_row = ttk.Frame(chad_frame)
    chad_button_row.pack(fill="x", pady=(8, 0))
    app.btn_roots_baseline_guard_analyze_chad = ttk.Button(
        chad_button_row,
        text=app.tr("roots_baseline_btn_chad_analyze", "Start Chad analysis"),
        command=app.analyze_roots_baseline_guard_with_chad,
    )
    app.btn_roots_baseline_guard_analyze_chad.pack(side="left")
    app.btn_roots_baseline_guard_explain_change = ttk.Button(
        chad_button_row,
        text=app.tr("roots_baseline_btn_explain_change", "Explain change"),
        command=app.explain_selected_roots_baseline_guard_change,
    )
    app.btn_roots_baseline_guard_explain_change.pack(side="left", padx=(8, 0))

    history_frame = ttk.LabelFrame(
        roots_lower_top,
        text=app.tr("roots_group_history", "History"),
        padding=8,
    )
    history_frame.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 8))
    history_frame.columnconfigure(0, weight=1)
    history_frame.rowconfigure(0, weight=1)
    history_frame.rowconfigure(1, weight=0)

    roots_history_scroll_x = ttk.Scrollbar(
        history_frame,
        orient="horizontal",
    )
    roots_history_scroll_x.grid(row=1, column=0, sticky="ew", pady=(6, 0))

    app.roots_baseline_guard_history_list = tk.Listbox(
        history_frame,
        height=7,
        xscrollcommand=roots_history_scroll_x.set,
    )
    app.roots_baseline_guard_history_list.grid(row=0, column=0, sticky="nsew")
    roots_history_scroll_x.configure(
        command=app.roots_baseline_guard_history_list.xview
    )
    for item in (
        app.tr("roots_history_last_baseline_default", "Last baseline: not created yet"),
        app.tr("roots_history_last_check_default", "Last check: not performed yet"),
        app.tr("roots_history_found_changes", "Found changes: {count}").format(count=0),
        app.tr("roots_history_accepted_changes", "Accepted changes: {count}").format(count=0),
    ):
        app.roots_baseline_guard_history_list.insert("end", item)
    app.attach_selection_copy_shortcuts(
        app.roots_baseline_guard_history_list, "listbox"
    )
    app.attach_chad_listbox_context_menu(
        app.roots_baseline_guard_history_list,
        "Roots Baseline Guard history analysis",
    )

    trust_frame = ttk.LabelFrame(
        roots_lower_top,
        text=app.tr("roots_group_trusted_changes", "Trusted changes"),
        padding=8,
    )
    trust_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(0, 8))

    trust_options = [
        (
            "Bekannte Systemänderungen ignorieren",
            app.tr("roots_trust_option_ignore_known", "Ignore known system changes"),
        ),
        (
            "Paketupdates niedriger einstufen",
            app.tr("roots_trust_option_lower_package_updates", "Rate package updates lower"),
        ),
        (
            "Benutzer-Whitelist berücksichtigen",
            app.tr("roots_trust_option_respect_user_whitelist", "Respect user whitelist"),
        ),
        (
            "Wiederkehrende harmlose Änderungen minimieren",
            app.tr(
                "roots_trust_option_minimize_recurring_harmless",
                "Minimize recurring harmless changes",
            ),
        ),
    ]
    app.roots_baseline_guard_trust_vars = {}
    for option_key, label in trust_options:
        var = tk.BooleanVar(value=False)
        app.roots_baseline_guard_trust_vars[option_key] = var
        ttk.Checkbutton(trust_frame, text=label, variable=var).pack(
            anchor="w", pady=(2, 2)
        )

    trust_button_row = ttk.Frame(trust_frame)
    trust_button_row.pack(fill="x", pady=(8, 0))
    app.btn_roots_baseline_guard_add_whitelist = ttk.Button(
        trust_button_row,
        text=app.tr("roots_baseline_btn_add_whitelist", "Add to whitelist"),
        command=app.add_selected_roots_baseline_guard_change_to_whitelist,
    )
    app.btn_roots_baseline_guard_add_whitelist.pack(side="left")
    app.btn_roots_baseline_guard_remove_whitelist = ttk.Button(
        trust_button_row,
        text=app.tr(
            "roots_baseline_btn_remove_whitelist",
            "Remove from whitelist",
        ),
        command=app.remove_selected_roots_baseline_guard_change_from_whitelist,
    )
    app.btn_roots_baseline_guard_remove_whitelist.pack(side="left", padx=(8, 0))
    app.btn_roots_baseline_guard_show_whitelist = ttk.Button(
        trust_button_row,
        text=app.tr("roots_baseline_btn_show_whitelist", "Show whitelist"),
        command=app.show_roots_baseline_guard_whitelist,
    )
    app.btn_roots_baseline_guard_show_whitelist.pack(side="left", padx=(8, 0))

    trust_list_frame = ttk.Frame(trust_frame)
    trust_list_frame.pack(fill="both", expand=True, pady=(8, 0))
    trust_list_frame.columnconfigure(0, weight=1)
    trust_list_frame.rowconfigure(0, weight=1)
    trust_list_frame.rowconfigure(1, weight=0)

    roots_whitelist_scroll_y = ttk.Scrollbar(
        trust_list_frame,
        orient="vertical",
    )
    roots_whitelist_scroll_y.grid(row=0, column=1, sticky="ns")
    roots_whitelist_scroll_x = ttk.Scrollbar(
        trust_list_frame,
        orient="horizontal",
    )
    roots_whitelist_scroll_x.grid(row=1, column=0, sticky="ew", pady=(6, 0))

    app.roots_baseline_guard_whitelist_list = tk.Listbox(
        trust_list_frame,
        height=4,
        yscrollcommand=roots_whitelist_scroll_y.set,
        xscrollcommand=roots_whitelist_scroll_x.set,
    )
    app.roots_baseline_guard_whitelist_list.grid(row=0, column=0, sticky="nsew")
    roots_whitelist_scroll_y.configure(
        command=app.roots_baseline_guard_whitelist_list.yview
    )
    roots_whitelist_scroll_x.configure(
        command=app.roots_baseline_guard_whitelist_list.xview
    )
    app.roots_baseline_guard_whitelist_list.bind(
        "<<ListboxSelect>>",
        app.on_roots_baseline_guard_whitelist_select,
    )
    app.roots_baseline_guard_whitelist_list.bind(
        "<Double-Button-1>",
        app.open_selected_roots_baseline_guard_whitelist_entry,
    )
    app.attach_selection_copy_shortcuts(
        app.roots_baseline_guard_whitelist_list, "listbox"
    )

    info_frame = ttk.LabelFrame(
        app.roots_baseline_guard_lower_pane,
        text=app.tr("roots_group_details_context", "Details / Kontext"),
        padding=8,
    )
    info_frame.columnconfigure(0, weight=1)
    info_frame.rowconfigure(0, weight=1)

    info_scroll_y = ttk.Scrollbar(info_frame, orient="vertical")
    info_scroll_y.grid(row=0, column=1, sticky="ns")

    app.roots_baseline_guard_info_text = tk.Text(
        info_frame,
        wrap="word",
        height=6,
        yscrollcommand=info_scroll_y.set,
    )
    app.roots_baseline_guard_info_text.grid(row=0, column=0, sticky="nsew")
    info_scroll_y.configure(command=app.roots_baseline_guard_info_text.yview)
    app.roots_baseline_guard_info_text.insert(
        "1.0",
        "Roots Baseline Guard is prepared as a working foundation. "
        "Baseline logic, file monitoring, and analysis will be connected step by step later.",
    )
    app.roots_baseline_guard_info_text.configure(state="disabled")
    app.roots_baseline_guard_lower_pane.add(roots_lower_top, weight=3)
    app.roots_baseline_guard_lower_pane.add(info_frame, weight=2)
    app.attach_chad_context_menu(
        app.roots_baseline_guard_info_text,
        "Roots Baseline Guard detail analysis",
    )


def build_firewall_tab(app):
    app.tab_firewall = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_firewall,
        text=app.tr("security_tab_firewall", "FW"),
    )

    app.firewall_tab_status_var = tk.StringVar(
        value=app.tr("firewall_status_unknown", "UFW: unbekannt")
    )
    app.firewall_tab_default_in_var = tk.StringVar(
        value=app.tr("firewall_status_inbound_default", "Eingehend: -")
    )
    app.firewall_tab_default_out_var = tk.StringVar(
        value=app.tr("firewall_status_outbound_default", "Ausgehend: -")
    )
    app.firewall_tab_logging_var = tk.StringVar(
        value=app.tr("firewall_status_logging_default", "Logging: -")
    )
    app.firewall_tab_logging_menu_var = tk.StringVar(
        value=app.tr("firewall_status_menu_default", "UFW Logging: -")
    )
    app.firewall_tab_rule_count_var = tk.StringVar(
        value=app.tr("firewall_status_rule_count_default", "Regeln: 0")
    )
    app.firewall_tab_external_open_var = tk.StringVar(
        value=app.tr("firewall_status_external_ports_default", "Externe Ports: 0")
    )
    app.firewall_tab_listener_count_var = tk.StringVar(
        value=app.tr("firewall_status_listener_count_default", "Lokale Listener: 0")
    )
    app.firewall_tab_last_check_var = tk.StringVar(
        value=app.tr("firewall_status_last_check_default", "Letzter Check: Noch kein Check")
    )

    frame = app.tab_firewall
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)

    app.firewall_tab_pane = ttk.Panedwindow(frame, orient="vertical")
    app.firewall_tab_pane.grid(row=0, column=0, sticky="nsew")
    app.firewall_tab_pane_markers = _install_vertical_pane_drag_markers(
        frame, app.firewall_tab_pane
    )

    top = ttk.Frame(app.firewall_tab_pane, padding=0)
    top.columnconfigure(0, weight=1)
    top.rowconfigure(0, weight=0)
    top.rowconfigure(1, weight=0)
    top.rowconfigure(2, weight=0)

    status_group = ttk.LabelFrame(
        top,
        text=app.tr("firewall_group_status", "Firewall Status"),
        padding=8,
    )
    status_group.grid(row=0, column=0, sticky="ew", pady=(0, 8))
    for col in range(4):
        status_group.columnconfigure(col, weight=1)

    ttk.Label(status_group, textvariable=app.firewall_tab_status_var).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_rule_count_var).grid(
        row=0, column=1, sticky="w", padx=(8, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_external_open_var).grid(
        row=0, column=2, sticky="w", padx=(8, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_listener_count_var).grid(
        row=0, column=3, sticky="w", padx=(8, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_default_in_var).grid(
        row=1, column=0, sticky="w", pady=(4, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_default_out_var).grid(
        row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_logging_var).grid(
        row=1, column=2, sticky="w", padx=(8, 0), pady=(4, 0)
    )
    ttk.Label(status_group, textvariable=app.firewall_tab_last_check_var).grid(
        row=1, column=3, sticky="w", padx=(8, 0), pady=(4, 0)
    )

    scan_group = ttk.LabelFrame(
        top,
        text=app.tr("firewall_group_scan_hints", "Portscan-Hinweise"),
        padding=8,
    )
    scan_group.grid(row=1, column=0, sticky="ew", pady=(0, 8))
    for col in range(4):
        scan_group.columnconfigure(col, weight=1)

    for col, title, var in [
        (0, "BLOCK-Events", app.security_stat_block_var),
        (1, "Portscan-Verdacht", app.security_stat_scan_var),
        (2, "Top Quelle-IP", app.security_stat_top_ip_var),
        (3, "Häufigster Ziel-Port", app.security_stat_top_port_var),
    ]:
        box = ttk.LabelFrame(scan_group, text=title, padding=5)
        box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
        ttk.Label(box, textvariable=var).pack(anchor="center")

    quick_group = ttk.LabelFrame(
        top,
        text=app.tr("firewall_group_quick_access", "Schnellzugriff"),
        padding=8,
    )
    quick_group.grid(row=2, column=0, sticky="ew")
    for col in range(3):
        quick_group.columnconfigure(col, weight=1)

    app.btn_firewall_on = ttk.Button(
        quick_group,
        text=app.tr("btn_firewall_on", "Firewall EIN"),
        command=lambda: (
            app.fw_enable(),
            app.after(900, app.refresh_firewall_transparency_view),
        ),
    )
    app.btn_firewall_on.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 6))
    app.btn_firewall_off = ttk.Button(
        quick_group,
        text=app.tr("btn_firewall_off", "Firewall AUS"),
        command=lambda: (
            app.fw_disable(),
            app.after(900, app.refresh_firewall_transparency_view),
        ),
    )
    app.btn_firewall_off.grid(row=0, column=1, sticky="ew", padx=6, pady=(0, 6))
    app.btn_firewall_status = ttk.Button(
        quick_group,
        text=app.tr("btn_firewall_status", "Firewall Status"),
        command=app.show_firewall_status_clean,
    )
    app.btn_firewall_status.grid(
        row=0, column=2, sticky="ew", padx=(6, 0), pady=(0, 6)
    )

    app.firewall_logging_button = tk.Menubutton(
        quick_group,
        textvariable=app.firewall_tab_logging_menu_var,
        relief="raised",
        direction="below",
    )
    app.firewall_logging_button.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=6)
    app.firewall_logging_button_menu = tk.Menu(
        app.firewall_logging_button,
        tearoff=0,
    )
    app.firewall_logging_button_menu.add_command(
        label=app.tr("menu_logging_off", "Logging AUS"),
        command=lambda: app.show_firewall_ufw_logging("off"),
    )
    app.firewall_logging_button_menu.add_command(
        label=app.tr("menu_logging_low", "Logging LOW"),
        command=lambda: app.show_firewall_ufw_logging("low"),
    )
    app.firewall_logging_button_menu.add_command(
        label=app.tr("menu_logging_high", "Logging HIGH"),
        command=lambda: app.show_firewall_ufw_logging("high"),
    )
    app.firewall_logging_button.configure(menu=app.firewall_logging_button_menu)
    app.btn_firewall_port_reality = ttk.Button(
        quick_group,
        text=app.tr("firewall_btn_port_reality", "Port Reality Check"),
        command=app.run_firewall_port_reality_check,
    )
    app.btn_firewall_port_reality.grid(row=1, column=1, sticky="ew", padx=6, pady=6)
    app.btn_firewall_last_scan = ttk.Button(
        quick_group,
        text=app.tr("btn_last_scan", "Letzter Scan"),
        command=app.show_firewall_port_reality_last,
    )
    app.btn_firewall_last_scan.grid(
        row=1, column=2, sticky="ew", padx=(6, 0), pady=6
    )
    app.btn_firewall_refresh_table = ttk.Button(
        quick_group,
        text=app.tr("security_btn_refresh_table", "Tabelle aktualisieren"),
        command=app.refresh_firewall_transparency_view,
    )
    app.btn_firewall_refresh_table.grid(
        row=2, column=0, sticky="ew", padx=(0, 6), pady=(6, 0)
    )
    app.btn_firewall_open_log = ttk.Button(
        quick_group,
        text=app.tr("firewall_btn_open_log", "UFW Log öffnen"),
        command=app.open_ufw_log_file,
    )
    app.btn_firewall_open_log.grid(row=2, column=1, sticky="ew", padx=6, pady=(6, 0))
    app.btn_firewall_clear_log = ttk.Button(
        quick_group,
        text=app.tr("firewall_btn_clear_log", "UFW Log leeren"),
        command=app.clear_ufw_log_file,
    )
    app.btn_firewall_clear_log.grid(
        row=2, column=2, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    app.btn_firewall_add_rule = ttk.Button(
        quick_group,
        text=app.tr("firewall_btn_add_rule", "Regel hinzufügen"),
        command=app.open_add_firewall_rule_dialog,
    )
    app.btn_firewall_add_rule.grid(
        row=3, column=0, sticky="ew", padx=(0, 6), pady=(6, 0)
    )
    app.firewall_rule_remove_button = ttk.Button(
        quick_group,
        text=app.tr("firewall_btn_remove_rule", "Regel entfernen"),
        command=app.remove_selected_firewall_rule,
        state="disabled",
    )
    app.firewall_rule_remove_button.grid(
        row=3, column=1, sticky="ew", padx=6, pady=(6, 0)
    )
    app.btn_firewall_clear_output = ttk.Button(
        quick_group,
        text=app.tr("btn_clear_output", "Ausgabe leeren"),
        command=app.clear_firewall_transparency_view,
    )
    app.btn_firewall_clear_output.grid(
        row=3, column=2, sticky="ew", padx=(6, 0), pady=(6, 0)
    )

    rules_frame = ttk.Frame(app.firewall_tab_pane, padding=0)
    rules_frame.columnconfigure(0, weight=1)
    rules_frame.rowconfigure(0, weight=1)

    rules_group = ttk.LabelFrame(
        rules_frame,
        text=app.tr("firewall_group_active_rules", "Aktive Firewall-Regeln"),
        padding=6,
    )
    rules_group.grid(row=0, column=0, sticky="nsew")
    rules_group.columnconfigure(0, weight=1)
    rules_group.rowconfigure(0, weight=1)
    rules_group.rowconfigure(1, weight=0)

    rules_wrap = ttk.Frame(rules_group)
    rules_wrap.grid(row=0, column=0, sticky="nsew")
    rules_wrap.columnconfigure(0, weight=1)
    rules_wrap.rowconfigure(0, weight=1)
    rules_y = ttk.Scrollbar(rules_wrap, orient="vertical")
    rules_y.grid(row=0, column=1, sticky="ns")
    rules_x = ttk.Scrollbar(rules_wrap, orient="horizontal")
    rules_x.grid(row=1, column=0, sticky="ew")
    app.firewall_rules_table = ttk.Treeview(
        rules_wrap,
        columns=("action", "target", "proto", "source", "note"),
        show="headings",
        height=10,
        yscrollcommand=rules_y.set,
        xscrollcommand=rules_x.set,
    )
    for col, title, width, anchor in [
        ("action", app.tr("firewall_col_action", "Aktion"), 90, "center"),
        ("target", app.tr("firewall_col_target", "Port / Ziel"), 190, "w"),
        ("proto", app.tr("firewall_col_proto", "Proto"), 70, "center"),
        ("source", app.tr("firewall_col_source", "Quelle"), 170, "w"),
        ("note", app.tr("firewall_col_rating", "Bewertung"), 150, "w"),
    ]:
        app.firewall_rules_table.heading(col, text=title)
        app.firewall_rules_table.column(col, width=width, anchor=anchor)
    app.firewall_rules_table.grid(row=0, column=0, sticky="nsew")
    rules_y.configure(command=app.firewall_rules_table.yview)
    rules_x.configure(command=app.firewall_rules_table.xview)
    app.firewall_rules_table.bind(
        "<<TreeviewSelect>>",
        app.on_firewall_rule_select,
    )
    app.attach_simple_tree_context_menu(app.firewall_rules_table)

    firewall_rule_detail_group = ttk.LabelFrame(
        rules_group,
        text=app.tr("firewall_group_rule_details", "Regel-Details"),
        padding=6,
    )
    firewall_rule_detail_group.grid(row=1, column=0, sticky="ew", pady=(8, 0))
    for col in range(3):
        firewall_rule_detail_group.columnconfigure(col, weight=1)
    app.firewall_rule_detail_action_var = tk.StringVar(
        value=app.tr("firewall_detail_no_selection", "keine Auswahl")
    )
    app.firewall_rule_detail_direction_var = tk.StringVar(
        value=app.tr("firewall_detail_no_selection", "keine Auswahl")
    )
    app.firewall_rule_detail_target_var = tk.StringVar(
        value=app.tr(
            "firewall_detail_no_rule_selected",
            "Noch keine Firewall-Regel ausgewählt.",
        )
    )
    app.firewall_rule_detail_protocol_var = tk.StringVar(
        value=app.tr("firewall_detail_no_selection", "keine Auswahl")
    )
    app.firewall_rule_detail_source_var = tk.StringVar(
        value=app.tr("firewall_detail_no_selection", "keine Auswahl")
    )
    app.firewall_rule_detail_note_var = tk.StringVar(
        value=app.tr("firewall_detail_no_note", "kein Hinweis")
    )

    for col, title, var in [
        (0, "Aktion", app.firewall_rule_detail_action_var),
        (1, "Richtung", app.firewall_rule_detail_direction_var),
        (2, "Ziel", app.firewall_rule_detail_target_var),
        (0, "Protokoll", app.firewall_rule_detail_protocol_var),
        (1, "Quelle", app.firewall_rule_detail_source_var),
        (2, "Hinweis", app.firewall_rule_detail_note_var),
    ]:
        row = 0 if title in {"Aktion", "Richtung", "Ziel"} else 1
        box = ttk.LabelFrame(firewall_rule_detail_group, text=title, padding=5)
        box.grid(
            row=row,
            column=col,
            sticky="nsew",
            padx=(0 if col == 0 else 6, 0),
            pady=(0 if row == 0 else 6, 0),
        )
        ttk.Label(
            box,
            textvariable=var,
            justify="left",
            anchor="w",
        ).pack(fill="x")

    listeners_frame = ttk.Frame(app.firewall_tab_pane, padding=0)
    listeners_frame.columnconfigure(0, weight=1)
    listeners_frame.rowconfigure(0, weight=1)

    listeners_group = ttk.LabelFrame(
        listeners_frame,
        text=app.tr("firewall_group_open_ports", "Offene Ports / Dienste"),
        padding=6,
    )
    listeners_group.grid(row=0, column=0, sticky="nsew")
    listeners_group.columnconfigure(0, weight=1)
    listeners_group.rowconfigure(0, weight=1)

    listeners_wrap = ttk.Frame(listeners_group)
    listeners_wrap.grid(row=0, column=0, sticky="nsew")
    listeners_wrap.columnconfigure(0, weight=1)
    listeners_wrap.rowconfigure(0, weight=1)
    listeners_y = ttk.Scrollbar(listeners_wrap, orient="vertical")
    listeners_y.grid(row=0, column=1, sticky="ns")
    listeners_x = ttk.Scrollbar(listeners_wrap, orient="horizontal")
    listeners_x.grid(row=1, column=0, sticky="ew")
    app.firewall_listeners_table = ttk.Treeview(
        listeners_wrap,
        columns=("port", "proto", "process", "pid", "bind", "firewall", "rating"),
        show="headings",
        height=10,
        yscrollcommand=listeners_y.set,
        xscrollcommand=listeners_x.set,
    )
    for col, title, width, anchor in [
        ("port", app.tr("firewall_col_port", "Port"), 70, "center"),
        ("proto", app.tr("firewall_col_proto", "Proto"), 70, "center"),
        ("process", app.tr("firewall_col_process", "Prozess"), 130, "w"),
        ("pid", app.tr("firewall_col_pid", "PID"), 80, "center"),
        ("bind", app.tr("firewall_col_binding", "Bindung"), 140, "w"),
        ("firewall", app.tr("firewall_col_firewall", "Firewall"), 90, "center"),
        ("rating", app.tr("firewall_col_rating", "Bewertung"), 130, "w"),
    ]:
        app.firewall_listeners_table.heading(col, text=title)
        app.firewall_listeners_table.column(col, width=width, anchor=anchor)
    app.firewall_listeners_table.grid(row=0, column=0, sticky="nsew")
    listeners_y.configure(command=app.firewall_listeners_table.yview)
    listeners_x.configure(command=app.firewall_listeners_table.xview)
    app.attach_simple_tree_context_menu(app.firewall_listeners_table)

    bottom = ttk.Frame(app.firewall_tab_pane, padding=0)
    bottom.columnconfigure(0, weight=1)
    bottom.rowconfigure(0, weight=1)

    summary_group = ttk.LabelFrame(
        bottom,
        text=app.tr("firewall_group_summary", "Firewall-Bewertung"),
        padding=6,
    )
    summary_group.grid(row=0, column=0, sticky="nsew")
    summary_group.columnconfigure(0, weight=1)
    summary_group.rowconfigure(0, weight=1)

    app.firewall_tab_summary_text = tk.Text(
        summary_group,
        height=7,
        wrap="word",
        relief="solid",
        borderwidth=1,
    )
    app.firewall_tab_summary_text.grid(row=0, column=0, sticky="nsew")
    app.firewall_tab_summary_text.insert(
        "1.0",
        app.tr("firewall_summary_loading", "Firewall-Transparenz wird geladen..."),
    )
    app.firewall_tab_summary_text.configure(state="disabled")
    app.attach_selection_copy_shortcuts(app.firewall_tab_summary_text, "text")
    app.attach_text_context_menu(app.firewall_tab_summary_text)

    firewall_summary_buttons = ttk.Frame(summary_group)
    firewall_summary_buttons.grid(row=1, column=0, sticky="w", pady=(8, 0))
    app.btn_firewall_chad = ttk.Button(
        firewall_summary_buttons,
        text=app.tr("btn_send_to_chad", "An Chad senden"),
        command=app.analyze_firewall_with_chad,
    )
    app.btn_firewall_chad.pack(side="left")

    app.firewall_tab_pane.add(top, weight=2)
    app.firewall_tab_pane.add(rules_frame, weight=3)
    app.firewall_tab_pane.add(listeners_frame, weight=3)
    app.firewall_tab_pane.add(bottom, weight=2)

    app.after(250, app.refresh_firewall_transparency_view)


def build_security_tabs(app):
    app.tab_security = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_security,
        text=app.tr("security_tab_guards", "Guard"),
    )
    app.security_status_var = tk.StringVar(
        value=app.tr("security_status_monitoring_off", "Monitoring: AUS")
    )
    app.security_level_var = tk.StringVar(
        value=app.tr("security_status_logging_default", "Logging: -")
    )
    app.security_count_var = tk.StringVar(
        value=app.tr("security_status_events_default", "Events: 0")
    )
    app.security_alarm_var = tk.StringVar(
        value=app.tr("security_status_last_alarm_default", "Letzter Alarm: –")
    )
    app.security_stat_total_var = tk.StringVar(value="0")
    app.security_stat_block_var = tk.StringVar(value="0")
    app.security_stat_scan_var = tk.StringVar(value="0")
    app.security_stat_top_ip_var = tk.StringVar(value="–")
    app.security_stat_top_port_var = tk.StringVar(value="–")
    build_firewall_tab(app)
    security_body = ttk.Frame(app.tab_security)
    security_body.pack(fill="both", expand=True)
    security_body.columnconfigure(0, weight=1)
    security_body.rowconfigure(0, weight=1)

    app.security_tab_pane = ttk.Panedwindow(security_body, orient="vertical")
    app.security_tab_pane.grid(row=0, column=0, sticky="nsew")
    app.security_tab_pane_markers = _install_vertical_pane_drag_markers(
        security_body, app.security_tab_pane
    )

    security_overview = ttk.Frame(app.security_tab_pane, padding=0)
    security_overview.columnconfigure(0, weight=1)
    security_events = ttk.Frame(app.security_tab_pane, padding=0)
    security_events.columnconfigure(0, weight=1)
    security_events.rowconfigure(0, weight=1)
    security_detail_frame = ttk.LabelFrame(
        app.security_tab_pane,
        text=app.tr("security_details_title", "Details"),
        padding=6,
    )
    app.security_detail_frame = security_detail_frame
    security_detail_frame.columnconfigure(0, weight=1)
    security_detail_frame.rowconfigure(0, weight=1)

    app.security_tab_pane.add(security_overview, weight=3)
    app.security_tab_pane.add(security_events, weight=3)
    app.security_tab_pane.add(security_detail_frame, weight=2)

    security_devices_frame = ttk.LabelFrame(
        security_overview,
        text=app.tr("security_group_device_guard", "Device Guard"),
        padding=5,
    )
    security_devices_frame.columnconfigure(0, weight=1)
    security_devices_frame.pack(fill="both", expand=True, pady=(0, 8))

    security_devices_top = ttk.Frame(security_devices_frame)
    security_devices_top.pack(fill="x", pady=(0, 4))
    ttk.Label(
        security_devices_top,
        text=app.tr(
            "security_device_guard_hint",
            "Live-Snapshot der aktuell erkannten Eingabe-Geräte.",
        ),
    ).pack(side="left")

    security_devices_table_frame = ttk.Frame(security_devices_frame)
    security_devices_table_frame.pack(fill="both", expand=True)
    security_devices_table_frame.columnconfigure(0, weight=1)
    security_devices_table_frame.rowconfigure(0, weight=1)
    security_devices_scroll_y = ttk.Scrollbar(
        security_devices_table_frame,
        orient="vertical",
    )
    security_devices_scroll_y.grid(row=0, column=1, sticky="ns")
    security_devices_scroll_x = ttk.Scrollbar(
        security_devices_table_frame,
        orient="horizontal",
    )
    security_devices_scroll_x.grid(row=1, column=0, sticky="ew")

    app.security_devices_table = ttk.Treeview(
        security_devices_table_frame,
        columns=("name", "type", "vendor", "product", "baseline", "path"),
        show="headings",
        height=4,
        yscrollcommand=security_devices_scroll_y.set,
        xscrollcommand=security_devices_scroll_x.set,
    )
    for col, title, w, anchor in [
        ("name", "Name", 220, "w"),
        ("type", "Typ", 110, "center"),
        ("vendor", "Vendor", 90, "center"),
        ("product", "Product", 90, "center"),
        ("baseline", "Baseline", 110, "center"),
        ("path", "Pfad", 320, "w"),
    ]:
        app.security_devices_table.heading(col, text=title)
        app.security_devices_table.column(col, width=w, anchor=anchor)
    app.security_devices_table.grid(row=0, column=0, sticky="nsew")
    security_devices_scroll_y.configure(command=app.security_devices_table.yview)
    security_devices_scroll_x.configure(command=app.security_devices_table.xview)
    app.security_devices_table.bind(
        "<<TreeviewSelect>>",
        app.on_connected_device_select,
    )
    app.attach_security_devices_tree_context_menu()

    sec_controls = ttk.Frame(security_overview)
    sec_controls.pack(fill="x", pady=(0, 8))

    sec_status = ttk.Frame(sec_controls)
    sec_status.pack(fill="x", pady=(0, 6))
    ttk.Label(
        sec_status,
        text=app.tr("privacy_check_enabled", "Stealthmodus aktiv"),
    ).pack(side="left")

    sec_actions = ttk.LabelFrame(
        sec_controls,
        text=app.tr("security_group_actions", "Aktionen"),
        padding=6,
    )
    sec_actions.pack(fill="x")

    app.btn_security_input_scan = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_input_scan", "Input-Zugriffe prüfen"),
        command=app.refresh_input_access_table,
    )
    app.btn_security_input_scan.pack(side="left")
    app.add_tooltip(
        app.btn_security_input_scan,
        app.tr(
            "tooltip_security_input_scan",
            "Prüft aktuell offene Zugriffe auf /dev/input-Geräte.",
        ),
    )

    app.btn_security_show_devices = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_show_devices", "Verbundene Geräte anzeigen"),
        command=app.security_show_connected_devices,
    )
    app.btn_security_show_devices.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_security_show_devices,
        app.tr(
            "tooltip_security_show_devices",
            "Zeigt alle aktuell erkannten Eingabe-Geräte an, nicht nur Änderungen.",
        ),
    )

    app.btn_security_rebaseline = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_rebaseline", "Baseline neu erstellen"),
        command=app.security_build_baseline,
    )
    app.btn_security_rebaseline.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_security_rebaseline,
        app.tr(
            "tooltip_security_rebaseline",
            "Erstellt die File/Device-Baseline neu.",
        ),
    )

    app.btn_security_clear_views = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_clear_views", "Ansichten leeren"),
        command=app.security_clear_views,
    )
    app.btn_security_clear_views.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_security_clear_views,
        app.tr(
            "tooltip_security_clear_views",
            "Leert die sichtbaren Tabellen und Detailansichten im Guards-Tab, ohne Baselines zu ändern.",
        ),
    )

    input_access_frame = ttk.LabelFrame(
        security_overview,
        text=app.tr("security_group_input_access", "Aktuelle Input-Zugriffe"),
        padding=6,
    )
    input_access_frame.pack(fill="both", expand=True, pady=(0, 8))
    input_access_frame.columnconfigure(0, weight=1)
    input_access_frame.rowconfigure(0, weight=1)

    input_access_wrap = ttk.Frame(input_access_frame)
    input_access_wrap.grid(row=0, column=0, sticky="nsew")
    input_access_wrap.columnconfigure(0, weight=1)
    input_access_wrap.rowconfigure(0, weight=1)
    input_access_y = ttk.Scrollbar(input_access_wrap, orient="vertical")
    input_access_y.grid(row=0, column=1, sticky="ns")
    input_access_x = ttk.Scrollbar(input_access_wrap, orient="horizontal")
    input_access_x.grid(row=1, column=0, sticky="ew")

    app.input_access_table = ttk.Treeview(
        input_access_wrap,
        columns=("device", "process", "pid", "type", "status", "path"),
        show="headings",
        height=6,
        yscrollcommand=input_access_y.set,
        xscrollcommand=input_access_x.set,
    )
    for col, title, width, anchor in [
        ("device", "Gerät", 180, "w"),
        ("process", "Prozess", 150, "w"),
        ("pid", "PID", 80, "center"),
        ("type", "Typ", 110, "center"),
        ("status", "Status", 120, "center"),
        ("path", "Pfad", 260, "w"),
    ]:
        app.input_access_table.heading(col, text=title)
        app.input_access_table.column(col, width=width, anchor=anchor)
    app.input_access_table.grid(row=0, column=0, sticky="nsew")
    input_access_y.configure(command=app.input_access_table.yview)
    input_access_x.configure(command=app.input_access_table.xview)
    app.attach_simple_tree_context_menu(app.input_access_table)

    ttk.Label(
        security_overview,
        text=app.tr(
            "security_integrity_hint",
            "Hinweis: NetMon-eigene State- und Konfigurationsdateien werden im Integrity-Check nicht als Security-Fund gemeldet.",
        ),
    ).pack(anchor="w", pady=(0, 8))

    app.tab_path_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_path_guard,
        text=app.tr("security_tab_path_guard", "PATH-Guard"),
    )

    path_guard_frame = ttk.LabelFrame(
        app.tab_path_guard,
        text=app.tr("path_guard_group_title", "PATH Guard"),
        padding=6,
    )
    path_guard_frame.pack(fill="x", pady=(0, 8))

    app.btn_path_guard_check = ttk.Button(
        path_guard_frame,
        text=app.tr("path_guard_btn_check", "PATH prüfen"),
        command=app.run_path_guard_check,
    )
    app.btn_path_guard_check.pack(side="left")
    app.add_tooltip(
        app.btn_path_guard_check,
        app.tr(
            "tooltip_path_guard_check",
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen.",
        ),
    )

    app.btn_path_guard_chad = ttk.Button(
        path_guard_frame,
        text=app.tr("path_guard_btn_chad", "Mit Chad analysieren"),
        command=app.analyze_path_guard_with_chad,
    )
    app.btn_path_guard_chad.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_path_guard_chad,
        app.tr(
            "tooltip_path_guard_chad",
            "Bereitet die letzte PATH Guard Prüfung für Chad vor.",
        ),
    )

    ttk.Label(
        path_guard_frame,
        textvariable=app.path_guard_status_var,
    ).pack(side="left", padx=(12, 0))

    app.path_guard_pane = ttk.Panedwindow(
        app.tab_path_guard,
        orient="vertical",
    )
    app.path_guard_pane.pack(fill="both", expand=True)

    path_guard_detail_frame = ttk.LabelFrame(
        app.path_guard_pane,
        text=app.tr("path_guard_group_details", "Details"),
        padding=6,
    )
    app.path_guard_pane.add(path_guard_detail_frame, weight=1)
    path_guard_detail_frame.columnconfigure(0, weight=1)
    path_guard_detail_frame.rowconfigure(0, weight=1)

    app.path_guard_detail = tk.Text(
        path_guard_detail_frame,
        wrap="word",
        height=18,
    )
    app.path_guard_detail.grid(row=0, column=0, sticky="nsew")
    app.path_guard_detail.insert(
        "1.0",
        app.tr(
            "path_guard_details_placeholder",
            "PATH-Guard-Details erscheinen hier.\n",
        ),
    )
    app.path_guard_detail.configure(state="disabled")
    app.attach_selection_copy_shortcuts(app.path_guard_detail, "text")
    app.attach_text_context_menu(app.path_guard_detail)

    app.tab_process_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_process_guard,
        text=app.tr("security_tab_process_guard", "Process Guard"),
    )

    process_guard_frame = ttk.LabelFrame(
        app.tab_process_guard,
        text=app.tr("process_guard_group_title", "Process Guard"),
        padding=6,
    )
    process_guard_frame.pack(fill="x", pady=(0, 8))
    for col in range(3):
        process_guard_frame.columnconfigure(col, weight=1)

    process_guard_status_row = ttk.Frame(app.tab_process_guard)
    process_guard_status_row.pack(fill="x", pady=(0, 8))
    ttk.Label(
        process_guard_status_row,
        textvariable=app.process_guard_monitoring_status_var,
    ).pack(side="left")
    ttk.Label(process_guard_status_row, text=" | ").pack(side="left")
    ttk.Label(
        process_guard_status_row,
        textvariable=app.process_guard_filter_status_var,
    ).pack(side="left")
    ttk.Label(process_guard_status_row, text=" | ").pack(side="left")
    ttk.Label(
        process_guard_status_row,
        textvariable=app.process_guard_visible_count_var,
    ).pack(side="left")

    process_guard_btn_row1 = ttk.Frame(process_guard_frame)
    process_guard_btn_row1.grid(row=0, column=0, columnspan=3, sticky="ew")
    for col in range(3):
        process_guard_btn_row1.columnconfigure(col, weight=1)

    app.btn_process_guard_check = ttk.Button(
        process_guard_btn_row1,
        text=app.tr("process_guard_btn_check", "Prozesse prüfen"),
        command=app.run_process_guard_check,
        width=28,
    )
    app.btn_process_guard_check.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    app.add_tooltip(
        app.btn_process_guard_check,
        app.tr(
            "tooltip_process_guard_check",
            "Prüft laufende Prozesse auf auffällige Pfade, Shell-Ketten und verdächtige Starts.",
        ),
    )

    app.btn_process_guard_start = ttk.Button(
        process_guard_btn_row1,
        text=app.tr("process_guard_btn_start", "Monitoring starten"),
        command=app.start_process_guard_monitoring,
        width=28,
    )
    app.btn_process_guard_start.grid(row=0, column=1, sticky="ew", padx=6)
    app.add_tooltip(
        app.btn_process_guard_start,
        app.tr(
            "tooltip_process_guard_start",
            "Startet ein leichtes lokales Monitoring für neue Prozesse.",
        ),
    )

    app.btn_process_guard_stop = ttk.Button(
        process_guard_btn_row1,
        text=app.tr("process_guard_btn_stop", "Monitoring stoppen"),
        command=app.stop_process_guard_monitoring,
        width=28,
    )
    app.btn_process_guard_stop.grid(row=0, column=2, sticky="ew", padx=(6, 0))
    app.add_tooltip(
        app.btn_process_guard_stop,
        app.tr(
            "tooltip_process_guard_stop",
            "Stoppt das lokale Process Guard Monitoring.",
        ),
    )

    process_guard_btn_row2 = ttk.Frame(process_guard_frame)
    process_guard_btn_row2.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(6, 0))
    for col in range(3):
        process_guard_btn_row2.columnconfigure(col, weight=1)

    app.btn_process_guard_chad = ttk.Button(
        process_guard_btn_row2,
        text=app.tr("process_guard_btn_chad", "Mit Chad analysieren"),
        command=app.analyze_process_guard_with_chad,
        width=28,
    )
    app.btn_process_guard_chad.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    app.add_tooltip(
        app.btn_process_guard_chad,
        app.tr(
            "tooltip_process_guard_chad",
            "Bereitet die letzte Process Guard Prüfung für Chad vor.",
        ),
    )

    app.btn_process_guard_mark_trusted = ttk.Button(
        process_guard_btn_row2,
        text=app.tr(
            "process_guard_btn_mark_trusted",
            "Als bekannt markieren",
        ),
        command=app.mark_selected_process_guard_trusted,
        width=28,
    )
    app.btn_process_guard_mark_trusted.grid(row=0, column=1, sticky="ew", padx=6)
    app.add_tooltip(
        app.btn_process_guard_mark_trusted,
        app.tr(
            "tooltip_process_guard_mark_trusted",
            "Markiert den ausgewählten Process Guard Fund als bekannt, damit er künftig ausgeblendet wird.",
        ),
    )
    app.btn_process_guard_selected_chad = ttk.Button(
        process_guard_btn_row2,
        text=app.tr(
            "process_guard_btn_selected_chad",
            "Auswahl mit Chad analysieren",
        ),
        command=app.analyze_selected_process_guard_with_chad,
        width=28,
    )
    app.btn_process_guard_selected_chad.grid(
        row=0, column=2, sticky="ew", padx=(6, 0)
    )

    process_guard_btn_row3 = ttk.Frame(process_guard_frame)
    process_guard_btn_row3.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(6, 0))
    for col in range(3):
        process_guard_btn_row3.columnconfigure(col, weight=1)

    app.btn_process_guard_remove_trusted = ttk.Button(
        process_guard_btn_row3,
        text=app.tr(
            "process_guard_btn_remove_trusted",
            "Als bekannt entfernen",
        ),
        command=app.remove_selected_process_guard_trusted,
        width=28,
    )
    app.btn_process_guard_remove_trusted.grid(row=0, column=0, sticky="ew", padx=(0, 6))
    app.add_tooltip(
        app.btn_process_guard_remove_trusted,
        app.tr(
            "tooltip_process_guard_remove_trusted",
            "Entfernt den ausgewählten Process Guard Fund aus der Vertrauensliste.",
        ),
    )

    app.btn_process_guard_show_trustlist = ttk.Button(
        process_guard_btn_row3,
        text=app.tr(
            "process_guard_btn_show_trustlist",
            "Vertrauensliste anzeigen",
        ),
        command=app.show_process_guard_trustlist,
        width=28,
    )
    app.btn_process_guard_show_trustlist.grid(row=0, column=1, sticky="ew", padx=6)
    app.add_tooltip(
        app.btn_process_guard_show_trustlist,
        app.tr(
            "tooltip_process_guard_show_trustlist",
            "Zeigt die aktuell bekannten Process Guard Ausnahmen an.",
        ),
    )

    app.btn_process_guard_reset_trustlist = ttk.Button(
        process_guard_btn_row3,
        text=app.tr(
            "process_guard_btn_reset_trustlist",
            "Vertrauensliste zurücksetzen",
        ),
        command=app.reset_process_guard_trustlist,
        width=28,
    )
    app.btn_process_guard_reset_trustlist.grid(row=0, column=2, sticky="ew", padx=(6, 0))
    app.add_tooltip(
        app.btn_process_guard_reset_trustlist,
        app.tr(
            "tooltip_process_guard_reset_trustlist",
            "Leert alle bekannten Process Guard Ausnahmen und prüft die Prozesse erneut.",
        ),
    )

    ttk.Label(
        process_guard_frame,
        textvariable=app.process_guard_status_var,
    ).grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))

    process_guard_filter_frame = ttk.Frame(app.tab_process_guard)
    process_guard_filter_frame.pack(fill="x", pady=(0, 6))
    ttk.Label(
        process_guard_filter_frame,
        text=app.tr("process_guard_filter_label", "Process Guard Filter:"),
    ).pack(side="left")
    ttk.Button(
        process_guard_filter_frame,
        text=app.tr("process_guard_filter_all", "Alle"),
        command=lambda: app.set_process_guard_filter("all"),
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        process_guard_filter_frame,
        text=app.tr("process_guard_filter_high_medium", "Hoch + Mittel"),
        command=lambda: app.set_process_guard_filter("high_medium"),
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        process_guard_filter_frame,
        text=app.tr("process_guard_filter_high", "Nur hoch"),
        command=lambda: app.set_process_guard_filter("high"),
    ).pack(side="left", padx=(8, 0))

    app.process_guard_pane = ttk.Panedwindow(
        app.tab_process_guard,
        orient="vertical",
    )
    app.process_guard_pane.pack(fill="both", expand=True)

    process_guard_tree_frame = ttk.Frame(app.process_guard_pane)
    process_guard_detail_frame = ttk.LabelFrame(
        app.process_guard_pane,
        text=app.tr("process_guard_details_title", "Details"),
        padding=6,
    )
    app.process_guard_detail_frame = process_guard_detail_frame
    app.process_guard_pane.add(process_guard_tree_frame, weight=3)
    app.process_guard_pane.add(process_guard_detail_frame, weight=2)

    app.process_guard_tree = ttk.Treeview(
        process_guard_tree_frame,
        columns=("risk", "pid", "name", "user", "path"),
        show="headings",
        height=5,
    )
    for col, title, width, anchor in [
        ("risk", app.tr("process_guard_col_risk", "Risiko"), 90, "center"),
        ("pid", app.tr("process_guard_col_pid", "PID"), 80, "center"),
        ("name", app.tr("process_guard_col_name", "Name"), 140, "w"),
        ("user", app.tr("process_guard_col_user", "User"), 120, "w"),
        ("path", app.tr("process_guard_col_path", "Pfad"), 420, "w"),
    ]:
        app.process_guard_tree.heading(col, text=title)
        app.process_guard_tree.column(col, width=width, anchor=anchor)
    app.process_guard_tree.pack(fill="both", expand=True)
    app.process_guard_tree.bind("<<TreeviewSelect>>", app.on_process_guard_select)
    app.attach_process_guard_tree_context_menu()

    app.process_guard_detail = tk.Text(
        process_guard_detail_frame,
        wrap="word",
        height=10,
    )
    app.process_guard_detail.pack(fill="both", expand=True)
    app.process_guard_detail.insert(
        "1.0",
        app.tr(
            "process_guard_details_placeholder",
            "Process Guard Details erscheinen hier.\n",
        ),
    )
    app.process_guard_detail.configure(state="disabled")
    app.attach_text_context_menu(app.process_guard_detail)

    app.security_table = ttk.Treeview(
        security_events,
        columns=("time", "type", "src", "port", "proto", "level", "action"),
        show="headings",
        height=12,
    )
    for col, title, w, anchor in [
        ("time", "Zeit", 150, "w"),
        ("type", "Typ", 160, "w"),
        ("src", "Quelle-IP", 130, "w"),
        ("port", "Ziel-Port", 90, "center"),
        ("proto", "Protokoll", 90, "center"),
        ("level", "Level", 90, "center"),
        ("action", "Aktion", 90, "center"),
    ]:
        app.security_table.heading(col, text=title)
        app.security_table.column(col, width=w, anchor=anchor)
    app.security_table.grid(row=0, column=0, sticky="nsew")
    app.security_table.bind("<<TreeviewSelect>>", app.on_security_event_select)
    app.attach_security_table_context_menu()

    security_detail_scroll_y = ttk.Scrollbar(
        security_detail_frame,
        orient="vertical",
    )
    security_detail_scroll_y.grid(row=0, column=1, sticky="ns")
    app.security_detail = tk.Text(
        security_detail_frame,
        wrap="word",
        height=8,
        yscrollcommand=security_detail_scroll_y.set,
    )
    app.security_detail.grid(row=0, column=0, sticky="nsew")
    security_detail_scroll_y.configure(command=app.security_detail.yview)
    app.attach_text_context_menu(app.security_detail)

    app.tab_clamav = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_clamav,
        text=app.tr("security_tab_clamav", "ClamAV"),
    )

    clamav_wrap = ttk.Frame(app.tab_clamav)
    clamav_wrap.pack(fill="both", expand=True)

    app.clamav_canvas = tk.Canvas(clamav_wrap, highlightthickness=0)
    app.clamav_canvas.pack(fill="both", expand=True)

    app.clamav_scroll_frame = ttk.Frame(app.clamav_canvas)
    app.clamav_canvas_window = app.clamav_canvas.create_window(
        (0, 0),
        window=app.clamav_scroll_frame,
        anchor="nw",
    )

    def _on_clamav_frame_config(_event):
        app.clamav_canvas.configure(scrollregion=app.clamav_canvas.bbox("all"))

    def _on_clamav_canvas_config(event):
        app.clamav_canvas.itemconfig(app.clamav_canvas_window, width=event.width)

    app.clamav_scroll_frame.bind("<Configure>", _on_clamav_frame_config)
    app.clamav_canvas.bind("<Configure>", _on_clamav_canvas_config)

    clamav_status = ttk.LabelFrame(
        app.clamav_scroll_frame,
        text=app.tr("clamav_group_status", "Status"),
        padding=6,
    )
    clamav_status.pack(fill="x")
    clamav_status.columnconfigure(1, weight=1)
    clamav_status.columnconfigure(3, weight=1)

    ttk.Label(clamav_status, text=app.tr("clamav_label_status", "Status:")).grid(
        row=0, column=0, sticky="w"
    )
    ttk.Label(clamav_status, textvariable=app.clamav_status_var).grid(
        row=0, column=1, sticky="w", padx=(8, 12)
    )
    ttk.Label(clamav_status, text=app.tr("clamav_label_runtime", "Laufzeit:")).grid(
        row=0, column=2, sticky="w"
    )
    ttk.Label(clamav_status, textvariable=app.clamav_runtime_var).grid(
        row=0, column=3, sticky="w", padx=(8, 0)
    )

    ttk.Label(clamav_status, text=app.tr("clamav_label_signatures", "Signaturen:")).grid(
        row=1, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_signatures_var).grid(
        row=1, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(
        clamav_status, text=app.tr("clamav_label_scanned_files", "Dateien gescannt:")
    ).grid(
        row=1, column=2, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_scanned_files_var).grid(
        row=1, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text=app.tr("clamav_label_last_scan", "Letzter Scan:")).grid(
        row=2, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_last_scan_var).grid(
        row=2, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(clamav_status, text=app.tr("clamav_label_speed", "Geschwindigkeit:")).grid(
        row=2, column=2, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_speed_var).grid(
        row=2, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text=app.tr("clamav_label_last_target", "Letztes Ziel:")).grid(
        row=3, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_last_target_var).grid(
        row=3, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(clamav_status, text=app.tr("clamav_label_eta", "ETA:")).grid(
        row=3, column=2, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_eta_var).grid(
        row=3, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text=app.tr("clamav_label_findings", "Funde:")).grid(
        row=4, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_findings_var).grid(
        row=4, column=1, sticky="w", padx=(8, 0), pady=(2, 0)
    )
    ttk.Label(clamav_status, text=app.tr("clamav_label_result", "Ergebnis:")).grid(
        row=5, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_result_var).grid(
        row=5, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    clamav_scan = ttk.LabelFrame(
        app.clamav_scroll_frame,
        text=app.tr("clamav_group_scan", "Scan"),
        padding=6,
    )
    clamav_scan.pack(fill="x", pady=(8, 0))
    for col in range(3):
        clamav_scan.columnconfigure(col, weight=1)

    app.btn_clamav_update = ttk.Button(
        clamav_scan,
        text=app.tr("clamav_btn_update", "ClamAV Update"),
        command=app.security_clamav_update_async,
    )
    app.btn_clamav_update.grid(
        row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 6)
    )
    app.register_feature_button("clamav_update", app.btn_clamav_update)
    app.add_tooltip(
        app.btn_clamav_update,
        app.tr(
            "tooltip_clamav_update",
            "Aktualisiert ClamAV-Signaturen mit freshclam.",
        ),
    )

    app.btn_clamav_quick = ttk.Button(
        clamav_scan,
        text=app.tr("clamav_btn_quickscan", "ClamAV Schnellscan"),
        command=app.security_clamav_quickscan_async,
    )
    app.btn_clamav_quick.grid(row=0, column=1, sticky="ew", padx=6, pady=(0, 6))
    app.register_feature_button("clamav_scan", app.btn_clamav_quick)
    app.add_tooltip(
        app.btn_clamav_quick,
        app.tr(
            "tooltip_clamav_quick",
            "Startet einen kompakten ClamAV-Schnellscan auf typische Benutzerordner.",
        ),
    )

    app.btn_clamav_folder = ttk.Button(
        clamav_scan,
        text=app.tr("clamav_btn_scan_folder", "ClamAV Ordner scannen"),
        command=app.security_clamav_folder_scan_async,
    )
    app.btn_clamav_folder.grid(
        row=0, column=2, sticky="ew", padx=(6, 0), pady=(0, 6)
    )
    app.register_feature_button("clamav_scan", app.btn_clamav_folder)
    app.add_tooltip(
        app.btn_clamav_folder,
        app.tr(
            "tooltip_clamav_folder",
            "Öffnet eine Ordnerauswahl und scannt den gewählten Ordner mit ClamAV.",
        ),
    )

    app.btn_clamav_system = ttk.Button(
        clamav_scan,
        text=app.tr("clamav_btn_systemscan", "Systemscan"),
        command=app.security_clamav_systemscan_async,
    )
    app.btn_clamav_system.grid(
        row=1, column=0, sticky="ew", padx=(0, 6), pady=(6, 0)
    )
    app.register_feature_button("clamav_scan", app.btn_clamav_system)
    app.add_tooltip(
        app.btn_clamav_system,
        app.tr(
            "tooltip_clamav_system",
            "Startet einen erweiterten ClamAV-Systemscan auf sinnvollen Standardpfaden.",
        ),
    )

    clamav_actions = ttk.LabelFrame(
        app.clamav_scroll_frame,
        text=app.tr("clamav_group_findings_quarantine", "Funde & Quarantäne"),
        padding=6,
    )
    clamav_actions.pack(fill="x", pady=(8, 0))
    for col in range(3):
        clamav_actions.columnconfigure(col, weight=1)

    app.btn_clamav_show_findings = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_show_findings", "Funde anzeigen"),
        command=app.show_clamav_findings,
    )
    app.btn_clamav_show_findings.grid(
        row=0, column=0, sticky="ew", padx=(0, 6), pady=(0, 6)
    )
    app.add_tooltip(
        app.btn_clamav_show_findings,
        app.tr(
            "tooltip_clamav_show_findings",
            "Zeigt aktuell offene ClamAV-Funde mit Signatur an.",
        ),
    )

    app.btn_clamav_export_findings = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_export_findings", "Funde exportieren"),
        command=app.export_clamav_findings,
    )
    app.btn_clamav_export_findings.grid(
        row=0, column=1, sticky="ew", padx=6, pady=(0, 6)
    )
    app.add_tooltip(
        app.btn_clamav_export_findings,
        app.tr(
            "tooltip_clamav_export_findings",
            "Exportiert ClamAV-Funde/Historie als JSON und TXT.",
        ),
    )

    app.btn_clamav_show_quarantine = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_show_quarantine", "Quarantäne anzeigen"),
        command=app.show_clamav_quarantine_history,
    )
    app.btn_clamav_show_quarantine.grid(
        row=0, column=2, sticky="ew", padx=(6, 0), pady=(0, 6)
    )
    app.add_tooltip(
        app.btn_clamav_show_quarantine,
        app.tr(
            "tooltip_clamav_show_quarantine",
            "Zeigt Dateien in/aus der Quarantänehistorie.",
        ),
    )

    app.btn_clamav_abort_scan = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_abort_scan", "Scan abbrechen"),
        command=app.clamav_abort_scan,
    )
    app.btn_clamav_abort_scan.grid(
        row=2, column=2, sticky="ew", padx=(6, 0), pady=(6, 0)
    )
    app.add_tooltip(
        app.btn_clamav_abort_scan,
        app.tr(
            "tooltip_clamav_abort_scan",
            "Bricht einen laufenden ClamAV-Scan ab.",
        ),
    )
    app.btn_clamav_abort_scan.configure(state="disabled")

    app.btn_clamav_quarantine = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_quarantine", "In Quarantäne verschieben"),
        command=app.quarantine_clamav_findings_async,
    )
    app.btn_clamav_quarantine.grid(row=1, column=0, sticky="ew", padx=(0, 6), pady=6)
    app.add_tooltip(
        app.btn_clamav_quarantine,
        app.tr(
            "tooltip_clamav_quarantine",
            "Verschiebt offene ClamAV-Funde sicher nach ~/.netmon_quarantine.",
        ),
    )

    app.btn_clamav_quarantine_selected = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_quarantine_selected", "Auswahl quarantänisieren"),
        command=app.quarantine_selected_clamav_findings_async,
    )
    app.btn_clamav_quarantine_selected.grid(
        row=1, column=1, sticky="ew", padx=6, pady=6
    )
    app.add_tooltip(
        app.btn_clamav_quarantine_selected,
        app.tr(
            "tooltip_clamav_quarantine_selected",
            "Öffnet eine Auswahl und verschiebt nur ausgewählte Funde in Quarantäne.",
        ),
    )

    app.btn_clamav_restore_quarantine = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_restore_quarantine", "Aus Quarantäne wiederherstellen"),
        command=app.restore_clamav_quarantine_async,
    )
    app.btn_clamav_restore_quarantine.grid(
        row=1, column=2, sticky="ew", padx=(6, 0), pady=6
    )
    app.add_tooltip(
        app.btn_clamav_restore_quarantine,
        app.tr(
            "tooltip_clamav_restore_quarantine",
            "Stellt quarantänisierte Dateien sicher an ihren Ursprungsort wieder her.",
        ),
    )

    app.btn_clamav_restore_selected = ttk.Button(
        clamav_actions,
        text=app.tr("clamav_btn_restore_selected", "Auswahl wiederherstellen"),
        command=app.restore_selected_clamav_quarantine_async,
    )
    app.btn_clamav_restore_selected.grid(
        row=2, column=0, sticky="ew", padx=(0, 6), pady=(6, 0)
    )
    app.add_tooltip(
        app.btn_clamav_restore_selected,
        app.tr(
            "tooltip_clamav_restore_selected",
            "Öffnet eine Auswahl und stellt nur ausgewählte Quarantäne-Dateien wieder her.",
        ),
    )

    clamav_output_frame = ttk.LabelFrame(
        app.clamav_scroll_frame,
        text=app.tr(
            "clamav_group_output_history",
            "Ergebnis / Fundliste / Historie",
        ),
        padding=6,
    )
    clamav_output_frame.pack(fill="both", expand=True, pady=(8, 0))
    clamav_output_frame.columnconfigure(0, weight=1)
    clamav_output_frame.rowconfigure(0, weight=1)

    clamav_output_scroll_y = ttk.Scrollbar(
        clamav_output_frame,
        orient="vertical",
    )
    clamav_output_scroll_y.grid(row=0, column=1, sticky="ns")

    app.clamav_output_text = tk.Text(
        clamav_output_frame,
        wrap="word",
        height=12,
        yscrollcommand=clamav_output_scroll_y.set,
    )
    app.clamav_output_text.grid(row=0, column=0, sticky="nsew")
    clamav_output_scroll_y.configure(command=app.clamav_output_text.yview)
    app.clamav_output_text.insert(
        "1.0",
        app.tr(
            "clamav_output_placeholder",
            "ClamAV results and progress appear here.",
        )
        + "\n",
    )
    app.clamav_output_text.configure(state="disabled")

    app._update_clamav_findings_buttons_state()

    app.tab_lynis = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_lynis,
        text=app.tr("security_tab_lynis", "Lynis"),
    )
    app.build_lynis_tab()

    app.tab_rkhunter = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_rkhunter,
        text=app.tr("security_tab_rkhunter", "rkh"),
    )
    app.build_rkhunter_tab()

    build_repository_guard_tab(app)
    build_roots_baseline_guard_tab(app)

    app.tab_startup_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_startup_guard,
        text=app.tr("security_tab_startup_guard", "Startup Guard"),
    )
    build_startup_guard_tab(app)

    app.tab_packet_capture = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_packet_capture,
        text=app.tr("security_tab_packet_capture", "Cap"),
    )
    app.build_packet_capture_tab()
    app.after(300, app.refresh_packet_capture_interfaces)
