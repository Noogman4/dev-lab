# 13 Radio Safe Translate

## Ausgangszustand

- Datei: `netmon/ui/tabs/radio_tab.py`
- Fokus dieses Schritts: wiederverwendbare fehlerrobuste Uebersetzung fuer Radio-Tab-Texthelper
- Bestehende Tests: `tests/test_radio_tab.py`, `tests/test_netmon_radio_module.py`
- Indirekte Aufrufer: Radio-Status-Text, Detached-Placeholder-Text, Source-basierte Radio-Tests

## Abhaengigkeiten und Seiteneffekte

- Nutzt weiterhin `app.tr`, wenn vorhanden und aufrufbar.
- Fallback-Texte bleiben unveraendert.
- Fehlerhafte `tr`-Callbacks fallen weiterhin auf den Fallback zurueck.
- Keine Widget-Struktur, Grid-Werte oder Button-Kommandos geaendert.
- Keine Aenderung an Radio-Start, Detach/Reattach oder Embedded-Panel.

## Risiken

- Bereits getestete Status- und Placeholder-Texte duerfen sich nicht aendern.
- `app=None` und Apps ohne `tr` muessen weiter funktionieren.
- Fehler in `app.tr` duerfen den Radio-Tab-Aufbau nicht abbrechen.
- Source-basierte Radio-Tests duerfen nicht durch den Helper-Schnitt brechen.

## Performance Vorher

- Commit vorher: `3e90102a`
- Messbedingungen: zwei direkte Uebersetzungsaufrufe mit Dummy-App und lokalem bisherigen `_t`-Ablauf, `time.perf_counter()`, 1000 Wiederholungen.
- `radio_safe_translate_pair`: Median `0.0004 ms`

## Geplante kleine Aenderung

- Direkte Tests fuer die gemeinsame fehlerrobuste Uebersetzung ergaenzen.
- Doppelte lokale `_t`-Implementierungen in den Radio-Texthelpern durch `_safe_translate` ersetzen.
- Texte, Layout und Radio-Kommandos unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_safe_translate` eingefuehrt.
- `_radio_launcher_status_text` nutzt den Helper.
- `_radio_detached_placeholder_texts` nutzt den Helper.
- Bestehende Legacy-Source-Marker bleiben erhalten.
- Keine Widget-Struktur, Layoutwerte oder Radio-Kommandos geaendert.

## Unveraendertes Sollverhalten

- Radio-Status-Texte bleiben unveraendert.
- Detached-Placeholder-Texte bleiben unveraendert.
- Uebersetzungen per `app.tr` werden weiterhin genutzt.
- Fallbacks greifen weiterhin, wenn `app.tr` fehlt oder fehlschlaegt.

## Betroffene Dateien

- `netmon/ui/tabs/radio_tab.py`
- `tests/test_radio_tab.py`
- `docs/refactoring/areas/13-radio-safe-translate.md`
- `docs/refactoring/performance/areas/13-radio-safe-translate.md`

## Hinzugefuegte Tests

- `test_safe_translate_uses_fallback_without_translator`
- `test_safe_translate_uses_translation_and_handles_failures`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `132 passed` vor Refactoring
- `.venv/bin/python -m pytest tests/test_radio_tab.py tests/test_netmon_radio_module.py`: `134 passed`
- `.venv/bin/python -m ruff check netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/ui/tabs/radio_tab.py tests/test_radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check netmon/ui/tabs/radio_tab.py`: bestanden
- `timeout 60 .venv/bin/python -m black --check tests/test_radio_tab.py`: bestanden

## Ausgefuehrte Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest`: `2211 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh`: in der Sandbox wegen Tk/Xvfb-Displayzugriff fehlgeschlagen, ausserhalb der Sandbox bestanden

## Performance Nachher

- `radio_safe_translate_pair`: Median `0.0003 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests pruefen die Uebersetzungslogik direkt, aber keine vollstaendige manuelle Radio-Tab-Bedienung.
- Source-basierte Tests bleiben als Legacy-Schutz erhalten.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `13-radio-safe-translate`.
