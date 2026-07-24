# 13 Standalone Radio Marker Schedule Callback Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Schedule-Callback-Bau aus dem Standalone-Radio-Pane-Marker-Update-Callback-Helper herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_update_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Update-Pair-Bau bleibt bei `_standalone_radio_pane_marker_update_pair`.
- Schedule-Callback-Bau nutzt weiterhin `_standalone_radio_pane_schedule_callback`.
- Basis-Callback-Orchestrierung bleibt unveraendert.
- Marker-Callback-Orchestrator und Binding-Aktivierung bleiben unveraendert.

## Risiken

- Schedule-Callback muss weiterhin Container, Drag-State und `update_marker` erhalten.
- Update-Pair muss weiterhin vor dem Schedule-Callback gebaut werden.
- Der Update-Callback-Helper muss weiterhin dasselbe Rueckgabe-Tuple liefern.
- Fehler aus dem Schedule-Callback-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `120ac7c2`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Callbacks, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_update_callbacks_current`: best of 5 `274 ns`

## Geplante kleine Aenderung

- Schedule-Callback-Bau in `_standalone_radio_pane_marker_schedule_callback` extrahieren.
- Direkte Tests fuer Builder-Argumente, Rueckgabewert und Fehlerpropagation ergaenzen.
- Update-Callback-Helper unveraendert als Pair-plus-Schedule-Orchestrator lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_schedule_callback` eingefuehrt.
- `_standalone_radio_pane_marker_update_callbacks` nutzt den neuen Schedule-Helper als Default-Builder.
- Tests fuer Schedule-Callback-Bau und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Update-Pair wird weiterhin vor dem Schedule-Callback gebaut.
- Schedule-Callback erhaelt weiterhin Container, Drag-State und `update_marker`.
- Basis-Callback-Helper gibt weiterhin dasselbe Tuple zurueck.
- Marker-Parts-Installation erhaelt weiterhin dasselbe Callback-Tuple.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-schedule-callback-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-schedule-callback-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_schedule_callback_builds_schedule`
- `test_standalone_radio_pane_marker_schedule_callback_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `206 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `208 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2444 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_update_callbacks_schedule_helper`: best of 5 `266 ns`

## Bewertung

- Der Schedule-Callback-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-schedule-callback-build`.
