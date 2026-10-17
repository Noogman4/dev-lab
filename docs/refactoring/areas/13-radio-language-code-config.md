# 13 Radio Language Code Config

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Sprachcode-Auswertung aus `_load_language` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `NetMonRadioApp._load_language`

## Abhaengigkeiten und Seiteneffekte

- Es wird nur ein bereits geladenes Config-Payload ausgewertet.
- Datei-I/O fuer `config.json` und Sprachdateien bleibt unveraendert in `_load_language`.
- Der Helper `_radio_language_code_from_config_payload` hat keine Datei-, Netzwerk-, Tk- oder Subprocess-Zugriffe.

## Risiken

- Gueltige Codes muessen weiterhin nur `de` und `en` sein.
- Gross-/Kleinschreibung und Leerzeichen muessen weiterhin normalisiert werden.
- Ungueltige Werte, leere Payloads und Nicht-Dicts muessen weiterhin auf `de` fallen.
- `_load_language` muss weiterhin Exceptions beim Dateilesen schlucken.

## Performance Vorher

- Commit vorher: `65820471`
- Messbedingungen: Sprachcode-Auswertung aus Dict-Payload, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_language_code_config_inline`: best of 5 `0.08908957800122153 s`

## Durchgefuehrte Aenderungen

- `_radio_language_code_from_config_payload` eingefuehrt.
- `_load_language` delegiert die Sprachcode-Auswertung an den neuen Helper.
- Direkte Tests fuer gueltige Codes und Fallbacks ergaenzt.

## Unveraendertes Sollverhalten

- Ohne gueltige Config bleibt Deutsch der Default.
- `en` wird weiterhin akzeptiert.
- `de` wird weiterhin akzeptiert.
- Sprachdatei-Laden und Translation-Dict-Zuweisung bleiben unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-language-code-config.md`
- `docs/refactoring/performance/areas/13-radio-language-code-config.md`

## Hinzugefuegte Tests

- `test_radio_language_code_from_config_payload_accepts_supported_codes`
- `test_radio_language_code_from_config_payload_falls_back_to_german`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `294 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2530 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_language_code_config_helper`: best of 5 `0.12287723400004325 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft nur beim App-Start und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist direkte Testbarkeit der Config-Normalisierung ohne Datei-I/O.

## Bekannte Restrisiken

- Die direkten Tests pruefen nur Payload-Auswertung, nicht das Laden realer Sprachdateien.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Pruefung aller Uebersetzungen.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-language-code-config`.
