# 13 Standalone Radio Marker Initial Update After Args

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: `container.after`-Argumente fuer den Initial-Update-Request herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_request_initial_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Initial-Update-Request bleibt bei `_standalone_radio_pane_request_initial_marker_update`.
- Initial-Update-Scheduler bleibt bei `_standalone_radio_pane_schedule_initial_marker_update`.
- Aktiver Initial-Update-Scheduler bleibt bei `_standalone_radio_pane_schedule_active_marker_initial_update`.
- Widget-Bau, Drag-Logik und sichtbares Marker-Verhalten bleiben unveraendert.

## Risiken

- `container.after` muss weiterhin mit Delay `0` und dem Update-Callback aufgerufen werden.
- Fehler beim Bauen der `after`-Argumente muessen weiterhin im Request-Helper ignoriert werden.
- Fehler aus `container.after` muessen weiterhin ignoriert werden.
- Die Initial-Update-Reihenfolge im Aktivator bleibt unveraendert.

## Performance Vorher

- Commit vorher: `fb91c2b4`
- Messbedingungen: Dummy-Container mit `after`, Dummy-Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_initial_update_after_current`: best of 5 `45 ns`

## Geplante kleine Aenderung

- `container.after`-Argumente in `_standalone_radio_pane_initial_update_after_args` extrahieren.
- Direkte Tests fuer Delay und Callback ergaenzen.
- Request-Test auf Argument-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_initial_update_after_args` eingefuehrt.
- `_standalone_radio_pane_request_initial_marker_update` nutzt den neuen Argument-Helper.
- Tests fuer Argument-Reihenfolge, `after`-Delegation und ignorierten Argument-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Initiales Marker-Update wird weiterhin mit `container.after(0, update_marker)` geplant.
- Fehler aus Argument-Bau oder `after`-Aufruf werden weiterhin ignoriert.
- Der Initial-Update-Scheduler ruft weiterhin den Request-Helper auf.
- Der oeffentliche Marker-Installer bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-initial-update-after-args.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-initial-update-after-args.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_initial_update_after_args_uses_after_zero`
- `test_standalone_radio_pane_request_initial_marker_update_ignores_after_args_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `242 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `244 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2480 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_initial_update_after_args`: best of 5 `88 ns`

## Bewertung

- Die `after`-Argumentbildung ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-initial-update-after-args`.
