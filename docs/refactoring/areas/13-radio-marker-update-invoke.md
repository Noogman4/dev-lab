# 13 Radio Marker Update Invoke

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Weitergabe von Pane, Place-Callback, Marker und Event an den Update-Handler
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_make_radio_pane_marker_update_callback`

## Abhaengigkeiten und Seiteneffekte

- `_make_radio_pane_marker_update_callback` bindet weiterhin Pane, Place-Callback und Marker in einer Closure.
- `_invoke_radio_pane_marker_update_handler` ruft nur `update_handler(pane, place_marker, marker, event)` auf.
- Der Standard-Handler bleibt `_handle_radio_pane_marker_update_event`.
- Marker-Placement und Fehlerbehandlung bleiben unveraendert.

## Risiken

- Die Reihenfolge der weitergegebenen Argumente muss exakt unveraendert bleiben.
- Das Default-Event `None` muss weiterhin an den Handler gelangen.
- Fehler des Handlers duerfen nicht geschluckt werden.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `7a2bf2fc`
- Messbedingungen: Dummy-Update-Handler mit Pane, Place-Callback, Marker und Event, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_invoke`: best of 5 `24 ns`

## Geplante kleine Aenderung

- Update-Handler-Aufruf in `_invoke_radio_pane_marker_update_handler` extrahieren.
- Direkten Test fuer die Parameterweitergabe ergaenzen.
- `_make_radio_pane_marker_update_callback` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_invoke_radio_pane_marker_update_handler` eingefuehrt.
- `_make_radio_pane_marker_update_callback` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Pane, Place-Callback und Marker bleiben im Callback gebunden.
- Das Event wird weiterhin bei jedem Callback-Aufruf weitergegeben.
- Ohne Event wird weiterhin `None` an den Handler uebergeben.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-invoke.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-invoke.md`

## Hinzugefuegte Tests

- `test_invoke_radio_pane_marker_update_handler_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `261 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `262 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2339 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_invoke`: best of 5 `45 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Handler statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-invoke`.
