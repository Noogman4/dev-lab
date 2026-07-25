# 13 Radio Runtime Host State

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Embedded- und Host-App-Theme-State aus `_init_radio_runtime_state` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_init_radio_runtime_state`

## Abhaengigkeiten und Seiteneffekte

- `radio_embedded_mode`, `radio_detach_callback` und `radio_host_app` bleiben unveraendert initialisiert.
- Host-App-Theme wird weiterhin klein geschrieben und getrimmt uebernommen.
- Fehler beim Theme-Zugriff oder beim Schreiben in `radio_settings` bleiben toleriert.
- Style-, Runtime- und ProjectM-Initialisierung bleiben in `_init_radio_runtime_state`.

## Risiken

- Host-App-Theme darf nur uebernommen werden, wenn ein nichtleerer Name ermittelt wurde.
- Fehlerhafte Host-App-Objekte duerfen den Start nicht abbrechen.
- Der neue Helper darf keine Tk-Widgets erzeugen.

## Performance Vorher

- Commit vorher: `c71d4055`
- Messbedingungen: Embedded-/Host-Theme-State mit `SimpleNamespace`, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_runtime_host_state_inline`: best of 5 `0.382116149000467 s`

## Durchgefuehrte Aenderungen

- `_init_radio_runtime_host_state` eingefuehrt.
- `_init_radio_runtime_state` delegiert Embedded-/Host-App-Theme-State an den neuen Helper.
- Direkte Tests fuer Theme-Uebernahme und tolerierten Host-Theme-Fehler ergaenzt.

## Unveraendertes Sollverhalten

- Embedded-Mode wird weiterhin per `bool(embedded_mode)` gesetzt.
- Detach-Callback startet weiterhin mit `None`.
- Host-App-Referenz bleibt erhalten.
- Gueltiges Host-Theme ueberschreibt weiterhin `radio_settings["theme"]`.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-runtime-host-state.md`
- `docs/refactoring/performance/areas/13-radio-runtime-host-state.md`

## Hinzugefuegte Tests

- `test_init_radio_runtime_host_state_applies_host_theme`
- `test_init_radio_runtime_host_state_ignores_theme_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `261 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2497 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_runtime_host_state_helper`: best of 5 `0.42722241499996017 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen den Helper auf einem `SimpleNamespace`, nicht auf einer echten Tk-App.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Theme-Umschaltung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-runtime-host-state`.
