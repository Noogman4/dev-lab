---
id: "ranlib"
name: "ranlib"
command: "ranlib"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "ranlib"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 296
reviewed_at: "2026-11-13"
locally_checked_version: "GNU ranlib / Binutils 2.42; gcc 13.3.0"
---

# ranlib – Symbolindex eines Objektarchivs erzeugen

## 1. Kurzbeschreibung

GNU ranlib schreibt einen Symbolindex in ein bestehendes ar-Archiv. Damit ist der normale Aufruf schreibend. Es erzeugt keine einzelnen Objektdateien und keine fertig gelinkte Anwendung.

## 2. Was macht der Befehl?

Der Index ordnet definierte Symbole den Archivmitgliedern zu und unterstützt den Linker bei der Auswahl benötigter Objekte. GNU ranlib entspricht funktional ar -s. Viele ar-Aufrufe erzeugen oder aktualisieren den Index bereits; ein zusätzlicher ranlib-Schritt ist dann oft redundant. Ein Index ist kein Integritätsnachweis der enthaltenen Funktionen. Normale Archive enthalten die Mitglieder, Thin-Archive dagegen Verweise auf externe Objektdateien.

Quelle, am 2026-11-13 gelesen: [GNU-Binutils: ranlib](https://sourceware.org/binutils/docs/binutils/ranlib.html) und [ar](https://sourceware.org/binutils/docs/binutils/ar.html)

## 3. Syntax

```text
ranlib [OPTIONEN] ARCHIV
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-D` | Deterministische Metadaten des Indexmitglieds verwenden; Inhalt und sonstige Mitglieder bleiben gesonderte Reproduzierbarkeitsfaktoren. |
| `-U` | Reale UID/GID-/Zeitmetadaten verwenden; Gegenstück zu -D. |
| `-t` | Zeitstempel des Symbolindex aktualisieren; ebenfalls Schreibzugriff. |
| `--plugin NAME` | Plugin laden; ausführbarer Code, hier nicht verwenden. |
| `--version`, `--help` | Version beziehungsweise Aufrufhilfe lesen. |
| `nm -s ARCHIV` | Index anzeigen; anderer lesender Befehl. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-296-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
ranlib --version
printf 'int lernfunktion(void) { return 42; }
' > lernen.c
gcc -c lernen.c -o lernen.o
ar rcS liblernen.a lernen.o
ranlib -D liblernen.a
nm -s liblernen.a
cp -- liblernen.a nach_index.a
ranlib -D liblernen.a
cmp -- liblernen.a nach_index.a
printf 'Wiederholter Index bytegleich
'

```

### Schritt 3: Ergebnis auswerten

ar rcS legt das eigene Archiv ausdrücklich ohne Symbolindex an. ranlib -D ergänzt ihn; nm -s zeigte lernfunktion in lernen.o. Der zweite deterministische Lauf blieb bytegleich zur eigenen Kopie. Das belegt nur diesen kleinen lokalen Fall, keine plattformunabhängige Reproduzierbarkeit fremder Archive und keinen späteren Linklauf. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Archivbau verstehen: Objektinhalt und Suchindex auseinanderhalten. Toolchains vergleichen: Prüfen, ob ar bereits einen Index erzeugt.

## 7. Risiken, Nebenwirkungen und Vorsicht

ranlib verändert das Archiv direkt. Nur entbehrliche eigene Kopien für Übungen benutzen. Plugin- und LTO-Unterstützung sind toolchainabhängig und können Code aus Bibliotheken laden. Thin-Archive sind keine unabhängigen Sicherungen ihrer referenzierten Objekte. Keine Systembibliotheken werden bearbeitet. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| File format not recognized | Kein passendes ar-Archiv oder inkompatibles Format. |
| Index schon vorhanden | Viele ar-Modi pflegen ihn bereits; nicht als Fehler behandeln. |
| Symbole fehlen | Mitglieder, Objektformat und gegebenenfalls LTO-Unterstützung prüfen. |
| Deterministischer Index, anderes Archivhash | Sonstige Metadaten/Inhalte und Eingabereihenfolge prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU ranlib / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ar` | Erzeugt und bearbeitet Objektarchive. |
| `nm -s` | Liest den Symbolindex. |
| `ld` | Nutzt Archive beim Linken. |

Ausgangsdatensatz 296 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
