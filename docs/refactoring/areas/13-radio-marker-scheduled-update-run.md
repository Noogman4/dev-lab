# 13 Radio Marker Scheduled Update Run

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Ausfuehrung eines geplanten Pane-Drag-Marker-Updates
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_schedule_radio_pane_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Scheduling erfolgt weiterhin ueber `_schedule_radio_pane_marker_update`.
- `update_pending` wird weiterhin vor dem Update-Callback zurueckgesetzt.
- `after_idle`-Fallback laeuft weiterhin sofort.
- Binding-, Drag- und Marker-Placement-Verhalten bleiben unveraendert.

## Risiken

- `update_pending` muss weiterhin vor dem Update-Callback auf `False` stehen.
- Der `after_idle`-Callback muss weiterhin denselben Update-Pfad ausfuehren.
- Fallback bei `after_idle`-Fehlern muss weiterhin sofort ausfuehren.
- Bestehende Scheduling-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `25eaf41d`
- Messbedingungen: Dummy-Drag-State und Dummy-Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_scheduled_update_run`: best of 5 `103 ns`

## Geplante kleine Aenderung

- Ruecksetzen von `update_pending` plus Update-Callback in `_run_radio_pane_marker_update` extrahieren.
- Direkten Test fuer die Reihenfolge ergaenzen.
- `_schedule_radio_pane_marker_update` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_run_radio_pane_marker_update` eingefuehrt.
- Der interne `after_idle`-Callback ruft den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pending-Updates werden weiterhin nicht doppelt geplant.
- Neue Updates setzen `update_pending` weiterhin vor dem Scheduling auf `True`.
- Der geplante Run setzt `update_pending` weiterhin auf `False` und ruft danach den Update-Callback.
- Bei `after_idle`-Fehlern laeuft der Run weiterhin sofort.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-scheduled-update-run.md`
- `docs/refactoring/performance/areas/13-radio-marker-scheduled-update-run.md`

## Hinzugefuegte Tests

- `test_run_radio_pane_marker_update_clears_pending_before_update`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `245 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `246 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2323 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_scheduled_update_run`: best of 5 `70 ns`

## Bewertung

- Der Helper bleibt deutlich unter 1 us.
- Die Messabweichung liegt im Dummy-Pfad und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-scheduled-update-run`.
