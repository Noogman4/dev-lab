---
id: "bunzip2"
name: "bunzip2"
command: "bunzip2"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "bzip2", "entpacken"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 4
reviewed_at: "2026-11-13"
locally_checked_version: "bzip2 1.0.8"
---

# bunzip2 – Bzip2-Dateien mit Kontrolle über die Originaldatei entpacken

## 1. Kurzbeschreibung

`bunzip2` dekomprimiert Daten im Bzip2-Format. Typisch ist eine Datei wie `notiz.txt.bz2`, aus der wieder `notiz.txt` wird. Es handelt sich um die Entpack-Variante des Programms `bzip2`.

**Für eigene Dateien sind keine Root-Rechte nötig.** Wichtig ist der normale Dateimodus: Nach erfolgreicher Dekompression kann die komprimierte Eingabedatei entfernt werden. Mit `-k` bleibt sie erhalten. Der Befehl ist daher nicht pauschal „sicher lesend“.

## 2. Was macht der Befehl?

`bunzip2` entspricht in seiner Grundaufgabe `bzip2 -d`. Der Inhalt wird dekomprimiert; die Ausgabe wird entweder als Datei angelegt oder mit `-c` auf die Standardausgabe geschrieben.

Ein Bzip2-Datenstrom ist kein Verzeichnisarchiv mit einer frei auswählbaren Mitgliederliste. Bei `sammlung.tar.bz2` entsteht zunächst `sammlung.tar`. Die darin enthaltenen Dateien werden erst in einem weiteren, gesondert zu prüfenden Schritt mit einem Archivwerkzeug ausgepackt.

Ohne Dateinamen liest das Programm von der Standardeingabe. Dass es dann auf Daten wartet, ist nicht automatisch ein Fehler. Die Zusammenhänge und Standardwirkungen beschreibt das [offizielle Bzip2-Handbuch](https://sourceware.org/bzip2/manual/manual.html#description).

## 3. Syntax

```text
bunzip2 [OPTIONEN] [DATEI.bz2 ...]
```

Die Schreibweise für die meisten vorsichtigen ersten Versuche lautet:

```bash
bunzip2 -k "notiz.txt.bz2"
```

`-k` ist eine Option; der folgende Name ist die Eingabedatei. Die aus dem Namen abgeleitete Ausgabedatei wäre hier `notiz.txt`. Bei mehreren Eingabedateien werden mehrere Dekompressionsvorgänge durchgeführt.

Für einen Test ohne neue Ausgabedatei:

```bash
bunzip2 -t "notiz.txt.bz2"
```

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Eingabedatei erhalten. | Empfehlenswert für die erste Dekompression. |
| `-c`, `--stdout` | Dekomprimierten Inhalt ausgeben. | Die Eingabe bleibt erhalten; die Shell kann eine Umleitung trotzdem überschreibend öffnen. |
| `-t`, `--test` | Integrität prüfen und Ausgabe verwerfen. | Keine wiederhergestellte Datei; kein Virenscan. |
| `-v`, `--verbose` | Zusätzliche Angaben ausgeben. | Praktisch zur Beobachtung des Ablaufs. |
| `-f`, `--force` | Bestimmte Schutzprüfungen übergehen. | Kann vorhandene Ausgabe ersetzen; nicht als allgemeine Reparatur verwenden. |
| `-s`, `--small` | Mit geringerem Speicherbedarf arbeiten. | Kann die Verarbeitung verlangsamen. |
| `--` | Ende der Optionen markieren. | Folgende Namen werden nicht als Optionen interpretiert. |

Die Optionen wurden mit der lokal installierten Bzip2-Hilfe abgeglichen. Das [Herstellerhandbuch zu den Optionen](https://sourceware.org/bzip2/manual/manual.html#options) erläutert auch die Unterschiede zwischen Dateiausgabe und Standardausgabe. `-1` bis `-9` sind Kompressionsparameter und keine sinnvollen Geschwindigkeitsstufen für das Wiederherstellen einer bereits komprimierten Datei.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsordner anlegen

```bash
uebung="$(mktemp -d -t netmon-bunzip2-XXXXXX)"
cd "$uebung"
pwd
```

Vor dem nächsten Schritt prüfen, dass der Verzeichniswechsel erfolgreich war. Es werden nur neue Übungsdaten verwendet.

### Schritt 2: Kleine komprimierte Eingabe erzeugen

```bash
printf '%s\n' 'Eine kleine Bzip2-Testnotiz.' | bzip2 -c > "notiz.txt.bz2"
```

`printf` liefert einen Text. Die Pipe gibt ihn an `bzip2` weiter. `-c` schreibt die komprimierten Daten auf die Standardausgabe; `>` lenkt diese in eine neue Testdatei. Der Dateiname ist bewusst noch nicht belegt.

### Schritt 3: Eingabe testen

```bash
bunzip2 -t "notiz.txt.bz2"
```

Das prüft die Integrität. Bei Erfolg kann die normale Ausgabe leer bleiben. Wichtig sind Fehlermeldungen und der unmittelbar danach verfügbare Rückgabewert `echo $?`. `0` bedeutet einen erfolgreichen Abschluss; ein anderer Wert muss eingeordnet werden.

### Schritt 4: Mit erhaltener Eingabe dekomprimieren

```bash
bunzip2 -kv "notiz.txt.bz2"
```

`-k` erhält die komprimierte Datei, `-v` zeigt zusätzliche Angaben. Anschließend sollten `notiz.txt.bz2` und `notiz.txt` vorhanden sein. Die Textdatei sollte die ursprüngliche Testnotiz enthalten.

### Schritt 5: Alternative ohne Dateiausgabe ansehen

```bash
bunzip2 -c "notiz.txt.bz2"
```

Für diesen bekannten Text zeigt das die Notiz direkt im Terminal. Es wird keine neue Zieldatei durch `bunzip2` angelegt. Für unbekannte Binärdaten sollte diese Anzeige nicht ungeprüft verwendet werden.

## 6. Typische Anwendungsfälle

**Eine heruntergeladene Textdatei wiederherstellen:** Zuerst Integrität und Herkunft prüfen, dann mit `-k` dekomprimieren. Für den Zielnamen ausreichenden Platz einplanen.

**Ein `.tar.bz2` vorbereiten:** `bunzip2 -k sammlung.tar.bz2` liefert eine TAR-Datei. Diese ist anschließend gesondert mit `tar` zu untersuchen. Die beiden Dateiformate und die dafür zuständigen Schritte nicht verwechseln.

**Daten an ein weiteres Werkzeug liefern:** `bunzip2 -c datei.bz2` kann Teil einer Pipe sein. Das nächste Programm bestimmt, was danach mit dem Datenstrom geschieht. Der lesende erste Schritt macht die gesamte Pipeline nicht automatisch ungefährlich.

**Vor einer Übertragung oder Archivierung prüfen:** `-t` kann beschädigte Bzip2-Daten erkennen, ohne die große unkomprimierte Ausgabe auf die Platte zu schreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Eingabe nach Erfolg entfernt

Ohne `-k` ist das Entfernen der komprimierten Eingabe nach erfolgreicher Dateiausgabe normales Verhalten. Das spart Platz, kann aber eine gewünschte zusätzliche Kopie verlieren lassen. Deshalb zuerst bewusst zwischen Dateimodus mit und ohne `-k` entscheiden.

### Speicherplatz und Datenmenge

Die unkomprimierte Ausgabe kann sehr viel größer als die `.bz2`-Datei sein. `-s` reduziert nicht die nötige Plattenkapazität. Auch eine Integritätsprüfung verbraucht Rechenzeit und verarbeitet fremde Daten.

### Überschreiben durch Programm oder Shell

`-f` kann den Schutz vor vorhandenen Ausgabedateien aufheben. Bei `bunzip2 -c quelle.bz2 > ziel` ist zusätzlich die Shell beteiligt: Sie kann `ziel` bereits leeren, bevor die Dekompression beginnt. Niemals Eingabe und umgeleitete Ausgabe auf denselben Pfad setzen.

### Format und Sicherheit

Ein Integritätstest bestätigt weder die Herkunft noch die Harmlosigkeit des Inhalts. Die Bzip2-Prüfsumme ist kein Ersatz für eine vertrauenswürdig erhaltene Signatur oder Referenz. Dekomprimierte Skripte nicht allein deshalb starten, weil der Test erfolgreich war.

**Root ist für die gezeigten Arbeitsweisen nicht erforderlich.** Ein unpassender Zielordner ist kein Grund, den gesamten Vorgang ungeprüft zu privilegieren.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| „already exists“ | Abgeleitete Zieldatei ist vorhanden. | Bestehende Datei prüfen oder einen neuen Ausgabeort wählen; nicht sofort `-f` einsetzen. |
| „not a bzip2 file“ | Falscher Inhalt, falsche Endung oder beschädigter Anfang. | Tatsächlichen Dateityp und Download prüfen. |
| Integritätsfehler | Daten unvollständig oder beschädigt. | Komprimiertes Original erhalten und weitere Kopie beziehungsweise erneuten Download prüfen. |
| Programm wartet ohne sichtbare Ausgabe | Keine Eingabedatei; es wird von stdin gelesen. | Den vorgesehenen Dateinamen ergänzen. |
| Platz reicht nicht | Die dekomprimierte Ausgabe ist größer als erwartet. | Freien Platz prüfen und teilweise Ausgaben bewusst behandeln. |

Das [Bzip2-Handbuch](https://sourceware.org/bzip2/manual/manual.html#description) nennt `0` für Erfolg, `1` für Umgebungs- und Ein-/Ausgabeprobleme, `2` für fehlerhafte komprimierte Daten und `3` für einen internen Konsistenzfehler. Meldung und Code gemeinsam auswerten.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit `-k` beginnen und das komprimierte Original behalten.
2. Für wichtige Dateien erst `-t` verwenden und dessen Ergebnis lesen.
3. Vor dem Schreiben abgeleiteten Zielnamen und freien Platz prüfen.
4. Einen bekannten Text von unbekannten Binärdaten unterscheiden.
5. Bei ungewöhnlichen Dateinamen Anführungszeichen und gegebenenfalls `--` verwenden.
6. Unerwartete globale Voreinstellungen prüfen: Die Bzip2-Familie kann Optionen aus `BZIP2` und `BZIP` übernehmen. Das ist ein Prüfpunkt bei abweichendem Verhalten.

**Prüfstand:** Mit Bzip2 1.0.8 wurden Integritätstest, Dekompression mit `-kv` und Ausgabe mit `-c` an einer eigenen kleinen Datei geprüft. Die Ausgabe entsprach den Testdaten, die komprimierte Eingabe blieb erhalten. Beschädigte Fremddateien, sehr große Daten und Wiederherstellung nach Datenträgerfehlern wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bzip2` | Standardmäßig komprimieren; mit `-d` dekomprimieren. |
| `bzcat` | Bzip2-Inhalte unmittelbar als Datenstrom ausgeben. |
| `bzip2recover` | Versucht bei bestimmten Schäden Datenblöcke zu gewinnen; kein garantierter Reparaturweg. |
| `tar` | Eine nach der Dekompression verbleibende TAR-Datei untersuchen oder auspacken. |
| `gunzip`, `unxz`, `unzstd` | Dekompression anderer Formate mit jeweils eigener Syntax und eigenen Voreinstellungen. |

Der Ausgangseintrag ist als Datensatz 4 in `index.json` erhalten. Die Dateilöschung im Standardmodus und die Trennung zwischen Integrität und Sicherheit sind gegenüber der bisherigen allgemeinen Erklärung ausdrücklich ergänzt.
