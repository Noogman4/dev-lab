---
id: "vboxmanage"
name: "VBoxManage"
command: "VBoxManage"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "VBoxManage"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 688
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht vorhanden; Host- und VM-Funktionen offen"
---

# VBoxManage – VirtualBox über die korrekte Kommandozeile verwalten

## 1. Kurzbeschreibung

VBoxManage ist die VirtualBox-Kommandozeile auf dem Host.

## 2. Was macht der Befehl?

Groß-/Kleinschreibung des Programmnamens ist auf Linux relevant. Unterbefehle unterscheiden registrierte VMs, laufende Instanzen und Konfigurationsänderungen. Name und UUID sind verschiedene Zielbezeichner; Namen mit Leerzeichen werden zitiert.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://docs.oracle.com/en/virtualization/virtualbox/7.1/user/vboxmanage.html)

## 3. Syntax

```text
VBoxManage UNTERBEFEHL [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| list vms | Registrierte VMs |
| list runningvms | Laufende VMs |
| showvminfo | Informationen einer VM |
| startvm | VM tatsächlich starten |
| modifyvm | Konfiguration ändern |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
VBoxManage list vms
```

Das Programm fehlt; keine VirtualBox-Konfiguration oder reale VM-Liste gelesen.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Registrierung und Laufzustand auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Start, Steuerung und Snapshotaktionen können Daten oder Ressourcen verändern. Keine VMs und kein Hypervisor gestartet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Befehl fehlt | Exakten Programmnamen prüfen |
| VM unbekannt | Name und Registrierungskontext prüfen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht vorhanden; Host- und VM-Funktionen offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| qemu-system-x86_64 | Andere Virtualisierung |
| virsh | Libvirt-Verwaltung |
| virt-manager | Grafische Verwaltung |

Ausgangsdatensatz 688 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
