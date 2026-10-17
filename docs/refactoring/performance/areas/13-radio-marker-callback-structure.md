# 13 Radio Marker Callback Structure Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `8f460020`
- Operation: Marker-Callbacks aus Dummy-Factories erzeugen und zurueckgeben
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container, Dummy-Pane, Dummy-Marker, Dummy-Drag-State und Dummy-Callback-Factories ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_callbacks` | 238 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_callbacks` | 394 ns |

## Bewertung

- `NamedTuple` erzeugt mehr Overhead als ein rohes Tuple.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Falls der Pfad jemals in einer Hot-Loop liegen sollte, koennte ein rohes Tuple oder ein slots-Dataclass-Vergleich erneut bewertet werden.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Callback-Aufbaus.
- Reale Laufzeit haengt staerker von Tk-Event-Binding und spaeteren UI-Events ab.
