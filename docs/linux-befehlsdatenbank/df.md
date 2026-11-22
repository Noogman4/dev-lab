---
id: "df"
name: "df"
command: "df"
category: "Dateien & Verzeichnisse"
language: "de"
root_required: false
risk_level: "safe"
tags: ["dateien", "verzeichnisse", "speicherplatz", "dateisysteme"]
status: "Ausgearbeitet; Quellen geprüft; Beispiel praktisch geprüft"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 179
reviewed_at: "2026-11-13"
locally_checked_version: "GNU coreutils 9.4"
---

# df – Belegten und freien Speicherplatz von Dateisystemen anzeigen

## 1. Kurzbeschreibung

`df` („disk free“) zeigt für eingehängte **Dateisysteme**, wie groß sie sind, wie viel belegt und wie viel noch frei ist. Damit erkennt man schnell, ob eine Partition voll läuft.

**Root-Rechte sind nicht nötig.** `df` liest nur Statusinformationen des Kernels und verändert nichts.

Grundlage ist die [Debian-Manpage zu df](https://manpages.debian.org/trixie/coreutils/df.1.en.html) (GNU coreutils).

## 2. Was macht der Befehl?

Ohne Argumente listet `df` alle eingehängten Dateisysteme, standardmäßig in Blöcken zu 1 KiB. Mit einem Pfad zeigt es das Dateisystem, auf dem dieser Pfad liegt.

Beispielausgabe auf dem geprüften System:

```text
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/nvme0n1p2 ext4  457G  190G  245G  44% /
```

| Spalte | Bedeutung |
| --- | --- |
| `Filesystem` | Gerät oder Quelle. |
| `Type` | Dateisystemtyp (mit `-T`). |
| `Size`, `Used`, `Avail` | Größe, belegt, für normale Benutzer verfügbar. |
| `Use%` | Belegung in Prozent. |
| `Mounted on` | Einhängepunkt. |

`Size` minus `Used` ist oft größer als `Avail`. Bei ext4 liegt das typischerweise an Blöcken, die für Root reserviert sind. **Prüfpunkt:** Die Reservierung wurde nicht mit Root-Werkzeugen nachgeprüft.

## 3. Syntax

```text
df [OPTIONEN] [DATEI ...]
```

```bash
df -h
df -h /home
df -hT -x tmpfs -x squashfs
df -i /
```

Das bisherige NetMon-Beispiel `df --help` zeigt die Hilfe. Der Platzhalter `df [OPTIONEN] [ARGUMENTE]` wurde oben präzisiert.

## 4. Wichtige Optionen

| Option | Bedeutung | Konkreter Hinweis |
| --- | --- | --- |
| `-h` | Lesbare Größen (Basis 1024: K, M, G). | Für Menschen. |
| `-H` | Lesbare Größen mit Basis 1000. | – |
| `-T` | Dateisystemtyp anzeigen. | – |
| `-i` | Inodes statt Blöcken. | Dateisysteme können auch an Inodes voll laufen. |
| `-x TYP` | Typ ausblenden, etwa `tmpfs`. | Mehrfach angebbar. |
| `-t TYP` | Nur diesen Typ zeigen. | – |
| `-l`, `--local` | Nur lokale Dateisysteme. | Blendet Netzlaufwerke aus. |
| `--output=FELDER` | Spalten wählen, z. B. `source,size,avail,target`. | Für Skripte. |
| `--total` | Summenzeile. | – |
| `-a` | Auch Pseudo- und doppelte Dateisysteme. | – |

## 5. Beispiel erklärt Schritt für Schritt

### Ziel

Prüfen, ob auf dem Dateisystem des Heimatordners genug Platz für einen großen Download ist.

### Schritt 1: Übersicht ohne Pseudodateisysteme

```bash
df -hT -x tmpfs -x squashfs
```

Zeigt nur echte Datenträger mit Typ und Belegung.

### Schritt 2: Dateisystem eines Pfads

```bash
df -h "$HOME"
```

Die Zeile nennt Gerät, Größe, Belegung und `Avail`. Im Test lag `$HOME` auf `/` mit 245G frei.

### Schritt 3: Inodes prüfen

```bash
df -i "$HOME"
```

Zeigt die Zahl der Dateieinträge; bei 100 % lassen sich trotz freiem Platz keine neuen Dateien anlegen.

### Schritt 4: Für Skripte

```bash
df --output=avail -B1 "$HOME" | tail -n 1
```

Gibt den freien Platz in Bytes aus. **Prüfpunkt:** `-B1` nicht ausgeführt.

## 6. Typische Anwendungsfälle

- **„Kein Platz mehr“-Fehler** untersuchen.
- **Vor großen Downloads, Updates oder Sicherungen** freien Platz prüfen.
- **Überwachung** in Skripten mit `--output`.
- **Eingehängte Datenträger** und deren Typ überblicken.

## 7. Risiken, Nebenwirkungen und Vorsicht

`df` ist rein lesend. Die ursprüngliche Einstufung „Grün – sicher lesend“ wird als `safe` übernommen. Hinweise:

- **Hängende Netzlaufwerke:** Ist ein Netzlaufwerk (NFS, sshfs) nicht erreichbar, kann `df` ohne Argumente hängen. `-l` oder ein Pfad auf einem lokalen Dateisystem vermeidet das. **Prüfpunkt:** nicht praktisch geprüft.
- **Abweichungen zu `du`:** Gelöschte, aber noch geöffnete Dateien belegen Platz, den `du` nicht sieht.
- **Einheiten:** `-h` rechnet mit 1024, `-H` mit 1000; Herstellerangaben nutzen meist 1000.

## 8. Häufige Fehler

| Meldung oder Beobachtung | Ursache | Vorgehen |
| --- | --- | --- |
| `df: …: No such file or directory` (Rückgabe 1) | Pfad existiert nicht (im Test). | Pfad prüfen. |
| `Avail` kleiner als erwartet | Reservierte Blöcke. | Normal; siehe Abschnitt 2. |
| Platz frei, aber „No space left on device“ | Inodes erschöpft. | `df -i`. |
| `df` und `du` widersprechen sich | Geöffnete gelöschte Dateien oder Einhängepunkte über Daten. | Programme neu starten; Einhängungen prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

1. **`df -h` für die schnelle Übersicht.**
2. **Mit Pfad abfragen**, statt die ganze Liste zu deuten.
3. **`-x tmpfs`** blendet Arbeitsspeicher-Dateisysteme aus.
4. **Bei Platzmangel mit `du`** die großen Ordner suchen.

### Prüfstand

- **Geprüfte Version:** GNU coreutils 9.4 (Ubuntu 24.04-Basis); Debian-Manpage aus trixie.
- **Tatsächlich ausgeführt:** `df -h --output=…` für `/` und `/tmp`, `df -i /`, `df -hT -x tmpfs -x squashfs`, nicht vorhandener Pfad (Rückgabe 1).
- **Nicht geprüft:** `-B1`, Netzlaufwerke, `--total`.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `du` | Belegung einzelner Ordner und Dateien. |
| `findmnt`, `lsblk` | Einhängepunkte und Geräte. |
| `ncdu` | Interaktive Belegungsanalyse (nicht geprüft). |

Ausgangseintrag: Datensatz 179 in `index.json` (`df`, Risiko „Grün – sicher lesend“, Root „Nein/selten“). Der Hilfe-Platzhalter wurde durch Spaltenbedeutung, Optionen, Inode-Hinweis und einen geprüften Ablauf ersetzt.
