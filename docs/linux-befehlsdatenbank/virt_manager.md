---
id: "virt_manager"
name: "virt-manager"
command: "virt-manager"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "virt-manager"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 702
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; GUI und Libvirt-Zugriff offen"
---

# virt-manager – Grafische VM-Verwaltung richtig einordnen

## 1. Kurzbeschreibung

virt-manager ist eine grafische Verwaltungsanwendung für Libvirt.

## 2. Was macht der Befehl?

Die Oberfläche kann Verbindungen öffnen, Gäste anlegen, starten und konfigurieren sowie Storage und virtuelle Netze verwalten. Ein GUI-Start ist deshalb nicht automatisch eine nebenwirkungsfreie Dateiansicht. Gespeicherte Verbindungen beeinflussen den Startkontext.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/virt-manager/virt-manager.1.en.html)

## 3. Syntax

```text
virt-manager [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c URI | Verbindung vorgeben |
| --no-fork | Im Vordergrund bleiben |
| --debug | Zusätzliche Diagnose |
| --show-domain-console NAME | Gastkonsole anzeigen, versionsabhängig |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
virt-manager --help
```

Das Programm fehlt. Keine GUI, Verbindung oder Gastkonsole geöffnet. Hilfemuster wurde nicht als funktionaler Oberflächentest ausgegeben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Verwaltungsoberfläche von reiner Konsolenanzeige unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Klicks in der Oberfläche können reale VM- und Netzwerkaktionen auslösen. Keine GUI-Bedienung und keine Einstellungen getestet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Connection error | URI und Rechte prüfen |
| Leere Liste | System-/Sitzungsverbindung unterscheiden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; GUI und Libvirt-Zugriff offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| virsh | CLI |
| virt-install | Gastanlage |
| virt-viewer | Konsolenanzeige |

Ausgangsdatensatz 702 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
