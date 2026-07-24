# 13 Standalone Radio Marker Initial Update Schedule

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: initiales Marker-Update-Scheduling fuer den Standalone-Radio-Pane-Marker vom Request trennen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Der Scheduler delegiert weiterhin an den bestehenden Initial-Update-Request.
- Der Request nutzt weiterhin `container.after(0, update_marker)`.
- Fehler-Toleranz bleibt im Request-Helper.
- Binding-Installation, Drag-Callbacks und Marker-Update-Logik bleiben unveraendert.

## Risiken

- Der Scheduler muss `container` und `update_marker` unveraendert weiterreichen.
- Fehlerverhalten darf nicht vom Request in den Scheduler verschoben werden.
- Der Installer muss weiterhin den Scheduler nach der Binding-Installation aufrufen.
- Der Marker muss weiterhin am Ende des Installers zurueckgegeben werden.

## Performance Vorher

- Commit vorher: `f28a524c`
- Messbedingungen: direkter Request-Aufruf mit Dummy-Container und Dummy-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_initial_update_schedule_inline`: best of 5 `66 ns`

## Geplante kleine Aenderung

- Initial-Update-Scheduling in `_standalone_radio_pane_schedule_initial_marker_update` extrahieren.
- Direkten Test fuer Delegation an den Request-Helper ergaenzen.
- `_install_pane_drag_marker` auf den neuen Scheduler umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_schedule_initial_marker_update` eingefuehrt.
- `_install_pane_drag_marker` delegiert das initiale Scheduling an den neuen Helper.
- Test fuer Weiterreichen von `container` und `update_marker` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur, Binding- oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Initiales Marker-Update wird weiterhin ueber den bestehenden Request geplant.
- `after(0, update_marker)` bleibt der konkrete Request-Pfad.
- Fehler beim initialen Request werden weiterhin ignoriert.
- Drag- und Binding-Verhalten bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-initial-update-schedule.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-initial-update-schedule.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_schedule_initial_marker_update_delegates_request`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `156 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `157 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2393 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_initial_update_schedule_helper`: best of 5 `94 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-initial-update-schedule`.
