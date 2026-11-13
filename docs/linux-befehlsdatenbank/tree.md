---
id: "tree"
name: "tree"
command: "tree"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["verzeichnisse", "anzeige", "baumstruktur"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 202
reviewed_at: "2026-11-13"
locally_checked_version: "tree v2.1.1"
---

# tree – Verzeichnisbäume mit bewusster Tiefe anzeigen

## 1. Kurzbeschreibung

`tree` stellt Dateien und Verzeichnisse als eingerückten Baum dar. Ohne Pfad beginnt es im aktuellen Verzeichnis. **Für zugängliche eigene Verzeichnisse sind keine Root-Rechte nötig.** Die normale Terminalanzeige verändert keine Dateiinhalte; schreibende Ausgabeoptionen sind gesondert zu beachten.

## 2. Was macht der Befehl?

Das Programm liest Verzeichniseinträge rekursiv und zeigt ihre Beziehung zueinander. Die eingerückte Darstellung ist eine Übersicht, keine Sicherung und keine Inhaltsprüfung. Versteckte Namen mit führendem Punkt fehlen standardmäßig. Symbolische Links erscheinen mit ihrem Zielpfad; erst `-l` verfolgt verlinkte Verzeichnisse rekursiv.

Die Tiefe zählt ab dem angegebenen Startverzeichnis: Dessen direkte Kinder liegen auf Ebene 1, deren Kinder auf Ebene 2. Bei `Projekt/docs/info.txt` zeigt `-L 1` nur `docs`, während `-L 2` bereits `info.txt` erreicht.

Grundlage sind die gelesene [tree-Manpage bei Debian, Version 2.2.1](https://manpages.debian.org/trixie/tree/tree.1.en.html) und die lokale Projekt-Manpage zu 2.1.1. Die folgenden Kernfunktionen wurden mit 2.1.1 geprüft; neuere Spezialoptionen werden nicht vorausgesetzt.

## 3. Syntax

```text
tree [OPTIONEN] [--] [VERZEICHNIS ...]
```

Mehrere Startpfade sind möglich. `--` beendet die Optionsauswertung. Pfade mit Leerzeichen werden zitiert. Das Programm ist nicht auf jedem System installiert; `command -v tree` prüft die Verfügbarkeit, ohne etwas zu installieren.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Grenze |
| --- | --- | --- |
| `-L N` | Höchstens N Ebenen anzeigen. | Nicht mit einer Begrenzung der Dateianzahl verwechseln. |
| `-a` | Versteckte Namen einbeziehen. | `.` und `..` werden trotzdem nicht als Einträge aufgeführt. |
| `-d` | Nur Verzeichnisse anzeigen. | Dateien fehlen absichtlich. |
| `-P MUSTER` | Dateinamen nach Muster auswählen. | Versteckte Treffer brauchen zusätzlich `-a`; Verzeichnisse bleiben grundsätzlich sichtbar. |
| `-I MUSTER` | Passende Namen ausblenden. | Muster zitieren, damit die Shell sie nicht vorher expandiert. |
| `--prune` | Nach Filterung leere Verzeichniszweige auslassen. | Kann Speicherbedarf und Wartezeit erhöhen. |
| `-l` | Links auf Verzeichnisse verfolgen. | Kann Daten außerhalb des erwarteten Teilbaums zeigen. |
| `-x` | Auf dem aktuellen Dateisystem bleiben. | Kein Berechtigungs- oder Isolationsmechanismus. |
| `-f` | Pfadpräfixe anzeigen. | Bei absolutem Startpfad können persönliche Pfade sichtbar werden. |
| `-n`, `--noreport` | Farben beziehungsweise Abschlusszählung weglassen. | Für reproduzierbare Textausgabe hilfreich. |
| `-o DATEI` | Ausgabe in eine Datei schreiben. | Schreibender Aufruf; vorhandener Inhalt kann ersetzt werden. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, `tree`, GNU coreutils und ein beschreibbarer temporärer Bereich. Alle Schritte in derselben Shell ausführen; bei Fehlern abbrechen. Kein `sudo` verwenden.

### Schritt 1: Kleine eigene Struktur anlegen

```bash
uebung="$(mktemp -d -t netmon-tree-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
mkdir -p Projekt/docs Projekt/src || exit 1
printf '%s\n' 'Test' > Projekt/docs/info.txt || exit 1
printf '%s\n' 'Nur eine Übungsdatei' > Projekt/.intern || exit 1
```

Der neue Ordner enthält zwei Unterverzeichnisse, eine Textdatei und eine versteckte Datei. Die Übungsdatei `.intern` enthält keine echten Geheimnisse.

### Schritt 2: Erste Ebene ansehen

```bash
tree -n --noreport -L 1 -- Projekt
```

Erwartete Ausgabe, grafische Linien können je nach Terminal abweichen:

```text
Projekt
├── docs
└── src
```

Beide direkten Unterverzeichnisse sind sichtbar. `info.txt` ist ein Kind von `docs` und liegt damit außerhalb der gewählten ersten Ebene.

### Schritt 3: Zweite Ebene vergleichen

```bash
tree -n --noreport -L 2 -- Projekt
```

Jetzt lautet die Struktur:

```text
Projekt
├── docs
│   └── info.txt
└── src
```

Das ist die Korrektur des ursprünglichen Entwurfs: Die Datei erscheint bereits bei Tiefe 2, nicht erst bei 3. `.intern` bleibt ohne `-a` unsichtbar.

### Schritt 4: Versteckte Namen und Verzeichnisfilter prüfen

```bash
tree -n --noreport -a -L 2 -- Projekt
tree -n --noreport -d -L 2 -- Projekt
tree -n --noreport -L 2 -P '*.txt' -- Projekt
```

Der erste Aufruf zeigt zusätzlich `.intern`. Der zweite zeigt nur `docs` und `src`. Der dritte zeigt `info.txt`, aber weiterhin auch das leere Verzeichnis `src`: Ein Dateifilter entfernt Verzeichnisse nicht automatisch. Die einfachen Anführungszeichen geben das Muster unverändert an `tree` weiter.

## 6. Typische Anwendungsfälle

**Projektaufbau erklären:** Einen überschaubaren Teilbaum mit begrenzter Tiefe anzeigen und die Ausgabe vor dem Weitergeben auf private Namen prüfen.

**Ergebnis einer Ablage prüfen:** Nach dem Anlegen eigener Unterordner sehen, ob Dateien tatsächlich im vorgesehenen Zweig liegen. Inhalte und Vollständigkeit separat prüfen.

**Dateitypen überblicken:** Mit einem zitierten Namensmuster passende Endungen hervorheben. Eine Endung sagt noch nichts Verlässliches über den Inhalt aus.

## 7. Risiken, Nebenwirkungen und Vorsicht

`safe` bezieht sich auf die beschriebene Anzeige. `-o`, Shell-Umleitungen und die rekursive Ausgabeoption `-R` können Dateien schreiben. Diese Optionen sind für den gezeigten Überblick unnötig.

Große Bäume und Optionen wie `--prune` oder `--du` können viel Speicher und Laufzeit benötigen. Mit kleinen Startpfaden und geringer Tiefe beginnen. Die Abschlusszählung ist bei Filtern keine verlässliche Inventur; ausgeblendete oder nicht lesbare Einträge können fehlen. Eine laufend veränderte Struktur wird nicht als atomarer Schnappschuss gelesen.

`-a` und `-f` können vertrauliche Namen offenlegen. `-l` kann den sichtbaren Suchbereich erweitern. Keiner dieser Schalter erteilt Zugriffsrechte; Zugriffsfehler bewusst lesen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `tree` fehlt | Separates Programm nicht installiert. | Verfügbarkeit prüfen; alternativ `find` für eine andere Darstellungsform. |
| Datei fehlt im Baum | Tiefe, versteckter Name oder Filter. | Zuerst Tiefe und Optionen prüfen. |
| Leere Ordner bleiben bei `-P` sichtbar | Filter gilt nicht wie eine vollständige Zweigbereinigung. | Bei Bedarf `--prune` und dessen Aufwand beachten. |
| Muster verhält sich unerwartet | Shell expandierte es vor dem Aufruf. | Muster zitieren. |
| Zählung passt nicht zum Gesamtbestand | Filter, Rechte oder parallele Änderungen. | Keine Vollständigkeit aus der Zahl ableiten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den Startpfad ausdrücklich angeben, Linkverfolgung zunächst weglassen und Ansichten mit und ohne Filter vergleichen. Die Datei mit der Ausgabe außerhalb des untersuchten Baums ablegen, falls später bewusst ein Bericht geschrieben wird.

**Prüfstand am 2026-11-13:** `tree v2.1.1`; lokale Manpage und verlinkte Debian-Manpage gelesen. Alle Schritte aus Abschnitt 5 wurden mit eigenen temporären Daten ausgeführt. Ebene 1 ohne `info.txt`, Ebene 2 mit `info.txt`, versteckte Namen, Verzeichnisansicht und zitierter Textfilter entsprachen den Beschreibungen.

**Nicht praktisch geprüft:** `-l`, Dateisystemgrenzen mit `-x`, Ausgabedateien, riesige Bäume und Version 2.2.1. Keine Paketinstallation.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `find` | Rekursive Suche mit ausdrücklichen Auswahlbedingungen. |
| `ls` | Verzeichnisinhalte ohne standardmäßige Rekursion anzeigen. |
| `du` | Speicherbelegung untersuchen statt nur Namen darzustellen. |
| `stat` | Metadaten eines einzelnen Pfads untersuchen. |

Ausgangsdatensatz 202, Kategorie und Dateizuordnung wurden mit eingefrorenem Katalog und Original-CSV abgeglichen; deren Felder bleiben unverändert.
