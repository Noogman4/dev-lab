---
id: "bzip2"
name: "bzip2"
command: "bzip2"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "bzip2"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 6
reviewed_at: "2026-11-13"
locally_checked_version: "bzip2 1.0.8"
---

# bzip2 – Einzelne Dateien komprimieren und wiederherstellen

## 1. Kurzbeschreibung

`bzip2` komprimiert Daten im Bzip2-Format. Bei einer Datei entsteht typischerweise eine Ausgabe mit der zusätzlichen Endung `.bz2`. Mit passenden Optionen kann dasselbe Programm auch dekomprimieren oder einen Integritätstest durchführen.

**Root-Rechte brauchst du für eigene Dateien nicht.** Der gewöhnliche Dateiaufruf ersetzt nach erfolgreicher Kompression die Eingabe durch die komprimierte Ausgabe. Wenn die ursprüngliche Datei erhalten bleiben soll, verwende ausdrücklich `-k`.

## 2. Was macht der Befehl?

Kompression versucht, denselben Inhalt platzsparender zu speichern. Sie verschlüsselt die Daten nicht. Ein Bzip2-Datenstrom enthält auch keine frei auswählbare Sammlung von Ordnern und Dateinamen wie ein ZIP-Archiv.

Mehrere Dateinamen im gewöhnlichen Dateimodus ergeben mehrere komprimierte Dateien. Für einen Ordnerbaum ist zuerst eine geeignete Archivierung nötig, etwa als TAR-Datei. Bei der gemeinsamen Ausgabe mehrerer Eingaben auf stdout entstehen dagegen aufeinanderfolgende Datenströme ohne eine unabhängige Mitgliederliste.

Bzip2 nutzt blockweise Verarbeitung. Kompressionsparameter beeinflussen unter anderem die Blockgröße und damit den Speicherbedarf. Die Grundlagen erläutert das [offizielle Bzip2-Handbuch](https://sourceware.org/bzip2/manual/manual.html).

## 3. Syntax

```text
bzip2 [OPTIONEN] [DATEI ...]
```

Typische Absichten sollten in der Befehlszeile sichtbar werden:

```bash
bzip2 -k "notiz.txt"
bzip2 -dk "notiz.txt.bz2"
bzip2 -t "notiz.txt.bz2"
```

Der erste Aufruf komprimiert und behält die Eingabe. Der zweite dekomprimiert mit erhaltener komprimierter Eingabe. Der dritte testet ohne wiederhergestellte Ausgabedatei. **Nicht alle drei Aufrufe direkt nacheinander am selben Ort ausführen:** Beim zweiten würde eine bereits vorhandene `notiz.txt` den üblichen Schutz vor einer belegten Ausgabe auslösen.

Ohne Dateinamen liest das Programm aus stdin und schreibt nach stdout. Binäre komprimierte Ausgabe gehört in eine Datei oder Pipe, nicht als lesbarer Text ins Terminal.

## 4. Wichtige Optionen

| Option | Bedeutung | Praktische Auswirkung |
| --- | --- | --- |
| `-k`, `--keep` | Eingabedatei behalten. | Verhindert deren normales Entfernen nach erfolgreichem Dateivorgang. |
| `-d`, `--decompress` | Dekomprimieren. | Aus komprimierten Daten wieder den ursprünglichen Inhalt gewinnen. |
| `-c`, `--stdout` | Ergebnis auf stdout schreiben. | Eingabe bleibt erhalten; Umleitung und nachfolgende Programme separat betrachten. |
| `-t`, `--test` | Datenintegrität prüfen. | Keine wiederhergestellte Datei; verarbeitet trotzdem die komprimierten Inhalte. |
| `-1` bis `-9` | Kompressionsblockgröße wählen. | 100 bis 900 kB; größer bedeutet nicht automatisch eine praktisch bessere Wahl. |
| `-s`, `--small` | Speicherbedarf reduzieren. | Kann Verarbeitung verlangsamen; keine Begrenzung der Ausgabedateigröße. |
| `-v`, `--verbose` | Zusätzliche Angaben ausgeben. | Erleichtert Beobachtung und Diagnose. |
| `-f`, `--force` | Schutzprüfungen übergehen. | Kann vorhandene Ausgabedateien ersetzen und weitere Standardprüfungen verändern. |
| `--` | Optionen beenden. | Anschließende Namen werden als Dateinamen interpretiert. |

`-1` bis `-9` sind bei Bzip2 Blockgrößenstufen und keine Zusage proportional steigender Geschwindigkeit oder Packwirkung. Beim Dekomprimieren steht die verwendete Blockgröße bereits in den Daten. Weitere Einzelheiten: [Optionen und Speicherbedarf im Herstellerhandbuch](https://sourceware.org/bzip2/manual/manual.html#options).

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Neue Testdaten vorbereiten

```bash
uebung="$(mktemp -d -t netmon-bzip2-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eigene Bzip2-Uebungsdaten.' > "notiz.txt"
```

Prüfe den erfolgreichen Verzeichniswechsel. Die Übung verwendet nur eine neu angelegte Textdatei. Eine kleine Datei muss durch Kompression nicht kleiner werden: Format- und Prüfungsinformationen benötigen ebenfalls Platz.

### Schritt 2: Mit erhaltener Quelle komprimieren

```bash
bzip2 -kv "notiz.txt"
```

`-k` hält die ursprüngliche Datei, `-v` zeigt zusätzliche Angaben. Danach sollten `notiz.txt` und `notiz.txt.bz2` vorhanden sein. Ohne `-k` würde die erfolgreiche Dateikompression die unkomprimierte Eingabe normalerweise entfernen.

### Schritt 3: Komprimierte Daten prüfen

```bash
bzip2 -t "notiz.txt.bz2"
```

Der Test liest und verarbeitet die Daten ohne eine wiederhergestellte Ausgabedatei. Eine leere normale Ausgabe kann Erfolg bedeuten. Fehlermeldungen lesen und den Rückgabewert unmittelbar mit `echo $?` kontrollieren.

### Schritt 4: Inhalt ohne Namenskollision zurücklesen

```bash
bzip2 -dc "notiz.txt.bz2"
```

`-d` dekomprimiert, `-c` liefert den Inhalt auf stdout. So lässt sich die bekannte Testnotiz ansehen, obwohl die ursprüngliche `notiz.txt` noch existiert. Ein normaler Dateiaufruf `-dk` würde an diesem Ort einen vorhandenen Zielnamen antreffen.

### Schritt 5: Unter einem neuen Namen wiederherstellen

```bash
bzip2 -dc "notiz.txt.bz2" > "kontrolle.txt"
```

Die Shell legt `kontrolle.txt` an. Vergleiche deren Inhalt mit `notiz.txt`. Verwende bewusst einen neuen Namen; eine vorhandene Datei könnte durch die Umleitung bereits vor Beginn der Dekompression geleert werden.

## 6. Typische Anwendungsfälle

**Eine große Textdatei platzsparend ablegen:** Mit `-k` bleibt die direkt nutzbare Originaldatei erhalten. Ob eine zusätzliche komprimierte Kopie sinnvoll ist, hängt vom tatsächlichen Platzgewinn und dem späteren Zugriff ab.

**Vorhandene Bzip2-Daten dekomprimieren:** `-d` wählt die Gegenrichtung. Für eine getrennt erhaltene Eingabe zusätzlich `-k` setzen oder die Ausgabe ausdrücklich als Datenstrom verwenden.

**Ein TAR-Archiv nachträglich komprimieren:** Eine vorher passend erstellte TAR-Datei kann als einzelne Datei komprimiert werden. Bzip2 bewahrt dabei den TAR-Datenstrom, übernimmt aber nicht die Aufgaben des Archivwerkzeugs beim richtigen Erfassen von Metadaten.

**Integrität vor längerer Aufbewahrung prüfen:** `-t` erkennt bestimmte Beschädigungen. Für wichtige Sicherungen gehört zusätzlich eine tatsächlich kontrollierte Wiederherstellung zum Ablauf.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Dateiersetzung ist Standardverhalten

Bei erfolgreicher Dateikompression oder Dateidekompression wird die Eingabe normalerweise entfernt. Das ist der wichtigste Unterschied zu einem bloßen Anzeigeprogramm. `-k` gehört in ein Beispiel, wenn Originale erhalten bleiben sollen.

### Mehr Platz statt weniger Platz

Bereits komprimierte Daten und sehr kleine Eingaben können gering oder überhaupt nicht profitieren. Während der Verarbeitung und bei zusätzlichen Kopien muss genügend freier Speicherplatz vorhanden sein. Beim Entpacken kann die unkomprimierte Datei wesentlich größer werden.

### Keine Verschlüsselung und keine vollständige Sicherung

Wer die `.bz2`-Datei lesen kann, kann sie grundsätzlich auch dekomprimieren. Kompression ist kein Zugriffsschutz. Ebenso ersetzt eine einzelne komprimierte Datei kein vollständiges Systembackup mit passender Metadatenbehandlung und Wiederherstellung.

### Schutzoptionen nicht übergehen

`-f` ist nicht einfach eine Komfortoption gegen jede Fehlermeldung. Es verändert Schutzverhalten, unter anderem beim Überschreiben und bei bestimmten Eingaben. Vor einer Verwendung die konkrete Ursache verstehen und eine eigene Kopie behalten.

### Fremde Daten und Umleitungen

Die Integritätsprüfung sagt nichts über Herkunft oder Harmlosigkeit. Teilausgaben können vor einem Fehler bereits geschrieben worden sein. Eingabe und umgeleitete Ausgabe niemals auf denselben Pfad legen. Die Shell kennt die Kompressionsabsicht nicht.

**Root ist für die Beispiele nicht nötig.** Nur Daten bearbeiten, für die eine passende Lese- und Schreibberechtigung besteht.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Zieldatei existiert schon | Eine frühere Ausgabe oder das erhaltene Original belegt den Namen. | Datei prüfen oder einen getrennten Zielnamen wählen. |
| Datei wird nicht kleiner | Kleine oder schon komprimierte Daten. | Ergebnis vergleichen; keinen Fehler allein aus geringer Ersparnis ableiten. |
| Ordner kann nicht wie erwartet verarbeitet werden | Bzip2 ist kein rekursiver Verzeichnisarchivierer. | Zunächst geeignet archivieren, nicht erfundene ZIP-Optionen übernehmen. |
| Integritätstest meldet einen Fehler | Unter anderem unvollständiger oder beschädigter Datenstrom. | Eingabe erhalten und Herkunft beziehungsweise weitere Kopien prüfen. |
| Keine Daten nach einem Aufruf ohne Dateiname | Das Programm wartet auf stdin. | Vorgesehenen Eingabepfad angeben. |
| Verhalten weicht von Beispiel ab | Varianten, Voreinstellungen oder belegte Ziele. | Version sowie `BZIP2` und `BZIP` prüfen. |

Rückgabewerte: `0` bezeichnet Erfolg, `1` beispielsweise Ein-/Ausgabe- und Umgebungsprobleme, `2` fehlerhafte komprimierte Daten und `3` interne Konsistenzfehler. Die [offizielle Beschreibung](https://sourceware.org/bzip2/manual/manual.html#description) erläutert die Einordnung. Eine vorhandene Datei allein genügt nicht als Erfolgskriterium.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erste Versuche ausschließlich mit kleinen, eigenen Testdateien durchführen.
2. `-k` bewusst verwenden, solange die Eingabe noch gebraucht wird.
3. Für die Gegenrichtung ausdrücklich `-d` schreiben.
4. Vor einer Umleitung Zielnamen prüfen und nachher Inhalt sowie Rückgabewert kontrollieren.
5. Kompressionsgrad nicht mit Vertraulichkeit oder Integrität verwechseln.
6. Eine TAR-Datei und deren Bzip2-Kompression als zwei verschiedene Verarbeitungsschritte verstehen.
7. Bei Problemen nicht automatisch `-f` oder `sudo` ergänzen.

**Prüfstand:** Mit Bzip2 1.0.8 wurden Kompression mit `-kv`, Integritätstest und Ausgabe mit `-dc` an kleinen eigenen Dateien geprüft. Die rückgewonnenen Daten entsprachen der Eingabe. An einer zusätzlichen neu angelegten Testdatei wurde das normale Entfernen der Eingabe ohne `-k` bestätigt. Es wurden keine Originaldateien des Benutzers verändert.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `bunzip2` | Entpack-Variante derselben Werkzeugfamilie. |
| `bzcat` | Dekomprimierte Inhalte auf stdout ausgeben. |
| `bzip2recover` | Bestimmte beschädigte Datenblöcke untersuchen beziehungsweise gewinnen; kein Erfolg garantiert. |
| `gzip`, `xz`, `zstd` | Andere Kompressionsformate und Verfahren. Optionen sind nicht austauschbar. |
| `tar` | Dateien und Verzeichnisse vor einer Kompression bündeln. |

Ausgangseintrag: Datensatz 6 in `index.json`. Gegenüber dem bisherigen Hilfe-Platzhalter sind die Richtungswahl, die Originaldateibehandlung und die konkrete Schreibwirkung ergänzt.
