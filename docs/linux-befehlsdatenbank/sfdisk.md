---
id: "sfdisk"
name: "sfdisk"
command: "sfdisk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "sfdisk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 243
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; sfdisk fehlt"
---

# sfdisk – Partitionstabellen als Skriptdaten behandeln

## 1. Kurzbeschreibung

`sfdisk` aus util-linux liest oder schreibt Partitionstabellen, besonders für Skripte. Der Standardauftrag mit Ziel liest einen Plan von Standardeingabe und kann ihn schreiben. Das ist keine reine Inventur; reale Ziele benötigen passende Verwaltungsrechte.

## 2. Was macht der Befehl?

Ein Textdump kann als spätere Eingabe dienen und enthält Tabelleninformationen, keine vollständigen Dateiinhalte. JSON ist ein Ausgabeformat und laut Handbuch kein akzeptiertes Eingabeformat. Sektorgenau angegebene Grenzen und Größen mit Suffixen haben unterschiedliche Ausrichtungsregeln. Kopieren eines Layouts kann Kennungen duplizieren.

Quelle, am 2026-11-13 gelesen: [sfdisk-Projekthandbuch](https://manpages.debian.org/trixie/fdisk/sfdisk.8.en.html)

## 3. Syntax

```text
sfdisk --dump ZIEL
sfdisk --json ZIEL
sfdisk [OPTIONEN] ZIEL < PLAN
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--dump` | Wiederverwendbaren Textplan ausgeben; Umleitung schreibt eine Hostdatei. |
| `--json` | JSON-Ausgabe erzeugen; keine JSON-Importfunktion. |
| `--list`, `--list-free` | Partitionen oder unpartitionierte Bereiche auflisten. |
| `--no-act` | Nicht auf das Ziel schreiben; Vorarbeiten und Lesen bleiben möglich. |
| `-N NUMMER` | Gezielten Partitionseintrag verändern; fehlt nicht automatisch in jeder Lücke. |
| `--backup`, `--backup-file` | Tabellensektoren sichern; Default kann ins Heimatverzeichnis schreiben. |
| `--force` | Konsistenzprüfungen abschalten, keine Standardoption. |
| `--move-data` | Daten bei Verlagerung bewegen; riskant und nicht atomar. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundener Ausschnitt eines Eingabeplans:
label: gpt
unit: sectors
start=2048, size=2048
```

Bei 512-Byte-Sektoren wäre der Eintrag 1 MiB lang. Der Ausschnitt ist absichtlich kein vollständiger freigegebener Importplan. Größe und Anfang müssen zum gesamten Medium passen; ein aus einem anderen Ziel kopierter Dump braucht eine vollständige Prüfung von IDs, Grenzen und belegten Bereichen.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Reproduzierbarer Plan:** Partitionstabellen in lesbarer Form vergleichen. **Sicherung:** Tabellendaten zusätzlich zu einem tatsächlichen Datenbackup dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Umleitungen aus ungeprüften Dateien können einen vollständigen Schreibauftrag liefern. Standard-Backuppfade sind außerhalb einer isolierten Übung. Schutzumgehung und Kernel-Synchronisierung nicht als harmlose Parameter behandeln. Kein Dump eines realen Geräts, kein Import oder Datenverschieben ausgeführt; Programm fehlt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| JSON-Import scheitert | Nur dokumentiertes Textformat ist Eingabe. |
| Unerwartete IDs doppelt | Dump von anderem Medium unverändert übernommen. |
| Neue Größe abweichend | Ausrichtung/Suffixe änderten den Plan; Sektoren und Einheiten nachvollziehen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; sfdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fdisk` | Interaktiver Editor aus derselben Familie. |
| `sgdisk` | GPT-spezifische Skriptverwaltung. |
| `partprobe` | Kernelansicht nach Tabelle abgleichen. |

Ausgangsdatensatz 243 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
