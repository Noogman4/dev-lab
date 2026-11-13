---
id: "exiftool"
name: "exiftool"
command: "exiftool"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "exiftool"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 33
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle Projektdokumentation geprüft"
---

# exiftool – Metadaten lesen und Änderungen gezielt abgrenzen

## 1. Kurzbeschreibung

`exiftool` liest und verändert Metadaten in zahlreichen Bild-, Audio-, Video- und anderen Dateiformaten. Ein reiner Leseaufruf zeigt Angaben an; Zuweisungen wie `-TAG=WERT` wechseln in einen schreibenden Arbeitsablauf.

**Für eigene Dateien sind keine Root-Rechte nötig.** Das Werkzeug ist nicht generell nur lesend: Es kann Metadaten und bestimmte Dateisystemangaben verändern. Diese Dokumentation führt keine Metadatenänderung aus.

## 2. Was macht der Befehl?

Metadaten können Kameraeinstellungen, Zeitstempel, Ortskoordinaten, Kommentare, Urheberangaben und viele technische Werte umfassen. Unterschiedliche Gruppen wie EXIF, XMP und IPTC können ähnliche Angaben parallel enthalten. Ein einziger angezeigter Wert ist deshalb nicht zwingend die einzige gespeicherte Fassung.

Lesen und Schreiben werden anhand der Optionen unterschieden. Nicht jedes lesbare Format und nicht jeder Tag ist auch schreibbar. Die tatsächliche Unterstützung hängt vom Format, Tag und Versionsstand ab.

Grundlagen: [offizielle Anwendungsreferenz im Projektarchiv](https://raw.githubusercontent.com/exiftool/exiftool/master/html/exiftool_pod.html) und [offizielle FAQ](https://raw.githubusercontent.com/exiftool/exiftool/master/html/faq.html). Die Projektwebsite war bei dieser Prüfung nicht direkt abrufbar; verwendet wurden ihre Dokumentationsdateien im offiziellen Quellrepository. ExifTool ist hier nicht installiert.

## 3. Syntax

```text
exiftool [OPTIONEN] [-TAG ...] DATEI ...
exiftool [OPTIONEN] -TAG=WERT DATEI ...
```

```bash
exiftool -a -G1 -s "eigene-probe.jpg"
exiftool -j "eigene-probe.jpg"
```

Diese beiden Beispiele lesen Metadaten. Ein angehängtes Gleichheitszeichen kann die Bedeutung wesentlich ändern: `-Comment` liest einen Tag, `-Comment=Text` schreibt, und eine leere Zuweisung kann löschen. Befehle vor dem Ausführen genau prüfen.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-ver` | Versionsnummer anzeigen. | Vor Übernahme neuerer Funktionen prüfen. |
| `-a` | Doppelte Tags beim Lesen berücksichtigen. | Hilft beim Auffinden paralleler Angaben. |
| `-G1` | Gruppennamen der Familie 1 ausgeben. | Macht die Herkunft ähnlich benannter Tags sichtbarer. |
| `-s` | Technische Tagnamen anzeigen. | Beschreibender Anzeigename und wirklicher Tagname unterscheiden sich. |
| `-n` | Bestimmte formatierte Anzeigen in numerischer Form liefern. | Einheiten und Bedeutung weiterhin fachlich prüfen. |
| `-j` | JSON-Ausgabe. | Nicht gleichbedeutend mit dem schreibenden JSON-Import. |
| `-TAG` | Einen Tag lesen. | Unterstützte Gruppen und Namen nachschlagen. |
| `-TAG=WERT` | Einen Wert schreiben. | Verändert die Datei beziehungsweise einschlägige Angaben. |
| `-TAG=` | Einen Wert löschen, soweit unterstützt. | Nicht als reine Auswahl missverstehen. |
| `-r` | Unterverzeichnisse verarbeiten. | Kann aus einem kleinen Auftrag viele Änderungen machen. |
| `-ext ENDUNG` | Dateiauswahl nach Endung einschränken. | Dateiendung allein beweist kein tatsächliches Format. |
| `-overwrite_original` | Normale Originalkopie beim Schreiben vermeiden. | Für erste Versuche nicht verwenden. |

Die übliche Sicherung beim Schreiben hängt `_original` an den Namen an. Diese Kopie kann weiterhin sämtliche ursprünglichen privaten Metadaten enthalten. Sie gehört nicht automatisch in eine bereinigte Veröffentlichung.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Lokale Version prüfen

```bash
exiftool -ver
```

Wenn der Befehl fehlt, nicht so tun, als sei das Beispiel erfolgreich gelaufen. Den Paketstand und passenden Installationsweg getrennt klären. Für die vorliegende Dokumentation wurde nichts nachinstalliert.

### Schritt 2: Eigene Datei auswählen

Eine Kopie eines eigenen kleinen Bildes als `eigene-probe.jpg` bereitstellen. Eine fremde Datei nicht bloß umbenennen. Der folgende Arbeitsablauf liest nur; die Kopie verhindert trotzdem Verwechslungen mit einem einzigen Original.

### Schritt 3: Vollere Übersicht lesen

```bash
exiftool -a -G1 -s "eigene-probe.jpg"
```

`-a` berücksichtigt doppelte Angaben, `-G1` zeigt deren Gruppen und `-s` die technischen Namen. Die Ausgabe kann persönliche Werte enthalten. Sie deshalb nicht ungeprüft öffentlich teilen.

### Schritt 4: Einzelne Angaben gezielt auswählen

```bash
exiftool -FileType -ImageWidth -ImageHeight "eigene-probe.jpg"
```

Diese Auswahl enthält keine Zuweisung und ist damit kein Metadatenänderungsauftrag. Fehlende Tags können je nach Datei schlicht nicht vorhanden sein.

### Schritt 5: Bericht als eigene Datei ablegen

```bash
exiftool -j "eigene-probe.jpg" > "metadaten.json"
```

Die JSON-Ausgabe wird durch die Shell geschrieben. `metadaten.json` muss ein freier kontrollierter Zielname sein. Der Bericht kann genauso vertraulich sein wie die Bildmetadaten selbst.

## 6. Typische Anwendungsfälle

**Vor einer Veröffentlichung prüfen:** Ortsdaten, Kommentare und Urheberangaben sichtbar machen. Sichtprüfung und ein späterer bewusster Bereinigungsschritt sind unterschiedliche Aufgaben.

**Zeitangaben nachvollziehen:** Aufnahmezeit, Änderungszeit, Zeitzone und Dateisystemzeit auseinanderhalten. Ein ähnlicher Name bedeutet nicht dieselbe technische Bedeutung.

**Metadatenkonflikte untersuchen:** Parallele EXIF-, XMP- und IPTC-Werte mit Gruppenangaben lesen und erst danach eine passende Änderungsstrategie wählen.

**Maschinellen Bericht erzeugen:** JSON für eigene Weiterverarbeitung verwenden. Bei doppelten Tags und Gruppierung die konkrete Ausgabestruktur prüfen, bevor eine Anwendung blind Werte übernimmt.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Schreiben beginnt schon durch Optionen

Ein Zuweisungszeichen oder Import kann eine Leseanweisung in eine Änderung verwandeln. Ein vorhandenes `-j` ist nicht dasselbe wie ein schreibender JSON-Import. Bei rekursiver Auswahl können viele Dateien betroffen sein.

### Originalkopien und Veröffentlichung

Die normale `_original`-Kopie erleichtert die Rückkehr zum alten Stand, ersetzt aber keine unabhängige Sicherung. Nach einer Bereinigung darf sie nicht versehentlich mit veröffentlicht werden. `-overwrite_original` entfernt diesen üblichen Rückweg.

### Grenzen pauschaler Metadatenlöschung

Einzelne GPS-Tags zu entfernen bedeutet nicht, alle Ortsinformationen beseitigt zu haben. Auch Dateinamen, Vorschaubilder oder Bildinhalt können etwas verraten. Pauschale Löschrezepte sind außerdem nicht für jedes Format verlustfrei oder vollständig. Die [Projekt-FAQ zur sicheren Metadatenentfernung](https://raw.githubusercontent.com/exiftool/exiftool/master/html/faq.html) behandelt diese formatabhängigen Grenzen.

### Profile und fachliche Bedeutung

Ein Farbprofil kann für korrekte Darstellung wichtig sein. Zeitwerte ohne passende Zeitzoneninterpretation können falsch verstanden werden. Nach Änderungen sowohl relevante Werte als auch Nutzbarkeit der Datei unabhängig prüfen.

**Root-Rechte sind für eigene Lese- und Schreibdateien nicht erforderlich.** Der Auftrag zur Dokumentation erteilt keine Freigabe, echte Benutzerbilder zu bereinigen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Tag wird nicht gefunden | Anzeigename statt technischem Tag verwendet. | Mit `-s` und Gruppenangaben lesen. |
| Wert erscheint weiterhin | Andere Gruppe oder doppelte Angabe. | `-a -G1 -s` verwenden. |
| Keine Datei aktualisiert | Tag nicht schreibbar oder Auswahl passt nicht. | Format- und Tagunterstützung prüfen. |
| Originalkopie erscheint | Normales Sicherungsverhalten beim Schreiben. | Getrennt aufbewahren, nicht versehentlich veröffentlichen. |
| Zeit wirkt falsch | Andere Zeitzone oder andere Zeitart. | Semantik des konkreten Tags klären. |

Meldungen nicht unterdrücken, wenn eine Änderung tatsächlich geprüft werden soll. Die Existenz einer Datei beweist keinen korrekten Metadatenstand.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zunächst nur lesen, ohne Zuweisungen und ohne Rekursion.
2. Gruppen und technische Tagnamen anzeigen.
3. Berichte ebenso vertraulich behandeln wie Originalmetadaten.
4. Änderungen nur an eigenen Kopien planen.
5. Normalen Originalrückweg nicht vorschnell abschalten.
6. Bereinigungserfolg formatbezogen prüfen und nicht pauschal versprechen.

**Prüfstand:** Offizielle Anwendungsreferenz und FAQ wurden gelesen. ExifTool ist hier nicht installiert. Lesen, JSON-Ausgabe, Schreiben, Originalkopien und Metadatenentfernung wurden nicht praktisch ausgeführt und bleiben entsprechend gekennzeichnete Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `identify` | Untersucht Bildeigenschaften mit ImageMagick. |
| `ffprobe` | Analysiert Medienstreams und deren Metadaten. |
| `mediainfo` | Technische Medieninformationen. |
| `convert`, `magick` | Pixelverarbeitung mit eigener Metadatenbehandlung. |

Ausgangseintrag: Datensatz 33 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
