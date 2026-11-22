---
id: "recode"
name: "recode"
command: "recode"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "recode"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 670
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Konvertierung offen"
---

# recode – Zeichensätze mit Recode umwandeln

## 1. Kurzbeschreibung

recode wandelt Zeichensätze und bestimmte Oberflächenkodierungen um.

## 2. Was macht der Befehl?

Eine Anfrage verwendet QUELLE..ZIEL. Bei benannten Dateien kann recode den Dateiinhalt ersetzen; ohne Dateiangabe arbeitet es als Filter. Codierungsnamen und Oberflächen sind keine automatische Erkennung. Das Programm fehlt lokal.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://raw.githubusercontent.com/rrthomas/recode/master/doc/recode.texi)

## 3. Syntax

```text
recode [OPTIONEN] QUELLE..ZIEL [DATEI ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -l | Verfügbare Zeichensätze auflisten |
| -v | Vorgang erläutern |
| -f | Bestimmte Probleme übergehen, kann Verluste verdecken |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
recode UTF-8..ISO-8859-1 < EIGENE_UTF8_DATEI > NEUE_DATEI
```

Das Filtermuster wurde nicht ausgeführt. Keine echte Datei umcodiert und kein anderer Konverter als recode-Test ausgegeben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Codierungsverfahren in älteren Skripten verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Nicht darstellbare Zeichen und Normalisierung können Informationen verändern. Originaldaten aufbewahren und Rückweg gesondert prüfen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unknown charset | Tatsächliche Implementierung und Namen prüfen |
| Datenverlust | Keine Force-Option als Reparaturgarantie |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| iconv | Andere Konvertierung |
| dos2unix | Zeilenenden |
| od | Bytekontrolle |

Ausgangsdatensatz 670 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
