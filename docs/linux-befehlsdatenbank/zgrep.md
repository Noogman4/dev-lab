---
id: "zgrep"
name: "zgrep"
command: "zgrep"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "safe"
tags: ["archive & kompression", "zgrep"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 24
reviewed_at: "2026-11-13"
locally_checked_version: "zgrep aus GNU gzip 1.12; GNU grep"
---

# zgrep – Text in komprimierten Dateien suchen

## 1. Kurzbeschreibung

`zgrep` sucht nach Textmustern in unterstützten komprimierten und unkomprimierten Dateien. Es kombiniert die vorbereitende Dekompression mit einer Suche durch `grep`.

**Für eigene lesbare Dateien sind keine Root-Rechte nötig.** Die normalen Suchaufrufe verändern die Quellen nicht. Treffer können vertrauliche Inhalte offenlegen; Umleitungen speichern sie gegebenenfalls in einer weiteren Datei.

## 2. Was macht der Befehl?

Die Suchregeln stammen von `grep`. Standardmäßig werden Muster als reguläre Ausdrücke behandelt. Mit `-F` werden sie stattdessen als feste Zeichenfolgen gesucht. Für einen bekannten Suchtext ist diese zweite Arbeitsweise oft verständlicher.

Ein Treffer bezieht sich auf den entpackten Inhalt. Angezeigte Zeilennummern zählen deshalb dessen Textzeilen, nicht Positionen in der komprimierten Datei. Normale unkomprimierte Dateien werden ebenfalls verarbeitet; eine erfolgreiche Suche beweist daher nicht, dass eine gültige gzip-Datei vorlag.

Grundlagen: [Distributions-Manpage zu zgrep](https://manpages.debian.org/trixie/gzip/zgrep.1.en.html), lokale `zgrep --help` und `grep --help`. Nicht sämtliche Optionen des vollständigen `grep` werden vom Wrapper unterstützt.

## 3. Syntax

```text
zgrep [OPTIONEN] [-e] MUSTER [DATEI ...]
```

```bash
zgrep -n -F -e 'Fehler' "probe.log.gz"
zgrep -n -i -F -e 'fehler' "probe.log.gz"
```

Anführungszeichen erhalten Leerzeichen und Sonderzeichen des Musters vor der Shell. `-e` macht eindeutig, dass das folgende Argument ein Muster ist, auch wenn es mit einem Bindestrich beginnt. Ohne Datei wird stdin verarbeitet.

## 4. Wichtige Optionen

| Option | Wirkung | Konkreter Hinweis |
| --- | --- | --- |
| `-F` | Feste Zeichenfolge suchen. | Punkt und Stern sind dadurch keine Regex-Operatoren. |
| `-E` | Erweiterte reguläre Ausdrücke. | Andere Mustersprache als feste Zeichenfolgen. |
| `-e MUSTER` | Muster ausdrücklich übergeben. | Mehrfach für mehrere Suchmuster möglich. |
| `-i` | Groß-/Kleinschreibung ignorieren. | Verhalten hängt auch von Zeichensatz und Locale ab. |
| `-n` | Zeilennummer ausgeben. | Bezieht sich auf den entpackten Text. |
| `-c` | Anzahl passender Zeilen ausgeben. | Nicht Anzahl aller einzelnen Vorkommen. |
| `-l` | Nur Namen von Dateien mit Treffern ausgeben. | Nicht deren vollständige Inhalte. |
| `-v` | Nicht passende Zeilen auswählen. | Kehrt die Auswahl um. |
| `-A N`, `-B N`, `-C N` | Kontext nach, vor oder beidseitig anzeigen. | Kann zusätzliche vertrauliche Zeilen zeigen. |
| `-q` | Normale Ausgabe unterdrücken. | Erfolg nur als Status; kein vollständiger Archivtest. |

Rekursive Suchoptionen `-r` und `-R`, `--include`, `--exclude`, `-Z` und `-z` gehören zu den in der Wrapper-Hilfe ausgeschlossenen Funktionen. Nicht ungeprüft normale grep-Verzeichnisrezepte auf zgrep übertragen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Arbeitsort vorbereiten

```bash
zgrep --version
uebung="$(mktemp -d -t netmon-zgrep-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Wechsel fortfahren.

### Schritt 2: Bekannten Text erzeugen und komprimieren

```bash
printf '%s\n' 'Info: Start' 'FEHLER: Probe' 'Info: Ende' > "probe.log"
gzip -k "probe.log"
```

Die Originaldatei bleibt erhalten. Es handelt sich ausschließlich um selbst geschriebene Übungszeilen.

### Schritt 3: Fehlermeldung finden

```bash
zgrep -n -i -F -e 'fehler' "probe.log.gz"
```

Erwartet wird `2:FEHLER: Probe`. `-i` findet die großgeschriebene Variante, `-n` zeigt die zweite Textzeile, `-F` behandelt den Suchtext wörtlich.

### Schritt 4: Passende Zeilen zählen

```bash
zgrep -c -F -e 'Info' "probe.log.gz"
```

Die Testdatei enthält zwei passende Zeilen. Mehrere gleiche Vorkommen in nur einer Zeile würden weiterhin nur eine passende Zeile ergeben.

### Schritt 5: Fehlenden Text unterscheiden

```bash
zgrep -F -e 'fehlt' "probe.log.gz"
printf 'Abschlussstatus: %s\n' "$?"
```

Unmittelbar danach wird `1` erwartet: kein Treffer. Ein technisches Problem ist ein anderer Zustand und darf nicht als „Text fehlt sicher“ behandelt werden.

## 6. Typische Anwendungsfälle

**Archivierte Protokolle durchsuchen:** Einzelne passende komprimierte Dateien ausdrücklich auswählen, statt einen großen Verzeichnisbaum unkontrolliert einzubeziehen.

**Festen Fehlercode finden:** Mit `-F -e` einen wörtlichen Code suchen. Für mehrere Varianten können mehrere Muster oder bewusst entwickelte reguläre Ausdrücke sinnvoll sein.

**Trefferdateien bestimmen:** `-l` zeigt, welche Eingaben passende Zeilen besitzen. Der Name allein ist keine maschinell sichere Trennung für beliebige Sonderzeichen in Dateinamen.

**Kontext beurteilen:** Wenige Nachbarzeilen erleichtern die Einordnung einer Meldung. Vor dem Teilen prüfen, ob dort personenbezogene Daten oder Schlüssel stehen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Muster können anders verstanden werden als erwartet

Ohne `-F` ist etwa ein Punkt ein Regex-Zeichen. Ein zu breites Muster kann viele irrelevante Treffer erzeugen; ein zu enges kann wichtige Varianten übersehen. Unterschiedliche Schreibweisen und Locale bewusst berücksichtigen.

### Sucherfolg ist keine vollständige Prüfung

Ein Treffer bestätigt eine ausgewählte Zeile. Er bestätigt weder vollständige Dateiintegrität noch vertrauenswürdige Herkunft. Insbesondere frühes Beenden beziehungsweise stille Suche kann andere Prüfziele nicht ersetzen. Für gzip-Integrität separat `gzip -t` verwenden.

### Vertrauliche Ausgabe und Ressourcen

Treffer und Kontext können Zugangsdaten oder private Inhalte zeigen. Eine Umleitung schreibt diese in eine neue Datei und kann ein bestehendes Ziel überschreiben. Große entpackte Texte benötigen Rechenzeit; stdout und lesender Zugriff bilden keine Ressourcenbegrenzung.

### Aufgerufenes Suchprogramm

Der Wrapper kann das verwendete grep über seine Umgebung beeinflussen lassen. Für Diagnose die lokale Implementierung und Umgebung prüfen. Diese Dokumentation verändert keine solchen Vorgaben und gibt keine zusätzlichen Ausführungsrechte frei.

**Root-Rechte sind für die eigenen Testdateien unnötig.** Fehlende Zugriffsrechte sollten zuerst Anlass sein, den ausgewählten Pfad zu prüfen.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Kein Treffer | Andere Schreibweise, falsches Muster oder falsche Datei. | Mit bekanntem Text und `-F` beginnen. |
| Status `1` | Keine passende Zeile gefunden. | Von technischem Fehler unterscheiden. |
| Status `2` | Lese-, Dekompressions- oder Suchproblem. | Genaue Meldung prüfen. |
| Viel zu viele Treffer | Regex statt wörtlichem Muster. | Bei Bedarf `-F` verwenden. |
| Rekursion wird abgelehnt | Option vom Wrapper nicht unterstützt. | Dateiauswahl separat planen. |
| Zahl kleiner als erwartet | `-c` zählt Zeilen, keine Einzelvorkommen. | Gewünschte Zähleinheit klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit `-F -e` und einer bekannten kurzen Datei anfangen.
2. `-n` zur nachvollziehbaren Fundstelle ergänzen.
3. Fehlenden Treffer und Ausführungsfehler unterscheiden.
4. Nur nötige Kontextzeilen ausgeben.
5. Vertrauliche Inhalte vor dem Weitergeben entfernen.
6. Formatprüfung getrennt von Textsuche durchführen.

**Prüfstand:** GNU-gzip-Wrapper 1.12 wurde mit einer eigenen gzip-Datei und derselben unkomprimierten Textdatei geprüft. Feste Suche mit Groß-/Kleinschreibungsignorierung und Zeilennummer, Zeilenzählung sowie fehlender Treffer lieferten die erwarteten Inhalte und Statuswerte. Große Dateien, beschädigte Eingaben und alternative grep-Programme wurden nicht praktisch geprüft.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `grep` | Suchprogramm für bereits zugängliche Textdaten. |
| `zcat` | Gibt den gesamten entpackten Strom aus. |
| `zless` | Interaktive Anzeige unterstützter komprimierter Inhalte. |
| `gzip -t` | Datenprüfung ohne Textsuche. |
| `xzgrep`, `bzgrep` | Ähnliche Wrapper für andere Kompressionsfamilien. |

Ausgangseintrag: Datensatz 24 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
