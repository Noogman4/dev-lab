---
id: "mpstat"
name: "mpstat"
command: "mpstat"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "mpstat"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 612
reviewed_at: "2026-11-13"
locally_checked_version: "Sysstat 12.6.1; Versionsaufruf, kein Funktionslauf"
---

# mpstat – CPU-Zeitanteile je Prozessor einordnen

## 1. Kurzbeschreibung

mpstat aus Sysstat zeigt CPU-Aktivitätsstatistiken.

## 2. Was macht der Befehl?

Ohne Intervall beziehen sich Werte typischerweise auf die Zeit seit Boot; mit Intervall werden Zeitabschnitte berichtet. -P ALL trennt Prozessoren von der Gesamtzeile. iowait ist keine direkt gemessene Gerätewarteschlange und allein kein Ursachenbeweis.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/mpstat.1.html)

## 3. Syntax

```text
mpstat [OPTIONEN] [INTERVALL [ANZAHL]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -P ALL | Alle CPUs getrennt |
| -u | CPU-Auslastung |
| -I SUM | Interruptübersicht |
| -o JSON | Strukturierte Ausgabe |
| -V | Version |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
mpstat -P ALL 1 2
```

Das Muster würde zwei begrenzte Messberichte erzeugen. Nur die Version wurde separat gelesen; keine CPU-Messung ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

CPU-Gesamtmittel und Einzelprozessoren unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Last erzeugt, Affinität oder Priorität geändert. Virtuelle Umgebung und CPU-Sicht begrenzen die Aussage.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| CPU fehlt | Offlinezustand und Sichtbarkeit prüfen |
| Andere Prozente | Intervall und Rundung beachten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Sysstat 12.6.1; Versionsaufruf, kein Funktionslauf. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| sar | Historische Statistik |
| iostat | I/O-Bezug |
| top | Prozesswerte |

Ausgangsdatensatz 612 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
