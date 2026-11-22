---
id: "rm"
name: "rm"
command: "rm"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "rm"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 196
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# rm – Dateinamen bewusst entfernen und Löschwirkungen begrenzen

## 1. Kurzbeschreibung

rm entfernt angegebene Dateinamen und mit rekursiven Optionen auch Verzeichnisinhalte. Es verschiebt Dateien nicht in einen Desktop-Papierkorb und besitzt keine allgemeine Rückgängig-Funktion.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Das Entfernen eines Namens ist nicht dasselbe wie sicheres Überschreiben des Inhalts. Weitere Hardlinks oder ein noch offener Dateideskriptor können die Datei beziehungsweise belegte Daten weiter erhalten. Ob ein Name entfernt werden darf, hängt wesentlich von den Rechten seines Elternverzeichnisses sowie zusätzlichen Regeln wie dem Sticky-Bit ab. Ein nicht schreibbarer Dateiinhalt ist daher kein allgemeiner Löschschutz. Ein Symlink wird bei einem gewöhnlichen Dateinamenargument selbst entfernt, nicht automatisch sein Ziel. Erweiterte oder rekursive Fälle mit Pfadbestandteilen verlangen zusätzliche Vorsicht.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt rm invocation](https://www.gnu.org/software/coreutils/manual/html_node/rm-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
rm [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -i | Für jeden ausgewählten Namen nachfragen |
| -I | Nur unter bestimmten Mengen-/Rekursionsbedingungen einmal fragen, nicht bei jeder Datei |
| -r, -R | Verzeichnisinhalt rekursiv entfernen, destruktiv |
| -f | Keine Rückfragen und bestimmte Fehlermeldungen unterdrücken, kein sicherer Modus |
| --one-file-system | Bei Rekursion andere Dateisysteme auslassen, keine vollständige Isolation |
| --preserve-root | Schutz gegen rekursives Entfernen von /, keine allgemeine Pfadabsicherung |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen einordnen

Das folgende Muster bezieht sich ausschließlich auf eine neu erzeugte eigene Wegwerfdatei. Es wurde bewusst keine Löschaktion ausgeführt. Version und Primärquelle wurden geprüft, Rückfragen und tatsächliches Entfernen bleiben praktisch offen.

### Schritt 2: Nicht ausgeführtes Muster lesen

Die folgenden Zeilen sind ausdrücklich ein Erklärungsmuster, kein ausgeführter Test und keine gemessene Ausgabe.

```text
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-rm-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'eigene Wegwerfdatei, keine Nutzerdaten\n' > eigene-datei.txt
rm -i -- ./eigene-datei.txt
)
```

### Schritt 3: Wirkung und Grenze verstehen

Bei einem später ausdrücklich freigegebenen eigenen Lauf würde -i zur Entscheidung über genau diesen Namen auffordern. Ablehnen belässt die Datei, Bestätigen entfernt ihren Namen. Die konkrete Sprache und Eingabe sind hier nicht gemessen. -- beendet die Optionsauswertung und ./ macht den gewählten relativen Dateinamen sichtbar. Das Muster enthält weder Rekursion noch -f.

## 6. Typische Anwendungsfälle

Eine zuvor geprüfte einzelne eigene Datei gezielt entfernen. Das Aufräumen ganzer Bäume und ein sicheres Vernichten vertraulicher Datenträger sind andere Aufgaben mit anderen Voraussetzungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein falscher Pfad, leere Variablen oder von der Shell expandierte Muster können andere Dateien auswählen als gedacht. -f reduziert Schutzfragen, -r erweitert den Bereich stark. Schutz vor / verhindert keine Löschung eines falschen Unterordners. --one-file-system schützt nicht vor fremden Daten auf demselben Dateisystem. Nicht auf einen Alias als einzigen Schutz vertrauen und keine destruktive Systemzeile zum Test verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Permission denied trotz schreibbarer Datei | Elternverzeichnis und zusätzliche Zugriffsregeln prüfen |
| Datei entfernt aber Platz bleibt belegt | Andere Namen oder offene Deskriptoren können Daten erhalten |
| Rückfrage fehlt bei -I | Die Option fragt nicht grundsätzlich bei jedem einzelnen Namen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für eine einzelne überprüfte Datei die klare Namensangabe und gegebenenfalls -i verwenden. Vor Bestätigung die tatsächliche Auswahl lesen. Keine Löschpipeline aus einer dekorierten ls-Ausgabe bilden. Ein Löschtest ist keine Prüfung sicherer Datenvernichtung; auch shred hat erhebliche Speichermediengrenzen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Nicht praktisch geprüft; praktische Prüfung offen. Kein Entfernen, keine rekursive Aktion und keine Rückfrage praktisch ausgeführt; nur Version gelesen. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| rmdir | Nur leere Verzeichnisse entfernen |
| unlink | Genau einen Namen ohne Rekursion lösen |
| shred | Überschreiben mit wichtigen Wirksamkeitsgrenzen |

Herkunft: Originaldatensatz 196 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
