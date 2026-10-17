# 13 Standalone Radio Marker Drag Start

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Drag-Start-State des Standalone-Radio-Pane-Markers aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` gibt im lokalen Drag-Start-Callback weiterhin `"break"` zurueck.
- `_standalone_radio_pane_start_drag` liest `event.y_root` und `pane.sashpos(0)`.
- Bei Fehlern setzt der Helper weiterhin `root_y` und `sash_y` auf `0`.
- Keine Binding- oder Drag-Motion-Logik wird veraendert.

## Risiken

- `root_y` muss weiterhin aus `event.y_root` gelesen und in `int` umgewandelt werden.
- `sash_y` muss weiterhin aus `pane.sashpos(0)` gelesen und in `int` umgewandelt werden.
- Bei Fehlern muessen beide Werte weiterhin auf `0` fallen.
- Der lokale Callback muss weiterhin `"break"` zurueckgeben.

## Performance Vorher

- Commit vorher: `cc750c61`
- Messbedingungen: direkter Drag-Start-State-Write mit Dummy-Event und Dummy-Pane, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_drag_start_inline`: best of 5 `106 ns`

## Geplante kleine Aenderung

- Drag-Start-State-Write in `_standalone_radio_pane_start_drag` extrahieren.
- Direkte Tests fuer Erfolgs- und Fehlerpfad ergaenzen.
- Lokalen `_start_drag` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_start_drag` eingefuehrt.
- Lokaler `_start_drag` delegiert an den neuen Helper und gibt weiterhin `"break"` zurueck.
- Tests fuer normalen State-Write und Fehler-Fallback ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Motion-Logik geaendert.

## Unveraendertes Sollverhalten

- Drag-Start speichert weiterhin Root-Y und Sash-Y.
- Bei unlesbaren Werten werden beide Felder weiterhin auf `0` gesetzt.
- Der Tk-Eventfluss wird weiterhin durch `"break"` gestoppt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-drag-start.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-drag-start.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_start_drag_records_event_and_sash`
- `test_standalone_radio_pane_start_drag_uses_zeroes_on_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `132 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `134 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2370 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_drag_start_helper`: best of 5 `128 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Objekte, nicht echte Standalone-Marker-Drag-Bedienung.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-drag-start`.
