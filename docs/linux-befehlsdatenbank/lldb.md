---
id: "lldb"
name: "lldb"
command: "lldb"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "lldb"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 285
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# lldb – Eigene Programme mit LLDB untersuchen

## 1. Kurzbeschreibung

LLDB ist der Debugger des LLVM-Projekts. Er kann Symbole lesen, Prozesse starten oder übernehmen und deren Zustand verändern. Seine Befehle sind nicht durchgehend mit GDB austauschbar.

## 2. Was macht der Befehl?

LLDB verwendet häufig die Form Hauptwort Aktion, etwa breakpoint set und thread backtrace. Ein angelegtes Target ist noch kein gestarteter Prozess. process launch führt das Programm tatsächlich aus, process continue setzt es fort. frame variable liest lokale Variablen, während expression auch Codeausführung und Zustandsänderungen ermöglichen kann. Debugdaten und passende Architektur erleichtern die Zuordnung zu Quellzeilen.

Quelle, am 2026-11-13 gelesen: [LLDB-Aufrufhandbuch](https://lldb.llvm.org/man/lldb.html) und [LLDB-Tutorial](https://lldb.llvm.org/use/tutorial.html)

## 3. Syntax

```text
lldb [OPTIONEN] PROGRAMM [-- PROGRAMMARGUMENTE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--no-lldbinit` / `-x` | Automatische Initialisierungsdateien nicht ausführen. |
| `--batch` / `-b` | Angegebene Befehle abarbeiten und beenden. |
| `--one-line BEFEHL` / `-o` | Befehl nach dem Laden der Datei ausführen. |
| `--one-line-before-file BEFEHL` / `-O` | Befehl vor dem Laden ausführen. |
| `--core DATEI` | Core-Datei öffnen; kann vertrauliche Speicherinhalte enthalten. |
| `--attach-pid PID` | An laufenden Prozess hängen; hier nicht vorgesehen. |
| `--version` | Installierten Debuggerstand anzeigen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-285-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'int main(void) { return 0; }
' > lernen.c
gcc -g -O0 lernen.c -o lernen
lldb --no-lldbinit --batch -o 'image lookup -n main' ./lernen

```

### Schritt 3: Ergebnis auswerten

Erwartet wäre eine Symbolsuche nach main im eigenen Programm; es gibt keinen process-launch- oder Attach-Aufruf. LLDB fehlt lokal, daher ist selbst diese statische Symbolabfrage praktisch offen. Eine GDB-Prüfung wäre kein Ersatz für dieses Werkzeug. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Eigene Fehler nachvollziehen: Haltepunkte und Stackframes untersuchen. Toolchainvergleich: Debugformat und Architektur mit Compiler und Debugger abgleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Debuggerbefehle, Python-Skripte, Formatter und automatisch geladene Erweiterungen können Code ausführen. --no-lldbinit ist kein vollständiger Schutz gegen jede Erweiterung oder einen unsicheren Parser. Fremde Prozesse, Dienste und Systemregeln werden nicht geändert. Keine Schutzregel für Debuggerzugriff umgehen. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Target passt nicht | Architektur und Binärformat prüfen. |
| Breakpoint ohne Treffer | Symbolname, Debugdaten und geladenes Modul prüfen. |
| Launch nicht erlaubt | Sandbox-/ptrace-Grenzen belassen. |
| GDB-Befehl unbekannt | LLDB-Hilfe und vollständige Befehlsform verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gdb` | Alternativer Debugger. |
| `clang` | Compiler aus LLVM. |
| `readelf` | Statische Metadatenansicht. |

Ausgangsdatensatz 285 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
