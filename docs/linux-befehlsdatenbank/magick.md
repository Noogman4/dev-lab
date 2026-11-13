---
id: "magick"
name: "magick"
command: "magick"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "magick"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 37
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle ImageMagick-7-Dokumentation geprüft"
---

# magick – Bildverarbeitung mit der ImageMagick-7-Oberfläche

## 1. Kurzbeschreibung

`magick` ist die Hauptoberfläche von ImageMagick 7 für Bildkonvertierung und Bildoperationen. Es kann außerdem Unterwerkzeuge wie `identify` aufrufen. Ein vorhandenes `convert` aus ImageMagick 6 ist kein Nachweis dafür, dass `magick` installiert ist.

**Für eigene Bilder sind keine Root-Rechte nötig.** Konvertierung schreibt Ausgabedateien und kann bestehende Ziele überschreiben. Die folgenden Anleitungen werden hier nicht praktisch ausgeführt, weil ImageMagick 7 nicht installiert ist.

## 2. Was macht der Befehl?

Das Programm liest Bilder, wendet Einstellungen und Operatoren an und schreibt Ergebnisse. Einstellungen können für folgende Verarbeitung fortgelten; Operatoren bearbeiten die bereits gelesenen Bilder. Deshalb ist die Reihenfolge Teil der Bedeutung des Aufrufs.

Ein Formatwechsel betrifft unter anderem Kompression, Transparenz, Farbtiefe und Metadaten. Nicht jedes Format kann alle Eigenschaften des Originals erhalten. Mehrere Frames können zusätzliche Ausgabedateien oder eine andere Sequenzbehandlung erfordern.

Grundlagen: [offizielle magick-Referenz](https://imagemagick.org/magick/), [Verarbeitung und Bildgeometrie](https://imagemagick.org/command-line-processing/) und [Optionsreferenz](https://imagemagick.org/command-line-options/). Die Quellen beschreiben ImageMagick 7; hier ausgeführte Tests mit ImageMagick 6 werden nicht als Nachweis für diese Oberfläche übernommen.

## 3. Syntax

```text
magick [EINSTELLUNGEN] EINGABE [OPERATIONEN] AUSGABE
magick identify [OPTIONEN] BILD
```

```bash
magick "eigene-probe.png" -resize '800x600>' "vorschau.png"
magick identify "vorschau.png"
```

Der erste Aufruf schreibt eine neue Vorschau, der zweite untersucht deren Eigenschaften. Der zitierte Geometrieausdruck verhindert hier Vergrößerung und schützt `>` vor einer Shell-Umleitung.

## 4. Wichtige Optionen

| Option oder Unterwerkzeug | Wirkung | Konkreter Hinweis |
| --- | --- | --- |
| `-version` | Versions- und Builddaten. | Vor Rezeptübernahme prüfen. |
| `identify` | Informationsoberfläche. | Als erstes Argument hinter `magick`. |
| `-resize GEOMETRIE` | Größe ändern. | Geometriemodifikatoren bewusst unterscheiden. |
| `-auto-orient` | Gespeicherte Orientierung anwenden. | Vor relevanter Metadatenentfernung einsetzen. |
| `-crop GEOMETRIE` | Zuschneiden beziehungsweise Kacheln. | Kann mehrere Bilder erzeugen. |
| `+repage` | Virtuelle Seitengeometrie zurücksetzen. | Nach geeignetem Zuschnitt prüfen. |
| `-quality WERT` | Formatspezifische Qualitäts-/Kompressionseinstellung. | Kein universeller Prozentwert für sichtbare Qualität. |
| `-strip` | Profile und Kommentare entfernen. | Kann Farbmanagement verändern. |
| `-background FARBE` | Hintergrund einstellen. | Wirkt zusammen mit der jeweiligen Operation. |
| `-alpha OPTION` | Alphakanal behandeln. | Transparenz und Zielformat gemeinsam beurteilen. |
| `-limit TYP WERT` | Ressourcenbegrenzung wählen. | Keine umfassende Isolation fremder Bilddecoder. |
| `-list format` | Formatfähigkeiten anzeigen. | Auch lokale Richtlinien und Delegates beachten. |

`800x600` passt innerhalb eines Rahmens ein. `800x600^` deckt mindestens diesen Rahmen ab und kann darüber hinausgehen. `800x600!` erzwingt Maße und kann verzerren. Für Einsteiger ist eine zitierte Begrenzungsgeometrie meist nachvollziehbarer.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Vorhandene Version prüfen

```bash
magick -version
```

Fehlt der Aufruf, nicht einfach eine andere Installation als praktischen Nachweis ausgeben. Eine Installation wäre ein eigener Schritt und wurde für diese Dokumentation nicht vorgenommen.

### Schritt 2: Neuen eigenen Arbeitsordner verwenden

```bash
uebung="$(mktemp -d -t netmon-magick-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Eine bekannte eigene Bildkopie als `eigene-probe.png` bereitstellen.

### Schritt 3: Ausgangsmaße lesen

```bash
magick identify -format '%m %w %h\n' "eigene-probe.png"
```

Format und Pixelabmessungen notieren. Die Datei kann zusätzlich Profile und Metadaten besitzen, die mit diesen drei Feldern nicht vollständig beschrieben werden.

### Schritt 4: Neue Vorschau schreiben

```bash
magick "eigene-probe.png" -auto-orient -resize '800x600>' "vorschau.png"
```

Die Orientierung wird vor dem Skalieren angewendet. Bilder, die bereits innerhalb des Rahmens liegen, werden durch diese Geometrie nicht unnötig vergrößert. Der Zielname muss frei von wichtigen Daten sein.

### Schritt 5: Ergebnis kontrollieren

```bash
magick identify -format '%m %w %h\n' "vorschau.png"
```

Abmessungen zum gewünschten Rahmen und Seitenverhältnis prüfen. Anschließend eine eigene visuelle Kontrolle planen, wenn Farbe, Schärfe oder Transparenz wichtig sind. Die Originalkopie behalten.

## 6. Typische Anwendungsfälle

**Vorschau für eine Oberfläche:** In einen klar definierten Rahmen einpassen und die tatsächlichen Maße anschließend lesen.

**Formatwechsel:** Zielformat anhand von Transparenz, Farbtiefe und Empfängeranforderungen auswählen. Eine kompaktere Datei ist nicht automatisch ein gleichwertiges Original.

**Nachvollziehbare Verarbeitungskette:** Orientierung, Skalierung und weitere Operationen bewusst anordnen. Komplexe Stack- und Sequenzoperationen erst nach einfachen kontrollierten Schritten einsetzen.

**Informationsansicht:** Mit `magick identify` die passende Unteroberfläche verwenden, ohne unnötig ein neues Bild zu schreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Originale und Ausgaben trennen

Bestehende Ziele können überschrieben werden. Ein neuer Arbeitsordner und neue Dateinamen verhindern Verwechslungen. Für Originalerhalt nicht auf ein vermutetes Rückfrageverhalten vertrauen.

### Informationsverlust beim Formatwechsel

JPEG kann Transparenz nicht wie PNG speichern. Profilentfernung kann Farben beeinflussen; wiederholte verlustbehaftete Neukodierung kann Details verlieren. Sichtbare Pixel, Farbmanagement und private Metadaten getrennt prüfen.

### Fremde Formate und Richtlinien

Decoder und zusätzliche Hilfsprogramme können komplexe Inhalte verarbeiten. Lokale Sicherheitsrichtlinien beschränken bestimmte Formate und Ressourcen. Eine Sperre nicht pauschal aufheben, um ein einzelnes fremdes Rezept zum Laufen zu bringen.

### Geometrie und Sequenzen

Ein unzitiertes `>` kann zur Shell-Umleitung werden. Erzwungene Seitenverhältnisse können verzerren. Mehrere Frames können mehrere Dateien und erheblichen Speicherbedarf erzeugen. Dateinamen mit spezieller ImageMagick-Syntax bewusst behandeln.

**Root-Rechte sind für die eigene Bildverarbeitung nicht erforderlich.** Versionswechsel und Systeminstallation sind keine Voraussetzungen, die dieser Auftrag automatisch ausführt.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| magick fehlt, convert existiert | Nur ImageMagick 6 installiert. | Version und gewünschte Oberfläche klären. |
| Bild größer als Rahmen | Mindestgeometrie `^` statt Einpassung. | Geometriemodifikator prüfen. |
| Verzerrte Darstellung | `!` erzwingt abweichendes Verhältnis. | Seitenverhältnis erhalten. |
| Format gesperrt | Policy oder Decoder fehlt. | Grund und geeigneten Verarbeitungspfad prüfen. |
| Farben oder Transparenz ändern sich | Profil-/Alpha- oder Zielformateigenschaften. | Fachlich passende Einstellungen wählen. |
| Viele Dateien entstehen | Mehrbildquelle oder Sequenzoperation. | Frames und Ausgabeformat bewusst auswählen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Tatsächlich ImageMagick 7 nachweisen, bevor Beispiele übernommen werden.
2. Mit eigener Bildkopie und neuem Ausgabenamen beginnen.
3. Geometrieausdrücke zitieren.
4. Erst einfache Einzelbildoperationen prüfen.
5. Ergebnismaße und sichtbare Eigenschaften getrennt kontrollieren.
6. Keine vollständige Datenschutzbereinigung oder Farbtreue ohne passenden Test behaupten.

**Prüfstand:** Offizielle ImageMagick-7-Dokumentation wurde geprüft. Der Aufruf `magick` ist hier nicht installiert; die Beispiele wurden nicht ausgeführt. Ein vorhandener ImageMagick-6-Test wird bewusst nicht als Laufzeitprüfung dieser Version gewertet. Orientierung, Skalierung, Profilbehandlung und Ausgabeprüfung bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `convert` | Ältere ImageMagick-6-Oberfläche mit eigener Versionsumgebung. |
| `identify` | Eigenständige Bildeigenschaftsansicht, sofern installiert. |
| `mogrify` | Verarbeitet häufig bestehende Bilder direkt. |
| `exiftool` | Metadaten mit anderer Spezialisierung lesen und ändern. |

Ausgangseintrag: Datensatz 37 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
