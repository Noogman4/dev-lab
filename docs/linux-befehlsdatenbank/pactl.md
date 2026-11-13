---
id: "pactl"
name: "pactl"
command: "pactl"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "pactl"]
status: "Ausgearbeitet; lokale Hilfe geprüft; Serveraktionen nicht getestet"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 40
reviewed_at: "2026-11-13"
locally_checked_version: "pactl/libpulse 16.1; Hilfe und Version geprüft"
---

# pactl – Audiogeräte lesen und Soundserver-Zustand gezielt ändern

## 1. Kurzbeschreibung

`pactl` fragt einen PulseAudio-kompatiblen Soundserver ab und steuert Geräte, Lautstärke sowie laufende Audioverbindungen. Auf einem PipeWire-System kann die Verbindung über dessen PulseAudio-Kompatibilitätsschicht laufen.

**Für die normale Audiosteuerung der eigenen Desktop-Sitzung sind keine Root-Rechte nötig.** Leseaufrufe und verändernde Unterbefehle müssen klar getrennt werden. Diese Dokumentation verändert keine Lautstärke und kein Routing.

## 2. Was macht der Befehl?

Der Client verbindet sich mit einem Soundserver. „Sink“ bezeichnet ein Wiedergabeziel, „Source“ eine Aufnahmequelle. „Sink-input“ ist ein Wiedergabestream einer Anwendung, „Source-output“ ein Aufnahmestream. Diese Bezeichnungen sind keine physischen Stecker und keine dauerhaften Dateipfade.

Nummerische Indizes sind laufzeitabhängig. Nach Neustarts oder Gerätewechseln kann dieselbe Zahl ein anderes Objekt bezeichnen. Symbolische Namen und die aktuelle Liste unmittelbar vor einer bewussten Änderung prüfen.

Grundlagen: [Distributions-Manpage zu pactl](https://manpages.debian.org/trixie/pulseaudio-utils/pactl.1.en.html) und lokale Hilfe von pactl/libpulse 16.1. Welcher Server tatsächlich läuft und welche Operationen er unterstützt, wurde hier nicht abgefragt.

## 3. Syntax

```text
pactl [OPTIONEN] UNTERBEFEHL [ARGUMENTE ...]
```

```bash
pactl info
pactl list short sinks
pactl get-default-sink
```

Diese Aufrufe lesen Serverangaben. Im Gegensatz dazu verändern Unterbefehle mit `set-`, `move-`, `load-` oder `unload-` den Audiostand. `pactl exit` beendet nicht einfach den Client, sondern fordert den Soundserver zum Beenden auf.

## 4. Wichtige Optionen

| Option oder Unterbefehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--version`, `--help` | Lokale Version und Hilfe. | Benötigen keine normale Serveränderung. |
| `info` | Server- und Standardangaben lesen. | Kann Namen und Sitzungsinformationen enthalten. |
| `list short sinks` | Wiedergabeziele kurz auflisten. | Aktuelle Namen und Indizes. |
| `list short sources` | Aufnahmequellen auflisten. | Monitorquelle nicht mit Mikrofon verwechseln. |
| `list short sink-inputs` | Laufende Wiedergabestreams. | Indizes können sich ändern. |
| `get-default-sink` | Standardausgabe lesen. | Keine Gewissheit über alle bereits laufenden Streams. |
| `get-sink-volume NAME` | Lautstärke lesen. | Von Stummschaltung unterscheiden. |
| `get-sink-mute NAME` | Stummzustand lesen. | Null Pegel und Mute sind verschiedene Zustände. |
| `set-sink-volume NAME WERT` | Lautstärke verändern. | Werte können relative Änderungen ausdrücken; bewusst wählen. |
| `set-sink-mute NAME 1` | Ziel stummschalten. | Wirkt auf zugehörige Wiedergabe. |
| `set-default-sink NAME` | Standardausgabe ändern. | Nicht pauschal alle laufenden Streams umziehen. |
| `move-sink-input ID ZIEL` | Einen Wiedergabestream umhängen. | Aktuellen Stream eindeutig bestimmen. |
| `--format=json` | Strukturierte Ausgabe bei unterstützten Aufrufen. | Lokales Schema und Unterstützung prüfen. |
| `--server=SERVER` | Anderen Server wählen. | Kann Verbindung zu anderem Endpunkt bedeuten. |

`@DEFAULT_SINK@` und `@DEFAULT_SOURCE@` sind symbolische Auswahlhilfen. Ihr aktuelles Ziel kann sich ändern; sie sind keine dauerhafte Bindung an ein bestimmtes Gerät.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Client prüfen

```bash
pactl --version
pactl --help
```

Diese beiden lokalen Informationsaufrufe wurden hier ausgeführt. Die folgenden Serverabfragen sind eine dokumentierte Anleitung und wurden für diesen Auftrag nicht gestartet.

### Schritt 2: Eigene Sitzung einordnen

```bash
pactl info
```

Prüfen, ob der beabsichtigte lokale Soundserver erreicht wird. Ein Client-Versionswert allein sagt nicht, ob der Server PulseAudio oder eine kompatible Implementierung ist.

### Schritt 3: Ziele und Quellen lesen

```bash
pactl list short sinks
pactl list short sources
```

Wiedergabe und Aufnahme getrennt betrachten. Eine Monitorquelle bildet typischerweise einen Wiedergabepfad ab und ist kein sicherer Beleg für das gewünschte Mikrofon.

### Schritt 4: Standardausgabe und Pegel prüfen

```bash
pactl get-default-sink
pactl get-sink-volume @DEFAULT_SINK@
pactl get-sink-mute @DEFAULT_SINK@
```

Damit lassen sich Standardziel, Lautstärke und Mute getrennt lesen. Bei laufender Musik zusätzlich den konkreten Anwendungsstream prüfen; dieser muss nicht denselben Weg verwenden.

### Schritt 5: Änderungen als eigenen Auftrag behandeln

Erst nach eindeutiger Objektzuordnung eine notwendige Änderung planen und den bisherigen Zustand notieren. Diese Dokumentation führt weder Lautstärkeänderung noch Streamverschiebung oder Serverneustart aus.

## 6. Typische Anwendungsfälle

**Kein Ton trotz laufender Anwendung:** Standardziel, tatsächlichen Anwendungsstream, Pegel und Mute auseinanderhalten.

**Gezieltes Routing:** Einen bestimmten laufenden Stream bewusst einem passenden Ziel zuordnen. Numerische IDs unmittelbar zuvor erneut prüfen.

**Eingangsquelle verstehen:** Aufnahmegerät und Monitorquelle getrennt bestimmen, bevor ein aufnehmendes Programm gestartet wird.

**Strukturierte Diagnose:** Kleine JSON-Berichte für eigene Auswertung verwenden. Laufzeit-IDs und fehlende Geräte ausdrücklich behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Lautstärke und Aufnahmequelle

Verändernde Befehle können überraschend lauten Ton, Stille oder eine unerwartete Aufnahmequelle verursachen. Relative Lautstärkeschritte addieren sich bei Wiederholung. Werte über der normalen Verstärkungsreferenz sind je nach Server möglich und können verzerren.

### Flüchtige IDs und Standardziele

Ein aus einem alten Bericht kopierter Index kann falsch sein. Auch ein Standardalias kann inzwischen auf ein anderes Gerät zeigen. Unmittelbar vor einer Änderung die aktuelle Zuordnung prüfen; Standardwechsel und Streamumzug nicht gleichsetzen.

### Module und Serverzustand

`load-module`, `unload-module`, Profilwechsel und `exit` greifen weiter in den Audiobetrieb ein. Sie können laufende Wiedergabe oder Aufnahme unterbrechen. Solche Befehle nicht als allgemeine erste Reparatur verwenden.

### Serverwahl und vertrauliche Informationen

Umgebung und Serveroption können den Verbindungsendpunkt beeinflussen. Listen können Anwendungsnamen, Geräte und Sitzungsdaten zeigen. Berichte vor dem Weitergeben prüfen. Keine unbekannten Servervorgaben als legitimes Ziel voraussetzen.

**Root-Rechte sind für die eigene Desktop-Sitzung gewöhnlich unnötig.** `sudo pactl` kann eine andere Umgebung oder einen falschen Serverkontext verwenden und ist keine Standardlösung.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Verbindung abgelehnt | Kein passender Server oder falscher Sitzungskontext. | Clientumgebung und Serverziel prüfen. |
| Objekt nicht gefunden | Alter Index oder Gerät nicht mehr vorhanden. | Aktuelle Liste erneut lesen. |
| Standard geändert, Ton unverändert | Laufender Stream verwendet weiter anderes Ziel. | Konkreten sink-input betrachten. |
| Pegel vorhanden, trotzdem still | Mute, Port, Profil oder falscher Ausgang. | Zustände getrennt prüfen. |
| Falscher Aufnahmeton | Monitor oder andere Source gewählt. | Quelle vor Aufnahme eindeutig zuordnen. |
| JSON-Option anders beschrieben | Versions-/Implementierungsunterschied. | Lokale Hilfe und Schema prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit Version und lesenden Abfragen beginnen.
2. Sink, Source und Anwendungsstream begrifflich trennen.
3. Aktuelle Namen und IDs vor Änderungen prüfen.
4. Bisherigen Zustand für einen Rückweg notieren.
5. Keine pauschalen Modul- oder Serverbeendigungen ausführen.
6. `sudo` nicht reflexartig für Sitzungsaudio verwenden.

**Prüfstand:** Nur `pactl --version` und `pactl --help` wurden ausgeführt; sie melden pactl/libpulse 16.1. Kein Server wurde für diesen Dokumentationstest abgefragt, kein Gerät umgestellt, kein Ton gestartet und keine Lautstärke geändert. Alle beschriebenen Serveraktionen bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pavucontrol` | Grafische PulseAudio-kompatible Audioverwaltung. |
| `wpctl` | WirePlumber-/PipeWire-Sitzungssteuerung. |
| `aplay`, `arecord` | Tatsächliche Audioausgabe und Aufnahme über ALSA. |
| `playerctl` | Medienplayer-Steuerung über MPRIS, keine allgemeine Gerätesteuerung. |

Ausgangseintrag: Datensatz 40 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
