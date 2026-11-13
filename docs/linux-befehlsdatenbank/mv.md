---
id: "mv"
name: "mv"
command: "mv"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "mv"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 191
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# mv – Dateien verschieben und Kollisionen vorher verstehen

## 1. Kurzbeschreibung

mv benennt Dateien oder Verzeichnisse um beziehungsweise verschiebt sie. Anders als cp soll nach erfolgreichem Verschieben der ursprüngliche Quellname verschwunden sein.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Innerhalb desselben Dateisystems genügt oft eine Umbenennung. Über eine Dateisystemgrenze kann GNU mv dagegen kopieren und anschließend die Quelle entfernen. Eine Gruppe von Verschiebungen ist deshalb keine gemeinsame atomare Transaktion. Ein bestehendes Ziel kann ohne ausdrücklich gewählten Schutz ersetzt werden. -T legt fest, dass das letzte Argument der genaue Zielname ist und nicht als vorhandenes Zielverzeichnis verwendet werden soll. Ob die Ausführung erlaubt ist, hängt wesentlich von den Rechten an Quell- und Zielverzeichnissen ab, nicht nur vom Schreibbit der Datei.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt mv invocation](https://www.gnu.org/software/coreutils/manual/html_node/mv-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
mv [OPTIONEN] QUELLE ZIEL
mv [OPTIONEN] QUELLE ... ZIELORDNER
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -i | Vor einem Ersetzen nachfragen |
| -n | Vorhandenes Ziel nicht ersetzen, Statusverhalten ist versionsabhängig |
| --update=none | Bei GNU 9.4 vorhandene Ziele überspringen, kein Fehler allein wegen Überspringens |
| -b | Vor einem Ersetzen Sicherungsname verwenden |
| -T | Ziel als konkreten Namen behandeln |
| -v | Durchgeführte Schritte melden |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Nur neu angelegte eigene Textdateien werden innerhalb desselben privaten Übungsordners verschoben. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-mv-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'eigene Quelle\n' > quelle.txt
printf 'eigenes Ziel\n' > ziel.txt
mv --update=none -- quelle.txt ziel.txt
test -f quelle.txt
printf 'eigenes Ziel\n' > erwartet.txt
cmp ziel.txt erwartet.txt
mv -T -- quelle.txt neuer-name.txt
test ! -e quelle.txt
printf 'eigene Quelle\n' > erwartet-quelle.txt
cmp neuer-name.txt erwartet-quelle.txt
printf 'Kollision uebersprungen, eigener neuer Name geprueft\n'
)
```

### Schritt 3: Ergebnis verstehen

Der erste Aufruf überspringt die Kollision: quelle.txt bleibt vorhanden und ziel.txt unverändert. Der zweite benennt die eigene Quelle unter einen bisher freien Namen um; der alte Name ist danach weg und der Inhalt bleibt gleich. Der erfolgreiche Status des ersten Aufrufs bedeutet gerade nicht, dass die Verschiebung stattfand.

## 6. Typische Anwendungsfälle

Eigene Dateien ordnen oder bewusst umbenennen. Bei mehreren Quellen Kollisionen und Teilfortschritt planen und Kopieren, Umbenennen sowie Löschen fachlich unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Überschreiben kann vorhandenen Inhalt verlieren lassen. Beim Wechsel auf ein anderes Dateisystem können Kopierfehler und Teilstände entstehen. Ein leerer Zielordner kann unter anderen Regeln behandelt werden als eine normale Zieldatei. An Symlinknamen keine unbedachten abschließenden Slashes ergänzen. Die Übung verwendet weder -f noch fremde Quellen und überschreitet keine Dateisystemgrenze.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Quelle bleibt trotz Status 0 | Ein bewusstes Überspringen kann erfolgreich sein, Dateizustand prüfen |
| Datei landet im Zielordner statt unter dessen Namen | Zieltyp verstehen und bei exakter Absicht -T prüfen |
| Mehrere Dateien nur teilweise verschoben | Keine Gesamttransaktion, jeden verbleibenden Quell- und Zielpfad abgleichen |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für die erste Übung neue eindeutige Zielnamen wählen. Ein Trockenlauf für beliebige mv-Aktionen wird hier nicht behauptet. Schutzoption, Rückgabestatus, Diagnose und tatsächlichen Dateizustand gemeinsam beurteilen. Neuere GNU-Optionen vor Verwendung gegen die lokale Hilfe prüfen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Nur eigene Umbenennung und Kollisionsüberspringen geprüft, keine Fremdpfade oder Dateisystemwechsel. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| cp | Quelle beim Kopieren erhalten |
| rename.ul | Einfache serienweise Teilstringumbenennung |
| stat | Dateiidentität und Metadaten vergleichen |

Herkunft: Originaldatensatz 191 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
