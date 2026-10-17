# 13 Standalone Radio Marker Binding Spec Materialization

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Update- und Grip-Binding-Spezifikationen explizit materialisieren
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_binding_sets`

## Abhaengigkeiten und Seiteneffekte

- Standard-Eventnamen bleiben unveraendert.
- Callback-Zuordnung bleibt unveraendert.
- Gueltige Custom-Spezifikationen muessen drei Events liefern.
- Ungueltige Custom-Spezifikationen fallen jetzt direkt beim Entpacken auf.

## Risiken

- Zu kurze oder zu lange Test-Doubles erzeugen nun `ValueError`.
- Der echte Pfad nutzt weiterhin die vorhandenen Drei-Event-Spezifikationen.
- Binding-Fehler werden weiterhin erst im bestehenden Bind-Helper toleriert.

## Performance Vorher

- Commit vorher: `d9a3dff1`
- Messbedingungen: Update- und Grip-Bindings mit Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_binding_spec_materialization_before`: best of 5 `0.6737667029997283 s`

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_bindings` entpackt exakt drei Update-Events.
- `_standalone_radio_pane_grip_bindings` entpackt exakt drei Grip-Events.
- Generator- und `zip`-Materialisierung durch direkte Tuple-Erzeugung ersetzt.
- Tests fuer gueltige und ungueltige Custom-Spezifikationen ergaenzt.

## Unveraendertes Sollverhalten

- Container und Pane erhalten weiterhin `Configure`, `ButtonRelease-1` und `B1-Motion`.
- Grip erhaelt weiterhin `Button-1`, `B1-Motion` und `ButtonRelease-1`.
- Callback-Identitaeten bleiben erhalten.
- Es werden keine Tk-Widgets erzeugt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-binding-spec-materialization.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-binding-spec-materialization.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_bindings_rejects_invalid_specs`
- `test_standalone_radio_pane_grip_bindings_rejects_invalid_specs`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `255 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2491 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_binding_spec_materialization_after`: best of 5 `0.2230273440000019 s`

## Bewertung

- Die direkte Tuple-Erzeugung reduziert den gemessenen Micro-Overhead deutlich.
- Der reale GUI-Pfad bleibt weiterhin von Tk-Binding-Arbeit dominiert.
- Die strengere Entpackung macht fehlerhafte Custom-Spezifikationen sichtbar.

## Bekannte Restrisiken

- Tests pruefen die Binding-Tuples ohne echte Tk-Eventausloesung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-binding-spec-materialization`.
