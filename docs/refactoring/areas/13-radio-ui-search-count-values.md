# 13 Radio UI Search Count Values

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Suchtext- und Datenbankzaehlwerte fuer `_init_radio_ui_state` normalisieren
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Suchtext kommt weiterhin aus `app.radio_settings["last_search"]`.
- Fehlender oder leerer Suchtext wird weiterhin zu `""`.
- Datenbankzaehler nutzt weiterhin `app.radio_db`.
- Fehlendes oder leeres `radio_db` wird weiterhin als `0` gezaehlt.

## Risiken

- Der Suchtext darf nicht ungewollt getrimmt werden.
- `None` fuer `radio_db` muss weiterhin als leer gelten.
- Die Helper duerfen keine Tk-Variablen erzeugen.

## Performance Vorher

- Commit vorher: `3e8b32f0`
- Messbedingungen: Suchtext- und DB-Count-Normalisierung mit Dummy-Objekt, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_search_count_values_inline`: best of 5 `0.07673324600000342 s`

## Durchgefuehrte Aenderungen

- `_radio_ui_search_value` eingefuehrt.
- `_radio_ui_database_count` eingefuehrt.
- `_init_radio_ui_state` nutzt die normalisierten Werte fuer `StringVar`-Initialisierung.
- Direkte Tests fuer Suchtext-Fallbacks und DB-Count-Faelle ergaenzt.

## Unveraendertes Sollverhalten

- Suchtext bleibt exakt der gespeicherte String.
- Fehlender Suchtext bleibt leer.
- DB-Count ist weiterhin die Laenge von `radio_db`.
- Die Anzeigeformatierung ueber `app.tr("radio_database_count", ...)` bleibt unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-search-count-values.md`
- `docs/refactoring/performance/areas/13-radio-ui-search-count-values.md`

## Hinzugefuegte Tests

- `test_radio_ui_search_value_uses_setting_and_default`
- `test_radio_ui_database_count_handles_missing_and_empty_db`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `266 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2502 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_search_count_values_helper`: best of 5 `0.11710662099994806 s`

## Bewertung

- Die Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen reine Wertnormalisierung ohne echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Suchfeld-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-search-count-values`.
