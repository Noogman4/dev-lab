# 13 Radio Embedded Panel Show Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `f3aef195`
- Operation: Embedded-Mode pruefen, Host leeren, Panel bauen und App-State setzen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-App, Dummy-Host, Dummy-Clear und Dummy-Panel ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_embedded_panel_show` | 682 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_embedded_panel_show` | 772 ns |

## Bewertung

- Der extrahierte Helper fuegt keine relevante Laufzeit hinzu.
- Die Operation bleibt im Dummy-Pfad unter 1 us.
- Keine Widget-Erzeugung ausser dem unveraenderten Panel-Factory-Pfad eingefuehrt.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte NetMonRadioPanel-Erzeugung und Tk-Layout-Verarbeitung.

## Aussagekraft

- Die Messung prueft nur den erfolgreichen Dummy-Pfad.
- Reale Laufzeit haengt staerker von Panel-Erzeugung, Tk-Layout und Radio-Initialisierung ab.
