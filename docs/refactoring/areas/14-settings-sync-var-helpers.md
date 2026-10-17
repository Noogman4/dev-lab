# Settings Sync Var Helpers

## Ziel

Kleiner Settings-Sync-Schnitt aus dem Residualplan: robuste Tk-Variable-Reads und
-Writes liegen jetzt in einem eigenen Helper-Modul statt lokal in `app.py`.

## Aenderungen

- Neues Modul `netmon/ui/settings_sync.py` mit:
  - `app_var_value(app, name, default)` fuer fehlende oder fehlerhafte Tk-Variablen.
  - `sync_app_vars_from_mapping(app, mapping)` fuer tolerantes Setzen vorhandener
    Settings-Variablen.
- `App._sync_settings_vars_from_settings()` nutzt den gemeinsamen Set-Helfer.
- `App.apply_settings_from_ui()` nutzt den gemeinsamen Get-Helfer.
- Die Settings-Schluessel und Persistenzlogik bleiben unveraendert.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Ruff/Black fuer die betroffenen Dateien

## Naechster Schnitt

Die eigentliche Payload-Bildung in `apply_settings_from_ui()` kann danach weiter
in thematische Helper zerlegt werden, z. B. Backup-/Download-Scan-Felder oder
Chad-Settings.
