"""DNS tab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.config.constants import DNS_MODE_LABELS
except ModuleNotFoundError:
    from config.constants import DNS_MODE_LABELS


def build_dns_tab(app):
    app.tab_dns = ttk.Frame(app.nb, padding=10)
    app.nb.add(app.tab_dns, text=app.tr("tab_dns", "DNS"))

    # UI Cleanup inventory (DNS):
    # Standard: DNS Status aktualisieren -> resolved_status_async
    # Standard: DNS Leak Check -> run_dns_leak_check
    # Standard: DNS Guard aktivieren -> save_privacy_config
    # Expert: DNS reparieren -> apply_vpn_dns_policy_async
    # Expert: DoT AN/AUS/Test/Status -> enable/disable/test/show_dot_status_async
    # Expert: DNSSEC prüfen -> run_dnssec_check
    # Expert: DNS Health Check -> run_dns_health_check
    # Expert: DNS Repair Rollback -> dns_repair_rollback_async
    # Expert: DoT Leak-Konflikt beheben -> fix_dot_leak_conflict_async
    dns_standard_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_standard", "DNS Standard"),
        padding=6,
    )
    dns_standard_frame.pack(fill="x", pady=(0, 8))
    dns_standard_row1 = ttk.Frame(dns_standard_frame)
    dns_standard_row1.pack(fill="x")
    dns_standard_row2 = ttk.Frame(dns_standard_frame)
    dns_standard_row2.pack(fill="x", pady=(6, 0))
    ttk.Button(
        dns_standard_row1,
        text=app.tr("dns_btn_refresh_status", "DNS Status aktualisieren"),
        command=app.resolved_status_async,
    ).pack(side="left")
    ttk.Button(
        dns_standard_row1,
        text=app.tr("dns_btn_leak_check", "DNS Leak Check"),
        command=app.run_dns_leak_check,
    ).pack(side="left", padx=(8, 0))
    ttk.Button(
        dns_standard_row1,
        text=app.tr("dns_btn_clear_output", "DNS-Ausgabe leeren"),
        command=app.clear_dns_output,
    ).pack(side="right")
    ttk.Checkbutton(
        dns_standard_row2,
        text=app.tr("dns_check_enable_guard", "DNS Guard aktivieren"),
        variable=app.dns_guard_enabled_var,
        command=app.save_privacy_config,
    ).pack(side="left")
    ttk.Button(
        dns_standard_row2,
        text=app.tr("btn_analyze_with_chad", "Analyse mit Chad"),
        command=lambda: app.prepare_chad_analysis(
            "DNS Analyse",
            app.dns_text.get("1.0", "end").strip(),
        ),
    ).pack(side="left", padx=(8, 0))

    dns_policy_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_control", "DNS Control"),
        padding=6,
    )
    dns_policy_frame.pack(fill="x", pady=(0, 8))

    dns_policy_top = ttk.Frame(dns_policy_frame)
    dns_policy_top.pack(fill="x")
    ttk.Label(
        dns_policy_top,
        text=app.tr("dns_label_mode", "DNS Modus:"),
    ).pack(side="left")
    app.dns_mode_combo = ttk.Combobox(
        dns_policy_top,
        textvariable=app.dns_mode_var,
        values=list(DNS_MODE_LABELS.values()),
        state="readonly",
        width=24,
    )
    app.dns_mode_combo.pack(side="left", padx=(8, 8))
    app.dns_mode_combo.bind(
        "<<ComboboxSelected>>",
        lambda _event: app.on_dns_mode_selected(),
    )
    ttk.Button(
        dns_policy_top,
        text=app.tr("dns_btn_evaluate_status", "DNS Status bewerten"),
        command=app.fix_dns_conflicts_async,
    ).pack(side="left")
    btn_dns_repair = ttk.Button(
        dns_policy_top,
        text=app.tr("dns_btn_repair", "DNS reparieren"),
        command=app.apply_vpn_dns_policy_async,
    )
    btn_dns_repair.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_dns_repair,
        "Behebt DNS-Konflikte und stellt sicher,\n"
        "dass nur der korrekte DNS (z.B. VPN-DNS) aktiv ist.",
    )

    dns_guard_row = ttk.Frame(dns_policy_frame)
    dns_guard_row.pack(fill="x", pady=(6, 0))
    ttk.Label(
        dns_guard_row,
        text=app.tr("dns_label_guard_status", "Guard-Status:"),
    ).pack(side="left")

    ttk.Label(
        dns_policy_frame,
        textvariable=app.dns_mode_status_var,
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
        text=app.tr("dns_group_expert", "DNS Experten / Wartung"),
        padding=6,
    )
    dns_expert_frame.pack(fill="x", pady=(0, 8))
    dns_expert_row1 = ttk.Frame(dns_expert_frame)
    dns_expert_row1.pack(fill="x")
    dns_expert_row2 = ttk.Frame(dns_expert_frame)
    dns_expert_row2.pack(fill="x", pady=(6, 0))

    btn_dnssec = ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_dnssec_check", "DNSSEC prüfen"),
        command=app.run_dnssec_check,
    )
    btn_dnssec.pack(side="left")
    app.register_feature_button("dns_consistency", btn_dnssec)

    ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_health_check", "DNS Health Check"),
        command=app.run_dns_health_check,
    ).pack(side="left", padx=(8, 0))

    btn_dns_repair = ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_repair", "DNS reparieren"),
        command=app.apply_vpn_dns_policy_async,
    )
    btn_dns_repair.pack(side="left", padx=(8, 0))
    app.add_tooltip(
        btn_dns_repair,
        "Behebt DNS-Konflikte und stellt sicher,\n"
        "dass nur der korrekte DNS (z.B. VPN-DNS) aktiv ist.",
    )

    ttk.Button(
        dns_expert_row1,
        text=app.tr("dns_btn_repair_rollback", "DNS Repair Rollback"),
        command=app.dns_repair_rollback_async,
    ).pack(side="left", padx=(8, 0))

    app.btn_dot_on = ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_dot_on", "DoT AN"),
        command=app.enable_dot_async,
    )
    app.btn_dot_on.pack(side="left")
    app.register_feature_button("dot", app.btn_dot_on)
    app.add_tooltip(
        app.btn_dot_on,
        "Aktiviert DNS over TLS über eine NetMon-Drop-in-Datei für systemd-resolved. "
        "Bei aktivem VPN ist diese Aktion gesperrt.",
    )

    app.btn_dot_off = ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_dot_off", "DoT AUS"),
        command=app.disable_dot_async,
    )
    app.btn_dot_off.pack(side="left", padx=(8, 0))
    app.register_feature_button("dot", app.btn_dot_off)
    app.add_tooltip(
        app.btn_dot_off,
        "Entfernt die NetMon-DoT-Konfiguration wieder aus systemd-resolved.",
    )

    btn_dot_test = ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_dot_test", "DoT testen"),
        command=app.test_dot_async,
    )
    btn_dot_test.pack(side="left", padx=(8, 0))
    app.register_feature_button("dot", btn_dot_test)
    app.add_tooltip(
        btn_dot_test,
        "Prüft Konfiguration, Resolver-Antwort und optional eine TLS-Verbindung auf Port 853.",
    )

    btn_dot_status = ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_dot_status", "DoT Status"),
        command=app.show_dot_status_async,
    )
    btn_dot_status.pack(side="left", padx=(8, 0))
    app.register_feature_button("dot", btn_dot_status)
    app.add_tooltip(
        btn_dot_status,
        "Zeigt den aktuellen DoT-Status im DNS-Tab an.",
    )

    ttk.Button(
        dns_expert_row2,
        text=app.tr("dns_btn_fix_dot_leak", "DoT Leak-Konflikt beheben"),
        command=app.fix_dot_leak_conflict_async,
    ).pack(side="left", padx=(8, 0))

    dot_status_frame = ttk.LabelFrame(
        app.tab_dns,
        text=app.tr("dns_group_dot", "DNS over TLS"),
        padding=6,
    )
    dot_status_frame.pack(fill="x", pady=(0, 8))
    ttk.Label(dot_status_frame, textvariable=app.dot_status_var).pack(anchor="w")
    ttk.Label(dot_status_frame, textvariable=app.dot_profile_var).pack(anchor="w")
    ttk.Label(dot_status_frame, textvariable=app.dot_server_var).pack(anchor="w")
    ttk.Label(dot_status_frame, textvariable=app.dot_mode_var).pack(anchor="w")
    ttk.Label(dot_status_frame, textvariable=app.dot_last_test_var).pack(anchor="w")

    app.dns_text = tk.Text(app.tab_dns, wrap="word")
    app.dns_text.pack(fill="both", expand=True)
    app.attach_chad_context_menu(app.dns_text, "DNS Analyse")
