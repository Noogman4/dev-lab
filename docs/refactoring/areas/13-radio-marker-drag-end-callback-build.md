# 13 Radio Marker Drag End Callback Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des Drag-End-Callbacks fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_pane_marker_callbacks`

## Abhaengigkeiten und Seiteneffekte

- `_build_radio_pane_marker_callbacks` baut weiterhin alle Marker-Callbacks in derselben Reihenfolge.
- `_build_radio_pane_marker_drag_end_callback` ruft nur `drag_end_callback_factory(update_marker)` auf.
- Der Standard-Factory bleibt `_make_radio_pane_marker_drag_end_callback`.
- Die Rueckgabe von `_RadioPaneMarkerCallbacks` bleibt unveraendert.

## Risiken

- Update-Callback muss unveraendert an die Drag-End-Factory gehen.
- Die Callback-Build-Reihenfolge darf sich nicht aendern.
- Fehler der Factory duerfen nicht geschluckt werden.
- Echte Tk-Drag-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `a91ca078`
- Messbedingungen: Dummy-Factory mit Update-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_end_callback_build`: best of 5 `20 ns`

## Geplante kleine Aenderung

- Drag-End-Callback-Aufbau in `_build_radio_pane_marker_drag_end_callback` extrahieren.
- Direkten Test fuer die Factory-Weitergabe ergaenzen.
- `_build_radio_pane_marker_callbacks` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_drag_end_callback` eingefuehrt.
- `_build_radio_pane_marker_callbacks` nutzt den neuen Helper fuer den Drag-End-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Der Drag-End-Callback wird weiterhin zuletzt gebaut.
- Update-Callback wird weiterhin an die Drag-End-Factory uebergeben.
- `_RadioPaneMarkerCallbacks` enthaelt weiterhin Update-, Start-, Drag- und End-Callback.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-end-callback-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-end-callback-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_drag_end_callback_forwards_dependencies`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `272 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `273 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2350 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_end_callback_build`: best of 5 `38 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Factory statt echter Tk-Callbacks.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-end-callback-build`.
