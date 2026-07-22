# 13 Radio Detached Placeholder State Performance

## Messbedingungen

- Bereich: `netmon/ui/tabs/radio_tab.py`
- Commit vorher: `ca3b1591`
- Operation: Feature-Button-Registrierung und Launcher-Mode-Setzen fuer den Detached-Placeholder
- Messuhr: `time.perf_counter()`
- 1000 Wiederholungen
- Dummy-App und Dummy-Button
- Keine Tk-Widgets erzeugt
- Keine Radio-Kommandos gestartet
- Keine Performance-Optimierung vorgenommen

## Ergebnisse Vorher

| Operation | Median |
| --- | ---: |
| `radio_detached_placeholder_state` | 0.0001 ms |

## Ergebnisse Nachher

| Operation | Median |
| --- | ---: |
| `radio_detached_placeholder_state` | 0.0001 ms |

## Bewertung

- Der extrahierte Helper fuegt keine messbare Laufzeit hinzu.
- Die Operation bleibt deutlich unter 1 ms.
- Keine Widget-, Datei-, Netzwerk- oder Subprocess-Zugriffe eingefuehrt.
- Keine Performance-Optimierung vorgenommen.

## Moegliche spaetere Optimierungen

- Keine aktuelle Optimierung empfohlen.
- Laufzeitrelevanter waere echte Widget-Erzeugung oder Reattach-Logik, nicht dieses State-Setzen.

## Aussagekraft

- Die Messung prueft nur Register-/State-Delegation mit Dummy-Objekten.
- Reale Laufzeit haengt staerker von Tk-Rendering und externer Radio-App ab.
