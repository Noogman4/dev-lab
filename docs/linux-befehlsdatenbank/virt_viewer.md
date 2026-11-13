---
id: "virt_viewer"
name: "virt-viewer"
command: "virt-viewer"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "virt-viewer"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 703
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Konsole und Transport offen"
---

# virt-viewer – Eine grafische Gastkonsole als Verbindung verstehen

## 1. Kurzbeschreibung

virt-viewer verbindet sich mit der grafischen Konsole einer virtuellen Maschine.

## 2. Was macht der Befehl?

Domänen-ID, UUID und Name können ein Ziel bestimmen. Die Libvirt-URI legt den Kontext fest. --wait wartet auf Verfügbarkeit, --reconnect auf erneute Verbindung. Das Werkzeug ist keine Gastinstallationsroutine und startet nicht automatisch eine sicher isolierte Testumgebung.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://manpages.debian.org/bookworm/virt-viewer/virt-viewer.1.en.html)

## 3. Syntax

```text
virt-viewer [OPTIONEN] [ID oder UUID oder DOMÄNENNAME]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -c URI | Libvirt-Verbindung |
| -w | Auf Gastverfügbarkeit warten |
| -r | Wiederverbinden |
| -f | Vollbild |
| -d, --direct | Keinen SSH-Tunnel für die Konsolenverbindung verwenden |
| -a, --attach | Libvirt um einen vorverbundenen Socket bitten; nur für lokale Gäste, sonst möglicher direkter Fallback |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
virt-viewer -c qemu:///session TESTDOMAIN
```

Keine Grafikverbindung oder Eingabe an einen Gast. Das fehlende Werkzeug wurde nicht installiert.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Konsolenverbindung und VM-Verwaltung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Tastatur, Zwischenablage oder dargestellte Daten können vertraulich sein und Gastaktionen auslösen. Kein Anmelde- oder Fernsteuerungstest.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Konsole fehlt | Gastzustand und Grafikprotokoll prüfen |
| Wartet weiter | Wait/Reconnect bewusst wählen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Konsole und Transport offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| virt-manager | Verwaltung |
| virsh | Domänenzustand |
| remote-viewer | Andere Viewer-Schnittstelle |

Ausgangsdatensatz 703 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
