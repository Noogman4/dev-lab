---
id: "gdb"
name: "gdb"
command: "gdb"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "gdb"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 274
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# gdb – Eigene Programme mit GNU GDB untersuchen

## 1. Kurzbeschreibung

GDB ist ein Debugger. Er liest Symbole, kann Programme starten und anhalten, Speicher ändern und Funktionen aufrufen. Er ist deshalb kein grundsätzlich passiver Analysebefehl.

## 2. Was macht der Befehl?

Debugdaten aus -g verbinden Maschinenadressen mit Quelltext. Hohe Optimierung kann Variablen und Abläufe verändern. break setzt einen Haltepunkt; run startet das Ziel wirklich. next geht über Funktionsaufrufe hinweg, step hinein; backtrace zeigt den Aufrufstapel. print ist nicht automatisch nebenwirkungsfrei: Ausdrücke können Funktionsaufrufe oder Zuweisungen enthalten. Attach an fremde laufende Prozesse ist keine Übung dieses Dokuments.

Quelle, am 2026-11-13 gelesen: [GDB-Modusoptionen](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Mode-Options.html), [Beispielsitzung](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Sample-Session.html), [Auto-load-Sicherheitsgrenze](https://sourceware.org/gdb/current/onlinedocs/gdb.html/Auto_002dloading-safe-path.html)

## 3. Syntax

```text
gdb [OPTIONEN] PROGRAMM
gdb [OPTIONEN] --args PROGRAMM ARGUMENTE...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-nx` | Initialisierungsdateien unterdrücken; -nh betrifft nur Heimverzeichnisdateien. |
| `-q` | Begrüßung unterdrücken. |
| `-batch` | Befehle ohne interaktiven Prompt ausführen; keine automatische Bestätigung durch einen Menschen. |
| `-ex BEFEHL` | Debuggerbefehl ausführen, mehrfach möglich. |
| `-iex "set auto-load no"` | Automatisches Laden früh deaktivieren. |
| `--args` | Nachfolgende Argumente dem Zielprogramm zuordnen. |
| `-return-child-result` | Rückgabestatus des Zielprozesses übernehmen, dokumentierte Ausnahmen beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-274-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'int main(void) { return 0; }
' > lernen.c
gcc -g -O0 lernen.c -o lernen
gdb -nx -q -batch -iex 'set auto-load no' -ex 'info functions main' ./lernen

```

### Schritt 3: Ergebnis auswerten

Erwartet wäre eine Symbolauflistung mit main und Quellbezug. Das Muster enthält absichtlich kein run und kein Attach. GDB fehlt lokal; auch die Symbolabfrage wurde nicht ausgeführt. Ein späterer Laufzeittest müsste ausdrücklich nur das eigene Programm betreffen. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Fehler verstehen: Haltepunkte und Stackframes mit eigenem Quelltext verbinden. Core-Dateien untersuchen: Nur vertrauenswürdige Daten verwenden und sensible Speicherinhalte schützen.

## 7. Risiken, Nebenwirkungen und Vorsicht

run und continue führen echte Programmaktionen aus; set und call können den Prozess verändern. Automatisch geladene Skripte sind ausführbarer Code. safe-path nicht pauschal auf / setzen. Core-Dateien können Passwörter und andere private Daten enthalten. Keine ptrace- oder Kernelregeln ändern. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| No debugging symbols | Mit -g neu in eigenem Ordner bauen. |
| Operation not permitted | Debuggerzugriff eingeschränkt; Schutz nicht umgehen. |
| Auto-loading declined | Sicherheitsgrenze beibehalten; Herkunft der Skripte prüfen. |
| Variable optimized out | Optimierung und Debugbau prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gcc` | Erzeugt Programme mit Debugdaten. |
| `lldb` | Alternativer Debugger mit anderer Befehlssprache. |
| `readelf` | Statische ELF-Sicht ohne Programmlauf. |

Ausgangsdatensatz 274 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
