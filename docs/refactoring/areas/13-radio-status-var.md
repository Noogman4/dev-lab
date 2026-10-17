# 13 Radio Status Var

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Initialisierung von `radio_launcher_status_var`
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab-Aufbau, Detached-Placeholder, Launcher-Refresh

## Abhaengigkeiten und Seiteneffekte

- Vorhandene Instanz-Variable wird weiterhin wiederverwendet.
- Fehlt die Variable, wird weiterhin eine leere `tk.StringVar` erzeugt.
- Das Ergebnis wird weiterhin im Tab-Aufbau auf `app.radio_launcher_status_var` gesetzt.
- Keine Widget-Struktur, Texte oder Button-Kommandos geaendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Ein bereits gesetztes Status-Var-Objekt darf nicht ersetzt werden.
- Die Default-Erzeugung darf ausserhalb echter Tk-Tests ueber eine Factory testbar bleiben.
- Das bisherige Verhalten fuer falsy Werte bleibt erhalten, weil der Helper den bisherigen `or`-Ablauf nutzt.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `2bdd62e7`
- Messbedingungen: direkte Status-Var-Initialisierung mit Dummy-App und Dummy-Var-Factory, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_launcher_status_var_init`: Median `0.0004 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer Wiederverwendung und Factory-Erzeugung der Status-Var ergaenzen.
- Inline-Initialisierung aus `build_radio_tab` in einen internen Helper extrahieren.
- App-Zustand, Texte, Layout und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_launcher_status_var` eingefuehrt.
- `build_radio_tab` nutzt den Helper fuer `app.radio_launcher_status_var`.
- Keine Widget-Struktur, Texte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Vorhandene `radio_launcher_status_var` wird wiederverwendet.
- Ohne vorhandene Var wird eine leere Var erzeugt.
- Der Launcher-Refresh schreibt weiterhin in dieselbe App-Variable.
- Detached-Placeholder nutzt weiterhin dieselbe Textvariable.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-status-var.md`
- `docs/refactoring/performance/areas/13-radio-status-var.md`

## Hinzugefuegte Tests

- `test_radio_launcher_status_var_reuses_existing_var`
- `test_radio_launcher_status_var_creates_empty_var_with_factory`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `134 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `136 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2213 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_status_var_init`: Median `0.0004 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen eine Dummy-Factory statt echter `tk.StringVar`.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Radio-Tab-Bedienung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-status-var`.
