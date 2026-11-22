---
id: "lsblk"
name: "lsblk"
command: "lsblk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "lsblk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 226
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# lsblk – Blockgeräte und ihre Abhängigkeiten darstellen

## 1. Kurzbeschreibung

`lsblk` zeigt Blockgeräte und ihre Beziehungen an. Normale Informationen aus sysfs/udev benötigen üblicherweise kein Root. Falls diese Daten fehlen, kann Dateisystemerkennung direkte Gerätezugriffe mit anderen Rechteanforderungen benötigen.

## 2. Was macht der Befehl?

Ein Baum zeigt Abhängigkeiten, keine einfache Liste unabhängiger physischer Platten. RAID, Device Mapper und Multipath können N:M-Beziehungen erzeugen. Derselbe Eintrag kann wiederholt erscheinen. MOUNTPOINT zeigt nur einen zugeordneten Pfad, MOUNTPOINTS gegebenenfalls mehrere; eine leere Zelle beweist nicht zuverlässig, dass ein Objekt unbenutzt ist.

Quelle, am 2026-11-13 gelesen: [lsblk-Handbuch](https://manpages.debian.org/trixie/util-linux/lsblk.8.en.html)

## 3. Syntax

```text
lsblk [OPTIONEN] [GERAET ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-o SPALTEN` | Spalten ausdrücklich wählen, statt veränderliche Standardausgabe zu parsen. |
| `-b` | Größen in Bytes anzeigen; Standard ist menschenlesbar mit 1024er-Schritten. |
| `-f` | Dateisystemfelder anzeigen; deren Metadatenquelle und Aktualität beachten. |
| `-J` | JSON; Kinderstruktur braucht NAME oder ausdrücklichen Baummodus. |
| `-l` | Flache Liste; Abhängigkeiten daraus nicht vollständig ablesbar. |
| `-d` | Abhängige/untergeordnete Geräte nicht ausgeben. |
| `-p` | Vollständige Gerätenamen anzeigen. |
| `--merge` | Komplexe Beziehungen übersichtlicher gruppieren. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundener Baum:
lerndisk   disk   1073741824
└─lernteil part    536870912
```

Bei ausdrücklich gewählter Byteanzeige wären das 1 GiB für das ganze Objekt und 512 MiB für die Partition. Beide Größen zu addieren würde denselben Speicher teilweise doppelt zählen. Der Typ part sagt nichts darüber aus, welches Dateisystem tatsächlich gespeichert ist.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Speicherstruktur erklären:** Partition, Verschlüsselung, LVM und physisches Laufwerk unterscheiden. **Inventar planen:** Spalten und Einheit vor dem Vergleich festlegen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die reine Übersicht verändert keine Partitionen. Sie kann Seriennummern, Kennungen und private Pfade offenlegen. Veraltete udev-Daten und gleichzeitige Änderungen begrenzen die Aussage. Gerätenamen, Größe oder ein einzelner Mountpunkt reichen nicht als alleinige Löschfreigabe. Hier keine reale Inventur ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Doppelte Namen im Baum | Mehrere Beziehungen, nicht zwingend doppelte Hardware. |
| Dateisystemfeld leer | Quelle fehlt, Erkennung eingeschränkt oder noch nicht aktuell. |
| JSON ohne children | NAME/--tree fehlt oder flache Ausgabe gewählt. |
| Skript bricht nach Update | Spalten/Formate nicht ausdrücklich gewählt. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `findmnt` | Mountbeziehungen statt primär Geräteschichten. |
| `blkid` | Direkte Signatur-/Kennungsanalyse. |
| `ls` | Listet Dateinamen; andere Aufgabe. |

Ausgangsdatensatz 226 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
