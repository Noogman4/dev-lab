# 13 Radio Drag State Init Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `7e02bcb7`
- Operation: Aufbau des Drag-State-Dicts mit `root_y`, `sash_y` und `update_pending`
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Keine echten Tk-Widgets erzeugt
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_drag_state_init` | 55 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_drag_state_init` | 67 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Event-Verarbeitung und Rendering.

## Aussagekraft

- Die Messung prueft nur den Dict-Aufbau.
- Reale Laufzeit haengt staerker von Tk-Events, Pane-Rendering und Marker-Platzierung ab.
