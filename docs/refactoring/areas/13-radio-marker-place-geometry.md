# 13 Radio Marker Place Geometry

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau der `place`-Geometrie fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_radio_pane_marker_geometry`

## Abhaengigkeiten und Seiteneffekte

- Marker-Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Marker-X wird weiterhin ueber `_radio_pane_marker_x` berechnet.
- Marker-Y wird weiterhin ueber `_radio_pane_marker_y` berechnet.
- Marker-Breite und Marker-Hoehe bleiben unveraendert.
- `_place_radio_pane_marker` erhaelt weiterhin ein Dict mit `x`, `y`, `width` und `height`.

## Risiken

- Die Dict-Schluessel muessen exakt unveraendert bleiben.
- Die Werte muessen weiterhin als Integer an `place` gehen.
- Geometrie muss weiterhin dieselben Werte liefern.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `3c1f6695`
- Messbedingungen: direkter Dict-Aufbau mit Dummy-Werten, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_geometry_dict`: best of 5 `66 ns`

## Geplante kleine Aenderung

- Dict-Aufbau in `_radio_pane_marker_place_geometry` extrahieren.
- Direkten Test fuer die `place`-Keyword-Struktur ergaenzen.
- `_radio_pane_marker_geometry` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_place_geometry` eingefuehrt.
- `_radio_pane_marker_geometry` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Geometrie enthaelt weiterhin `x`, `y`, `width` und `height`.
- Marker-X, Marker-Y, Breite und Hoehe bleiben unveraendert.
- Marker-Placement fuer Sash-Positionen bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-place-geometry.md`
- `docs/refactoring/performance/areas/13-radio-marker-place-geometry.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_place_geometry_builds_int_place_kwargs`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `256 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `257 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2334 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_geometry_dict`: best of 5 `202 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf- und Integer-Normalisierungs-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Werte statt echter Tk-Widgetbreiten.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-place-geometry`.
