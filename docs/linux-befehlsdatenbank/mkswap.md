---
id: "mkswap"
name: "mkswap"
command: "mkswap"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "mkswap"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 233
reviewed_at: "2026-11-13"
locally_checked_version: "mkswap from util-linux 2.39.3"
---

# mkswap – Swap-Metadaten vorbereiten, ohne Swap zu aktivieren

## 1. Kurzbeschreibung

`mkswap` legt einen Linux-Swap-Header in einer Datei oder auf einem Gerät an. Es aktiviert keinen Swap. Für die neue eigene Testdatei ist kein Root nötig; echte Gerätezugriffe und die spätere Aktivierung sind Verwaltungsaktionen.

## 2. Was macht der Befehl?

Anlage und Aktivierung sind getrennt: mkswap schreibt Metadaten, swapon würde den Kernel den Bereich nutzen lassen. Ein Partitions-Typcode allein initialisiert nichts. Ein gültiger Header macht eine beliebige Datei noch nicht automatisch als Swap nutzbar: Löcher, Copy-on-Write und Dateisystemgrenzen können die Aktivierung verhindern. Die aktuelle Webreferenz enthält neue --file-Funktionen, die eine ältere lokale Version nicht voraussetzen darf.

Quelle, am 2026-11-13 gelesen: [mkswap-Handbuch](https://manpages.debian.org/trixie/util-linux/mkswap.8.en.html)

## 3. Syntax

```text
mkswap [OPTIONEN] DATEI_ODER_GERAET [BLOCKZAHL]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-L NAME` | Label setzen; keine physische Laufwerkskennung. |
| `-U UUID` | Kennung festlegen; Duplikate vermeiden. |
| `-p BYTES` | Seitengröße überschreiben; normalerweise automatische Größe verwenden. |
| `-c` | Blockgerät vor Anlage prüfen; nicht Teil der Dateiübung. |
| `-f` | Schutzprüfungen übergehen; nicht zum Lernen verwenden. |
| `--file`, `--size` | Neuere dokumentierte Erzeugungsoptionen; lokal erst Verfügbarkeit prüfen. |
| `--version` | Programmversion anzeigen, nicht Swapformatversion verwechseln. |

## 5. Beispiel erklärt Schritt für Schritt

Voraussetzungen: Bash, util-linux und GNU stat. Nur eine neue gewöhnliche Datei wird beschrieben; kein Gerät, keine fstab-Änderung, kein swapon.

### Schritt 1: Einen MiB eigene Daten erzeugen und Header schreiben

```bash
uebung="$(mktemp -d -t netmon-mkswap-XXXXXX)" || exit 1
cd -- "$uebung" || exit 1
umask 077
printf '%1048576s' '' > swap.test
chmod 600 swap.test
mkswap -L LERNEN swap.test
stat -c '%n: %s Byte, Modus %a' swap.test
```

### Schritt 2: Ausgabe verstehen

Erwartet werden Swapformat, eine nutzbare Bereichsgröße etwas kleiner als 1 MiB, das Label `LERNEN` und eine erzeugte UUID. Die Dateilänge bleibt 1048576 Bytes und Modus 600. Die nutzbare Swapgröße ist wegen des Headers nicht identisch mit der Dateilänge.

### Schritt 3: Vor Aktivierung stoppen

Die Datei bleibt zur Kontrolle bestehen. Sie wird nicht als Swap verwendet. Der Test bestätigt nur Headeranlage und Dateimetadaten, keine spätere Kernelkompatibilität oder Leistungswirkung.

## 6. Typische Anwendungsfälle

**Formatlernen:** Header und vollständige Datei unterscheiden. **Wartungsplanung:** Speicherbedarf, Dateisystembedingungen und Aktivierung separat planen; keine bestehende Swapdatei neu initialisieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falsche Ziele können Dateisystemsignaturen und Daten verlieren. Swap kann sensible Speicherinhalte enthalten, falls er später tatsächlich benutzt wird; Dateirechte allein ersetzen keine passende Verschlüsselungsplanung. Keine bestehenden Benutzerdateien oder aktiven Swapbereiche überschreiben.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bereich zu klein | Mindestbedarf in Speicherseiten prüfen. |
| Datei angelegt, aber kein zusätzlicher Swap | mkswap aktiviert nichts. |
| swapon würde Datei ablehnen | Layout/Dateisystembedingungen sind zusätzlich nötig; hier nicht als Folgeaktion ausführen. |
| Label/UUID verwechselt | Namen und gespeicherte Kennung getrennt behandeln. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Neue entbehrliche Dateien, restriktive Rechte und explizite Größen verwenden. Die optionale alte Blockzahl nicht mit Bytes verwechseln; sie zählt 1024-Byte-Blöcke und wird gewöhnlich weggelassen.

**Prüfstand am 2026-11-13:** mkswap from util-linux 2.39.3. Praktisch geprüft: Nur Header in eigener voll beschriebener 1-MiB-Datei angelegt; Länge und Modus geprüft. Nicht praktisch geprüft: Geräte, Aktivierung, Kernel-/Dateisystemeignung und neue --file-Optionen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `swapon` | Aktiviert vorbereiteten Swap; Systemänderung. |
| `swapoff` | Deaktiviert aktiven Swap. |
| `stat` | Dateigröße und Rechte der eigenen Datei kontrollieren. |

Ausgangsdatensatz 233 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
