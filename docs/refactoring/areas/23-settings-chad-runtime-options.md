# Settings Chad Runtime Options

## Ziel

Die verbliebenen Chad-Modell- und Vorschauoptionen aus
`App.apply_settings_from_ui()` werden als eigenstaendige Settings-Payload
synchronisiert.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_chad_runtime_options_from_app(app)`.
- Der Helper uebernimmt automatisches Umschalten zu Chad, die
  Vorschau-Dialogoption und das normalisierte Modell mit dem bisherigen
  Fallback `gpt-4.1-mini`.
- Die bestehende Synchronisierung der Chad-Analyseoptionen bleibt getrennt.

## Tests

- Direkter Helper-Test in `tests/test_settings_sync.py`.
- Settings-Tab-Tests und volle Suite nach dem Schnitt.

## Naechster Schnitt

In `apply_settings_from_ui()` verbleiben nach den Payload-Delegationen die
Lade-, Runtime-, Theme- und Persistenz-Side-Effects. Diese werden nur nach
einer eigenen Abhaengigkeitspruefung weiter separiert.
