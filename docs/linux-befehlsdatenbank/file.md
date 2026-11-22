---
id: "file"
name: "file"
command: "file"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "file"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 183
reviewed_at: "2026-11-13"
locally_checked_version: "file 5.45"
---

# file – Dateitypen anhand von Metadaten und Inhalt einschätzen

## 1. Kurzbeschreibung

file ordnet Dateien anhand von Dateisystemmerkmalen, Formatkennungen und Textmerkmalen ein. Die Endung allein entscheidet nicht über das Ergebnis.

Für die Arbeit mit eigenen zugänglichen Dateien sind keine Root-Rechte erforderlich. Entscheidend sind die nötigen Rechte an den jeweils betroffenen Verzeichnissen und Dateien.

## 2. Was macht der Befehl?

Die Erkennung ist eine Heuristik mit einer Magic-Datenbank. Ein Treffer bestätigt weder vollständige Formatgültigkeit noch Herkunft oder Harmlosigkeit. -b lässt den Namen weg, --mime-type liefert den erkannten Medientyp. -h betrachtet einen Symlink selbst, -L dessen Ziel. Die Vorgabe kann durch POSIXLY_CORRECT beeinflusst werden, deshalb den gewünschten Modus ausdrücklich wählen. Das Lesen kann den Zugriffszeitstempel beeinflussen. Optionen wie -z können komprimierten Inhalt untersuchen und zusätzliche Verarbeitung auslösen.

[Gelesene Primärquelle: file(1)](https://man7.org/linux/man-pages/man1/file.1.html), ergänzt durch die lokale Hilfe von file 5.45. Die Online-Manpage beschreibt 5.46, der eigene Test 5.45.

## 3. Syntax

```text
file [OPTIONEN] DATEI ...
```

Großgeschriebene Namen sind Platzhalter; eckige Klammern zeigen optionale Argumente. Pfade mit Leerzeichen zitieren. `--` beendet bei den hier beschriebenen GNU-/util-linux-Dateiaufrufen die Optionsauswertung, soweit die jeweilige Syntax es vorsieht.

## 4. Wichtige Optionen

| Option | Bedeutung und Grenze |
| --- | --- |
| -b | Nur Klassifikation ohne Dateiname |
| --mime-type | Erkannten MIME-Medientyp ausgeben |
| -i | MIME-Typ und Codierungsangabe |
| -h | Symlink selbst beschreiben |
| -L | Ziel eines Links untersuchen |
| -E | Dateisystemfehler als Fehlerstatus behandeln |
| -s | Spezialdateien lesen, kein Bestandteil dieser Übung |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und die im Block genannten Werkzeuge. Nur eine eigene kurze ASCII-Datei mit absichtlich unpassender Endung wird untersucht. Keine Geräte und keine fremden Binärdateien. Der Block läuft in einer Subshell. Fehler bei mktemp oder cd brechen vor den Schreibzugriffen ab. Die eigenen Übungsdaten bleiben zur Kontrolle im ausgegebenen Temporärpfad erhalten.

### Schritt 1: Eigenen Arbeitsbereich und Daten vorbereiten

Der folgende zusammenhängende Block legt einen neuen privaten Übungsordner an. Alle relativen Pfade beziehen sich ausschließlich auf ihn.

### Schritt 2: Übung und Ergebnisprüfung ausführen

```bash
(
set -eu
uebung=$(mktemp -d --tmpdir netmon-file-XXXXXX) || exit 1
cd "$uebung" || exit 1
printf 'Uebungsordner: %s\n' "$uebung"
printf 'Ein eigener einfacher ASCII-Text.\n' > notiz.jpg
LC_ALL=C file -b --mime-type -- notiz.jpg > typ.txt
printf 'text/plain\n' > erwartet.txt
cmp typ.txt erwartet.txt
cat typ.txt
)
```

### Schritt 3: Ergebnis verstehen

Obwohl der Name auf .jpg endet, ergibt die eigene Textdatei text/plain. Das beweist den Erkennungsfall dieser kleinen Eingabe und Magic-Version. Es beweist nicht, dass jedes vermeintliche Bild ungefährlich oder vollständig erkannt wäre. Ein erfolgreiches Dateikommando ist keine Freigabe zum Öffnen oder Ausführen des Inhalts.

## 6. Typische Anwendungsfälle

Unklare Dateiendungen untersuchen, passende Anzeigeprogramme eingrenzen oder vor einer Konvertierung einen ersten Hinweis zum Format gewinnen. Anschließend das zuständige Formatwerkzeug und die Herkunft getrennt prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Eingabe wird von Parsern ausgewertet. Fremde oder sehr große Daten brauchen einen gesonderten Prüfkontext. -s kann Gerätezugriffe erlauben, -z Dekompression und -S eine vorhandene Sandbox abschalten. Diese Modi sind nicht pauschal sichere Dateianzeigen. Ausgabe oder Fehlertext ohne -E allein nicht als gesicherten Erfolg interpretieren.

## 8. Häufige Fehler

| Beobachtung | Ursache und Vorgehen |
| --- | --- |
| Endung und Ergebnis widersprechen sich | Dateiname und Datenformat sind unabhängig |
| data statt Formatname | Die Daten passen zu keiner ausreichend eindeutigen Regel |
| Fehlende Datei mit scheinbar erfolgreichem Lauf | Diagnose lesen und bei Bedarf -E verwenden |

## 9. Sichere Varianten oder Tipps für Einsteiger

Eine konkrete eigene normale Datei auswählen und unnötige Dekompressions- oder Spezialdateioptionen weglassen. Die lokale Hilfe von file 5.45 wurde mit der online neueren Manpage abgeglichen; Grenzen und Magic-Regeln können zwischen Versionen abweichen.

**Prüfstand am 2026-11-13:** file 5.45. Praktisch geprüft: der veröffentlichte eigene Beispielblock, Gesamtstatus 0. Keine Spezialdateien, Kompressionsvarianten oder unbekannten Binärdateien geprüft. Quellenprüfung, Syntaxprüfung und Funktionsnachweis sind unterschiedliche Schritte. Die Strukturprüfung ist keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| od | Tatsächliche Bytes anzeigen |
| stat | Metadaten unabhängig von Formatmustern |
| strings | Druckbare Zeichenfolgen finden |

Herkunft: Originaldatensatz 183 der unveränderten CSV. Die feste Kennung, Nummer, Kategorie und der Dateiname wurden gegen die Zuordnung geprüft; fachlich unpassende Platzhalter und Risikoeinstufungen werden nicht ungeprüft übernommen.
