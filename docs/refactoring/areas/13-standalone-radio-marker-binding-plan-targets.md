# 13 Standalone Radio Marker Binding Plan Targets

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Buendels: Update- und Grip-Zielplaene aus dem Standalone-Radio-Pane-Marker-Binding-Plan herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_binding_plan`

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_update_binding_plan` eingefuehrt.
- `_standalone_radio_pane_marker_grip_binding_plan` eingefuehrt.
- `_standalone_radio_pane_marker_binding_plan` kombiniert beide Zielplaene.
- Tests fuer Update-Ziele, Grip-Ziel, Delegation und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin dieselben Update-Bindings.
- Grip erhaelt weiterhin die Grip-Bindings.
- Die Reihenfolge bleibt weiterhin Container, Pane, Grip.
- Nachgelagerte Binding-Aktivierung bleibt unveraendert.

## Risiken

- Plan-Konkatenation muss weiterhin Tupel in derselben Reihenfolge liefern.
- Fehler aus Teilplan-Buildern duerfen nicht geschluckt werden.
- Binding-Plan-Consumer duerfen weiterhin dieselbe Struktur erhalten.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-plan-targets.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-plan-targets.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_update_binding_plan_maps_update_targets`
- `test_standalone_radio_pane_marker_grip_binding_plan_maps_grip_target`
- `test_standalone_radio_pane_marker_binding_plan_propagates_plan_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `246 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `249 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2485 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance

- Vorher, Commit `d1d7946a`: `standalone_radio_marker_binding_plan_current` best of 5 `102 ns`
- Nachher: `standalone_radio_marker_binding_plan_targets` best of 5 `172 ns`

## Bewertung

- Das Buendel trennt Zielplanung sauber vom Gesamtplan.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-plan-targets`.
