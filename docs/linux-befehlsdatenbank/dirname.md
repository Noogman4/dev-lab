---
id: "dirname"
name: "dirname"
command: "dirname"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "dirname"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 181
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# dirname – Den Verzeichnisanteil einer Pfadzeichenfolge bestimmen

## 1. Kurzbeschreibung

dirname entfernt die letzte Pfadkomponente aus einer Zeichenfolge. Es prüft nicht, ob dieser Pfad oder sein Elternverzeichnis existiert.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Der Befehl arbeitet lexikalisch: Er entfernt abschließende Schrägstriche und die letzte verbleibende Komponente. Ohne Schrägstrich ergibt sich ein Punkt als Bezeichnung des aktuellen Verzeichnisses. Ein absoluter Eintrag direkt unter / liefert /. Mehrere Argumente werden getrennt verarbeitet. Punkte, .. und symbolische Links werden damit nicht zu einer tatsächlich existierenden kanonischen Datei aufgelöst. Gerade in Skripten ist die Ausgabe daher nur ein abgeleiteter Name, keine Zusicherung, dass cd dorthin erfolgreich wäre.

[Gelesene Primärquelle: GNU-Handbuch, Abschnitt dirname invocation](https://www.gnu.org/software/coreutils/manual/html_node/dirname-invocation.html). Tatsächlich lokal gelesen: /usr/share/info/coreutils.info.gz (GNU coreutils 9.4), einschließlich der jeweils erläuterten Optionsabschnitte.

## 3. Syntax

```text
dirname [OPTION] NAME ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -z, --zero | Ausgaben mit NUL statt Newline abschließen |
| --help | Lokale Syntax lesen |
| --version | Implementierung und Version feststellen |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Die Eingaben sind erfundene Pfadzeichenfolgen; es werden keine genannten Pfade gelesen. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-dirname-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
dirname -- 'paket/unter/notiz.txt' 'notiz.txt' 'paket/unter/' > anteile.txt
printf 'paket/unter\n.\npaket\n' > erwartet.txt
cmp anteile.txt erwartet.txt
cat anteile.txt
)
```

### Schritt 3: Ergebnis verstehen

Das erste Argument ergibt paket/unter, ein einzelner Dateiname ergibt ., und beim letzten Argument wird nach Entfernen des letzten Slash die Komponente unter entfernt: Ergebnis paket. cmp bestätigt ausschließlich diese Zeichenfolgen. Dass die genannten Ordner nicht angelegt wurden, zeigt die Unabhängigkeit von einer Dateisystemabfrage.

## 6. Typische Anwendungsfälle

In Skripten Namen für einen bereits anderweitig geprüften Elternpfad ableiten. Mit basename den letzten Namensbestandteil und mit realpath die tatsächliche Auflösung vergleichen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Gefahr entsteht vor allem bei der Weiterverwendung: Ein abgeleiteter Pfad kann falsch, nicht vorhanden oder zwischenzeitlich ausgetauscht sein. Fehlender Slash bedeutet . und nicht automatisch das Heimatverzeichnis. Ausgabe nicht mit eval ausführen. Doppelte führende Slashes haben POSIX-seitig Sonderfälle und können auf anderen Plattformen anders behandelt werden.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Ergebnis ist nur ein Punkt | Die Eingabe hatte keinen Slash, das ist kein Fehler |
| Ordner existiert nicht | dirname validiert die Existenz nicht |
| Pfad mit Leerzeichen zerfällt | Das Argument und eine spätere Befehlsersetzung zitieren |

## 9. Sichere Varianten oder Tipps für Einsteiger

Für einen einzelnen gewöhnlichen Namen kann eltern=$(dirname -- "$name") verwendet werden; den Erfolg eines folgenden cd trotzdem prüfen. Bei eingebetteten Newlines die NUL-Variante mit einem NUL-fähigen Empfänger einsetzen. Shell-Befehlsersetzung entfernt abschließende Newlines und ist kein verlustfreier Transport beliebiger Dateinamen.

**Prüfstand am 2026-11-13:** GNU coreutils 9.4. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. POSIX-Sonderfall // und Dateinamen mit Newlines nicht praktisch geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| basename | Letzte Komponente statt Elternanteil |
| realpath | Kanonischer Pfad mit Auflösungsregeln |
| readlink | Linkinhalt oder gewählte Kanonisierung |

Herkunft: Originaldatensatz 181 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
