---
id: "unlink"
name: "unlink"
command: "unlink"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "loeschen", "links"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 204
reviewed_at: "2026-11-13"
locally_checked_version: "unlink (GNU coreutils) 9.4"
---

# unlink – Genau einen Dateinamen oder symbolischen Link entfernen

## 1. Kurzbeschreibung

`unlink` entfernt einen einzelnen Verzeichniseintrag. Das ist ein Löschvorgang ohne Papierkorb und ohne Rückfrage. **Für eigene Testdateien in einem eigenen beschreibbaren Verzeichnis sind keine Root-Rechte nötig.** Der Originaleintrag „sicher lesend“ wird deshalb durch `danger` ersetzt.

## 2. Was macht der Befehl?

Ein Dateiname verweist auf ein Dateisystemobjekt. Mehrere Hardlinks sind mehrere Namen desselben Objekts. `unlink` entfernt einen solchen Namen; andere Hardlinks bleiben erhalten. Wenn der letzte Name entfernt wurde, halten offene Dateideskriptoren die Datei gegebenenfalls noch am Leben. Speicherfreigabe und Verschwinden eines Namens sind deshalb verschiedene Vorgänge.

Bei einem symbolischen Link wird der Link selbst entfernt, nicht sein Ziel. Ein kaputter Symlink ist ebenfalls ein entfernbarer Eintrag. Dagegen kann ein Symlink in einer **vorherigen Pfadkomponente** die Pfadauflösung weiterhin auf einen anderen Ort lenken.

GNU `unlink` bearbeitet genau einen Operanden und ruft die entsprechende Systemfunktion auf. Es bietet keine rekursive Verzeichnislöschung. Grundlagen: [GNU-unlink-Manpage](https://manpages.debian.org/trixie/coreutils/unlink.1.en.html), [Linux-Systemfunktion und Fehlerbedingungen](https://man7.org/linux/man-pages/man2/unlink.2.html); beide sowie die lokalen Manpages wurden gelesen.

## 3. Syntax

```text
unlink [--] DATEI
unlink --help
unlink --version
```

Ein echter Löschaufruf braucht genau einen Pfad. `--` verhindert, dass ein mit Bindestrich beginnender Name als Option gelesen wird. Dateinamen mit Leerzeichen zitieren. Keine Platzhalter als vermeintliche Sammellöschung verwenden: Die Shell kann sie vor dem Aufruf in mehrere Argumente auflösen.

## 4. Wichtige Optionen

| Element | Bedeutung | Hinweis |
| --- | --- | --- |
| `DATEI` | Ein zu entfernender Verzeichniseintrag. | Wird ohne Nachfrage entfernt, sofern Rechte und Dateisystem es erlauben. |
| `--` | Optionsende bei GNU. | Schützt die Interpretation des Namens, nicht vor falscher Zielwahl. |
| `--help` | Hilfe anzeigen. | Kein Entfernen eines Pfads. |
| `--version` | Programmversion anzeigen. | Kein Entfernen eines Pfads. |

Optionen wie `-i`, `-f` und `-r` gehören nicht zu GNU `unlink`. Wer ausdrücklich eine Rückfrage benötigt, muss ein Werkzeug mit einer solchen Funktion wählen, beispielsweise `rm -i`, und dessen eigene Regeln beachten.

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und GNU coreutils. Alle Daten werden eigens angelegt. Die folgenden Schritte ausschließlich in derselben Shell und im neuen Übungsordner ausführen. Sie entfernen nur die gerade selbst erzeugten Übungseinträge.

### Schritt 1: Ziel und symbolischen Link erstellen

```bash
uebung="$(mktemp -d -t netmon-unlink-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' 'Eigene Testdaten' > ziel.txt || exit 1
ln -s ziel.txt verknuepfung || exit 1
ls -ld -- verknuepfung
readlink -- verknuepfung
```

Die Liste kennzeichnet einen Link mit `verknuepfung -> ziel.txt`. `readlink` gibt `ziel.txt` aus. Diese beiden Namen liegen im eigenen Übungsordner; der relative Link bezieht sich auf diesen Ort.

### Schritt 2: Nur den Link entfernen und das Ziel kontrollieren

```bash
unlink -- verknuepfung || exit 1
if test ! -L verknuepfung; then printf '%s\n' 'Symlink entfernt'; fi
cat -- ziel.txt
```

Erwartet werden die Bestätigung und weiterhin `Eigene Testdaten`. Das Ziel bleibt vorhanden. `test -L` prüft hier den Link selbst; `test -e` allein wäre bei einem kaputten Link irreführend, weil es dem Ziel folgt.

### Schritt 3: Unterschied zu einem Hardlink zeigen

```bash
ln -- ziel.txt zweiter-name.txt || exit 1
stat -c '%n: inode=%i; links=%h' -- ziel.txt zweiter-name.txt
unlink -- zweiter-name.txt || exit 1
stat -c '%n: inode=%i; links=%h' -- ziel.txt
cat -- ziel.txt
```

Die beiden Namen haben vor dem Entfernen dieselbe Inode-Nummer und Linkanzahl 2. Danach bleibt `ziel.txt` mit derselben Inode-Nummer und Linkanzahl 1 erhalten. Der Inhalt ist unverändert. Inode-Nummern hängen vom Dateisystem ab; entscheidend ist die Übereinstimmung in dieser Übung.

Der Ordner und `ziel.txt` bleiben zur gemeinsamen Kontrolle bestehen. Es wird kein letzter Name einer wichtigen Datei entfernt.

## 6. Typische Anwendungsfälle

**Einen bekannten Symlink entfernen:** Erst Link und Pfad prüfen, dann genau diesen Eintrag entfernen. Ein Linkname und sein Zielpfad sind unterschiedliche Löschziele.

**Einen einzelnen temporären Namen aufräumen:** In einem Skript einen vorher selbst angelegten und eindeutig bekannten Pfad entfernen. Kein allgemeiner Ersatz für sichere Temporärdateiverwaltung.

**Hardlink-Verhalten lernen:** Zwei eigene Namen desselben Objekts vergleichen und einen davon entfernen. Eine Hardlink-Kopie ist keine unabhängige Sicherung: Änderungen am Inhalt betreffen dasselbe Objekt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Für das Entfernen sind insbesondere Schreib- und Suchrechte im Elternverzeichnis sowie Suchrechte auf den Pfad wichtig. Leserecht oder Schreibschutz der Datei allein entscheiden nicht darüber. Sticky-Bit-Regeln, unveränderliche Attribute und schreibgeschützte Dateisysteme können den Vorgang zusätzlich verhindern.

Ein vorangehendes `ls` schützt nicht vor einem Austausch des Pfads zwischen Kontrolle und Entfernen. Das ist besonders bei gemeinsam beschreibbaren Verzeichnissen relevant. Im Beispiel begrenzt ein eigenes temporäres Verzeichnis die Übung.

Das Entfernen des letzten Namens kann Daten unzugänglich machen. Es ist keine zugesicherte physische Datenvernichtung; Kopien, Snapshots und offene Zugriffe sind gesondert zu berücksichtigen. Nicht mit `sudo` experimentieren.

## 8. Häufige Fehler

| Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `extra operand` | Mehrere Pfade, möglicherweise durch ein expandiertes Muster. | Genau einen geprüften Pfad übergeben. |
| `Is a directory` | Ein Verzeichnis wurde übergeben. | Für leere Verzeichnisse gegebenenfalls `rmdir` gesondert prüfen. |
| `No such file or directory` | Eintrag oder Zwischenpfad fehlt. | Arbeitsort und Pfad kontrollieren. |
| `Permission denied` | Verzeichnisrechte oder andere Regeln verhindern das Entfernen. | Rechteursache klären, nicht pauschal erhöhen. |
| Platz wird nicht sofort frei | Anderer Hardlink oder offener Zugriff bleibt. | Dateisystemzustand verstehen; nicht wahllos weitere Namen entfernen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor dem Entfernen `pwd`, `ls -ld` und bei Links `readlink` nutzen. Mit konkreten zitierten Namen arbeiten und echte Daten durch eine unabhängige Sicherung schützen. `unlink` besitzt weder Rückfrage noch allgemeinen Trockenlauf.

**Prüfstand am 2026-11-13:** GNU `unlink` 9.4; offizielle und lokale Manpages gelesen. Abschnitt 5 vollständig mit selbst erzeugten Daten ausgeführt: Symlink verschwand, Zielinhalt blieb; Hardlinks hatten dieselbe Inode-Nummer, Linkanzahl sank von 2 auf 1.

**Nicht praktisch geprüft:** offene Dateideskriptoren nach Entfernen des letzten Namens, fremde Eigentümer, Sticky-Bit-Ausnahmen, Netzdateisysteme und Wiederherstellung. Kein vorhandener Benutzerbestand wurde entfernt.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `ln` | Hardlinks und symbolische Links anlegen. |
| `readlink` | Inhalt eines symbolischen Links lesen. |
| `stat` | Inode und Linkanzahl anzeigen. |
| `rm` | Weitergehende Löschfunktionen, ebenfalls mit Datenverlustrisiko. |
| `rmdir` | Leere Verzeichnisse entfernen. |

Ausgangsdatensatz 204 ist mit Katalog und Original-CSV abgeglichen; Entwurfsoriginal und Quelldaten bleiben erhalten.
