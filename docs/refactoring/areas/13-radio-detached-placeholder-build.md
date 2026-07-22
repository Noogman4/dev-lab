# 13 Radio Detached Placeholder Build

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Widget-Aufbau des Detached-Placeholders im Radio-Tab
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Detached-Placeholder, Launcher-Refresh, Reattach-Workflow

## Abhaengigkeiten und Seiteneffekte

- Titel-, Hinweis-, Status- und Reattach-Button-Widgets bleiben unveraendert.
- Grid-Positionen und Padding-Werte bleiben unveraendert.
- Reattach-Command bleibt `app.reattach_radio_app`.
- Button-Registrierung und Launcher-Mode bleiben im aufrufenden State-Helper.
- Source-basierte Legacy-Marker bleiben im Tab-Aufbau erhalten.

## Risiken

- Der sichtbare Detached-Placeholder darf sich nicht aendern.
- Der Reattach-Button muss weiterhin zurueckgegeben und registriert werden.
- Status-Label muss weiterhin dieselbe `radio_launcher_status_var` nutzen.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `a26a51c6`
- Messbedingungen: Dummy-Widget-Factories fuer Frame, Label und Button, direkter Widget-Aufbau, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_detached_placeholder_build`: Median `0.0020 ms`

## Geplante kleine Aenderung

- Direkten Test fuer den Detached-Placeholder-Widget-Aufbau ergaenzen.
- Frame-, Label- und Button-Aufbau in einen internen Helper mit injizierbaren Factories extrahieren.
- Textauswahl, State-Setzen und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_build_detached_radio_placeholder` eingefuehrt.
- `_show_detached_placeholder` delegiert den Widget-Aufbau an den Helper.
- Button-Registrierung und `detached`-Mode bleiben in `_set_detached_radio_placeholder_state`.
- Keine sichtbaren Texte, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Placeholder-Box wird weiterhin mit `padding=18` im Host erzeugt.
- Titel-Label nutzt weiterhin `("TkDefaultFont", 12, "bold")`.
- Hinweis-Label nutzt weiterhin `justify="left"` und `wraplength=760`.
- Status-Label nutzt weiterhin `textvariable=app.radio_launcher_status_var`.
- Reattach-Button nutzt weiterhin den uebersetzten Buttontext und `app.reattach_radio_app`.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-detached-placeholder-build.md`
- `docs/refactoring/performance/areas/13-radio-detached-placeholder-build.md`

## Hinzugefuegte Tests

- `test_build_detached_radio_placeholder_creates_expected_widgets`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `141 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `142 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2219 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detached_placeholder_build`: Median `0.0020 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Dummy-Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Widget-Factories statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Reattach-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detached-placeholder-build`.
