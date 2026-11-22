"""Tk-facing integration for the snapshot-only multi-recording manager."""

from tkinter import messagebox

from netmon.core.radio_multi_recording import MultiRecording, saved_settings


def target(app):
    return vars(app).get("radio_embedded_panel") or app


def busy(app):
    mode = vars(target(app)).get("_radio_multi_recording")
    return mode is not None and mode.busy


def blocked_handover(app):
    if not busy(app):
        return False
    source = target(app)
    message = source.tr(
        "radio_multi_handover_blocked",
        "An-/Abkoppeln erst nach Abschluss der Mehrfachaufnahmen möglich.",
    )
    status = vars(source).get("radio_record_status_var")
    if status is not None:
        status.set(message)
    window = vars(source).get("radio_multi_recording_window")
    if window is not None and window.winfo_exists():
        window.notice.set(message)
    return True


def manager(app):
    app = target(app)
    mode = vars(app).get("_radio_multi_recording")
    if mode is None:
        from netmon.features import radio_controller as radio

        mode = MultiRecording(translate=getattr(app, "tr", None))
        for identifier in saved_settings(app.radio_settings)[
            "multi_recording_station_ids"
        ]:
            station = radio._resolve_station_by_id(app, identifier)
            if station:
                mode.add(station)
        app._radio_multi_recording = mode
    return mode


def persist(app, minutes=None):
    from netmon.features import radio_controller as radio

    rows, _message, _active = manager(app).snapshot()
    app.radio_settings["multi_recording_station_ids"] = [row["id"] for row in rows]
    if minutes is not None:
        app.radio_settings["multi_recording_minutes"] = minutes
    return radio.save_radio_settings(app)


def open_window(app):
    from netmon.ui.radio_multi_recording import MultiRecordingWindow

    app = target(app)
    window = vars(app).get("radio_multi_recording_window")
    if window is None or not window.winfo_exists():
        window = MultiRecordingWindow(app, manager(app))
        app.radio_multi_recording_window = window
    window.deiconify()
    window.lift()
    return window


def add_selected(app):
    from netmon.features import radio_controller as radio

    app = target(app)
    station = radio._resolve_station_by_id(app, radio._selected_station_id(app))
    window = open_window(app)
    if station is None:
        window.notice.set(
            app.tr("radio_multi_select_station", "Bitte zuerst einen Sender auswählen.")
        )
        return False
    try:
        manager(app).add(station)
    except ValueError as exc:
        window.notice.set(str(exc))
        return False
    if not persist(app):
        window.notice.set(
            app.tr(
                "radio_multi_add_save_failed",
                "Auswahl übernommen, aber Speichern fehlgeschlagen.",
            )
        )
    else:
        window.notice.set(
            app.tr(
                "radio_multi_station_added", "Sender zur Aufnahmeauswahl hinzugefügt."
            )
        )
    window.refresh()
    return True


def start(app, minutes):
    from netmon.features import radio_controller as radio

    app = target(app)
    if not 1 <= minutes <= 1440:
        raise ValueError(
            app.tr("radio_multi_time_invalid", "Aufnahmezeit: 1 bis 1440 Minuten.")
        )
    if not radio.radio_recording_available(app):
        raise ValueError(
            app.tr(
                "radio_multi_protected_unavailable",
                "Geschützte Aufnahme ist nicht verfügbar.",
            )
        )
    if not persist(app, minutes):
        raise ValueError(
            app.tr(
                "radio_multi_settings_failed",
                "Aufnahmeeinstellungen konnten nicht gespeichert werden.",
            )
        )
    with radio._recording_lock(app):
        manager(app).start(
            radio._radio_recordings_dir(app),
            minutes,
            external_count=int(radio._recording_busy(app)),
            work_root=radio._radio_ipc_dir(app),
        )
    radio.stop_radio_random(app, "recording")


def confirm_close(app):
    if not busy(app):
        return True
    if not messagebox.askyesno(
        app.tr("radio_multi_close_title", "Aufnahmen beenden"),
        app.tr(
            "radio_multi_close_message",
            "Mehrfachaufnahmen laufen oder werden geprüft. Alle stoppen und das Programm schließen?",
        ),
        parent=app.winfo_toplevel(),
        default="no",
    ):
        return False
    shutdown(app)
    return True


def shutdown(app):
    mode = vars(target(app)).get("_radio_multi_recording")
    if mode is not None:
        mode.stop()
