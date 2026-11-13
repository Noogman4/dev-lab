---
id: "cfdisk"
name: "cfdisk"
command: "cfdisk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "cfdisk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 212
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; cfdisk fehlt"
---

# cfdisk – Partitionstabellen interaktiv bearbeiten

## 1. Kurzbeschreibung

`cfdisk` ist ein textbasierter interaktiver Partitionstabelleneditor aus util-linux. Er benötigt für reale Datenträger üblicherweise administrative Zugriffsrechte. Er ändert Partitionierung, nicht automatisch das enthaltene Dateisystem.

## 2. Was macht der Befehl?

Änderungen werden zunächst im Speicher gesammelt und erst mit der Schreibaktion auf das Ziel übertragen. Ein Aufruf ohne Ziel kann ein Standardgerät öffnen; deshalb ist er keine harmlose Übung. Eine verkleinerte Partition kann Dateisystemdaten abschneiden, auch wenn die Oberfläche plausible Größen zeigt. Neuere Optionen wie `--read-only` müssen in der vorhandenen Version nachgewiesen werden.

Quelle, am 2026-11-13 gelesen: [cfdisk-Projekthandbuch bei Debian](https://manpages.debian.org/trixie/fdisk/cfdisk.8.en.html)

## 3. Syntax

```text
cfdisk [OPTIONEN] [GERAET]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-r`, `--read-only` | In der verlinkten aktuellen Version schreibgeschützt öffnen; lokale Verfügbarkeit prüfen. |
| `-z`, `--zero` | Mit leerer Tabelle im Arbeitsspeicher beginnen; löscht nicht bereits beim Start das Medium. |
| `--lock` | Exklusive BSD-Sperre anfordern; verhindert nicht jeden Fremdzugriff. |
| `q` | Ohne Schreiben beenden. |
| `W` | Partitionstabelle nach Bestätigung schreiben; Großbuchstabe beachten. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Plan: Startsektor 2048, Länge 1048576 Sektoren
Aktion q: geplante Tabelle verwerfen
Aktion W: geplante Tabelle dauerhaft schreiben
```

Bei angenommenen 512 Byte je logischem Sektor entsprechen 1048576 Sektoren 512 MiB. Sektorgröße und Bytegröße sind verschieden. Das ist nur eine Rechnung, keine am Rechner gelesene Partition. `q` verwirft ungeschriebene Planänderungen; bereits zuvor geschriebene Änderungen macht es nicht rückgängig.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Wartungsplanung:** Eine geplante Partitionstabelle vor dem Schreiben überprüfen. **Abgrenzung:** Dateisystemvergrößerung und Änderung einer Partitionsgrenze als getrennte Operationen behandeln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Das Schreiben einer falschen Tabelle kann alle vorhandenen Dateisysteme unzugänglich machen. Rückfragen sind keine Sicherung. Nach Schreiben kann der Kernel die neue Tabelle wegen aktiver Nutzung nicht übernehmen; keine hektischen Folgeaktionen erzwingen. Hier kein Programmstart und kein Datenträgerzugriff.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Keine Terminaloberfläche | Terminaltyp oder Programm fehlt; nicht als Gerätefehler interpretieren. |
| Neue Größe, alte Datenstruktur | Partition und Dateisystem wurden verwechselt; keine weiteren Schreibaktionen. |
| Kernel übernimmt Tabelle nicht | Ziel noch in Benutzung; Wartungsplan statt erzwungener Wiederholung. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; cfdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `fdisk` | Anderer Editor derselben Werkzeugfamilie. |
| `sfdisk` | Skriptfähige Tabellenverwaltung. |
| `lsblk` | Geräteschichten anzeigen. |

Ausgangsdatensatz 212 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
