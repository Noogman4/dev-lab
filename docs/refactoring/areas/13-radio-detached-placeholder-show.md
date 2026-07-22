# 13 Radio Detached Placeholder Show

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Anzeigeablauf fuer den Detached-Radio-Placeholder
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: `build_radio_tab`, Refresh-Entscheidung fuer Detached-Modus

## Abhaengigkeiten und Seiteneffekte

- Bereits aktiver Detached-Modus wird weiterhin uebersprungen.
- Der Radio-Host wird weiterhin vor dem Placeholder-Aufbau geleert.
- Placeholder-Texte werden weiterhin ueber `_radio_detached_placeholder_texts` ermittelt.
- Reattach-Button und App-State werden weiterhin ueber `_set_detached_radio_placeholder_state` gesetzt.
- Embedded-Panel- und Refresh-Logik bleiben unveraendert.

## Risiken

- Der Skip bei `radio_launcher_mode == "detached"` muss erhalten bleiben.
- Reattach-Command und Status-Variable muessen unveraendert in den Placeholder gehen.
- Source-basierte Radio-Tests erwarten weiterhin Legacy-Hinweise in `build_radio_tab`.
- Der Helper darf keine neue Widget-Struktur einfuehren.

## Performance Vorher

- Commit vorher: `dcc2620a`
- Messbedingungen: Dummy-App, Dummy-Host, Dummy-Clear, Dummy-Builder und Dummy-State-Setter, `timeit.repeat`, 1.000.000 Wiederholungen
- `radio_detached_placeholder_flow`: best of 5 `745 ns`

## Geplante kleine Aenderung

- Detached-Placeholder-Anzeige in `_show_radio_detached_placeholder` extrahieren.
- Direkte Tests fuer Skip und vollstaendigen Aufbau ergaenzen.
- Lokalen `_show_detached_placeholder`-Callback und Source-Hinweise erhalten.

## Durchgefuehrte Aenderungen

- `_show_radio_detached_placeholder` eingefuehrt.
- `build_radio_tab` nutzt den Helper im lokalen Detached-Callback.
- Keine sichtbaren Texte, Widget-Struktur oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Detached-Modus baut weiterhin den Reattach-Placeholder.
- Bereits detached bleibt weiterhin ohne erneuten Aufbau.
- Host-Clear laeuft weiterhin vor dem Placeholder-Aufbau.
- Radio-Launcher-State wird weiterhin auf `detached` gesetzt.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-detached-placeholder-show.md`
- `docs/refactoring/performance/areas/13-radio-detached-placeholder-show.md`

## Hinzugefuegte Tests

- `test_show_radio_detached_placeholder_skips_when_already_detached`
- `test_show_radio_detached_placeholder_clears_builds_and_sets_state`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `194 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `196 passed`
- `bash scripts/run_black_filewise.sh --check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2273 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detached_placeholder_flow`: best of 5 `818 ns`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests nutzen Dummy-Builder statt echter Tk-Widgets.
- Der GUI-Smoke prueft Startbarkeit, aber keinen manuellen Detached-/Reattach-Wechsel.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detached-placeholder-show`.
