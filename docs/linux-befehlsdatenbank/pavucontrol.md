---
id: "pavucontrol"
name: "pavucontrol"
command: "pavucontrol"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "pavucontrol"]
status: "Ausgearbeitet; Quellen geprüft; grafische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 41
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Projektbeschreibung und Manpage geprüft"
---

# pavucontrol – Audioausgänge und Anwendungsstreams grafisch verwalten

## 1. Kurzbeschreibung

`pavucontrol` öffnet eine grafische Audioverwaltung für einen PulseAudio-kompatiblen Soundserver. Sie kann Gerätepegel und die Zuordnung einzelner Anwendungsstreams getrennt steuern.

**Für die normale eigene Desktop-Sitzung sind keine Root-Rechte nötig.** Einstellungen können unmittelbar auf laufende Wiedergabe und Aufnahme wirken. Hier wird das Programm nicht installiert oder gestartet.

## 2. Was macht der Befehl?

Das Programm verbindet sich mit dem Soundserver der Sitzung und zeigt dessen Geräte und Streams. Auf PipeWire-Systemen kann die PulseAudio-Kompatibilitätsschicht die Verbindung bereitstellen. Eine installierte Oberfläche allein bestätigt keinen erreichbaren Server.

Übliche Bereiche betreffen Wiedergabe, Aufnahme, Ausgabegeräte, Eingabegeräte und Konfiguration. Beschriftungen, Reihenfolge und verfügbare Funktionen können sich nach Version und Übersetzung unterscheiden. Ein laufender Playerstream und ein physischer Ausgang sind unterschiedliche Objekte.

Grundlagen: [offizielle Projektseite](https://freedesktop.org/software/pulseaudio/pavucontrol/) und [Distributions-Manpage](https://manpages.debian.org/trixie/pavucontrol/pavucontrol.1.en.html). Die Projektseite dokumentiert unter anderem getrennte Geräte-/Streamsteuerung und Versionsänderungen. Die tatsächliche Oberfläche wurde hier nicht geprüft.

## 3. Syntax

```text
pavucontrol [OPTIONEN]
```

```bash
pavucontrol
pavucontrol --version
```

Der normale Aufruf öffnet die Oberfläche. `--version` ist für neuere dokumentierte Versionen vorgesehen; vor Übernahme auf alte Systeme die lokale Hilfe prüfen. Es gibt keinen allgemeinen Syntaxzusatz wie `pavucontrol set-volume`, der die GUI zu pactl machen würde.

## 4. Wichtige Optionen

| Option oder Bedienelement | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Lokale Hilfe. | Verfügbare GTK-/Programmoptionen versionsabhängig prüfen. |
| `--version` | Versionsangabe neuerer Versionen. | Nicht als Nachweis einer laufenden Serververbindung verstehen. |
| `-t NUMMER`, `--tab NUMMER` | Beim Start einen Reiter wählen. | Zuordnung anhand der konkreten Version prüfen; keine feste Nummer hier vorausgesetzt. |
| Wiedergabe-Streamauswahl | Ausgang einer Anwendung zuordnen. | Kann laufenden Ton sofort umleiten. |
| Geräte-Lautstärke | Ausgangs- oder Eingangspegel ändern. | Nicht mit Pegel eines einzelnen Streams verwechseln. |
| Stummschaltung | Gewähltes Gerät beziehungsweise Stream stumm schalten. | Wirkung hängt vom gewählten Objekt ab. |
| Standardgerät | Vorgabe für neue beziehungsweise automatisch zugeordnete Streams. | Bereits laufende Streams können weiter anders geroutet sein. |
| Kartenprofil | Verfügbare Ein-/Ausgabekombination wählen. | Kann Geräte und aktive Verbindungen verändern. |

Bedienelemente sind hier keine zusätzlichen Kommandozeilenschalter. Keine erfundenen CLI-Optionen aus GUI-Beschriftungen ableiten.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Programm und Version prüfen

```bash
pavucontrol --version
```

Fehlt das Programm, ist die weitere Anleitung kein ausgeführter Test. Für dieses Dokument wurde keine Installation vorgenommen.

### Schritt 2: Bewusst in der eigenen Sitzung öffnen

```bash
pavucontrol
```

Dieser optionale Schritt würde die grafische Oberfläche mit der eigenen Sitzung verbinden. Kein `sudo` verwenden. Zunächst nur ansehen und noch keine Profile oder Standardgeräte ändern.

### Schritt 3: Wiedergabeobjekte unterscheiden

Im Wiedergabebereich einen vorhandenen Anwendungsstream erkennen. Manche Streams sind nur sichtbar, solange eine Anwendung tatsächlich Audio verarbeitet. Ein fehlender Eintrag bedeutet deshalb nicht automatisch, dass die ganze Soundkarte fehlt.

### Schritt 4: Ausgänge und Mute prüfen

Den dem Stream zugeordneten Ausgang und dessen Lautstärke sowie Stummzustand ansehen. Vor einer nötigen Änderung den vorherigen Zustand notieren. Eine umgeroutete Anwendung kann sofort auf einem anderen Lautsprecher hörbar werden.

### Schritt 5: Änderungen getrennt und einzeln vornehmen

Wenn ein später ausdrücklich gewünschter Test eine Änderung erfordert, jeweils nur eine Einstellung verändern und deren Wirkung kontrollieren. Das Schließen des Fensters ist kein automatisches Zurücksetzen aller vorgenommenen Audioeinstellungen.

## 6. Typische Anwendungsfälle

**Eine Anwendung am falschen Ausgang:** Deren Stream unabhängig vom allgemeinen Standardgerät betrachten und bei Bedarf gezielt umleiten.

**Kein Ton trotz sichtbarem Pegel:** Anwendungspegel, Ausgangspegel, Mute, Port und Profil voneinander unterscheiden. Ein bewegter Pegelbalken beweist nicht, dass der gewünschte Lautsprecher hörbar arbeitet.

**Aufnahmequelle zuordnen:** Einen laufenden Aufnahmestream und seine Quelle prüfen. Eine Monitorquelle kann Desktopton statt eines Mikrofons liefern.

**Gerätekonfiguration verstehen:** Ein aktives Kartenprofil kann bestimmen, welche Ein- und Ausgänge überhaupt angeboten werden. Profilwechsel ist ein verändernder Schritt.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Änderungen wirken im laufenden Betrieb

Pegel, Mute, Streamzuordnung und Profile können sofort wirksam werden. Unerwartet lauter Ton oder ein anderer Wiedergabeort sind möglich. Vorherige Werte notieren und Lautstärke bewusst niedrig wählen.

### Aufnahme und Privatsphäre

Das Programm ist eine Audioverwaltung, keine reine Metadatenliste. Die Wahl einer Quelle kann beeinflussen, was ein bereits laufendes Aufnahmeprogramm erhält. Das Fenster nicht als Anlass nutzen, ohne eigenen Zweck eine Aufnahme zu starten.

### Profile und verschwundene Geräte

Ein anderes Profil kann Verbindungen unterbrechen oder zuvor sichtbare Wege entfernen. Nicht mehrere Einstellungen gleichzeitig umstellen; sonst bleibt die Ursache einer Änderung unklar.

### Sitzung und Serverkontext

Die Oberfläche soll zum normalen Soundserver des Benutzers verbinden. Ein Start als root kann falschen Kontext oder Berechtigungsprobleme erzeugen. Ein Verbindungsfehler rechtfertigt keinen pauschalen Neustart sämtlicher Audiodienste.

### Persistenz und Versionsunterschiede

Je nach Server und Sitzungsverwaltung können Einstellungen gespeichert und später wiederhergestellt werden. Fenster schließen ist kein allgemeiner Rückweg. Unterschiede zwischen älteren „Fallback“-Beschriftungen und neueren Standard-Markierungen anhand der installierten Version einordnen.

**Root-Rechte sind für die gewöhnliche eigene Desktop-Audioverwaltung nicht nötig.** Das Dokumentieren der Oberfläche ist keine Freigabe für reale Systemänderungen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Serververbindung | Sitzung oder Kompatibilitätsschicht nicht erreichbar. | Gewünschten Serverkontext prüfen. |
| Anwendung fehlt | Gerade kein aktiver Stream oder Filter ausgeblendet. | Sichtbarkeitsfilter und laufende Anwendung betrachten. |
| Standard gewechselt, Ton bleibt | Bestehender Stream weiter separat zugeordnet. | Konkrete Streamauswahl prüfen. |
| Mikrofon fehlt | Profil, Port oder Geräteverfügbarkeit. | Eingangsbereich und Kartenprofil bewusst lesen. |
| Falscher Aufnahmeton | Monitor statt Mikrofon gewählt. | Quelltyp und Anwendung zuordnen. |
| Fenster zu, Änderung bleibt | Zustand wurde im Server gespeichert. | Bewusst notierten Ausgangszustand wiederherstellen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zunächst nur die eigene Sitzung ansehen.
2. Gerätepegel und Anwendungspegel auseinanderhalten.
3. Vor Änderungen bisherigen Zustand notieren.
4. Jeweils nur eine Einstellung verändern.
5. Mit niedriger Lautstärke und bekanntem Ausgang arbeiten.
6. Kein `sudo` und keine pauschalen Serverneustarts verwenden.

**Prüfstand:** Offizielle Projektbeschreibung und Manpage wurden gelesen. Pavucontrol ist hier nicht installiert; kein Fenster wurde geöffnet und keine Audioeinstellung verändert. Reiter, Übersetzungen, Streamzuordnung und tatsächliche Persistenz bleiben praktische versionsabhängige Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pactl` | PulseAudio-kompatible CLI-Abfragen und Steuerbefehle. |
| `wpctl` | PipeWire-/WirePlumber-Sitzungssteuerung. |
| `aplay`, `arecord` | Wiedergabe und Aufnahme über ALSA. |
| `playerctl` | Medienplayer über MPRIS statt Audiogeräte steuern. |

Ausgangseintrag: Datensatz 41 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
