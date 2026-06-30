"""Fun tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def _bind_if_callable(widget, sequence: str, callback, *, add=None):
    if not callable(callback):
        return False
    widget.bind(sequence, callback, add=add)
    return True


def build_fun_tab(app):
    app.tab_fun = ttk.Frame(app.tools_nb, padding=10)
    app.tools_nb.add(app.tab_fun, text=app.tr("tools_tab_fun", "Fun"))

    top = ttk.LabelFrame(
        app.tab_fun,
        text=app.tr("fun_group_actions", "Fun Aktionen"),
        padding=6,
    )
    top.pack(fill="x", pady=(0, 8))

    app.btn_fun_open_folder = ttk.Button(
        top,
        text=app.tr("fun_btn_open_folder", "Spieleordner öffnen"),
        command=app.open_fun_games_folder,
    )
    app.btn_fun_open_folder.pack(side="left")

    app.btn_fun_refresh = ttk.Button(
        top,
        text=app.tr("fun_btn_refresh", "Liste aktualisieren"),
        command=app.refresh_fun_games,
    )
    app.btn_fun_refresh.pack(side="left", padx=(6, 0))

    app.btn_fun_start = ttk.Button(
        top,
        text=app.tr("fun_btn_start", "Spiel starten"),
        command=app.start_selected_fun_game,
    )
    app.btn_fun_start.pack(side="left", padx=(12, 0))
    app.register_feature_button("fun", app.btn_fun_start)

    app.btn_fun_stop = ttk.Button(
        top,
        text=app.tr("fun_btn_stop", "Spiel stoppen"),
        command=app.stop_running_fun_game,
    )
    app.btn_fun_stop.pack(side="left", padx=(6, 0))
    app.register_feature_button("fun", app.btn_fun_stop)

    app.fun_games_table = ttk.Treeview(
        app.tab_fun,
        columns=("name", "source", "status", "start"),
        show="headings",
        height=10,
    )
    for col, title, width in [
        ("name", app.tr("fun_col_name", "Spiel"), 220),
        ("source", app.tr("fun_col_source", "Quelle"), 180),
        ("status", app.tr("fun_col_status", "Status"), 140),
        ("start", app.tr("fun_col_start", "Start"), 80),
    ]:
        app.fun_games_table.heading(col, text=title)
        app.fun_games_table.column(col, width=width, anchor="w")
    app.fun_games_table.pack(fill="both", expand=True)
    _bind_if_callable(
        app.fun_games_table,
        "<Double-1>",
        lambda _e: app.start_selected_fun_game(),
    )

    status_row = ttk.Frame(app.tab_fun)
    status_row.pack(fill="x", pady=(8, 0))
    ttk.Label(status_row, textvariable=app.fun_status_var).pack(side="left")
    ttk.Label(status_row, textvariable=app.fun_dependency_var).pack(
        side="right", padx=(8, 0)
    )

    ttk.Label(
        app.tab_fun,
        textvariable=app.fun_hint_var,
        justify="left",
    ).pack(anchor="w", pady=(6, 0))

    app.refresh_fun_games()
