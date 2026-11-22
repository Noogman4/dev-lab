---
id: "npm"
name: "npm"
command: "npm"
category: "Paketverwaltung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Paketverwaltung", "npm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 464
reviewed_at: "2026-11-13"
locally_checked_version: "npm 10.9.9"
---

# npm – Eigene package.json ohne Installation auslesen

## 1. Kurzbeschreibung

npm verwaltet JavaScript-Pakete und führt Projektskripte aus. npm pkg get liest gezielt lokale Manifestfelder. npm view fragt dagegen Registrymetadaten ab und ist nicht dieselbe Informationsquelle.

## 2. Was macht der Befehl?

package.json enthält Anforderungen und Skripte; ein Lockfile beschreibt die konkrete Auflösung. node_modules ist der tatsächliche lokale Installationsbestand. Die Übung erzeugt nur ein Manifest ohne Abhängigkeiten oder Skripte. Online-Dokumentation v11 und lokal ausgeführtes npm 10.9.9 sind getrennt benannt; die verwendete Form wurde lokal geprüft.

Quelle, am 2026-11-13 gelesen: [npm-Projekt: pkg](https://docs.npmjs.com/cli/v11/commands/npm-pkg/) und [Lifecycle-Skripte v10](https://docs.npmjs.com/cli/v10/using-npm/scripts/)

## 3. Syntax

```text
npm [OPTIONEN] KOMMANDO [ARGUMENTE]
npm pkg get FELD...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `pkg get` | Lokale Manifestfelder als JSON lesen. |
| `pkg set`, `pkg delete` | Manifest verändern. |
| `install` | Abhängigkeiten installieren; Lifecycle-Skripte möglich. |
| `ci` | Lock-basierte Installation; ersetzt bestehenden node_modules-Bestand. |
| `--offline` | Keine Netzabfrage; nicht automatisch schreibfrei. |
| `--ignore-scripts` | Automatische Skripte unterdrücken; explizite run-Befehle trotzdem beachten. |
| `audit`, `publish` | Netz-/Veröffentlichungsaktionen, nicht Teil der Übung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Abgegrenzte Übung vorbereiten

Voraussetzungen: Bash und die im Block genannten lokal vorhandenen Werkzeuge. Alle Schritte gehören in dieselbe Shell. Eigene Dateien werden ausschließlich in einem neuen privaten Temporärordner angelegt; bei Fehlern abbrechen. Kein Download und keine Installation.

### Schritt 2: Eigenes Beispiel ausführen

```bash
uebung="$(mktemp -d -t netmon-npm-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' '{"name":"lernpaket","version":"1.2.3","private":true}' > package.json
touch user.npmrc global.npmrc
npm --version
npm --offline --ignore-scripts --cache "$uebung/cache" --userconfig "$uebung/user.npmrc" --globalconfig "$uebung/global.npmrc" --no-audit --no-fund --update-notifier=false pkg get name version > bericht.json
cat bericht.json
```

### Schritt 3: Ergebnis einordnen

Der Bericht enthält name=lernpaket und version=1.2.3. Der JSON-Text wurde mit npm aus dem eigenen Manifest gelesen. Kein node_modules angelegt, keine Registry kontaktiert und kein Projektskript gestartet. Die Cacheauswahl begrenzt mögliche npm-Logdateien auf den Übungsordner. Die eigenen Übungsdaten bleiben zur Kontrolle erhalten.

## 6. Typische Anwendungsfälle

**Manifest verstehen:** Anforderungen, Lock und installierte Dateien getrennt beurteilen. **Skripte prüfen:** Lifecycle-Aktionen vor fremden Installationen lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Installation, ci, run, exec und publish haben unterschiedliche erhebliche Wirkungen. --ignore-scripts ist keine Sandbox für explizit gestarteten Code. Tokens und Registrykonfiguration können vertraulich sein. Keine Benutzerkonfiguration geändert und keine echten Projektdateien angefasst.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| ENOENT package.json | Im richtigen eigenen Projektordner arbeiten. |
| Manifestversion mit installierter Version verwechselt | Feld beschreibt das Projekt, nicht die gesamte Abhängigkeitsauflösung. |
| Offline-Paket fehlt | Kein Download freigegeben; Voraussetzung fehlt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Aufrufmodus, konkrete Datenquelle und Ergebnis zusammen lesen. Die Übung beweist ausschließlich den beschriebenen eigenen Testfall; daraus keine Freigabe für fremde Daten oder systemweite Änderungen ableiten.

**Prüfstand am 2026-11-13:** npm 10.9.9. Praktisch geprüft: Eigene package.json mit pkg get offline gelesen; JSON-Felder geprüft. Installation, Lifecycle-Skripte, Registry, Audit, Workspaces und Veröffentlichung praktisch offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `node` | JavaScript-Laufzeit. |
| `pnpm` | Anderes Installationsmodell. |
| `yarn` | Andere CLI-/Lockfilevarianten. |

Ausgangsdatensatz 464 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
