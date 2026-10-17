# 13 Radio Marker Place For Sash

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Marker-Platzierung aus Container-Breite und Sash-Y
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Marker-Update und Marker-Drag

## Abhaengigkeiten und Seiteneffekte

- Die Container-Breite wird weiterhin ueber `container.winfo_width()` gelesen.
- Die Geometrie wird weiterhin ueber `_radio_pane_marker_geometry` berechnet.
- Die Platzierung laeuft weiterhin ueber `_place_radio_pane_marker`.
- Fehler aus `winfo_width` werden weiterhin von den aeusseren Update- oder Drag-Pfaden abgefangen.
- Bindings, Drag-State und Sash-Setzung bleiben unveraendert.

## Risiken

- Die Reihenfolge `width lesen -> Geometrie berechnen -> Marker platzieren` muss erhalten bleiben.
- Die source-basierten Radio-Tests erwarten weiterhin den Legacy-Hinweis in `_install_pane_drag_marker`.
- Der Helper darf keine neuen Tk-Widgets erzeugen.
- Fehlerbehandlung darf nicht versehentlich breiter oder enger werden.

## Performance Vorher

- Commit vorher: `150bddb1`
- Messbedingungen: Dummy-Container, Dummy-Marker und Sash-Y, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_place_for_sash`: best of 5 `903 ns`

## Geplante kleine Aenderung

- Platzierung aus Container-Breite und Sash-Y in `_place_radio_pane_marker_for_sash` extrahieren.
- Direkte Tests fuer Erfolgsweg und Width-Fehler ergaenzen.
- Lokale Callback-Struktur und Rueckgabewerte unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_place_radio_pane_marker_for_sash` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im lokalen Place-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin anhand der aktuellen Container-Breite zentriert.
- Marker wird weiterhin fuer die uebergebene Sash-Position platziert.
- Marker-Place-Fehler werden weiterhin ueber `_place_radio_pane_marker` behandelt.
- Drag-Start, Drag-Motion und Update-Scheduling bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-place-for-sash.md`
- `docs/refactoring/performance/areas/13-radio-marker-place-for-sash.md`

## Hinzugefuegte Tests

- `test_place_radio_pane_marker_for_sash_uses_container_width_and_sash`
- `test_place_radio_pane_marker_for_sash_propagates_width_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `176 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `178 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2255 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_place_for_sash`: best of 5 `925 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt unter 1 us im Dummy-Pfad.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Container und Dummy-Marker statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-place-for-sash`.
