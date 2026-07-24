# 13 Standalone Radio Marker Update Pair Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Place- und Update-Callback-Bau aus dem Update-Callback-Helper herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_update_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Place-Callback-Bau bleibt bei `_standalone_radio_pane_place_callback`.
- Update-Callback-Bau bleibt bei `_standalone_radio_pane_update_callback`.
- Schedule-Callback-Bau bleibt bei `_standalone_radio_pane_schedule_callback`.
- Basis-Callback-Orchestrierung bleibt unveraendert.

## Risiken

- Place-Callback muss weiterhin Container, Marker und `y_offset` erhalten.
- Update-Callback muss weiterhin Pane, Place-Callback und Marker erhalten.
- Schedule-Callback muss weiterhin den gebauten `update_marker` erhalten.
- Fehler aus dem Update-Pair-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `503dbca9`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_update_callbacks_current`: best of 5 `338 ns`

## Geplante kleine Aenderung

- Place- und Update-Callback-Bau in `_standalone_radio_pane_marker_update_pair` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Update-Callback-Test auf Pair-Builder plus Schedule-Callback umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_update_pair` eingefuehrt.
- `_standalone_radio_pane_marker_update_callbacks` nutzt den neuen Pair-Helper.
- Tests fuer Update-Pair-Bau, Fehlerpropagation und Update-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Place- und Update-Callback-Reihenfolge bleibt unveraendert.
- Schedule-Callback wird weiterhin nach dem Update-Callback gebaut.
- Basis-Callback-Helper gibt weiterhin dasselbe Tuple zurueck.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-update-pair-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-update-pair-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_update_pair_builds_place_then_update`
- `test_standalone_radio_pane_marker_update_pair_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `204 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `206 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2442 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_update_callbacks_pair_helper`: best of 5 `267 ns`

## Bewertung

- Der Update-Pair-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-update-pair-build`.
