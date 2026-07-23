# 13 Radio Launcher Display Callbacks

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: lokale Anzeige-Callbacks fuer detached Placeholder und embedded Panel
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`

## Abhaengigkeiten und Seiteneffekte

- Detached-Callback bindet weiterhin `app`, `host` und den Host-Clear-Callback.
- Embedded-Callback bindet weiterhin `app`, `host` und den Host-Clear-Callback.
- Anzeige erfolgt weiterhin ueber `_show_radio_detached_placeholder` und `_show_radio_embedded_panel`.
- Launcher-Refresh erhaelt weiterhin beide Anzeige-Callbacks.
- Source-basierte Legacy-Marker bleiben in `build_radio_tab` erhalten.

## Risiken

- Die Callbacks muessen dieselben Objekte binden wie die lokalen Funktionen vorher.
- Mehrfache Aufrufe muessen erneut an die Anzeige-Helper delegieren.
- Der Helper darf keine Widget-Erzeugung vorziehen.
- Source-basierte Radio-Tests duerfen durch die Extraktion nicht brechen.

## Performance Vorher

- Commit vorher: `9a2cbae0`
- Messbedingungen: Dummy-App, Dummy-Host und Dummy-Shower, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_launcher_display_callback_detached`: best of 5 `64 ns`
- `radio_launcher_display_callback_embedded`: best of 5 `64 ns`

## Geplante kleine Aenderung

- Detached-Callback-Erzeugung in `_make_radio_detached_placeholder_callback` extrahieren.
- Embedded-Callback-Erzeugung in `_make_radio_embedded_panel_callback` extrahieren.
- Direkte Tests fuer gebundene Objekte und wiederholte Aufrufe ergaenzen.
- Restlichen Radio-Tab-Aufbau unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_make_radio_detached_placeholder_callback` eingefuehrt.
- `_make_radio_embedded_panel_callback` eingefuehrt.
- `build_radio_tab` nutzt beide Helper fuer die Launcher-Anzeige-Callbacks.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Detached-Zustand zeigt weiterhin den externen Radio-Placeholder.
- Embedded-Zustand zeigt weiterhin das eingebettete Radio-Panel.
- Host-Clear wird weiterhin vor dem Anzeigen genutzt.
- Launcher-Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-launcher-display-callbacks.md`
- `docs/refactoring/performance/areas/13-radio-launcher-display-callbacks.md`

## Hinzugefuegte Tests

- `test_make_radio_detached_placeholder_callback_binds_app_host_and_clearer`
- `test_make_radio_detached_placeholder_callback_invokes_shower_each_time`
- `test_make_radio_embedded_panel_callback_binds_app_host_and_clearer`
- `test_make_radio_embedded_panel_callback_invokes_shower_each_time`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `211 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `215 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2292 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_display_callback_detached`: best of 5 `154 ns`
- `radio_launcher_display_callback_embedded`: best of 5 `153 ns`

## Bewertung

- Die Helper fuegen nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Beide Operationen bleiben deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Launcher-Umschaltung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-launcher-display-callbacks`.
