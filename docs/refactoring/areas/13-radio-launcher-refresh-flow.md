# 13 Radio Launcher Refresh Flow

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Refresh-Entscheidung fuer Radio-Launcher-State
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`, `app.refresh_radio_launcher_state`

## Abhaengigkeiten und Seiteneffekte

- Runtime-State wird weiterhin ueber `_radio_launcher_runtime_state` gelesen.
- Status-Text wird weiterhin ueber `_radio_launcher_status_text` gesetzt.
- Zielmodus wird weiterhin ueber `_radio_launcher_target_mode` entschieden.
- Detached- und Embedded-Callbacks bleiben unveraendert.
- Source-basierte Legacy-Hinweise bleiben im lokalen Refresh-Callback erhalten.

## Risiken

- Der Status muss vor dem Anzeigen des Zielmodus gesetzt werden.
- Detached-Ziel muss weiterhin den Detached-Callback aufrufen.
- Embedded-Ziel muss weiterhin den Embedded-Callback aufrufen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `c0ade6b8`
- Messbedingungen: Dummy-App, Dummy-Core, Dummy-Var und Dummy-Callbacks, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_launcher_refresh_flow`: best of 5 `677 ns`

## Geplante kleine Aenderung

- Refresh-Entscheidung in `_refresh_radio_launcher_state` extrahieren.
- Direkte Tests fuer Detached- und Embedded-Ziel ergaenzen.
- Lokalen `refresh_radio_launcher_state`-Callback und Source-Hinweise erhalten.

## Durchgefuehrte Aenderungen

- `_refresh_radio_launcher_state` eingefuehrt.
- `build_radio_tab` delegiert den lokalen Refresh-Callback an den Helper.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Refresh liest weiterhin den Runtime-State.
- Status-Variable wird weiterhin aktualisiert.
- Detached-Ziel zeigt weiterhin den Detached-Placeholder.
- Embedded-Ziel zeigt weiterhin das Embedded-Panel.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-launcher-refresh-flow.md`
- `docs/refactoring/performance/areas/13-radio-launcher-refresh-flow.md`

## Hinzugefuegte Tests

- `test_refresh_radio_launcher_state_sets_status_and_shows_detached`
- `test_refresh_radio_launcher_state_sets_status_and_shows_embedded`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `198 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `200 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2277 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_refresh_flow`: best of 5 `691 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Core und Dummy-Callbacks statt echter Radio-App-Zustaende.
- Der GUI-Smoke prueft Startbarkeit, aber keinen manuellen Wechsel zwischen Detached und Embedded.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-launcher-refresh-flow`.
