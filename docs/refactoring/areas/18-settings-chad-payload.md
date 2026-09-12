# Settings Chad Payload

## Ziel

Weiterer Settings-Sync-Schnitt: Der strukturierte Chad-Settings-Payload wird aus
`App.apply_settings_from_ui()` herausgeloest.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_chad_settings_from_app(app)`.
- Der Helper uebernimmt:
  - Chad-Profil, Analysemodus und Systemcheck-Profil.
  - Filter-Flags.
  - Fokus-Flags.
  - Antwort-/Ausgabe-Flags.
- `App.apply_settings_from_ui()` ruft den Helper nur noch auf.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Nach diesem Schritt sind die groessten Settings-Payload-Bloecke aus
`apply_settings_from_ui()` extrahiert. Sinnvolle Folgeschritte sind jetzt kleinere
Restgruppen wie Speedtest/Security-Baseline oder der Settings-Tab-Builder selbst.
