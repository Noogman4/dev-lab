---
id: "ag"
name: "ag"
command: "ag"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "ag"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 645
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; ag-Suche offen"
---

# ag – Silver-Searcher-Suchumfang verstehen

## 1. Kurzbeschreibung

ag ist der Programmname von The Silver Searcher.

## 2. Was macht der Befehl?

Die Suche ist rekursiv und berücksichtigt Ignoreregeln. -Q verwendet ein literales Muster; versteckte und ignorierte Dateien sind separate Auswahlfragen. Eine Option zur Erweiterung der Auswahl ist keine Garantie vollständiger Datenabdeckung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://raw.githubusercontent.com/ggreer/the_silver_searcher/master/doc/ag.1)

## 3. Syntax

```text
ag [OPTIONEN] MUSTER [PFAD ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -Q | Literale Suche |
| -i | Ohne Groß-/Kleinschreibung |
| -l | Dateinamen mit Treffer |
| --hidden | Versteckte Dateien einbeziehen |
| -g MUSTER | Dateipfade filtern |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ag -Q LERNTEXT EIGENE_DATEI
```

ag ist nicht installiert und wurde nicht ausgeführt. Kein fremder Quelltext gelesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Rekursive Suchwerkzeuge nach Auswahl und Musterregeln beurteilen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ausgaben können Geheimnisse und Dateipfade enthalten. Keine ungeprüften großen Verzeichnisbäume durchsuchen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei fehlt im Ergebnis | Ignoreregeln und Hidden-Auswahl prüfen |
| Regex anders | PCRE-Semantik nicht mit jeder grep-Variante gleichsetzen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; ag-Suche offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ack | Quelltextsuche |
| rg | Andere Engine |
| grep | Zeilenfilter |

Ausgangsdatensatz 645 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
