# Settings Base Network Payload

## Ziel

Weiterer Settings-Sync-Schnitt: Basis-, Guard-, DNS- und Startnetzwerkwerte
werden aus `App.apply_settings_from_ui()` herausgeloest.

## Aenderungen

- `netmon/ui/settings_sync.py` enthaelt jetzt
  `update_base_network_settings_from_app(app, new_language=...)`.
- Der Helper uebernimmt:
  - Sprache.
  - Startup-/Process-/PATH-Guard-Autorun.
  - feste Startnetzwerkwerte (`system`, kein VPN-Profil, kein Killswitch, kein DoT).
  - DNS Guard.
  - DNSSEC-Modus inklusive Strict/Standard-Normalisierung.
  - ISP-DNS-Fallback-Profil.
  - Start Security Monitoring.
- `App.apply_settings_from_ui()` berechnet weiter `language_changed`, delegiert
  aber die Payload-Zuweisungen.

## Tests

- `tests/test_settings_sync.py`
- `tests/test_netmon_settings_tab.py`
- Volle Suite nach dem Schnitt.

## Naechster Schnitt

Im Kern von `apply_settings_from_ui()` bleiben nun vor allem Chad-Modell/Preview
und die abschliessenden Runtime-Side-Effects. Diese sollten separat behandelt
werden, weil sie weniger reine Payload-Logik sind.
