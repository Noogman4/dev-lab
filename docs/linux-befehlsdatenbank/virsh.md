---
id: "virsh"
name: "virsh"
command: "virsh"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "virsh"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 700
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Libvirt-Betrieb offen"
---

# virsh – Libvirt-Verbindung und Domänenaktion auswählen

## 1. Kurzbeschreibung

virsh ist eine Kommandozeile zur Verwaltung von Libvirt-Domänen und Ressourcen.

## 2. Was macht der Befehl?

URI, Verbindungstyp und Aktion bestimmen den Bereich. qemu:///session und qemu:///system sind verschieden. --readonly begrenzt erlaubte API-Aktionen, ersetzt aber keine Auswahl einer freigegebenen Verbindung; Verbindungen können Dienste kontaktieren oder aktivieren.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.libvirt.org/manpages/virsh.html)

## 3. Syntax

```text
virsh [OPTIONEN] [UNTERBEFEHL [ARGUMENTE]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c URI | Verbindung wählen |
| -r | Nur lesende Verbindung |
| list --all | Alle bekannten Domänen |
| start | Domäne starten |
| destroy | Harte Beendigung, nicht bloße Dateilöschung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
virsh -r -c qemu:///session list --all
```

Keine Libvirt-Verbindung oder echte Domänenliste. virsh ist nicht vorhanden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Domänenzustand und Verwaltungsverbindung bewusst prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Start, Destroy, Undefine und Storageaktionen besitzen unterschiedliche Risiken. Keine VM gesteuert oder Hostberechtigung erweitert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Domänen | Verbindungskontext prüfen |
| Connection failed | Keinen Dienst eigenmächtig starten |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Libvirt-Betrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| virt-manager | Grafische Libvirt-Verwaltung |
| virt-install | Anlage |
| virt-viewer | Konsole |

Ausgangsdatensatz 700 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
