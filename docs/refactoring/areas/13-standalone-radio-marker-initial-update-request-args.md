# 13 Standalone Radio Marker Initial Update Request Args

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Argumentbildung fuer den Initial-Update-Request des Standalone-Radio-Pane-Markers herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_schedule_initial_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Initial-Update-Request bleibt bei `_standalone_radio_pane_request_initial_marker_update`.
- Aktiver Initial-Update-Scheduler bleibt bei `_standalone_radio_pane_schedule_active_marker_initial_update`.
- Callback-Aktivierung bleibt bei `_standalone_radio_pane_activate_marker_callbacks`.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- Container und Update-Callback muessen weiterhin unveraendert an `request_update` gehen.
- Ungueltige Request-Argumente duerfen nicht stillschweigend akzeptiert werden.
- Fehler aus dem Request-Aufruf duerfen nicht geschluckt werden.
- Die Reihenfolge im aktiven Callback-Aktivator bleibt unveraendert.

## Performance Vorher

- Commit vorher: `5d52a349`
- Messbedingungen: Dummy-Container, Dummy-Update-Callback, Dummy-Request, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_initial_update_request_current`: best of 5 `71 ns`

## Geplante kleine Aenderung

- Initial-Update-Request-Argumente in `_standalone_radio_pane_initial_update_request_args` extrahieren.
- Direkte Tests fuer Argument-Zusammensetzung und ungueltige Argumente ergaenzen.
- Initial-Update-Scheduler auf Argument-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_initial_update_request_args` eingefuehrt.
- `_standalone_radio_pane_schedule_initial_marker_update` nutzt den neuen Argument-Helper.
- Tests fuer Argument-Reihenfolge, Fehlerfall und Request-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Der Initial-Update-Request wird weiterhin mit Container und Update-Callback aufgerufen.
- Fehler aus ungueltigen Argumenten oder Request-Aufruf werden weiterhin propagiert.
- Der aktive Callback-Aktivator plant das initiale Marker-Update weiterhin nach dem Binding.
- Der oeffentliche Marker-Installer bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-initial-update-request-args.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-initial-update-request-args.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_initial_update_request_args_combines_arguments`
- `test_standalone_radio_pane_schedule_initial_marker_update_rejects_invalid_args`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `240 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `242 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2478 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_initial_update_request_args`: best of 5 `116 ns`

## Bewertung

- Die Argumentbildung ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Request-Funktionen statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-initial-update-request-args`.
