# 13 Radio UI Status Indicator Images

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Status-Indicator-Bilder aus `_init_radio_ui_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_ui_state`

## Abhaengigkeiten und Seiteneffekte

- Es werden weiterhin drei Status-Indicator-Bilder fuer `unknown`, `online` und `offline` erzeugt.
- Der normale UI-Pfad nutzt weiterhin `_build_radio_status_indicator`.
- Der neue Helper erlaubt fuer Tests einen injizierten Indicator-Builder ohne Tk-PhotoImage.
- Die Farbwerte bleiben unveraendert.

## Risiken

- Die Keys `unknown`, `online` und `offline` muessen erhalten bleiben.
- Die Farben `#8a8f98`, `#2fb344` und `#d9485f` muessen unveraendert bleiben.
- Der Default-Builder darf wegen der Funktionsreihenfolge im Modul nicht beim Import vorzeitig aufgeloest werden.

## Performance Vorher

- Commit vorher: `48181840`
- Messbedingungen: Status-Indicator-Dict mit `SimpleNamespace`, Dummy-Indicator-Builder, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_ui_status_indicator_images_inline`: best of 5 `0.12262295700020331 s`

## Durchgefuehrte Aenderungen

- `_init_radio_ui_status_indicator_images` eingefuehrt.
- `_init_radio_ui_state` delegiert den Status-Indicator-Dict-Aufbau an den neuen Helper.
- Direkter Test fuer Keys, Farben und Builder-Aufrufe ergaenzt.

## Unveraendertes Sollverhalten

- Unknown-Indicator nutzt weiterhin `#8a8f98`.
- Online-Indicator nutzt weiterhin `#2fb344`.
- Offline-Indicator nutzt weiterhin `#d9485f`.
- Im normalen UI-Pfad werden weiterhin Tk-PhotoImages gebaut.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-ui-status-indicator-images.md`
- `docs/refactoring/performance/areas/13-radio-ui-status-indicator-images.md`

## Hinzugefuegte Tests

- `test_init_radio_ui_status_indicator_images_initializes_color_images`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `282 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2518 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_ui_status_indicator_images_helper`: best of 5 `0.16603284500160953 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim UI-Start und baut nur drei Indicator-Bilder.
- Der Hauptgewinn ist geringere Blockgroesse in `_init_radio_ui_state` und direkte Testbarkeit ohne Tk-PhotoImage.

## Bekannte Restrisiken

- Der direkte Test nutzt Dummy-Bilder statt echte Tk-PhotoImages.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Sichtpruefung der Status-Indicator-Bilder.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-ui-status-indicator-images`.
