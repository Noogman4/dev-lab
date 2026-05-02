"""Security notebook tab builders for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_security_tabs(app):
    app.tab_privacy = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_privacy,
        text=app.tr("security_tab_privacy", "Privacy"),
    )

    privacy_frame = ttk.LabelFrame(
        app.tab_privacy,
        text=app.tr("privacy_group_stealth", "ISP-Stealthmodus"),
        padding=10,
    )
    privacy_frame.pack(fill="x", pady=(0, 8))

    cb_stealth = ttk.Checkbutton(
        privacy_frame,
        text=app.tr("privacy_check_enabled", "Stealthmodus aktiv"),
        variable=app.isp_stealth_enabled,
        command=app.save_privacy_config,
    )
    cb_stealth.pack(anchor="w")

    cb_autostart = ttk.Checkbutton(
        privacy_frame,
        text=app.tr("privacy_check_autostart", "Autostart beim Programmstart"),
        variable=app.isp_stealth_autostart,
        command=app.save_privacy_config,
    )
    cb_autostart.pack(anchor="w", pady=(4, 0))

    app.cb_privacy_ipv6 = ttk.Checkbutton(
        privacy_frame,
        text=app.tr("privacy_check_disable_ipv6", "IPv6 deaktivieren"),
        variable=app.isp_stealth_disable_ipv6,
        command=app.save_privacy_config,
    )
    app.cb_privacy_ipv6.pack(anchor="w", pady=(4, 0))
    app.add_tooltip(
        app.cb_privacy_ipv6,
        "Diese Option ist nur verfuegbar, wenn das aktive oder gewaehlte VPN-Profil IPv6 unterstuetzt.",
    )
    app.privacy_ipv6_hint = ttk.Label(
        privacy_frame,
        text="",
        foreground="#666666",
        wraplength=240,
        justify="left",
    )
    app.privacy_ipv6_hint.pack(anchor="w")

    app.cb_privacy_ipv6.pack_forget()
    app.privacy_ipv6_hint.pack_forget()

    cb_killswitch = ttk.Checkbutton(
        privacy_frame,
        text=app.tr("privacy_check_killswitch", "Killswitch aktivieren"),
        variable=app.isp_stealth_enable_killswitch,
        command=app.save_privacy_config,
    )
    cb_killswitch.pack(anchor="w", pady=(4, 0))

    cb_strict = ttk.Checkbutton(
        privacy_frame,
        text=app.tr(
            "privacy_check_strict",
            "Strenger Schutz (kritische Aktionen nur mit Bestätigungswort)",
        ),
        variable=app.strict_protection_var,
        command=app.save_privacy_config,
    )
    cb_strict.pack(anchor="w", pady=(4, 0))
    app.add_tooltip(
        cb_strict,
        "Wenn aktiv, verlangen kritische Aktionen zusaetzlich das Wort AUSFUEHREN.",
    )

    vpn_frame = ttk.Frame(privacy_frame)
    vpn_frame.pack(fill="x", pady=(8, 0))
    ttk.Label(vpn_frame, text=app.tr("privacy_label_vpn_profile", "VPN-Profil:")).pack(
        side="left"
    )
    app.isp_stealth_vpn_combo = ttk.Combobox(
        vpn_frame,
        textvariable=app.isp_stealth_vpn_choice,
        values=[item["label"] for item in app.get_privacy_vpn_options()],
        state="readonly",
    )
    app.isp_stealth_vpn_combo.pack(side="left", fill="x", expand=True, padx=(8, 0))
    app.isp_stealth_vpn_combo.bind(
        "<<ComboboxSelected>>", lambda e: app.on_privacy_vpn_selected()
    )

    dns_frame = ttk.Frame(privacy_frame)
    dns_frame.pack(fill="x", pady=(4, 0))
    ttk.Label(dns_frame, text=app.tr("privacy_label_dns_profile", "DNS-Profil:")).pack(
        side="left"
    )
    ttk.Label(dns_frame, textvariable=app.isp_stealth_dns_profile).pack(
        side="left", fill="x", expand=True, padx=(8, 0)
    )

    btn_frame = ttk.Frame(privacy_frame)
    btn_frame.pack(fill="x", pady=(12, 0))
    btn_on = ttk.Button(
        btn_frame,
        text=app.tr("privacy_btn_on", "Stealthmodus AN"),
        command=app.isp_stealth_on,
    )
    btn_on.pack(side="left")
    btn_off = ttk.Button(
        btn_frame,
        text=app.tr("privacy_btn_off", "Stealthmodus AUS"),
        command=app.isp_stealth_off,
    )
    btn_off.pack(side="left", padx=(8, 0))

    app.tab_security = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(
        app.tab_security,
        text=app.tr("security_tab_main", "Security"),
    )
    app.security_status_var = tk.StringVar(value="Monitoring: AUS")
    app.security_level_var = tk.StringVar(value="Logging: –")
    app.security_count_var = tk.StringVar(value="Events: 0")
    app.security_alarm_var = tk.StringVar(value="Letzter Alarm: –")
    sec_top = ttk.Frame(app.tab_security)
    sec_top.pack(fill="x", pady=(0, 8))
    ttk.Label(sec_top, textvariable=app.security_status_var).pack(side="left")
    ttk.Label(sec_top, text=" | ").pack(side="left")
    ttk.Label(sec_top, textvariable=app.security_level_var).pack(side="left")
    ttk.Label(sec_top, text=" | ").pack(side="left")
    ttk.Label(sec_top, textvariable=app.security_count_var).pack(side="left")
    ttk.Label(sec_top, text=" | ").pack(side="left")
    ttk.Label(sec_top, textvariable=app.security_alarm_var).pack(side="left")

    sec_controls = ttk.Frame(app.tab_security)
    sec_controls.pack(fill="x", pady=(0, 8))

    sec_actions = ttk.LabelFrame(
        sec_controls,
        text=app.tr("security_group_actions", "Aktionen"),
        padding=6,
    )
    sec_actions.pack(fill="x")

    btn_sec_export = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_export_logs", "Logs exportieren (.txt)"),
        command=app.export_security_logs,
    )
    btn_sec_export.pack(side="left")
    app.add_tooltip(
        btn_sec_export,
        "Exportiert alle Security-Events als TXT-Datei auf den Desktop.",
    )

    btn_sec_refresh = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_refresh_table", "Tabelle aktualisieren"),
        command=app.security_refresh_table_action,
    )
    btn_sec_refresh.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_refresh,
        "Aktualisiert die Security-Tabelle und Statistik manuell.",
    )

    btn_sec_scan = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_scan_now", "Security-Scan jetzt"),
        command=app.security_scan_now,
    )
    btn_sec_scan.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_scan,
        "Führt einen sofortigen File/Device-/UFW-Scan aus.",
    )

    btn_sec_input_scan = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_input_scan", "Input-Zugriffe prüfen"),
        command=app.security_input_access_scan,
    )
    btn_sec_input_scan.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_input_scan,
        "Prüft aktuell offene Zugriffe auf /dev/input-Geräte.",
    )

    btn_sec_chad = ttk.Button(
        sec_actions,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=app.prepare_security_chad_analysis,
    )
    btn_sec_chad.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_chad,
        "Bereitet eine lokale Security-Zusammenfassung für den Chad Analyse-Tab vor.",
    )

    btn_sec_rebaseline = ttk.Button(
        sec_actions,
        text=app.tr("security_btn_rebaseline", "Baseline neu erstellen"),
        command=app.security_build_baseline,
    )
    btn_sec_rebaseline.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_rebaseline,
        "Erstellt die File/Device-Baseline neu.",
    )

    sec_filters = ttk.LabelFrame(
        sec_controls,
        text=app.tr("security_group_filters", "Filter"),
        padding=6,
    )
    sec_filters.pack(fill="x", pady=(8, 0))

    btn_sec_filter_scan = ttk.Button(
        sec_filters,
        text=app.tr("security_btn_filter_scan", "Nur Portscan"),
        command=app.security_filter_portscan,
    )
    btn_sec_filter_scan.pack(side="left")
    app.add_tooltip(
        btn_sec_filter_scan,
        "Zeigt nur Events mit Portscan-Verdacht an.",
    )

    btn_sec_filter_relevant = ttk.Button(
        sec_filters,
        text=app.tr("security_btn_filter_relevant", "Relevant"),
        command=app.security_filter_relevant,
    )
    btn_sec_filter_relevant.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_filter_relevant,
        "Zeigt nur Warnungen und Alarme an.",
    )

    btn_sec_filter_external = ttk.Button(
        sec_filters,
        text=app.tr("security_btn_filter_external", "Externe"),
        command=app.security_filter_external,
    )
    btn_sec_filter_external.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_filter_external,
        "Zeigt nur externe UFW-Blocks an.",
    )

    btn_sec_filter_all = ttk.Button(
        sec_filters,
        text=app.tr("security_btn_filter_all", "Alle Events"),
        command=app.security_filter_all,
    )
    btn_sec_filter_all.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_filter_all,
        "Zeigt wieder alle Security-Events an.",
    )

    btn_sec_clear = ttk.Button(
        sec_filters,
        text=app.tr("security_btn_clear_events", "Events leeren"),
        command=lambda: app.security_clear_events(confirm=True),
    )
    btn_sec_clear.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_sec_clear,
        "Löscht die aktuelle Eventliste im Security-Tab.",
    )

    path_guard_frame = ttk.LabelFrame(
        app.tab_security,
        text=app.tr("path_guard_group_title", "PATH Guard"),
        padding=6,
    )
    path_guard_frame.pack(fill="x", pady=(0, 8))

    btn_path_guard_check = ttk.Button(
        path_guard_frame,
        text=app.tr("path_guard_btn_check", "PATH prüfen"),
        command=app.run_path_guard_check,
    )
    btn_path_guard_check.pack(side="left")
    app.add_tooltip(
        btn_path_guard_check,
        app.tr(
            "tooltip_path_guard_check",
            "Prüft PATH-Einträge und Shell-Profile auf auffällige Manipulationen.",
        ),
    )

    btn_path_guard_chad = ttk.Button(
        path_guard_frame,
        text=app.tr("path_guard_btn_chad", "Mit Chad analysieren"),
        command=app.analyze_path_guard_with_chad,
    )
    btn_path_guard_chad.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_path_guard_chad,
        app.tr(
            "tooltip_path_guard_chad",
            "Bereitet die letzte PATH Guard Prüfung für Chad vor.",
        ),
    )

    ttk.Label(
        path_guard_frame,
        textvariable=app.path_guard_status_var,
    ).pack(side="left", padx=(12, 0))

    sec_stats = ttk.Frame(app.tab_security)
    sec_stats.pack(fill="x", pady=(0, 8))
    app.security_stat_total_var = tk.StringVar(value="0")
    app.security_stat_block_var = tk.StringVar(value="0")
    app.security_stat_scan_var = tk.StringVar(value="0")
    app.security_stat_top_ip_var = tk.StringVar(value="–")
    app.security_stat_top_port_var = tk.StringVar(value="–")
    for i in range(5):
        sec_stats.columnconfigure(i, weight=1)
    for col, title, var in [
        (0, "Gesamt-Events", app.security_stat_total_var),
        (1, "BLOCK-Events", app.security_stat_block_var),
        (2, "Portscan-Verdacht", app.security_stat_scan_var),
        (3, "Top Quelle-IP", app.security_stat_top_ip_var),
        (4, "Häufigster Ziel-Port", app.security_stat_top_port_var),
    ]:
        box = ttk.LabelFrame(sec_stats, text=title, padding=6)
        box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0))
        ttk.Label(box, textvariable=var).pack(anchor="center")

    app.security_table = ttk.Treeview(
        app.tab_security,
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
    app.security_table.pack(fill="both", expand=True)
    app.security_table.bind("<<TreeviewSelect>>", app.on_security_event_select)

    app.security_detail = tk.Text(app.tab_security, wrap="word", height=8)
    app.security_detail.pack(fill="both", expand=True, pady=(8, 0))

    app.tab_clamav = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(app.tab_clamav, text="ClamAV")

    clamav_wrap = ttk.Frame(app.tab_clamav)
    clamav_wrap.pack(fill="both", expand=True)

    app.clamav_canvas = tk.Canvas(clamav_wrap, highlightthickness=0)
    app.clamav_canvas.pack(side="left", fill="both", expand=True)

    app.clamav_scrollbar = ttk.Scrollbar(
        clamav_wrap,
        orient="vertical",
        command=app.clamav_canvas.yview,
    )
    app.clamav_scrollbar.pack(side="right", fill="y")
    app.clamav_canvas.configure(yscrollcommand=app.clamav_scrollbar.set)

    app.clamav_scroll_frame = ttk.Frame(app.clamav_canvas)
    app.clamav_canvas_window = app.clamav_canvas.create_window(
        (0, 0),
        window=app.clamav_scroll_frame,
        anchor="nw",
    )

    app._clamav_canvas_mousewheel_active = False

    def _on_clamav_frame_config(_event):
        app.clamav_canvas.configure(scrollregion=app.clamav_canvas.bbox("all"))

    def _on_clamav_canvas_config(event):
        app.clamav_canvas.itemconfig(app.clamav_canvas_window, width=event.width)

    def _clamav_canvas_set_wheel_active(active):
        app._clamav_canvas_mousewheel_active = bool(active)

    def _on_clamav_canvas_wheel(event):
        if not getattr(app, "_clamav_canvas_mousewheel_active", False):
            return None

        if getattr(event, "num", None) == 4:
            app.clamav_canvas.yview_scroll(-1, "units")
            return "break"
        if getattr(event, "num", None) == 5:
            app.clamav_canvas.yview_scroll(1, "units")
            return "break"

        delta = getattr(event, "delta", 0)
        if delta:
            step = -1 if delta > 0 else 1
            app.clamav_canvas.yview_scroll(step, "units")
            return "break"
        return None

    app.clamav_scroll_frame.bind("<Configure>", _on_clamav_frame_config)
    app.clamav_canvas.bind("<Configure>", _on_clamav_canvas_config)

    app.clamav_canvas.bind("<Enter>", lambda _e: _clamav_canvas_set_wheel_active(True))
    app.clamav_canvas.bind("<Leave>", lambda _e: _clamav_canvas_set_wheel_active(False))
    app.clamav_canvas.bind_all("<MouseWheel>", _on_clamav_canvas_wheel)
    app.clamav_canvas.bind_all("<Button-4>", _on_clamav_canvas_wheel)
    app.clamav_canvas.bind_all("<Button-5>", _on_clamav_canvas_wheel)

    clamav_status = ttk.LabelFrame(app.clamav_scroll_frame, text="Status", padding=6)
    clamav_status.pack(fill="x")
    clamav_status.columnconfigure(1, weight=1)
    clamav_status.columnconfigure(3, weight=1)

    ttk.Label(clamav_status, text="Status:").grid(row=0, column=0, sticky="w")
    ttk.Label(clamav_status, textvariable=app.clamav_status_var).grid(
        row=0, column=1, sticky="w", padx=(8, 12)
    )
    ttk.Label(clamav_status, text="Laufzeit:").grid(row=0, column=2, sticky="w")
    ttk.Label(clamav_status, textvariable=app.clamav_runtime_var).grid(
        row=0, column=3, sticky="w", padx=(8, 0)
    )

    ttk.Label(clamav_status, text="Signaturen:").grid(
        row=1, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_signatures_var).grid(
        row=1, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(clamav_status, text="Dateien gescannt:").grid(
        row=1, column=2, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_scanned_files_var).grid(
        row=1, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text="Letzter Scan:").grid(
        row=2, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_last_scan_var).grid(
        row=2, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(clamav_status, text="Geschwindigkeit:").grid(
        row=2, column=2, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_speed_var).grid(
        row=2, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text="Letztes Ziel:").grid(
        row=3, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_last_target_var).grid(
        row=3, column=1, sticky="w", padx=(8, 12), pady=(2, 0)
    )
    ttk.Label(clamav_status, text="ETA:").grid(row=3, column=2, sticky="w", pady=(2, 0))
    ttk.Label(clamav_status, textvariable=app.clamav_eta_var).grid(
        row=3, column=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    ttk.Label(clamav_status, text="Funde:").grid(
        row=4, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_findings_var).grid(
        row=4, column=1, sticky="w", padx=(8, 0), pady=(2, 0)
    )
    ttk.Label(clamav_status, text="Ergebnis:").grid(
        row=5, column=0, sticky="w", pady=(2, 0)
    )
    ttk.Label(clamav_status, textvariable=app.clamav_result_var).grid(
        row=5, column=1, columnspan=3, sticky="w", padx=(8, 0), pady=(2, 0)
    )

    clamav_scan = ttk.LabelFrame(app.clamav_scroll_frame, text="Scan", padding=6)
    clamav_scan.pack(fill="x", pady=(8, 0))

    clamav_scan_row1 = ttk.Frame(clamav_scan)
    clamav_scan_row1.pack(fill="x")

    btn_clamav_update = ttk.Button(
        clamav_scan_row1,
        text="ClamAV Update",
        command=app.security_clamav_update_async,
    )
    btn_clamav_update.pack(side="left")
    app.register_feature_button("clamav_update", btn_clamav_update)
    app.add_tooltip(
        btn_clamav_update,
        "Aktualisiert ClamAV-Signaturen mit freshclam.",
    )

    btn_clamav_quick = ttk.Button(
        clamav_scan_row1,
        text="ClamAV Schnellscan",
        command=app.security_clamav_quickscan_async,
    )
    btn_clamav_quick.pack(side="left", padx=(8, 0))
    app.register_feature_button("clamav_scan", btn_clamav_quick)
    app.add_tooltip(
        btn_clamav_quick,
        "Startet einen kompakten ClamAV-Schnellscan auf typische Benutzerordner.",
    )

    btn_clamav_folder = ttk.Button(
        clamav_scan_row1,
        text="ClamAV Ordner scannen",
        command=app.security_clamav_folder_scan_async,
    )
    btn_clamav_folder.pack(side="left", padx=(8, 0))
    app.register_feature_button("clamav_scan", btn_clamav_folder)
    app.add_tooltip(
        btn_clamav_folder,
        "Öffnet eine Ordnerauswahl und scannt den gewählten Ordner mit ClamAV.",
    )

    btn_clamav_system = ttk.Button(
        clamav_scan_row1,
        text="Systemscan",
        command=app.security_clamav_systemscan_async,
    )
    btn_clamav_system.pack(side="left", padx=(8, 0))
    app.register_feature_button("clamav_scan", btn_clamav_system)
    app.add_tooltip(
        btn_clamav_system,
        "Startet einen erweiterten ClamAV-Systemscan auf sinnvollen Standardpfaden.",
    )

    clamav_actions = ttk.LabelFrame(
        app.clamav_scroll_frame, text="Funde & Quarantäne", padding=6
    )
    clamav_actions.pack(fill="x", pady=(8, 0))

    clamav_actions_row1 = ttk.Frame(clamav_actions)
    clamav_actions_row1.pack(fill="x")
    clamav_actions_row2 = ttk.Frame(clamav_actions)
    clamav_actions_row2.pack(fill="x", pady=(6, 0))

    app.btn_clamav_show_findings = ttk.Button(
        clamav_actions_row1,
        text="Funde anzeigen",
        command=app.show_clamav_findings,
    )
    app.btn_clamav_show_findings.pack(side="left")
    app.add_tooltip(
        app.btn_clamav_show_findings,
        "Zeigt aktuell offene ClamAV-Funde mit Signatur an.",
    )

    app.btn_clamav_export_findings = ttk.Button(
        clamav_actions_row1,
        text="Funde exportieren",
        command=app.export_clamav_findings,
    )
    app.btn_clamav_export_findings.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_export_findings,
        "Exportiert ClamAV-Funde/Historie als JSON und TXT.",
    )

    app.btn_clamav_show_quarantine = ttk.Button(
        clamav_actions_row1,
        text="Quarantäne anzeigen",
        command=app.show_clamav_quarantine_history,
    )
    app.btn_clamav_show_quarantine.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_show_quarantine,
        "Zeigt Dateien in/aus der Quarantänehistorie.",
    )

    app.btn_clamav_abort_scan = ttk.Button(
        clamav_actions_row1,
        text="Scan abbrechen",
        command=app.clamav_abort_scan,
    )
    app.btn_clamav_abort_scan.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_abort_scan,
        "Bricht einen laufenden ClamAV-Scan ab.",
    )
    app.btn_clamav_abort_scan.configure(state="disabled")

    app.btn_clamav_quarantine = ttk.Button(
        clamav_actions_row2,
        text="In Quarantäne verschieben",
        command=app.quarantine_clamav_findings_async,
    )
    app.btn_clamav_quarantine.pack(side="left")
    app.add_tooltip(
        app.btn_clamav_quarantine,
        "Verschiebt offene ClamAV-Funde sicher nach ~/.netmon_quarantine.",
    )

    app.btn_clamav_quarantine_selected = ttk.Button(
        clamav_actions_row2,
        text="Auswahl quarantänisieren",
        command=app.quarantine_selected_clamav_findings_async,
    )
    app.btn_clamav_quarantine_selected.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_quarantine_selected,
        "Öffnet eine Auswahl und verschiebt nur ausgewählte Funde in Quarantäne.",
    )

    app.btn_clamav_restore_quarantine = ttk.Button(
        clamav_actions_row2,
        text="Aus Quarantäne wiederherstellen",
        command=app.restore_clamav_quarantine_async,
    )
    app.btn_clamav_restore_quarantine.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_restore_quarantine,
        "Stellt quarantänisierte Dateien sicher an ihren Ursprungsort wieder her.",
    )

    app.btn_clamav_restore_selected = ttk.Button(
        clamav_actions_row2,
        text="Auswahl wiederherstellen",
        command=app.restore_selected_clamav_quarantine_async,
    )
    app.btn_clamav_restore_selected.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        app.btn_clamav_restore_selected,
        "Öffnet eine Auswahl und stellt nur ausgewählte Quarantäne-Dateien wieder her.",
    )

    clamav_output_frame = ttk.LabelFrame(
        app.clamav_scroll_frame, text="Ergebnis / Fundliste / Historie", padding=6
    )
    clamav_output_frame.pack(fill="both", expand=True, pady=(8, 0))

    app.clamav_output_text = tk.Text(clamav_output_frame, wrap="word", height=12)
    app.clamav_output_text.pack(fill="both", expand=True)
    app.clamav_output_text.insert(
        "1.0", "ClamAV-Ergebnisse und Fortschritt erscheinen hier.\n"
    )
    app.clamav_output_text.configure(state="disabled")

    app._update_clamav_findings_buttons_state()

    app.tab_lynis = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(app.tab_lynis, text="Lynis")
    app.build_lynis_tab()

    app.tab_rkhunter = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(app.tab_rkhunter, text="rkhunter")
    app.build_rkhunter_tab()

    app.tab_startup_guard = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(app.tab_startup_guard, text="Startup")
    app.build_startup_guard_tab()

    app.tab_packet_capture = ttk.Frame(app.security_nb, padding=10)
    app.security_nb.add(app.tab_packet_capture, text="Capture")
    app.build_packet_capture_tab()
    app.after(300, app.refresh_packet_capture_interfaces)
