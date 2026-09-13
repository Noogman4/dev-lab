"""Download scan tab builder for NetMon."""

from __future__ import annotations

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


def build_download_scan_tab(app):
    app.tab_download_scan = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_download_scan,
        text=app.tr("tab_download_scan", "D-Scan"),
    )
    app.build_download_scan_tab()
