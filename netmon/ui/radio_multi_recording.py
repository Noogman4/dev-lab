"""Recording selection and live snapshots, without Tk-thread process waits."""

import tkinter as tk
from tkinter import ttk

from netmon.core.radio_multi_recording import OUTPUT_BYTES_SECOND, saved_settings
from netmon.features import radio_multi_recording_controller as controller

STATUS = {
    "ready": ("radio_multi_status_ready", "Bereit"),
    "checking": ("radio_multi_status_checking", "Wird geprüft"),
    "recording": ("radio_multi_status_recording", "Aufnahme läuft"),
    "stopped": ("radio_multi_status_stopped", "Gestoppt"),
    "finished": ("radio_multi_status_finished", "Beendet"),
    "failed": ("radio_multi_status_failed", "Fehlgeschlagen"),
    "cancelled": ("radio_multi_status_cancelled", "Nicht gestartet"),
}


class MultiRecordingWindow(tk.Toplevel):
    def __init__(self, app, mode):
        super().__init__(app)
        self.app, self.mode = app, mode
        self.title(app.tr("radio_multi_title", "Mehrfachaufnahme"))
        self.geometry("850x500")
        self.minsize(850, 400)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.count = tk.StringVar(self)
        self.notice = tk.StringVar(self)
        self.summary = tk.StringVar(self)
        self.minutes = tk.StringVar(
            self,
            value=str(saved_settings(app.radio_settings)["multi_recording_minutes"]),
        )
        ttk.Label(
            self, textvariable=self.count, font=("TkDefaultFont", 12, "bold")
        ).grid(row=0, column=0, sticky="w", padx=12, pady=10)
        frame = ttk.Frame(self)
        frame.grid(row=1, column=0, sticky="nsew", padx=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            frame,
            columns=("bitrate", "status", "elapsed", "size", "title"),
            selectmode="browse",
        )
        for key, text, width in [
            ("#0", app.tr("radio_miniplayer_label_station", "Sender"), 190),
            ("bitrate", app.tr("radio_col_bitrate", "Bitrate"), 65),
            ("status", app.tr("radio_miniplayer_label_status", "Status"), 115),
            ("elapsed", app.tr("radio_multi_col_elapsed", "Laufzeit"), 65),
            ("size", app.tr("radio_multi_col_size", "Größe"), 65),
            ("title", app.tr("radio_multi_col_last_title", "Letzter Titel"), 210),
        ]:
            self.tree.heading(key, text=text)
            self.tree.column(
                key, width=width, minwidth=45, stretch=key in {"#0", "title"}
            )
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(frame, command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.bind("<ButtonRelease-3>", self.context)
        self.tree.bind("<<TreeviewSelect>>", self.selected)
        options = ttk.Frame(self)
        options.grid(row=2, column=0, sticky="ew", padx=12, pady=10)
        ttk.Label(
            options, text=app.tr("radio_multi_max_time", "Max. Aufnahmezeit je Sender:")
        ).pack(side="left")
        self.duration = ttk.Spinbox(
            options, from_=1, to=1440, textvariable=self.minutes, width=6
        )
        self.duration.pack(side="left", padx=6)
        ttk.Label(
            options, text=app.tr("radio_multi_minutes_all", "Minuten (gilt für alle)")
        ).pack(side="left")
        ttk.Label(self, textvariable=self.summary, wraplength=800, justify="left").grid(
            row=3, column=0, sticky="ew", padx=12
        )
        ttk.Label(
            self,
            text=app.tr(
                "radio_multi_help",
                "Je Sender eine MP3 und eine Metadatendatei mit Titelverlauf. Popup schließen lässt Aufnahmen weiterlaufen.",
            ),
            wraplength=800,
        ).grid(row=4, column=0, sticky="w", padx=12, pady=6)
        ttk.Label(self, textvariable=self.notice, wraplength=800).grid(
            row=5, column=0, sticky="ew", padx=12
        )
        buttons = ttk.Frame(self)
        buttons.grid(row=6, column=0, sticky="ew", padx=12, pady=12)
        self.start_button = ttk.Button(
            buttons,
            text=app.tr("radio_multi_check_start", "Prüfen & starten"),
            command=self.start,
        )
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(
            buttons,
            text=app.tr("radio_multi_stop_all", "Alle stoppen"),
            command=lambda: self.mode.stop(),
        )
        self.stop_button.pack(side="left", padx=6)
        self.remove_button = ttk.Button(
            buttons,
            text=app.tr("radio_multi_remove_selection", "Auswahl entfernen"),
            command=self.remove,
        )
        self.remove_button.pack(side="left")
        self.one_stop = ttk.Button(
            buttons,
            text=app.tr("radio_multi_stop_station", "Sender stoppen"),
            command=self.stop_selected,
        )
        self.one_stop.pack(side="left", padx=6)
        ttk.Button(
            buttons, text=app.tr("btn_close", "Schließen"), command=self.withdraw
        ).pack(side="right")
        self.protocol("WM_DELETE_WINDOW", self.withdraw)
        self.bind("<Escape>", lambda _e: self.withdraw())
        self._last_message = None
        self._was_busy = False
        self.refresh()
        self._poll()
        app._apply_tk_widget_theme(self, app._app_theme)

    def _poll(self):
        self.refresh()
        self._poll_timer = self.after(500, self._poll)

    def destroy(self):
        timer = vars(self).get("_poll_timer")
        if timer is not None:
            self.after_cancel(timer)
        super().destroy()

    def refresh(self):
        from netmon.features import radio_controller as radio

        rows, message, busy = self.mode.snapshot()
        ids = {row["id"] for row in rows}
        for identifier in self.tree.get_children():
            if identifier not in ids:
                self.tree.delete(identifier)
        demand = 0
        unknown = False
        for row in rows:
            station = row["station"]
            try:
                bitrate = max(0, int(station.get("bitrate") or 0))
            except (ValueError, TypeError):
                bitrate = 0
            demand += bitrate
            unknown |= not bool(bitrate)
            values = (
                (
                    str(bitrate) + " kbps"
                    if bitrate
                    else self.app.tr("radio_multi_bitrate_unknown", "unbekannt")
                ),
                self.app.tr(*STATUS[row["status"]]),
                f"{row['elapsed']//60}:{row['elapsed']%60:02d}",
                f"{row['size']/1_000_000:.1f} MB",
                row["title"] or "—",
            )
            if not self.tree.exists(row["id"]):
                self.tree.insert(
                    "",
                    "end",
                    iid=row["id"],
                    text=station.get("name") or row["id"],
                    values=values,
                )
            else:
                self.tree.item(row["id"], values=values)
        self.count.set(
            self.app.tr(
                "radio_multi_count", "Mehrfachaufnahme · {count} / 10 Sender"
            ).format(count=len(rows))
            + (self.app.tr("radio_multi_count_active", " · aktiv") if busy else "")
        )
        try:
            minutes = max(1, min(1440, int(self.minutes.get())))
        except ValueError:
            minutes = 60
        size = len(rows) * OUTPUT_BYTES_SECOND * minutes * 60 / 1_000_000_000
        self.summary.set(
            self.app.tr(
                "radio_multi_summary",
                "Netzbedarf laut Senderdaten: {bandwidth:.2f} Mbit/s{unknown} · MP3-Speicherbedarf ca. {size:.2f} GB plus Reserve.\nVor Start: 10 Sekunden gemeinsamer Empfangstest; keine dauerhafte Bandbreitengarantie.",
            ).format(
                bandwidth=demand / 1000,
                unknown=(
                    self.app.tr(
                        "radio_multi_unknown_bitrates", " + unbekannte Bitraten"
                    )
                    if unknown
                    else ""
                ),
                size=size,
            )
        )
        if message != self._last_message:
            self.notice.set(message)
            self._last_message = message
        self.start_button.state(["disabled"] if busy or not rows else ["!disabled"])
        self.stop_button.state(["!disabled"] if busy else ["disabled"])
        self.duration.state(["disabled"] if busy else ["!disabled"])
        self.remove_button.state(["disabled"] if busy else ["!disabled"])
        self.one_stop.state(["!disabled"] if busy else ["disabled"])
        active = sum(row["status"] == "recording" for row in rows)
        opener = vars(self.app).get("radio_multi_recording_button")
        if opener is not None:
            opener.configure(
                text=(
                    self.app.tr(
                        "radio_multi_button_active", "Mehrfachaufnahme ({active}/10)"
                    ).format(active=active)
                    if busy
                    else self.app.tr("radio_multi_open", "Mehrfachaufnahme …")
                )
            )
        for name in ("radio_attach_button", "radio_detach_button"):
            action = vars(self.app).get(name)
            if action is not None:
                action.state(["disabled"] if busy else ["!disabled"])
        if busy and not radio._recording_busy(self.app):
            radio._recording_status_text(
                self.app,
                (
                    self.app.tr(
                        "radio_multi_streams_running",
                        "Mehrfachaufnahme: {active} Streams laufen.",
                    ).format(active=active)
                    if active
                    else self.app.tr(
                        "radio_multi_preflight", "Mehrfachaufnahme: Vorprüfung läuft …"
                    )
                ),
            )
        if self._was_busy and not busy:
            if not radio._recording_busy(self.app):
                radio._recording_status_text(
                    self.app,
                    self.app.tr(
                        "radio_multi_finished_status",
                        "Mehrfachaufnahmen beendet. Details im Aufnahmefenster.",
                    ),
                )
            radio.refresh_radio_recordings_browser_ui(self.app)
        self._was_busy = busy

    def selected(self, _event=None):
        selection = self.tree.selection()
        if selection:
            rows, _, _ = self.mode.snapshot()
            row = next((row for row in rows if row["id"] == selection[0]), None)
            if row and row["reason"]:
                self.notice.set(row["reason"])

    def start(self):
        try:
            controller.start(self.app, int(self.minutes.get()))
        except (ValueError, OSError, RuntimeError) as exc:
            self.notice.set(str(exc))
        self.refresh()

    def remove(self):
        for identifier in self.tree.selection():
            try:
                self.mode.remove(identifier)
            except ValueError as exc:
                self.notice.set(str(exc))
                return
        if not controller.persist(self.app):
            self.notice.set(
                self.app.tr(
                    "radio_multi_remove_save_failed",
                    "Auswahl geändert, aber Speichern fehlgeschlagen.",
                )
            )
        self.refresh()

    def stop_selected(self):
        for identifier in self.tree.selection():
            self.mode.stop(identifier)

    def context(self, event):
        identifier = self.tree.identify_row(event.y)
        if not identifier:
            return "break"
        self.tree.selection_set(identifier)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(
            label=self.app.tr("radio_multi_stop_station", "Sender stoppen"),
            command=self.stop_selected,
            state="normal" if self.mode.busy else "disabled",
        )
        menu.add_command(
            label=self.app.tr(
                "radio_multi_remove_from_selection", "Aus Aufnahmeauswahl entfernen"
            ),
            command=self.remove,
            state="disabled" if self.mode.busy else "normal",
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"
