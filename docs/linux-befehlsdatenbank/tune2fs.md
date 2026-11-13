---
id: "tune2fs"
name: "tune2fs"
command: "tune2fs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "tune2fs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 248
reviewed_at: "2026-11-13"
locally_checked_version: "tune2fs 1.47.0 (5-Feb-2023)"
---

# tune2fs – ext-Superblockparameter lesen und gezielt ändern

## 1. Kurzbeschreibung

`tune2fs` zeigt oder verändert ext2/ext3/ext4-Verwaltungsparameter. Kleinbuchstabe -l listet, Großbuchstabe -L ändert das Label. Für die neue eigene Abbilddatei braucht man kein Root; echte Datenträger haben andere Zugriffsbedingungen.

## 2. Was macht der Befehl?

Die Metadaten enthalten Kennung, reservierte Blöcke, Featureflags und Prüfparameter. Deren Änderung kann späteres Mount-, Prüf- und Fehlerverhalten beeinflussen. Ein Labelwechsel kopiert keine Inhalte und ist keine Reparatur. Defaults im Superblock sind von fstab und Optionen eines tatsächlich ausgeführten Mounts zu unterscheiden.

Quelle, am 2026-11-13 gelesen: [tune2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/tune2fs.8.en.html)

## 3. Syntax

```text
tune2fs [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-l` | Superblockwerte anzeigen; keine neue Konfiguration anfordern. |
| `-L NAME` | Dateisystemlabel schreiben. |
| `-m PROZENT`, `-r ANZAHL` | Reservierten Blockanteil beziehungsweise Anzahl verändern. |
| `-c ANZAHL`, `-i ZEIT` | Mountzähl-/Zeitintervall für Prüfungen einstellen; ändert spätere Prüfplanung. |
| `-U UUID` | Kennung verändern; Boot-/Mountverweise können ungültig werden. |
| `-O FEATURES` | Features ändern; zusätzliche Prüfungen und Kompatibilität nötig. |
| `-e VERHALTEN` | Fehlerreaktion wie remount-ro oder panic setzen; keine bloße Meldungsoption. |
| `-f` | Schutzumgehung; kein allgemeiner Diagnosezusatz. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, truncate, e2fsprogs und rg. Nur eine neue nicht gemountete ext2-Abbilddatei wird beschrieben.

### Schritt 1: Eigenes Abbild mit bekanntem Label anlegen

### Schritt 2: Vorher lesen, genau das Label ändern und danach lesen

```bash
uebung="$(mktemp -d -t netmon-tune2fs-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
truncate -s 16M fs.img
mkfs.ext2 -q -E nodiscard -L VORHER fs.img
tune2fs -l fs.img > vorher.txt
tune2fs -L NACHHER fs.img
tune2fs -l fs.img > nachher.txt
rg 'Filesystem volume name' vorher.txt nachher.txt
```

### Schritt 3: Berichte vergleichen

Erwartet steht in vorher.txt `VORHER`, in nachher.txt `NACHHER`. Das belegt eine gezielte Superblockänderung in dieser Datei. Es wurde weder ein reales Laufwerk umbenannt noch eine Mountkonfiguration angepasst. Abbild und beide Berichte bleiben erhalten.

## 6. Typische Anwendungsfälle

**Metadatenkontrolle:** Vor einer gesonderten Wartung aktuelle Werte lesen. **Eigene Abbilder:** Ein Label zur Wiedererkennung setzen; dabei Kennung und Inhalt auseinanderhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Feature-, UUID- und Fehlerverhaltensänderungen können schwerwiegende Folgen haben. Reserven auf Systemdateisystemen nicht pauschal wegoptimieren. Das Entfernen von Journal-/Schutzfeatures kann Datenverlust verursachen. Eine Undo-Datei ist kein Schutz vor Stromausfall und ersetzt keine unabhängige Kopie.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Label bleibt unverändert | -l statt -L oder anderes Ziel; Meldungen prüfen. |
| Nach UUID-Wechsel nicht gefunden | Konfiguration referenziert alte Kennung. |
| Feature nicht unterstützt | Werkzeug/Kernel passen nicht; keine erzwungene Entfernung auf Verdacht. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Groß-/Kleinschreibung der Optionen prüfen und lesende Ausgangsberichte aufbewahren. Für Lernversuche neue Abbilddateien verwenden; keine Systemeinstellungen aus dem Muster ableiten.

**Prüfstand am 2026-11-13:** tune2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Eigenes frisches ext2-Abbild vor/nach Labeländerung erfolgreich gelesen. Nicht praktisch geprüft: echte Geräte, Feature-/UUID-Konvertierung, Mount-/Prüfplanung und Wiederherstellung. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `dumpe2fs` | Superblock und Gruppen lesen. |
| `mke2fs` | Dateisystem neu anlegen. |
| `e2fsck` | Strukturen prüfen und gegebenenfalls reparieren. |

Ausgangsdatensatz 248 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
