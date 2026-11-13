---
id: "timeshift"
name: "timeshift"
command: "timeshift"
category: "Backup & Sync"
language: "de"
root_required: true
risk_level: "danger"
tags: ["backup & sync", "timeshift"]
status: "Projektunterlagen und lokale Manpage geprüft; Snapshots und Restore praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 70
reviewed_at: "2026-11-13"
locally_checked_version: "Paket 24.01.1-1build2; lokale Manpage gelesen"
---

# timeshift – Systemzustände sichern und Wiederherstellung planen

## 1. Kurzbeschreibung

Timeshift hält Systemzustände fest, auf die man nach problematischen Änderungen zurückkehren kann. Der Schwerpunkt liegt auf Systemdateien und Einstellungen. **Snapshot-Erstellung und Systemwiederherstellung benötigen administrative Rechte.** Zum Lesen der Dokumentation ist Root nicht nötig.

Persönliche Dokumente sind nicht automatisch durch einen Timeshift-Stand geschützt. Ein Systemwiederherstellungspunkt ist deshalb kein Ersatz für eine gesonderte, geprüfte Dateisicherung.

## 2. Was macht der Befehl?

Timeshift unterstützt einen rsync-/Hardlink-Modus und einen Btrfs-Modus mit passenden Dateisystemvoraussetzungen. Die konkrete Einrichtung bestimmt Speicherort, Umfang, Zeitplanung und Aufbewahrung. Der [offizielle Linux-Mint-Projekttext](https://github.com/linuxmint/timeshift) beschreibt den Schwerpunkt und die Unterschiede.

Bei einer Wiederherstellung können heutige Systemdateien durch frühere Fassungen ersetzt werden. Dadurch verändern sich nicht nur sichtbare Einstellungen, sondern unter Umständen auch installierte Komponenten und deren zusammenpassender Zustand. Ein geeigneter Wiederanlaufplan ist deshalb Teil der Aufgabe. Ein Snapshot auf demselben defekten Laufwerk ist keine unabhängige Sicherung gegen dessen Ausfall.

## 3. Syntax

```text
timeshift --help
timeshift --list
timeshift --create [OPTIONEN]
timeshift --restore [OPTIONEN]
```

Dies sind Aufrufmuster. Sie sind keine gemeinsame ungefährliche Befehlsfolge. Insbesondere ist `--check` **kein rein lesender Gesundheitstest**: Es kann einen fälligen geplanten Snapshot erstellen. Die lokale Manpage zu Version 24.01.1 beschreibt dieses Verhalten ausdrücklich.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkrete Wirkung |
| --- | --- | --- |
| `--help` | Optionen anzeigen. | Geeigneter Einstieg zur Syntaxprüfung. |
| `--list` | Snapshots auflisten. | Zugriff auf konfigurierte Ablagen und Rechte separat beachten. |
| `--create` | Neuen Snapshot anlegen. | Schreibt Daten beziehungsweise Dateisystemzustand. |
| `--check` | Bei Fälligkeit geplanten Snapshot anlegen. | Nicht mit einem passiven Check verwechseln. |
| `--comments TEXT` | Beschreibung für einen Snapshot setzen. | Hilft bei späterer Zuordnung, beweist keine Integrität. |
| `--tags O` | On-Demand-Markierung verwenden. | Tags beeinflussen Einordnung und Aufbewahrung. |
| `--restore` | Wiederherstellung beginnen. | Kann das gesamte ausgewählte System verändern. |
| `--snapshot NAME` | Bestimmten Stand auswählen. | Namen und Herkunft vor Restore prüfen. |
| `--delete` | Einen Snapshot entfernen. | Verringert Wiederherstellungsmöglichkeiten. |
| `--yes` | Bestätigungsfragen automatisch bejahen. | Für erste Versuche ausdrücklich ungeeignet. |

Weitere Schalter wählen Zielgeräte, Bootloaderbehandlung und Modus. Sie nicht ohne Kenntnis von Layout und Auswirkungen kombinieren. Hilfe anderer Versionen kann abweichen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Einen Wiederherstellungsplan schreiben

Angenommen, vor einer geplanten Systemänderung soll eine Rückkehrmöglichkeit vorbereitet werden. Notiere zunächst den konkreten Zweck: etwa eine problematische Systemkonfiguration zurücksetzen. Für die gleichzeitig bearbeiteten persönlichen Dokumente eine eigene Dateisicherung einplanen.

### Schritt 2: Modus und Umfang klären

Vor einem realen Auftrag müsste geprüft werden, welcher Modus eingerichtet ist und welche Verzeichnisse eingeschlossen oder ausgeschlossen sind. Die [Projektbeschreibung](https://raw.githubusercontent.com/linuxmint/timeshift/master/README.md) nennt für Btrfs bestimmte Subvolume-Anforderungen. Das bloße Vorhandensein eines Btrfs-Dateisystems beweist noch keine passende Einrichtung.

### Schritt 3: Ziel und Platzbedarf prüfen

Ein Snapshotziel muss tatsächlich verfügbar sein und ausreichend Raum haben. Bei externen Medien deren konkrete Identität prüfen. Ein erfolgreich angelegter leerer Verzeichnispfad beweist nicht, dass das erwartete Medium eingebunden ist. Die nötige Geräteprüfung ist hier kein ausgeführter Teil des Beispiels.

### Schritt 4: Snapshot und Rückkehr voneinander trennen

Ein später ausdrücklich freigegebener Create-Lauf müsste anhand Abschlussmeldung und verfügbarem Stand geprüft werden. Eine sichere Wiederherstellungsprobe benötigt entbehrliche Testumgebung oder einen gesonderten abgestimmten Ablauf. Restore nicht als beiläufige „Funktionsprüfung“ des Produktivsystems starten.

### Schritt 5: Erwartetes Ergebnis benennen

Am Ende des Plans stehen ein eindeutig zugeordneter Systemstand, getrennte persönliche Datensicherung und ein nachvollziehbarer Wiederanlaufweg. Dieses Dokument erstellt keinen Snapshot. Der lokal durchgeführte Schritt bestand ausschließlich darin, die installierte Paketversion und vorhandene Manpage zu lesen.

## 6. Typische Anwendungsfälle

### Vor Systemänderungen

Ein vorhandener, getesteter Rückkehrweg kann beim Ausprobieren von Systemanpassungen helfen. Er ersetzt keine Prüfung, ob der gewünschte Zustand alle betroffenen Komponenten umfasst.

### Fehlerhafte Konfiguration zurücknehmen

Ein bekannter früherer Stand kann als Restore-Ziel dienen. Vorher prüfen, welche neueren Änderungen ebenfalls verloren gehen würden und ob zusätzliche persönliche Konfigurationen eingeschlossen sind.

### Nicht mehr startfähiges System

Ein vorbereitetes Live-System kann Teil der Wiederherstellungsplanung sein. Erforderliche Werkzeuge, Zugriff auf verschlüsselte Volumes und Bootkonfiguration müssen separat funktionieren; das ist durch eine Snapshotliste nicht nachgewiesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Restore kann Dateien ersetzen, Systemzustände ändern und Bootloaderaktionen erfordern. Falsches Zielgerät oder falscher Stand können schwerwiegende Folgen haben. Automatische Bestätigung überspringt Rückfragen und ist deshalb kein Komfortschalter für ungeprüfte Abläufe.

Persönliche Daten sind standardmäßig nicht der Schwerpunkt. Werden sie ausdrücklich eingeschlossen, können auch sie beim Zurücksetzen betroffen sein. Aufbewahrung und Löschen alter Stände beeinflussen die Rückkehrmöglichkeiten. Snapshots können vertrauliche Systemdaten enthalten und sind nicht allein durch den Namen verschlüsselt.

## 8. Häufige Fehler

- **`--check` als bloße Diagnose gestartet:** Der Aufruf kann einen fälligen Snapshot erstellen.
- **Dokumente als mitgesichert angenommen:** Ein- und Ausschlüsse tatsächlich prüfen.
- **Snapshot mit externem Backup verwechselt:** Gemeinsames Laufwerksrisiko bleibt möglich.
- **Btrfs-Modus funktioniert nicht:** Subvolume-Layout und Programmversion prüfen.
- **Falsche Rückkehr gewählt:** Beschreibung, Zeitpunkt und enthaltenen Zustand vergleichen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst Dokumentation und lokale Manpage lesen. Persönliche Dateien unabhängig sichern. Einen System-Restore nur als geplante Änderung mit eindeutigem Ziel und Wiederanlaufweg durchführen; nicht zur schnellen Prüfung eines Menüpunkts.

**Prüfstand:** Paketversion 24.01.1-1build2 festgestellt, lokale Manpage und offizielle Projektbeschreibung gelesen. Timeshift nicht ausgeführt. Keine Konfiguration, Snapshotliste, Geräte oder Benutzerdateien ausgewertet; kein Create-, Check-, Delete- oder Restore-Lauf. Praktische Wiederherstellung und konkrete Systemeignung bleiben offen.

## 10. Verwandte Befehle

- `restic`, `borg`: versionierte persönliche Dateisicherungen.
- `deja-dup`: grafische Dateisicherung mit versionsabhängigem Backend.
- `rsnapshot`: dateibasierte Sicherungsstände über rsync und Hardlinks.
- `clonezilla`: Datenträgerabbilder mit anderem Wiederherstellungsumfang.

Ausgangseintrag: Datensatz 70 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
