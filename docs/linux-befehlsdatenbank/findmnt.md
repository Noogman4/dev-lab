---
id: "findmnt"
name: "findmnt"
command: "findmnt"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Datentraeger & Dateisysteme", "findmnt"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 219
reviewed_at: "2026-11-13"
locally_checked_version: "findmnt from util-linux 2.39.3"
---

# findmnt – Mountinformationen und Konfigurationspläne getrennt lesen

## 1. Kurzbeschreibung

`findmnt` sucht in Mounttabellen und zeigt Dateisystembeziehungen an. Das Programm hängt nichts ein. Gewöhnliche Auskünfte und die eigene Testtabelle benötigen kein Root.

## 2. Was macht der Befehl?

Die Kernelansicht beschreibt aktive Mounts im betrachteten Mount-Namespace. Eine fstab-Ansicht beschreibt dagegen Konfiguration, die nicht aktiv sein muss. `--target` kann den umgebenden Mount für eine beliebige Datei finden; `--mountpoint` verlangt den genauen Einhängepunkt. Ein einzelner Quellname muss nicht genau einem physischen Gerät entsprechen. Standardspalten können sich ändern; Skripte sollen ihre Spalten auswählen.

Quelle, am 2026-11-13 gelesen: [findmnt-Handbuch](https://manpages.debian.org/trixie/util-linux/findmnt.8.en.html) und lokale Manpage 2.39.3

## 3. Syntax

```text
findmnt [OPTIONEN]
findmnt --target PFAD
findmnt --fstab --tab-file DATEI [OPTIONEN]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--fstab` | Konfiguration statt Kernel-Mounttabelle lesen. |
| `--tab-file DATEI` | Alternative Tabelle wählen; ohne dies würde eine Systemdatei gelesen. |
| `--source`, `--target`, `--mountpoint` | Suchrichtung ausdrücklich festlegen; keine Mountaktionen. |
| `--output LISTE` | Spalten wählen; Namen in der lokalen Hilfe prüfen. |
| `--json`, `--raw`, `--noheadings` | Ausgabeformat wählen; rohe Werte können Escape-Sequenzen enthalten. |
| `--evaluate` | Tags zu Geräten auflösen; nicht für das isolierte Muster verwenden. |
| `--poll`, `--timeout` | Mountänderungen beobachten und Wartezeit begrenzen. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und util-linux. Es wird nur eine eigene Texttabelle gelesen, keine reale Quelle aufgelöst.

### Schritt 1: Eigene fstab-Zeile schreiben und anzeigen

```bash
uebung="$(mktemp -d -t netmon-findmnt-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' 'LERNQUELLE /lernziel ext4 ro 0 0' > fstab.test
findmnt --fstab --tab-file "$uebung/fstab.test" --nocanonicalize --noheadings --raw --output SOURCE,TARGET,FSTYPE,OPTIONS
```

### Schritt 2: Ausgabe zuordnen

Erwartet ist `LERNQUELLE /lernziel ext4 ro`. SOURCE ist die frei erfundene Quelle, TARGET ein geplanter Pfad, FSTYPE ein deklarierter Typ und OPTIONS die Textoption `ro`. Es wird weder `/lernziel` angelegt noch etwas gemountet.

### Schritt 3: Schlussfolgerung begrenzen

Diese Ausgabe bestätigt nur die Interpretation der Testtabelle. Sie beweist weder Existenz der Quelle noch Dateisystemtyp oder aktive Schreibschutzwirkung. Ohne `--evaluate` werden die Platzhalter nicht zu Geräten aufgelöst.

## 6. Typische Anwendungsfälle

**Konfiguration vergleichen:** Geplanten und aktiven Mountzustand unterscheiden. **Pfadzuordnung:** Bei später autorisierter Diagnose den zu einer Datei gehörenden Mount suchen. **Berichte:** Bewusst ausgewählte Spalten exportieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Tabellen können vertrauliche Pfade enthalten. Tags auswerten oder Kernelzustände beobachten erweitert den gelesenen Bereich. Eine syntaktisch lesbare fstab-Zeile ist keine Freigabe zum Mounten. Andere Namespaces können andere Ergebnisse sehen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein Treffer, Status 1 | Filter passt nicht oder Tabelle/Pfad fehlt; nicht automatisch defektes Dateisystem. |
| Pfad ist kein eigener Mount | `--target` fand den übergeordneten Mount; für exakten Test --mountpoint verwenden. |
| Konfiguration und Kernel widersprechen sich | Geplanten und aktiven Zustand getrennt dokumentieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einer eigenen Tabelle, expliziten Spalten und ohne Tagauflösung beginnen. Roh- oder JSON-Ausgaben als Daten behandeln, nicht mit eval ausführen.

**Prüfstand am 2026-11-13:** findmnt from util-linux 2.39.3. Praktisch geprüft: Eigene alternative fstab-Tabelle vollständig wie im Beispiel gelesen. Nicht praktisch geprüft: echte Mountsuche, Tagauflösung, Polling und fremde Namespaces. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mountpoint` | Prüft einen bestimmten Mountpunkt. |
| `mount` | Führt echte Einhängungen aus. |
| `lsblk` | Andere Sicht auf Geräteschichten. |

Ausgangsdatensatz 219 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
