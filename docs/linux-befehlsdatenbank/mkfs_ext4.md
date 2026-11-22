---
id: "mkfs_ext4"
name: "mkfs.ext4"
command: "mkfs.ext4"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "mkfs.ext4"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 231
reviewed_at: "2026-11-13"
locally_checked_version: "mke2fs 1.47.0 (5-Feb-2023)"
---

# mkfs.ext4 – Ein ext4-Dateisystem in einer eigenen Abbilddatei anlegen

## 1. Kurzbeschreibung

`mkfs.ext4` ist ein Aufrufname von mke2fs und wählt ext4 als Typ. Es erzeugt neue Strukturen und kann bestehende Daten überschreiben. Für die ausschließlich eigene gewöhnliche Abbilddatei ist kein Root erforderlich; ein echtes Blockgerät hätte andere Rechte- und Freigabebedingungen.

## 2. Was macht der Befehl?

Ext4 verwendet typischerweise ein Journal und Extent-Abbildung; moderne Profile können Metadatenprüfsummen und weitere Features enthalten. Das [ext4-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/ext4.5.en.html) wurde für die Featurebedeutung zusätzlich gelesen. Metadatenprüfsummen sind keine durchgehende Inhaltsprüfung aller normalen Dateidaten. Nicht jedes ältere Rettungsmedium unterstützt neue Features; den erzeugten Featurebericht deshalb aufbewahren.

Die tatsächlichen Voreinstellungen hängen von mke2fs.conf und Programmversion ab. Ein Typname ist deshalb kein vollständiges Featuremanifest. Blockgröße, Inodeanzahl und reservierter Platz beeinflussen nutzbare Kapazität; Rohgröße und freie Nutzdatenmenge sind verschieden. Die Originaleinstufung als allgemeiner Verwaltungsbefehl wird zu danger konkretisiert.

Quelle, am 2026-11-13 gelesen: [mke2fs-Projekthandbuch](https://manpages.debian.org/trixie/e2fsprogs/mke2fs.8.en.html) und lokale mke2fs-Manpage

## 3. Syntax

```text
mkfs.ext4 [OPTIONEN] ZIEL [GROESSE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-L NAME` | Label setzen, höchstens 16 Bytes; keine eindeutige Hardwarekennung. |
| `-b BYTES` | Dateisystemblockgröße wählen; Kernelkompatibilität beachten. |
| `-i BYTES`, `-N ANZAHL` | Inodeverhältnis beziehungsweise Inodeanzahl beeinflussen. |
| `-m PROZENT` | Reservierten Blockanteil wählen; nicht freie Gesamtkapazität. |
| `-O FEATURES` | Features gezielt ändern; kann den gewählten Typ inkompatibel machen. |
| `-E nodiscard` | Discard beim Anlegen unterlassen; kein allgemeiner Schreibschutz. |
| `-n` | Anlage nur berechnen; Ergebnis gilt nur für passende Layoutparameter. |
| `-F` | Schutzprüfungen übergehen; in dieser Übung nicht verwendet. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GNU truncate, e2fsprogs und rg. Alle Schreibziele werden neu im privaten Temporärordner erzeugt. Keine Loop-Zuordnung, kein Gerät und kein Mount. Die Schritte gehören in dieselbe Shell.

### Schritt 1: Neue leere Abbilddatei vorbereiten

```bash
uebung="$(mktemp -d -t netmon-ext4-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
truncate -s 16M fs.img
mkfs.ext4 -V
mkfs.ext4 -q -E nodiscard -L LERNEN fs.img
dumpe2fs -h fs.img > bericht.txt
rg 'Filesystem volume name|Filesystem features|Block count|Block size' bericht.txt
```

### Schritt 2: Bericht lesen

truncate reserviert die logische Länge von 16 MiB; die physische Belegung kann kleiner sein. mkfs schreibt Dateisystemmetadaten in genau diese eigene Datei. Im Bericht muss das Label `LERNEN` stehen. Blockanzahl und Blockgröße gemeinsam ergeben die Dateisystemgröße. Der Versionsaufruf bestätigt nur die ausgeführte Werkzeugversion.

### Schritt 3: Grenzen festhalten

Das Abbild wurde nicht gemountet. Die gelesene Metadatenliste ist kein Test von Kernelzugriff, Datenwiederherstellung oder Stromausfallverhalten. Bericht und Abbild bleiben zur Kontrolle im Übungsordner.

## 6. Typische Anwendungsfälle

**Formatlernen:** Den Typ und die erzeugten Features an einer entbehrlichen eigenen Datei vergleichen. **Kompatibilität planen:** Anforderungen des Zielkernels und benötigte Funktionen vor echter Anlage prüfen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Niemals einen realen Gerätepfad anstelle von fs.img einsetzen, ohne einen gesonderten Wartungsauftrag zu haben. Vorhandene Dateien würden zerstört oder unbrauchbar. Neuanlage repariert kein altes Dateisystem. Keine Erzwingung bei Schutzmeldungen; ein Label oder eine UUID ist kein Backup.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ziel zu klein | Mindestbedarf für Metadaten oder Journal nicht erfüllt; Größe und Typ prüfen. |
| Unerwartete Features | Lokale Konfiguration und Version beeinflussen die Vorgabe. |
| Kein Zugriff auf neues Dateisystem | Formatierung allein mountet nichts und ändert keine Hostrechte. |
| Unbekannte Option | Aufrufname und mke2fs-Version prüfen; --help nicht pauschal voraussetzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Nur frisch erzeugte Dateien verwenden und bei fehlgeschlagenem mktemp stoppen. Neue Versuche bekommen neue Ordner. Für echte Planung die komplette Größen-/Featurewahl dokumentieren.

**Prüfstand am 2026-11-13:** mke2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Beispiel mit eigener 16-MiB-Abbilddatei ausgeführt und Label/Featureliste gelesen. Nicht praktisch geprüft: reale Geräte, Mounts, Kernelkompatibilität, Reparatur, Datenwiederherstellung und andere Versionen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mke2fs` | Gemeinsame Implementierung der ext-Ersteller. |
| `dumpe2fs` | Erzeugte Metadaten lesen. |
| `e2fsck` | Konsistenzprüfung; von Anlage getrennt. |
| `truncate` | Legt hier nur die Größe der eigenen leeren Datei fest. |

Ausgangsdatensatz 231 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
