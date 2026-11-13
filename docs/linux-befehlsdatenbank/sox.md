---
id: "sox"
name: "sox"
command: "sox"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "sox"]
status: "Ausgearbeitet; Quellen geprüft; Dateiverarbeitung nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 44
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; SoX-Handbuch geprüft"
---

# sox – Audiodateien umwandeln und Effektketten nachvollziehbar aufbauen

## 1. Kurzbeschreibung

`sox` liest Audiodaten, wendet bei Bedarf Effekte an und schreibt ein Ergebnis. Es kann Formate konvertieren, Kanäle ändern, Ausschnitte erzeugen und Audiodaten kombinieren.

**Für eigene Dateien sind keine Root-Rechte nötig.** Der normale Dateiaufruf schreibt eine Ausgabe und kann vorhandene Ziele überschreiben. Die Aufrufnamen `play` und `rec` verwenden dagegen gewöhnlich Audiogeräte als Ausgang beziehungsweise Eingang.

## 2. Was macht der Befehl?

Der Ablauf besteht aus Eingaben, ihrer gegebenenfalls gewählten Zusammenführung, einer Effektkette und der Ausgabe. Auf der Kommandozeile steht der Ausgabepfad vor den Effekten, obwohl die Effekte logisch vor dem Schreiben wirken.

Dateioptionen vor einer Eingabe beschreiben diese Eingabe. Dateioptionen vor der Ausgabe beschreiben das Ausgabeformat. Effekte nach dem Ausgabepfad bearbeiten den Datenstrom in ihrer Reihenfolge. Diese Unterscheidung verhindert viele scheinbar plausible, aber falsche Aufrufe.

Grundlage ist das [SoX-Distributionshandbuch](https://manpages.debian.org/trixie/sox/sox.1.en.html), einschließlich Dateisyntax, globaler Optionen und Effekterklärungen. Welche Formate und Audiobackends verfügbar sind, hängt vom Build ab. SoX ist hier nicht installiert.

## 3. Syntax

```text
sox [GLOBALE_OPTIONEN] [EINGABEOPTIONEN] EINGABE [AUSGABEOPTIONEN] AUSGABE [EFFEKT ...]
```

```bash
sox --no-clobber "probe.wav" -b 16 "mono-16k.wav" channels 1 rate 16000
```

Die Eingabe ist eine bekannte eigene WAV-Datei. `-b 16` steht vor der Ausgabe und wählt deren Samplebreite. Danach folgen die Kanalumwandlung und Abtastratenumwandlung als Effekte. Der neue Ausgabename hält Quelle und Ergebnis auseinander.

## 4. Wichtige Optionen

| Option oder Effekt | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--version`, `--help` | Version und Hilfe. | Konkreten Build prüfen. |
| `--help-effect NAME` | Hilfe für einen Effekt. | Parameter nicht aus fremder Werkzeugsyntax übernehmen. |
| `--help-format NAME` | Formatunterstützung erklären. | Codec- und Bibliotheksabhängigkeiten beachten. |
| `--no-clobber` | Vor Überschreiben nachfragen. | Kein allgemeines garantiertes „niemals schreiben“-Flag. |
| `--clobber` | Ohne Rückfrage überschreiben. | Laut Handbuch Standard; neue Ziele wählen. |
| `-b BITS` | Samplebreite des zugehörigen Dateipfads. | Position bestimmt Ein- oder Ausgabebedeutung. |
| `-r RATE`, `-c KANÄLE` | Rate und Kanalzahl beschreiben beziehungsweise vorgeben. | Bei Rohdaten tatsächliche Eigenschaften kennen. |
| `-v FAKTOR` | Eingabesignal skalieren. | Nicht mit Diagnoseoption `-V` verwechseln. |
| `-m` | Eingaben mischen. | Pegelsumme und Clipping beachten. |
| `-M` | Eingaben zu Kanälen zusammenführen. | Andere Wirkung als zeitliches Mischen. |
| `-n` | SoX-Nullquelle beziehungsweise Nullausgabe. | Als Quelle ohne Endeffekt potenziell unbegrenzt. |
| `trim START DAUER` | Ausschnitt wählen. | Endliche Übungslänge bewusst setzen. |
| `channels ANZAHL` | Kanalzahl umwandeln. | Kann Inhalte zusammenführen beziehungsweise verändern. |
| `rate RATE` | Abtastrate umrechnen. | Nicht bloß falsche Eingangsdaten umdeklarieren. |
| `stat` | Signalstatistik ausgeben. | Bericht gewöhnlich auf stderr statt normalem Audiodatenstrom. |

Normalisierung, Gain und Clipping-Schutz haben eigene Semantik. Eine höhere Lautstärke ist nicht automatisch bessere Qualität. `SOX_OPTS` kann globale Vorgaben ergänzen und sollte bei überraschendem Verhalten betrachtet werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Werkzeug und Effektinformationen prüfen

```bash
sox --version
sox --help-effect channels
sox --help-effect rate
```

Fehlt das Programm, ist dieser Ablauf nicht praktisch bestätigt. Für die Dokumentation wurde keine Installation vorgenommen.

### Schritt 2: Eigenen Arbeitsordner wählen

```bash
uebung="$(mktemp -d -t netmon-sox-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren. Eine kurze bekannte eigene WAV-Datei als `probe.wav` bereitstellen.

### Schritt 3: In neue Ausgabe umwandeln

```bash
sox --no-clobber "probe.wav" -b 16 "mono-16k.wav" channels 1 rate 16000
```

Die Ausgabe soll einen Kanal, 16.000 Samples pro Sekunde und 16-Bit-Samples besitzen. Die Kanalumwandlung kann Unterschiede zwischen Stereokanälen zusammenführen und ist deshalb keine byteidentische Kopie des Originals.

### Schritt 4: Eigenschaften getrennt lesen

```bash
sox --i "mono-16k.wav"
```

`--i` als erster Parameter wählt die SoXI-Informationsansicht. Erwartete Rate, Kanalzahl und Samplebreite prüfen. Eine vorhandene Datei allein beweist keinen vollständigen Konvertierungserfolg.

### Schritt 5: Fachliches Ergebnis beurteilen

Das Original behalten. Für Klangqualität, Pegel oder Spracherkennbarkeit einen eigenen bewusst gestarteten Hör- beziehungsweise Messtest planen. Die aktuelle Anleitung führt keine Wiedergabe aus und behauptet keinen getesteten Klanggewinn.

## 6. Typische Anwendungsfälle

**Sprachdatei vorbereiten:** Eine vom Empfänger benötigte Rate und Kanalzahl gezielt herstellen. Vorher dessen wirkliche Formatvorgaben prüfen.

**Ausschnitt erzeugen:** Mit `trim` nur einen bekannten Bereich in eine neue Datei schreiben. Originalerhalt und Ausgabenamen ausdrücklich wählen.

**Dateien kombinieren:** Zeitliche Verkettung, Mischen und Kanalkombination sind verschiedene Aufgaben. Erst die gewünschte Wirkung benennen, dann das passende Verfahren auswählen.

**Signal untersuchen:** Eine Statistik auf eine Nullausgabe anwenden, wenn kein neues Audiosignal gespeichert werden soll. Diagnoseausgabe und Nutzdatenausgabe auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Vorhandene Ziele können überschrieben werden

Der normale Standard fragt nicht zwingend nach. `--no-clobber` fordert eine Nachfrage, ersetzt aber weder einen freien Ausgabepfad noch eine Sicherung. Bei unbeaufsichtigten Abläufen das konkrete Konfliktverhalten gesondert testen.

### Qualitäts- und Pegeländerungen

Weniger Kanäle oder andere Samplebreite können Informationen verändern beziehungsweise reduzieren. Mischen und Verstärken können übersteuern. Wiederholte verlustbehaftete Neukodierung kann zusätzliche Verluste erzeugen.

### Rohparameter und Effektposition

Falsch deklarierte Rohdaten können falsche Geschwindigkeit oder Rauschen liefern. Optionen vor dem falschen Dateipfad können eine andere Datei betreffen als gedacht. Ein ähnlich benannter FFmpeg- oder ALSA-Schalter ist kein Ersatz für SoX-Syntax.

### Geräte und unbegrenzte Quellen

`-d`, `play` und `rec` können reale Audiogeräte verwenden. Eine Nullquelle `-n` kann ohne geeignete endliche Effektbegrenzung unendlich Daten liefern. Diese Möglichkeiten sind keine reinen Dateimetadatenabfragen.

### Ressourcen und Umgebung

Lange Quellen, mehrere Eingaben und aufwendige Effekte brauchen Zeit, RAM und Ausgabeplatz. Umgebungsvorgaben können zusätzliche Optionen aktivieren. Für erste Versuche kleine bekannte Eingaben und eine überschaubare Effektkette wählen.

**Root-Rechte sind für die eigenen Dateipfade unnötig.** Audioaufnahme und Systemkonfiguration sind nicht Bestandteil des Dokumentationstests.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Format nicht unterstützt | Build besitzt keinen passenden Handler. | Lokale Hilfe zum Format prüfen. |
| Ausgabe unerwartet | Dateioption oder Effekt falsch positioniert. | Eingabe, Ausgabe und Effekte getrennt lesen. |
| Clippingwarnung | Pegel zu hoch beziehungsweise Signale summiert. | Gain und Mischverfahren bewusst prüfen. |
| Datei wird ersetzt | Normaler Clobber-Standard oder zugestimmte Nachfrage. | Neues Ziel und unabhängige Originalkopie wählen. |
| Verarbeitung endet nicht | Unbegrenzte Quelle ohne endlichen Effekt. | Bewusst abbrechen und Länge begrenzen. |
| Falscher Klang | Kanal-/Ratenumwandlung oder Rohparameter passen nicht. | Tatsächliche Quelle und gewünschtes Ziel prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Eigene kleine Datei und neuen Zielpfad verwenden.
2. `--no-clobber` als Nachfrage verstehen, nicht als universelles Schreibverbot.
3. Nur einen klar begründeten Effekt nach dem anderen ergänzen.
4. Ausgabeparameter mit SoXI oder einem anderen Analysewerkzeug prüfen.
5. Original bis zur passenden Inhaltskontrolle behalten.
6. Geräte- und Nullquellen nicht ohne eigene Zweck- und Längenprüfung einsetzen.

**Prüfstand:** Das offizielle Distributionshandbuch wurde geprüft. SoX ist hier nicht installiert. Dateikonvertierung, Effektkette, Nachfrageverhalten, Signalstatistik und Klangqualität wurden nicht praktisch getestet. Es wurde weder eine Audiodatei über SoX verändert noch ein Audiogerät verwendet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `soxi`, `sox --i` | Audioeigenschaften lesen. |
| `play`, `rec` | SoX-Aufrufnamen mit Geräteausgabe beziehungsweise -eingabe. |
| `ffmpeg` | Andere Medienkonvertierung mit eigener Syntax. |
| `ffprobe`, `mediainfo` | Technische Analyse der Ergebnisse. |

Ausgangseintrag: Datensatz 44 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
