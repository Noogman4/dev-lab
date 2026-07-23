# 13 Radio Marker Place Invoke

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Weitergabe von Container, Marker und Sash-Y an den Marker-Placer
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_make_radio_pane_marker_place_callback`

## Abhaengigkeiten und Seiteneffekte

- `_make_radio_pane_marker_place_callback` bindet weiterhin Container und Marker in einer Closure.
- `_invoke_radio_pane_marker_placer` ruft nur `marker_placer(container, marker, sash_y)` auf.
- Marker-Placement und Fehlerbehandlung bleiben unveraendert.
- Der Standard-Placer bleibt `_place_radio_pane_marker_for_sash`.

## Risiken

- Die Reihenfolge der weitergegebenen Argumente muss exakt unveraendert bleiben.
- Der Placer muss weiterhin bei jedem Callback-Aufruf neu ausgefuehrt werden.
- Fehler des Placer duerfen nicht geschluckt werden.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `87a39681`
- Messbedingungen: Dummy-Placer mit Container, Marker und Sash-Y, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_place_invoke`: best of 5 `23 ns`

## Geplante kleine Aenderung

- Placer-Aufruf in `_invoke_radio_pane_marker_placer` extrahieren.
- Direkten Test fuer die Parameterweitergabe ergaenzen.
- `_make_radio_pane_marker_place_callback` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_invoke_radio_pane_marker_placer` eingefuehrt.
- `_make_radio_pane_marker_place_callback` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container und Marker bleiben im Callback gebunden.
- Der Sash-Wert wird weiterhin bei jedem Callback-Aufruf weitergegeben.
- Der Placer wird weiterhin mit `(container, marker, sash_y)` aufgerufen.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-place-invoke.md`
- `docs/refactoring/performance/areas/13-radio-marker-place-invoke.md`

## Hinzugefuegte Tests

- `test_invoke_radio_pane_marker_placer_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `260 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `261 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2338 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_place_invoke`: best of 5 `43 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Placer statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-place-invoke`.
