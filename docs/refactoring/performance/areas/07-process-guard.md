# 07 Process Guard Performance

## Messbedingungen

- Bereich: `netmon/services/process_guard_service.py`
- Commit vorher: `f9df361a`
- Operation: direkter Aufruf von `ProcessGuardService.evaluate_process`
- Messuhr: `time.perf_counter()`
- Synthetischer Temp-Shell-Prozess mit Browser-Parent
- 100 Wiederholungen pro Operation
- Keine Prozesse beendet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `process_guard_evaluate_process` | 0.015 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `process_guard_evaluate_process` | 0.018 ms |

## Bewertung

- `evaluate_process` bleibt deutlich unter 1 ms.
- Die Differenz von 0.003 ms liegt im Messrauschen.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Bei sehr vielen Prozessen koennte spaeter die Sortierung in `run_check` separat gemessen werden.

## Aussagekraft

- Die Messung nutzt einen synthetischen Prozess und prueft die reine Bewertung eines Prozess-Dicts.
- Reale Laufzeit bei `run_check` haengt staerker von Snapshot-Erzeugung via `psutil` oder `ps` ab.
