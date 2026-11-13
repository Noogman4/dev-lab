---
id: "dnf"
name: "dnf"
command: "dnf"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "dnf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 456
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; dnf fehlt"
---

# dnf – DNF-Version und Transaktionsumfang klären

## 1. Kurzbeschreibung

dnf löst Pakettransaktionen in RPM-basierten Distributionen. Hier wird die DNF4-Schnittstelle des gelesenen Handbuchs beschrieben. DNF5 kann unter demselben Aufrufnamen installiert sein und abweichende Optionen besitzen.

## 2. Was macht der Befehl?

Repository-Metadaten, installierte RPMs und Transaktionshistorie sind verschiedene Informationsquellen. Eine Abhängigkeitslösung kann weitere Pakete einbeziehen. Ein History-Eintrag ist kein vollständiges Systembackup; ein späterer Undo kann an fehlenden Versionen oder verändertem Bestand scheitern.

Quelle, am 2026-11-13 gelesen: [DNF-Projekt: DNF4-Kommandoreferenz](https://dnf.readthedocs.io/en/latest/command_ref.html)

## 3. Syntax

```text
dnf [OPTIONEN] KOMMANDO [PAKETE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `info`, `list` | Metadaten oder Bestand anzeigen; Cacheaktualisierung möglich. |
| `--cacheonly`, `-C` | Nur vorhandenen Cache nutzen; versionsabhängiger Umfang. |
| `--assumeno` | Fragen verneinen; Metadatenzugriffe dadurch nicht verhindert. |
| `install`, `upgrade`, `remove` | Paketbestand ändern. |
| `--downloadonly` | Pakete herunterladen, kein reiner Lesemodus. |
| `history` | Transaktionen anzeigen oder Unteraktionen ausführen; Modus genau lesen. |
| `--allowerasing` | Entfernungen zur Auflösung zulassen; keine allgemeine Fehlerbehebung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
dnf --cacheonly info lernpaket
```

Der erfundene Name wird nicht abgefragt. Ohne passenden Cache könnte die Information fehlen, obwohl ein Repository das Paket anbietet. Die Form soll Metadaten erklären, nicht eine Installation freigeben.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**RPM-Wartung vorbereiten:** Version, Quellen und geplante Paketmenge festhalten. **Diagnose verstehen:** Installierter Bestand und Repositoryangebot trennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Transaktionen können RPM-Skripte und Dienstaktionen ausführen. Downloads, Plugins und Metadaten können auch vor einer Bestätigung wirken. Keine Datenbank initialisiert, kein Cache aktualisiert und keine Transaktion ausgeführt. DNF ist lokal nicht vorhanden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| DNF4-Option unbekannt | DNF5/Distributionsvariante prüfen. |
| Keine Cachedaten | Offline-Voraussetzung fehlt; nicht automatisch refresh ausführen. |
| Undo scheitert | Historie ersetzt keine verfügbaren Pakete oder Sicherung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; dnf fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `rpm` | Unterliegender Paket-/Datenbankzugriff. |
| `yum` | Historischer oder kompatibler Aufruf. |
| `zypper` | Anderer RPM-Resolver. |

Ausgangsdatensatz 456 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
