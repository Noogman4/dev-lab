---
id: "taskset"
name: "taskset"
command: "taskset"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "taskset"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 508
reviewed_at: "2026-11-13"
locally_checked_version: "util-linux 2.39.3"
---

# taskset – CPU-Affinität gezielt abfragen

## 1. Kurzbeschreibung

taskset liest oder setzt die Menge logischer CPUs, auf denen ein Prozess laufen darf.

## 2. Was macht der Befehl?

Affinität begrenzt zulässige CPUs; sie reserviert keine CPU exklusiv. Die zulässige Menge kann durch cpusets und Container bereits eingeschränkt sein. Eine Bitmaske und eine CPU-Liste sind unterschiedliche Darstellungen derselben Auswahl. Der reine PID-Aufruf ohne Maske liest die bestehende Zuordnung.

Quelle, am 2026-11-13 gelesen: [util-linux taskset-Handbuch](https://man7.org/linux/man-pages/man1/taskset.1.html)

## 3. Syntax

```text
taskset -p PID
taskset -pc CPU_LISTE PID
taskset MASKE BEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -p PID | Ohne zusätzliche Maske lesende Abfrage. |
| -c | Numerische CPU-Liste statt hexadezimaler Maske. |
| -a | Alle Threads des ausgewählten Prozesses berücksichtigen. |
| MASKE | Bit 0 entspricht logischer CPU 0; keine Auslastungsangabe. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
taskset --version
taskset -pc "$$"
printf 'Affinitaet nur gelesen
'
```

### Schritt 3: Ergebnis einordnen

Die vorhandene CPU-Liste der eigenen Shell wird gelesen. Es wird weder eine Maske gesetzt noch ein Programm auf einer anderen CPU gestartet. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

Einschränkungen einer eigenen Umgebung verstehen; CPU-Affinität von Prozessgewichtung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ungültige oder zu enge Masken können Programme ausbremsen. Schreibender PID-Modus betrifft den laufenden Prozess, mit -a mehrere Threads. Auch ein erfolgreicher Setzaufruf garantiert keine sofort beobachtbare Migration. Keine Affinität geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Invalid argument | Keine zulässige CPU in der gewünschten Menge. |
| CPU 0 fehlt | Container oder cpuset können andere CPUs zulassen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** util-linux 2.39.3. Praktisch geprüft: Eigene PID nur abgefragt; Maskensetzen und Threadänderungen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| renice | Relative CPU-Bevorzugung ändern. |
| ps | Aktuelle Ausführungs-CPU und Prozessdaten. |
| lscpu | Logische CPU-Topologie. |

Ausgangsdatensatz 508 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
