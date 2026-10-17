# Settings Systemcheck Payload

## Ziel

Weiterer kleiner Settings-Sync-Schnitt: Systemcheck-Auswahlflags werden aus
`App.apply_settings_from_ui()` herausgeloest.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_systemcheck_settings_from_app(app)`.
- Der Helper uebernimmt:
  - Security Summary.
  - Startup Guard.
  - PATH Guard.
  - Process Guard.
  - Lynis.
  - Rkhunter.
  - ClamAV.
- `App.apply_settings_from_ui()` ruft den Helper nur noch auf.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Der verbleibende Kern in `apply_settings_from_ui()` besteht nun vor allem aus
Basis-/Theme-/Logging-Settings und den abschliessenden Runtime-Side-Effects.
