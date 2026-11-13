---
id: "tar"
name: "tar"
command: "tar"
category: "Archive & Kompression"
language: "de"
root_required: false
risk_level: "caution"
tags: ["archive", "kompression", "tar", "dateisammlung"]
status: "Ausgearbeitet; Beispiele mit Testdaten geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 14
reviewed_at: "2026-11-13"
locally_checked_version: "GNU tar 1.35"
---

# tar – Dateien gesammelt archivieren und kontrolliert wiederherstellen

## 1. Kurzbeschreibung

`tar` fasst Dateien und Verzeichnisse zu einem Archiv zusammen. Es kann dessen Einträge auflisten und wiederherstellen. Diese Dokumentation beschreibt **GNU tar**. Andere Implementierungen können bei langen Optionen und Sonderfunktionen abweichen.

**Für Archive mit eigenen, zugänglichen Dateien sind keine Root-Rechte nötig.** Erstellen und Entpacken schreiben Dateien; vorhandene Ziele können betroffen sein. Der Befehl ist deshalb nicht pauschal nur lesend.

## 2. Was macht der Befehl?

Eine TAR-Datei enthält einzelne Einträge mit Namen, Dateiinhalten und Metadaten. Dadurch lässt sich eine ganze Ordnerstruktur als eine Datei transportieren. Ein einfaches `.tar`-Archiv ist noch nicht zwangsläufig komprimiert. Für `.tar.gz` wird zusätzlich ein gzip-Datenstrom verwendet.

Für die Arbeit sind drei Fragen getrennt zu beantworten: Welche Aufgabe soll ausgeführt werden? Welche Datei ist das Archiv? Welche Quell- oder Zielpfade gelten? Die verbreiteten Aufrufe `-cf`, `-tf` und `-xf` kombinieren jeweils Aufgabe und Archivdateiangabe.

Die [Debian-Manpage zu GNU tar](https://manpages.debian.org/trixie/tar/tar.1.en.html) beschreibt die Betriebsarten. Die Optionsangaben wurden zusätzlich mit der lokal installierten Hilfe von GNU tar 1.35 abgeglichen.

## 3. Syntax

```text
tar -cf ARCHIV.tar [OPTIONEN] QUELLE ...
tar -tf ARCHIV.tar [OPTIONEN]
tar -xf ARCHIV.tar [OPTIONEN]
```

Die Beispiele verwenden kurze Optionen mit Bindestrich. Bei `-cf sammlung.tar` bedeutet `-c` Erstellen und `-f` Archivdatei; das folgende Argument ist deren Name. Ohne eine bewusste Archivdateiangabe können andere Vorgaben greifen.

```bash
tar -cf "sammlung.tar" -C "Material" .
tar -tf "sammlung.tar"
tar -xf "sammlung.tar" -C "Ausgabe" --keep-old-files
```

`-C` ist positionsabhängig. Beim Erstellen gilt der Verzeichniswechsel für die folgenden Quellen. Der Punkt nimmt den Inhalt dieses Verzeichnisses einschließlich seiner Unterordner auf. Das Archiv im Beispiel liegt außerhalb von `Material`.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-c`, `--create` | Neues Archiv schreiben. | Ein bestehender Archivpfad kann überschrieben werden. |
| `-t`, `--list` | Eintragsnamen auflisten. | Keine vollständige Inhalts- oder Herkunftsprüfung. |
| `-x`, `--extract` | Einträge wiederherstellen. | Schreibt im gewählten Zielverzeichnis. |
| `-f DATEI`, `--file=DATEI` | Archiv auswählen. | Nicht mit einem Quellnamen verwechseln. |
| `-C ORDNER`, `--directory=ORDNER` | Arbeitsverzeichnis für nachfolgende Verarbeitung wechseln. | Zielordner beim Entpacken vorher anlegen. |
| `-v`, `--verbose` | Verarbeitete Einträge anzeigen. | Mehr Ausgabe allein beweist keinen vollständigen Erfolg. |
| `-z`, `--gzip` | gzip-Kompression verwenden. | Passender Kompressor muss verfügbar sein. |
| `-j`, `--bzip2`; `-J`, `--xz` | Andere Kompressionsverfahren wählen. | Groß- und Kleinschreibung unterscheiden. |
| `--keep-old-files` | Vorhandene Ausgabedateien nicht ersetzen. | Konflikte werden als Fehler gemeldet. |
| `--skip-old-files` | Vorhandene Dateien überspringen. | Anders als die vorherige Option stilles Überspringen. |
| `--no-same-owner` | Unter eigener Benutzerkennung entpacken. | Für gewöhnliche Nutzer bereits Standard; keine Isolation. |
| `--exclude=MUSTER` | Passende Einträge ausnehmen. | Muster zitieren und die tatsächliche Auswahl prüfen. |
| `-h`, `--dereference` | Beim Erstellen symbolischen Links folgen. | Kann unerwartet Daten außerhalb der sichtbaren Quellstruktur aufnehmen. |
| `--remove-files` | Eingaben nach Aufnahme entfernen. | Für die Einsteigerübung ausdrücklich nicht verwenden. |

Weitere Funktionen wie inkrementelle Sicherungen, ACLs und erweiterte Attribute benötigen einen eigenen Sicherungsplan. Die einfache Übung garantiert keine vollständige Wiederherstellung sämtlicher Dateisystemeigenschaften.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Übungsordner anlegen

```bash
tar --version
uebung="$(mktemp -d -t netmon-tar-XXXXXX)"
cd "$uebung"
pwd
```

Nur nach erfolgreichem Verzeichniswechsel fortfahren. Die folgenden Namen sind eigene Testdateien, keine vorhandenen privaten Dokumente.

### Schritt 2: Kleine Ordnerstruktur vorbereiten

```bash
mkdir -p "Material/unterordner"
printf '%s\n' 'Eigene TAR-Testnotiz.' > "Material/unterordner/notiz.txt"
```

Eine erneute Ausführung der Umleitung würde die eigene Testnotiz ersetzen. Für eine neue Übung einen neuen Arbeitsordner verwenden.

### Schritt 3: Archiv erstellen

```bash
tar -cf "sammlung.tar" -C "Material" .
```

Das Archiv entsteht im Übungsordner. Die Eingabedateien bleiben erhalten. Durch den Wechsel nach `Material` stehen darin relative Einträge wie `./unterordner/notiz.txt` statt eines vollständigen persönlichen Heimatpfads.

### Schritt 4: Inhalt auflisten

```bash
tar -tf "sammlung.tar"
```

Die Liste sollte den Unterordner und die Testnotiz zeigen. Vor dem Entpacken eines fremden Archivs hilft eine solche Übersicht, auffällige Pfade und eine unerwartete Struktur zu erkennen. Sie macht ein fremdes Archiv nicht automatisch vertrauenswürdig.

### Schritt 5: In einen frischen Ordner entpacken

```bash
mkdir "Ausgabe"
tar -xf "sammlung.tar" -C "Ausgabe" --no-same-owner --keep-old-files
cmp "Material/unterordner/notiz.txt" "Ausgabe/unterordner/notiz.txt"
```

`cmp` vergleicht hier die bekannte Testdatei byteweise. Bei gleichem Inhalt bleibt es normalerweise ohne Ausgabe und endet erfolgreich. Ein Konflikt durch eine bereits vorhandene Zieldatei lässt `--keep-old-files` fehlschlagen; das ist ein Schutzsignal.

### Schritt 6: Optional zusätzlich komprimieren

```bash
tar -czf "sammlung.tar.gz" -C "Material" .
tar -tzf "sammlung.tar.gz"
```

Das sind neue Aufrufe mit einem anderen Archivnamen. Die zusätzliche Option `-z` wählt gzip. Eine bloße Umbenennung von `.tar` in `.tar.gz` würde keine Kompression erzeugen.

## 6. Typische Anwendungsfälle

**Projektdateien weitergeben:** Ein ausgewählter Ordner lässt sich samt Unterstruktur bündeln. Vorher prüfen, ob Zugangsdaten, private Notizen oder unnötige Build-Dateien enthalten wären.

**Eigene Dateisammlung sichern:** Ein Archiv kann Teil einer Sicherung sein. Für wichtige Daten gehören ein unabhängiger Speicherort und eine tatsächlich geprüfte Wiederherstellung dazu.

**Einzelne Archivmitglieder untersuchen:** Zunächst die Namen auflisten und dann gezielt einen Eintrag in einen frischen Ordner entpacken. Der Mitgliedsname muss zur tatsächlichen Archivliste passen.

**Daten für einen Kompressor vorbereiten:** TAR übernimmt die Zusammenstellung, gzip oder XZ die anschließende Kompression. Fehler können auf beiden Ebenen auftreten.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Vorhandene Daten können überschrieben werden

Beim Erstellen ist der Archivname ein Schreibziel. Beim Entpacken sind es die Mitgliedspfade im Zielordner. Ein neuer Ausgabeordner und `--keep-old-files` verringern Namenskonflikte. Sie ersetzen keine Prüfung, ob überhaupt in den richtigen Ordner geschrieben wird.

### Unbekannte Archive brauchen zusätzliche Vorsicht

Archivnamen, Verknüpfungen und Metadaten können unerwartete Wirkungen haben. Nicht direkt in das Heimatverzeichnis oder ein bestehendes Projekt entpacken. `-P` zur Übernahme absoluter Namen und Optionen zum aggressiven Entfernen vorhandener Ziele gehören nicht in einen unbedachten Standardaufruf. Die aufgeführten Schutzoptionen sind keine Sandbox.

### Eine Liste ist keine vollständige Prüfung

Eine erfolgreiche Auflistung kann die erwarteten Namen zeigen, ohne jede Inhaltsveränderung nachzuweisen. Ein TAR-Headerprüfwert ist kein kryptografischer Herkunftsnachweis. Für eine wichtige Wiederherstellung zusätzlich bekannte Inhalte vergleichen und die Herkunft separat prüfen.

### Laufende Daten und besondere Metadaten

Dateien können sich während der Aufnahme verändern. Ein Archiv einer laufenden Datenbank ist deshalb nicht automatisch eine konsistente Datenbanksicherung. ACLs, erweiterte Attribute, Links und besondere Dateien verlangen passende Planung und gezielte Rücksicherungstests.

### Platz und Umgebungsoptionen

Eine kleine komprimierte Eingabe kann viel Ausgabespeicher benötigen. Außerdem können Umgebungsoptionen wie `TAR_OPTIONS` das Verhalten ergänzen. Bei überraschenden Ergebnissen die lokale Umgebung und Fehlermeldungen prüfen, statt Schutzmechanismen blind abzuschalten.

**Root-Rechte sind für alle gezeigten Übungen unnötig.** Eine Systemrücksicherung mit fremden Eigentümern, Geräten oder Mounts ist eine andere Aufgabe.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Archiv ist unerwartet leer oder falsch | Quelle und Archivargument verwechselt. | `-f`-Argument und nachfolgende Quellen getrennt prüfen. |
| Zielordner wird nicht gefunden | `-C` verweist auf einen nicht angelegten Ordner. | Ordner vorher bewusst erstellen. |
| Vorhandene Datei wird abgelehnt | `--keep-old-files` schützt das bestehende Ziel. | Frisches Ziel verwenden oder Konflikt einzeln klären. |
| Datei änderte sich beim Lesen | Quelle wurde parallel bearbeitet. | Konsistenten Aufnahmezeitpunkt beziehungsweise anwendungseigene Sicherung wählen. |
| Dekompression scheitert | Inhalt, gewählte Option oder benötigtes Programm passt nicht. | Tatsächliches Format und genaue Meldung prüfen. |
| Fehlende Rechte | Eingabe oder Ziel gehört nicht zum zugänglichen Bereich. | Pfade prüfen; nicht reflexartig `sudo` ergänzen. |

GNU tar unterscheidet erfolgreichen Abschluss, bestimmte Abweichungen und schwerwiegende Fehler. Auch ein vorhandenes Archiv kann unvollständig sein. Den Abschlussstatus zusammen mit den Meldungen und einer passenden Wiederherstellung beurteilen.

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Mit eigenen kleinen Testdaten und einem neuen Arbeitsordner beginnen.
2. Den Archivnamen immer ausdrücklich über `-f` angeben.
3. Das Archiv außerhalb der aufgenommenen Quellstruktur anlegen.
4. Relative Mitgliedspfade bevorzugen und zuerst auflisten.
5. In einen neuen Ordner ohne Root-Rechte entpacken.
6. Konflikte mit `--keep-old-files` sichtbar machen.
7. Mindestens eine bekannte Datei nach der Wiederherstellung vergleichen.
8. Ein vollständiges Sicherungsverfahren getrennt von dieser einfachen Übung planen.

**Prüfstand:** Mit GNU tar 1.35 wurden Erstellen, Auflisten und Entpacken einer eigenen kleinen Ordnerstruktur geprüft. Der wiederhergestellte Dateiinhalt war bytegleich. Eine nachträglich geänderte eigene Zieldatei blieb bei erneutem Entpacken mit `--keep-old-files` erhalten; der Aufruf meldete einen Fehler. gzip-komprimiertes Erstellen und Auflisten wurden ebenfalls geprüft. Keine praktischen Tests mit fremden Archiven, besonderen Metadaten, Systemrücksicherungen oder großen Datenmengen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gzip`, `bzip2`, `xz`, `zstd` | Komprimieren den von TAR zusammengestellten Datenstrom. |
| `cpio` | Anderes Archivwerkzeug mit eigenen Modi und Eingabekonventionen. |
| `zip`, `unzip` | Andere Archivfamilie mit eigenen Metadaten- und Kompressionsregeln. |
| `cmp` | Vergleicht zwei bekannte Dateien byteweise. |
| `rsync` | Überträgt beziehungsweise gleicht Dateibestände ab; kein austauschbarer TAR-Aufruf. |

Ausgangseintrag: Datensatz 14 in `index.json`. Der allgemeine Hilfe-Platzhalter wurde durch konkrete Betriebsarten, einen Wiederherstellungsablauf und die Grenzen einer einfachen Archivierung ersetzt.
