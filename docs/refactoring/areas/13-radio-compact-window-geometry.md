# 13 Radio Compact Window Geometry

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: reine Geometrie-Rechnung aus `_configure_compact_standalone_window` herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `NetMonRadioApp._configure_compact_standalone_window`

## Abhaengigkeiten und Seiteneffekte

- Bildschirm- und Request-Groessen werden weiterhin in `_configure_compact_standalone_window` gelesen.
- Der echte `geometry(...)`-, `minsize(...)`-, `maxsize(...)`- und `resizable(...)`-Aufruf bleibt unveraendert in der Methode.
- Der neue Helper `_compact_standalone_window_geometry` berechnet nur Breite, Hoehe, Max-Hoehe und Position.
- Source-Anker fuer bestehende UI-Layout-Tests bleiben in `_configure_compact_standalone_window` erhalten.

## Risiken

- Mindestbreite muss weiterhin `980` bleiben.
- Fensterbreite muss weiterhin auf `screen_width - 120` begrenzt werden.
- Mindesthoehe muss weiterhin mindestens `int(screen_height * 0.86)` sein.
- Fensterhoehe muss weiterhin auf `screen_height - 80` begrenzt werden.
- Zentrierung muss weiterhin nicht-negativ bleiben.

## Performance Vorher

- Commit vorher: `06ffd402`
- Messbedingungen: reine Geometrie-Rechnung mit lokalen Integern, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_compact_window_geometry_inline`: best of 5 `0.6599256030003744 s`

## Durchgefuehrte Aenderungen

- `_compact_standalone_window_geometry` eingefuehrt.
- `_configure_compact_standalone_window` delegiert die reine Rechenlogik an den neuen Helper.
- Direkte Tests fuer Zentrierung und Screen-Clamping ergaenzt.

## Unveraendertes Sollverhalten

- Kompaktes Standalone-Fenster wird weiterhin zentriert.
- Mindest- und Maximalgroessen bleiben unveraendert.
- Eingebetteter Modus kehrt weiterhin frueh zurueck.
- Fehler beim Fenster-Setup werden weiterhin geschluckt.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-radio-compact-window-geometry.md`
- `docs/refactoring/performance/areas/13-radio-compact-window-geometry.md`

## Hinzugefuegte Tests

- `test_compact_standalone_window_geometry_centers_requested_window`
- `test_compact_standalone_window_geometry_clamps_to_screen`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `285 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2521 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_compact_window_geometry_helper`: best of 5 `0.7069952000001649 s`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Pfad laeuft einmal beim Standalone-Fensterstart und ist nicht laufzeitkritisch.
- Der Hauptgewinn ist direkte Testbarkeit der Fenstergeometrie ohne Tk-Fenster.

## Bekannte Restrisiken

- Die direkten Tests pruefen nur die reine Geometrie-Rechnung.
- GUI-Smoke deckt Startbarkeit ab, aber keine manuelle Sichtpruefung der Fensterposition.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-compact-window-geometry`.
