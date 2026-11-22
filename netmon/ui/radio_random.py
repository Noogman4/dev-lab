"""Compact random-mode controls and its non-modal timer/history window."""

from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk

from netmon.core import radio_random
from netmon.features import radio_controller
from netmon.ui.radio_filters import StationFilterWindow, filter_summary

REASONS = {
    "off": "Random mode is off.",
    "running": "Random mode is on. Switch every {minutes} minutes.",
    "no_stations": "No playable stations in the database.",
    "no_matches": "No stations match the selected filters. Adjust the filters.",
    "write_failed": "Random mode stopped: the history could not be saved.",
    "start_failed": "Random mode stopped: playback unavailable or three failed attempts.",
    "retrying": "Station unavailable. Trying another station in 5 seconds.",
    "recording": "Random mode is off: keep the station fixed while recording.",
}
HISTORY_LABELS = {
    "selected": "Connecting",
    "started": "Started",
    "switched": "Switched",
    "failed": "Failed",
    "ended": "Ended",
    "stopped": "Stopped",
    "interrupted": "Interrupted",
}


def build_controls(app, parent):
    controls = ttk.Frame(parent)
    controls.columnconfigure(0, weight=1)
    ttk.Label(controls, text=app.tr("radio_random_title", "Random stations")).grid(
        row=0, column=0, sticky="w", padx=(0, 10)
    )
    app.radio_random_switch_var = tk.BooleanVar(controls)
    app.radio_random_switch_text = tk.StringVar(controls)
    # A real checkbutton supplies keyboard toggling and the selected state.
    images = []
    for enabled in (False, True):
        image = tk.PhotoImage(master=controls, width=34, height=20)
        for y in range(20):
            for x in range(34):
                distance = (x - min(24, max(10, x))) ** 2 + (y - 10) ** 2
                if distance <= 81:
                    image.put("#289558" if enabled else "#636b75", (x, y))
                if (x - (24 if enabled else 10)) ** 2 + (y - 10) ** 2 <= 36:
                    image.put("#ffffff", (x, y))
        images.append(image)
    app._radio_random_switch_images = images
    element = f"RadioRandomSwitch{controls.winfo_id()}.indicator"
    style = f"RadioRandomSwitch{controls.winfo_id()}.TCheckbutton"
    app.style.element_create(element, "image", images[0], ("selected", images[1]))
    app.style.layout(
        style,
        [
            (
                "Checkbutton.padding",
                {
                    "children": [
                        ("Checkbutton.label", {"side": "left", "sticky": "w"}),
                        (element, {"side": "right", "sticky": "e"}),
                    ]
                },
            )
        ],
    )
    app.radio_random_button = ttk.Checkbutton(
        controls,
        variable=app.radio_random_switch_var,
        textvariable=app.radio_random_switch_text,
        style=style,
        command=app.toggle_radio_random,
    )
    app.radio_random_button.grid(row=0, column=1)

    def settings():
        manage = vars(app).get("radio_manage_popup")
        if manage is not None:
            manage.hide()
        app.open_radio_random_popup()

    app.radio_random_settings_button = ttk.Button(
        controls, text="⋯", width=2, command=settings
    )
    app.radio_random_settings_button.grid(row=0, column=2, padx=(8, 0))
    refresh_controls(app)
    return controls


def refresh_controls(app):
    mode = radio_controller.radio_random_mode(app)
    button = vars(app).get("radio_random_button")
    popup = vars(app).get("radio_random_window")
    try:
        if button is not None and button.winfo_exists():
            app.radio_random_switch_var.set(mode.active)
            app.radio_random_switch_text.set(
                app.tr("radio_random_switch_on", "ON")
                if mode.active
                else app.tr("radio_random_switch_off", "OFF")
            )
            button.state(["selected"] if mode.active else ["!selected"])
        if popup is not None and popup.winfo_exists():
            popup.refresh()
    except tk.TclError:
        # The root also emits Destroy after destroying its child controls.
        pass


def open_popup(app):
    existing = vars(app).get("radio_random_window")
    if existing is not None and existing.winfo_exists():
        existing.deiconify()
        existing.lift()
        return existing
    popup = RandomRadioWindow(app)
    app.radio_random_window = popup
    return popup


class RandomRadioWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.mode = radio_controller.radio_random_mode(app)
        self.title(app.tr("radio_random_title", "Random stations"))
        self.transient(app.winfo_toplevel())
        self.minsize(540, 360)
        self.geometry("660x430")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        body = ttk.Frame(self, padding=14)
        body.grid(sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(4, weight=1)
        ttk.Label(
            body,
            text=app.tr("radio_random_title", "Random stations"),
            font=("TkDefaultFont", 12, "bold"),
        ).grid(row=0, column=0, sticky="w")
        intro = ttk.Label(
            body,
            text=app.tr(
                "radio_random_hint",
                "Choose from the entire database. Stop, manual playback or recording ends random mode.",
            ),
            wraplength=610,
        )
        intro.grid(row=1, column=0, sticky="w", pady=(8, 10))
        timer = ttk.Frame(body)
        timer.grid(row=2, column=0, sticky="ew")
        ttk.Label(
            timer, text=app.tr("radio_random_interval", "Switch after (minutes):")
        ).grid(row=0, column=0)
        self.minutes = tk.StringVar(self, value=str(self.mode.minutes))
        self.interval = ttk.Spinbox(
            timer,
            from_=1,
            to=radio_random.MAX_INTERVAL_MINUTES,
            width=6,
            textvariable=self.minutes,
        )
        self.interval.grid(row=0, column=1, padx=8)
        self.apply_button = ttk.Button(
            timer,
            text=app.tr("btn_apply", "Apply"),
            command=self.apply_interval,
        )
        self.apply_button.grid(row=0, column=2)
        self.filter_button = ttk.Button(
            timer,
            text=app.tr("radio_filter_button", "Filter…"),
            command=self.open_filters,
        )
        self.filter_button.grid(row=0, column=3, padx=(8, 0))
        self.filter_window = None
        self.filter_text = tk.StringVar(self)
        ttk.Label(timer, textvariable=self.filter_text, wraplength=500).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(8, 0)
        )
        self.interval.bind("<Return>", lambda _event: self.apply_interval())
        self.status = tk.StringVar(self)
        status_label = ttk.Label(body, textvariable=self.status, wraplength=610)
        status_label.grid(row=3, column=0, sticky="w", pady=10)
        history = ttk.Frame(body)
        history.grid(row=4, column=0, sticky="nsew")
        history.columnconfigure(0, weight=1)
        history.rowconfigure(0, weight=1)
        self.history = ttk.Treeview(
            history, columns=("time", "name", "status"), show="headings", height=9
        )
        for key, label, width in (
            ("time", app.tr("radio_random_history_time", "Selected at"), 145),
            ("name", app.tr("radio_field_name", "Station"), 285),
            ("status", app.tr("radio_random_history_status", "Status"), 100),
        ):
            self.history.heading(key, text=label)
            self.history.column(key, width=width, minwidth=70, stretch=key == "name")
        self.history.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(history, orient="vertical", command=self.history.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.history.configure(yscrollcommand=scroll.set)
        self._history_rows = {}
        self.history_menu = tk.Menu(self.history, tearoff=0)
        self.history_menu.add_command(label="", state="disabled")
        self.history_menu.add_separator()
        self.history_menu.add_command(
            label=app.tr("radio_menu_add_favorite", "Add to favorites")
        )
        self.history_menu.add_command(
            label=app.tr(
                "radio_history_delete_station", "Delete from entire station list…"
            )
        )
        self.history_menu.add_separator()
        self.history_menu.add_command(
            label=app.tr("radio_history_clear", "Clear list"),
            command=self.clear_history,
        )
        self.history.bind("<ButtonRelease-3>", self.show_history_menu)
        self.history.bind("<Menu>", self.show_history_menu)
        self.history.bind("<Shift-F10>", self.show_history_menu)
        history_hint = ttk.Label(
            body,
            text=app.tr(
                "radio_random_history_hint",
                "The last 500 stations remain saved after restarting. Random mode starts off.",
            ),
            wraplength=610,
        )
        history_hint.grid(row=5, column=0, sticky="w", pady=(8, 10))

        def wrap_text(event):
            for label in (intro, status_label, history_hint):
                label.configure(wraplength=max(200, event.width - 28))

        body.bind("<Configure>", wrap_text)
        actions = ttk.Frame(body)
        actions.grid(row=6, column=0, sticky="ew")
        actions.columnconfigure(1, weight=1)
        self.toggle_button = ttk.Button(actions, command=app.toggle_radio_random)
        self.toggle_button.grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text=app.tr("btn_close", "Close"), command=self.close).grid(
            row=0, column=2, sticky="e"
        )
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda _event: self.close())
        self.refresh()
        theme = app._app_theme or app._theme_with_palette(app._start_theme_name)
        app._apply_tk_widget_theme(self, theme)

    def apply_interval(self):
        try:
            self.mode.set_minutes(self.minutes.get().strip())
        except ValueError:
            self.status.set(
                self.app.tr(
                    "radio_random_invalid_interval",
                    "Enter whole minutes from 1 to 1440.",
                )
            )

    def open_filters(self):
        if self.filter_window is not None and self.filter_window.winfo_exists():
            self.filter_window.lift()
            return self.filter_window
        self.filter_window = StationFilterWindow(
            self, self.app, self.mode.filters, self.mode.set_filter
        )
        return self.filter_window

    def refresh(self):
        app, mode = self.app, self.mode
        self.filter_text.set(filter_summary(app, mode.filters))
        self.status.set(
            app.tr("radio_random_reason_" + mode.reason, REASONS[mode.reason]).format(
                minutes=mode.minutes
            )
        )
        self.toggle_button.configure(
            text=(
                app.tr("radio_random_stop", "Stop random mode")
                if mode.active
                else app.tr("radio_random_start", "Start random mode")
            )
        )
        children = self.history.get_children()
        selected = [
            self._history_rows[key]
            for key in self.history.selection()
            if key in self._history_rows
        ]
        scroll = self.history.yview()
        if children:
            self.history.delete(*children)
        self._history_rows = {}
        for index, entry in reversed(list(enumerate(mode.history))):
            stamp = datetime.fromisoformat(entry["selected_at"]).astimezone()
            status = entry["status"]
            key = self.history.insert(
                "",
                "end",
                iid=f"history-{index}",
                values=(
                    stamp.strftime("%d.%m.%Y %H:%M:%S"),
                    entry["name"],
                    app.tr("radio_random_history_" + status, HISTORY_LABELS[status]),
                ),
            )
            self._history_rows[key] = entry
            if any(entry is previous for previous in selected):
                self.history.selection_add(key)
                self.history.focus(key)
        if selected and scroll:
            self.history.yview_moveto(scroll[0])
        self.history_menu.entryconfigure(
            5, state="normal" if mode.history else "disabled"
        )
        if not mode.history:
            for index in (2, 3):
                self.history_menu.entryconfigure(index, state="disabled")

    def clear_history(self):
        self.history_menu.unpost()
        if not self.mode.history:
            return False
        if not messagebox.askyesno(
            self.app.tr("radio_history_clear", "Clear list"),
            self.app.tr(
                "radio_history_clear_prompt",
                "Clear the entire saved history? Stations, favorites and playback remain unchanged.",
            ),
            parent=self,
        ):
            return False
        if not self.mode.clear_history():
            self.status.set(
                self.app.tr(
                    "radio_history_clear_failed", "The history could not be cleared."
                )
            )
            return False
        self.refresh()
        return True

    def _history_station(self, entry):
        # History intentionally stores no playable URL. Resolve only a unique
        # database identity, never the main selection or currently playing row.
        rows = [
            row for row in self.app.radio_db if row.get("id") == entry["station_id"]
        ]
        if len(rows) != 1 or rows[0].get("name") != entry["name"]:
            return None
        return rows[0]

    def show_history_menu(self, event):
        if getattr(event, "num", None) == 3:
            if self.history.identify_region(event.x, event.y) in {
                "heading",
                "separator",
            }:
                return "break"
            key = self.history.identify_row(event.y)
        else:
            selected = self.history.selection()
            key = selected[0] if selected else self.history.focus()
            if key:
                self.history.see(key)
                x, y, _, height = self.history.bbox(key)
                event.x_root = self.history.winfo_rootx() + x + 12
                event.y_root = self.history.winfo_rooty() + y + height
        entry = self._history_rows.get(key)
        if entry is not None:
            self.history.selection_set(key)
            self.history.focus(key)
        self.history.focus_set()
        station = self._history_station(entry) if entry is not None else None
        snapshot = dict(station) if station is not None else None
        favorite_ids = {row.get("id") for row in self.app.radio_favorites}
        menu = self.history_menu
        menu.entryconfigure(
            0,
            label=(
                entry["name"]
                if entry
                else self.app.tr("radio_history_title", "History")
            ),
        )
        menu.entryconfigure(
            2,
            state=(
                "normal"
                if station and station["id"] not in favorite_ids
                else "disabled"
            ),
            command=lambda: self._history_action(entry, snapshot, delete=False),
        )
        menu.entryconfigure(
            3,
            state="normal" if station else "disabled",
            command=lambda: self._history_action(entry, snapshot, delete=True),
        )
        return self.app._show_context_menu(menu, event)

    def _history_action(self, entry, snapshot, *, delete):
        self.history_menu.unpost()
        station = self._history_station(entry)
        if station is None or station != snapshot:
            self.status.set(
                self.app.tr(
                    "radio_history_station_missing",
                    "Station no longer uniquely available in the database.",
                )
            )
            return False
        if delete:
            result = radio_controller.delete_selected_station(
                self.app, station=dict(station), allow_catalog=True, parent=self
            )
        else:
            result = radio_controller.add_to_favorites(self.app, station)
            if result:
                radio_controller.refresh_radio_ui(self.app)
        self.refresh()
        return result

    def close(self):
        if self.filter_window is not None and self.filter_window.winfo_exists():
            self.filter_window.close()
        self.history_menu.unpost()
        self.app.radio_random_window = None
        self.destroy()
