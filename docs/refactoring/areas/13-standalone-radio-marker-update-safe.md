# 13 Standalone Radio Marker Update Safe

## Ausgangszustand

- Datei: `netmon/netmon_radio_app.py`
- Fokus dieses Schritts: Safe-Update-Fallback fuer den Standalone-Radio-Pane-Marker aus dem Installer herausziehen
- Bestehende Tests: `tests/test_netmon_radio_module.py`
- Direkter Aufrufer: `_install_pane_drag_marker`

## Abhaengigkeiten und Seiteneffekte

- Marker-Update wird weiterhin ueber die bestehende Update-Logik ausgefuehrt.
- Bei Update-Fehlern wird weiterhin versucht, den Marker per `place_forget` auszublenden.
- Fehler beim Forget-Fallback werden weiterhin ignoriert.
- Drag-Start, Drag-Motion, Drag-End und Bindings bleiben unveraendert.

## Risiken

- Der Forget-Fallback muss weiterhin nur nach einem Update-Fehler laufen.
- Fehler im Forget-Fallback duerfen weiterhin nicht nach aussen laufen.
- Die Argumente `pane`, `place_marker_for_sash` und `marker` muessen unveraendert weitergereicht werden.
- Der lokale `_update_marker`-Callback muss weiterhin mit optionalem Tk-Event aufrufbar bleiben.

## Performance Vorher

- Commit vorher: `9cff6b89`
- Messbedingungen: direkter Safe-Update-Pfad mit Dummy-Objekten und Callback-Pfad, `timeit.repeat`, 1.000.000 Wiederholungen
- `standalone_radio_marker_update_safe_inline`: best of 5 `66 ns`

## Geplante kleine Aenderung

- Safe-Update-Fallback in `_standalone_radio_pane_update_marker_safe` extrahieren.
- Direkte Tests fuer Erfolgsweg, Update-Fehler-Fallback und Forget-Fehler ergaenzen.
- Lokalen `_update_marker` im Installer auf den neuen Helper umstellen.

## Durchgefuehrte Aenderungen

- `_standalone_radio_pane_update_marker_safe` eingefuehrt.
- Lokaler `_update_marker` delegiert an den neuen Helper.
- Tests fuer Update-Erfolg, Forget-Fallback und ignorierten Forget-Fehler ergaenzt.
- Keine sichtbaren Texte, Widget-Struktur oder Drag-Logik geaendert.

## Unveraendertes Sollverhalten

- Marker-Update liest weiterhin die aktuelle Sash-Position ueber die bestehende Update-Logik.
- Bei Update-Fehlern wird weiterhin `place_forget` versucht.
- Fehler im Forget-Fallback werden weiterhin ignoriert.
- Der lokale Callback bleibt weiterhin event-kompatibel.

## Betroffene Dateien

- `netmon/netmon_radio_app.py`
- `tests/test_netmon_radio_module.py`
- `docs/refactoring/areas/13-standalone-radio-marker-update-safe.md`
- `docs/refactoring/performance/areas/13-standalone-radio-marker-update-safe.md`

## Hinzugefuegte Tests

- `test_standalone_radio_pane_update_marker_safe_updates_marker`
- `test_standalone_radio_pane_update_marker_safe_forgets_on_update_failure`
- `test_standalone_radio_pane_update_marker_safe_ignores_forget_failure`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `144 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_netmon_radio_module.py`: `147 passed`
- `bash scripts/run_black_filewise.sh --check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m ruff check netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/netmon_radio_app.py tests/test_netmon_radio_module.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2383 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `standalone_radio_marker_update_safe_helper`: best of 5 `99 ns`

## Bewertung

- Der Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen Dummy-Callbacks, nicht echtes Standalone-Marker-Update in Tk.
- Der GUI-Smoke prueft Startbarkeit, aber keine manuelle Standalone-Marker-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-standalone-radio-marker-update-safe`.
