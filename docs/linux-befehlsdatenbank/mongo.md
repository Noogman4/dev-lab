---
id: "mongo"
name: "mongo"
command: "mongo"
category: "Python & Daten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Python & Daten", "mongo"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 517
reviewed_at: "2026-11-13"
locally_checked_version: "mongo und mongosh nicht vorhanden; Legacy-Optionen gegen Quellstand r5.0.31 gelesen, nicht ausgeführt"
---

# mongo – Historische MongoDB-Shell richtig zuordnen

## 1. Kurzbeschreibung

mongo bezeichnet im Katalog die ältere MongoDB-Shell, nicht den Datenbankserver und nicht automatisch mongosh.

## 2. Was macht der Befehl?

Die aktuell abrufbare Herstellerdokumentation beschreibt mongosh als JavaScript-REPL für MongoDB. Historische mongo-Referenzadressen leiten dorthin um. Optionen und Startverhalten dürfen deshalb nicht ungeprüft auf eine alte mongo-Installation übertragen werden. Für die Legacy-Schnittstelle wurde deshalb zusätzlich der Herstellerquellstand r5.0.31 gelesen: --nodb unterdrückt die anfängliche Datenbankverbindung, --norc das Laden von .mongorc.js und --eval wertet JavaScript aus. Diese begrenzenden Optionen machen beliebigen JavaScript-Code nicht sicher. Die feste Katalogkennung bleibt erhalten; ein stiller Austausch des Befehls wäre eine falsche Zuordnung.

Quelle, am 2026-11-13 gelesen: [MongoDB: Legacy-Optionsdefinition r5.0.31](https://raw.githubusercontent.com/mongodb/mongo/r5.0.31/src/mongo/shell/shell_options.idl), [Legacy-Optionsverarbeitung](https://raw.githubusercontent.com/mongodb/mongo/r5.0.31/src/mongo/shell/shell_options.cpp), [heutiges mongosh](https://www.mongodb.com/docs/mongodb-shell/)

## 3. Syntax

```text
mongo [OPTIONEN] [DATENBANKADRESSE] [DATEI.js ...]
Aktuelle separate Shell: mongosh [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| mongo | Historischer Client; exakte lokale Version zuerst feststellen. |
| mongosh | Eigenständiger heutiger Client mit eigener Dokumentation. |
| --nodb | Keine Datenbankverbindung beim Start, kein Datenbankadressenargument erwartet (r5.0.31). |
| --norc | Persönliche .mongorc.js nicht ausführen (r5.0.31). |
| --eval CODE | JavaScript tatsächlich auswerten (r5.0.31). |
| Verbindungszeichenfolge | Server und Datenbank auswählen; kann echte Netzwerkverbindung auslösen. |
| JavaScript / CRUD | Abfragen und Änderungen erfolgen über die Shell, nicht nur Anzeige. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
mongo --help
```

Dies ist nur ein nicht ausgeführtes historisches Hilfemuster. Die Hilfeverarbeitung ist im gelesenen Legacy-Quellstand belegt; gegen eine installierte Version wurde sie nicht geprüft. Kein mongosh-Aufruf wurde als mongo-Test ausgegeben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Ältere Skripte identifizieren; eine bewusst geplante Migration der Shell vorbereiten; Client und Server auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Verbindungen, Startdateien und JavaScript können echte Daten verändern. Geheimnisse in URI oder Historie vermeiden. Die Übertragbarkeit des gelesenen r5.0.31-Quellstands auf andere Legacy-Versionen bleibt offen; keine pauschale Kompatibilitätszusage.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| mongo fehlt | Nicht automatisch durch einen Alias auf mongosh ersetzen. |
| Alte Dokumentationsadresse leitet um | Legacy-Handbuch und konkrete Programmversion gesondert beschaffen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** mongo und mongosh nicht vorhanden; Legacy-Optionen gegen Quellstand r5.0.31 gelesen, nicht ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mongosh | Aktuelle separate MongoDB-Shell. |
| mongod | Datenbankserver. |
| psql | Client einer anderen Datenbankfamilie. |

Ausgangsdatensatz 517 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
