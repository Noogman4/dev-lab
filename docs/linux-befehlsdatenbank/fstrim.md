---
id: "fstrim"
name: "fstrim"
command: "fstrim"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "fstrim"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 221
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# fstrim – Freie Dateisystembereiche für Discard melden

## 1. Kurzbeschreibung

`fstrim` meldet unbenutzte Bereiche eines eingehängten Dateisystems an den Speicherstack. Es löscht keine benannten Dateien, ist aber eine wirkliche Speicherverwaltungsaktion mit administrativen Rechteanforderungen.

## 2. Was macht der Befehl?

Discard betrifft freie Bereiche aus Sicht des Dateisystems. SSD, Thin Provisioning, Verschlüsselungs- und RAID-Schichten können die Weitergabe verändern oder nicht unterstützen. Die gemeldete Bytezahl ist eine potenzielle Discardmenge und kann bei Wiederholung gleich bleiben; sie ist keine Messung neu freigegebenen physischen Speichers und kein sicherer Löschbeweis.

Quelle, am 2026-11-13 gelesen: [fstrim-Handbuch](https://manpages.debian.org/trixie/util-linux/fstrim.8.en.html)

## 3. Syntax

```text
fstrim [OPTIONEN] MOUNTPUNKT
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-v` | Potenzielle Discardmenge anzeigen; nicht mit neu gewonnenem Speicher verwechseln. |
| `-n`, `--dry-run` | In der dokumentierten Version kein FITRIM-ioctl; andere Vorarbeiten bleiben. |
| `-o BYTES`, `-l BYTES` | Suchbereich über Offset und Länge begrenzen. |
| `-m BYTES` | Mindestlänge zusammenhängender freier Bereiche; Rundung auf Blockgröße möglich. |
| `-a`, `-A` | Viele Mounts beziehungsweise fstab-Ziele bearbeiten; ausdrücklich kein Lernstandard. |
| `--quiet-unsupported` | Nichtunterstützung verbergen und Status beeinflussen; Diagnose nicht blind unterdrücken. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Fiktiver Bericht: LERNMOUNT: 1048576 bytes trimmed
```

Die angenommene Zahl entspricht 1 MiB potenziell gemeldeter Bereiche. Sie beweist nicht, dass 1 MiB zuvor belegt war, dass Zellen physisch gelöscht wurden oder dass derselbe Betrag beim nächsten Lauf fehlt. Ein Mountpfad statt eines rohen Gerätepfads wäre das gewöhnliche Ziel.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Geplante Speicherpflege:** Unterstützte SSD-/Thin-Provisioning-Stacks nach bestehendem Wartungsplan pflegen. **Berichte einordnen:** Wiederholt gemeldete Zahlen richtig lesen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Keine Trims, Timeränderungen oder Mountaktionen als Dokumentationsnachweis. Discard kann Datenrettungsmöglichkeiten aus freien Bereichen einschränken und Last erzeugen. `-a` erweitert den Bereich erheblich. Ein erfolgreicher Teil eines Sammellaufs ist kein Gesamterfolg; --all unterscheidet 0, 32 (alle fehlgeschlagen) und 64 (teilweise fehlgeschlagen).

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Operation not supported | Dateisystem oder darunterliegender Stack unterstützt Discard nicht; nichts erzwingen. |
| Bytezahl wiederholt gleich | Potenzielle Bereiche werden erneut gemeldet; keine neue Gewinnmessung. |
| Kein Gerät unter dem Pfad | Mountpunkt und Gerätepfad verwechselt; Zielplanung klären. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `blkdiscard` | Discard direkt auf Blockobjekten; anderer, gefährlicherer Zugriff. |
| `findmnt` | Mountzuordnung verstehen. |
| `df` | Dateisystembelegung anzeigen; andere Messgröße. |

Ausgangsdatensatz 221 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
