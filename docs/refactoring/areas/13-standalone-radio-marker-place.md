# 13 Standalone Radio Marker Place

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Platzieren und Anheben des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` berechnet weiterhin die Geometrie und behandelt Placement-Fehler.
- `_standalone_radio_pane_place_marker` ruft nur `marker.place(**geometry)` und danach `marker.lift()` auf.
- Die Source-basierte Marker-Breiten-Referenz bleibt in `_install_pane_drag_marker` erhalten.
- Keine Callback- oder Binding-Logik wird veraendert.

## Risiken

- `place` muss vor `lift` laufen.
- Die Geometrie muss unveraendert als Keyword-Argumente an `place` gehen.
- Fehlerbehandlung muss im Installer erhalten bleiben.
- Echte Tk-Widgets duerfen nicht ersetzt werden.

## Performance Vorher

- Commit vorher: `fa392f37`
- Messbedingungen: direkter `place(**geometry)`- und `lift()`-Aufruf mit Dummy-Marker, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_place_inline`: best of 5 `254 ns`

## Geplante kleine Aenderung

- Marker-Placement in `_standalone_radio_pane_place_marker` extrahieren.
- Direkten Test fuer `place`-Argumente und `lift`-Reihenfolge ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_place_marker` eingefuehrt.
- `_install_pane_drag_marker` nutzt den neuen Helper nach der Geometrie-Berechnung.
- Neuer Test `test_standalone_radio_pane_place_marker_places_and_lifts` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin mit derselben Geometrie platziert.
- Marker wird weiterhin nach dem Platzieren angehoben.
- Fehler beim Platzieren werden weiterhin im Installer abgefangen und fuehren zum `place_forget`-Fallback.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-place.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-place.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_place_marker_places_and_lifts`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `123 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `124 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2360 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_place_helper`: best of 5 `280 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen das Placement mit Dummy-Marker, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-place`.
