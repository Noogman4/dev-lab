# 13 Radio UI Database Custom Vars

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Datenbank-, Favoriten- und Custom-Form-Variablen aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur `BooleanVar`-, `DoubleVar`- und `StringVar`-Initialwerte am App-Objekt gesetzt.
- Der Datenbankzaehler kommt weiterhin aus `_radio_ui_database_count`.
- Status-Indicator-Bilder bleiben bewusst in `_init_radio_ui_state`, weil sie Bildobjekte bauen.
- Der neue Helper erlaubt fuer Tests injizierte Var-Builder ohne Tk-Root.

## Risiken

- Favoriten-Status muss weiterhin mit `False` starten.
- Datenbankzaehler muss weiterhin mit dem berechneten Count formatiert werden.
- Datenbank-Progress und Auswahlmodus muessen ihre Defaults behalten.
- Custom-Form-Felder muessen weiterhin leer starten.
- Custom-Submit-Text muss weiterhin uebersetzt initialisiert werden.

## Performance Vorher

- Commit vorher: `ef7121de`
- Messbedingungen: Datenbank-/Favoriten-/Custom-Form-Variablen mit `SimpleNamespace`, Dummy-Var-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_database_custom_vars_inline`: best of 5 `2.4601719040001626 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_database_custom_vars` eingefuehrt.
- `_init_radio_ui_state` delegiert Datenbank-, Favoriten- und Custom-Form-Variablen an den neuen Helper.
- Direkter Test fuer uebersetzte Texte, Defaults und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Favoritenfilter startet weiterhin deaktiviert.
- Seitentext startet weiterhin mit `1/1`.
- Datenbankzaehler startet weiterhin mit dem berechneten Count.
- Datenbank-Progress startet weiterhin mit `0.0`.
- Datenbank-Exklusivmodus startet weiterhin aktiv.
- Custom-Form-Felder und Status starten weiterhin leer.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-database-custom-vars.md`
- `docs/refactoring/performance/areas/13-radio-ui-database-custom-vars.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_database_custom_vars_initializes_values`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `277 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2513 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_database_custom_vars_helper`: best of 5 `2.54130477200124 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-Root.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Variablen statt echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Bedienung der Datenbank- oder Custom-Form-Controls.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-database-custom-vars`.
