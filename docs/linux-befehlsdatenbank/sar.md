---
id: "sar"
name: "sar"
command: "sar"
category: "Systeminformationen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Systeminformationen", "sar"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 614
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; Funktionsprüfung offen"
---

# sar – Aktuelle und gespeicherte Aktivitätsberichte unterscheiden

## 1. Kurzbeschreibung

sar sammelt oder liest Systemaktivitätsstatistiken aus dem Sysstat-Paket.

## 2. Was macht der Befehl?

Ohne Intervall wird meist eine vorhandene Tagesdatei gelesen; mit Intervall erfolgt eine neue Messung. -f wählt eine Binärdatei, -o schreibt Messdaten. Historische Dateien und lokale Version müssen zueinander passen.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://man7.org/linux/man-pages/man1/sar.1.html)

## 3. Syntax

```text
sar [OPTIONEN] [INTERVALL [ANZAHL]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -u | CPU-Bericht |
| -r | Speicherbericht |
| -d | Gerätebericht |
| -f DATEI | Gespeicherte Binärdaten lesen |
| -o DATEI | Messdaten schreiben |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
sar -u -f EIGENE_SYSSTAT_DATEI
```

Eine eigene gültige Statistikdatei wäre Voraussetzung. Keine reale Tagesdatei gelesen und kein Datensammler gestartet.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Historische Leistungskurven von aktuellen Messungen unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Berichte können Infrastrukturdetails enthalten. Fehlende Dateien rechtfertigen keinen Dienststart und keine Systempaketinstallation.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Cannot open file | Ausgewählte Quelle fehlt |
| Format inkompatibel | Sysstat-Version und Erzeuger prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; Funktionsprüfung offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mpstat | CPU-Bericht |
| iostat | I/O-Bericht |
| vmstat | Andere Zeitreihe |

Ausgangsdatensatz 614 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
