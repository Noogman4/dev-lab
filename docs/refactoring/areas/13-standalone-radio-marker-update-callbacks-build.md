# 13 Standalone Radio Marker Update Callbacks Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Place-, Update- und Schedule-Callback-Bau aus dem Basis-Callback-Helper herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_base_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Drag-Setup bleibt bei `_standalone_radio_pane_marker_drag_setup`.
- Place-Callback-Bau bleibt bei `_standalone_radio_pane_place_callback`.
- Update-Callback-Bau bleibt bei `_standalone_radio_pane_update_callback`.
- Schedule-Callback-Bau bleibt bei `_standalone_radio_pane_schedule_callback`.

## Risiken

- Place-Callback muss weiterhin Container, Marker und `y_offset` erhalten.
- Update-Callback muss weiterhin Pane, Place-Callback und Marker erhalten.
- Schedule-Callback muss weiterhin Container, Drag-State und `update_marker` erhalten.
- Fehler aus dem Update-Callback-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `6fa905d9`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_base_callbacks_current`: best of 5 `396 ns`

## Geplante kleine Aenderung

- Place-, Update- und Schedule-Callback-Bau in `_standalone_radio_pane_marker_update_callbacks` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Basis-Callback-Test auf Update-Callback-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_update_callbacks` eingefuehrt.
- `_standalone_radio_pane_marker_base_callbacks` nutzt den neuen Update-Callback-Helper.
- Tests fuer Update-Callback-Bau, Fehlerpropagation und Basis-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Place-, Update- und Schedule-Callbacks bleiben in derselben Reihenfolge.
- Drag-State und Sash-Setter bleiben erste Werte des Basis-Callback-Tuples.
- Der Marker-Callback-Orchestrator gibt weiterhin dasselbe finale Callback-Tuple zurueck.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-update-callbacks-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-update-callbacks-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_update_callbacks_builds_callbacks_in_order`
- `test_standalone_radio_pane_marker_update_callbacks_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `202 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `204 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2440 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_base_callbacks_update_helper`: best of 5 `271 ns`

## Bewertung

- Der Update-Callback-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-update-callbacks-build`.
