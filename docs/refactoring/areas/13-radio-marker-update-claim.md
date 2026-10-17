# 13 Radio Marker Update Claim

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Claiming eines geplanten Pane-Drag-Marker-Updates
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_schedule_radio_pane_marker_update`

## Abhaengigkeiten und Seiteneffekte

- `update_pending` verhindert weiterhin doppelte geplante Updates.
- Scheduling erfolgt weiterhin ueber `_schedule_radio_pane_marker_update`.
- Runner-Erzeugung und `after_idle`-Request bleiben unveraendert.
- Drag-, Binding- und Marker-Placement-Verhalten bleiben unveraendert.

## Risiken

- Pending-State darf weiterhin kein weiteres Scheduling zulassen.
- Freier State muss weiterhin auf `update_pending=True` gesetzt werden.
- Der Scheduler darf bei fehlgeschlagenem Claim keinen Runner bauen.
- Bestehende Scheduling-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `f0e197a7`
- Messbedingungen: Dummy-Drag-State, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_claim`: best of 5 `32 ns`

## Geplante kleine Aenderung

- Pending-Check und Setzen von `update_pending=True` in `_claim_radio_pane_marker_update` extrahieren.
- Direkte Tests fuer Pending- und freien State ergaenzen.
- `_schedule_radio_pane_marker_update` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_claim_radio_pane_marker_update` eingefuehrt.
- `_schedule_radio_pane_marker_update` nutzt den Claim-Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pending-Updates werden weiterhin nicht doppelt geplant.
- Neue Updates setzen `update_pending` weiterhin vor Runner-Erzeugung auf `True`.
- Geplante Updates laufen weiterhin ueber Runner-Factory und `after_idle`-Request.
- Bei `after_idle`-Fehlern laeuft der Runner weiterhin sofort.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-claim.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-claim.md`

## Hinzugefuegte Tests

- `test_claim_radio_pane_marker_update_skips_pending_state`
- `test_claim_radio_pane_marker_update_marks_available_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `249 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `251 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2328 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_claim`: best of 5 `52 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-claim`.
