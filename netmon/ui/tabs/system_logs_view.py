"""System-Logs sub-tab: read-only Linux logs, anonymised hand-over to Chad.

Logs are read in a worker thread (never in the Tk main thread) and only when
the user opens the sub-tab or presses refresh. Nothing is sent anywhere
automatically: the Chad button shows the anonymised text first.
"""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk

try:
    from netmon.core import system_logs
except ModuleNotFoundError:  # pragma: no cover - legacy flat layout
    from core import system_logs

RANGE_LABELS = (
    ("boot", "Dieser Start"),
    ("previous", "Letzter Start"),
    ("hour", "Letzte Stunde"),
    ("today", "Heute"),
)
ERROR_WORDS = ("error", "fail", "critical", "panic", "segfault", "denied", "fehler")
WARNING_WORDS = ("warn", "timeout", "unable", "could not", "block")


def _tr(app, key, default):
    translate = getattr(app, "tr", None)
    try:
        return translate(key, default) if callable(translate) else default
    except Exception:
        return default


class SystemLogsView:
    def __init__(self, app, parent):
        self.app = app
        self.generation = 0
        self.loaded_once = False
        self.raw_text = ""
        self.source_key = system_logs.SOURCES[0].key
        self.loaded_key = None  # source of the text currently shown (snapshot)
        self.preview = None
        self._worker_busy = False  # at most one reader thread at a time
        self._pending = False  # a newer request waits for the running one

        self.frame = ttk.Frame(parent, padding=(0, 8, 0, 0))
        top = ttk.Frame(self.frame)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text=_tr(app, "syslogs_range", "Zeitraum:")).pack(side="left")
        self.range_var = tk.StringVar(self.frame, RANGE_LABELS[0][1])
        self.range_box = ttk.Combobox(
            top,
            textvariable=self.range_var,
            values=[label for _key, label in RANGE_LABELS],
            state="readonly",
            width=14,
        )
        self.range_box.pack(side="left", padx=(4, 12))
        ttk.Label(top, text=_tr(app, "syslogs_lines", "Zeilen:")).pack(side="left")
        self.lines_var = tk.StringVar(self.frame, str(system_logs.DEFAULT_LINES))
        self.lines_box = ttk.Combobox(
            top,
            textvariable=self.lines_var,
            values=[str(n) for n in system_logs.LINE_CHOICES],
            state="readonly",
            width=6,
        )
        self.lines_box.pack(side="left", padx=(4, 12))
        ttk.Label(top, text=_tr(app, "syslogs_filter", "Filter:")).pack(side="left")
        self.filter_var = tk.StringVar(self.frame, "")
        self.filter_entry = ttk.Entry(top, textvariable=self.filter_var, width=22)
        self.filter_entry.pack(side="left", padx=(4, 12))
        self.filter_var.trace_add("write", lambda *_: self._render())
        self.btn_refresh = ttk.Button(
            top, text=_tr(app, "syslogs_refresh", "Aktualisieren"), command=self.refresh
        )
        self.btn_refresh.pack(side="left")
        self.btn_chad = ttk.Button(
            top,
            text=_tr(app, "syslogs_chad", "Mit Chad analysieren…"),
            command=self.open_chad_preview,
        )
        self.btn_chad.pack(side="right")
        self.btn_copy = ttk.Button(
            top, text=_tr(app, "syslogs_copy", "Kopieren"), command=self.copy_text
        )
        self.btn_copy.pack(side="right", padx=(0, 6))
        self.range_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())
        self.lines_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        body = ttk.Frame(self.frame)
        body.pack(fill="both", expand=True)
        self.sources = tk.Listbox(body, exportselection=False, width=26, height=8)
        for source in system_logs.SOURCES:
            self.sources.insert("end", source.label)
        self.sources.selection_set(0)
        self.sources.bind("<<ListboxSelect>>", self._source_selected)
        self.sources.pack(side="left", fill="y", padx=(0, 6))
        text_frame = ttk.Frame(body)
        text_frame.pack(side="left", fill="both", expand=True)
        text_frame.grid_rowconfigure(0, weight=1)
        text_frame.grid_columnconfigure(0, weight=1)
        scroll_y = ttk.Scrollbar(text_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(text_frame, orient="horizontal")
        self.text = tk.Text(
            text_frame,
            wrap="none",
            font=("Courier", 10),
            yscrollcommand=scroll_y.set,
            xscrollcommand=scroll_x.set,
        )
        self.text.grid(row=0, column=0, sticky="nsew")
        scroll_y.configure(command=self.text.yview)
        scroll_x.configure(command=self.text.xview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")
        self.text.tag_configure("error", foreground="#c62828")
        self.text.tag_configure("warning", foreground="#b26a00")
        self.text.bind("<Key>", self._read_only_key)
        self.text.bind("<<Paste>>", lambda _e: "break")
        self.text.bind("<<Cut>>", lambda _e: "break")

        self.status_var = tk.StringVar(
            self.frame,
            _tr(
                app,
                "syslogs_hint",
                "Nur lesen. Wird beim Öffnen geladen; nichts wird automatisch gesendet.",
            ),
        )
        ttk.Label(self.frame, textvariable=self.status_var, anchor="w").pack(
            fill="x", pady=(6, 0)
        )

    # ── loading ─────────────────────────────────────────────────────────────

    @staticmethod
    def _read_only_key(event):
        if event.state & 0x4 and event.keysym.lower() in {"c", "a"}:
            return None  # allow copy / select all
        return "break"

    def _range_key(self):
        label = self.range_var.get()
        return next(
            (k for k, v in RANGE_LABELS if v == label), system_logs.DEFAULT_RANGE
        )

    def _lines(self):
        try:
            value = int(self.lines_var.get())
        except ValueError:
            return system_logs.DEFAULT_LINES
        return value if value in system_logs.LINE_CHOICES else system_logs.DEFAULT_LINES

    def _source_selected(self, _event=None):
        selection = self.sources.curselection()
        if selection:
            self.source_key = system_logs.SOURCES[selection[0]].key
            # Files are shown as their end; the time range applies to journals only.
            self.range_box.configure(
                state=(
                    "disabled"
                    if system_logs.is_file_source(self.source_key)
                    else "readonly"
                )
            )
            self.refresh()

    def on_shown(self):
        """Load lazily the first time the sub-tab becomes visible."""
        if not self.loaded_once:
            self.refresh()

    def refresh(self):
        self.loaded_once = True
        self.generation += 1
        self.status_var.set(_tr(self.app, "syslogs_loading", "Wird geladen …"))
        if self._worker_busy:
            # Never stack readers: the running one finishes, then only the
            # newest request is read (older clicks are coalesced).
            self._pending = True
            return self.generation
        self._start(self.generation)
        return self.generation

    def _start(self, generation):
        key, range_key, lines = self.source_key, self._range_key(), self._lines()
        results = {}
        self._worker_busy = True

        def work():
            # Worker touches no Tk object; the Tk thread polls for the result.
            try:
                results["value"] = system_logs.read_source(key, range_key, lines)
            except Exception as exc:
                results["value"] = (False, f"Fehler beim Lesen: {type(exc).__name__}")

        def poll():
            if not self._alive():
                return
            if "value" not in results:
                self.frame.after(50, poll)
                return
            self._worker_busy = False
            if self._pending or generation != self.generation:
                self._pending = False
                self._start(self.generation)
                return
            ok, text = results["value"]
            self._deliver(generation, key, ok, text)

        threading.Thread(target=work, name="system-logs", daemon=True).start()
        self.frame.after(50, poll)

    def _deliver(self, generation, key, ok, text):
        if generation != self.generation or not self._alive():
            return False  # a newer request or a closed view wins
        self.raw_text = text
        self.loaded_key = key  # text and its source are published together
        self._render()
        label = system_logs.resolve_source(key).label
        lines = len(text.splitlines())
        note = (
            " · "
            + _tr(
                self.app,
                "syslogs_file_tail",
                "Dateiende – der Zeitraum gilt nur für Journal-Quellen",
            )
            if system_logs.is_file_source(key)
            else ""
        )
        self.status_var.set(
            f"{label}: {lines} Zeilen" + ("" if ok else " – mit Hinweis/Fehler") + note
        )
        return True

    def _alive(self):
        try:
            return bool(self.frame.winfo_exists())
        except tk.TclError:
            return False

    def _filtered_lines(self):
        needle = self.filter_var.get().strip().lower()
        rows = self.raw_text.splitlines()
        return [row for row in rows if needle in row.lower()] if needle else rows

    def _render(self):
        self.text.delete("1.0", "end")
        for row in self._filtered_lines():
            lowered = row.lower()
            tag = (
                "error"
                if any(word in lowered for word in ERROR_WORDS)
                else "warning" if any(word in lowered for word in WARNING_WORDS) else ""
            )
            self.text.insert("end", row + "\n", tag)
        self.text.see("end")

    # ── actions ─────────────────────────────────────────────────────────────

    def current_text(self):
        try:
            selected = self.text.get("sel.first", "sel.last")
        except tk.TclError:
            selected = ""
        return selected.strip() or "\n".join(self._filtered_lines())

    def copy_text(self):
        text = self.current_text()
        if text:
            self.app.clipboard_clear()
            self.app.clipboard_append(text)

    def open_chad_preview(self):
        text = self.current_text()
        if not text.strip():
            self.status_var.set(
                _tr(self.app, "syslogs_empty", "Kein Log-Text vorhanden.")
            )
            return None
        anonymized, counts = system_logs.anonymize_for_ai(text)
        anonymized, truncated = system_logs.truncate_for_ai(anonymized)
        # Label from the snapshot actually shown, not from a pending selection.
        label = (
            system_logs.resolve_source(self.loaded_key).label
            if self.loaded_key
            else "System-Log"
        )
        if self.preview is not None:
            try:
                self.preview.destroy()
            except tk.TclError:
                pass
        window = tk.Toplevel(self.frame)
        window.title(
            _tr(self.app, "syslogs_preview_title", "Vorschau für Chad (anonymisiert)")
        )
        window.geometry("820x520")
        summary = ", ".join(
            f"{kind}: {count}" for kind, count in sorted(counts.items())
        )
        info = _tr(
            self.app,
            "syslogs_preview_info",
            "Ersetzt: {summary}. Bitte prüfen – nur dieser Text wird an Chad übergeben.",
        ).format(summary=summary or "nichts")
        if truncated:
            info += " " + _tr(
                self.app, "syslogs_truncated", "Gekürzt auf die neuesten Zeilen."
            )
        ttk.Label(window, text=info, wraplength=780, justify="left").pack(
            fill="x", padx=10, pady=(10, 4)
        )
        preview = tk.Text(window, wrap="none", font=("Courier", 10))
        preview.insert("1.0", anonymized)
        preview.configure(state="disabled")
        preview.pack(fill="both", expand=True, padx=10)
        buttons = ttk.Frame(window)
        buttons.pack(fill="x", padx=10, pady=10)

        def hand_over():
            self.app.prepare_chad_analysis(f"System-Log: {label}", anonymized)
            window.destroy()
            self.preview = None
            self.status_var.set(
                _tr(
                    self.app,
                    "syslogs_handed_over",
                    "Anonymisiert an den Chad-Tab übergeben.",
                )
            )

        ttk.Button(
            buttons,
            text=_tr(self.app, "syslogs_hand_over", "An Chad übergeben"),
            command=hand_over,
        ).pack(side="right")
        ttk.Button(
            buttons,
            text=_tr(self.app, "syslogs_cancel", "Abbrechen"),
            command=window.destroy,
        ).pack(side="right", padx=(0, 6))
        window.preview_text = anonymized
        window.hand_over = hand_over
        self.preview = window
        return window


def build_system_logs_view(app, parent):
    view = SystemLogsView(app, parent)
    app.system_logs_view = view
    return view
