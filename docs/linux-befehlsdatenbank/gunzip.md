---
id: "gunzip"
name: "gunzip"
command: "gunzip"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "gzip", "entpacken"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 8
reviewed_at: "2026-11-13"
locally_checked_version: "GNU gzip 1.12"
---

# gunzip – Gzip-Dateien dekomprimieren und die Quelle bewusst erhalten

## 1. Kurzbeschreibung

`gunzip` stellt den Inhalt komprimierter Gzip-Dateien wieder her. Aus `bericht.txt.gz` wird im gewöhnlichen Dateimodus `bericht.txt`. Es ist die Entpack-Variante von `gzip` und entspricht grundsätzlich dessen Aufruf mit `-d`.

**Für eigene Dateien und einen eigenen Zielort brauchst du keine Root-Rechte.** Nach einer erfolgreichen normalen Dateidekompression wird die `.gz`-Eingabe üblicherweise entfernt. Mit `-k` bleibt sie erhalten. Ein solcher Aufruf ist daher keine bloße Leseoperation.

## 2. Was macht der Befehl?

Gzip-Kompression speichert einen Datenstrom platzsparender. `gunzip` macht diese Kompression rückgängig. Der dadurch erhaltene Inhalt kann Text, Binärdaten oder ein anderes Archiv sein.

Bei `sammlung.tar.gz` bleibt nach dem Dekomprimieren zunächst eine TAR-Datei. Erst ein Archivwerkzeug behandelt die darin enthaltene Verzeichnisstruktur. Gzip und TAR erfüllen unterschiedliche Aufgaben; die doppelte Endung ist ein Hinweis auf diese zwei Schichten.

Ohne Dateinamen liest `gunzip` aus der Standardeingabe und schreibt auf die Standardausgabe. Im Dateimodus wird ein Zielname aus der Eingabe beziehungsweise mit passenden Optionen aus gespeicherten Angaben abgeleitet. Die Grundlagen beschreibt die [GNU-gzip-Manpage bei Debian](https://manpages.debian.org/trixie/gzip/gunzip.1.en.html#DESCRIPTION).

## 3. Syntax

```text
gunzip [OPTIONEN] [DATEI.gz ...]
```

Für die erste Wiederherstellung mit erhaltener Quelle:

```bash
gunzip -k "bericht.txt.gz"
```

Für eine Integritätsprüfung ohne entpackte Ausgabedatei:

```bash
gunzip -t "bericht.txt.gz"
```

Für einen ausdrücklich gewählten Datenstrom:

```bash
gunzip -c "bericht.txt.gz"
```

Der letzte Aufruf ist nur für bekannte Textinhalte direkt im Terminal sinnvoll. Er bedeutet nicht, dass jede `.gz`-Datei lesbaren Text enthält.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Komprimierte Eingabedatei behalten. | Verhindert deren normales Entfernen nach erfolgreicher Dateiausgabe. |
| `-c`, `--stdout` | Dekomprimierten Inhalt auf stdout schreiben. | Keine namensabhängige Zieldatei durch `gunzip`; Shell-Umleitungen gesondert beachten. |
| `-t`, `--test` | Integrität prüfen. | Kein Herkunfts- oder Schadsoftwaretest. |
| `-v`, `--verbose` | Mehr Verarbeitungsangaben zeigen. | Erleichtert Diagnose, ändert nicht die Datenprüfung in einen Sicherheitsnachweis. |
| `-l`, `--list` | Größen- und Namensangaben anzeigen. | Keine vollständige Mitgliederliste wie bei einem ZIP-Archiv. |
| `-f`, `--force` | Schutzprüfungen übergehen. | Kann vorhandene Ausgaben ersetzen und weitere Standardbehandlung ändern. |
| `-N`, `--name` | Gespeicherten ursprünglichen Namen und Zeitangaben berücksichtigen. | Der erwartete Zielname kann sich dadurch ändern. |
| `-n`, `--no-name` | Gespeicherten ursprünglichen Namen nicht wiederherstellen. | Bei der Dekompression grundsätzlich die normale Namensabsicht. |
| `-r`, `--recursive` | Verzeichnisse rekursiv bearbeiten. | Erfasst mehr Dateien; ohne `-k` können entsprechend viele Eingaben ersetzt werden. |
| `--` | Ende der Optionen markieren. | Für ungewöhnliche Dateinamen hilfreich. |

Die lokale GNU-gzip-Hilfe und die [Distributionsreferenz](https://manpages.debian.org/trixie/gzip/gunzip.1.en.html#OPTIONS) sind für konkrete Versionen maßgeblich. Kompressionsstufen wie `-9` machen das Entpacken einer vorhandenen Datei nicht zu einer neuen stärkeren Kompression.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen neuen Arbeitsordner verwenden

```bash
uebung="$(mktemp -d -t netmon-gunzip-XXXXXX)"
cd "$uebung"
pwd
```

Nach einem fehlgeschlagenen Verzeichniswechsel nicht mit den folgenden Umleitungen fortfahren. Der neue Ordner soll die Übungsdaten vollständig von vorhandenen Dokumenten trennen.

### Schritt 2: Eine kleine Gzip-Eingabe erzeugen

```bash
printf '%s\n' 'Eigene Gzip-Testnotiz.' | gzip -c > "notiz.txt.gz"
```

Der Text wird komprimiert auf stdout ausgegeben und von der Shell in die neue Datei geschrieben. Eine unkomprimierte `notiz.txt` existiert noch nicht; deshalb droht im nächsten Schritt keine Namenskollision mit einem erhaltenen Original.

### Schritt 3: Vorher prüfen

```bash
gunzip -t "notiz.txt.gz"
```

Eine erfolgreiche Prüfung kann ohne normale Ausgabe enden. Fehlerausgabe beachten und den Rückgabewert unmittelbar mit `echo $?` ansehen. Ein späterer anderer Befehl ersetzt diesen Shell-Wert.

### Schritt 4: Mit erhaltener Quelle dekomprimieren

```bash
gunzip -kv "notiz.txt.gz"
```

`-k` erhält `notiz.txt.gz`, `-v` zeigt zusätzliche Angaben. Danach sollte `notiz.txt` die Testnotiz enthalten. Ohne `-k` wäre das Entfernen der komprimierten Eingabe nach erfolgreichem Dateivorgang normalerweise beabsichtigt.

### Schritt 5: Alternativ direkt ausgeben

```bash
gunzip -c "notiz.txt.gz"
```

Damit lässt sich der bekannte Text nochmals lesen, ohne den bereits vorhandenen Zielnamen `notiz.txt` neu zu schreiben. Ein erneuter Dateiaufruf mit `-k` am selben Ort würde dagegen auf den belegten Namen treffen.

## 6. Typische Anwendungsfälle

**Eine heruntergeladene `.gz`-Datei öffnen:** Herkunft und Datenformat prüfen, eine Kopie erhalten und mit `-k` wiederherstellen. Die Dekompression startet den Inhalt nicht automatisch als Programm.

**Komprimierte Protokolle weiterverarbeiten:** Mit `-c` kann Text in eine Pipe geliefert werden. Die Wirkung der weiteren Werkzeuge ist gesondert zu beurteilen.

**Eine `.tar.gz`-Datei vorbereiten:** Nach der Gzip-Schicht die TAR-Datei zunächst auflisten und dann bewusst in ein neues Ziel entpacken. `gunzip` allein wählt keine einzelnen TAR-Mitglieder aus.

**Daten vor dem Rückspielen testen:** `-t` prüft den komprimierten Datenstrom ohne große wiederhergestellte Datei. Bei wichtigen Sicherungen gehört trotzdem ein später kontrollierter Wiederherstellungsversuch dazu.

**Prüfpunkt bei ZIP:** GNU gunzip unterstützt nur bestimmte eingeschränkte ZIP-Fälle. Für ein allgemeines ZIP mit mehreren Dateien das passende Archivwerkzeug verwenden, statt daraus eine universelle ZIP-Funktion abzuleiten.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Komprimierte Eingabe ersetzt

Ohne `-k` kann nach Erfolg die `.gz`-Datei verschwinden. Das ist normalerweise keine Beschädigung, sondern der gewählte Dateimodus. Für wichtige Daten die komprimierte Quelle zunächst erhalten.

### Vorhandenes Ziel und Shell-Umleitung

`-f` kann Schutz vor Ersetzen aufheben. Bei `gunzip -c quelle.gz > ziel` öffnet die Shell `ziel`; eine vorhandene Datei kann bereits leer sein, bevor die Eingabe erfolgreich geprüft wurde. Niemals auf denselben Pfad zurückschreiben, aus dem gelesen werden soll.

### Ausgabemenge und Teilzustände

Die unkomprimierte Ausgabe kann viel größer sein. Angezeigte Größen sind bei besonderen oder zusammengesetzten Datenströmen nicht als verlässliche Ressourcenbegrenzung zu behandeln. Nach einem Abbruch können Ausgaben unvollständig sein.

### Namen und Vertrauen

Mit `-N` können im Datenstrom gespeicherte Namensangaben eine Rolle spielen. Nicht nur auf die äußere Endung achten. Eine erfolgreich geprüfte Prüfsumme beweist keine vertrauenswürdige Herkunft und keine Harmlosigkeit des Inhalts.

### Rekursion

`-r` erweitert den Bearbeitungsbereich auf Verzeichnisse. Das kann zusammen mit dem normalen Ersetzen von Eingaben viele Dateien betreffen. Die hier gezeigte kleine Übung benötigt keine Rekursion.

**Keine Root-Rechte für diese Beispiele.** Geschützte Systemprotokolle und Systempfade erfordern eine gesonderte Berechtigung; die Anleitung ist keine Ausführungsfreigabe.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ausgabe existiert bereits | Erhaltenes Original oder frühere Wiederherstellung belegt den Zielnamen. | Datei prüfen oder ausdrücklich einen neuen Ausgabenamen wählen. |
| „not in gzip format“ | Andere Daten als erwartet oder fehlerhafte Eingabe. | Tatsächlichen Inhalt und Download überprüfen. |
| „unexpected end of file“ | Beispielsweise unvollständige Übertragung. | Eingabe erhalten; weitere Kopie oder erneuten Download prüfen. |
| Nach Erfolg fehlt `.gz` | Normaler Dateimodus ohne `-k`. | Für künftige Aufrufe Originalerhalt ausdrücklich wählen. |
| Nach `.tar.gz`-Verarbeitung bleibt `.tar` | Die Kompressionsschicht wurde entfernt. | TAR gesondert untersuchen; nicht erneut wahllos gunzip aufrufen. |
| Keine Reaktion ohne Eingabename | Es wird auf stdin gewartet. | Gewünschte Datei angeben. |

GNU gzip verwendet `0` für einen normalen Abschluss, `1` für Fehler und `2` für Warnungen. Die [Manpage](https://manpages.debian.org/trixie/gzip/gunzip.1.en.html) beschreibt Diagnosen und Einschränkungen. Den Rückgabewert nicht mit der bloßen Existenz einer Zieldatei ersetzen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Für die erste Wiederherstellung `-k` verwenden.
2. Vorher die Eingabe mit `-t` prüfen und Meldungen lesen.
3. Erwarteten Ausgabenamen und freien Platz kontrollieren.
4. Für eine andere Ausgabe ausdrücklich `-c` und einen neuen Zielpfad verwenden.
5. Datenstrom-Kompression und Archivierung auseinanderhalten.
6. `-f`, `-N` und `-r` erst nach Verständnis der zusätzlichen Wirkung einsetzen.
7. Für maschinelle Abläufe Teilausgaben und Rückgabewerte bewusst behandeln.

**Prüfstand:** Mit GNU gzip 1.12 wurden Integritätstest, Dekompression mit `-kv` und Ausgabe mit `-c` an kleinen eigenen Dateien geprüft. Der Inhalt stimmte bytegenau mit der Eingabe überein. An einer separaten eigenen Testdatei wurde das normale Entfernen der `.gz`-Eingabe ohne `-k` bestätigt. ZIP-Sonderfälle, Rekursion, gespeicherte Namenswiederherstellung und beschädigte Fremddaten wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gzip -d` | Ausdrückliche Wahl der Dekompression über den Familiennamen. |
| `zcat` | Gzip-Inhalt unmittelbar als Datenstrom ausgeben. |
| `tar` | TAR-Mitglieder nach oder zusammen mit der Dekompression behandeln. |
| `unzip` | Für reguläre ZIP-Archive mit eigener Mitgliederstruktur. |
| `bunzip2`, `unxz`, `unzstd` | Entsprechende Aufgaben für andere Formate; Optionen nicht pauschal übertragen. |

Ausgangseintrag: Datensatz 8 in `index.json`. Die allgemeine Altsyntax wurde konkretisiert; Originalerhalt und Schreibwirkung sind nun ausdrücklich beschrieben.
