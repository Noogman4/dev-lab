# 13 Radio Marker Activate Return Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `c04a3780`
- Operation: Marker-Installation aktivieren und Marker-Widget zurueckgeben
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Objekte ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_activate_and_return_inline` | 35 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_activate_and_return_helper` | 67 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter ist echte Tk-Widget-, Callback- und Drag-Event-Arbeit.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad aus Aktivierung und Marker-Rueckgabe.
- Reale Laufzeit haengt staerker von Tk und den Callback-Bindings ab.
