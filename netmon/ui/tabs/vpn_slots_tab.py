"""VPN slots subtab builder for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

try:
    from netmon.config.constants import VPN_SLOT_COUNT
except ModuleNotFoundError:
    from config.constants import VPN_SLOT_COUNT


def build_vpn_slots_tab(app):
    app.tab_vpn_slots = ttk.Frame(app.system_nb, padding=10)
    app.system_nb.add(
        app.tab_vpn_slots,
        text=app.tr("system_tab_vpn_slots", "VPN Slots"),
    )

    vpn_manage = ttk.LabelFrame(
        app.tab_vpn_slots,
        text=app.tr("vpn_slots_group_manage", "VPN-Slot Verwaltung"),
        padding=8,
    )
    vpn_manage.pack(fill="x", pady=(0, 8))

    vpn_form = ttk.Frame(vpn_manage)
    vpn_form.pack(fill="x")
    for col, weight in [
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 1),
        (4, 0),
        (5, 1),
        (6, 0),
        (7, 0),
        (8, 0),
    ]:
        vpn_form.columnconfigure(col, weight=weight)

    app.vpn_slot_choice = tk.StringVar(value="1")
    ttk.Label(vpn_form, text=app.tr("label_slot", "Slot:")).grid(
        row=0, column=0, sticky="w"
    )
    app.vpn_slot_combo = ttk.Combobox(
        vpn_form,
        textvariable=app.vpn_slot_choice,
        values=[str(i) for i in range(1, VPN_SLOT_COUNT + 1)],
        state="readonly",
        width=4,
    )
    app.vpn_slot_combo.grid(row=0, column=1, sticky="w", padx=(4, 10))
    app.vpn_slot_combo.bind("<<ComboboxSelected>>", app.on_vpn_slot_select)

    ttk.Label(
        vpn_form,
        text=app.tr("label_display_name", "Anzeigename:"),
    ).grid(row=0, column=2, sticky="w")
    app.vpn_custom_name_var = tk.StringVar(value="")
    app.vpn_custom_name_entry = ttk.Entry(
        vpn_form,
        textvariable=app.vpn_custom_name_var,
    )
    app.vpn_custom_name_entry.grid(row=0, column=3, sticky="ew", padx=(4, 10))

    ttk.Label(vpn_form, text=app.tr("label_profile", "Profil:")).grid(
        row=0, column=4, sticky="w"
    )
    app.vpn_profile_var = tk.StringVar(value="")
    app.vpn_profile_combo = ttk.Combobox(
        vpn_form,
        textvariable=app.vpn_profile_var,
        values=app.wg_profiles,
        state="normal",
    )
    app.vpn_profile_combo.grid(row=0, column=5, sticky="ew", padx=(4, 10))

    btn_vpn_apply = ttk.Button(
        vpn_form,
        text=app.tr("btn_apply_assignment", "Zuordnung übernehmen"),
        command=app.assign_vpn_slot,
    )
    btn_vpn_apply.grid(row=0, column=6, sticky="e")
    app.register_feature_button("wg", btn_vpn_apply)
    app.add_tooltip(
        btn_vpn_apply,
        "Speichert die VPN-Zuordnung fuer den gewaehlten Slot.",
    )

    btn_vpn_clear = ttk.Button(
        vpn_form,
        text=app.tr("btn_clear_assignment", "Zuordnung aufheben"),
        command=lambda: app.clear_vpn_slot(confirm=True),
    )
    btn_vpn_clear.grid(row=0, column=7, sticky="e", padx=(8, 0))
    app.register_feature_button("wg", btn_vpn_clear)
    app.add_tooltip(
        btn_vpn_clear,
        "Entfernt Profil und Anzeigenamen des gewaehlten VPN-Slots.",
    )

    btn_vpn_test = ttk.Button(
        vpn_form,
        text=app.tr("btn_test", "Testen"),
        command=app.test_vpn_slot,
    )
    btn_vpn_test.grid(row=0, column=8, sticky="e", padx=(8, 0))
    app.register_feature_button("wg", btn_vpn_test)
    app.add_tooltip(
        btn_vpn_test,
        "Startet testweise das aktuell im Formular gewaehlte Profil.",
    )

    btn_vpn_delete = ttk.Button(
        vpn_form,
        text=app.tr("btn_delete_profile", "Profil löschen"),
        command=app.delete_selected_vpn_profile,
    )
    btn_vpn_delete.grid(row=0, column=9, sticky="e", padx=(8, 0))
    app.register_feature_button("wg", btn_vpn_delete)
    app.add_tooltip(
        btn_vpn_delete,
        "Loescht das aktuell im Formular gewaehlte WireGuard-Profil inklusive interner IPv4-Kopie.",
    )

    primary_frame = ttk.LabelFrame(
        vpn_manage,
        text=app.tr("vpn_slots_group_primary", "Standard-VPN links"),
        padding=8,
    )
    primary_frame.pack(fill="x", pady=(10, 8))

    app.primary_vpn_1_name_var = tk.StringVar(
        value=app.primary_vpn_slots[0].get("custom_name", "Proton CH")
    )
    app.primary_vpn_1_profile_var = tk.StringVar(
        value=app.primary_vpn_slots[0].get("profile", "proton")
    )

    ttk.Label(
        primary_frame,
        text=app.tr("vpn_slots_label_primary1_name", "Standard 1 Name:"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Entry(
        primary_frame,
        textvariable=app.primary_vpn_1_name_var,
        width=20,
    ).grid(row=0, column=1, sticky="w", padx=(4, 10))

    ttk.Label(primary_frame, text=app.tr("label_profile", "Profil:")).grid(
        row=0, column=2, sticky="w"
    )
    app.primary_vpn_1_profile_combo = ttk.Combobox(
        primary_frame,
        textvariable=app.primary_vpn_1_profile_var,
        values=app.wg_profiles,
        state="readonly",
        width=18,
    )
    app.primary_vpn_1_profile_combo.grid(row=0, column=3, sticky="w", padx=(4, 10))

    btn_primary_1_apply = ttk.Button(
        primary_frame,
        text=app.tr("btn_apply", "Übernehmen"),
        command=lambda: app.save_primary_vpn_slot(1),
    )
    btn_primary_1_apply.grid(row=0, column=4, sticky="w")

    app.primary_vpn_2_name_var = tk.StringVar(
        value=app.primary_vpn_slots[1].get("custom_name", "Proton DE")
    )
    app.primary_vpn_2_profile_var = tk.StringVar(
        value=app.primary_vpn_slots[1].get("profile", "proton-de")
    )

    ttk.Label(
        primary_frame,
        text=app.tr("vpn_slots_label_primary2_name", "Standard 2 Name:"),
    ).grid(row=1, column=0, sticky="w", pady=(6, 0))
    ttk.Entry(
        primary_frame,
        textvariable=app.primary_vpn_2_name_var,
        width=20,
    ).grid(row=1, column=1, sticky="w", padx=(4, 10), pady=(6, 0))

    ttk.Label(primary_frame, text=app.tr("label_profile", "Profil:")).grid(
        row=1, column=2, sticky="w", pady=(6, 0)
    )
    app.primary_vpn_2_profile_combo = ttk.Combobox(
        primary_frame,
        textvariable=app.primary_vpn_2_profile_var,
        values=app.wg_profiles,
        state="readonly",
        width=18,
    )
    app.primary_vpn_2_profile_combo.grid(
        row=1, column=3, sticky="w", padx=(4, 10), pady=(6, 0)
    )

    btn_primary_2_apply = ttk.Button(
        primary_frame,
        text=app.tr("btn_apply", "Übernehmen"),
        command=lambda: app.save_primary_vpn_slot(2),
    )
    btn_primary_2_apply.grid(row=1, column=4, sticky="w", pady=(6, 0))

    app.vpn_table = ttk.Treeview(
        app.tab_vpn_slots,
        columns=("slot", "name", "profile", "status"),
        show="headings",
        height=8,
    )
    for col, title, width, anchor in [
        ("slot", "Slot", 60, "center"),
        ("name", "Anzeigename", 180, "w"),
        ("profile", "Profil", 180, "w"),
        ("status", "Status", 120, "center"),
    ]:
        app.vpn_table.heading(col, text=title)
        app.vpn_table.column(col, width=width, anchor=anchor)
    app.vpn_table.pack(fill="x")
    app.vpn_table.bind("<<TreeviewSelect>>", app.on_vpn_table_select)

    manual_wg_frame = ttk.LabelFrame(
        app.tab_vpn_slots,
        text="Manuelle WireGuard-Konfiguration",
        padding=8,
    )
    manual_wg_frame.pack(fill="x", pady=(10, 0))
    manual_wg_frame.columnconfigure(1, weight=1)
    manual_wg_frame.columnconfigure(3, weight=1)

    app.manual_wg_profile_name_var = tk.StringVar(value="")
    app.manual_wg_private_key_var = tk.StringVar(value="")
    app.manual_wg_public_key_var = tk.StringVar(value="")
    app.manual_wg_endpoint_var = tk.StringVar(value="")
    app.manual_wg_allowed_ips_var = tk.StringVar(value="0.0.0.0/0")
    app.manual_wg_dns_var = tk.StringVar(value="")
    app.manual_wg_keepalive_var = tk.StringVar(value="25")
    app.manual_wg_save_slot_var = tk.BooleanVar(value=False)
    app.manual_wg_slot_var = tk.StringVar(value="1")

    ttk.Label(manual_wg_frame, text="Profilname:").grid(
        row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_profile_name_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_profile_name_var,
    )
    app.manual_wg_profile_name_entry.grid(
        row=0, column=1, sticky="ew", padx=(0, 10), pady=(0, 4)
    )

    ttk.Label(manual_wg_frame, text="Private Key:").grid(
        row=0, column=2, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_private_key_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_private_key_var,
        show="*",
    )
    app.manual_wg_private_key_entry.grid(row=0, column=3, sticky="ew", pady=(0, 4))

    ttk.Label(manual_wg_frame, text="Public Key:").grid(
        row=1, column=0, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_public_key_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_public_key_var,
    )
    app.manual_wg_public_key_entry.grid(
        row=1, column=1, sticky="ew", padx=(0, 10), pady=(0, 4)
    )

    ttk.Label(manual_wg_frame, text="Endpoint:").grid(
        row=1, column=2, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_endpoint_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_endpoint_var,
    )
    app.manual_wg_endpoint_entry.grid(row=1, column=3, sticky="ew", pady=(0, 4))

    ttk.Label(manual_wg_frame, text="Allowed IPs:").grid(
        row=2, column=0, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_allowed_ips_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_allowed_ips_var,
    )
    app.manual_wg_allowed_ips_entry.grid(
        row=2, column=1, sticky="ew", padx=(0, 10), pady=(0, 4)
    )

    ttk.Label(manual_wg_frame, text="DNS (optional):").grid(
        row=2, column=2, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_dns_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_dns_var,
    )
    app.manual_wg_dns_entry.grid(row=2, column=3, sticky="ew", pady=(0, 4))

    ttk.Label(manual_wg_frame, text="Persistent Keepalive (optional):").grid(
        row=3, column=0, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_keepalive_entry = ttk.Entry(
        manual_wg_frame,
        textvariable=app.manual_wg_keepalive_var,
        width=8,
    )
    app.manual_wg_keepalive_entry.grid(
        row=3, column=1, sticky="w", padx=(0, 10), pady=(0, 4)
    )

    app.manual_wg_save_slot_check = ttk.Checkbutton(
        manual_wg_frame,
        text="Als VPN-Slot speichern",
        variable=app.manual_wg_save_slot_var,
        command=app._sync_manual_wg_slot_controls,
    )
    app.manual_wg_save_slot_check.grid(
        row=3, column=2, sticky="w", padx=(0, 4), pady=(0, 4)
    )
    app.manual_wg_slot_combo = ttk.Combobox(
        manual_wg_frame,
        textvariable=app.manual_wg_slot_var,
        values=[str(i) for i in range(1, VPN_SLOT_COUNT + 1)],
        state="readonly",
        width=4,
    )
    app.manual_wg_slot_combo.grid(row=3, column=3, sticky="w", pady=(0, 4))

    btn_manual_wg_apply = ttk.Button(
        manual_wg_frame,
        text="Profil anwenden",
        command=app.apply_manual_wireguard_profile,
    )
    btn_manual_wg_apply.grid(row=4, column=3, sticky="e", pady=(6, 0))
    app.register_feature_button("wg", btn_manual_wg_apply)
    app.add_tooltip(
        btn_manual_wg_apply,
        "Erstellt aus den Eingaben ein WireGuard-Profil, speichert es sicher und startet den Tunnel.",
    )

    btn_manual_wg_clear = ttk.Button(
        manual_wg_frame,
        text="Felder leeren",
        command=app.clear_manual_wireguard_form,
    )
    btn_manual_wg_clear.grid(row=4, column=2, sticky="e", padx=(0, 8), pady=(6, 0))
    app.add_tooltip(
        btn_manual_wg_clear,
        "Setzt die manuelle WireGuard-Eingabe auf Standardwerte zurück.",
    )

    app.manual_wg_status_var = tk.StringVar(
        value="Bereit für manuelle WireGuard-Konfiguration."
    )
    app.manual_wg_status_label = tk.Label(
        manual_wg_frame,
        textvariable=app.manual_wg_status_var,
        fg="#1f4f1f",
        anchor="w",
        justify="left",
    )
    app.manual_wg_status_label.grid(
        row=5,
        column=0,
        columnspan=4,
        sticky="ew",
        pady=(8, 0),
    )

    app._sync_manual_wg_slot_controls()

    app._vpn_form_loading = False
    app._vpn_form_dirty = False
    app.vpn_custom_name_var.trace_add("write", app._on_vpn_form_field_changed)
    app.vpn_profile_var.trace_add("write", app._on_vpn_form_field_changed)

    app.load_vpn_slot_into_form(1)
    app.refresh_vpn_slots_table()
    app.update_vpn_slot_buttons()
