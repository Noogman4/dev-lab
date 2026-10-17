# 13 Standalone Radio Marker Install Marker

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Standalone-Radio-Pane-Marker-Installation aus dem oeffentlichen Installer-Einstieg herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Widget-Bau bleibt bei `_standalone_radio_pane_marker_widgets`.
- Callback- und Binding-Aktivierung bleiben bei `_standalone_radio_pane_install_marker_parts`.
- `_install_pane_drag_marker` bleibt der bestehende API-Einstieg.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` bleibt im API-Einstieg.

## Risiken

- Widgets muessen weiterhin vor Marker-Parts gebaut werden.
- Marker und Grip muessen unveraendert an die Installation weitergereicht werden.
- Farbe und `y_offset` muessen unveraendert durchgereicht werden.
- Fehler aus dem Widget-Bau duerfen nicht versehentlich geschluckt werden.

## Performance Vorher

- Commit vorher: `8021fc49`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Grip, Dummy-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_install_inline`: best of 5 `150 ns`

## Geplante kleine Aenderung

- Installer-Orchestrierung in `_standalone_radio_pane_install_marker` extrahieren.
- Direkte Tests fuer Builder-Reihenfolge, Rueckgabewert und Fehlerpropagation ergaenzen.
- `_install_pane_drag_marker` als schmalen API-Einstieg erhalten.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_install_marker` eingefuehrt.
- `_install_pane_drag_marker` delegiert an den neuen Helper.
- Tests fuer Widget-Bau, Part-Installation und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- Marker und Grip werden weiterhin vor Callback- und Binding-Aktivierung erstellt.
- Die Marker-Parts-Installation gibt weiterhin den Marker zurueck.
- `_install_pane_drag_marker` gibt weiterhin den installierten Marker zurueck.
- Der Legacy-Source-Hinweis fuer source-basierte Tests bleibt erhalten.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-install-marker.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-install-marker.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_install_marker_builds_widgets_and_installs_parts`
- `test_standalone_radio_pane_install_marker_propagates_widget_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `192 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `194 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2430 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_install_helper`: best of 5 `128 ns`

## Bewertung

- Der API-Einstieg ist schmaler und die Installation ist separat testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Builder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-install-marker`.
