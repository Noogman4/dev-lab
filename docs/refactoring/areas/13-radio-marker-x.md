# 13 Radio Marker X

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: X-Position des Pane-Drag-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_radio_pane_marker_geometry`

## Abhaengigkeiten und Seiteneffekte

- Marker-Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Marker-X bleibt weiterhin zentriert, aber mindestens `8`.
- Marker-Breite wird weiterhin ueber `_radio_pane_marker_width` berechnet.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.

## Risiken

- X-Clamp muss exakt unveraendert bleiben.
- Geometrie muss weiterhin dieselben Werte liefern.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `1b12227e`
- Messbedingungen: Dummy-Breite und Dummy-Marker-Breite, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_x`: best of 5 `121 ns`

## Geplante kleine Aenderung

- X-Positionsberechnung in `_radio_pane_marker_x` extrahieren.
- Direkten Test fuer Zentrierung und linken Mindestabstand ergaenzen.
- `_radio_pane_marker_geometry` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_x` eingefuehrt.
- `_radio_pane_marker_geometry` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-X bleibt bei breiten Containern zentriert.
- Marker-X bleibt mindestens `8`.
- Marker-Breite, Y-Position und Hoehe bleiben unveraendert.
- Marker-Placement fuer Sash-Positionen bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-x.md`
- `docs/refactoring/performance/areas/13-radio-marker-x.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_x_centers_and_clamps_left_padding`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `253 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `254 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2331 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_x`: best of 5 `187 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Werte statt echter Tk-Widgetbreiten.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-x`.
