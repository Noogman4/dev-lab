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


def build_download_scan_tab(app):
    app.tab_download_scan = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_download_scan,
        text=app.tr("tab_download_scan", "D-Scan"),
    )
    app.build_download_scan_tab()
