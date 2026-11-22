"""Reusable category/bitrate dialog; edits remain a draft until Apply."""

import queue
import threading
import time
import tkinter as tk
from tkinter import ttk

from netmon.core import radio_station_filters as filters


def filter_summary(app, criteria):
    criteria = filters.normalize_filter(criteria)
    labels = dict(filters.CATEGORIES)
    names = [
        app.tr("radio_filter_category_" + key, labels[key])
        for key in criteria["categories"]
    ]
    category = ", ".join(names) or app.tr(
        "radio_filter_all_categories", "All categories"
    )
    minimum = criteria["minimum_bitrate"]
    rate = (
        app.tr("radio_filter_at_least", "at least {rate} kbps").format(rate=minimum)
        if minimum
        else app.tr("radio_filter_all_bitrates", "all bitrates")
    )
    if minimum and criteria["include_unknown"]:
        rate += app.tr("radio_filter_with_unknown", " + unknown bitrate")
    summary = app.tr("radio_filter_summary", "Filter: {categories} · {bitrate}").format(
        categories=category, bitrate=rate
    )
    if criteria.get("country"):
        summary = app.tr(
            "radio_filter_summary_country", "{summary} · Country: {country}"
        ).format(summary=summary, country=criteria["country"])
    return summary


class StationFilterWindow(tk.Toplevel):
    def __init__(
        self,
        parent,
        app,
        criteria,
        on_apply,
        *,
        hint=None,
        stations=None,
        countries=False,
    ):
        super().__init__(parent)
        self.app, self.on_apply = app, on_apply
        self.station_source = stations if stations is not None else lambda: app.radio_db
        self.title(app.tr("radio_filter_title", "Station filters"))
        self.transient(parent.winfo_toplevel())
        self.resizable(False, False)
        self.stop = threading.Event()
        self.results = queue.Queue()
        self.worker = None
        self.generation = 0
        self.poll_id = None
        criteria = filters.normalize_filter(criteria)
        body = ttk.Frame(self, padding=14)
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=1)
        ttk.Label(
            body,
            text=app.tr("radio_filter_categories", "Categories"),
            font=("TkDefaultFont", 11, "bold"),
        ).grid(row=0, column=0, sticky="w")
        choices = ttk.Frame(body)
        choices.grid(row=1, column=0, sticky="ew", pady=(8, 12))
        self.categories = {}
        for index, (key, label) in enumerate(filters.CATEGORIES):
            variable = tk.BooleanVar(self, value=key in criteria["categories"])
            self.categories[key] = variable
            ttk.Checkbutton(
                choices,
                text=app.tr("radio_filter_category_" + key, label),
                variable=variable,
                command=self.preview,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=(0, 30), pady=2)
        rate_row = ttk.Frame(body)
        rate_row.grid(row=2, column=0, sticky="ew")
        ttk.Label(
            rate_row, text=app.tr("radio_filter_minimum", "Minimum bitrate:")
        ).pack(side="left", padx=(0, 10))
        self.bitrate = ttk.Combobox(
            rate_row,
            state="readonly",
            width=14,
            values=[
                app.tr("radio_filter_all", "All"),
                *[f"{rate} kbps" for rate in filters.BITRATES[1:]],
            ],
        )
        self.bitrate.current(filters.BITRATES.index(criteria["minimum_bitrate"]))
        self.bitrate.pack(side="left")
        self.bitrate.bind("<<ComboboxSelected>>", lambda event: self.preview())
        self.country = None
        self._country_tag = None
        extra = int(countries)
        if countries:
            country_row = ttk.Frame(body)
            country_row.grid(row=3, column=0, sticky="ew", pady=(8, 0))
            ttk.Label(
                country_row, text=app.tr("radio_filter_country", "Country:")
            ).pack(side="left", padx=(0, 10))
            names = filters.country_names(app.radio_db)
            selected = criteria.get("country", "")
            if selected and selected.casefold() not in {
                name.casefold() for name in names
            }:
                names = sorted([*names, selected], key=str.casefold)
            values = [app.tr("radio_filter_all_countries", "All countries"), *names]
            self.country = ttk.Combobox(
                country_row, state="readonly", values=values, width=30, height=12
            )
            self.country.current(
                next(
                    (
                        i
                        for i, name in enumerate(values[1:], 1)
                        if name.casefold() == selected.casefold()
                    ),
                    0,
                )
            )
            self.country.pack(side="left")
            self.country.bind("<<ComboboxSelected>>", lambda event: self.preview())
            self._country_prefix = ""
            self._country_last_key = 0
            self.country.bind("<KeyPress>", self._country_key)
            # Bind the native popdown list too; readonly comboboxes otherwise
            # consume printable keys without providing prefix navigation on Tk/X11.
            popdown = self.tk.call("ttk::combobox::PopdownWindow", str(self.country))
            self._country_listbox = f"{popdown}.f.l"
            self._country_tag = f"RadioCountryJump{self.country.winfo_id()}"
            tags = self.tk.splitlist(self.tk.call("bindtags", self._country_listbox))
            self.tk.call("bindtags", self._country_listbox, (self._country_tag, *tags))
            self.bind_class(self._country_tag, "<KeyPress>", self._country_key)
        self.unknown = tk.BooleanVar(self, value=criteria["include_unknown"])
        self.unknown_button = ttk.Checkbutton(
            body,
            text=app.tr("radio_filter_unknown", "Allow unknown bitrate"),
            variable=self.unknown,
            command=self.preview,
        )
        self.unknown_button.grid(row=3 + extra, column=0, sticky="w", pady=(8, 12))
        ttk.Label(
            body,
            text=(
                hint
                if hint is not None
                else app.tr(
                    "radio_filter_hint",
                    "No checked category means all categories. Changes apply to the next station switch.",
                )
            ),
            wraplength=390,
        ).grid(row=4 + extra, column=0, sticky="w")
        self.count = tk.StringVar(self)
        ttk.Label(body, textvariable=self.count, wraplength=390).grid(
            row=5 + extra, column=0, sticky="w", pady=12
        )
        actions = ttk.Frame(body)
        actions.grid(row=6 + extra, column=0, sticky="ew")
        actions.columnconfigure(1, weight=1)
        self.reset_button = ttk.Button(
            actions, text=app.tr("radio_filter_reset", "Reset"), command=self.reset
        )
        self.reset_button.grid(row=0, column=0, sticky="w")
        self.apply_button = ttk.Button(
            actions,
            text=app.tr("radio_filter_apply", "Apply filters"),
            command=self.apply,
        )
        self.apply_button.grid(row=0, column=2, sticky="e", padx=(20, 0))
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.bind("<Escape>", lambda event: self.close())
        self.bind("<Destroy>", self._destroyed)
        app._apply_tk_widget_theme(
            self, app._app_theme or app._theme_with_palette(app._start_theme_name)
        )
        self.preview()

    def criteria(self):
        raw = {
            "categories": [
                key for key, variable in self.categories.items() if variable.get()
            ],
            "minimum_bitrate": filters.BITRATES[max(0, self.bitrate.current())],
            "include_unknown": self.unknown.get(),
        }
        if self.country is not None and self.country.current() > 0:
            raw["country"] = self.country.get()
        return filters.normalize_filter(raw)

    def _country_key(self, event):
        char = str(event.char or "").casefold()
        if not char.isalpha() or event.state & (4 | 8):
            return None
        now = time.monotonic()
        previous = self._country_prefix if now - self._country_last_key < 1.2 else ""
        cycle = previous == char
        prefix = char if cycle else previous + char
        values = list(self.country.cget("values"))
        matches = [
            i
            for i, value in enumerate(values[1:], 1)
            if value.casefold().startswith(prefix)
        ]
        if not matches:
            prefix = char
            matches = [
                i
                for i, value in enumerate(values[1:], 1)
                if value.casefold().startswith(prefix)
            ]
        self._country_prefix, self._country_last_key = prefix, now
        if matches:
            current = self.country.current()
            index = (
                matches[(matches.index(current) + 1) % len(matches)]
                if cycle and current in matches
                else matches[0]
            )
            self.country.current(index)
            if str(event.widget) == self._country_listbox:
                for command, args in [
                    ("selection", ("clear", 0, "end")),
                    ("selection", ("set", index)),
                    ("activate", (index,)),
                    ("see", (index,)),
                ]:
                    self.tk.call(self._country_listbox, command, *args)
            self.preview()
        return "break"

    def preview(self):
        self.generation += 1
        self.unknown_button.state(
            ["disabled"] if self.bitrate.current() == 0 else ["!disabled"]
        )
        self.count.set(
            self.app.tr("radio_filter_count", "Matching stations: {count}").format(
                count="…"
            )
        )
        if self.worker is None:
            self._start_count()

    def _start_count(self):
        criteria = self.criteria()
        generation = self.generation
        stations = tuple(self.station_source())
        stop, results = self.stop, self.results

        # Only plain draft values and station metadata cross the boundary.
        # One worker at a time; later checkbox changes coalesce into one recount.
        def count():
            total = 0
            for station in stations:
                if stop.is_set():
                    return
                total += filters.matches_station(station, criteria)
            results.put((generation, total))

        self.worker = threading.Thread(target=count, daemon=True)
        self.worker.start()
        self.poll_id = self.after(40, self._poll)

    def _poll(self):
        self.poll_id = None
        try:
            generation, count = self.results.get_nowait()
        except queue.Empty:
            self.poll_id = self.after(40, self._poll)
            return
        self.worker = None
        if generation == self.generation:
            self.count.set(
                self.app.tr("radio_filter_count", "Matching stations: {count}").format(
                    count=count
                )
            )
        else:
            self._start_count()

    def reset(self):
        for variable in self.categories.values():
            variable.set(False)
        self.bitrate.current(0)
        self.unknown.set(False)
        if self.country is not None:
            self.country.current(0)
            self._country_prefix = ""
        self.preview()

    def apply(self):
        if self.on_apply(self.criteria()):
            self.close()
        else:
            self.count.set(
                self.app.tr("radio_filter_save_failed", "Filters could not be saved.")
            )

    def close(self):
        self.stop.set()
        if self.poll_id is not None:
            self.after_cancel(self.poll_id)
            self.poll_id = None
        self.destroy()

    def _destroyed(self, event):
        if event.widget is self:
            self.stop.set()
            if self._country_tag is not None:
                self.unbind_class(self._country_tag, "<KeyPress>")
            if self.poll_id is not None:
                self.after_cancel(self.poll_id)
                self.poll_id = None
