# Settings Theme Logging Payload

## Ziel

Weiterer Settings-Sync-Schnitt: Theme-, Tooltip-, Logging- und
Schutz-Settings werden aus `App.apply_settings_from_ui()` herausgeloest.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_theme_logging_settings_from_app(app, new_theme=..., normalize_hex_color=...)`.
- Der Helper uebernimmt:
  - Theme-Auswahl.
  - Theme-Studio-Farben, Stil und Profilname.
  - Tooltip-Status.
  - Auto-Log-Clear und Debug-Network-Logging.
  - Strict Protection.
  - UFW-Logging-Default inklusive Fallback auf `keep`.
- `App.apply_settings_from_ui()` uebergibt weiterhin die bestehende
  `normalize_hex_color`-Funktion.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Der verbleibende Settings-Kern besteht nun im Wesentlichen aus Basis-/Netzwerk-
Startwerten, Chad-Modell/Preview und den abschliessenden Runtime-Side-Effects.
