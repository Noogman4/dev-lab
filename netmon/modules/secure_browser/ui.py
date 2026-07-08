"""Tkinter UI scaffolding for the NetMon Secure Browser tab."""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk

from .manager import SecureBrowserManager


LOGGER = logging.getLogger(__name__)

HEADER_BUTTON_WIDTH = 16
CREATE_BUTTON_WIDTH = 12
FIELD_PAD_X = 12
ROW_PAD_Y = 8
CREATE_LABEL_WIDTH = 16
CREATE_FIELD_WIDTH = 28
CREATE_COMBO_WIDTH = 24


PRIMARY_ACTIONS = [
    ("secure_browser_btn_register_existing", "Einbinden", "backup"),
    ("secure_browser_btn_edit_whitelist", "Whitelist", "edit_policy"),
    ("secure_browser_btn_add_whitelist_exception", "Ausnahme", "add_policy_exception"),
    ("secure_browser_btn_save_whitelist", "Speichern", "save_policy"),
]

MAINTENANCE_ACTIONS = [
    ("secure_browser_btn_refresh_existing", "Aktualisieren", "refresh_existing"),
    ("secure_browser_btn_repair_policy", "Reparieren", "repair_policy"),
    ("secure_browser_btn_inspect_launcher", "Launcher", "inspect_launcher"),
]

STATUS_STYLE_MAP = {
    "OK:": "SecureBrowser.Status.Ok.TLabel",
    "Vorschau:": "SecureBrowser.Status.Preview.TLabel",
    "Dry-Run:": "SecureBrowser.Status.DryRun.TLabel",
    "Blockiert:": "SecureBrowser.Status.Blocked.TLabel",
    "Fehler:": "SecureBrowser.Status.Error.TLabel",
    "Ausgeführt:": "SecureBrowser.Status.Executed.TLabel",
    "Bereit:": "SecureBrowser.Status.Ready.TLabel",
}


def _bind_entry_clipboard_support(widget) -> None:
    def handle_copy(_event=None):
        try:
            widget.event_generate("<<Copy>>")
        except Exception:
            LOGGER.exception("Secure Browser copy failed")
        return "break"

    def handle_cut(_event=None):
        try:
            widget.event_generate("<<Cut>>")
        except Exception:
            LOGGER.exception("Secure Browser cut failed")
        return "break"

    def handle_paste(_event=None):
        try:
            widget.event_generate("<<Paste>>")
        except Exception:
            LOGGER.exception("Secure Browser paste failed")
        return "break"

    def show_context_menu(event):
        menu_factory = getattr(tk, "Menu", None)
        if menu_factory is None:
            return "break"
        try:
            menu = menu_factory(widget, tearoff=0)
            menu.add_command(label="Ausschneiden", command=handle_cut)
            menu.add_command(label="Kopieren", command=handle_copy)
            menu.add_command(label="Einfügen", command=handle_paste)
            menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            LOGGER.exception("Secure Browser clipboard menu failed")
        finally:
            try:
                menu.grab_release()
            except Exception:
                pass
        return "break"

    for sequence, handler in (
        ("<Control-c>", handle_copy),
        ("<Control-C>", handle_copy),
        ("<Control-x>", handle_cut),
        ("<Control-X>", handle_cut),
        ("<Control-v>", handle_paste),
        ("<Control-V>", handle_paste),
        ("<Button-3>", show_context_menu),
    ):
        try:
            widget.bind(sequence, handler)
        except Exception:
            LOGGER.exception("Secure Browser clipboard binding failed: %s", sequence)


def _prompt_url_with_context_menu(parent, title: str, prompt: str) -> str | None:
    toplevel_factory = getattr(tk, "Toplevel", None)
    if toplevel_factory is None:
        return simpledialog.askstring(title, prompt)

    result = {"value": None}

    dialog = toplevel_factory(parent)
    try:
        if hasattr(dialog, "title"):
            dialog.title(title)
        if hasattr(dialog, "transient"):
            dialog.transient(parent)
        if hasattr(dialog, "grab_set"):
            dialog.grab_set()
        if hasattr(dialog, "columnconfigure"):
            dialog.columnconfigure(0, weight=1)

        content = ttk.Frame(dialog, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        if hasattr(content, "columnconfigure"):
            content.columnconfigure(0, weight=1)

        ttk.Label(content, text=prompt, justify="left", wraplength=420).grid(
            row=0, column=0, sticky="w"
        )

        entry = ttk.Entry(content, width=56)
        entry.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        _bind_entry_clipboard_support(entry)
        if hasattr(entry, "focus_set"):
            entry.focus_set()

        button_row = ttk.Frame(content)
        button_row.grid(row=2, column=0, sticky="e", pady=(12, 0))

        def accept(_event=None):
            result["value"] = entry.get().strip()
            if hasattr(dialog, "destroy"):
                dialog.destroy()
            return "break"

        def cancel(_event=None):
            result["value"] = None
            if hasattr(dialog, "destroy"):
                dialog.destroy()
            return "break"

        ttk.Button(button_row, text="OK", command=accept).grid(
            row=0, column=0, padx=(0, 8)
        )
        ttk.Button(button_row, text="Abbrechen", command=cancel).grid(
            row=0, column=1
        )

        try:
            dialog.bind("<Return>", accept)
            dialog.bind("<Escape>", cancel)
        except Exception:
            pass

        wait_window = getattr(dialog, "wait_window", None)
        if callable(wait_window):
            wait_window()
        return result["value"]
    except Exception:
        try:
            if hasattr(dialog, "destroy"):
                dialog.destroy()
        except Exception:
            pass
        LOGGER.exception("Secure Browser URL exception dialog failed")
        return simpledialog.askstring(title, prompt)


class _FallbackBoolVar:
    def __init__(self, value: bool = False) -> None:
        self._value = bool(value)

    def get(self) -> bool:
        return self._value

    def set(self, value: bool) -> None:
        self._value = bool(value)


def _make_bool_var(value: bool = False):
    variable_factory = getattr(tk, "BooleanVar", None)
    if callable(variable_factory):
        try:
            return variable_factory(value=value)
        except Exception:
            LOGGER.exception("Secure Browser BooleanVar fallback activated")
    return _FallbackBoolVar(value=value)


def create_secure_browser_tab(
    parent,
    manager: SecureBrowserManager,
    *,
    tr=None,
    title: str = "NetMon Secure Browser",
    description: str = (
        "NetMon Secure Browser erstellt für jede Webseite einen eigenen, "
        "getrennten Firefox-Container mit eigenem Profil. Dadurch bleiben "
        "Cookies, Website-Daten und Einstellungen auf den jeweiligen Browser "
        "beschränkt und werden nicht mit anderen Diensten geteilt. Das "
        "erschwert dienstübergreifendes Tracking und sorgt für eine klarere "
        "Trennung Ihrer Online-Aktivitäten."
    ),
    hint: str = "",
):
    """Create the placeholder Secure Browser tab content."""

    def T(key: str, default: str) -> str:
        if callable(tr):
            try:
                return str(tr(key, default))
            except Exception:
                return default
        return default

    frame = ttk.Frame(parent, padding=12)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(10, weight=1)

    style_factory = getattr(ttk, "Style", None)
    if style_factory is not None:
        try:
            style = style_factory()
            style.configure("SecureBrowser.Status.Ready.TLabel")
            style.configure("SecureBrowser.Status.Ok.TLabel", foreground="#1f6f43")
            style.configure("SecureBrowser.Status.Preview.TLabel", foreground="#8a5a00")
            style.configure("SecureBrowser.Status.DryRun.TLabel", foreground="#0b5cab")
            style.configure("SecureBrowser.Status.Blocked.TLabel", foreground="#8b2e16")
            style.configure("SecureBrowser.Status.Error.TLabel", foreground="#b42318")
            style.configure(
                "SecureBrowser.Status.Executed.TLabel", foreground="#5b21b6"
            )
        except Exception:
            LOGGER.exception("Secure Browser status styles could not be initialized")

    header = ttk.Label(frame, text=title, font=("TkDefaultFont", 14, "bold"))
    header.grid(row=0, column=0, sticky="w")

    description_label = ttk.Label(
        frame,
        text=description,
        wraplength=720,
        justify="left",
    )
    description_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

    hint_label = ttk.Label(frame, text=hint, wraplength=720, justify="left")
    if hint:
        hint_label.grid(row=2, column=0, sticky="w", pady=(6, 12))

    status_row = ttk.Frame(frame)
    status_row.grid(row=3, column=0, sticky="ew")

    status_title = ttk.Label(status_row, text=T("secure_browser_label_status", "Status:"))
    status_title.grid(row=0, column=0, sticky="w", padx=(0, 8))

    status_badge = ttk.Label(
        status_row,
        text=T("secure_browser_status_ready_initial", "Bereit: read-only Startzustand"),
        style="SecureBrowser.Status.Ready.TLabel",
    )
    status_badge.grid(row=0, column=1, sticky="w")

    button_row = ttk.Frame(frame)
    button_row.grid(row=4, column=0, sticky="w", pady=(12, 0))
    if hasattr(button_row, "columnconfigure"):
        for column in range(4):
            button_row.columnconfigure(column, weight=0)

    filter_row = ttk.Frame(frame)
    filter_row.grid(row=5, column=0, sticky="w", pady=(12, 0))

    view_label = ttk.Label(filter_row, text=T("secure_browser_label_view", "Ansicht:"))
    view_label.grid(row=0, column=0, sticky="w", padx=(0, 8))

    view_mode = ttk.Combobox(
        filter_row,
        state="readonly",
        width=18,
        values=[
            manager.VIEW_OVERVIEW,
            manager.VIEW_LAUNCHER,
            manager.VIEW_ARTIFACTS,
        ],
    )
    view_mode.grid(row=0, column=1, sticky="w")
    view_mode.set(manager.VIEW_OVERVIEW)

    create_section_label = ttk.Label(
        frame,
        text=T("secure_browser_section_create", "Erstellen"),
        font=("TkDefaultFont", 10, "bold"),
    )
    create_section_label.grid(row=7, column=0, sticky="w", pady=(12, 0))

    draft_row = ttk.Frame(frame)
    draft_row.grid(row=8, column=0, sticky="w", pady=(8, 0))
    if hasattr(draft_row, "columnconfigure"):
        for column in range(5):
            draft_row.columnconfigure(column, weight=0)

    draft_hint_label = ttk.Label(
        draft_row,
        text=T(
            "secure_browser_draft_hint",
            "Webseite eingeben, Rest wird automatisch abgeleitet. Felder bleiben änderbar.",
        ),
    )
    draft_hint_label.grid(row=0, column=0, columnspan=6, sticky="w")

    fields_row = ttk.Frame(draft_row)
    fields_row.grid(row=1, column=0, columnspan=6, sticky="w", pady=(ROW_PAD_Y, 0))
    if hasattr(fields_row, "columnconfigure"):
        fields_row.columnconfigure(0, weight=0)
        fields_row.columnconfigure(1, weight=0)

    left_fields = ttk.Frame(fields_row)
    left_fields.grid(row=0, column=0, sticky="nw")
    right_fields = ttk.Frame(fields_row)
    right_fields.grid(row=0, column=1, sticky="nw", padx=(28, 0))
    if hasattr(left_fields, "columnconfigure"):
        left_fields.columnconfigure(0, minsize=120)
        left_fields.columnconfigure(1, minsize=240)
    if hasattr(right_fields, "columnconfigure"):
        right_fields.columnconfigure(0, minsize=120)
        right_fields.columnconfigure(1, minsize=240)

    draft_name_label = ttk.Label(
        left_fields, text=T("secure_browser_label_container_name", "Containername:")
        , width=CREATE_LABEL_WIDTH
    )
    draft_name_label.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 0))

    draft_name_entry = ttk.Entry(left_fields, width=CREATE_FIELD_WIDTH)
    draft_name_entry.grid(
        row=0,
        column=1,
        sticky="w",
        padx=(0, FIELD_PAD_X),
        pady=(0, 0),
    )
    _bind_entry_clipboard_support(draft_name_entry)

    draft_homepage_label = ttk.Label(
        right_fields, text=T("secure_browser_label_website", "Webseite:"), width=CREATE_LABEL_WIDTH
    )
    draft_homepage_label.grid(
        row=0,
        column=0,
        sticky="w",
        padx=(0, 8),
        pady=(0, 0),
    )

    draft_homepage_entry = ttk.Entry(right_fields, width=CREATE_FIELD_WIDTH)
    draft_homepage_entry.grid(
        row=0,
        column=1,
        sticky="w",
        padx=(0, FIELD_PAD_X),
        pady=(0, 0),
    )
    _bind_entry_clipboard_support(draft_homepage_entry)

    draft_domains_label = ttk.Label(
        left_fields,
        text=T("secure_browser_label_domains", "Domains:"),
        width=CREATE_LABEL_WIDTH,
    )
    draft_domains_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(ROW_PAD_Y, 0))

    draft_domains_entry = ttk.Entry(left_fields, width=CREATE_FIELD_WIDTH)
    draft_domains_entry.grid(
        row=1,
        column=1,
        sticky="w",
        padx=(0, FIELD_PAD_X),
        pady=(ROW_PAD_Y, 0),
    )
    _bind_entry_clipboard_support(draft_domains_entry)

    draft_menu_label = ttk.Label(
        right_fields,
        text=T("secure_browser_label_menu_name", "Menüname:"),
        width=CREATE_LABEL_WIDTH,
    )
    draft_menu_label.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(ROW_PAD_Y, 0))

    draft_menu_entry = ttk.Entry(right_fields, width=CREATE_FIELD_WIDTH)
    draft_menu_entry.grid(
        row=1,
        column=1,
        sticky="w",
        padx=(0, FIELD_PAD_X),
        pady=(ROW_PAD_Y, 0),
    )
    _bind_entry_clipboard_support(draft_menu_entry)

    draft_new_tab_label = ttk.Label(
        left_fields,
        text=T("secure_browser_label_new_tabs", "Neue Tabs:"),
        width=CREATE_LABEL_WIDTH,
    )
    draft_new_tab_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(ROW_PAD_Y, 0))

    draft_new_tab_entry = ttk.Entry(left_fields, width=CREATE_FIELD_WIDTH)
    draft_new_tab_entry.grid(
        row=2,
        column=1,
        sticky="w",
        padx=(0, FIELD_PAD_X),
        pady=(ROW_PAD_Y, 0),
    )
    _bind_entry_clipboard_support(draft_new_tab_entry)

    draft_icon_mode_label = ttk.Label(
        right_fields,
        text=T("secure_browser_label_icon_mode", "Icon-Modus:"),
        width=CREATE_LABEL_WIDTH,
    )
    draft_icon_mode_label.grid(row=2, column=0, sticky="w", padx=(0, 8), pady=(ROW_PAD_Y, 0))

    draft_icon_mode = ttk.Combobox(
        right_fields,
        state="readonly",
        width=CREATE_COMBO_WIDTH,
        values=["favicon", "default", "custom"],
    )
    draft_icon_mode.grid(row=2, column=1, sticky="w", pady=(ROW_PAD_Y, 0))
    draft_icon_mode.set(manager.CREATE_DEFAULT_ICON_MODE)

    security_row = ttk.Frame(draft_row)
    security_row.grid(row=2, column=0, columnspan=6, sticky="w", pady=(ROW_PAD_Y, 0))
    if hasattr(security_row, "columnconfigure"):
        security_row.columnconfigure(0, minsize=120)
        security_row.columnconfigure(1, minsize=240)
        security_row.columnconfigure(2, minsize=320)

    draft_security_profile_label = ttk.Label(
        security_row,
        text=T("secure_browser_label_security_profile", "Sicherheitsprofil:"),
        width=CREATE_LABEL_WIDTH,
    )
    draft_security_profile_label.grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 0)
    )

    draft_security_profile = ttk.Combobox(
        security_row,
        state="readonly",
        width=CREATE_COMBO_WIDTH,
        values=manager.get_security_profile_options(),
    )
    draft_security_profile.grid(row=0, column=1, sticky="w", pady=(0, 0))
    draft_security_profile.set(manager.CREATE_DEFAULT_SECURITY_PROFILE)

    draft_security_profile_hint = ttk.Label(
        security_row,
        text="",
        wraplength=420,
        justify="left",
    )
    draft_security_profile_hint.grid(
        row=0, column=2, sticky="w", padx=(FIELD_PAD_X, 0), pady=(0, 0)
    )

    allow_password_manager_var = _make_bool_var(True)
    keep_cookies_var = _make_bool_var(True)
    enable_website_filter_var = _make_bool_var(True)

    def sync_security_controls_from_profile(*_args) -> None:
        resolved = manager.resolve_security_options(draft_security_profile.get())
        allow_password_manager_var.set(bool(resolved["allow_password_manager"]))
        keep_cookies_var.set(bool(resolved["keep_cookies"]))
        enable_website_filter_var.set(bool(resolved["enable_website_filter"]))
        hint_map = {
            manager.SECURITY_PROFILE_COMPATIBLE: T(
                "secure_browser_security_hint_compatible",
                "Kompatibel: weniger Brüche bei Login, Redirects und 2FA.",
            ),
            manager.SECURITY_PROFILE_STANDARD: T(
                "secure_browser_security_hint_standard",
                "Standard: guter Mittelweg aus Trennung, Komfort und Kompatibilität.",
            ),
            manager.SECURITY_PROFILE_STRICT: T(
                "secure_browser_security_hint_strict",
                "Streng: maximale Trennung, höhere Störanfälligkeit bei komplexen Diensten.",
            ),
            manager.SECURITY_PROFILE_CUSTOM: T(
                "secure_browser_security_hint_custom",
                "Benutzerdefiniert: manuell angepasste Sicherheitsoptionen.",
            ),
        }
        draft_security_profile_hint.configure(
            text=hint_map.get(
                draft_security_profile.get(),
                hint_map[manager.CREATE_DEFAULT_SECURITY_PROFILE],
            )
        )

    def sync_profile_from_security_controls(*_args) -> None:
        resolved = manager.resolve_security_options(
            draft_security_profile.get(),
            allow_password_manager=bool(allow_password_manager_var.get()),
            keep_cookies=bool(keep_cookies_var.get()),
            enable_website_filter=bool(enable_website_filter_var.get()),
        )
        draft_security_profile.set(str(resolved["security_profile"]))

    checkbutton_factory = getattr(ttk, "Checkbutton", ttk.Button)
    security_options_row = ttk.Frame(security_row)
    security_options_row.grid(row=1, column=0, columnspan=3, sticky="w", pady=(ROW_PAD_Y, 0))
    if hasattr(security_options_row, "columnconfigure"):
        security_options_row.columnconfigure(0, minsize=240)
        security_options_row.columnconfigure(1, minsize=240)
        security_options_row.columnconfigure(2, minsize=240)

    draft_allow_password_manager = checkbutton_factory(
        security_options_row,
        text=T(
            "secure_browser_option_password_manager",
            "Passwortspeicher erlauben",
        ),
        variable=allow_password_manager_var,
        command=sync_profile_from_security_controls,
    )
    draft_allow_password_manager.grid(
        row=0, column=0, sticky="w", pady=(0, 0)
    )

    draft_keep_cookies = checkbutton_factory(
        security_options_row,
        text=T("secure_browser_option_keep_cookies", "Cookies behalten"),
        variable=keep_cookies_var,
        command=sync_profile_from_security_controls,
    )
    draft_keep_cookies.grid(
        row=0, column=1, sticky="w", padx=(FIELD_PAD_X, 0), pady=(0, 0)
    )

    draft_enable_website_filter = checkbutton_factory(
        security_options_row,
        text=T(
            "secure_browser_option_enable_filter",
            "Website-Filter aktivieren",
        ),
        variable=enable_website_filter_var,
        command=sync_profile_from_security_controls,
    )
    draft_enable_website_filter.grid(
        row=0, column=2, sticky="w", padx=(FIELD_PAD_X, 0), pady=(0, 0)
    )

    if hasattr(draft_security_profile, "bind"):
        draft_security_profile.bind(
            "<<ComboboxSelected>>",
            sync_security_controls_from_profile,
        )
    sync_security_controls_from_profile()

    draft_dry_run_button = ttk.Button(
        draft_row,
        text=T("secure_browser_btn_builder_dry_run", "Dry-Run"),
        state="normal",
        width=CREATE_BUTTON_WIDTH,
    )

    draft_preview_button = ttk.Button(
        draft_row,
        text=T("secure_browser_btn_new_browser", "Neu"),
        state="normal",
        width=CREATE_BUTTON_WIDTH,
    )
    draft_preview_button.grid(row=3, column=0, sticky="w", pady=(ROW_PAD_Y, 0))

    draft_dry_run_button.grid(
        row=3,
        column=1,
        sticky="w",
        padx=(FIELD_PAD_X, 0),
        pady=(ROW_PAD_Y, 0),
    )

    draft_execute_button = ttk.Button(
        draft_row,
        text=T("secure_browser_btn_create_browser", "Anlegen"),
        state="normal",
        width=CREATE_BUTTON_WIDTH,
    )
    draft_execute_button.grid(
        row=3,
        column=2,
        sticky="w",
        padx=(FIELD_PAD_X, 0),
        pady=(ROW_PAD_Y, 0),
    )

    draft_remove_button = ttk.Button(
        draft_row,
        text=T("secure_browser_btn_remove_browser", "Entfernen"),
        state="normal",
        width=CREATE_BUTTON_WIDTH,
    )
    draft_remove_button.grid(
        row=3,
        column=3,
        sticky="w",
        padx=(FIELD_PAD_X, 0),
        pady=(ROW_PAD_Y, 0),
    )

    draft_inventory_button = ttk.Button(
        draft_row,
        text=T("secure_browser_btn_inventory", "Inventur"),
        state="normal",
        width=CREATE_BUTTON_WIDTH,
    )
    draft_inventory_button.grid(
        row=3,
        column=4,
        sticky="w",
        padx=(FIELD_PAD_X, 0),
        pady=(ROW_PAD_Y, 0),
    )

    admin_section_label = ttk.Label(
        frame,
        text=T("secure_browser_section_admin", "Verwaltung"),
        font=("TkDefaultFont", 10, "bold"),
    )
    admin_section_label.grid(row=9, column=0, sticky="w", pady=(12, 0))

    content_frame = ttk.Frame(frame)
    content_frame.grid(row=10, column=0, sticky="nsew", pady=(12, 0))
    content_frame.columnconfigure(2, weight=1)
    content_frame.rowconfigure(1, weight=1)
    scrollbar_factory = getattr(ttk, "Scrollbar", ttk.Frame)

    summary_text = tk.Text(
        content_frame,
        wrap="word",
        height=3,
        font=("TkDefaultFont", 10),
    )
    summary_text.grid(row=0, column=0, columnspan=4, sticky="ew", pady=(0, 8))
    summary_text.insert(
        "1.0",
        T("secure_browser_inventory_not_run", "Inventur noch nicht ausgeführt.")
        + "\n\n"
        + T(
            "secure_browser_inventory_read_only_hint",
            "Die erste Integrationsstufe ist rein lesend und nutzt keinen --apply-Modus.",
        ),
    )
    summary_text.configure(state="disabled")

    container_list = tk.Listbox(
        content_frame,
        exportselection=False,
        height=12,
    )
    container_list.grid(row=1, column=0, sticky="nsw", padx=(0, 12))

    container_list_scrollbar = scrollbar_factory(
        content_frame,
        orient="vertical",
        command=getattr(container_list, "yview", None),
    )
    container_list_scrollbar.grid(row=1, column=1, sticky="ns")
    try:
        container_list.configure(
            yscrollcommand=getattr(container_list_scrollbar, "set", None)
        )
    except Exception:
        LOGGER.exception("Secure Browser list scrollbar binding failed")

    detail_text = tk.Text(
        content_frame,
        wrap="word",
        height=16,
        font=("Courier", 10),
    )
    detail_text.grid(row=1, column=2, sticky="nsew", padx=(12, 0))
    detail_scrollbar = scrollbar_factory(
        content_frame,
        orient="vertical",
        command=getattr(detail_text, "yview", None),
    )
    detail_scrollbar.grid(row=1, column=3, sticky="ns")
    try:
        detail_text.configure(yscrollcommand=getattr(detail_scrollbar, "set", None))
    except Exception:
        LOGGER.exception("Secure Browser detail scrollbar binding failed")
    detail_text.insert("1.0", manager.render_preflight_text())
    detail_text.configure(state="disabled")

    current_admin_action: str | None = None
    current_admin_target: str | None = None
    current_detail_mode = "readonly"

    def set_text(widget, value: str, *, readonly: bool = True) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled" if readonly else "normal")

    def get_text(widget) -> str:
        getter = getattr(widget, "get", None)
        if callable(getter):
            try:
                return getter("1.0", "end").rstrip()
            except TypeError:
                pass
        return getattr(widget, "text_content", "").rstrip()

    def set_input_value(widget, value: str) -> None:
        if hasattr(widget, "set"):
            widget.set(value)
            return
        widget.delete(0, "end")
        widget.insert(0, value)

    def set_status(message: str) -> None:
        prefixes = [
            ("OK:", "[OK] "),
            ("Vorschau:", "[Vorschau] "),
            ("Dry-Run:", "[Dry-Run] "),
            ("Blockiert:", "[Blockiert] "),
            ("Fehler:", "[Fehler] "),
            ("Ausgeführt:", "[Ausgeführt] "),
            ("Bereit:", "[Bereit] "),
        ]
        formatted = message
        style_name = "SecureBrowser.Status.Ready.TLabel"
        for raw_prefix, badge_prefix in prefixes:
            if message.startswith(raw_prefix):
                formatted = f"{badge_prefix}{message[len(raw_prefix):].strip()}"
                style_name = STATUS_STYLE_MAP.get(
                    raw_prefix,
                    "SecureBrowser.Status.Ready.TLabel",
                )
                break
        status_badge.configure(text=formatted, style=style_name)

    def selected_container_context() -> tuple[str | None, str, str, str]:
        selection = container_list.curselection()
        if not selection:
            return (
                None,
                manager.STATUS_FILTER_ALL,
                "",
                manager.RISK_FILTER_ALL,
            )
        return (
            container_list.get(selection[0]),
            manager.STATUS_FILTER_ALL,
            "",
            manager.RISK_FILTER_ALL,
        )

    def update_copy_buttons() -> None:
        selection = container_list.curselection()
        has_selection = bool(selection)
        selected_name = container_list.get(selection[0]) if selection else None
        selected_container = None
        selected_risks: list[str] = []
        if selected_name:
            try:
                selected_container = manager.get_container_by_name(
                    selected_name,
                    manager.STATUS_FILTER_ALL,
                    "",
                    manager.RISK_FILTER_ALL,
                )
                if selected_container is not None:
                    selected_risks = manager.service.derive_risk_hints(selected_container)
            except Exception:
                LOGGER.exception("Secure Browser action state refresh failed")
        needs_registration = False
        if selected_container is not None:
            needs_registration = (
                selected_container.menu_entry_path is None
                or "fehlt" in (selected_container.status or "").lower()
                or any("Menüeintrag fehlt" in risk for risk in selected_risks)
                or any("Launcher fehlt" in risk for risk in selected_risks)
            )
        action_states = {
            "backup": has_selection and needs_registration,
            "inspect_launcher": has_selection,
            "edit_policy": has_selection,
            "add_policy_exception": has_selection,
            "save_policy": current_detail_mode == "policy_editor",
            "refresh_existing": has_selection or bool(manager.last_scan),
            "repair_policy": has_selection or bool(manager.last_scan),
        }
        for action, is_enabled in action_states.items():
            button = buttons.get(action)
            if button is None:
                continue
            try:
                button.configure(state="normal" if is_enabled else "disabled")
            except Exception:
                pass
            if hasattr(button, "kwargs"):
                button.kwargs["state"] = "normal" if is_enabled else "disabled"

    def load_policy_editor_for_selection() -> str | None:
        nonlocal current_detail_mode
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        if not selected_name:
            set_text(detail_text, "Whitelist bearbeiten\n\nKein Container ausgewählt.")
            set_status("Blockiert: keine Auswahl")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return None
        try:
            container = manager.get_container_by_name(
                selected_name,
                manager.STATUS_FILTER_ALL,
                "",
                manager.RISK_FILTER_ALL,
            )
            if container is None:
                raise ValueError("Container nicht mehr in der letzten Inventur vorhanden.")
            policy_json = manager.service.read_policy_json(container)
        except Exception as exc:
            LOGGER.exception("Secure Browser policy editor failed")
            set_text(detail_text, f"Fehler beim Laden der Whitelist: {exc}")
            set_status("Fehler: Whitelist")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return None
        set_text(detail_text, policy_json, readonly=False)
        set_status("Vorschau: Whitelist-Editor")
        current_detail_mode = "policy_editor"
        update_copy_buttons()
        return selected_name

    def render_selected_container(_event=None) -> None:
        nonlocal current_detail_mode
        selection = container_list.curselection()
        if not selection:
            set_text(detail_text, "Kein Container ausgewählt.")
            set_status("Bereit: keine Auswahl")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        selected_name = container_list.get(selection[0])
        active_filter = manager.STATUS_FILTER_ALL
        search_query = ""
        active_risk_filter = manager.RISK_FILTER_ALL
        active_view = view_mode.get() or manager.VIEW_OVERVIEW
        try:
            report = manager.render_selected_view(
                active_view,
                selected_name,
                active_filter,
                search_query,
                active_risk_filter,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser detail rendering failed")
            error_label = {
                manager.VIEW_LAUNCHER: "Launcher-Prüfung",
                manager.VIEW_ARTIFACTS: "Artefakt-Ansicht",
            }.get(active_view, "Verifikation")
            set_text(detail_text, f"Fehler bei {error_label}: {exc}")
            set_status(f"Fehler: {error_label}")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        set_text(detail_text, report)
        set_status(f"OK: {active_view}")
        current_detail_mode = "readonly"
        update_copy_buttons()

    def render_launcher_report() -> None:
        view_mode.set(manager.VIEW_LAUNCHER)
        render_selected_container()

    def render_artifact_report() -> None:
        view_mode.set(manager.VIEW_ARTIFACTS)
        render_selected_container()

    def render_overview_report() -> None:
        view_mode.set(manager.VIEW_OVERVIEW)
        selection = container_list.curselection()
        if not selection:
            set_text(detail_text, "Kein Container ausgewählt.")
            set_status("Bereit: keine Auswahl")
            update_copy_buttons()
            return
        render_selected_container()

    def execute_register_existing_direct() -> None:
        nonlocal current_admin_action, current_admin_target
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        if not selected_name:
            set_text(detail_text, "Registrieren\n\nKein Container ausgewählt.")
            set_status("Blockiert: keine Auswahl")
            return
        current_admin_action = "register"
        current_admin_target = selected_name
        confirmed = messagebox.askyesno(
            "Bestehende Container registrieren",
            f"{selected_name} jetzt registrieren?",
        )
        if not confirmed:
            set_status("Blockiert: Verwaltung abgebrochen")
            return
        try:
            manager.execute_register_existing_apply(
                current_admin_target,
                manager.REGISTER_CONFIRM_TOKEN,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser register failed")
            set_text(detail_text, f"Fehler bei Verwaltungsaktion: {exc}")
            set_status("Fehler: Verwaltung")
            update_copy_buttons()
            return
        refresh_inventory_after_action(preferred_name=current_admin_target)

    def execute_refresh_existing_direct() -> None:
        nonlocal current_admin_action, current_admin_target
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        current_admin_action = "refresh"
        current_admin_target = selected_name
        if selected_name:
            title = "Launcher/Icon aktualisieren"
            prompt = f"{selected_name} jetzt aktualisieren?"
        else:
            title = "Alle Launcher/Icons aktualisieren"
            prompt = "Alle erkannten Secure-Browser jetzt aktualisieren?"
        confirmed = messagebox.askyesno(title, prompt)
        if not confirmed:
            set_status("Blockiert: Verwaltung abgebrochen")
            return
        try:
            manager.execute_refresh_existing_apply(
                current_admin_target,
                manager.REFRESH_CONFIRM_TOKEN,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser refresh failed")
            set_text(detail_text, f"Fehler bei Verwaltungsaktion: {exc}")
            set_status("Fehler: Verwaltung")
            update_copy_buttons()
            return
        if current_admin_target:
            refresh_inventory_after_action(preferred_name=current_admin_target)
        else:
            refresh_inventory_after_action()

    def execute_repair_policy_direct() -> None:
        nonlocal current_admin_action, current_admin_target
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        current_admin_action = "repair_policy"
        current_admin_target = selected_name
        if selected_name:
            title = "Policy reparieren"
            prompt = f"{selected_name} jetzt reparieren?"
        else:
            title = "Policies aller Browser reparieren"
            prompt = "Alle erkannten Secure-Browser-Policies jetzt reparieren?"
        confirmed = messagebox.askyesno(title, prompt)
        if not confirmed:
            set_status("Blockiert: Verwaltung abgebrochen")
            return
        try:
            manager.execute_repair_policy_apply(
                current_admin_target,
                manager.REPAIR_POLICY_CONFIRM_TOKEN,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser policy repair failed")
            set_text(detail_text, f"Fehler bei Verwaltungsaktion: {exc}")
            set_status("Fehler: Verwaltung")
            update_copy_buttons()
            return
        if current_admin_target:
            refresh_inventory_after_action(preferred_name=current_admin_target)
        else:
            refresh_inventory_after_action()

    def render_policy_editor() -> None:
        load_policy_editor_for_selection()

    def execute_policy_save_direct() -> None:
        nonlocal current_detail_mode
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        if not selected_name:
            set_text(detail_text, "Whitelist speichern\n\nKein Container ausgewählt.")
            set_status("Blockiert: keine Auswahl")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        if current_detail_mode != "policy_editor":
            set_text(
                detail_text,
                "Whitelist speichern\n\nBitte zuerst 'Whitelist bearbeiten' öffnen.",
            )
            set_status("Blockiert: Editor nicht aktiv")
            update_copy_buttons()
            return
        confirmed = messagebox.askyesno(
            "Whitelist speichern",
            f"Änderungen für {selected_name} jetzt speichern?",
        )
        if not confirmed:
            set_status("Blockiert: Speichern abgebrochen")
            return
        try:
            output = manager.execute_policy_save_apply(
                selected_name,
                get_text(detail_text),
                manager.STATUS_FILTER_ALL,
                "",
                manager.RISK_FILTER_ALL,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser policy save failed")
            set_text(detail_text, f"Fehler beim Speichern der Whitelist: {exc}")
            set_status("Fehler: Whitelist")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        set_text(detail_text, output)
        set_status("Ausgeführt: Whitelist gespeichert")
        current_detail_mode = "readonly"
        refresh_inventory_after_action(preferred_name=selected_name)

    def execute_add_policy_exception_direct() -> None:
        nonlocal current_detail_mode
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        if not selected_name:
            set_text(detail_text, "Whitelist-Ausnahme\n\nKein Container ausgewählt.")
            set_status("Blockiert: keine Auswahl")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        if current_detail_mode != "policy_editor":
            selected_name = load_policy_editor_for_selection()
            if selected_name is None or current_detail_mode != "policy_editor":
                return
        value = _prompt_url_with_context_menu(
            frame,
            "URL als Ausnahme",
            "Fehlende URL oder Domain einfügen:",
        )
        if value is None:
            set_status("Blockiert: Ausnahme abgebrochen")
            return
        try:
            updated = manager.append_policy_exception_json(
                get_text(detail_text),
                value,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser add whitelist exception failed")
            set_text(detail_text, f"Whitelist-Ausnahme\n\nFehler: {exc}")
            set_status("Fehler: Whitelist")
            update_copy_buttons()
            return
        set_text(detail_text, updated, readonly=False)
        set_status("Vorschau: Ausnahme ergänzt")
        current_detail_mode = "policy_editor"
        update_copy_buttons()
        confirmed = messagebox.askyesno(
            "Whitelist speichern",
            f"Ausnahme für {selected_name} jetzt direkt speichern?",
        )
        if not confirmed:
            return
        try:
            output = manager.execute_policy_save_apply(
                selected_name,
                get_text(detail_text),
                manager.STATUS_FILTER_ALL,
                "",
                manager.RISK_FILTER_ALL,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser policy save after exception failed")
            set_text(detail_text, f"Fehler beim Speichern der Whitelist: {exc}")
            set_status("Fehler: Whitelist")
            current_detail_mode = "readonly"
            update_copy_buttons()
            return
        set_text(detail_text, output)
        set_status("Ausgeführt: Whitelist gespeichert")
        current_detail_mode = "readonly"
        refresh_inventory_after_action(preferred_name=selected_name)

    def render_cleanup_menu_preview() -> None:
        nonlocal current_admin_action, current_admin_target
        current_admin_action = "cleanup"
        current_admin_target = None
        set_text(
            detail_text,
            manager.render_cleanup_menu_preview(""),
        )
        set_status("Vorschau: Menü bereinigen")
        update_copy_buttons()

    def execute_uninstall_direct() -> None:
        nonlocal current_admin_action, current_admin_target
        selection = container_list.curselection()
        selected_name = container_list.get(selection[0]) if selection else None
        if not selected_name:
            set_text(detail_text, "Entfernen\n\nKein Container ausgewählt.")
            set_status("Blockiert: keine Auswahl")
            return
        current_admin_action = "uninstall"
        current_admin_target = selected_name
        confirmed = messagebox.askyesno(
            "Container entfernen",
            f"{selected_name} jetzt deinstallieren?",
        )
        if not confirmed:
            set_status("Blockiert: Verwaltung abgebrochen")
            return
        try:
            manager.execute_uninstall_apply(
                current_admin_target,
                manager.UNINSTALL_CONFIRM_TOKEN,
            )
        except Exception as exc:
            LOGGER.exception("Secure Browser uninstall failed")
            set_text(detail_text, f"Fehler bei Verwaltungsaktion: {exc}")
            set_status("Fehler: Verwaltung")
            update_copy_buttons()
            return
        refresh_inventory_after_action()

    def render_create_draft() -> None:
        try:
            output = manager.render_create_browser_draft(
                draft_name_entry.get(),
                draft_homepage_entry.get(),
                draft_domains_entry.get(),
                draft_menu_entry.get(),
                draft_new_tab_entry.get(),
                draft_icon_mode.get(),
                draft_security_profile.get(),
                bool(allow_password_manager_var.get()),
                bool(keep_cookies_var.get()),
                bool(enable_website_filter_var.get()),
            )
        except ValueError as exc:
            set_text(detail_text, f"Neuer Browser\n\nValidierung\n- {exc}")
            set_status("Fehler: Neuer Browser")
            update_copy_buttons()
            return
        set_text(detail_text, output)
        set_status("Vorschau: Neuer Browser")
        update_copy_buttons()

    def render_builder_dry_run() -> None:
        try:
            output = manager.render_create_browser_builder_dry_run(
                draft_name_entry.get(),
                draft_homepage_entry.get(),
                draft_domains_entry.get(),
                draft_menu_entry.get(),
                draft_new_tab_entry.get(),
                draft_icon_mode.get(),
                draft_security_profile.get(),
                bool(allow_password_manager_var.get()),
                bool(keep_cookies_var.get()),
                bool(enable_website_filter_var.get()),
            )
        except ValueError as exc:
            set_text(detail_text, f"Neuer Browser\n\nValidierung\n- {exc}")
            set_status("Fehler: Neuer Browser")
            update_copy_buttons()
            return
        set_text(detail_text, output)
        set_status("Dry-Run: Neuer Browser")
        update_copy_buttons()

    def execute_apply() -> None:
        confirmed = messagebox.askyesno(
            "Browser anlegen",
            "Secure Browser jetzt anlegen?\n\nVorher sollte der Dry-Run geprüft worden sein.",
        )
        if not confirmed:
            set_status("Blockiert: Erstellung abgebrochen")
            return
        created_name = draft_name_entry.get().strip() or None
        try:
            manager.execute_create_browser_apply(
                draft_name_entry.get(),
                draft_homepage_entry.get(),
                draft_domains_entry.get(),
                draft_menu_entry.get(),
                draft_new_tab_entry.get(),
                draft_icon_mode.get(),
                draft_security_profile.get(),
                bool(allow_password_manager_var.get()),
                bool(keep_cookies_var.get()),
                bool(enable_website_filter_var.get()),
                manager.APPLY_CONFIRM_TOKEN,
            )
        except ValueError as exc:
            set_text(detail_text, f"Neuer Browser\n\nValidierung\n- {exc}")
            set_status("Fehler: Neuer Browser")
            update_copy_buttons()
            return
        except Exception as exc:
            set_text(detail_text, str(exc))
            set_status("Fehler: Neuer Browser")
            update_copy_buttons()
            return
        refresh_inventory_after_action(preferred_name=created_name)

    def apply_filter(_event=None, preferred_name: str | None = None) -> None:
        active_filter = manager.STATUS_FILTER_ALL
        search_query = ""
        active_risk_filter = manager.RISK_FILTER_ALL
        names = manager.get_container_names(
            active_filter,
            search_query,
            active_risk_filter,
        )
        set_text(
            summary_text,
            manager.render_inventory_summary(
                active_filter,
                search_query,
                active_risk_filter,
            )
            + "\n"
            + manager.render_inventory_metrics(),
        )
        container_list.delete(0, tk.END)
        for name in names:
            container_list.insert(tk.END, name)
        if names:
            container_list.selection_clear(0, tk.END)
            target_index = 0
            if preferred_name and preferred_name in names:
                target_index = names.index(preferred_name)
            container_list.selection_set(target_index)
            container_list.activate(target_index)
            render_selected_container()
        else:
            set_text(detail_text, "Kein Container ausgewählt.")
            set_status("Bereit: keine gefilterten Container")
            update_copy_buttons()

    def render_inventory(preferred_name: str | None = None) -> None:
        try:
            manager.scan_inventory()
        except Exception as exc:
            LOGGER.exception("Secure Browser inventory failed")
            container_list.delete(0, tk.END)
            set_text(
                summary_text,
                "Inventur fehlgeschlagen.\n\n"
                "Es wurden keine Änderungen durchgeführt.",
            )
            set_text(detail_text, f"Fehler: {exc}")
            set_status("Fehler: Inventur")
            return

        set_status("OK: Inventur aktualisiert")
        apply_filter(preferred_name=preferred_name)

    def refresh_inventory_after_action(preferred_name: str | None = None) -> None:
        render_inventory(preferred_name=preferred_name)

    container_list.bind("<<ListboxSelect>>", render_selected_container)
    view_mode.bind("<<ComboboxSelected>>", render_selected_container)

    draft_preview_button.configure(command=render_create_draft)
    draft_dry_run_button.configure(command=render_builder_dry_run)
    draft_execute_button.configure(command=execute_apply)
    draft_remove_button.configure(command=execute_uninstall_direct)
    draft_inventory_button.configure(command=render_inventory)
    if hasattr(draft_inventory_button, "kwargs"):
        draft_inventory_button.kwargs["command"] = render_inventory

    def get_button_command(action: str):
        if action == "inventory":
            return render_inventory
        if action == "inspect_launcher":
            return render_launcher_report
        if action == "backup":
            return execute_register_existing_direct
        if action == "refresh_existing":
            return execute_refresh_existing_direct
        if action == "repair_policy":
            return execute_repair_policy_direct
        if action == "edit_policy":
            return render_policy_editor
        if action == "add_policy_exception":
            return execute_add_policy_exception_direct
        if action == "save_policy":
            return execute_policy_save_direct
        return lambda current=action: manager.todo_action(current)

    buttons = {}
    buttons["inventory"] = draft_inventory_button

    for column_index, (label_key, label_fallback, action) in enumerate(PRIMARY_ACTIONS):
        button = ttk.Button(
            button_row,
            text=T(label_key, label_fallback),
            width=HEADER_BUTTON_WIDTH,
            state=(
                "normal"
                if action
                in {
                    "inventory",
                    "inspect_launcher",
                    "backup",
                    "refresh_existing",
                    "repair_policy",
                    "edit_policy",
                }
                else "disabled"
            ),
            command=get_button_command(action),
        )
        button.grid(
            row=0,
            column=column_index,
            padx=(0, 8),
            pady=(0, 8),
            sticky="w",
        )
        buttons[action] = button

    for column_index, (label_key, label_fallback, action) in enumerate(
        MAINTENANCE_ACTIONS
    ):
        button = ttk.Button(
            button_row,
            text=T(label_key, label_fallback),
            width=HEADER_BUTTON_WIDTH,
            state=(
                "normal"
                if action
                in {
                    "inventory",
                    "inspect_launcher",
                    "backup",
                    "refresh_existing",
                    "repair_policy",
                    "edit_policy",
                }
                else "disabled"
            ),
            command=get_button_command(action),
        )
        button.grid(
            row=1,
            column=column_index,
            padx=(0, 8),
            pady=(0, 0),
            sticky="w",
        )
        buttons[action] = button

    frame.secure_browser_buttons = buttons
    frame.secure_browser_manager = manager
    frame.secure_browser_summary_text = summary_text
    frame.secure_browser_status_badge = status_badge
    frame.secure_browser_create_section_label = create_section_label
    frame.secure_browser_admin_section_label = admin_section_label
    frame.secure_browser_view_mode = view_mode
    frame.secure_browser_draft_hint_label = draft_hint_label
    frame.secure_browser_draft_name_entry = draft_name_entry
    frame.secure_browser_draft_homepage_entry = draft_homepage_entry
    frame.secure_browser_draft_domains_entry = draft_domains_entry
    frame.secure_browser_draft_menu_entry = draft_menu_entry
    frame.secure_browser_draft_new_tab_entry = draft_new_tab_entry
    frame.secure_browser_draft_icon_mode = draft_icon_mode
    frame.secure_browser_draft_security_profile = draft_security_profile
    frame.secure_browser_draft_security_profile_hint = draft_security_profile_hint
    frame.secure_browser_draft_allow_password_manager = draft_allow_password_manager
    frame.secure_browser_draft_keep_cookies = draft_keep_cookies
    frame.secure_browser_draft_enable_website_filter = draft_enable_website_filter
    frame.secure_browser_draft_allow_password_manager_var = allow_password_manager_var
    frame.secure_browser_draft_keep_cookies_var = keep_cookies_var
    frame.secure_browser_draft_enable_website_filter_var = enable_website_filter_var
    frame.secure_browser_draft_preview_button = draft_preview_button
    frame.secure_browser_draft_dry_run_button = draft_dry_run_button
    frame.secure_browser_draft_execute_button = draft_execute_button
    frame.secure_browser_draft_remove_button = draft_remove_button
    frame.secure_browser_draft_inventory_button = draft_inventory_button
    frame.secure_browser_container_list = container_list
    frame.secure_browser_container_list_scrollbar = container_list_scrollbar
    frame.secure_browser_detail_text = detail_text
    frame.secure_browser_detail_scrollbar = detail_scrollbar
    update_copy_buttons()
    return frame
