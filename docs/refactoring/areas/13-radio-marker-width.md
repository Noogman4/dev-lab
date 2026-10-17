# 13 Radio Marker Width

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Breitenberechnung des Pane-Drag-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_radio_pane_marker_geometry`

## Abhaengigkeiten und Seiteneffekte

- Marker-Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Marker-Breite bleibt weiterhin zwischen `42` und `66` begrenzt.
- Die Container-Breite wird weiterhin auf mindestens `0` normalisiert.
- Source-basierter Marker-Kommentar bleibt in `_install_pane_drag_marker` erhalten.

## Risiken

- Breiten-Clamp muss exakt unveraendert bleiben.
- Geometrie muss weiterhin dieselben `x`, `y`, `width` und `height`-Werte liefern.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `29765f96`
- Messbedingungen: Dummy-Breite, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_width`: best of 5 `169 ns`

## Geplante kleine Aenderung

- Breiten-Clamp in `_radio_pane_marker_width` extrahieren.
- Direkten Test fuer Minimal- und Maximalbreite ergaenzen.
- `_radio_pane_marker_geometry` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_width` eingefuehrt.
- `_radio_pane_marker_geometry` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Breite bleibt maximal `66`.
- Marker-Breite bleibt minimal `42`.
- Marker-X-Position und Y-Position bleiben unveraendert.
- Marker-Placement fuer Sash-Positionen bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-width.md`
- `docs/refactoring/performance/areas/13-radio-marker-width.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_width_clamps_between_min_and_max`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `252 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `253 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2330 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_width`: best of 5 `286 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Werte statt echter Tk-Widgetbreiten.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-width`.
