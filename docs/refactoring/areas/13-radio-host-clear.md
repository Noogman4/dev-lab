# 13 Radio Host Clear

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Aufraeumen des Radio-Tab-Hosts beim Wechsel zwischen Embedded-Panel und Detached-Platzhalter
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab, Detach/Reattach-Refresh, Embedded-Radio-Panel

## Abhaengigkeiten und Seiteneffekte

- Stoppt vorhandene Radio-Wiedergabe weiterhin mit `async_mode=False`.
- Zerstoert weiterhin alle aktuellen Host-Kinder.
- Fehler beim Stoppen oder Zerstoeren werden weiterhin geschluckt.
- Setzt `app.radio_embedded_panel` weiterhin erst im aufrufenden App-Kontext zurueck.
- Aktualisiert den unteren Placeholder weiterhin im aufrufenden App-Kontext.

## Risiken

- Ein vorhandenes Embedded-Panel muss beim Host-Wechsel weiterhin gestoppt werden.
- Defekte oder bereits entfernte Widgets duerfen den Refresh weiterhin nicht abbrechen.
- Die App-Zustandsfelder duerfen nicht in den Helper verschoben werden, damit der Schritt klein bleibt.
- Source-basierte Radio-Tests duerfen nicht durch Layout-Umbau gebrochen werden.

## Performance Vorher

- Commit vorher: `5b48cf1d`
- Messbedingungen: synthetischer Host mit drei Dummy-Kindern und Dummy-Panel, direkter Stop-/Destroy-Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_host_clear`: Median `0.0003 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die Host-Aufraeumlogik ergaenzen.
- Stop-/Destroy-Ablauf aus der verschachtelten `_clear_host`-Funktion in einen internen Helper extrahieren.
- App-Zustand, Placeholder-Aktualisierung, Layout und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_clear_radio_host` eingefuehrt.
- `_clear_host` delegiert Stoppen und Widget-Zerstoerung an den Helper.
- Fehlerbehandlung beim Stoppen und Zerstoeren bleibt unveraendert tolerant.
- Keine Widget-Struktur, Texte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Ein vorhandenes Panel wird vor dem Host-Wechsel gestoppt.
- Host-Kinder werden zerstoert.
- Fehler beim Panel-Stop oder Child-Destroy brechen den Refresh nicht ab.
- `app.radio_embedded_panel` wird weiterhin auf `None` gesetzt.
- Der untere Placeholder wird weiterhin nach dem Host-Clear wieder aufgebaut.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-host-clear.md`
- `docs/refactoring/performance/areas/13-radio-host-clear.md`

## Hinzugefuegte Tests

- `test_clear_radio_host_stops_panel_and_destroys_children`
- `test_clear_radio_host_ignores_stop_and_destroy_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `126 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `128 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2205 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_host_clear`: Median `0.0003 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Hosts statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Detach/Reattach-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-host-clear`.
