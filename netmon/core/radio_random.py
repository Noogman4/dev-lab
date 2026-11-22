"""Random station rotation; playback and Tk remain owned by the radio controller."""

from __future__ import annotations

import random
import re
import time
from datetime import datetime, timezone

from netmon.core import radio_station_filters

DEFAULT_INTERVAL_MINUTES = 5
MAX_INTERVAL_MINUTES = 1440
MAX_HISTORY = 500
CONNECT_TIMEOUT_SECONDS = 30
RETRY_SECONDS = 5
MAX_FAILURES = 3
HISTORY_STATES = frozenset(
    {"selected", "started", "switched", "failed", "ended", "stopped", "interrupted"}
)


def interval_minutes(value):
    """Accept whole minutes only; never turn malformed settings into a hot timer."""
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{1,4}", str(value)):
        raise ValueError("Interval must be a whole number of minutes")
    value = int(value)
    if not 1 <= value <= MAX_INTERVAL_MINUTES:
        raise ValueError("Interval must be between 1 and 1440 minutes")
    return value


def _text(value, limit):
    if not isinstance(value, str):
        return ""
    return re.sub(r"[\x00-\x1f\x7f-\x9f\u2028\u2029]+", " ", value)[:limit]


def saved_settings(settings):
    """Bound the persisted history and keep its schema independent of Tk."""
    try:
        minutes = interval_minutes(settings.get("random_interval_minutes", 5))
    except (TypeError, ValueError):
        minutes = DEFAULT_INTERVAL_MINUTES
    raw = settings.get("random_history", [])
    history = []
    for entry in raw[-MAX_HISTORY:] if isinstance(raw, list) else []:
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("status"), str)
            or entry["status"] not in HISTORY_STATES
        ):
            continue
        stamp = _text(entry.get("selected_at"), 40)
        try:
            parsed = datetime.fromisoformat(stamp)
            if parsed.tzinfo is None:
                continue
        except ValueError:
            continue
        name = _text(entry.get("name"), 512)
        station_id = _text(entry.get("station_id"), 256)
        if not name or not station_id:
            continue
        history.append(
            {
                "selected_at": stamp,
                "station_id": station_id,
                "name": name,
                "status": entry["status"],
            }
        )
    return {
        "random_interval_minutes": minutes,
        "random_history": history,
        "random_filter": radio_station_filters.normalize_filter(
            settings.get("random_filter")
        ),
    }


class RandomRadio:
    """One cancellable timer and a shuffled round of the current database.

    Callbacks and methods run on the UI thread. A playback token prevents late
    notifications from a stopped/replaced player from reviving this mode.
    The mode is deliberately never enabled by loading saved settings.
    """

    def __init__(
        self,
        settings,
        *,
        stations,
        normalize,
        play,
        schedule,
        cancel,
        save,
        abort=lambda token: None,
        changed=lambda: None,
        rng=None,
        clock=time.monotonic,
        now=lambda: datetime.now(timezone.utc),
    ):
        settings = saved_settings(settings)
        self.minutes = settings["random_interval_minutes"]
        self.history = settings["random_history"]
        self.filters = settings["random_filter"]
        for entry in self.history:
            if entry["status"] in {"selected", "started"}:
                entry["status"] = "interrupted"
        self.active = False
        self.reason = "off"
        self.stations, self.normalize, self.play = stations, normalize, play
        self.schedule, self.cancel, self.save = schedule, cancel, save
        self.abort = abort
        self.changed = changed
        self.rng = rng or random.Random()
        self.clock, self.now = clock, now
        self._timer = None
        self._epoch = 0
        self._serial = 0
        self._token = None
        self._entry = None
        self._started = None
        self._seen = set()
        self._current = ""
        self._failures = 0

    def settings(self):
        return saved_settings(
            {
                "random_interval_minutes": self.minutes,
                "random_history": self.history,
                "random_filter": self.filters,
            }
        )

    def set_filter(self, criteria):
        filters = radio_station_filters.normalize_filter(criteria)
        settings = self.settings()
        settings["random_filter"] = filters
        if not self.save(settings):
            return False
        self.filters = filters
        self._seen = {self._current} if self._current else set()
        self.changed()
        return True

    def clear_history(self):
        """Persist the empty list before clearing it; preserve playback/timers."""
        if not self.history:
            return True
        settings = self.settings()
        settings["random_history"] = []
        if not self.save(settings):
            return False
        self.history = []
        # _entry still belongs to the in-flight player. Its later status updates
        # may finish normally, but must never put it back in the cleared list.
        self.changed()
        return True

    def _cancel_timer(self):
        self._epoch += 1
        if self._timer is not None:
            self.cancel(self._timer)
            self._timer = None

    def _later(self, seconds, callback):
        self._cancel_timer()
        epoch = self._epoch

        def due():
            if self.active and epoch == self._epoch:
                self._timer = None
                callback()

        self._timer = self.schedule(max(1, int(seconds * 1000)), due)

    def _persist(self):
        ok = self.save(self.settings())
        if not ok:
            self.active = False
            self.reason = "write_failed"
            self._token = None
            self._cancel_timer()
        self.changed()
        return ok

    def start(self, current_station_id=""):
        if self.active:
            return True
        self.active = True
        self.reason = "running"
        self._seen = {current_station_id} if current_station_id else set()
        self._current = current_station_id
        self._failures = 0
        return self._advance()

    def stop(self, reason="off"):
        was_active = self.active
        self.active = False
        self.reason = reason
        self._token = None
        self._cancel_timer()
        if self._entry and self._entry["status"] in {"selected", "started"}:
            self._entry["status"] = "stopped"
            self._persist()
        else:
            self.changed()
        return was_active

    def set_minutes(self, value):
        self.minutes = interval_minutes(value)
        if not self._persist():
            return False
        if self.active and self._started is not None:
            remaining = self.minutes * 60 - (self.clock() - self._started)
            self._later(max(0.1, remaining), self._interval_elapsed)
        return True

    def _pick(self):
        pool = {
            row["id"]: row
            for row in self.stations()
            if isinstance(row, dict)
            and isinstance(row.get("id"), str)
            and row["id"]
            and radio_station_filters.matches_station(row, self.filters)
        }
        self._seen.intersection_update(pool)
        while pool:
            choices = list(pool.keys() - self._seen)
            if not choices:
                self._seen.clear()
                choices = [key for key in pool if key != self._current] or list(pool)
            self.rng.shuffle(choices)
            while choices:
                key = choices.pop()
                station = self.normalize(pool[key])
                if station is not None:
                    self._seen.add(key)
                    return station
                del pool[key]
                self._seen.discard(key)
        return None

    def _advance(self):
        if not self.active:
            return False
        station = self._pick()
        if station is None:
            filtered = bool(
                self.filters["categories"] or self.filters["minimum_bitrate"]
            )
            self.stop("no_matches" if filtered else "no_stations")
            return False
        if self._entry and self._entry["status"] == "started":
            self._entry["status"] = "switched"
        self._serial += 1
        token = self._token = self._serial
        self._current = station["id"]
        self._started = None
        self._entry = {
            "selected_at": self.now().isoformat(timespec="seconds"),
            "station_id": _text(station["id"], 256),
            "name": _text(station["name"], 512),
            "status": "selected",
        }
        self.history.append(self._entry)
        self.history = self.history[-MAX_HISTORY:]
        if not self._persist():
            return False
        self._later(CONNECT_TIMEOUT_SECONDS, lambda: self._connection_timeout(token))
        if not self.play(station["id"], token):
            # A missing dependency/output setup cannot improve by retrying.
            self.failed(token, terminal=True)
            return False
        return True

    def _connection_timeout(self, token):
        if self.owns(token):
            self.abort(token)
            self.failed(token)

    def started(self, token):
        if not self.owns(token):
            return
        self._started = self.clock()
        self._entry["status"] = "started"
        self.reason = "running"
        if self._persist():
            self._later(self.minutes * 60, self._interval_elapsed)

    def _interval_elapsed(self):
        self._failures = 0
        self._advance()

    def failed(self, token, *, terminal=False, ended=False):
        if not self.owns(token):
            return
        self._entry["status"] = "ended" if ended else "failed"
        if self._started is not None and self.clock() - self._started >= 15:
            self._failures = 0
        self._failures += 1
        self._token = None
        self._started = None
        self._cancel_timer()
        if terminal or self._failures >= MAX_FAILURES:
            self.active = False
            self.reason = "start_failed"
        else:
            self.reason = "retrying"
        if self._persist() and self.active:
            self._later(RETRY_SECONDS, self._advance)

    def owns(self, token):
        return self.active and token is not None and token == self._token
