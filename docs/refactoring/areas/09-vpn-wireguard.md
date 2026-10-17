# 09 VPN und WireGuard

## Ausgangszustand

- Datei: `netmon/features/vpn_controller.py`
- Fokus dieses Schritts: interne IPv4-Profilkandidaten
- Bestehende Tests: `tests/test_netmon_vpn_slots.py`, `tests/test_vpn_slots_tab.py`
- Indirekte Aufrufer: Slot-Start, Profil-Loeschung, Firewall-Reconcile, interne IPv4-Runtimeprofile

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur Profilnamen und bestehende Namenshelfer.
- Keine WireGuard-Profile werden gelesen, geschrieben, gestartet oder geloescht.
- Keine Root-Rechte.
- Kein Subprocess-Aufruf im refaktorierten Pfad.
- Slot-Konfigurationsformate bleiben unberuehrt.

## Risiken

- Kandidatenreihenfolge fuer interne IPv4-Profile darf sich nicht aendern.
- Kurze Profilnamen muessen weiterhin nur den Legacy-Namen liefern.
- Lange Profilnamen muessen weiterhin zuerst den kompakten Namen und danach den Legacy-Namen liefern.
- Leere Profilnamen muessen weiterhin keine Kandidaten liefern.

## Performance Vorher

- Commit vorher: `3d4b232e`
- Messbedingungen: direkter Aufruf von `internal_ipv4_profile_candidates` fuer langes Profil, kurzes Profil und leeren Wert, `time.perf_counter()`, 100 Wiederholungen.
- `vpn_internal_ipv4_profile_candidates`: Median `0.003 ms`

## Geplante kleine Aenderung

- Tests fuer interne IPv4-Profilkandidaten ergaenzen.
- Deduplizierung der Kandidatenliste in einen internen Helper extrahieren.
- Namensschema, Reihenfolge, WireGuard-Aufrufe und Slot-Formate unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_unique_profile_names` fuer getrimmte, eindeutige Profilnamen eingefuehrt.
- `internal_ipv4_profile_candidates` nutzt diesen Helper fuer die finale Kandidatenliste.
- Oeffentliche Methodensignaturen und Rueckgabestruktur unveraendert gelassen.
- Keine WireGuard-, Slot- oder Firewall-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Kurze Profilnamen liefern weiterhin nur `<profil>__ipv4`.
- Lange Profilnamen liefern weiterhin zuerst den kompakten `n4_...`-Namen.
- Legacy-Kandidaten bleiben bei langen Profilnamen als Rueckfall erhalten.
- Leere Kandidaten werden weiterhin ignoriert.
- Reihenfolge der eindeutigen Kandidaten bleibt stabil.

## Betroffene Dateien

- `netmon/features/vpn_controller.py`
- `tests/test_netmon_vpn_slots.py`
- `docs/refactoring/areas/09-vpn-wireguard.md`
- `docs/refactoring/performance/areas/09-vpn-wireguard.md`

## Hinzugefuegte Tests

- `test_internal_ipv4_profile_candidates_keep_legacy_name_for_short_profile`
- `test_internal_ipv4_profile_candidates_prefer_compact_name_for_long_profile`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_vpn_slots.py tests/test_vpn_slots_tab.py`: `75 passed, 1 skipped` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/features/vpn_controller.py tests/test_netmon_vpn_slots.py`: bestanden
- `.venv/bin/python -m ruff check netmon/features/vpn_controller.py tests/test_netmon_vpn_slots.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/features/vpn_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_netmon_vpn_slots.py`: bestanden
- `.venv/bin/python -m pytest tests/test_netmon_vpn_slots.py tests/test_vpn_slots_tab.py`: `75 passed, 1 skipped`
- `.venv/bin/python -m pytest tests/test_netmon_vpn_slots.py tests/test_vpn_slots_tab.py tests/test_netmon_killswitch.py`: `122 passed, 1 skipped`

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2177 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: bestanden ausserhalb der Sandbox wegen `xvfb-run`/Tk-Displayzugriff

## Performance Nachher

- `vpn_internal_ipv4_profile_candidates`: Median `0.004 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Die Tests pruefen Namenskandidaten und Slotlogik, aber keine echte WireGuard-Runtime.
- Der GUI-Smoke prueft Startbarkeit, aber keine komplette VPN-Slot-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `09-vpn-wireguard`.
