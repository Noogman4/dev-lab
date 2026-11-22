"""Native, read-only Linux-help Markdown reader; no HTML/browser rendering."""

from __future__ import annotations

from bisect import bisect_right
import re
import subprocess
import tkinter as tk
from tkinter import font as tkfont, messagebox, ttk

try:
    from netmon.services.linux_help_glossary_service import linked_glossary_id
    from netmon.services.linux_help_markdown_service import source_url
except ModuleNotFoundError:
    from services.linux_help_glossary_service import linked_glossary_id
    from services.linux_help_markdown_service import source_url

INLINE = re.compile(r"(`[^`\n]+`|\*\*[^*\n]+\*\*|(?<!!)\[[^]\n]+\]\([^()\s]+\))")


class LinuxHelpReader(ttk.Frame):
    def __init__(
        self, parent, *, tr=None, allow_popout=True, source_validator=source_url
    ):
        super().__init__(parent)
        self.tr = tr or (lambda _key, fallback: fallback)
        self.source_validator = source_validator
        self.document = None
        self.entry = {}
        self.on_glossary_link = None
        self.embedded = []
        self.cells = []
        self.code_buttons = []
        self.links = []
        self.headings = []
        self.matches = []
        self.match_position = -1
        self.size = 11
        self.normal_font = tkfont.Font(self, font="TkDefaultFont")
        self.bold_font = self.normal_font.copy()
        self.code_font = tkfont.Font(self, font="TkFixedFont")
        self.heading_fonts = [self.normal_font.copy() for _ in range(3)]
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self.info = tk.StringVar(master=self)
        self.status = tk.StringVar(master=self)
        self.query = tk.StringVar(master=self)
        ttk.Label(self, textvariable=self.info, wraplength=850, justify="left").grid(
            row=0, column=0, sticky="ew", pady=(0, 5)
        )
        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        self.contents = ttk.Combobox(toolbar, state="readonly", width=32)
        self.contents.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.contents.bind("<<ComboboxSelected>>", self.jump_to_section)
        for column, (label, action) in enumerate(
            [("A−", lambda: self.change_font(-1)), ("A+", lambda: self.change_font(1))],
            1,
        ):
            ttk.Button(toolbar, text=label, width=3, command=action).grid(
                row=0, column=column, padx=2
            )
        self.popout = ttk.Button(
            toolbar,
            text=self.tr("linux_help_reader_window", "Lesefenster öffnen"),
            command=self.open_window,
        )
        if allow_popout:
            self.popout.grid(row=0, column=3, padx=(6, 0))
        search = ttk.Frame(self)
        search.grid(row=2, column=0, sticky="ew", pady=5)
        search.columnconfigure(0, weight=1)
        entry = ttk.Entry(search, textvariable=self.query)
        entry.grid(row=0, column=0, sticky="ew")
        entry.bind("<Return>", lambda _event: self.find_next())
        ttk.Button(
            search, text=self.tr("linux_help_reader_find", "Suchen"), command=self.find
        ).grid(row=0, column=1, padx=4)
        ttk.Button(search, text="‹", width=3, command=lambda: self.find_next(-1)).grid(
            row=0, column=2
        )
        ttk.Button(search, text="›", width=3, command=self.find_next).grid(
            row=0, column=3
        )
        viewport = ttk.Frame(self)
        viewport.grid(row=3, column=0, sticky="nsew")
        viewport.columnconfigure(0, weight=1)
        viewport.rowconfigure(0, weight=1)
        self.text = tk.Text(viewport, wrap="word", height=12, padx=12, pady=10, bd=0)
        self.text.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(viewport, orient="vertical", command=self.text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.bind("<Configure>", self._resize_windows)
        self.bind("<<ThemeChanged>>", self._theme_changed)
        ttk.Label(self, textvariable=self.status, anchor="w", wraplength=700).grid(
            row=4, column=0, sticky="ew", pady=(3, 0)
        )
        self._update_fonts()
        self.show_empty()

    def show_empty(self, message=""):
        self.set_document(None)
        self.info.set(
            message
            or self.tr(
                "linux_help_reader_missing",
                "Noch keine ausführliche Markdown-Dokumentation vorhanden. Die Kurzinfo bleibt verfügbar.",
            )
        )

    def set_document(self, document, entry=None):
        for widget, tag, bindings in self.links:
            for sequence, binding in bindings:
                widget.tag_unbind(tag, sequence, binding)
            widget.tag_delete(tag)
        self.links.clear()
        for widget, _mark in self.embedded:
            widget.destroy()
        self.embedded.clear()
        self.cells.clear()
        self.code_buttons.clear()
        self.headings.clear()
        self.matches.clear()
        self.match_position = -1
        self.searched_query = ""
        self.document = document
        self.entry = dict(entry or {})
        self.query.set("")
        self.status.set("")
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        for mark in self.text.mark_names():
            if mark.startswith(("section_", "window_")):
                self.text.mark_unset(mark)
        self.popout.configure(state="normal" if document else "disabled")
        if document:
            meta = document.metadata
            if meta.get("entry_type") == "glossary":
                kind = self.tr("linux_help_reader_glossary", "Glossarbegriff")
                self.info.set(f"{meta['name']} · {meta['category']} · {kind}")
            elif meta.get("entry_type") == "reference":
                self.info.set(meta["name"])
            else:
                self._command_info(meta)
            self._render_blocks(document)
        self.contents.configure(values=[title for title, _mark in self.headings])
        self.contents.set(self.tr("linux_help_reader_contents", "Inhaltsverzeichnis"))
        self.text.configure(state="disabled")
        self.text.yview_moveto(0)
        self._apply_theme()
        self._resize_windows()

    def _command_info(self, meta):
        risk = {
            "safe": self.tr("linux_help_reader_safe", "überwiegend lesend"),
            "caution": self.tr(
                "linux_help_reader_caution", "funktionsabhängig – mit Vorsicht"
            ),
            "danger": self.tr("linux_help_reader_danger", "gefährlich"),
        }[meta["risk_level"]]
        root = (
            self.tr("label_yes", "Ja")
            if meta["root_required"]
            else self.tr("label_no", "Nein")
        )
        self.info.set(f"{meta['name']} · {meta['category']} · Root: {root} · {risk}")
        if self.entry.get("risk") and self.entry["risk"] != meta["risk_level"]:
            self.status.set(
                self.tr(
                    "linux_help_reader_risk_difference",
                    "Hinweis: Die Risikoeinstufung der bisherigen Kurzinfo weicht von dieser Dokumentation ab.",
                )
            )

    def _render_blocks(self, document):
        for block in document.blocks:
            if block.kind == "heading":
                mark = f"section_{len(self.headings)}_{self.text.index('end-1c')}"
                self.text.mark_set(mark, "end-1c")
                self.text.mark_gravity(mark, "left")
                if block.level == 2:
                    self.headings.append((block.text, mark))
                self._inline(self.text, block.text, (f"h{min(3, block.level)}",))
                self.text.insert("end", "\n\n")
            elif block.kind == "table":
                self._table(block.rows)
            elif block.kind == "code":
                button = ttk.Button(
                    self.text,
                    text=self.tr("linux_help_reader_copy", "Code kopieren"),
                    command=lambda code=block.text: self.copy_code(code),
                )
                self.code_buttons.append(button)
                self._window(button, stretch=False)
                self.text.insert("end", block.text + "\n\n", "code")
            else:
                line = re.sub(r"^\s*- ", "• ", block.text)
                self._inline(self.text, line)
                self.text.insert("end", "\n\n")

    def _inline(self, widget, text, tags=()):
        position = 0
        for match in INLINE.finditer(text):
            widget.insert("end", text[position : match.start()], tags)
            token = match[0]
            if token.startswith("`"):
                widget.insert("end", token[1:-1], (*tags, "inline_code"))
            elif token.startswith("**"):
                widget.insert("end", token[2:-2], (*tags, "bold"))
            else:
                label, url = token[1:-1].split("](", 1)
                identifier = self._glossary_target(url)
                if identifier or self.source_validator(url):
                    tag = f"source_{len(self.links)}"
                    widget.tag_configure(tag, foreground=self._accent(), underline=True)
                    binding = widget.tag_bind(
                        tag,
                        "<Button-1>",
                        lambda _e, target=url: self.open_link(target),
                    )
                    hover = widget.tag_bind(
                        tag, "<Enter>", lambda _e, target=url: self.status.set(target)
                    )
                    self.links.append(
                        (widget, tag, [("<Button-1>", binding), ("<Enter>", hover)])
                    )
                    widget.insert("end", label, (*tags, tag))
                else:
                    widget.insert("end", f"{label} ({url})", tags)
            position = match.end()
        widget.insert("end", text[position:], tags)

    def _glossary_target(self, url):
        if (
            not callable(self.on_glossary_link)
            or self.document is None
            or self.document.metadata.get("entry_type") != "glossary"
        ):
            return ""
        try:
            return linked_glossary_id(url)
        except (OSError, ValueError, RecursionError):
            return ""

    def open_link(self, url):
        identifier = self._glossary_target(url)
        if identifier:
            return self.on_glossary_link(identifier)
        return self.open_source(url)

    def _window(self, widget, *, stretch=True):
        mark = f"window_{len(self.embedded)}"
        self.text.mark_set(mark, "end-1c")
        self.text.mark_gravity(mark, "left")
        self.text.window_create("end", window=widget, stretch=stretch)
        self.text.insert("end", "\n")
        self.embedded.append((widget, mark))
        return mark

    def _table(self, rows):
        frame = ttk.Frame(self.text)
        frame.grid_propagate(False)
        mark = self._window(frame)
        for column in range(len(rows[0])):
            frame.columnconfigure(column, weight=1, uniform="cells")
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                cell = tk.Text(
                    frame,
                    width=1,
                    height=1,
                    wrap="word",
                    padx=6,
                    pady=5,
                    bd=1,
                    relief="solid",
                )
                cell.grid(row=row, column=column, sticky="nsew")
                self._inline(cell, value, ("bold",) if row == 0 else ())
                cell.configure(state="disabled")
                self.cells.append((cell, mark))
                cell.bind("<Configure>", lambda event: self._fit_cell(event.widget))
                cell.bind(
                    "<MouseWheel>", lambda e: self._scroll(-1 if e.delta > 0 else 1)
                )
                cell.bind("<Button-4>", lambda _e: self._scroll(-1))
                cell.bind("<Button-5>", lambda _e: self._scroll(1))
        self.text.insert("end", "\n")

    def _scroll(self, direction):
        self.text.yview_scroll(direction * 3, "units")
        return "break"

    def _fit_cell(self, cell):
        if cell.winfo_width() < 10:
            return
        count = cell.count("1.0", "end", "displaylines")
        height = max(1, count[0] if count else 1)
        if int(cell.cget("height")) != height:
            cell.configure(height=height)
        row_heights = {}
        for sibling in cell.master.winfo_children():
            row = int(sibling.grid_info()["row"])
            row_heights[row] = max(row_heights.get(row, 0), sibling.winfo_reqheight())
        cell.master.configure(height=sum(row_heights.values()))

    def _resize_windows(self, _event=None):
        width = max(240, self.text.winfo_width() - 32)
        for widget, mark in self.embedded:
            if isinstance(widget, ttk.Frame):
                widget.configure(width=width)
        for cell, _mark in self.cells:
            self._fit_cell(cell)

    def _update_fonts(self):
        self.normal_font.configure(size=self.size)
        self.bold_font.configure(size=self.size, weight="bold")
        self.code_font.configure(size=self.size)
        for level, font in enumerate(self.heading_fonts, 1):
            font.configure(size=self.size + 7 - 2 * level, weight="bold")

    def change_font(self, delta):
        self.size = min(22, max(9, self.size + delta))
        self._update_fonts()
        self._resize_windows()

    def _accent(self):
        return ttk.Style(self).lookup("TLabel", "foreground") or "#1b5599"

    def _theme_changed(self, _event=None):
        self._apply_theme()

    def _apply_theme(self):
        style = ttk.Style(self)
        bg = style.lookup("TFrame", "background") or "#ffffff"
        fg = style.lookup("TLabel", "foreground") or "#101010"
        rgb_bg, rgb_fg = self.winfo_rgb(bg), self.winfo_rgb(fg)
        code_bg = "#" + "".join(
            f"{int(a * .92 + b * .08) // 256:02x}" for a, b in zip(rgb_bg, rgb_fg)
        )
        for widget in [self.text, *(cell for cell, _mark in self.cells)]:
            widget.configure(
                background=bg, foreground=fg, insertbackground=fg, font=self.normal_font
            )
            widget.tag_configure("bold", font=self.bold_font)
            widget.tag_configure("inline_code", font=self.code_font, background=code_bg)
            widget.tag_configure(
                "code", font=self.code_font, background=code_bg, lmargin1=8, lmargin2=8
            )
            widget.tag_configure(
                "search_hit", background="#f3ca52", foreground="#101010"
            )
            for level, font in enumerate(self.heading_fonts, 1):
                widget.tag_configure(f"h{level}", font=font)
        for widget, tag, _binding in self.links:
            widget.tag_configure(tag, foreground=fg, underline=True)

    def copy_code(self, code):
        self.clipboard_clear()
        self.clipboard_append(code.rstrip("\n"))
        self.status.set(
            self.tr(
                "linux_help_reader_copied", "Code kopiert. Es wurde nichts ausgeführt."
            )
        )

    def jump_to_section(self, _event=None):
        index = self.contents.current()
        if 0 <= index < len(self.headings):
            self.text.yview(self.headings[index][1])

    def find(self):
        self.matches.clear()
        self.match_position = -1
        query = self.query.get()
        self.searched_query = query
        pattern = (
            re.compile(re.escape(query), re.IGNORECASE)
            if 0 < len(query) <= 256
            else None
        )
        for widget, mark in [(self.text, None), *self.cells]:
            widget.tag_remove("search_hit", "1.0", "end")
            if pattern is None or len(self.matches) == 500:
                continue
            # Tk 8.6 can crash when searching formatted text containing emoji.
            content = widget.get("1.0", "end-1c")
            line_starts = [
                0,
                *(newline.end() for newline in re.finditer("\n", content)),
            ]
            for match in pattern.finditer(content):
                positions = []
                for offset in match.span():
                    line = bisect_right(line_starts, offset)
                    prefix = content[line_starts[line - 1] : offset]
                    column = self.tk.call("string", "length", prefix)
                    positions.append(f"{line}.{column}")
                start, end = positions
                widget.tag_add("search_hit", start, end)
                self.matches.append((widget, start, mark))
                if len(self.matches) == 500:
                    break
        self.matches.sort(
            key=lambda match: tuple(
                int(part) for part in self.text.index(match[2] or match[1]).split(".")
            )
        )
        self._show_match(1)

    def find_next(self, direction=1):
        if self.query.get() != self.searched_query:
            self.find()
        else:
            self._show_match(direction)

    def _show_match(self, direction):
        if not self.matches:
            self.status.set(self.tr("linux_help_reader_no_match", "Keine Treffer."))
            return
        if self.match_position < 0:
            self.match_position = 0 if direction > 0 else len(self.matches) - 1
        else:
            self.match_position = (self.match_position + direction) % len(self.matches)
        widget, found, mark = self.matches[self.match_position]
        self.text.see(mark if mark else found)
        widget.see(found)
        self.status.set(f"{self.match_position + 1} / {len(self.matches)}")

    def open_source(self, url):
        from netmon.features.web_browser_controller import route_if_enabled

        if not self.source_validator(url):
            return False
        protected = route_if_enabled(self._root(), url)
        if protected is not None:
            return protected
        for argv in (["/usr/bin/xdg-open", url], ["/usr/bin/gio", "open", url]):
            try:
                subprocess.Popen(
                    argv,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return True
            except OSError:
                continue
        messagebox.showerror(
            self.tr("linux_help_reader_sources", "Quelle"),
            self.tr(
                "linux_help_reader_browser_failed",
                "Browser konnte nicht gestartet werden. Adresse: {url}",
            ).format(url=url),
            parent=self.winfo_toplevel(),
        )
        return False

    def open_window(self):
        if self.document is None:
            return None
        return open_reader_window(
            self,
            tr=self.tr,
            document=self.document,
            entry=self.entry,
            on_glossary_link=self.on_glossary_link,
        )


def _style_short_info(window):
    style = ttk.Style(window)
    window.short_info.configure(
        font=window.reader.normal_font,
        background=style.lookup("TFrame", "background") or "#ffffff",
        foreground=style.lookup("TLabel", "foreground") or "#101010",
    )


def set_reader_reading_state(window, state):
    window.reading_state = dict(state or {"read": False})
    window.read_var.set(window.reading_state["read"])
    saved = bool(window.reading_state.get("bookmark"))
    enabled = callable(window.on_reading_change)
    window.bookmark_button.configure(
        text=(
            window.reader.tr("linux_help_bookmark_update", "★ Aktualisieren")
            if saved
            else window.reader.tr("linux_help_bookmark_set", "☆ Lesezeichen setzen")
        ),
        state="normal" if enabled else "disabled",
    )
    for button in (window.bookmark_jump_button, window.bookmark_remove_button):
        button.configure(state="normal" if enabled and saved else "disabled")
    window.read_button.configure(state="normal" if enabled else "disabled")


def _change_reading(window, **changes):
    result = (
        window.on_reading_change(**changes)
        if callable(window.on_reading_change)
        else None
    )
    if result is None:
        window.read_var.set(window.reading_state["read"])
        window.reading_status.set(
            window.reader.tr(
                "linux_help_reading_failed",
                "Lesestatus konnte nicht gespeichert werden.",
            )
        )
        return False
    set_reader_reading_state(window, result)
    window.reading_status.set("")
    return True


def _save_bookmark(window):
    documentation = window.notebook.select() == str(window.reader)
    if documentation and window.reader.document is None:
        window.reading_status.set(
            window.reader.tr(
                "linux_help_bookmark_unavailable",
                "Die Dokumentation ist derzeit nicht verfügbar. Das Lesezeichen bleibt erhalten.",
            )
        )
        return
    widget = window.reader.text if documentation else window.short_info
    _change_reading(
        window,
        bookmark={
            "tab": "documentation" if documentation else "short_info",
            "position": widget.yview()[0],
        },
    )


def _jump_to_bookmark(window):
    bookmark = window.reading_state.get("bookmark")
    if bookmark is None:
        return
    documentation = bookmark["tab"] == "documentation"
    if documentation and window.reader.document is None:
        window.reading_status.set(
            window.reader.tr(
                "linux_help_bookmark_unavailable",
                "Die Dokumentation ist derzeit nicht verfügbar. Das Lesezeichen bleibt erhalten.",
            )
        )
        return
    window.notebook.select(window.reader if documentation else window.short_frame)
    window.update_idletasks()
    widget = window.reader.text if documentation else window.short_info
    widget.yview_moveto(bookmark["position"])
    window.reading_status.set("")


def open_reader_window(
    parent,
    *,
    document=None,
    entry=None,
    short_info="",
    error_message="",
    tr=None,
    window=None,
    reading_state=None,
    on_reading_change=None,
    on_glossary_link=None,
):
    """The existing reading window, now with quick-reference/documentation tabs."""
    tr = tr or (lambda _key, fallback: fallback)
    item = dict(entry or {})
    if window is None:
        window = tk.Toplevel(parent)
        # A normal window keeps the desktop's maximize controls available.
        window.resizable(True, True)
        window.geometry("1100x800")
        window.minsize(650, 400)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(0, weight=1)
        window.notebook = ttk.Notebook(window)
        window.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 0))
        window.short_frame = ttk.Frame(window.notebook, padding=10)
        window.short_frame.columnconfigure(0, weight=1)
        window.short_frame.rowconfigure(0, weight=1)
        window.notebook.add(
            window.short_frame, text=tr("linux_help_short_info", "Kurzinfo")
        )
        window.short_info = tk.Text(
            window.short_frame, wrap="word", padx=10, pady=10, bd=0
        )
        window.short_info.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            window.short_frame, orient="vertical", command=window.short_info.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        window.short_info.configure(yscrollcommand=scrollbar.set)
        window.reader = LinuxHelpReader(window.notebook, tr=tr, allow_popout=False)
        window.notebook.add(
            window.reader, text=tr("linux_help_reader_title", "Dokumentation")
        )
        window.short_frame.bind(
            "<<ThemeChanged>>", lambda _event: _style_short_info(window)
        )
        footer = ttk.Frame(window)
        footer.grid(row=1, column=0, sticky="ew", padx=10, pady=8)
        footer.columnconfigure(0, weight=1)
        window.reading_controls = ttk.Frame(footer)
        window.reading_controls.grid(row=0, column=0, sticky="w")
        window.bookmark_button = ttk.Button(
            window.reading_controls, command=lambda: _save_bookmark(window)
        )
        window.bookmark_button.grid(row=0, column=0, padx=(0, 4))
        window.bookmark_jump_button = ttk.Button(
            window.reading_controls,
            text=tr("linux_help_bookmark_jump", "Zum Lesezeichen"),
            command=lambda: _jump_to_bookmark(window),
        )
        window.bookmark_jump_button.grid(row=0, column=1, padx=4)
        window.bookmark_remove_button = ttk.Button(
            window.reading_controls,
            text=tr("linux_help_bookmark_remove", "Entfernen"),
            command=lambda: _change_reading(window, bookmark=None),
        )
        window.bookmark_remove_button.grid(row=0, column=2, padx=4)
        window.read_var = tk.BooleanVar(master=window)
        window.read_button = ttk.Checkbutton(
            window.reading_controls,
            text=tr("linux_help_reading_read", "Gelesen"),
            variable=window.read_var,
            command=lambda: _change_reading(window, read=window.read_var.get()),
        )
        window.read_button.grid(row=0, column=3, padx=(8, 4))
        ttk.Button(
            footer, text=tr("btn_close", "Schließen"), command=window.destroy
        ).grid(row=0, column=1, sticky="e", padx=(8, 0))
        window.reading_status = tk.StringVar(master=window)
        ttk.Label(footer, textvariable=window.reading_status, wraplength=620).grid(
            row=1, column=0, columnspan=2, sticky="w"
        )
        window.bind("<Escape>", lambda _event: window.destroy())
    title = item.get("name") or (document.metadata["name"] if document else "Linux")
    window.title(title + " – " + tr("linux_help_reader_title", "Dokumentation"))
    window.entry = item
    window.on_reading_change = on_reading_change
    window.reading_status.set("")
    set_reader_reading_state(window, reading_state)
    window.short_info.configure(state="normal")
    window.short_info.delete("1.0", "end")
    window.short_info.insert("1.0", short_info or item.get("info") or title)
    window.short_info.configure(state="disabled")
    _style_short_info(window)
    window.reader.on_glossary_link = on_glossary_link
    if document:
        window.reader.set_document(document, item)
        window.notebook.select(window.reader)
    else:
        window.reader.show_empty(error_message)
        window.notebook.select(window.short_frame)
    window.deiconify()
    window.lift()
    return window
