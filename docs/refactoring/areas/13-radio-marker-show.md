# 13 Radio Marker Show

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: erfolgreicher `place`- und `lift`-Ablauf fuer den Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_place_radio_pane_marker`

## Abhaengigkeiten und Seiteneffekte

- `_place_radio_pane_marker` bleibt fuer Fehlerbehandlung und `place_forget` verantwortlich.
- `_show_radio_pane_marker` fuehrt nur `marker.place(**geometry)` und `marker.lift()` aus.
- Fehler bei `place` oder `lift` werden weiterhin vom aeusseren Wrapper abgefangen.
- Marker-Geometrie wird weiterhin unveraendert ueber `_radio_pane_marker_geometry` berechnet.

## Risiken

- Reihenfolge `place` vor `lift` muss unveraendert bleiben.
- Fehlerbehandlung darf nicht in den neuen Helper verschoben werden.
- `place_forget` muss bei `place`- oder `lift`-Fehlern weiterhin ausgefuehrt werden.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `8927ff82`
- Messbedingungen: Dummy-Marker mit `place` und `lift`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_show`: best of 5 `256 ns`

## Geplante kleine Aenderung

- Erfolgreichen `place`- und `lift`-Ablauf in `_show_radio_pane_marker` extrahieren.
- Direkten Test fuer Reihenfolge und Geometrieuebergabe ergaenzen.
- `_place_radio_pane_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_show_radio_pane_marker` eingefuehrt.
- `_place_radio_pane_marker` nutzt den neuen Helper im bestehenden Try-Block.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin mit derselben Geometrie platziert.
- Marker wird weiterhin nach dem Platzieren angehoben.
- Bei `place`- oder `lift`-Fehlern wird weiterhin `place_forget` versucht.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-show.md`
- `docs/refactoring/performance/areas/13-radio-marker-show.md`

## Hinzugefuegte Tests

- `test_show_radio_pane_marker_places_and_lifts_marker`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `257 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `258 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2335 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_show`: best of 5 `289 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Marker statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-show`.
