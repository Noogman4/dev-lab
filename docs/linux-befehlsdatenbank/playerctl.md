---
id: "playerctl"
name: "playerctl"
command: "playerctl"
category: "Audio Video Grafik"
language: "de"
root_required: false
risk_level: "caution"
tags: ["audio video grafik", "playerctl"]
status: "Ausgearbeitet; Quellen geprüft; Sitzungstest offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 43
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielles Projekt und Handbuch geprüft"
---

# playerctl – Medienplayer über MPRIS lesen und gezielt steuern

## 1. Kurzbeschreibung

`playerctl` fragt MPRIS-fähige Medienplayer ab und sendet ihnen Steuerbefehle. Es kann Status und Titel lesen oder Wiedergabe, Pause, Titelwechsel und bestimmte Player-Einstellungen auslösen.

**Für die eigene Desktop-Sitzung sind keine Root-Rechte nötig.** Steuerbefehle können laufende Player und Browsermedien beeinflussen. Hier ist das Werkzeug nicht installiert und es werden keine Player gesteuert.

## 2. Was macht der Befehl?

MPRIS stellt eine Mediensteuerung über den Sitzungs-D-Bus bereit. Playerctl spricht mit Anwendungen, die diese Schnittstelle anbieten. Das ist keine allgemeine Steuerung aller Audiohardware und kein Garant dafür, dass jede Anwendung dieselben Funktionen unterstützt.

Bei mehreren Playern ist die Auswahl entscheidend. Ohne bewusste Namensauswahl kann ein anderer Player als erwartet angesprochen werden. Ein zusätzlich laufendes `playerctld` kann die Auswahl nach Aktivität beeinflussen; dieser Dienst wird hier weder gestartet noch eingerichtet.

Grundlagen: [offizielles Projekt](https://github.com/altdesktop/playerctl) und [offizieller Handbuchquelltext](https://raw.githubusercontent.com/altdesktop/playerctl/master/doc/playerctl.1.in). Laufende Player und Unterstützung einzelner Eigenschaften bleiben sitzungsabhängig.

## 3. Syntax

```text
playerctl [OPTIONEN] BEFEHL [ARGUMENTE]
```

```bash
playerctl --list-all
playerctl --player=NAME status
playerctl --player=NAME metadata
```

`NAME` ist ein Platzhalter für einen aktuell aufgelisteten eigenen Player, kein vorgegebener Programmtitel. Die Beispiele lesen Informationen. `play`, `pause`, `next` oder eine Lautstärkezuweisung wären verändernde Aufträge.

## 4. Wichtige Optionen

| Option oder Befehl | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `--version`, `--help` | Version und Hilfe. | Vor lokaler Verwendung prüfen. |
| `-l`, `--list-all` | Steuerbare Playernamen auflisten. | Aktuelle Sitzung betrachten. |
| `-p NAME`, `--player=NAME` | Player wählen. | Instanzen und mögliche Namensübereinstimmungen beachten. |
| `-a`, `--all-players` | Befehl auf alle passenden Player anwenden. | Bei Steuerbefehlen wesentlich größerer Umfang. |
| `-i NAME`, `--ignore-player=NAME` | Player ausschließen. | Auswahl ist nicht dieselbe wie garantierte Einzelbindung. |
| `-F`, `--follow` | Aktualisierte Abfrage fortlaufend ausgeben. | Bleibt normalerweise aktiv, bis beendet. |
| `status` | Wiedergabestatus lesen. | Kein Nachweis für hörbaren Ton. |
| `metadata [SCHLÜSSEL]` | Titel- und weitere Metadaten lesen. | Eingabewerte stammen vom Player. |
| `position` | Aktuelle Position lesen. | Mit zusätzlichem Wert wird daraus ein Such-/Sprungauftrag. |
| `volume` | Playerlautstärke lesen. | Mit Wert wird sie verändert; Skala gewöhnlich 0,0 bis 1,0. |
| `play`, `pause`, `stop` | Wiedergabe steuern. | Kann sofort Ton oder Unterbrechung auslösen. |
| `next`, `previous` | Titel wechseln. | Wirkung hängt vom Player und seiner Liste ab. |
| `--format=VORLAGE` | Informationsausgabe formatieren. | Nicht als ausführbaren Shell-Text behandeln. |

Eine Formatvorlage kann etwa `{{artist}}` und `{{title}}` verwenden. Leere beziehungsweise abweichende Metadaten sind möglich. Aus Vorlagenersetzung keine sichere Shell-Zitierung ableiten.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Lokales Werkzeug prüfen

```bash
playerctl --version
playerctl --help
```

Fehlt das Programm, bleibt die Anleitung ungeprüft. Hier wurde es nicht nachinstalliert.

### Schritt 2: Vorhandene Player lesen

```bash
playerctl --list-all
```

Dieser optionale Sitzungsaufruf listet geeignete Player. Es wird nicht automatisch ein neuer Player gestartet. Auch ein Browser kann einen MPRIS-Eintrag bereitstellen.

### Schritt 3: Ziel ausdrücklich einsetzen

Einen tatsächlich gelisteten eigenen Namen auswählen und im folgenden Aufruf `NAME` ersetzen:

```bash
playerctl --player=NAME status
```

Ein Status wie „Playing“ beschreibt die Anwendung. Ob Lautsprecher, Routing oder Systempegel richtig eingestellt sind, wird damit nicht geprüft.

### Schritt 4: Titel lesen

```bash
playerctl --player=NAME metadata --format '{{artist}} – {{title}}'
```

Die Ausgabe kann fehlen oder unvollständig sein, wenn der Player keine entsprechenden Tags liefert. Sie kann persönliche Mediennamen enthalten. Den Text nicht an `sh`, `eval` oder eine andere Befehlsauswertung weiterreichen.

### Schritt 5: Steuerung getrennt planen

Für einen später ausdrücklich gewünschten Pausentest einen eindeutigen Player wählen und den vorherigen Zustand notieren. Der aktuelle Dokumentationsauftrag führt keinen Pausen-, Start- oder Titelwechsel aus.

## 6. Typische Anwendungsfälle

**Statusanzeige bauen:** Playerstatus und Titel für eine eigene Oberfläche lesen. Fehlende Player und leere Metadaten ausdrücklich behandeln.

**Einen bestimmten Player steuern:** Vorherige Namensauswahl verhindert manche Verwechslungen mit parallel laufenden Browsermedien.

**Tastenkürzel vorbereiten:** Ein späterer eigener Shortcut kann Pause oder Titelwechsel auslösen. Dessen Zielauswahl und Mehrfachausführung vorher bewusst prüfen.

**Statusänderungen verfolgen:** `--follow` für eine fortlaufende Informationsansicht verwenden. Ein dauerhaft laufender Prozess und seine Beendigung gehören dann zum Verfahren.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Falscher oder zu großer Zielumfang

Ein fehlender Playerfilter oder `--all-players` kann mehrere Anwendungen betreffen. Ein Play-Pause-Toggle kann bei Wiederholung den Zustand wieder zurückändern. Für einen bestimmten Zielzustand ist ein eindeutiger Start- oder Pausenauftrag besser nachvollziehbar als blindes Umschalten.

### Lesen und Schreiben liegen eng beieinander

`volume` und `position` lesen ohne Wert, verändern mit Wert. Eine angehängte Zahl ist daher keine bloße Anzeigeformatierung. Relative Änderungen können sich bei wiederholten Aufrufen addieren.

### URLs und fremde Metadaten

`open URI` kann einen Player zum Öffnen einer Datei oder externen Quelle auffordern und dadurch Netzwerkaktivität auslösen. Titel und Tags sind fremde Daten, keine vertrauenswürdigen Kommandos. Für die Beispiele werden weder Quellen geöffnet noch Metadaten ausgeführt.

### Sitzung und unterstützte Fähigkeiten

Ein root-Prozess spricht nicht automatisch mit dem richtigen Sitzungs-D-Bus. Manche Player unterstützen keine Positionierung, Lautstärke oder bestimmte Statuswerte. Eine entsprechende Fehlermeldung ist kein Grund für pauschale Berechtigungsänderungen.

**Root-Rechte sind für die eigene MPRIS-Sitzungssteuerung unnötig.** Playerlautstärke und systemweite Gerätepegel sind unterschiedliche Ebenen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Player gefunden | Kein passender MPRIS-Dienst in dieser Sitzung. | Sitzung und laufende Anwendung prüfen. |
| Falsche Anwendung reagiert | Unklare Auswahl oder mehrere Instanzen. | Aktuelle Namen ausdrücklich zuordnen. |
| Metadaten leer | Player liefert die Felder nicht. | Verfügbare Schlüssel lesen und leere Werte behandeln. |
| Status Playing, kein Ton | Audioausgang oder Pegelproblem. | Mit Audioverwaltung getrennt prüfen. |
| Befehl nicht unterstützt | Player bietet betreffende Fähigkeit nicht. | Schnittstellenfähigkeit berücksichtigen. |
| Aufruf bleibt aktiv | `--follow` gewählt. | Bewusst beenden beziehungsweise Beobachtungsdauer planen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Zuerst nur Playerliste, Status und Metadaten lesen.
2. Das Ziel ausdrücklich auswählen.
3. Keine pauschale Steuerung aller Player als ersten Test verwenden.
4. Toggle und eindeutige Zielzustände unterscheiden.
5. Metadaten ausschließlich als Daten behandeln.
6. MPRIS-Status und tatsächliche Audioausgabe getrennt beurteilen.

**Prüfstand:** Offizielles Projekt und Handbuch wurden geprüft. Playerctl ist hier nicht installiert. Keine D-Bus-Abfrage, Playersteuerung, Quellenöffnung oder dauerhafte Beobachtung wurde ausgeführt. Zielauswahl, Metadaten und konkrete Playerfähigkeiten bleiben praktische Prüfpunkte.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `playerctld` | Optionaler Dienst für aktivitätsbezogene Auswahl. |
| `pactl`, `wpctl` | Audio-Routing und Gerätepegel statt Medienplayerzustand. |
| `pavucontrol` | Grafische Audioverwaltung. |
| `play`, `aplay` | Eigentliche Audio-Wiedergabewerkzeuge. |

Ausgangseintrag: Datensatz 43 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
