# 13 Radio Marker Binding Plan Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `b5e0f4e7`
- Operation: Binding-Plan aus Dummy-Widgets und Dummy-Callbacks erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container, Dummy-Pane, Dummy-Grip und Dummy-Callbacks ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_binding_plan` | 280 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_binding_plan` | 308 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter sind echte Tk-`bind`-Aufrufe.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Binding-Plans.
- Reale Laufzeit haengt staerker von Tk-Event-Bindings ab.
