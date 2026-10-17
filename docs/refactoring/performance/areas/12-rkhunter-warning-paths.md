# 12 rkhunter Warning Paths Performance

## Messbedingungen

- Bereich: `netmon/services/rkhunter_analysis_service.py`
- Commit vorher: `fc3742ee`
- Operation: direkter Aufruf von `extract_replaced_script_paths` und `extract_warning_command_paths`
- Messuhr: `time.perf_counter()`
- Synthetische rkhunter-Ausgabe mit Script-, Warning-, System- und Nicht-System-Pfaden
- 100 Wiederholungen pro Operation
- Keine rkhunter-Kommandos gestartet
- Keine Dateien gelesen oder geschrieben
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `rkhunter_warning_path_extractors` | 0.0650 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `rkhunter_warning_path_extractors` | 0.0778 ms |

## Bewertung

- Die Pfadextraktion bleibt deutlich unter 1 ms.
- Keine Datei-, Netzwerk-, Root- oder Subprocess-Zugriffe eingefuehrt.
- Die Differenz liegt im Messrauschen.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren echte rkhunter-, dpkg- und file-Aufrufe, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft nur die reine Pfadextraktion.
- Reale rkhunter-Laufzeit haengt fast vollstaendig von Prozesslaufzeit, Logzugriff und Systemzustand ab.
