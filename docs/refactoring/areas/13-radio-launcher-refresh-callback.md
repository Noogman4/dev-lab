# 13 Radio Launcher Refresh Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Refresh-Callback fuer den Radio-Launcher
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `app`, Detached-Anzeige und Embedded-Anzeige.
- Refresh erfolgt weiterhin ueber `_refresh_radio_launcher_state`.
- `app.refresh_radio_launcher_state` erhaelt weiterhin den lokalen Callback-Namen.
- Initialer Refresh wird weiterhin direkt am Ende von `build_radio_tab` ausgefuehrt.
- Source-basierte Legacy-Marker bleiben in `build_radio_tab` erhalten.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Mehrfache Aufrufe muessen erneut an den Refresh-Helper delegieren.
- Der Helper darf keinen Refresh vorzeitig ausloesen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `11d77ce6`
- Messbedingungen: Dummy-App, Dummy-Anzeige-Callbacks und Dummy-Refresher, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_launcher_refresh_callback`: best of 5 `63 ns`

## Geplante kleine Aenderung

- Refresh-Callback-Erzeugung in `_make_radio_launcher_refresh_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und wiederholte Aufrufe ergaenzen.
- Restlichen Radio-Tab-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_launcher_refresh_callback` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer den Launcher-Refresh-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Launcher-Refresh setzt weiterhin den Status-Text.
- Detached-Ziel zeigt weiterhin den Detached-Placeholder.
- Embedded-Ziel zeigt weiterhin das Embedded-Panel.
- Initialer Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-launcher-refresh-callback.md`
- `docs/refactoring/performance/areas/13-radio-launcher-refresh-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_launcher_refresh_callback_binds_refresh_dependencies`
- `test_make_radio_launcher_refresh_callback_invokes_refresher_each_time`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `215 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `217 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2294 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_refresh_callback`: best of 5 `157 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Launcher-Umschaltung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-launcher-refresh-callback`.
