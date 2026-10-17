# Settings ClamAV Quickscan Payload

## Ziel

Weiterer kleiner Settings-Sync-Schnitt: ClamAV-Quickscan-Settings werden aus
`App.apply_settings_from_ui()` herausgeloest und separat testbar gemacht.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_clamav_quickscan_settings_from_app(app, clamav_controller)`.
- Der Helper uebernimmt:
  - Normalisierung der Quickscan-Ziel-IDs.
  - Normalisierung der Custom-Quickscan-Pfade.
- `App.apply_settings_from_ui()` uebergibt weiterhin den bestehenden
  `clamav_controller`; das Sync-Modul importiert keine Feature-Controller.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_clamav_controller.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Als naechstes bleibt in `apply_settings_from_ui()` vor allem der groessere
Chad-Settings-Payload als sinnvoller Kandidat.
