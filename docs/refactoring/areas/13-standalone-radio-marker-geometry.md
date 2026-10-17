# 13 Standalone Radio Marker Geometry

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Geometrie des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` liest weiterhin die Container-Breite und platziert den Marker.
- `_standalone_radio_pane_marker_geometry` berechnet nur `x`, `y`, `width` und `height`.
- Die Marker-Breiten-Logik bleibt unveraendert.
- Die Source-basierte Marker-Breiten-Referenz bleibt in `_install_pane_drag_marker` erhalten.

## Risiken

- Breiten-Clamping muss unveraendert bleiben.
- X-Clamping muss unveraendert bleiben.
- Y-Offset und oberes Y-Clamping muessen unveraendert bleiben.
- Fehler beim echten Tk-Placement muessen weiter im Installer behandelt werden.

## Performance Vorher

- Commit vorher: `462c3385`
- Messbedingungen: direkte Geometrie-Berechnung mit Dummy-Werten, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_geometry_inline`: best of 5 `492 ns`

## Geplante kleine Aenderung

- Geometrie-Berechnung in `_standalone_radio_pane_marker_geometry` extrahieren.
- Direkten Test fuer Zentrierung, Breiten-Clamping, Y-Offset und Y-Clamping ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_geometry` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper und ruft `marker.place(**geometry)` auf.
- Neuer Test `test_standalone_radio_pane_marker_geometry_centers_and_offsets_marker` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Breite bleibt zwischen `42` und `66`.
- X-Position bleibt zentriert und mindestens `8`.
- Y-Position bleibt `sash_y - 5 + y_offset` und mindestens `2`.
- Marker-Hoehe bleibt `12`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-geometry.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-geometry.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_geometry_centers_and_offsets_marker`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `122 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `123 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2359 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_geometry_helper`: best of 5 `538 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die reine Geometrie, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-geometry`.
