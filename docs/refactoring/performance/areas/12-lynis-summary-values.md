# 12 Lynis Summary Values Performance

## Messbedingungen

- Bereich: `netmon/features/security_audit_controller.py`
- Commit vorher: `3c731e10`
- Operation: direkter Aufruf von `update_lynis_summary_from_output`
- Messuhr: `time.perf_counter()`
- Synthetische Lynis-Ausgabe mit Hardening-, Warning-, Suggestion- und Testwerten
- 100 Wiederholungen pro Operation
- Keine Lynis-Kommandos gestartet
- Keine Dateien gelesen oder geschrieben
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `lynis_summary_values` | 0.0342 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `lynis_summary_values` | 0.0404 ms |

## Bewertung

- Die Summary-Auswertung bleibt deutlich unter 1 ms.
- Keine Datei-, Netzwerk-, Root- oder Subprocess-Zugriffe eingefuehrt.
- Die Differenz liegt im Messrauschen.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren echte Lynis-Prozesslaeufe und UI-Aktualisierungen, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft nur die Summary-Auswertung mit synthetischem Text.
- Reale Lynis-Laufzeit haengt fast vollstaendig vom Lynis-Prozess und Systemzustand ab.
