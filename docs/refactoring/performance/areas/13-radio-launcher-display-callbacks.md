# 13 Radio Launcher Display Callbacks Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `9a2cbae0`
- Operation: Anzeige-Callbacks fuer detached Placeholder und embedded Panel erzeugen
- Messwerkzeug: `timeit.repeat` ueber `.venv/bin/python -c`
- 1.000.000 Wiederholungen
- Dummy-App, Dummy-Host und Dummy-Shower ohne echte Tk-Widgets
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Best of 5 |
| --- | ---: |
| `radio_launcher_display_callback_detached` | 64 ns |
| `radio_launcher_display_callback_embedded` | 64 ns |

## Ergebnisse Nachher

| Operation | Best of 5 |
| --- | ---: |
| `radio_launcher_display_callback_detached` | 154 ns |
| `radio_launcher_display_callback_embedded` | 153 ns |

## Bewertung

- Die extrahierten Helper fuegen nur den erwartbaren Funktionsaufruf-Overhead hinzu.
- Beide Operationen bleiben deutlich unter 1 us.
- Keine Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Placeholder- oder Panel-Erzeugung.

## Aussagekraft

- Die Messung prueft nur die Callback-Erzeugung.
- Reale Laufzeit haengt staerker von Tk-Widget-Erzeugung und Radio-Panel-Aufbau ab.
