# 11 Packet Capture

## Ausgangszustand

- Datei: `netmon/features/packet_capture_controller.py`
- Fokus dieses Schritts: Interface-Ermittlung in `refresh_packet_capture_interfaces`
- Bestehende Tests: `tests/test_packet_capture_controller.py`
- Indirekte Aufrufer: Packet-Capture-Tab, Start-Button-Freigabe, Interface-Auswahl

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt liest nur bereits gelieferte Ausgaben von `tshark -D` und `ip -o link show`.
- Keine Capture-Kommandos fuer Start/Stop geaendert.
- Keine Capture-Dateipfade geaendert.
- Keine Root-Rechte.
- Keine neuen Subprocess-Aufrufe.

## Risiken

- `tshark -D`-Zeilen muessen weiterhin Namen und Detailzeilen liefern.
- `ip -o link show`-Zeilen muessen weiterhin Peer-Suffixe wie `@if3` entfernen.
- Doppelte Interfaces muessen weiterhin in erster Reihenfolge dedupliziert werden.
- Die bevorzugte Interface-Auswahl darf sich nicht aendern.
- Permission-Hinweise fuer `dumpcap` duerfen nicht beeinflusst werden.

## Performance Vorher

- Commit vorher: `47e74ac7`
- Messbedingungen: direkter Aufruf von `refresh_packet_capture_interfaces` mit synthetischem App-Objekt und ersetztem `run_cmd`, `time.perf_counter()`, 100 Wiederholungen.
- `packet_capture_refresh_interfaces`: Median `0.0041 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer `tshark`-/`ip`-Parser und Interface-Deduplizierung ergaenzen.
- Parser fuer `tshark -D` in einen internen Helper extrahieren.
- Parser fuer `ip -o link show` in einen internen Helper extrahieren.
- Interface-Deduplizierung in einen internen Helper extrahieren.
- Capture-Start, Capture-Stop, Dateipfade und UI-Status unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_packet_capture_interfaces_from_tshark_output` eingefuehrt.
- `_packet_capture_interfaces_from_ip_output` eingefuehrt.
- `_packet_capture_unique_interfaces` eingefuehrt.
- `refresh_packet_capture_interfaces` nutzt diese Helper und behaelt die bisherige Ablaufreihenfolge bei.
- Keine Capture-Kommandos, Dateipfade oder Permission-Hinweise geaendert.

## Unveraendertes Sollverhalten

- `tshark -D` bleibt der bevorzugte Interface-Quelle.
- `ip -o link show` bleibt der Fallback, wenn `tshark` keine Interfaces liefert.
- Detailzeilen aus `tshark -D` werden weiterhin im Output angezeigt.
- Das erste Nicht-Loopback-Interface bleibt bevorzugt.
- Der Status `interfaces ready` wird weiterhin nur bei gefundenen Interfaces gesetzt.

## Betroffene Dateien

- `netmon/features/packet_capture_controller.py`
- `tests/test_packet_capture_controller.py`
- `docs/refactoring/areas/11-packet-capture.md`
- `docs/refactoring/performance/areas/11-packet-capture.md`

## Hinzugefuegte Tests

- `test_packet_capture_interfaces_from_tshark_output_extracts_names_and_details`
- `test_packet_capture_interfaces_from_ip_output_strips_peer_suffix`
- `test_packet_capture_unique_interfaces_keeps_first_seen_order`
- `test_refresh_packet_capture_interfaces_deduplicates_tshark_interfaces`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_packet_capture_controller.py`: `99 passed`
- `.venv/bin/python -m ruff check netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/features/packet_capture_controller.py tests/test_packet_capture_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/features/packet_capture_controller.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_packet_capture_controller.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2183 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `packet_capture_refresh_interfaces`: Median `0.0044 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0003 ms` liegt im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Parser-Tests nutzen synthetische Ausgaben von `tshark` und `ip`.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige Live-Capture-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `11-packet-capture`.
