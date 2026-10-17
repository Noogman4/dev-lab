# 13 Standalone Radio Marker Activation Schedule

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: initiales Marker-Update nach Standalone-Marker-Aktivierung separat schedulen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` bindet weiterhin zuerst alle Marker-Callbacks.
- `_standalone_radio_pane_schedule_active_marker_initial_update` ruft nur `initial_update_scheduler(container, update_marker)` auf.
- Der Standard-Scheduler bleibt `_standalone_radio_pane_schedule_initial_marker_update`.
- Reihenfolge Bindung vor initialem Scheduling bleibt unveraendert.

## Risiken

- Das initiale Scheduling darf erst nach erfolgreicher Bindung erfolgen.
- Fehler beim Binden duerfen das Scheduling weiterhin verhindern.
- Fehler des Schedulers duerfen nicht geschluckt werden.
- Echte Tk-Scheduling-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `fa136460`
- Messbedingungen: Dummy-Scheduler mit Container und Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_activation_schedule_inline`: best of 5 `64 ns`

## Geplante kleine Aenderung

- Initiales Scheduling in `_standalone_radio_pane_schedule_active_marker_initial_update` extrahieren.
- Direkten Test fuer die Parameterweitergabe ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_schedule_active_marker_initial_update` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper nach dem Binding.
- Test fuer Weiterreichen von `container` und `update_marker` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Callback-Bindung erfolgt weiterhin vor dem initialen Scheduling.
- Initialer Scheduler erhaelt weiterhin `(container, update_marker)`.
- Fehler beim Binding verhindern weiterhin das Scheduling.
- Initiales Update bleibt beim bestehenden Scheduler.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-activation-schedule.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-activation-schedule.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_schedule_active_marker_initial_update_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `157 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `158 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2394 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_activation_schedule_helper`: best of 5 `95 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Scheduler statt echter Tk-Scheduling-Aufrufe.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-activation-schedule`.
