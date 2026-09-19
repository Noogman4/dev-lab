"""Theme Studio UI builders for NetMon."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def build_theme_studio_layout(app):
    """Build the Theme Studio two-column layout and return its content areas."""
    frame = ttk.Frame(app.tab_theme_studio, padding=12)
    frame.pack(fill="both", expand=True)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    layout = ttk.Frame(frame)
    layout.grid(row=0, column=0, sticky="nsew")
    layout.columnconfigure(0, weight=0, minsize=320)
    layout.columnconfigure(1, weight=1)
    layout.rowconfigure(0, weight=1)
    controls = ttk.Frame(layout)
    controls.grid(row=0, column=0, sticky="nsw", padx=(0, 12))
    preview = ttk.LabelFrame(
        layout,
        text=app.tr("theme_studio_group_live_preview", "Live-Vorschau"),
        padding=10,
    )
    preview.grid(row=0, column=1, sticky="nsew")
    preview.columnconfigure(0, weight=1)
    return controls, preview


def build_theme_studio_profile_panel(app, controls) -> None:
    """Build the fixed Pop-profile identity and name controls."""
    basics = ttk.LabelFrame(
        controls,
        text=app.tr("theme_studio_group_pop_profile", "Pop profile"),
        padding=8,
    )
    basics.pack(fill="x", pady=(0, 8))
    app.var_theme_studio_base_theme.set(app._get_theme_display_name("pop"))
    ttk.Label(
        basics,
        text=app.tr("theme_studio_label_edited_profile", "Edited profile:"),
    ).grid(row=0, column=0, sticky="w")
    ttk.Label(
        basics,
        text="Pop",
        font=("TkDefaultFont", 10, "bold"),
    ).grid(row=0, column=1, sticky="w", padx=(8, 0))
    ttk.Label(
        basics,
        text=app.tr(
            "theme_studio_pop_profile_note",
            "Theme Studio only affects the Pop test profile.\nLight, Dark and Beige remain unchanged.",
        ),
        justify="left",
        wraplength=260,
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
    ttk.Label(
        basics,
        text=app.tr("theme_studio_label_profile_name", "Profilname:"),
    ).grid(row=2, column=0, sticky="w", pady=(8, 0))
    app.theme_studio_profile_entry = ttk.Entry(
        basics,
        textvariable=app.var_theme_studio_profile_name,
        width=20,
    )
    app.theme_studio_profile_entry.grid(
        row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0)
    )


def build_theme_studio_color_controls(app, controls) -> None:
    """Build Theme Studio color inputs, choosers and preset buttons."""
    colors = ttk.LabelFrame(
        controls,
        text=app.tr("theme_studio_group_color_adjustment", "Farbanpassung"),
        padding=8,
    )
    colors.pack(fill="x", pady=(0, 8))
    ttk.Label(
        colors,
        text=app.tr("theme_studio_label_primary_color", "Hauptfarbe:"),
    ).grid(row=0, column=0, sticky="w")
    app.theme_studio_accent_entry = ttk.Entry(
        colors,
        textvariable=app.var_theme_studio_accent,
        width=12,
    )
    app.theme_studio_accent_entry.grid(row=0, column=1, sticky="w", padx=(8, 0))
    app.theme_studio_accent_entry.bind(
        "<KeyRelease>", lambda _event: app.refresh_theme_studio_preview()
    )
    app.btn_theme_studio_choose_accent = ttk.Button(
        colors,
        text=app.tr("theme_studio_btn_choose_color", "Farbe wählen"),
        command=app.choose_theme_studio_accent_color,
    )
    app.btn_theme_studio_choose_accent.grid(row=0, column=2, sticky="w", padx=(8, 0))
    ttk.Label(
        colors,
        text=app.tr("theme_studio_label_panel_color", "Panelfarbe:"),
    ).grid(row=1, column=0, sticky="w", pady=(8, 0))
    app.theme_studio_panel_entry = ttk.Entry(
        colors,
        textvariable=app.var_theme_studio_panel,
        width=12,
    )
    app.theme_studio_panel_entry.grid(
        row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0)
    )
    app.theme_studio_panel_entry.bind(
        "<KeyRelease>", lambda _event: app.refresh_theme_studio_preview()
    )
    app.btn_theme_studio_choose_panel = ttk.Button(
        colors,
        text=app.tr("theme_studio_btn_choose_color", "Farbe wählen"),
        command=app.choose_theme_studio_panel_color,
    )
    app.btn_theme_studio_choose_panel.grid(
        row=1, column=2, sticky="w", padx=(8, 0), pady=(8, 0)
    )
    preset_row = ttk.Frame(colors)
    preset_row.grid(row=2, column=0, columnspan=3, sticky="w", pady=(8, 0))
    ttk.Label(
        preset_row,
        text=app.tr("theme_studio_label_button_presets", "Button-Presets:"),
    ).pack(side="left")
    for label, color in (
        ("Ocean", "#58a6ff"),
        ("Sunset", "#ff8f5a"),
        ("Berry", "#ff5a8a"),
        ("Terminal", "#7cff6b"),
    ):
        ttk.Button(
            preset_row,
            text=label,
            width=9,
            command=lambda c=color: app.set_theme_studio_accent_preset(c),
        ).pack(side="left", padx=(6, 0))
    panel_preset_row = ttk.Frame(colors)
    panel_preset_row.grid(row=3, column=0, columnspan=3, sticky="w", pady=(8, 0))
    ttk.Label(
        panel_preset_row,
        text=app.tr("theme_studio_label_panel_presets", "Panel-Presets:"),
    ).pack(side="left")
    for label, color in (
        ("Soft Pop", "#fff4ef"),
        ("Night Ink", "#1c1824"),
        ("Cream", "#f6ead7"),
        ("Mint", "#e6fff3"),
    ):
        ttk.Button(
            panel_preset_row,
            text=label,
            width=9,
            command=lambda c=color: app.set_theme_studio_panel_preset(c),
        ).pack(side="left", padx=(6, 0))


def build_theme_studio_style_actions(app, controls) -> None:
    """Build Theme Studio style selection and profile action controls."""
    style_box = ttk.LabelFrame(
        controls,
        text=app.tr("theme_studio_group_style_direction", "Stilrichtung"),
        padding=8,
    )
    style_box.pack(fill="x", pady=(0, 8))
    for index, (key, fallback, value) in enumerate(
        (
            ("theme_studio_style_subtle", "Subtle", "dezent"),
            ("theme_studio_style_bold", "Bold", "kräftig"),
            ("theme_studio_style_warm", "Warm", "warm"),
            ("theme_studio_style_cool", "Cool", "kühl"),
        )
    ):
        ttk.Radiobutton(
            style_box,
            text=app.tr(key, fallback),
            value=value,
            variable=app.var_theme_studio_style,
            command=app.refresh_theme_studio_preview,
        ).grid(
            row=index // 2,
            column=index % 2,
            sticky="w",
            padx=(0, 14 if index % 2 == 0 else 0),
            pady=(0 if index < 2 else 6, 0),
        )
    actions = ttk.LabelFrame(
        controls, text=app.tr("theme_studio_group_actions", "Actions"), padding=8
    )
    actions.pack(fill="x")
    app.btn_theme_studio_apply = ttk.Button(
        actions,
        text=app.tr("btn_apply", "Anwenden"),
        command=app.apply_theme_studio_settings,
    )
    app.btn_theme_studio_apply.pack(fill="x")
    app.btn_theme_studio_save = ttk.Button(
        actions,
        text=app.tr("theme_studio_btn_save_theme", "Theme speichern"),
        command=app.save_theme_studio_profile,
    )
    app.btn_theme_studio_save.pack(fill="x", pady=(6, 0))
    app.btn_theme_studio_load = ttk.Button(
        actions,
        text=app.tr("theme_studio_btn_load_theme", "Theme laden"),
        command=app.load_theme_studio_profile,
    )
    app.btn_theme_studio_load.pack(fill="x", pady=(6, 0))
    app.btn_theme_studio_load_pop = ttk.Button(
        actions,
        text=app.tr("theme_studio_btn_load_pop_profile", "Load pop profile"),
        command=app.load_theme_studio_from_current_theme,
    )
    app.btn_theme_studio_load_pop.pack(fill="x", pady=(6, 0))
    app.btn_theme_studio_reset = ttk.Button(
        actions,
        text=app.tr(
            "theme_studio_btn_restore_pop_default",
            "Pop-Standard wiederherstellen",
        ),
        command=app.reset_theme_studio_settings,
    )
    app.btn_theme_studio_reset.pack(fill="x", pady=(6, 0))
    ttk.Label(
        actions,
        textvariable=app.theme_studio_status_var,
        justify="left",
        wraplength=260,
    ).pack(anchor="w", pady=(8, 0))


def build_theme_studio_preview(app, preview) -> None:
    """Build the live Theme Studio preview and bind it to its inputs."""
    preview_hint = ttk.Label(
        preview,
        text=(
            "V1: Hier wird ausschließlich das Testprofil Pop gestaltet. "
            "Andere Themes bleiben unberührt."
        ),
        justify="left",
        wraplength=520,
    )
    preview_hint.grid(row=0, column=0, sticky="w")

    app.theme_studio_preview_shell = tk.Frame(
        preview,
        bd=1,
        relief="solid",
        padx=12,
        pady=12,
    )
    app.theme_studio_preview_shell.grid(row=1, column=0, sticky="ew", pady=(10, 0))
    app.theme_studio_preview_shell.grid_columnconfigure(0, weight=1)

    app.theme_studio_preview_title = tk.Label(
        app.theme_studio_preview_shell,
        text=app.tr("theme_studio_preview_title", "NetMon Theme Studio"),
        font=("TkDefaultFont", 11, "bold"),
        anchor="w",
    )
    app.theme_studio_preview_title.grid(row=0, column=0, sticky="w")
    app.theme_studio_preview_subtitle = tk.Label(
        app.theme_studio_preview_shell,
        text=app.tr(
            "theme_studio_preview_subtitle",
            "Vorschau für Buttons, Tabs, Status und Logbereiche",
        ),
        anchor="w",
    )
    app.theme_studio_preview_subtitle.grid(row=1, column=0, sticky="w", pady=(2, 10))

    tabs_row = tk.Frame(app.theme_studio_preview_shell, bd=0)
    tabs_row.grid(row=2, column=0, sticky="w")
    app.theme_studio_preview_tab_active = tk.Label(
        tabs_row,
        text=app.tr("theme_studio_preview_active_tab", "Aktiver Tab"),
        padx=10,
        pady=4,
    )
    app.theme_studio_preview_tab_active.pack(side="left")
    app.theme_studio_preview_tab_idle = tk.Label(
        tabs_row,
        text=app.tr("theme_studio_preview_inactive_tab", "Inactive tab"),
        padx=10,
        pady=4,
    )
    app.theme_studio_preview_tab_idle.pack(side="left", padx=(8, 0))

    action_row = tk.Frame(app.theme_studio_preview_shell, bd=0)
    action_row.grid(row=3, column=0, sticky="w", pady=(12, 0))
    app.theme_studio_preview_button = tk.Button(
        action_row,
        text=app.tr("theme_studio_preview_test_button", "Test-Button"),
        padx=14,
        pady=4,
    )
    app.theme_studio_preview_button.pack(side="left")
    for key, fallback, widget_name in (
        (
            "theme_studio_preview_status_active",
            "Aktiv",
            "theme_studio_preview_status_ok",
        ),
        (
            "theme_studio_preview_status_warning",
            "Warnung",
            "theme_studio_preview_status_warn",
        ),
        (
            "theme_studio_preview_status_error",
            "Fehler",
            "theme_studio_preview_status_err",
        ),
    ):
        status = tk.Label(
            action_row,
            text=app.tr(key, fallback),
            padx=10,
            pady=4,
        )
        status.pack(side="left", padx=(10, 0))
        setattr(app, widget_name, status)

    app.theme_studio_preview_entry = tk.Entry(
        app.theme_studio_preview_shell,
        relief="solid",
        bd=1,
    )
    app.theme_studio_preview_entry.grid(row=4, column=0, sticky="ew", pady=(12, 0))
    app.theme_studio_preview_entry.insert(
        0,
        app.tr(
            "theme_studio_preview_entry_example",
            "Beispiel für Eingabefeld und Fokusfarbe",
        ),
    )

    app.theme_studio_preview_log = tk.Label(
        app.theme_studio_preview_shell,
        text=app.tr(
            "theme_studio_preview_log_ready",
            "[LOG] Theme Studio bereit. Vorschau aktualisiert.",
        ),
        justify="left",
        anchor="w",
        padx=10,
        pady=8,
        relief="solid",
        bd=1,
    )
    app.theme_studio_preview_log.grid(row=5, column=0, sticky="ew", pady=(12, 0))

    swatch_row = tk.Frame(app.theme_studio_preview_shell, bd=0)
    swatch_row.grid(row=6, column=0, sticky="w", pady=(12, 0))
    for label_text, widget_name in (
        ("Akzent", "theme_studio_swatch_accent"),
        ("Panel", "theme_studio_swatch_panel"),
        ("Rahmen", "theme_studio_swatch_border"),
        ("Log", "theme_studio_swatch_log"),
    ):
        block = tk.Frame(swatch_row, bd=0)
        block.pack(side="left", padx=(0, 12))
        tk.Label(block, text=label_text, anchor="w").pack(anchor="w")
        swatch = tk.Frame(block, width=46, height=18, bd=1, relief="solid")
        swatch.pack(anchor="w", pady=(4, 0))
        swatch.pack_propagate(False)
        setattr(app, widget_name, swatch)

    app.theme_studio_preview_meta = tk.Label(
        app.theme_studio_preview_shell,
        text=app.tr("theme_studio_preview_profile_placeholder", "Profil: –"),
        anchor="w",
    )
    app.theme_studio_preview_meta.grid(row=7, column=0, sticky="w", pady=(12, 0))
    app.theme_studio_preview_status_line = tk.Label(
        app.theme_studio_preview_shell,
        text=app.tr(
            "theme_studio_preview_status_placeholder",
            "Basis: – | Akzent: – | Stil: –",
        ),
        anchor="w",
    )
    app.theme_studio_preview_status_line.grid(row=8, column=0, sticky="w", pady=(4, 0))

    for source_var in (
        app.var_theme_studio_profile_name,
        app.var_theme_studio_accent,
        app.var_theme_studio_panel,
        app.var_theme_studio_style,
        app.var_theme_studio_base_theme,
    ):
        try:
            source_var.trace_add(
                "write",
                lambda *_args: app.refresh_theme_studio_preview(),
            )
        except Exception:
            pass

    app.refresh_theme_studio_preview()
    app.theme_studio_preview_meta.configure(
        text=app.tr(
            "theme_studio_preview_profile_value",
            "Profile: {profile}",
        ).format(
            profile=(
                app.var_theme_studio_profile_name.get()
                or app.tr("theme_studio_default_profile_name", "My Theme")
            )
        )
    )
