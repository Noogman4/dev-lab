---
id: "basename"
name: "basename"
command: "basename"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "verzeichnisse", "pfade", "skripte"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 177
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# basename – Letzten Bestandteil eines Pfads ausgeben

## 1. Kurzbeschreibung

`basename` gibt den **letzten Teil eines Pfads** aus – meist den Dateinamen ohne vorangehende Ordner. Optional entfernt es zusätzlich eine Endung. Der Befehl arbeitet **nur mit Text**: Er prüft nicht, ob die Datei existiert, und verändert nichts.

**Root-Rechte sind nicht nötig.**

Grundlage ist die [Debian-Manpage zu basename](https://manpages.debian.org/trixie/coreutils/basename.1.en.html) (GNU coreutils).

## 2. Was macht der Befehl?

`basename PFAD` entfernt alles bis zum letzten `/` sowie abschließende Schrägstriche. Mit einer zweiten Angabe (`SUFFIX`) oder `-s` wird außerdem diese Endung entfernt, sofern sie vorhanden ist und nicht der ganze Name ist.

| Eingabe | Ausgabe (im Test) |
| --- | --- |
| `basename /usr/lib/datei.tar.gz` | `datei.tar.gz` |
| `basename /usr/lib/datei.tar.gz .gz` | `datei.tar` |
| `basename /usr/lib/` | `lib` |
| `basename /` | `/` |
| `basename ''` | leere Zeile |

## 3. Syntax

```text
basename NAME [SUFFIX]
basename OPTION... NAME...
```

```bash
basename /home/anna/bericht.pdf
basename /home/anna/bericht.pdf .pdf
basename -s .txt a.txt b.txt
```

Das bisherige NetMon-Beispiel `basename --help` zeigt die Hilfe. Der Platzhalter `basename [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-a`, `--multiple` | Mehrere Namen verarbeiten. | Jede Ausgabe auf eigener Zeile. |
| `-s SUFFIX`, `--suffix` | Endung entfernen; schließt `-a` ein. | Für viele Dateien gleicher Endung. |
| `-z`, `--zero` | Ausgaben mit Nullbyte statt Zeilenumbruch trennen. | Für Dateinamen mit Zeilenumbrüchen. |
| `--` | Ende der Optionen. | Für Namen, die mit `-` beginnen. |

Andere Implementierungen (POSIX, BusyBox) kennen oft nur `basename NAME [SUFFIX]`; `-a`, `-s` und `-z` sind GNU-Erweiterungen. **Prüfpunkt:** in anderen Implementierungen nicht geprüft.

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

In einem Skript aus einem vollständigen Pfad den Dateinamen und den Namen ohne Endung gewinnen.

### Schritt 1: Dateiname

```bash
pfad="/home/anna/Bilder/urlaub 2026.jpg"
name="$(basename "$pfad")"
echo "$name"
```

Ausgabe: `urlaub 2026.jpg`. Die Anführungszeichen sind wegen des Leerzeichens nötig.

### Schritt 2: Ohne Endung

```bash
stamm="$(basename "$pfad" .jpg)"
echo "$stamm"
```

Ausgabe: `urlaub 2026`.

### Schritt 3: Mehrere Namen

```bash
basename -s .txt a.txt b.txt
```

Ausgabe: `a` und `b` auf getrennten Zeilen.

## 6. Typische Anwendungsfälle

- **Skripte:** Ausgabedateien nach Eingabedateien benennen, etwa `"$(basename "$f" .wav).mp3"`.
- **Protokolle:** Nur den Dateinamen statt des langen Pfads ausgeben.
- **Schleifen** über `find`-Ergebnisse.

In Bash geht dasselbe ohne Zusatzprozess mit Parameter-Erweiterung: `${pfad##*/}` (Name) und `${name%.jpg}` (ohne Endung). **Prüfpunkt:** Unterschiede bei abschließenden Schrägstrichen beachten.

## 7. Risiken, Nebenwirkungen und Vorsicht

`basename` verändert nichts. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Fehlende Anführungszeichen** bei Pfaden mit Leerzeichen führen zu falschen Ergebnissen.
- **Namen mit führendem `-`** werden ohne `--` als Option gedeutet.
- **Keine Existenzprüfung:** Tippfehler im Pfad fallen nicht auf.
- **Endung nur einmal:** `basename x.tar.gz .gz` ergibt `x.tar`.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `basename: missing operand` (Rückgabe 1) | Kein Name angegeben (im Test). | Pfad angeben. |
| `basename: extra operand 'c'` | Mehr als zwei Argumente ohne `-a`/`-s` (im Test). | `-a` oder `-s` verwenden. |
| Nur Teil des Namens | Leerzeichen ohne Anführungszeichen. | `"$pfad"` verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **Variablen immer in Anführungszeichen.**
2. **`--` vor Namen,** die mit `-` beginnen könnten.
3. **In Bash** für viele Dateien die Parameter-Erweiterung nutzen.

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** alle Fälle aus der Tabelle in Abschnitt 2, `-s`, `-a`, `-z` (Nullbyte), fehlender Operand (Rückgabe 1).
- **Nicht geprüft:** andere Implementierungen. Zusätzlich geprüft: Beispiel aus Abschnitt 5 und `extra operand`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dirname` | Gibt den Ordnerteil eines Pfads aus. |
| `realpath`, `readlink -f` | Vollständige, aufgelöste Pfade. |
| `find` | Liefert Pfade, die man mit `basename` kürzt. |

Ausgangseintrag: Datensatz 177 in `index.json` (`basename`, Kategorie „Dateien & Verzeichnisse“, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Funktionsweise, geprüfte Beispiele, Optionen und Skripthinweise ersetzt.
