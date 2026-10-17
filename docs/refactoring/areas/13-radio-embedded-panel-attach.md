# 13 Radio Embedded Panel Attach

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Einhaengen des Embedded-Radio-Panels in den Radio-Tab
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Embedded-Radio-Panel, Launcher-Refresh, Source-basierte Radio-Tests

## Abhaengigkeiten und Seiteneffekte

- `NetMonRadioPanel(host, on_detach=_detach_from_tab, host_app=app)` bleibt im Tab-Aufbau erhalten.
- Panel wird weiterhin an `row=0`, `column=0`, `sticky="nsew"` gegriddet.
- Host-Row `0` erhaelt weiterhin `weight=1`.
- `app.radio_embedded_panel` wird weiterhin auf das neue Panel gesetzt.
- `app.radio_launcher_mode` wird weiterhin auf `embedded` gesetzt.

## Risiken

- Das Embedded-Panel muss nach dem Wechsel sichtbar bleiben.
- Source-basierte Radio-Tests erwarten die Panel-Erzeugungszeile im Tab-Aufbau.
- Launcher-Modus muss nach dem Attach exakt `embedded` sein.
- Der Helper darf keine Panel-Erzeugung oder Detach-Callback-Logik uebernehmen.

## Performance Vorher

- Commit vorher: `f7511556`
- Messbedingungen: Dummy-App, Dummy-Host und Dummy-Panel, direkter Grid-/Rowconfigure-/State-Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_embedded_panel_attach`: Median `0.0002 ms`

## Geplante kleine Aenderung

- Direkten Test fuer Grid, Host-Rowconfigure und App-State ergaenzen.
- Post-Setup des Embedded-Panels aus `_show_embedded_panel` in einen internen Helper extrahieren.
- Panel-Erzeugung, Layoutwerte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_attach_embedded_radio_panel` eingefuehrt.
- `_show_embedded_panel` erzeugt das Panel weiterhin direkt und delegiert nur das Einhaengen an den Helper.
- Keine Widget-Erzeugung, Texte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Embedded-Panel wird weiterhin im Host sichtbar eingehangen.
- Host-Layout bleibt fuer das Panel expandierbar.
- App-State verweist weiterhin auf das aktuelle Embedded-Panel.
- Launcher-Modus wird weiterhin `embedded`.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-embedded-panel-attach.md`
- `docs/refactoring/performance/areas/13-radio-embedded-panel-attach.md`

## Hinzugefuegte Tests

- `test_attach_embedded_radio_panel_grids_panel_and_sets_app_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `139 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `140 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2217 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_embedded_panel_attach`: Median `0.0002 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Host und Dummy-Panel statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Radio-Tab-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-embedded-panel-attach`.
