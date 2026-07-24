# 13 Radio Marker Schedule Callback Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des Schedule-Callbacks fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` baut weiterhin alle Marker-Callbacks in derselben Reihenfolge.
- `_build_radio_pane_marker_schedule_callback` ruft nur `schedule_callback_factory(container, drag_state, update_marker)` auf.
- Der Standard-Factory bleibt `_make_radio_pane_marker_schedule_callback`.
- Drag-Callbacks erhalten weiterhin denselben Schedule-Callback.

## Risiken

- Container, Drag-State und Update-Callback muessen unveraendert an die Schedule-Factory gehen.
- Die Callback-Build-Reihenfolge darf sich nicht aendern.
- Fehler der Factory duerfen nicht geschluckt werden.
- Echte Tk-Scheduling-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `46f647ec`
- Messbedingungen: Dummy-Factory mit Container, Drag-State und Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_schedule_callback_build`: best of 5 `23 ns`

## Geplante kleine Aenderung

- Schedule-Callback-Aufbau in `_build_radio_pane_marker_schedule_callback` extrahieren.
- Direkten Test fuer die Factory-Weitergabe ergaenzen.
- `_build_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_schedule_callback` eingefuehrt.
- `_build_radio_pane_marker_callbacks` nutzt den neuen Helper fuer den Schedule-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Schedule-Callback wird weiterhin nach dem Update-Callback gebaut.
- Container, Drag-State und Update-Callback werden weiterhin an die Schedule-Factory uebergeben.
- Alle weiteren Marker-Callbacks behalten ihre bisherigen Abhaengigkeiten.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-schedule-callback-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-schedule-callback-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_schedule_callback_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `269 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `270 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2347 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_schedule_callback_build`: best of 5 `42 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Factory statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-schedule-callback-build`.
