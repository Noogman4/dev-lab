# 13 Radio Detached Placeholder Texts Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `7866b81a`
- Operation: Auswahl von Titel, Hinweistext und Reattach-Buttontext fuer den Detached-Placeholder
- Messuhr: `time.perf_counter()`
- 1000 Wiederholungen
- Dummy-App mit `tr`-Fallbacks
- Keine Tk-Widgets erzeugt
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `radio_detached_placeholder_texts` | 0.0002 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `radio_detached_placeholder_texts` | 0.0004 ms |

## Bewertung

- Die Textauswahl bleibt deutlich unter 1 ms.
- Die Differenz liegt fuer diesen kleinen Helper im Messrauschen.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Widget-Erzeugung oder der externe Radio-Prozesszustand, die in diesem Schritt bewusst nicht beruehrt wurden.

## Aussagekraft

- Die Messung prueft nur die reine Textauswahl.
- Reale Radio-Launcher-Laufzeit haengt staerker von Tk, Radio-Panel und externem Prozesszustand ab.
