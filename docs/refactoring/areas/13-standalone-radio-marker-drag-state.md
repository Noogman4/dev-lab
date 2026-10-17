# 13 Standalone Radio Marker Drag State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-State des Standalone-Radio-Pane-Markers aus dem monolithischen Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` baut weiterhin Marker, Grip, Callbacks und Bindings.
- `_standalone_radio_pane_drag_state` erstellt nur den initialen Drag-State.
- Keine Tk-Widgets werden im neuen Helper erzeugt.
- Die Source-basierte Marker-Breiten-Referenz bleibt in `_install_pane_drag_marker` erhalten.

## Risiken

- Die drei Startwerte muessen unveraendert bleiben.
- Jeder Aufruf muss ein eigenes Dict liefern.
- Bestehende Callback-Closures muessen weiter dasselbe State-Dict verwenden.
- Standalone-UI-Source-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `310cc8d2`
- Messbedingungen: direkter Dict-Aufbau mit Dummy-Werten, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_drag_state_inline`: best of 5 `51 ns`

## Geplante kleine Aenderung

- Drag-State-Aufbau in `_standalone_radio_pane_drag_state` extrahieren.
- Direkten Test fuer Startwerte und eigene Dict-Instanzen ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_drag_state` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper fuer `drag_state`.
- Neuer Test `test_standalone_radio_pane_drag_state_uses_initial_values` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- `root_y` startet weiterhin mit `0`.
- `sash_y` startet weiterhin mit `0`.
- `update_pending` startet weiterhin mit `False`.
- Der Standalone-Marker wird weiterhin von `_install_pane_drag_marker` installiert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-state.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-state.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_drag_state_uses_initial_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `121 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `122 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2358 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_drag_state_helper`: best of 5 `67 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen nur den State-Helper, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-state`.
