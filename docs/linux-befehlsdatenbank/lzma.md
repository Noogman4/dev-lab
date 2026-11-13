---
id: "lzma"
name: "lzma"
command: "lzma"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "lzma", "xz-utils"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 12
reviewed_at: "2026-11-13"
locally_checked_version: "lzma aus XZ Utils 5.4.5"
---

# lzma – Das ältere LZMA-Dateiformat gezielt verwenden

## 1. Kurzbeschreibung

`lzma` komprimiert in der hier dokumentierten XZ-Utils-Variante Daten im älteren `.lzma`-Format. Der Aufruf entspricht grundsätzlich `xz --format=lzma`. Die Dateiendung ist von `.xz` und `.7z` zu unterscheiden, obwohl dabei verwandte Kompressionsverfahren vorkommen können.

**Für eigene Dateien sind keine Root-Rechte nötig.** Bei erfolgreicher gewöhnlicher Dateikompression wird die Eingabe normalerweise entfernt. Mit `-k` bleibt sie erhalten. Eine pauschale Einstufung als nur lesendes Werkzeug wäre falsch.

## 2. Was macht der Befehl?

Der Aufrufname wählt bei XZ Utils ein Format. Er bedeutet nicht, dass eine beliebige Datei mit irgendeiner LZMA-Kompression ohne Kenntnis ihres Containers verarbeitet werden kann.

Das ältere `.lzma`-Format ist ein einzelner komprimierter Datenstrom. Es enthält keine allgemeine Ordner- und Mitgliederliste. Eine Dateisammlung muss vorher passend archiviert werden. Zudem unterstützt dieser Container nicht die zusätzlichen Inhaltsprüfsummen des `.xz`-Formats.

Die Zuordnung der Aliasse steht in der [Distributions-Manpage zu XZ Utils](https://manpages.debian.org/trixie/xz-utils/lzma.1.en.html#COMMAND_ALIASES). Formatgrenzen, Speicherbedarf und Prüfmöglichkeiten beschreibt die [offizielle XZ-Dokumentation](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1).

## 3. Syntax

```text
lzma [OPTIONEN] [DATEI ...]
xz --format=lzma [OPTIONEN] [DATEI ...]
```

Die folgenden Aufrufe verfolgen unterschiedliche Ziele:

```bash
lzma -k "notiz.txt"
lzma -t "notiz.txt.lzma"
lzma -dc "notiz.txt.lzma"
```

Der erste komprimiert und behält die Quelle. Der zweite testet die Verarbeitbarkeit. Der dritte dekomprimiert auf stdout und legt keine namensabhängige Ausgabedatei an.

**Prüfpunkt:** Es existieren beziehungsweise existierten andere LZMA-Werkzeuge. Vor Übernahme der Optionen mit `lzma --version` prüfen, ob tatsächlich die hier beschriebene XZ-Utils-Variante verwendet wird.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Eingabedatei erhalten. | Verhindert das normale Entfernen nach erfolgreicher Dateiausgabe. |
| `-d`, `--decompress` | Dekomprimieren. | Gegenrichtung zur normalen Formatwahl durch den Namen. |
| `-c`, `--stdout` | Ergebnis auf stdout schreiben. | Die Shell kann ein umgeleitetes Ziel trotzdem überschreibend öffnen. |
| `-t`, `--test` | Daten verarbeiten und Ausgabe verwerfen. | Bei `.lzma` kein Ersatz für eine fehlende zusätzliche Inhaltsprüfsumme. |
| `-0` bis `-9` | Kompressionsvorgabe wählen. | Speicherbedarf und Aufwand können stark variieren. |
| `-M LIMIT`, `--memlimit=LIMIT` | Speicherbedarf begrenzen. | Keine Begrenzung der unkomprimierten Dateigröße; Verhalten bei Kompression und Dekompression unterscheiden. |
| `-v`, `--verbose` | Mehr Angaben ausgeben. | Für Beobachtung und Diagnose. |
| `-f`, `--force` | Bestimmte Schutzprüfungen übergehen. | Nicht vorschnell bei vorhandenen Zielen verwenden. |
| `--` | Optionen beenden. | Für Namen mit führendem Bindestrich hilfreich. |

Ein allgemeiner XZ-Schalter ist nicht in jedem Format sinnvoll. Insbesondere kann man `.lzma` nicht durch eine XZ-Prüfsummenoption nachträglich mit dem Prüfumfang des `.xz`-Containers ausstatten. Grundlage: [XZ-Optionsreferenz](https://manpages.debian.org/trixie/xz-utils/lzma.1.en.html#OPTIONS).

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und neuen Arbeitsort prüfen

```bash
lzma --version
uebung="$(mktemp -d -t netmon-lzma-XXXXXX)"
cd "$uebung"
pwd
```

Die Übung ist auf die XZ-Utils-Variante ausgerichtet. Nach einem fehlgeschlagenen Wechsel nicht am bisherigen Ort weiterschreiben.

### Schritt 2: Kleine Eingabe erzeugen

```bash
printf '%s\n' 'Eigene LZMA-Testnotiz.' > "notiz.txt"
```

Die Datei entsteht neu im Übungsordner. Eine erneute Ausführung würde dieselbe Testdatei überschreiben. Es werden keine vorhandenen privaten Dokumente benötigt.

### Schritt 3: Mit erhaltener Quelle komprimieren

```bash
lzma -k "notiz.txt"
```

Erwartet werden danach `notiz.txt` und `notiz.txt.lzma`. Die Quelle wird wegen `-k` nicht durch die komprimierte Datei ersetzt. Bei sehr kleinen Eingaben kann die zusätzliche Formatverwaltung den Platzgewinn überwiegen.

### Schritt 4: Verarbeitbarkeit prüfen

```bash
lzma -t "notiz.txt.lzma"
```

Der Datenstrom wird verarbeitet, ohne eine neue unkomprimierte Datei abzulegen. Ein erfolgreicher Abschluss erkennt nicht jede denkbare Veränderung des Inhalts. Die zusätzliche Integritätsprüfung des `.xz`-Formats ist im `.lzma`-Format nicht vorhanden.

### Schritt 5: Bekannten Inhalt zurücklesen

```bash
lzma -dc "notiz.txt.lzma"
```

`-d` dekomprimiert, `-c` liefert den Text auf stdout. Die vorhandene Originaldatei wird nicht neu geschrieben. Für einen eigenen Kontrollpfad kann die Ausgabe in eine bisher nicht belegte Datei umgeleitet und anschließend mit dem Original verglichen werden.

## 6. Typische Anwendungsfälle

**Kompatibilität mit einem älteren Datenformat:** Eine Anwendung oder ein vorhandenes Verfahren kann ausdrücklich `.lzma` erwarten. Dann sind Format, Parameter und der tatsächlich vorhandene Decoder entscheidend.

**Alte komprimierte Dateien untersuchen:** Vorher Herkunft und Format prüfen. Eine ähnlich benannte `.xz`- oder `.7z`-Datei ist nicht allein wegen eines verwandten Algorithmus austauschbar.

**Ein Archiv als einzelnen Datenstrom komprimieren:** Aus einer passenden TAR-Datei kann eine `.tar.lzma`-Datei entstehen. Die inhaltliche Archivierung und deren Metadatenbehandlung sind weiterhin Aufgaben des Archivwerkzeugs.

**Ein Werkzeugverhalten vergleichen:** Explizites `xz --format=lzma` zeigt in einem Skript deutlicher, welche Formatwahl beabsichtigt ist. Das ist keine Aufforderung, bestehende produktive Daten ohne Kompatibilitätsprüfung umzustellen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Eingabe wird normalerweise entfernt

Ein erfolgreicher normaler Dateiaufruf ersetzt die Eingabe, sofern nicht `-k` oder eine passende stdout-Arbeitsweise gewählt wurde. Das gilt in entsprechender Richtung auch für das Dekomprimieren. Für wichtige Originale zuerst den Erhalt ausdrücklich wählen.

### Keine zusätzliche Inhaltsprüfsumme im Legacy-Container

Das [offizielle XZ-Handbuch](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1) unterscheidet die Integritätsfunktionen von `.xz` und `.lzma`. Ein erfolgreicher `-t`-Lauf bei `.lzma` ist kein gleichwertiger Ersatz für die fehlende zusätzliche Inhaltsprüfung und erst recht kein Herkunftsnachweis. Bei wichtigen Daten eine vertrauenswürdige Referenz beziehungsweise einen geeigneten vollständigen Sicherungsablauf vorsehen.

### Speicherbedarf und Ausgabemenge

Einstellungen des Kompressors beeinflussen auch den später benötigten Dekompressionsspeicher. Eine hohe Vorgabe ist nicht automatisch für jedes Zielgerät geeignet. `-M` betrifft den Speicherbedarf des Werkzeugs und ist keine Quote für die auf die Platte geschriebene Ausgabe.

### Besonderheiten älterer Verbraucher

Eingebettete oder ältere Decoder können bestimmte Header- oder Filterparameter voraussetzen. Auch das Hintereinanderhängen mehrerer `.lzma`-Dateien ist nicht einfach wie bei allen anderen Kompressionscontainern zu behandeln. Solche Kompatibilität muss im konkreten Austauschweg geprüft werden.

### Umleitungen und Namenskonflikte

Eine Shell-Umleitung kann ein Ziel schon vor erfolgreicher Verarbeitung leeren. Eingabe und Ausgabe dürfen nie derselbe Pfad sein. Bestehende Ausgaben nicht ungeprüft mit `-f` ersetzen.

**Root-Rechte sind für die gezeigten eigenen Dateien nicht nötig.** Sie ändern weder Formatgrenzen noch Kompatibilität.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Unbekannter Schalter | Andere Implementierung oder ältere Variante. | Version und passende Hilfe prüfen. |
| Bereits vorhandenes Ziel | Original wurde mit `-k` erhalten oder früher schon dekomprimiert. | Neuen Ausgabeort wählen statt sofort zu erzwingen. |
| Format wird nicht erkannt | `.xz`, `.7z`, roher Datenstrom oder beschädigter Inhalt statt `.lzma`. | Erzeugungsweg und tatsächliches Format prüfen. |
| Speicherlimit überschritten | Die Eingabe benötigt mehr Dekompressionsspeicher. | Quelle und Limit bewusst beurteilen; nicht beliebig alle Grenzen entfernen. |
| Auflisten wie bei `.xz` funktioniert nicht | Formatabhängige Funktion auf `.lzma` übertragen. | Keine XZ-Metadatenübersicht für jeden Legacy-Container voraussetzen. |
| Alter Verbraucher lehnt die Datei ab | Parameter oder Headerkonventionen passen nicht. | Zielgerät und passende Erzeugungsparameter gesondert prüfen. |

Für XZ Utils bezeichnet `0` einen erfolgreichen Abschluss, `1` einen Fehler und `2` eine Warnung. Bei wichtigen Daten zusätzlich die tatsächliche Wiederherstellung vergleichen; eine Datei allein ist kein Erfolgsnachweis.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zuerst sicherstellen, dass die XZ-Utils-Variante gemeint ist.
2. Mit einer kleinen Datei und ausdrücklich gesetztem `-k` beginnen.
3. Legacy-Dateiformat und Kompressionsalgorithmus begrifflich trennen.
4. Nach einem Test den Inhalt zusätzlich kontrolliert zurückgewinnen und vergleichen.
5. Speicherbedarf und Kompatibilität des Empfängers beachten.
6. Für einen neuen Ablauf ohne Legacy-Anforderung das geeignete Containerformat gesondert auswählen.
7. Warnungen nicht als Beleg dafür behandeln, dass das Ergebnis trotzdem vollständig geeignet sei.

**Prüfstand:** Mit `lzma` aus XZ Utils 5.4.5 wurden Kompression mit `-k`, Testmodus und Dekompression auf stdout geprüft. Die Quelle blieb erhalten; der ausgegebene Inhalt entsprach bytegenau der Eingabe. Der erzeugte Datenstrom wurde zusätzlich als LZMA-Alone-Format decodiert. Ältere Fremddecoder, Speichergrenzen und beschädigte Daten wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xz --format=lzma` | Die Formatwahl ausdrücklich über den Hauptnamen schreiben. |
| `unlzma` | Entpack-Variante mit derselben Legacy-Formatwahl. |
| `lzcat` | Legacy-LZMA-Inhalt als Datenstrom ausgeben. |
| `xz`, `unxz`, `xzcat` | Verwandte Befehle für das `.xz`-Format mit anderen Containerfunktionen. |
| `7z` | Kann verwandte Verfahren in anderen Archivstrukturen verwenden; kein austauschbarer Aufruf. |

Ausgangseintrag: Datensatz 12 in `index.json`. Gegenüber dem allgemeinen Hilfe-Platzhalter sind Legacy-Format, fehlende zusätzliche Inhaltsprüfsumme und Originalerhalt präzisiert.
