---
id: "convert"
name: "convert"
command: "convert"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "convert"]
status: "Ausgearbeitet; Beispiele mit eigenen Bildtestdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 32
reviewed_at: "2026-11-13"
locally_checked_version: "ImageMagick 6.9.12-98 Q16"
---

# convert – Bilder mit ImageMagick 6 in neue Ausgaben umwandeln

## 1. Kurzbeschreibung

`convert` ist ein Bildverarbeitungswerkzeug von ImageMagick 6. Es kann Formate umwandeln, Bilder skalieren, zuschneiden und mehrere Verarbeitungsschritte kombinieren. Unter ImageMagick 7 ist der Hauptaufruf `magick`; dessen konkrete Umgebung getrennt prüfen.

**Für eigene Bilder sind keine Root-Rechte nötig.** Die Verarbeitung schreibt Ausgaben und kann vorhandene Zieldateien überschreiben. Für erste Versuche immer einen neuen Ausgabenamen verwenden.

## 2. Was macht der Befehl?

Das Programm liest Bilddaten, wendet die angegebenen Operationen an und schreibt ein Zielbild. Die Endung beziehungsweise ein ausdrücklich gewählter Formatpräfix beeinflusst die Ausgabe. JPEG, PNG und andere Formate unterscheiden sich bei Transparenz, Farbtiefe, Kompression und Metadaten.

ImageMagick verarbeitet außerdem Bildsequenzen und kann für einzelne Formate zusätzliche Decoder oder Hilfsprogramme verwenden. Die installierten Funktionen und Sicherheitsrichtlinien bestimmen, was tatsächlich verfügbar ist. Eine reine Dateiendungsänderung außerhalb des Programms konvertiert keine Bilddaten.

Quellen: [offizielle ImageMagick-6-Referenz zu convert](https://legacy.imagemagick.org/script/convert.php), [Optionsreferenz](https://legacy.imagemagick.org/script/command-line-options.php) und die lokale Hilfe von ImageMagick 6.9.12-98. Die Dokumentation beschreibt übliche Optionen, nicht sämtliche möglichen Bildoperatoren.

## 3. Syntax

```text
convert [EINSTELLUNGEN] EINGABE [OPERATIONEN] AUSGABE
```

```bash
convert "bild.png" -resize '800x600>' "klein.png"
```

Der Ausdruck `800x600>` passt innerhalb des Begrenzungsrahmens unter Erhalt des Seitenverhältnisses ein und verhindert hier eine Vergrößerung kleinerer Bilder. Anführungszeichen schützen `>` vor der Shell-Interpretation als Umleitung. Die Reihenfolge von Einstellungen und Operatoren ist relevant.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-resize GEOMETRIE` | Bildgröße ändern. | Ohne `!` normalerweise Seitenverhältnis erhalten. |
| `-thumbnail GEOMETRIE` | Vorschaubild erzeugen. | Metadatenbehandlung und Qualitätsziel gesondert prüfen. |
| `-auto-orient` | Ausrichtung anhand gespeicherter Orientierung anwenden. | Vor Entfernen einschlägiger Metadaten einsetzen. |
| `-crop GEOMETRIE` | Bildausschnitt beziehungsweise Kacheln erzeugen. | Geometrie kann mehrere Ausgabebilder erzeugen. |
| `+repage` | Virtuelle Seitengeometrie zurücksetzen. | Häufig nach bewusstem Zuschneiden sinnvoll. |
| `-rotate WINKEL` | Drehen. | Kann Fläche und Hintergrund ändern. |
| `-quality WERT` | Formatspezifische Qualitäts-/Kompressionseinstellung. | Gleicher Zahlenwert bedeutet nicht bei jedem Format dieselbe Eigenschaft. |
| `-strip` | Profile und Kommentare entfernen. | Kann für Farbe oder Orientierung wichtige Informationen entfernen. |
| `-colorspace NAME` | Farbraumoperation wählen. | Nicht beliebig mit sauberem ICC-Profilmanagement gleichsetzen. |
| `-limit TYP WERT` | Bestimmte Ressourcen begrenzen. | Keine vollständige Prozessisolation. |
| `-version` | Versions- und Buildinformationen. | Verfügbare Delegates können abweichen. |
| `-list format` | Formatunterstützung auflisten. | Lese-/Schreibunterstützung und lokale Policy beachten. |

Eine erzwungene Geometrie wie `800x600!` kann das Seitenverhältnis verzerren. Für normale Vorschaubilder zunächst einen Begrenzungsrahmen wählen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Neue Testumgebung wählen

```bash
convert -version
uebung="$(mktemp -d -t netmon-convert-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Eigenes winziges Bild erzeugen

```bash
printf 'P3\n4 2\n255\n255 0 0  255 0 0  255 0 0  255 0 0\n255 0 0  255 0 0  255 0 0  255 0 0\n' > "probe.ppm"
```

Dies beschreibt ein einfaches PPM-Bild mit vier mal zwei roten Pixeln. Es enthält keine fremden Bilddaten, persönlichen Metadaten oder externen Ressourcen.

### Schritt 3: Skalieren und als PNG schreiben

```bash
convert "probe.ppm" -resize '2x2' "klein.png"
```

Der Rahmen ist zwei mal zwei Pixel. Wegen des ursprünglichen Seitenverhältnisses wird ein Bild mit zwei mal einem Pixel erwartet. Das Ausgangsbild bleibt bei diesem getrennten Zielpfad erhalten.

### Schritt 4: Ergebnisdimensionen lesen

```bash
identify -format '%w %h %m\n' "klein.png"
```

Erwartet wird `2 1 PNG`. Damit sind Größe und Ausgabeformat geprüft. Diese Kontrolle bewertet keine fotografische Qualität und keine Farbechtheit komplexer Bilder.

## 6. Typische Anwendungsfälle

**Vorschaubilder erzeugen:** Große eigene Bilder in einen begrenzten Rahmen einpassen, ohne kleine Eingaben unnötig zu vergrößern.

**Format wechseln:** Beispielsweise ein geeignetes Rasterbild als PNG speichern. Vorher prüfen, welche Transparenz- und Farbinformationen der Empfänger braucht.

**Eigene Bilder vorbereiten:** Orientierung anwenden und gezielt Metadaten beurteilen. Ein pauschales Entfernen aller Profile ist nicht für jede Veröffentlichung sinnvoll.

**Einzelne Verarbeitungsschritte kombinieren:** Reihenfolge bewusst aufbauen und nach jedem wesentlichen Schritt ein bekanntes Ergebnis kontrollieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Ausgaben und Qualitätsverlust

Ein belegter Zielpfad kann überschrieben werden. Verlustbehaftete Formate und wiederholte Neukodierung können Details verlieren. Original separat behalten; eine große JPEG-Datei ist nicht automatisch ein hochwertiges Original.

### Metadaten und Farbe

Bilder können Ortsangaben, Aufnahmedaten und Kommentare enthalten. `-strip` entfernt zugleich eventuell nützliche Farbprofile. Sichtbare Pixel, Metadaten und korrekte Farbdarstellung getrennt beurteilen.

### Fremdformate und Ressourcen

Bilddecoder und Delegates verarbeiten komplexe Eingaben. Sehr große Dimensionen oder viele Frames können viel RAM, temporären Speicher und Zeit benötigen. Eine Policy-Sperre nicht blind aufheben, nur weil ein fremdes Format nicht geöffnet wird.

### Mehrere Bilder und besondere Namen

GIFs und andere Sequenzen können mehrere Frames enthalten. Eine Operation kann daraus mehrere Dateien erzeugen oder Animationseigenschaften verändern. ImageMagick kennt außerdem besondere Dateisyntax und Formatpräfixe; Dateinamen nicht wie beliebige ungeprüfte Kommandoargumente zusammensetzen.

**Root-Rechte sind für die eigene Bildverarbeitung unnötig.** Ein freier Arbeitsordner und getrennte Ausgaben machen die Wirkungen nachvollziehbarer.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Bild verzerrt | Erzwungene Geometrie mit `!`. | Seitenverhältnis bewusst erhalten. |
| Ausgabe falsch benannt oder fehlt | Shell hat `>` aus Geometrie interpretiert. | Gesamte Geometrie zitieren. |
| Format nicht erlaubt | Lokale Sicherheitsrichtlinie oder fehlender Decoder. | Grund und geeigneten Verarbeitungsweg prüfen. |
| Farben ändern sich | Profil beziehungsweise Farbraum verändert. | Farbmanagement und Zielanforderungen prüfen. |
| Transparenz verschwindet | Zielformat oder Hintergrundbehandlung ungeeignet. | Format und Alphakanal bewusst wählen. |
| Viele Dateien entstehen | Mehrbild-Eingabe oder Kacheloperation. | Frameauswahl und Geometrie klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit eigenen kleinen Bildern und getrennten Ausgaben beginnen.
2. Geometriezeichen wie `>` und `!` zitieren.
3. Originale vor Qualitäts- und Metadatenänderungen behalten.
4. Dimensionen und Format anschließend prüfen.
5. Bei Policy-Meldungen keine pauschale Freigabe aller Formate setzen.
6. ImageMagick 6 und 7 anhand der realen Version unterscheiden.

**Prüfstand:** Mit ImageMagick 6.9.12-98 Q16 wurde ein selbst geschriebenes PPM-Bild von 4×2 Pixeln in ein PNG innerhalb eines 2×2-Rahmens umgewandelt. `identify` bestätigte 2×1 Pixel und PNG; die Quelle blieb bytegleich. Farbprofile, Transparenz, Fremdbilder, Animationen und besondere Decoder wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `magick` | Hauptoberfläche von ImageMagick 7. |
| `identify` | Bilddaten und Eigenschaften untersuchen. |
| `mogrify` | Bearbeitet häufig direkt bestehende Dateien; anderes Risiko. |
| `exiftool` | Liest und verändert Metadaten mit eigener Syntax. |

Ausgangseintrag: Datensatz 32 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
