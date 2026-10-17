# 05 Core Tooling Performance

## Messbedingungen

- Bereich: `netmon/core/tooling.py`
- Commit vorher: `7324176d`
- Messuhr: `time.perf_counter()`
- Temporaeres Speedtest-Modul mit allen Pflichtfunktionen
- 20 Wiederholungen pro Operation
- Keine realen Systemaenderungen
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `has_cmd_python` | 0.023 ms |
| `get_cmd_path_python` | 0.023 ms |
| `check_speedtest_module_available` | 0.050 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `has_cmd_python` | 0.024 ms |
| `get_cmd_path_python` | 0.023 ms |
| `check_speedtest_module_available` | 0.054 ms |

## Bewertung

- Tool-Lookups unveraendert.
- Speedtest-Modulcheck +0.004 ms, innerhalb Messrauschen.
- Keine langsamen externen Befehle gemessen.
- Keine GUI-Hauptthread-Operationen instrumentiert.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wenn Preflight sehr haeufig laeuft, koennte `shutil.which` fuer stabile Toolnamen spaeter zeitlich begrenzt gecacht werden. Dafuer gibt es aktuell keinen Bedarf.

## Aussagekraft

- Alle gemessenen Operationen liegen deutlich unter 1 ms und sind entsprechend rauschanfaellig.
- Der erste Speedtest-Modulimport ist wegen Importlib-Kosten deutlich langsamer als Folgelaeufe; Median bleibt aussagekraeftiger.
