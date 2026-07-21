# 13 Radio Detach Callback

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Detach-Callback des Embedded-Radio-Panels
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Embedded-Radio-Panel, externer Radio-Launcher, Source-basierte Radio-Tests

## Abhaengigkeiten und Seiteneffekte

- Delegiert weiterhin an `app.open_radio_external_app`.
- Die `NetMonRadioPanel(host, on_detach=_detach_from_tab, host_app=app)`-Zeile bleibt im Tab-Aufbau erhalten.
- Keine Aenderung an Panel-Erzeugung, Grid-Werten oder Launcher-Modus.
- Keine Aenderung an gespeicherten Radio-Konfigurationen oder externen Player-Aufrufen.

## Risiken

- Der Detach-Button im Embedded-Panel muss weiterhin den externen Radio-Launcher ausloesen.
- Source-basierte Radio-Tests erwarten die Panel-Erzeugungszeile im Tab-Aufbau.
- Der Helper darf keine Tk-Widgets erzeugen.
- Fehlerverhalten von `open_radio_external_app` bleibt unveraendert, weil nichts abgefangen wird.

## Performance Vorher

- Commit vorher: `5530c889`
- Messbedingungen: direkter Callback-Aufruf mit Dummy-App, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_detach_callback`: Median `0.0001 ms`

## Geplante kleine Aenderung

- Direkten Test fuer die Detach-Delegation ergaenzen.
- Den Aufruf von `app.open_radio_external_app` in einen internen Helper extrahieren.
- Panel-Erzeugungszeile, Layout und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_detach_radio_from_tab` eingefuehrt.
- Der verschachtelte `_detach_from_tab`-Callback delegiert an den Helper.
- Keine Widget-Struktur, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Embedded-Panel erhaelt weiterhin einen `on_detach`-Callback.
- Detach delegiert weiterhin direkt an `app.open_radio_external_app`.
- Rueckgabewert des App-Aufrufs wird weiterhin durchgereicht.
- Exceptions wuerden weiterhin wie bisher durchgereicht.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-detach-callback.md`
- `docs/refactoring/performance/areas/13-radio-detach-callback.md`

## Hinzugefuegte Tests

- `test_detach_radio_from_tab_delegates_to_app`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `138 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `139 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2216 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detach_callback`: Median `0.0001 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die Callback-Delegation direkt, aber keine vollstaendige manuelle Detach/Reattach-Bedienung.
- Source-basierte Tests bleiben als Legacy-Schutz erhalten.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detach-callback`.
