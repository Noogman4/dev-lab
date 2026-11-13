---
id: "unlzma"
name: "unlzma"
command: "unlzma"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "lzma", "dekompression"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 15
reviewed_at: "2026-11-13"
locally_checked_version: "unlzma aus XZ Utils 5.4.5"
---

# unlzma – Legacy-LZMA-Dateien mit erhaltener Quelle entpacken

## 1. Kurzbeschreibung

`unlzma` dekomprimiert in der hier beschriebenen XZ-Utils-Variante Dateien des älteren `.lzma`-Formats. Der Aufruf entspricht `xz --format=lzma --decompress`.

**Für eigene Dateien sind keine Root-Rechte nötig.** Ein normaler erfolgreicher Dateiaufruf entfernt anschließend die komprimierte Eingabe. Wer sie behalten möchte, verwendet ausdrücklich `-k` oder eine Ausgabe auf stdout.

## 2. Was macht der Befehl?

Aus einem komprimierten Datenstrom wird wieder der ursprüngliche Inhalt. Bei einer Eingabe `notiz.txt.lzma` ist der abgeleitete Ausgabename normalerweise `notiz.txt`. Ein vorhandenes Ziel wird ohne erzwungenes Überschreiben abgelehnt.

Die Dateiendung `.lzma` bezeichnet einen älteren Container. Dieser ist kein Verzeichnisarchiv wie ZIP und kein `.xz`-Container. Eine enthaltene TAR-Datei muss nach der Dekompression weiterhin mit einem Archivwerkzeug behandelt werden.

Die [offizielle Distributions-Manpage](https://manpages.debian.org/trixie/xz-utils/unlzma.1.en.html) ordnet den Aufrufnamen und das Verhalten bei Eingabe und Ausgabe zu. Die [XZ-Projektdokumentation](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1) erläutert die Grenzen des Legacy-Formats. Die hier aufgeführten üblichen Schalter sind außerdem in der lokalen Hilfe von XZ Utils 5.4.5 vorhanden.

## 3. Syntax

```text
unlzma [OPTIONEN] [DATEI ...]
xz --format=lzma --decompress [OPTIONEN] [DATEI ...]
```

```bash
unlzma -k "notiz.txt.lzma"
unlzma -t "notiz.txt.lzma"
unlzma -c "notiz.txt.lzma"
```

Die erste Variante schreibt eine Datei und behält die Quelle. Die zweite prüft den Datenstrom ohne Ausgabedatei. Die dritte liefert den dekomprimierten Inhalt auf stdout. Das sind unterschiedliche Aufgaben; ein Testlauf ist keine Wiederherstellung.

**Prüfpunkt:** Mit `unlzma --version` feststellen, ob tatsächlich die XZ-Utils-Variante verwendet wird. Die ähnliche Benennung anderer oder älterer LZMA-Werkzeuge garantiert keine identischen Optionen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Komprimierte Eingabe behalten. | Für eine erste Wiederherstellung ausdrücklich setzen. |
| `-c`, `--stdout` | Dekomprimierten Inhalt auf stdout schreiben. | Erhält die Eingabe; eine Shell-Umleitung kann trotzdem ein Ziel überschreiben. |
| `-t`, `--test` | Dekomprimieren und Ergebnis verwerfen. | Keine Ausgabedatei; bei `.lzma` fehlt weiterhin eine zusätzliche Inhaltsprüfsumme. |
| `-d`, `--decompress` | Dekompressionsmodus wählen. | Durch den Namen `unlzma` schon vorgegeben. |
| `-M LIMIT`, `--memlimit=LIMIT` | Speicherbedarf begrenzen. | Begrenzt nicht die Menge der entpackten Daten auf der Platte. |
| `-v`, `--verbose` | Zusätzliche Verarbeitungsangaben. | Hilfreich bei Diagnose und Fortschritt. |
| `-f`, `--force` | Bestimmte Schutzregeln übergehen. | Kann vorhandene Ausgaben ersetzen; kein normaler Reparaturschritt. |
| `-S .ENDUNG`, `--suffix=.ENDUNG` | Zusätzliche Namensendung berücksichtigen. | Ändert keine falschen Daten in das richtige Format. |
| `--single-stream` | Nachfolgende Daten nach dem ersten Datenstrom ignorieren. | Kann sonst sichtbare Probleme verdecken. |
| `--` | Optionen beenden. | Nützlich bei Dateinamen mit führendem Bindestrich. |

Eine allgemeine XZ-Hilfe enthält auch Kompressions- und `.xz`-spezifische Funktionen. Daraus folgt nicht, dass jede davon bei einer Legacy-LZMA-Eingabe sinnvoll ist.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und neuen Arbeitsordner prüfen

```bash
unlzma --version
uebung="$(mktemp -d -t netmon-unlzma-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Alle weiteren Dateien gehören zur eigenen Übung.

### Schritt 2: Bekannte Testeingabe vorbereiten

```bash
printf '%s\n' 'Eigene UNLZMA-Testnotiz.' > "original.txt"
lzma -k "original.txt"
cp "original.txt.lzma" "probe.lzma"
```

Die Kompression dient nur dazu, eine bekannte Eingabe zu erzeugen. `-k` erhält das Original. Die zusätzliche Kopie bekommt beim späteren Entpacken den freien Namen `probe`, sodass kein Konflikt mit `original.txt` entsteht.

### Schritt 3: Verarbeitbarkeit prüfen

```bash
unlzma -t "probe.lzma"
```

Dieser Aufruf legt keine Datei `probe` an. Ein Fehler ist zuerst zu klären. Ein Erfolg bedeutet beim Legacy-Format nicht, dass ein zusätzlicher vollständiger Inhaltsprüfwert verglichen wurde.

### Schritt 4: Quelle behalten und entpacken

```bash
unlzma -k "probe.lzma"
cmp "original.txt" "probe"
```

Danach sollen die komprimierte `probe.lzma` und die dekomprimierte `probe` existieren. `cmp` prüft bei diesen eigenen Daten die byteweise Übereinstimmung. Eine erneute Ausführung trifft auf das bereits vorhandene Ziel; dafür nicht ungeprüft `-f` ergänzen.

### Schritt 5: Bekannten Text ohne Ausgabedatei lesen

```bash
unlzma -c "original.txt.lzma"
```

Der Inhalt der eigenen Textdatei erscheint auf stdout. Bei einer beliebigen binären Eingabe wäre eine direkte Terminalausgabe ungeeignet. Die komprimierte Datei bleibt erhalten.

## 6. Typische Anwendungsfälle

**Ältere Datenbestände wiederherstellen:** Wenn der tatsächliche Erzeugungsweg `.lzma` verwendet hat, passt die ausdrückliche Formatwahl. Die bloße Dateiendung ist noch kein Nachweis für unbeschädigte Daten.

**Ein komprimiertes TAR-Archiv vorbereiten:** Aus `sammlung.tar.lzma` kann `sammlung.tar` entstehen. Die Ordnerstruktur wird erst beim nachfolgenden kontrollierten TAR-Schritt wiederhergestellt.

**Dateiinhalt an ein passendes Werkzeug weitergeben:** stdout eignet sich für Verarbeitungsketten, sofern deren Empfänger, Fehlerbehandlung und Ausgabemengen bewusst gewählt wurden. Eine Pipeline kann trotz eines früheren Fehlers scheinbar enden.

**Kompatibilität nachvollziehbar dokumentieren:** In Skripten macht `xz --format=lzma -d` die Formatwahl sichtbar. Vor einer Umstellung bestehender Abläufe trotzdem deren Dateinamen, Fehlerbehandlung und Originalerhalt prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Erfolgreiches Entpacken entfernt normalerweise die Eingabe

Ohne `-k` beziehungsweise stdout wird die komprimierte Quelle nach erfolgreicher Dateiausgabe entfernt. Wer nur nachsehen wollte, kann dadurch unbeabsichtigt den gespeicherten Bestand verändern. Die Einsteigerbeispiele erhalten ihn ausdrücklich.

### Legacy-LZMA hat keine zusätzliche Inhaltsprüfsumme

Die Formatgrenze ist im [XZ-Handbuch](https://raw.githubusercontent.com/tukaani-project/xz/master/src/xz/xz.1) beschrieben. Ein Decoder kann verschiedene Strukturfehler erkennen, ohne jede mögliche Inhaltsveränderung sicher nachzuweisen. Ein erfolgreicher Test ersetzt weder eine vertrauenswürdige Referenz noch einen Herkunftsnachweis.

### Eine kleine Eingabe kann eine große Ausgabe erzeugen

RAM und Plattenplatz sind verschiedene Ressourcen. `-M` begrenzt den Speicherbedarf des Decoders. Es setzt keine Ausgabedatei-Quote und verhindert nicht jedes Ressourcenproblem durch große entpackte Inhalte.

### Format und Dateisammlung unterscheiden

`unlzma` ist kein allgemeiner ZIP-, RAR- oder 7z-Entpacker. Eine umbenannte Datei ist noch nicht konvertiert. Auch die Regeln für mehrere hintereinandergehängte `.xz`-Datenströme dürfen nicht einfach auf `.lzma` übertragen werden.

### Ausgabeumleitungen sind Schreiboperationen

Bei `unlzma -c eingabe.lzma > ziel` öffnet die Shell das Ziel. Ein bereits vorhandener Inhalt kann schon vor einem späteren Dekompressionsfehler verloren gehen. Eingabe und Ausgabe deshalb nie auf denselben Pfad setzen.

**Für die gezeigten eigenen Dateien sind Root-Rechte unnötig.** Fehlende Rechte können auf einen falschen Zielpfad hinweisen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ausgabe existiert bereits | Früher entpackt oder Original behalten. | Frischen, bewusst gewählten Namen verwenden. |
| Unbekanntes Format | Falscher Container, falsche Benennung oder beschädigte Datei. | Herkunft und Erzeugungswerkzeug prüfen. |
| Speicherlimit überschritten | Datei benötigt mehr Decoder-RAM. | Bedarf, Herkunft und verfügbare Ressourcen beurteilen. |
| Es erscheint kein Text | Inhalt ist binär oder die Datei wird statt stdout geschrieben. | Aufgabe und Ausgabeart prüfen. |
| Nach dem Entpacken bleibt eine `.tar`-Datei | Nur die Kompressionsschicht wurde entfernt. | Archiv separat auflisten und kontrolliert entpacken. |
| Test erfolgreich, Inhalt trotzdem zweifelhaft | Keine bekannte Inhaltsreferenz beziehungsweise fehlende Legacy-Prüfsumme. | Mit vertrauenswürdiger Referenz vergleichen. |

Bei XZ Utils steht Abschlussstatus `0` für Erfolg, `1` für einen Fehler und `2` für eine Warnung. Meldungen mitlesen; eine angelegte Datei allein beweist keinen brauchbaren Abschluss.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Implementierung und tatsächliches Format zuerst prüfen.
2. Mit kleinen eigenen Daten beginnen und `-k` ausdrücklich setzen.
3. Vorhandene Ziele nicht vorschnell erzwingen.
4. Testmodus und tatsächliche Wiederherstellung getrennt durchführen.
5. Bei bekannten Daten das Ergebnis byteweise vergleichen.
6. RAM-Limit und benötigten Plattenplatz getrennt beurteilen.
7. Keine unbekannten binären Inhalte unmittelbar an das Terminal senden.
8. Komprimierte Originale behalten, bis das Ergebnis unabhängig geprüft ist.

**Prüfstand:** Mit `unlzma` aus XZ Utils 5.4.5 wurden Testmodus, Entpacken mit `-k` und stdout-Ausgabe mit eigenen kleinen Daten geprüft. Die Inhalte waren bytegleich; `-k` erhielt die komprimierte Eingabe. An einer zusätzlichen eigenen Kopie wurde bestätigt, dass der normale erfolgreiche Dateiaufruf die `.lzma`-Eingabe entfernt. Fremddecoder, manipulierte Daten und Speichergrenzen wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lzma` | Erstellt in der XZ-Utils-Variante das Legacy-Format. |
| `xz --format=lzma -d` | Ausdrückliche Schreibweise derselben Aufgabe. |
| `lzcat` | Gibt Legacy-LZMA-Inhalt auf stdout aus. |
| `unxz`, `xzcat` | Verwandte Aufrufe mit anderer Formatvoreinstellung. |
| `tar` | Behandelt eine gegebenenfalls enthaltene Dateisammlung. |
| `cmp` | Vergleicht bekannte Originale und Wiederherstellungen byteweise. |

Ausgangseintrag: Datensatz 15 in `index.json`. Der Originalerhalt, die Legacy-Formatgrenzen und die Bedeutung eines erfolgreichen Testlaufs sind gegenüber dem Ausgangseintrag genauer erklärt.
