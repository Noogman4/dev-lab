"""Settings tab builder for NetMon."""

from __future__ import annotations

from tkinter import ttk


def build_settings_tab(app):
    app.tab_settings = ttk.Frame(app.nb, padding=10)
    app.nb.add(
        app.tab_settings,
        text=app.tr("tab_settings", "Einstellungen"),
    )
    app.build_settings_tab()


def build_settings_general_system(
    app, general_tab, theme_display_names, dns_profiles
) -> None:
    """Build the general start and system settings controls."""
    system_group = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_start_system", "Start & System"),
        padding=10,
    )
    system_group.pack(fill="x", pady=(0, 10))
    system_group.columnconfigure(1, weight=1)
    actions = ttk.Frame(system_group)
    actions.grid(row=0, column=1, sticky="e", padx=(8, 0), pady=(0, 6))
    for key, fallback, command, padding in (
        (
            "settings_save_button",
            "Einstellungen speichern",
            app.apply_settings_from_ui,
            None,
        ),
        (
            "settings_restart_netmon_only",
            "NetMon neu starten",
            app.restart_netmon_only,
            (6, 0),
        ),
        (
            "settings_reset_button",
            "Zurücksetzen",
            app.reset_settings_to_defaults,
            (6, 0),
        ),
    ):
        button = ttk.Button(actions, text=app.tr(key, fallback), command=command)
        if padding is None:
            button.pack(anchor="e")
        else:
            button.pack(anchor="e", pady=padding)
    for row, key, fallback, variable, command in (
        (
            1,
            "settings_autostart",
            "NetMon automatisch beim Login starten",
            app.autostart_var,
            app.toggle_autostart,
        ),
        (
            2,
            "settings_radio_desktop_launcher",
            "Radio-Desktopstarter aktivieren",
            app.radio_desktop_launcher_var,
            app.toggle_radio_desktop_launcher,
        ),
        (
            5,
            "settings_start_security_monitoring",
            "Security Monitoring beim Start aktivieren",
            app.var_start_security_monitoring,
            None,
        ),
    ):
        check = ttk.Checkbutton(
            system_group, text=app.tr(key, fallback), variable=variable, command=command
        )
        check.grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(4, 0) if row != 1 else 0
        )
    for row, key, fallback, variable, values, width in (
        (
            3,
            "settings_language_label",
            "Sprache:",
            app.var_language,
            app._language_choice_values(),
            18,
        ),
        (
            4,
            "settings_theme_label",
            "Theme:",
            app.var_theme_choice,
            list(theme_display_names.values()),
            18,
        ),
        (
            6,
            "settings_isp_dns_fallback",
            "DNS after VPN disconnect:",
            app.var_isp_dns_fallback_profile,
            [choice for choice in dns_profiles if choice != "System (DHCP/auto)"],
            24,
        ),
    ):
        ttk.Label(system_group, text=app.tr(key, fallback)).grid(
            row=row, column=0, sticky="w", pady=(8, 0)
        )
        ttk.Combobox(
            system_group,
            textvariable=variable,
            values=values,
            state="readonly",
            width=width,
        ).grid(row=row, column=1, sticky="w", padx=(8, 0), pady=(8, 0))


def build_settings_tooltips(app, general_tab) -> None:
    """Build the main-window status tooltip settings."""
    tooltip_group = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_status_tooltips", "Status / Tooltips"),
        padding=10,
    )
    tooltip_group.pack(fill="x", pady=(0, 10))
    ttk.Checkbutton(
        tooltip_group,
        text=app.tr("settings_tooltips_enabled", "Enable tooltips in the main window"),
        variable=app.tooltips_enabled,
        command=app.on_tooltip_toggle,
    ).pack(anchor="w")
    ttk.Label(
        tooltip_group,
        text=app.tr(
            "settings_tooltips_help_text",
            "Status help for the left header area:\n"
            "Firewall: left click opens Security, right click toggles / shows status.\n"
            "VPN: left click opens VPN, right click switches profile / disconnects.\n"
            "DNS Guard: left click opens DNS, right click opens maintenance / guard.\n"
            "Startup Guard / Process Guard / PATH Guard: left click opens Security, "
            "right click starts the matching check.\n"
            "DoT / Killswitch / Security / UFW Logging: left click opens details, "
            "right click controls the respective function.",
        ),
        justify="left",
        wraplength=620,
    ).pack(anchor="w", pady=(8, 0))


def build_settings_donation(app, general_tab) -> None:
    """Build the donation reminder settings."""
    donation_group = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_donation", "NetMon unterstützen"),
        padding=10,
    )
    donation_group.pack(fill="x", pady=(0, 10))
    option_row = ttk.Frame(donation_group)
    option_row.pack(fill="x")
    app.cb_donation_popup_enabled = ttk.Checkbutton(
        option_row,
        text=app.tr(
            "settings_donation_popup_enabled", "Spendenhinweis beim Start anzeigen"
        ),
        variable=app.var_donation_popup_enabled,
    )
    app.cb_donation_popup_enabled.pack(side="left", anchor="w")
    ttk.Button(
        option_row,
        text=app.tr("settings_donation_support_button", "NetMon Roots unterstützen"),
        state="disabled",
    ).pack(side="left", padx=(12, 0))
    ttk.Label(
        donation_group,
        textvariable=app.donation_popup_settings_note_var,
        justify="left",
        wraplength=620,
    ).pack(anchor="w", pady=(6, 0))
    app.refresh_donation_settings_controls()


def build_settings_logging(app, general_tab) -> None:
    """Build application and network debug logging settings."""
    logging_group = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_logging", "Logging"),
        padding=10,
    )
    logging_group.pack(fill="x", pady=(0, 10))
    logging_group.columnconfigure(1, weight=1)
    ttk.Checkbutton(
        logging_group,
        text=app.tr("settings_auto_log_clear", "Clear log automatically on startup"),
        variable=app.var_auto_log_clear,
    ).grid(row=0, column=0, columnspan=2, sticky="w")
    ttk.Checkbutton(
        logging_group,
        text=app.tr(
            "settings_debug_network_logging", "Enable advanced network debug logging"
        ),
        variable=app.var_debug_network_logging,
    ).grid(row=1, column=0, sticky="w", pady=(4, 0))
    for column, key, fallback, command in (
        (
            1,
            "settings_open_network_debug_log",
            "Netzwerk-Debug-Log öffnen",
            app.open_network_debug_log_file,
        ),
        (
            2,
            "settings_clear_network_debug_log",
            "Log-Datei leeren",
            app.clear_network_debug_log_file,
        ),
    ):
        ttk.Button(logging_group, text=app.tr(key, fallback), command=command).grid(
            row=1, column=column, sticky="w", padx=(8, 0), pady=(4, 0)
        )
    ttk.Label(
        logging_group,
        text=app.tr("settings_ufw_logging_default", "Default UFW logging:"),
    ).grid(row=2, column=0, sticky="w", pady=(8, 0))
    ttk.Combobox(
        logging_group,
        textvariable=app.var_ufw_logging_default,
        values=["off", "low", "medium", "high", "full"],
        state="readonly",
        width=14,
    ).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))
