# 13 Radio Detached Placeholder State

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: State-Setzen nach Aufbau des Detached-Placeholders
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Detached-Placeholder, Launcher-Refresh, Feature-Button-Registrierung

## Abhaengigkeiten und Seiteneffekte

- Reattach-Button wird weiterhin fuer das Feature `radio` registriert.
- `app.radio_launcher_mode` wird weiterhin auf `detached` gesetzt.
- Widget-Aufbau und Grid-Werte bleiben unveraendert.
- Reattach-Command bleibt unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Der Reattach-Button muss weiterhin in der Feature-Button-Steuerung landen.
- Launcher-Modus muss nach dem Placeholder-Aufbau exakt `detached` sein.
- Der Helper darf keine Tk-Widgets erzeugen.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `ca3b1591`
- Messbedingungen: Dummy-App und Dummy-Button, direkter Register-/State-Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_detached_placeholder_state`: Median `0.0001 ms`

## Geplante kleine Aenderung

- Direkten Test fuer Button-Registrierung und Launcher-Mode ergaenzen.
- State-Setzen des Detached-Placeholders in einen internen Helper extrahieren.
- Widget-Aufbau, Layoutwerte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_set_detached_radio_placeholder_state` eingefuehrt.
- `_show_detached_placeholder` delegiert Button-Registrierung und Launcher-Mode an den Helper.
- Keine Widget-Struktur, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Reattach-Button wird weiterhin fuer `radio` registriert.
- Launcher-Modus wird weiterhin `detached`.
- Reattach-Button-Command bleibt `app.reattach_radio_app`.
- Detached-Placeholder wird weiterhin nur bei Mode-Wechsel neu aufgebaut.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-detached-placeholder-state.md`
- `docs/refactoring/performance/areas/13-radio-detached-placeholder-state.md`

## Hinzugefuegte Tests

- `test_set_detached_radio_placeholder_state_registers_button_and_mode`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `140 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `141 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2218 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detached_placeholder_state`: Median `0.0001 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-App und Dummy-Button statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Reattach-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detached-placeholder-state`.
