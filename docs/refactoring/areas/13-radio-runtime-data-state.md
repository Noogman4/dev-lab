# 13 Radio Runtime Data State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Radio-Daten- und Auswahl-State aus `_init_radio_runtime_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_runtime_state`

## Abhaengigkeiten und Seiteneffekte

- `radio_controller.default_radio_settings` bleibt die Quelle fuer Default-Radio-Settings.
- `ttk.Style`, Runtime-Laden und ProjectM-Preset-Initialisierung bleiben in `_init_radio_runtime_state`.
- Es werden nur Attribute am App-Objekt gesetzt.
- Keine Tk-Widgets werden erzeugt.

## Risiken

- Listen und Dicts muessen weiterhin frisch initialisiert werden.
- Initialwerte fuer aktuellen Sender, Suche und Reachability muessen exakt erhalten bleiben.
- GUI-Style-Initialisierung darf nicht in den neuen Helper wandern.

## Performance Vorher

- Commit vorher: `54ba16a1`
- Messbedingungen: reiner Daten- und Auswahl-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_runtime_data_state_inline`: best of 5 `0.49489559100038605 s`

## Durchgefuehrte Aenderungen

- `_init_radio_runtime_data_state` eingefuehrt.
- `_init_radio_runtime_selection_state` eingefuehrt.
- `_init_radio_runtime_state` delegiert die beiden nicht-GUI-State-Bloecke an die neuen Helper.
- Direkte Tests fuer beide Helper ergaenzt.

## Unveraendertes Sollverhalten

- Radio-Prozess, Stop-Flag und IPC-Pfad starten unveraendert.
- Radio-DB, Favoriten und Suchergebnisse starten leer.
- Radio-Settings kommen weiterhin aus `radio_controller.default_radio_settings`.
- Aktueller Sender, Suchseite, Filter-IDs, Live-Status und Reachability starten unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-runtime-data-state.md`
- `docs/refactoring/performance/areas/13-radio-runtime-data-state.md`

## Hinzugefuegte Tests

- `test_init_radio_runtime_data_state_initializes_radio_data`
- `test_init_radio_runtime_selection_state_initializes_selection_data`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `259 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2495 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_runtime_data_state_helper`: best of 5 `0.6810308980002446 s`

## Bewertung

- Der Helper fuegt nur kleinen Aufruf- und Test-Lambda-Overhead hinzu.
- Der Pfad laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die Helper auf einem `SimpleNamespace`, nicht auf einer echten Tk-App.
- Runtime-Laden und GUI-Startbarkeit werden ueber Regressionstests und GUI-Smoke abgedeckt.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-runtime-data-state`.
