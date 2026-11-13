---
id: "parted"
name: "parted"
command: "parted"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "parted"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 237
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# parted – Partitionen mit GNU Parted verändern

## 1. Kurzbeschreibung

`parted` zeigt und verändert Partitionstabellen. Schreibende Befehle gehören in einen Wartungsablauf; sie sind kein Lesecheck. Auf realen Datenträgern sind passende administrative Rechte nötig.

## 2. Was macht der Befehl?

Eine Partition und ihr Dateisystem sind getrennte Strukturen. `resizepart` ändert das Partitionsende, nicht den enthaltenen Datenbestand. Ein Dateisystemtyp bei `mkpart` ist kein ausgeführtes mkfs. Ohne Ziel kann das erste gefundene Gerät gewählt werden. Optionen und Einheiten deshalb vor dem Start festlegen; eine abschließende allgemeine Speichern-Frage ist kein verlässliches Schutzmodell.

Quelle, am 2026-11-13 gelesen: [GNU-Parted-Manpage bei Debian](https://manpages.debian.org/trixie/parted/parted.8.en.html)

## 3. Syntax

```text
parted [OPTIONEN] [ZIEL [BEFEHL [ARGUMENTE] ...]]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `print`, `print free` | Gewählte Tabelle beziehungsweise freie Bereiche anzeigen. |
| `unit EINHEIT` | Ausgabe und nicht ausdrücklich suffigierte Eingaben bestimmen; Sektoren und MiB unterscheiden. |
| `mklabel TYP` | Neue Partitionstabelle anlegen; vorhandene Zuordnung kann verloren gehen. |
| `mkpart ...` | Partitionseintrag erzeugen; Dateisystemanlage separat. |
| `resizepart NUMMER ENDE` | Endgrenze ändern; keine Dateisystemverkleinerung. |
| `-s`, `--script` | Rückfragen unterdrücken; kein Trockenlauf. |
| `-f`, `--fix` | Im Skriptmodus Fix-Antworten automatisch geben; kann schreiben. |
| `-m`, `-j` | Maschinen-/JSON-Ausgabe; Verfügbarkeit versionsabhängig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Planungsmuster: unit MiB, anschließend print free
Keine tatsächliche Tabellenanzeige und keine Änderung
```

Explizite MiB-Angaben vermeiden Verwechslung mit dezimalen MB oder unklaren Standardwerten. Freie Bereiche einer Partitionstabelle sind nicht derselbe freie Platz, den df innerhalb eines Dateisystems meldet. Ein späteres resizepart müsste auf dessen tatsächliche Datenreichweite abgestimmt werden.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Partitionierungsplan:** Ausrichtung und freie Lücken verstehen. **Kapazitätsänderung:** Reihenfolge von darunterliegendem Speicher, Partition und Dateisystem gesondert planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Änderungsbefehle können unmittelbar auf das Ziel wirken; quit nicht als Undo verwenden. -s/-f entfernen Interaktion statt Risiken. Verkleinern über belegte Dateisystembereiche zerstört Daten. Keine realen Tabellen eingelesen und keine Partition verändert. GNU-Webmanual war nicht abrufbar; die verlinkte Distributions-Manpage wurde tatsächlich gelesen.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateisystem nach resizepart unverändert | Nur Partitionsgrenze bearbeitet; getrennte Werkzeuge nötig. |
| Keine Rückfrage | Skriptmodus beziehungsweise direkte Aktion; kein Beweis für Harmlosigkeit. |
| Größe passt nicht | Einheit, Endposition und Ausrichtung kontrollieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fdisk` | Anderer Partitionstabelleneditor. |
| `partprobe` | Informiert den Kernel über Tabellenänderungen. |
| `resize2fs` | Ändert ext-Dateisystemgröße. |

Ausgangsdatensatz 237 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
