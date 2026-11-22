---
id: "as"
name: "as"
command: "as"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "as"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 268
reviewed_at: "2026-11-13"
locally_checked_version: "GNU as / Binutils 2.42, Target x86_64-linux-gnu"
---

# as – Assemblertext in eine Objektdatei übersetzen

## 1. Kurzbeschreibung

GNU as übersetzt zielarchitekturspezifischen Assemblertext in Objektdateien. Es ist weder ein C-Compiler noch ein vollständiger Programmlinker. Die erzeugte .o-Datei wird hier nicht ausgeführt.

## 2. Was macht der Befehl?

Der Assembler ordnet Anweisungen und Direktiven einem konkreten Binärformat zu. Symbole und Relokationen erlauben einem späteren Linker, Adressen zu verbinden. Sprache und zulässige Maschinenoptionen hängen vom konfigurierten Target ab. GNU-as-Syntax ist nicht automatisch mit NASM oder anderen Assemblern austauschbar. Die Übung verwendet absichtlich nur eine Datendirektive und keinen Maschinenbefehl.

Quelle, am 2026-11-13 gelesen: [GNU-as-Überblick](https://sourceware.org/binutils/docs/as/Overview.html), [Aufrufoptionen](https://sourceware.org/binutils/docs/as/Invoking.html)

## 3. Syntax

```text
as [OPTIONEN] -o OBJEKT QUELLE.s
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-o DATEI` | Ausgabe benennen; sonst gewöhnlich a.out, trotz Objektinhalt. |
| `-g` | Debuginformation erzeugen, Format/Target beachten. |
| `-I ORDNER` | Suchpfad für .include, nicht für C-Header. |
| `--fatal-warnings` | Warnungen als Fehler behandeln. |
| `--32`, `--64` | Auf x86 Ausgabeart wählen; keine allgemeine Crosscompilerinstallation. |
| `--version`, `--target-help` | Implementierung/Target beziehungsweise Maschinenoptionen lesen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-268-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
as --version
printf '.section .data
.globl lernwert
lernwert:
.long 42
' > wert.s
as --fatal-warnings -o wert.o wert.s
readelf -s wert.o

```

### Schritt 3: Ergebnis auswerten

Die Symboltabelle enthält lernwert. .long legt hier den Datenwert 42 ab; die Objektdatei besitzt keinen lauffähigen Programmeinstieg. readelf liest sie nur. Der Test lief mit Target x86_64-linux-gnu; andere Syntaxfamilien und Maschinenbefehle sind nicht geprüft. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Objektformat lernen: Symbole und Sektionen an eigenem Minimaltext untersuchen. Compilerabläufe verstehen: Assemblerstufe von Kompilierung und Linken unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Assemblieren schreibt Binärdateien und kann Includes aus zusätzlichen Pfaden lesen. Fremde Quellen und Antwortdateien nicht blind verarbeiten. Eine fehlerfrei übersetzte Instruktion ist keine Aussage über ihr Laufzeitverhalten. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Unknown instruction | Syntax oder Architektur passt nicht zum Assembler. |
| Undefined reference beim späteren Linken | Assemblieren und Auflösen externer Symbole sind verschiedene Stufen. |
| Objekt lässt sich nicht starten | Eine Objektdatei ist kein fertiges Programm. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU as / Binutils 2.42, Target x86_64-linux-gnu. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ld` | Verbindet Objektdateien. |
| `readelf` | Liest ELF-Strukturen. |
| `gcc -S` | Erzeugt Assemblertext aus C. |

Ausgangsdatensatz 268 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
