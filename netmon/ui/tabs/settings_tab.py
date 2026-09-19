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


def build_settings_security(app, general_tab) -> None:
    """Build startup security and local tool protection settings."""
    security = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_security", "Security"),
        padding=10,
    )
    security.pack(fill="x", pady=(0, 10))
    ttk.Checkbutton(
        security,
        text=app.tr(
            "settings_startup_guard_autorun", "Check Startup Guard on program start"
        ),
        variable=app.var_startup_guard_autorun,
    ).pack(anchor="w")
    app.cb_settings_prequarantine_startup = ttk.Checkbutton(
        security,
        text=app.tr(
            "settings_prequarantine_startup",
            "Automatically enable pre-quarantine on NetMon start",
        ),
        variable=app.download_scan_prequarantine_startup_var,
        command=app.on_download_scan_prequarantine_startup_toggle,
    )
    app.cb_settings_prequarantine_startup.pack(anchor="w", pady=(4, 0))
    app.add_tooltip(
        app.cb_settings_prequarantine_startup,
        app.tr(
            "settings_prequarantine_startup_tooltip",
            "Enables download pre-quarantine on NetMon start and keeps the protected temporary folder ready automatically.",
        ),
    )
    for key, fallback, variable in (
        (
            "settings_process_guard_autorun",
            "Check Process Guard on program start",
            app.var_process_guard_autorun,
        ),
        (
            "settings_path_guard_autorun",
            "Check PATH Guard on program start",
            app.var_path_guard_autorun,
        ),
    ):
        ttk.Checkbutton(security, text=app.tr(key, fallback), variable=variable).pack(
            anchor="w", pady=(4, 0)
        )
    app.cb_wireshark_launch_blocked = ttk.Checkbutton(
        security,
        text=app.tr(
            "settings_wireshark_launch_blocked", "Block Wireshark launch inside NetMon"
        ),
        variable=app.var_wireshark_launch_blocked,
        command=app.on_wireshark_launch_block_toggle,
    )
    app.cb_wireshark_launch_blocked.pack(anchor="w", pady=(8, 0))
    app.add_tooltip(
        app.cb_wireshark_launch_blocked,
        app.tr(
            "settings_wireshark_launch_blocked_tooltip",
            "Blocks only Wireshark launches from NetMon. Direct launch via system menu or terminal remains possible.",
        ),
    )
    for key, fallback in (
        (
            "settings_wireshark_launch_blocked_note",
            "Note: this option only blocks Wireshark launches from NetMon and is not a real system-wide lock.",
        ),
        (
            "settings_wireshark_launch_blocked_system_hint",
            "Disable system-wide: e.g. uninstall Wireshark, remove the desktop launcher, or revoke user/group permissions for wireshark and dumpcap.",
        ),
    ):
        ttk.Label(
            security,
            text=app.tr(key, fallback),
            justify="left",
            wraplength=620,
        ).pack(anchor="w", pady=(4, 0))


def build_settings_privacy(app, general_tab) -> None:
    """Build ISP stealth mode controls and related VPN selection."""
    privacy = ttk.LabelFrame(
        general_tab,
        text=app.tr("privacy_group_stealth", "ISP-Stealthmodus"),
        padding=10,
    )
    privacy.pack(fill="x", pady=(0, 10))
    ttk.Label(
        privacy,
        text=app.tr("privacy_intro_text", "Manage the full ISP stealth mode here."),
        justify="left",
    ).pack(anchor="w", pady=(0, 8))
    for key, fallback, variable, padding in (
        (
            "privacy_check_enabled",
            "Stealth mode enabled",
            app.isp_stealth_enabled,
            None,
        ),
        (
            "privacy_check_autostart",
            "Start automatically with NetMon",
            app.isp_stealth_autostart,
            (4, 0),
        ),
        (
            "privacy_check_killswitch",
            "Enable killswitch",
            app.isp_stealth_enable_killswitch,
            (4, 0),
        ),
        (
            "privacy_check_strict",
            "Enable strict protection",
            app.strict_protection_var,
            (4, 0),
        ),
    ):
        check = ttk.Checkbutton(
            privacy,
            text=app.tr(key, fallback),
            variable=variable,
            command=app.save_privacy_config,
        )
        if padding is None:
            check.pack(anchor="w")
        else:
            check.pack(anchor="w", pady=padding)
    app.cb_privacy_ipv6 = ttk.Checkbutton(
        privacy,
        text=app.tr("privacy_check_disable_ipv6", "Disable IPv6"),
        variable=app.isp_stealth_disable_ipv6,
        command=app.save_privacy_config,
    )
    app.cb_privacy_ipv6.pack(anchor="w", pady=(4, 0))
    app.add_tooltip(
        app.cb_privacy_ipv6,
        "This option is only available if the active or selected VPN profile supports IPv6.",
    )
    app.privacy_ipv6_hint = ttk.Label(
        privacy, text="", foreground="#666666", wraplength=240, justify="left"
    )
    app.privacy_ipv6_hint.pack(anchor="w")
    app.cb_privacy_ipv6.pack_forget()
    app.privacy_ipv6_hint.pack_forget()
    vpn_frame = ttk.Frame(privacy)
    vpn_frame.pack(fill="x", pady=(8, 0))
    ttk.Label(vpn_frame, text=app.tr("privacy_label_vpn_profile", "VPN profile:")).pack(
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
        "<<ComboboxSelected>>", lambda _event: app.on_privacy_vpn_selected()
    )
    ttk.Label(
        privacy,
        text=app.tr(
            "privacy_dns_profile_vpn_managed_hint",
            "Um vor DNS-Leaks zu schützen,\n"
            "wird das DNS-Profil vom gewählten VPN-Profil verwaltet.",
        ),
        justify="left",
        wraplength=620,
    ).pack(anchor="w", pady=(2, 0))
    actions = ttk.Frame(privacy)
    actions.pack(fill="x", pady=(12, 0))
    ttk.Button(
        actions,
        text=app.tr("privacy_btn_on", "Stealth mode ON"),
        command=app.isp_stealth_on,
    ).pack(side="left")
    ttk.Button(
        actions,
        text=app.tr("privacy_btn_off", "Stealth mode OFF"),
        command=app.isp_stealth_off,
    ).pack(side="left", padx=(8, 0))
