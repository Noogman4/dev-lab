---
id: "xz"
name: "xz"
command: "xz"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive & kompression", "xz"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 20
reviewed_at: "2026-11-13"
locally_checked_version: "XZ Utils 5.4.5"
---

# xz – Einzelne Datenströme komprimieren und zuverlässig zurücklesen

## 1. Kurzbeschreibung

`xz` komprimiert Daten gewöhnlich in das `.xz`-Format und kann sie wieder dekomprimieren. Das Werkzeug bietet außerdem Test- und Informationsmodi. Diese Dokumentation bezieht sich auf XZ Utils.

**Für eigene Dateien sind keine Root-Rechte nötig.** Bei gewöhnlicher erfolgreicher Dateiausgabe wird die Eingabe entfernt. `-k` erhält das Original. Der Aufruf ist somit nicht pauschal nur lesend.

## 2. Was macht der Befehl?

XZ komprimiert einen Datenstrom. Bei mehreren Eingabedateien entstehen normalerweise getrennte komprimierte Dateien. Eine `.xz`-Datei enthält keine allgemeine Ordner- und Mitgliederverwaltung wie ZIP. Für eine Dateisammlung wird häufig zunächst TAR verwendet.

Das Format kann Inhaltsprüfwerte enthalten. Diese helfen bei der Erkennung bestimmter Beschädigungen, sind aber keine Unterschrift eines vertrauenswürdigen Absenders. Auch die höchste Kompressionsvorgabe garantiert weder den kleinsten Inhalt für jede Datei noch eine für jedes Zielgerät passende Ressourcennutzung.

Quelle ist die [offizielle Referenz der lokal verwendeten Version 5.4.5](https://raw.githubusercontent.com/tukaani-project/xz/v5.4.5/src/xz/xz.1), abgeglichen mit `xz --long-help`. Neuere Versionen können andere Voreinstellungen, insbesondere bei Threads, besitzen.

## 3. Syntax

```text
xz [OPTIONEN] [DATEI ...]
xz -d [OPTIONEN] [DATEI ...]
```

```bash
xz -k "notiz.txt"
xz -t "notiz.txt.xz"
xz -dc "notiz.txt.xz"
```

Ohne Modusoption komprimiert `xz`. `-d` dekomprimiert, `-t` verarbeitet zur Prüfung ohne normale Ausgabedatei. `-c` schreibt auf stdout und erhält die Eingabe. Ohne Dateinamen oder mit `-` wird stdin verwendet.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Eingabedatei behalten. | Für Übungen und erste Versuche ausdrücklich setzen. |
| `-d`, `--decompress` | Dekomprimieren. | Ohne `-k` kann auch dabei die Eingabe nach Erfolg entfernt werden. |
| `-c`, `--stdout` | Daten auf stdout schreiben. | Shell-Umleitungen können vorhandene Ziele trotzdem überschreiben. |
| `-t`, `--test` | Daten dekomprimieren und verwerfen. | Unterstützte gespeicherte Inhaltsprüfwerte werden geprüft. |
| `-l`, `--list` | XZ-Metadaten anzeigen. | Keine Archivmitgliederliste und kein vollständiger Inhaltstest. |
| `-0` bis `-9` | Kompressionsvorgabe wählen. | Beeinflusst Zeit und RAM auf Erzeuger- und Empfängerseite. |
| `-e`, `--extreme` | Mehr Suchaufwand für Kompression. | Nicht automatisch ein großer Nutzen; kann deutlich länger dauern. |
| `-T ANZAHL` | Threadzahl wählen. | `0` nutzt eine automatische Auswahl; Version und Build beachten. |
| `-M LIMIT`, `--memlimit=LIMIT` | Speicherbedarf begrenzen. | Bei Kompression gegebenenfalls Anpassung, bei Dekompression Fehler. |
| `--check=crc64` | Inhaltsprüfwert bei XZ-Kompression wählen. | CRC64 ist hier der Standard; keine Authentifizierung. |
| `--format=lzma` | Legacy-LZMA-Format wählen. | Dieses besitzt nicht die zusätzlichen XZ-Inhaltsprüfwerte. |
| `-f`, `--force` | Schutzregeln übergehen. | Kann vorhandene Ziele ersetzen und Linkbehandlung ändern. |
| `-v`, `--verbose` | Mehr Informationen. | Für Beobachtung und Diagnose. |

`--check=none` deaktiviert einen zusätzlichen Inhaltsprüfwert. Dafür ist eine besondere Begründung nötig; es gehört nicht in das Einsteigerbeispiel. Formatabhängige Optionen nicht beliebig kombinieren.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Testbereich wählen

```bash
xz --version
uebung="$(mktemp -d -t netmon-xz-XXXXXX)"
cd "$uebung"
pwd
```

Nach fehlgeschlagenem Wechsel nicht fortfahren. Die folgenden Dateien werden neu für die Übung angelegt.

### Schritt 2: Kleine Eingabe schreiben

```bash
printf '%s\n' 'Eigene XZ-Testnotiz.' > "original.txt"
```

Bei einer erneuten Ausführung im selben Ordner würde diese eigene Testdatei ersetzt. Ein neuer Übungsordner vermeidet den Konflikt.

### Schritt 3: Mit erhaltenem Original komprimieren

```bash
xz -k "original.txt"
```

Es sollen anschließend `original.txt` und `original.txt.xz` vorhanden sein. Bei sehr kleinen Dateien kann die Formatverwaltung größer sein als die eingesparten Bytes.

### Schritt 4: Informationen und Test unterscheiden

```bash
xz -l "original.txt.xz"
xz -t "original.txt.xz"
```

Die erste Zeile zeigt Struktur- beziehungsweise Größeninformationen. Die zweite verarbeitet die Daten zur Prüfung. Keine der beiden Zeilen legt eine normale entpackte Datei an.

### Schritt 5: Inhalt kontrolliert wiederherstellen

```bash
xz -dc "original.txt.xz" > "wiederhergestellt.txt"
cmp "original.txt" "wiederhergestellt.txt"
```

Der neue Ausgabename darf vorher nicht mit wichtigen Daten belegt sein. Eine Umleitung öffnet das Ziel bereits durch die Shell. `cmp` prüft den bekannten Inhalt byteweise. Beide Eingaben bleiben durch die stdout-Arbeitsweise erhalten.

## 6. Typische Anwendungsfälle

**Einzeldatei platzsparend ablegen:** Für eigene Daten mit `-k` beginnen und das Ergebnis zurücklesen, bevor die einzige Originalkopie aufgegeben wird.

**Dateisammlung komprimieren:** Eine vorbereitete TAR-Datei als einzelnen Datenstrom verarbeiten. Archivstruktur und Kompression bleiben getrennte Aufgaben.

**Software- oder Datenpakete prüfen:** Ein XZ-Test kann Übertragungs- beziehungsweise Speicherfehler erkennen. Eine vertrauenswürdige Signaturprüfung ist ein zusätzlicher, anderer Schritt.

**Ressourcen für ein Zielgerät planen:** Eine hohe Kompressionsvorgabe kann mehr Decoder-RAM benötigen. Die konkrete Empfängerumgebung testen, statt nur die Dateigröße auf dem Erzeuger zu vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Originale und bestehende Ziele

Ein erfolgreicher Standardaufruf ersetzt die Eingabe durch die komprimierte Datei. Mit `-k` wird das vermieden. `-f` kann vorhandene Ziele entfernen. Eine Shell-Umleitung schützt das Ziel nicht vor frühem Leeren, wenn später die Verarbeitung fehlschlägt.

### Speicher, Laufzeit und Ausgabemenge

Kompressionsvorgaben und Filter bestimmen Ressourcenbedarf. Ein RAM-Limit ist keine Plattenplatzquote. Mehr Threads können zusätzliches RAM benötigen; die Anzahl allein sagt nichts über eine sinnvolle Einstellung für den aktuellen Rechner aus.

### Format und Prüfumfang

`.xz`, Legacy-`.lzma` und rohe Datenströme unterscheiden sich. Das ältere `.lzma` unterstützt keine zusätzlichen Inhaltsprüfwerte. Auch ein XZ-Prüfwert verifiziert keine Quelle. `--ignore-check` nicht verwenden, um zweifelhafte Eingaben scheinbar erfolgreich zu verarbeiten.

### Keine vollständige Metadatensicherung

Die gewöhnliche Einzeldateikompression ersetzt keinen gezielten Sicherungsablauf für ACLs, erweiterte Attribute, Verzeichnisstruktur oder laufende Datenbanken. Ein bekannter Dateiinhalt und vollständige Systemwiederherstellbarkeit sind verschiedene Prüfziele.

### Umgebungsvorgaben

`XZ_DEFAULTS` und `XZ_OPT` können Optionen ergänzen. Bei überraschendem Verhalten diese Vorgaben und die lokale Hilfe prüfen. Keine unbekannten Shell-Vorgaben als unveränderliche Werkzeugeigenschaft beschreiben.

**Root-Rechte sind für das Beispiel nicht nötig.** Das Werkzeug verschafft keine fehlende Berechtigung und keine Konsistenz laufender Daten.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ziel existiert bereits | Original oder Ergebnis eines früheren Laufs liegt dort. | Neuen Namen wählen statt sofort zu erzwingen. |
| Speicherlimit überschritten | Parameter benötigen mehr RAM. | Einstellungen und Zielbedarf bewusst prüfen. |
| Unbekanntes Format | Falscher Container oder beschädigte Eingabe. | Erzeugungsweg und Dateiinhalt klären. |
| Kompression bringt wenig | Bereits komprimierte oder sehr kleine Daten. | Nutzen anhand echter Daten beurteilen. |
| Erwartete Ordnerliste fehlt | Einzelstrom mit Archiv verwechselt. | TAR- beziehungsweise ZIP-Ebene getrennt behandeln. |
| Nur Warnung gemeldet | Bestimmte Datei wurde ausgelassen oder anders behandelt. | Meldung und vollständigen Abschlussstatus lesen. |

XZ Utils verwendet `0` für Erfolg, `1` für Fehler und `2` für Warnung. Eine bereits vorhandene Ergebnisdatei ist kein Ersatz für diese Bewertung.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit `-k` und eigenen kleinen Daten beginnen.
2. Nicht sofort die höchste Vorgabe und alle Threads wählen.
3. Metadatenansicht, Inhaltstest und Wiederherstellung unterscheiden.
4. Wiederhergestellte Daten mit einer bekannten Referenz vergleichen.
5. Originale und Wörterbuch-/Filtervoraussetzungen dokumentieren.
6. Für neue Skripte den expliziten Hauptaufruf `xz -d` beziehungsweise `xz -dc` erwägen.

**Prüfstand:** Mit XZ Utils 5.4.5 wurden Kompression mit `-k`, Liste, Testmodus und stdout-Dekompression geprüft; der Inhalt war bytegleich. An einer zusätzlichen eigenen Kopie wurde die normale Entfernung der Quelle nach erfolgreicher Kompression bestätigt. Keine praktischen Tests zu Threadskalierung, Speichergrenzen, Sonderfiltern oder großen Datenbeständen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `unxz` | Dekompressionsalias. |
| `xzcat` | Dekompression auf stdout. |
| `lzma`, `unlzma` | Legacy-Formatwahl derselben Werkzeugfamilie. |
| `tar` | Bündelt eine Dateisammlung. |
| `zstd`, `gzip`, `bzip2` | Andere Verfahren mit eigenen Ressourcen- und Originalregeln. |

Ausgangseintrag: Datensatz 20 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
