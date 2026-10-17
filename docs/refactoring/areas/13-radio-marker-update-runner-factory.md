# 13 Radio Marker Update Runner Factory

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Factory fuer den geplanten Pane-Drag-Marker-Update-Runner
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_schedule_radio_pane_marker_update`

## Abhaengigkeiten und Seiteneffekte

- Der eigentliche Update-Run erfolgt weiterhin ueber `_run_radio_pane_marker_update`.
- Scheduling erfolgt weiterhin ueber `_schedule_radio_pane_marker_update`.
- `after_idle`-Fallback laeuft weiterhin denselben Runner sofort aus.
- Drag-, Binding- und Marker-Placement-Verhalten bleiben unveraendert.

## Risiken

- Der Runner muss weiterhin Drag-State und Update-Callback korrekt binden.
- Der `after_idle`-Callback und der Fallback muessen denselben Runner verwenden.
- Pending-Update-Verhalten darf sich nicht aendern.
- Bestehende Scheduling-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `d58eea3a`
- Messbedingungen: Dummy-Drag-State, Dummy-Update-Callback und Dummy-Runner, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_runner_factory`: best of 5 `59 ns`

## Geplante kleine Aenderung

- Lokale `_run`-Closure in `_make_radio_pane_marker_update_runner` extrahieren.
- Direkten Test fuer die gebundenen Dependencies ergaenzen.
- `_schedule_radio_pane_marker_update` auf die Runner-Factory umstellen.

## Durchgefuehrte Aenderungen

- `_make_radio_pane_marker_update_runner` eingefuehrt.
- `_schedule_radio_pane_marker_update` erzeugt den Runner vor `after_idle`.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pending-Updates werden weiterhin nicht doppelt geplant.
- Neue Updates setzen `update_pending` weiterhin vor dem Scheduling auf `True`.
- Der geplante Runner setzt `update_pending` weiterhin zurueck und ruft danach den Update-Callback.
- Bei `after_idle`-Fehlern laeuft derselbe Runner weiterhin sofort.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-runner-factory.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-runner-factory.md`

## Hinzugefuegte Tests

- `test_make_radio_pane_marker_update_runner_binds_update_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `246 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `247 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2324 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_runner_factory`: best of 5 `177 ns`

## Bewertung

- Der Helper fuegt nur kleinen Closure- und Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-runner-factory`.
