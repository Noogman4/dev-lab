# 13 Standalone Radio Marker Callback Tuple

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: finale Callback-Tuple-Zusammensetzung aus dem Standalone-Radio-Pane-Marker-Callback-Orchestrator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Basis-Callback-Bau bleibt bei `_standalone_radio_pane_marker_base_callbacks`.
- Drag-Callback-Bau bleibt bei `_standalone_radio_pane_marker_drag_callbacks`.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.
- Binding-Aktivierung bleibt unveraendert.

## Risiken

- `update_marker` muss weiterhin erstes Element des finalen Callback-Tuples bleiben.
- Start-, Drag- und End-Callbacks muessen weiterhin in derselben Reihenfolge folgen.
- Ungueltige Drag-Callback-Tuples duerfen nicht stillschweigend akzeptiert werden.
- Fehler aus der Tuple-Zusammensetzung duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `32ef8c66`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_callbacks_current`: best of 5 `217 ns`

## Geplante kleine Aenderung

- Finale Callback-Tuple-Zusammensetzung in `_standalone_radio_pane_marker_callback_tuple` extrahieren.
- Direkte Tests fuer Tuple-Zusammensetzung und ungueltige Drag-Callbacks ergaenzen.
- Marker-Callback-Test auf Basis-, Drag- und Tuple-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_callback_tuple` eingefuehrt.
- `_standalone_radio_pane_marker_callbacks` nutzt den neuen Tuple-Helper.
- Tests fuer Tuple-Zusammensetzung, Fehlerfall und Orchestrator-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Das finale Callback-Tuple bleibt `(update_marker, start_drag, drag, end_drag)`.
- Basis-Callbacks werden weiterhin vor Drag-Callbacks gebaut.
- Drag-Callbacks werden weiterhin vor der finalen Tuple-Zusammensetzung gebaut.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-callback-tuple.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-callback-tuple.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_callback_tuple_combines_callbacks`
- `test_standalone_radio_pane_marker_callback_tuple_rejects_invalid_callbacks`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `216 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `218 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2454 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_callbacks_tuple_helper`: best of 5 `257 ns`

## Bewertung

- Die finale Callback-Tuple-Zusammensetzung ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-callback-tuple`.
