# 13 Radio Single Cell Layout

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: wiederholte Ein-Zellen-Layout-Konfiguration im Radio-Tab
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab-Aufbau, Top-/Bottom-Section, Host-Frame

## Abhaengigkeiten und Seiteneffekte

- `columnconfigure(0, weight=1)` bleibt fuer die betroffenen Frames erhalten.
- `rowconfigure(0, weight=1)` bleibt fuer die betroffenen Frames erhalten.
- Widget-Erzeugung, Grid-Werte und Pane-Gewichte bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.
- Source-basierte Radio-Tests werden nicht auf diese Layout-Zeilen gestuetzt.

## Risiken

- Frames muessen weiterhin in Zeile und Spalte 0 expandieren.
- Der Helper darf keine Widgets erzeugen.
- Marker-spezifische `columnconfigure`-Logik bleibt bewusst unberuehrt.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `1cbddd56`
- Messbedingungen: Dummy-Widget mit `columnconfigure` und `rowconfigure`, direkter Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_single_cell_configure`: Median `0.0001 ms`

## Geplante kleine Aenderung

- Direkten Test fuer die Ein-Zellen-Layout-Konfiguration ergaenzen.
- Wiederholte `columnconfigure`-/`rowconfigure`-Paare in einen internen Helper extrahieren.
- Widget-Aufbau, Pane-Struktur, Texte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_configure_single_cell_expand` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer Body, Top-Section, Host und Bottom-Section.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Body, Top-Section, Host und Bottom-Section expandieren weiterhin in Zelle 0.
- Pane-Struktur bleibt unveraendert.
- Drag-Marker-Layout bleibt unveraendert.
- Radio-Launcher-Refresh bleibt unveraendert.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-single-cell-layout.md`
- `docs/refactoring/performance/areas/13-radio-single-cell-layout.md`

## Hinzugefuegte Tests

- `test_configure_single_cell_expand_sets_column_and_row_weight`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `143 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `144 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2221 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_single_cell_configure`: Median `0.0002 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen ein Dummy-Widget statt echter Tk-Frames.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Radio-Tab-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-single-cell-layout`.
