# 13 Radio Marker Update Request

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Scheduling-Request fuer Radio-Pane-Marker-Updates
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Drag-Motion-Scheduling

## Abhaengigkeiten und Seiteneffekte

- Update-Scheduling laeuft weiterhin ueber `_schedule_radio_pane_marker_update`.
- Pending-Updates werden weiterhin nicht doppelt geplant.
- `update_pending` wird weiterhin vor dem Idle-Callback gesetzt und danach zurueckgesetzt.
- Drag-Motion, Bindings und Initial-Update bleiben unveraendert.

## Risiken

- Der Pending-Guard darf nicht umgangen werden.
- Der Helper muss denselben Drag-State mutieren wie bisher.
- Fehlerbehandlung im bestehenden Scheduler darf nicht veraendert werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `e5bc8709`
- Messbedingungen: Dummy-Container, Dict-State und Dummy-Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_request`: best of 5 `210 ns`

## Geplante kleine Aenderung

- Scheduling-Request in `_request_radio_pane_marker_update` extrahieren.
- Direkte Tests fuer normalen Request und Pending-Request ergaenzen.
- Scheduler-Implementierung und Drag-Motion-Callback unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_request_radio_pane_marker_update` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Schedule-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Motion plant weiterhin ein Marker-Update.
- Pending-Updates werden weiterhin uebersprungen.
- Idle-Callback setzt `update_pending` weiterhin zurueck.
- Fallback bei `after_idle`-Fehlern bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-request.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-request.md`

## Hinzugefuegte Tests

- `test_request_radio_pane_marker_update_schedules_update`
- `test_request_radio_pane_marker_update_keeps_pending_update`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `188 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `190 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2267 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_request`: best of 5 `232 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Idle-Verarbeitung.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-request`.
