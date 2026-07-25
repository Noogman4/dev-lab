# 13 Radio Runtime Paths Performance

## Messbedingungen

- Bereich: `netmon/netmon_radio_app.py`
- Commit vorher: `8db1fc54`
- Operation: Radio-Pfade auf einem `SimpleNamespace` initialisieren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-Pfad ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_paths_inline` | 1.462315311000566 s |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_runtime_paths_helper` | 1.6442980319998242 s |

## Bewertung

- Der neue Helper fuegt nur kleinen Aufruf- und Test-Lambda-Overhead hinzu.
- Die Operation laeuft einmal beim App-Start und ist nicht laufzeitkritisch.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Wichtiger fuer Startzeit sind echte Pfaderzeugung, Tk-Initialisierung und Runtime-Ladevorgaenge.

## Aussagekraft

- Die Messung prueft nur Attributzuweisungen mit Dummy-Pfaden.
- Reale Startzeit haengt staerker von Dateisystem- und Runtime-Ladevorgaengen ab.
