---
id: "dumpe2fs"
name: "dumpe2fs"
command: "dumpe2fs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "dumpe2fs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 215
reviewed_at: "2026-11-13"
locally_checked_version: "dumpe2fs 1.47.0 (5-Feb-2023), als Hilfswerkzeug an eigenen Abbildern geprüft"
---

# dumpe2fs – Superblock und Blockgruppen von ext lesen

## 1. Kurzbeschreibung

`dumpe2fs` zeigt Verwaltungsinformationen von ext2/ext3/ext4 an. Es prüft nicht sämtliche Nutzdaten und führt keine Reparatur aus. Ein lesbares eigenes Abbild benötigt kein Root; rohe Geräte erfordern passende Zugriffsrechte.

## 2. Was macht der Befehl?

Der Superblock enthält unter anderem Kennung, Blockgröße, Zähler und Featureflags. Gruppeninformationen beschreiben die Organisation des Dateisystems. Eine Anzeige an einem gemounteten, gleichzeitig veränderten Dateisystem kann alt oder inkonsistent sein. `-b` zeigt bereits als schlecht markierte Blöcke und startet keinen neuen Oberflächentest.

Quelle, am 2026-11-13 gelesen: [dumpe2fs-Handbuch](https://manpages.debian.org/trixie/e2fsprogs/dumpe2fs.8.en.html) und lokale Manpage 1.47.0

## 3. Syntax

```text
dumpe2fs [OPTIONEN] GERAET_ODER_ABBILD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-h` | Nur Superblock anzeigen, nicht alle Blockgruppen; hier keine Hilfeoption. |
| `-g` | Gruppendeskriptoren als Doppelpunktfelder ausgeben. |
| `-b` | Im Dateisystem vermerkte fehlerhafte Blöcke ausgeben. |
| `-x` | Detailblocknummern hexadezimal darstellen. |
| `-i` | Spezielles e2image-Abbild lesen, nicht allgemein für jede Rohkopie nötig. |
| `-f` | Unbekannte Features trotz möglicher Fehlinterpretation übergehen; kein Standard. |
| `-V` | Version anzeigen und beenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Superblockmuster:
Block count: 8192
Block size: 1024
```

Bei diesen angenommenen Werten beträgt die logische Dateisystemgröße 8192 × 1024 = 8388608 Bytes, also 8 MiB. Das ist nicht die belegte Größe einer Host-Abbilddatei und sagt nichts über freie Nutzerbytes aus. Blockzähler, Inodezähler und reservierte Blöcke sind verschiedene Größen.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Bestandsanalyse:** Featureflags und Blockgröße einer gesicherten ext-Kopie dokumentieren. **Fehlerklärung:** Vermerkte schlechte Blöcke von neu erkannten Hardwarefehlern unterscheiden.

## 7. Risiken, Nebenwirkungen und Vorsicht

Lesen belastet Speicher und Geräte; ein Strukturbericht ersetzt weder `e2fsck` noch eine Inhaltsprüfung. `-f` kann unzuverlässige Interpretation erzwingen. Nicht vermeintlich passende Alternativsuperblöcke oder Blockgrößen raten. Keine reale Datenträgerabfrage in dieser Übung.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Bad magic number | Falscher Typ, falscher Bereich oder beschädigter Superblock; keine Formatanlage versuchen. |
| Keine Ausgabe mit -b | Keine gespeicherten schlechten Blöcke; kein Nachweis eines fehlerfreien Laufwerks. |
| Freie Zähler wirken widersprüchlich | Laufende Änderungen oder andere Zählgrößen; konsistente Kopie und Einheiten vergleichen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** dumpe2fs 1.47.0 (5-Feb-2023), als Hilfswerkzeug an eigenen Abbildern geprüft. Das Erklärungsmuster in Abschnitt 5 wurde nicht ausgeführt. Ergänzender praktischer Nachweis aus den späteren Datensätzen 229–231, 242 und 250: dumpe2fs -h las Label, Features und Blockgeometrie ausschließlich selbst angelegter Abbilddateien. Diese Abläufe stehen dort vollständig. Praktische Prüfung realer Geräte, vollständiger Blockgruppenberichte, schlechter Blöcke und anderer Versionen offen. Quellenprüfung, Strukturprüfung und begrenzter Hilfstest sind getrennte Nachweise.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `tune2fs -l` | Andere Anzeige ausgewählter ext-Metadaten; Änderungsoptionen separat. |
| `debugfs` | Tiefergehende Strukturanalyse. |
| `e2fsck` | Strukturen prüfen, gegebenenfalls reparieren. |

Ausgangsdatensatz 215 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
