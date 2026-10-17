# 13 Radio Marker Drag Start

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Start-Drag-Callback fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Grip-Button-Callback

## Abhaengigkeiten und Seiteneffekte

- Der Drag-Start-Zustand wird weiterhin ueber `_record_radio_pane_drag_start` gespeichert.
- Der Drag-Start-Handler gibt weiterhin `"break"` zurueck.
- Fehler beim Lesen von Event oder Sash fallen weiterhin auf `0` zurueck.
- Drag-Motion, Drag-End, Sash-Positionierung und Bindings bleiben unveraendert.

## Risiken

- Der Rueckgabewert `"break"` muss erhalten bleiben, damit Tk das Event nicht weiterverarbeitet.
- Der Drag-State muss unter denselben Keys aktualisiert werden.
- Fehler-Fallback darf nicht nur teilweise gespeichert werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `10f9e1f2`
- Messbedingungen: Dummy-Event, Dummy-Pane und Dict-State, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_drag_start_handler`: best of 5 `175 ns`

## Geplante kleine Aenderung

- Start-Drag-Ablauf in `_handle_radio_pane_marker_drag_start` extrahieren.
- Direkte Tests fuer Erfolgsweg plus `"break"` und Fehler-Fallback plus `"break"` ergaenzen.
- Bindings und lokale Callback-Signatur unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_handle_radio_pane_marker_drag_start` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper im internen Start-Drag-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag-Start liest weiterhin Root-Y und aktuelle Sash-Position.
- Bei Lesefehlern werden weiterhin beide Werte auf `0` gesetzt.
- Drag-Start gibt weiterhin `"break"` zurueck.
- Drag-Motion und Marker-Platzierung bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-drag-start.md`
- `docs/refactoring/performance/areas/13-radio-marker-drag-start.md`

## Hinzugefuegte Tests

- `test_handle_radio_pane_marker_drag_start_updates_state_and_breaks`
- `test_handle_radio_pane_marker_drag_start_uses_zeroes_and_breaks_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `180 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `182 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2259 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_drag_start_handler`: best of 5 `185 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dummy-Panes statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-drag-start`.
