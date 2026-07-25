# 13 Radio UI Volume EQ Values

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Volume- und EQ-Werte fuer `_init_radio_ui_state` normalisieren
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Werte kommen weiterhin aus `app.radio_settings`.
- Volume nutzt weiterhin Default `50`.
- EQ-Werte nutzen weiterhin Default `0`.
- Ungueltige numerische Werte erzeugen weiterhin `ValueError` ueber `int(...)`.

## Risiken

- Fallback fuer `0` beim Volume muss erhalten bleiben.
- EQ-Werte duerfen negative Werte weiterhin akzeptieren.
- Die Helper duerfen keine Tk-Variablen erzeugen.

## Performance Vorher

- Commit vorher: `79df1af2`
- Messbedingungen: Volume/EQ-Normalisierung mit Settings-Dict, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_volume_eq_values_inline`: best of 5 `0.2743742590000693 s`

## Durchgefuehrte Aenderungen

- `_radio_ui_volume_value` eingefuehrt.
- `_radio_ui_eq_values` eingefuehrt.
- `_init_radio_ui_state` nutzt die normalisierten Werte fuer Tk-Variablen und Labels.
- Direkte Tests fuer Defaults, Stringwerte und ungueltige Zahlen ergaenzt.

## Unveraendertes Sollverhalten

- Volume-Var und Volume-Labels verwenden denselben Wert.
- EQ-Variablen und EQ-Labels verwenden dieselben Werte.
- `volume=0` faellt weiterhin auf Default `50` zurueck.
- Ungueltige Zahlen werden weiterhin nicht still korrigiert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-volume-eq-values.md`
- `docs/refactoring/performance/areas/13-radio-ui-volume-eq-values.md`

## Hinzugefuegte Tests

- `test_radio_ui_volume_value_uses_setting_and_default`
- `test_radio_ui_eq_values_use_settings_and_defaults`
- `test_radio_ui_value_helpers_propagate_invalid_numbers`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `264 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2500 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_volume_eq_values_helper`: best of 5 `0.34003705800023454 s`

## Bewertung

- Die Helper fuegen nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen reine Wertnormalisierung ohne echte Tk-Variablen.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Slider-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-volume-eq-values`.
