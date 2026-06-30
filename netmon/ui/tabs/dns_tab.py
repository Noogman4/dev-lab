"""DNS tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def _app_value(app, name: str, default=None):
    return app.__dict__.get(name, default)


def _text_widget_value(widget) -> str:
    if widget is None:
        return ""
    try:
        return str(widget.get("1.0", "end").strip())
    except Exception:
        return ""


def build_dns_tab(app):
    app.tab_dns = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_dns, text=app.tr("tab_dns", "DNS"))

    # UI Cleanup inventory (DNS):
    # Expert: DNS reparieren -> apply_vpn_dns_policy_async
    # Expert: DoT AN/AUS/Test/Status -> enable/disable/test/show_dot_status_async
    # Expert: DNSSEC prüfen -> run_dnssec_check
    # Expert: DNS Health Check -> run_dns_health_check
    # Expert: DNS Repair Rollback -> dns_repair_rollback_async
    # Expert: DoT Leak-Konflikt beheben -> fix_dot_leak_conflict_async
    dns_policy_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_control", "DNS Control"),
        padding=6,
    )
    dns_policy_frame.pack(fill="x", pady=(0, 8))
    ttk.Checkbutton(
        dns_policy_frame,
        text=app.tr("dns_check_enable_guard", "Enable DNS Guard"),
        variable=app.dns_guard_enabled_var,
        command=app.save_privacy_config,
    ).pack(anchor="w", pady=(6, 0))

    dns_guard_row = ttk.Frame(dns_policy_frame)
    dns_guard_row.pack(fill="x", pady=(6, 0))
    ttk.Label(
        dns_guard_row,
        text=app.tr("dns_label_guard_status", "Guard status:"),
    ).pack(side="left")

    ttk.Label(
        dns_policy_frame,
        text=app.tr("dns_rule_status", "DNS rule: prefer VPN DNS"),
    ).pack(anchor="w", pady=(6, 0))
    ttk.Label(
        dns_policy_frame,
        textvariable=app.dns_resolver_status_var,
    ).pack(anchor="w")
    ttk.Label(
        dns_policy_frame,
        textvariable=app.dns_conflict_status_var,
    ).pack(anchor="w")
    ttk.Label(
        dns_policy_frame,
        textvariable=app.dns_guard_status_var,
    ).pack(anchor="w")
    ttk.Label(
        dns_policy_frame,
        textvariable=app.dns_guard_last_action_var,
    ).pack(anchor="w")

    dns_expert_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_expert", "DNS expert / maintenance"),
        padding=6,
    )
    dns_expert_frame.pack(fill="x", pady=(0, 8))
    dns_expert_row1 = ttk.Frame(dns_expert_frame)
    dns_expert_row1.pack(fill="x")
    dns_expert_row2 = ttk.Frame(dns_expert_frame)
    dns_expert_row2.pack(fill="x", pady=(6, 0))
    for row in (dns_expert_row1, dns_expert_row2):
        for col in range(3):
            row.columnconfigure(col, weight=1, uniform="dns_expert")

    app.btn_dns_status_refresh = ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_refresh_status", "DNS Status aktualisieren"),
        command=app.resolved_status_async,
    )
    app.btn_dns_status_refresh.grid(row=0, column=0, sticky="ew", padx=(0, 4))

    btn_dnssec = ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_dnssec_check", "Check DNSSEC"),
        command=app.run_dnssec_check,
    )
    btn_dnssec.grid(row=0, column=1, sticky="ew", padx=4)
    app.register_feature_button("dns_consistency", btn_dnssec)

    ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_health_check", "DNS Health Check"),
        command=app.run_dns_health_check,
    ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

    ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_leak_check", "DNS Leak Check"),
        command=app.run_dns_leak_check,
    ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

    app.btn_dns_repair = ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_repair", "Repair DNS"),
        command=app.apply_vpn_dns_policy_async,
    )
    app.btn_dns_repair.grid(row=0, column=1, sticky="ew", padx=4)
    app.add_tooltip(
        app.btn_dns_repair,
        app.tr(
            "dns_tooltip_repair",
            "Fixes DNS conflicts and ensures\n"
            "that only the correct DNS (for example VPN DNS) is active.",
        ),
    )

    ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_repair_rollback", "DNS Repair Rollback"),
        command=app.dns_repair_rollback_async,
    ).grid(row=0, column=2, sticky="ew", padx=(4, 0))

    dot_status_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_dot", "DNS over TLS"),
        padding=6,
    )
    dot_status_frame.pack(fill="x", pady=(0, 8))
    dot_status_frame.columnconfigure(0, weight=1)
    dot_status_frame.columnconfigure(1, weight=0)

    dot_info_frame = ttk.Frame(dot_status_frame)
    dot_info_frame.grid(row=0, column=0, sticky="nw")

    dot_button_frame = ttk.Frame(dot_status_frame)
    dot_button_frame.grid(row=0, column=1, sticky="ne", padx=(12, 0))
    dot_button_frame.columnconfigure(0, weight=1, uniform="dot")
    dot_button_frame.columnconfigure(1, weight=1, uniform="dot")

    ttk.Label(dot_info_frame, textvariable=app.dot_status_var).pack(anchor="w")
    ttk.Label(dot_info_frame, textvariable=app.dot_profile_var).pack(anchor="w")
    ttk.Label(dot_info_frame, textvariable=app.dot_server_var).pack(anchor="w")
    ttk.Label(dot_info_frame, textvariable=app.dot_mode_var).pack(anchor="w")
    ttk.Label(dot_info_frame, textvariable=app.dot_last_test_var).pack(anchor="w")

    app.btn_dot_on = ttk.Button(
        dot_button_frame,
        text=app.tr("dns_btn_dot_on", "DoT ON"),
        command=app.enable_dot_async,
    )
    app.btn_dot_on.grid(row=0, column=0, sticky="ew", padx=2, pady=2)
    app.register_feature_button("dot", app.btn_dot_on)
    app.add_tooltip(
        app.btn_dot_on,
        app.tr(
            "dns_tooltip_dot_on",
            "Enables DNS over TLS through a NetMon drop-in file for systemd-resolved. "
            "This action is blocked while a VPN is active.",
        ),
    )

    app.btn_dot_off = ttk.Button(
        dot_button_frame,
        text=app.tr("dns_btn_dot_off", "DoT OFF"),
        command=app.disable_dot_async,
    )
    app.btn_dot_off.grid(row=0, column=1, sticky="ew", padx=2, pady=2)
    app.register_feature_button("dot", app.btn_dot_off)
    app.add_tooltip(
        app.btn_dot_off,
        app.tr(
            "dns_tooltip_dot_off",
            "Removes the NetMon DoT configuration from systemd-resolved again.",
        ),
    )

    app.btn_dot_test = ttk.Button(
        dot_button_frame,
        text=app.tr("dns_btn_dot_test", "Test DoT"),
        command=app.test_dot_async,
    )
    app.btn_dot_test.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
    app.register_feature_button("dot", app.btn_dot_test)
    app.add_tooltip(
        app.btn_dot_test,
        app.tr(
            "dns_tooltip_dot_test",
            "Checks the configuration, resolver response, and optionally a TLS connection on port 853.",
        ),
    )

    btn_dot_status = ttk.Button(
        dot_button_frame,
        text=app.tr("dns_btn_dot_status", "DoT status"),
        command=app.show_dot_status_async,
    )
    btn_dot_status.grid(row=1, column=1, sticky="ew", padx=2, pady=2)
    app.register_feature_button("dot", btn_dot_status)
    app.add_tooltip(
        btn_dot_status,
        app.tr(
            "dns_tooltip_dot_status",
            "Shows the current DoT status in the DNS tab.",
        ),
    )

    btn_dot_fix = ttk.Button(
        dot_button_frame,
        text=app.tr("dns_btn_fix_dot_leak", "Fix DoT leak conflict"),
        command=app.fix_dot_leak_conflict_async,
    )
    btn_dot_fix.grid(
        row=2,
        column=0,
        columnspan=2,
        sticky="ew",
        padx=2,
        pady=2,
    )
    app.add_tooltip(
        btn_dot_fix,
        app.tr(
            "dns_tooltip_dot_fix",
            "Resolves a conflict between global NetMon DoT and active VPN DNS.",
        ),
    )

    manual_dns_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_manual", "Manual DNS"),
        padding=6,
    )
    manual_dns_frame.pack(fill="x", pady=(0, 8))

    ttk.Label(
        manual_dns_frame,
        text=app.tr("dns_label_manual_entry", "Enter DNS server manually:"),
    ).pack(anchor="w")

    manual_dns_row = ttk.Frame(manual_dns_frame)
    manual_dns_row.pack(anchor="w", pady=(4, 0))

    app.manual_dns_entry = ttk.Entry(
        manual_dns_row,
        textvariable=app.manual_dns_entry_var,
        width=42,
    )
    app.manual_dns_entry.pack(side="left")
    app.attach_text_context_menu(app.manual_dns_entry)

    ttk.Button(
        manual_dns_row,
        text=app.tr("dns_btn_add_manual", "Add to selection"),
        command=app.add_manual_dns_server,
    ).pack(side="left", padx=(8, 0))

    app.btn_dns_manage_profiles = ttk.Button(
        manual_dns_row,
        text=app.tr("dns_btn_manage_profiles", "Manage DNS..."),
        command=app.open_dns_profile_manager,
    )
    app.btn_dns_manage_profiles.pack(side="left", padx=(8, 0))

    dns_output_actions = ttk.Frame(app.tab_dns)
    dns_output_actions.pack(fill="x", pady=(0, 6))
    app.btn_dns_analyze_with_chad = ttk.Button(
        dns_output_actions,
        text=app.tr("btn_analyze_with_chad", "Analyze with Chad"),
        command=lambda: app.prepare_chad_analysis(
            "DNS analysis",
            _text_widget_value(_app_value(app, "dns_text")),
        ),
    )
    app.btn_dns_analyze_with_chad.pack(side="left")
    ttk.Button(
        dns_output_actions,
        text=app.tr("dns_btn_clear_output", "Clear DNS output"),
        command=app.clear_dns_output,
    ).pack(side="right")

    app.dns_text = tk.Text(app.tab_dns, wrap="word")
    app.dns_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.dns_text, "DNS analysis")
