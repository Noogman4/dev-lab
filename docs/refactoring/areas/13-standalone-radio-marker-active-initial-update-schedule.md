# 13 Standalone Radio Marker Active Initial Update Schedule

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: aktives initiales Marker-Update im Standalone-Radio-Pane-Marker-Callback-Aktivator injizierbar machen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_activate_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- Aktives Binding bleibt bei `_standalone_radio_pane_bind_active_marker_callbacks`.
- Initiales Marker-Update bleibt bei `_standalone_radio_pane_schedule_active_marker_initial_update`.
- Die Reihenfolge bleibt: erst binden, dann initiales Update planen.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- Das initiale Marker-Update darf erst nach erfolgreichem Binding geplant werden.
- Container, Update-Callback und Initial-Update-Scheduler muessen unveraendert weitergegeben werden.
- Fehler aus dem aktiven Scheduler duerfen nicht geschluckt werden.
- Bestehende Fehlerpropagation aus dem Binding muss erhalten bleiben.

## Performance Vorher

- Commit vorher: `747c9e9a`
- Messbedingungen: Dummy-Container, Dummy-Binding-Plan, Dummy-Update-Callback, Dummy-Binder, Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_activate_callbacks_current`: best of 5 `137 ns`

## Geplante kleine Aenderung

- `_standalone_radio_pane_activate_marker_callbacks` um den injizierbaren `active_initial_update_scheduler` erweitern.
- Orchestrator-Test auf aktive Initial-Update-Delegation umstellen.
- Fehlerpropagation fuer den aktiven Scheduler ergaenzen.

## Durchgefuehrte Aenderungen

- `active_initial_update_scheduler` als Keyword-only-Dependency eingefuehrt.
- `_standalone_radio_pane_activate_marker_callbacks` nutzt diese Dependency.
- Tests fuer Delegation, Fehlerfall und Reihenfolge ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Binding passiert weiterhin vor dem initialen Marker-Update.
- Der Binding-Plan wird weiterhin unveraendert gebunden.
- Initiales Marker-Update wird weiterhin ueber den bestehenden Scheduler geplant.
- Fehler aus Binding oder Scheduling brechen den Aktivierungsablauf weiterhin ab.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-active-initial-update-schedule.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-active-initial-update-schedule.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_activate_marker_callbacks_propagates_active_schedule_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `237 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `238 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2474 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_activate_callbacks_active_schedule`: best of 5 `141 ns`

## Bewertung

- Der aktive Initial-Update-Scheduler ist im Orchestrator separat kontrollierbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Binder und Dummy-Scheduler statt echter Tk-Bindings.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-active-initial-update-schedule`.
