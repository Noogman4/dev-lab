"""Bounded recording sessions. Workers own children; Tk reads snapshots only."""

from copy import deepcopy
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import tempfile
import threading
import time
import uuid

from netmon.core import radio_sandbox
from netmon.core.utils import safe_write_json, user_json_write_scope

MAX_STREAMS = 10
MAX_TITLES = 4096
OUTPUT_BYTES_SECOND = 24_000  # Existing fixed 192 kbps MP3 encoder.
RESERVE_BYTES = 100 * 1024 * 1024
CHECK_SECONDS = 10


def saved_settings(settings):
    try:
        minutes = max(1, min(1440, int(settings.get("multi_recording_minutes", 60))))
    except (TypeError, ValueError, OverflowError):
        minutes = 60
    identifiers = settings.get("multi_recording_station_ids", [])
    if not isinstance(identifiers, list):
        identifiers = []
    return {
        "multi_recording_minutes": minutes,
        "multi_recording_station_ids": list(
            dict.fromkeys(
                item
                for item in identifiers[:100]
                if isinstance(item, str) and 0 < len(item) <= 256
            )
        )[:MAX_STREAMS],
    }


def _utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MultiRecording:
    def __init__(self, *, start=None, check_seconds=CHECK_SECONDS, translate=None):
        self._start = start or radio_sandbox.start_recording
        # The optional translator reads a catalog and must be safe in workers.
        self.tr = translate or (lambda _key, fallback: fallback)
        self.check_seconds = check_seconds
        self._lock = threading.RLock()
        self._rows = {}
        self._active = False
        self._cancel = threading.Event()
        self._session = {}
        self.message = self.tr(
            "radio_multi_add_instructions",
            "Sender über Rechtsklick aus Senderliste oder Favoriten hinzufügen.",
        )

    @property
    def busy(self):
        with self._lock:
            return self._active

    @property
    def active_count(self):
        with self._lock:
            return len(self._session) if self._active else 0

    def snapshot(self):
        with self._lock:
            return deepcopy(list(self._rows.values())), self.message, self._active

    def add(self, station):
        with self._lock:
            if self._active:
                raise ValueError(
                    self.tr(
                        "radio_multi_selection_locked",
                        "Auswahl kann nach Abschluss der laufenden Aufnahmen geändert werden.",
                    )
                )
            identifier = station["id"]
            if identifier in self._rows:
                return
            if len(self._rows) >= MAX_STREAMS:
                raise ValueError(
                    self.tr(
                        "radio_multi_max_stations", "Höchstens zehn Sender auswählen."
                    )
                )
            self._rows[identifier] = {
                "id": identifier,
                "station": deepcopy(station),
                "status": "ready",
                "elapsed": 0,
                "size": 0,
                "title": "",
                "path": "",
                "reason": "",
            }

    def remove(self, identifier):
        with self._lock:
            if self._active:
                raise ValueError(
                    self.tr(
                        "radio_multi_remove_busy",
                        "Laufende Aufnahme zuerst stoppen und deren Abschluss abwarten.",
                    )
                )
            self._rows.pop(identifier, None)

    def stop(self, identifier=None):
        with self._lock:
            if identifier is None:
                self._cancel.set()
            elif identifier in self._session:
                self._session[identifier]["stop"].set()

    def start(self, directory, minutes, *, external_count=0, work_root=None):
        minutes = int(minutes)
        if not 1 <= minutes <= 1440:
            raise ValueError(
                self.tr("radio_multi_time_invalid", "Aufnahmezeit: 1 bis 1440 Minuten.")
            )
        directory = Path(directory)
        with self._lock:
            if self._active:
                raise ValueError(
                    self.tr(
                        "radio_multi_already_busy",
                        "Aufnahmen laufen oder werden beendet.",
                    )
                )
            if not self._rows or len(self._rows) + external_count > MAX_STREAMS:
                raise ValueError(
                    self.tr(
                        "radio_multi_max_concurrent",
                        "Insgesamt höchstens zehn gleichzeitige Aufnahmen, einschließlich Einzelaufnahme.",
                    )
                )
            with user_json_write_scope(directory):
                directory.mkdir(parents=True, exist_ok=True)
            required = (
                int(len(self._rows) * OUTPUT_BYTES_SECOND * minutes * 60 * 1.05)
                + RESERVE_BYTES
            )
            if shutil.disk_usage(directory).free < required:
                raise ValueError(
                    self.tr(
                        "radio_multi_storage_insufficient",
                        "Nicht genügend freier Speicher für die gewählte Aufnahmezeit.",
                    )
                )
            self._cancel = threading.Event()
            self._session = {
                key: {
                    "stop": threading.Event(),
                    "ready": threading.Event(),
                    "failed": False,
                    "progress": 0,
                    "baseline": 0,
                }
                for key in self._rows
            }
            for row in self._rows.values():
                row.update(
                    status="checking", elapsed=0, size=0, title="", path="", reason=""
                )
            self._active = True
            self.message = self.tr(
                "radio_multi_checking_all",
                "Gemeinsame Verbindungs-, Bandbreiten- und Encoderprüfung läuft …",
            )
            thread = threading.Thread(
                target=self._run, args=(directory, minutes, work_root), daemon=False
            )
            try:
                thread.start()
            except Exception:
                self._active = False
                self._session = {}
                raise

    def _update(self, key, **values):
        with self._lock:
            self._rows[key].update(values)

    def _run(self, directory, minutes, work_root):
        workers = []
        publish = threading.Event()
        staging = None
        running_message = self.tr(
            "radio_multi_running",
            "Gemeinsamer Empfang geprüft. Aufnahmen laufen; das Prüfaudio ist enthalten.",
        )
        try:
            staging = tempfile.TemporaryDirectory(
                prefix=".netmon-aufnahme-pruefung-", dir=directory
            )
            for key, state in self._session.items():
                thread = threading.Thread(
                    target=self._record,
                    args=(
                        key,
                        state,
                        Path(staging.name),
                        directory,
                        minutes,
                        work_root,
                        publish,
                    ),
                    daemon=False,
                )
                thread.start()
                workers.append(thread)
            deadline = time.monotonic() + 45
            while not all(state["ready"].is_set() for state in self._session.values()):
                if self._cancel.wait(0.05) or time.monotonic() >= deadline:
                    raise ValueError(
                        self.tr(
                            "radio_multi_preflight_cancelled_or_timeout",
                            "Vorprüfung abgebrochen oder Zeitlimit erreicht.",
                        )
                    )
            if any(state["failed"] for state in self._session.values()):
                raise ValueError(
                    self.tr(
                        "radio_multi_preflight_station_failed",
                        "Mindestens ein Sender konnte nicht geprüft werden. Auswahl prüfen und erneut starten.",
                    )
                )
            with self._lock:
                for state in self._session.values():
                    state["baseline"] = state["progress"]
            if self._cancel.wait(self.check_seconds):
                raise ValueError(
                    self.tr(
                        "radio_multi_preflight_cancelled", "Vorprüfung abgebrochen."
                    )
                )
            with self._lock:
                stable = all(
                    not state["failed"]
                    and state["progress"] - state["baseline"]
                    >= self.check_seconds * 0.9
                    for state in self._session.values()
                )
            if not stable:
                raise ValueError(
                    self.tr(
                        "radio_multi_preflight_unstable",
                        "Gemeinsamer Empfang nicht stabil genug. Weniger oder andere Sender auswählen.",
                    )
                )
            if shutil.disk_usage(directory).free < RESERVE_BYTES:
                raise ValueError(
                    self.tr("radio_multi_space_low", "Zu wenig freier Speicher.")
                )
            with self._lock:
                self.message = running_message
            publish.set()
            while any(worker.is_alive() for worker in workers):
                if shutil.disk_usage(directory).free < RESERVE_BYTES // 2:
                    with self._lock:
                        self.message = self.tr(
                            "radio_multi_shutdown_low_space",
                            "Speicher knapp: alle Aufnahmen werden beendet.",
                        )
                    self._cancel.set()
                for worker in workers:
                    worker.join(timeout=0.05)
        except Exception as exc:
            with self._lock:
                self.message = (
                    str(exc)
                    if isinstance(exc, ValueError)
                    else self.tr(
                        "radio_multi_start_failed",
                        "Mehrfachaufnahme konnte nicht gestartet werden.",
                    )
                )
            self._cancel.set()
        finally:
            for worker in workers:
                worker.join()
            try:
                if staging is not None:
                    staging.cleanup()
            except OSError:
                with self._lock:
                    self.message = self.tr(
                        "radio_multi_cleanup_failed",
                        "Aufnahmen beendet; temporäre Prüfdateien konnten nicht entfernt werden.",
                    )
            with self._lock:
                for row in self._rows.values():
                    if row["status"] == "checking":
                        row.update(
                            status="cancelled",
                            reason=self.tr(
                                "radio_multi_preflight_incomplete",
                                "Vorprüfung nicht abgeschlossen.",
                            ),
                        )
                if publish.is_set() and self.message == running_message:
                    failed = sum(
                        row["status"] == "failed" for row in self._rows.values()
                    )
                    self.message = self.tr(
                        "radio_multi_finished_summary",
                        "Mehrfachaufnahmen beendet. Fehler: {failed}. Details stehen beim jeweiligen Sender.",
                    ).format(failed=failed)
                self._active = False
                self._session = {}

    def _record(self, key, state, staging, directory, minutes, work_root, publish):
        row = self._rows[key]
        station = row["station"]
        proc = None
        final_path = None
        started = time.monotonic()
        started_at = _utc()
        events = []
        truncated = False
        outcome = "failed"
        reason = self.tr("radio_multi_recording_failed", "Aufnahme fehlgeschlagen.")
        token = uuid.uuid4().hex[:12]
        name = (
            re.sub(r"[^\w-]+", "_", str(station.get("name") or "radio"))[:70].strip("_")
            or "radio"
        )
        name += "_" + datetime.now().strftime("%Y%m%d-%H%M%S") + "_" + token + ".mp3"
        try:
            url = station.get("url_resolved") or station.get("url") or ""
            proc = self._start(url, staging / name, work_root=work_root, metadata=True)
            started = time.monotonic()
            started_at = _utc()
            state["ready"].set()
            last_save = float("-inf")
            while True:
                result = proc.poll()
                elapsed = time.monotonic() - started
                audio_seconds, size = proc.progress()
                with self._lock:
                    state["progress"] = audio_seconds
                for title in proc.take_titles():
                    if not events or events[-1]["title"] != title:
                        if len(events) < MAX_TITLES:
                            events.append(
                                {
                                    "at": _utc(),
                                    "offset_seconds": round(elapsed, 3),
                                    "title": title,
                                }
                            )
                        else:
                            truncated = True
                        self._update(key, title=title)
                self._update(key, elapsed=int(elapsed), size=size)
                if (
                    publish.is_set()
                    and final_path is None
                    and not self._cancel.is_set()
                ):
                    candidate = directory / name
                    with user_json_write_scope(candidate):
                        os.link(proc.output_path, candidate, follow_symlinks=False)
                    final_path = candidate
                    proc.output_path = str(final_path)
                    self._update(key, path=str(final_path))
                if final_path is not None and elapsed - last_save >= 5:
                    self._save_metadata(
                        final_path,
                        station,
                        started_at,
                        minutes,
                        events,
                        truncated,
                        "recording",
                        "",
                        size,
                    )
                    last_save = elapsed
                    self._update(key, status="recording")
                if self._cancel.is_set() or state["stop"].is_set():
                    outcome, reason = "stopped", self.tr(
                        "radio_multi_stopped_by_user", "Manuell gestoppt."
                    )
                    break
                if elapsed >= minutes * 60:
                    outcome, reason = "finished", self.tr(
                        "radio_multi_duration_reached",
                        "Maximale Aufnahmezeit erreicht.",
                    )
                    break
                if result is not None:
                    if result == 0 and final_path is not None:
                        outcome, reason = "finished", self.tr(
                            "radio_multi_stream_finished", "Stream beendet."
                        )
                    else:
                        reason = self.tr(
                            "radio_multi_stream_interrupted",
                            "Stream abgebrochen oder Dateigrenze erreicht.",
                        )
                    break
                self._cancel.wait(0.05)
        except Exception:
            reason = self.tr(
                "radio_multi_protected_failed",
                "Geschützte Aufnahme oder Metadatenspeicherung fehlgeschlagen.",
            )
        finally:
            if proc is not None:
                try:
                    proc.terminate()
                    result = proc.wait(timeout=3)
                    if result != 0 and outcome in {"finished", "stopped"}:
                        outcome, reason = (
                            "failed",
                            self.tr(
                                "radio_multi_finish_failed",
                                "Aufnahme konnte nicht vollständig abgeschlossen werden.",
                            ),
                        )
                except Exception:
                    outcome, reason = "failed", self.tr(
                        "radio_multi_aborted", "Aufnahme musste abgebrochen werden."
                    )
                    try:
                        proc.kill()
                        proc.wait(timeout=3)
                    except Exception:
                        pass
            if final_path is not None:
                try:
                    size = final_path.stat().st_size
                    self._save_metadata(
                        final_path,
                        station,
                        started_at,
                        minutes,
                        events,
                        truncated,
                        outcome,
                        reason,
                        size,
                        ended_at=_utc(),
                    )
                except Exception:
                    outcome, reason = (
                        "failed",
                        self.tr(
                            "radio_multi_metadata_failed",
                            "Metadaten konnten nicht vollständig gespeichert werden.",
                        ),
                    )
            with self._lock:
                state["failed"] = final_path is None or outcome == "failed"
            state["ready"].set()
            self._update(
                key, status=outcome if final_path else "cancelled", reason=reason
            )

    @staticmethod
    def _save_metadata(
        path,
        station,
        started_at,
        minutes,
        events,
        truncated,
        status,
        reason,
        size,
        *,
        ended_at=None,
    ):
        payload = {
            "version": 1,
            "station_id": station.get("id"),
            "station_name": station.get("name"),
            "stream_url": station.get("url_resolved") or station.get("url"),
            "source_bitrate_kbps": station.get("bitrate"),
            "output_codec": "mp3",
            "output_bitrate_kbps": 192,
            "audio_file": path.name,
            "started_at": started_at,
            "ended_at": ended_at,
            "max_minutes": minutes,
            "status": status,
            "reason": reason,
            "size_bytes": size,
            "titles": events,
            "title_history_truncated": truncated,
            "includes_preflight_audio": True,
        }
        ok, _error = safe_write_json(
            path.with_suffix(".json"), payload, ensure_ascii=False
        )
        if not ok:
            raise OSError("Metadaten konnten nicht gespeichert werden.")
