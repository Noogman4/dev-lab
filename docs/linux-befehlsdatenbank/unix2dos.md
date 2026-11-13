---
id: "unix2dos"
name: "unix2dos"
command: "unix2dos"
category: "Text suchen & verarbeiten"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text suchen & verarbeiten", "unix2dos"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 685
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; CRLF-Konvertierung offen"
---

# unix2dos – LF-Zeilenenden in CRLF umwandeln

## 1. Kurzbeschreibung

unix2dos ist die Gegenrichtung zu dos2unix für Textzeilenenden.

## 2. Was macht der Befehl?

Unix-LF und Windows-CRLF sind Bytekonventionen, keine vollständige Zeichencodierung. Der normale Dateimodus kann die Eingabe ersetzen; -n erlaubt getrennte Ziele. Eine bereits vorhandene CRLF-Datei darf nicht durch einfache blind eingefügte CR-Zeichen beschädigt werden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://dos2unix.sourceforge.io/dos2unix/man1/dos2unix.htm)

## 3. Syntax

```text
unix2dos [OPTIONEN] DATEI ...
unix2dos -n EINGABE AUSGABE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -n IN OUT | Getrenntes Ziel |
| -i | Informationen statt Konvertierung |
| -k | Zeitstempel bewahren |
| -f | Binärschutz übergehen, riskant |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
unix2dos -n EIGENE_LF_DATEI NEUE_CRLF_DATEI
```

Das Programm fehlt. Die Konvertierung bleibt praktisch offen, keine Ersatzimplementierung als Nachweis verwendet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Plattformübergreifende Textdateien bewusst vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Binärdateien oder echten Skripte bearbeiten. Zeilenenden können Programminterpretation beeinflussen; Originaldaten bewahren.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Doppelte CR-Zeichen | Eingabeformat und früheren Konverter prüfen |
| Umlaute falsch | Codierung separat klären |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; CRLF-Konvertierung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| dos2unix | Gegenrichtung |
| iconv | Zeichencodierung |
| od | Byteansicht |

Ausgangsdatensatz 685 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
