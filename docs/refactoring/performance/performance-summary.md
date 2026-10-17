# Performance Summary

## Aktuelle Baseline

- Baseline-Commit: `204e6daa`
- Messdatei: `docs/refactoring/performance/performance-measurements.jsonl`
- Laufzeitlog im Betrieb: `~/.local/state/netmon/logs/performance_measurements.jsonl`
- Zentrale Messkomponente: `netmon/core/performance_monitor.py`
- Aktivierung: `NETMON_PERFORMANCE_MONITORING=off|basic|detailed`
- Standard: `off`

## Langsamste gemessene Operationen

1. `startup/headless_gui_smoke_startup`: Median 4925.237 ms
2. `tests/pytest_core_perf_seed`: Median 188.424 ms
3. `tests/ruff_check`: Median 21.081 ms

## Schnelle gemessene Core-Operationen

- `core/state_path_helpers`: Median 0.069 ms
- `diagnostics/support_bundle_inputs`: Median 0.643 ms
- `diagnostics/support_manifest_build`: Median 0.112 ms

## Instrumentiert

- `startup/headless_gui_smoke_startup`
- `system_command/run_cmd`
- `system_command/run_cmd_with_input`
- `diagnostics/support_bundle_inputs`
- `diagnostics/create_support_package`

## Noch nicht instrumentiert

- Tab-Aufbau und Tab-Wechsel.
- Firewall-, VPN-, DNS- und Security-Guard-Aktionen.
- Parser fuer Lynis, rkhunter, ClamAV und grosse Logs.

## Logrotation

- Standard-Maximalgroesse: `5000000` Bytes
- Standard-Backups: `3`
- Overrides: `NETMON_PERFORMANCE_MAX_BYTES`, `NETMON_PERFORMANCE_BACKUPS`

## Naechster Schritt

- Vor dem naechsten Refactoring-Bereich relevante Vorher-Messung mit `basic` oder `detailed` erfassen.
- Nach dem Bereich dieselbe Messung wiederholen.
- Ergebnis in `docs/refactoring/performance/areas/` dokumentieren.
