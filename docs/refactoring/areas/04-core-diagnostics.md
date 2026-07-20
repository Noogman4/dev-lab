# 04 Core Diagnostics

## Ausgangszustand

- Datei: `netmon/core/diagnostics.py`
- Funktionen: `redact_sensitive_text`, `redact_diagnostic_value`, `diagnostic_reports_dir`, `diagnostic_report_path`, `_read_os_release`, `current_os_label`, `diagnostic_system_info`, `latest_diagnostic_report_path`, `build_diagnostic_report`, `write_diagnostic_report`
- Bestehende Tests: `tests/test_netmon_diagnostics.py`
- Neue Fokus-Tests: `tests/test_core_diagnostics.py`

## Abhaengigkeiten und Seiteneffekte

- Liest `/etc/os-release`.
- Schreibt Diagnoseberichte ueber `safe_write_json`.
- Erstellt den Diagnoseordner unter `NetMon/diagnostics`.
- Nutzt Prozess-/Python-/Plattformdaten fuer Berichte.
- Keine Root-Rechte.
- Keine Systembefehle.
- Keine GUI-Verbindung.
- Keine Threads oder Timer.

## Risiken

- Redaction darf nicht gelockert werden.
- Diagnosebericht-Dateinamen muessen stabil sanitisiert bleiben.
- Latest-Suche darf nur `netmon-*.json`-Dateien beruecksichtigen.
- Fehler beim Ordneranlegen werden aktuell geschluckt; dieses Verhalten bleibt unveraendert.

## Performance Vorher

- Commit vorher: `56310997`
- Messbedingungen: temporärer Diagnoseordner, `time.perf_counter()`, 20 Wiederholungen, keine realen Systemänderungen.
- `diagnostic_report_path`: Median `0.019 ms`
- `latest_diagnostic_report_path`: Median `0.061 ms`
- `build_diagnostic_report`: Median `0.115 ms`

## Geplante kleine Aenderung

- Ordner-Erstellung in einen internen Helfer extrahieren.
- Diagnosebericht-Kind-Sanitizing in einen internen Helfer extrahieren.
- Latest-Kandidaten-Ermittlung in einen internen Helfer extrahieren.
- Verhalten unveraendert lassen.

## Durchgefuehrte Aenderungen

- `_ensure_dir` eingefuehrt und in `diagnostic_reports_dir` verwendet.
- `_safe_report_kind` fuer Dateiname-Sanitizing eingefuehrt.
- `_diagnostic_report_candidates` fuer die Suche nach `netmon-*.json`-Dateien eingefuehrt.
- Oeffentliche Funktionssignaturen und Rueckgabewerte unveraendert gelassen.

## Unveraendertes Sollverhalten

- Diagnoseberichte landen weiterhin unter `NetMon/diagnostics`.
- Report-Kind wird weiterhin kleingeschrieben, mit `-` normalisiert und auf `report` zurueckgesetzt, falls leer.
- `latest_diagnostic_report_path` ignoriert weiterhin fremde Dateinamen und Verzeichnisse.
- Redaction fuer E-Mail, Home-Pfade und Secrets bleibt unveraendert.

## Betroffene Dateien

- `netmon/core/diagnostics.py`
- `tests/test_core_diagnostics.py`
- `docs/refactoring/areas/04-core-diagnostics.md`
- `docs/refactoring/performance/areas/04-core-diagnostics.md`

## Hinzugefuegte Tests

- `tests/test_core_diagnostics.py`

## Ausgefuehrte Bereichstests

- `.venv/bin/python -m pytest tests/test_core_diagnostics.py`: `3 passed` vor Refactoring
- `.venv/bin/python -m compileall -q netmon/core/diagnostics.py tests/test_core_diagnostics.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check netmon/core/diagnostics.py`: bestanden
- `timeout 60 .venv/bin/python -m black --fast --check tests/test_core_diagnostics.py`: bestanden
- `.venv/bin/python -m ruff check netmon/core/diagnostics.py tests/test_core_diagnostics.py`: bestanden
- `.venv/bin/python -m pytest tests/test_core_diagnostics.py tests/test_netmon_diagnostics.py`: `44 passed`

## Regressionstests

- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m pytest tests/test_core_diagnostics.py tests/test_netmon_diagnostics.py tests/test_support_bundle.py tests/test_performance_monitor.py`: `55 passed`
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- `.venv/bin/python -m pytest`: `2163 passed, 2 skipped`

## Performance Nachher

- `diagnostic_report_path`: Median `0.019 ms`
- `latest_diagnostic_report_path`: Median `0.062 ms`
- `build_diagnostic_report`: Median `0.118 ms`

## Bewertung

- Keine relevante Performance-Abweichung.
- Keine Optimierung vorgenommen.

## Bekannte Restrisiken

- Tests verwenden temporaere Diagnoseordner und monkeypatchen Systemdaten teilweise.
- `/etc/os-release`-Lesefehler bleiben wie zuvor tolerant.

## Rueckrollmoeglichkeit

- Rueckrollbar ueber den Bereichs-Commit fuer `04-core-diagnostics`.
