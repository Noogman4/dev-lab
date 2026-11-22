---
id: "help_2"
name: "help"
command: "help"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["help_2", "grundlagen & hilfe"]
status: "Mehrere Builtin-Hilfen erfolgreich abgerufen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 356
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# help – die eingebaute Bash-Dokumentation lesen

## 1. Kurzbeschreibung

`help` zeigt die Dokumentation eingebauter Bash-Befehle. Für `cd`, `alias` oder `history` ist das oft der direkteste Einstieg. **Root-Rechte sind nicht nötig.** Der dokumentierte Befehl wird dabei nicht als Arbeitsaktion ausgeführt.

## 2. Was macht der Befehl?

Die lokale Ausgabe von `help help` beschreibt die Oberfläche. Ohne Thema erscheint eine Übersicht; mit Thema die passende Builtinbeschreibung. Ein externes Programm wie `mpv` gehört nicht automatisch dazu.

Die Ausgabe passt zur aufgerufenen Bash. Das ist wichtig, wenn ein Onlinehandbuch eine neuere Funktion nennt oder die aktuelle Sitzung eine andere Shell benutzt.

## 3. Syntax

```bash
help
help cd
help -s printf
help -m test
```

Für diese Datenbank wurden mehrere solcher Hilfen in einer Bash ohne persönliche Startdateien gelesen. Das war Dokumentationszugriff und keine Ausführung der beschriebenen Verwaltungsfunktionen.

## 4. Wichtige Optionen

| Option | Zweck | Anwendung |
| --- | --- | --- |
| `-d` | Kurze Beschreibung. | Themenüberblick. |
| `-s` | Kurze Syntax. | Argumentstruktur nachsehen. |
| `-m` | Handbuchähnliche Ausgabe. | Ausführlicher lesen. |
| Thema/Muster | Passende Hilfe auswählen. | Muster bei Bedarf quotieren. |

Eine Hilfe zu `test` ist nicht dasselbe wie das Ausführen eines Dateitests. Ebenso löscht `help history` keinen Verlauf.

## 5. Beispiel erklärt Schritt für Schritt

```bash
help cd
```

Zuerst wird das Thema `cd` ausgewählt. Bash gibt Syntax, Optionen und Statusbedeutung aus. Ein Zielverzeichnis muss dafür nicht existieren, und die Shell wechselt ihren Ort nicht.

Der entsprechende Hilfsabruf wurde lokal erfolgreich durchgeführt. Er bestätigt den gelesenen Hilfetext, nicht einen echten Verzeichniswechsel oder die Zugänglichkeit bestimmter Pfade.

Für eine erste Übersicht genügt `help -s cd`; für Details folgt der vollständige Text. Syntaxklammern und Alternativen anschließend in einen tatsächlichen Aufruf übersetzen, nicht wörtlich kopieren.

## 6. Typische Anwendungsfälle

- Vor einem Builtinaufruf Optionen klären.
- Bash-Builtin und externes Programm unterscheiden.
- Rückgabestatus einer Bedingung verstehen.
- Eine lokale Versionsabweichung zu einer Anleitung einordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der Hilfeaufruf selbst ist lesend. Die dort beschriebenen Funktionen können dagegen Dateien, Sitzungen oder Prozesse verändern. Ein aus der Hilfe kopierter Beispieltext ist deshalb vor Ausführung auf Ziel und Wirkung zu prüfen.

Nicht allein wegen fehlender Builtinhilfe eine Root-Shell starten. Eine andere Shell oder ein externer Befehl ist eine häufigere Erklärung.

## 8. Häufige Fehler

- **Hilfe für jedes Programm erwartet:** Geltungsbereich ist die Shell.
- **Andere Shell:** Unterstützung und Syntax können fehlen.
- **Nur Kurzsyntax gelesen:** Nebenwirkungen stehen möglicherweise im Langtext.
- **Hilfe als Wirkungstest:** Es wurde nur Dokumentation gelesen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit `type NAME` feststellen, ob ein Builtin vorliegt. Dann `help NAME` für dessen lokale Bedienung nutzen.

Für externe Werkzeuge bei dokumentierter Unterstützung `NAME --help`, sonst die passende Manpage verwenden. Ein unbekanntes Programm nicht nur für eine vermeintlich sichere Hilfeausgabe starten.

## 10. Verwandte Befehle

- `man`: Handbuchseiten.
- `info`: Strukturierte Dokumentation.
- `type`: Aufrufart erkennen.
- `apropos`: Handbuchthemen nach Aufgabe suchen.

**Prüfstand:** Lokale Builtinhilfen erfolgreich gelesen. Keine beschriebenen Systemaktionen dadurch ausgeführt.

Ausgangsdatensatz 356 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
