"""Theme Studio UI builders for NetMon."""

from __future__ import annotations

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
