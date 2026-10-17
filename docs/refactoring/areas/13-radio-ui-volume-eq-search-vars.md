# 13 Radio UI Volume EQ Search Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Volume-, Equalizer- und Such-Variablen aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur `IntVar`- und `StringVar`-Initialwerte am App-Objekt gesetzt.
- Die Eingabewerte kommen weiterhin aus `_radio_ui_volume_value`, `_radio_ui_eq_values` und `_radio_ui_search_value`.
- Der normale UI-Pfad nutzt weiterhin `tk.IntVar` und `tk.StringVar`.
- Der neue Helper erlaubt fuer Tests injizierte Var-Builder ohne Tk-Root.

## Risiken

- Volume-Text und Volume-Label muessen weiterhin aus demselben Prozentwert entstehen.
- Equalizer-IntVars und ihre Label-Strings muessen dieselben Werte behalten.
- Der Suchtext muss unveraendert in `radio_search_var` landen.
- `_init_radio_ui_state` darf die bestehende Reihenfolge der Initialisierung nicht verlieren.

## Performance Vorher

- Commit vorher: `9052ffbe`
- Messbedingungen: Volume-/EQ-/Search-Variablen mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_volume_eq_search_vars_inline`: best of 5 `1.9567533569988882 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_volume_eq_search_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Volume-, EQ- und Such-Variablen an den neuen Helper.
- Direkter Test fuer uebersetzte Volume-Texte, EQ-Werte, Suchwert und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Volume-IntVar startet weiterhin mit dem berechneten Einstellungswert.
- Volume-Text nutzt weiterhin `radio_volume_short_label`.
- EQ-Bass, EQ-Mid und EQ-Treble starten weiterhin mit den berechneten Werten.
- EQ-Labelvariablen starten weiterhin als Stringdarstellung der EQ-Werte.
- Suchvariable startet weiterhin mit dem berechneten Suchwert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-volume-eq-search-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-volume-eq-search-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_volume_eq_search_vars_initializes_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `276 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2512 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_volume_eq_search_vars_helper`: best of 5 `1.9925489609995566 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Volume-, EQ- oder Such-Controls.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-volume-eq-search-vars`.
