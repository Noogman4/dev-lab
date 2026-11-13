---
id: "partclone"
name: "partclone"
command: "partclone.DATEISYSTEM"
category: "Backup & Sync"
language: "de"
root_required: true
risk_level: "danger"
tags: ["backup & sync", "partclone"]
status: "Quellen geprüft; Geräteabbild und Wiederherstellung praktisch offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 66
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht installiert; Distributions-Manpage geprüft"
---

# partclone – Dateisystembezogene Partitionsabbilder verstehen

## 1. Kurzbeschreibung

Partclone ist eine Sammlung dateisystemspezifischer Werkzeuge zum Sichern und Wiederherstellen von Partitionen. Statt immer jeden freien Bereich zu kopieren, können unterstützte Varianten belegte Blöcke anhand des Dateisystems erkennen. **Für reale Partitionszugriffe sind gewöhnlich administrative Rechte erforderlich.** Das Lesen einer Hilfe benötigt kein Root.

`partclone` ist der Sammelname. Tatsächliche Programme heißen beispielsweise `partclone.ext4`; vorhandene Varianten hängen vom installierten Paket ab. Ein erfundener universeller Aufruf `partclone --help` ersetzt diese Unterscheidung nicht.

## 2. Was macht der Befehl?

Im Clone-Modus liest das passende Werkzeug eine Dateisystemquelle und erzeugt ein eigenes Imageformat. Im Restore-Modus schreibt es aus diesem Image Daten auf ein Ziel zurück. Ein solches Image ist weder ein gewöhnliches tar-Archiv noch automatisch ein unmittelbar einhängbares vollständiges Rohabbild.

Die [Distributions-Manpage](https://manpages.debian.org/trixie/partclone/partclone.8.en.html) erklärt die Modi und die Variante nach Dateisystem. Ein Partitionsimage enthält nicht automatisch das vollständige Layout eines mehrteiligen Datenträgers samt Bootkonfiguration. Wer einen ganzen Rechner wiederherstellen möchte, muss diese zusätzlichen Bestandteile separat berücksichtigen.

## 3. Syntax

```text
partclone.DATEISYSTEM -c -s QUELLE -o NEUES_IMAGE
partclone.DATEISYSTEM -r -s IMAGE -o ZIEL
```

Dies sind ausschließlich Syntaxmuster. `DATEISYSTEM`, `QUELLE`, `IMAGE` und `ZIEL` müssen nach sorgfältiger Planung ersetzt werden. Keine tatsächlichen Gerätedateien werden in dieser Anleitung verwendet. Die Wahl der Variante orientiert sich am vorhandenen Dateisystem, nicht an einer frei gewählten Dateiendung des Images.

## 4. Wichtige Optionen

| Option | Bedeutung | Risiko oder Grenze |
| --- | --- | --- |
| `-c`, `--clone` | Quelle ins Partclone-Imageformat sichern. | Schreibt eine Ausgabedatei. |
| `-r`, `--restore` | Image zurückschreiben. | Vorhandene Zieldaten können verloren gehen. |
| `-b`, `--dev-to-dev` | Direkt zwischen Geräten kopieren. | Quelle und Ziel besonders sicher bestimmen. |
| `-s QUELLE` | Eingabe auswählen. | Rollen nicht vertauschen. |
| `-o ZIEL` | Ausgabe auswählen. | Zielbedeutung hängt vom Modus ab. |
| `-O ZIEL` | Vorhandene Ausgabe überschreiben. | Ist eine bewusste Aufhebung einer Schutzwirkung. |
| `-L DATEI` | Protokollpfad bestimmen. | Standard kann eine systemweite Logdatei sein. |
| `-h`, `--help` | Variantenhilfe anzeigen. | Nur falls dieses Programm tatsächlich installiert ist. |
| `-v`, `--version` | Version anzeigen. | Nicht mit einem Verbose-Schalter verwechseln. |

Prüfungen mit Optionen wie `--nocheck` oder `--ignore_crc` abzuschalten ist kein sinnvoller Anfängerweg bei unerklärten Fehlern. Manche Parameter sind versions- oder variantenspezifisch; lokale Hilfe hat Vorrang vor übertragenen Beispielen.

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Aufgabenart festlegen

Angenommen, eine entbehrliche Testpartition soll vor einer Laboränderung gesichert werden. Zuerst klären, ob ein Partitionsimage ausreicht oder ob tatsächlich der gesamte Datenträger samt Layout benötigt wird. Das verhindert, dass ein technisch erfolgreiches Teilimage später als Vollsicherung missverstanden wird.

### Schritt 2: Voraussetzungen dokumentieren

Dateisystemtyp, Partclone-Variante, Größe und eindeutige Identität der Quelle sowie die getrennte Ablage des Images notieren. Eine aktive, gleichzeitig veränderte Partition liefert keinen verlässlich konsistenten Ausgangsstand. Zustand und geeigneten Offline-Ablauf vor einer realen Aktion planen.

### Schritt 3: Image und Rückschreibziel trennen

Das Sicherungsziel wäre eine neue Datei auf ausreichend großem, getrenntem Speicher. Das spätere Restore-Ziel wäre hingegen eine ausdrücklich entbehrliche Partition. Die Tatsache, dass beide als `-o` angegeben werden, macht ihre Wirkung nicht gleich ungefährlich.

### Schritt 4: Ergebnisprüfung planen

Nach einem echten späteren Versuch wären Prozessstatus, Protokoll, Lesbarkeit des Images und eine Wiederherstellung auf einem Testziel zu prüfen. Ein Rückgabewert 0 zeigt zunächst den erfolgreichen Programmabschluss; ein bootfähiges System oder vollständige Anwendungsdaten sind damit noch nicht belegt.

Hier wird nur dieser Plan beschrieben. Es wurde weder ein Dateisystem angelegt noch eine Partition geöffnet, kopiert, eingehängt oder zurückgeschrieben. Ein sicherer realer Test erfordert getrennte Vorbereitung und Freigabe.

## 6. Typische Anwendungsfälle

### Partitionssicherung im Labor

Bei passendem Dateisystem können Images weniger Speicher als eine vollständige Sektorkopie beanspruchen. Der tatsächliche Platzbedarf hängt von Inhalt, Format und optionaler weiterer Verarbeitung ab.

### Bestandteil eines umfassenderen Imaging-Ablaufs

Clonezilla kann entsprechende Werkzeuge verwenden und zusätzliche Informationen verwalten. Ein einzelner manueller Partclone-Aufruf reproduziert deshalb nicht automatisch sämtliche Funktionen eines Clonezilla-Laufs.

## 7. Risiken, Nebenwirkungen und Vorsicht

Beim Zurückschreiben können bestehende Daten überschrieben werden. Eine falsche Variante, inkonsistente Quelle, beschädigte Sicherung oder unpassendes Ziel können den Vorgang scheitern lassen. Warnungen nicht durch Abschalten von Prüfungen übergehen.

Ein Abbild kann vertrauliche Daten enthalten; das Dateiformat selbst verspricht keine Verschlüsselung. Nicht jedes Speziallayout oder Dateisystemfeature ist in jeder Paketversion unterstützt. Bei bereits ausfallenden Medien ist der normale Imaging-Ablauf möglicherweise nicht die geeignete Rettungsstrategie. Bootloader, Partitionstabelle und andere Partitionen bleiben gesonderte Bestandteile einer vollständigen Wiederherstellungsplanung.

## 8. Häufige Fehler

- **Programmname fehlt:** Sammelname und tatsächlich vorhandene Dateisystemvariante verwechselt.
- **Image lässt sich nicht normal mounten:** Partclone-Image und Rohabbild verwechselt.
- **Sicherung abgeschlossen, Rechner startet nicht:** Es wurde nur eine Partition und nicht das gesamte notwendige Systemlayout gesichert.
- **Logpfad nicht beschreibbar:** Ein systemweiter Standardpfad benötigt andere Rechte; nicht einfach das gesamte Programm unüberlegt privilegieren.
- **Ziel zu klein:** Dateisystem- und Partitionsanforderungen statt nur sichtbarer Dateigröße prüfen.

## 9. Sichere Varianten oder Tipps für Einsteiger

Vor einer Geräteaktion die konkrete Variante und ihre Hilfe lesen. Für erste Erfahrungen den geplanten Workflow mit entbehrlichen Laborressourcen durchgehen. Quelle, Image-Ablage und Restore-Ziel immer als drei unterschiedliche Rollen dokumentieren.

**Prüfstand:** Distributions-Manpage geprüft. Partclone lokal nicht installiert; keine Version und keine Variante praktisch bestätigt. Kein Image erstellt oder zurückgeschrieben. Dateisystemkompatibilität, Prüfsummenverhalten und Wiederherstellung bleiben offen.

## 10. Verwandte Befehle

- `clonezilla`: umfassenderer menügeführter Imaging-Ablauf.
- `ddrescue`: Rettung mit Mapdatei bei Lesefehlern.
- `lsblk`: Geräte und Dateisysteminformationen lesend anzeigen.
- `borg`, `restic`: dateibasierte Sicherungsstände mit anderer Zielsetzung.

Ausgangseintrag: Datensatz 66 in `index.json`. Allgemeine Platzhalter wurden fachlich präzisiert; der unveränderte Ausgangsdatensatz bleibt im Index erhalten.
