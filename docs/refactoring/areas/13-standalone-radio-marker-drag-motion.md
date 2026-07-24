# 13 Standalone Radio Marker Drag Motion

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-Motion des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` behandelt Drag-Motion-Fehler weiterhin selbst.
- `_standalone_radio_pane_drag_motion` liest `event.y_root`, `drag_state["root_y"]` und `drag_state["sash_y"]`.
- Der Helper ruft weiterhin Sash-Setzen, Marker-Platzierung und Marker-Update-Scheduling in dieser Reihenfolge auf.
- Keine Binding-, Drag-Start- oder Drag-End-Logik wird veraendert.

## Risiken

- Die Delta-Berechnung muss weiterhin aus aktueller Root-Y-Position minus gespeicherter Root-Y-Position entstehen.
- Die neue Sash-Position muss weiterhin aus gespeicherter Sash-Y-Position plus Delta entstehen.
- Alle Werte muessen weiterhin vor der Rechnung in `int` umgewandelt werden.
- Der lokale Drag-Callback muss weiterhin `"break"` zurueckgeben und Fehler abfangen.

## Performance Vorher

- Commit vorher: `a1ea59fd`
- Messbedingungen: direkter Drag-Motion-Pfad mit Dummy-Event, Dummy-State und No-op-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_motion_inline`: best of 5 `171 ns`

## Geplante kleine Aenderung

- Drag-Motion-Berechnung in `_standalone_radio_pane_drag_motion` extrahieren.
- Direkten Test fuer Delta-Rechnung und Callback-Reihenfolge ergaenzen.
- Lokalen `_drag` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_drag_motion` eingefuehrt.
- Lokaler `_drag` delegiert an den neuen Helper und gibt weiterhin `"break"` zurueck.
- Neuer Test `test_standalone_radio_pane_drag_motion_moves_places_and_schedules` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Start/Drag-End-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Motion verschiebt weiterhin die erste Sash-Position relativ zur Startposition.
- Marker wird weiterhin sofort zur neuen Sash-Position platziert.
- Marker-Update wird weiterhin nach der Bewegung geplant.
- Fehler im Drag-Callback werden weiterhin geschluckt, damit der Tk-Eventfluss stabil bleibt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-motion.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-motion.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_drag_motion_moves_places_and_schedules`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `134 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `135 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2371 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_motion_helper`: best of 5 `199 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-motion`.
