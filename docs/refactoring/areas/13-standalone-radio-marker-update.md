# 13 Standalone Radio Marker Update

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Aktualisieren des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` behandelt Update-Fehler weiterhin selbst.
- `_standalone_radio_pane_update_marker` liest `pane.sashpos(0)`, wandelt in `int` und ruft den Place-for-Sash-Callback auf.
- Der Forget-Fallback bleibt im lokalen `_update_marker`.
- Keine Binding- oder Drag-Logik wird veraendert.

## Risiken

- Die aktuelle Sash-Position muss weiterhin aus `pane.sashpos(0)` gelesen werden.
- Die Sash-Position muss weiterhin vor dem Platzieren in `int` umgewandelt werden.
- Fehler muessen weiterhin im lokalen Update-Callback abgefangen werden.
- Der Place-for-Sash-Callback muss unveraendert mit der aktuellen Sash-Position aufgerufen werden.

## Performance Vorher

- Commit vorher: `972cce75`
- Messbedingungen: direkter `place(int(pane.sashpos(0)))`-Pfad mit Dummy-Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_update_inline`: best of 5 `63 ns`

## Geplante kleine Aenderung

- Update-Pfad in `_standalone_radio_pane_update_marker` extrahieren.
- Direkten Test fuer Sash-Lesen und Place-Aufruf ergaenzen.
- Lokalen `_update_marker` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_marker` eingefuehrt.
- Lokaler `_update_marker` delegiert an den neuen Helper.
- Neuer Test `test_standalone_radio_pane_update_marker_places_current_sash` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Update nutzt weiterhin die aktuelle erste Sash-Position.
- Marker wird weiterhin ueber den lokalen Place-for-Sash-Callback platziert.
- Fehler beim Update fuehren weiterhin zum Forget-Fallback.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-update.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-update.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_marker_places_current_sash`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `128 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `129 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2365 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_update_helper`: best of 5 `79 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-update`.
