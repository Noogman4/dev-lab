---
id: "losetup"
name: "losetup"
command: "losetup"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "losetup"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 224
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# losetup – Abbilddateien und Loop-Geräte zuordnen

## 1. Kurzbeschreibung

`losetup` verknüpft Dateien mit Loop-Blockgeräten, zeigt Zuordnungen oder löst sie. Eine Zuordnung ist eine Kernelzustandsänderung, selbst wenn die Datei im temporären Ordner liegt. Dafür sind üblicherweise administrative Rechte nötig.

## 2. Was macht der Befehl?

Ein Loop-Gerät stellt einen Bereich einer Datei als Blockgerät bereit. Es erzeugt weder automatisch ein Dateisystem noch einen Mount. Eine schreibende Verwendung des Loop-Geräts verändert die zugrunde liegende Datei. Mehrere unabhängige Zuordnungen derselben Datei können konkurrierende Zugriffe verursachen.

Quelle, am 2026-11-13 gelesen: [losetup-Handbuch](https://manpages.debian.org/trixie/mount/losetup.8.en.html)

## 3. Syntax

```text
losetup --list [LOOPGERAET]
losetup --find --show [OPTIONEN] ABBILD
losetup --detach LOOPGERAET
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `--list`, `--output SPALTEN` | Status mit ausdrücklich gewählten Feldern anzeigen. |
| `--find` | Ohne Datei ein freies Gerät suchen; mit Datei zuordnen. |
| `--show` | Bei Zuordnung gewählten Gerätenamen ausgeben. |
| `--nooverlap` | Bei --find bereits zugeordnete Datei erkennen/wiederverwenden; keine vollständige Prozesssperre. |
| `--read-only` | Neue Zuordnung lesend einrichten; bleibt eine Systemänderung. |
| `--offset`, `--sizelimit` | Abgebildeten Dateibereich in Bytes bestimmen. |
| `--partscan` | Kernel nach Partitionen suchen lassen. |
| `--detach-all` | Alle Zuordnungen lösen; gefährlicher systemweiter Umfang. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Zuordnungsschema:
LOOPGERAET -> ABBILD
Offset: 1048576 Byte
Sizelimit: 2097152 Byte
```

Der sichtbare Bereich beginnt nach 1 MiB in der Datei und ist höchstens 2 MiB lang. Diese Werte sind keine Sektornummern. Ein Rückgabename wäre bei echtem --find --show festzuhalten, nicht als pauschales loop0 vorauszusetzen. Hier wird keinerlei Loop-Gerät angelegt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Abbildanalyse planen:** Dateibereiche und eventuelle Partitionen zuordnen. **Verfügbarkeit klären:** Eine vorhandene Zuordnung von Dateisystem und Mount unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

--find ist zusammen mit Einrichtung nicht insgesamt gegen parallele Aufrufer atomar. Detach kann eine verzögerte Freigabe markieren; Erfolg bedeutet nicht immer sofortige Zerstörung eines noch verwendeten Geräts. Erst Nutzung geordnet beenden, kein --detach-all zum Aufräumen einer Einzelübung. Keine Zuordnung oder Ablösung ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Datei über mehrere Geräte sichtbar | Doppelte Zuordnungen; nicht gleichzeitig schreibend verwenden. |
| Gerät nach detach noch sichtbar | Verzögerte Freigabe oder aktive Nutzung; keine Gewaltmaßnahmen. |
| Partitionen falsch interpretiert | Sektorgröße und Offset nicht passend; Abbildlayout prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mount` | Hängt ein vorhandenes Dateisystem ein. |
| `findmnt` | Mountbeziehungen anzeigen. |
| `partx` | Partitionsinformationen für Kernel verwalten; eigener Eingriff. |

Ausgangsdatensatz 224 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
