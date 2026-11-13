---
id: "mediainfo"
name: "mediainfo"
command: "mediainfo"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "safe"
tags: ["audio video grafik", "mediainfo"]
status: "Ausgearbeitet; Analyse mit eigenen Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 38
reviewed_at: "2026-11-13"
locally_checked_version: "MediaInfoLib 24.01, Kommandozeilenoberfläche"
---

# mediainfo – Technische Medienangaben als Text oder JSON lesen

## 1. Kurzbeschreibung

`mediainfo` zeigt technische Informationen und Tags aus Audio- und Videodateien. Es unterscheidet allgemeine Containerdaten von Angaben zu Audio-, Video-, Text- und weiteren Spuren.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Die gewöhnliche Analyse konvertiert die Quelle nicht. Berichtsoptionen und Shell-Umleitungen schreiben dagegen eigene Ausgaben. Hier werden ausschließlich lokale Testdateien untersucht.

## 2. Was macht der Befehl?

Das Programm erkennt unterstützte Medienstrukturen und stellt verfügbare Eigenschaften dar. Dazu können Codec, Abtastrate, Kanalzahl, Auflösung, Laufzeit, Sprache und Tags gehören. Nicht jede Datei enthält alle Angaben und nicht jedes Feld stammt aus einer vollständigen Decodierung des Inhalts.

Die Kommandozeilenoberfläche ist von einer eventuell installierten grafischen MediaInfo-Anwendung zu unterscheiden. Ein Bericht zeigt technische Merkmale; er bestätigt keine fehlerfreie reale Wiedergabe oder vertrauenswürdige Herkunft.

Grundlagen: [offizielle Projektübersicht](https://mediaarea.net/en/MediaInfo), [Distributions-Manpage](https://manpages.debian.org/trixie/mediainfo/mediainfo.1.en.html) und lokale Hilfe von MediaInfoLib 24.01. Die Manpage enthält ältere Beschreibungsstände; aktuelle lokale Optionen wie JSON wurden deshalb direkt abgeglichen.

## 3. Syntax

```text
mediainfo [OPTIONEN] DATEI [DATEI ...]
mediainfo --Inform=VORLAGE DATEI
```

```bash
mediainfo "probe.wav"
mediainfo --Output=JSON "probe.wav"
mediainfo '--Inform=Audio;%Format%|%SamplingRate%|%Channels%' "probe.wav"
```

Die Vorlage enthält Abschnitt und Feldplatzhalter. Das gesamte Argument wird zitiert, damit Semikolon und senkrechte Striche nicht als Shell-Steuerzeichen wirken. `--Inform` formatiert die Informationsausgabe und ist keine Medienkonvertierung.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--Version` | Versionsangabe. | CLI und Bibliotheksstand erkennen. |
| `--Help` | Lokale Hilfe. | Vor neuen Sonderoptionen prüfen. |
| `--Full`, `-f` | Umfangreichere Angaben. | Kann mehr private Tags enthalten. |
| `--Output=JSON` | JSON-Bericht. | Mit einem JSON-Parser auswerten. |
| `--Output=XML` | XML-Bericht. | Schema und konkrete Version beachten. |
| `--Output=HTML` | HTML-Ausgabe. | Berichtformat, kein neues Medium. |
| `--Inform=VORLAGE` | Gezielt formatierte Felder. | Leere beziehungsweise fehlende Werte bewusst behandeln. |
| `--Info-Parameters` | Verfügbare Vorlagenparameter auflisten. | Nicht jede Datei besitzt jeden Parameter. |
| `--Language=raw` | Nicht übersetzte Kennungen wählen. | Hilfreich für stabile eigene Zuordnung. |
| `--LogFile=DATEI` | Bericht direkt speichern. | Schreibt auf den gewählten Zielpfad. |
| `--File_TestContinuousFileNames=0` | Erkennung fortlaufender Bildsequenznamen abschalten. | Für bewusst einzelne Bildquellen gegebenenfalls relevant. |

Textausgaben können lokalisierte Einheiten oder formatierte Werte enthalten. Für automatisierte Auswertung nicht allein nach zufälliger Spaltenposition oder übersetztem Anzeigenamen parsen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und eigene Eingabe auswählen

```bash
mediainfo --Version
```

Eine bekannte eigene kurze WAV-Datei als `probe.wav` bereitstellen. Eine Geräteeingabe oder ein Online-Dienst ist dafür nicht nötig. Im tatsächlichen Test wurde eine selbst erzeugte stille PCM-Datei mit 8.000 Hz, einem Kanal und 0,1 Sekunden verwendet.

### Schritt 2: Standardbericht lesen

```bash
mediainfo "probe.wav"
```

Die Abschnitte „General“ und „Audio“ beschreiben unterschiedliche Ebenen. WAV ist ein Container; PCM ist die Kodierung des Audiostreams. Diese Begriffe nicht als austauschbare Formate behandeln.

### Schritt 3: Strukturierte Ausgabe anfordern

```bash
mediainfo --Output=JSON "probe.wav"
```

Die JSON-Struktur enthält Medien- und Trackangaben. Bei mehreren Spuren nicht einfach den ersten Track als Audiospur annehmen, sondern dessen Typ prüfen.

### Schritt 4: Kleine gezielte Ansicht erzeugen

```bash
mediainfo '--Inform=Audio;%Format%|%SamplingRate%|%Channels%' "probe.wav"
```

Für die beschriebene Testdatei wurde `PCM|8000|1` erwartet. Die Platzhalter sind technische Parameternamen und nicht beliebige übersetzte Bezeichnungen aus einer Benutzeroberfläche.

### Schritt 5: Bericht bewusst speichern

```bash
mediainfo --Output=JSON "probe.wav" > "medieninfo.json"
```

Der Ausgabename muss frei von wichtigen Daten sein. Die Shell kann ihn schon vor einem späteren Analysefehler leeren. Den erzeugten Bericht auf erwartete Tracks und Werte prüfen, nicht nur auf seine Existenz.

## 6. Typische Anwendungsfälle

**Kompatibilität einordnen:** Prüfen, welcher Container und welche Codecs vorliegen, wenn eine Anwendung die Datei nicht abspielt.

**Konvertierungsergebnis kontrollieren:** Erwartete Rate, Kanalzahl, Auflösung und Spurauswahl nach einem eigenen Medienauftrag überprüfen.

**Technische Bestandsliste erstellen:** Mit gezielten Feldern übersichtliche Informationen aus eigenen Medien sammeln. Fehlende Werte und mehrere Spuren ausdrücklich berücksichtigen.

**Diagnosebericht teilen:** Nur die für das Problem benötigten Angaben ausgeben und private Tags vorher prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Berichte können private Angaben enthalten

Titel, Kommentare, Urheber, Aufnahmezeiten und Pfade können sichtbar werden. JSON oder XML anonymisieren diese Daten nicht. Einen Bericht vor dem Weitergeben prüfen und nur erforderliche Angaben teilen.

### Analyse ist kein vollständiger Qualitätstest

Plausible Metadaten beweisen weder korrekte Bild-/Tonqualität noch vollständige Decodierbarkeit aller Inhalte. Containerlaufzeit und Streamlaufzeit können verschieden sein. Eine technische Übersicht ersetzt keinen zweckgerechten Inhalts- und Wiederherstellungstest.

### Eingaben und Ressourcen

Je nach Build können Medienquellen mehr als einfache lokale Dateien sein. Für die hier beschriebene Übung lokale Pfade verwenden. Sehr komplexe Medien oder tiefe Analyseoptionen können Zeit und Ressourcen benötigen; ein lesender Aufruf ist keine Decoder-Sandbox.

### Formate und Vorlagen

Feldnamen, Verfügbarkeit und Darstellung können versionsabhängig sein. Ein leerer Vorlagenwert ist nicht automatisch null und nicht zwangsläufig ein Fehler. Trennzeichen in beliebigen Textwerten können einfache selbstgebaute Listenformate mehrdeutig machen; für solche Daten ein strukturiertes Ausgabeformat vorziehen.

**Root-Rechte sind für die lokale Analyse unnötig.** Ein Berichtsziel benötigt lediglich passende normale Schreibrechte.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Feld leer | Angabe nicht vorhanden oder falscher Abschnitt. | Standardbericht und Parameternamen prüfen. |
| Andere Einheit als erwartet | Formatierte Anzeige statt Rohwert. | Gewünschte Ausgabe und Semantik klären. |
| JSON enthält mehrere Tracks | Container und mehrere Streams separat erfasst. | Tracktypen bewusst auswählen. |
| Datei nicht erkannt | Format fehlt, Daten beschädigt oder Pfad falsch. | Quelle und konkrete Meldung prüfen. |
| Bericht unerwartet groß | Vollständige beziehungsweise detaillierte Ausgabe. | Benötigte Felder eingrenzen. |
| Vorlage wird als Shell-Befehl zerlegt | Sonderzeichen nicht zitiert. | Gesamtes Inform-Argument zitieren. |

Meldungen und tatsächlichen Bericht gemeinsam beurteilen. Eine leere oder unvollständige Informationsausgabe ist kein positiver Qualitätsnachweis.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit einem eigenen bekannten lokalen Medium beginnen.
2. Container und Streamangaben getrennt lesen.
3. Erst Standardbericht, danach gezielte Felder verwenden.
4. Vorlagen mit Shell-Sonderzeichen vollständig zitieren.
5. Für automatische Verarbeitung strukturierte Daten wirklich parsen.
6. Berichte vor dem Weitergeben auf private Angaben prüfen.

**Prüfstand:** MediaInfoLib 24.01 wurde mit einer selbst erzeugten stillen PCM-WAV-Datei geprüft. Standardbericht, JSON und die gezielte Audio-Vorlage funktionierten; PCM, 8.000 Hz und ein Kanal wurden bestätigt. Die Quelle blieb bytegleich. Video, Untertitel, Netzquellen, Bildsequenzen und tiefe Inhaltsprüfung wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ffprobe` | Andere strukturierte Medienanalyse. |
| `ffmpeg` | Konvertiert und schreibt Medien. |
| `exiftool` | Metadaten lesen und gezielt verändern. |
| `identify` | Bildeigenschaften mit ImageMagick. |

Ausgangseintrag: Datensatz 38 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
