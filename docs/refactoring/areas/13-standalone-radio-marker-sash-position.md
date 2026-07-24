# 13 Standalone Radio Marker Sash Position

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Setzen der Sash-Position des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` ruft weiterhin die Sash-Positionierung waehrend Drag-Bewegungen auf.
- `_standalone_radio_pane_set_sash_pos` versucht zuerst `pane.sashpos(0, int(new_y))`.
- Falls `sashpos` fehlschlaegt, bleibt der Fallback auf `pane.sash_place(0, 0, int(new_y))` erhalten.
- Fehler im Fallback werden weiterhin ignoriert.

## Risiken

- Der primaere `sashpos`-Pfad muss unveraendert bleiben.
- Der `sash_place`-Fallback muss nur nach einem `sashpos`-Fehler laufen.
- `new_y` muss weiterhin vor der Uebergabe in `int` umgewandelt werden.
- Fehler duerfen weiterhin nicht bis in Drag-Callbacks durchschlagen.

## Performance Vorher

- Commit vorher: `0c4109eb`
- Messbedingungen: direkter `sashpos`-Aufruf mit Dummy-Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_sash_pos_inline`: best of 5 `49 ns`

## Geplante kleine Aenderung

- Sash-Positionierung in `_standalone_radio_pane_set_sash_pos` extrahieren.
- Direkte Tests fuer primaeren `sashpos`-Pfad und Fallback auf `sash_place` ergaenzen.
- `_install_pane_drag_marker` auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_set_sash_pos` eingefuehrt.
- Lokaler `_set_sash_pos`-Callback delegiert an den neuen Helper.
- Neue Tests `test_standalone_radio_pane_set_sash_pos_prefers_sashpos` und `test_standalone_radio_pane_set_sash_pos_falls_back_to_sash_place` ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Bewegungen setzen weiterhin die erste Sash-Position.
- Wenn `sashpos` nicht verfuegbar ist, wird weiterhin `sash_place` versucht.
- Fehler in beiden Wegen bleiben weiterhin ignoriert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-sash-position.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-sash-position.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_set_sash_pos_prefers_sashpos`
- `test_standalone_radio_pane_set_sash_pos_falls_back_to_sash_place`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `125 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `127 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2363 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_sash_pos_helper`: best of 5 `66 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Panes, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-sash-position`.
