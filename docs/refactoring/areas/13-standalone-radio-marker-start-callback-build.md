# 13 Standalone Radio Marker Start Callback Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Start-Callback-Bau aus dem Standalone-Radio-Pane-Marker-Drag-Pair herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_drag_pair`

## Abhaengigkeiten und Seiteneffekte

- Start-Callback-Bau bleibt bei `_standalone_radio_pane_start_callback`.
- Drag-Callback-Bau bleibt bei `_standalone_radio_pane_drag_callback`.
- Drag-Pair-Bau gibt weiterhin Start- und Drag-Callback zurueck.
- End-Callback-Bau bleibt bei `_standalone_radio_pane_marker_drag_callbacks`.

## Risiken

- Start-Callback muss weiterhin Drag-State und Pane erhalten.
- Start-Callback muss weiterhin vor dem Drag-Callback gebaut werden.
- Drag-Pair muss weiterhin dasselbe Rueckgabe-Tuple liefern.
- Fehler aus dem Start-Callback-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `9e97a6f3`
- Messbedingungen: Dummy-Drag-State, Dummy-Pane, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_pair_current`: best of 5 `253 ns`

## Geplante kleine Aenderung

- Start-Callback-Bau in `_standalone_radio_pane_marker_start_callback` extrahieren.
- Direkte Tests fuer Builder-Argumente, Rueckgabewert und Fehlerpropagation ergaenzen.
- Drag-Pair-Helfer unveraendert als Start-plus-Drag-Orchestrator lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_start_callback` eingefuehrt.
- `_standalone_radio_pane_marker_drag_pair` nutzt den neuen Start-Callback-Helper als Default-Builder.
- Tests fuer Start-Callback-Bau und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Start- und Drag-Callbacks bleiben in derselben Rueckgabe-Reihenfolge.
- Start-Callback erhaelt weiterhin Drag-State und Pane.
- Drag-Callback erhaelt weiterhin Drag-State, Sash-Setter, Place-Callback und Schedule-Callback.
- Marker-Callback-Orchestrator gibt weiterhin dasselbe finale Callback-Tuple zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-start-callback-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-start-callback-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_start_callback_builds_start_callback`
- `test_standalone_radio_pane_marker_start_callback_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `210 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `212 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2448 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_pair_start_helper`: best of 5 `249 ns`

## Bewertung

- Der Start-Callback-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-start-callback-build`.
