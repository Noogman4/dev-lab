# 13 Standalone Radio Marker Widget Options

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Frame- und Grip-Optionen fuer den Standalone-Radio-Pane-Marker aus der Widget-Erzeugung herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_widgets`

## Abhaengigkeiten und Seiteneffekte

- Marker-Frame erhaelt weiterhin `bg`, `bd=1` und `relief="solid"`.
- Grip-Label behaelt Text, Farbe, Font, Cursor, Padding und Anchor.
- Widget-Erzeugung nutzt weiterhin dieselben Frame- und Label-Builder.
- Grid- und Column-Konfiguration bleiben unveraendert in `_standalone_radio_pane_marker_widgets`.

## Risiken

- Optionsdicts muessen exakt dieselben Werte liefern.
- Farbe muss weiterhin an Frame und Grip weitergereicht werden.
- Widget-Builder duerfen weiterhin ihre Fehler propagieren.
- Sichtbares Marker-Verhalten darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `528383be`
- Messbedingungen: Optionsdicts fuer Frame und Grip, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_widget_options_inline`: best of 5 `218 ns`

## Geplante kleine Aenderung

- Frame-Optionen in `_standalone_radio_pane_marker_frame_options` extrahieren.
- Grip-Optionen in `_standalone_radio_pane_marker_grip_options` extrahieren.
- Widget-Test so erweitern, dass die Builder-Verdrahtung sichtbar bleibt.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_frame_options` eingefuehrt.
- `_standalone_radio_pane_marker_grip_options` eingefuehrt.
- `_standalone_radio_pane_marker_widgets` nutzt die neuen Optionsbuilder.
- Tests fuer beide Optionsdicts und die Optionsbuilder-Verdrahtung ergaenzt.

## Unveraendertes Sollverhalten

- Marker-Frame wird weiterhin vor dem Grip gebaut.
- Marker-Spalte 0 bekommt weiterhin `weight=1`.
- Grip wird weiterhin mit `row=0`, `column=0`, `sticky="ew"` gegridet.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-widget-options.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-widget-options.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_frame_options_use_marker_style`
- `test_standalone_radio_pane_marker_grip_options_use_marker_style`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `182 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `184 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2420 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_widget_options_helper`: best of 5 `257 ns`

## Bewertung

- Die Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Optionsdicts und Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-widget-options`.
