# 13 Radio UI Status Indicator Images Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `48181840`
- Operation: Status-Indicator-Dict auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Indicator-Builder ohne echte Tk-PhotoImages
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_status_indicator_images_inline` | 0.12262295700020331 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_ui_status_indicator_images_helper` | 0.16603284500160953 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Der Unterschied ist fuer den einmaligen UI-Start nicht relevant.
- Im echten UI-Pfad dominiert eher die Tk-PhotoImage-Erzeugung.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Die drei Bilder koennten spaeter gecacht werden, falls ein echter Startzeitbefund das rechtfertigt.

## Aussagekraft

- Die Messung prueft nur den ausgelagerten Dict-Aufbau mit Dummy-Bildern.
- Reale Startzeit haengt staerker von Tk, Bildaufbau und weiteren UI-Initialisierungen ab.
