# 13 Radio Marker Container Width

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Breitenabfrage des Pane-Marker-Containers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_place_radio_pane_marker_for_sash`

## Abhaengigkeiten und Seiteneffekte

- `_place_radio_pane_marker_for_sash` berechnet weiterhin die Marker-Geometrie aus Container-Breite und Sash-Y.
- `_radio_pane_container_width` liest nur `container.winfo_width()` und wandelt in `int`.
- Fehler bei `winfo_width` laufen weiterhin nach aussen.
- Marker-Placement und Fehlerbehandlung bleiben unveraendert.

## Risiken

- Die Breitenabfrage muss vor dem Placement weiterhin exakt einmal erfolgen.
- Fehler bei `winfo_width` duerfen nicht geschluckt werden.
- Geometrie muss weiterhin dieselben Werte erhalten.
- Echte Tk-Placement-Aufrufe duerfen nicht veraendert werden.

## Performance Vorher

- Commit vorher: `cdaee995`
- Messbedingungen: Dummy-Container mit `winfo_width`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_container_width`: best of 5 `22 ns`

## Geplante kleine Aenderung

- Container-Breitenabfrage in `_radio_pane_container_width` extrahieren.
- Direkten Test fuer die Integer-Breitenabfrage ergaenzen.
- `_place_radio_pane_marker_for_sash` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_radio_pane_container_width` eingefuehrt.
- `_place_radio_pane_marker_for_sash` nutzt den neuen Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Container-Breite wird weiterhin ueber `winfo_width` gelesen.
- Marker-Geometrie bleibt fuer dieselbe Breite und Sash-Y unveraendert.
- Fehler bei der Breitenabfrage laufen weiterhin bis zum Aufrufer.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-container-width.md`
- `docs/refactoring/performance/areas/13-radio-marker-container-width.md`

## Hinzugefuegte Tests

- `test_radio_pane_container_width_reads_widget_width_as_int`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `258 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `259 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2336 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_container_width`: best of 5 `66 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf- und Integer-Normalisierungs-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-container-width`.
