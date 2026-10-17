# 13 Standalone Radio Marker Base Callbacks Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Basis-Callback-Bau aus dem Standalone-Radio-Pane-Marker-Callback-Orchestrator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Drag-State-Bau bleibt bei `_standalone_radio_pane_drag_state`.
- Sash-, Place-, Update- und Schedule-Callback-Bau nutzen weiterhin dieselben Builder.
- Start-, Drag- und End-Callback-Bau bleibt bei `_standalone_radio_pane_marker_drag_callbacks`.
- Marker-Parts-Installation und Binding-Aktivierung bleiben unveraendert.

## Risiken

- Basis-Callbacks muessen weiterhin in derselben Reihenfolge gebaut werden.
- `schedule_marker_update` muss weiterhin Container, Drag-State und `update_marker` erhalten.
- Der Haupt-Orchestrator muss weiterhin dasselbe Callback-Tuple zurueckgeben.
- Fehler aus dem Basis-Callback-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `97e36bc1`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_callbacks_current`: best of 5 `509 ns`

## Geplante kleine Aenderung

- Drag-State-, Sash-, Place-, Update- und Schedule-Callback-Bau in `_standalone_radio_pane_marker_base_callbacks` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Marker-Callback-Test auf Basis- plus Drag-Callback-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_base_callbacks` eingefuehrt.
- `_standalone_radio_pane_marker_callbacks` nutzt den neuen Basis-Callback-Helper.
- Tests fuer Basis-Callback-Bau, Fehlerpropagation und Marker-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- `update_marker` bleibt erstes Element des finalen Callback-Tuples.
- Start-, Drag- und End-Callbacks bleiben in derselben Rueckgabe-Reihenfolge.
- Schedule-Callback wird weiterhin vor dem Drag-Callback-Bau erzeugt.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-base-callbacks-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-base-callbacks-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_base_callbacks_builds_callbacks_in_order`
- `test_standalone_radio_pane_marker_base_callbacks_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `198 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `200 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2436 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_callbacks_base_helper`: best of 5 `203 ns`

## Bewertung

- Der Basis-Callback-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-base-callbacks-build`.
