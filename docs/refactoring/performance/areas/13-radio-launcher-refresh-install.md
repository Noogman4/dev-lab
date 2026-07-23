# 13 Radio Launcher Refresh Install Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `67f14fb7`
- Operation: Launcher-Callbacks erzeugen, App-Refresh setzen und initialen Refresh ausfuehren
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-App, Dummy-Host und Dummy-Callback-Factories ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_launcher_wiring` | 208 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_launcher_wiring` | 278 ns |

## Bewertung

- Der extrahierte Helper fuegt nur kleinen Funktionsaufruf-Overhead hinzu.
- Die Operation bleibt deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echter Launcher-State-Refresh mit Tk-Status-Update.

## Aussagekraft

- Die Messung prueft nur den Dummy-Pfad der Launcher-Verkabelung.
- Reale Laufzeit haengt staerker von Status-Ermittlung, Text-Update und Widget-Anzeige ab.
