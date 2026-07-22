# 13 Radio Drag Start State

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Drag-Start-Zustand fuer den vertikalen Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Start der Marker-Drag-Bewegung

## Abhaengigkeiten und Seiteneffekte

- `event.y_root` wird weiterhin zu `int` konvertiert.
- `pane.sashpos(0)` wird weiterhin zu `int` konvertiert.
- Fehler setzen weiterhin beide Drag-Start-Werte auf `0`.
- Rueckgabewert des Drag-Start-Handlers bleibt `"break"`.
- Drag-Bewegung, Sash-Positionierung, Marker-Geometrie und Bindings bleiben unveraendert.

## Risiken

- Wenn nur eine der beiden Leseoperationen fehlschlaegt, muessen weiterhin beide Werte auf `0` fallen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Der Drag-Start-Handler muss den Zustand weiterhin unter denselben Keys speichern.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `de35d15a`
- Messbedingungen: Dummy-Event und Dummy-Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_drag_start_state`: best of 5 `108 ns`

## Geplante kleine Aenderung

- Drag-Start-Leselogik in `_radio_pane_drag_start_state` extrahieren.
- Direkte Tests fuer Erfolgsweg und Fehler-Fallback ergaenzen.
- Bindings, Drag-Rueckgabewerte und Sash-Setzlogik unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_pane_drag_start_state` eingefuehrt.
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
- `docs/refactoring/areas/13-radio-drag-start-state.md`
- `docs/refactoring/performance/areas/13-radio-drag-start-state.md`

## Hinzugefuegte Tests

- `test_radio_pane_drag_start_state_reads_event_and_sash`
- `test_radio_pane_drag_start_state_returns_zeroes_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `148 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `150 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2227 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_drag_start_state`: best of 5 `117 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dummy-Panes statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-drag-start-state`.
