---
id: "rsnapshot"
name: "rsnapshot"
command: "rsnapshot"
category: "Backup & Sync"
language: "de"
root_required: false
risk_level: "caution"
tags: ["backup & sync", "rsnapshot"]
status: "Quellen geprüft; eigene Konfiguration und Rotation praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 69
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Distributions-Manpage geprüft"
---

# rsnapshot – Sicherungsstände mit rsync und Hardlinks verwalten

## 1. Kurzbeschreibung

`rsnapshot` verwaltet mehrere dateibasierte Sicherungsstände mithilfe von `rsync` und Hardlinks. Unveränderte Dateien können zwischen Ständen denselben gespeicherten Inhalt teilen. **Für eigene zugängliche Dateien und ein eigenes Sicherungsziel ist Root nicht grundsätzlich nötig.** Systemweite Sicherungsaufträge haben andere Rechteanforderungen.

Der Begriff Snapshot bedeutet hier nicht automatisch einen atomaren Dateisystemsnapshot. Die Quelldateien werden in einem zeitlich ablaufenden Sicherungsvorgang gelesen; Änderungen währenddessen müssen gesondert berücksichtigt werden.

## 2. Was macht der Befehl?

Eine Konfigurationsdatei bestimmt Quelle, Speicherort, aufbewahrte Stufen und weitere Werkzeuge. Ein Aufruf mit einem Stufennamen, beispielsweise `alpha`, führt die dafür vorgesehene Sicherung oder Rotation aus. Namen wie `daily` sind keine eingebauten Zeitgeber. Ein Zeitplan benötigt zusätzlich einen bewusst eingerichteten Scheduler.

Die [Distributions-Manpage](https://manpages.debian.org/trixie/rsnapshot/rsnapshot.1.en.html) beschreibt alternative Konfigurationen und Hardlinks. Werden zwei Sicherungspfade hart auf dieselbe Datei verlinkt, kann eine nachträgliche Änderung dieses Inhalts mehrere scheinbar getrennte Stände betreffen. Deshalb Sicherungsstände nicht wie normale Arbeitsordner bearbeiten.

## 3. Syntax

```text
rsnapshot -c EIGENE_KONFIGURATION configtest
rsnapshot -c EIGENE_KONFIGURATION -t STUFE
rsnapshot -c EIGENE_KONFIGURATION STUFE
```

Ohne `-c` wird üblicherweise die systemweite Konfiguration verwendet. Der erste Übungsaufruf sollte deshalb immer die eigene Datei ausdrücklich nennen. Der Stufenname muss zu einem `retain`-Eintrag dieser Konfiguration passen.

## 4. Wichtige Optionen

| Option oder Konfiguration | Bedeutung | Hinweis |
| --- | --- | --- |
| `-c DATEI` | Andere Konfiguration auswählen. | Keine fremde ungeprüfte Konfiguration übernehmen. |
| `-t` | Geplante Kommandos anzeigen. | Vorschau, kein ausgeführtes Backup. |
| `-v` | Ausgeführte Kommandos ausführlicher anzeigen. | Hebt Schreib- oder Löschwirkung nicht auf. |
| `configtest` | Konfiguration auf erkennbare Fehler prüfen. | Keine vollständige Wiederherstellungsprüfung. |
| `snapshot_root` | Ablage der Sicherungsstände. | Sollte unabhängig von der Quelle sein. |
| `retain alpha 2` | Zwei Stände dieser Stufe aufbewahren. | Ältere Stände können bei Rotation entfallen. |
| `backup` | Quellpfad und relativen Zielbereich festlegen. | Quell-/Zielbedeutung sorgfältig lesen. |
| `no_create_root` | Automatische Erzeugung des Sicherungswurzelordners steuern. | Kann bei erwarteten Wechselmedien vor falscher Ersatzablage helfen. |

Konfigurationseinträge werden mit Tabulatoren getrennt, nicht beliebig mit Leerzeichen. Zusätzliche Hooks oder dynamische Includes können Befehle ausführen; eine Konfiguration ist nicht automatisch passives, vertrauenswürdiges Datenmaterial.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigene isolierte Konfiguration erzeugen

Das Beispiel setzt installiertes rsnapshot und `/usr/bin/rsync` voraus. Es wurde hier nicht ausgeführt. Es plant nur kleine eigene Testdaten und startet keine echte Sicherung.

```bash
(
  uebung="$(mktemp -d -t netmon-rsnapshot-XXXXXX)" || exit 1
  mkdir "$uebung/daten" "$uebung/snapshots" || exit 1
  printf 'Testnotiz\n' > "$uebung/daten/notiz.txt" || exit 1
  printf 'config_version\t1.2\nsnapshot_root\t%s/snapshots/\ncmd_rsync\t/usr/bin/rsync\nretain\talpha\t2\nlockfile\t%s/rsnapshot.pid\nlogfile\t%s/rsnapshot.log\nbackup\t%s/daten/\tlokal/\n' \
    "$uebung" "$uebung" "$uebung" "$uebung" > "$uebung/probe.conf" || exit 1
  rsnapshot -c "$uebung/probe.conf" configtest || exit 1
  rsnapshot -c "$uebung/probe.conf" -t alpha
)
```

### Schritt 2: Ausgabe einordnen

`printf` schreibt echte Tabulatoren in die eigene Konfiguration. `snapshot_root`, Lockdatei und Logdatei zeigen ausschließlich in den Übungsordner. `configtest` sollte die Konfiguration akzeptieren. Fehlende Werkzeuge oder versionsabhängige Anforderungen zuerst klären, statt Fehlermeldungen zu unterdrücken.

### Schritt 3: Vorschau prüfen

`-t alpha` zeigt die geplanten Befehle. Deren Quellen und Ziele müssen zum eigenen Übungsordner passen. Ein tatsächlich geschriebenes Backup wird hier nicht erwartet. Für einen späteren echten Laborlauf müsste bewusst derselbe Aufruf ohne `-t` geplant und danach Inhalt, Aufbewahrung und Rückgabe geprüft werden.

Die Vorschau darf nicht mit einer fremden Konfiguration als risikofrei angesehen werden: Dynamische Konfigurationsteile und Hooks erfordern vorherige Prüfung. Das Beispiel erzeugt ausdrücklich selbst eine einfache Datei ohne solche Zusätze.

## 6. Typische Anwendungsfälle

### Mehrere Dateistände behalten

Ältere Versionen bleiben als durchsuchbare Verzeichnisbäume verfügbar. Speicherverbrauch hängt von Änderungen und gemeinsam genutzten Dateien ab.

### Geplante Rotation

Häufige und seltenere Stufen können unterschiedliche Aufbewahrung ermöglichen. Reihenfolge und Zuordnung der Stufen verstehen; ein Name allein startet keinen regelmäßigen Auftrag.

### Entfernte Quellen

Rsync über SSH kann entfernte Dateien einbeziehen. Das verlangt zusätzliche Anmeldung und Rechte und ist im lokalen Beispiel nicht geprüft.

## 7. Risiken, Nebenwirkungen und Vorsicht

Rotation kann alte Stände löschen. Ein falscher `snapshot_root` oder eine unbeabsichtigt verwendete Systemkonfiguration kann damit wichtige Sicherungen betreffen. Nicht mit `sudo` starten, nur weil ein eigener Testpfad falsch gewählt wurde.

Hardlinks sind kein Kopierschutz: Inhalte nicht direkt im Sicherungsbestand editieren oder rekursiv Rechte ändern. Eine Rückgabe zunächst in einen getrennten Ordner kopieren. Unverschlüsselte Sicherungsdateien bleiben bei Verlust des Mediums lesbar. Ein Ausfall des einzigen gemeinsamen Quell- und Sicherungslaufwerks kann beide Bestände vernichten.

## 8. Häufige Fehler

- **Syntaxfehler in der Konfiguration:** Leerzeichen statt erforderlicher Tabulatoren verwendet.
- **Unbekannte Stufe:** Aufrufname stimmt nicht mit `retain` überein.
- **Keine tägliche Ausführung:** Stufenname und Scheduler verwechselt.
- **Alte Stände unerwartet verändert:** Gemeinsam hart verlinkte Inhalte nachträglich bearbeitet.
- **Backup liegt auf falschem Medium:** Erwartetes Ziel war nicht verfügbar; tatsächlichen Pfad und Mountzustand separat prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Immer mit eigener Konfiguration, `configtest` und Vorschau beginnen. Aufbewahrung an entbehrlichen Daten verstehen, bevor echte Bestände aufgenommen werden. Eine Wiederherstellungsprobe gehört zusätzlich zur reinen Rotationserprobung.

**Prüfstand:** Distributions-Manpage gelesen. rsnapshot lokal nicht installiert. Konfiguration, Vorschau, Sicherung und Rotation nicht praktisch ausgeführt. Keine Systemkonfiguration oder Zeitplanung geändert. Hardlinkverhalten im konkreten Sicherungsablauf und Rückgabe bleiben offen.

## 10. Verwandte Befehle

- `rsync`: übernimmt die eigentliche Dateisynchronisation.
- `cp -a`: Dateien mit Metadaten kopieren, abhängig von Rechten und Zielsystem.
- `borg`, `restic`: verschlüsselte Repositorysicherungen mit anderer Ablage.
- `timeshift`: Systemwiederherstellung statt allgemeiner persönlicher Dateisicherung.

Ausgangseintrag: Datensatz 69 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
