---
id: "multipass"
name: "multipass"
command: "multipass"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "multipass"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 696
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Instanzbetrieb offen"
---

# multipass – Multipass-Instanzen bewusst verwalten

## 1. Kurzbeschreibung

multipass verwaltet virtuelle Instanzen über einen Hintergrunddienst.

## 2. Was macht der Befehl?

list und info sind Abfragen; launch erzeugt und startet Instanzen. exec und shell führen im Gast aus. Imagebeschaffung kann Netzverkehr erzeugen. Verhalten von delete, recover und purge ist versionsabhängig und darf nicht aus älteren Anleitungen garantiert werden.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://canonical.com/multipass/docs/latest/reference/command-line-interface/)

## 3. Syntax

```text
multipass UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list | Instanzbestand |
| info NAME | Details |
| launch | Imagebasierte Erzeugung und Start |
| exec | Gastbefehl |
| mount | Hostdaten in Gast verfügbar machen |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
multipass list
```

Kein Server kontaktiert; Multipass fehlt. Keine Instanz, Imagebeschaffung oder Hostfreigabe.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Informationsabfrage und Provisionierung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Hostfreigaben und Netzwerke verbinden Ressourcenräume. Lösch- und Purgeaktionen können unwiederbringlich sein.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dienst nicht erreichbar | Nicht eigenmächtig starten |
| Instanz fehlt | Kontext und tatsächlichen Namen prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Instanzbetrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| qemu-system-x86_64 | Emulator |
| vagrant | Andere Provisionierung |
| virsh | Libvirt-Verwaltung |

Ausgangsdatensatz 696 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
