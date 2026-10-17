# 13 Radio Marker Base Structure Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `13a963cd`
- Operation: Marker-Basis aus Dummy-Widget-Builder und Dummy-Drag-State-Factory erzeugen und zurueckgeben
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container, Dummy-Widget-Builder und Dummy-Drag-State-Factory ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_base` | 142 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_base` | 295 ns |

## Bewertung

- `NamedTuple` erzeugt mehr Overhead als ein rohes Tuple.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Falls der Pfad jemals in einer Hot-Loop liegen sollte, koennte ein rohes Tuple oder ein slots-Dataclass-Vergleich erneut bewertet werden.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Marker-Basisaufbaus.
- Reale Laufzeit haengt staerker von Tk-Frame- und Label-Erzeugung ab.
