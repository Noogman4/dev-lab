---
id: "badblocks"
name: "badblocks"
command: "badblocks"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["datentraeger", "diagnose", "datenverlust"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 209
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# badblocks – Blockgeräte auf fehlerhafte Blöcke untersuchen

## 1. Kurzbeschreibung

`badblocks` untersucht Blockgeräte auf fehlerhafte Speicherblöcke. Schon der lesende Modus kann ein Gerät stark belasten; **`-w` überschreibt Daten destruktiv**. Für reale Blockgeräte sind häufig privilegierte Zugriffsrechte nötig. **Keine Geräteprüfung in dieser Dokumentationsübung.**

## 2. Was macht der Befehl?

Der Standardmodus ist lesend. `-n` führt einen nichtdestruktiv gedachten Lese-Schreib-Test durch, der dennoch auf das Gerät schreibt und bei Störungen Datenverlust riskieren kann. `-w` schreibt Testmuster über den untersuchten Bereich und zerstört vorhandene Daten. Blockgröße und Blocknummern müssen zur späteren Verwendung passen. Grundlage: [e2fsprogs-Manpage](https://www.man7.org/linux/man-pages/man8/badblocks.8.html).

## 3. Syntax

```text
badblocks [OPTIONEN] GERAET [LETZTER_BLOCK [ERSTER_BLOCK]]
```

**Nur Syntaxdarstellung, kein ausführbarer Geräteaufruf.** `GERAET` bezeichnet typischerweise einen Blockgerätepfad; nie einen vermuteten `/dev/...`-Pfad blind einsetzen.

## 4. Wichtige Optionen

| Option | Bedeutung | Risiko |
| --- | --- | --- |
| `-s` | Fortschritt anzeigen. | Zusätzliche Anzeige, keine Absicherung. |
| `-v` | Ausführlichere Fehlerstatistik. | Kein Gesundheitszertifikat. |
| `-b BYTES` | Blockgröße festlegen. | Falsche Einheit macht Ergebnislisten ungeeignet. |
| `-o DATEI` | Fehlerblockliste schreiben. | Überschreibt ggf. Ausgabedatei. |
| `-n` | Lese-Schreib-Test mit Rückschreiben. | **Schreibzugriffe, nicht risikofrei.** |
| `-w` | Destruktiver Schreibtest. | **Datenverlust auf geprüftem Bereich.** |
| `-e N` | Nach N gefundenen Fehlern abbrechen. | Liste kann unvollständig sein. |
| `-X` | Interne Schutzprüfung umgehen. | Nicht manuell verwenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Dokumentation statt Gerätetest

```bash
man 8 badblocks
```

Das liest die lokale Handbuchseite, falls installiert. Es startet **keinen** Blocktest.

### Schritt 2: Testmodus gedanklich unterscheiden

```text
Standard: lesende Prüfung, kann lange dauern.
-n: Lese-Schreib-Modus, trotz Name nicht risikofrei.
-w: destruktiver Schreibmodus, löscht vorhandene Daten.
```

### Schritt 3: Vor einem echten Diagnoseauftrag

Geräteidentität, Backup, Aushängen, Wartungsfenster, Hardwarezustand und geeignetes Dateisystemwerkzeug durch eine verantwortliche Fachperson prüfen lassen. **Hier wird kein `badblocks`-Geräteaufruf ausgeführt oder empfohlen.**

## 6. Typische Anwendungsfälle

**Fehlerdiagnose:** In einem kontrollierten Wartungsablauf Lesefehler ermitteln. **Dateisystemwerkzeuge:** `e2fsck` und `mke2fs` können eigene, passend integrierte Prüfabläufe haben. **Hardwarebewertung:** SMART-/NVMe-Gesundheitsinformationen ergänzend auswerten, nicht als Ersatz für Datensicherung.

## 7. Risiken, Nebenwirkungen und Vorsicht

**Kritisch:** `-w` zerstört vorhandene Daten. Auch `-n` schreibt und kann bei Ausfall, Stromverlust oder Gerätefehlern Daten beschädigen. Laufende Dateisysteme, RAID-/LVM-Schichten und falsche Gerätenamen machen Prüfungen besonders gefährlich. Ein lesender Scan kann geschädigte Hardware weiter belasten. Ergebnisse sind keine Garantie für künftige Zuverlässigkeit. Root-Rechte erteilen keine fachliche Freigabe.

## 8. Häufige Fehler

| Problem | Ursache | Vorgehen |
| --- | --- | --- |
| Falsches Gerät | Gerätebezeichnung verwechselt. | Keine Ausführung; Identität extern verifizieren. |
| Gerät ist in Benutzung | Dateisystem aktiv. | Fachgerechten Wartungsplan erstellen. |
| Fehlerliste unbrauchbar | Falsche Blockgröße. | Dateisystem-/Tool-Kontext abgleichen. |
| Kein Fehler gefunden | Prüfung begrenzt oder Defekt intermittierend. | Nicht als Gesundnachweis werten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Einsteiger sollten nur die Manpage lesen und keinen Blocktest starten. `-w`, `-n` und `-X` sind keine Lernoptionen an realen Datenträgern. Für Verdacht auf Defekte zunächst Backups und professionelle Diagnose planen.

**Prüfstand:** e2fsprogs-Manpage am 2026-11-13 gelesen. **Kein Gerät geöffnet, kein Scan, kein Schreib- oder Lesetest, keine lokale Version geprüft.** Geräteverhalten und konkrete Freigaben bleiben ausdrücklich offen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `e2fsck` | Dateisystemprüfung mit eigenen Risiken. |
| `mke2fs` | Dateisystemerstellung, potenziell destruktiv. |
| `smartctl` | Laufwerksdiagnose über SMART. |
| `lsblk` | Blockgeräteübersicht, vor Änderungen verifizieren. |

**Ausgangseintrag:** `source_record` 209 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
