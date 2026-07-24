# 13 Radio Marker Install Dependencies

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Abhaengigkeiten von `_install_pane_drag_marker` explizit injizierbar machen
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_build_radio_tab_pane`

## Abhaengigkeiten und Seiteneffekte

- `_install_pane_drag_marker` baut weiterhin zuerst die Marker-Installation.
- Danach wird weiterhin aktiviert und das Marker-Widget zurueckgegeben.
- Standard-Builder und Standard-Aktivator werden zur Laufzeit aufgeloest.
- Die Legacy-Source-Referenz in `_install_pane_drag_marker` bleibt erhalten.

## Risiken

- Der normale Aufruf ohne injizierte Abhaengigkeiten muss unveraendert bleiben.
- Monkeypatching der bisherigen Standardfunktionen muss weiter funktionieren.
- Die Farbe muss weiterhin als `color` an den Installation-Builder gehen.
- Die Aktivierung muss weiterhin vor der Marker-Rueckgabe laufen.

## Performance Vorher

- Commit vorher: `0a8bd34a`
- Messbedingungen: `_install_pane_drag_marker` mit Dummy-Installation und gepatchten Modul-Globals, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_marker_install_default_globals`: best of 5 `100 ns`

## Geplante kleine Aenderung

- Optionale `installation_builder`- und `marker_activator`-Parameter an `_install_pane_drag_marker` ergaenzen.
- Defaults zur Laufzeit aufloesen, damit bestehende Monkeypatch-Tests stabil bleiben.
- Direkten Test fuer injizierte Abhaengigkeiten ergaenzen.

## Durchgefuehrte Aenderungen

- `_install_pane_drag_marker` akzeptiert jetzt `installation_builder` und `marker_activator`.
- Der normale Aufrufpfad nutzt weiterhin `_build_radio_pane_marker_installation` und `_activate_radio_pane_marker_and_return_marker`.
- Direkter Injection-Test ohne Monkeypatch ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- `_install_pane_drag_marker` gibt weiterhin das Marker-Widget zurueck.
- Die Installation wird weiterhin vor der Rueckgabe aktiviert.
- Direkte initiale Scheduling-Aufrufe bleiben weiterhin vermieden.
- Source-basierte Tests finden weiterhin die Legacy-Referenz fuer die Marker-Breite.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-marker-install-dependencies.md`
- `docs/refactoring/performance/areas/13-radio-marker-install-dependencies.md`

## Hinzugefuegte Tests

- `test_install_pane_drag_marker_uses_injected_builder_and_activator`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `279 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `280 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2357 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_marker_install_injected`: best of 5 `113 ns`

## Bewertung

- Die injizierte Variante bleibt deutlich unter 1 us.
- Der kleine Overhead ist fuer diesen Tk-nahen Pfad irrelevant.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Objekte statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Drag-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-marker-install-dependencies`.
