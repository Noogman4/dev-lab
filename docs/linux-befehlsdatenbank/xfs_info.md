---
id: "xfs_info"
name: "xfs_info"
command: "xfs_info"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "xfs_info"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 251
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; xfs_info fehlt"
---

# xfs_info – XFS-Geometrie ohne Größenänderung lesen

## 1. Kurzbeschreibung

`xfs_info` beschreibt die Geometrie eines vorhandenen XFS-Dateisystems und verändert dessen Inhalte nicht. Ein lesbares eigenes Abbild braucht kein Root; rohe Geräte unterliegen deren Dateirechten. Das Werkzeug ist keine Reparatur und keine Vergrößerung.

## 2. Was macht der Befehl?

Die Abschnitte der Ausgabe trennen Metadaten, Daten, Namen, Log und gegebenenfalls Realtime-Bereich. Blockgröße und Anzahl gehören zusammen; Stripeeinheiten können in Dateisystemblöcken stehen. Ein Featurewert wie reflink=1 beschreibt eine Fähigkeit, nicht ob alle Dateien gerade gemeinsam genutzte Blöcke haben.

Quelle, am 2026-11-13 gelesen: [xfs_info-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/xfs_info.8.en.html)

## 3. Syntax

```text
xfs_info [-t MOUNTTABELLE] MOUNTPUNKT_ODER_GERAET_ODER_ABBILD
xfs_info -V
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| Zieloperand | Mountpunkt, Blockgerät oder Rohabbild des vorhandenen XFS auswählen. |
| `-t DATEI` | Alternative Mounttabelle für Mountpunktauswertung; ohne Wirkung bei Geräte-/Abbildziel. |
| `-V` | Version anzeigen und beenden; kein Ziel nötig. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Geometriemuster:
data: bsize=4096, blocks=131072, sunit=16, swidth=64
```

Die Datenregion hätte 512 MiB. Eine Stripeunit entspräche 16 × 4096 = 65536 Bytes, die Stripebreite 64 × 4096 = 262144 Bytes. Das wären vier Einheiten pro Stripe. Diese Rechnung beschreibt nur das Schema; sie prüft kein reales RAID und misst keinen freien Platz.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Geometrie verstehen:** Dateisystemblöcke von Gerätesektoren unterscheiden. **Betriebsdokumentation:** Features, Log und Allokationsgruppen einer bereits autorisierten Auskunft zuordnen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Die Anzeige kann Pfade und Gerätebezüge enthalten. Unbekannte Rohabbilder sind komplexe Parser-Eingaben. Aus Geometrie folgt keine sichere Hardwareidentität oder Inhaltsintegrität. Programm fehlt; keine echte Mount-/Geräte-/Abbildabfrage wurde ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kein XFS erkannt | Falscher Zieltyp oder Bereich; keine Neuanlage als Fehlerbehebung. |
| Kapazität passt nicht zu df | Gesamtgeometrie und freier nutzbarer Platz verschieden. |
| Stripewerte falsch umgerechnet | bsize als Einheit der blks-Angaben beachten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; xfs_info fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mkfs.xfs` | Erzeugt XFS mit Geometrieparametern. |
| `xfs_growfs` | Vergrößert XFS, kein Synonym zur Anzeige. |
| `xfs_repair` | Prüft/repariert mit eigenem Ablauf. |

Ausgangsdatensatz 251 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
