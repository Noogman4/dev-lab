# 13 Radio Launcher Refresh Install

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Launcher-Callback-Verkabelung und initialer Refresh
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Host-Clear-, Detached-, Embedded- und Refresh-Callback werden weiterhin in derselben Reihenfolge erzeugt.
- `app.refresh_radio_launcher_state` wird weiterhin gesetzt.
- Initialer Launcher-Refresh wird weiterhin direkt ausgefuehrt.
- Source-basierte Legacy-Marker bleiben in `build_radio_tab` erhalten.
- Scaffold-Aufbau bleibt unveraendert.

## Risiken

- Die erzeugten Callbacks muessen dieselben Objekte binden wie vorher.
- Der initiale Refresh darf nicht entfallen oder vorgezogen werden.
- `app.refresh_radio_launcher_state` muss weiterhin den Refresh-Callback referenzieren.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `67f14fb7`
- Messbedingungen: Dummy-App, Dummy-Host und Dummy-Callback-Factories, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_launcher_wiring`: best of 5 `208 ns`

## Geplante kleine Aenderung

- Launcher-Verkabelung in `_install_radio_launcher_refresh` extrahieren.
- Direkte Tests fuer Reihenfolge, App-Zuweisung, initialen Refresh und Rueckgabewert ergaenzen.
- Scaffold-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_install_radio_launcher_refresh` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer Launcher-Callback-Verkabelung und initialen Refresh.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Launcher-Refresh ist weiterhin als App-Callback verfuegbar.
- Initialer Refresh startet weiterhin sofort am Ende des Radio-Tab-Aufbaus.
- Detached- und Embedded-Anzeige bleiben unveraendert.
- Host-Clear und Bottom-Placeholder bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-launcher-refresh-install.md`
- `docs/refactoring/performance/areas/13-radio-launcher-refresh-install.md`

## Hinzugefuegte Tests

- `test_install_radio_launcher_refresh_wires_assigns_and_runs_refresh`
- `test_install_radio_launcher_refresh_returns_assigned_callback`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `219 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `221 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2298 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_wiring`: best of 5 `278 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Factories statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Launcher-Umschaltung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-launcher-refresh-install`.
