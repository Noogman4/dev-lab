# 13 Radio UI Header Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Header-, Status-, Stream- und Listen-Variablen aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur uebersetzte `StringVar`-Initialwerte und `radio_handover_title` gesetzt.
- Der normale UI-Pfad nutzt weiterhin `tk.StringVar`.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.
- Keine Widgets, Dateien, Subprozesse oder Radio-Kommandos werden erzeugt.

## Risiken

- Header- und Status-Variablen muessen weiterhin dieselben uebersetzten Defaults erhalten.
- `radio_handover_title` muss weiterhin leer starten.
- Die Stationszaehler-Variable muss weiterhin mit `0` formatiert werden.
- `_init_radio_ui_state` darf keine Reihenfolge verlieren, die spaetere UI-Initialisierung erwartet.

## Performance Vorher

- Commit vorher: `b01b5db2`
- Messbedingungen: Header-StringVar-Werte mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_header_vars_inline`: best of 5 `1.7028966560010304 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_header_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Header-, Status-, Stream-, Bitrate-, Dependency- und Listenstatus-Variablen an den neuen Helper.
- Direkter Test fuer uebersetzte Initialwerte und Aufrufreihenfolge des Var-Builders ergaenzt.

## Unveraendertes Sollverhalten

- Header-Anzeige startet weiterhin mit `Radio: off`.
- Titelanzeige startet weiterhin mit `Title: -`.
- Stream-URL und Bitrate starten weiterhin mit Platzhaltertexten.
- Dependency-Status startet weiterhin mit `Radio ready.`.
- Listenstatus startet weiterhin mit `Stations: 0`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-header-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-header-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_header_vars_initializes_translated_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `275 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2511 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_header_vars_helper`: best of 5 `1.712749784999687 s`

## Bewertung

- Der Helper fuegt nur minimalen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und bleibt nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Header-, Stream- oder Stationslisten-Anzeige.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-header-vars`.
