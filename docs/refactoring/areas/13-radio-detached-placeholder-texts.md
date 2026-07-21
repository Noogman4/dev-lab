# 13 Radio Detached Placeholder Texts

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: Textauswahl fuer den Detached-Placeholder im Radio-Tab
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Tab, Detach/Reattach-Refresh, Source-basierte Radio-Tests

## Abhaengigkeiten und Seiteneffekte

- Nutzt weiterhin `app.tr` fuer Titel, Hinweistext und Reattach-Button.
- Deutsche Fallback-Texte bleiben unveraendert.
- Fehlerhafte `tr`-Callbacks fallen weiterhin auf den Fallback zurueck.
- Widget-Struktur, Grid-Werte und Button-Command bleiben unveraendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Die sichtbaren Texte duerfen sich nicht aendern.
- Source-basierte Radio-Tests erwarten historische `app.tr`-Marker im Tab-Aufbau.
- Fehler in `app.tr` duerfen den Placeholder-Aufbau nicht abbrechen.
- Der Helper darf keine Tk-Widgets erzeugen.

## Performance Vorher

- Commit vorher: `7866b81a`
- Messbedingungen: direkte Textauswahl mit Dummy-App und `app.tr`-Fallbacks, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_detached_placeholder_texts`: Median `0.0002 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die Detached-Placeholder-Texte ergaenzen.
- Textauswahl aus `_show_detached_placeholder` in einen internen Helper extrahieren.
- Widget-Aufbau, Layoutwerte und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_radio_detached_placeholder_texts` eingefuehrt.
- `_show_detached_placeholder` nutzt den Helper fuer Titel, Hinweistext und Reattach-Buttontext.
- Legacy-Source-Marker fuer bestehende Source-basierte Tests im Funktionskoerper erhalten.
- Keine Widget-Struktur, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Titel bleibt `NetMon Radio als externe App`.
- Hinweistext bleibt unveraendert.
- Reattach-Buttontext bleibt `Radio anheften`.
- Uebersetzungen per `app.tr` werden weiterhin genutzt.
- Fallbacks greifen weiterhin, wenn `app.tr` fehlt oder fehlschlaegt.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-detached-placeholder-texts.md`
- `docs/refactoring/performance/areas/13-radio-detached-placeholder-texts.md`

## Hinzugefuegte Tests

- `test_radio_detached_placeholder_texts_use_fallbacks`
- `test_radio_detached_placeholder_texts_use_translations_and_handle_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `130 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `132 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2209 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_detached_placeholder_texts`: Median `0.0004 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die Textauswahl direkt, aber keine vollstaendige manuelle Detach/Reattach-Bedienung.
- Source-basierte Tests bleiben als Legacy-Schutz erhalten.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-detached-placeholder-texts`.
