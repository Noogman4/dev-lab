# 13 Radio Marker Callbacks Activate Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `1fdf0baf`
- Operation: Marker-Callbacks binden und initiales Marker-Update planen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Widgets, Dummy-Callbacks, Dummy-Binder und Dummy-Scheduler ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_callbacks_activate` | 60 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_callbacks_activate` | 117 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echtes Tk-Binding und Initial-Update-Scheduling.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad fuer Binding und Initial-Update.
- Reale Laufzeit haengt staerker von Tk-Bindings, Event-System und `after`-Scheduling ab.
