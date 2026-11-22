---
id: "extundelete"
name: "extundelete"
command: "extundelete"
category: "Forensik & Recovery"
language: "de"
root_required: false
risk_level: "danger"
tags: ["extundelete", "forensik & recovery"]
status: "Projektbeschreibung und Manpage geprüft; kein Medium angesprochen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 328
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; keine lokale Ausführung"
---

# extundelete – gelöschte ext3/ext4-Dateien aus einer Kopie zu retten versuchen

## 1. Kurzbeschreibung

`extundelete` versucht, gelöschte Dateien aus ext3- oder ext4-Dateisystemen wiederzugewinnen. Es nutzt dabei noch vorhandene Dateisystem- und Journalinformationen. Eine Wiederherstellung ist nicht garantiert.

**Für eine eigene lesbare Abbilddatei und einen eigenen Ausgabeort sind keine Root-Rechte nötig.** Zugriff auf ein geschütztes Gerät braucht andere Rechte. Dieses Dokument arbeitet ausschließlich mit einer geplanten Kopie, nicht mit einem echten Gerät.

## 2. Was macht der Befehl?

Das Werkzeug sucht verwertbare Informationen zu gelöschten Dateien und schreibt gefundene Inhalte in eine Ausgabeablage. Die [Projektbeschreibung](https://extundelete.sourceforge.net/) nennt den Ordner `RECOVERED_FILES` unter dem aktuellen Arbeitsverzeichnis. Die [Distributions-Manpage](https://manpages.debian.org/trixie/extundelete/extundelete.1.en.html) beschreibt Dateiauswahl und Eingabeabbilder.

Ob etwas verwertbar bleibt, hängt vom konkreten Zustand ab. Eine inzwischen überschriebene Datei wird nicht allein durch einen passenden Dateinamen wiederherstellbar. Auch ein gefundenes Ergebnis muss auf Inhalt und Vollständigkeit geprüft werden.

Die Projektseite nennt eine ältere Hauptversion. Unterstützung aktueller ext4-Features und verwendeter Bibliotheken bleibt deshalb vor einem realen Einsatz ein konkreter Prüfpunkt. Das bloße Wort „ext4“ ist keine vollständige Kompatibilitätszusage für jede Ausstattung.

## 3. Syntax

```text
extundelete --help
extundelete ABBILD --restore-file PFAD_IM_DATEISYSTEM
extundelete ABBILD --restore-directory VERZEICHNIS_IM_DATEISYSTEM
extundelete ABBILD --restore-all
```

Der Wiederherstellungspfad bezieht sich auf die untersuchte Dateisystemwurzel. Er ist nicht automatisch der Hostpfad, unter dem früher ein Mount lag. Ein Partitionsabbild und ein ganzes Laufwerksabbild sind ebenfalls nicht austauschbar.

## 4. Wichtige Optionen

| Form | Zweck | Praktische Grenze |
| --- | --- | --- |
| `--help` | Bedienung lesen. | Kein Wiederherstellungsversuch. |
| `--version` | Version anzeigen. | Kompatibilität bleibt gesondert zu prüfen. |
| `--restore-file PFAD` | Eine benannte Datei versuchen. | Benötigt verwertbare Restinformationen. |
| `--restore-directory PFAD` | Dateien eines Bereichs versuchen. | Kann viele Ausgaben erzeugen. |
| `--restore-all` | Alle möglichen Wiederherstellungen versuchen. | Große und teilweise unzuordenbare Ergebnisse möglich. |
| `--inode NUMMER` | Inodeinformationen betrachten. | Andere Aufgabe als eine Dateiwiederherstellung. |
| `--restore-inode NUMMER` | Wiederherstellung über Inode versuchen. | Kennung muss zum richtigen Dateisystem gehören. |
| `--before`, `--after` | Nach Löschzeit begrenzen. | Erwartet Epochensekunden, nicht beliebige Datumstexte. |

Keine unbekannte Option zur automatischen Dateisystemreparatur ergänzen. Die Rettung gelöschter Inhalte und das Reparieren einer Struktur sind unterschiedliche Aufgaben.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Eine vorbereitete Partitionskopie voraussetzen

Angenommen, `partition.img` ist bereits eine bekannte, autorisiert bereitgestellte Arbeitskopie. Ihr absoluter Pfad, Ursprung und Dateisystemtyp sind dokumentiert. Diese Dokumentation erstellt oder mountet die Kopie nicht.

### Schritt 2: Ausgabe getrennt planen

Ein neuer Arbeitsordner auf einem geeigneten anderen Zielmedium wird für Ergebnisse vorgesehen. Das aktuelle Arbeitsverzeichnis ist wichtig, weil dort der Wiederherstellungsordner entsteht. Keinesfalls im betroffenen Originaldateisystem Ergebnisse speichern.

### Schritt 3: Eine einzelne Auswahl beschreiben

```text
extundelete /ABSOLUTER/PFAD/partition.img --restore-file dokumente/notiz.txt
```

Das ist eine Planungsschablone. Der Großbuchstabenpfad muss durch den bekannten Abbildpfad ersetzt werden. Der Aufruf wurde nicht ausgeführt, da Werkzeug und geeignetes Übungsabbild fehlen.

### Schritt 4: Ergebnisse fachlich prüfen

Eine neu entstandene Datei wäre zunächst ein Rettungsergebnis. Inhalt, erwartete Größe und gegebenenfalls bekannte Prüfsumme müssen dazu passen. Ein lesbarer Anfang beweist noch nicht die Vollständigkeit des gesamten Dokuments.

## 6. Typische Anwendungsfälle

- Eine versehentlich gelöschte Datei aus einer vorbereiteten ext-Arbeitskopie zu retten versuchen.
- Eine bekannte Teilmenge statt sofort sämtliche Reste zu extrahieren.
- Ergebnisse mit einer vorhandenen Sicherung vergleichen.
- Grenzen der journalbasierten Wiederherstellung feststellen.

Für einen echten Verlustfall laufende Schreibzugriffe und den Zustand des Originalmediums zuerst fachlich behandeln. Ein solches Vorgehen kann Mount-, Geräte- und Systemmaßnahmen erfordern und wird nicht automatisch aus diesem Text ausgeführt.

## 7. Risiken, Nebenwirkungen und Vorsicht

Weitere Schreibzugriffe auf das betroffene Original können noch vorhandene Daten zerstören. Deshalb weder das Werkzeug dort installieren noch Rettungsergebnisse dorthin schreiben. Auch normale Hintergrundaktivität kann relevant sein.

Ergebnisse können alte persönliche oder fremde Inhalte enthalten. Eine Rettungsablage muss entsprechend geschützt bleiben. Wiedergewonnene ausführbare Dateien oder Dokumente mit aktiven Inhalten nicht ungeprüft starten.

## 8. Häufige Fehler

- **Ganzes Laufwerk statt Dateisystemabbild:** Eingabegrenze und Partition klären.
- **Hostpfad statt interner Pfad:** Dateisystemwurzel beachten.
- **Keine Datei gefunden:** Kein Beweis, dass es sie nie gab.
- **Ergebnis zurück auf Quelle schreiben:** Kann weitere Rettungsmöglichkeiten zerstören.
- **Absturz bei ext4:** Features und Bibliothekskompatibilität bleiben Prüfpunkte.

## 9. Sichere Varianten oder Tipps für Einsteiger

Vorhandene Sicherungen zuerst berücksichtigen. Bei wichtigen Daten nicht mit mehreren ungeplanten Reparatur- und Rettungswerkzeugen am Original experimentieren.

Auf einer Arbeitskopie klein beginnen und Ergebnisse getrennt sammeln. Eine fehlgeschlagene Auswahl rechtfertigt keine Formatierung oder pauschale Reparatur des Originaldateisystems.

## 10. Verwandte Befehle

- `photorec`, `foremost`: Inhaltsbasierte Rettungsansätze mit anderen Grenzen.
- `testdisk`: Partitions- und Dateisystemanalyse mit potenziellen Schreibfunktionen.
- `fls`, `icat`: Dateisystemeinträge und Inhalte aus Abbildern betrachten.
- `ddrescue`: Geplante Aufnahme bei Lesefehlern.

**Prüfstand:** Handbücher gelesen. Kein Abbild ausgewertet, kein Datenträger gelesen oder verändert und kein Erfolg einer realen Rettung behauptet.

Ausgangsdatensatz 328 und feste Zuordnung stammen aus `index.json`. Die ursprünglichen Katalogfelder bleiben erhalten; fachlich unzutreffende Platzhalter wurden in dieser Dokumentation präzisiert.
