# 13 Radio Tab Host Clear Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Callback zum Leeren des Radio-Hosts
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `app`, `host` und den Bottom-Placeholder-Callback.
- Host wird weiterhin ueber `_clear_radio_tab_host` geleert.
- Bottom-Placeholder wird weiterhin nach dem Host-Clear angezeigt.
- Detach-Placeholder und Embedded-Panel erhalten weiterhin denselben Clear-Callback.
- Pane-, Section- und Launcher-Aufbau bleiben unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Mehrfache Aufrufe muessen den Host jedes Mal erneut leeren.
- Der Helper darf kein Widget vorzeitig zerstoeren.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `a4251df1`
- Messbedingungen: Dummy-App, Dummy-Host und Dummy-Clearer, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_tab_clear_host_callback`: best of 5 `63 ns`

## Geplante kleine Aenderung

- Callback-Erzeugung in `_make_radio_tab_host_clear_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und wiederholte Aufrufe ergaenzen.
- Restlichen Radio-Tab-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_tab_host_clear_callback` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer den Host-Clear-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Host-Clear stoppt und entfernt weiterhin das eingebettete Panel.
- App-State fuer `radio_embedded_panel` wird weiterhin zurueckgesetzt.
- Unterer Placeholder wird weiterhin nach dem Host-Clear angezeigt.
- Launcher-Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-tab-host-clear-callback.md`
- `docs/refactoring/performance/areas/13-radio-tab-host-clear-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_tab_host_clear_callback_binds_app_host_and_placeholder`
- `test_make_radio_tab_host_clear_callback_invokes_clearer_each_time`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `209 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `211 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2288 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_tab_clear_host_callback`: best of 5 `159 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Host-Clear-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-tab-host-clear-callback`.
