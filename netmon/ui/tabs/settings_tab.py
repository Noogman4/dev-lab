"""Settings tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
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


def build_settings_tours(app, tours_tab) -> None:
    """Build guided-tour controls and launchers."""
    tours_group = ttk.LabelFrame(
        tours_tab,
        text=app.tr("tours_group_title", "Guided tours"),
        padding=10,
    )
    tours_group.pack(fill="x", pady=(0, 10))
    ttk.Label(
        tours_group,
        text=app.tr(
            "tours_group_intro",
            "Starts guided introductions for major areas and individual tabs. "
            "Completed tours are marked and can be opened again at any time.",
        ),
        justify="left",
        wraplength=620,
    ).pack(anchor="w")
    for key, fallback, variable, command, padding in (
        (
            "tours_offer_on_startup",
            "Offer quick-start tour on startup",
            app.var_guided_tour_offer_on_startup,
            app.on_guided_tour_offer_toggle,
            (8, 0),
        ),
        (
            "tours_default_full_on_startup",
            "Preselect the full tour by default in the startup dialog",
            app.var_guided_tour_full_on_startup,
            app.on_guided_tour_startup_mode_toggle,
            (6, 0),
        ),
    ):
        ttk.Checkbutton(
            tours_group,
            text=app.tr(key, fallback),
            variable=variable,
            command=command,
        ).pack(anchor="w", pady=padding)
    ttk.Button(
        tours_group,
        text=app.tr("tours_reset_progress", "Reset tour progress"),
        command=app.reset_guided_tour_progress,
    ).pack(anchor="w", pady=(8, 0))
    ttk.Label(
        tours_group,
        textvariable=app.guided_tour_status_var,
        justify="left",
        wraplength=620,
    ).pack(anchor="w", pady=(8, 0))

    tours_grid = ttk.Frame(tours_group)
    tours_grid.pack(fill="x", pady=(10, 0))
    tours_grid.columnconfigure(0, weight=1)
    tours_grid.columnconfigure(1, weight=1)
    launcher_columns = [ttk.Frame(tours_grid), ttk.Frame(tours_grid)]
    launcher_columns[0].grid(row=0, column=0, sticky="nw", padx=(0, 8))
    launcher_columns[1].grid(row=0, column=1, sticky="nw", padx=(8, 0))
    launcher_specs = app._guided_tour_launcher_specs()
    split_index = (len(launcher_specs) + 1) // 2
    app.guided_tour_launcher_buttons = {}
    for index, (group_title, tours) in enumerate(launcher_specs):
        column = launcher_columns[0] if index < split_index else launcher_columns[1]
        section = ttk.LabelFrame(column, text=group_title, padding=8)
        section.pack(fill="x", pady=(0, 8))
        for tour_name, base_label in tours:
            row = ttk.Frame(section)
            row.pack(fill="x", pady=(0, 6))
            row.columnconfigure(1, weight=1)
            status_label = ttk.Label(
                row,
                text=app._guided_tour_status_symbol(tour_name),
                width=4,
                anchor="w",
            )
            status_label.grid(row=0, column=0, sticky="w")
            title_label = ttk.Label(row, text=base_label, anchor="w")
            title_label.grid(row=0, column=1, sticky="ew", padx=(4, 10))
            button = ttk.Button(
                row,
                text=app.tr("guided_tour_btn_start_short", "Start"),
                width=8,
                command=lambda name=tour_name: app.start_guided_tour(name),
            )
            button.grid(row=0, column=2, sticky="e")
            app._register_guided_tour_launcher_button(
                tour_name,
                button,
                base_label,
                title_widget=title_label,
                status_widget=status_label,
            )
            if tour_name == "full-tour":
                app.btn_full_tour = button
            elif tour_name == "quickstart":
                app.btn_quickstart_tour = button
            elif tour_name == "dns":
                app.btn_dns_tour = button
            elif tour_name == "security":
                app.btn_security_tour = button
            elif tour_name == "download-scan":
                app.btn_download_scan_tour = button
            elif tour_name == "radio":
                app.btn_radio_tour = button
    app.refresh_guided_tour_status()


def build_settings_support(app, support_tab) -> None:
    """Build support package actions and the optional support form."""
    support_group = ttk.LabelFrame(
        support_tab,
        text=app.tr("support_group_title", "Support / diagnostics"),
        padding=10,
    )
    support_group.pack(fill="x", pady=(0, 10))
    for key, fallback, padding in (
        (
            "support_intro_text",
            "Creates a support package with the current diagnostic reports and basic "
            "technical information under Documents/NetMon/support.",
            None,
        ),
        (
            "support_recommendation_text",
            "Empfehlung: Paket erzeugen, kurz den Inhalt im Supportordner prüfen und die "
            "ZIP-Datei anschließend manuell an den Support oder den eigenen Mail-Client anhängen.",
            (6, 0),
        ),
    ):
        label = ttk.Label(
            support_group,
            text=app.tr(key, fallback),
            justify="left",
            wraplength=620,
        )
        if padding is None:
            label.pack(anchor="w")
        else:
            label.pack(anchor="w", pady=padding)
    privacy_box = tk.Frame(
        support_group,
        bg="#6b4b00",
        bd=1,
        relief="solid",
        padx=10,
        pady=10,
    )
    privacy_box.pack(fill="x", pady=(10, 0))
    tk.Label(
        privacy_box,
        text=app.tr("support_privacy_box_title", "⚠ Datenschutzhinweis"),
        bg="#6b4b00",
        fg="#fff4d6",
        font=("TkDefaultFont", 10, "bold"),
        justify="left",
        anchor="w",
    ).pack(anchor="w")
    for key, fallback in (
        (
            "support_privacy_line_1",
            "Das Diagnosepaket wird ausschließlich zur Analyse gemeldeter Fehler und zur "
            "Verbesserung von NetMon Roots verwendet.",
        ),
        (
            "support_privacy_line_2",
            "Die übermittelten Daten werden nicht an Dritte weitergegeben und nicht für "
            "Werbezwecke oder Nutzerprofile verwendet.",
        ),
        (
            "support_privacy_line_3",
            "Diagnoseprotokolle können je nach Fehlerfall systembezogene Informationen wie "
            "Hostname, Benutzernamen, Dateipfade oder IP-Adressen enthalten.",
        ),
        (
            "support_privacy_line_4",
            "Bitte prüfen Sie das Paket vor dem Versand, wenn Sie bestimmte Informationen "
            "nicht weitergeben möchten.",
        ),
        (
            "support_privacy_line_5",
            "Eingesandte Diagnosepakete werden ausschließlich zur Bearbeitung Ihrer "
            "Supportanfrage verwendet und anschließend gelöscht.",
        ),
    ):
        tk.Label(
            privacy_box,
            text=app.tr(key, fallback),
            bg="#6b4b00",
            fg="#fff4d6",
            justify="left",
            wraplength=600,
            anchor="w",
        ).pack(anchor="w", pady=(6, 0))

    support_buttons = ttk.Frame(support_group)
    support_buttons.pack(fill="x", pady=(8, 0))
    for column in range(4):
        support_buttons.columnconfigure(column, weight=1)
    app.btn_create_support_package = ttk.Button(
        support_buttons,
        text=app.tr("support_btn_create_package", "Supportpaket erzeugen"),
        command=app.create_support_package,
    )
    app.btn_create_support_package.grid(row=0, column=0, sticky="ew", padx=(0, 8))
    for column, key, fallback, command, padding in (
        (
            1,
            "support_btn_open_package",
            "Supportpaket öffnen",
            app.open_latest_support_package,
            4,
        ),
        (
            2,
            "support_btn_open_folder",
            "Supportordner öffnen",
            app.open_support_packages_folder,
            4,
        ),
        (
            3,
            "support_btn_copy_path",
            "Copy path",
            app.copy_latest_support_package_path,
            (4, 0),
        ),
    ):
        ttk.Button(
            support_buttons,
            text=app.tr(key, fallback),
            command=command,
        ).grid(row=0, column=column, sticky="ew", padx=padding)

    placeholders = app._support_form_placeholders()
    contact_name_var = tk.StringVar(value=placeholders["contact_name"])
    contact_email_var = tk.StringVar(value=placeholders["contact_email"])
    last_step_var = tk.StringVar(value=placeholders["last_step"])
    repro_var = tk.StringVar(value=placeholders["repro"])
    support_form = ttk.LabelFrame(
        support_group,
        text=app.tr("support_group_form", "Supportformular"),
        padding=8,
    )
    support_form.pack(fill="x", pady=(10, 0))
    support_form.columnconfigure(1, weight=1)
    ttk.Label(
        support_form,
        text=app.tr(
            "support_form_intro_text",
            "Optional: briefly describe the error and export it together with the support package.",
        ),
        justify="left",
        wraplength=620,
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
    for row, key, fallback, variable in (
        (1, "support_label_name_short", "Name / short tag", contact_name_var),
        (2, "support_label_email", "Email", contact_email_var),
        (3, "support_label_last_step", "Last step", last_step_var),
        (4, "support_label_reproducibility", "Reproducibility", repro_var),
    ):
        ttk.Label(support_form, text=app.tr(key, fallback)).grid(
            row=row, column=0, sticky="w", pady=(0, 6)
        )
        ttk.Entry(support_form, textvariable=variable).grid(
            row=row, column=1, sticky="ew", pady=(0, 6)
        )
    ttk.Label(
        support_form,
        text=app.tr("support_label_error_description", "Error description"),
    ).grid(row=5, column=0, sticky="nw", pady=(0, 6))
    details_wrap = ttk.Frame(support_form)
    details_wrap.grid(row=5, column=1, sticky="nsew", pady=(0, 6))
    details_wrap.columnconfigure(0, weight=1)
    details_wrap.rowconfigure(0, weight=1)
    details_text = tk.Text(details_wrap, height=11, wrap="word")
    app.settings_support_details_text = details_text
    details_scrollbar = ttk.Scrollbar(
        details_wrap, orient="vertical", command=details_text.yview
    )
    details_text.configure(yscrollcommand=details_scrollbar.set)
    details_text.grid(row=0, column=0, sticky="nsew")
    details_scrollbar.grid(row=0, column=1, sticky="ns")
    details_text.insert("1.0", placeholders["details"])

    def create_package_with_form() -> object:
        metadata = app._build_about_support_form_metadata(
            contact_name=contact_name_var.get(),
            contact_email=contact_email_var.get(),
            last_step=last_step_var.get(),
            repro_status=repro_var.get(),
            details=details_text.get("1.0", "end-1c"),
        )
        return app.create_support_package(extra_metadata=metadata)

    ttk.Button(
        support_form,
        text=app.tr(
            "support_btn_create_package_with_form",
            "Supportpaket mit Formular erzeugen",
        ),
        command=create_package_with_form,
    ).grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))


def build_settings_maintenance(app, general_tab) -> None:
    """Build system restart, reset, and maintenance actions."""
    system = ttk.LabelFrame(
        general_tab,
        text=app.tr("settings_group_system", "System"),
        padding=10,
    )
    system.pack(fill="x", pady=(0, 10))
    for key, fallback, command, padding in (
        (
            "settings_restart_netmon_only",
            "Restart NetMon",
            app.restart_netmon_only,
            None,
        ),
        (
            "settings_restart_netmon_with_reset",
            "Restart NetMon with network reset",
            app.restart_netmon_with_network_reset,
            (6, 0),
        ),
        (
            "settings_reset_network_stack",
            "Reset network stack",
            app.reset_network_stack,
            (6, 0),
        ),
        (
            "settings_emergency_stop_radio",
            "Radio emergency stop",
            app.emergency_stop_radio_mpv,
            (6, 0),
        ),
    ):
        button = ttk.Button(system, text=app.tr(key, fallback), command=command)
        if padding is None:
            button.pack(anchor="w")
        else:
            button.pack(anchor="w", pady=padding)
    maintenance = ttk.LabelFrame(
        system,
        text=app.tr("maintenance_group_system_updates", "System & updates"),
        padding=8,
    )
    maintenance.pack(fill="x", pady=(10, 0))
    buttons = ttk.Frame(maintenance)
    buttons.pack(anchor="w")
    for row, column, key, fallback, command, grid_options in (
        (
            0,
            0,
            "maintenance_btn_apt_update",
            "Update package lists",
            app.run_apt_update_in_terminal,
            {},
        ),
        (
            0,
            1,
            "maintenance_btn_apt_upgrade",
            "Upgrade system",
            app.run_apt_upgrade_in_terminal,
            {"padx": (8, 0)},
        ),
        (
            1,
            0,
            "maintenance_btn_apt_autoremove",
            "Remove unused packages",
            app.run_apt_autoremove_in_terminal,
            {"pady": (8, 0)},
        ),
        (
            1,
            1,
            "maintenance_btn_apt_clean",
            "Clean APT cache",
            app.run_apt_clean_in_terminal,
            {"padx": (8, 0), "pady": (8, 0)},
        ),
        (
            2,
            0,
            "maintenance_btn_refresh_menu",
            "Refresh menu",
            app.run_menu_refresh_in_terminal,
            {"pady": (8, 0)},
        ),
        (
            2,
            1,
            "maintenance_btn_refresh_menu_icon_cache",
            "Menü + Icon-Cache aktualisieren",
            app.run_menu_and_icon_refresh_in_terminal,
            {"padx": (8, 0), "pady": (8, 0)},
        ),
    ):
        ttk.Button(buttons, text=app.tr(key, fallback), command=command).grid(
            row=row, column=column, sticky="w", **grid_options
        )
