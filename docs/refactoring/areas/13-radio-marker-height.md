# 13 Radio Marker Height

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Hoehe des Pane-Drag-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_radio_pane_marker_geometry`

## Abhaengigkeiten und Seiteneffekte

- Marker-Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Marker-Hoehe bleibt weiterhin fest `12`.
- Marker-X wird weiterhin ueber `_radio_pane_marker_x` berechnet.
- Marker-Y wird weiterhin ueber `_radio_pane_marker_y` berechnet.
- Marker-Breite wird weiterhin ueber `_radio_pane_marker_width` berechnet.

## Risiken

- Die feste Hoehe muss exakt unveraendert bleiben.
- Geometrie muss weiterhin dieselben Werte liefern.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `767345ce`
- Messbedingungen: direkte Konstante, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_height`: best of 5 `6 ns`

## Geplante kleine Aenderung

- Marker-Hoehe in `_radio_pane_marker_height` extrahieren.
- Direkten Test fuer die feste Drag-Ziel-Hoehe ergaenzen.
- `_radio_pane_marker_geometry` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_height` eingefuehrt.
- `_radio_pane_marker_geometry` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Hoehe bleibt `12`.
- Marker-X, Marker-Y und Breite bleiben unveraendert.
- Marker-Placement fuer Sash-Positionen bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-height.md`
- `docs/refactoring/performance/areas/13-radio-marker-height.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_height_returns_fixed_drag_target_height`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `255 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `256 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2333 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_height`: best of 5 `19 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die feste Hoehe isoliert und ueber die Geometrie.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-height`.
