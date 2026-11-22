---
id: "cp"
name: "cp"
command: "cp"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "verzeichnisse", "kopieren"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 178
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# cp – Dateien und Ordner kopieren

## 1. Kurzbeschreibung

`cp` („copy“) kopiert Dateien und – mit `-r` oder `-a` – ganze Ordner. Die Quelle bleibt erhalten; am Ziel entsteht eine Kopie. **Vorhandene Zieldateien werden standardmäßig ohne Rückfrage überschrieben.**

**Root-Rechte sind nicht nötig,** solange du die Quelle lesen und im Ziel schreiben darfst. Für Systemdateien oder zum Erhalten fremder Eigentümer sind Root-Rechte nötig.

Grundlage ist die [Debian-Manpage zu cp](https://manpages.debian.org/trixie/coreutils/cp.1.en.html) (GNU coreutils 9.7) und die lokale Hilfe von coreutils 9.4.

## 2. Was macht der Befehl?

| Aufruf | Wirkung |
| --- | --- |
| `cp QUELLE ZIEL` | Datei kopieren; ein vorhandenes `ZIEL` wird ersetzt. |
| `cp QUELLE … ORDNER/` | Eine oder mehrere Dateien in einen vorhandenen Ordner kopieren. |
| `cp -r ORDNER ZIEL` | Ordner rekursiv kopieren. |
| `cp -a ORDNER ZIEL` | Wie `-r`, zusätzlich Rechte, Zeiten, Eigentümer (soweit erlaubt), Links und erweiterte Attribute erhalten. |

Bei **neu angelegten** normalen Zieldateien werden ohne `-a` oder `-p` die Quellrechte unter Berücksichtigung von umask beziehungsweise Default-ACL angewendet; Eigentümer ist normalerweise der Aufrufende, Zeiten werden neu gesetzt. Beim normalen Überschreiben einer **vorhandenen** Zieldatei bleiben deren Rechte und Eigentümer grundsätzlich erhalten. GNU `cp` folgt Quellsymlinks standardmäßig beim nichtrekursiven Kopieren; beim rekursiven Kopieren bleiben sie normalerweise Links. `-L`, `-P`, `-H` und `-a` können diese Auswahl verändern. Im Test entstand aus `cp link kopie1` eine normale Datei, aus `cp -P link kopie2` ein Link.

## 3. Syntax

```text
cp [OPTIONEN] QUELLE ZIEL
cp [OPTIONEN] QUELLE ... ORDNER
cp [OPTIONEN] -t ORDNER QUELLE ...
```

```bash
cp bericht.txt bericht-kopie.txt
cp -i *.jpg ~/Bilder/
cp -a projekt/ projekt-sicherung/
```

Das bisherige NetMon-Beispiel `cp --help` zeigt die Hilfe. Der Platzhalter `cp [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-i` | Vor dem Überschreiben fragen. | Ohne Eingabe (z. B. in Skripten) wird nicht überschrieben. |
| `--update=none` | Vorhandene Dateien nie überschreiben. | Ersatz für das veraltete `-n`. |
| `-n` | Vorhandene Dateien überspringen. | Laut Manpage veraltet; 9.4 warnt bei Verwendung. |
| `-u`, `--update` | Nur ersetzen, wenn die Quelle neuer ist. | Neuere Fassungen kennen `--update=none-fail`. |
| `-b`, `--backup[=numbered]` | Vorhandenes Ziel vorher sichern. | Im Test entstand `c.txt.~1~`. |
| `-r`, `-R` | Ordner rekursiv. | – |
| `-a`, `--archive` | `-dR --preserve=all`. | Für Sicherungen. |
| `-p` | Modus, Eigentümer, Zeiten erhalten. | – |
| `-P`, `-L` | Symlinks nicht folgen bzw. immer folgen. | – |
| `-v` | Jede Kopie melden. | – |
| `-t ORDNER` | Zielordner zuerst angeben. | Praktisch mit `xargs`. |
| `--reflink=auto` | Platzsparende Kopie auf Btrfs/XFS, falls möglich. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Den Unterschied zwischen Überschreiben, Rückfrage, Überspringen und Sicherung an eigenen Übungsdateien sehen.

### Schritt 1: Übungsdateien

```bash
uebung="$(mktemp -d -t netmon-cp-XXXXXX)" || exit 1
cd "$uebung" || exit 1
echo eins > a.txt
echo zwei > b.txt
echo drei > c.txt
```

### Schritt 2: Stilles Überschreiben

```bash
cp a.txt b.txt
cat b.txt
```

Ausgabe: `eins` – der alte Inhalt von `b.txt` ist ohne Nachfrage verloren.

### Schritt 3: Mit Rückfrage

```bash
cp -i a.txt c.txt
```

`cp` fragt `cp: overwrite 'c.txt'?`. Mit `n` bleibt `c.txt` unverändert.

### Schritt 4: Mit Sicherung

```bash
cp --backup=numbered a.txt c.txt
ls
```

Der alte Inhalt liegt jetzt in `c.txt.~1~`.

### Schritt 5: Ordner

```bash
mkdir q && echo x > q/x
cp q z
cp -r q z
```

Der erste Befehl scheitert mit `-r not specified; omitting directory 'q'`; der zweite kopiert den Ordner.

## 6. Typische Anwendungsfälle

- **Schnelle Sicherungskopie** vor dem Bearbeiten: `cp -p datei datei.bak`.
- **Ordner sichern** mit allen Eigenschaften: `cp -a`.
- **Dateien in einen Ordner sammeln:** `cp -t ziel/ *.pdf`.
- **Vorlagen übernehmen**, ohne Vorhandenes zu überschreiben: `cp -r --update=none vorlage/ projekt/`.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die ursprüngliche Einstufung „Grün – sicher lesend“ trifft nicht zu: `cp` überschreibt Dateien ohne Rückfrage. Der Kopf verwendet `caution`.

- **Überschreiben:** Ein vertauschtes Paar `cp neu alt` statt `cp alt neu` zerstört die neuere Datei.
- **Platzhalter mit einem Ordner am Ende:** Fehlt der Zielordner, kann `cp *.txt ziel` je nach Anzahl der Dateien scheitern oder eine Datei überschreiben.
- **Speicherplatz:** Große rekursive Kopien können das Ziel füllen.
- **Metadaten:** Ohne `-a` gehen Zeiten, Rechte, ACLs und Links verloren; Kopien können offener lesbar sein als das Original.
- **Symbolische Links:** Ohne `-P` landen Inhalte der Linkziele im Ziel – möglicherweise außerhalb des gedachten Bereichs.
- **Mit Root-Rechten** kann `cp` Systemdateien ersetzen.

## 8. Häufige Fehler

| Meldung | Ursache | Vorgehen |
| --- | --- | --- |
| `cp: -r not specified; omitting directory '…'` (Rückgabe 1) | Ordner ohne `-r` (im Test). | `-r` oder `-a`. |
| `cp: cannot create regular file '…/': Not a directory` (Rückgabe 1) | Zielordner existiert nicht (im Test). | Ordner anlegen. |
| `cp: warning: behavior of -n is non-portable …` | `-n` in coreutils 9.4 (im Test). | `--update=none`. |
| `cp: cannot open '…' for reading: Permission denied` | Keine Leserechte. | Rechte prüfen. **Prüfpunkt:** nicht ausgelöst. |
| `No space left on device` | Ziel voll. | `df -h`. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`cp -i`** oder `--update=none`, wenn Überschreiben nicht gewollt ist.
2. **`--backup=numbered`** als Sicherheitsnetz.
3. **Zielordner mit `/` am Ende** schreiben (`ziel/`), dann fällt ein fehlender Ordner auf.
4. **Für Sicherungen `cp -a`** oder `rsync -a`.
5. **Mit `-v`** sehen, was passiert.

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4 (Ubuntu 24.04-Basis); Debian-Manpage 9.7.
- **Tatsächlich ausgeführt** im Testordner: stilles Überschreiben, `-n` (Warnung, Ziel erhalten), `-i` ohne Eingabe (Rückgabe 1, Ziel erhalten), `--backup=numbered`, Ordner ohne und mit `-r`, `-a`, Symlink mit und ohne `-P`, fehlender Zielordner, `--update=none`.
- **Nicht geprüft:** `--reflink`, ACL-/xattr-Erhalt, Kopien mit Root-Rechten.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mv` | Verschieben statt kopieren. |
| `rsync` | Abgleich, auch über das Netz. |
| `install` | Kopieren mit Rechten und Besitz in einem Schritt. |
| `ln` | Verknüpfung statt Kopie. |
| `scp` | Kopieren über SSH. |

Ausgangseintrag: Datensatz 178 in `index.json` (`cp`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Überschreibregeln, Optionen zum Schutz vorhandener Dateien, Metadaten- und Link-Verhalten und einen geprüften Ablauf ersetzt. Die Risikostufe wurde auf „Vorsicht“ angehoben.
