---
id: "screen"
name: "screen"
command: "screen"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "safe"
tags: ["cloud", "remote", "terminal", "sitzung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 133
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# screen – Terminalsitzungen dauerhaft halten und mehrere Fenster nutzen

## 1. Kurzbeschreibung

GNU `screen` ist ein **Terminal-Multiplexer**: Er startet in einem Terminal mehrere Fenster mit eigenen Shells oder Programmen. Vor allem kann man eine Sitzung **abkoppeln** („detach“), die Programme laufen weiter, und sie später – auch von einem anderen Rechner per SSH – wieder **anhängen** („reattach“).

**Root-Rechte sind nicht nötig.** Jeder Benutzer kann eigene Sitzungen starten. Nur der Mehrbenutzerbetrieb, bei dem andere Konten an eine Sitzung angehängt werden, setzt laut Manpage ein setuid-root installiertes `screen` voraus.

Grundlage ist die [Debian-Manpage zu screen](https://manpages.debian.org/trixie/screen/screen.1.en.html) für GNU Screen 4.9.1. Auf dem geprüften System ist `screen` nicht installiert.

## 2. Was macht der Befehl?

Laut Manpage startet `screen` zunächst ein Fenster mit einer Shell. Weitere Fenster entstehen mit einer Tastenfolge. Alle Fenster laufen unabhängig; Programme laufen weiter, auch wenn ihr Fenster nicht sichtbar ist oder die ganze Sitzung abgekoppelt wurde. Endet das letzte Programm, beendet sich `screen`.

Befehle an `screen` selbst beginnen mit der **Befehlstaste `Strg+a`** (in der Manpage `C-a`), gefolgt von einer weiteren Taste:

| Tasten | Wirkung |
| --- | --- |
| `Strg+a` dann `c` | Neues Fenster mit Shell. |
| `Strg+a` dann `n` / `p` | Nächstes / vorheriges Fenster. |
| `Strg+a` dann `0` bis `9` | Fenster mit dieser Nummer. |
| `Strg+a` dann `w` | Fensterliste anzeigen. |
| `Strg+a` dann `"` | Auswahlliste der Fenster. |
| `Strg+a` dann `d` | Sitzung abkoppeln; Programme laufen weiter. |
| `Strg+a` dann `[` | Kopier- und Rückblättermodus. |
| `Strg+a` dann `S` | Bereich horizontal teilen; `Tab` wechselt den Bereich. |
| `Strg+a` dann `H` | Protokollierung des Fensters ein/aus. |
| `Strg+a` dann `k` | Aktuelles Fenster beenden. |
| `Strg+a` dann `\` | Alle Fenster beenden und `screen` verlassen. |
| `Strg+a` dann `?` | Tastenbelegung anzeigen. |

Weil `Strg+a` von `screen` abgefangen wird, erreicht man das Zeichen in der Shell (Zeilenanfang) mit `Strg+a` und dann `a`.

## 3. Syntax

```text
screen [OPTIONEN] [BEFEHL [ARGUMENTE]]
screen -r [SITZUNG]
screen -ls
```

```bash
screen -S arbeit
screen -ls
screen -r arbeit
screen -dmS sicherung rsync -a quelle/ ziel/
```

Das bisherige NetMon-Beispiel `screen --help` ist keine dokumentierte Option; die Manpage nennt `-v` für die Version, und die Tastenbelegung erscheint mit `Strg+a ?`. **Prüfpunkt:** Verhalten von `--help` in der installierten Version prüfen. Der Platzhalter `screen [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-S NAME` | Sitzung mit Namen starten. | Höchstens 80 Zeichen; erleichtert `-r`. |
| `-ls`, `-list` | Eigene Sitzungen auflisten. | Zeigt `Attached`, `Detached`, `Dead`. |
| `-r [SITZUNG]` | Abgekoppelte Sitzung anhängen. | Bei mehreren Sitzungen Namen angeben. |
| `-R`, `-RR` | Anhängen, sonst neu starten. | `-RR` nimmt die jüngste (Debian-Ergänzung). |
| `-d -r` | Woanders angehängte Sitzung abkoppeln und hier anhängen. | Hilfreich nach abgerissener SSH-Verbindung. |
| `-x` | An eine angehängte Sitzung zusätzlich anhängen. | Mehrere Terminals sehen dasselbe. |
| `-d -m` | Sitzung direkt abgekoppelt starten. | Für Hintergrundaufgaben. |
| `-X BEFEHL` | Befehl an laufende Sitzung senden. | Mit `-S NAME`. |
| `-L`, `-Logfile DATEI` | Ausgabeprotokoll aktivieren und Datei wählen. | Protokolle können Geheimnisse enthalten. |
| `-wipe` | Tote Sitzungen entfernen. | – |
| `-U` | UTF-8-Modus. | – |
| `-v` | Version anzeigen. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Server eine lang laufende Aufgabe starten, die Verbindung trennen und später weiterarbeiten. Das Beispiel wurde **nicht ausgeführt**, weil `screen` nicht installiert ist.

### Schritt 1: Benannte Sitzung starten

```bash
screen -S arbeit
```

Eine neue Shell erscheint – scheinbar unverändert.

### Schritt 2: Lange Aufgabe starten

```bash
ping -c 600 localhost
```

Dies dient nur als harmloses, lange laufendes Beispiel.

### Schritt 3: Abkoppeln

`Strg+a`, dann `d`. Es erscheint `[detached ...]`. Die Aufgabe läuft weiter; du kannst dich abmelden.

### Schritt 4: Sitzungen anzeigen und wieder anhängen

```bash
screen -ls
screen -r arbeit
```

`-ls` zeigt die Sitzung als `Detached`. Nach `-r` siehst du die laufende Ausgabe wieder.

### Schritt 5: Beenden

`exit` in der letzten Shell oder `Strg+a`, dann `\` (beendet alle Fenster).

## 6. Typische Anwendungsfälle

- **Fernarbeit per SSH:** Aufgaben überstehen Verbindungsabbrüche.
- **Mehrere Shells** in einem Terminal, etwa Protokoll und Editor.
- **Hintergrundaufgaben:** `screen -dmS NAME BEFEHL`.
- **Serielle Konsolen:** `screen /dev/ttyUSB0 115200` öffnet eine serielle Schnittstelle; laut Manpage sind Lese- und Schreibrechte auf das Gerät nötig. **Prüfpunkt:** Auf Debian/Ubuntu meist über die Gruppe `dialout`; nicht geprüft.
- **Gemeinsame Sitzung** mit `-x` für Vorführungen.

## 7. Risiken, Nebenwirkungen und Vorsicht

`screen` verändert keine Dateien, solange keine Protokollierung aktiv ist. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen, mit diesen Hinweisen:

- **Vergessene Sitzungen:** Abgekoppelte Programme laufen weiter und belegen Speicher. Root-Shells in abgekoppelten Sitzungen bleiben offen, bis jemand sie beendet. Regelmäßig `screen -ls` prüfen.
- **Protokolle:** Mit `-L` oder `Strg+a H` landet alles, was im Fenster erscheint, in einer Datei – auch Passwörter, die angezeigt wurden.
- **Versehentliches Beenden:** `Strg+a k` und `Strg+a \` beenden Programme; laufende Arbeit kann verloren gehen.
- **Mehrbenutzerbetrieb:** Mit setuid-root und Freigaben (`acladd`) können andere Konten an Sitzungen teilnehmen. Falsch eingerichtet, sieht oder steuert ein fremdes Konto die Sitzung.
- **Verschachtelung:** `screen` innerhalb von `screen` wird laut Manpage bei `-x` nicht als Schleife erkannt.
- **Tastenkonflikt:** `Strg+a` ist in der Shell „Zeilenanfang“; das kann irritieren.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `There is no screen to be resumed.` | Keine abgekoppelte Sitzung. | `screen -ls` prüfen. |
| `There are several suitable screens` | Mehrere Sitzungen. | Namen oder `PID.tty.host` angeben. |
| Sitzung als `Attached` angezeigt, aber Verbindung weg | Alte SSH-Verbindung noch nicht beendet. | `screen -d -r NAME`. |
| Sitzung als `Dead` | Prozess abgestürzt oder Rechner neu gestartet. | `screen -wipe`. |
| `Strg+a` springt nicht an den Zeilenanfang | Von `screen` abgefangen. | `Strg+a` dann `a`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Sitzungen immer benennen** (`-S`).
2. **Zum Abkoppeln `Strg+a d`,** nicht das Terminal schließen, wenn es sich vermeiden lässt.
3. **Regelmäßig `screen -ls`** und alte Sitzungen beenden.
4. **Protokollierung nur bewusst** einschalten.
5. **Alternative `tmux`** prüfen; es ist auf vielen Systemen ebenfalls verbreitet.

### Prüfstand

- **Geprüfte Version:** keine; `screen` ist nicht installiert. Die gelesene Manpage beschreibt GNU Screen 4.9.1 (Debian trixie). **Prüfpunkt:** Neuere Hauptversionen können abweichen.
- **Quellen gelesen:** Debian-Manpage `screen(1)` (Beschreibung, Optionen, Tastenbelegung, Mehrbenutzerbetrieb), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Fehlermeldungen, serielle Konsole, `--help`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tmux` | Modernerer Terminal-Multiplexer mit ähnlichen Aufgaben. |
| `nohup`, `setsid` | Starten Programme unabhängig vom Terminal, ohne Wiederanhängen. |
| `ssh`, `mosh` | Fernzugang; oft mit `screen` kombiniert. |
| `script` | Protokolliert eine Terminalsitzung in eine Datei. |

Ausgangseintrag: Datensatz 133 in `index.json` (`screen`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, Tastenbelegung, Optionen und einen Ablauf zum Abkoppeln und Anhängen ersetzt.
