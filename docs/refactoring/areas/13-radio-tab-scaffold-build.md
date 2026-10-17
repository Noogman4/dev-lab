# 13 Radio Tab Scaffold Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: oberer Scaffold-Aufbau des Radio-Tabs
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Body, Status-Variable, Pane und Sections werden weiterhin in derselben Reihenfolge aufgebaut.
- Bottom-Placeholder-Callback wird weiterhin vor dem State-Init erzeugt.
- Pane-Sections werden weiterhin vor dem State-Init hinzugefuegt.
- Initialer Bottom-Placeholder wird weiterhin direkt nach dem State-Init angezeigt.
- Launcher-Callbacks und initialer Launcher-Refresh bleiben unveraendert.

## Risiken

- Scaffold-Aufbau muss dieselben Objekte an die nachfolgenden Launcher-Callbacks liefern.
- `app.radio_launcher_status_var` muss weiterhin vor dem Launcher-Refresh gesetzt sein.
- Bottom-Placeholder muss weiterhin einmal initial angezeigt werden.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `8c160ac9`
- Messbedingungen: Dummy-App und Dummy-Bausteine, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_tab_scaffold_build`: best of 5 `374 ns`

## Geplante kleine Aenderung

- Scaffold-Aufbau in `_build_radio_tab_scaffold` extrahieren.
- Direkte Tests fuer Reihenfolge, App-State, Rueckgabewerte und initiale Bottom-Anzeige ergaenzen.
- Launcher-Callback-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_build_radio_tab_scaffold` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer Body, Status-Var, Pane, Sections, State-Init und Bottom-Placeholder.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Radio-Tab-Scaffold wird weiterhin vollstaendig aufgebaut.
- Radio-Status-Variable wird weiterhin am App-Objekt gesetzt.
- Bottom-Placeholder erscheint weiterhin initial.
- Launcher-Refresh bleibt weiterhin der letzte Schritt.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-tab-scaffold-build.md`
- `docs/refactoring/performance/areas/13-radio-tab-scaffold-build.md`

## Hinzugefuegte Tests

- `test_build_radio_tab_scaffold_builds_sections_initializes_and_shows_bottom`
- `test_build_radio_tab_scaffold_returns_host_and_bottom_callback`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `217 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `219 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2296 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_tab_scaffold_build`: best of 5 `448 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Bausteine statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Radio-Tab-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-tab-scaffold-build`.
