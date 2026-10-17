# 04 Core Diagnostics Performance

## Messbedingungen

- Bereich: `netmon/core/diagnostics.py`
- Commit vorher: `56310997`
- Messuhr: `time.perf_counter()`
- Temporärer Diagnoseordner mit 5 `netmon-*.json`-Dateien
- 20 Wiederholungen pro Operation
- Keine realen Systemaenderungen
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `diagnostic_report_path` | 0.019 ms |
| `latest_diagnostic_report_path` | 0.061 ms |
| `build_diagnostic_report` | 0.115 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `diagnostic_report_path` | 0.019 ms |
| `latest_diagnostic_report_path` | 0.062 ms |
| `build_diagnostic_report` | 0.118 ms |

## Bewertung

- `diagnostic_report_path`: unveraendert.
- `latest_diagnostic_report_path`: +0.001 ms, innerhalb Messrauschen.
- `build_diagnostic_report`: +0.003 ms, innerhalb Messrauschen.
- Keine langsamen externen Befehle.
- Keine GUI-Hauptthread-Operationen instrumentiert.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Bei sehr vielen Diagnoseberichten koennte die Latest-Suche spaeter begrenzt oder gecacht werden; dafuer gibt es aktuell keinen Beleg.

## Aussagekraft

- Sehr kurze Operationen unter 1 ms sind stark rauschanfaellig.
- Median ist aussagekraeftiger als Mittelwert, weil `build_diagnostic_report` beim ersten Aufruf Plattformdaten initialisiert.
