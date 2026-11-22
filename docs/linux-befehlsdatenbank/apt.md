---
id: "apt"
name: "apt"
command: "apt"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "apt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 450
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt"
---

# apt – Interaktive Paketverwaltung mit klaren Änderungsgrenzen

## 1. Kurzbeschreibung

apt ist die benutzerorientierte Oberfläche des APT-Systems. Such-/Anzeigeformen unterscheiden sich von update, Installation und Entfernung. Die Oberfläche ist primär für Menschen gedacht.

## 2. Was macht der Befehl?

update aktualisiert Paketinformationen, nicht die installierten Programme. upgrade kann in apt neue Abhängigkeiten hinzufügen, entfernt aber bestehende Pakete nicht; full-upgrade kann zur Auflösung auch entfernen. Das unterscheidet sich von einzelnen apt-get-Vorgaben. Repositoryangebot, Installationsstatus und Kandidatenversion sind getrennt zu lesen.

Quelle, am 2026-11-13 gelesen: [APT-Team: apt-Handbuch](https://manpages.debian.org/trixie/apt/apt.8.en.html)

## 3. Syntax

```text
apt [OPTIONEN] {search|show|list} [PAKET]
apt [OPTIONEN] {install|remove|purge|upgrade|full-upgrade} [PAKETE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `search` | In Paketmetadaten suchen. |
| `show` | Paketbeschreibung und Abhängigkeiten anzeigen. |
| `list --installed` | Installierte Paketnamen auflisten. |
| `update` | Indizes herunterladen und speichern. |
| `install`, `remove` | Paketbestand ändern. |
| `purge` | Zusätzlich verwaltete Konfigurationsreste entfernen; kein Löschen sämtlicher Benutzerdaten. |
| `autoremove` | Als nicht mehr benötigte automatische Abhängigkeiten eingestufte Pakete entfernen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
apt show lernpaket
```

Das erfundene Paket wird nicht abgefragt. show ist eine Metadatenanzeige, kein Nachweis einer lokalen Installation oder eines laufenden Dienstes. Mehrere Versionen und Quellen erfordern eine genaue Zuordnung.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Paketwahl verstehen:** Beschreibung, Herkunft und Abhängigkeiten lesen. **Wartung planen:** Update der Indizes und Upgrade der Software getrennt freigeben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installationen und Entfernungen können Skripte und Dienstaktionen auslösen. Eine autoremove-Liste muss fachlich geprüft werden. Für Skripte empfiehlt das Projekt spezialisierte apt-get/apt-cache-Schnittstellen. Keine Paketlisten, Quellen, Markierungen oder Installationen verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Paket unbekannt | Metadatenstand und Name offen; nicht automatisch Quellen hinzufügen. |
| Full-upgrade entfernt Pakete | Möglicher Teil der Auflösung, vor Ausführung prüfen. |
| Ausgabeformat in Skript geändert | apt ist eine Endnutzeroberfläche, keine zugesicherte Text-API. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine ausgeführte Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `apt-cache` | Spezialisierte Metadatenabfragen. |
| `apt-get` | Spezialisierte Transaktionsoberfläche. |
| `dpkg-query` | Installationsdatenbank statt Repositoryangebot. |

Ausgangsdatensatz 450 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
