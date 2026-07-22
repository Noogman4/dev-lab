# 13 Radio Drag Target Sash

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Ziel-Sash-Berechnung waehrend der Radio-Pane-Marker-Drag-Bewegung
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Drag-Bewegung des Radio-Pane-Markers

## Abhaengigkeiten und Seiteneffekte

- Delta bleibt `int(event.y_root) - int(drag_state["root_y"])`.
- Ziel-Sash bleibt `int(drag_state["sash_y"]) + delta`.
- Fehler bleiben weiterhin im bestehenden Drag-Handler abgefangen.
- Sash-Setzlogik, Marker-Platzierung, Update-Scheduling und Bindings bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Positive und negative Drag-Bewegungen muessen weiterhin korrekt berechnet werden.
- Der Helper darf keine Tk-Widgets erzeugen.
- Fehler duerfen den Drag-Handler weiterhin nicht verlassen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `decf867e`
- Messbedingungen: Dummy-Event und Drag-State-Dict, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_drag_target_sash`: best of 5 `123 ns`

## Geplante kleine Aenderung

- Ziel-Sash-Rechnung in `_radio_pane_drag_target_sash` extrahieren.
- Direkte Tests fuer positive und negative Drag-Deltas ergaenzen.
- Drag-Handler, Marker-Platzierung und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_pane_drag_target_sash` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper in der Drag-Bewegung.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Drag nach unten erhoeht die Sash-Position.
- Drag nach oben senkt die Sash-Position.
- Fehler werden weiterhin vom Drag-Handler abgefangen.
- Drag-Handler gibt weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-drag-target-sash.md`
- `docs/refactoring/performance/areas/13-radio-drag-target-sash.md`

## Hinzugefuegte Tests

- `test_radio_pane_drag_target_sash_adds_positive_delta`
- `test_radio_pane_drag_target_sash_adds_negative_delta`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `150 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `152 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --quiet netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: wegen Black-Timeout abgebrochen

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2229 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_drag_target_sash`: best of 5 `142 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Events und Dict-Zustand statt echter Tk-Events.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Drag-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-drag-target-sash`.
