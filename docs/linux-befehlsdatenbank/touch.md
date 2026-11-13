---
id: "touch"
name: "touch"
command: "touch"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "caution"
tags: ["dateien", "zeitstempel", "metadaten"]
status: "Korrigiert; Quellen und temporäre Beispiele geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 201
reviewed_at: "2026-11-13"
locally_checked_version: "touch (GNU coreutils) 9.4"
---

# touch – Dateien anlegen und Zeitstempel gezielt ändern

## 1. Kurzbeschreibung

`touch` setzt Zugriffszeit (`atime`) und Änderungszeit (`mtime`) von Dateien. Ein fehlender Dateipfad wird normalerweise als leere Datei angelegt. Eine vorhandene Datei wird dabei nicht geleert. **Für eigene Dateien sind keine Root-Rechte erforderlich.**

Der Ausgangseintrag „sicher lesend“ ist irreführend: Schon ein einfacher Aufruf verändert Metadaten oder legt eine Datei an. Deshalb gilt hier `caution`.

## 2. Was macht der Befehl?

Ohne Zeitoption setzt GNU `touch` beide Zeiten auf die aktuelle Systemzeit. `-a` beschränkt die Änderung auf die Zugriffszeit, `-m` auf die Änderungszeit. Der Dateiinhalt bleibt erhalten. Ein Build-Werkzeug kann eine Datei trotzdem anschließend als neuer ansehen und neu verarbeiten.

`ctime` bezeichnet die Zeit einer Metadatenänderung, nicht die Erstellung der Datei. Sie wird bei solchen Änderungen vom System aktualisiert und lässt sich mit `touch` nicht auf einen frei gewählten Zeitpunkt zurücksetzen. Eine gegebenenfalls gespeicherte Erstellungszeit ist ebenfalls kein mit `touch` frei setzbarer Wert.

Standardmäßig betrifft ein symbolischer Link sein Ziel; `-h` wählt stattdessen den Link selbst. Die Optionen sind im [GNU-Handbuch bei Debian](https://manpages.debian.org/trixie/coreutils/touch.1.en.html) dokumentiert und wurden mit der lokalen Manpage zu coreutils 9.4 abgeglichen.

### Welche Rechte sind erforderlich?

Bei einer **Neuanlage** braucht man Schreib- und Suchrecht im Elternverzeichnis sowie Suchrecht auf den übrigen Pfadkomponenten. Bei einer **vorhandenen Datei** muss man unterscheiden: Beide Zeiten auf jetzt zu setzen ist unter Linux unter anderem als Eigentümer oder mit Schreibzugriff möglich. Für explizite Zeiten, etwa mit `-d` oder `-r`, ist grundsätzlich Eigentümerschaft oder eine passende Privilegierung nötig; bloßes Schreibrecht genügt nicht allgemein. Auch die Auswahl nur eines Zeitstempels kann strengere Bedingungen haben.

Eine Referenzdatei muss für die Metadatenabfrage erreichbar sein; Leserecht auf ihren **Inhalt** ist dafür nicht generell nötig. Schreibgeschützte Dateisysteme und besondere Dateiattribute können Änderungen auch dem Eigentümer verbieten. Quelle: [Linux-Handbuch zu `utimensat`, Rechte und Fehler](https://man7.org/linux/man-pages/man2/utimensat.2.html).

## 3. Syntax

```text
touch [OPTIONEN] DATEI ...
touch -r REFERENZ [OPTIONEN] DATEI ...
```

Mindestens ein Ziel ist erforderlich. Eckige Klammern werden nicht mitgetippt. Dateipfade mit Leerzeichen zitieren; `--` beendet die Optionsauswertung. Ein einzelnes Argument `-` bezeichnet bei GNU `touch` die mit der Standardausgabe verbundene Datei. Für eine wirklich so benannte Datei den Pfad `./-` verwenden.

## 4. Wichtige Optionen

| Option | Bedeutung | Grenze oder Hinweis |
| --- | --- | --- |
| `-a` | Nur `atime` setzen. | Automatische Zugriffszeitpflege des Dateisystems ist eine andere Frage. |
| `-m` | Nur `mtime` setzen. | Kann Build- und Synchronisationsentscheidungen beeinflussen. |
| `-c`, `--no-create` | Fehlende Ziele nicht erzeugen. | Erfolgreicher Abschluss beweist dann keine Existenz. |
| `-d ZEIT`, `--date=ZEIT` | Eine ausgeschriebene Zeit verwenden. | Zeitzone ausdrücklich angeben, wenn ein fester Zeitpunkt gemeint ist. |
| `-t ZEIT` | Format `[[CC]YY]MMDDhhmm[.ss]`. | Andere Eingabesyntax als `-d`; lokale Zeitzone beachten. |
| `-r REFERENZ` | Zeitstempel einer anderen Datei übernehmen. | Kopiert keinen Inhalt und keine sonstigen Rechte. |
| `-h`, `--no-dereference` | Link selbst bearbeiten. | Unterstützung des Systems nötig; erzeugt fehlende Ziele nicht. |
| `--version`, `--help` | Version beziehungsweise Hilfe anzeigen. | Verändern keine Zieldatei. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash und GNU coreutils, ein beschreibbares temporäres Verzeichnis und ein normaler Benutzer. Die Schritte gehören zu derselben Shell. Jeder Schreibschritt muss erfolgreich sein, bevor es weitergeht. Der Übungsordner bleibt zur Kontrolle bestehen.

### Schritt 1: Sicher im eigenen Verzeichnis beginnen

```bash
uebung="$(mktemp -d -t netmon-touch-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
printf '%s\n' 'Testinhalt' > notiz.txt || exit 1
touch -d '2020-01-02 03:04:05 UTC' -- notiz.txt || exit 1
stat -c '%n: %s Byte; atime=%X; mtime=%Y' -- notiz.txt
```

Der Abbruch bei fehlgeschlagenem `mktemp` verhindert ein Weiterschreiben am falschen Ort. `printf` legt elf Bytes einschließlich Zeilenumbruch an. Der feste Ausgangszeitpunkt macht die folgende Änderung erkennbar. Die beiden Sekundenwerte sind zunächst gleich.

### Schritt 2: Nur die Änderungszeit erneuern

```bash
touch -m -- notiz.txt || exit 1
stat -c '%n: %s Byte; atime=%X; mtime=%Y' -- notiz.txt
cat -- notiz.txt
```

Die Größe bleibt elf Bytes, `atime` bleibt beim gesetzten Zeitpunkt, `mtime` entspricht jetzt der Systemuhr. `cat` zeigt weiterhin `Testinhalt`. Das anschließende Lesen durch `cat` kann selbst die Zugriffszeit beeinflussen; deshalb steht die Metadatenkontrolle davor.

### Schritt 3: Neuanlage und unterdrückte Neuanlage vergleichen

```bash
touch -- leer.txt || exit 1
stat -c '%n: %s Byte' -- leer.txt
touch -c -- fehlt.txt || exit 1
if test ! -e fehlt.txt; then printf '%s\n' 'fehlt.txt wurde nicht angelegt'; fi
```

Erwartet werden `leer.txt: 0 Byte` und die Bestätigung, dass `fehlt.txt` fehlt. `-c` ist damit kein bloßer Existenztest: Bereits vorhandene Ziele würde es weiterhin verändern.

### Schritt 4: Zeitstempel aus einer Referenz übernehmen

```bash
touch -r notiz.txt -- kopie.txt || exit 1
stat -c '%n: atime=%X; mtime=%Y' -- notiz.txt kopie.txt
```

Die Zeitpaare stimmen überein. `kopie.txt` ist neu und leer; der Name bedeutet hier keine Inhaltskopie. Erst dieser Metadatenvergleich prüft die Wirkung von `-r`.

## 6. Typische Anwendungsfälle

**Markerdatei:** Eine selbst gewählte leere Datei signalisiert, dass ein Arbeitsschritt erfolgt ist. Ein wiederholter Aufruf aktualisiert ihre Zeiten, statt sie zu leeren.

**Build-Verhalten untersuchen:** Die `mtime` einer eigenen Quelldatei erneuern und danach bewusst einen Build starten. Das kann weitere Verarbeitung auslösen und ist deshalb eine Änderung am Projektzustand.

**Zeitstempel nach einer Verarbeitung übernehmen:** Mit `-r` einem selbst erzeugten Ergebnis die Zeiten einer Referenz geben. Gleiche Zeiten beweisen weder gleichen Inhalt noch gleiche Herkunft.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Pfade können unerwünschte Dateien erzeugen; fehlende Zwischenverzeichnisse werden nicht automatisch angelegt. Links können die Änderung auf ein anderes Ziel lenken. Keine unkontrollierten Platzhalter auf wichtige Verzeichnisbäume anwenden.

Zeitabhängige Backups und Überwachung können auf die neuen Metadaten reagieren. `touch` ist kein Werkzeug, um eine Datei unbemerkt „original“ erscheinen zu lassen. Für eine reine Bestandsaufnahme `stat` oder `test` verwenden.

## 8. Häufige Fehler

| Beobachtung | Erklärung | Sinnvoller nächster Schritt |
| --- | --- | --- |
| Neue leere Datei statt Fehlermeldung | Ziel fehlte, `-c` war nicht gesetzt. | Schreibziel vorab prüfen. |
| `-c` meldet Erfolg, Datei fehlt weiterhin | Genau das ist die gewählte Funktion. | Existenz getrennt prüfen. |
| `Permission denied` oder `Operation not permitted` | Pfadrechte, Eigentümer, Attribute oder Dateisystem verhindern die Änderung. | Bedingungen unterscheiden; nicht pauschal `sudo` ergänzen. |
| Uhrzeit wirkt verschoben | UTC-Eingabe und lokale Anzeige unterscheiden sich. | Zeitzone und Sekundenwert vergleichen. |
| Referenz und Ziel haben verschiedenen Inhalt | `-r` kopiert nur Zeiten. | Für Inhaltskopien ein Kopierwerkzeug verwenden. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Mit einem frischen Übungsordner beginnen, konkrete Pfade zitieren und `-c` einsetzen, wenn eine Neuanlage unerwünscht ist. Für Nachweise den Inhalt zusätzlich kontrollieren; die Größe allein genügt nicht.

**Prüfstand am 2026-11-13:** GNU `touch` 9.4, lokale Manpage sowie die verlinkten Handbücher gelesen. Die Schritte aus Abschnitt 5 wurden mit eigenen temporären Daten ausgeführt. Zusätzlich geprüft: unveränderter Inhalt bei `-m`, getrennte Zeiten, `-r` mit einer Referenz ohne Inhaltsleserecht, explizite Zeitsetzung auf eigener Datei mit Modus `000` und `-h` ohne Änderung des Linkziels. Alle Zusatzprüfungen liefen als UID 1000.

**Nicht praktisch geprüft:** fremde Eigentümer, privilegierte Ausnahmen, besondere Dateiattribute, andere Dateisysteme und andere Implementierungen. Die getestete lokale Version ist 9.4; die Debian-Webreferenz beschreibt 9.7.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `stat` | Zeitstempel und weitere Metadaten prüfen. |
| `date` | Zeitangaben und Zeitzonen verstehen. |
| `test` | Existenz oder Eigenschaften ohne bewusstes Setzen von Zeiten prüfen. |
| `cp` | Inhalte kopieren; Erhalt von Metadaten benötigt passende Optionen. |

Ausgangsdatensatz 201 und Dateizuordnung wurden gegen den eingefrorenen Katalog und die bytegleich geprüfte Original-CSV abgeglichen. Die Originale bleiben unverändert.
