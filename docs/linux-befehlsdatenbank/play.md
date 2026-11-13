---
id: "play"
name: "play"
command: "play"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "play"]
status: "Ausgearbeitet; Quellen geprüft; Wiedergabe nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 42
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; SoX-Distributionshandbuch geprüft"
---

# play – Audiodateien mit SoX wiedergeben und Effekte bewusst wählen

## 1. Kurzbeschreibung

`play` ist die Wiedergabeoberfläche von SoX. Sie liest Audiodaten und verwendet statt einer gewöhnlichen Ausgabedatei den konfigurierten Audioausgang. Optional können SoX-Effekte während der Verarbeitung angewendet werden.

**Für die normale Wiedergabe im eigenen Konto sind keine Root-Rechte nötig.** Der Aufruf erzeugt hörbaren Ton. Hier ist `play` nicht installiert; es wird keine Wiedergabe gestartet.

## 2. Was macht der Befehl?

Die Verarbeitung besteht aus Eingaben, gegebenenfalls ihrer Zusammenführung, einer Effektkette und einem Ausgabeziel. Beim Namen `play` ist dieses Ziel gewöhnlich das Standard-Audiogerät. Das unterscheidet sich vom normalen `sox`-Aufruf, bei dem eine Ausgabedatei ausdrücklich angegeben wird.

Dateiformat und Audio-Backend müssen im konkreten Build unterstützt werden. WAV oder FLAC können selbstbeschreibende Parameter enthalten; Rohdaten benötigen dagegen korrekte Angaben zu Rate, Sampledarstellung und Kanalzahl.

Grundlagen: [SoX-Handbuch der Distribution](https://manpages.debian.org/trixie/sox/play.1.en.html) und dessen [Hauptansicht zu sox](https://manpages.debian.org/trixie/sox/sox.1.en.html). Der gleiche Handbuchtext behandelt mehrere Aufrufnamen; ihre Standard-Ein-/Ausgaben müssen deshalb ausdrücklich unterschieden werden.

## 3. Syntax

```text
play [GLOBALE_OPTIONEN] [EINGABEOPTIONEN] DATEI [EFFEKT [PARAMETER] ...]
```

```bash
play -v 0.2 "eigene-probe.wav" trim 0 5
```

`-v 0.2` skaliert hier die Eingabe mit dem Faktor 0,2. `trim 0 5` wählt ab Beginn höchstens fünf Sekunden. Der Effekt steht nach der Eingabe. Dies ist ein dokumentierter Wiedergabeaufruf, kein hier durchgeführter Tonversuch.

## 4. Wichtige Optionen

| Option oder Effekt | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--version` | SoX-Version zeigen. | Unterstützung anhand des tatsächlichen Builds prüfen. |
| `--help` | Optionen, Formate und Effekthinweise. | Keine pauschale Verfügbarkeit jedes Codecs voraussetzen. |
| `--help-effect NAME` | Hilfe zu einem Effekt. | Parameter lokal nachlesen. |
| `-v FAKTOR` | Eingabelautstärke skalieren. | Vor die betreffende Eingabe setzen; kein absoluter Lautsprecherpegel. |
| `-V` | Diagnoseausgabe steuern. | Großes V ist nicht die kleine Lautstärkeoption. |
| `-q` | Fortschrittsanzeige reduzieren. | Schaltet den Ton nicht stumm. |
| `-t TYP` | Eingabetyp angeben. | Vor der zugehörigen Eingabe; kein Umbenennungsersatz. |
| `-r RATE`, `-c KANÄLE` | Rate beziehungsweise Kanalzahl bei passenden Rohdaten beschreiben. | Falsche Werte können falsch klingenden Ton erzeugen. |
| `trim START DAUER` | Ausschnitt auswählen. | Geeignet für einen begrenzten ersten Versuch. |
| `gain WERT` | Pegel in dB verändern. | Positive Verstärkung kann Clipping erzeugen. |
| `rate RATE` | Abtastrate als Effekt umwandeln. | Nicht einfach dasselbe wie eine Eingabe nur anders zu deklarieren. |

Die Manpage beschreibt zusätzlich zahlreiche Filter und Syntheseeffekte. Solche Effekte verändern hörbare Eigenschaften und gehören nicht ohne konkreten Zweck in einen Einsteiger-Test.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Vorhandenes Werkzeug prüfen

```bash
play --version
play --help
```

Wenn das Programm fehlt, bleibt die Übung eine Anleitung. Hier wurde nichts nachinstalliert.

### Schritt 2: Eigene kurze PCM-Datei wählen

Eine bekannte eigene WAV-Datei als `eigene-probe.wav` bereitstellen. Vor einem echten Versuch den gewünschten Ausgang und eine niedrige Systemlautstärke wählen. Keine unbekannten Rohdaten und keinen unendlichen Syntheseton als ersten Test verwenden.

### Schritt 3: Begrenzte Wiedergabe starten

```bash
play -v 0.2 "eigene-probe.wav" trim 0 5
```

Dieser optionale Schritt erzeugt Ton. Der Faktor senkt das digitale Eingabesignal, garantiert aber keine bestimmte Lautstärke am Lautsprecher. Mit Strg+C abbrechen, falls der Ausgang oder Inhalt nicht passt.

### Schritt 4: Meldungen einordnen

Auf Format-, Backend- und Clippingmeldungen achten. Ein laufender Prozess ohne hörbaren Ton kann am Routing, am stummen Ausgang oder am Inhalt der Datei liegen. Nicht sofort erhöhte Rechte einsetzen.

### Schritt 5: Effekte getrennt vergleichen

Erst einen bekannten Grundaufruf beurteilen. Weitere Effekte einzeln und mit bewussten Parametern ergänzen. Eine hörbare Änderung ist kein Nachweis besserer Qualität und kein Grund, das einzige Original zu verändern.

## 6. Typische Anwendungsfälle

**Kurze lokale Hörprobe:** Einen bekannten Inhalt bewusst über den normalen Audioausgang abspielen.

**Nicht dauerhaft gespeicherte Effektvorschau:** Einen Filter hören, bevor ein späterer separater SoX-Dateiauftrag geplant wird.

**Formatunterstützung eingrenzen:** Prüfen, ob der konkrete Build die Datei und das gewünschte Backend versteht. Eine Dateiendung allein reicht nicht.

**Begrenzte Ausschnittskontrolle:** Mit `trim` einen bekannten Bereich wiedergeben, statt einen langen Bestand vollständig abzuspielen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Hörbare Ausgabe und Pegel

Hohe Verstärkung, falsche Rohparameter oder Synthese können unerwartet lauten oder unangenehmen Ton erzeugen. Systemlautstärke und digitalen Eingabepegel getrennt verstehen. `-q` ist keine Stummschaltung.

### Reihenfolge beeinflusst das Ergebnis

Eingabeoptionen gelten vor ihrer Datei, Effekte folgen danach. Eine falsche Position kann die Bedeutung ändern oder einen Fehler erzeugen. Nicht normale ffmpeg- oder ALSA-Optionen ungeprüft übernehmen.

### Ausgabeweg und Gerätebelegung

Das Standardbackend kann über den Soundserver oder einen anderen Weg laufen. Eine belegte Hardware ist nicht automatisch ein Defekt. Server- und Backend-Auswahl anhand der aktuellen Sitzung prüfen, statt pauschal Dienste zu stoppen.

### Qualität und Ressourcen

Verstärkung kann übersteuern, Umrechnung kann Samples verändern, große beziehungsweise komplexe Quellen können Ressourcen kosten. Der lesende Zugriff auf die Quelldatei verhindert keine hörbaren Nebenwirkungen.

**Root-Rechte sind für die eigene Wiedergabe gewöhnlich nicht erforderlich.** Eine Aufnahme wäre ein anderer Aufruf und wurde nicht beauftragt.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Befehl fehlt | SoX-/play-Komponente nicht installiert. | Passenden Paketstand getrennt klären. |
| Format nicht unterstützt | Fehlender Codec beziehungsweise Build-Funktion. | Lokale Formatliste lesen. |
| Kein Ton | Falscher Ausgang, Mute oder fehlendes Backend. | Audio-Routing und Meldungen prüfen. |
| Ton verzerrt | Clipping oder falsche Sampleinterpretation. | Pegel und echte Eingabeparameter prüfen. |
| Option falsch verstanden | `-v` und `-V` oder Optionsposition verwechselt. | Lokale Syntax nachlesen. |
| Wiedergabe dauert zu lange | Ausschnitt fehlt oder Parameter falsch. | Bewusst begrenzen beziehungsweise abbrechen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Eigene kurze WAV-Datei statt unbekannter Rohdaten verwenden.
2. Systemlautstärke niedrig einstellen.
3. Einen kurzen Ausschnitt und gedämpften Eingabefaktor wählen.
4. Ohne zusätzliche Effektkette anfangen.
5. Meldungen sichtbar lassen und Clipping ernst nehmen.
6. Erhöhte Rechte nicht als Standardreparatur verwenden.

**Prüfstand:** Das SoX-Distributionshandbuch wurde geprüft. `play` ist hier nicht installiert. Keine Tonwiedergabe, Synthese, Gerätekonfiguration oder Effektprüfung wurde ausgeführt. Backend, Formatunterstützung, reale Lautstärke und Tonausgabe bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sox` | Dateiverarbeitung und Effektketten mit ausdrücklicher Ausgabe. |
| `rec` | SoX-Aufnahmeoberfläche. |
| `soxi` | Informationen über Audiodateien. |
| `aplay` | Einfachere ALSA-Wiedergabe mit anderer Syntax. |
| `pactl`, `wpctl` | Soundserver-Routing und Pegel verwalten. |

Ausgangseintrag: Datensatz 42 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
