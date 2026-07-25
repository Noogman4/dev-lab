# 13 Standalone Radio Marker Active Callback Bind

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: aktives Binding des Marker-Callback-Plans aus dem Standalone-Radio-Pane-Marker-Callback-Aktivator herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_activate_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Binding-Plan-Bindung bleibt bei `_standalone_radio_pane_bind_marker_callbacks`.
- Initiales Marker-Update bleibt bei `_standalone_radio_pane_schedule_initial_marker_update`.
- Die Reihenfolge bleibt: erst binden, dann initiales Update planen.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- Der Binding-Plan muss weiterhin unveraendert an den Callback-Binder gehen.
- Fehler aus dem Binding duerfen nicht geschluckt werden.
- Das initiale Marker-Update darf erst nach erfolgreichem Binding geplant werden.
- Bestehende Fehlerpropagation aus dem Callback-Binder muss erhalten bleiben.

## Performance Vorher

- Commit vorher: `2d5a9f2d`
- Messbedingungen: Dummy-Container, Dummy-Binding-Plan, Dummy-Update-Callback, Dummy-Binder, Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_activate_callbacks_current`: best of 5 `110 ns`

## Geplante kleine Aenderung

- Aktives Binding in `_standalone_radio_pane_bind_active_marker_callbacks` extrahieren.
- Direkte Tests fuer Binding-Delegation und Fehlerpropagation ergaenzen.
- Callback-Aktivator auf den neuen Binding-Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_bind_active_marker_callbacks` eingefuehrt.
- `_standalone_radio_pane_activate_marker_callbacks` nutzt den neuen Binding-Helper.
- Tests fuer Delegation, Fehlerfall und Orchestrator-Reihenfolge ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Binding passiert weiterhin vor dem initialen Marker-Update.
- Der Binding-Plan wird weiterhin unveraendert gebunden.
- Initiales Marker-Update wird weiterhin ueber den bestehenden Scheduler geplant.
- Fehler aus dem Binding brechen den Aktivierungsablauf weiterhin ab.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-active-callback-bind.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-active-callback-bind.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_bind_active_marker_callbacks_delegates_binder`
- `test_standalone_radio_pane_bind_active_marker_callbacks_propagates_failures`
- `test_standalone_radio_pane_activate_marker_callbacks_propagates_active_binding_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `234 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `237 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2473 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_activate_callbacks_active_bind`: best of 5 `136 ns`

## Bewertung

- Das aktive Binding ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Binder und Dummy-Scheduler statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-active-callback-bind`.
