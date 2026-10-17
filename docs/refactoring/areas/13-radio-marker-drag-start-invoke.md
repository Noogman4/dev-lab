# 13 Radio Marker Drag Start Invoke

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Weitergabe von Drag-State, Event und Pane an den Drag-Start-Handler
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_make_radio_pane_marker_drag_start_callback`

## Abhaengigkeiten und Seiteneffekte

- `_make_radio_pane_marker_drag_start_callback` bindet weiterhin Drag-State und Pane in einer Closure.
- `_invoke_radio_pane_marker_drag_start_handler` ruft nur `drag_start_handler(drag_state, event, pane)` auf.
- Der Standard-Handler bleibt `_handle_radio_pane_marker_drag_start`.
- Drag-State-Erfassung und Rueckgabewert bleiben unveraendert.

## Risiken

- Die Reihenfolge der weitergegebenen Argumente muss exakt unveraendert bleiben.
- Das Handler-Ergebnis muss weiterhin an Tk zurueckgegeben werden.
- Fehler des Handlers duerfen nicht geschluckt werden.
- Echte Tk-Drag-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `9091f977`
- Messbedingungen: Dummy-Drag-Start-Handler mit Drag-State, Event und Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_start_invoke`: best of 5 `23 ns`

## Geplante kleine Aenderung

- Drag-Start-Handler-Aufruf in `_invoke_radio_pane_marker_drag_start_handler` extrahieren.
- Direkten Test fuer die Parameterweitergabe und Rueckgabe ergaenzen.
- `_make_radio_pane_marker_drag_start_callback` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_invoke_radio_pane_marker_drag_start_handler` eingefuehrt.
- `_make_radio_pane_marker_drag_start_callback` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-State und Pane bleiben im Callback gebunden.
- Das Event wird weiterhin bei jedem Callback-Aufruf weitergegeben.
- Der Handler-Rueckgabewert wird weiterhin unveraendert zurueckgegeben.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-start-invoke.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-start-invoke.md`

## Hinzugefuegte Tests

- `test_invoke_radio_pane_marker_drag_start_handler_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `263 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `264 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2341 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_start_invoke`: best of 5 `41 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Handler statt echter Tk-Drag-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-start-invoke`.
