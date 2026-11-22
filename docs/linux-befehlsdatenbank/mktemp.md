---
id: "mktemp"
name: "mktemp"
command: "mktemp"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "mktemp"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 190
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# mktemp – Temporäre Objekte anlegen statt nur Namen raten

## 1. Kurzbeschreibung

mktemp erzeugt eine neue temporäre Datei oder mit -d ein Verzeichnis und gibt den tatsächlich reservierten Namen aus. Der erfolgreiche Anlegevorgang unterscheidet es von einer bloßen Zufallszeichenfolge.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die Vorlage braucht bei GNU mktemp mindestens drei aufeinanderfolgende X im letzten Namensbestandteil. --tmpdir beziehungsweise -p wählen das Basisverzeichnis. Ohne Vorlage wird eine Vorgabe im temporären Basisverzeichnis verwendet. Neue Dateien beginnen höchstens mit Benutzer-Lese-/Schreibrechten, neue Verzeichnisse höchstens mit Benutzer-Lese-/Schreib-/Suchrechten; eine strengere umask kann weiter einschränken. -u erzeugt nur einen noch unbenutzten Namen und reserviert nichts. Dessen spätere Verwendung als sicherer Dateiname wäre ein Race, weil ein anderer Prozess dazwischen ein Objekt anlegen könnte.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt mktemp invocation](https://www.gnu.org/software/coreutils/manual/html_node/mktemp-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
mktemp [OPTIONEN] [VORLAGE]
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -d | Verzeichnis statt Datei anlegen |
| --tmpdir[=ORDNER] | Vorlage relativ zum ausgewählten temporären Basisordner auswerten |
| -p ORDNER | Explizites Basisverzeichnis |
| --suffix=TEXT | Suffix ohne Slash ergänzen |
| -q | Diagnosen unterdrücken, Status trotzdem prüfen |
| -u | Nur Namen ausgeben, unsicher als spätere Reservierung |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Der äußere Übungsordner wird ebenfalls mit mktemp erzeugt. Darin entstehen zwei eigene neue Objekte; keine vorhersagbaren Namen im allgemeinen /tmp werden verwendet. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-mktemp-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
umask 0077
eigene_datei=$(mktemp --tmpdir="$uebung" notiz-XXXXXX.txt) || exit 1
eigener_ordner=$(mktemp -d --tmpdir="$uebung" bereich-XXXXXX) || exit 1
test -f "$eigene_datei"
test -d "$eigener_ordner"
test "$(stat -c '%a' -- "$eigene_datei")" = 600
test "$(stat -c '%a' -- "$eigener_ordner")" = 700
printf 'eigene Notiz\n' > "$eigene_datei"
stat -c '%a %n' -- "$eigene_datei" "$eigener_ordner"
)
```

### Schritt 3: Ergebnis verstehen

Jede Zuweisung übernimmt genau den erfolgreich angelegten Namen und bricht bei Fehler ab. Die Zahlenprüfung bestätigt im eigenen Kontext 600 für die Datei und 700 für das Verzeichnis. Das Suffix .txt bleibt erhalten. Die Zufallsnamen und konkreten Inodewerte sind absichtlich nicht als konstante Ausgabe vorgegeben.

## 6. Typische Anwendungsfälle

Eigene Zwischenprodukte ohne Namenskollision anlegen oder mehrere Übungsdateien in einem privaten temporären Ordner bündeln. Ein nachprüfbarer Fehlerpfad gehört zur Verwendung ebenso wie die Namensbildung.

## 7. Risiken, Nebenwirkungen und Vorsicht

-u ist kein sicherer Trockenlauf für ein anschließendes Öffnen. Namen aus $$ oder Zeitstempeln sind keine gleichwertige Reservierung. Ein voller Datenträger oder ein ungeeigneter TMPDIR-Wert kann die Anlage verhindern. Temporäre Daten bleiben ohne geplantes Aufräumen bestehen und können vertraulich sein; ein zufälliger Name allein schützt ihren Inhalt nicht.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Zu wenige X | Eine geeignete Vorlage mit mindestens drei aufeinanderfolgenden X wählen |
| Leere Variable nach Fehlschlag | Status sofort prüfen und vor Folgeschritten abbrechen |
| Datei scheinbar sicher aber austauschbar | -u reserviert kein Objekt, regulär anlegen lassen |

## 9. Sichere Varianten oder Tipps für Einsteiger

GNU empfiehlt die flexiblere --tmpdir-/ -p-Form gegenüber dem älteren -t. Rückgabestatus und nötigen Verzeichniswechsel ausdrücklich prüfen, Variablen zitieren und nur die selbst erzeugten Objekte später gezielt aufräumen. Diese Übung lässt ihre Daten zur Kontrolle erhalten.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine künstlich herbeigeführten Platz-/Rechtefehler, keine -u-Reservierungsrennen und keine fremden Objekte geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| mkdir | Verzeichnisse mit festem Namen |
| umask | Weiter einschränkende Anlegevorgaben |
| stat | Tatsächlichen Typ und Modus prüfen |

Herkunft: Originaldatensatz 190 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
