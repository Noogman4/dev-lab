# 13 Standalone Radio Marker Widgets Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Marker-Frame und Grip-Label fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker-Frame wird weiterhin mit `bg`, `bd=1` und `relief="solid"` gebaut.
- Marker-Spalte 0 bekommt weiterhin `weight=1`.
- Grip-Label behaelt Text, Farbe, Font, Cursor, Padding und Anchor.
- Grip wird weiterhin mit `row=0`, `column=0`, `sticky="ew"` gegridet.

## Risiken

- Sichtbarer Grip-Text, Cursor und Farben duerfen sich nicht aendern.
- Widget-Hierarchie muss Marker als Parent des Grip-Labels behalten.
- Grid- und Column-Konfiguration duerfen nicht verschoben werden.
- Fehler der Widget-Builder duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `e4d26ff7`
- Messbedingungen: Dummy-Container, Dummy-Marker, Dummy-Grip, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_widgets_inline_comparable`: best of 5 `582 ns`

## Geplante kleine Aenderung

- Widget-Erzeugung in `_standalone_radio_pane_marker_widgets` extrahieren.
- Direkte Tests fuer Builder-Argumente, Layout-Aufrufe und Fehlerpropagation ergaenzen.
- Callback- und Binding-Logik unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_widgets` eingefuehrt.
- `_install_pane_drag_marker` nutzt den Helper fuer Marker und Grip.
- Tests fuer Frame-/Label-Argumente, Column/Grid-Aufrufe und Fehlerpropagation ergaenzt.
- Keine Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin vor Drag-State und Callback-Aufbau erstellt.
- Der Installer gibt weiterhin den Marker zurueck.
- Callback-Aufbau und Binding-Aktivierung bleiben unveraendert.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` bleibt im Installer.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-widgets-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-widgets-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_widgets_builds_marker_and_grip`
- `test_standalone_radio_pane_marker_widgets_propagates_frame_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `176 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `178 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2414 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_widgets_helper`: best of 5 `600 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-widgets-build`.
