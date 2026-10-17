# 13 Standalone Radio Marker Binding Spec Helpers

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Buendels: Update- und Grip-Binding-Event-Spezifikationen aus den Binding-Buildern herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkte Aufrufer: `_standalone_radio_pane_update_bindings`, `_standalone_radio_pane_grip_bindings`

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_binding_specs` eingefuehrt.
- `_standalone_radio_pane_grip_binding_specs` eingefuehrt.
- Update-Bindings bauen ihre Event-Liste aus dem Update-Spec-Helper.
- Grip-Bindings bauen ihre Event-Liste aus dem Grip-Spec-Helper.
- Tests fuer Standard-Specs und Custom-Specs ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Update-Bindings bleiben `Configure`, `ButtonRelease-1`, `B1-Motion`.
- Grip-Bindings bleiben `Button-1`, `B1-Motion`, `ButtonRelease-1`.
- Callbacks werden weiterhin in derselben Reihenfolge zugeordnet.
- Nachgelagerte Binding-Plan-Erzeugung bleibt strukturell unveraendert.

## Risiken

- Event-Reihenfolge muss stabil bleiben.
- Grip-Events muessen weiterhin zu Start-, Drag- und End-Callback passen.
- Custom-Specs duerfen nur Tests betreffen; Standardpfad bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-spec-helpers.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-spec-helpers.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_binding_specs_use_update_events`
- `test_standalone_radio_pane_update_bindings_use_custom_specs`
- `test_standalone_radio_pane_grip_binding_specs_use_drag_events`
- `test_standalone_radio_pane_grip_bindings_use_custom_specs`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `249 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `253 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2489 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance

- Vorher, Commit `d6598a85`: beide Binding-Builder zusammen best of 5 `156 ns`
- Nachher: beide Binding-Builder zusammen best of 5 `676 ns`

## Bewertung

- Die Event-Spezifikationen sind separat testbar.
- Die Dummy-Operation bleibt unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-spec-helpers`.
