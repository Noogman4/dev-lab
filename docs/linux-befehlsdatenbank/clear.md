---
id: "clear"
name: "clear"
command: "clear"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["clear", "grundlagen & hilfe"]
status: "Anzeigeverhalten anhand des Handbuchs geprüft; kein sichtbares Terminal geleert"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 348
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale ncurses-Manpage gelesen"
---

# clear – Terminalanzeige leeren, ohne Befehle zu beenden

## 1. Kurzbeschreibung

`clear` sendet Steuerfolgen zum Leeren der Terminalansicht. Je nach Terminal und Optionen kann auch der Rückscrollpuffer betroffen sein. **Root-Rechte sind nicht nötig.** Laufende Programme werden dadurch nicht automatisch beendet.

## 2. Was macht der Befehl?

Die lokale ncurses-Manpage beschreibt die Auswahl über `TERM` und die terminfo-Datenbank. Die erzeugten Anweisungen richten sich an das Terminal, nicht an Protokolldateien oder Shellhistorie.

Eine leere Ansicht bedeutet daher nicht, dass frühere Befehle oder Inhalte aus allen Aufzeichnungen verschwunden sind. Ebenso bleibt ein im Hintergrund laufender Prozess aktiv.

## 3. Syntax

```bash
clear
clear -x
```

Die Formen sind für ein passendes Terminal gedacht. In eine Datei umgeleitet entstehen Steuerzeichen, keine gewöhnliche Textbeschreibung einer leeren Seite.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-x` | Rückscrollpuffer nicht gezielt löschen. | Sichtbarer Bildschirm wird weiterhin geleert. |
| `-T TYP` | Terminaltyp ausdrücklich wählen. | Falscher Typ kann ungeeignete Steuerfolgen erzeugen. |
| `-V` | ncurses-Version zeigen. | Kein Leeren nötig. |

`TERM` sollte zum tatsächlichen Terminal passen. Einen zufälligen Wert zu setzen ist keine allgemeine Reparatur seiner Darstellung.

## 5. Beispiel erklärt Schritt für Schritt

Für eine aufgeräumte Anzeige unter Erhalt des erreichbaren Rückscrollbereichs ist der geplante Aufruf:

```bash
clear -x
```

Vorher wichtige Meldungen lesen oder bei Bedarf bewusst sichern. Anschließend wäre die sichtbare Ansicht leer; weiterlaufende Aufgaben und deren Ausgabeströme bleiben bestehen.

Der Befehl wurde hier nicht auf das Benutzerterminal angewendet. Das Verhalten ist anhand der lokalen Manpage beschrieben. Welche Rückscrollfunktionen tatsächlich vorhanden sind, hängt vom konkreten Terminal ab.

## 6. Typische Anwendungsfälle

- Nach längerer Ausgabe wieder eine übersichtliche Eingabeansicht herstellen.
- Eine neue Demonstration im eigenen Terminal beginnen.
- Sichtbare Anzeige und laufenden Prozesszustand auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Wichtige vorherige Meldungen können aus dem direkt erreichbaren Bild verschwinden. Ohne `-x` kann die dokumentierte Variante zusätzlich den Rückscrollbereich löschen, soweit das Terminal dies unterstützt.

Das ist keine zuverlässige Geheimnislöschung. Screenshots, Logs, Terminalmitschnitte und Shellverlauf können weiter existieren. Versehentlich sichtbare Passwörter werden dadurch nicht wieder vertraulich.

## 8. Häufige Fehler

- **Prozessende erwartet:** `clear` beendet keinen Job.
- **Historie gelöscht geglaubt:** Andere Datenhaltung.
- **Unpassende Darstellung:** Terminaltyp und Umgebung prüfen.
- **Umgeleitete Ausgabe als Text behandeln:** Enthält Steuerfolgen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Wichtige Fehlermeldungen vor dem Leeren erfassen. Wenn der Verlauf erhalten bleiben soll, die dokumentierte `-x`-Variante bevorzugen.

Bei einer grundsätzlich beschädigten Terminalkonfiguration kann `reset` eine andere Aufgabe lösen. Es ist nicht einfach dieselbe Aktion unter anderem Namen.

## 10. Verwandte Befehle

- `reset`: Terminalzustand neu initialisieren.
- `tput`: Terminalspezifische Fähigkeiten ansprechen.
- `history`: Bash-Befehlsverlauf; andere Funktion.
- `jobs`: Hintergrundaufgaben betrachten.

**Prüfstand:** Lokale Manpage gelesen. Kein Benutzerbildschirm oder Verlauf geleert.

Ausgangsdatensatz 348 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
