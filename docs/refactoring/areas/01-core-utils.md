# 01 Core Utilities

## Ausgangszustand

- Datei: `netmon/core/utils.py`
- Funktionen: `safe_write_json`, `format_table`, `ts`, `human_rate`, `human_size`, `call_in_ui_thread`
- Direkte Tests vor Beginn: keine dedizierte `core/utils`-Testdatei
- Indirekte Aufrufer: App, Feature-Controller, Services und UI-Tabs

## Abhaengigkeiten und Seiteneffekte

- `safe_write_json` schreibt JSON atomar per temporaerer Datei und `os.replace`.
- `format_table`, `human_rate`, `human_size` und `ts` sind reine Formatierungshelfer.
- `call_in_ui_thread` importiert `threading` lokal und ruft entweder direkt `fn()` auf oder plant `app.after(0, fn)`.
- Keine Root-Rechte.
- Keine Systembefehle.
- Dateisystemzugriff nur in `safe_write_json`.
- GUI-Verbindung nur in `call_in_ui_thread` ueber `app.after`.
- Keine eigenen Threads oder Timer; nur Main-Thread-Erkennung.

## Risiken

- Viele Aufrufer erwarten die exakten Rueckgabestrings von `human_size`, `human_rate` und `format_table`.
- Bestehender Befund: Bei JSON-Serialisierungsfehlern kann `safe_write_json`
  aktuell eine `.netmon-tmp-*.json`-Datei im Zielordner hinterlassen, weil der
  Temp-Pfad erst nach `json.dump` gesetzt wird. Das wird in diesem Bereich
  dokumentiert, aber nicht als Refactoring-Nebenwirkung veraendert.
- `call_in_ui_thread` darf bestehendes Thread-Verhalten nicht aendern.

## Absicherung vor Refactoring

- Neue Tests in `tests/test_core_utils.py` dokumentieren:
  - Tabellenformatierung inklusive leerem Body.
  - Groessen- und Ratenformatierung.
  - atomisches JSON-Schreiben mit Unterordneranlage.
  - Fehlerfall mit nicht serialisierbarem Payload ohne geschriebene Zieldatei.
  - direktes Ausfuehren im Main-Thread.

## Geplante kleine Aenderung

- Gemeinsame Skalierungslogik fuer `human_rate` und `human_size` extrahieren.
- Typannotationen fuer Utility-Funktionen ergaenzen.
- Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_RATE_UNITS` und `_SIZE_UNITS` als Modulkonstanten eingefuehrt.
- `_format_scaled_value` fuer die gemeinsame 1024er-Skalierung extrahiert.
- `human_rate` und `human_size` nutzen die gemeinsame Skalierungsfunktion.
- Rueckgabeverhalten durch Tests fuer B/s, KiB/s, MiB/s, B, KiB, MiB, negative Werte und ungueltige Groessenwerte abgesichert.
- `safe_write_json` nicht veraendert; der bestehende Serialisierungsfehler-Befund bleibt dokumentiert.

## Unveraendertes Sollverhalten

- `human_size(None)` und ungueltige Groessenwerte liefern weiterhin `–`.
- Negative Groessen- und Ratenwerte werden weiterhin als `0 B` bzw. `0 B/s` angezeigt.
- Werte ab 1024 werden weiterhin mit einer Nachkommastelle formatiert.
- `format_table` behaelt Trennzeichen, Padding und `(keine Regeln)` bei leerem Body bei.
- `call_in_ui_thread` ruft im Main-Thread weiterhin direkt auf.

## Betroffene Dateien

- `netmon/core/utils.py`
- `tests/test_core_utils.py`
- `docs/refactoring/areas/01-core-utils.md`

## Hinzugefuegte Tests

- `tests/test_core_utils.py`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_core_utils.py`: `7 passed`
- `.venv/bin/python -m compileall -q netmon/core/utils.py tests/test_core_utils.py`: bestanden
- `.venv/bin/python -m ruff check netmon/core/utils.py tests/test_core_utils.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/core/utils.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_core_utils.py`: bestanden

## Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- `.venv/bin/python -m pytest`: `2143 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh` ausserhalb der Sandbox: `NetMon GUI smoke test ok`

## Bekannte Restrisiken

- Die neue gemeinsame Skalierungsfunktion wird nur ueber die oeffentlichen Helfer getestet, nicht direkt.
- Der dokumentierte Temp-Datei-Rest bei `safe_write_json`-Serialisierungsfehlern ist bewusst nicht Teil dieser Refactoring-Aenderung.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `01-core-utils`.
