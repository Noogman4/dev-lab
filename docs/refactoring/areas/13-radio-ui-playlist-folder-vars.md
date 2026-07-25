# 13 Radio UI Playlist Folder Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Playlist- und Folder-Browser-StringVars aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur uebersetzte `StringVar`-Initialwerte am App-Objekt gesetzt.
- Playlist-Runtime-State bleibt weiterhin in `_init_radio_ui_playlist_runtime_state`.
- Folder-Browser-Runtime-State bleibt weiterhin in `_init_radio_ui_folder_browser_runtime_state`.
- Recordings- und Mini-Player-Variablen bleiben in diesem Schritt unveraendert.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.

## Risiken

- Playlist-Status muss weiterhin mit `Playlist: 0 Dateien` starten.
- Folder-Browser-Titel muss weiterhin mit `Aufnahmeordner` starten.
- Folder-Browser-Pfad muss weiterhin leer starten.
- `_init_radio_ui_state` muss Playlist-Runtime-State weiterhin vor den Playlist-/Folder-Variablen initialisieren.

## Performance Vorher

- Commit vorher: `665cb8ec`
- Messbedingungen: Playlist-/Folder-Browser-StringVars mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_playlist_folder_vars_inline`: best of 5 `0.4884465140003158 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_playlist_folder_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Playlist-Status, Folder-Browser-Titel und Folder-Browser-Pfad an den neuen Helper.
- Direkter Test fuer uebersetzte Initialwerte und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Playlist-Status startet weiterhin mit `Playlist: 0 Dateien`.
- Folder-Browser-Titel startet weiterhin mit `Aufnahmeordner`.
- Folder-Browser-Pfad startet weiterhin leer.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-playlist-folder-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-playlist-folder-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_playlist_folder_vars_initializes_translated_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `280 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2516 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_playlist_folder_vars_helper`: best of 5 `0.5292913070006762 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Playlist- oder Folder-Browser-Controls.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-playlist-folder-vars`.
