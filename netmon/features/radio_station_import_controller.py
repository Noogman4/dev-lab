"""User-selected station files: preview, archive and add without playback."""

from pathlib import Path
import subprocess
from tkinter import filedialog, messagebox

from netmon.core import radio_station_import as station_import
from netmon.core.private_logs import ensure_private_log_directory
from netmon.features import radio_controller as radio
from netmon.netmon_radio_core import radio_user_data_dir


def station_import_folder():
    return Path(radio_user_data_dir()) / "Senderimporte"


def import_station_file_path(app, path):
    if app.__dict__.get("radio_database_refresh_running", False):
        radio.set_radio_status(
            app, "Senderimport bitte nach der Datenbank-Aktualisierung starten."
        )
        return False
    try:
        payload, rows, summary = station_import.read_station_file(path)
        folder = station_import_folder()
        existing = [dict(row) for row in app.radio_db]
        merged, added, duplicates = station_import.merge_imported_stations(
            existing, rows
        )
        duplicates += summary["duplicates"]
        preview = "\n".join("• " + row["name"] for row in rows[:8])
        if len(rows) > 8:
            preview += f"\n… und {len(rows) - 8} weitere Sender"
        if not messagebox.askyesno(
            app.tr("radio_xspf_import_title", "Senderdatei importieren"),
            app.tr(
                "radio_xspf_import_preview",
                "{preview}\n\nNeu: {added}; bereits vorhanden/doppelt: {duplicates}; nicht unterstützte Einträge: {skipped}.\n\nDateikopie nach:\n{folder}\n\nImportieren? Die Wiedergabe startet nicht automatisch.",
            ).format(
                preview=preview,
                added=added,
                duplicates=duplicates,
                skipped=summary["skipped"],
                folder=folder,
            ),
            parent=app,
        ):
            return False
        if app.radio_db != existing or app.__dict__.get(
            "radio_database_refresh_running", False
        ):
            raise ValueError(
                "Senderliste wurde während der Vorschau geändert. Bitte den Import erneut starten."
            )
        archived = station_import.archive_station_file(payload, path, folder)
        if added and not radio.save_radio_db(app, stations=merged):
            raise OSError(
                "Senderliste konnte nicht gespeichert werden; die Dateikopie bleibt im Importordner."
            )
    except (OSError, ValueError) as exc:
        radio.set_radio_status(app, f"Senderimport fehlgeschlagen: {exc}")
        return False
    if added:
        for name, value in (
            ("radio_search_var", merged[-1]["name"] if added == 1 else ""),
            ("radio_show_favorites_var", False),
        ):
            variable = app.__dict__.get(name)
            if variable is not None:
                variable.set(value)
        toggle_text = app.__dict__.get("radio_toggle_favorites_text_var")
        if toggle_text is not None:
            toggle_text.set(app.tr("radio_show_favorites", "Favoriten anzeigen"))
        radio.refresh_radio_station_table(app, reset_page=True)
    radio.set_radio_status(
        app,
        f"Senderdatei importiert: {added} neu, {duplicates} doppelt, {summary['skipped']} nicht unterstützt. Kopie: {archived.name}",
    )
    return True


def import_station_file_dialog(app):
    folder = station_import_folder()
    path = filedialog.askopenfilename(
        parent=app,
        title=app.tr("radio_xspf_import_title", "Senderdatei importieren"),
        initialdir=str(folder if folder.is_dir() else Path.home() / "Downloads"),
        filetypes=(
            ("Senderdateien", "*.xspf *.XSPF *.m3u *.M3U *.m3u8 *.M3U8 *.pls *.PLS"),
            ("XSPF", "*.xspf *.XSPF"),
            ("M3U / M3U8", "*.m3u *.M3U *.m3u8 *.M3U8"),
            ("PLS", "*.pls *.PLS"),
        ),
    )
    return import_station_file_path(app, path) if path else False


def open_station_import_folder(app):
    try:
        folder = station_import_folder()
        ensure_private_log_directory(folder)
        subprocess.Popen(
            ["/usr/bin/xdg-open", str(folder)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        return True
    except (OSError, ValueError) as exc:
        radio.set_radio_status(
            app, f"Senderimport-Ordner konnte nicht geöffnet werden: {exc}"
        )
        return False
