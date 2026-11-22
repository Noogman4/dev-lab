---
id: "tmux"
name: "tmux"
command: "tmux"
category: "Cloud & Remote"
language: "de"
root_required: false
risk_level: "safe"
tags: ["cloud", "remote", "terminal", "sitzung"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 134
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; nicht praktisch geprüft"
---

# tmux – Terminal-Multiplexer mit dauerhaften Sitzungen, Fenstern und Bereichen

## 1. Kurzbeschreibung

`tmux` erzeugt in einem einzigen Terminal mehrere Shells und Programme, verteilt auf **Fenster** und geteilte **Bereiche** („panes“). Sitzungen bleiben bestehen, wenn die Verbindung abbricht oder du sie bewusst abkoppelst, und lassen sich später wieder anhängen – auch von einem anderen Rechner per SSH.

**Root-Rechte sind nicht nötig.** Jeder Benutzer startet seinen eigenen tmux-Server.

Grundlage ist die [Debian-Manpage zu tmux](https://manpages.debian.org/trixie/tmux/tmux.1.en.html). Auf dem geprüften System ist `tmux` nicht installiert.

## 2. Was macht der Befehl?

Laut Manpage gibt es drei Ebenen:

| Ebene | Bedeutung |
| --- | --- |
| Sitzung | Sammlung von Pseudo-Terminals unter tmux; überlebt Verbindungsabbrüche. |
| Fenster | Füllt den Bildschirm; eine Sitzung kann viele haben. |
| Bereich | Teil eines Fensters mit eigenem Pseudo-Terminal. |

Alle Sitzungen verwaltet ein **tmux-Server**; was du siehst, ist ein **Client**. Beide sprechen über einen Socket in einem Ordner `tmux-UID` unter `/tmp` (oder `TMUX_TMPDIR`), der laut Manpage nicht für andere lesbar sein darf. Am unteren Rand zeigt eine Statuszeile Sitzung und Fenster.

Befehle an tmux beginnen mit der **Präfixtaste `Strg+b`** (in der Manpage `C-b`), gefolgt von einer Taste:

| Tasten | Wirkung |
| --- | --- |
| `Strg+b` dann `c` | Neues Fenster. |
| `Strg+b` dann `n` / `p` | Nächstes / vorheriges Fenster. |
| `Strg+b` dann `0` bis `9` | Fenster mit dieser Nummer. |
| `Strg+b` dann `%` | Bereich links/rechts teilen. |
| `Strg+b` dann `"` | Bereich oben/unten teilen. |
| `Strg+b` dann `o` | Nächster Bereich. |
| `Strg+b` dann `z` | Bereich vergrößern/zurück. |
| `Strg+b` dann `d` | Abkoppeln; Programme laufen weiter. |
| `Strg+b` dann `[` | Kopiermodus und Verlauf. |
| `Strg+b` dann `x` / `&` | Bereich / Fenster beenden. |
| `Strg+b` dann `?` | Alle Tastenbelegungen. |

## 3. Syntax

```text
tmux [OPTIONEN] [BEFEHL [BEFEHLSOPTIONEN]]
```

Ohne Befehl startet `tmux` eine neue Sitzung (`new-session`).

```bash
tmux new -s arbeit
tmux ls
tmux attach -t arbeit
tmux kill-session -t arbeit
```

`new`, `ls` und `attach` sind laut Manpage Kurzformen von `new-session`, `list-sessions` und `attach-session`.

Das bisherige NetMon-Beispiel `tmux --help` ist keine dokumentierte Option; die Manpage nennt `-V` für die Version, und `Strg+b ?` zeigt die Tastenbelegung. **Prüfpunkt:** Verhalten von `--help` nicht geprüft. Der Platzhalter `tmux [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Aufruf oder Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `tmux new -s NAME` | Benannte Sitzung starten. | `-d` startet sie abgekoppelt. |
| `tmux ls` | Sitzungen auflisten. | – |
| `tmux attach -t NAME` | An Sitzung anhängen. | `-d` koppelt andere Clients ab. |
| `tmux detach` | Abkoppeln (wie `Strg+b d`). | – |
| `tmux kill-session -t NAME` | Sitzung mit allen Programmen beenden. | Laufende Arbeit endet. |
| `tmux kill-server` | Server, alle Clients und Sitzungen beenden. | Beendet alles auf einmal. |
| `-f DATEI` | Andere Konfigurationsdatei. | Standard: `/etc/tmux.conf`, dann `~/.tmux.conf` oder `$XDG_CONFIG_HOME/tmux/tmux.conf`. |
| `-L NAME`, `-S PFAD` | Anderen Socket verwenden. | Für getrennte Server. |
| `-u` | UTF-8-Ausgabe erzwingen. | – |
| `-v` | Ausführliche Protokolle. | Schreibt Dateien in den aktuellen Ordner; `-vv` auch alle Ausgaben. |
| `-V` | Version anzeigen. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Auf einem Server eine Sitzung mit zwei Bereichen anlegen, abkoppeln und wieder anhängen. Das Beispiel wurde **nicht ausgeführt**, weil `tmux` nicht installiert ist.

### Schritt 1: Sitzung starten

```bash
tmux new -s arbeit
```

Unten erscheint die Statuszeile mit dem Sitzungsnamen `[arbeit]`.

### Schritt 2: Bereich teilen

`Strg+b`, dann `%`. Das Fenster ist jetzt links und rechts geteilt. Mit `Strg+b o` wechselst du zwischen den Bereichen.

### Schritt 3: Aufgabe starten und abkoppeln

Im rechten Bereich zum Beispiel `top` starten. Dann `Strg+b`, `d`. Die Meldung `[detached (from session arbeit)]` erscheint.

### Schritt 4: Wieder anhängen

```bash
tmux ls
tmux attach -t arbeit
```

`tmux ls` zeigt die Sitzung. Nach `attach` sind beide Bereiche mit `top` wieder da.

### Schritt 5: Aufräumen

```bash
tmux kill-session -t arbeit
```

## 6. Typische Anwendungsfälle

- **Fernarbeit per SSH oder mosh:** Sitzungen überstehen Abbrüche.
- **Mehrere Ansichten:** Editor, Protokoll und Shell nebeneinander.
- **Hintergrundaufgaben:** `tmux new -d -s sicherung 'rsync -a quelle/ ziel/'`.
- **Gemeinsames Arbeiten:** Mehrere Clients können sich an dieselbe Sitzung hängen.
- **Skripte:** `tmux send-keys` und `tmux capture-pane` automatisieren Eingaben und lesen Inhalte aus. **Prüfpunkt:** Details in der Manpage, nicht geprüft.

## 7. Risiken, Nebenwirkungen und Vorsicht

`tmux` verändert keine Dateien, solange keine Protokollierung aktiv ist. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen, mit diesen Hinweisen:

- **Vergessene Sitzungen:** Programme laufen weiter, auch Root-Shells. Regelmäßig `tmux ls` prüfen.
- **`kill-server`** beendet alle Sitzungen mit allen Programmen.
- **Socket-Rechte:** Wer auf den Socket zugreifen kann, kann die Sitzung steuern. tmux schützt den Ordner selbst; bei `-S` mit eigenem Pfad musst du auf die Rechte achten.
- **Protokolle mit `-v`/`-vv`:** Können alle Terminalausgaben enthalten, inklusive angezeigter Geheimnisse.
- **Verlauf im Kopiermodus:** Enthält frühere Ausgaben; bei gemeinsamen Sitzungen sichtbar für alle Beteiligten.
- **Präfix `Strg+b`:** Programme, die diese Taste selbst nutzen, erhalten sie nur über `Strg+b Strg+b`. **Prüfpunkt:** Standardbindung `send-prefix` nicht geprüft.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `no server running on ...` | Keine Sitzung vorhanden. | Mit `tmux new` starten. |
| `can't find session: ...` | Name falsch. | `tmux ls` prüfen. |
| `sessions should be nested with care` | tmux innerhalb von tmux gestartet. | Vorhandene Sitzung nutzen. |
| Farben oder Zeichen falsch | Terminalfähigkeiten oder Locale. | `-2`, `-u` oder `TERM` prüfen. |
| Konfiguration wirkt nicht | Wird nur beim Serverstart geladen. | `tmux source-file ~/.tmux.conf`. |

**Prüfpunkt:** Meldungstexte sinngemäß, nicht praktisch ausgelöst.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Sitzungen benennen** (`-s`).
2. **Abkoppeln mit `Strg+b d`** statt Terminal schließen.
3. **`Strg+b ?`** zeigt jederzeit die Tasten.
4. **Vor `kill-server` mit `tmux ls`** prüfen, was beendet würde.
5. **`-v` nur zur Fehlersuche** und Protokolldateien danach löschen.

### Prüfstand

- **Geprüfte Version:** keine; `tmux` ist nicht installiert.
- **Quellen gelesen:** Debian-Manpage `tmux(1)` (Aufbau, Optionen, Tastenbelegung, Sitzungsbefehle), Abruf 2026-11-13.
- **Nicht geprüft:** alle Aufrufe, Fehlermeldungen, `--help`, Automatisierungsbefehle.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `screen` | Älterer Terminal-Multiplexer mit ähnlicher Aufgabe. |
| `ssh`, `mosh` | Fernzugang, oft mit tmux kombiniert. |
| `nohup`, `setsid` | Hintergrundprozesse ohne Wiederanhängen. |
| `script` | Zeichnet eine Terminalsitzung auf. |

Ausgangseintrag: Datensatz 134 in `index.json` (`tmux`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch das Sitzungsmodell, Tastenbelegung, Sitzungsbefehle, Konfigurationsorte und einen Ablauf zum Abkoppeln ersetzt.
