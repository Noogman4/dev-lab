# 13 Radio Marker Geometry Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `ae6c4443`
- Operation: Berechnung von `x`, `y`, `width` und `height` fuer den vertikalen Radio-Pane-Drag-Marker
- Messwerkzeug: `.venv/bin/python -m timeit`
- Keine echten Tk-Widgets erzeugt
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_geometry` | 500 nsec per loop |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_geometry` | 529 nsec per loop |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echter Tk-Widget-Aufbau und Rendering, nicht diese reine Geometrie-Rechnung.

## Aussagekraft

- Die Messung prueft nur die reine Python-Rechnung.
- Reale Laufzeit haengt staerker von Tk-Rendering, Pane-Events und Marker-Platzierung ab.
