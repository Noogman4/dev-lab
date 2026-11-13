---
id: "aplay"
name: "aplay"
command: "aplay"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "aplay"]
status: "Ausgearbeitet; Quellen und lokale Hilfe geprüft; Audiowiedergabe nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 30
reviewed_at: "2026-11-13"
locally_checked_version: "ALSA utils 1.2.9; Hilfe und Version geprüft"
---

# aplay – Audiodateien über ALSA wiedergeben

## 1. Kurzbeschreibung

`aplay` spielt unterstützte Audiodateien über die ALSA-Schnittstelle unter Linux ab. Es ist ein einfacher PCM-orientierter Player und kein allgemeiner Ersatz für jeden Multimedia-Decoder.

**Für die normale Wiedergabe im eigenen Benutzerkonto sind keine Root-Rechte nötig.** Der Aufruf kann hörbaren Ton erzeugen und ein Audiogerät öffnen. Diese Dokumentation führt keine Wiedergabe auf dem Rechner aus.

## 2. Was macht der Befehl?

Das Programm liest Audiodaten aus einer Datei oder von stdin und übergibt sie an ein ausgewähltes ALSA-PCM. Ein PCM kann ein Hardwaregerät, ein Plugin oder ein Weg über den laufenden Soundserver sein. Der Name `default` steht deshalb nicht zwingend für eine bestimmte physische Buchse.

Bei geeigneten Headerformaten lassen sich Parameter aus der Datei lesen. Rohe Audiodaten besitzen dagegen keine ausreichende Selbstbeschreibung; Sampleformat, Rate und Kanalzahl müssen zum Inhalt passen. Ein falsch gewählter Satz kann Rauschen, falsche Geschwindigkeit oder Kanalprobleme verursachen.

Quellen: [Distributions-Manpage zu aplay](https://manpages.debian.org/trixie/alsa-utils/aplay.1.en.html) und die lokal geprüfte Hilfe der ALSA utils 1.2.9. Unterstützung von Sampleformaten und Geräten ist hardware- und konfigurationsabhängig.

## 3. Syntax

```text
aplay [OPTIONEN] [DATEI ...]
```

```bash
aplay -d 5 "eigene-probe.wav"
aplay -D default -d 5 "eigene-probe.wav"
```

Diese Aufrufe würden tatsächlich Audio wiedergeben. Die Datei muss existieren und passend codiert sein. Die Dauergrenze begrenzt die Wiedergabe, stellt aber keinen Lautstärkeschutz her.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Lokale Hilfe. | Öffnet für sich keine normale Audiodatei zur Wiedergabe. |
| `--version` | Versionsangabe. | ALSA-utils-Stand prüfen. |
| `-l` | Hardware-Wiedergabegeräte auflisten. | Anders als die Liste logischer PCMs. |
| `-L` | PCM-Namen auflisten. | Kann Plugins und Soundserverwege enthalten. |
| `-D NAME` | PCM auswählen. | Direkte Hardwarewahl kann den Soundserver umgehen. |
| `-t wav` | Eingabeformat ausdrücklich angeben. | Dateiendung allein konvertiert keine Daten. |
| `-f S16_LE` | Sampleformat angeben. | Bei raw entscheidend; kein allgemeines MP3-Decoding. |
| `-r 48000` | Abtastrate setzen. | Bei raw muss sie zur Quelle passen. |
| `-c 2` | Kanalzahl setzen. | Beispielsweise Stereo. |
| `-d SEKUNDEN` | Wiedergabedauer begrenzen. | `0` bedeutet keine entsprechende zeitliche Grenze. |
| `-N` | Nicht blockierend öffnen. | Bei belegtem Gerät kann unmittelbar ein Fehler folgen. |
| `-v` | PCM-Konfiguration anzeigen. | Diagnose statt Lautstärkeregelung. |
| `-q` | Meldungen reduzieren. | **Schaltet den Ton nicht stumm.** |

Pufferparameter nur mit konkretem Diagnoseziel verändern. Eine minimale Pufferzeit ist nicht automatisch störungsfreier.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Hilfe und Version lesen

```bash
aplay --version
aplay --help
```

Damit zunächst die vorhandenen Optionen prüfen. Der tatsächliche Ausgabepfad wird dadurch noch nicht nachgewiesen.

### Schritt 2: Eigene kurze WAV-Datei auswählen

Für die Übung eine bekannte eigene PCM-WAV-Datei unter dem Namen `eigene-probe.wav` bereitstellen. Keine unbekannte Binärdatei in `.wav` umbenennen. Die Lautstärke am vorgesehenen Ausgang vorher niedrig und bewusst einstellen.

### Schritt 3: Geräteauswahl nachvollziehen

```bash
aplay -L
```

Die Ausgabe zeigt logische PCM-Namen. Falls mehrere Audioausgänge existieren, bedeutet `default` nicht zwangsläufig den gerade erwarteten Lautsprecher. Eine solche lokale Geräteabfrage wurde im Rahmen dieser Dokumentation nicht durchgeführt.

### Schritt 4: Bewusster Wiedergabeversuch

```bash
aplay -D default -d 5 "eigene-probe.wav"
```

Dieser optionale praktische Schritt erzeugt Ton. Mit Strg+C abbrechen, falls der Ausgang oder Inhalt nicht passt. Erfolgreiches Dateiöffnen und tatsächlich hörbare Ausgabe sind getrennt zu beurteilen.

### Schritt 5: Beobachtung einordnen

Auf Meldungen zu Rate, Format, Gerät und Unterläufen achten. Wenn kein Ton zu hören ist, zunächst den gewählten Ausgang, Stummschaltung und Soundserver-Routing prüfen, statt den Aufruf als root zu wiederholen.

## 6. Typische Anwendungsfälle

**Bekannte PCM-Datei wiedergeben:** Für eine kurze lokale Funktionskontrolle geeignet, wenn Lautstärke und Ausgang bewusst gewählt wurden.

**ALSA-Pfad eingrenzen:** Logische PCM-Auswahl und tatsächliches Soundserver-Routing unterscheiden. Ein Direktgerät ist eine andere Prüfstufe als der normale Desktop-Ausgang.

**Rohdaten gezielt abspielen:** Nur mit bekanntem Sampleformat, Rate und Kanalzahl. Unbekannte Rohdaten sind kein sinnvoller Einstiegstest.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Lautstärke und falsche Rohparameter

Eine kurze Dauer verhindert keine unerwartet laute Ausgabe. Falsche Sampleinterpretation kann unangenehmes Rauschen erzeugen. Keine beliebigen Daten als raw-Audio testen und Lautstärke nicht durch `-q` vermeintlich absichern.

### Gerätekonflikte

Ein direkt geöffnetes Hardwaregerät kann mit laufenden Anwendungen konkurrieren. Plugins und Soundserver lösen nicht jeden Konflikt gleich. Eine Meldung „belegt“ ist kein Anlass, wahllos Dienste zu stoppen.

### Grenzen der Formatunterstützung

MP3, AAC oder komplexe Container benötigen passende Decoder. Aplay versteht nicht automatisch alles, was eine Audiodateiendung trägt. Für Konvertierung eine getrennte, gezielte Verarbeitung verwenden.

### Kein vollständiger Desktop-Audiotest

Ein erfolgreicher Prozess bestätigt nicht jede Lautsprecherroute, Bluetooth-Verbindung oder Lautstärkestufe. Die reale hörbare Ausgabe muss bewusst geprüft werden.

**Root-Rechte sind für eigene normale Wiedergabe nicht erforderlich.** Berechtigungsprobleme anhand von Sitzung, Gerät und Konfiguration untersuchen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Ton | Falscher Ausgang, Stummschaltung oder Routing. | Desktop-Audioweg und PCM-Zuordnung prüfen. |
| Gerät belegt | Direkter Zugriff konkurriert mit anderem Prozess. | Normalen Soundserverweg und legitimen Nutzer klären. |
| Format nicht unterstützt | Datei oder Hardwareparameter passen nicht. | Tatsächlichen Codec und PCM-Fähigkeiten prüfen. |
| Falsche Geschwindigkeit | Raw-Rate beziehungsweise Format falsch. | Erzeugungsparameter ermitteln. |
| Unterlauf | Daten oder Zeitplanung reichen nicht rechtzeitig. | Last und Puffer gezielt diagnostizieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Bekannte kurze PCM-WAV-Datei statt unbekannter Rohdaten verwenden.
2. Lautstärke niedrig und Ausgang bewusst wählen.
3. Wiedergabe zeitlich begrenzen.
4. Erst normalen Desktop-Pfad prüfen, dann gegebenenfalls Direktgeräte.
5. Meldungen sichtbar lassen und `-q` nicht als Stummoption behandeln.

**Prüfstand:** Lokale Hilfe und Version der ALSA utils 1.2.9 wurden gelesen. Es wurde kein Gerät aufgelistet, geöffnet oder zur Tonwiedergabe verwendet. Lautstärke, Routing, tatsächliche Formatwiedergabe und hörbarer Erfolg bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `arecord` | ALSA-Aufnahme statt Wiedergabe. |
| `pactl`, `wpctl` | Soundserver- beziehungsweise Sitzungs-Audioverwaltung. |
| `ffprobe` | Untersucht Medienstreams ohne normale Wiedergabe. |
| `ffmpeg` | Kontrollierte Formatkonvertierung. |
| `play` | SoX-basierte Wiedergabe mit anderen Optionen. |

Ausgangseintrag: Datensatz 30 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
