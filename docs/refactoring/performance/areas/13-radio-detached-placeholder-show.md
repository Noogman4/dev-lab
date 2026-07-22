# 13 Radio Detached Placeholder Show Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `dcc2620a`
- Operation: Detached-Mode pruefen, Host leeren, Placeholder-Texte holen, Placeholder bauen und State setzen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-App, Dummy-Host, Dummy-Clear, Dummy-Builder und Dummy-State-Setter ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detached_placeholder_flow` | 745 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_detached_placeholder_flow` | 818 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Widget-Erzeugung ausser dem unveraenderten Placeholder-Builder-Pfad eingefuehrt.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Tk-Widget-Erzeugung und Host-Clear-Verarbeitung.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Tk-Layout und Widget-Erzeugung ab.
