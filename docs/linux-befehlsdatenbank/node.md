---
id: "node"
name: "node"
command: "node"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "node"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 290
reviewed_at: "2026-11-13"
locally_checked_version: "Node.js v22.23.3"
---

# node – JavaScript mit Node.js prüfen und starten

## 1. Kurzbeschreibung

node führt JavaScript außerhalb des Browsers aus. Node.js stellt unter anderem Datei-, Prozess- und Netzwerkschnittstellen bereit. Es ist deshalb kein bloßer Textbetrachter und keine Browser-Sandbox.

## 2. Was macht der Befehl?

Der Einstieg kann eine Skriptdatei, Standardinput oder ein Ausdruck sein. .cjs legt CommonJS fest, .mjs ECMAScript-Module; bei .js beeinflussen Paketkontext und Version die Interpretation. Nodeoptionen stehen vor dem Skript, Argumente danach erhält die Anwendung. --check prüft die Syntax ohne normalen Programmlauf; es beweist keine richtigen Imports oder Laufzeitlogik. node und npm sind getrennte Programme.

Quelle, am 2026-11-13 gelesen: [Node.js-Aufrufhandbuch](https://nodejs.org/api/cli.html); die aktuelle Webfassung beschreibt eine neuere Hauptversion als der lokale Test. Die Version-22-spezifische URL war nicht erreichbar; lokale Nachweise gelten nur für die ausgeführten Optionen

## 3. Syntax

```text
node [OPTIONEN] [SKRIPT [ARGUMENTE...]]
node -e AUSDRUCK
node --check SKRIPT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--version` | Laufzeitversion anzeigen. |
| `--check` / `-c` | Skript syntaktisch prüfen, ohne seinen normalen Inhalt auszuführen. |
| `-e CODE` | Code sofort ausführen. |
| `-p CODE` | Ausführen und Ergebnis ausgeben; nicht nur Text anzeigen. |
| `--input-type=module` | Modus für String-/Standardinputquellen wählen. |
| `--require MODUL`, `--import MODUL` | Module vorladen; echte Codeausführung. |
| `--inspect` | Debuggerzugang öffnen; hier nicht verwenden. |
| `--test` | Testcode tatsächlich ausführen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-290-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
env -u NODE_OPTIONS node --version
printf 'console.log("Hallo Node", 6 * 7);
' > lernen.cjs
env -u NODE_OPTIONS NODE_DISABLE_COMPILE_CACHE=1 node --check lernen.cjs
env -u NODE_OPTIONS NODE_DISABLE_COMPILE_CACHE=1 node lernen.cjs

```

### Schritt 3: Ergebnis auswerten

Die Syntaxprüfung blieb ohne Fehlermeldung und endete mit Status 0. Der separate Start gab Hallo Node 42 aus. Das eigene .cjs verwendet keine Imports, Pakete oder Netzschnittstellen. NODE_OPTIONS wird für die Aufrufe entfernt; der Compilecache wird pro Prozess deaktiviert. Es wurden keine Benutzereinstellungen geändert. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Kleine Skripte ausführen: Syntaxkontrolle und tatsächlichen Test trennen. Modulfehler verstehen: Dateiendung, Paketkontext und unterstützte Node-Version vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Fremde Skripte, vorab geladene Module und native Addons können beliebige Aktionen ausführen. --check ist keine allgemeine Isolierung gegen veränderte Laufzeitoptionen. Inspector nicht auf öffentliche Adressen binden. Paketinstallation und npm-Skripte sind nicht Teil der Übung. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Cannot find module | Pfad, Modulmodus und Abhängigkeiten prüfen. |
| require/import passt nicht | CommonJS und ESM unterscheiden. |
| Skriptargument als Nodeoption | Argumentposition beachten. |
| Syntaxprüfung erfolgreich, Laufzeitfehler | Imports und tatsächlich ausgeführte Pfade sind eigene Prüfungen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Node.js v22.23.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `npm` | Paketverwaltung mit eigenen Skript-/Netzrisiken. |
| `python3` | Andere Skriptlaufzeit. |
| `node --help` | Optionen der installierten Version lesen. |

Ausgangsdatensatz 290 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
