---
id: "dos2unix"
name: "dos2unix"
command: "dos2unix"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "dos2unix"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 658
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Konvertierung offen"
---

# dos2unix – Windows-Zeilenenden bewusst umwandeln

## 1. Kurzbeschreibung

dos2unix wandelt unter anderem CRLF-Zeilenenden in LF um.

## 2. Was macht der Befehl?

Der normale Dateiaufruf arbeitet im alten Dateimodus und kann die Eingabe ersetzen. -n EINGABE AUSGABE wählt getrennte Dateien. Codierungs- und BOM-Behandlung sind zusätzliche Fragen und nicht dasselbe wie Zeilenenden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://dos2unix.sourceforge.io/dos2unix/man1/dos2unix.htm)

## 3. Syntax

```text
dos2unix [OPTIONEN] DATEI ...
dos2unix -n EINGABE AUSGABE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n IN OUT | Neues Ziel |
| -i | Dateiinformationen |
| -k | Zeitstempel erhalten |
| -f | Konvertierung erzwingen, riskant |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
dos2unix -n EIGENE_CRLF_DATEI NEUE_LF_DATEI
```

Das Werkzeug fehlt lokal. Keine Python- oder sed-Umwandlung wird als dos2unix-Test ausgegeben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Zeilenenden von Zeichencodierung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Binärdaten und vorhandene Eingaben können beschädigt werden. Keine echten Skripte oder Konfigurationen konvertiert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei unverändert | Binärerkennung oder fehlende CRLF prüfen |
| Umlaute kaputt | Codierung getrennt analysieren |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| unix2dos | Gegenrichtung |
| iconv | Codierungen |
| od | Bytes kontrollieren |

Ausgangsdatensatz 658 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
