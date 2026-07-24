# 13 Standalone Radio Marker Widget Layout

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Layout-Konfiguration fuer Marker-Frame und Grip-Label aus der Widget-Erzeugung herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_widgets`

## Abhaengigkeiten und Seiteneffekte

- Marker-Spalte 0 bekommt weiterhin `weight=1`.
- Grip wird weiterhin mit `row=0`, `column=0`, `sticky="ew"` gegridet.
- Frame- und Grip-Optionshelper bleiben unveraendert.
- Widget-Erzeugung nutzt weiterhin dieselben Frame- und Label-Builder.

## Risiken

- Layout-Aufrufe muessen in derselben Reihenfolge erfolgen.
- Fehler aus `columnconfigure` oder `grid` duerfen nicht versehentlich geschluckt werden.
- Widget-Builder duerfen weiterhin ihre Werte unveraendert erhalten.
- Sichtbares Marker-Verhalten darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `4e6f3b53`
- Messbedingungen: Dummy-Marker, Dummy-Grip, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_widget_layout_inline`: best of 5 `273 ns`

## Geplante kleine Aenderung

- Layout-Aufrufe in `_standalone_radio_pane_configure_marker_widgets` extrahieren.
- Direkte Tests fuer Layout-Aufrufe und Fehlerpropagation ergaenzen.
- Widget-Test auf die neue Layout-Helper-Verdrahtung anpassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_configure_marker_widgets` eingefuehrt.
- `_standalone_radio_pane_marker_widgets` nutzt den neuen Layout-Helper.
- Tests fuer Layout-Aufrufe, Fehlerpropagation und Helper-Verdrahtung ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker-Frame wird weiterhin vor dem Grip gebaut.
- Grip-Label behaelt Text, Farbe, Font, Cursor, Padding und Anchor.
- Grip bleibt weiterhin Kind des Markers.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-widget-layout.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-widget-layout.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_configure_marker_widgets_applies_layout`
- `test_standalone_radio_pane_configure_marker_widgets_propagates_layout_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `184 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `186 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2422 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_widget_layout_helper`: best of 5 `276 ns`

## Bewertung

- Der Helper fuegt praktisch keinen relevanten Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widgets statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-widget-layout`.
