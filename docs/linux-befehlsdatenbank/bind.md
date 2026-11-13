---
id: "bind"
name: "bind"
command: "bind"
category: "Bash Builtins"
language: "de"
root_required: false
risk_level: "caution"
tags: ["bash builtins", "bind"]
status: "Lokale Primärhilfe geprüft; lesende Readline-Abfragen in isolierter Bash geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 71
reviewed_at: "2026-11-13"
locally_checked_version: "GNU Bash 5.2.21"
---

# bind – Tastenkürzel der Bash-Eingabezeile anzeigen und anpassen

## 1. Kurzbeschreibung

`bind` ist ein eingebauter Bash-Befehl zur Steuerung von Readline, also der interaktiven Bearbeitung der Eingabezeile. Er kann Belegungen anzeigen und Tastenkombinationen mit Bearbeitungsfunktionen, Textmakros oder Shellbefehlen verbinden. **Root ist dafür nicht nötig.**

Gemeint ist nicht das DNS-Serverprodukt BIND und nicht das Binden eines Netzwerksockets. Ein pauschaler Hilfetext über ein externes Linux-Programm wäre für diesen Eintrag falsch.

## 2. Was macht der Befehl?

Eine Taste kann beispielsweise den Cursor an den Zeilenanfang setzen. Readline verwaltet solche Zuordnungen in Keymaps. Emacs- und Vi-Eingabemodus verwenden unterschiedliche Zuordnungen. Ein Bind-Aufruf verändert gegebenenfalls nur die laufende Shell; dauerhafte Einstellungen gehören in eine gesondert bewusst bearbeitete Konfiguration.

Primärquelle für die hier geprüfte Installation ist `help bind` in Bash 5.2.21. Die ergänzende [Distributionsreferenz](https://manpages.debian.org/trixie/bash/bash-builtins.7.en.html) beschreibt denselben Builtin. Die Eingabezeichenfolge muss als einzelnes Shellargument übergeben werden, damit Anführungszeichen und Backslashes nicht unbeabsichtigt anders ausgewertet werden.

## 3. Syntax

```text
bind -q READLINE_FUNKTION
bind -p
bind -m KEYMAP 'TASTENFOLGE: READLINE_FUNKTION'
```

Die Schlüsselwörter in Großbuchstaben sind Platzhalter. Readline-Funktionsnamen wie `beginning-of-line` sind keine separat installierten Programme. Ein Shellkommando wird nur bei der besonderen `-x`-Variante gebunden.

## 4. Wichtige Optionen

| Option | Bedeutung | Wirkung |
| --- | --- | --- |
| `-l` | Namen der Readline-Funktionen auflisten. | Lesender Überblick. |
| `-q NAME` | Zugeordnete Tasten einer Funktion abfragen. | Ausgabe kann je Keymap unterschiedlich sein. |
| `-p` | Funktionsbelegungen wieder einlesbar ausgeben. | Ausgabe nicht ungeprüft als Code übernehmen. |
| `-P` | Funktionsbelegungen beschreibend anzeigen. | Nicht mit kleinem `-p` verwechseln. |
| `-m KEYMAP` | Keymap für diesen Aufruf wählen. | Ändert den betrachteten Kontext. |
| `-r FOLGE` | Eine Tastenbelegung entfernen. | Kann gewohnte Bedienung stören. |
| `-f DATEI` | Readline-Konfiguration einlesen. | Nur eigene geprüfte Inhalte verwenden. |
| `-x FOLGE:BEFEHL` | Shellbefehl an Tastenkombination binden. | Tastendruck kann dann echte Aktionen auslösen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine getrennte Testshell verwenden

In einem Terminal folgende eigene Bash starten. Sie liest keine normalen Startdateien und verwendet für Readline keine persönliche `.inputrc`:

```bash
INPUTRC=/dev/null bash --noprofile --norc -i
```

Damit wirkt eine spätere Änderung nur in dieser zusätzlichen Shell. Es wird keine Konfigurationsdatei überschrieben. Eine interaktive Shell ist wichtig, weil Readline im normalen Skriptbetrieb nicht wie eine interaktive Eingabezeile arbeitet.

### Schritt 2: Bestehende Funktionen abfragen

In der Testshell:

```bash
bind -q beginning-of-line
bind -q end-of-line
```

Die Ausgabe nennt die zugeordneten Tastensequenzen. In einer üblichen Emacs-Keymap gehören etwa Strg+A und Strg+E dazu; genaue Escape-Darstellung und weitere Sequenzen hängen von Umgebung und Version ab. Nicht jedes Terminal sendet für eine beschriftete Taste dieselben Zeichen.

### Schritt 3: Ergebnis einordnen und Sitzung beenden

Es wurde keine neue Belegung gesetzt. Du hast nur geprüft, welche Kombinationen die gewählten Funktionen aufrufen. Mit `exit` die zusätzliche Testshell verlassen; die ursprüngliche Shell läuft weiter. Eine vollständige Belegungsliste kann mit `bind -p` umfangreicher ausfallen und eigene früher konfigurierte Kommandos enthalten.

## 6. Typische Anwendungsfälle

### Unbekannte Tastenkürzel verstehen

Eine bestimmte Bearbeitungsfunktion mit `-q` nachschlagen, bevor dieselbe Aktion mehrfach an verschiedenen Tasten ausprobiert wird.

### Abweichende Eingabemodi untersuchen

Wenn Tastenkürzel zwischen Terminals unterschiedlich reagieren, Keymap, Eingabemodus und tatsächliche Tastensequenz getrennt betrachten. Eine abweichende Belegung ist nicht automatisch ein Defekt.

### Eigene Bedienung vorbereiten

Erst in einer zusätzlichen Shell testen. Eine dauerhafte Konfiguration danach als eigene bewusste Änderung planen; nicht aus einem einzelnen erfolgreichen Query darauf schließen, dass ein neues Mapping überall passt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Mit `-x` gebundene Befehle laufen beim Tastendruck unter deinen Benutzerrechten. Eine harmlos wirkende Tastenkonfiguration kann dadurch Dateien ändern oder Programme starten. Unbekannte Belegungsdateien nicht ungeprüft laden.

Ungünstige Zuordnungen können Eingabe und Bearbeitung erschweren. Listen eigener Shellbindungen können vertrauliche Befehlsargumente sichtbar machen. Die Änderung betrifft Shellbedienung, nicht automatisch globale Desktopkürzel. Für systemweite Tastaturverwaltung ist `bind` deshalb nicht das passende universelle Werkzeug.

## 8. Häufige Fehler

- **`bind` in einer anderen Shell aufgerufen:** Bash-Builtin und Shelltyp prüfen.
- **Warnung zu deaktivierter Zeilenbearbeitung:** Skriptbetrieb mit interaktivem Readline verwechselt.
- **Falsche Keymap:** Vi-/Emacs-Kontext berücksichtigen.
- **Anführungszeichen fehlen:** Shell verarbeitet die gewünschte Bindungszeichenfolge vor Readline.
- **Änderung nach Neustart weg:** Nur die laufende Shell wurde angepasst.

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit lesenden Abfragen beginnen, keine Standardtasten überschreiben und eine getrennte Shell verwenden. Shellausführung über `-x` erst einsetzen, wenn die spätere Wirkung jedes Tastendrucks verstanden ist.

**Prüfstand:** Bash 5.2.21 und lokale Hilfe geprüft. `beginning-of-line` und `end-of-line` in einer interaktiven Bash ohne persönliche Start-/Readline-Dateien abgefragt, Status 0. Keine Bindung gesetzt oder Konfiguration geschrieben. Tatsächliche Tastendrücke, Vi-Keymap und dauerhafte Einrichtung nicht praktisch geprüft.

## 10. Verwandte Befehle

- `help bind`: installierte Builtin-Hilfe.
- `set -o emacs`, `set -o vi`: Eingabemodus beeinflussen.
- `read`: Eingaben in Skripten lesen, anderer Einsatzbereich.
- `type bind`: Einordnung als Shell-Builtin prüfen.

Ausgangseintrag: Datensatz 71 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
