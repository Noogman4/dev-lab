---
id: "ac"
name: "ac"
command: "ac"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "ac"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 588
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Wtmp-Auswertung offen"
---

# ac – Verbindungszeiten aus Wtmp-Daten summieren

## 1. Kurzbeschreibung

ac aus GNU acct berechnet Sitzungszeiten anhand von Login- und Logoutdatensätzen.

## 2. Was macht der Befehl?

Connect time ist keine CPU-Zeit und kein Beweis für aktive Arbeit. Die Berechnung hängt von Vollständigkeit und Qualität der Wtmp-Daten ab. Überschneidende Sitzungen, Neustarts und Uhrsprünge können die Einordnung beeinflussen. ac ist lokal nicht vorhanden.

Quelle, am 2026-11-13 gelesen: [GNU-acct: mit Debian ausgeliefertes ac-Handbuch](https://manpages.debian.org/bookworm/acct/ac.1.en.html)

## 3. Syntax

```text
ac [OPTIONEN] [BENUTZER ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -d | Tageswerte statt nur Gesamtsumme. |
| -p | Zusätzliche Summen je Benutzer. |
| -f DATEI | Ausdrücklich gewählte Wtmp-Datei verwenden. |
| --complain | Datenprobleme melden. |
| -y | Jahresangabe ergänzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
ac -f EIGENE_WTMP_DATEI -p
```

Die unausgeführte Übung würde nur eine zuvor selbst erzeugte Wtmp-Testdatei auswerten. Eine normale Textdatei ist kein passendes binäres Wtmp-Format. Es werden keine tatsächlichen Benutzerzeiten ausgewiesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Historische Sitzungsstatistik verstehen; Datengrundlage und Summen auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reale Loginhistorie ist vertraulich. Fehlende Wtmp-Dateien nicht als Teil einer Probe systemweit anlegen. Keine Benutzerdateien, Konten oder Protokollierungsdienste verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei fehlt | Datenquelle und Aufzeichnung prüfen, keine Systemdatei erzeugen. |
| Unplausible Summe | Uhrsprünge und unvollständige Sitzungsdatensätze berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Wtmp-Auswertung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| last | Einzelsitzungen anzeigen. |
| times | CPU-Zeit der Shell. |
| time | Einzelnen Befehl messen. |

Ausgangsdatensatz 588 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
