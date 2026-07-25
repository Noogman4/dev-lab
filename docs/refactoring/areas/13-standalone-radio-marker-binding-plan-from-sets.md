# 13 Standalone Radio Marker Binding Plan From Sets

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Binding-Plan-Bau aus Binding-Sets aus dem Standalone-Radio-Pane-Marker-Binding-Aktivator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_activate_marker_bindings`

## Abhaengigkeiten und Seiteneffekte

- Binding-Set-Bau bleibt bei `_standalone_radio_pane_marker_binding_sets`.
- Binding-Plan-Zuordnung bleibt bei `_standalone_radio_pane_marker_binding_plan`.
- Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_callbacks`.
- Event-Binding und initiales Marker-Update bleiben unveraendert.

## Risiken

- Update- und Grip-Bindings muessen weiterhin in derselben Reihenfolge aus dem Binding-Set entpackt werden.
- Container, Pane und Grip muessen weiterhin unveraendert an den Binding-Plan-Builder gehen.
- Aktivierung muss weiterhin Container, Binding-Plan und Update-Callback erhalten.
- Fehler aus Binding-Set-Bau, Plan-Bau oder Aktivierung duerfen nicht geschluckt werden.

## Performance Vorher

- Commit vorher: `0eec7191`
- Messbedingungen: Dummy-Widgets, Dummy-Callbacks, Dummy-Binding-Sets, Dummy-Plan-Builder, Dummy-Aktivierung, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_activation_current`: best of 5 `324 ns`

## Geplante kleine Aenderung

- Binding-Plan-Bau aus Sets in `_standalone_radio_pane_marker_binding_plan_from_sets` extrahieren.
- Direkte Tests fuer Plan-Bau und ungueltige Binding-Sets ergaenzen.
- Aktivierungs-Orchestrator auf Plan-from-Sets-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_binding_plan_from_sets` eingefuehrt.
- `_standalone_radio_pane_activate_marker_bindings` nutzt den neuen Plan-Helper.
- Tests fuer Plan-Bau, Fehlerfall und Orchestrator-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin die Update-Bindings.
- Grip erhaelt weiterhin Start-, Drag- und End-Bindings.
- Binding-Plan wird weiterhin vor der Aktivierung gebaut.
- Initiales Marker-Update wird weiterhin ueber die bestehende Aktivierung geplant.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-plan-from-sets.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-plan-from-sets.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_binding_plan_from_sets_builds_plan`
- `test_standalone_radio_pane_marker_binding_plan_from_sets_rejects_invalid_sets`
- `test_standalone_radio_pane_activate_marker_bindings_propagates_plan_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `229 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `232 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2468 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_activation_plan_from_sets`: best of 5 `268 ns`

## Bewertung

- Der Binding-Plan-Bau aus Sets ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks und Dummy-Builder statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-plan-from-sets`.
