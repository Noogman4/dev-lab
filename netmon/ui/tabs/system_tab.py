"""System subtab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_system_tab(app):
    app.tab_system = ttk.Frame(app.system_nb, padding=10)
    app.system_nb.add(
        app.tab_system,
        text=app.tr("system_tab_system", "System"),
    )
    app._build_system_tab()


def build_system_monitor(app) -> None:
    """Build the system monitor controls and information panels."""
    top = ttk.Frame(app.tab_system)
    top.pack(fill="x", pady=(0, 3))
    ttk.Label(
        top,
        text=app.tr(
            "system_monitor_intro",
            "Integrierter Systemmonitor (aktualisiert alle 1-2 Sekunden).",
        ),
    ).pack(side="left")
    app.btn_system_monitor_refresh = ttk.Button(
        top,
        text=app.tr("system_monitor_btn_refresh_now", "Jetzt aktualisieren"),
        command=app.system_monitor_refresh,
    )
    app.btn_system_monitor_refresh.pack(side="right")
    body = ttk.Frame(app.tab_system)
    body.pack(fill="both", expand=True)
    body.columnconfigure(0, weight=1)
    body.columnconfigure(1, weight=0)
    for name, key, fallback in (
        ("system_cpu_var", "system_status_cpu_default", "CPU: –"),
        ("system_ram_var", "system_status_ram_default", "RAM: –"),
        ("system_swap_var", "system_status_swap_default", "Swap: –"),
        ("system_disk_var", "system_status_disk_default", "Disk /: –"),
        ("system_temp_var", "system_status_temp_default", "CPU temp (sensor): –"),
        ("system_gpu_temp_var", "system_status_gpu_temp_default", "GPU temp: –"),
        ("system_uptime_var", "system_status_uptime_default", "Uptime: –"),
    ):
        setattr(app, name, tk.StringVar(value=app.tr(key, fallback)))
    app.system_cpu_bar = app._system_row(body, 0, "CPU-Auslastung", app.system_cpu_var)
    app.system_ram_bar = app._system_row(body, 1, "RAM", app.system_ram_var)
    app.system_swap_bar = app._system_row(body, 2, "Swap", app.system_swap_var)
    app.btn_system_swap_clear = ttk.Button(
        app.system_swap_bar["box"],
        text=app.tr("system_swap_clear_btn", "Clear swap"),
        command=app.clear_swap_async,
    )
    app.btn_system_swap_clear.grid(row=2, column=0, sticky="w", pady=(8, 0))
    app.btn_system_swap_resize = ttk.Button(
        app.system_swap_bar["box"],
        text=app.tr("system_swap_resize_btn", "Resize swap"),
        command=app.resize_swap_async,
    )
    app.btn_system_swap_resize.grid(
        row=2, column=0, sticky="w", padx=(110, 0), pady=(8, 0)
    )
    app.system_disk_bar = app._system_row(body, 3, "Disk /", app.system_disk_var)
    app.system_temp_bar = app._system_row(
        body,
        4,
        app.tr("system_group_cpu_temperature", "CPU temperature"),
        app.system_temp_var,
    )
    app.system_gpu_temp_bar = app._system_row(
        body,
        5,
        app.tr("system_group_gpu_temperature", "GPU temperature"),
        app.system_gpu_temp_var,
    )
    app.system_cpu_bar_widget = app.system_cpu_bar["bar"]
    app.system_temp_bar_widget = app.system_temp_bar["bar"]
    app.system_gpu_temp_bar_widget = app.system_gpu_temp_bar["bar"]
    uptime = ttk.LabelFrame(
        body, text=app.tr("system_group_uptime", "Uptime"), padding=8
    )
    uptime.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(8, 0))
    ttk.Label(uptime, textvariable=app.system_uptime_var).pack(anchor="w")
    sysinfo = ttk.LabelFrame(
        body, text=app.tr("system_group_sysinfo", "Sysinfo"), padding=8
    )
    sysinfo.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(10, 0))
    app.system_sysinfo_group = sysinfo
    sysinfo.columnconfigure(0, weight=1)
    sysinfo.columnconfigure(1, weight=1)
    body.rowconfigure(8, weight=1)
    app.sysinfo_vars = {}
    for row, column, title, entries in (
        (
            0,
            0,
            "Betriebssystem",
            [
                ("os_distribution", "Distribution"),
                ("os_version", "Version"),
                ("os_kernel", "Kernel"),
                ("os_arch", "Architektur"),
                ("os_hostname", "Hostname"),
                ("os_user", "Benutzer"),
            ],
        ),
        (
            0,
            1,
            "Hardware",
            [
                ("hw_cpu", "CPU"),
                ("hw_cores_threads", "Kerne/Threads"),
                ("hw_gpu", "GPU"),
                ("hw_board", "Mainboard"),
                ("hw_ram_total", "RAM gesamt"),
                ("hw_swap_total", "Swap gesamt"),
            ],
        ),
        (1, 0, "System", [("sys_root", "Root /"), ("sys_swap", "Swap")]),
        (
            1,
            1,
            "Software",
            [("sw_python", "Python"), ("sw_desktop", "Desktop-Session")],
        ),
    ):
        app._build_sysinfo_group(
            sysinfo, row=row, col=column, title=title, entries=entries
        )
    ttk.Frame(body).grid(row=8, column=0, columnspan=2, sticky="nsew")
    app._load_sysinfo_static()
    app._update_sysinfo_dynamic()
