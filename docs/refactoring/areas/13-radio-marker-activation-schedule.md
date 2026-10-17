# 13 Radio Marker Activation Schedule

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: initiales Marker-Update nach Callback-Aktivierung
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_activate_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_activate_radio_pane_marker_callbacks` bindet weiterhin zuerst alle Marker-Callbacks.
- `_schedule_active_radio_pane_marker_initial_update` ruft nur `initial_update_scheduler(container, update_marker)` auf.
- Der Standard-Scheduler bleibt `_schedule_initial_radio_pane_marker_update`.
- Reihenfolge Bindung vor initialem Scheduling bleibt unveraendert.

## Risiken

- Das initiale Scheduling darf erst nach erfolgreicher Bindung erfolgen.
- Fehler beim Binden duerfen das Scheduling weiterhin verhindern.
- Fehler des Schedulers duerfen nicht geschluckt werden.
- Echte Tk-Scheduling-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `1110674d`
- Messbedingungen: Dummy-Scheduler mit Container und Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_activation_schedule`: best of 5 `22 ns`

## Geplante kleine Aenderung

- Initiales Scheduling in `_schedule_active_radio_pane_marker_initial_update` extrahieren.
- Direkten Test fuer die Parameterweitergabe ergaenzen.
- `_activate_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_schedule_active_radio_pane_marker_initial_update` eingefuehrt.
- `_activate_radio_pane_marker_callbacks` nutzt den neuen Helper nach dem Binding.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Callback-Bindung erfolgt weiterhin vor dem initialen Scheduling.
- Initialer Scheduler erhaelt weiterhin `(container, update_marker)`.
- Fehler beim Binding verhindern weiterhin das Scheduling.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-activation-schedule.md`
- `docs/refactoring/performance/areas/13-radio-marker-activation-schedule.md`

## Hinzugefuegte Tests

- `test_schedule_active_radio_pane_marker_initial_update_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `266 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `267 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2344 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_activation_schedule`: best of 5 `40 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Scheduler statt echter Tk-Scheduling-Aufrufe.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-activation-schedule`.
