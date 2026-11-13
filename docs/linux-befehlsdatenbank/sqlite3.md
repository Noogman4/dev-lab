---
id: "sqlite3"
name: "sqlite3"
command: "sqlite3"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "sqlite3"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 524
reviewed_at: "2026-11-13"
locally_checked_version: "sqlite3-CLI nicht vorhanden; Python-Modul vorhanden, nicht als CLI-Test genutzt"
---

# sqlite3 – SQLite mit der Kommandozeile verwenden

## 1. Kurzbeschreibung

sqlite3 ist eine Kommandozeilenanwendung für SQLite-Datenbanken und kein eigenständiger Server.

## 2. Was macht der Befehl?

Die Kommandozeile und die SQLite-Bibliothek sind verschiedene Komponenten. Ein vorhandenes Python-Modul sqlite3 belegt keine installierte CLI. Ein neuer Dateiname kann eine Datenbank anlegen; :memory: bezeichnet eine flüchtige Datenbank. SQL endet mit Semikolon, Punktbefehle sind Anweisungen des Clients. Die CLI fehlt hier.

Quelle, am 2026-11-13 gelesen: [SQLite: offizielles CLI-Handbuch](https://sqlite.org/cli.html)

## 3. Syntax

```text
sqlite3 [OPTIONEN] [DATENBANKDATEI] [SQL]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| :memory: | Flüchtige Datenbank innerhalb dieses Prozesses. |
| -readonly | Vorhandene Datenbank lesend öffnen; kein allgemeiner Schutz vor sämtlichen CLI-Nebenwirkungen. |
| -header | Spaltennamen anzeigen. |
| -csv | CSV-Ausgabe wählen. |
| .schema | Schema anzeigen; Punktbefehl. |
| .read DATEI | Befehle aus Datei ausführen, nicht bloß deren Text ansehen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
sqlite3 ':memory:' 'SELECT 2 + 3 AS summe;'
```

Der Ausdruck würde in einer neuen flüchtigen Datenbank 5 ergeben. Dies ist nur eine Erklärung; kein Test mit dem Python-Modul wird als CLI-Test gezählt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Lokale Datenbankformate verstehen; eigene kleine SQL-Ausdrücke prüfen; Schema einer freigegebenen Datenbank lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Produktive Datenbanken können durch SQL verändert werden. .shell, .output, .read und Erweiterungen haben zusätzliche Wirkungen. Eine Shellumleitung kann Dateien überschreiben, selbst wenn die Datenbank lesend geöffnet ist.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Continuation prompt | SQL-Abschluss mit Semikolon fehlt möglicherweise. |
| Unable to open database | Pfad und Modus prüfen; nicht einfach eine neue Datei unter anderem Namen erzeugen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** sqlite3-CLI nicht vorhanden; Python-Modul vorhanden, nicht als CLI-Test genutzt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| python3 | Kann SQLite-Bibliothek separat verwenden. |
| psql | Servergebundener Client. |
| mysql | Anderer SQL-Client. |

Ausgangsdatensatz 524 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
