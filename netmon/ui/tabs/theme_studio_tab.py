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
