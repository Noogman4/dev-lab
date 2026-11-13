---
id: "restic"
name: "restic"
command: "restic"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "restic"]
status: "Quellen geprüft; Repository, Sicherung und Rücksicherung praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 68
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; offizielle restic-Dokumentation geprüft"
---

# restic – Verschlüsselte Snapshots sichern und gezielt zurückholen

## 1. Kurzbeschreibung

`restic` erstellt verschlüsselte, versionierte Dateisicherungen in einem Repository. Ein gespeicherter Stand heißt Snapshot. Deduplizierung kann mehrfach vorkommende Daten gemeinsam speichern. **Für eigene lesbare Dateien und ein eigenes beschreibbares Ziel sind keine Root-Rechte nötig.**

Ein restic-Snapshot ist nicht automatisch ein Btrfs-Dateisystemsnapshot und kein bootfähiges Datenträgerimage. Die Wiederherstellung einzelner Dateien ist eine andere Aufgabe als die vollständige Wiederinbetriebnahme eines Betriebssystems.

## 2. Was macht der Befehl?

`init` legt ein neues Repository an. `backup` liest ausgewählte Daten und schreibt einen Sicherungsstand. `snapshots` listet vorhandene Stände, `ls` deren Inhalte. `restore` schreibt ausgewählte Sicherungsdaten in ein Ziel zurück.

Die [Repository-Anleitung](https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html) beschreibt Passwort und Initialisierung. Daten und Metadaten im Repository sind gemeinsam aufzubewahren. Ein verlorenes Passwort kann die Rückgabe verhindern. Verschlüsselung schützt nicht gegen das Löschen des gesamten Repositorys durch einen Angreifer mit entsprechenden Speicherrechten.

## 3. Syntax

```text
restic -r REPOSITORY init
restic -r REPOSITORY backup PFAD ...
restic -r REPOSITORY snapshots
restic -r REPOSITORY ls SNAPSHOT
restic -r REPOSITORY restore SNAPSHOT --target NEUER_ORDNER
```

Die Repositoryangabe muss zum gewünschten Sicherungsbestand passen. `latest` ist ein auswählbarer jüngster Snapshot, aber in gemeinsam genutzten Repositories nicht unbedingt der gewünschte Stand. Für echte Rückgaben zunächst Snapshot-ID und enthaltene Pfade prüfen.

## 4. Wichtige Optionen

| Option oder Unterbefehl | Bedeutung | Grenze |
| --- | --- | --- |
| `-r`, `--repo` | Repository auswählen. | Falsches Ziel bedeutet falschen Sicherungsbestand. |
| `--cache-dir PFAD` | Lokalen Cache verlagern. | Cache ist nicht das eigentliche Backup. |
| `backup --dry-run` | Geplante Sicherung ohne Repositoryänderung prüfen. | Keine tatsächlich lesbare neue Sicherung. |
| `backup --exclude MUSTER` | Bestimmte Pfade ausnehmen. | Auswahl danach bewusst kontrollieren. |
| `restore --target PFAD` | Rückgabeordner festlegen. | Darin können Dateien geschrieben oder ersetzt werden. |
| `restore --include MUSTER` | Teilmenge des Snapshotinhalts wählen. | Muster auf archivinterne Pfade beziehen. |
| `check` | Repositorystruktur prüfen. | Vollständiges Datenlesen ist eine zusätzliche Prüfstufe. |
| `--password-file DATEI` | Passwort aus Datei beziehen. | Datei und Zugriffsrechte müssen geschützt sein. |

Die [Backup-Referenz](https://restic.readthedocs.io/en/stable/040_backup.html) erklärt relative und absolute Pfade. Die [Restore-Anleitung](https://restic.readthedocs.io/en/stable/050_restore.html) unterscheidet Snapshotauswahl und Auswahl einzelner Inhalte. Beispielsweise beschränkt `--path` bei der Snapshotauswahl nicht automatisch den gesamten zurückgeschriebenen Inhalt.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur eine kleine Testdatei verwenden

Das folgende Beispiel ist für ein installiertes restic gedacht. Es wurde hier nicht ausgeführt. Das Programm fragt interaktiv nach dem gewählten Repositorypasswort; dieses nicht in den Code schreiben.

```bash
(
  uebung="$(mktemp -d -t netmon-restic-XXXXXX)" || exit 1
  mkdir "$uebung/daten" || exit 1
  printf 'Eigene Testnotiz\n' > "$uebung/daten/notiz.txt" || exit 1
  cd "$uebung" || exit 1
  rest=(restic -r "$uebung/repo" --cache-dir "$uebung/cache")
  "${rest[@]}" init || exit 1
  "${rest[@]}" backup daten || exit 1
  "${rest[@]}" snapshots || exit 1
  "${rest[@]}" ls latest || exit 1
  "${rest[@]}" restore latest --target "$uebung/rueckgabe" || exit 1
  cmp -- "$uebung/daten/notiz.txt" "$uebung/rueckgabe/daten/notiz.txt"
)
```

### Schritt 2: Speicherrollen verstehen

`repo` ist die neue Sicherungsablage, `cache` nur lokaler Hilfsspeicher. Das Bash-Array `rest` bündelt den gemeinsamen Aufruf; `"${rest[@]}"` erhält die getrennten Argumente korrekt. Der Quellordner wird relativ als `daten` übergeben. Dadurch ist diese Struktur auch im Snapshot zu erwarten.

### Schritt 3: Rückgabe prüfen

Da das Repository neu ist und nur ein Beispielsnapshot erzeugt wurde, ist `latest` hier eindeutig genug. In einer echten gemeinsamen Ablage stattdessen den gewollten Stand ausdrücklich bestimmen. Die Rückgabe landet in einem neuen Ordner. Ein stilles `cmp` mit Status 0 würde die Inhaltsgleichheit dieser Testdatei bestätigen, nicht die Vollständigkeit aller Sicherungen oder Metadaten.

## 6. Typische Anwendungsfälle

### Versionierte persönliche Dateien

Mehrere Stände ermöglichen, eine frühere Dateifassung gezielt zurückzuholen. Das erfordert, dass der betreffende Snapshot noch aufbewahrt und sein Repository lesbar ist.

### Getrennte Sicherungsablage

Ein eigenes externes oder entferntes Ziel kann Schäden am Quelllaufwerk abfangen. Entfernter Zugriff erfordert zusätzlich geprüfte Anmeldung, Transport- und Speicherrechte.

### Sicherungen kontrollieren

Die [Repository-Verwaltung](https://restic.readthedocs.io/en/stable/045_working_with_repos.html) beschreibt Auflistung und Prüfungen. Strukturprüfung, Datenprüfung und tatsächlich erfolgreiche Rücksicherung sind verschiedene Nachweise.

## 7. Risiken, Nebenwirkungen und Vorsicht

`forget` verändert Aufbewahrungsstände, `prune` entfernt nicht mehr benötigte Repositorydaten. Beide Aktionen können die verfügbaren Wiederherstellungsmöglichkeiten verringern. Sie gehören nicht als automatische Ergänzung in einen ungetesteten Erstlauf.

Bei laufenden Datenbanken oder gleichzeitig geänderten Dateien ist Anwendungskonsistenz gesondert zu planen. Eine Sicherung auf demselben einzigen Laufwerk bietet keine unabhängige Ausfallreserve. Zugangsdaten und Repositorypasswort getrennt schützen. Netzwerkbackends können Kosten und Bandbreite verursachen; dies ist kein Bestandteil des lokalen Beispiels.

## 8. Häufige Fehler

- **Falscher Inhalt mit `latest`:** Es war ein anderer Host oder Pfad zuletzt gesichert worden.
- **Rückgabe verschachtelt:** Absolute Archivpfade und relative Quellpfade verwechselt.
- **Passwortdatei fehlt:** Repositorydaten allein reichen nicht zur Entschlüsselung.
- **Snapshotliste als Datenprüfung angesehen:** Auflistung liest nicht zwingend sämtliche gespeicherten Nutzdaten.
- **Cache gelöscht und Backup verloren vermutet:** Repository und lokalen Cache auseinanderhalten.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst eine eigene Testdatei sichern, den Snapshotinhalt ansehen und in eine neue Ablage zurückholen. Für echte Daten eine geeignete Passwortvorsorge und getrennte Aufbewahrung festlegen. Löschende Wartung erst nach verstandenem Aufbewahrungsmodell planen.

**Prüfstand:** Offizielle Repository-, Backup-, Restore- und Verwaltungsanleitungen gelesen. restic lokal nicht installiert. Kein Repository angelegt, kein Passwort gespeichert, keine Sicherung oder Rücksicherung ausgeführt. Beispiel und Backend-Kompatibilität praktisch offen.

## 10. Verwandte Befehle

- `borg`: anderes dedupliziertes Repositoryformat.
- `duplicity`: Voll-/Inkrementketten mit anderem Aufbewahrungsmodell.
- `rclone`: Übertragung und Abgleich; allein keine gleiche Versionshistorie.
- `cmp`: Inhalt zweier eigener Dateien vergleichen.

Ausgangseintrag: Datensatz 68 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
