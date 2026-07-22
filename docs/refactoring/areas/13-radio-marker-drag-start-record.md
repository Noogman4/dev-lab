# 13 Radio Marker Drag Start Record

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Speichern des Drag-Start-Zustands fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Start der Marker-Drag-Bewegung

## Abhaengigkeiten und Seiteneffekte

- Root-Y und Sash-Y werden weiterhin ueber `_radio_pane_drag_start_state` gelesen.
- Die Werte werden weiterhin unter `root_y` und `sash_y` im Drag-State gespeichert.
- Fehler beim Lesen setzen weiterhin beide Werte auf `0`.
- Rueckgabewert des Drag-Start-Handlers bleibt `"break"`.
- Drag-Bewegung, Sash-Positionierung, Marker-Geometrie und Bindings bleiben unveraendert.

## Risiken

- Der Helper muss denselben Dict-State mutieren, den der Drag-Motion-Handler nutzt.
- Fehler-Fallback darf nicht nur teilweise gespeichert werden.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `546d1525`
- Messbedingungen: Dummy-Event, Dummy-Pane und Dict-State, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_start_record`: best of 5 `111 ns`

## Geplante kleine Aenderung

- Drag-Start-State-Zuweisung in `_record_radio_pane_drag_start` extrahieren.
- Direkte Tests fuer Erfolgsweg und Fehler-Fallback ergaenzen.
- Bindings, Drag-Rueckgabewerte und Sash-Setzlogik unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_record_radio_pane_drag_start` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im Drag-Start-Handler.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Start liest weiterhin Root-Y und aktuelle Sash-Position.
- Bei Lesefehlern werden weiterhin beide Werte auf `0` gesetzt.
- Drag-Start gibt weiterhin `"break"` zurueck.
- Drag-Bewegung und Marker-Platzierung bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-start-record.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-start-record.md`

## Hinzugefuegte Tests

- `test_record_radio_pane_drag_start_updates_drag_state`
- `test_record_radio_pane_drag_start_uses_zeroes_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `174 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `176 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2253 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_start_record`: best of 5 `166 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dummy-Panes statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-start-record`.
