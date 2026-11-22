---
id: "updatedb"
name: "updatedb"
command: "updatedb"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["suche", "datenbank", "dateinamen", "plocate"]
status: "Korrigiert; Quellen und Shellsyntax geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 205
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft: updatedb und plocate fehlen"
---

# updatedb – Eine begrenzte Dateinamen-Datenbank aufbauen und abfragen

## 1. Kurzbeschreibung

`updatedb` erstellt oder aktualisiert einen Index von Dateinamen für eine spätere Suche mit `locate` beziehungsweise `plocate`. Diese Dokumentation beschreibt ausdrücklich **die plocate-Implementierung**. Andere Programme gleichen Namens können andere Optionen und Datenbankformate verwenden.

**Für eine private Datenbank eigener zugänglicher Dateien ist Root nicht nötig.** Der Dokumentkopf bezieht sich auf diese Verwendung. Der systemweite Standardlauf ist dagegen eine Verwaltungsaufgabe mit entsprechendem Rechtebedarf und gehört nicht zur Übung.

## 2. Was macht der Befehl?

Das Programm erfasst Pfade, nicht den Textinhalt der Dateien. Ein vorhandener Index kann zum Einsparen erneuter Verzeichniszugriffe verwendet werden. Zwischen Aufbau und Suche kann sich der Bestand verändern: Neue Namen fehlen, entfernte können noch erscheinen.

Die drei gelesenen Primärquellen ergänzen sich: [updatedb aus plocate](https://manpages.debian.org/trixie/plocate/updatedb.8.en.html) beschreibt Aufbau und private Datenbanken, [updatedb.conf](https://manpages.debian.org/trixie/plocate/updatedb.conf.5.en.html) erklärt Ausschlüsse, [plocate](https://manpages.debian.org/trixie/plocate/plocate.1.en.html) beschreibt Suche und ausdrückliche Datenbankwahl. Die Webseiten stammen aus Debian plocate 1.1.23; das ist keine lokal geprüfte Version.

## 3. Syntax

```text
updatedb [OPTIONEN]
updatedb -U QUELLORDNER -o DATENBANK -l 0 [WEITERE_OPTIONEN]
plocate -d DATENBANK [SUCHOPTIONEN] MUSTER ...
```

Nicht ohne Begrenzung starten: Standardmäßig wird das ganze Dateisystem als Ausgangsbereich verwendet und die Standarddatenbank geschrieben. `-U` wählt den Quellbaum, `-o` die Ausgabedatei. Die Suche muss anschließend dieselbe Datenbank ausdrücklich über `-d` auswählen.

## 4. Wichtige Optionen

| Option bei plocate-updatedb | Bedeutung | Hinweis |
| --- | --- | --- |
| `-U PFAD`, `--database-root PFAD` | Nur den ausgewählten Teilbaum erfassen. | Kein Ersatz für restriktive Datenbankrechte. |
| `-o DATEI`, `--output DATEI` | Datenbank an diesem Ort schreiben. | Bestehende Datenbank kann aktualisiert oder ersetzt werden. |
| `-l 0`, `--require-visibility no` | Sichtbarkeitsprüfung für spätere Treffer deaktivieren. | Nur für die geschützte private Testdatenbank verwenden. |
| `-l 1` | Sichtbarkeitsprüfung anfordern. | Kein allgemeiner Schutz für eine beliebig weitergegebene private DB; Besitzer und Rechte spielen mit. |
| `--prunepaths LISTE` | Ausgeschlossene Verzeichnispfade ersetzen. | Leerzeichengetrennte Liste; keine allgemeine Shell-Mustersprache. |
| `--prunefs LISTE`, `--prunenames LISTE` | Dateisystemtypen beziehungsweise Verzeichnisnamen ausschließen. | Leere Liste überschreibt die betreffende Vorgabe. |
| `--prune-bind-mounts no` | Bind-Mount-Ausschluss deaktivieren. | Hier nur innerhalb des eigenen begrenzten Testbaums. |
| `-e LISTE` | Zusätzliche Ausschlusspfade ergänzen. | Pfade mit Leerzeichen benötigen die dafür vorgesehene Einzelpfadoption. |
| `--debug-pruning` | Ausschlussentscheidungen diagnostizieren. | Kann Pfade in der Fehlerausgabe zeigen. |
| `-v`, `--version` | Pfade ausgeben beziehungsweise Version anzeigen. | `-v` und die Versionsoption nicht verwechseln. |

Bei der Suche hat `plocate -d` eine andere Aufgabe als `updatedb -o`. Mit `plocate -b` wird nur der letzte Namensbestandteil verglichen; die Ausgabe bleibt ein vollständiger Pfad. `-e` bei **plocate** prüft die Existenz eines Treffers zur Suchzeit und ist damit eine andere Option als `updatedb -e`.

## 5. Beispiel erklärt Schritt für Schritt

**Nicht praktisch geprüft:** Die benötigten Programme fehlen in dieser Arbeitsumgebung. Das folgende Beispiel wurde anhand der Quellen und mit `bash -n` auf Shellsyntax geprüft. Seine erwarteten Ergebnisse sind keine gemessenen Ergebnisse.

Voraussetzungen für eine spätere Ausführung: Bash, ausdrücklich plocate mit dessen `updatedb`, ein normaler Benutzer und ein beschreibbarer temporärer Bereich. Alle Schritte in derselben Shell ausführen; bei einem Fehler stoppen.

### Schritt 1: Programme identifizieren und private Testdaten anlegen

```bash
command -v updatedb >/dev/null || exit 1
command -v plocate >/dev/null || exit 1
updatedb --version
plocate --version
uebung="$(mktemp -d -t netmon-updatedb-XXXXXX)" || exit 1
chmod 700 -- "$uebung" || exit 1
mkdir -- "$uebung/quelle" || exit 1
printf '%s\n' 'Eigene Testnotiz' > "$uebung/quelle/notiz.txt" || exit 1
```

Vor dem nächsten Schritt müssen die Versionsausgaben tatsächlich zu plocate gehören. Der neue Ordner ist nur für den eigenen Benutzer zugänglich. Er enthält eine einzige eigene Testnotiz; keine fremden oder realen Projektpfade werden indiziert.

### Schritt 2: Index ausschließlich für diesen Quellbaum erstellen

```bash
updatedb -l 0 -U "$uebung/quelle" -o "$uebung/test.db" \
  --prunefs '' --prunenames '' --prunepaths '' \
  --prune-bind-mounts no || exit 1
chmod 600 -- "$uebung/test.db" || exit 1
ls -l -- "$uebung/test.db"
```

Erwartet wird eine Datenbankdatei im privaten Ordner. Die leeren Ausschlusslisten verhindern, dass lokale Regeln etwa für temporäre Pfade die kleine Übung ausblenden. Sie ändern keine Systemkonfiguration und gelten nur für diesen Aufruf. Ihre Verwendung ist hier an den ausdrücklich angegebenen eigenen `-U`-Teilbaum gebunden.

`-l 0` macht den Inhalt nicht geheim. Wer die Datenbank lesen kann, kann ihre gespeicherten Namen ermitteln. Deshalb schützen Verzeichnis- und Dateirechte die private Übung; eine solche Datenbank nicht veröffentlichen.

### Schritt 3: Genau die eigene Datenbank durchsuchen

```bash
LOCATE_PATH= plocate -d "$uebung/test.db" -b -- notiz.txt
LOCATE_PATH= plocate -d "$uebung/test.db" -e -b -- notiz.txt
```

`-d` ersetzt die Standarddatenbank. Das für diesen Aufruf leere `LOCATE_PATH` verhindert zusätzlich durch diese Umgebungsvariable ergänzte Datenbanken. Erwartet wird jeweils genau der absolute Pfad zur eigenen `quelle/notiz.txt`, beispielsweise `/tmp/netmon-updatedb-ABC123/quelle/notiz.txt`; der tatsächliche Temporärpfad kann anders aussehen.

Der zweite Aufruf kontrolliert zusätzlich, ob der gespeicherte Pfad noch existiert. Er entdeckt keine neuen, noch nicht indizierten Namen. Bei fehlenden Treffern oder einem Fehler beendet sich plocate mit Status 1; Status 0 bedeutet einen Treffer oder einen erfolgreichen Hilfe-/Versionsaufruf. Der Übungsordner bleibt erhalten.

## 6. Typische Anwendungsfälle

**Viele Namenssuchen:** Ein Index beschleunigt wiederholte Suchen in einem weitgehend stabilen Bestand. Für aktuelle Inhalte oder neu angelegte Dateien kann eine direkte Suche passender sein.

**Eigener Projektindex:** Quelle und Datenbank bewusst begrenzen. Eine private Datenbank ist nicht automatisch mit dem Systemindex verbunden; sie muss bei der Suche ausgewählt werden.

**Fehlende Treffer erklären:** Aktualität, Ausschlussregeln und Zugriffsrechte getrennt prüfen. Nicht als erste Reaktion einen vollständigen Systemscan starten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Indexaufbau verursacht Lesezugriffe, I/O und eine schreibende Datenbankaktualisierung. Dateinamen können bereits vertraulich sein. Ein Index ist weder Inhaltsbackup noch Existenzgarantie und kann einen veralteten Bestand offenlegen.

Systemweite Timer und Standarddatenbanken werden hier nicht verändert. `sudo` ist für die private Übung unnötig. Ein größeres eigenes Verzeichnis kann ebenfalls viel Aufwand erzeugen; mit dem winzigen Testbaum beginnen.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Programm oder Option fehlt | Andere oder keine Implementierung. | Version und passende Manpage prüfen; nicht blind Optionen übernehmen. |
| Neue Testdatei fehlt | Alter Index oder Ausschlussregel. | Eigene Quelle, Aufbau und Pruning-Ausgabe prüfen. |
| Fremde Treffer erscheinen | Falsche DB oder ergänztes `LOCATE_PATH`. | `-d` und Umgebung ausdrücklich setzen. |
| Treffer existiert nicht mehr | Index enthält einen älteren Pfad. | `plocate -e` und gegebenenfalls direkte Suche verwenden. |
| Datenbank unlesbar | Pfad oder Rechte passen nicht. | Private Zugänglichkeit unter derselben Benutzerkennung prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für eine einmalige aktuelle Suche in einem kleinen eigenen Ordner kann `find` einen Index überflüssig machen. Datenbank und Quellbaum getrennt anlegen; die Datenbank nicht in den indizierten Quellordner schreiben.

**Prüfstand am 2026-11-13:** Die drei verlinkten plocate-Handbücher gelesen; Verfügbarkeit geprüft: `updatedb`, `locate` und `plocate` fehlen. Keine Installation durchgeführt. Bashsyntax des vollständigen Beispiels geprüft. **Nicht praktisch geprüft:** Indexaufbau, Abfrage und alle erwarteten Ausgaben; praktische Prüfung offen. Es gibt keine lokal bestätigte plocate-Version.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `plocate`, `locate` | Gespeicherte Dateinamen durchsuchen; Implementierung beachten. |
| `find` | Den aktuellen Dateibaum direkt durchsuchen. |
| `stat` | Eigenschaften eines gefundenen Pfads kontrollieren. |
| `chmod` | Rechte der eigenen Datenbank und ihres Ordners begrenzen. |

Ausgangsdatensatz 205 und Zuordnung sind gegen den eingefrorenen Katalog und die Original-CSV geprüft. Diese Quellen wurden nicht verändert.
