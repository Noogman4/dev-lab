---
id: "systemd_sysusers"
name: "systemd-sysusers"
command: "systemd-sysusers"
category: "Systemd & Dienste"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Systemd & Dienste", "systemd-sysusers"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 577
reviewed_at: "2026-11-13"
locally_checked_version: "Programm vorhanden; keine Kontenregeln ausgeführt"
---

# systemd-sysusers – Systemkonten aus Sysusers-Regeln anlegen

## 1. Kurzbeschreibung

systemd-sysusers legt Systembenutzer und Gruppen nach Konfigurationsregeln an.

## 2. Was macht der Befehl?

Der normale Aufruf ist eine Kontenänderung, keine Bestandsliste. Ohne Dateiauswahl werden die vorgesehenen Konfigurationsverzeichnisse ausgewertet. Ein absoluter Dateipfad wählt eine konkrete Konfiguration. --cat-config zeigt Text; --dry-run beschreibt beabsichtigte Änderungen, ersetzt aber keine Rechte- und Identitätsprüfung.

Quelle, am 2026-11-13 gelesen: [Systemd: sysusers-Werkzeug](https://man7.org/linux/man-pages/man8/systemd-sysusers.8.html), [Regelformat sysusers.d](https://man7.org/linux/man-pages/man5/sysusers.d.5.html); lokale Hilfe gelesen

## 3. Syntax

```text
systemd-sysusers [OPTIONEN] [KONFIGURATION ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| --cat-config | Ausgewählte Konfiguration ausgeben, nicht anwenden. |
| --dry-run | Geplante Kontenanlegung anzeigen; Version prüfen. |
| --root=PFAD | Andere Wurzel verwenden; kein allgemeiner Sandboxersatz. |
| --inline | Argumente als Konfigurationszeilen verstehen. |
| --no-pager | Pager vermeiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
systemd-sysusers --cat-config /ABSOLUTER/EIGENER/PFAD/lesson.conf
```

Das Muster würde nur die ausgewählte Konfigurationsdatei anzeigen. Es wurde nicht ausgeführt. Die Quelle definiert Regeltypen für Benutzer und Gruppen; hier wurden bewusst keine realen Kontonamen angelegt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

Paketregeln zur Systemkontenanlegung lesen; Dateiauswahl vor einem späteren administrativen Ablauf prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

UID/GID-Zuordnung betrifft Dateieigentum und Dienste. Eine fremde Root-Wurzel oder unbekannte Regeldatei nicht anwenden. Keine Kontendateien, NSS-Konfiguration oder Gruppenmitgliedschaften verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Konto existiert schon | Idempotentes Regelverhalten und tatsächliche Identität prüfen. |
| Unexpected rules | Suchpfadprioritäten und konkrete Dateiauswahl prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Programm vorhanden; keine Kontenregeln ausgeführt. Nicht praktisch geprüft; praktische Prüfung offen. Erklärungsmuster und echte Betriebs-/Änderungsfälle nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| getent | NSS-Kontenabfrage, eigener Geltungsbereich. |
| useradd | Andere Kontenverwaltung. |
| systemd-tmpfiles | Dateiregeln statt Kontenanlegung. |

Ausgangsdatensatz 577 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
