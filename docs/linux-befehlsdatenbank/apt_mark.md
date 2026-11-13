---
id: "apt_mark"
name: "apt-mark"
command: "apt-mark"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "apt-mark"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 453
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# apt-mark – Paketmarkierungen und ihre späteren Folgen

## 1. Kurzbeschreibung

apt-mark zeigt und ändert APT-Markierungen sowie dpkg-Auswahlzustände. Eine Markierung installiert nicht unmittelbar ein Paket, kann aber spätere Upgrade- oder Entfernungsentscheidungen beeinflussen.

## 2. Was macht der Befehl?

auto/manual beschreibt den Installationsgrund. Automatische Pakete ohne benötigenden manuellen Verbraucher können für autoremove vorgeschlagen werden. hold/unhold betrifft dagegen das Zurückhalten von Paketänderungen. manual ist deshalb kein Update-Hold und hold kein Ersatz für eine dokumentierte Versionsstrategie.

Quelle, am 2026-11-13 gelesen: [APT-Team: apt-mark-Handbuch](https://manpages.debian.org/trixie/apt/apt-mark.8.en.html)

## 3. Syntax

```text
apt-mark {showauto|showmanual|showhold} [PAKET...]
apt-mark {auto|manual|hold|unhold} PAKET...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `showauto`, `showmanual` | Markierungen anzeigen. |
| `auto`, `manual` | Installationsgrund ändern. |
| `showhold` | Zurückgehaltene Auswahl anzeigen. |
| `hold`, `unhold` | Paketänderungen zurückhalten beziehungsweise freigeben. |
| `install`, `remove`, `purge` | Auswahl für spätere Umsetzung durch passende Frontends setzen. |
| `-f DATEI` | Alternative Statistikdatei; gilt nicht pauschal für alle dpkg-Auswahlpfade. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
apt-mark showhold lernpaket
```

Das erfundene Paket wird nicht abgefragt. Eine leere Ausgabe kann bedeuten, dass es nicht auf hold steht; sie beweist keine verfügbare oder kompatible Aktualisierung. showhold und hold dürfen nicht verwechselt werden.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Wartung erklären:** Installationsgrund von Update-Sperre unterscheiden. **Bestandsplanung:** Vorgeschlagene Entfernungen im Kontext manueller Paketwünsche bewerten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein versehentliches auto kann spätere Entfernung begünstigen; ein vergessenes hold kann Sicherheitsupdates verhindern. Auswahländerungen sind echte Verwaltungsänderungen auch ohne sofortige Installation. Keine Markierungen oder dpkg-Auswahlzustände geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Paket bleibt bei Upgrade alt | Hold ist nur eine mögliche Ursache; Kandidat und Abhängigkeiten prüfen. |
| manual verhindert kein Update | Das ist kein Hold-Modus. |
| Andere Datei angegeben, Hostzustand betroffen | Optionsumfang beachten; -f isoliert nicht jede Funktion. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt-get` | Setzt Pakettransaktionen um. |
| `apt-cache policy` | Kandidaten erklären. |
| `dpkg --get-selections` | Auswahlzustände getrennt von Installationsgründen. |

Ausgangsdatensatz 453 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
