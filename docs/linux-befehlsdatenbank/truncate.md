---
id: "truncate"
name: "truncate"
command: "truncate"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "groesse", "datenverlust", "sparse"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 203
reviewed_at: "2026-11-13"
locally_checked_version: "truncate (GNU coreutils) 9.4"
---

# truncate – Dateilänge verändern und Datenverlust verstehen

## 1. Kurzbeschreibung

`truncate` verkleinert oder vergrößert die logische Länge einer Datei. Beim Verkleinern gehen die abgeschnittenen Inhalte verloren. **Für eigene beschreibbare Dateien ist kein Root erforderlich.** Die Einstufung `danger` betrifft den unmittelbaren möglichen Datenverlust; der Originaleintrag „sicher lesend“ trifft nicht zu.

## 2. Was macht der Befehl?

Das Programm arbeitet mit Größen in Bytes, ohne Textzeilen, Zeichenkodierung oder Dateiformat zu berücksichtigen. Es kann mitten in einem Zeichen oder Datensatz abschneiden. Die Datei bleibt unter demselben Namen vorhanden, ihr Inhalt kann danach aber unbrauchbar sein.

Bei einer Vergrößerung wird der zusätzliche Bereich als Nullbytes gelesen. Er kann als Loch einer Sparse-Datei vorliegen: Logische Größe und tatsächlich belegter Speicher sind dann verschieden. Eine spätere Beschreibung dieses Bereichs kann weiteren Speicher benötigen. Ein größerer Endwert stellt zuvor abgeschnittene Daten nicht wieder her.

Fehlende Dateien werden normalerweise neu erzeugt. `-c` unterdrückt nur diese Neuanlage, schützt aber keine bestehenden Inhalte. Referenz: [GNU-truncate-Manpage bei Debian](https://manpages.debian.org/trixie/coreutils/truncate.1.en.html), zusätzlich lokale Manpage von coreutils 9.4 gelesen.

## 3. Syntax

```text
truncate -s GROESSE [OPTIONEN] -- DATEI ...
truncate -r REFERENZ [OPTIONEN] -- DATEI ...
```

Eine Größe oder Referenz ist nötig. `-r` verwendet deren Länge, kopiert aber keinen Inhalt. Bei Kombination mit einer relativen Größenangabe ist die Referenz die Ausgangsgröße. Diese Kombination ist fortgeschritten und nicht Teil der Übung.

`--` beendet die Optionsauswertung. Ein Größenargument wie `'<100'` muss zitiert werden, damit `<` nicht als Shell-Umleitung verstanden wird.

## 4. Wichtige Optionen

| Option oder Größenform | Bedeutung | Konsequenz |
| --- | --- | --- |
| `-s N`, `--size=N` | Absolute Länge N setzen. | N kleiner als bisher schneidet Daten ab. |
| `-s 0` | Datei auf null Bytes verkürzen. | Vollständiges Leeren ohne Rückfrage. |
| `-c`, `--no-create` | Fehlende Dateien nicht erzeugen. | Bestehende Ziele werden weiterhin verändert. |
| `-r DATEI`, `--reference=DATEI` | Referenzgröße verwenden. | Kein Inhaltsvergleich und keine Kopie. |
| `-o`, `--io-blocks` | Größe in I/O-Blöcken statt Bytes interpretieren. | Nicht mit Dateisystembelegung verwechseln; lokale Blockgröße berücksichtigen. |
| `-s +N`, `-s -N` | Um N vergrößern beziehungsweise verkleinern. | Negative Form ist eine Verringerung, keine negative absolute Dateilänge. |
| `-s '<N'`, `-s '>N'` | Höchstens beziehungsweise mindestens N. | Kann abhängig von der Ausgangsgröße unverändert bleiben. |
| `-s '/N'`, `-s '%N'` | Auf ein Vielfaches von N ab- beziehungsweise aufrunden. | Abrunden kann Inhalte entfernen. |

GNU-Einheiten unterscheiden: `1K` und `1KiB` bedeuten 1024 Bytes, `1KB` bedeutet 1000 Bytes. Die Übung verwendet bewusst kleine Werte ohne Suffix.

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GNU coreutils und ausschließlich neue, entbehrliche Testdaten. Die Schritte in einer Shell ausführen. Der temporäre Ordner bleibt erhalten; keine vorhandenen Benutzerdateien verwenden.

### Schritt 1: Acht bekannte Bytes vorbereiten

```bash
uebung="$(mktemp -d -t netmon-truncate-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf 'ABCDEFGH' > muster.txt || exit 1
cp -- muster.txt original.txt || exit 1
wc -c < muster.txt
```

Die Ausgabe ist `8`. `printf` fügt hier keinen Zeilenumbruch an. `original.txt` ist die getrennte Kontrollkopie innerhalb der Übung.

### Schritt 2: Auf vier Bytes kürzen

```bash
truncate -s 4 -- muster.txt || exit 1
stat -c '%s Byte' -- muster.txt
od -An -tx1 -- muster.txt
```

Erwartet: `4 Byte` und die Hexwerte `41 42 43 44` für `ABCD`. Die Bytes `EFGH` sind aus dieser Datei entfernt. Die Kontrollkopie bleibt acht Bytes lang.

### Schritt 3: Wieder auf acht Bytes vergrößern

```bash
truncate -s 8 -- muster.txt || exit 1
od -An -tx1 -- muster.txt
```

Erwartet: `41 42 43 44 00 00 00 00`. Die Endposition wurde erweitert; der entfernte Inhalt kehrt nicht zurück. Nullbytes sind Datenwerte, keine sichtbaren Zeichen `0`.

### Schritt 4: Referenz und unterdrückte Neuanlage prüfen

```bash
truncate -r original.txt -- nur-groesse.bin || exit 1
stat -c '%n: %s Byte' -- original.txt nur-groesse.bin
od -An -tx1 -- nur-groesse.bin
truncate -c -s 0 -- fehlt.txt || exit 1
if test ! -e fehlt.txt; then printf '%s\n' 'Keine neue Datei'; fi
```

Beide aufgelisteten Dateien haben acht Bytes. Die neu erzeugte Referenzgrößen-Datei enthält acht Nullbytes statt `ABCDEFGH`. Der letzte Aufruf erzeugt `fehlt.txt` nicht und die Bestätigung erscheint. Bei einem existierenden Ziel hätte derselbe `-c -s 0`-Aufruf den Inhalt geleert.

## 6. Typische Anwendungsfälle

**Kleine Testdateien definierter Länge:** Programme mit vorhersehbaren Dateigrößen prüfen. Dateiformate erfordern trotzdem gültigen Inhalt; eine Länge allein erzeugt kein gültiges Bild oder Dateisystem.

**Sparse-Verhalten untersuchen:** Logische Länge mit `stat` und belegte Blöcke mit `du` vergleichen. Dateisystem, Kompression und weitere Eigenschaften können das Ergebnis beeinflussen.

**Verarbeitung beschädigter Daten testen:** Nur eine eigene Kopie absichtlich verkürzen und die Reaktion einer Anwendung untersuchen. Das Original getrennt erhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Es gibt keine eingebaute Rückfrage und keinen allgemeinen Trockenlauf. `-c` ist kein Schutz vor Abschneiden. Symbolische Links können die Änderung auf ihre Ziele lenken. Pfad und Größe vor jedem Aufruf prüfen.

Laufende Datenbanken oder Protokolle dürfen nicht nach diesem Übungsmuster bearbeitet werden. Ein schreibender Prozess kann anschließend an einer alten Dateiposition fortfahren; Konsistenz und Inhalte können verloren gehen. Für Protokolle einen passend konfigurierten Rotationsablauf verwenden.

Abschneiden ist keine sichere physische Löschung: Snapshots, Kopien oder Speicherverwaltung können Daten weiterhin enthalten. Umgekehrt ist eine zuverlässige Wiederherstellung aus der gekürzten Datei nicht zugesichert.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| Datei unerwartet leer | Größe null oder zu klein. | Nicht weiter verändern; separate Sicherung prüfen. |
| Alte Daten fehlen nach Vergrößern | Neue Bereiche enthalten Nullbytes. | Inhalt aus einer erhaltenen Kopie wiederherstellen. |
| Dateigröße und `du` unterscheiden sich | Logische Länge und Belegung sind verschieden. | Beide Messgrößen unterscheiden. |
| Shell meldet Umleitungsfehler | Größenoperator nicht zitiert. | Das ganze Größenargument zitieren. |
| Fehlende Datei wird trotz `-c` nicht angelegt | Genau dafür steht `-c`. | Bestehende und fehlende Ziele unterscheiden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst Größen nur mit `stat` lesen. Änderungen ausschließlich an eigenen Kopien üben. Keine Systempfade, Geräte oder aktiven Anwendungsdateien verwenden; `sudo` ist für die Beispiele unnötig.

**Prüfstand am 2026-11-13:** GNU `truncate` 9.4; lokale und verlinkte Manpage gelesen. Abschnitt 5 vollständig ausgeführt: acht auf vier Bytes gekürzt, auf acht erweitert und Nullbytes kontrolliert; Referenzgröße ohne Inhaltskopie sowie `-c` auf fehlendem Ziel bestätigt.

**Nicht praktisch geprüft:** relative Größen, Rundungsoperatoren, `-o`, große Sparse-Dateien, aktive Anwendungen und andere Dateisysteme. Keine Behauptung einer physischen Löschung oder Wiederherstellung.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `stat` | Logische Länge und Metadaten lesen. |
| `du` | Tatsächliche Belegung untersuchen. |
| `od` | Bytes sichtbar darstellen. |
| `cp` | Eine getrennte Inhaltskopie anlegen. |
| `fallocate` | Speicherbereiche mit anderen, dateisystemabhängigen Funktionen verwalten. |

Ausgangsdatensatz 203 und Zuordnung sind gegen Katalog und Original-CSV geprüft. Originalfelder und Entwurf bleiben unverändert.
