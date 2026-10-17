# 13 Radio Marker Update From Sash

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Marker-Update anhand der aktuellen Radio-Pane-Sash-Position
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Marker-Update-Callback

## Abhaengigkeiten und Seiteneffekte

- `pane.sashpos(0)` wird weiterhin gelesen und zu `int` konvertiert.
- Die gelesene Sash-Position wird weiterhin an die Marker-Platzierung uebergeben.
- Fehler beim Sash-Lesen oder Platzieren blenden den Marker weiterhin fehlertolerant aus.
- Marker-Geometrie, Drag-State, Event-Bindings und Scheduling bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Fehler aus beiden Quellen muessen weiterhin zum `place_forget`-Fallback fuehren.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests muessen ihren Marker-Geometrie-Anker im Installer behalten.
- Keine Aenderung an Drag-Rueckgabewerten.

## Performance Vorher

- Commit vorher: `e9f41424`
- Messbedingungen: Dummy-Pane, Dummy-Marker und Place-Callback, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_update_from_sash`: best of 5 `70 ns`

## Geplante kleine Aenderung

- Marker-Update aus aktueller Sash-Position in `_update_radio_pane_marker_from_sash` extrahieren.
- Direkte Tests fuer Erfolgsweg, Sash-Fehler und Place-Fehler ergaenzen.
- Marker-Drag-Logik, Update-Scheduling und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_update_radio_pane_marker_from_sash` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im Update-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Marker-Updates lesen weiterhin die aktuelle Sash-Position.
- Erfolgreiche Updates platzieren den Marker weiterhin fuer diese Sash-Position.
- Fehlerhafte Updates blenden den Marker weiterhin aus.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-update-from-sash.md`
- `docs/refactoring/performance/areas/13-radio-marker-update-from-sash.md`

## Hinzugefuegte Tests

- `test_update_radio_pane_marker_from_sash_places_current_sash`
- `test_update_radio_pane_marker_from_sash_forgets_marker_on_sash_failure`
- `test_update_radio_pane_marker_from_sash_forgets_marker_on_place_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `163 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `166 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2243 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_update_from_sash`: best of 5 `92 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Panes und Dummy-Marker statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-update-from-sash`.
