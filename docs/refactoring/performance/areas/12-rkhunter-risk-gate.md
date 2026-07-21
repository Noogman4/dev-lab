# 12 rkhunter Risk Gate Performance

## Messbedingungen

- Bereich: `netmon/services/rkhunter_analysis_service.py`
- Commit vorher: `72645586`
- Operation: direkter Aufruf von `analyze_rkhunter_output`
- Messuhr: `time.perf_counter()`
- Synthetische rkhunter- und dpkg-Ausgaben mit Expected-, Hidden- und Summary-Signalen
- 100 Wiederholungen pro Operation
- Keine rkhunter-Kommandos gestartet
- Keine Dateien gelesen oder geschrieben
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `rkhunter_analysis_risk_gate` | 0.0865 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `rkhunter_analysis_risk_gate` | 0.0885 ms |

## Bewertung

- Die deterministische Analyse bleibt deutlich unter 1 ms.
- Keine Datei-, Netzwerk-, Root- oder Subprocess-Zugriffe eingefuehrt.
- Die Differenz liegt im Messrauschen.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren echte rkhunter-, dpkg- und file-Aufrufe, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft die deterministische Analyse mit synthetischem Text.
- Reale rkhunter-Laufzeit haengt fast vollstaendig von Prozesslaufzeit, Logzugriff und Systemzustand ab.
