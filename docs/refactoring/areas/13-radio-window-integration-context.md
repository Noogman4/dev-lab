# 13 Radio Window Integration Context

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Window-Integration-Context aus `NetMonRadioApp._window_integration_context` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `NetMonRadioApp._window_integration_context`

## Abhaengigkeiten und Seiteneffekte

- Es werden nur Attribute vom App-Objekt gelesen und in ein Dict formatiert.
- Icon-Pfad-Aufloesung und Icon-Anwendung bleiben unveraendert.
- Window-Diagnostic-Logging nutzt weiterhin `self._window_integration_context()`.
- Bestehende Source-Anker fuer Window-Integration-Methoden bleiben erhalten.

## Risiken

- `window_class` und `startup_wm_class` muessen weiterhin `NetMonRadio` bleiben.
- `icon_path` muss weiterhin getrimmt werden.
- `icon_applied` muss weiterhin `yes` oder `no` sein.
- `started_from` muss weiterhin getrimmt werden.
- Fehlende Attribute muessen weiterhin robuste Defaults liefern.

## Performance Vorher

- Commit vorher: `71e07bb2`
- Messbedingungen: Context-Dict mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_window_integration_context_inline`: best of 5 `0.22459047899974394 s`

## Durchgefuehrte Aenderungen

- `_radio_window_integration_context` eingefuehrt.
- `NetMonRadioApp._window_integration_context` delegiert an den neuen Helper.
- Direkte Tests fuer formatierte Werte und Default-Werte ergaenzt.

## Unveraendertes Sollverhalten

- Diagnostic-Context enthaelt weiterhin Window-Class, StartupWMClass, Icon-Pfad, Icon-Status und Startquelle.
- Window-Diagnostic-Logzeile bleibt im bestehenden Format.
- Icon-Laden und Fallback-Pfade bleiben unveraendert.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-window-integration-context.md`
- `docs/refactoring/performance/areas/13-radio-window-integration-context.md`

## Hinzugefuegte Tests

- `test_radio_window_integration_context_formats_values`
- `test_radio_window_integration_context_uses_defaults`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `287 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2523 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_window_integration_context_helper`: best of 5 `0.2477268450002157 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft nur fuer Diagnostic-Context-Erzeugung und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist direkte Testbarkeit der Formatierungslogik ohne Tk-App.

## Bekannte Restrisiken

- Die direkten Tests pruefen nur das Context-Dict, nicht das Log-Ziel.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Pruefung der Diagnostic-Logzeile.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-window-integration-context`.
