---
id: "arecord"
name: "arecord"
command: "arecord"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "arecord"]
status: "Ausgearbeitet; Quellen und lokale Hilfe geprüft; Aufnahme nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 31
reviewed_at: "2026-11-13"
locally_checked_version: "ALSA utils 1.2.9; Hilfe und Version geprüft"
---

# arecord – Audio über ALSA gezielt und zeitlich begrenzt aufnehmen

## 1. Kurzbeschreibung

`arecord` nimmt Audiodaten über ein ALSA-PCM auf und schreibt sie in eine Datei oder auf stdout. Ein ausgewähltes PCM kann ein Mikrofon, Line-Eingang oder ein anderer konfigurierter Aufnahmeweg sein.

**Für eine normale Aufnahme im eigenen Desktop-Benutzerkonto sind keine Root-Rechte nötig.** Der Aufruf kann ein Mikrofon aktivieren und private Umgebungsgeräusche speichern. Hier wird keine Aufnahme ausgeführt.

## 2. Was macht der Befehl?

Das Programm öffnet die Aufnahmequelle und verarbeitet Samples mit einer bestimmten Rate, Kanalzahl und Sampledarstellung. Mit einem geeigneten Container wie WAV werden diese Parameter zusammen mit dem Inhalt gespeichert. Raw-Daten besitzen diese Selbstbeschreibung nicht.

Der Name `default` ist ein logischer ALSA-Pfad. Je nach System kann er durch einen Soundserver geführt werden und muss nicht dauerhaft auf dasselbe physische Mikrofon zeigen. Eine vorhandene Soundkarte besitzt außerdem nicht zwingend einen passenden aktiven Aufnahmeweg.

Grundlagen: [Distributions-Manpage zu arecord](https://manpages.debian.org/trixie/alsa-utils/arecord.1.en.html) und die lokale gemeinsame Hilfe von arecord/aplay aus ALSA utils 1.2.9. Erforderliche Geräteparameter bleiben von Hardware und Konfiguration abhängig.

## 3. Syntax

```text
arecord [OPTIONEN] [AUSGABEDATEI]
```

```bash
arecord -D default -d 5 -t wav -f S16_LE -r 48000 -c 1 "aufnahme.wav"
```

Dieser dokumentierte Beispielaufruf würde fünf Sekunden Audio aufnehmen. Ohne passende Dauerbegrenzung kann eine Aufnahme weiterlaufen und Speicher belegen. `-d 0` bedeutet keine solche zeitliche Grenze.

Ohne Dateinamen kann Audio auf stdout geschrieben werden. Binäre Audiodaten nicht direkt auf ein Terminal ausgeben.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Hilfe anzeigen. | Parameter vor einer Aufnahme prüfen. |
| `--version` | Versionsstand anzeigen. | Implementierung dokumentieren. |
| `-l` | Aufnahme-Hardwaregeräte auflisten. | Nicht mit Wiedergabegeräten gleichsetzen. |
| `-L` | Definierte PCMs anzeigen. | Kann logische und pluginbasierte Wege enthalten. |
| `-D NAME` | Aufnahme-PCM wählen. | Tatsächliche Quelle gesondert prüfen. |
| `-d SEKUNDEN` | Aufnahme zeitlich begrenzen. | Für erste Versuche ausdrücklich setzen. |
| `-t wav` | WAV-Container schreiben. | Für nachvollziehbare PCM-Testdateien geeignet. |
| `-f S16_LE` | 16-Bit-Samples, Little Endian. | Muss vom gewählten Weg unterstützt werden. |
| `-r 48000` | 48.000 Samples pro Sekunde wählen. | Nicht jede Hardware unterstützt jede Rate direkt. |
| `-c 1` | Einen Kanal aufnehmen. | Stereo ist nicht für jede Quelle sinnvoll. |
| `-V mono` | Monopegelanzeige. | Zeigt Pegel, bestätigt aber nicht die richtige Quelle. |
| `-v` | PCM-Einrichtung anzeigen. | Für Diagnose geeignet. |
| `-q` | Meldungen reduzieren. | Beendet oder verhindert keine Aufnahme. |
| `-N` | Nicht blockierend öffnen. | Belegtes Gerät kann direkt abgelehnt werden. |

`-f cd` ist eine Parameterkurzform für 16 Bit, 44,1 kHz und zwei Kanäle. Sie bedeutet keine automatische Auswahl der besten Mikrofoneinstellungen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen klären

```bash
arecord --version
arecord --help
```

Vor einem echten Versuch die gewünschte Aufnahmequelle und die Privatsphäre anwesender Personen klären. Die folgenden Schritte sind eine Anleitung für einen bewusst gestarteten Test, kein hier ausgeführter Aufnahmebericht.

### Schritt 2: Frischen eigenen Zielordner verwenden

```bash
uebung="$(mktemp -d -t netmon-arecord-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Ein frischer Ordner vermeidet das Überschreiben einer vorhandenen wichtigen Aufnahme.

### Schritt 3: Quelle prüfen

```bash
arecord -L
```

Die logischen PCM-Namen geben mögliche Wege an. Falls `default` zum Soundserver führt, dessen tatsächlich gewählte Eingangsquelle in der Desktop-Audioverwaltung prüfen. Diese Geräteabfrage wurde hier nicht ausgeführt.

### Schritt 4: Optional fünf Sekunden aufnehmen

```bash
arecord -D default -d 5 -t wav -f S16_LE -r 48000 -c 1 "aufnahme.wav"
```

Dieser Schritt aktiviert den gewählten Aufnahmeweg. Mit Strg+C vorzeitig abbrechen, wenn die Quelle unerwartet ist. Die Datei kann dabei bereits Ton enthalten. Keine pauschale Endlosschleife und keine echte Daueraufnahme als Test verwenden.

### Schritt 5: Ergebnis getrennt beurteilen

Eine angelegte WAV-Datei kann Stille, die falsche Quelle oder einen übersteuerten Inhalt enthalten. Formatdaten lassen sich mit einem geeigneten Analysewerkzeug lesen. Eine bewusst gestartete leise Wiedergabe wäre ein weiterer eigener Schritt; sie wird hier nicht automatisch ausgeführt.

## 6. Typische Anwendungsfälle

**Kurze eigene Sprachprobe:** Mit klarem Aufnahmezweck, bekannter Quelle und begrenzter Dauer.

**Mikrofonweg eingrenzen:** Geräteauswahl, Soundserver-Routing und Pegel getrennt betrachten. Eine vorhandene Karte beweist keinen funktionierenden Eingang.

**PCM-Eingabe für Verarbeitung erzeugen:** Container, Sampleformat und Zielanwendung aufeinander abstimmen. Ein größerer Zahlenwert ist nicht automatisch bessere praktische Aufnahmequalität.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Private Toninhalte

Eine Aufnahme kann Gespräche und Umgebungsgeräusche speichern. Vor Beginn bewusst entscheiden, was aufgenommen werden soll und wer Zugang zur Datei haben darf. Die Dateirechte ergeben sich unter anderem aus dem Zielordner und der eigenen umask; sie sind nicht allein durch die Endung geschützt.

### Vorhandene Ziele und unbegrenzte Dauer

Ein bereits belegter Ausgabeweg kann überschrieben werden. Eine fehlende Dauergrenze kann ungewollt weiter aufnehmen und Speicher belegen. Neue Dateinamen und eine kurze ausdrückliche Dauer wählen.

### Falsche Quelle und Umwandlung

Ein Loopback- oder Monitorweg kann andere Inhalte als das erwartete Mikrofon liefern. Plugins können Rate, Kanalzahl oder Sampleformat umwandeln. Aus einer erfolgreichen Parameterverhandlung folgt keine Gewissheit über den realen Inhalt.

### Gerätezugriff und Fehlersuche

Direkter Hardwarezugriff kann mit Soundservern konkurrieren. Nicht wahllos Berechtigungen ändern, Dienste stoppen oder den Prozess als root starten. Erst die legitime Sitzung, den gewünschten Weg und die konkrete Meldung prüfen.

**Root-Rechte sind für die normale eigene Desktop-Aufnahme nicht erforderlich.** Der Dokumentationsauftrag erteilt keine Freigabe zur tatsächlichen Tonaufnahme.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Aufnahme still | Falsche Quelle, stummer Eingang oder Pegel zu niedrig. | Quelle und Aufnahmepegel bewusst prüfen. |
| Gerät belegt | Direkter ALSA-Weg konkurriert mit anderer Nutzung. | Gewünschten Soundserverweg klären. |
| Format abgelehnt | Hardware beziehungsweise PCM unterstützt Parameter nicht. | Fähigkeiten und Pluginweg prüfen. |
| Verzerrter Ton | Übersteuerung oder falsche Parametrierung. | Pegel und Quellformat prüfen. |
| Aufnahme läuft weiter | Dauer fehlt oder ist null. | Bewusst abbrechen und begrenzten Test wählen. |
| Datei existiert, aber unbrauchbar | Fehler oder unerwarteter Inhalt. | Meldungen, Format und tatsächlichen Inhalt getrennt prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Keine Aufnahme ohne bewusst gewählten Zweck und Quelle starten.
2. Mit fünf Sekunden und einer neuen WAV-Datei beginnen.
3. Rohformate erst bei bekannten Parametern verwenden.
4. Dateirechte und Aufbewahrung privater Inhalte beachten.
5. Bei Fehlern nicht reflexartig erhöhte Rechte einsetzen.
6. Dateierzeugung und brauchbaren Audioinhalt getrennt beurteilen.

**Prüfstand:** Lokale Hilfe und Versionsstand ALSA utils 1.2.9 wurden geprüft. Kein Mikrofon, Aufnahme-PCM oder sonstiges Audiogerät wurde geöffnet oder aufgelistet. Aufnahmequalität, Dateierzeugung durch arecord, reale Pegel und Wiedergabe bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `aplay` | ALSA-Wiedergabe statt Aufnahme. |
| `pactl`, `wpctl` | Sitzungs-Audioquellen und Routing verwalten. |
| `ffprobe` | Aufgezeichnete Datei untersuchen. |
| `ffmpeg`, `sox` | Audiodaten konvertieren beziehungsweise verarbeiten. |

Ausgangseintrag: Datensatz 31 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
