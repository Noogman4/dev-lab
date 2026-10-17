# 13 Radio Marker Place

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: fehlertolerantes Platzieren und Anheben des Radio-Pane-Markers
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Marker-Platzierung fuer Sash-Positionen

## Abhaengigkeiten und Seiteneffekte

- `marker.place(**geometry)` bleibt der Platzierungsweg.
- `marker.lift()` wird weiterhin nach erfolgreichem `place` aufgerufen.
- Fehler beim Platzieren oder Anheben blenden den Marker weiterhin fehlertolerant aus.
- Marker-Geometrie, Drag-State, Event-Bindings und Scheduling bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- `lift()` muss weiterhin nur nach `place()` versucht werden.
- Fehler aus beiden Quellen muessen weiterhin zum `place_forget`-Fallback fuehren.
- Der Source-Test-Anker fuer die Marker-Geometrie muss im Installer erhalten bleiben.
- Keine Aenderung an Drag-Rueckgabewerten.

## Performance Vorher

- Commit vorher: `28257fb9`
- Messbedingungen: Dummy-Marker und Geometrie-Dict, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_place`: best of 5 `272 ns`

## Geplante kleine Aenderung

- Marker-Platzierung in `_place_radio_pane_marker` extrahieren.
- Direkte Tests fuer Erfolg, Place-Fehler und Lift-Fehler ergaenzen.
- Geometrie-Berechnung, Marker-Update und Drag-Handler unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_place_radio_pane_marker` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im Sash-Platzierungs-Callback.
- Legacy-Source-Marker fuer bestehende Quelltext-Tests erhalten.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin anhand der berechneten Geometrie platziert.
- Marker wird weiterhin angehoben.
- Fehlerhafte Platzierung oder fehlerhaftes Anheben blenden den Marker weiterhin aus.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-place.md`
- `docs/refactoring/performance/areas/13-radio-marker-place.md`

## Hinzugefuegte Tests

- `test_place_radio_pane_marker_places_and_lifts_marker`
- `test_place_radio_pane_marker_forgets_marker_on_place_failure`
- `test_place_radio_pane_marker_forgets_marker_on_lift_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `166 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `169 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2246 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_place`: best of 5 `295 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Marker statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-place`.
