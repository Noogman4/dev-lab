---
id: "systemd_resolve"
name: "systemd-resolve"
command: "systemd-resolve"
category: "Netzwerk Grundlagen"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Netzwerk Grundlagen", "systemd-resolve"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 444
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale systemd-resolve-Manpage"
---

# systemd-resolve – Historische Resolveroberfläche mit eigener Syntax

## 1. Kurzbeschreibung

systemd-resolve ist die ältere CLI für systemd-resolved. Der eingefrorene Katalogname bleibt erhalten. Auf aktuellen Installationen ist üblicherweise resolvectl die dokumentierte Oberfläche; alte Optionen werden nicht unverändert übertragen.

## 2. Was macht der Befehl?

Als überprüfbare historische Primärquelle dient die Handbuchdatei aus systemd v238. Dort wird ein Name direkt als Operand aufgelöst und --status als Option angegeben. Bei resolvectl stehen query und status als Unterbefehle. Beide betreffen den Resolverdienst, nicht die Registrierung einer DNS-Zone. Historische Dokumentation beweist keine lokale Verfügbarkeit.

Quelle, am 2026-11-13 gelesen: [systemd v238: originale systemd-resolve-Handbuchdatei](https://raw.githubusercontent.com/systemd/systemd/v238/man/systemd-resolve.xml)

## 3. Syntax

```text
systemd-resolve [OPTIONEN] NAME_ODER_ADRESSE
systemd-resolve --status
Heutige Vergleichsform: resolvectl status
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--status` | Historische globale und linkbezogene DNS-Anzeige. |
| `--statistics` | Statistiken anzeigen. |
| `--type=TYP` | Bestimmten DNS-Record abfragen. |
| `--interface=LINK` | Linkwahl, soweit zur Konfiguration passend. |
| `--flush-caches` | Dienstcache leeren; echte Änderung. |
| `--set-dns=SERVER` | Historischer Setzmodus, kein Server-Test. |
| `--revert` | Linkbezogene DNS-Konfiguration zurücksetzen. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Ziel klären

Diese Leseübung führt den folgenden Funktionsaufruf nicht aus. Die genannten Ziele sind Platzhalter oder erfundene Beispieldaten. Vor einem späteren echten Einsatz wären die passende Implementierung, Zielauswahl, Rechte und Auswirkungen gesondert zu prüfen.

### Schritt 2: Muster und Bedeutung lesen

**Nicht ausgeführtes Muster; keine gemessene Ausgabe:**

```text
Historisch, nicht ausgeführt: systemd-resolve --status
Heute als Vergleich: resolvectl status
```

Die Zeilen erklären eine Syntaxmigration. Sie sind keine automatisch auszuführende Fallbackkette. Ein fehlendes systemd-resolve ist kein Defekt, wenn die Distribution resolvectl bereitstellt. Weder Resolver noch Dienststatus wurden abgefragt.

### Schritt 3: Aussagegrenze festhalten

Die Funktionsausführung bleibt praktisch offen. Quellen- und Strukturprüfung bestätigen weder Erreichbarkeit noch die Wirksamkeit einer realen Aktion.

## 6. Typische Anwendungsfälle

**Alte Anleitungen migrieren:** Semantik statt bloß Programmnamen übersetzen. **Fehlerberichte verstehen:** Handbuchversion und lokale Programmoberfläche benennen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Auflösungen können Netzverkehr erzeugen; Setz- und Resetoptionen ändern Dienstzustand. Alte Angaben über Rechte und Managerzusammenarbeit sind versionsgebunden. Keine alten Pakete installiert, Kompatibilitätssymlinks angelegt oder Systemdateien geändert.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| command not found | Lokale aktuelle Schnittstelle prüfen; keine Altinstallation erzwingen. |
| query unbekannt | Alte Optionssyntax mit neuer Unterbefehlssyntax vermischt. |
| Status vorhanden, DNS scheitert | Konfiguration ist kein Erreichbarkeitsbeweis. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Den konkreten Unterbefehl beziehungsweise Modus vor dem Start lesen. Rückgabestatus, Diagnose und fachliches Ergebnis gemeinsam auswerten; fehlende Ausgabe ist kein automatischer Erfolgsnachweis. Nur die dokumentierte Variante und passende Version verwenden.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale systemd-resolve-Manpage. Nicht praktisch geprüft; praktische Prüfung offen. Das Erklärungsmuster und alle echten Eingriffe oder Netzabfragen wurden nicht ausgeführt; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `resolvectl` | Aktuelle Oberfläche. |
| `systemd-resolved` | Zugehöriger Resolverdienst. |
| `nmcli` | Kann DNS-Konfiguration liefern. |

Ausgangsdatensatz 444 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
