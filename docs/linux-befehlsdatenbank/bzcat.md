---
id: "bzcat"
name: "bzcat"
command: "bzcat"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive", "kompression", "bzip2", "datenstrom"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 5
reviewed_at: "2026-11-13"
locally_checked_version: "bzip2 1.0.8"
---

# bzcat – Bzip2-Inhalte ausgeben, ohne die Quelldatei zu ersetzen

## 1. Kurzbeschreibung

`bzcat` dekomprimiert Bzip2-Dateien und schreibt deren Inhalt auf die Standardausgabe. Bei einem normalen Aufruf im Terminal wird der Inhalt dort angezeigt; mit einer Pipe kann ihn ein weiteres Programm verarbeiten.

**Root-Rechte sind zum Lesen eigener Dateien nicht erforderlich.** Im normalen Aufruf bleibt die komprimierte Eingabe erhalten. „Überwiegend lesend“ gilt für diesen Schritt; Umleitungen und nachgeschaltete Programme können trotzdem Daten verändern.

## 2. Was macht der Befehl?

Die Grundfunktion entspricht `bzip2 -dc`: dekomprimieren und auf stdout schreiben. Anders als eine Dateidekompression mit `bunzip2` wird dabei kein Ausgabename aus der Endung abgeleitet und die Eingabedatei nicht durch eine entpackte Datei ersetzt.

Bei mehreren Dateinamen schreibt `bzcat` die dekomprimierten Inhalte nacheinander in denselben Ausgabestrom. Die Dateinamen werden nicht als Trennzeilen ergänzt. Ohne abschließenden Zeilenumbruch in der ersten Datei können zwei Textinhalte unmittelbar ineinander übergehen.

Wenn die komprimierten Daten ein TAR-Archiv enthalten, ist die Ausgabe wieder ein TAR-Datenstrom. `bzcat` macht daraus nicht selbst die einzelnen Dateien und Ordner. Beschreibung und Varianten erklärt das [offizielle Bzip2-Handbuch](https://sourceware.org/bzip2/manual/manual.html#description).

## 3. Syntax

```text
bzcat [OPTIONEN] [DATEI.bz2 ...]
```

Für bekannte Textdaten:

```bash
bzcat "notiz.txt.bz2"
```

Als Bestandteil einer Anzeige mit seitenweisem Lesen:

```bash
bzcat "protokoll.txt.bz2" | less
```

Die Pipe übergibt die Ausgabe an `less`. Dadurch wird keine neue entpackte Datei durch `bzcat` angelegt. Gibt man keinen Dateinamen an, liest das Programm aus stdin und kann auf weitere Eingaben warten.

## 4. Wichtige Optionen

| Option | Bedeutung | Einordnung |
| --- | --- | --- |
| `-s`, `--small` | Mit geringerem Speicherbedarf dekomprimieren. | Kann langsamer sein; begrenzt nicht automatisch die Gesamtmenge der Ausgabe. |
| `-v`, `--verbose` | Zusätzliche Verarbeitungsangaben ausgeben. | Datenstrom und Diagnoseausgabe unterscheiden. |
| `-q`, `--quiet` | Bestimmte nicht wesentliche Meldungen unterdrücken. | Zum ersten Prüfen eher weglassen, damit Hinweise sichtbar bleiben. |
| `--` | Ende der Optionen markieren. | Hilfreich für Namen, die mit einem Bindestrich beginnen. |
| `-h`, `--help` | Hilfe anzeigen. | Die Hilfe kann die gesamte Bzip2-Werkzeugfamilie beschreiben. |

`-c` ist für den üblichen `bzcat`-Aufruf bereits durch den Programmnamen vorgegeben. Weitere Familienoptionen nicht blind kombinieren: Der Name `bzcat` allein ist keine Garantie, dass beliebige zusätzliche Schalter dieselbe Arbeitsweise beibehalten. Die Optionen sind im [Herstellerhandbuch](https://sourceware.org/bzip2/manual/manual.html#options) und in der lokalen Hilfe von Bzip2 1.0.8 beschrieben.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen Übungsordner verwenden

```bash
uebung="$(mktemp -d -t netmon-bzcat-XXXXXX)"
cd "$uebung"
pwd
```

Erst weiterarbeiten, wenn der Wechsel gelungen ist. So werden im folgenden Beispiel keine vorhandenen Dokumente als Übungsdateien verwendet.

### Schritt 2: Zwei kleine Eingaben erzeugen

```bash
printf '%s\n' 'Erste Bzip2-Zeile.' | bzip2 -c > "eins.txt.bz2"
printf '%s\n' 'Zweite Bzip2-Zeile.' | bzip2 -c > "zwei.txt.bz2"
```

Jeder Aufruf erzeugt einen eigenen Bzip2-Datenstrom. Die Umleitungen schreiben die Dateien im neuen Arbeitsordner. Bei einer Wiederholung würden dieselben Zieldateien überschrieben.

### Schritt 3: Einen Inhalt anzeigen

```bash
bzcat "eins.txt.bz2"
```

Erwartet wird `Erste Bzip2-Zeile.` mit einem Zeilenumbruch. Die Datei `eins.txt.bz2` bleibt erhalten. Es entsteht keine Datei namens `eins.txt`.

### Schritt 4: Beide Inhalte in Reihenfolge ausgeben

```bash
bzcat "eins.txt.bz2" "zwei.txt.bz2"
```

Nun erscheinen beide Zeilen in der angegebenen Reihenfolge. Das eignet sich für zusammengehörige Textdaten, ersetzt aber keine archivierte Zuordnung einzelner Dateien zu ihren Namen.

### Schritt 5: Bei Bedarf in eine neue Datei schreiben

```bash
bzcat "eins.txt.bz2" > "wiederhergestellt.txt"
```

Hier schreibt die Shell die Ausgabe in `wiederhergestellt.txt`. Dieser Schritt ist bewusst nicht mehr nur eine Anzeige. Verwende einen neuen Namen und prüfe Rückgabewert sowie Inhalt. Die Eingabe und die Ausgabedatei dürfen niemals derselbe Pfad sein.

## 6. Typische Anwendungsfälle

**Komprimierte Protokolle nachlesen:** Text kann ohne dauerhaft angelegte Zwischenkopie an einen Pager geliefert werden. Zugriffsrechte und sensible Inhalte gelten trotzdem unverändert.

**Text durchsuchen oder auswerten:** Der dekomprimierte Datenstrom kann an passende Werkzeuge weitergereicht werden. Suchprogramme dürfen das Textformat und die Zeichenkodierung nicht ungeprüft voraussetzen.

**Eine Datei unter einem frei gewählten Namen wiederherstellen:** Eine Umleitung wählt den Zielpfad unabhängig von der `.bz2`-Endung. Dadurch ist die Kontrolle über den Zielnamen größer, die Verantwortung für Überschreiben liegt aber bei der Shell.

**Zusammengehörige Datenströme verbinden:** Mehrere Eingaben lassen sich nacheinander ausgeben. Das ist nur passend, wenn das nachfolgende Datenformat eine solche Verbindung sinnvoll zulässt.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Lesende Quelle, möglicherweise schreibende Pipeline

`bzcat quelle.bz2` verändert die Eingabe normalerweise nicht. `bzcat quelle.bz2 > ziel` kann hingegen eine vorhandene Datei leeren. Noch bevor `bzcat` den ersten Datenblock geprüft hat, kann die Shell das Ziel bereits geöffnet haben. Ein späterer Fehler stellt den früheren Zielinhalt nicht wieder her.

### Nicht jeder Inhalt ist Text

Eine `.bz2`-Datei kann Binärdaten enthalten. Direkte Ausgabe kann das Terminal mit unlesbaren Daten oder Steuerzeichen füllen. Auch ein harmloser Text kann sehr groß werden. Für unbekannte Inhalte zuerst Dateityp, Herkunft und Größenverhältnisse prüfen.

### Integrität ist keine Echtheitsprüfung

Bzip2-Daten enthalten Integritätsinformationen. Das Erkennen eines beschädigten Datenstroms bestätigt nicht, wer ihn erstellt hat. Die Verarbeitung kann außerdem bereits eine Teilausgabe geliefert haben, bevor ein Fehler sichtbar wird. Eine umgeleitete Datei deshalb nicht allein wegen ihrer Existenz als vollständig ansehen.

### Vorzeitiges Ende eines Verbrauchers

Wenn ein nachgeschaltetes Programm die Pipe früh schließt, kann `bzcat` einen Schreibfehler melden. Das ist anders einzuordnen als ein nachgewiesener Fehler im komprimierten Inhalt. Für einen gezielten vollständigen Integritätstest ist `bzip2 -t datei.bz2` die klarere Absicht.

**Kein `sudo` für normale Anzeige erforderlich.** Für geschützte Protokolle ist eine ausdrücklich berechtigte Lesemöglichkeit zu prüfen; dieses Dokument erteilt keine zusätzliche Freigabe.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Reaktion nach `bzcat` ohne Argument | Es wird auf stdin gewartet. | Vorgesehenen Dateinamen angeben. |
| Unlesbare Ausgabe | Inhalt ist kein geeigneter Text. | Anzeige beenden und Dateiformat prüfen. |
| „not a bzip2 file“ | Falsches Format oder fehlerhafte Daten. | Nicht allein auf die Dateiendung vertrauen. |
| Zwei Textteile laufen zusammen | Die erste Eingabe endet ohne Zeilenumbruch. | Dateigrenzen bei der Auswertung ausdrücklich berücksichtigen. |
| Zieldatei trotz Fehler vorhanden | Shell hat sie bereits angelegt oder eine Teilausgabe erhalten. | Ergebnis nicht ungeprüft weiterverwenden. |
| Meldungen vermischen sich mit Daten | Daten- und Diagnoseausgabe wurden zusammengeführt. | stdout und stderr bei maschineller Verarbeitung getrennt behandeln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zunächst die beiden bekannten Testzeilen verwenden.
2. Die Dateien vor und nach dem Aufruf kontrollieren: `bzcat` braucht keine separate entpackte Datei, um Text auszugeben.
3. Vor einer Umleitung prüfen, ob der Zielname bereits existiert.
4. Für sehr große Textausgaben einen geeigneten Pager nutzen statt das ganze Terminal zu füllen.
5. Fehlerausgabe nicht achtlos mit in eine Datendatei umleiten.
6. Bei einer Pipeline die Wirkung jedes beteiligten Befehls betrachten.
7. Bei ungewöhnlichem Verhalten mögliche Optionen in den Umgebungsvariablen `BZIP2` und `BZIP` prüfen.

**Prüfstand:** Unter Bzip2 1.0.8 wurden eine einzelne Eingabe, zwei aufeinanderfolgende Eingaben sowie die speichersparende Ausgabe mit `-s` geprüft. Die Ausgaben stimmten bytegenau mit den Testtexten überein, die komprimierten Eingaben blieben unverändert. Pager, große Protokolle und beschädigte Fremddaten wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bzip2 -dc` | Ausdrückliche Schreibweise derselben Grundaufgabe. |
| `bunzip2` | Dekomprimiert standardmäßig in eine Datei; Erhalt der Eingabe mit `-k` beachten. |
| `bzgrep` | Suchen in Bzip2-komprimierten Texten, sofern das Werkzeug vorhanden ist. |
| `zcat`, `xzcat`, `zstdcat` | Ähnliche Datenstrom-Ausgabe für andere Formate. |
| `less` | Text seitenweise lesen; ist kein Archivprüfer. |

Der ursprüngliche NetMon-Eintrag bleibt unter Datensatz 5 in `index.json` erhalten. Die neue Erklärung unterscheidet ausdrücklich Datenstrom, Umleitung und Datei-Dekompression.
