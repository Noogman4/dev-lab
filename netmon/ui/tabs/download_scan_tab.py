"""Download scan tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_download_scan_header(app, frame) -> None:
    """Build the static Download Scan introduction panel."""
    header = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_header", "Download scan / temp download"),
        padding=10,
    )
    header.pack(fill="x", pady=(0, 10))
    ttk.Label(
        header,
        text=app.tr(
            "download_scan_header_intro",
            "Save downloads to this pre-quarantine folder first. After a successful check, NetMon can move the file to the normal download folder.",
        ),
        justify="left",
        wraplength=760,
    ).pack(anchor="w")
    ttk.Label(
        header,
        text=app.tr(
            "download_scan_label_files_not_auto_deleted",
            "Files are not deleted automatically.",
        ),
        justify="left",
    ).pack(anchor="w", pady=(4, 0))
    ttk.Label(
        header,
        text=app.tr(
            "download_scan_header_hint_persistent",
            "Note: files in this area are intended for temporary use only, but they remain across NetMon restarts and usually disappear only after a system/mount restart or manual clearing.",
        ),
        justify="left",
        wraplength=760,
    ).pack(anchor="w", pady=(4, 0))


def build_download_scan_prequarantine_summary(app, frame):
    """Build the Pre-Quarantine status summary and return its container."""
    temp_group = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_prequarantine", "Pre-quarantine folder"),
        padding=8,
    )
    temp_group.pack(fill="x", pady=(0, 8))
    temp_group.columnconfigure(1, weight=1)
    ttk.Label(
        temp_group,
        text=app.tr(
            "download_scan_label_current_prequarantine_path",
            "Current pre-quarantine path:",
        ),
    ).grid(row=0, column=0, sticky="nw")
    ttk.Label(
        temp_group,
        textvariable=app.download_scan_temp_dir_var,
        justify="left",
        wraplength=520,
    ).grid(row=0, column=1, sticky="w", padx=(8, 0))
    ttk.Label(
        temp_group,
        textvariable=app.download_scan_temp_security_var,
        justify="left",
        wraplength=520,
    ).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Label(
        temp_group,
        textvariable=app.download_scan_temp_hint_var,
        justify="left",
        wraplength=520,
    ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Label(
        temp_group,
        textvariable=app.download_scan_temp_success_var,
        justify="left",
        wraplength=520,
        foreground="#2e7d32",
        font=("TkDefaultFont", 9, "bold"),
    ).grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    ttk.Label(
        temp_group,
        textvariable=app.download_scan_temp_warning_var,
        justify="left",
        wraplength=520,
        foreground="#c62828",
        font=("TkDefaultFont", 9, "bold"),
    ).grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(4, 0))
    return temp_group


def build_download_scan_prequarantine_actions(app, temp_group) -> None:
    """Build Pre-Quarantine management, access and startup controls."""
    temp_btns = ttk.Frame(temp_group)
    temp_btns.grid(row=5, column=0, columnspan=2, sticky="w", pady=(8, 0))
    temp_manage_btns = ttk.Frame(temp_btns)
    temp_manage_btns.grid(row=0, column=0, sticky="w")
    app.btn_download_scan_temp_activate = ttk.Button(
        temp_manage_btns,
        text="Temp-Ordner aktivieren",
        command=app.create_download_scan_temp_folder,
    )
    app.btn_download_scan_temp_activate.pack(side="left")
    ttk.Button(
        temp_manage_btns,
        text="Temp-Ordner deaktivieren",
        command=app.disable_download_scan_temp_folder,
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        temp_manage_btns,
        text="Temp-Ordner leeren",
        command=app.clear_download_scan_temp_folder,
    ).pack(side="left", padx=(8, 0))
    temp_access_btns = ttk.Frame(temp_btns)
    temp_access_btns.grid(row=1, column=0, sticky="w", pady=(8, 0))
    ttk.Button(
        temp_access_btns,
        text="Temp-Ordner öffnen",
        command=app.open_download_scan_temp_folder,
    ).pack(side="left")
    ttk.Button(
        temp_access_btns,
        text="Pfad kopieren",
        command=app.copy_download_scan_temp_folder_path,
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        temp_access_btns,
        text=app.tr("download_scan_btn_change_path", "Change path"),
        command=app.choose_download_scan_temp_dir,
    ).pack(side="left", padx=(8, 0))
    app.cb_download_scan_prequarantine_startup = ttk.Checkbutton(
        temp_group,
        text="Vor-Quarantäne bei NetMon-Start automatisch aktivieren",
        variable=app.download_scan_prequarantine_startup_var,
        command=app.on_download_scan_prequarantine_startup_toggle,
    )
    app.cb_download_scan_prequarantine_startup.grid(
        row=6, column=0, columnspan=2, sticky="w", pady=(8, 0)
    )


def build_download_scan_target_folder_panel(app, frame) -> None:
    """Build the normal Download target folder panel and its actions."""
    target_group = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_target_folder", "Target folder"),
        padding=8,
    )
    target_group.pack(fill="x", pady=(0, 8))
    target_group.columnconfigure(1, weight=1)
    ttk.Label(
        target_group,
        text=app.tr(
            "download_scan_label_normal_download_folder",
            "Normal download folder:",
        ),
    ).grid(row=0, column=0, sticky="nw")
    ttk.Label(
        target_group,
        textvariable=app.download_scan_target_dir_var,
        justify="left",
        wraplength=520,
    ).grid(row=0, column=1, sticky="w", padx=(8, 0))
    target_btns = ttk.Frame(target_group)
    target_btns.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Button(
        target_btns,
        text=app.tr("download_scan_btn_choose_target", "Choose target folder"),
        command=app.choose_download_scan_target_dir,
    ).pack(side="left")
    ttk.Button(
        target_btns,
        text=app.tr("download_scan_btn_open_target", "Open target folder"),
        command=app.open_download_scan_target_folder,
    ).pack(side="left", padx=(8, 0))


def build_download_scan_actions(app, frame) -> None:
    """Build the Download Scan action buttons."""
    scan_actions = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_scan_actions", "Scan actions"),
        padding=8,
    )
    scan_actions.pack(fill="x", pady=(0, 8))
    scan_btns_top = ttk.Frame(scan_actions)
    scan_btns_top.pack(fill="x")
    app.btn_download_scan_scan_file = ttk.Button(
        scan_btns_top,
        text=app.tr("download_scan_btn_choose_and_scan", "Choose file and scan"),
        command=app.choose_and_scan_download_scan_file,
    )
    app.btn_download_scan_scan_file.pack(side="left")
    app.btn_download_scan_scan_temp = ttk.Button(
        scan_btns_top,
        text=app.tr(
            "download_scan_btn_scan_temp_with_clamav",
            "Scan temporary folder with ClamAV",
        ),
        command=app.scan_download_scan_temp_folder,
    )
    app.btn_download_scan_scan_temp.pack(side="left", padx=(8, 0))


def build_download_scan_post_scan_options(app, frame) -> None:
    """Build Download Scan options applied after a clean scan."""
    post_scan = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_after_success", "After successful scan"),
        padding=8,
    )
    post_scan.pack(fill="x", pady=(0, 8))
    ttk.Checkbutton(
        post_scan,
        text=app.tr(
            "download_scan_check_auto_move_clean",
            "Automatically move to Downloads after a clean ClamAV scan",
        ),
        variable=app.download_scan_auto_move_var,
    ).pack(anchor="w")
    ttk.Checkbutton(
        post_scan,
        text=app.tr("download_scan_check_ask_before_move", "Ask before moving"),
        variable=app.download_scan_ask_before_move_var,
    ).pack(anchor="w", pady=(4, 0))
    ttk.Checkbutton(
        post_scan,
        text=app.tr(
            "download_scan_check_keep_original",
            "Keep original in temporary folder",
        ),
        variable=app.download_scan_keep_original_var,
    ).pack(anchor="w", pady=(4, 0))
    ttk.Checkbutton(
        post_scan,
        text=app.tr("download_scan_check_save_report", "Save scan report"),
        variable=app.download_scan_save_report_var,
    ).pack(anchor="w", pady=(4, 0))


def build_download_scan_result_panel(app, frame) -> None:
    """Build Download Scan status and detailed result output."""
    status_group = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_status", "Download scan status"),
        padding=8,
    )
    status_group.pack(fill="x", pady=(0, 8))
    status_group.columnconfigure(1, weight=1)
    status_group.columnconfigure(3, weight=1)
    ttk.Label(
        status_group,
        text=app.tr("download_scan_label_traffic_light", "Indicator:"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        status_group,
        textvariable=app.download_scan_status_var,
        font=("TkDefaultFont", 10, "bold"),
    ).grid(row=0, column=1, sticky="w", padx=(8, 20))
    ttk.Label(
        status_group,
        text=app.tr(
            "download_scan_legend",
            "🟢 clean   🟡 unchecked   🔴 finding / suspicious",
        ),
    ).grid(row=0, column=2, columnspan=2, sticky="w")
    ttk.Label(
        status_group, text=app.tr("download_scan_label_last_scan", "Last scan:")
    ).grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Label(
        status_group,
        textvariable=app.download_scan_last_scan_var,
    ).grid(row=1, column=1, sticky="w", padx=(8, 20), pady=(6, 0))
    ttk.Label(status_group, text=app.tr("download_scan_label_result", "Result:")).grid(
        row=1, column=2, sticky="w", pady=(6, 0)
    )
    ttk.Label(
        status_group,
        textvariable=app.download_scan_result_summary_var,
    ).grid(row=1, column=3, sticky="w", padx=(8, 0), pady=(6, 0))
    ttk.Label(status_group, text=app.tr("download_scan_label_file", "File:")).grid(
        row=2, column=0, sticky="w", pady=(6, 0)
    )
    ttk.Label(
        status_group,
        textvariable=app.download_scan_file_var,
        wraplength=620,
    ).grid(row=2, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=(6, 0))
    result_group = ttk.LabelFrame(
        frame,
        text=app.tr("download_scan_group_result", "Scan result"),
        padding=8,
    )
    result_group.pack(fill="both", expand=True)
    result_group.columnconfigure(0, weight=1)
    result_group.rowconfigure(0, weight=1)
    app.download_scan_result_text = tk.Text(
        result_group,
        height=7,
        wrap="word",
        relief="solid",
        borderwidth=1,
    )
    app.download_scan_result_text.grid(row=0, column=0, sticky="nsew")
    app.download_scan_result_text.insert(
        "1.0",
        app.tr("download_scan_result_text_default", "No scan executed yet."),
    )
    app.download_scan_result_text.configure(state="disabled")
    app.attach_selection_copy_shortcuts(app.download_scan_result_text, "text")
    app.attach_text_context_menu(app.download_scan_result_text)


def build_download_scan_tab(app):
    app.tab_download_scan = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_download_scan,
        text=app.tr("tab_download_scan", "D-Scan"),
    )
    app.build_download_scan_tab()
