---
id: "lz4cat"
name: "lz4cat"
command: "lz4cat"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive", "kompression", "lz4", "datenstrom"]
status: "Ausgearbeitet; Quellen geprüft, praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 11
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle CLI-Dokumentation v1.10.0 geprüft"
---

# lz4cat – LZ4-Daten ausgeben und den Durchreichmodus verstehen

## 1. Kurzbeschreibung

`lz4cat` gibt den Inhalt von LZ4-komprimierten Dateien als Datenstrom aus. Typische Ziele sind ein Terminal, ein Pager oder ein nachgeschaltetes Auswertungsprogramm. Im normalen Anzeigeablauf bleibt die Eingabe erhalten.

**Zum Lesen eigener Dateien sind keine Root-Rechte nötig.** Die Einstufung als überwiegend lesend bezieht sich auf diesen Schritt. Eine Shell-Umleitung oder ein nachgeschalteter Befehl kann trotzdem Dateien verändern.

## 2. Was macht der Befehl?

Laut [offizieller LZ4-CLI-Dokumentation v1.10.0](https://raw.githubusercontent.com/lz4/lz4/v1.10.0/programs/lz4.1.md) entspricht der Alias der Kombination `lz4 -dcfm`:

| Vorgabe | Bedeutung |
| --- | --- |
| `-d` | Dekomprimieren. |
| `-c` | Daten auf stdout schreiben. |
| `-f` | Unter anderem einen Durchreichmodus für nicht erkannte Eingaben ermöglichen. |
| `-m` | Mehrere Eingabedateien verarbeiten. |

**Wichtige Folge:** Eine erfolgreich ausgegebene Datei ist nicht automatisch als gültige LZ4-Datei bestätigt. Durch den Durchreichmodus können nicht erkannte Daten unverändert ausgegeben werden. Das ist ein entscheidender Unterschied zwischen „Inhalt bereitstellen“ und „Dateiformat streng prüfen“.

Für Skripte, die eine bestimmte Dekompressionsabsicht deutlich machen sollen, empfiehlt das Projekt den Namen `lz4` mit ausdrücklichen Optionen. Für eine einzelne Eingabe ist etwa `lz4 -dc datei.lz4` verständlicher als das unbesehene Übernehmen aller Alias-Vorgaben.

## 3. Syntax

```text
lz4cat [OPTIONEN] DATEI.lz4 [WEITERE_DATEI.lz4 ...]
```

Für einen bekannten komprimierten Text:

```bash
lz4cat "notiz.txt.lz4"
```

Mit einem weiterlesenden Programm:

```bash
lz4cat "protokoll.txt.lz4" | less
```

Mehrere Eingaben werden nacheinander ausgegeben. Die Ausgabe ergänzt nicht automatisch Dateinamen oder sichere Trennmarken. Enthält die Eingabe ein anderes Archivformat, wird dessen Datenstrom ausgegeben, nicht dessen gesamte Ordnerstruktur von `lz4cat` selbst angelegt.

## 4. Wichtige Optionen

Die meisten bedeutsamen Vorgaben stecken bereits im Alias. Gerade deshalb ist die genaue Bedeutung des Namens wichtig.

| Option oder Alternative | Wirkung | Einordnung |
| --- | --- | --- |
| `-q` | Bestimmte Statusmeldungen reduzieren. | Keine zusätzliche Daten- oder Sicherheitsprüfung. |
| `-v` | Zusätzliche Diagnoseinformationen anzeigen. | Datenstrom von Diagnoseausgabe unterscheiden. |
| `--help` | Hilfe anzeigen. | Installierte Variante und angebotene Optionen prüfen. |
| `--version` | Version anzeigen. | Grundlage für einen Vergleich mit der passenden Dokumentation. |
| `lz4 -dc DATEI` | Einzeldatei ausdrücklich dekomprimieren und auf stdout liefern. | Der zusätzliche Alias-Schalter `-f` wird dabei nicht absichtlich angefordert. |
| `lz4 -t DATEI` | Ausdrücklich einen Integritätstest anfordern. | Die bessere Absicht für einen Test statt bloßer Inhaltsausgabe. |

Diese Zuordnung wird auch in der [LZ4-Manpage bei Debian](https://manpages.debian.org/trixie/lz4/lz4.1.en.html) erläutert. **Prüfpunkt:** Ein anders bereitgestellter Alias oder eine andere Implementierung muss am Zielsystem geprüft werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Vorhandenes Programm prüfen

```bash
command -v lz4
command -v lz4cat
lz4 --version
```

Die folgende Übung setzt beide Aufrufe voraus. In der hier verwendeten Umgebung sind sie nicht installiert; die Schritte sind deshalb als nachvollziehbare Anleitung dokumentiert, nicht als lokal erfolgreich ausgeführter Test.

### Schritt 2: Neue kleine Testdatei anlegen

```bash
uebung="$(mktemp -d -t netmon-lz4cat-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eine LZ4-Anzeigenotiz.' > "notiz.txt"
```

Vor dem nächsten Schritt den erfolgreichen Verzeichniswechsel prüfen. Nur der neu angelegte Testtext wird verwendet.

### Schritt 3: Eine bekannte komprimierte Eingabe erzeugen

```bash
lz4 -z "notiz.txt" "notiz.txt.lz4"
```

Die Richtung und beide Pfade sind ausdrücklich genannt. Die komprimierte Datei stammt dadurch aus einer bekannten kleinen Eingabe und nicht aus einer unbekannten Downloadquelle.

### Schritt 4: Formatbezogenen Test separat durchführen

```bash
lz4 -t "notiz.txt.lz4"
```

Meldungen und Rückgabewert prüfen. Dieser Schritt soll nicht durch die bloße Beobachtung ersetzt werden, dass `lz4cat` etwas ausgegeben hat.

### Schritt 5: Den Inhalt ausgeben

```bash
lz4cat "notiz.txt.lz4"
```

Erwartet wird die bekannte Anzeigenotiz. Es soll keine neue Datei mit abgeleitetem Namen entstehen. Für einen ausdrücklich geschriebenen Alternativaufruf:

```bash
lz4 -dc "notiz.txt.lz4"
```

Die erwarteten Textinhalte beider Aufrufe lassen sich am Zielsystem vergleichen. Das ist eine praktische Prüfung, die hier noch offen ist.

## 6. Typische Anwendungsfälle

**Komprimierte Textausgaben unmittelbar lesen:** Der Inhalt kann ohne dauerhaft angelegte unkomprimierte Zwischenkopie an einen Pager gehen. Auch dabei werden Daten dekomprimiert und Ressourcen benötigt.

**Zusammengehörige Textdateien nacheinander ausgeben:** Mehrere Eingaben können in der angegebenen Reihenfolge verarbeitet werden. Bei fehlenden Zeilenumbrüchen und binären Formaten sind Dateigrenzen nicht automatisch eindeutig.

**Einen vorhandenen Arbeitsablauf verstehen:** Wenn ein Skript `lz4cat` verwendet, muss bei einer Fehlersuche berücksichtigt werden, dass unkomprimierte oder nicht erkannte Eingaben möglicherweise durchgereicht werden.

**In eine neue Zieldatei schreiben:** Das kann bewusst mit einer Shell-Umleitung erfolgen. Die umgeleitete Datei ist dann aber eine neue Schreibwirkung der Shell, nicht mehr bloß eine Anzeige.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Durchreichen ist kein Formatnachweis

Ein Decoder, der unbekannte Eingaben unverändert weitergibt, ist kein allgemeiner Validator. Wenn ein nachgeschaltetes Programm nur streng geprüfte LZ4-Daten erwartet, muss die Prüfung ausdrücklich vorgesehen werden. Auch ein erfolgreicher Integritätstest wäre noch kein Herkunftsnachweis.

### Shell-Umleitungen können überschreiben

`lz4cat quelle.lz4 > ziel` kann ein vorhandenes Ziel schon vor erfolgreicher Verarbeitung leeren. Eingabe und Ausgabe dürfen nicht dieselbe Datei sein. Eine vorhandene Ausgabedatei kann außerdem nur einen Teil des Datenstroms enthalten.

### Unbekannte Inhalte gehören nicht blind ins Terminal

Die Daten können Binärwerte, Steuerzeichen oder sehr große Textmengen enthalten. Die Endung `.lz4` sagt nichts darüber aus, ob die dekomprimierte Ausgabe als lesbarer Text geeignet ist.

### Pipeline und Rückgabewerte

Wenn ein nachgeschaltetes Programm früher beendet, kann der schreibende Teil einen Pipe-Fehler erhalten. Umgekehrt kann ein erfolgreicher letzter Pipeline-Schritt einen früheren Fehler verdecken. Den Status des gesamten vorgesehenen Ablaufs auswerten, nicht nur irgendeine sichtbare Ausgabe.

### Keine automatische Entschlüsselung oder Sicherheit

LZ4-Kompression schützt Daten nicht durch ein Passwort. Optionale Integritätsinformationen im [Frame-Format](https://github.com/lz4/lz4/blob/dev/doc/lz4_Frame_format.md) sind nicht mit einer kryptografischen Herkunftsprüfung gleichzusetzen. Entpackte Programme nicht ungeprüft ausführen.

**Root-Rechte sind für die Übung nicht erforderlich.** Der Alias erteilt keine zusätzliche Leseberechtigung für geschützte Dateien.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Alias fehlt | Paket stellt nur `lz4` oder eine andere Variante bereit. | Vorhandenen Programmnamen und lokale Hilfe prüfen. |
| Unkomprimierter Inhalt wird ohne Fehler ausgegeben | Der Durchreichmodus ist wirksam. | Nicht als Beweis für eine gültige LZ4-Eingabe werten. |
| Mehrere Textteile laufen zusammen | Keine automatischen Dateigrenzen. | Eingabeformat und Zeilenumbrüche berücksichtigen. |
| Unlesbare Terminalausgabe | Dekomprimierter Inhalt ist binär. | Dateityp und Anzeigeabsicht prüfen. |
| Ziel existiert trotz eines Fehlers | Shell hat es angelegt oder Teildaten geschrieben. | Nicht ungeprüft weiterverwenden. |
| Scheinbarer Erfolg der Pipeline | Nur letzter Teil wurde ausgewertet. | Rückgabewerte aller wichtigen Verarbeitungsschritte beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Erst mit einem selbst komprimierten kleinen Text beginnen.
2. Bei gewünschter Formatprüfung ausdrücklich den Testmodus verwenden.
3. Für Skripte eine deutlich geschriebene `lz4 -dc`-Absicht für eine einzelne Eingabe bevorzugen.
4. Unbekannte Daten nicht direkt als Terminaltext behandeln.
5. Vor dem Umleiten einen noch unbelegten Zielpfad wählen.
6. Anzeige, Integrität und Herkunft als drei unterschiedliche Fragen behandeln.
7. Eingaben behalten, bis eine kontrollierte Wiederherstellung überprüft ist.

**Prüfstand:** Alias-Zuordnung und Optionen wurden anhand der offiziellen CLI-Unterlagen v1.10.0 und der Distributions-Manpage geprüft. Ein lokaler Lauf war mangels installiertem LZ4-Programm nicht möglich. Durchreichverhalten, konkrete Fehlermeldungen und Ausgaben sind hier deshalb nicht praktisch bestätigt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lz4 -dc` | Ausdrücklich dekomprimierende Datenstromvariante. |
| `lz4 -t` | Daten prüfen statt sie nur auszugeben. |
| `unlz4` | Je nach Installation ein anderer Alias für Dekompression. |
| `bzcat`, `zcat`, `xzcat`, `zstdcat` | Ähnliche Aufgaben für andere Kompressionsfamilien; Vorgaben jeweils prüfen. |
| `less` | Text seitenweise anzeigen, ohne selbst das Kompressionsformat zu prüfen. |

Der unveränderte Ausgangseintrag steht unter Datensatz 11 in `index.json`. Die zuvor allgemeine Erklärung ist um die besonders wichtige Durchreich-Semantik ergänzt.
