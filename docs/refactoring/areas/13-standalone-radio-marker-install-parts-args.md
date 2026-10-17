# 13 Standalone Radio Marker Install Parts Args

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Install-Parts-Argumente aus der Standalone-Radio-Pane-Marker-Installation herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_install_marker`

## Abhaengigkeiten und Seiteneffekte

- Widget-Bau bleibt bei `_standalone_radio_pane_marker_widgets`.
- Marker-Parts-Installation bleibt bei `_standalone_radio_pane_install_marker_parts`.
- `_install_pane_drag_marker` bleibt der bestehende API-Einstieg.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` bleibt im API-Einstieg.

## Risiken

- Marker und Grip muessen weiterhin aus dem Widget-Tuple in derselben Reihenfolge entpackt werden.
- Container, Pane, Marker, Grip und `y_offset` muessen unveraendert an `install_parts` gehen.
- Ungueltige Widget-Tuples duerfen nicht stillschweigend akzeptiert werden.
- Fehler aus Widget-Bau, Argument-Bau oder Part-Installation duerfen nicht geschluckt werden.

## Performance Vorher

- Commit vorher: `8a75e6a2`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Grip, Dummy-Builder, Dummy-Installer, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_install_current`: best of 5 `146 ns`

## Geplante kleine Aenderung

- Install-Parts-Argumente in `_standalone_radio_pane_install_marker_parts_args` extrahieren.
- Direkte Tests fuer Argument-Zusammensetzung und ungueltige Widget-Tuples ergaenzen.
- Install-Marker-Test auf Widget-Bau, Argument-Bau und Install-Delegation umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_install_marker_parts_args` eingefuehrt.
- `_standalone_radio_pane_install_marker` nutzt den neuen Argument-Helper.
- Tests fuer Argument-Zusammensetzung, Fehlerfall und Orchestrator-Delegation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin vor der Part-Installation erstellt.
- `install_parts` erhaelt weiterhin Container, Pane, Marker, Grip und `y_offset`.
- `_install_pane_drag_marker` gibt weiterhin den installierten Marker zurueck.
- Der oeffentliche Installer-Einstieg bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-install-parts-args.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-install-parts-args.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_install_marker_parts_args_combines_arguments`
- `test_standalone_radio_pane_install_marker_parts_args_rejects_invalid_widgets`
- `test_standalone_radio_pane_install_marker_propagates_args_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `221 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `224 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2460 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_install_parts_args`: best of 5 `198 ns`

## Bewertung

- Die Install-Parts-Argumente sind separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets und Dummy-Installer statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-install-parts-args`.
