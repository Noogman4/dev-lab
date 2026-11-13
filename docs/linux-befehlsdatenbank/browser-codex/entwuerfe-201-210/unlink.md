---
id: "unlink"
name: "unlink"
command: "unlink"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "danger"
tags: ["dateien", "loeschen", "links"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 204
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# unlink – Einen Dateinamen entfernen

## 1. Kurzbeschreibung

`unlink` entfernt **einen** Verzeichniseintrag für eine Datei oder einen symbolischen Link. Das ist ein Löschvorgang ohne Papierkorb. Für eine eigene Datei in einem beschreibbaren Verzeichnis ist **kein Root nötig**.

## 2. Was macht der Befehl?

GNU `unlink` ruft die gleichnamige Systemfunktion auf. Bei mehreren Hardlinks bleibt der Dateiinhalt über andere Namen erreichbar; bei letztem Link und keinem offenen Dateizugriff kann Speicher freigegeben werden. Ein Symlink wird selbst entfernt, nicht sein Ziel. Ein gewöhnliches Verzeichnis kann damit nicht entfernt werden. Siehe [GNU-coreutils-Manpage](https://manpages.debian.org/trixie/coreutils/unlink.1.en.html).

## 3. Syntax

```bash
unlink DATEI
unlink -- "testlink"
```

GNU `unlink` akzeptiert genau einen Dateioperanden; es besitzt **keine** Optionen `-i`, `-r` oder `-f` wie `rm`.

## 4. Wichtige Optionen

| Argument/Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `DATEI` | Genau ein zu entfernender Pfad. | Keine Rückfrage. |
| `--help` | Hilfe anzeigen. | Kein Löschvorgang. |
| `--version` | Version anzeigen. | Kein Löschvorgang. |
| `--` | Optionsende (GNU-Konvention). | Pfad danach eindeutig angeben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Wegwerfbare Übungsdaten

```bash
uebung="$(mktemp -d -t netmon-unlink-XXXXXX)"
printf 'Test\n' > "$uebung/ziel.txt"
ln -s ziel.txt "$uebung/verknuepfung"
ls -l -- "$uebung/verknuepfung"
```

### Schritt 2: Nur den Symlink entfernen

```bash
unlink -- "$uebung/verknuepfung"
```

### Schritt 3: Ziel weiterhin nachweisen

```bash
cat -- "$uebung/ziel.txt"
```

Der Inhalt der eigenen `ziel.txt` bleibt erhalten. Das Beispiel wurde **nicht ausgeführt**. Bei einem normalen Dateinamen statt des Symlinks würde `unlink` diesen Namen löschen.

## 6. Typische Anwendungsfälle

**Kaputte Symlinks aufräumen:** Genau einen vorher geprüften Link entfernen. **Skripte:** Einen bekannten temporären Dateinamen gezielt löschen. Für mehrere Dateien ist `unlink` keine geeignete Sammeloperation.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Entfernen des letzten Dateinamens kann Daten unwiederbringlich unzugänglich machen. Die Rechte am **Elternverzeichnis** sind entscheidend, nicht nur die Dateirechte; Sticky-Bit-Regeln können eingreifen. Rennen zwischen Prüfung und Löschung sind möglich. Keine interaktive Sicherheitsfrage, kein rekursives Löschen. `sudo` nicht leichtfertig verwenden.

## 8. Häufige Fehler

| Fehler | Ursache | Vorgehen |
| --- | --- | --- |
| `Is a directory` | Verzeichnis statt Datei. | Nicht mit `unlink` entfernen. |
| `No such file` | Pfad fehlt / Link schon entfernt. | Pfad einzeln prüfen. |
| `Permission denied` | Elternverzeichnis nicht beschreibbar. | Rechte verstehen, nicht blind erhöhen. |
| Ziel statt Link weg | Falscher Pfad übergeben. | `ls -ld` vorab prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Bei Unsicherheit zunächst `ls -ld -- PFAD` und `readlink -- PFAD` ausführen. Die Übung ausschließlich mit selbst erzeugten Links durchführen. Einen echten Löschvorgang nicht als Test auf vorhandene Dateien verwenden.

**Prüfstand:** GNU-coreutils-9.7-Manpage am 2026-11-13 gelesen. Keine Löschtests, keine lokale Version und kein Wiederherstellungstest.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `rm` | Mehr Optionen, ebenfalls destruktiv. |
| `readlink` | Symlink-Ziel anzeigen. |
| `ln` | Hardlinks oder Symlinks erstellen. |
| `rmdir` | Leere Verzeichnisse entfernen. |

**Ausgangseintrag:** `source_record` 204 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
