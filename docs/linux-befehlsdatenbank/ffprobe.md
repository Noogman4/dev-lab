---
id: "ffprobe"
name: "ffprobe"
command: "ffprobe"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "safe"
tags: ["audio video grafik", "ffprobe"]
status: "Ausgearbeitet; Dateianalyse mit eigenen Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 35
reviewed_at: "2026-11-13"
locally_checked_version: "FFprobe 6.1.1-3ubuntu5"
---

# ffprobe – Medienstreams gezielt und maschinenlesbar untersuchen

## 1. Kurzbeschreibung

`ffprobe` liest technische Angaben aus Medienquellen. Es zeigt Container, Streams, Codecs, Laufzeiten und Metadaten in menschenlesbaren oder strukturierten Ausgabeformaten.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Ein normaler lokaler Analyseaufruf konvertiert die Quelle nicht. Eine URL kann jedoch Netzwerkzugriffe auslösen; Berichtsdateien und Umleitungen schreiben eigene Ausgaben.

## 2. Was macht der Befehl?

Eine Mediendatei kann mehrere Video-, Audio-, Untertitel- und andere Streams enthalten. ffprobe trennt deren Eigenschaften von Angaben zum Container. Beispielsweise ist `wav` der Container und `pcm_s16le` eine darin mögliche Audiokodierung.

Die Analyse liest je nach Optionen mehr als nur einen Dateinamen oder eine kurze Kopfzeile. Paket- und Framezählungen können umfangreiche Verarbeitung verursachen. Eine plausible Metadatenliste ist keine vollständige Qualitäts-, Harmlosigkeits- oder Herkunftsprüfung.

Grundlagen: [offizielle FFprobe-Dokumentation](https://ffmpeg.org/ffprobe.html), die [FFmpeg-Referenz zur Streamauswahl](https://ffmpeg.org/ffmpeg.html) und lokale Versions-/Hilfedaten von FFprobe 6.1.1-3ubuntu5. Neuere Dokumentationsfunktionen nicht ohne Prüfung auf den lokalen Build übertragen.

## 3. Syntax

```text
ffprobe [OPTIONEN] EINGABE
```

```bash
ffprobe -v error -show_format -show_streams -of json "probe.wav"
```

`-show_format` fordert Containerangaben an, `-show_streams` Streamangaben, `-of json` wählt strukturierte Ausgabe. `-v error` reduziert begleitende Meldungen, nicht den Informationsumfang der ausdrücklich gewählten Berichte.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-version` | Versions- und Buildinformationen. | Vor konkreter Funktionsübernahme prüfen. |
| `-v error` | Nur einschlägige Fehler protokollieren. | Keine Garantie, dass leere Ausgabe einen sinnvollen Bericht bedeutet. |
| `-show_format` | Containerdaten ausgeben. | Von Streamdaten unterscheiden. |
| `-show_streams` | Streambeschreibungen ausgeben. | Kann mehrere Sprachen oder Kommentarspuren zeigen. |
| `-select_streams a:0` | Ersten Audiostream auswählen. | Relativer Audioindex, nicht zwingend globaler Streamindex null. |
| `-show_entries AUSWAHL` | Gewünschte Abschnitte und Felder auswählen. | Ausgabereihenfolge nicht als starre Feldreihenfolge voraussetzen. |
| `-of json` | JSON-Writer wählen. | Geeignet für einen wirklichen JSON-Parser. |
| `-show_packets` | Paketinformationen. | Kann sehr große Berichte erzeugen. |
| `-show_frames` | Frameinformationen. | Mehr Aufwand und Ausgabe als eine Kurzansicht. |
| `-count_frames` | Frames für gewählte Streams zählen. | Kann umfangreiches Lesen beziehungsweise Decodieren verlangen. |
| `-read_intervals INTERVALLE` | Bestimmte Lesebereiche anfordern. | Suchgenauigkeit hängt auch von Eingabe und Format ab. |
| `-show_error` | Fehlerinformationen im gewählten Ausgabeformat. | Abschlussstatus zusätzlich prüfen. |

Nicht jedes Feld ist bei jedem Container verfügbar. Zahlen können in JSON als Zeichenketten erscheinen; die Bedeutung des Feldes anhand der Referenz interpretieren.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und Eingabe festlegen

```bash
ffprobe -version
```

Eine eigene bekannte kurze WAV-Datei als `probe.wav` bereitstellen. Keine Netzwerkadresse, Kamera oder Mikrofonquelle für eine reine Dateianalyse verwenden. Der hier ausgeführte Test nutzte synthetische Stille mit 8.000 Hz, einem Kanal und 0,1 Sekunden Dauer.

### Schritt 2: Container und Streams ansehen

```bash
ffprobe -v error -show_format -show_streams -of json "probe.wav"
```

Die Ausgabe enthält getrennte Bereiche. Bei der Testdatei wurden WAV und PCM erwartet. Die gleichen Werte sind bei beliebigen anderen Originalen nicht vorgegeben.

### Schritt 3: Nur relevante Audiofelder auswählen

```bash
ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,sample_rate,channels,duration -of json "probe.wav"
```

Die Auswahl begrenzt den Bericht auf die erste Audiospur und vier Felder. `sample_rate` beschreibt Samples pro Sekunde, `channels` die Kanalzahl. `duration` kann formatabhängig fehlen oder anders abgeleitet sein.

### Schritt 4: Bericht kontrolliert speichern

```bash
ffprobe -v error -show_format -show_streams -of json "probe.wav" > "medienbericht.json"
```

Nur einen freien kontrollierten Ausgabenamen wählen. Die Shell kann eine vorhandene Datei schon öffnen und leeren, bevor die Analyse erfolgreich ist. Der Bericht kann private Metadaten enthalten.

### Schritt 5: Ergebnis fachlich beurteilen

Prüfen, ob die erwarteten Streams vorhanden sind und die Angaben zum bekannten Original passen. Bei automatisierter Verarbeitung JSON wirklich parsen und Fehlerstatus, fehlende Felder sowie leere Streamlisten berücksichtigen. Ein lesbarer Bericht bedeutet keine geprüfte hörbare oder sichtbare Qualität.

## 6. Typische Anwendungsfälle

**Konvertierung vorbereiten:** Vor einem ffmpeg-Auftrag herausfinden, welche Ton-, Video- und Untertitelspuren tatsächlich existieren.

**Ergebnis kontrollieren:** Nach einer Konvertierung Codec, Rate, Kanalzahl und erwartete Streams prüfen. Diese Eigenschaftskontrolle ergänzt einen passenden Inhaltstest, ersetzt ihn aber nicht.

**Formatprobleme eingrenzen:** Container und Codec trennen, wenn eine Anwendung eine Datei nicht öffnen kann. Eine passende Endung allein ist kein Kompatibilitätsnachweis.

**Technischen Bericht erzeugen:** Mit gezielten Feldern eine übersichtliche maschinenlesbare Grundlage schaffen. Umfangreiche Paketlisten nur bei konkretem Diagnosebedarf anfordern.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Metadaten können vertraulich sein

Titel, Kommentare, Aufnahmezeiten oder Ortsangaben können im Bericht auftauchen. Vor dem Teilen die konkret ausgegebenen Informationen prüfen. Strukturierte JSON-Ausgabe macht Inhalte nicht anonym.

### Eingabe ist nicht zwangsläufig lokal

Das Programm akzeptiert Medien-URLs und je nach Build weitere Protokolle. Schon eine Analyse kann dadurch Verbindungen auslösen. Für diesen Dokumentationsablauf wurden ausschließlich eigene lokale Dateien verwendet.

### Aufwand und Grenzen der Analyse

Frame- oder Paketausgabe kann viel Laufzeit und Speicher für Berichte beanspruchen. Eine kleine komprimierte Datei kann komplexen Inhalt enthalten. Ein lesender Aufruf ist keine vollständige Isolation des Medienparsers.

### Zeit- und Qualitätsangaben richtig verstehen

Containerlaufzeit, Streamlaufzeit und Anzahl tatsächlich decodierbarer Frames müssen nicht identisch sein. Eine plausible Bitrate beweist keine gute Qualität. Für konkrete fachliche Fragen geeignete Messung und reale Wiedergabe getrennt planen.

### Berichte sind keine ausführbaren Befehle

Metadaten und Namen stammen aus Eingaben. Sie nicht ungeprüft in Shell-Kommandos einbauen. Ein JSON-Parser ersetzt keine sichere Behandlung späterer Dateipfade oder Optionen.

**Root-Rechte sind für die gezeigte lokale Analyse nicht erforderlich.** Ein Dokumentationsbeispiel gibt keine Gerätediagnose oder Aufnahme frei.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Streams in Auswahl | Gewählter Streamtyp oder Index fehlt. | Zunächst vollständige Streamliste lesen. |
| Feld fehlt | Format enthält keine entsprechende Angabe. | Fehlenden Wert ausdrücklich behandeln. |
| Unlesbare Eingabe | Falscher Container, Beschädigung oder fehlende Unterstützung. | Genaue Meldung und lokalen Build prüfen. |
| Bericht riesig | Paket- oder Frameausgabe aktiviert. | Auf benötigte Abschnitte begrenzen. |
| Angaben wirken widersprüchlich | Container- und Streamebene vermischt. | Felder zur richtigen Ebene zuordnen. |
| Datei nicht gefunden | Pfad verwechselt. | Kontrollierten lokalen Pfad prüfen. |

Ein fehlgeschlagener Eingabezugriff wird nicht durch einen vorhandenen, eventuell leeren Bericht erfolgreich. Abschlussstatus und ausgewählte Inhalte gemeinsam prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Nur eigene lokale Dateien auswählen.
2. Mit Container- und Streamübersicht beginnen.
3. Danach die benötigten Felder gezielt einschränken.
4. Fehlende Felder und mehrere Streams ausdrücklich behandeln.
5. Vor dem Teilen private Metadaten prüfen.
6. Analyseerfolg, Inhaltsqualität und Herkunft getrennt beurteilen.

**Prüfstand:** FFprobe 6.1.1-3ubuntu5 analysierte eine selbst erzeugte stille PCM-WAV-Datei. Codec `pcm_s16le`, 8.000 Hz, ein Kanal, 0,1 Sekunden und WAV-Container wurden geprüft. Die Quelle blieb bytegleich. Eine fehlende Datei lieferte einen Fehlerstatus. Netzwerkquellen, Geräte, Video-, Untertitel-, Paket- und Framezählungen wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ffmpeg` | Konvertiert, filtert und schreibt Medien. |
| `mediainfo` | Andere technische Informationsansicht. |
| `exiftool` | Liest und verändert Metadaten mit anderen Schwerpunkten. |
| `identify` | Bildbezogene Eigenschaften mit ImageMagick. |

Ausgangseintrag: Datensatz 35 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
