# 13 Standalone Radio Marker Place For Sash

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Platzieren des Standalone-Radio-Pane-Markers fuer eine Sash-Position aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` behandelt Placement-Fehler weiterhin selbst.
- `_standalone_radio_pane_place_marker_for_sash` liest die Container-Breite, baut Geometrie und delegiert das Placement.
- Die Source-basierte Marker-Breiten-Referenz bleibt in `_install_pane_drag_marker` erhalten.
- Keine Callback- oder Binding-Logik wird veraendert.

## Risiken

- Die Container-Breite muss weiterhin vor der Geometrie-Berechnung gelesen werden.
- `sash_y` und `y_offset` muessen unveraendert an die Geometrie-Berechnung gehen.
- Das erzeugte Geometrie-Objekt muss unveraendert an den Placement-Helper gehen.
- Fehlerbehandlung muss im Installer erhalten bleiben.

## Performance Vorher

- Commit vorher: `90698310`
- Messbedingungen: direkte Breitenabfrage, Geometrie-Build und Place-Delegation mit Dummy-Objekten, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_place_for_sash_inline`: best of 5 `116 ns`

## Geplante kleine Aenderung

- Place-for-Sash-Pfad in `_standalone_radio_pane_place_marker_for_sash` extrahieren.
- Direkten Test fuer Abhaengigkeitsreihenfolge und Argumentweitergabe ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_place_marker_for_sash` eingefuehrt.
- Lokaler `_place_marker_for_sash` delegiert an den neuen Helper.
- Neuer Test `test_standalone_radio_pane_place_marker_for_sash_builds_geometry_then_places` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Geometrie wird weiterhin aus Container-Breite, Sash-Position und Offset berechnet.
- Marker wird weiterhin mit der berechneten Geometrie platziert und angehoben.
- Fehler beim Platzieren werden weiterhin im Installer abgefangen und fuehren zum Forget-Fallback.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-place-for-sash.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-place-for-sash.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_place_marker_for_sash_builds_geometry_then_places`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `127 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `128 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2364 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_place_for_sash_helper`: best of 5 `157 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-place-for-sash`.
