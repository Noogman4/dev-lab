---
id: "mkfs_xfs"
name: "mkfs.xfs"
command: "mkfs.xfs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "mkfs.xfs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 232
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; mkfs.xfs fehlt"
---

# mkfs.xfs – XFS-Geometrie und Anlageparameter festlegen

## 1. Kurzbeschreibung

`mkfs.xfs` erzeugt ein neues XFS-Dateisystem. Der Inhalt eines vorhandenen Ziels kann dabei zerstört werden. Eigene Abbilddateien sind ohne Root möglich; reale Geräte verlangen passende Verwaltungsrechte.

## 2. Was macht der Befehl?

XFS organisiert Daten in Allocation Groups und führt ein Metadatenlog. Blockgröße, Sektorgröße, Log und Features sind getrennte Parameter. Der angegebene Typ beweist nicht, dass ältere Kernel die erzeugten Features verstehen. Die verlinkte aktuelle Dokumentation nennt eine Mindestgröße der Datensektion; winzige Beispiele aus alten Anleitungen sind nicht ungeprüft übertragbar.

Quelle, am 2026-11-13 gelesen: [mkfs.xfs-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/mkfs.xfs.8.en.html)

## 3. Syntax

```text
mkfs.xfs [OPTIONEN] ZIEL
mkfs.xfs -V
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-N` | Parameter anzeigen, ohne ein Dateisystem anzulegen; lokal nicht erprobt. |
| `-L NAME` | XFS-Label setzen; verlinktes Handbuch begrenzt auf 12 Zeichen. |
| `-b size=BYTES` | Dateisystemblockgröße wählen; Kernelgrenzen beachten. |
| `-d file,name=DATEI,size=GROESSE` | Explizite Abbilddateianlage planen; schreibt die Datei. |
| `-m OPTION=WERT` | Metadatenfeatures wählen, etwa Prüfsummen/Reflinks; Kompatibilität separat. |
| `-K` | Discard bei Anlage unterlassen. |
| `-f` | Überschreiben erkannter Inhalte erzwingen; keine Standardlösung. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Fiktiver Geometrieauszug:
data: bsize=4096, blocks=131072
```

Die angenommene Datensektion umfasst 512 MiB. Das ist nicht gleich dem freien Platz für Benutzerdateien. Ein angezeigtes crc-Feature betrifft Metadatenprüfsummen, keine vollständige Inhaltsauthentifizierung. Ein Parameterbericht mit -N ist keine tatsächliche Anlage.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Speicherlayout planen:** Allocation Groups, Log und Gerätegeometrie aufeinander abstimmen. **Kompatibilität dokumentieren:** Erzeugte Featureliste und Werkzeugversion vor späterer Nutzung festhalten.

## 7. Risiken, Nebenwirkungen und Vorsicht

Formatierung ist keine Reparatur. Externe Log-/Realtime-Ziele erweitern den Schreibbereich. Force und widersprüchliche Geometriewerte können Daten verlieren lassen. Keine XFS-Anlage oder Geräteprobe ausgeführt; Programm fehlt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateisystem zu klein | Mindestgeometrie der konkreten Version nicht erfüllt. |
| Respecification error | Option mehrfach widersprüchlich in Konfiguration und Kommandozeile angegeben. |
| Kernel kann nicht mounten | Neue Features oder unpassende Blockgröße; nicht blind neu formatieren. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; mkfs.xfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xfs_info` | Geometrie vorhandener XFS-Strukturen anzeigen. |
| `xfs_repair` | Strukturreparatur mit eigenen Risiken. |
| `mkfs.ext4` | Anderer Dateisystemersteller. |

Ausgangsdatensatz 232 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
