---
id: "identify"
name: "identify"
command: "identify"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "safe"
tags: ["audio video grafik", "identify"]
status: "Ausgearbeitet; Bildanalyse mit eigenen Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 36
reviewed_at: "2026-11-13"
locally_checked_version: "ImageMagick 6.9.12-98 Q16"
---

# identify – Bildformat, Abmessungen und Eigenschaften untersuchen

## 1. Kurzbeschreibung

`identify` liest Bildeigenschaften mit ImageMagick. Es zeigt beispielsweise Format, Pixelabmessungen, Farbraum und je nach Modus ausführliche Attribute. Unter ImageMagick 7 lautet der entsprechende Hauptaufruf gewöhnlich `magick identify`.

**Für eigene lesbare Bilder sind keine Root-Rechte nötig.** Normale Informationsaufrufe schreiben kein bearbeitetes Ersatzbild. Berichtsdateien durch Umleitung haben eigene Schreibwirkungen.

## 2. Was macht der Befehl?

Das Werkzeug erkennt ein unterstütztes Bildformat und stellt Eigenschaften des Bildes beziehungsweise seiner Frames dar. Eine Mehrbilddatei kann mehrere Ausgabeeinträge erzeugen. Angezeigte Pixelgröße und virtuelle Seitengeometrie sind unterschiedliche Angaben.

Ein lesbarer Header ist kein vollständiger Nachweis dafür, dass jedes Pixel decodiert werden kann oder ein Bild vertrauenswürdig ist. Mit `-ping` wird eine reduzierte Informationsabfrage angestrebt; aufwendige Statistiken und pixelabhängige Eigenschaften verlangen entsprechend mehr Verarbeitung.

Grundlagen: [offizielle ImageMagick-6-Referenz zu identify](https://legacy.imagemagick.org/script/identify.php), [Optionsreferenz](https://legacy.imagemagick.org/script/command-line-options.php) und die lokale ImageMagick-Version 6.9.12-98. Die Formatunterstützung hängt vom Build und dessen Richtlinien ab.

## 3. Syntax

```text
identify [OPTIONEN] BILD ...
```

```bash
identify "probe.ppm"
identify -format '%m %w %h\n' "probe.ppm"
```

`%m` ist das erkannte Format, `%w` die Breite und `%h` die Höhe. Die Formatzeichenfolge ist ein ImageMagick-Ausdruck und kein Shell-Befehl. Sie wird zitiert, damit die Shell Sonderzeichen und Leerzeichen nicht verändert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-verbose` | Ausführliche Eigenschaften. | Kann Metadaten und pixelabhängige Statistiken enthalten. |
| `-format TEXT` | Gewünschte Ausgabefelder. | Platzhalter anhand der verwendeten Version wählen. |
| `-ping` | Grundinformationen möglichst ohne vollständiges Pixellesen. | Kein vollständiger Bildprüfungslauf. |
| `-precision N` | Zahlenpräzision der Ausgabe einstellen. | Verändert nicht die tatsächliche Qualität des Originals. |
| `-limit TYP WERT` | Bestimmte Ressourcen begrenzen. | Keine umfassende Prozessisolation. |
| `-list format` | Unterstützte Formate auflisten. | Lese- und Schreibfähigkeit unterscheiden. |
| `-version` | Versions- und Buildangaben. | ImageMagick 6 und 7 getrennt prüfen. |
| `-regard-warnings` | Warnungen stärker berücksichtigen. | Für Automatisierung genaue lokale Semantik prüfen. |

Bildselektoren wie `datei.gif[0]` können einen einzelnen Frame wählen. Die eckigen Klammern zitieren und nicht mit einem gewöhnlichen Dateinamen ohne ImageMagick-Sonderbedeutung verwechseln. Eine Frameauswahl untersucht nicht alle übrigen Frames.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsbereich wählen

```bash
identify -version
uebung="$(mktemp -d -t netmon-identify-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel weiterarbeiten.

### Schritt 2: Einfaches eigenes Bild schreiben

```bash
printf 'P3\n4 2\n255\n255 0 0  255 0 0  255 0 0  255 0 0\n255 0 0  255 0 0  255 0 0  255 0 0\n' > "probe.ppm"
```

Die Datei beschreibt vier mal zwei rote Pixel als einfaches PPM. Es werden keine echten Benutzerbilder oder persönlichen Metadaten benötigt.

### Schritt 3: Standardansicht lesen

```bash
identify "probe.ppm"
```

Erwartet werden PPM und eine Größe von 4×2 Pixeln. Weitere Felder können je nach Version, Build und Datei variieren.

### Schritt 4: Eindeutige Kurzansicht anfordern

```bash
identify -ping -format '%m %w %h\n' "probe.ppm"
```

Die bekannte Testdatei soll `PPM 4 2` liefern. Die reduzierte Abfrage ist für diese Grunddaten geeignet, bestätigt aber keine allgemeine Qualität oder Herkunft.

### Schritt 5: Details untersuchen

```bash
identify -verbose "probe.ppm"
```

Für das einfache Testbild sind Farb- und Größenangaben nachvollziehbar. Bei fremden Bildern kann die ausführliche Ausgabe zusätzliche private Informationen enthalten; sie vor dem Teilen prüfen.

## 6. Typische Anwendungsfälle

**Bildkonvertierung kontrollieren:** Nach `convert` oder `magick` Format und erwartete Dimensionen prüfen. Ein dimensionsrichtiges Ergebnis kann trotzdem visuell falsch aussehen.

**Größenbestand erfassen:** Eigene Bilddateien anhand von Pixelabmessungen ordnen. Beliebige Dateinamen nicht über unzitierte Textlisten in Shell-Schleifen zurückführen.

**Formatprobleme untersuchen:** Erkannte Bildstruktur und verfügbaren Decoder prüfen, wenn eine Anwendung eine Datei ablehnt.

**Mehrbilddateien verstehen:** Anzahl und Eigenschaften der angezeigten Frames bewusst beachten, statt die erste Zeile als Beschreibung der ganzen Animation anzusehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Datenangaben nicht mit Herkunft verwechseln

Format, Zeitstempel oder gespeicherte Profile stammen aus der Eingabe. Sie beweisen weder einen vertrauenswürdigen Absender noch einen unveränderten Originalzustand. Eine erfolgreiche Kurzabfrage ist kein Schadsoftwaretest.

### Decoder und Ressourcen

Auch Analyse verarbeitet komplexe Formate und gegebenenfalls Hilfsdecoder. Große Dimensionen, viele Frames und Statistiken können RAM, Laufzeit und temporären Speicher beanspruchen. Sicherheitsrichtlinien nicht pauschal abschalten, wenn ein Format gesperrt ist.

### Private Metadaten

Ausführliche Listen können Kommentare, Profilinformationen oder weitere persönliche Angaben zeigen. Das Ausgeben allein sendet sie nicht ins Internet; eine später bewusst geteilte Berichtsdatei kann sie jedoch offenlegen.

### Geometrie und Dateinamensyntax

Pixelabmessungen, Auflösung in dpi und virtuelle Seitengeometrie sind nicht austauschbar. ImageMagick-Spezialsyntax in Pfaden und Framewahlen bewusst behandeln. Eine umbenannte Endung konvertiert keine Datei.

**Root-Rechte sind für die gezeigte eigene Analyse unnötig.** Ein Berichts-Zielpfad braucht gegebenenfalls normale Schreibrechte.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Decoder | Format oder zugehörige Bibliothek nicht verfügbar. | Build und lokale Formatliste prüfen. |
| Policy-Meldung | Verarbeitung bewusst eingeschränkt. | Ursache und geeigneten Arbeitsweg klären. |
| Mehrere Ausgabezeilen | Bildsequenz mit mehreren Frames. | Gewünschte Untersuchungsebene festlegen. |
| Dimensionen unerwartet | Orientierung, Framegeometrie oder anderes Original. | Pixelgröße und Metadaten getrennt prüfen. |
| Statistiken fehlen | Reduzierter `-ping`-Modus. | Für konkrete Pixelwerte passende vollständige Analyse wählen. |
| Bilddaten falsch trotz plausibler Kurzansicht | Nicht alle Daten in der Kurzabfrage geprüft. | Geeigneten vollständigen Decodier- und Inhaltsvergleich planen. |

Meldungen und Abschlussstatus lesen; eine einzelne plausible Ausgabezeile ist kein vollständiger Prüfnachweis.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit eigenem winzigem Bild beginnen.
2. Zuerst Format und Dimensionen, danach gezielte Details prüfen.
3. `-ping` nicht als vollständige Integritätsprüfung ausgeben.
4. Profile, Geometrie und sichtbare Pixel getrennt verstehen.
5. Technische Berichte vor dem Weitergeben auf private Angaben prüfen.
6. Bei fremden Formaten bestehende Sicherheitsgrenzen respektieren.

**Prüfstand:** Mit ImageMagick 6.9.12-98 Q16 wurden Standardansicht, `-ping -format` und ausführliche Ansicht eines selbst geschriebenen PPM-Bilds geprüft. Format PPM und 4×2 Pixel entsprachen der Erwartung. Die Quelldatei blieb bytegleich. Fremdbilder, beschädigte Dateien, Mehrbildformate und externe Decoder wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `magick identify` | Entsprechende Oberfläche in ImageMagick 7. |
| `convert`, `magick` | Verändern Bilddaten und schreiben Ausgaben. |
| `exiftool` | Metadatenanalyse und gezielte Metadatenänderungen. |
| `file` | Allgemeine Dateityperkennung mit anderen Grenzen. |

Ausgangseintrag: Datensatz 36 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
