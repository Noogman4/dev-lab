# 13 Radio Marker Widgets Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau von Marker-Frame und Grip-Label fuer den Radio-Pane-Marker
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `_install_pane_drag_marker`, Radio-Tab-Aufbau

## Abhaengigkeiten und Seiteneffekte

- Marker bleibt ein Frame mit `bg`, `bd=1` und `relief="solid"`.
- Marker-Spalte `0` bleibt mit `weight=1` konfiguriert.
- Grip bleibt ein Label mit Text `\u2261`, weisser Schrift und Drag-Cursor.
- Grip wird weiterhin in Zeile `0`, Spalte `0`, `sticky="ew"` gegridet.
- Marker-Geometrie, Drag-State, Event-Bindings und Scheduling bleiben unveraendert.

## Risiken

- Widget-Optionen muessen exakt erhalten bleiben.
- Der Helper darf keine Drag-Callbacks oder Bindings verschieben.
- Source-basierte Radio-Tests muessen ihren Marker-Geometrie-Anker im Installer behalten.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Performance Vorher

- Commit vorher: `06a7fdc7`
- Messbedingungen: Dummy-Widget-Factories, `.venv/bin/python -m timeit`
- `radio_marker_widgets_build`: best of 5 `929 nsec per loop`

## Geplante kleine Aenderung

- Marker-/Grip-Widget-Aufbau in `_build_radio_pane_marker_widgets` extrahieren.
- Direkten Factory-Test fuer Frame-Optionen, Grip-Optionen und Grid-Werte ergaenzen.
- Marker-Drag-Logik, Update-Scheduling und Pane-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_build_radio_pane_marker_widgets` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Marker und Grip.
- Keine sichtbaren Texte, Widget-Struktur ausserhalb des Helpers oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin mit denselben Optionen erzeugt.
- Der Marker bleibt horizontal expandierbar.
- Der Grip bleibt sichtbar und bedienbar.
- Drag-Handler geben weiterhin `"break"` zurueck.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-widgets-build.md`
- `docs/refactoring/performance/areas/13-radio-marker-widgets-build.md`

## Hinzugefuegte Tests

- `test_build_radio_pane_marker_widgets_creates_marker_and_grip`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `162 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `163 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2240 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_widgets_build`: best of 5 `1.01 usec per loop`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Bereich um 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-widgets-build`.
