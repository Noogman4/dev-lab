---
id: "top"
name: "top"
command: "top"
category: "Prozesse & Jobs"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Prozesse & Jobs", "top"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 512
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# top – Prozess- und Systemwerte wiederholt beobachten

## 1. Kurzbeschreibung

top zeigt Prozessdaten und eine laufend aktualisierte Systemübersicht.

## 2. Was macht der Befehl?

Interaktive Tasten können Darstellung und teilweise Prozesse verändern. Der Batchmodus erlaubt dagegen eine begrenzte Textausgabe. CPU-, Speicher- und Lastwerte beschreiben verschiedene Größen. Eine einzelne Startanzeige genügt nicht für belastbare Leistungsdiagnosen; gespeicherte Einstellungen können die sichtbaren Felder beeinflussen.

Quelle, am 2026-11-13 gelesen: [procps-ng top-Handbuch](https://man7.org/linux/man-pages/man1/top.1.html)

## 3. Syntax

```text
top [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -b | Batchmodus ohne interaktive Eingaben. |
| -n ZAHL | Nach dieser Zahl von Aktualisierungen enden. |
| -p PID | Ausgewählte PIDs anzeigen. |
| -d SEKUNDEN | Aktualisierungsintervall. |
| -H | Threads statt nur Prozesse zeigen. |
| q / h | Interaktiv beenden beziehungsweise Hilfe lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
top -b -n 1 -p EIGENE_TEST_PID
```

Das Muster würde genau eine Batchanzeige für eine zuvor bestimmte eigene PID ausgeben. Es wurde nicht ausgeführt. Konfiguration, globale Zusammenfassung und PID-Lebensdauer wären vor realer Nutzung zu prüfen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Eigene Prozessaktivität beobachten; CPU- und Speicherwerte im Zusammenhang lesen; eine begrenzte Diagnoseaufnahme vorbereiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Interaktives k signalisiert Prozesse, r kann Nice-Werte ändern und W Konfiguration schreiben. Diese Funktionen sind keine lesende Anzeige. Argumentlisten können Geheimnisse zeigen. Kein interaktiver Start und keine Prozessänderung getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Anzeige läuft endlos | Batchmodus zusätzlich mit -n begrenzen. |
| Andere Spalten als erwartet | Version und gespeicherte Konfiguration vergleichen. |
| Hohe VIRT-Zahl | Virtueller Adressraum ist nicht gleich belegter RAM. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| ps | Einmalige kontrollierte Tabelle. |
| free | Speicherübersicht. |
| htop | Alternative interaktive Prozessanzeige. |

Ausgangsdatensatz 512 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
