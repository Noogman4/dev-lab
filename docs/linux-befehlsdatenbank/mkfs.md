---
id: "mkfs"
name: "mkfs"
command: "mkfs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "mkfs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 227
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# mkfs – Den Dateisystem-Ersteller bewusst auswählen

## 1. Kurzbeschreibung

`mkfs` ist ein älteres Frontend für dateisystemspezifische Ersteller. Eine Ausführung kann bestehende Dateisystemstrukturen überschreiben. Das Projekthandbuch bevorzugt die konkreten Programme `mkfs.TYP`. Auf realen Datenträgern sind entsprechende Verwaltungsrechte nötig.

## 2. Was macht der Befehl?

Das Frontend sucht den eigentlichen Ersteller über PATH. Der Typ bestimmt Optionen, Einheiten und Schutzprüfungen. Ohne Typ kann eine Vorgabe wie ext2 greifen; das ist keine automatische Erkennung dessen, was erhalten werden soll. Das Programm erstellt ein Dateisystem, keine Partitionstabelle, und hängt nichts ein.

Quelle, am 2026-11-13 gelesen: [mkfs-Projekthandbuch](https://manpages.debian.org/trixie/util-linux/mkfs.8.en.html)

## 3. Syntax

```text
mkfs [ALLGEMEINE_OPTIONEN] -t TYP [TYP_OPTIONEN] ZIEL [GROESSE]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-t TYP` | Ersteller auswählen; allgemeine Option vor typabhängigen Optionen. |
| `--help` | Frontendhilfe anzeigen, nicht die gesamte Hilfe aller Ersteller. |
| `--verbose` | Erstelleraufruf anzeigen und gewöhnlich ausführen; kein normaler Trockenlauf. |
| mehrfach `-V` | Dokumentierter Frontend-Testmodus unterdrückt Ersteller-Ausführung; lokal nicht erprobt. |
| `--version` | Version anzeigen; -V hat mit weiteren Argumenten andere Bedeutung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
mkfs -t ext4 ZIEL
Bedeutung: passenden ext4-Ersteller mit Ziel beauftragen
```

Das Muster ist eine Schreiboperation, keine Prüfung auf ein vorhandenes ext4. Eine spätere Größenzahl ist laut Frontend eine Blockzahl; die tatsächliche Interpretation und Erzeugung muss im konkreten Erstellerhandbuch geklärt werden. Es gibt hier weder Ziel noch Formatierungsausgabe.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Werkzeugketten verstehen:** Frontend und eigentlichen Ersteller trennen. **Dokumentationen berichtigen:** Eine Dateisystemanlage nicht als lesenden Hilfe- oder Statusbefehl einstufen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Falscher Typ, falscher Bereich oder falsches PATH-Programm kann Daten zerstören. Ein vorhandenes Dateisystem wird durch Formatierung nicht repariert. Keine Erzwingungsoptionen ergänzen, keine realen Medien oder Benutzerdateien als Versuchsziele verwenden.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Ersteller fehlt | mkfs.TYP nicht vorhanden; keine andere Formatierung improvisieren. |
| Unbekannte Option | Frontend- und Typoptionen verwechselt; jeweiliges Handbuch lesen. |
| Neues Dateisystem, alte Daten weg | Anlage statt Prüfung gewählt; nicht weiter schreiben. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `mkfs.ext4` | Konkreter ext-Ersteller. |
| `mkfs.btrfs` | Konkreter Btrfs-Ersteller. |
| `fsck` | Prüferauswahl statt Neuanlage. |

Ausgangsdatensatz 227 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
