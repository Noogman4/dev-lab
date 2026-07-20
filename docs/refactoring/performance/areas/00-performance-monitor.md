# 00 Performance Monitor

## Ziel

Zentrale Laufzeitmessung fuer das weitere schrittweise Refactoring, ohne fachliches Verhalten zu veraendern.

## Zentrale Komponente

- Datei: `netmon/core/performance_monitor.py`
- Messuhr: `time.perf_counter()`
- Verwendung: `with measure(area="...", operation="...") as measurement:`
- Optional: `@measure_runtime(area="...", operation="...")`
- Fehlerverhalten: Loggingfehler werden geschluckt; die gemessene Funktion laeuft weiter.
- Ausnahmen aus gemessenen Funktionen werden nicht geschluckt.

## Aktivierung

- `NETMON_PERFORMANCE_MONITORING=off`: keine Protokollierung
- `NETMON_PERFORMANCE_MONITORING=basic`: groessere Aktionen
- `NETMON_PERFORMANCE_MONITORING=detailed`: zusaetzliche interne Teilschritte und Systembefehle
- Kurzformen `1`, `true`, `yes`, `on` aktivieren `basic`.
- Standard: `off`, damit Release- und Normalbetrieb nicht veraendert werden.

## Logpfad und Rotation

- Standard-Laufzeitlog: `~/.local/state/netmon/logs/performance_measurements.jsonl`
- Override: `NETMON_PERFORMANCE_LOG_PATH`
- Maximalgroesse: `NETMON_PERFORMANCE_MAX_BYTES`, Standard `5000000`
- Backups: `NETMON_PERFORMANCE_BACKUPS`, Standard `3`
- Rotation: `performance_measurements.jsonl` -> `.1`, `.1` -> `.2`, usw.

## Datenschutz

- Vollstaendige Befehlszeilen werden nicht geloggt.
- `run_cmd` protokolliert nur `command_name`, z. B. `ufw`, `wg`, `true`.
- Metadaten-Schluessel mit sensiblen Namen wie `password`, `token`, `secret`, `api_key`, `private_key` werden als `[REDACTED]` gespeichert.
- Freitextwerte werden auf 200 Zeichen gekuerzt.

## Instrumentierte Bereiche

- `startup/headless_gui_smoke_startup` in `netmon/main.py`
- `system_command/run_cmd` in `netmon/core/command.py`
- `system_command/run_cmd_with_input` in `netmon/core/command.py`
- `diagnostics/support_bundle_inputs` in `netmon/core/support_bundle.py`
- `diagnostics/create_support_package` in `netmon/core/support_bundle.py`

## Beispielmesswerte

Runtime-Log nach aktiviertem GUI-Smoke:

```json
{"area": "startup", "duration_ms": 4514.223, "gui_thread": true, "metadata": {"theme": ""}, "netmon_version": "1.1.20", "operation": "headless_gui_smoke_startup", "return_code": 0, "severity": "CRITICAL", "status": "success", "timestamp": "2026-07-20T22:48:16.044+02:00"}
```

Temporäre Beispielmessung mit `NETMON_PERFORMANCE_LOG_PATH=/tmp/netmon-performance-example.jsonl`:

```json
{"area": "system_command", "command_name": "true", "duration_ms": 0.572, "gui_thread": true, "netmon_version": "1.1.20", "operation": "run_cmd", "return_code": 0, "severity": "FAST", "status": "success", "timestamp": "2026-07-20T22:48:27.386+02:00"}
{"area": "diagnostics", "duration_ms": 0.733, "gui_thread": true, "metadata": {"file_count": 6}, "netmon_version": "1.1.20", "operation": "support_bundle_inputs", "severity": "FAST", "status": "success", "timestamp": "2026-07-20T22:48:27.387+02:00"}
```

## Eigenaufwand der Instrumentierung

- Deaktiviert: nur Context-Manager-Aufbau und `perf_counter()`-Messung, kein Dateischreibzugriff.
- Aktiviert: eine JSONL-Zeile pro Messpunkt plus optionale Rotation.
- Die Messkomponente ist bewusst klein gehalten und fuehrt keine Systembefehle fuer Git- oder Umgebungsdaten aus.

## Tests

- `tests/test_performance_monitor.py`
- Deaktiviertes Logging
- Aktiviertes JSONL-Schreiben
- Fehlerdurchleitung bei Exceptions
- Logrotation
- Sichere Kommandonamen
- Decorator-Verwendung
- Integration mit `run_cmd`
- Integration mit `create_support_package`

## Ausgefuehrte Tests

- `.venv/bin/python -m pytest tests/test_performance_monitor.py tests/test_netmon_command_core.py tests/test_support_bundle.py tests/test_netmon_diagnostics.py`: `54 passed`
- `.venv/bin/python -m ruff check netmon/core/performance_monitor.py netmon/core/command.py netmon/core/support_bundle.py netmon/main.py tests/test_performance_monitor.py`: bestanden
- `.venv/bin/python -m compileall -q netmon/core/performance_monitor.py netmon/core/command.py netmon/core/support_bundle.py netmon/main.py tests/test_performance_monitor.py`: bestanden
- Dateiweiser Black-Check fuer die betroffenen Python-Dateien: bestanden
- `.venv/bin/python -m ruff check netmon tests tools scripts agent`: bestanden
- `.venv/bin/python -m compileall -q netmon tests tools scripts agent`: bestanden
- `make roots-guard-smoke`: `7 passed, 1 skipped`
- `make roots-guard-checks`: UI `7 passed, 1 skipped`; Controller `90 passed`
- `.venv/bin/python -m pytest`: `2160 passed, 2 skipped`
- `bash scripts/run_netmon_gui_smoke.sh` ausserhalb der Sandbox: `NetMon GUI smoke test ok`
- `NETMON_PERFORMANCE_MONITORING=basic bash scripts/run_netmon_gui_smoke.sh` ausserhalb der Sandbox: `NetMon GUI smoke test ok`

## Aktueller Runtime-Logpfad

- `/home/happy/.local/state/netmon/logs/performance_measurements.jsonl`
- Letzter gepruefter Startup-Messwert: `duration_ms` 4515.921, `status` success, `return_code` 0.

## Noch nicht instrumentiert

- Tab-Wechsel und Tab-Aufbau ausserhalb des Headless-Smokes
- Firewall-, VPN-, DNS- und Security-Guard-Benutzeraktionen
- Parser fuer Lynis, rkhunter, ClamAV und grosse Logdateien
- File-Hash-Berechnungen
- Nmap-, MTR-, Traceroute- und Geo-IP-Aktionen

## Bewertung

- Keine Performance-Optimierung vorgenommen.
- Diese Komponente schafft nur Messbarkeit fuer die naechsten Refactoring-Bereiche.
