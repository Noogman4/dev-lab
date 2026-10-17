# Settings Finalization Flow

## Ziel

Die Runtime- und Persistenz-Side-Effects nach der UI-Synchronisierung werden
von der fachlichen Orchestrierung in `App.apply_settings_from_ui()` getrennt.

## Aenderungen

- `App._finalize_settings_application(new_language)` laedt die Sprache,
  aktualisiert den Runtime-Zustand, wendet bei vorhandener GUI das Theme an und
  speichert Settings sowie Privacy-Konfiguration.
- `apply_settings_from_ui()` bleibt fuer die Reihenfolge der Payload-Helper
  und die fachlichen Abschlussmeldungen verantwortlich.
- Der bestehende Settings-Tab-Test sichert die Reihenfolge von Runtime-Update,
  Settings-Persistenz, Privacy-Persistenz und Meldungen ab.

## Tests

- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

`apply_settings_from_ui()` ist nun eine kompakte Orchestrierung. Weitere
Aufteilung sollte nur erfolgen, wenn ein neuer klarer Verantwortungsbereich
entsteht; die verbleibende Sequenz sollte nicht um ihrer selbst willen weiter
zerlegt werden.
