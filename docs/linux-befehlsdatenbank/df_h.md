---
id: "df_h"
name: "df -h"
command: "df -h"
category: "Aufgabenorientierte Hilfe"
language: "de"
root_required: false
risk_level: "safe"
tags: ["aufgabenorientierte hilfe", "df_h"]
status: "Ausgearbeitet; Abfrage am eigenen temporären Testpfad geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 53
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils df 9.4"
---

# df -h – Freien Platz des richtigen Dateisystems beurteilen

## 1. Kurzbeschreibung

`df -h` zeigt belegten und verfügbaren Platz von Dateisystemen mit gut lesbaren Größenangaben. `-h` ist die Darstellungsoption des Programms `df`, kein eigener Größenmessbefehl für einzelne Ordner.

**Für normale Abfragen zugänglicher Pfade sind keine Root-Rechte nötig.** Der übliche Aufruf verändert keine Dateien. Ein ausdrücklich angegebener Pfad hilft, das tatsächlich relevante Dateisystem zu betrachten.

## 2. Was macht der Befehl?

Df fragt die Platzstatistik des Dateisystems ab, auf dem ein gegebener Pfad liegt. Wird eine Datei angegeben, erscheint damit nicht deren Dateigröße, sondern die Statistik ihres Dateisystems. Ohne Pfadangabe werden die im aktuellen Kontext sichtbaren eingehängten Dateisysteme betrachtet.

Wichtige Angaben sind Gesamtgröße, benutzt, verfügbar, Nutzungsgrad und Einhängepunkt. Die verfügbaren Bytes müssen wegen Reservierungen und Dateisystemregeln nicht einfach Gesamtgröße minus benutzt entsprechen. Der aktuelle Mount-Namespace kann beeinflussen, was sichtbar ist.

Grundlagen: [Distributions-Manpage zu df](https://manpages.debian.org/trixie/coreutils/df.1.en.html) und die lokale Hilfe von coreutils 9.4. Das konkrete Dateisystem kann zusätzliche Quoten-, Snapshot- oder Poolregeln besitzen, die eine einfache Übersicht nicht vollständig erklärt.

## 3. Syntax

```text
df -h [PFAD ...]
```

```bash
df -h .
df -h "/PFAD/ZUR/DATEI"
```

Die zweite Zeile enthält einen bewusst zu ersetzenden Pfad. Beide Formen fragen das jeweils zugehörige Dateisystem ab. Ohne vorhandenen passenden Mount sieht man möglicherweise die darunterliegende lokale Partition statt des erwarteten Datenträgers.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-h`, `--human-readable` | Größen auf Basis 1024 darstellen. | Gerundete Einheiten sind nicht exakte Bytes. |
| `-H`, `--si` | Basis 1000 verwenden. | Andere Zahlen trotz gleichem realem Platz. |
| `-T` | Dateisystemtyp anzeigen. | Hilft bei passender Interpretation. |
| `-i` | Inode-Nutzung statt Blockplatz anzeigen. | Für viele kleine Dateien relevant. |
| `-P` | POSIX-Ausgabeformat. | Für bewusstes Textformat; nicht mit jeder Output-Option kombinieren. |
| `--output=FELDER` | Spalten gezielt wählen. | GNU-spezifisch; lokale Felder prüfen. |
| `-l` | Lokale Dateisysteme begrenzen. | Keine Garantie, dass jedes gewünschte Medium darunter fällt. |
| `-t TYP`, `-x TYP` | Bestimmten Typ ein- beziehungsweise ausschließen. | Kann wichtige sichtbare Einträge ausblenden. |
| `--sync` | Vor der Abfrage synchronisieren. | Zusätzliche Systemwirkung und möglicher Aufwand; für die Übung nicht verwendet. |
| `--no-sync` | Kein vorangestelltes Sync. | Normaler Standard der dokumentierten GNU-Version. |
| `--help`, `--version` | Hilfe und Version. | Verfügbare Funktionen prüfen. |

Ein sinnvoller ausgewählter Bericht kann die Felder `source,size,avail,pcent,target` enthalten. Zahlenformat und Übersetzung müssen beim maschinellen Parsen bewusst behandelt werden.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eigenen Testbereich anlegen

```bash
df --version
uebung="$(mktemp -d -t netmon-df-XXXXXX)"
cd "$uebung"
pwd
printf '%s\n' 'Eigene Platzabfrage.' > "probe.txt"
```

Nur nach erfolgreichem Wechsel fortfahren. Die kleine Testdatei dient als eindeutiger eigener Pfad.

### Schritt 2: Zugehöriges Dateisystem ansehen

```bash
df -h "probe.txt"
```

Die Zeile beschreibt das Dateisystem, nicht die wenigen Bytes der Textdatei. Quelle und Einhängepunkt zur erwarteten Umgebung zuordnen.

### Schritt 3: Platz und Inodes trennen

```bash
df -i "probe.txt"
```

Ein Dateisystem kann hinsichtlich einer begrenzten Inode-Zahl ausgelastet sein, obwohl noch Datenblöcke frei erscheinen. Manche Dateisystemtypen liefern diese Information anders oder nicht in gleicher Bedeutung.

### Schritt 4: Gezielte Spalten lesen

```bash
df --output=source,size,avail,pcent,target "probe.txt"
```

Dieser GNU-Aufruf begrenzt die Anzeige auf relevante Felder. Die Einheiten anhand der gewählten Optionen beziehungsweise Kopfzeile beurteilen. Ohne `-h` ist dies nicht dieselbe gerundete Darstellung wie im ersten Beispiel.

### Schritt 5: Keine automatische Bereinigung ableiten

Wenn Platz knapp ist, zunächst mit geeigneten lesenden Werkzeugen Ursache und betroffenen Bestand eingrenzen. Die Statistik löscht nichts und ist keine Freigabe für eine automatische Bereinigung.

## 6. Typische Anwendungsfälle

**Vor einer großen neuen Datei:** Prüfen, auf welchem Dateisystem das Ziel tatsächlich liegt und wie viel Platz verfügbar gemeldet wird.

**Fehler „kein Platz“ eingrenzen:** Blockplatz, Inodes und mögliche Quoten als verschiedene Ursachen betrachten.

**Mount-Verwechslung erkennen:** Ein unerwarteter Einhängepunkt kann erklären, warum Daten auf der Systempartition statt dem gewünschten Medium landen würden.

**Übersicht gezielt erstellen:** Einen Pfad angeben, statt unnötig alle sichtbaren Dateisysteme und Netz-Mounts abzufragen.

## 7. Risiken, Nebenwirkungen und Vorsicht

### Keine Garantie für einen späteren Schreibauftrag

Andere Prozesse können freien Platz unmittelbar verbrauchen. Quoten, Reservierungen und weitere Dateisystemregeln können zusätzlich gelten. Der Bericht ist ein Zustand, keine Speicherplatzreservierung.

### Df und du messen verschiedene Dinge

Df betrachtet Dateisystemstatistik. Du summiert ausgewählte erreichbare Dateibestände. Geöffnete bereits gelöschte Dateien, Snapshots, Reservierungen oder nicht gelesene Bereiche können Unterschiede erklären. Nicht aus einer Differenz pauschal einen Defekt ableiten.

### Verfügbarkeit und langsame Mounts

Nicht erreichbare beziehungsweise langsame Netzwerkdateisysteme können Abfragen verzögern. Ein begrenzter eigener Pfad reduziert unnötigen Umfang. Nicht aufgrund eines langsamen Berichts ungeprüft Mounts entfernen.

### Berichte und Systeminformationen

Quellnamen und Mountpfade können interne Struktur verraten. Vor dem Teilen auf private Angaben prüfen. Eine Shell-Umleitung schreibt zudem einen eigenen Bericht und kann eine vorhandene Datei ersetzen.

**Root-Rechte sind für die gezeigte Abfrage nicht nötig.** Die Übung verwendet kein `--sync` und verändert keine Mounts.

## 8. Häufige Fehler

| Beobachtung | Mögliche Ursache | Vorgehen |
| --- | --- | --- |
| Viel größer als der Ordner | Dateisystem statt Ordnergröße angezeigt. | Für Bestandsgröße du verwenden. |
| Falscher Datenträger | Erwarteter Mount nicht aktiv oder falscher Pfad. | Einhängepunkt bewusst prüfen. |
| Bytes frei, Schreiben scheitert | Inodes, Quote, Rechte oder Reservierung. | Fehlerursachen getrennt lesen. |
| Andere Größen als Herstellerangabe | Basis 1000 gegenüber 1024 und Dateisystemverwaltung. | Einheiten unterscheiden. |
| Df und du widersprechen sich | Unterschiedliche Messgegenstände. | Offene Dateien, Snapshots und Auswahlgrenzen gezielt klären. |
| Bericht hängt | Langsamer beziehungsweise nicht erreichbarer Mount. | Auf relevanten Pfad begrenzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. Den konkreten vorgesehenen Zielpfad angeben.
2. Dateisystem und Ordnergröße nicht verwechseln.
3. Gerundete Einheiten und exakte Bytes trennen.
4. Bei Platzfehlern Inodes und Quoten mitdenken.
5. Keine automatische Löschaktion aus einer Statistik ableiten.
6. Bericht als Momentaufnahme behandeln.

**Prüfstand:** GNU df 9.4 wurde ausschließlich für eine eigene Datei im temporären Testbereich ausgeführt. Human-Readable-Ausgabe, Inode-Ansicht und gezielte Spaltenabfrage endeten erfolgreich. Die Quelldatei blieb unverändert. Quoten, volle Datenträger, Netzwerk-Mounts und Snapshot-Sonderfälle wurden nicht praktisch getestet.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `du` | Verbrauch ausgewählter erreichbarer Bestände. |
| `findmnt` | Einhängepunkte und Mountzuordnung lesen. |
| `lsblk` | Blockgeräte und Zuordnung untersuchen. |
| `stat` | Einzeldateieigenschaften statt gesamter Platzübersicht. |

Ausgangseintrag: Datensatz 53 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
