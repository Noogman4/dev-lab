---
id: "resize2fs"
name: "resize2fs"
command: "resize2fs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "resize2fs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 242
reviewed_at: "2026-11-13"
locally_checked_version: "resize2fs 1.47.0 (5-Feb-2023)"
---

# resize2fs – Dateisystemgröße von Partitionsgröße unterscheiden

## 1. Kurzbeschreibung

`resize2fs` ändert die Größe von ext2/ext3/ext4. Es ändert keine Partitionstabelle. Für die eigene neue Abbilddatei sind keine Root-Rechte nötig; reale Online-/Offline-Wartung erfordert andere Rechte und Freigaben.

## 2. Was macht der Befehl?

Vergrößern braucht zunächst genügend Platz im darunterliegenden Objekt. Verkleinern braucht umgekehrt zuerst ein erfolgreich verkleinertes ungemountetes Dateisystem, bevor dessen Träger kleiner werden darf. Online-Vergrößerung ist nur mit unterstütztem Kernel/Dateisystem möglich; die Übung verwendet ausschließlich eine nicht gemountete Datei. Ohne Größenargument wird die Größe des Trägers verwendet.

Quelle, am 2026-11-13 gelesen: [resize2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/resize2fs.8.en.html)

## 3. Syntax

```text
resize2fs [OPTIONEN] ZIEL [NEUE_GROESSE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Größe ohne Suffix | Anzahl Dateisystemblöcke, nicht Bytes. |
| `K`, `M`, `G`, `T` | Größe in Zweierpotenzen; s bedeutet 512-Byte-Sektoren. |
| `-P` | Geschätzte Minimalblockzahl anzeigen und beenden; Schätzung kann falsch sein. |
| `-M` | Wirklich auf Minimalgröße verkleinern; keine reine Anzeige. |
| `-f` | Einige Schutzprüfungen übergehen; in der Übung nicht verwendet. |
| `-p` | Fortschritt eines geeigneten Offline-Vorgangs anzeigen. |
| `-b`, `-s` | 64bit-Feature ein-/ausschalten; nicht gleichzeitig allgemeine Größenänderung. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, GNU truncate, e2fsprogs und rg. Sämtliche Dateien sind neu und entbehrlich; keine Partition, kein Loop-Gerät, kein Mount.

### Schritt 1: Eigene 16-MiB-Dateisystemdatei erzeugen und lesend prüfen

### Schritt 2: Erst die Datei auf 32 MiB erweitern, dann das Dateisystem

```bash
uebung="$(mktemp -d -t netmon-resize2fs-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
truncate -s 16M fs.img
mkfs.ext2 -q -E nodiscard fs.img
e2fsck -f -n fs.img
truncate -s 32M fs.img
resize2fs fs.img
dumpe2fs -h fs.img > bericht.txt
rg 'Block count|Block size' bericht.txt
```

### Schritt 3: Ergebnis ausrechnen

Block count mal Block size soll 33554432 Bytes ergeben. Lokal waren es 8192 Blöcke zu 4096 Bytes. truncate allein hätte nur die Hostdatei verlängert; erst resize2fs passt die ext-Struktur an. Die Abbilddatei bleibt erhalten. Eine Verkleinerung wird nicht als automatischer Folgeschritt ausgeführt.

## 6. Typische Anwendungsfälle

**Kapazität erweitern:** Verfügbaren Trägerplatz und tatsächlich verwendete Dateisystemgröße unterscheiden. **Wartung planen:** Vergrößerungs- und Verkleinerungsreihenfolge getrennt beschreiben.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Reihenfolge beim Verkleinern schneidet Nutzdaten ab. Schätzungen von -P, besonders bei kleinen Blockgrößen, sind keine Freigabe zum Abschneiden des Trägers. Featureänderungen und Schutzumgehungen benötigen eigene Planung. Keine echten Datenträger oder aktiven Dateisysteme verändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Nichts zu tun | Dateisystem hat bereits die erkannte Trägergröße. |
| Datei größer, df unverändert | Nur Träger erweitert oder falsche Ansicht; keine reale Probe hier. |
| Minimalschätzung unterschätzt | Bekannte Grenze; niemals allein darauf den Träger verkürzen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

An einer neu erzeugten Kopie lernen. Blockanzahl und Blockgröße zusammen prüfen. Niemals truncate zum Verkleinern einer gefüllten Dateisystemdatei vor deren interner Verkleinerung verwenden.

**Prüfstand am 2026-11-13:** resize2fs 1.47.0 (5-Feb-2023). Praktisch geprüft: Offline-Vergrößerung der eigenen frischen ext2-Datei von 16 auf 32 MiB erfolgreich, Blockgeometrie gelesen. Nicht praktisch geprüft: Verkleinern, Onlinebetrieb, echte Partitionen, 64bit-Konvertierung und Wiederherstellung. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `truncate` | Hier nur Trägergröße der eigenen Datei ändern. |
| `e2fsck` | Vorhandene ext-Struktur prüfen. |
| `parted` | Partitionsebene, nicht Dateisystemgröße. |

Ausgangsdatensatz 242 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
