# 13 Radio Marker Widgets Build Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `06a7fdc7`
- Operation: Aufbau von Marker-Frame und Grip-Label mit Dummy-Factories
- Messwerkzeug: `.venv/bin/python -m timeit`
- Dummy-Widgets ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_widgets_build` | 929 nsec per loop |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_widgets_build` | 1.01 usec per loop |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt im Bereich um 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe ausserhalb des bestehenden Widget-Aufbaus eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Widget-Erzeugung und Rendering.

## Aussagekraft

- Die Messung prueft nur Dummy-Widget-Aufbau.
- Reale Laufzeit haengt staerker von Tk-Widget-Erzeugung, Event-Verarbeitung und Rendering ab.
