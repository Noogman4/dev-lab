# 13 Radio Status Var Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `2bdd62e7`
- Operation: Initialisierung von `radio_launcher_status_var` mit Dummy-App und Dummy-Var-Factory
- Messuhr: `time.perf_counter()`
- 1000 Wiederholungen
- Keine echten Tk-Widgets erzeugt
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `radio_launcher_status_var_init` | 0.0004 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `radio_launcher_status_var_init` | 0.0004 ms |

## Bewertung

- Der extrahierte Helper fuegt keine messbare Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echter Tk-Tab-Aufbau, nicht diese reine Initialisierungsentscheidung.

## Aussagekraft

- Die Messung prueft nur die reine Status-Var-Auswahl und Dummy-Erzeugung.
- Reale Laufzeit haengt staerker von Tk-Initialisierung und Widget-Aufbau ab.
