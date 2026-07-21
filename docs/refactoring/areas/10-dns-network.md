# 10 DNS und Netzwerkdienste

## Ausgangszustand

- Datei: `netmon/services/dns_control_service.py`
- Fokus dieses Schritts: DNS-Server-Folgezeilen in `resolvectl status`
- Bestehende Tests: `tests/test_netmon_dns_consistency.py`
- Indirekte Aufrufer: DNS Health Check, DNS Leak Check, VPN-DNS-Policy, Startup-DNS-Restore

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur bereits uebergebenen `resolvectl`-Text.
- Keine DNS- oder Netzwerk-Konfiguration wird geschrieben.
- Keine Root-Rechte.
- Kein Subprocess-Aufruf im refaktorierten Parserpfad.
- NetworkManager-, `resolvectl`- und Drop-in-Schreibpfade bleiben unberuehrt.

## Risiken

- Mehrzeilige DNS-Server-Bloecke muessen weiterhin erkannt werden.
- Nicht-DNS-Folgezeilen muessen weiterhin das Sammeln beenden.
- VPN-/physische Link-Sektion-Zuordnung darf sich nicht aendern.
- Sortierung und Deduplizierung der erkannten DNS-Server muessen stabil bleiben.

## Performance Vorher

- Commit vorher: `d2c618ce`
- Messbedingungen: direkter Aufruf von `parse_active_dns_servers`, `parse_link_sections` und `dns_sources_for_sections` mit synthetischem `resolvectl`-Text, `time.perf_counter()`, 100 Wiederholungen.
- `dns_resolvectl_parsers`: Median `0.021 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer DNS-Server-Folgezeilen ergaenzen.
- Gemeinsame Erkennung von DNS-Server-Folgezeilen in einen internen Helper extrahieren.
- DNS-/NetworkManager-Schreibpfade, `resolvectl`-Aufrufe und UI-Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_dns_server_continuation_tokens` fuer DNS-Server-Folgezeilen eingefuehrt.
- `parse_active_dns_servers` nutzt diesen Helper fuer mehrzeilige DNS-Server-Bloecke.
- `parse_link_sections` nutzt denselben Helper fuer Link-spezifische DNS-Server-Bloecke.
- Keine DNS-/NetworkManager-Schreibpfade, `resolvectl`-Aufrufe oder UI-Callbacks geaendert.
- Black hat in derselben Service-Datei mehrere bestehende lange Zeilen rein formatiert.

## Unveraendertes Sollverhalten

- DNS-Server aus `Current DNS Server:` und `DNS Servers:` werden weiterhin gesammelt.
- DNS-Server-Folgezeilen werden weiterhin nur akzeptiert, wenn alle Tokens wie DNS-Werte aussehen.
- Nicht-DNS-Folgezeilen beenden weiterhin das Sammeln.
- DNS-Serverlisten werden weiterhin dedupliziert und sortiert.
- VPN-/physische Link-Sektion-Zuordnung bleibt unveraendert.

## Betroffene Dateien

- `netmon/services/dns_control_service.py`
- `tests/test_netmon_dns_consistency.py`
- `docs/refactoring/areas/10-dns-network.md`
- `docs/refactoring/performance/areas/10-dns-network.md`

## Hinzugefuegte Tests

- `test_parse_active_dns_servers_includes_continuation_lines`
- `test_parse_link_sections_stops_dns_collection_on_non_dns_line`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_dns_consistency.py`: `128 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/services/dns_control_service.py tests/test_netmon_dns_consistency.py`: bestanden
- `.venv/bin/python -m ruff check netmon/services/dns_control_service.py tests/test_netmon_dns_consistency.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/services/dns_control_service.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_netmon_dns_consistency.py`: bestanden
- `.venv/bin/python -m pytest tests/test_netmon_dns_consistency.py`: `128 passed`
- `.venv/bin/python -m pytest tests/test_netmon_dns_consistency.py tests/test_dot_controller.py tests/test_netmon_killswitch.py`: `187 passed`

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2179 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: bestanden ausserhalb der Sandbox wegen `xvfb-run`/Tk-Displayzugriff

## Performance Nachher

- `dns_resolvectl_parsers`: Median `0.022 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische `resolvectl`-Ausgaben.
- Der GUI-Smoke prueft Startbarkeit, aber keine komplette DNS-Policy-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `10-dns-network`.
