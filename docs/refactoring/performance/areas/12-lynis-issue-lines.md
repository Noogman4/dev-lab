# 12 Lynis Issue Lines Performance

## Messbedingungen

- Bereich: `netmon/features/security_audit_controller.py`
- Commit vorher: `69e47dbd`
- Operation: direkter Aufruf von `extract_lynis_issues_and_recommendations`
- Messuhr: `time.perf_counter()`
- Synthetische Lynis-Ausgabe mit OK-, Warning-, Suggestion-, Hardening- und Fundzeilen
- 100 Wiederholungen pro Operation
- Keine Lynis-Kommandos gestartet
- Keine Dateien gelesen oder geschrieben
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `lynis_issue_line_filter` | 0.0585 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `lynis_issue_line_filter` | 0.0646 ms |

## Bewertung

- Die Zeilenfilterung bleibt deutlich unter 1 ms.
- Keine Datei-, Netzwerk-, Root- oder Subprocess-Zugriffe eingefuehrt.
- Die Differenz liegt im Messrauschen.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren echte Lynis-Prozesslaeufe und UI-Aktualisierungen, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft nur die reine Zeilenfilterung plus bestehende Header-Erzeugung.
- Reale Lynis-Laufzeit haengt fast vollstaendig vom Lynis-Prozess und Systemzustand ab.
