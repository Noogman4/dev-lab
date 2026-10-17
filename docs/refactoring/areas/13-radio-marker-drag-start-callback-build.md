# 13 Radio Marker Drag Start Callback Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des Drag-Start-Callbacks fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` baut weiterhin alle Marker-Callbacks in derselben Reihenfolge.
- `_build_radio_pane_marker_drag_start_callback` ruft nur `drag_start_callback_factory(drag_state, pane)` auf.
- Der Standard-Factory bleibt `_make_radio_pane_marker_drag_start_callback`.
- Drag-Event- und Drag-End-Callbacks bleiben unveraendert.

## Risiken

- Drag-State und Pane muessen unveraendert an die Drag-Start-Factory gehen.
- Die Callback-Build-Reihenfolge darf sich nicht aendern.
- Fehler der Factory duerfen nicht geschluckt werden.
- Echte Tk-Drag-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `c5e7c2df`
- Messbedingungen: Dummy-Factory mit Drag-State und Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_start_callback_build`: best of 5 `21 ns`

## Geplante kleine Aenderung

- Drag-Start-Callback-Aufbau in `_build_radio_pane_marker_drag_start_callback` extrahieren.
- Direkten Test fuer die Factory-Weitergabe ergaenzen.
- `_build_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_drag_start_callback` eingefuehrt.
- `_build_radio_pane_marker_callbacks` nutzt den neuen Helper fuer den Drag-Start-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Drag-Start-Callback wird weiterhin nach dem Schedule-Callback gebaut.
- Drag-State und Pane werden weiterhin an die Drag-Start-Factory uebergeben.
- Alle weiteren Marker-Callbacks behalten ihre bisherigen Abhaengigkeiten.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-start-callback-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-start-callback-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_drag_start_callback_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `270 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `271 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2348 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_start_callback_build`: best of 5 `40 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Factory statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-start-callback-build`.
