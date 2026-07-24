# 13 Radio Marker Drag End Invoke

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Weitergabe des Update-Callbacks an den Drag-End-Handler
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_make_radio_pane_marker_drag_end_callback`

## Abhaengigkeiten und Seiteneffekte

- `_make_radio_pane_marker_drag_end_callback` bindet weiterhin den Update-Callback in einer Closure.
- `_invoke_radio_pane_marker_drag_end_handler` ruft nur `drag_end_handler(update_marker)` auf.
- Der Standard-Handler bleibt `_handle_radio_pane_marker_drag_end`.
- Drag-End-Update und Rueckgabewert bleiben unveraendert.

## Risiken

- Der gebundene Update-Callback muss unveraendert an den Handler gehen.
- Das Handler-Ergebnis muss weiterhin an Tk zurueckgegeben werden.
- Fehler des Handlers duerfen nicht geschluckt werden.
- Echte Tk-Drag-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `b8f7648a`
- Messbedingungen: Dummy-Drag-End-Handler mit Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_end_invoke`: best of 5 `20 ns`

## Geplante kleine Aenderung

- Drag-End-Handler-Aufruf in `_invoke_radio_pane_marker_drag_end_handler` extrahieren.
- Direkten Test fuer die Weitergabe und Rueckgabe ergaenzen.
- `_make_radio_pane_marker_drag_end_callback` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_invoke_radio_pane_marker_drag_end_handler` eingefuehrt.
- `_make_radio_pane_marker_drag_end_callback` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Update-Callback bleibt im Callback gebunden.
- Das Event-Argument bleibt weiterhin ignoriert.
- Der Handler-Rueckgabewert wird weiterhin unveraendert zurueckgegeben.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-end-invoke.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-end-invoke.md`

## Hinzugefuegte Tests

- `test_invoke_radio_pane_marker_drag_end_handler_forwards_update_marker`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `265 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `266 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2343 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_end_invoke`: best of 5 `38 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Handler statt echter Tk-Drag-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-end-invoke`.
