---
id: "qemu_system_x86_64"
name: "qemu-system-x86_64"
command: "qemu-system-x86_64"
category: "Virtualisierung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Virtualisierung", "qemu-system-x86_64"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 698
reviewed_at: "2026-11-13"
locally_checked_version: "QEMU 8.2.2; nur -version, VM-Betrieb offen"
---

# qemu-system-x86_64 – Systememulator von Imagewerkzeug unterscheiden

## 1. Kurzbeschreibung

qemu-system-x86_64 startet einen x86-64-Systememulator mit konfigurierten Geräten.

## 2. Was macht der Befehl?

Das Programm ist kein einfacher Bilddateibetrachter. Maschinenmodell, Beschleuniger, Disks und Netzgeräte sind eigenständige Konfigurationen. -display none unterdrückt nur Grafik und verhindert nicht Prozess-, Disk- oder Netzaktivität.

Quelle, am 2026-11-13 gelesen: [Gelesene Primärquelle](https://www.qemu.org/docs/master/system/invocation.html)

## 3. Syntax

```text
qemu-system-x86_64 [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| -machine TYP | Maschinenmodell |
| -accel TYP | Beschleunigung |
| -drive PARAMETER | Datenträger anbinden |
| -nic none | Standard-NIC unterbinden, kein vollständiger Netzschutz |
| -snapshot | Disk-Schreibumleitung, keine allgemeine Isolation |
| -version | Version ohne VM-Start |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
qemu-system-x86_64 -version
```

Nur dieser Versionsaufruf wurde gelesen. Kein Emulatorlauf und keine VM, KVM-, Grafik-, Geräte- oder Netzaktivierung.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Emulatorstart und Offline-Abbildbearbeitung unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Gastcode und angebundene Hostpfade können Wirkungen haben. Keine Boot- oder Installationsprobe mit realen Images.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Display fehlt | Keine Rechtfertigung für unkontrollierten Headlessstart |
| KVM fehlt | Keine Capability- oder Gerätereparatur zum Beispiel |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** QEMU 8.2.2; nur -version, VM-Betrieb offen. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| qemu-img | Offline-Abbildwerkzeug |
| virsh | Management |
| virt-install | Gastanlage |

Ausgangsdatensatz 698 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
