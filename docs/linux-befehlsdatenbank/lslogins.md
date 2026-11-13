---
id: "lslogins"
name: "lslogins"
command: "lslogins"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "lslogins"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 607
reviewed_at: "2026-11-13"
locally_checked_version: "Lokale Hilfe gelesen; keine Kontenabfrage"
---

# lslogins – Konteninformationen gezielt zusammenführen

## 1. Kurzbeschreibung

lslogins zeigt ausgewählte Konten- und Loginmerkmale aus mehreren Datenquellen.

## 2. Was macht der Befehl?

Passwortstatus, letzte Anmeldung und Benutzerklassifikation sind unterschiedliche Angaben. Die Quellen können Passwd-/Shadowdaten sowie Wtmp/Btmp umfassen. -l begrenzt Konten; ein positionsgebundener Benutzername hat ein anderes ausführliches Ausgabeformat.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/lslogins.1.html)

## 3. Syntax

```text
lslogins [OPTIONEN] [BENUTZER]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -l NAMEN | Kontenauswahl |
| -o SPALTEN | Explizite Felder |
| -L | Letzte Sitzungsdaten |
| -f | Letzte Fehlversuche |
| -u | Benutzerkontenfilter, kein allgemeiner Sicherheitsbeweis |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
lslogins -l TESTKONTO -o USER,UID
```

Das Muster würde reale Kontendaten benötigen und bleibt unausgeführt. Die lokale Optionshilfe wurde gelesen, nicht die Kontenliste.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Kontenattribute von tatsächlicher Anmeldeberechtigung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Shadowdaten für ein Beispiel lesen. Gesperrtes Passwort bedeutet nicht automatisch gesperrte SSH-Schlüsselanmeldung. Keine Konten verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Leeres Feld | Quelle fehlt oder nicht zugänglich |
| Andere Ausgabe | Positionsargument und -l unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Lokale Hilfe gelesen; keine Kontenabfrage. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| lastlog | Letzter Login |
| getent | NSS-Abfrage |
| id | Identitätsinformationen |

Ausgangsdatensatz 607 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
