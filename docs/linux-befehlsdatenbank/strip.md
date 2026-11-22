---
id: "strip"
name: "strip"
command: "strip"
category: "Entwicklung"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Entwicklung", "strip"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 300
reviewed_at: "2026-11-13"
locally_checked_version: "GNU strip / Binutils 2.42; gcc 13.3.0"
---

# strip – Symbol- und Debugdaten gezielt entfernen

## 1. Kurzbeschreibung

GNU strip entfernt Symbole oder Debuginformationen aus Binärdateien und Archiven. Ohne eigenes Ausgabeziel verändert es die angegebenen Dateien. Die ursprüngliche pauschale Einstufung als sicher lesend ist daher falsch.

## 2. Was macht der Befehl?

Debugdaten unterstützen Quellzeilen- und Variablenanalyse; Symboltabellen können zusätzlich fürs Linken oder Laden nötig sein. --strip-debug ist zurückhaltender als --strip-all. Letzteres kann insbesondere relokatierbare Objekte für weiteres Linken unbrauchbar machen. Größenreduktion ist keine Verschlüsselung: Zeichenketten, benötigte dynamische Symbole und Programmlogik können weiterhin erkennbar sein. Nachträgliches Strippen kann Signaturen und Hashnachweise ungültig machen.

Quelle, am 2026-11-13 gelesen: [GNU-Binutils: strip](https://sourceware.org/binutils/docs/binutils/strip.html)

## 3. Syntax

```text
strip [OPTIONEN] DATEI...
strip [OPTIONEN] -o NEUE-AUSGABE EINGABE
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--strip-debug` / `-g` / `-S` | Nur Debuginformationen entfernen. |
| `--strip-all` / `-s` | Weitgehend Symbole entfernen; Dateinutzung kann beschädigt werden. |
| `--strip-unneeded` | Für Relokationen nicht benötigte Symbole und Debugdaten entfernen; eigenes Ziel prüfen. |
| `-o DATEI` | Neue Ausgabe statt Eingabeersetzung; nur ein Eingabeobjekt. |
| `-K SYMBOL` | Bestimmtes Symbol bewahren. |
| `-R SEKTION` | Sektion zusätzlich entfernen; kann das Ergebnis unbrauchbar machen. |
| `-p` | Zugriffs-/Änderungszeiten bewahren; beweist keinen unveränderten Inhalt. |
| `-V` / `-v` | Version beziehungsweise Änderungsdetails unterscheiden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene Übungsdaten vorbereiten

Voraussetzungen: Bash und die in den Schritten genannten Werkzeuge. Alle Schritte gehören in dieselbe Shell. Das Verzeichnis wird neu erzeugt; ein Fehler beim Anlegen oder Wechseln bricht ab. Ausschließlich selbst geschriebene Inhalte verwenden.

### Schritt 2: Beispiel nachvollziehen

Das folgende Beispiel wurde ausgeführt.

```bash
uebung="$(mktemp -d -t lernen-300-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
strip --version
printf 'int lernfunktion(void) { return 42; }
' > lernen.c
gcc -g -O0 -c lernen.c -o original.o
sha256sum original.o > original.sha256
readelf -S original.o > vorher.txt
strip --strip-debug -o ohne_debug.o original.o
readelf -S ohne_debug.o > nachher.txt
rg '\.debug_info' vorher.txt
if rg '\.debug_info' nachher.txt; then
  exit 1
fi
nm ohne_debug.o
sha256sum -c original.sha256

```

### Schritt 3: Ergebnis auswerten

Die ursprüngliche Objektdatei enthielt .debug_info, die neue Ausgabe nicht mehr. nm zeigte weiterhin die definierte lernfunktion. Der Hashvergleich meldete original.o: OK: Das Original blieb bytegleich, weil -o ein anderes Ziel vorgab. Dies belegt nur das Entfernen von Debugdaten aus dem eigenen Objekt; kein endgültiger Link, Laufzeit-/Signaturtest oder Strippen eines Systemprogramms wurde ausgeführt. Der eigene Ordner bleibt zur Kontrolle bestehen. Eine erfolgreiche Ausführung dieses kleinen Beispiels beweist weder die Sicherheit fremden Codes noch die Eignung für andere Plattformen.

## 6. Typische Anwendungsfälle

Artefakte vorbereiten: Volle Debugfassung und ausdrücklich gewählte Auslieferungsfassung getrennt halten. Toolchainverhalten lernen: Unterschied zwischen Symbol- und Debugdatenentfernung nachvollziehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Entfernte Debug- und Symbolinformationen sind ohne Original nicht zuverlässig rekonstruierbar. Keine Systembibliotheken, laufenden Anwendungen, signierten Originale oder einzigen Buildkopien bearbeiten. Wildcard-/Rekursionssammlungen ohne Zielkontrolle vermeiden. strip ist kein Löschen vertraulicher Inhalte und keine Sicherheitsprüfung. Für eigene Dateien sind keine Rootrechte nötig. Ausgabedateien können vorhandene Ziele überschreiben; deshalb bleiben alle Schreibziele im neuen Übungsordner. Keine Installation oder systemweite Konfigurationsänderung ist Teil des Beispiels.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Debugger findet keine Quellzeilen | Debugdaten entfernt; unveränderte volle Fassung verwenden. |
| Linken scheitert nach strip-all | Erforderliche Symbole/Relokationen wurden entfernt; Original neu verwenden. |
| Programm kleiner, Namen noch sichtbar | Nicht jede Information wird vom gewählten Modus entfernt. |
| Hash oder Signatur stimmt nicht | Binärinhalt wurde verändert; alte Integritätsnachweise gelten nicht mehr. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Quelltext, Eingaben und Ausgabeziele vor der Ausführung lesen. Bei Fehlern zuerst Diagnose, Version und gewählten Modus prüfen. Fremde Projekte können schon beim Konfigurieren oder Bauen beliebigen Code ausführen; ein temporärer Ordner isoliert solche Programme nicht vom Benutzerkonto.

**Prüfstand am 2026-11-13:** GNU strip / Binutils 2.42; gcc 13.3.0. Praktisch geprüft: Abschnitt 5 ausschließlich mit eigenen temporären Daten geprüft. Praktische Prüfung anderer Versionen, Plattformen, größerer Projekte und der nicht im Beispiel ausgeführten Optionen offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `readelf` | Sektionen vor/nach der Änderung lesen. |
| `nm` | Verbleibende Symbole prüfen. |
| `objcopy` | Gezieltes Kopieren und Auslagern von Debugdaten. |
| `gdb` | Benötigt für Quellanalysen passende Debuginformationen. |

Ausgangsdatensatz 300 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
