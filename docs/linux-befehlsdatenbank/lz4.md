---
id: "lz4"
name: "lz4"
command: "lz4"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "lz4", "datenstrom"]
status: "Ausgearbeitet; Quellen geprüft, praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 10
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle CLI-Dokumentation v1.10.0 geprüft"
---

# lz4 – Daten mit ausdrücklich gewählter Richtung und Ausgabe komprimieren

## 1. Kurzbeschreibung

`lz4` komprimiert und dekomprimiert Daten im LZ4-Format. Das Verfahren wird häufig für Abläufe verwendet, bei denen Verarbeitungsaufwand und Datendurchsatz wichtig sind. Der tatsächliche Nutzen hängt von Daten, Datenträger und Einstellungen ab; eine bestimmte Geschwindigkeit ist nicht garantiert.

**Für eigene Dateien sind keine Root-Rechte nötig.** Das Programm schreibt Ausgaben, behält Eingabedateien im normalen Verhalten aber bei. Das unterscheidet es von gewöhnlichen Dateiaufrufen vieler gzip-ähnlicher Werkzeuge.

## 2. Was macht der Befehl?

`lz4` verarbeitet einen komprimierten oder unkomprimierten Datenstrom. Eine `.lz4`-Datei ist nicht automatisch ein Verzeichnisarchiv mit einzeln wählbaren Mitgliedern. Für Ordnerbäume muss ein passendes Archivierungsverfahren hinzukommen.

Zwei Besonderheiten sind für korrekte Befehle entscheidend: `lz4 eingabe ausgabe` benennt normalerweise eine Eingabe und ein Ziel, nicht zwei unabhängige Eingaben. Wird das Ziel weggelassen, hängt die implizite Ausgabe davon ab, ob stdout ein Terminal oder eine Weiterleitung ist. Für nachvollziehbare Skripte sollten Richtung und Ausgabe deshalb ausdrücklich gewählt werden.

Diese Unterschiede sind im [offiziellen LZ4-Handbuch der Version 1.10.0](https://raw.githubusercontent.com/lz4/lz4/v1.10.0/programs/lz4.1.md) beschrieben.

## 3. Syntax

```text
lz4 [OPTIONEN] EINGABE AUSGABE
lz4 -c [OPTIONEN] EINGABE > AUSGABE.lz4
lz4 -d [OPTIONEN] EINGABE.lz4 AUSGABE
```

Für einen gut nachvollziehbaren Ablauf:

```bash
lz4 -z "notiz.txt" "notiz.txt.lz4"
lz4 -t "notiz.txt.lz4"
lz4 -d "notiz.txt.lz4" "kontrolle.txt"
```

`-z` fordert Kompression, `-d` Dekompression an. Die unterschiedlichen Namen trennen Quelle und Ziel. Eine Dateiendung kann sonst eine Arbeitsweise nahelegen; ein ausdrücklicher Schalter ist für eine Anleitung verständlicher.

**Prüfpunkt:** `lz4` ist in der hier verwendeten Umgebung nicht installiert. Die Befehle sind anhand der offiziellen CLI-Dokumentation geprüft, aber hier nicht praktisch ausgeführt worden.

## 4. Wichtige Optionen

| Option | Bedeutung | Praktischer Hinweis |
| --- | --- | --- |
| `-z`, `--compress` | Komprimieren. | Richtung unabhängig von einer möglicherweise irreführenden Endung festlegen. |
| `-d`, `--decompress` | Dekomprimieren. | Ausgabe ist der ursprüngliche Datenstrom, nicht automatisch ein Ordnerbaum. |
| `-c` | Ausgabe ausdrücklich auf stdout schreiben. | Die Shell verwaltet eine mögliche Zieldatei. |
| `-t`, `--test` | Daten prüfen und dekomprimierte Ausgabe verwerfen. | Kein Herkunfts- oder Schadsoftwaretest. |
| `--list` | Informationen über LZ4-Dateien anzeigen. | Eine technische Übersicht ist keine vollständige Ressourcenbegrenzung. |
| `-m` | Mehrere Eingaben verarbeiten. | Verändert die Interpretation nachfolgender Dateinamen. |
| `-1`, `-9` | Unterschiedliche Kompressionsstufen. | Höhere Stufe gegen Aufwand und tatsächliche Einsparung abwägen. |
| `-f`, `--force` | Schutzprüfungen übergehen. | Kann vorhandene Ziele ohne Rückfrage überschreiben. |
| `--rm` | Eingaben nach erfolgreicher Verarbeitung entfernen. | Ändert das normale Beibehalten der Originale. |

Weitere Schalter und Versionsunterschiede beschreibt die [Distributions-Manpage](https://manpages.debian.org/trixie/lz4/lz4.1.en.html#OPTIONS). Neue Optionen aus einem Entwicklungszweig nicht automatisch auf ein älteres installiertes Paket übertragen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Installation und Hilfe prüfen

```bash
command -v lz4
lz4 --version
lz4 --help
```

Nur fortfahren, wenn das Programm vorhanden ist und die benötigten Schalter anbietet. Paketinstallation ist eine eigene Systemänderung und nicht Bestandteil dieser Übung.

### Schritt 2: Getrennte Testdaten vorbereiten

```bash
uebung="$(mktemp -d -t netmon-lz4-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eigene LZ4-Testnotiz.' > "notiz.txt"
```

Prüfe den erfolgreichen Verzeichniswechsel. Die kleine Datei dient zum Verstehen des Ablaufs, nicht zu einer aussagekräftigen Geschwindigkeitsmessung.

### Schritt 3: Mit ausdrücklich benanntem Ziel komprimieren

```bash
lz4 -z "notiz.txt" "notiz.txt.lz4"
```

Die erste Datei ist die Eingabe, die zweite das Ziel. Das normale Beibehalten der Quelle ist hier beabsichtigt. Prüfe vor dem Aufruf, dass das Ziel noch nicht belegt ist.

### Schritt 4: Datenstrom prüfen

```bash
lz4 -t "notiz.txt.lz4"
```

Das prüft die Verarbeitbarkeit und vorhandene Integritätsinformationen, ohne den entpackten Inhalt als normale Datei abzulegen. Meldung und Rückgabewert müssen ausgewertet werden.

### Schritt 5: Unter einem anderen Namen wiederherstellen

```bash
lz4 -d "notiz.txt.lz4" "kontrolle.txt"
```

Vergleiche danach `kontrolle.txt` mit der ursprünglichen Textdatei. Erst ein überprüfter Vergleich zeigt, dass der Beispielablauf am Zielsystem wie erwartet funktioniert hat. Die bloße Existenz von drei Dateien genügt dafür nicht.

## 6. Typische Anwendungsfälle

**Datenströme mit geringem Verarbeitungsaufwand komprimieren:** Ob dies für einen konkreten Export sinnvoll ist, hängt unter anderem vom Engpass zwischen Rechenleistung und Datenübertragung ab.

**Eine einzelne Datei für einen vorhandenen LZ4-Ablauf erzeugen:** Die empfangende Seite muss das Format und gegebenenfalls benötigte Parameter unterstützen. Eine bekannte Endung allein garantiert keine Kompatibilität.

**Ergebnisse in einer Pipeline weiterreichen:** `-c` macht stdout ausdrücklich zum Ziel. Damit ist klarer, ob ein nachfolgendes Programm komprimierte oder unkomprimierte Daten erhalten soll.

**Mehrere Dateien gesondert bearbeiten:** `-m` kann mehrere Eingaben in getrennte Ergebnisse überführen. Das ist ein anderer Modus als die Schreibweise mit einer Eingabe und einem ausdrücklichen Ausgabenamen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Eingabe und Ausgabe verwechselt

Wer die Syntax wie bei `gzip` liest, kann den zweiten Dateinamen irrtümlich für eine weitere Quelle halten. Im normalen Zweidateiaufruf ist er das Ziel. Bevor geschrieben wird, jeden Pfad seiner Rolle zuordnen.

### Implizite Ausgabe verändert sich

Ein Aufruf kann je nach Terminal- oder Pipe-Umgebung ein anderes implizites Ziel verwenden. In Skripten deshalb ausdrücklich `-c` oder einen Ausgabenamen benutzen. Ein interaktiver Versuch allein beweist nicht dasselbe Verhalten in einer Automatisierung.

### Originale entfernen und Ziele überschreiben

`--rm` fordert das Entfernen der Eingabe nach Erfolg an. `-f` kann vorhandene Ziele ersetzen. Die vorsichtigen Beispiele benötigen beides nicht. Eine Shell-Umleitung kann ein Ziel zudem schon vor erfolgreicher Verarbeitung leeren.

### Prüfsummen sind keine Authentifizierung

Das [offizielle LZ4-Frame-Format](https://github.com/lz4/lz4/blob/dev/doc/lz4_Frame_format.md) beschreibt unter anderem optionale Prüfinformationen. Ihr Vorhandensein und ihre Prüfung sind format- und implementationsabhängig. Daraus keine Garantie für die Herkunft oder Harmlosigkeit beliebiger Inhalte ableiten.

### Große Daten und spezielle Formate

Entpackte Ausgaben können viel größer sein als die Eingabe. Ein Frame-Format und ein roher LZ4-Block sind außerdem nicht automatisch austauschbar. Die Daten müssen zum erwarteten Decoder passen; keine pauschale Behauptung „alle LZ4-Daten sind gleich“ verwenden.

**Root ist für die eigenen Übungsdateien nicht nötig.** Verfügbarkeit des Programms und Systempaketänderungen sind getrennt zu behandeln.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| `command not found` | LZ4-CLI fehlt. | Paket und vorgesehene Bereitstellung der Distribution prüfen. |
| Unerwartetes Ausgabeziel | Auf implizite Ausgabe verlassen. | `-c` oder Zielpfad ausdrücklich setzen. |
| Zweite Datei wurde als Ziel behandelt | Zweidateisyntax mit Mehrfachmodus verwechselt. | Bei mehreren Eingaben den vorgesehenen Modus prüfen. |
| Ziel existiert schon | Ergebnis früherer Verarbeitung. | Bestehenden Inhalt prüfen oder neuen Zielnamen wählen. |
| Daten werden nicht erkannt | Falsches Format, unvollständiger Datenstrom oder andere LZ4-Variante. | Herkunft und Erzeugungsweg prüfen. |
| Unbekannte Option | Installierte Version bietet sie nicht an. | Lokale Hilfe statt fremden Entwicklungsstand verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Richtung und beide Pfade ausdrücklich angeben.
2. Für den ersten Ablauf eine neue kleine Textdatei verwenden.
3. Keine Originalentfernung und kein erzwungenes Überschreiben ergänzen.
4. Danach Integrität prüfen und eine getrennte Wiederherstellung vergleichen.
5. Den Mehrfachmodus nicht mit der Eingabe-/Ausgabeschreibweise mischen.
6. Aus einem kleinen Funktionstest keine Leistungszusage ableiten.
7. Neue Versionseigenschaften ausdrücklich als Prüfpunkt behandeln.

**Prüfstand:** Die Beschreibung wurde mit der offiziellen CLI-Dokumentation für v1.10.0 sowie der Distributions-Manpage abgeglichen. Die lokale Umgebung enthält kein `lz4`-Programm; sämtliche praktischen Schritte sind deshalb offen und nicht als erfolgreich ausgeführt ausgewiesen. Die generische Altsyntax ist durch ausdrücklich erklärte Pfadrollen ersetzt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `unlz4` | Je nach Installation ein dekomprimierender Alias. |
| `lz4cat` | Alias zur Datenstromausgabe mit weiteren Vorgaben; separat dokumentiert. |
| `gzip`, `bzip2`, `xz`, `zstd` | Andere Kompressionsformate; Syntax und Standardwirkungen unterscheiden sich. |
| `tar` | Kann eine Dateisammlung vor einem Kompressionsschritt bündeln. |
| `cmp` | Eine kleine wiederhergestellte Datei mit dem Original vergleichen. |

Der Ausgangseintrag bleibt unter Datensatz 10 in `index.json` erhalten. Die neue Dokumentation unterscheidet ausdrücklich Quellenprüfung von fehlender praktischer Prüfung.
