---
id: "yum"
name: "yum"
command: "yum"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "yum"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 476
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; yum fehlt"
---

# yum – Historisches Yum und aktuelle Kompatibilitätsnamen trennen

## 1. Kurzbeschreibung

yum ist historisch ein Repository- und Abhängigkeitsmanager für RPM-Pakete. Auf neueren Distributionen kann der Aufruf auf DNF-Technik verweisen. Die tatsächlich installierte Variante ist vor Optionsübernahme zu klären.

## 2. Was macht der Befehl?

Geprüft wurde die originale Yum-Manpage im Projektquellbaum. Die folgende Form beschreibt diese klassische Schnittstelle, nicht garantiert einen heutigen DNF5-Wrapper. Daten im Cache, verfügbare Repositoryversionen und installierte RPMs sind unterschiedliche Bestände. Plugins und Konfiguration können das Verhalten erweitern.

Quelle, am 2026-11-13 gelesen: [Yum-Projekt: originale yum-Manpage](https://raw.githubusercontent.com/rpm-software-management/yum/master/docs/yum.8)

## 3. Syntax

```text
yum [OPTIONEN] KOMMANDO [PAKETE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list`, `info`, `search` | Bestands-/Metadatenabfragen je Modus. |
| `-C`, `--cacheonly` | Nur vorhandene Cachedaten verwenden. |
| `check-update` | Aktualisierungen prüfen; Status 100 kann verfügbare Updates bedeuten. |
| `install`, `update`, `remove` | Pakettransaktionen. |
| `--assumeno` | Fragen verneinen, verhindert nicht jede vorherige Metadatenaktion. |
| `-y` | Fragen automatisch bejahen; keine Sicherheitsoption. |
| `clean` | Cacheinhalte löschen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
yum --cacheonly info lernpaket
```

Das erfundene Paket wird nicht abgefragt. Fehlende Cachedaten wären kein Beweis, dass das Paket grundsätzlich nicht existiert. Status 100 bei check-update darf in einem Skript nicht pauschal wie ein gewöhnlicher Fehler behandelt werden; diese Form wurde hier nicht ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Altanleitungen lesen:** Yum3 und DNF-Kompatibilität unterscheiden. **Wartungsberichte planen:** Rückgabestatus und Updateangebot getrennt vom ausgeführten Upgrade bewerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installation und Entfernung können RPM-Skripte und Dienste beeinflussen. Cachebereinigung ist schreibend. Keine alten Yum-Pakete installiert, Plugins gestartet, Quellen geändert oder Transaktionen ausgeführt; yum fehlt lokal.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Option unbekannt | Implementierung hinter yum prüfen. |
| check-update liefert 100 | Dokumentierter Updateindikator, nicht automatisch Transaktionsfehler. |
| Cache leer | Voraussetzung fehlt; kein ungefragter Metadatenrefresh. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; yum fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dnf` | Nachfolgende Technik mit eigener Versionssemantik. |
| `rpm` | Unterliegender Paketzugriff. |
| `zypper` | Andere RPM-Repositoryverwaltung. |

Ausgangsdatensatz 476 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
