# 13 Standalone Radio Marker Widget Pair

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Frame-und-Grip-Erzeugung aus der Standalone-Radio-Pane-Marker-Widget-Konfiguration herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_standalone_radio_pane_marker_widgets`

## Abhaengigkeiten und Seiteneffekte

- Marker-Frame-Bau bleibt bei `_standalone_radio_pane_marker_frame`.
- Grip-Bau bleibt bei `_standalone_radio_pane_marker_grip`.
- Layout-Konfiguration bleibt bei `_standalone_radio_pane_configure_marker_widgets`.
- Der Widget-Helper gibt weiterhin Marker und Grip zurueck.

## Risiken

- Frame muss weiterhin vor dem Grip gebaut werden.
- Grip muss weiterhin den Marker als Parent erhalten.
- Layout-Konfiguration darf erst nach erfolgreicher Pair-Erzeugung laufen.
- Fehler im Pair-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `94727c40`
- Messbedingungen: Dummy-Container, Dummy-Marker, Dummy-Grip, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_widgets_current`: best of 5 `158 ns`

## Geplante kleine Aenderung

- Frame-und-Grip-Erzeugung in `_standalone_radio_pane_marker_widget_pair` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- Widget-Test auf Pair-Builder plus Layout-Konfiguration umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_marker_widget_pair` eingefuehrt.
- `_standalone_radio_pane_marker_widgets` nutzt den neuen Pair-Helper.
- Tests fuer Pair-Build, Fehlerpropagation und Widget-Konfiguration ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker-Frame wird weiterhin vor dem Grip gebaut.
- Grip bleibt weiterhin Kind des Markers.
- Layout-Konfiguration laeuft weiterhin nach Frame- und Grip-Erzeugung.
- Der Installer gibt weiterhin den Marker zurueck.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-widget-pair.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-widget-pair.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_marker_widget_pair_builds_frame_then_grip`
- `test_standalone_radio_pane_marker_widget_pair_propagates_grip_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `190 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `192 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2428 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_widgets_pair_helper`: best of 5 `151 ns`

## Bewertung

- Der neue Pair-Helper macht die Erzeugungsreihenfolge explizit testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Builder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-widget-pair`.
