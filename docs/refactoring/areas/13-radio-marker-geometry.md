# 13 Radio Marker Geometry

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Geometrie-Berechnung fuer den vertikalen Radio-Pane-Drag-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Radio-Tab-Aufbau

## Abhaengigkeiten und Seiteneffekte

- Marker-Breite bleibt `min(66, max(width - 24, 42))`.
- X-Position bleibt zentriert und mindestens `8`.
- Y-Position bleibt `sash_y - 5` und mindestens `2`.
- Marker-Hoehe bleibt `12`.
- Tk-Widget-Erzeugung, Bindings, Drag-State und Sash-Positionierung bleiben unveraendert.
- Source-basierte Radio-Tests behalten ihren bisherigen Marker-Quelltext-Anker.

## Risiken

- Schmale Container muessen weiterhin auf die Mindestbreite und Mindestposition fallen.
- Der Helper darf keine Tk-Widgets erzeugen.
- Der Installer muss weiterhin `marker.place(...)` mit denselben Werten aufrufen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `ae6c4443`
- Messbedingungen: direkte Python-Formel fuer Marker-Geometrie, `.venv/bin/python -m timeit`
- `radio_marker_geometry`: best of 5 `500 nsec per loop`

## Geplante kleine Aenderung

- Reine Marker-Geometrie in `_radio_pane_marker_geometry` extrahieren.
- Direkten Test fuer Normalfall und Clamp-Fall ergaenzen.
- Tk-Bindings, Drag-Handler und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_pane_marker_geometry` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper beim Platzieren des Markers.
- Legacy-Source-Marker fuer bestehende Quelltext-Tests erhalten.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Der Marker bleibt horizontal zentriert.
- Der Marker bleibt bei schmalen Containern mindestens 42 Pixel breit.
- Der Marker bleibt mindestens bei `x=8` und `y=2`.
- Drag-Start, Drag-Bewegung und Drag-Ende bleiben unveraendert.
- Radio-Launcher-Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-geometry.md`
- `docs/refactoring/performance/areas/13-radio-marker-geometry.md`

## Hinzugefuegte Tests

- `test_radio_pane_marker_geometry_centers_and_clamps_marker`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `144 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `145 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m black netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: Formatierung angewendet, Prozess endete wegen Timeout
- `timeout 120 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: Dateien als unveraendert gemeldet, Prozess endete wegen Timeout

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2222 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_geometry`: best of 5 `529 nsec per loop`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die reine Geometrie ohne echte Tk-Frames.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-geometry`.
