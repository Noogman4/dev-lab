---
id: "go"
name: "go"
command: "go"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "go"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 277
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; Programm fehlt"
---

# go – Go-Quellen bauen und ausführen

## 1. Kurzbeschreibung

go ist die Werkzeugoberfläche der Go-Toolchain. Unterbefehle bauen, testen, formatieren, starten oder verwalten Abhängigkeiten. Besonders run und test führen Code aus; get ist kein allgemeiner Nur-Leseaufruf.

## 2. Was macht der Befehl?

build kompiliert Pakete und Abhängigkeiten. Ein einzelnes main-Paket kann ein Programm erzeugen; Bibliothekspakete ergeben nicht automatisch eine im Arbeitsordner sichtbare ausführbare Datei. run baut und startet das Programm. Module beschreiben Abhängigkeiten in go.mod und go.sum. Je nach Umgebung kann das Werkzeug Module oder eine passende Toolchain herunterladen und Caches schreiben. Deshalb sind Offlinewahl und Schreiborte ausdrücklich zu planen.

Quelle, am 2026-11-13 gelesen: [Go-Werkzeughandbuch](https://pkg.go.dev/cmd/go)

## 3. Syntax

```text
go UNTERBEFEHL [ARGUMENTE]
go build [-o ZIEL] [PAKETE-ODER-DATEIEN]
go run DATEI.go [ARGUMENTE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `version`, `help BEFEHL` | Toolchainstand und konkrete Hilfe lesen. |
| `build -o DATEI` | Eigene Programmausgabe benennen. |
| `run` | Kompiliertes Programm wirklich starten. |
| `test` | Testprogramme ausführen; kein passiver Syntaxcheck. |
| `fmt` | Quellen durch gofmt ändern. |
| `env` | Go-Kontext lesen; env -w würde persistente Einstellungen schreiben. |
| `GOTOOLCHAIN=local` | Automatischen Toolchainwechsel verhindern, Go-Version beachten. |
| `GOPROXY=off` | Modulbezug abschalten; keine allgemeine Netzwerksandbox für gestarteten Code. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

**Nicht praktisch ausgeführt; erklärendes Muster.** Die benötigte Umgebung fehlt oder die praktische Ausführung ist gesondert offen.

```bash
uebung="$(mktemp -d -t lernen-277-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
cat > hallo.go <<'GO'
package main
import "fmt"
func main() { fmt.Println("Hallo Go") }
GO
mkdir cache arbeitsbereich
GOTOOLCHAIN=local GOPROXY=off GOSUMDB=off GOENV=off GOWORK=off GO111MODULE=off GOCACHE="$uebung/cache" GOPATH="$uebung/arbeitsbereich" go run hallo.go

```

### Schritt 3: Ergebnis auswerten

Erwartet wäre Hallo Go. Das Beispiel verwendet nur die Standardbibliothek und verlegt Go-Caches in den eigenen Ordner; es benötigt eine installierte passende Toolchain. Go fehlt lokal, daher wurde die Ausgabe nicht gemessen. Die Umgebungsvariablen gelten nur für diesen Aufruf und sind keine Sicherheitsisolation für fremden Go-Code. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Kleine Programme nachvollziehen: Quelltext, Paket und Ausgabe verbinden. Projektarbeit: Modul- und Toolchainversionen ausdrücklich festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

go generate, Tests und ausgeführte Programme können beliebige Benutzeraktionen durchführen. Abhängigkeitsverwaltung kann Netz und fremden Quelltext einbeziehen. Keine globalen go env -w-Änderungen, keine Installation und kein Download gehören zu dieser Übung. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| go fehlt | Praktische Prüfung offen; keine Version aus einer Website ableiten. |
| Toolchain zu alt | Lokale Version und Sprachstand prüfen; automatischen Download nicht unbemerkt erlauben. |
| Modul nicht verfügbar | Offlinegrenze beibehalten und Abhängigkeiten gesondert klären. |
| Keine ausführbare Datei | build eines Bibliothekspakets und main-Paket unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; Programm fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gofmt` | Formatiert Go-Quellen. |
| `gcc` | Andere Compilerfamilie. |
| `git` | Verwaltet die Quellgeschichte, nicht Go-Abhängigkeiten. |

Ausgangsdatensatz 277 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
