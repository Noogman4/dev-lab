# 13 Radio Launcher Mode

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Zielmodus-Entscheidung im Radio-Launcher-Refresh
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab, externes Radio-Fenster, Reattach-Workflow

## Abhaengigkeiten und Seiteneffekte

- Dieser Schritt nutzt nur den bereits gelesenen Radio-Launcher-Zustand.
- Keine Widget-Hierarchie geaendert.
- Keine sichtbaren Texte geaendert.
- Keine Radio-Start-, Detach- oder Reattach-Kommandos geaendert.
- Keine gespeicherten Radio-Konfigurationen geaendert.

## Risiken

- `detaching` muss weiterhin den Detached-Platzhalter anzeigen.
- Bereits geloeste Radio-App muss weiterhin den Detached-Platzhalter anzeigen.
- `attaching` und normaler Attached-Zustand muessen weiterhin das Embedded-Panel anzeigen.
- Source-basierte Radio-Tests duerfen nicht durch Layout-Umbau gebrochen werden.

## Performance Vorher

- Commit vorher: `4f3d4d4f`
- Messbedingungen: direkter Aufruf von Radio-Status-Text und bisheriger Zielmodus-Entscheidung mit synthetischen Launcher-Zustaenden, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_launcher_state_decision`: Median `0.0016 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die Radio-Launcher-Zielmodus-Entscheidung ergaenzen.
- Inline-Entscheidung aus `refresh_radio_launcher_state` in einen internen Helper extrahieren.
- Layout, Texte, Detach/Reattach und Panel-Erzeugung unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_launcher_target_mode` eingefuehrt.
- `refresh_radio_launcher_state` nutzt den Helper fuer die Wahl zwischen Detached-Platzhalter und Embedded-Panel.
- Keine Widget-Struktur, Texte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- `detached=True` fuehrt weiterhin zum Detached-Platzhalter.
- `launcher_state == "detaching"` fuehrt weiterhin zum Detached-Platzhalter.
- Attached- und Attaching-Zustaende fuehren weiterhin zum Embedded-Panel.
- Status-Text wird weiterhin vor der Panel-Auswahl gesetzt.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-launcher-mode.md`
- `docs/refactoring/performance/areas/13-radio-launcher-mode.md`

## Hinzugefuegte Tests

- `test_radio_launcher_target_mode_selects_detached_for_detached_state`
- `test_radio_launcher_target_mode_selects_embedded_for_attached_states`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `124 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `126 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2203 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_launcher_state_decision`: Median `0.0019 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Differenz von `0.0003 ms` liegt fuer diesen kleinen UI-Helfer im Messrauschen.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen synthetische Launcher-Zustaende.
- Der GUI-Smoke prueft Startbarkeit, aber keine vollstaendige manuelle Radio-Detach-Interaktion.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-launcher-mode`.
