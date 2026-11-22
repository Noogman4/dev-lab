---
id: "objdump"
name: "objdump"
command: "objdump"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Entwicklung", "objdump"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 291
reviewed_at: "2026-11-13"
locally_checked_version: "GNU objdump / Binutils 2.42; gcc 13.3.0"
---

# objdump – Binärstrukturen und Maschinenbefehle statisch lesen

## 1. Kurzbeschreibung

GNU objdump zeigt Strukturen unterstützter Objektformate und kann Maschinenbefehle disassemblieren. Es startet das untersuchte Programm nicht. Zum sinnvollen Aufruf gehört eine ausdrückliche Auswahl der gewünschten Ansicht.

## 2. Was macht der Befehl?

-h zeigt Sektionen, -t Symbole und -d die als Code vorgesehenen Bereiche. -D versucht zusätzlich weitere Bereiche als Instruktionen zu deuten; dabei können gewöhnliche Daten wie Code aussehen. Disassemblierung rekonstruiert keinen ursprünglichen C-Quelltext und beweist keinen tatsächlich genommenen Laufzeitpfad. Objektadressen, Dateioffsets und spätere Laufzeitadressen sind verschiedene Größen.

Quelle, am 2026-11-13 gelesen: [GNU-Binutils: objdump](https://sourceware.org/binutils/docs/binutils/objdump.html)

## 3. Syntax

```text
objdump ANSICHTSOPTIONEN [WEITERE-OPTIONEN] DATEI...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-f`, `-h` | Datei- beziehungsweise Sektionsheader lesen. |
| `-t`, `-T` | Normale beziehungsweise dynamische Symbole. |
| `-d`, `-D` | Codebereiche beziehungsweise weitere Bereiche disassemblieren. |
| `-r`, `-R` | Normale beziehungsweise dynamische Relokationen. |
| `-p` | Formatspezifische Header, bei ELF unter anderem direkte dynamische Abhängigkeiten. |
| `-S` | Quelltext und Disassemblierung mischen, sofern Debugdaten und Quellen verfügbar sind. |
| `-j SEKTION`, `-C` | Ansicht auf Sektion begrenzen beziehungsweise Namen demangeln. |
| `--dwarf=no-follow-links` | Zusätzlichen Debugdateiverweisen nicht folgen. do-not-use-debuginfod aus neueren Handbüchern wird lokal nicht unterstützt. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-291-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
objdump --version
printf 'int doppelt(int wert) { return wert * 2; }
' > lernen.c
gcc -O0 -c lernen.c -o lernen.o
objdump -h lernen.o
objdump --dwarf=no-follow-links -dr lernen.o

```

### Schritt 3: Ergebnis auswerten

Im Test erschienen unter anderem .text und das Funktionssymbol doppelt mit x86-64-Instruktionen. Die genaue Befehlsfolge hängt vom Compiler und Target ab; sie wird nicht als allgemeingültiger Algorithmus ausgeschrieben. Nur die eigene Objektdatei ohne ausgelagerte Debugdaten wurde analysiert; kein Binärprogramm wurde gestartet. Ein erster Versuch mit do-not-use-debuginfod gab trotz Status 0 eine Warnung aus. Das korrigierte Beispiel wurde ohne diese nicht unterstützte Option erneut fehler- und warnungsfrei geprüft. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Compilerverhalten verstehen: Eigene Übersetzung anhand von Symbolen und Instruktionen betrachten. Linkprobleme eingrenzen: Relokationen und direkte Bibliotheksanforderungen lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Große oder manipulierte Binärdateien können Parserfehler und hohen Ressourcenbedarf auslösen. Quell- und Debugpfade können weitere Dateien einbeziehen; automatische Debugsymbolbezüge sind gesondert zu kontrollieren. Eine statische Metadatenansicht ist keine Malwarefreigabe. Keine Plugins oder Programme aus unbekannter Quelle starten. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Ausgabe ohne Ansichtsoption | Zum Beispiel -h oder -d ausdrücklich wählen. |
| Falsche Instruktionen | Architektur, Endianness und Code-/Datenbereich prüfen. |
| Kein Quelltext mit -S | Debugdaten und Originalquellen fehlen oder wurden optimiert. |
| NEEDED-Liste unvollständig | Sie zeigt direkte Abhängigkeiten, keine vollständige spätere Loaderaktivität. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU objdump / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `readelf` | Spezifische ELF-Strukturansicht. |
| `nm` | Kompakte Symbolansicht. |
| `ldd` | Loaderbasierte Abhängigkeitsauflösung mit anderen Risiken. |

Ausgangsdatensatz 291 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
