# 13 Standalone Radio Marker Activation Args

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Aktivierungsargumente aus dem Standalone-Radio-Pane-Marker-Parts-Aktivator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_activate_marker_parts`

## Abhaengigkeiten und Seiteneffekte

- Callback-Bau bleibt bei `_standalone_radio_pane_marker_callbacks`.
- Callback-Tuple-Zusammensetzung bleibt bei `_standalone_radio_pane_marker_callback_tuple`.
- Binding-Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_bindings`.
- Marker-Parts-Installation gibt weiterhin den Marker zurueck.

## Risiken

- Die Aktivierungsargumente muessen Container, Pane und Grip weiterhin vor den Callbacks enthalten.
- `update_marker`, `start_drag`, `drag` und `end_drag` muessen weiterhin in derselben Reihenfolge weitergegeben werden.
- Ungueltige Callback-Tuples duerfen nicht stillschweigend akzeptiert werden.
- Fehler aus Argument-Bau oder Binding-Aktivierung duerfen nicht geschluckt werden.

## Performance Vorher

- Commit vorher: `7dd38579`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Grip, Dummy-Callbacks, Dummy-Aktivator, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_activate_parts_current`: best of 5 `87 ns`

## Geplante kleine Aenderung

- Aktivierungsargumente in `_standalone_radio_pane_marker_activation_args` extrahieren.
- Direkte Tests fuer Argument-Zusammensetzung und ungueltige Callback-Tuples ergaenzen.
- Parts-Aktivator-Test auf Argument-Bau plus Aktivierungsdelegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_activation_args` eingefuehrt.
- `_standalone_radio_pane_activate_marker_parts` nutzt den neuen Argument-Helper.
- Tests fuer Argument-Zusammensetzung, Fehlerfall und Orchestrator-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Binding-Aktivierung erhaelt weiterhin Container, Pane, Grip und die vier Callbacks.
- Die Callback-Reihenfolge bleibt `(update_marker, start_drag, drag, end_drag)`.
- Die Marker-Parts-Installation gibt weiterhin den Marker zurueck.
- Der oeffentliche Installer-Einstieg bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-activation-args.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-activation-args.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_activation_args_combines_arguments`
- `test_standalone_radio_pane_marker_activation_args_rejects_invalid_callbacks`
- `test_standalone_radio_pane_activate_marker_parts_propagates_args_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `218 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `221 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2457 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_activate_parts_activation_args`: best of 5 `136 ns`

## Bewertung

- Die Aktivierungsargumente sind separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Callbacks und Dummy-Aktivatoren statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-activation-args`.
