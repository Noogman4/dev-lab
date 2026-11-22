---
id: "scriptreplay"
name: "scriptreplay"
command: "scriptreplay"
category: "Text anzeigen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Text anzeigen", "scriptreplay"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 635
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# scriptreplay – Aufzeichnungen wiedergeben ohne Originalbefehle neu zu starten

## 1. Kurzbeschreibung

scriptreplay gibt aufgezeichnete Daten mit Timinginformationen wieder.

## 2. Was macht der Befehl?

Die ursprünglichen Befehle werden nicht erneut ausgeführt. Die wiedergegebenen Bytes können aber Terminalsteuersequenzen enthalten und wirken auf den aktuellen Anzeigekontext. Timingformat, Datenstream und Erzeugerversion müssen zusammenpassen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/scriptreplay.1.html)

## 3. Syntax

```text
scriptreplay [OPTIONEN] [TIMINGDATEI [AUSGABELOG [DIVISOR]]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --log-timing DATEI | Timingquelle |
| --log-out DATEI | Ausgabedaten |
| --divisor ZAHL | Geschwindigkeit skalieren |
| --maxdelay SEKUNDEN | Einzelwartezeit begrenzen |
| --summary | Zusammenfassung moderner Logs |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
scriptreplay --log-timing EIGENES_TIMING --log-out EIGENES_LOG
```

Keine echte oder fremde Terminalaufnahme wiedergegeben. Das Muster erklärt nur die Zusammengehörigkeit der beiden Dateien.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Archivierte eigene Sitzungsabläufe verstehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Aufzeichnungen nicht blind abspielen. Timingverkürzung entfernt keine Steuerzeichen und anonymisiert keine Inhalte.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Verzerrte Wiedergabe | Falscher Datenstream oder Timingformat |
| Sehr langsam | Pausen und Divisor prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| script | Aufnahme |
| cat | Ungetaktete Bytes |
| less | Kontrollierte Textansicht |

Ausgangsdatensatz 635 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
