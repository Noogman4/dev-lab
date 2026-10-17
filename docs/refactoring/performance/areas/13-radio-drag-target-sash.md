# 13 Radio Drag Target Sash Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `decf867e`
- Operation: Ziel-Sash-Rechnung aus `event.y_root`, `drag_state["root_y"]` und `drag_state["sash_y"]`
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Event und Dict-Zustand ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_drag_target_sash` | 123 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_drag_target_sash` | 142 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Event-Verarbeitung und Rendering.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Rechen-Pfad mit Dummy-Objekten.
- Reale Laufzeit haengt staerker von Tk-Events, Pane-Rendering und Marker-Platzierung ab.
