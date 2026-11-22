---
id: "type"
name: "type"
command: "type"
category: "Grundlagen & Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["type", "grundlagen & hilfe"]
status: "Auflösungsformen dokumentiert; keine Programmdatei gestartet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 370
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Bash-Hilfe gelesen"
---

# type – erkennen, was Bash unter einem Befehlsnamen versteht

## 1. Kurzbeschreibung

`type` zeigt, ob ein Name für Bash etwa ein Alias, eine Funktion, ein Builtin oder ein externes Programm ist. **Root-Rechte sind nicht nötig.** Das Zielprogramm wird zur normalen Abfrage nicht ausgeführt.

## 2. Was macht der Befehl?

Die lokale Hilfe `help type` beschreibt die verfügbaren Ansichten. Das Ergebnis hängt von der aktuellen Shell und ihrem Suchkontext ab. Eine saubere neue Bash kann deshalb anders auflösen als die persönliche interaktive Sitzung.

Eine Auflösungsangabe ist kein Integritätsnachweis. Ein gefundener Pfad kann weiterhin ungeeignet, manipuliert oder aus einem unerwünschten Suchverzeichnis stammen.

## 3. Syntax

```bash
type printf
type -a printf
type -t printf
```

`printf` ist ein geeignetes Modell, weil eine Bash-interne und eine externe Variante existieren können. Konkrete Ausgaben dieses Rechners werden hier nicht als neu gemessen angegeben.

## 4. Wichtige Optionen

| Option | Zweck | Grenze |
| --- | --- | --- |
| `-a` | Mehrere verfügbare Auflösungen zeigen. | Kontext bleibt die aktuelle Shell. |
| `-t` | Kurze Typkategorie ausgeben. | Kein ausführlicher Dateibericht. |
| `-p` | Passenden Dateipfad ausgeben, falls externe Auflösung. | Kann bei Builtins leer bleiben. |
| `-P` | PATH-Suche nach einer Datei erzwingen. | Startet diese Datei nicht. |
| `-f` | Funktionen bei der Suche auslassen. | Bewusst veränderte Suchsicht. |

Kombinationen können den Umfang beeinflussen. Beispielsweise verändert die Dateipfadsicht, welche anderen Namensarten berücksichtigt werden.

## 5. Beispiel erklärt Schritt für Schritt

```bash
type -a printf
```

Der geplante Aufruf würde die vorhandenen passenden Auflösungen zeigen. Eine Builtinangabe ist keine normale Dateiposition; eine zusätzliche Pfadangabe kann eine externe Alternative benennen.

Erst danach wäre zu entscheiden, welche Variante für eine Anleitung gemeint ist. Ein Optionsbeispiel der externen GNU-Version gilt nicht automatisch vollständig für das Builtin.

Für diesen Eintrag wurde nur die lokale Builtinhilfe gelesen. Persönliche Funktionskörper und Aliasdefinitionen wurden nicht für einen tatsächlichen Inventurbericht erhoben.

## 6. Typische Anwendungsfälle

- Unerwartetes Befehlsverhalten durch Wrapper erklären.
- Builtin und externe Variante unterscheiden.
- Den passenden Hilfekanal wählen.
- Mehrere installierte Programmpositionen sichtbar machen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige kann Funktionsdefinitionen, persönliche Pfade oder Abkürzungen offenlegen. Vor Weitergabe den benötigten Umfang prüfen.

Ein angezeigter Pfad garantiert weder sichere Eigentümerrechte noch unveränderte Bytes beim späteren Aufruf. Sicherheitsrelevante Ausführung braucht eine passende zusätzliche Vertrauensprüfung.

## 8. Häufige Fehler

- **Datei gefunden gleich vertrauenswürdig:** Integrität wurde nicht geprüft.
- **Leeres `-p` gleich fehlt:** Name kann ein Builtin sein.
- **Andere Shell gleiches Ergebnis:** Umgebung unterscheidet sich.
- **Abfrage gleich Funktionstest:** Zielprogramm wurde nicht gestartet.

## 9. Sichere Varianten oder Tipps für Einsteiger

Bei Überraschungen zuerst `type NAME`, bei mehreren Varianten `type -a NAME`. Danach die Hilfe der tatsächlich gewünschten Implementierung lesen.

Keine Dateien aus dem Suchpfad entfernen, nur weil mehrere Treffer erscheinen. Mehrere legitime Varianten sind möglich.

## 10. Verwandte Befehle

- `command -v`: Kurze Verfügbarkeitsabfrage.
- `which`: Externe PATH-Suche.
- `builtin`: Ein Builtin ausdrücklich ausführen.
- `alias`: Abkürzungen anzeigen oder definieren.

**Prüfstand:** Lokale Bash-Hilfe gelesen. Keine fremde Programmdatei ausgeführt und keine persönliche Auflösungsregel geändert.

Ausgangsdatensatz 370 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
