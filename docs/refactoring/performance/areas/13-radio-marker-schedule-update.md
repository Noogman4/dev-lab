# 13 Radio Marker Schedule Update Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `27fbffd4`
- Operation: Scheduling eines Marker-Updates ueber `after_idle`
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 100.000 Wiederholungen
- Dummy-Container und Dict-Zustand ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_schedule_update` | 124 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_schedule_update` | 174 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Event-Verarbeitung und Rendering.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Scheduling-Pfad mit Dummy-Objekten.
- Reale Laufzeit haengt staerker von Tk-Event-Verarbeitung und Marker-Platzierung ab.
