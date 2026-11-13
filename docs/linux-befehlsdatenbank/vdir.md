---
id: "vdir"
name: "vdir"
command: "vdir"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "verzeichnisse", "metadaten", "anzeige"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 206
reviewed_at: "2026-11-13"
locally_checked_version: "vdir (GNU coreutils) 9.4"
---

# vdir – Lange Dateilisten und ihre Felder verstehen

## 1. Kurzbeschreibung

GNU `vdir` zeigt Verzeichnisinhalte standardmäßig als lange Liste mit Rechten, Eigentümer, Größe und Zeitstempel. Es entspricht in seinen Vorgaben `ls -l -b`: Nichtgrafische Zeichen werden mit Rückstrichsequenzen dargestellt. **Für zugängliche eigene Pfade ist Root nicht erforderlich.** Der normale Anzeigeaufruf ist lesend.

## 2. Was macht der Befehl?

Ohne Operand wird das aktuelle Verzeichnis gelistet. Ein Verzeichnisoperand zeigt normalerweise dessen Inhalt; `-d` zeigt stattdessen den Verzeichniseintrag selbst. Ein Dateioperand zeigt diese Datei. Versteckte Namen fehlen ohne passende Option.

Die lange Zeile besteht üblicherweise aus Typ/Rechten, Hardlinkanzahl, Eigentümer, Gruppe, Größe, Änderungszeit und Name. Das erste Zeichen unterscheidet etwa `-` für reguläre Datei, `d` für Verzeichnis und `l` für symbolischen Link. Danach folgen die klassischen Rechte für Eigentümer, Gruppe und andere. Zusätzliche ACLs oder Sicherheitsregeln können die tatsächlichen Zugriffe weiter beeinflussen.

Die Standardgröße einer regulären Datei ist ihre logische Länge, nicht zwingend die belegte Speichermenge. Eine Kopfzeile `total` beziehungsweise `insgesamt` summiert belegte Blöcke der gelisteten Einträge, nicht einfach die sichtbaren Bytewerte. Verzeichnisgrößen sind keine rekursive Summe ihres Inhalts.

Gelesene Quellen: [GNU-vdir-Manpage bei Debian](https://manpages.debian.org/trixie/coreutils/vdir.1.en.html), lokale Manpage und lokales GNU-Info-Kapitel `vdir invocation` aus coreutils 9.4. Letzteres beschreibt ausdrücklich die Vorgaben `ls -l -b`.

## 3. Syntax

```text
vdir [OPTIONEN] [--] [DATEI_ODER_VERZEICHNIS ...]
```

`--` beendet die Optionsauswertung. Pfade zitieren, insbesondere bei Leerzeichen. `vdir` ist ein eigenes GNU-Programm; ein Shell-Alias für `ls` muss dieselben Einstellungen nicht teilen.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-a` | Auch Namen mit führendem Punkt anzeigen. | Einschließlich `.` und `..`. |
| `-A` | Versteckte Namen, aber ohne `.` und `..`. | Häufig übersichtlicher. |
| `-d` | Verzeichnisse selbst listen. | Keine Auflistung ihrer Kinder. |
| `-h` | Lesbare Größen in 1024er-Schritten. | Gerundet; kein exakter Bytevergleich. |
| `--si` | Lesbare Größen in 1000er-Schritten. | Andere Einheit als `-h`. |
| `--block-size=1` | Anzeigeeinheit ein Byte setzen. | Nützlich für exakte Größen ohne geerbte Größenskalierung. |
| `-n` | Numerische Benutzer- und Gruppenkennungen. | Vermeidet Namensauflösung für diese Felder. |
| `-t`, `-S` | Nach Zeit beziehungsweise Größe sortieren. | Standardmäßig neueste beziehungsweise größte zuerst. |
| `--time-style=long-iso` | Datum und Uhrzeit einheitlicher anzeigen. | Zeitzone bleibt gesondert relevant. |
| `-L` | Metadaten des Linkziels anzeigen. | Die sichtbare Zeile beschreibt dann nicht den Link selbst. |
| `-R` | Unterverzeichnisse rekursiv listen. | Kann sehr umfangreich werden. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und GNU coreutils. Alle Schritte in derselben Shell mit eigenen temporären Daten ausführen. Der Übungsordner bleibt zur Kontrolle erhalten.

### Schritt 1: Unterschiedliche Einträge anlegen

```bash
uebung="$(mktemp -d -t netmon-vdir-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir Projekt || exit 1
printf '%s\n' 'Test' > Projekt/datei.txt || exit 1
printf '%s\n' 'Verborgen' > Projekt/.intern || exit 1
ln -s datei.txt Projekt/link || exit 1
chmod 640 -- Projekt/datei.txt || exit 1
```

Die reguläre Datei enthält fünf Bytes einschließlich Zeilenumbruch. Modus `640` gibt dem Eigentümer Lese-/Schreibrecht, der Gruppe Leserecht und anderen keine Rechte. Diese Rechteänderung betrifft nur die neu angelegte Übungsdatei.

### Schritt 2: Die lange Liste lesen

```bash
LC_ALL=C vdir --block-size=1 --time-style=long-iso -- Projekt
```

Erwartet werden `datei.txt` und `link -> datei.txt`; `.intern` fehlt. Die Zeile der regulären Datei beginnt mit `-rw-r-----`, ihre Linkanzahl ist 1 und ihre Größe 5. Benutzername, Gruppe, Zeit und Blocksumme hängen von der lokalen Umgebung ab. Die Zeile des Links beginnt mit `l`; dessen Größenfeld beschreibt grundsätzlich den Linktext, nicht die Länge der Zieldatei.

### Schritt 3: Versteckte Namen und Verzeichnis selbst ansehen

```bash
LC_ALL=C vdir -A -n --block-size=1 -- Projekt
LC_ALL=C vdir -d -- Projekt
```

Der erste Aufruf enthält zusätzlich `.intern` und numerische Kennungen. Der zweite zeigt eine einzelne Zeile für `Projekt`, nicht nochmals dessen Inhalt. Das erste Zeichen ist hier `d`.

### Schritt 4: Link und Zielmetadaten unterscheiden

```bash
LC_ALL=C vdir --block-size=1 -- Projekt/link
LC_ALL=C vdir -L --block-size=1 -- Projekt/link
cat -- Projekt/datei.txt
```

Zuerst wird der symbolische Link mit Pfeil gezeigt. Mit `-L` erscheint unter demselben übergebenen Namen die reguläre Zieldatei mit Größe 5 und deren Rechten. Der abschließende Inhalt bleibt `Test`; die Liste hat ihn nicht umgeschrieben.

## 6. Typische Anwendungsfälle

**Rechteursachen eingrenzen:** Vor einer beabsichtigten Änderung Typ, Eigentümer und klassische Rechte ansehen. Aus der Anzeige allein folgt noch nicht, dass jede Operation erlaubt ist.

**Eigene Ablage prüfen:** Versteckte Einträge mit `-A` bewusst einbeziehen und Linkziele erkennen. Das ist keine Integritätsprüfung des Bestands.

**Größen sortieren:** Mit `-S` große reguläre Dateien sichtbar machen. Für Speicherverbrauch ganzer Verzeichnisbäume `du` verwenden; Verzeichnisgrößen in einer langen Liste beantworten eine andere Frage.

## 7. Risiken, Nebenwirkungen und Vorsicht

Der normale Aufruf schreibt keine Dateiinhalte oder Rechte. Shell-Umleitungen können dagegen eine Ausgabedatei erzeugen oder überschreiben. Bereits Dateinamen, Kennungen und Pfade können vertraulich sein; Listen vor dem Weitergeben prüfen.

`-L` ist kein Sicherheitstest eines Links. Rekursive Ansichten können lange laufen. Eine Liste ist außerdem eine Momentbeobachtung: Parallel können Dateien verändert oder ersetzt werden. Nicht aus einer alten Zeile auf einen unveränderten aktuellen Zustand schließen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Versteckter Eintrag fehlt | Standard blendet Punktnamen aus. | Gezielt `-A` verwenden. |
| Ordnerinhalt statt Ordnerzeile | `-d` fehlt. | Verzeichnis selbst mit `-d` wählen. |
| Größe passt nicht zu `du` | Länge und Belegung sind verschieden. | Messgröße unterscheiden. |
| Link sieht wie normale Datei aus | `-L` zeigt Zielmetadaten. | Ohne Dereferenzierung vergleichen. |
| Ausgabe eignet sich schlecht für ein Skript | Namen können Leerzeichen, Umbrüche und Escape-Darstellungen enthalten. | Keine lange Menschenleseliste als zuverlässiges Dateinamenprotokoll parsen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Kleine konkrete Pfade ohne Rekursion wählen. Optionen und Locale ausdrücklich setzen, wenn Ausgaben verglichen werden. Inhaltsgleichheit mit einem Inhaltsvergleich prüfen, nicht anhand gleicher Größe und Zeit vermuten.

**Prüfstand am 2026-11-13:** GNU `vdir` 9.4; lokale Manpage, GNU-Info und verlinkte Debian-Manpage gelesen. Abschnitt 5 vollständig ausgeführt: Fünf-Byte-Datei mit Modus 640, ausgeblendeter/eingeblendeter Punktname, numerische Kennungen, Verzeichniseintrag und `-L`-Unterschied bestätigt. Inhalt blieb erhalten.

**Nicht praktisch geprüft:** ACL-/Sicherheitskontexte, Rekursion, besondere Dateitypen, andere Locale-Konfigurationen und andere Implementierungen. Der Parser wurde separat strukturell geprüft; eine GUI-Anzeige ist damit nicht nachgewiesen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ls -l -b` | Entspricht den GNU-vdir-Vorgaben. |
| `stat` | Einzelne Metadaten genauer anzeigen. |
| `du` | Belegte Speicherblöcke untersuchen. |
| `tree` | Hierarchie statt langer flacher Liste darstellen. |

Ausgangsdatensatz 206 und Zuordnung wurden gegen Katalog und Original-CSV geprüft. Diese und das Entwurfsoriginal bleiben unverändert.
