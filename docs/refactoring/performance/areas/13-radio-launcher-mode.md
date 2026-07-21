# 13 Radio Launcher Mode Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `4f3d4d4f`
- Operation: direkter Aufruf von Radio-Status-Text und Zielmodus-Entscheidung
- Messuhr: `time.perf_counter()`
- Synthetische Launcher-Zustaende fuer `detaching`, detached, `attaching` und attached
- 1000 Wiederholungen pro Operation
- Keine Radio-Kommandos gestartet
- Keine Widgets erzeugt
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `radio_launcher_state_decision` | 0.0016 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `radio_launcher_state_decision` | 0.0019 ms |

## Bewertung

- Die reine Entscheidung bleibt deutlich unter 1 ms.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Die Differenz liegt im Messrauschen.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waeren echte Tk-Widget-Erzeugung, Radio-Prozessstart oder Interprozess-Handover, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft nur die reine Status- und Zielmodusentscheidung.
- Reale Radio-Launcher-Laufzeit haengt staerker von Tk, Radio-Panel und externem Prozesszustand ab.
