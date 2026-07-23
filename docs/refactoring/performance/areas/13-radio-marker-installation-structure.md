# 13 Radio Marker Installation Structure Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `67bf231c`
- Operation: Marker-Installation aus Dummy-Factories erzeugen und zurueckgeben
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Container, Dummy-Pane, Dummy-Basis-Builder und Dummy-Callback-Builder ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_installation` | 183 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_marker_installation` | 364 ns |

## Bewertung

- `NamedTuple` erzeugt mehr Overhead als ein rohes Tuple.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Falls der Pfad jemals in einer Hot-Loop liegen sollte, koennte ein rohes Tuple oder ein slots-Dataclass-Vergleich erneut bewertet werden.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad des Marker-Installationsaufbaus.
- Reale Laufzeit haengt staerker von Tk-Frame-, Label-, Place- und Bind-Aufrufen ab.
