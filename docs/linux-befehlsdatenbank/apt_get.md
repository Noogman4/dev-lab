---
id: "apt_get"
name: "apt-get"
command: "apt-get"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "apt-get"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 452
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# apt-get – Transaktionsplanung von Installation unterscheiden

## 1. Kurzbeschreibung

apt-get ist eine spezialisierte APT-Oberfläche. Es löst Abhängigkeiten und kann Pakete herunterladen, installieren oder entfernen. Eine Simulation beschreibt nur einen Plan auf Basis des aktuellen Stands.

## 2. Was macht der Befehl?

update lädt Indizes. upgrade installiert bei apt-get standardmäßig keine neuen Pakete und entfernt keine; dist-upgrade darf Abhängigkeiten umfassender auflösen und Pakete entfernen. remove und purge unterscheiden sich bei verwalteten Konfigurationsresten. Eine normale Transaktion kann Maintainerskripte und damit Dienstaktionen auslösen.

Quelle, am 2026-11-13 gelesen: [APT-Team: apt-get-Handbuch](https://manpages.debian.org/trixie/apt/apt-get.8.en.html)

## 3. Syntax

```text
apt-get [OPTIONEN] KOMMANDO [PAKETE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-s`, `--simulate` | Geplante Aktionen anzeigen; keine Installation. |
| `--no-download` | Downloads vermeiden, aber vorhandene Pakete können weiterhin installiert werden. |
| `-d`, `--download-only` | Nur herunterladen; schreibt Cache, ist nicht offline. |
| `-y` | Bestätigungen automatisch beantworten; keine Sicherheitserhöhung. |
| `install`, `remove`, `purge` | Paketbestand und gegebenenfalls Konfiguration ändern. |
| `check` | Abhängigkeiten prüfen; kein vollständiger Funktionstest. |
| `clean`, `autoremove` | Cachedaten beziehungsweise Pakete entfernen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
apt-get --simulate install lernpaket
```

Der erfundene Name ist nur Syntaxmaterial. In einer echten Vorschau wären Inst-, Conf- und Remv-Aktionen zu lesen. Nicht privilegierte Simulation kann wegen fehlender Konfigurationssicht anders ausfallen und sperrt die Datenbank nicht wie eine echte Transaktion. Das Muster wurde nicht ausgeführt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Wartung vorbereiten:** Abhängigkeitsänderungen und Entfernungen vollständig prüfen. **Automatisierung verstehen:** Vorschau, Download und Installation als getrennte Wirkungen behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Sicherheit aus --no-download oder -y ableiten. Simulation verhindert die Paketänderung dieser geplanten Aktion, ersetzt aber keine isolierte Ausführung fremder Konfiguration oder Hooks. Kein Download, keine Simulation am echten Bestand, keine Installation oder Entfernung vorgenommen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Lock belegt | Anderen Paketprozess nicht beenden und Sperrdatei nicht löschen. |
| Unmet dependencies | Ursache prüfen statt ungefragt --fix-broken auszuführen. |
| Plan ändert sich später | Metadaten und Paketbestand können zwischen Planung und Ausführung driften. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt-cache` | Kandidaten und Metadaten erklären. |
| `dpkg` | Unterliegende Paketverwaltung. |
| `apt` | Interaktive Oberfläche mit teils anderen Vorgaben. |

Ausgangsdatensatz 452 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
