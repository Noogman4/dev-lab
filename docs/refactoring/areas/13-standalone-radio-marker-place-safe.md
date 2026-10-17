# 13 Standalone Radio Marker Place Safe

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Safe-Place-Fallback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker-Platzierung wird weiterhin ueber die bestehende Place-for-Sash-Logik ausgefuehrt.
- Bei Place-Fehlern wird weiterhin versucht, den Marker per `place_forget` auszublenden.
- Fehler beim Forget-Fallback werden weiterhin ignoriert.
- Der Legacy-Quelltext-Kommentar fuer source-basierte Tests bleibt im Installer erhalten.

## Risiken

- Der Forget-Fallback muss weiterhin nur nach einem Place-Fehler laufen.
- Fehler im Forget-Fallback duerfen weiterhin nicht nach aussen laufen.
- Die Argumente `container`, `marker`, `sash_y` und `y_offset` muessen unveraendert weitergereicht werden.
- Source-basierte Tests duerfen den Legacy-Marker-Width-Hinweis weiterhin finden.

## Performance Vorher

- Commit vorher: `9905dff0`
- Messbedingungen: direkter Safe-Place-Pfad mit Dummy-Objekten und Callback-Pfad, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_place_safe_inline`: best of 5 `70 ns`

## Geplante kleine Aenderung

- Safe-Place-Fallback in `_standalone_radio_pane_place_marker_for_sash_safe` extrahieren.
- Direkte Tests fuer Erfolgsweg, Place-Fehler-Fallback und Forget-Fehler ergaenzen.
- Lokalen `_place_marker_for_sash` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_place_marker_for_sash_safe` eingefuehrt.
- Lokaler `_place_marker_for_sash` delegiert an den neuen Helper.
- Tests fuer Place-Erfolg, Forget-Fallback und ignorierten Forget-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker wird weiterhin fuer die aktuelle Sash-Position platziert.
- Bei Place-Fehlern wird weiterhin `place_forget` versucht.
- Fehler im Forget-Fallback werden weiterhin ignoriert.
- Der lokale Callback bleibt weiterhin nur ueber `sash_y` aufrufbar.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-place-safe.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-place-safe.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_place_marker_for_sash_safe_places_marker`
- `test_standalone_radio_pane_place_marker_for_sash_safe_forgets_on_place_failure`
- `test_standalone_radio_pane_place_marker_for_sash_safe_ignores_forget_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `141 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `144 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2380 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_place_safe_helper`: best of 5 `102 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Callbacks, nicht echte Standalone-Marker-Platzierung in Tk.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-place-safe`.
