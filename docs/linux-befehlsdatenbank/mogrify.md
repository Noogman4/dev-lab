---
id: "mogrify"
name: "mogrify"
command: "mogrify"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "danger"
tags: ["audio video grafik", "mogrify"]
status: "Ausgearbeitet; getrennte Ausgabe und Direktänderung an eigenen Testbildern geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 39
reviewed_at: "2026-11-13"
locally_checked_version: "ImageMagick 6.9.12-98 Q16"
---

# mogrify – Bildserien verarbeiten und Originale bewusst schützen

## 1. Kurzbeschreibung

`mogrify` verarbeitet Bilder mit ImageMagick und schreibt sie im üblichen Aufruf direkt an ihren bisherigen Pfad zurück. Es ist für Serienarbeit geeignet, besitzt dadurch aber ein erhebliches Überschreibpotenzial.

**Für eigene Bilder sind keine Root-Rechte nötig.** Die Risikoeinstufung bezieht sich auf direkte Änderungen an Originalen, insbesondere bei vielen ausgewählten Dateien. Für den Einstieg Kopien und einen getrennten Ausgabeordner verwenden.

## 2. Was macht der Befehl?

Die Bildoperatoren ähneln denen von `convert`. Der entscheidende Unterschied ist die Ausgabezuordnung: Ein gewöhnlicher `mogrify -resize ... bild.png` verändert diese Datei, statt ausdrücklich einen zweiten Ausgabenamen zu verlangen.

Mit `-path` lässt sich ein anderer Ausgabeordner wählen. Eine Formatänderung mit `-format` kann ebenfalls neue Namen erzeugen. Vorhandene Ziele im Ausgabeordner können trotzdem betroffen sein; weder Option ersetzt eine unabhängige Sicherung.

Grundlagen: [offizielle ImageMagick-6-Referenz zu mogrify](https://legacy.imagemagick.org/script/mogrify.php), [Optionsreferenz](https://legacy.imagemagick.org/script/command-line-options.php) und lokaler Stand ImageMagick 6.9.12-98. Für ImageMagick 7 den entsprechenden `magick mogrify`-Arbeitsweg gesondert prüfen.

## 3. Syntax

```text
mogrify [OPTIONEN] BILD ...
```

```bash
mogrify -path "Ausgabe" -resize '800x600>' "eigene-probe.png"
```

Das ist ein bewusst getrennter Ausgabeweg. Ohne `-path` beziehungsweise passende neue Formatzuordnung würde der normale Aufruf das ausgewählte Bild direkt verändern. Wildcards wie `*.jpg` können viele Dateien auswählen; zuerst die tatsächliche Auswahl prüfen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-path ORDNER` | Ausgaben in anderem Ordner schreiben. | Ordner vorher anlegen und vorhandene Namen prüfen. |
| `-format FORMAT` | Ausgabeformat wählen. | Neue Endung schützt nicht vor einem bereits vorhandenen Ziel gleichen Namens. |
| `-resize GEOMETRIE` | Größe verändern. | Verkleinerung entfernt Bilddetails. |
| `-thumbnail GEOMETRIE` | Vorschaubild erzeugen. | Für Veröffentlichung relevante Metadatenbehandlung prüfen. |
| `-auto-orient` | Gespeicherte Ausrichtung anwenden. | Vor einschlägiger Metadatenentfernung verwenden. |
| `-crop GEOMETRIE` | Ausschnitt beziehungsweise Kacheln. | Entfernt Inhalte oder erzeugt mehrere Ergebnisse. |
| `+repage` | Virtuelle Seitengeometrie zurücksetzen. | Nach bewusstem Zuschnitt passend einsetzen. |
| `-quality WERT` | Formatspezifische Qualität/Kompression. | Wiederholte verlustbehaftete Neukodierung kann schaden. |
| `-strip` | Profile und Kommentare entfernen. | Kann Farbdarstellung verändern und ist kein allgemeiner Datenschutzbeweis. |
| `-limit TYP WERT` | Ressourcen begrenzen. | Keine vollständige Isolation. |
| `-version` | Build- und Versionsdaten. | Konkrete Werkzeugfamilie prüfen. |

Geometrieausdrücke mit `>` oder `!` zitieren. Einstellungen und Bildoperatoren in der beabsichtigten Reihenfolge angeben.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen isolierten Übungsordner wählen

```bash
mogrify -version
uebung="$(mktemp -d -t netmon-mogrify-XXXXXX)"
cd "$uebung"
pwd
mkdir "Ausgabe"
```

Nur nach erfolgreichem Wechsel fortfahren. Keine Wildcard gegen einen echten Fotoordner als Einstieg verwenden.

### Schritt 2: Eigenes winziges Testbild schreiben

```bash
printf 'P3\n4 2\n255\n255 0 0  255 0 0  255 0 0  255 0 0\n255 0 0  255 0 0  255 0 0  255 0 0\n' > "probe.ppm"
```

Das Bild enthält vier mal zwei rote Pixel. Es besitzt keine unersetzlichen Inhalte.

### Schritt 3: Getrenntes Ergebnis erzeugen

```bash
mogrify -path "Ausgabe" -resize '2x2' "probe.ppm"
```

Im frischen Ausgabeordner entsteht `probe.ppm` mit veränderten Dimensionen. Die Eingabe im Übungsordner bleibt bei diesem getrennten Weg erhalten. Das ursprüngliche Seitenverhältnis führt zu 2×1 Pixeln.

### Schritt 4: Beide Stände prüfen

```bash
identify -format '%w %h\n' "probe.ppm"
identify -format '%w %h\n' "Ausgabe/probe.ppm"
```

Die Quelle soll 4×2 Pixel, das Ergebnis 2×1 Pixel besitzen. Die reine Existenz beider Dateien wäre kein Nachweis für richtige Dimensionen.

### Schritt 5: Auf echte Serien nur bewusst übertragen

Vor einer späteren Serienverarbeitung Dateiauswahl und Namenskonflikte prüfen und eine unabhängige Originalkopie behalten. Der Dokumentationsauftrag führt diese Übertragung auf Benutzerbilder nicht aus.

## 6. Typische Anwendungsfälle

**Eigene Bildserie skalieren:** Zunächst einzelne Kopie prüfen, dann nur bewusst ausgewählte weitere Dateien behandeln.

**Formatserien erzeugen:** Mit neuer Endung und getrenntem Ausgabeort arbeiten. Unterschiedliche Ausgangsformate mit gleichem Basisnamen können dasselbe Ziel beanspruchen.

**Orientierung vereinheitlichen:** Die tatsächlichen Metadaten und Bilder prüfen, bevor ein gemeinsamer Operator auf alle Quellen angewendet wird.

**Direktänderung eigener entbehrlicher Kopien:** Ein kompakter Arbeitsweg, wenn die direkte Veränderung ausdrücklich gewollt und der Rückweg gesichert ist.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Normaler Aufruf verändert das Original

Mogrify besitzt keinen allgemeinen automatischen Originalrückweg. Ein falsch gewählter Ordner oder eine breite Wildcard kann viele Bilder verändern. Verkleinerte oder verlustbehaftet neu kodierte Inhalte lassen sich aus dem Ergebnis nicht zuverlässig zum Original rekonstruieren.

### Ausgabeordner kann ebenfalls Konflikte enthalten

`-path` trennt Orte, garantiert aber keine freien Zieldateien. Vorhandene Ergebnisse mit gleichem Namen können ersetzt werden. Einen frischen Zielordner wählen und vor Serienarbeit die Namenszuordnung prüfen.

### Serien sind keine atomare Gesamtaktion

Ein Abbruch kann bereits verarbeitete Bilder verändert haben, während weitere unverändert bleiben. Nicht von einem vollständigen Zurückrollen ausgehen. Fortschritt, Meldungen und tatsächliche Ergebnisse prüfen.

### Metadaten, Farbe und Mehrbilddateien

Profile und Orientierung können entscheidend sein. Eine pauschale Bereinigung kann nützliche Angaben entfernen. Animierte oder mehrseitige Formate verlangen eigene Behandlung; ein Einzelbildrezept ist nicht automatisch korrekt für die ganze Sequenz.

### Fremddecoder und Ressourcen

Große Dimensionen, viele Frames oder Decoderdelegates können erheblichen Aufwand verursachen. Sicherheitsrichtlinien nicht pauschal lockern. Für Tests nur bekannte kleine eigene Bilder verwenden.

**Root-Rechte sind für eigene Serien nicht erforderlich.** Höhere Rechte würden lediglich die möglichen Schreibziele erweitern, nicht den Vorgang sicherer machen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Original plötzlich klein | Normaler In-place-Aufruf. | Nur aus unabhängiger Originalkopie wiederherstellen. |
| Ausgabeordner fehlt | `-path` verweist auf nicht angelegtes Ziel. | Frischen Ordner bewusst erstellen. |
| Vorhandenes Ergebnis ersetzt | Gleicher Ausgabename bereits belegt. | Neue Zielstruktur und Zuordnung prüfen. |
| Falsches Seitenverhältnis | Erzwungene Geometrie. | Seitenverhältnis erhaltende Geometrie wählen. |
| Nur Teil der Serie verändert | Fehler beziehungsweise Abbruch während Verarbeitung. | Tatsächlichen Bestand einzeln prüfen. |
| Format gesperrt | Policy oder Decoderanforderung. | Grund klären statt Schutz pauschal aufheben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zuerst `convert` beziehungsweise `magick` mit ausdrücklichem neuen Ziel erwägen.
2. Bei mogrify einen frischen `-path`-Ordner verwenden.
3. Nur eine eigene Testdatei vor einer Serie bearbeiten.
4. Originale unabhängig sichern.
5. Wildcards und Zielnamenskonflikte vorher prüfen.
6. Abbruch nicht als vollständiges Zurückrollen verstehen.

**Prüfstand:** Mit ImageMagick 6.9.12-98 wurden ausschließlich eigene PPM-Testbilder verarbeitet. `-path Ausgabe -resize 2x2` erhielt die Quelle und erzeugte 2×1 Pixel. Ein zusätzlicher normaler Direktaufruf veränderte die entbehrliche eigene Quelldatei tatsächlich; dies bestätigte das dokumentierte In-place-Risiko. Keine echten Benutzerbilder, Serien, Profile oder Mehrbilddateien wurden verändert.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `convert` | ImageMagick 6 mit ausdrücklich benannter Ausgabe. |
| `magick` | ImageMagick-7-Hauptoberfläche. |
| `identify` | Eigenschaften ohne normale Bildbearbeitung lesen. |
| `exiftool` | Gezielte Metadatenverarbeitung. |

Ausgangseintrag: Datensatz 39 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
