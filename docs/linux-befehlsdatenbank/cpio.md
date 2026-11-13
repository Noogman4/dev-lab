---
id: "cpio"
name: "cpio"
command: "cpio"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "dateiliste", "cpio"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 7
reviewed_at: "2026-11-13"
locally_checked_version: "GNU cpio 2.15"
---

# cpio – Archive aus Dateilisten erstellen und kontrolliert auspacken

## 1. Kurzbeschreibung

`cpio` überträgt Dateien zwischen Dateisystem und Archiv. Beim Erstellen liest es üblicherweise eine Liste von Dateinamen aus der Standardeingabe. Beim Entpacken liest es einen Archivdatenstrom und schreibt dessen Dateien an den gewählten Arbeitsort.

**Für eigene Dateien und einen eigenen Zielordner sind keine Root-Rechte nötig.** Wiederherstellung fremder Eigentümer, besonderer Dateitypen oder geschützter Systemdateien ist eine andere Aufgabe und nicht Teil dieses Beispiels.

## 2. Was macht der Befehl?

Es gibt drei unterschiedliche Betriebsarten:

| Modus | Aufgabe | Ein- und Ausgabe |
| --- | --- | --- |
| Copy-out mit `-o` | Archiv erzeugen. | Dateiliste hinein, Archivdaten hinaus. |
| Copy-in mit `-i` | Archiv lesen oder extrahieren. | Archivdaten hinein; Liste oder Dateien hinaus. |
| Pass-through mit `-p` | Dateien direkt in einen anderen Ordner übertragen. | Dateiliste hinein; Kopien im Ziel, ohne separate Archivdatei. |

Der Name „Copy-out“ meint aus Sicht des Dateisystems ins Archiv, nicht aus Sicht eines heruntergeladenen Archivs. Diese Unterscheidung verhindert eine häufige Verwechslung der Schalter.

Die GNU-Betriebsarten und unterstützten Formate sind in der [Debian-Manpage zu GNU cpio](https://manpages.debian.org/trixie/cpio/cpio.1.en.html#DESCRIPTION) dokumentiert. `cpio` ist dabei ein Archivwerkzeug; eine allgemeine automatische Kompression ist nicht die Grundfunktion.

## 3. Syntax

```text
cpio -o [OPTIONEN] < DATEILISTE > ARCHIV
cpio -it [OPTIONEN] < ARCHIV
cpio -i [OPTIONEN] < ARCHIV
cpio -p [OPTIONEN] ZIELORDNER < DATEILISTE
```

Die Zeichen `<` und `>` sind Shell-Umleitungen. Die Archivdatei einfach als unbeschriftetes zusätzliches Argument hinter `-o` zu hängen, ersetzt diese Eingabe-/Ausgabewahl nicht.

Für eine robust getrennte Dateiliste wird oft `find -print0` mit `cpio --null` kombiniert. Ein Nullbyte kann nicht Bestandteil eines Unix-Dateinamens sein; ein Zeilenumbruch dagegen schon. Das macht NUL-getrennte Listen für Dateinamen geeigneter als einfache Zeilenlisten.

## 4. Wichtige Optionen

| Option | Bedeutung | Voraussetzung oder Vorsicht |
| --- | --- | --- |
| `-o`, `--create` | Archiv erstellen. | Liest die Dateinamenliste. |
| `-i`, `--extract` | Archiv lesen und extrahieren. | Schreibt bei normaler Extraktion Dateien. |
| `-t`, `--list` | Inhalt auflisten. | Mit `-it` ist die Absicht besonders deutlich. |
| `-p`, `--pass-through` | Dateien unmittelbar ins Ziel übertragen. | Ziel ist ein Verzeichnis, kein Archivname. |
| `-0`, `--null` | NUL-getrennte Dateinamen lesen. | Für Copy-out oder Pass-through mit passender Quelle. |
| `-H newc`, `--format=newc` | Das portable `newc`-Format wählen. | Formatgrenzen, etwa bei großen Mitgliedern, beachten. |
| `-d`, `--make-directories` | Benötigte übergeordnete Zielordner anlegen. | Für die Extraktion von Unterordnern oft nötig. |
| `-v`, `--verbose` | Verarbeitete Namen anzeigen. | Ausgabe lesen statt Erfolg nur aus einer Datei abzuleiten. |
| `--no-absolute-filenames` | Wiederherstellung relativ zum aktuellen Verzeichnis anfordern. | Keine vollständige Sicherheitsisolierung für fremde Archive. |
| `-u`, `--unconditional` | Dateien ohne die übliche Altersprüfung ersetzen. | Überschreibverhalten wird weitreichender. |

Die Schalter wurden zusätzlich mit `cpio --help` der Version 2.15 abgeglichen. Nicht jede Option ist in jedem Betriebsmodus gültig. Die vollständigen Zuordnungen stehen in der [GNU-Optionsreferenz bei Debian](https://manpages.debian.org/trixie/cpio/cpio.1.en.html#OPTIONS).

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Kleine Übung vorbereiten

```bash
uebung="$(mktemp -d -t netmon-cpio-XXXXXX)"
cd "$uebung"
pwd
mkdir -p "Material/unterordner"
printf '%s\n' 'Eigene cpio-Testdaten.' > "Material/unterordner/notiz.txt"
```

Nur nach erfolgreichem Verzeichniswechsel fortfahren. So liegen die folgenden Eingaben und Ausgaben vollständig in einem neuen Testordner.

### Schritt 2: Relative Dateiliste ins neue Archiv übernehmen

```bash
(cd "Material" && find . -print0 | cpio --null -ov --format=newc) > "sammlung.cpio"
```

- Die runden Klammern bilden eine Subshell. Der Verzeichniswechsel bleibt auf diesen Teil beschränkt.
- `find . -print0` liefert eine NUL-getrennte Liste relativ zu `Material`.
- `--null` lässt `cpio` dieselbe Trennung verstehen.
- `-o` erstellt das Archiv; `-v` zeigt die verarbeiteten Namen.
- `--format=newc` legt das gewünschte Format fest.
- Die äußere Umleitung schreibt `sammlung.cpio` außerhalb des durchsuchten Ordners. So wird das gerade entstehende Archiv nicht selbst als Eingabedatei gefunden.

### Schritt 3: Inhalt ansehen

```bash
cpio -it < "sammlung.cpio"
```

In der Liste sollte `unterordner/notiz.txt` mit einem möglichen vorangestellten `./` vorkommen. Die Liste ist keine kryptografische Integritäts- oder Herkunftsprüfung.

### Schritt 4: In einen neuen Zielordner extrahieren

```bash
mkdir "Ausgabe"
(cd "Ausgabe" && cpio -idv --no-absolute-filenames < "../sammlung.cpio")
```

`-i` liest die Archivdaten, `-d` erlaubt benötigte Unterordner, `-v` zeigt die Namen. Das Beispiel verwendet ausschließlich das selbst erzeugte Archiv. Anschließend sollte die Notiz unter `Ausgabe/unterordner/notiz.txt` stehen und denselben Inhalt besitzen.

## 6. Typische Anwendungsfälle

**Dateien aus einer bewusst zusammengestellten Auswahl bündeln:** Die Dateiliste kann unabhängig von der Archivierung erzeugt und geprüft werden. Dabei muss ihr Arbeitsverzeichnis zur Interpretation relativer Namen passen.

**Vorhandene CPIO-Archive untersuchen:** Eine Inhaltsliste kann bei Softwarepaketen oder technischen Systemabbildern helfen. Unterschiedliche Kompressionshüllen und mehrere hintereinanderliegende Archive erfordern jedoch passende Spezialwerkzeuge.

**Dateien direkt kopieren:** Der Pass-through-Modus arbeitet ohne separate Archivdatei. Das macht ihn nicht zu einem universellen Ersatz für Sicherung, Synchronisation und deren Löschregeln.

**Initramfs-Dateien verstehen:** CPIO-Formate spielen in manchen frühen Linux-Startumgebungen eine Rolle. Das Übungsbeispiel ist ausdrücklich keine Anleitung zum Ersetzen einer produktiven Initramfs.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Falscher Modus oder falscher Arbeitsort

Copy-out und Copy-in haben entgegengesetzte Dateiwirkungen. Vor einer Extraktion kontrollieren, wo die Dateien entstehen würden. Vor der Erstellung prüfen, welche Namen die Dateiliste tatsächlich enthält.

### Überschreiben und relative Pfade

Extraktion kann vorhandene Dateien beeinflussen. `-u` erweitert die Ersetzungsbereitschaft. `--no-absolute-filenames` ist eine sinnvolle Begrenzung der Pfadabsicht, macht ein fremdes Archiv aber nicht harmlos. Relative Ausbruchspfade, Verknüpfungen und Dateitypen müssen versions- und fallbezogen geprüft werden. Ein leerer Zielordner ist keine Sandbox.

### Archiv selbst als Eingabe

Wenn die Ausgabedatei im durchsuchten Baum entsteht, kann sie in die Dateiliste geraten. Das ist ein Grund, Ein- und Ausgabe im Beispiel räumlich zu trennen.

### Unvollständige Pipelines

Eine schon angelegte Archivdatei beweist keinen vollständigen Lauf. Fehler beim Erzeugen der Dateiliste dürfen nicht durch einen erfolgreichen letzten Pipeline-Schritt verdeckt werden. In Bash-Skripten gegebenenfalls Pipeline-Fehler ausdrücklich auswerten und die Liste vorab kontrollieren.

### Metadaten und Formatgrenzen

Eigentümer, Berechtigungen und besondere Dateien sind bei Wiederherstellungen keine bloßen Textangaben. Für echte Systembackups ist der komplette Sicherungs- und Rückspielweg gesondert zu planen. `newc` hat außerdem eine begrenzte Größe je Mitglied; es ist nicht beliebig für jede große Datei geeignet.

**Keine Root-Rechte für diese Übung verwenden.** Auch eine vorhandene Administratorberechtigung ist keine Freigabe zum Wiederherstellen fremder Systempfade.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Eingabe nach `cpio -o` | Es fehlt die Dateinamenliste. | Quelle der Liste prüfen; Archivname nicht mit Namensliste verwechseln. |
| Datei aus Liste nicht gefunden | Falsches Arbeitsverzeichnis. | Relative Namen vom passenden Basisordner aus verwenden. |
| Unterordner können nicht angelegt werden | `-d` fehlt oder Rechte reichen nicht. | Neuen eigenen Zielordner und benötigte Optionen prüfen. |
| Seltsame oder abgeschnittene Namen | Zeilenliste für ungewöhnliche Dateinamen. | Zusammenpassend `find -print0` und `--null` nutzen. |
| Archiv lässt sich nicht lesen | Anderes Format, Kompressionshülle oder beschädigte Daten. | Inhaltstyp und Erzeugungsweg prüfen. |
| Eine bestehende Datei wurde nicht ersetzt | Zeit- oder Überschreibregeln greifen. | Ausgabe lesen, bevor ein unbedingtes Ersetzen erwogen wird. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zunächst nur das selbst erzeugte Übungsarchiv zurückspielen.
2. Betriebsart, Dateiliste und Zielort vor jedem schreibenden Aufruf getrennt prüfen.
3. Relative Pfade und neue Zielordner verwenden.
4. Ausgabe außerhalb des erfassten Eingabebaums anlegen.
5. Erfolgsstatus aller Teile einer Pipeline beachten.
6. Ein verwendbares Archiv erst nach einem überprüften Rückspielversuch annehmen.
7. Technische Systemabbilder nicht ohne eigenen Plan und Berechtigung verändern.

**Prüfstand:** Mit GNU cpio 2.15 wurden eine NUL-getrennte Liste eigener Dateien im Format `newc` archiviert, die Einträge aufgelistet und in einen getrennten Ordner extrahiert. Der zurückgewonnene Dateiinhalt entsprach der Eingabe. Systemstart, Gerätedateien, fremde Eigentümer, große Archive und bösartige Pfadkonstruktionen wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find` | Dateinamenlisten nach einer Auswahlregel erzeugen. |
| `tar` | Dateien und Ordner mit einer anderen Archivschnittstelle bündeln. |
| `pax` | Archiv- und Kopierwerkzeug, dessen Verfügbarkeit distributionsabhängig ist. |
| `gzip`, `xz`, `zstd` | Mögliche zusätzliche Kompressionsschritte; Formate nicht verwechseln. |
| `lsinitramfs` | In unterstützten Distributionen Inhalte einer Initramfs untersuchen. |

Der Ausgangseintrag steht unverändert unter Datensatz 7 in `index.json`. Die bisherige generische Syntax und Risikoeinstufung wurden durch Betriebsarten und deren konkrete Dateiwirkungen ersetzt.
