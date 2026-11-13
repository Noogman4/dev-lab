---
id: "borg"
name: "borg"
command: "borg"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "borg"]
status: "Quellen geprüft; Backup und Wiederherstellung praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 61
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Dokumentation für Borg 1.x geprüft"
---

# borg – Verschlüsselte und deduplizierte Dateisicherungen

## 1. Kurzbeschreibung

BorgBackup erstellt versionierte Sicherungen von Dateien und Verzeichnissen. Es kann Daten komprimieren, verschlüsseln und gleiche Datenstücke mehrfacher Sicherungen gemeinsam speichern. **Für eigene lesbare Dateien und ein beschreibbares Sicherungsziel ist Root nicht nötig.** Eine Systemvollsicherung benötigt gesonderte Rechte und Planung.

Diese Anleitung beschreibt **Borg 1.x**. Borg 2 hat geänderte Befehle und Repository-Konzepte; Syntax nicht zwischen Hauptversionen mischen. Vor Verwendung `borg --version` prüfen. Das [offizielle Schnellstart-Handbuch](https://borgbackup.readthedocs.io/en/stable/quickstart.html) liefert die hier verwendete Grundlage.

## 2. Was macht der Befehl?

Ein Repository ist der Speicherbehälter. Darin liegen benannte Archive, also Sicherungsstände. Deduplizierung spart Platz, wenn Datenstücke schon vorhanden sind. Ein neues Archiv verweist dann teilweise auf vorhandene Daten. Das ist keine gewöhnliche Ordnerkopie und kein Systemstart-Abbild.

Verschlüsselung schützt den Inhalt bei Verlust des Sicherungsspeichers. Sie ersetzt weder ein getrenntes Backupmedium noch die Aufbewahrung von Schlüssel und Passphrase. Fehlen die nötigen Geheimnisse, kann auch der Eigentümer seine Sicherung nicht wiederherstellen. Eine erfolgreiche Sicherung ist deshalb erst zusammen mit einer geprüften Rücksicherung praktisch bewertbar.

## 3. Syntax

```text
borg [GLOBALE_OPTIONEN] UNTERBEFEHL [OPTIONEN] ...
borg init --encryption=repokey REPOSITORY
borg create REPOSITORY::ARCHIV PFAD ...
borg list REPOSITORY
borg extract REPOSITORY::ARCHIV [ARCHIVPFAD ...]
```

`REPOSITORY::ARCHIV` ist die Borg-1-Schreibweise. Archivpfade beziehen sich auf den gespeicherten Inhalt; nicht blind den ursprünglichen absoluten Quellpfad einsetzen. Wiederherstellung erfolgt relativ zum aktuellen Arbeitsverzeichnis.

## 4. Wichtige Optionen

| Aufruf oder Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `init --encryption=repokey` | Verschlüsseltes Repository initialisieren. | Passphrase und separaten Schlüsselexport einplanen. |
| `create --stats` | Sicherung mit Statistik erstellen. | Gemeldete Deduplizierung ist keine Vollständigkeitsprüfung. |
| `create --dry-run` | Geplante Dateiauswahl prüfen. | Nicht mit `--stats` kombinieren; kein neues Backup. |
| `create --exclude MUSTER` | Passende Pfade ausschließen. | Borg-Mustersyntax prüfen und Auswahl kontrollieren. |
| `create --one-file-system` | Bestimmte Dateisystemgrenzen beachten. | Bind-Mounts und Subvolumes erfordern besondere Prüfung. |
| `extract --dry-run` | Extraktion prüfen, ohne Zieldateien zu schreiben. | Kein Ersatz für eine echte Proberücksicherung. |
| `extract --list` | Bearbeitete Archivpfade anzeigen. | Zieldateien können trotzdem geschrieben werden. |

Die [create-Referenz](https://borgbackup.readthedocs.io/en/stable/usage/create.html) beschreibt Auswahl und Statistik, die [extract-Referenz](https://borgbackup.readthedocs.io/en/stable/usage/extract.html) das Wiederherstellungsverhalten. Optionen gelten jeweils für den genannten Unterbefehl.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Ausschließlich eigene Übungsdaten anlegen

Das folgende Beispiel ist für eine separate Bash-Sitzung mit installiertem Borg 1 gedacht. Es wurde hier nicht ausgeführt. Nicht in einen bestehenden Repository-Pfad umschreiben.

```bash
(
  uebung="$(mktemp -d -t netmon-borg-XXXXXX)" || exit 1
  export BORG_CACHE_DIR="$uebung/cache"
  export BORG_CONFIG_DIR="$uebung/config"
  export BORG_SECURITY_DIR="$uebung/security"
  mkdir "$uebung/daten" "$uebung/rueckgabe" || exit 1
  printf 'Eigene Testnotiz\n' > "$uebung/daten/notiz.txt" || exit 1
  cd "$uebung" || exit 1
  borg init --encryption=repokey "$uebung/repo" || exit 1
  borg create --stats "$uebung/repo::probe" daten || exit 1
  borg list "$uebung/repo::probe" || exit 1
  cd "$uebung/rueckgabe" || exit 1
  borg extract "$uebung/repo::probe" || exit 1
  cmp -- "$uebung/daten/notiz.txt" "$uebung/rueckgabe/daten/notiz.txt"
)
```

### Schritt 2: Die einzelnen Wirkungen verstehen

`mktemp` erzeugt einen neuen privaten Ordner. Die Umgebungsvariablen verlagern Begleitdateien des Beispiels dorthin. `init` erstellt das Repository und fragt nach einer Passphrase. Diese bewusst wählen und nicht als Klartext in eine Befehlszeile schreiben.

`create` speichert das relative Verzeichnis `daten` unter dem Archivnamen `probe`. `list` muss dessen Datei zeigen. Vor `extract` wird in einen neuen Rückgabeordner gewechselt; dadurch wird nicht auf die ursprüngliche Testdatei zurückgeschrieben. Ein stilles `cmp` mit Rückgabewert 0 bedeutet, dass die beiden Testdateien denselben Inhalt haben. Es beweist keine vollständige Sicherung anderer Daten oder Metadaten.

## 6. Typische Anwendungsfälle

### Tägliche Dokumentstände

Getrennte Archivnamen ermöglichen, eine versehentlich überschriebene Datei aus einem älteren Stand zurückzuholen. Aufbewahrungsfristen bewusst festlegen, statt nur unbegrenzt anzusammeln.

### Externes oder entferntes Sicherungsziel

Ein getrenntes Medium schützt gegen den Ausfall des Quelllaufwerks. Entfernte Repositories über SSH benötigen zusätzlich sichere Anmeldung, passende Rechte und Netzwerkplanung; das lokale Beispiel prüft dies nicht.

## 7. Risiken, Nebenwirkungen und Vorsicht

`prune`, `delete` und `compact` beeinflussen Aufbewahrung und belegten Speicher. Sie gehören nicht in einen unkontrolliert übernommenen Erstversuch. Bei Deduplizierung können beschädigte gemeinsam genutzte Daten mehrere Archive betreffen.

Wachsende oder geöffnete Dateien können einen inkonsistenten Stand ergeben, insbesondere Datenbanken. Anwendungsgeeignete Exporte oder geplante Snapshots sind dafür separat nötig. Keine fremden Spezialdateien mit `--read-special` einbeziehen. Beim Extrahieren können vorhandene Dateien überschrieben werden; deshalb zunächst in ein leeres Ziel zurücksichern.

## 8. Häufige Fehler

- **Archiv existiert schon:** Für eine neue Sicherung einen neuen Namen verwenden.
- **Pfad fehlt im Archiv:** Relative Pfade, Ausschlüsse und fehlende Leserechte prüfen.
- **Passphrase bekannt, Wiederherstellung scheitert:** Benötigter Schlüssel oder Repository beschädigt; separate Schlüsselvorsorge ist wichtig.
- **Speicher unerwartet voll:** Repository, Cache und freier Platz für Wartung getrennt betrachten.
- **Syntax aus anderer Anleitung funktioniert nicht:** Borg-Hauptversion vergleichen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst kleine Dateien sichern, auflisten und in ein leeres Ziel zurückholen. Danach wichtige Metadaten, Ausschlüsse und Aufbewahrung gezielt testen. Schlüssel außerhalb des einzigen Repository-Datenträgers geschützt sichern.

**Prüfstand:** Offizielle Borg-1.x-Dokumentation gelesen; Borg lokal nicht installiert. Beispiel, Verschlüsselung, Repository-Anlage, Wiederherstellung und SSH-Betrieb wurden nicht praktisch geprüft. Das Dokument bestätigt keinen bestehenden Sicherungszustand.

## 10. Verwandte Befehle

- `restic`: anderes verschlüsseltes Sicherungssystem, eigenes Repositoryformat.
- `rsync`: Dateisynchronisation; allein keine automatische Versionshistorie.
- `tar`: Archivdateien statt dedupliziertem Repository.
- `duplicity`: dateibasierte Sicherungsketten mit eigenem Aufbewahrungsmodell.
- `cmp`: Inhalt zweier Dateien vergleichen.

Ausgangseintrag: Datensatz 61 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
