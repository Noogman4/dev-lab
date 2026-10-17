# Settings Security Tool Payload

## Ziel

Weiterer Settings-Sync-Schnitt: kleine Security-/Tool-Settings werden aus
`App.apply_settings_from_ui()` herausgeloest.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_security_tool_settings_from_app(app, speedtest_controller)`.
- Der Helper uebernimmt:
  - Security-Baseline-Profil-ID.
  - Security-Game-Mode-Preset.
  - Wireshark-Launch-Blockierung.
  - Speedtest-Server-ID inklusive bestehender Normalisierung.
- `App.apply_settings_from_ui()` ruft den Helper nur noch auf.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- `tests/test_speedtest_module.py`
- `tests/test_netmon_lynis_output.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

`apply_settings_from_ui()` enthaelt jetzt vor allem noch den allgemeinen
Settings-/Theme-/Systemcheck-Kern. Der naechste sinnvolle Schritt ist eine kleine
Extraktion fuer Theme/Logging oder Systemcheck-Flags.
