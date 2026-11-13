---
id: "fdisk"
name: "fdisk"
command: "fdisk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "fdisk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 218
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; fdisk fehlt"
---

# fdisk – Partitionstabellen anzeigen und Änderungen bewusst schreiben

## 1. Kurzbeschreibung

`fdisk` aus util-linux ist ein interaktiver Partitionstabelleneditor mit separatem Listenmodus. Anzeigen und Schreiben haben grundverschiedene Wirkungen. Für rohe Geräte sind passende, häufig administrative Rechte nötig.

## 2. Was macht der Befehl?

Partitionstabellen beschreiben Bereiche eines Datenträgers. Sie enthalten nicht automatisch das gesamte Dateisystemwissen. GPT, MBR und andere Formate unterscheiden sich; moderne Ausrichtung richtet sich nach Gerätetopologie, nicht nach historischen Zylindern. Ohne -l wird ein Dialog für ein bestimmtes Ziel geöffnet. Listen ohne Ziel können mehrere reale Geräte erfassen.

Quelle, am 2026-11-13 gelesen: [fdisk-Projekthandbuch](https://manpages.debian.org/trixie/fdisk/fdisk.8.en.html)

## 3. Syntax

```text
fdisk [OPTIONEN] GERAET
fdisk -l [GERAET ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-l`, `--list` | Tabellen auflisten und beenden; ohne Ziel systemweiter Bereich. |
| `-o SPALTEN` | Gewünschte Spalten wählen; Standardausgabe ist kein stabiles Skriptformat. |
| `-b BYTES` | Sektorgröße überschreiben; normalerweise automatisch erkennen lassen. |
| `--lock` | Sperre gegen konkurrierende Werkzeugzugriffe anfordern. |
| `-w WHEN`, `-W WHEN` | Löschen bestehender Signaturen steuern; keine harmlosen Anzeigeoptionen. |
| Dialog `p`, `q`, `w` | Tabelle anzeigen, ohne Schreiben beenden, Tabelle schreiben. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundene Tabelle:
Start 2048   Ende 4095   Sektoren 2048
```

Die angegebene Länge ist einschließlich beider Grenzen 4095 - 2048 + 1 = 2048 Sektoren. Bei 512 Byte pro Sektor sind das 1 MiB. Das ist eine Sektorrechnung und keine Empfehlung für eine sinnvolle Partitionsgröße. Das `w` im Dialog ist eine Schreibaktion; `q` verwirft nur noch ungeschriebene Änderungen.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Inventur vorbereiten:** Tabellenformat, Start, Ende und Einheiten einer bereits autorisierten Bestandsaufnahme verstehen. **Partitionierung planen:** Dateisystemänderung und Tabellenänderung getrennt abstimmen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Neue Tabellen und Signaturbereinigung können Daten unzugänglich machen. Ein scheinbar passendes Label beweist keine Zielidentität. Partitionsverkleinerung ersetzt keine vorgelagerte Dateisystemverkleinerung. Keine realen Listen, Dialoge oder Kernel-Neueinleseaktionen ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Argumente aus alter Anleitung passen nicht | Implementierung und Version vergleichen; fdisk ist hier util-linux. |
| Kernel sieht alte Grenzen | Ziel noch verwendet oder Neueinlesen fehlgeschlagen; keine erzwungene Folgeaktion. |
| Sektorzahl und Bytes passen nicht | Logische Sektorgröße und inklusive Endposition prüfen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; fdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `cfdisk` | Textoberfläche für Partitionierung. |
| `sfdisk` | Skriptfähige Tabellenverwaltung. |
| `resize2fs` | Ändert das ext-Dateisystem, nicht die Partitionstabelle. |

Ausgangsdatensatz 218 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
