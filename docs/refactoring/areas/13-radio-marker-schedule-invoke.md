# 13 Radio Marker Schedule Invoke

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Weitergabe von Container, Drag-State und Update-Callback an den Update-Requester
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_make_radio_pane_marker_schedule_callback`

## Abhaengigkeiten und Seiteneffekte

- `_make_radio_pane_marker_schedule_callback` bindet weiterhin Container, Drag-State und Update-Callback in einer Closure.
- `_invoke_radio_pane_marker_update_requester` ruft nur `update_requester(container, drag_state, update_marker)` auf.
- Der Standard-Requester bleibt `_request_radio_pane_marker_update`.
- Scheduling-Logik und Pending-State bleiben unveraendert.

## Risiken

- Die Reihenfolge der weitergegebenen Argumente muss exakt unveraendert bleiben.
- Der Requester muss weiterhin bei jedem Callback-Aufruf neu ausgefuehrt werden.
- Fehler des Requester duerfen nicht geschluckt werden.
- Echte Tk-Scheduling-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `553a6285`
- Messbedingungen: Dummy-Requester mit Container, Drag-State und Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_schedule_invoke`: best of 5 `23 ns`

## Geplante kleine Aenderung

- Update-Requester-Aufruf in `_invoke_radio_pane_marker_update_requester` extrahieren.
- Direkten Test fuer die Parameterweitergabe ergaenzen.
- `_make_radio_pane_marker_schedule_callback` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_invoke_radio_pane_marker_update_requester` eingefuehrt.
- `_make_radio_pane_marker_schedule_callback` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container, Drag-State und Update-Callback bleiben im Callback gebunden.
- Der Requester wird weiterhin bei jedem Callback-Aufruf ausgefuehrt.
- Der Requester wird weiterhin mit `(container, drag_state, update_marker)` aufgerufen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-schedule-invoke.md`
- `docs/refactoring/performance/areas/13-radio-marker-schedule-invoke.md`

## Hinzugefuegte Tests

- `test_invoke_radio_pane_marker_update_requester_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `262 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `263 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2340 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_schedule_invoke`: best of 5 `42 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Requester statt echter Tk-Scheduling-Aufrufe.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-schedule-invoke`.
