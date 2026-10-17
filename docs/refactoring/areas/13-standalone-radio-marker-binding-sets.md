# 13 Standalone Radio Marker Binding Sets

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Update- und Grip-Binding-Sets aus dem Standalone-Radio-Pane-Marker-Binding-Aktivator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_activate_marker_bindings`

## Abhaengigkeiten und Seiteneffekte

- Update-Bindings bleiben bei `_standalone_radio_pane_update_bindings`.
- Grip-Bindings bleiben bei `_standalone_radio_pane_grip_bindings`.
- Binding-Plan bleibt bei `_standalone_radio_pane_marker_binding_plan`.
- Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_callbacks`.

## Risiken

- `update_marker` muss weiterhin nur in die Update-Bindings fliessen.
- `start_drag`, `drag` und `end_drag` muessen weiterhin in derselben Reihenfolge in die Grip-Bindings fliessen.
- Binding-Plan und Aktivierung muessen weiterhin dieselben Ergebnisse erhalten.
- Fehler aus Binding-Set-Bau, Plan-Bau oder Aktivierung duerfen nicht geschluckt werden.

## Performance Vorher

- Commit vorher: `0f45f6be`
- Messbedingungen: Dummy-Widgets, Dummy-Callbacks, Dummy-Binding-Builder, Dummy-Plan-Builder, Dummy-Aktivierung, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_activation_current`: best of 5 `340 ns`

## Geplante kleine Aenderung

- Binding-Set-Bau in `_standalone_radio_pane_marker_binding_sets` extrahieren.
- Direkte Tests fuer Update- und Grip-Binding-Set-Reihenfolge ergaenzen.
- Aktivierungs-Orchestrator auf Binding-Set-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_binding_sets` eingefuehrt.
- `_standalone_radio_pane_activate_marker_bindings` nutzt den neuen Binding-Set-Helper.
- Tests fuer Binding-Set-Bau, Fehlerfall und Orchestrator-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin die Update-Bindings.
- Grip erhaelt weiterhin Start-, Drag- und End-Bindings.
- Binding-Plan wird weiterhin vor der Aktivierung gebaut.
- Initiales Marker-Update wird weiterhin ueber die bestehende Aktivierung geplant.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-sets.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-sets.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_binding_sets_builds_update_then_grip`
- `test_standalone_radio_pane_marker_binding_sets_propagates_builder_failures`
- `test_standalone_radio_pane_activate_marker_bindings_propagates_binding_set_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `226 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `229 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2465 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_activation_sets`: best of 5 `323 ns`

## Bewertung

- Der Binding-Set-Bau ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks und Dummy-Builder statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-sets`.
