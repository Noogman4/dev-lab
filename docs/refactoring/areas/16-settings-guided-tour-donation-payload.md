# Settings Guided Tour Donation Payload

## Ziel

Weiterer kleiner Settings-Sync-Schnitt: Guided-Tour- und Donation-Settings werden
aus `App.apply_settings_from_ui()` herausgeloest und separat testbar gemacht.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_guided_tour_and_donation_settings_from_app(app)`.
- Der Helper uebernimmt:
  - Startup-Angebot fuer Guided Tours.
  - Quickstart- vs. Full-Tour-Startup-Modus.
  - persistierte Guided-Tour-Abschluesse.
  - Donation-Popup-Enable/Disable inklusive Sperrfrist-Logik.
- `App.apply_settings_from_ui()` ruft den Helper nur noch auf.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Als naechstes bietet sich der ClamAV-Quickscan- oder Chad-Settings-Payload in
`apply_settings_from_ui()` an.
