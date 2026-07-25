# 13 Radio UI Theme Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Theme-StringVar aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es wird nur `radio_theme_name_var` am App-Objekt gesetzt.
- Logo-Runtime-State bleibt weiterhin in `_init_radio_ui_logo_runtime_state`.
- Der normale UI-Pfad nutzt weiterhin `tk.StringVar`.
- Der neue Helper erlaubt fuer Tests einen injizierten Var-Builder ohne Tk-Root.

## Risiken

- `radio_theme_name_var` muss weiterhin leer starten.
- `_init_radio_ui_state` muss Logo-Runtime-State weiterhin vor der Theme-Variable initialisieren.

## Performance Vorher

- Commit vorher: `7723d10f`
- Messbedingungen: Theme-StringVar mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_theme_vars_inline`: best of 5 `0.1374119560005056 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_theme_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert `radio_theme_name_var` an den neuen Helper.
- Direkter Test fuer den leeren Initialwert und Builder-Aufruf ergaenzt.

## Unveraendertes Sollverhalten

- Theme-Name startet weiterhin leer.
- Spaetere Theme-Updates koennen `radio_theme_name_var` weiterhin setzen.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-theme-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-theme-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_theme_vars_initializes_empty_theme_name`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `283 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2519 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_theme_vars_helper`: best of 5 `0.17177745899971342 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist, dass `_init_radio_ui_state` keine direkte Tk-Variablenanlage mehr fuer den Theme-Namen enthaelt.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Pruefung der Theme-Auswahl.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-theme-vars`.
