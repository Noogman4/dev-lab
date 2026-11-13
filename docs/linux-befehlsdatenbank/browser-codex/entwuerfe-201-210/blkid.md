---
id: "blkid"
name: "blkid"
command: "blkid"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["datentraeger", "uuid", "dateisystem"]
status: "Ausgearbeitet; Quellen geprüft; praktische Prüfung offen"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 210
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft"
---

# blkid – Dateisystemkennungen und Signaturen anzeigen

## 1. Kurzbeschreibung

`blkid` ermittelt Kennungen wie `UUID`, `LABEL` und `TYPE` von Blockgeräten. Die übliche Abfrage ist lesend, kann aber auf Geräte und einen Cache zugreifen. **Root ist für den allgemeinen lesenden Aufruf nicht zwingend erforderlich**, jedoch können unprivilegierte Nutzer nur eingeschränkte oder zwischengespeicherte Ergebnisse sehen.

## 2. Was macht der Befehl?

Das Programm gehört zu util-linux und verwendet `libblkid`. Standardmodus und Low-Level-Probe `-p` können unterschiedliche Felder liefern. Mehrdeutige Signaturen werden im Standardmodus unter Umständen unterdrückt. Die [offizielle util-linux-Manpage im Quellrepository](https://kernel.googlesource.com/pub/scm/utils/util-linux/util-linux/+/master/misc-utils/blkid.8.adoc) beschreibt Cache, Probe und Ausgaben.

## 3. Syntax

```bash
blkid [OPTIONEN] [GERAET ...]
blkid -s UUID -o value [GERAET]
blkid -p [GERAET]
```

Die Beispiele mit `[GERAET]` sind **Syntaxmuster**, keine Freigabe zum Zugriff auf ein reales Gerät. Für eine reine Befehlsübersicht `blkid --help` verwenden.

## 4. Wichtige Optionen

| Option | Bedeutung | Hinweis |
| --- | --- | --- |
| `-s TAG` | Nur bestimmten Tag anzeigen. | Z. B. `UUID`, `TYPE`. |
| `-o FORMAT` | Ausgabeformat wählen. | `value`, `export`, `full` je Version. |
| `-p` | Low-Level-Probe ohne Cache. | Direkter Gerätezugriff; Rechte nötig. |
| `-c DATEI` | Andere Cache-Datei verwenden. | `-c /dev/null` deaktiviert Cache-Verwendung. |
| `-L LABEL` | Gerät zu Label auflösen. | Labels sind nicht eindeutig garantiert. |
| `-U UUID` | Gerät zu UUID auflösen. | Ergebnis vor Verwendung prüfen. |
| `-g` | Cache bereinigen. | **Schreibt Cache-Metadaten**. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Nur die Dokumentation betrachten

```bash
blkid --help
```

Das zeigt verfügbare Optionen ohne einen bewusst angegebenen Gerätepfad. Je nach Implementierung unterscheiden sich Details.

### Schritt 2: Kennungen als Beispiel interpretieren

```text
/dev/BEISPIEL: UUID="beispiel-kennung" TYPE="ext4"
```

Diese Zeile ist **fiktiv** und kein Ergebnis eines echten Datenträgers. `UUID` bezeichnet eine Dateisystemkennung, nicht die eindeutige Hardwareidentität.

### Schritt 3: Keine Geräteprüfung

Ein konkreter `blkid -p`-Aufruf wird hier bewusst nicht ausgeführt. Direkte Signaturprüfung erfordert gesonderte Geräte- und Berechtigungsprüfung.

## 6. Typische Anwendungsfälle

**Konfiguration verstehen:** UUID und Dateisystemtyp in einer bestehenden Dokumentation zuordnen. **Diagnose:** Abweichungen zwischen Cache und Low-Level-Probe fachlich einordnen. **Mount-Vorbereitung:** Kennungen als eine von mehreren Identitätsprüfungen verwenden, nicht blind mounten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die reine Kennungsabfrage schreibt normalerweise nicht auf das Gerät; sie kann dennoch Geräte-I/O verursachen. Der Cache kann veraltet sein. `-g` ändert Cache-Daten, `-p` greift direkter auf das Gerät zu. Mehrdeutige Signaturen, Klone mit gleichen UUIDs und eingeschränkte Rechte erschweren eindeutige Zuordnung. Gerätebezeichnungen und Labels können sich ändern. Keine Root-Eskalation für Lernzwecke.

## 8. Häufige Fehler

| Problem | Ursache | Maßnahme |
| --- | --- | --- |
| Keine Ausgabe | Rechte, Cache oder fehlende Signatur. | Nicht automatisch auf leeres Gerät schließen. |
| UUID mehrfach | Geklonte Dateisysteme. | Identität unabhängig prüfen. |
| Werte unterscheiden sich | Cache vs. direkte Probe. | Modus und Zeitpunkt dokumentieren. |
| Mehrdeutiger Fund | Überlagerte Signaturen. | Fachliche Diagnose statt blindem Löschen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zunächst nur `blkid --help` lesen. Für die Übersicht eines Systems sind dokumentierte, autorisierte Inventarisierungswege sinnvoll; keine echten Geräte in dieser Übung öffnen. UUIDs vor administrativer Verwendung zusätzlich verifizieren.

**Prüfstand:** Offizielle util-linux-Manpage am 2026-11-13 gelesen; **keine lokale Version, kein Cache- oder Gerätezugriff, kein Parser-Test**. **Prüfpunkt:** Ausgabeformate und Zugriffsmöglichkeiten auf dem Zielsystem versionsabhängig prüfen.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `lsblk` | Geräte und Metadaten anzeigen. |
| `findmnt` | Bestehende Einhängepunkte prüfen. |
| `wipefs` | Signaturen anzeigen; Löschfunktionen besonders gefährlich. |
| `mount` | Dateisystem einhängen; eigenständiger Admin-Vorgang. |

**Ausgangseintrag:** `source_record` 210 aus `tools/netmon-linux-befehlsdatenbank-v1.csv` (Zuordnung aus dem übergebenen JSON, Original-CSV hier nicht selbst geprüft). Gegenüber dem Ausgangseintrag wurden die generische Syntax und das `--help`-Platzhalterbeispiel durch konkrete Funktionsweisen, Sicherheitsgrenzen und Quellen ersetzt; die pauschale Risikoeinstufung wurde fachlich neu bewertet. Die ursprünglichen `source`-Felder wurden nicht verändert.
