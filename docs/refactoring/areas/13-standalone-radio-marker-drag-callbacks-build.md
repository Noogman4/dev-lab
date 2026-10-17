# 13 Standalone Radio Marker Drag Callbacks Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Start-, Drag- und End-Callback-Bau aus dem Standalone-Radio-Pane-Marker-Callback-Orchestrator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Drag-State-Bau bleibt bei `_standalone_radio_pane_drag_state`.
- Sash-, Place-, Update- und Schedule-Callback-Bau bleiben im Marker-Callback-Orchestrator.
- Start-, Drag- und End-Callbacks werden weiterhin mit denselben Buildern erzeugt.
- Marker-Parts-Installation und Binding-Aktivierung bleiben unveraendert.

## Risiken

- Start-Callback muss weiterhin vor Drag- und End-Callback gebaut werden.
- Drag-Callback muss weiterhin Drag-State, Sash-Setter, Place-Callback und Schedule-Callback erhalten.
- End-Callback muss weiterhin `update_marker` erhalten.
- Fehler aus dem Drag-Callback-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `d1f5b590`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_callbacks_current`: best of 5 `667 ns`

## Geplante kleine Aenderung

- Start-, Drag- und End-Callback-Bau in `_standalone_radio_pane_marker_drag_callbacks` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Marker-Callback-Test auf Drag-Callback-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_drag_callbacks` eingefuehrt.
- `_standalone_radio_pane_marker_callbacks` nutzt den neuen Drag-Callback-Helper.
- Tests fuer Drag-Callback-Bau, Fehlerpropagation und Marker-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- `update_marker` bleibt erstes Element des Callback-Tuples.
- Start-, Drag- und End-Callbacks bleiben in derselben Rueckgabe-Reihenfolge.
- Schedule-Callback wird weiterhin vor dem Drag-Callback-Bau erzeugt.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-callbacks-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-callbacks-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_drag_callbacks_builds_callbacks_in_order`
- `test_standalone_radio_pane_marker_drag_callbacks_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `196 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `198 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2434 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_callbacks_drag_helper`: best of 5 `496 ns`

## Bewertung

- Der Drag-Callback-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-callbacks-build`.
