---
id: "make"
name: "make"
command: "make"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "make"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 286
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Make 4.3"
---

# make – Abhängigkeiten und Bauaktionen mit GNU Make steuern

## 1. Kurzbeschreibung

Make entscheidet anhand von Regeln und Dateizeitstempeln, welche Ziele neu erzeugt werden sollen. Die zugehörigen Rezepte sind echte Shellbefehle. Make ist nicht auf Compiler beschränkt und kein passiver Projektprüfer.

## 2. Was macht der Befehl?

Eine Regel verbindet Ziel, Voraussetzungen und Rezept. Normalerweise beginnt eine Rezeptzeile mit einem Tabulator, nicht mit Leerzeichen. Ein fehlendes Ziel oder eine neuere Voraussetzung löst das Rezept aus. Ohne angegebenes Ziel wird ein Vorgabeziel aus dem Makefile gewählt. Einzelne Rezeptzeilen laufen gewöhnlich in getrennten Shells; ein cd einer Zeile wirkt deshalb nicht selbstverständlich auf die nächste. GNU-Make-Erweiterungen sind nicht auf jede andere Make-Implementierung übertragbar.

Quelle, am 2026-11-13 gelesen: [GNU-Make-Handbuch als Projektmanpage](https://manpages.debian.org/trixie/make/make.1.en.html) und lokale Manpage; die GNU-HTML-Unterseiten waren beim Abruf nicht erreichbar

## 3. Syntax

```text
make [OPTIONEN] [ZIEL...] [VARIABLE=WERT...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-f DATEI` | Bestimmtes Makefile lesen. |
| `-C ORDNER` | Vor dem Lesen ins Verzeichnis wechseln. |
| `-n` | Rezepte normalerweise nur anzeigen; Ausnahmen und Auswertung bleiben möglich. |
| `-q` | Aktualität prüfen: 0 aktuell, 1 Neubau nötig, 2 Fehler. |
| `-j ANZAHL` | Parallelität begrenzen; nacktes -j begrenzt sie nicht. |
| `-rR` | Eingebaute Regeln und Variablen abschalten. |
| `--trace` | Gründe und ausgeführte Rezepte zeigen. |
| `-B` | Ziele unabhängig von Zeitstempeln neu bauen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-286-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
make --version
printf 'Quelle
' > quelle.txt
printf 'ergebnis.txt: quelle.txt
	cp quelle.txt ergebnis.txt
' > Makefile
export MAKEFLAGS= MFLAGS= MAKEFILES=
make -rR -n ergebnis.txt
test ! -e ergebnis.txt
make -rR -j1 ergebnis.txt
cmp -- quelle.txt ergebnis.txt
make -rR -q ergebnis.txt
printf 'Kopie gleich, Ziel aktuell
'

```

### Schritt 3: Ergebnis auswerten

Der erste Aufruf zeigte cp quelle.txt ergebnis.txt, ohne die Datei zu erzeugen. Der zweite erzeugte die eigene Kopie; cmp war erfolgreich und -q meldete Status 0. printf erzeugt hier den nötigen echten Tabulator. Nur dieses bekannte Makefile wurde getestet, kein fremder Build. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Wiederholbare Dateiverarbeitung: Abhängigkeiten eindeutig benennen. Builds prüfen: Diagnoseausgabe von tatsächlichem Rezeptlauf unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Makefiles können schon bei der Auswertung Aktionen anfordern, etwa über Shellfunktionen. Auch -n ist keine allgemeine Sandbox; rekursive oder besonders markierte Rezepte können ausgeführt werden. clean und install sind frei definierte Zielnamen, keine eingebaut sicheren Operationen. Das Beispiel setzt geerbte Make-Steuervariablen nur in der eigenen Übung leer. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Missing separator | Tabulator und Regelaufbau prüfen. |
| No rule to make target | Zielname oder Voraussetzung falsch. |
| Neubau bleibt aus | Zeitstempel und deklarierte Abhängigkeiten prüfen. |
| cd wirkt nicht weiter | Getrennte Rezept-Shells berücksichtigen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU Make 4.3. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cmake` | Kann Makefiles erzeugen. |
| `ninja` | Anderes Buildwerkzeug. |
| `stat` | Zeitstempel eigener Dateien lesen. |

Ausgangsdatensatz 286 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
