---
id: "wpctl"
name: "wpctl"
command: "wpctl"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "wpctl"]
status: "Ausgearbeitet; Quellen und lokale Hilfe geprüft; Serveraktionen offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 45
reviewed_at: "2026-11-13"
locally_checked_version: "WirePlumber-Paket 0.4.17-1ubuntu4.1; lokale CLI-Hilfe geprüft"
---

# wpctl – PipeWire-Objekte mit WirePlumber lesen und gezielt steuern

## 1. Kurzbeschreibung

`wpctl` ist die Kommandozeilensteuerung von WirePlumber, einer Sitzungsverwaltung für PipeWire. Es zeigt Medienobjekte und steuert unter anderem Standardziele, Lautstärke und Stummschaltung.

**Für die eigene normale Desktop-Sitzung sind keine Root-Rechte nötig.** Lesen und Ändern sind unterschiedliche Unterbefehle. Hier werden keine Serverobjekte abgefragt oder verändert; ausgeführt wurden nur Hilfeseiten und eine Paketversionsabfrage.

## 2. Was macht der Befehl?

PipeWire verwaltet Geräte, Nodes und Medienverbindungen. WirePlumber trifft darüber Sitzungsentscheidungen. Wpctl stellt ausgewählte Informationen und Steuerungen bereit. Ein Gerät, ein Wiedergabe-Node und ein Anwendungsstream sind nicht dieselbe Ebene.

Objekt-IDs gehören zum laufenden Zustand und können nach Änderungen wechseln. Standardaliase wie `@DEFAULT_AUDIO_SINK@` werden zur Laufzeit aufgelöst. Sie bedeuten nicht dauerhaft denselben physischen Ausgang.

Grundlagen: [offizielle aktuelle wpctl-Referenz](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html), [offizieller Quellstand 0.4.17](https://raw.githubusercontent.com/PipeWire/wireplumber/0.4.17/src/tools/wpctl.c) und lokale Unterbefehlshilfe. Die aktuelle Online-Referenz beschreibt neuere Versionen; zusätzliche dortige Befehle werden nicht als lokal verfügbar vorausgesetzt.

## 3. Syntax

```text
wpctl BEFEHL [BEFEHLSOPTIONEN] [ARGUMENTE]
```

```bash
wpctl status
wpctl get-volume @DEFAULT_AUDIO_SINK@
wpctl inspect @DEFAULT_AUDIO_SINK@
```

Diese Beispiele lesen Zustand. `set-volume`, `set-mute`, `set-default` und `set-profile` ändern ihn. Vor einer Änderung das aktuelle Objekt und seine Rolle unmittelbar prüfen.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--help` | Allgemeine Hilfe. | Lokal vorhandene Unterbefehle anzeigen. |
| `BEFEHL --help` | Hilfe zu einem Unterbefehl. | Vor Übernahme neuer Optionen lesen. |
| `status` | Objektübersicht. | Geräte, Sinks, Sources und Streams getrennt interpretieren. |
| `status --name` | Technische Namen anzeigen. | Unterstützt vom hier gelesenen lokalen Build. |
| `status --nick` | Kurznamen anzeigen. | Andere Darstellung, keine neue Objektbindung. |
| `inspect ID` | Eigenschaften eines Objekts lesen. | Fremde und sitzungsbezogene Werte können enthalten sein. |
| `inspect --referenced ID` | Referenzierte Objekte einbeziehen. | Größerer Berichtsumfang. |
| `get-volume ID` | Lautstärke und gegebenenfalls Mute lesen. | Lautstärke und hörbarer Erfolg unterscheiden. |
| `set-volume ID WERT` | Lautstärke ändern. | `0.5` entspricht der normalen 50-Prozent-Referenz. |
| `set-volume --limit 1.0 ID WERT` | Änderung mit gewählter Obergrenze. | Kein absoluter akustischer Lautstärkeschutz. |
| `set-mute ID 1`, `0`, `toggle` | Stumm an, aus oder umschalten. | Toggle kann bei Wiederholung wieder entstummen. |
| `set-default ID` | Standardziel setzen. | Kein pauschaler Umzug aller bestehenden Verbindungen. |
| `set-profile ID INDEX` | Kartenprofil wählen. | Kann verfügbare Geräte und Verbindungen ändern. |
| `clear-default [ID]` | Explizite Standardvorgabe zurücknehmen. | Syntax und gewünschte Klasse lokal prüfen. |

Die Listen zeigen hier dokumentierte Möglichkeiten, keine ausgeführten Änderungsaufträge. Nummerische Beispiel-IDs aus fremden Anleitungen niemals ungeprüft übernehmen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Lokale Befehle prüfen

```bash
wpctl --help
wpctl status --help
wpctl set-volume --help
```

Diese Hilfebefehle wurden gelesen. Der vorliegende Paketstand ist WirePlumber 0.4.17-1ubuntu4.1. Einen allgemeinen `wpctl --version`-Schalter nicht erfinden, wenn die konkrete lokale Hilfe ihn nicht anbietet.

### Schritt 2: Eigene Sitzung ansehen

```bash
wpctl status
```

Dieser optionale lesende Serveraufruf wurde hier nicht ausgeführt. In der Übersicht die Wiedergabeausgänge und Aufnahmequellen getrennt betrachten.

### Schritt 3: Standardausgang lesen

```bash
wpctl get-volume @DEFAULT_AUDIO_SINK@
```

Die Lautstärke beschreibt das aktuell aufgelöste Standardobjekt. Bei keinem passenden Standard kann der Aufruf fehlschlagen. Ein Wert ohne Mute garantiert nicht, dass ein bestimmter Player richtig geroutet ist.

### Schritt 4: Zuordnung genauer untersuchen

```bash
wpctl inspect @DEFAULT_AUDIO_SINK@
```

Eigenschaften des aktuellen Objekts helfen, Name und Rolle zuzuordnen. Den Bericht nicht ungeprüft teilen; Geräte- und Anwendungsinformationen können enthalten sein.

### Schritt 5: Änderungen separat planen

Für einen später beauftragten Pegel- oder Standardwechsel zuerst bisherigen Wert und Ziel notieren. Danach nur eine konkrete Änderung vornehmen und erneut lesen. Die aktuelle Dokumentation führt keine solche Änderung aus.

## 6. Typische Anwendungsfälle

**Kein Ton im PipeWire-Desktop:** Standardnode, Mute, Pegel und konkrete Anwendung getrennt untersuchen.

**Gerätezuordnung verstehen:** Aktuelle Namen und Objektrollen lesen, bevor eine neue Vorgabe gesetzt wird.

**Kontrollierter Lautstärkeauftrag:** Einen ausdrücklich ausgewählten Node und eine nachvollziehbare Grenze verwenden. Systempegel, Anwendungssignal und physische Lautstärke bleiben verschiedene Ebenen.

**Versionsunterschiede erkennen:** Mit lokaler Hilfe feststellen, welche der aktuellen Online-Funktionen tatsächlich vorhanden sind. Eine neue Dokumentationsseite ersetzt kein lokales Funktionsangebot.

## 7. Risiken, Nebenwirkungen und Vorsicht

### IDs und Standardaliase sind dynamisch

Ein alter Index kann später ein anderes Objekt bezeichnen. Auch ein Standardalias kann sich durch Gerätewechsel ändern. Vor einem schreibenden Aufruf aktuell prüfen, welches Objekt betroffen wäre.

### Pegel und relative Änderungen

Ein angehängtes Plus oder Minus kann eine relative Lautstärkeänderung bedeuten. Wiederholte Aufrufe addieren sich. Werte über der normalen Referenz können verstärken und verzerren. Eine Softwaregrenze sagt nichts über eine garantierte sichere Lautsprecherlautstärke aus.

### Mute und Profile verändern laufenden Betrieb

Entstummen kann sofort Ton hörbar machen. Profilwechsel kann Ausgänge oder Quellen entfernen und laufende Verbindungen unterbrechen. Den vorherigen Zustand festhalten und keine Serie unverbundener Reparaturbefehle ausführen.

### Persistenz und Sitzung

Standardvorgaben können durch die Sitzungsverwaltung gespeichert werden. Das Ende des Clients setzt sie nicht automatisch zurück. Ein Start als root ist nicht gleichbedeutend mit Zugriff auf die richtige Benutzersitzung.

### Diagnoseangaben sind Daten

Namen, Eigenschaften und IDs aus Berichten nicht ungeprüft in Shell-Auswertung übernehmen. Die Übersicht ist kein vollständiger Sicherheits- oder Qualitätsnachweis des Audioaufbaus.

**Root-Rechte sind für die gewöhnliche eigene Sitzungssteuerung unnötig.** Ein Fehler rechtfertigt keine pauschalen Rechte-, Dienst- oder Konfigurationsänderungen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Keine Verbindung | PipeWire-/WirePlumber-Sitzung nicht erreichbar. | Gewünschten Sitzungskontext prüfen. |
| ID nicht gefunden | Flüchtiger oder falscher Index. | Aktuelle Übersicht lesen. |
| Kein Standardobjekt | Kein passender verfügbarer Node. | Geräte und Objektrollen prüfen. |
| Ton trotz Pegel still | Mute, Routing oder Ausgang stimmt nicht. | Zustände einzeln untersuchen. |
| Online-Befehl unbekannt | Lokaler Stand älter. | Lokale Unterbefehlshilfe verwenden. |
| Lautstärke steigt bei Wiederholung | Relative statt absolute Zuweisung. | Syntax und gewünschten Zielwert prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Allgemeine und unterbefehlsspezifische Hilfe lesen.
2. Mit Status, Inspect und Get beginnen.
3. Aktuelle Objektrolle unmittelbar vor Änderungen prüfen.
4. Absolute Werte und relative Schritte unterscheiden.
5. Vorherigen Zustand für einen Rückweg notieren.
6. Keine festen IDs aus fremden Systemen übernehmen.

**Prüfstand:** Allgemeine Hilfe sowie Hilfe für Status, Inspect und Set-volume wurden gelesen. Die Paketmetadaten melden WirePlumber 0.4.17-1ubuntu4.1. Kein laufender Serverzustand wurde für diesen Dokumentationstest abgefragt, kein Pegel oder Profil geändert und kein Audiogerät benutzt. Alle realen Serveraktionen bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `pactl` | PulseAudio-kompatible Sicht und Steuerung. |
| `pavucontrol` | Grafische Audioverwaltung über passende Serverkompatibilität. |
| `playerctl` | MPRIS-Player statt PipeWire-Objekte steuern. |
| `aplay`, `arecord` | Reale Wiedergabe und Aufnahme über ALSA. |

Ausgangseintrag: Datensatz 45 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
