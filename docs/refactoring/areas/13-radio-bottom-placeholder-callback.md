# 13 Radio Bottom Placeholder Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokaler Callback fuer den unteren Radio-Placeholder
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Callback bindet weiterhin `bottom_section` und `app`.
- Placeholder wird weiterhin ueber `_show_radio_bottom_placeholder_for_app` angezeigt.
- `_clear_radio_tab_host` erhaelt weiterhin denselben Callback.
- Initiale Placeholder-Anzeige nach der State-Initialisierung bleibt unveraendert.
- Pane-, Section- und Launcher-Aufbau bleiben unveraendert.

## Risiken

- Der Callback muss dieselben Objekte binden wie die lokale Funktion vorher.
- Mehrfache Aufrufe muessen den Placeholder jedes Mal erneut anzeigen.
- Der Helper darf keine Widget-Erzeugung vorziehen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `04799746`
- Messbedingungen: Dummy-App, Dummy-Bottom-Section und Dummy-Shower, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_bottom_placeholder_callback`: best of 5 `59 ns`

## Geplante kleine Aenderung

- Callback-Erzeugung in `_make_radio_bottom_placeholder_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und wiederholte Aufrufe ergaenzen.
- Restlichen Radio-Tab-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_bottom_placeholder_callback` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer den Bottom-Placeholder-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Unterer Placeholder erscheint weiterhin beim Aufbau des Radio-Tabs.
- Host-Clear zeigt weiterhin den unteren Placeholder erneut an.
- Bottom-Section bleibt unveraendert.
- Launcher-Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-bottom-placeholder-callback.md`
- `docs/refactoring/performance/areas/13-radio-bottom-placeholder-callback.md`

## Hinzugefuegte Tests

- `test_make_radio_bottom_placeholder_callback_binds_app_and_section`
- `test_make_radio_bottom_placeholder_callback_invokes_shower_each_time`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `207 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `209 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2286 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_bottom_placeholder_callback`: best of 5 `139 ns`

## Bewertung

- Der Helper fuegt nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Bottom-Placeholder-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-bottom-placeholder-callback`.
