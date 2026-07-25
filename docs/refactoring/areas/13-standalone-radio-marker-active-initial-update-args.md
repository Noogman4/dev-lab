# 13 Standalone Radio Marker Active Initial Update Args

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Argumentbildung fuer den aktiven Initial-Update-Scheduler herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_schedule_active_marker_initial_update`

## Abhaengigkeiten und Seiteneffekte

- Initiales Marker-Update bleibt bei `_standalone_radio_pane_schedule_initial_marker_update`.
- Aktiver Scheduler-Aufruf bleibt in `_standalone_radio_pane_schedule_active_marker_initial_update`.
- Callback-Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_callbacks`.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- Container, Update-Callback und Scheduler muessen weiterhin unveraendert weitergegeben werden.
- Ungueltige aktive Initial-Update-Argumente duerfen nicht stillschweigend akzeptiert werden.
- Fehler aus dem Scheduler duerfen nicht geschluckt werden.
- Die Reihenfolge bleibt: erst aktiver Callback-Bind, dann aktives Initial-Update.

## Performance Vorher

- Commit vorher: `c0d338a4`
- Messbedingungen: Dummy-Container, Dummy-Update-Callback, Dummy-Scheduler, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_active_initial_update_current`: best of 5 `61 ns`

## Geplante kleine Aenderung

- Aktive Initial-Update-Argumente in `_standalone_radio_pane_active_initial_update_args` extrahieren.
- Direkte Tests fuer Argument-Zusammensetzung und ungueltige Argumente ergaenzen.
- Aktiven Initial-Update-Scheduler auf Argument-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_active_initial_update_args` eingefuehrt.
- `_standalone_radio_pane_schedule_active_marker_initial_update` nutzt den neuen Argument-Helper.
- Tests fuer Argument-Reihenfolge, Fehlerfall und Scheduler-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Der Initial-Update-Scheduler wird weiterhin mit Container und Update-Callback aufgerufen.
- Fehler aus ungueltigen Argumenten oder Scheduler-Aufruf werden weiterhin propagiert.
- Callback-Aktivierung plant das initiale Marker-Update weiterhin nach dem Binding.
- Der oeffentliche Marker-Installer bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-active-initial-update-args.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-active-initial-update-args.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_active_initial_update_args_combines_arguments`
- `test_standalone_radio_pane_schedule_active_marker_initial_update_rejects_invalid_args`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `238 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `240 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2476 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_active_initial_update_args`: best of 5 `121 ns`

## Bewertung

- Die Argumentbildung ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Scheduler statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-active-initial-update-args`.
