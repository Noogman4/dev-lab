# 13 Standalone Radio Marker API Delegation

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: oeffentlichen Standalone-Radio-Pane-Marker-Installer als schmale Delegation testbar machen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Die eigentliche Installation bleibt bei `_standalone_radio_pane_install_marker`.
- Widget-Bau, Callback-Bau und Binding-Aktivierung bleiben unveraendert.
- Der Legacy-Source-Hinweis fuer `marker_width = min(66, max(width - 24, 42))` bleibt im API-Einstieg.
- Bestehende Aufrufer nutzen weiterhin dieselbe Signatur fuer `container`, `pane`, `color` und `y_offset`.

## Risiken

- `container` und `pane` muessen unveraendert positional an den Installer gehen.
- `color` und `y_offset` muessen unveraendert als Keyword-Argumente weitergegeben werden.
- Fehler des Installers duerfen nicht geschluckt werden.
- Source-basierte Tests muessen den Legacy-Hinweis weiterhin finden.

## Performance Vorher

- Commit vorher: `d4ee27e6`
- Messbedingungen: Dummy-Container, Dummy-Pane, Dummy-Installer, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_api_current`: best of 5 `122 ns`

## Geplante kleine Aenderung

- `_install_pane_drag_marker` um den injizierbaren Keyword-only-Installer `install_marker` erweitern.
- Direkte Tests fuer Delegation und Fehlerpropagation ergaenzen.
- Normale Aufrufer unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_install_pane_drag_marker` delegiert ueber `install_marker`.
- Tests fuer Argumentweitergabe und Fehlerpropagation ergaenzt.
- Keine sichtbaren Texte, Widget-Optionen, Layout-Aufrufe, Drag-Logik oder Binding-Reihenfolge geaendert.

## Unveraendertes Sollverhalten

- `_install_pane_drag_marker` gibt weiterhin den installierten Marker zurueck.
- Standardpfad nutzt weiterhin `_standalone_radio_pane_install_marker`.
- Farbe und Offset werden weiterhin unveraendert weitergereicht.
- Der oeffentliche Installer-Einstieg bleibt rueckwaertskompatibel fuer bestehende Aufrufe.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-api-delegation.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-api-delegation.md`

## Hinzugefuegte Tests

- `test_install_pane_drag_marker_delegates_to_installer`
- `test_install_pane_drag_marker_propagates_installer_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `224 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `226 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2462 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_api_delegation`: best of 5 `127 ns`

## Bewertung

- Der API-Einstieg ist ohne echte Tk-Widgets direkt testbar.
- Die Dummy-Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen einen Dummy-Installer statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-api-delegation`.
