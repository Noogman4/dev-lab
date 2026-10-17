# 13 Radio Marker Drag Event Callback Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des Drag-Event-Callbacks fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` baut weiterhin alle Marker-Callbacks in derselben Reihenfolge.
- `_build_radio_pane_marker_drag_event_callback` ruft nur `drag_event_callback_factory(drag_state, pane, place_marker, schedule_marker_update)` auf.
- Der Standard-Factory bleibt `_make_radio_pane_marker_drag_event_callback`.
- Der Drag-End-Callback bleibt unveraendert.

## Risiken

- Drag-State, Pane, Place-Callback und Schedule-Callback muessen unveraendert an die Drag-Event-Factory gehen.
- Die Callback-Build-Reihenfolge darf sich nicht aendern.
- Fehler der Factory duerfen nicht geschluckt werden.
- Echte Tk-Drag-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `9924879a`
- Messbedingungen: Dummy-Factory mit Drag-State, Pane, Place-Callback und Schedule-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_event_callback_build`: best of 5 `24 ns`

## Geplante kleine Aenderung

- Drag-Event-Callback-Aufbau in `_build_radio_pane_marker_drag_event_callback` extrahieren.
- Direkten Test fuer die Factory-Weitergabe ergaenzen.
- `_build_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_drag_event_callback` eingefuehrt.
- `_build_radio_pane_marker_callbacks` nutzt den neuen Helper fuer den Drag-Event-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Drag-Event-Callback wird weiterhin nach dem Drag-Start-Callback gebaut.
- Drag-State, Pane, Place-Callback und Schedule-Callback werden weiterhin an die Drag-Event-Factory uebergeben.
- Der Drag-End-Callback behaelt seine bisherigen Abhaengigkeiten.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-event-callback-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-event-callback-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_drag_event_callback_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `271 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `272 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2349 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_event_callback_build`: best of 5 `45 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Factory statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-event-callback-build`.
