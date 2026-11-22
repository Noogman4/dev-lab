---
id: "readelf"
name: "readelf"
command: "readelf"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "safe"
tags: ["Entwicklung", "readelf"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 297
reviewed_at: "2026-11-13"
locally_checked_version: "GNU readelf / Binutils 2.42; gcc 13.3.0"
---

# readelf – ELF-Header, Sektionen und Symbole lesen

## 1. Kurzbeschreibung

readelf zeigt Strukturen von ELF-Dateien und Archiven mit ELF-Mitgliedern. Es führt das Zielprogramm nicht aus und arbeitet unabhängig von der BFD-Bibliothek, die andere Binutils-Werkzeuge verwenden.

## 2. Was macht der Befehl?

Der Dateikopf nennt unter anderem Klasse, Byteordnung, Maschinentyp und ELF-Typ. Relokatierbare Objekte haben andere Eigenschaften als ausführbare oder gemeinsame Objekte. Sektionen organisieren Link-/Analyseinformationen; Programmheader beschreiben Segmente für das Laden. Eine .o-Datei muss keine Programmheader haben. ET_DYN kann auch ein positionsunabhängiges ausführbares Programm bezeichnen und ist deshalb nicht allein als gewöhnliche Bibliothek zu deuten.

Quelle, am 2026-11-13 gelesen: [GNU-Binutils: readelf](https://sourceware.org/binutils/docs/binutils/readelf.html)

## 3. Syntax

```text
readelf [ANSICHTSOPTIONEN] [WEITERE-OPTIONEN] ELF-DATEI...
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-h` | ELF-Dateikopf; hier keine Hilfeoption. |
| `-l` | Programmheader/Segmente lesen. |
| `-S` | Sektionsheader lesen. |
| `-s`, `--dyn-syms` | Normale beziehungsweise dynamische Symboltabellen. |
| `-d` | Dynamische Einträge einschließlich direkter NEEDED-Abhängigkeiten. |
| `-r` | Relokationen lesen. |
| `-W` | Breite Ausgabe mit weniger Namenskürzung. |
| `-L` | Zusätzliche Konsistenzwarnungen; kein Sicherheitszertifikat. |
| `-v` / `-V` | Werkzeugversion beziehungsweise Symbolversionsinformationen unterscheiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-297-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
readelf --version
printf 'int lernwert = 42;
' > lernen.c
gcc -c lernen.c -o lernen.o
readelf -h lernen.o
readelf -W -s lernen.o
sha256sum lernen.o > original.sha256
readelf -S lernen.o > sektionen.txt
sha256sum -c original.sha256

```

### Schritt 3: Ergebnis auswerten

Der Dateikopf nannte ELF64, little endian, x86-64 und REL. Die Symboltabelle enthielt lernwert. Der Hashvergleich nach dem Sektionslesen meldete lernen.o: OK. Somit blieb die eigene Eingabedatei bytegleich. Die Architekturwerte gelten für diesen lokalen Build und sind keine Vorgabe für jeden Linuxrechner. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Formatfragen klären: Architektur und Objektart vor einem Linkversuch erkennen. Laufzeitprobleme eingrenzen: Statische Metadaten statt Ausführung unbekannter Ziele lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Statisch lesen bedeutet nicht, dass jedes manipulierte Format fehlerfrei geparst werden kann. Große Ausgaben, Debugverweise und zusätzliche Symbolquellen sind gesondert zu beachten; dafür wurden hier keine Optionen aktiviert. Ausgelesene Namen/Pfade können intern sein. NEEDED-Einträge zeigen keine vollständige spätere Bibliotheksaktivität. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Not an ELF file | Anderes Format oder beschädigte Eingabe. |
| Keine Programmheader | Bei relokatierbaren Objekten normal. |
| Keine dynamische Sektion | Statische oder nicht dynamisch gelinkte Objektart. |
| Abgeschnittene Namen | -W verwenden; Spalten nicht blind nach festen Positionen parsen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU readelf / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `objdump` | Mehrere Objektformate und Disassemblierung. |
| `nm` | Kompakte Symbolliste. |
| `file` | Grobe Formaterkennung. |
| `ldd` | Loaderbasierte Auflösung mit anderer Sicherheitsgrenze. |

Ausgangsdatensatz 297 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
