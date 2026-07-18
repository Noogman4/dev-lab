# Radio Smoke Test

Kurzer Praxis-Check fuer den NetMon-Radio-Flow mit `embedded`, `standalone`,
Detach, Reattach und Desktop-Launcher.

## Ziel

Sicherstellen, dass das Radio in diesen Wegen stabil arbeitet:

1. eingebettet in NetMon
2. aus NetMon geloest als Standalone-App
3. weiterlaufend nach NetMon-Schliessen
4. direkt ueber Starticon startbar
5. wieder an NetMon anheftbar

## Vorbereitung

Vor dem manuellen Test:

1. NetMon normal starten
2. sicherstellen, dass `mpv` verfuegbar ist
3. falls gewuenscht: in den Einstellungen das Radio-Starticon aktivieren
4. einen funktionierenden Radiosender im Radio-Tab auswaehlen

## Smoke-Ablauf

### A. Embedded-Basis

1. NetMon starten
2. Radio-Tab oeffnen
3. Radiosender starten
4. pruefen:
   - Header zeigt aktiven Sender
   - Status zeigt laufendes Radio
   - Radio spielt im eingebetteten Modus

### B. Detach zu Standalone

1. Im Radio-Tab `Radio-App erneut öffnen` bzw. `abloesen` ausloesen
2. pruefen:
   - Status im Tab zeigt Standalone-Uebergang
   - externe Radio-App startet
   - aktueller Sender, Lautstaerke, EQ und Suchzustand bleiben erhalten
   - falls Radio vorher lief, laeuft es in der Standalone-App weiter

### C. NetMon schliessen

1. NetMon komplett schliessen, waehrend Radio detached ist
2. pruefen:
   - Standalone-Radio bleibt offen
   - Wiedergabe bleibt erhalten
   - Standalone-App zeigt, dass NetMon nicht aktiv ist

### D. Direkter Standalone-Start

1. Radio-Starticon aus dem Desktop-Menue starten
2. pruefen:
   - Standalone-App startet direkt
   - kein unkontrollierter Doppelstart entsteht
   - Host-Zustand bleibt konsistent

### E. Reattach zu NetMon

1. NetMon erneut starten
2. In der Standalone-App `Radio anheften` klicken
3. pruefen:
   - Status zeigt Anheften/Uebergang
   - Radio erscheint wieder eingebettet in NetMon
   - Sender, Lautstaerke, EQ und Suchzustand bleiben erhalten
   - Standalone-App beendet sich sauber

## Erwartetes Ergebnis

- genau ein aktiver Radio-Host
- kein Playback-Verlust beim normalen Host-Wechsel
- kein versehentliches Stoppen beim NetMon-Schliessen im detached Zustand
- Starticon startet Radio auch ohne laufendes NetMon

## Optionaler Schnellcheck

Ohne kompletten manuellen Durchlauf:

1. `python3 netmon_radio_app.py --headless-smoke`
2. alternativ mit virtuellem Display:
   `xvfb-run -a python3 netmon_radio_app.py --headless-smoke`

Das prueft nur den Startpfad der Standalone-App, nicht den kompletten
Detach-/Reattach-Flow.
