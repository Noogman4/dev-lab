---
id: "reset"
name: "reset"
command: "reset"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "caution"
tags: ["reset", "grundlagen & hilfe"]
status: "Kein Reset des Benutzerterminals ausgeführt"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 366
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale ncurses-/tset-Manpage gelesen"
---

# reset – einen beschädigten Terminalzustand neu initialisieren

## 1. Kurzbeschreibung

`reset` initialisiert Terminalzustände neu, etwa nach einer Anwendung, die Echo oder Eingabemodus ungünstig hinterlassen hat. **Root-Rechte sind nicht nötig.** Es startet weder den Rechner noch einen Dienst neu.

## 2. Was macht der Befehl?

Die lokale gemeinsame Manpage von `tset` und `reset` beschreibt unter anderem die Rückkehr zu üblichen Eingabemodi und das Senden geeigneter Terminalsteuerfolgen. Der verwendete Terminaltyp ist dabei relevant.

Das ist mehr als das Leeren einer Ansicht. Es kann Eingabezeichen und Darstellung verändern. Eine allgemeine Anwendungsstörung, ein kaputter Netzwerkzugang oder ein hängender Systemdienst wird dadurch nicht automatisch behoben.

## 3. Syntax

```bash
reset
```

Den Aufruf nur in dem eigenen betroffenen Terminal verwenden. In einer anderen Sitzung würde er nicht zwangsläufig den gewünschten Zustand erreichen.

## 4. Wichtige Optionen

| Form | Aufgabe | Grenze |
| --- | --- | --- |
| Ohne Option | Neuinitialisierung anfordern. | Verändert Terminalzustand. |
| `-V` | Verwendete ncurses-Version anzeigen. | Kein gewöhnlicher Reparaturlauf. |
| `-e ZEICHEN` | Löschzeichen festlegen. | Gezielte Eingabekonfiguration. |
| `-i ZEICHEN` | Interruptzeichen festlegen. | Kann Bedienverhalten verändern. |
| `-k ZEICHEN` | Zeilenlöschzeichen festlegen. | Nicht für einen ersten Versuch nötig. |

Gemeinsame Optionen der tset-Familie nicht ungeprüft als vollständig schreibfreien Resetmodus verstehen. Die besondere Reset-Neuinitialisierung ist gesondert beschrieben.

## 5. Beispiel erklärt Schritt für Schritt

Angenommen, ein zuvor beendetes Terminalprogramm hat die Anzeige der eigenen Eingaben ausgeschaltet. Zuerst klären, ob tatsächlich eine Shell wartet und nicht eine noch laufende Anwendung Eingaben verarbeitet.

Ein bewusst eingegebenes `reset` könnte dann den üblichen Zustand wiederherstellen. Bei ungewöhnlicher Zeilenendeverarbeitung nennt das Handbuch auch die Eingabe über Control-J. Diese Bedienung ist eine mögliche Hilfe, keine hier ausgeführte Aktion.

Es wurde kein Reset im Benutzerterminal gestartet. Dadurch gingen keine sichtbaren Meldungen verloren und es wurden keine persönlichen Steuerzeichen geändert.

## 6. Typische Anwendungsfälle

- Nach einem beendeten Vollbildprogramm die Eingabe wieder nutzbar machen.
- Einen unerwarteten Rohmodus des eigenen Terminals verlassen.
- Terminalzustand von Programm- oder Systemzustand unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Aufruf kann Anzeige und Eingabezustand verändern. Wichtige sichtbare Meldungen vorher sichern, soweit das betroffene Terminal dies noch erlaubt.

Keine Passwörter eingeben, nur weil Zeichen gerade unsichtbar bleiben. Unsichtbare Eingabe kann zu einem anderen noch laufenden Programm gehören. `reset` ist auch keine Geheimnislöschung.

## 8. Häufige Fehler

- **Neustart erwartet:** Nur Terminalinitialisierung.
- **Falsches Terminal:** Andere Sitzung betroffen.
- **Noch laufende Anwendung übersehen:** Eingegebener Text kann an sie gehen.
- **`clear` gleichsetzen:** Leeren und Initialisieren sind verschieden.

## 9. Sichere Varianten oder Tipps für Einsteiger

Bei bloß unübersichtlicher Anzeige `clear -x` statt einer Neuinitialisierung erwägen. Bei echter Terminalstörung erst den eigenen Sitzungskontext klären.

Dauerhafte Shell- oder Terminaleinstellungen nicht wegen eines einmaligen Vorfalls verändern. Ursache und beobachteten Effekt getrennt beschreiben.

## 10. Verwandte Befehle

- `clear`: Anzeige leeren.
- `stty`: Terminalparameter anzeigen und ändern.
- `tset`: Terminalinitialisierung verwalten.
- `jobs`: Eigene Shellaufgaben betrachten.

**Prüfstand:** Lokale Manpage gelesen. Kein Terminalreset, Sitzungsabbruch oder Systemneustart.

Ausgangsdatensatz 366 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
