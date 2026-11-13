---
id: "sgdisk"
name: "sgdisk"
command: "sgdisk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "sgdisk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 244
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; sgdisk fehlt"
---

# sgdisk – GPT-Aktionen in Skripten ausdrücklich auswählen

## 1. Kurzbeschreibung

`sgdisk` ist die kommandozeilenorientierte GPT-Verwaltung aus GPT fdisk. Anders als der interaktive Verwandte gdisk führt es Änderungen gewöhnlich ohne abschließende Bestätigung aus. Für reale Ziele sind passende administrative Rechte nötig.

## 2. Was macht der Befehl?

Optionen werden in der angegebenen Reihenfolge verarbeitet. Sortieren und danach Löschen einer Partitionsnummer kann deshalb einen anderen Eintrag treffen als Löschen vor dem Sortieren. Eine gespeicherte Tabelle umfasst nicht die Nutzdaten. Interne Kurztypcodes, eindeutige Partitions-GUID und Dateisystem-UUID sind unterschiedliche Werte.

Quelle, am 2026-11-13 gelesen: [sgdisk-Projekthandbuch](https://manpages.debian.org/trixie/gdisk/sgdisk.8.en.html)

## 3. Syntax

```text
sgdisk [OPTIONEN] ZIEL
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-i NUMMER`, `--info=NUMMER` | Details eines Eintrags anzeigen. |
| `-b DATEI`, `--backup=DATEI` | Aktuellen Speicherstand der Tabelle binär exportieren. |
| `-d NUMMER` | Eintrag löschen; keine sichere Datenlöschung. |
| `-c NUMMER:NAME` | GPT-Partitionsnamen ändern, nicht Dateisystemlabel. |
| `-G` | Datenträger-/Partitions-GUIDs neu setzen; Typ-GUIDs bleiben. |
| `-e` | Backup-GPT an das Ende verschieben; echte Änderung. |
| `-g` | MBR/BSD zu GPT konvertieren; Startfähigkeit beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
sgdisk --info=1 ZIEL
Zu prüfende Felder: Typ-GUID, eindeutige GUID, Start, Ende, Name
```

Dieses lesende Muster würde genau Eintrag 1 beschreiben. Einträge mit anderer Nummer bleiben eine andere Auswahl; Nummerierungen können nach Sortierung wechseln. Der Bericht wäre kein Nachweis, dass die Datei- oder Bootdaten im beschriebenen Bereich gesund sind. Hier gibt es keine tatsächliche GPT-Ausgabe.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Skriptplanung:** Tabellenoperationen explizit statt interaktiv formulieren. **Klonverwaltung:** Doppelte GUIDs verstehen, bevor Konfigurationen absichtlich neu zugeordnet werden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Werkzeug fragt bei normalen Änderungen nicht allgemein nach einer Endfreigabe. Reihenfolge, kurze Optionsbuchstaben und Doppelpunkte gehören zum Schreibauftrag. GUID-Änderungen können Boot-/Mountverweise ungültig machen. Backup-/Konvertierungsbefehle sind keine ungefährlichen Probeparameter. Programm fehlt, keine Aktion ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Falscher Eintrag gelöscht | Nummern nach vorangegangener Sortierung anders. |
| Partitionsname nicht Dateisystemname | Zwei verschiedene Metadatenebenen. |
| Backup enthält bereits Änderungen | Export des aktuellen Speicherstands, nicht zwingend Ausgangszustand. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; sgdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `gdisk` | Interaktive Oberfläche. |
| `sfdisk` | Andere Syntax und Skriptformate. |
| `blkid` | Dateisystem- und Partitionskennungen unterscheiden. |

Ausgangsdatensatz 244 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
