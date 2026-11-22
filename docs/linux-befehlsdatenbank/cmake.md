---
id: "cmake"
name: "cmake"
command: "cmake"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "cmake"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 271
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# cmake – Buildsysteme erzeugen und getrennt bauen

## 1. Kurzbeschreibung

CMake liest CMakeLists.txt, konfiguriert ein Projekt und erzeugt Dateien für ein gewähltes Buildsystem. Konfigurieren, Bauen, Testen und Installieren sind eigenständige Schritte. CMake ist selbst kein C-Compiler.

## 2. Was macht der Befehl?

Ein eigener Buildordner enthält Cache und Generatorausgaben. -S und -B benennen Quelle und Buildziel eindeutig; diese Form benötigt CMake ab 3.13. --build ruft das passende native Werkzeug auf. Generator, Compiler und Cache gehören zusammen; ein Cache darf nicht beliebig zwischen Toolchains weiterverwendet werden. Debug-Konfiguration wird bei Einzelkonfigurationsgeneratoren meist über CMAKE_BUILD_TYPE gewählt, bei Mehrkonfigurationsgeneratoren beim Build über --config.

Quelle, am 2026-11-13 gelesen: [CMake-Aufrufhandbuch](https://cmake.org/cmake/help/latest/manual/cmake.1.html)

## 3. Syntax

```text
cmake -S QUELLE -B BUILD [OPTIONEN]
cmake --build BUILD [--target ZIEL] [--config KONFIGURATION]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-S`, `-B` | Quell- und Buildverzeichnis getrennt festlegen. |
| `-G NAME` | Generator wählen; entsprechendes Buildwerkzeug muss verfügbar sein. |
| `-DNAME:TYP=WERT` | Cachevariable setzen, keine beliebige Umgebungsvariable. |
| `--build BUILD` | Generiertes Projekt bauen. |
| `--parallel ANZAHL` | Parallelität des Builds begrenzen. |
| `--install BUILD` | Installationsregeln ausführen; hier ausdrücklich nicht Teil des Beispiels. |
| `-P SKRIPT` | CMake-Skript ausführen; kann eigenständige Aktionen enthalten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-271-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir quelle
cat > quelle/CMakeLists.txt <<'CMAKE'
cmake_minimum_required(VERSION 3.13)
project(Lernen LANGUAGES C)
add_executable(hallo hallo.c)
CMAKE
printf '#include <stdio.h>
int main(void) { puts("Hallo CMake"); return 0; }
' > quelle/hallo.c
cmake -S quelle -B build -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Debug
cmake --build build --parallel 1
./build/hallo

```

### Schritt 3: Ergebnis auswerten

Ein erfolgreicher Ablauf würde einen getrennten build-Ordner erzeugen und Hallo CMake ausgeben. Zusätzlich wären ein C-Compiler und Make nötig. CMake fehlt hier; weder Konfiguration noch Build oder Ausgabe sind praktisch bestätigt. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Projektbauten reproduzierbar beschreiben: Generator und Toolchain festhalten. Saubere Quellordner erhalten: Ausgaben in einen eigenen Buildbaum schreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Schon CMakeLists.txt kann Programme ausführen oder Inhalte herunterladen. Ein Konfigurationslauf ist daher kein sicherer passiver Scan. Installationsregeln können außerhalb des Buildordners schreiben. Das Beispiel enthält keine Fremdmodule, Downloads oder Installation. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Generator fehlt | Passendes Buildwerkzeug fehlt oder Name stimmt nicht. |
| Compiler nicht gefunden | Toolchain und Umgebung prüfen. |
| Cache passt nicht zur Quelle | Neuen eigenen Buildordner wählen; fremde Dateien nicht löschen. |
| Debug ignoriert | Einzel- und Mehrkonfigurationsgeneratoren unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `make` | Möglicher Buildbackend. |
| `ninja` | Alternativer Generatorbackend. |
| `ctest` | Führt projektdefinierte Tests aus, kein bloßes Strukturlesen. |

Ausgangsdatensatz 271 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
