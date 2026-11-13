---
id: "ffmpeg"
name: "ffmpeg"
command: "ffmpeg"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "ffmpeg"]
status: "Ausgearbeitet; lokale Dateikonvertierung mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 34
reviewed_at: "2026-11-13"
locally_checked_version: "FFmpeg 6.1.1-3ubuntu5"
---

# ffmpeg – Medien gezielt konvertieren und Streams bewusst auswählen

## 1. Kurzbeschreibung

`ffmpeg` liest Medien, wählt Audio-, Video- und andere Streams aus und schreibt sie in neue Ausgaben. Es kann Daten neu kodieren, filtern oder ohne Neukodierung in einen anderen Container übernehmen.

**Für eigene lokale Dateien sind keine Root-Rechte nötig.** Der Befehl schreibt Ausgaben und unterstützt außerdem Netzwerk- und Geräteeingaben. Die Beispiele hier verwenden ausschließlich eigene lokale Testdateien; es werden weder Aufnahmen noch Netzwerkzugriffe gestartet.

## 2. Was macht der Befehl?

Ein Container wie WAV, MP4 oder Matroska hält Streams und Metadaten zusammen. Ein Codec beschreibt die Kodierung eines Streams, etwa PCM, FLAC oder H.264. Eine andere Dateiendung allein wandelt weder Container noch Codec um.

Beim Transkodieren werden Daten decodiert und neu kodiert. Bei Streamcopy mit `-c copy` entfällt diese Neukodierung; der Zielcontainer muss die gewählten Streams trotzdem unterstützen. Filter benötigen gewöhnlich decodierte Daten und passen deshalb nicht beliebig zu Streamcopy.

Mehrere Eingaben und Ausgaben sind möglich. Optionspositionen bestimmen, auf welche Datei sie wirken. Ohne bewusste Streamauswahl kann eine automatische Auswahl andere Tonspuren oder Untertitel übernehmen beziehungsweise auslassen als erwartet.

Quellen: [offizielle FFmpeg-CLI-Dokumentation](https://ffmpeg.org/ffmpeg.html), [Gesamtreferenz](https://ffmpeg.org/ffmpeg-all.html) und lokale Hilfe von FFmpeg 6.1.1-3ubuntu5. Die Website kann neuere Funktionen beschreiben; lokale Encoder und Optionen separat prüfen.

## 3. Syntax

```text
ffmpeg [GLOBALE_OPTIONEN] [EINGABEOPTIONEN] -i EINGABE [AUSGABEOPTIONEN] AUSGABE
```

```bash
ffmpeg -hide_banner -nostdin -n -i "probe.wav" -map 0:a:0 -c:a flac "probe.flac"
```

`-i` kennzeichnet die Eingabe. Der erste Eingang hat Index `0`. `-map 0:a:0` wählt seinen ersten Audiostream. `-c:a flac` setzt dessen Ausgabecodec. Der abschließende Pfad ist das Schreibziel.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-i DATEI` | Eingabe öffnen. | Kann auch eine URL oder ein Gerät sein; Beispiele bleiben lokal. |
| `-n` | Vorhandene Ausgaben nicht überschreiben. | Für erste Versuche sinnvoll; tatsächliches Ergebnis mitprüfen. |
| `-y` | Ausgaben ohne Rückfrage überschreiben. | Kann vorhandene Daten ersetzen. |
| `-nostdin` | Interaktive Standardeingabe deaktivieren. | Für automatisierte lokale Dateikonvertierung hilfreich. |
| `-map 0:a:0` | Ersten Audiostream des ersten Eingangs wählen. | Bewusste Auswahl statt pauschal alle Streams. |
| `-c:a CODEC`, `-c:v CODEC` | Audio- beziehungsweise Videocodec wählen. | Encoder muss im Build vorhanden sein. |
| `-c copy` | Gewählte Streams ohne Neukodierung übernehmen. | Keine Garantie für jeden Zielcontainer. |
| `-an`, `-vn` | Audio beziehungsweise Video ausschließen. | Optionsposition und konkrete Datei beachten. |
| `-t DAUER` | Dauer begrenzen. | Je nach Position Ein- oder Ausgabe betreffende Wirkung prüfen. |
| `-ss ZEIT` | Zeitposition ansteuern. | Position vor oder nach `-i` beeinflusst den Ablauf. |
| `-ar RATE`, `-ac KANÄLE` | Audio-Abtastrate beziehungsweise Kanalzahl festlegen. | Kann Daten umrechnen beziehungsweise Kanäle verändern. |
| `-vf FILTER`, `-af FILTER` | Video- beziehungsweise Audiofilter. | Filter können Qualität, Pegel und Ressourcenbedarf verändern. |
| `-hide_banner` | Lange Build-Kopfzeile ausblenden. | Fehler werden dadurch nicht vollständig unterdrückt. |
| `-loglevel error` | Meldungsumfang reduzieren. | Für Diagnose zunächst normale relevante Meldungen behalten. |

Allgemeine Qualitätsregler sind codecspezifisch. Einen beliebigen `-crf`-Wert nicht als universelle Qualitätsoption für jeden Encoder verwenden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Version und eigenen Arbeitsort prüfen

```bash
ffmpeg -version
uebung="$(mktemp -d -t netmon-ffmpeg-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Eigene WAV-Testdatei bereitstellen

Eine bekannte kurze eigene PCM-WAV-Datei unter `probe.wav` in den neuen Arbeitsordner kopieren. Keine fremde Quelle und kein Mikrofonzugriff sind dafür nötig. Beim hier ausgeführten Test wurde eine synthetische stille PCM-Datei mit 8.000 Hz, einem Kanal und 0,1 Sekunden Länge verwendet.

### Schritt 3: Gezielt als FLAC speichern

```bash
ffmpeg -hide_banner -nostdin -n -i "probe.wav" -map 0:a:0 -c:a flac "probe.flac"
```

Der ausgewählte Audiostream wird verlustfrei als FLAC kodiert. Der Container und eventuell zusätzliche Metadaten sind trotzdem nicht byteidentisch mit WAV. Das Original bleibt durch den getrennten Ausgabepfad erhalten.

### Schritt 4: Ausgabeeigenschaften lesen

```bash
ffprobe -v error -show_entries stream=codec_name,sample_rate,channels -of json "probe.flac"
```

Für die beschriebene stille Testdatei wurden FLAC, 8.000 Hz und ein Kanal erwartet. Bei einem anderen eigenen Original gelten dessen passende Parameter.

### Schritt 5: Inhalt und Abschluss getrennt beurteilen

Bei einem wichtigen verlustfreien Ablauf beide Fassungen in dieselbe bekannte PCM-Darstellung zurücklesen und deren Samples vergleichen. Dateigröße oder Dateiendung sind keine solche Inhaltskontrolle. Für verlustbehaftete Codecs ist bytegleiche Rückgewinnung normalerweise kein passendes Ziel.

## 6. Typische Anwendungsfälle

**Formatkonvertierung:** Einen konkreten Codec und passenden Zielcontainer für den Empfänger auswählen.

**Tonspur extrahieren:** Gezielt den gewünschten Audiostream wählen. Sprachspuren und Kommentarspuren nicht nach zufälliger Reihenfolge verwechseln.

**Container wechseln:** Mit Streamcopy arbeiten, wenn die ausgewählten Streams im Zielcontainer zulässig sind. Der Weg vermeidet Neukodierung, nicht sämtliche Metadatenänderungen.

**Eigene Medien kürzen oder filtern:** Zeitposition, Dauer und Filter bewusst festlegen. Bei Schnittgenauigkeit zwischen Neukodierung und Streamcopy unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Überschreiben und unvollständige Ergebnisse

`-y` kann bestehende Ausgaben ohne Nachfrage ersetzen. Ein neuer Zielpfad und `-n` verringern dieses Risiko. Ein Abbruch kann dennoch eine unvollständige neue Datei hinterlassen. Eingabe und Ausgabe nicht auf denselben Pfad setzen.

### Streamverlust und Qualitätsänderung

Automatische Auswahl kann Spuren auslassen. Erneute verlustbehaftete Kodierung kann Qualität verlieren. Auch Kanalumwandlung, Farbraum und Pegelfilter verändern Inhalte. Gewünschte Streams und fachliche Qualitätsziele vorher benennen.

### Quellen können mehr als Dateien sein

URLs, Playlists und Geräte können Netzwerkzugriffe oder Aufnahmen auslösen. Für eine lokale Übung ausschließlich bekannte lokale Dateien verwenden. Eine dokumentierte Konvertierung gibt keine Aufnahme- oder Netzwerkaktion frei.

### Ressourcen und Metadaten

Hohe Auflösung, viele Frames, aufwendige Filter oder hohe Parallelität können RAM, Laufzeit und Speicher belegen. Metadaten können private Angaben enthalten; Konvertierung ist nicht automatisch eine vollständige Bereinigung.

### Lokaler Prüfbefund zum Abschlussstatus

Beim verwendeten Build meldete ein erneuter `-n`-Aufruf für ein schon vorhandenes Ziel dessen Ablehnung, lieferte aber Status `0`. Das Ziel blieb unverändert. Diesen beobachteten Fall nicht zu einer allgemeinen Versionsregel ausweiten. Für belastbare Abläufe zusätzlich Meldungen, tatsächliche Neuerzeugung und erwartete Ausgabeeigenschaften prüfen.

**Root-Rechte sind für die lokale Dateiumwandlung unnötig.** Geräte- und Systemoperationen sind ein anderer Aufgabenumfang.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Encoder nicht gefunden | Build enthält den gewählten Encoder nicht. | Lokale Encoderliste und passende Alternative prüfen. |
| Container lehnt Stream ab | Codec passt nicht zum Ausgabeformat. | Container und Codec gemeinsam auswählen. |
| Falsche Tonspur | Automatische oder falsche manuelle Auswahl. | Streams vorher mit ffprobe lesen. |
| Filter und copy scheitern | Filter benötigt decodierte Daten. | Bewusst neu kodieren oder Filter entfernen. |
| Ziel unverändert | `-n` hat vorhandene Datei geschützt. | Neue Ausgabe wählen und tatsächlichen Lauf prüfen. |
| Datei vorhanden, aber unbrauchbar | Abbruch oder unvollständige Ausgabe. | Eigenschaften und decodierten Inhalt prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Nur eigene lokale kurze Dateien verwenden.
2. Neuen Ausgabepfad und `-n` wählen.
3. Gewünschte Streams vorab mit ffprobe bestimmen.
4. Codec und Container ausdrücklich unterscheiden.
5. Für wichtige Ergebnisse nicht nur auf Dateiexistenz oder Status vertrauen.
6. Originale bis zur passenden Inhaltsprüfung behalten.

**Prüfstand:** FFmpeg 6.1.1-3ubuntu5 konvertierte eine selbst erzeugte stille PCM-WAV-Datei nach FLAC. FFprobe bestätigte Codec, Rate und Kanalzahl. Zurückdecodierte PCM-Samples waren bytegleich. Ein Wiederholungsversuch mit `-n` erhielt das vorhandene Ziel, zeigte aber den beschriebenen Status-0-Sonderfall. Keine Geräte, Netzquellen, realen Aufnahmen, Video-, Untertitel- oder verlustbehafteten Konvertierungen wurden getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ffprobe` | Medienstruktur und Eigenschaften analysieren. |
| `mediainfo` | Andere technische Medienübersicht. |
| `sox` | Audiospezifische Verarbeitung mit anderer Syntax. |
| `aplay`, `arecord` | Tatsächliche Wiedergabe beziehungsweise Aufnahme über ALSA. |

Ausgangseintrag: Datensatz 34 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
