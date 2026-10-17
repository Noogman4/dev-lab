# 13 Radio Marker Container Geometry

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Marker-Geometrie aus Container und Sash-Y
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_place_radio_pane_marker_for_sash`

## Abhaengigkeiten und Seiteneffekte

- `_place_radio_pane_marker_for_sash` platziert weiterhin den Marker fuer eine Sash-Position.
- `_radio_pane_marker_geometry_for_container` kombiniert nur Container-Breite und Sash-Y.
- Container-Breite wird weiterhin ueber `_radio_pane_container_width` gelesen.
- Marker-Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Fehler bei `winfo_width` laufen weiterhin nach aussen.

## Risiken

- Die Breitenabfrage muss weiterhin vor dem Placement erfolgen.
- Fehler bei `winfo_width` duerfen nicht geschluckt werden.
- Geometrie muss weiterhin dieselben Werte liefern.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `412b3554`
- Messbedingungen: Dummy-Container und Dummy-Sash-Y, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_container_geometry`: best of 5 `981 ns`

## Geplante kleine Aenderung

- Geometrieaufbau aus Container und Sash-Y in `_radio_pane_marker_geometry_for_container` extrahieren.
- Direkten Test fuer Container-Breite plus Sash-Y ergaenzen.
- `_place_radio_pane_marker_for_sash` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_geometry_for_container` eingefuehrt.
- `_place_radio_pane_marker_for_sash` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Geometrie bleibt fuer dieselbe Container-Breite und Sash-Y unveraendert.
- Marker-Placement und `place_forget`-Fehlerpfad bleiben unveraendert.
- Fehler bei der Breitenabfrage laufen weiterhin bis zum Aufrufer.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-container-geometry.md`
- `docs/refactoring/performance/areas/13-radio-marker-container-geometry.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_geometry_for_container_uses_width_and_sash`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `259 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `260 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2337 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_container_geometry`: best of 5 `1001 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt im Dummy-Pfad bei etwa 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-container-geometry`.
