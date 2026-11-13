---
id: "pnpm"
name: "pnpm"
command: "pnpm"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "pnpm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 471
reviewed_at: "2026-11-13"
locally_checked_version: "pnpm 11.25.0"
---

# pnpm – Ein eigenes Projekt ohne Abhängigkeiten anzeigen

## 1. Kurzbeschreibung

pnpm verwaltet JavaScript-Projekte mit eigenem Store-/Verlinkungsmodell. list zeigt einen Abhängigkeitsbestand; es ist vom installierenden Standardaufruf und von einem Lockfilebericht zu unterscheiden.

## 2. Was macht der Befehl?

package.json formuliert Anforderungen, pnpm-lock.yaml hält Auflösung fest und node_modules bildet die konkrete Installation ab. Storeobjekte können mehreren Projekten dienen. Die aktuelle Website enthält Funktionen ab v12.7.0; lokal geprüft wurde 11.25.0. Das Beispiel beschränkt sich auf ein eigenes Manifest ohne Hooks oder Abhängigkeiten.

Quelle, am 2026-11-13 gelesen: [pnpm: list](https://pnpm.io/cli/list) und [install](https://pnpm.io/cli/install)

## 3. Syntax

```text
pnpm KOMMANDO [OPTIONEN]
pnpm list [MUSTER...] [--depth TIEFE] [--json]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `list --depth -1` | Nur Projektangaben, keine Abhängigkeitsbaumtiefe. |
| `--json` | Strukturierte Ergebnisdarstellung. |
| `-r`, `--filter` | Mehrere Workspaceprojekte auswählen; Umfang vorab klären. |
| `install --offline` | Nur vorhandenen Store verwenden; weiterhin Installation. |
| `--prefer-offline` | Fehlendes darf trotzdem geladen werden. |
| `--frozen-lockfile` | Installationsauflösung darf Lockfile nicht verändern. |
| `--ignore-pnpmfile` | Installationsoption zur Hooksteuerung; list lehnt sie lokal als CLI-Option ab. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-pnpm-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' '{"name":"lernpaket","version":"1.0.0","private":true}' > package.json
pnpm --version
XDG_CONFIG_HOME="$uebung/config" XDG_CACHE_HOME="$uebung/cache" npm_config_offline=true npm_config_ignore_pnpmfile=true pnpm list --depth -1 --json > bericht.json
cat bericht.json
```

### Schritt 3: Ergebnis einordnen

Der JSON-Bericht enthält das eigene Projekt lernpaket. Da keinerlei Abhängigkeiten installiert werden, prüft dies nur die Projektanzeige, nicht Storeverlinkung oder vollständige Resolverfunktion. Die XDG-Pfade sind nur für diesen einen Prozess auf den Übungsordner begrenzt. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Projektberichte verstehen:** Installationsbaum und Lockauflösung getrennt lesen. **Workspaceaktionen planen:** Zielmenge vor rekursiven Befehlen benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installationen und Skripte können Code ausführen; die jeweiligen Versionsregeln zur Skriptfreigabe müssen geprüft werden. Offline ist kein Schreibschutz. Storebereinigung kann mehrere Projekte betreffen. Kein Installations-, Update- oder Cleanupmodus ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Paket offline nicht vorhanden | Storevoraussetzung fehlt; keine automatische Netzfreigabe. |
| Lockfile nicht passend | Frozen-Modus stoppt bewusst; keine ungefragte Neugenerierung. |
| Zu viele Projekte betroffen | Rekursions-/Filterauswahl prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** pnpm 11.25.0. Praktisch geprüft: Eigene Projektanzeige ohne Abhängigkeiten offline ausgeführt. Storeverlinkung, Installationsskripte, Registry, Workspaces und aktuelle v12-Funktionen praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `npm` | Andere CLI und Installationsstruktur. |
| `yarn` | Weitere Lock-/Linkermodelle. |
| `node` | Laufzeit ausgeführter JavaScript-Programme. |

Ausgangsdatensatz 471 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
