# 13 Radio UI Playlist Folder Runtime State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Playlist- und Folder-Browser-Runtime-State aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Playlist-Werte kommen weiterhin zuerst aus bestehendem App-State und danach aus `radio_settings`.
- Playlist- und Folder-Browser-`StringVar`s bleiben in `_init_radio_ui_state`.
- Listen fuer Playlist-, System- und Browser-State werden weiterhin frisch erzeugt.
- Keine Tk-Widgets werden erzeugt.

## Risiken

- Prioritaet App-State vor Settings muss erhalten bleiben.
- Leere App-Werte muessen weiterhin auf Settings zurueckfallen.
- Folder-Browser-Defaults und Button-Referenzen muessen unveraendert bleiben.

## Performance Vorher

- Commit vorher: `87fb63ab`
- Messbedingungen: reiner Playlist-/Folder-Runtime-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_playlist_folder_runtime_state_inline`: best of 5 `1.502659236000909 s`

## Durchgefuehrte Aenderungen

- `_radio_ui_playlist_entries` eingefuehrt.
- `_radio_ui_playlist_path` eingefuehrt.
- `_radio_ui_playlists_dir` eingefuehrt.
- `_init_radio_ui_playlist_runtime_state` eingefuehrt.
- `_init_radio_ui_folder_browser_runtime_state` eingefuehrt.
- Direkte Tests fuer Prioritaeten, Defaults und frische Listen ergaenzt.

## Unveraendertes Sollverhalten

- Playlist-Eintraege, Playlist-Pfad und Playlist-Ordner werden unveraendert normalisiert.
- Playlist-Buttons starten weiterhin mit `None`.
- Folder-Browser startet weiterhin im Modus `recordings`.
- Playback-Mode, lokaler Medienpfad und Playlist-Index behalten die bisherige Normalisierung.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-playlist-folder-runtime-state.md`
- `docs/refactoring/performance/areas/13-radio-ui-playlist-folder-runtime-state.md`

## Hinzugefuegte Tests

- `test_radio_ui_playlist_values_prefer_existing_state_then_settings`
- `test_init_radio_ui_playlist_runtime_state_initializes_fresh_state`
- `test_init_radio_ui_folder_browser_runtime_state_initializes_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `272 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2508 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_playlist_folder_runtime_state_helper`: best of 5 `1.6732723400000395 s`

## Bewertung

- Die Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Runtime-State ohne echte Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Playlist- oder Folder-Browser-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-playlist-folder-runtime-state`.
