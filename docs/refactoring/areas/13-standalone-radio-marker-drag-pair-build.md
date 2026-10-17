# 13 Standalone Radio Marker Drag Pair Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Start- und Drag-Callback-Bau aus dem Drag-Callback-Helper herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_drag_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Start-Callback-Bau bleibt bei `_standalone_radio_pane_start_callback`.
- Drag-Callback-Bau bleibt bei `_standalone_radio_pane_drag_callback`.
- End-Callback-Bau bleibt bei `_standalone_radio_pane_end_callback`.
- Marker-Callback-Orchestrator und Binding-Aktivierung bleiben unveraendert.

## Risiken

- Start-Callback muss weiterhin vor dem Drag-Callback gebaut werden.
- Drag-Callback muss weiterhin Drag-State, Sash-Setter, Place-Callback und Schedule-Callback erhalten.
- End-Callback muss weiterhin nach dem Drag-Pair gebaut werden.
- Fehler aus dem Drag-Pair-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `c042f754`
- Messbedingungen: Dummy-Drag-State, Dummy-Pane, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_callbacks_current`: best of 5 `334 ns`

## Geplante kleine Aenderung

- Start- und Drag-Callback-Bau in `_standalone_radio_pane_marker_drag_pair` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Drag-Callback-Test auf Pair-plus-End-Callback umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_drag_pair` eingefuehrt.
- `_standalone_radio_pane_marker_drag_callbacks` nutzt den neuen Pair-Helper.
- Tests fuer Drag-Pair-Bau, Fehlerpropagation und Drag-Callback-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Start-, Drag- und End-Callbacks bleiben in derselben Rueckgabe-Reihenfolge.
- Drag-Callback erhaelt weiterhin dieselben vier Eingaben.
- End-Callback erhaelt weiterhin `update_marker`.
- Marker-Callback-Orchestrator gibt weiterhin dasselbe finale Callback-Tuple zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-pair-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-pair-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_drag_pair_builds_start_then_drag`
- `test_standalone_radio_pane_marker_drag_pair_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `208 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `210 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2446 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_callbacks_pair_helper`: best of 5 `266 ns`

## Bewertung

- Der Drag-Pair-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-pair-build`.
