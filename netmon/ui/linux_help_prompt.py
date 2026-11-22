"""Shared local Markdown-prompt popup and user-confirmed import category."""

from __future__ import annotations

import tkinter as tk
from tkinter import simpledialog, ttk

try:
    from netmon.services.linux_help_prompt_service import (
        build_linux_help_markdown_prompt,
        validate_category,
    )
except ModuleNotFoundError:
    from services.linux_help_prompt_service import (
        build_linux_help_markdown_prompt,
        validate_category,
    )


def _controller():
    try:
        from netmon.features import linux_help_controller
    except ModuleNotFoundError:
        from features import linux_help_controller
    return linux_help_controller


def _tr(owner, key, fallback):
    return _controller()._tr(owner, key, fallback)


def _colors(owner, window):
    ctl = _controller()
    apply = ctl._app_value(owner, "_apply_tk_widget_theme")
    palette = ctl._app_value(owner, "_app_theme")
    if callable(apply) and palette:
        apply(window, palette)


def _categories(owner):
    ctl = _controller()
    return sorted(
        {
            str(row.get("category") or "").strip()
            for row in [
                *(ctl._app_value(owner, "linux_help_data", []) or []),
                *(ctl._app_value(owner, "linux_help_glossary", []) or []),
            ]
            if str(row.get("category") or "").strip()
        },
        key=str.casefold,
    )


class MarkdownPromptWindow(tk.Toplevel):
    def __init__(self, parent, owner):
        super().__init__(parent)
        self.owner = owner
        self.base = {}
        self.reference_markdown = ""
        self.prompt = ""
        self.draft = {}
        self.title(
            _tr(owner, "linux_help_prompt_window_title", "Markdown-Prompt erstellen")
        )
        self.geometry("900x800")
        self.minsize(700, 620)
        self.transient(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.kind_labels = {
            "command": _tr(owner, "linux_help_prompt_kind_command", "Befehl"),
            "glossary": _tr(owner, "linux_help_prompt_kind_glossary", "Glossarbegriff"),
        }
        self.kind_var = tk.StringVar(self, value=self.kind_labels["command"])
        self.name_var = tk.StringVar(self)
        self.command_var = tk.StringVar(self)
        self.category_var = tk.StringVar(self)
        self.status = tk.StringVar(self)
        form = ttk.Frame(self, padding=12)
        form.grid(row=0, column=0, sticky="ew")
        form.columnconfigure(1, weight=1)
        for row, (key, label) in enumerate(
            (
                ("linux_help_prompt_template", "Vorlage"),
                ("linux_help_prompt_name", "Name / Begriff"),
                ("linux_help_prompt_command_label", "Befehl"),
                ("linux_help_label_category", "Kategorie"),
            )
        ):
            widget = ttk.Label(form, text=_tr(owner, key, label))
            widget.grid(row=row, column=0, sticky="w", padx=(0, 8), pady=4)
            if row == 2:
                self.command_label = widget
        self.kind_combo = ttk.Combobox(
            form,
            textvariable=self.kind_var,
            values=list(self.kind_labels.values()),
            state="readonly",
        )
        self.kind_combo.grid(row=0, column=1, sticky="ew", pady=4)
        self.selection_button = ttk.Button(
            form,
            text=_tr(owner, "linux_help_prompt_take_selection", "Auswahl übernehmen"),
            command=self.take_selection,
        )
        self.selection_button.grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Entry(form, textvariable=self.name_var).grid(
            row=1, column=1, columnspan=2, sticky="ew", pady=4
        )
        self.command_entry = ttk.Entry(form, textvariable=self.command_var)
        self.command_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)
        self.category_combo = ttk.Combobox(
            form, textvariable=self.category_var, values=_categories(owner)
        )
        self.category_combo.grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)
        wishes_frame = ttk.LabelFrame(
            self,
            text=_tr(owner, "linux_help_prompt_wishes", "Zusätzliche Wünsche"),
            padding=8,
        )
        wishes_frame.grid(row=1, column=0, sticky="ew", padx=12)
        wishes_frame.columnconfigure(0, weight=1)
        self.wishes_text = tk.Text(wishes_frame, height=3, wrap="word", undo=True)
        self.wishes_text.grid(row=0, column=0, sticky="ew")
        build_row = ttk.Frame(self)
        build_row.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
        self.build_button = ttk.Button(
            build_row,
            text=_tr(owner, "linux_help_prompt_build", "Prompt erstellen"),
            command=self.build_prompt,
        )
        self.build_button.pack(side="right")
        preview_frame = ttk.LabelFrame(
            self,
            text=_tr(owner, "linux_help_prompt_preview", "Prompt-Vorschau"),
            padding=8,
        )
        preview_frame.grid(row=3, column=0, sticky="nsew", padx=12)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        self.preview = tk.Text(
            preview_frame, wrap="word", state="disabled", font="TkFixedFont"
        )
        self.preview.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(
            preview_frame, orient="vertical", command=self.preview.yview
        )
        scroll.grid(row=0, column=1, sticky="ns")
        self.preview.configure(yscrollcommand=scroll.set)
        actions = ttk.Frame(self, padding=12)
        actions.grid(row=4, column=0, sticky="ew")
        actions.columnconfigure(2, weight=1)
        self.chad_button = ttk.Button(
            actions,
            text=_tr(owner, "linux_help_prompt_to_chad", "An Chad übergeben"),
            command=self.to_chad,
            state="disabled",
        )
        self.chad_button.grid(row=0, column=0, sticky="w")
        self.copy_button = ttk.Button(
            actions,
            text=_tr(
                owner, "linux_help_prompt_copy_external", "Für externen Chat kopieren"
            ),
            command=self.copy_prompt,
            state="disabled",
        )
        self.copy_button.grid(row=0, column=1, padx=8, sticky="w")
        ttk.Button(
            actions, text=_tr(owner, "btn_close", "Schließen"), command=self.close
        ).grid(row=0, column=2, sticky="e")
        ttk.Label(self, textvariable=self.status, wraplength=670).grid(
            row=5, column=0, sticky="ew", padx=12, pady=(0, 8)
        )
        for variable in (
            self.kind_var,
            self.name_var,
            self.command_var,
            self.category_var,
        ):
            variable.trace_add("write", self.invalidate)
        self.wishes_text.bind("<<Modified>>", self._wishes_changed)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _e: self.close())
        _colors(owner, self)

    def kind(self):
        return (
            "glossary"
            if self.kind_var.get() == self.kind_labels["glossary"]
            else "command"
        )

    def invalidate(self, *_args):
        self.prompt = ""
        self.draft = {}
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.configure(state="disabled")
        self.chad_button.configure(state="disabled")
        self.copy_button.configure(state="disabled")
        self.status.set("")
        if self.kind() == "glossary":
            self.command_label.grid_remove()
            self.command_entry.grid_remove()
        else:
            self.command_label.grid()
            self.command_entry.grid()

    def _wishes_changed(self, _event=None):
        if self.wishes_text.edit_modified():
            self.wishes_text.edit_modified(False)
            self.invalidate()

    def take_selection(self):
        self.invalidate()
        item = _controller()._resolve_linux_help_item(self.owner)
        if item is None:
            self.status.set(
                _tr(
                    self.owner,
                    "linux_help_prompt_no_selection",
                    "Bitte zuerst einen Eintrag in der Liste auswählen.",
                )
            )
            return False
        try:
            document = _controller().load_entry_document(item)
            self.reference_markdown = (
                _controller().split_markdown(document.source)[1] if document else ""
            )
        except (OSError, ValueError, UnicodeError, RecursionError) as exc:
            self.status.set(str(exc))
            return False
        self.base = dict(item)
        self.kind_var.set(
            self.kind_labels[
                "glossary" if item.get("entry_type") == "glossary" else "command"
            ]
        )
        self.name_var.set(item.get("name", ""))
        self.command_var.set(item.get("cmd", ""))
        self.category_var.set(item.get("category", ""))
        return True

    def build_prompt(self):
        ctl = _controller()
        self.wishes_text.edit_modified(False)
        try:
            name = self.name_var.get().strip()
            command = self.command_var.get().strip() if self.kind() == "command" else ""
            if (
                not name
                or len(name) > 256
                or any(not char.isprintable() for char in name)
            ):
                raise ValueError(
                    _tr(
                        self.owner,
                        "linux_help_prompt_name_required",
                        "Bitte einen Namen oder Begriff mit höchstens 256 Zeichen eingeben.",
                    )
                )
            if self.kind() == "command" and (
                not command
                or len(command) > 2048
                or any(not char.isprintable() for char in command)
            ):
                raise ValueError(
                    _tr(
                        self.owner,
                        "linux_help_prompt_command_required",
                        "Bitte einen einzeiligen Befehl mit höchstens 2048 Zeichen eingeben.",
                    )
                )
            category = validate_category(self.category_var.get())
            base = (
                dict(self.base)
                if self.base.get("entry_type", "command") == self.kind()
                else {}
            )
            used = {
                row.get("id")
                for row in [
                    *(ctl._app_value(self.owner, "linux_help_data", []) or []),
                    *(ctl._app_value(self.owner, "linux_help_glossary", []) or []),
                ]
            }
            if base.get("id"):
                used.discard(base["id"])
            identifier = ctl.linux_help_make_id(
                {"id": base.get("id") or name}, existing_ids=used
            )
            self.draft = {
                **base,
                "id": identifier,
                "entry_type": self.kind(),
                "name": name,
                "cmd": command,
                "category": category,
            }
            prompt = build_linux_help_markdown_prompt(
                self.draft,
                wishes=self.wishes_text.get("1.0", "end-1c"),
                reference_markdown=self.reference_markdown if base else "",
            )
        except ValueError as exc:
            self.status.set(str(exc))
            return False
        self.prompt = prompt
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", prompt)
        self.preview.configure(state="disabled")
        self.preview.yview_moveto(0)
        self.chad_button.configure(state="normal")
        self.copy_button.configure(state="normal")
        self.status.set(
            _tr(
                self.owner,
                "linux_help_prompt_ready",
                "Prompt erstellt. Vorschau prüfen und anschließend übergeben oder kopieren.",
            )
        )
        return True

    def copy_prompt(self):
        if not self.prompt:
            return False
        self.clipboard_clear()
        self.clipboard_append(self.prompt)
        self.status.set(
            _tr(
                self.owner,
                "linux_help_prompt_copied",
                "Markdown-Prompt für den externen Chat kopiert.",
            )
        )
        return True

    def to_chad(self):
        if not self.prompt:
            return False
        ctl = _controller()
        title = _tr(
            self.owner, "linux_help_prompt_chad_title", "Markdown-Dokumentation: {name}"
        ).format(name=self.draft["name"])
        ctl.deliver_linux_help_markdown_prompt(self.owner, title, self.prompt)
        self.status.set(
            _tr(
                self.owner,
                "linux_help_prompt_prepared",
                "Markdown-Auftrag in Chad vorbereitet.",
            )
        )
        return True

    def close(self):
        if vars(self.owner).get("linux_help_prompt_window") is self:
            vars(self.owner).pop("linux_help_prompt_window", None)
        self.destroy()


class ImportCategoryDialog(simpledialog.Dialog):
    def __init__(self, parent, owner, raw):
        self.owner, self.raw = owner, dict(raw)
        self.result = None
        super().__init__(
            parent,
            _tr(owner, "linux_help_import_check_title", "Markdown-Import prüfen"),
        )

    def body(self, master):
        master.columnconfigure(1, weight=1)
        labels = (
            (
                _tr(self.owner, "linux_help_prompt_name", "Name / Begriff"),
                self.raw["name"],
            ),
            (
                _tr(self.owner, "linux_help_prompt_template", "Vorlage"),
                (
                    _tr(self.owner, "linux_help_prompt_kind_glossary", "Glossarbegriff")
                    if self.raw["entry_type"] == "glossary"
                    else _tr(self.owner, "linux_help_prompt_kind_command", "Befehl")
                ),
            ),
        )
        for row, (label, value) in enumerate(labels):
            ttk.Label(master, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=4
            )
            ttk.Label(master, text=value, wraplength=400).grid(
                row=row, column=1, sticky="w", pady=4
            )
        ttk.Label(
            master, text=_tr(self.owner, "linux_help_label_category", "Kategorie")
        ).grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        self.category_var = tk.StringVar(self, value=self.raw.get("category", ""))
        self.category_combo = ttk.Combobox(
            master,
            textvariable=self.category_var,
            values=_categories(self.owner),
            width=44,
        )
        self.category_combo.grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(
            master,
            text=_tr(
                self.owner,
                "linux_help_import_category_hint",
                "Kategorie aus der Datei prüfen und bei Bedarf ändern.",
            ),
            wraplength=480,
        ).grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.status = tk.StringVar(self)
        ttk.Label(master, textvariable=self.status, wraplength=480).grid(
            row=4, column=0, columnspan=2, sticky="w"
        )
        _colors(self.owner, self)
        return self.category_combo

    def validate(self):
        try:
            validate_category(self.category_var.get())
        except ValueError as exc:
            self.status.set(str(exc))
            return False
        return True

    def buttonbox(self):
        box = ttk.Frame(self, padding=8)
        ttk.Button(
            box,
            text=_tr(self.owner, "btn_continue", "Weiter"),
            command=self.ok,
            default="active",
        ).pack(side="left", padx=4)
        ttk.Button(
            box, text=_tr(self.owner, "btn_cancel", "Abbrechen"), command=self.cancel
        ).pack(side="left", padx=4)
        box.pack()
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        _colors(self.owner, self)

    def apply(self):
        self.result = {
            **self.raw,
            "category": validate_category(self.category_var.get()),
        }
