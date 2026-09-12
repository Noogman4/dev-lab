# Settings Backup Download Payload

## Ziel

Weiterer kleiner Settings-Sync-Schnitt: Backup- und Download-Scan-Payloads werden
aus `App.apply_settings_from_ui()` herausgeloest und separat testbar gemacht.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_backup_and_download_scan_settings_from_app(app)`.
- Der Helper uebernimmt:
  - Download-Scan-Pfade und Flags.
  - Backup-Zielpfad und Include-Flags.
  - Auswahl der NetMon-Backup-Verzeichnisse.
- `App.apply_settings_from_ui()` ruft den Helper nur noch auf.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Als naechstes kann ein weiterer thematischer Payload-Block aus
`apply_settings_from_ui()` folgen, z. B. Guided-Tour/Donation oder Chad-Settings.
