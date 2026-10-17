# 13 Radio Tab Body Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufbau des Radio-Tab-Containers und Body-Frames
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- `app.tab_radio` wird weiterhin als Frame unter `app.tools_nb` erzeugt.
- Notebook-Tab wird weiterhin mit `tools_tab_radio` und Fallback `Radio` hinzugefuegt.
- Body-Frame wird weiterhin unter `app.tab_radio` erzeugt und expandierend gepackt.
- Body-Layout wird weiterhin ueber `_configure_single_cell_expand` vorbereitet.
- Pane-, Sections- und Launcher-Aufbau bleiben unveraendert.

## Risiken

- `app.tab_radio` muss vor dem Pane- und Section-Aufbau gesetzt sein.
- Der Notebook-Tab muss weiterhin denselben uebersetzten Text erhalten.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.
- Der Helper darf keine Pane- oder Launcher-Initialisierung uebernehmen.

## Performance Vorher

- Commit vorher: `b5ec59e4`
- Messbedingungen: Dummy-App, Dummy-Notebook und Dummy-Frame, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_tab_body_build`: best of 5 `616 ns`

## Geplante kleine Aenderung

- Tab- und Body-Aufbau in `_build_radio_tab_body` extrahieren.
- Direkte Tests fuer Notebook-Add, App-State, Body-Pack und Layout ergaenzen.
- Restlichen Radio-Tab-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_build_radio_tab_body` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer Tab- und Body-Erzeugung.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Radio-Tab wird weiterhin im Tools-Notebook angelegt.
- Body-Frame expandiert weiterhin vollstaendig im Radio-Tab.
- Radio-Panedwindow wird weiterhin danach im Body aufgebaut.
- Radio-Launcher-Status und Sections bleiben unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-tab-body-build.md`
- `docs/refactoring/performance/areas/13-radio-tab-body-build.md`

## Hinzugefuegte Tests

- `test_build_radio_tab_body_creates_tab_adds_notebook_and_body`
- `test_build_radio_tab_body_returns_body_frame`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `205 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `207 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2284 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_tab_body_build`: best of 5 `661 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Frames statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Notebook-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-tab-body-build`.
