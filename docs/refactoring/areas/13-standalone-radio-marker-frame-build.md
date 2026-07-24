# 13 Standalone Radio Marker Frame Build

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Marker-Frame-Bau aus der Standalone-Radio-Pane-Marker-Widget-Erzeugung herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_widgets`

## Abhaengigkeiten und Seiteneffekte

- Frame-Optionen werden weiterhin ueber `_standalone_radio_pane_marker_frame_options` gebaut.
- Frame-Erzeugung nutzt weiterhin den injizierbaren Frame-Builder.
- Grip-Erzeugung und Layout-Konfiguration bleiben unveraendert.
- Der Widget-Helper gibt weiterhin Marker und Grip zurueck.

## Risiken

- Container und Farbe muessen unveraendert an den Frame-Bau weitergereicht werden.
- Frame-Optionsdict muss unveraendert in den Frame-Builder fliessen.
- Fehler des Frame-Builders duerfen nicht versehentlich geschluckt werden.
- Sichtbares Marker-Verhalten darf sich nicht aendern.

## Performance Vorher

- Commit vorher: `3a4a4fa8`
- Messbedingungen: Dummy-Container, Dummy-Frame-Builder, Dummy-Optionsbuilder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_frame_build_inline`: best of 5 `274 ns`

## Geplante kleine Aenderung

- Frame-Bau in `_standalone_radio_pane_marker_frame` extrahieren.
- Direkte Tests fuer Builder-Argumente, Rueckgabewert und Fehlerpropagation ergaenzen.
- Widget-Test auf die neue Frame-Helper-Verdrahtung anpassen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_frame` eingefuehrt.
- `_standalone_radio_pane_marker_widgets` nutzt den neuen Frame-Helper.
- Tests fuer Frame-Build, Fehlerpropagation und Widget-Verdrahtung ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker-Frame wird weiterhin vor dem Grip gebaut.
- Grip bleibt weiterhin Kind des Markers.
- Layout-Konfiguration laeuft weiterhin nach Frame- und Grip-Erzeugung.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-frame-build.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-frame-build.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_frame_builds_with_options`
- `test_standalone_radio_pane_marker_frame_propagates_builder_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `186 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `188 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2424 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_frame_build_helper`: best of 5 `299 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Builder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-frame-build`.
