# Performance Summary

## Aktuelle Baseline

- Baseline-Commit: `204e6daa`
- Messdatei: `docs/refactoring/performance/performance-measurements.jsonl`
- Laufzeitlog im Betrieb: noch nicht implementiert
- Zentrale Messkomponente: noch nicht implementiert

## Langsamste gemessene Operationen

1. `startup/headless_gui_smoke_startup`: Median 4925.237 ms
2. `tests/pytest_core_perf_seed`: Median 188.424 ms
3. `tests/ruff_check`: Median 21.081 ms

## Schnelle gemessene Core-Operationen

- `core/state_path_helpers`: Median 0.069 ms
- `diagnostics/support_bundle_inputs`: Median 0.643 ms
- `diagnostics/support_manifest_build`: Median 0.112 ms

## Noch nicht instrumentiert

- Laufzeitmessung im NetMon-Code.
- Externe Systembefehle in `netmon/core/command.py`.
- Tab-Aufbau und Tab-Wechsel.
- Firewall-, VPN-, DNS- und Security-Guard-Aktionen.
- Parser fuer Lynis, rkhunter, ClamAV und grosse Logs.

## Naechster Schritt

- Kleine zentrale Messkomponente unter `netmon/core/performance_monitor.py`.
- Tests fuer Aktivierung, JSONL-Schreiben, Fehlerdurchleitung und Rotation.
- Danach erste sehr gezielte Instrumentierung ohne Performance-Optimierung.
