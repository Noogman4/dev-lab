---
id: "ninja"
name: "ninja"
command: "ninja"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "ninja"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 288
reviewed_at: "2026-11-13"
locally_checked_version: "Ninja 1.11.1"
---

# ninja – Explizite Buildregeln mit Ninja ausführen

## 1. Kurzbeschreibung

Ninja führt einen vorgegebenen Abhängigkeitsgraphen aus build.ninja aus. Solche Dateien werden häufig von CMake oder anderen Generatoren erzeugt. Die darin genannten Kommandos sind echte Programme mit Benutzerrechten.

## 2. Was macht der Befehl?

Eine rule beschreibt eine Befehlsvorlage; build verbindet Ausgaben, Regel und Eingaben. $in und $out werden von Ninja eingesetzt, nicht von der äußeren Shell. Ninja beachtet neben Zeitstempeln auch gespeicherte Befehlsinformationen. Es hat keine allgemeine eingebaute C-Compilerregel. Parallelität ist standardmäßig aktiv; unvollständige Abhängigkeiten können deshalb fehlerhafte Builds ergeben.

Quelle, am 2026-11-13 gelesen: [Ninja-Projekthandbuch](https://ninja-build.org/manual.html)

## 3. Syntax

```text
ninja [OPTIONEN] [ZIEL...]
ninja -t WERKZEUG [ARGUMENTE...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-C ORDNER` | Vor dem Build ins Verzeichnis wechseln. |
| `-f DATEI` | Andere Ninja-Datei lesen. |
| `-n` | Benötigte Aktionen anzeigen, ohne den normalen Build auszuführen. |
| `-v` | Vollständige Kommandos zeigen. |
| `-j ANZAHL` | Anzahl paralleler Aufgaben begrenzen. |
| `-t query ZIEL` | Abhängigkeiten eines Ziels lesen. |
| `-t commands ZIEL` | Befehle für den Aufbau anzeigen. |
| `-t clean` | Buildausgaben löschen; kein allgemeiner Diagnoseaufruf. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-288-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
ninja --version
printf 'Eigene Quelle
' > quelle.txt
cat > build.ninja <<'NINJA'
rule kopie
  command = cp $in $out
build ergebnis.txt: kopie quelle.txt
default ergebnis.txt
NINJA
ninja -n
test ! -e ergebnis.txt
ninja -j1 -v
cmp -- quelle.txt ergebnis.txt
ninja -j1

```

### Schritt 3: Ergebnis auswerten

Der Plan zeigte cp quelle.txt ergebnis.txt ohne Ausgabedatei. Der echte Build erzeugte eine gleiche Kopie. Beim zweiten Build meldete Ninja no work to do. Eigene .ninja_log-Daten im Übungsordner sind normale Buildnebenprodukte. Nur dieses kleine bekannte Regelwerk wurde geprüft. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Inkrementelle Builds verstehen: Eingaben, Ausgaben und Befehle explizit verfolgen. Generatorprojekte verwenden: Ninja-Dateien normalerweise aus dem vorgesehenen Projektgenerator beziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Unbekannte Buildregeln können löschen, installieren oder das Netz nutzen. -t browse kann einen Server und Browserstart auslösen und gehört nicht zur Übung. clean löscht Dateien. Ein eigener Arbeitsordner beschränkt nicht die Rechte eines ausgeführten Kommandos. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| build.ninja fehlt | Richtiges Buildverzeichnis oder -f wählen. |
| Unknown target | Ausgabename statt vermutetem Tasknamen prüfen. |
| Immer erneuter Build | Eingabezeiten, Befehlsänderungen und fehlende Ausgaben prüfen. |
| Parallelfehler | Graphabhängigkeiten berichtigen; -j1 ist nur Diagnosehilfe. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Ninja 1.11.1. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cmake` | Erzeugt Ninja-Buildgraphen. |
| `make` | Andere Regelsprache. |
| `cmp` | Prüft den Inhalt der eigenen Kopie. |

Ausgangsdatensatz 288 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
