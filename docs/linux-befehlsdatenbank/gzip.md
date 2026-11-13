---
id: "gzip"
name: "gzip"
command: "gzip"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "gzip"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 9
reviewed_at: "2026-11-13"
locally_checked_version: "GNU gzip 1.12"
---

# gzip – Dateien komprimieren, ohne Archivierung und Kompression zu verwechseln

## 1. Kurzbeschreibung

`gzip` komprimiert Daten im Gzip-Format. Bei einem normalen Dateiaufruf wird beispielsweise aus `notiz.txt` die Datei `notiz.txt.gz`. Mit `-d` arbeitet das Programm in der Gegenrichtung.

**Für eigene Dateien sind keine Root-Rechte erforderlich.** Nach erfolgreicher Dateikompression wird die unkomprimierte Eingabe normalerweise entfernt. Die Option `-k` erhält sie. Ein normaler schreibender Aufruf ist daher nicht „sicher lesend“.

## 2. Was macht der Befehl?

Gzip beschreibt einen komprimierten Datenstrom, nicht eine allgemeine Verzeichnisstruktur mit einzeln auswählbaren Mitgliedern. Mehrere Dateinamen im normalen Dateimodus ergeben entsprechend mehrere `.gz`-Dateien. Ein Ordnerbaum wird häufig zunächst mit `tar` gebündelt.

Ein Name wie `sammlung.tar.gz` steht typischerweise für eine TAR-Datei, die anschließend mit Gzip komprimiert wurde. Dass man diese Schritte kombinieren kann, macht sie nicht zu derselben Aufgabe.

Die komprimierten Daten enthalten zusätzliche Verwaltungs- und Integritätsinformationen. Kompression ist weder Verschlüsselung noch ein Beweis für die Herkunft der Datei. Kleine oder schon komprimierte Eingaben müssen dadurch nicht kleiner werden. Die [GNU-gzip-Manpage bei Debian](https://manpages.debian.org/trixie/gzip/gzip.1.en.html#DESCRIPTION) beschreibt diese Grundwirkungen.

## 3. Syntax

```text
gzip [OPTIONEN] [DATEI ...]
```

Die Absicht sollte aus den Optionen hervorgehen:

```bash
gzip -k "notiz.txt"
gzip -t "notiz.txt.gz"
gzip -dc "notiz.txt.gz"
```

Der erste Aufruf erzeugt eine komprimierte Kopie mit erhaltener Eingabe. Der zweite testet. Der dritte dekomprimiert auf stdout statt in eine abgeleitete Zieldatei.

Ohne Dateinamen beziehungsweise mit einer passenden Standardeingabe arbeitet `gzip` als Datenstromfilter. Für eine selbst gewählte Ausgabedatei benutzt man ausdrücklich stdout und eine Shell-Umleitung; eine frei erfundene universelle `-o`-Option gehört nicht zur hier verwendeten GNU-Syntax.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-k`, `--keep` | Eingabe behalten. | Für eine zusätzliche komprimierte Kopie besonders wichtig. |
| `-c`, `--stdout` | Ergebnis auf stdout schreiben. | Eingaben bleiben erhalten; die Shell verwaltet eine mögliche Umleitung. |
| `-d`, `--decompress` | Dekomprimieren. | Gegenrichtung zur normalen Kompression. |
| `-t`, `--test` | Integrität prüfen. | Keine wiederhergestellte Datei, kein Herkunftsnachweis. |
| `-1` bis `-9` | Kompressionsstufe wählen. | Niedrigere Stufen priorisieren üblicherweise Aufwand, höhere die Verdichtung; Ergebnis und Bedarf prüfen. |
| `-v`, `--verbose` | Zusätzliche Angaben ausgeben. | Besonders für den ersten Versuch hilfreich. |
| `-l`, `--list` | Größen- und Namensinformationen anzeigen. | Nicht mit der Mitgliederliste eines TAR- oder ZIP-Archivs gleichsetzen. |
| `-n`, `--no-name` | Ursprünglichen Namen und Zeitstempel nicht im üblichen Gzip-Header speichern. | Nützlich als Teil eines reproduzierbaren Datenablaufs. |
| `-f`, `--force` | Schutzprüfungen übergehen. | Kann eine bestehende Ausgabe ersetzen oder andere Standardprüfungen verändern. |
| `-r`, `--recursive` | Ordner rekursiv bearbeiten. | Erzeugt einzelne komprimierte Dateien und kann viele Eingaben ersetzen. |

Die [Optionsreferenz](https://manpages.debian.org/trixie/gzip/gzip.1.en.html#OPTIONS) und die lokale Hilfe müssen zur installierten Variante passen. Diese Dokumentation wurde mit GNU gzip 1.12 geprüft; bei anderen Implementierungen nicht alle Schalter ungeprüft voraussetzen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Neue Übungsdaten anlegen

```bash
uebung="$(mktemp -d -t netmon-gzip-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eigene Gzip-Uebungsdaten.' > "notiz.txt"
```

Prüfe vor dem Schreiben, dass der Wechsel in den neuen Ordner gelungen ist. Die Umleitung `>` würde eine vorhandene Datei gleichen Namens ersetzen; deshalb wird hier ein neuer Arbeitsort verwendet.

### Schritt 2: Komprimieren und das Original behalten

```bash
gzip -kv "notiz.txt"
```

`-k` erhält `notiz.txt`, `-v` zeigt zusätzliche Angaben. Das Ergebnis heißt `notiz.txt.gz`. Bei diesem kleinen Text kann der Verwaltungsaufwand des Formats die Einsparung überwiegen; eine größere Ergebnisdatei wäre deshalb nicht automatisch ein Fehler.

### Schritt 3: Komprimierte Daten prüfen

```bash
gzip -t "notiz.txt.gz"
```

Keine normale Ausgabe kann einen erfolgreichen Test bedeuten. Lies Meldungen und sieh unmittelbar danach mit `echo $?` den Rückgabewert an. Eine schon vorhandene `.gz`-Datei beweist nicht, dass ein neuer Aufruf erfolgreich war.

### Schritt 4: Den Inhalt zurücklesen

```bash
gzip -dc "notiz.txt.gz"
```

Die bekannte Testnotiz wird dekomprimiert auf stdout ausgegeben. Es wird nicht versucht, die weiterhin vorhandene `notiz.txt` zu ersetzen. Für unbekannte Binärinhalte ist die direkte Terminalausgabe nicht geeignet.

### Schritt 5: Eine zweite, bewusst benannte Ausgabe erstellen

```bash
gzip -nc "notiz.txt" > "ohne-namensangaben.gz"
```

`-n` beeinflusst die üblichen Namens- und Zeitangaben im Gzip-Header, `-c` liefert den komprimierten Datenstrom. Die Shell schreibt ihn unter dem neuen Namen. Das allein macht noch keinen vollständigen reproduzierbaren Build: Inhalt, Optionen, Werkzeugversion und übriger Ablauf müssen ebenfalls passen.

## 6. Typische Anwendungsfälle

**Textdaten zusätzlich komprimiert aufbewahren:** Mit `-k` bleibt eine direkt lesbare Kopie erhalten. Wie viel Platz tatsächlich gewonnen wird, hängt von den Eingaben ab.

**Daten in einer Pipe komprimieren:** Ein Programm kann Text oder Binärdaten an `gzip -c` liefern. Die empfangende Stelle muss wissen, dass sie Gzip-Daten statt unkomprimiertem Text bekommt.

**Ein vorhandenes TAR-Archiv komprimieren:** Das TAR-Archiv trägt die Mitgliederstruktur; Gzip verarbeitet dessen Datenstrom. Für einen echten Backup-Ablauf müssen Erfassung und Rückspielen beider Schichten geeignet sein.

**Zeit- und Namensunterschiede im Header vermeiden:** `-n` kann für verteilte oder reproduzierbare Artefakte sinnvoll sein. Diese Wirkung ist von einer inhaltlichen Anonymisierung zu unterscheiden: Private Angaben innerhalb der Datei bleiben enthalten.

**Eine Gzip-Datei ohne separate unkomprimierte Zwischenkopie prüfen:** `-t` und eine gezielte Datenstromausgabe bieten dafür unterschiedliche Möglichkeiten. Nur die erste ist ausdrücklich als Integritätstest gedacht.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Die Eingabe wird normalerweise ersetzt

Eine erfolgreiche Dateikompression entfernt das unkomprimierte Original, sofern nicht `-k` oder eine andere passende Arbeitsweise gewählt wurde. Nach Dekompression gilt die entsprechende Wirkung für die komprimierte Eingabe. Die Richtung allein entscheidet nicht über den Originalerhalt.

### Ausgabe wird durch die Shell geöffnet

Bei `gzip -c quelle > ziel.gz` kann die Shell ein vorhandenes Ziel bereits leeren, bevor die Kompression erfolgreich läuft. Eingabe und Ausgabe niemals gleich benennen oder auf denselben Pfad beziehen. Die Shell-Umleitung kennt die Absicht von `gzip` nicht.

### Kompression ersetzt keinen Snapshot

Eine während des Lesens veränderte Eingabe ist keine verlässlich eingefrorene Datensicherung. Laufende Datenbanken, wichtige veränderliche Dateien und Systemzustände brauchen einen passenden Export- oder Sicherungsablauf. Einfaches Komprimieren beweist keine Anwendungskonsistenz.

### Vertraulichkeit und Ressourcen

Gzip verschlüsselt nicht. Auch ein mit `-n` erzeugter Header entfernt keine Geheimnisse aus dem eigentlichen Inhalt. Fremde komprimierte Daten können außerdem unerwartet große Ausgaben und hohen Verarbeitungsaufwand verursachen.

### Rekursion und Erzwingen

`-r` erweitert die betroffene Dateimenge. `-f` verändert Schutzverhalten. Beide Schalter gehören nicht in einen vorsichtigen ersten Versuch mit unbekannten Pfaden. Warnungen dürfen nicht allein deshalb unterdrückt werden, weil bereits eine Ausgabedatei sichtbar ist.

**Root ist für die Übungsbefehle nicht erforderlich.** Bei Systempfaden zuerst Berechtigung und Zweck klären.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Ausgabe existiert schon | Ergebnis eines früheren Laufs. | Vorhandene Datei prüfen oder neuen Namen wählen. |
| Eingabe nach Erfolg verschwunden | Normaler Dateimodus ohne `-k`. | Gewünschten Originalerhalt künftig ausdrücklich setzen. |
| Datei wurde größer | Kleine oder bereits komprimierte Daten. | Inhalt und erwarteten Nutzen beurteilen, nicht blind höhere Stufen wählen. |
| Ordner wurde nicht zu einem Archiv gebündelt | `gzip` ist kein Verzeichnisarchivierer. | Für eine Sammlung zunächst ein geeignetes Archivformat wählen. |
| „file changed while ...“ | Eingabe wurde während des Vorgangs verändert. | Konsistente Quelle herstellen und Ausgabe nicht ungeprüft als Sicherung betrachten. |
| Integritätstest schlägt fehl | Beispielsweise Datenfehler oder unvollständige Übertragung. | Original erhalten und weitere Kopie beziehungsweise erneuten Download prüfen. |

GNU gzip meldet unter anderem `0` für Erfolg, `1` für Fehler und `2` für Warnungen. Fehlerstatus und Diagnose sind wichtiger als eine bloße Ergebnisdatei. Einzelheiten nennt die [GNU-gzip-Manpage](https://manpages.debian.org/trixie/gzip/gzip.1.en.html).

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit kleinen selbst angelegten Dateien und `-k` beginnen.
2. Zwischen Kopie, Datenstrom und normalem Ersetzen der Eingabe unterscheiden.
3. Zielnamen vor jeder Umleitung kontrollieren.
4. Erfolgreiche Kompression durch Test und kontrollierte Rückgewinnung ergänzen.
5. Keine Kompressionsstufe als Sicherheits- oder Verschlüsselungsstufe betrachten.
6. Für Verzeichnisse und Systembackups einen passenden Archiv- und Sicherungsablauf wählen.
7. Bei wichtigen veränderlichen Daten zuerst Konsistenz sicherstellen.

**Prüfstand:** Mit GNU gzip 1.12 wurden Kompression mit `-kv`, Integritätstest, Dekompression auf stdout und Kompression mit `-nc` geprüft. Die Inhalte stimmten mit den eigenen Testdaten überein; bei `-n` waren die geprüften üblichen Namens- und Zeitfelder im Gzip-Header nicht belegt. An einer separaten eigenen Testdatei wurde die normale Ersetzung ohne `-k` bestätigt. Rekursive Verarbeitung, laufende Datenbanken und beschädigte Fremddaten wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gunzip` | Standardmäßig dekomprimierende Variante. |
| `zcat` | Dekomprimierte Daten auf stdout ausgeben. |
| `zgrep`, `zless` | Komprimierte Textdaten durchsuchen beziehungsweise lesen, soweit die installierte Variante sie unterstützt. |
| `tar` | Dateien und Ordner unabhängig von der Kompression bündeln. |
| `pigz` | Gzip-verwandtes Werkzeug mit anderer Parallelisierungsstrategie; separat prüfen. |
| `bzip2`, `xz`, `zstd` | Andere Formate mit eigenen Optionen und Leistungsmerkmalen. |

Ausgangseintrag: Datensatz 9 in `index.json`. Die bisherige allgemeine Erklärung ist durch die Unterschiede zwischen Kompression, Dateiersetzung, Archivierung und Integrität ergänzt.
