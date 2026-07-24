# 13 Standalone Radio Marker Grip Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Grip-Label-Bau aus der Standalone-Radio-Pane-Marker-Widget-Erzeugung herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_widgets`

## Abhaengigkeiten und Seiteneffekte

- Grip-Optionen werden weiterhin ueber `_standalone_radio_pane_marker_grip_options` gebaut.
- Grip-Erzeugung nutzt weiterhin den injizierbaren Label-Builder.
- Marker-Frame-Bau und Layout-Konfiguration bleiben unveraendert.
- Der Widget-Helper gibt weiterhin Marker und Grip zurueck.

## Risiken

- Marker und Farbe muessen unveraendert an den Grip-Bau weitergereicht werden.
- Grip-Optionsdict muss unveraendert in den Label-Builder fliessen.
- Fehler des Label-Builders duerfen nicht versehentlich geschluckt werden.
- Sichtbarer Grip-Text, Cursor und Farben duerfen sich nicht aendern.

## Performance Vorher

- Commit vorher: `710a319d`
- Messbedingungen: Dummy-Marker, Dummy-Label-Builder, Dummy-Optionsbuilder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_grip_build_inline`: best of 5 `460 ns`

## Geplante kleine Aenderung

- Grip-Bau in `_standalone_radio_pane_marker_grip` extrahieren.
- Direkte Tests fuer Builder-Argumente, Rueckgabewert und Fehlerpropagation ergaenzen.
- Widget-Test auf die neue Grip-Helper-Verdrahtung anpassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_grip` eingefuehrt.
- `_standalone_radio_pane_marker_widgets` nutzt den neuen Grip-Helper.
- Tests fuer Grip-Build, Fehlerpropagation und Widget-Verdrahtung ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker-Frame wird weiterhin vor dem Grip gebaut.
- Grip bleibt weiterhin Kind des Markers.
- Layout-Konfiguration laeuft weiterhin nach Frame- und Grip-Erzeugung.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-grip-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-grip-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_grip_builds_with_options`
- `test_standalone_radio_pane_marker_grip_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `188 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `190 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2426 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_grip_build_helper`: best of 5 `507 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Builder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-grip-build`.
