# 13 Radio Sash Position

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Sash-Positionierung fuer den vertikalen Radio-Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Drag-Bewegung des Radio-Pane-Markers

## Abhaengigkeiten und Seiteneffekte

- Primaerer Tk-Weg bleibt `pane.sashpos(0, int(new_y))`.
- Fallback bleibt `pane.sash_place(0, 0, int(new_y))`.
- Fehler werden weiterhin geschluckt.
- Drag-State, Marker-Geometrie, Bindings und Event-Rueckgaben bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Der Fallback muss weiterhin nur genutzt werden, wenn `sashpos` fehlschlaegt.
- Beide Wege muessen `new_y` weiterhin zu `int` konvertieren.
- Fehler duerfen den Drag-Handler nicht verlassen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `40df75a4`
- Messbedingungen: Dummy-Pane mit erfolgreichem `sashpos`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_sash_position`: best of 5 `64 ns`

## Geplante kleine Aenderung

- Sash-Setzlogik in `_set_radio_pane_sash_position` extrahieren.
- Direkte Tests fuer `sashpos`, Fallback auf `sash_place` und Fehler-Toleranz ergaenzen.
- Drag-Handler, Marker-Platzierung und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_set_radio_pane_sash_position` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper in der Drag-Bewegung.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Bewegung setzt weiterhin die Sash-Position.
- Wenn `sashpos` verfuegbar ist, wird kein Fallback genutzt.
- Wenn `sashpos` fehlschlaegt, wird `sash_place` versucht.
- Wenn beide Wege fehlschlagen, bleibt der Drag-Handler fehlertolerant.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-sash-position.md`
- `docs/refactoring/performance/areas/13-radio-sash-position.md`

## Hinzugefuegte Tests

- `test_set_radio_pane_sash_position_uses_sashpos`
- `test_set_radio_pane_sash_position_falls_back_to_sash_place`
- `test_set_radio_pane_sash_position_ignores_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `145 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `148 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2225 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_sash_position`: best of 5 `82 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Panes statt echter Tk-Panedwindows.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-sash-position`.
