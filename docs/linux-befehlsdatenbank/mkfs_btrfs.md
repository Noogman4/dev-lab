---
id: "mkfs_btrfs"
name: "mkfs.btrfs"
command: "mkfs.btrfs"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "mkfs.btrfs"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 228
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; mkfs.btrfs fehlt"
---

# mkfs.btrfs – Ein neues Btrfs-Dateisystem planen

## 1. Kurzbeschreibung

`mkfs.btrfs` legt Btrfs-Strukturen auf einem oder mehreren Zielen an. Vorhandene Daten können dadurch verloren gehen. Eigene Abbilddateien können ohne Root beschrieben werden; reale Geräte benötigen entsprechende Zugriffsrechte.

## 2. Was macht der Befehl?

Daten- und Metadatenprofile bestimmen Verteilung und Redundanz getrennt. Voreinstellungen haben sich zwischen Versionen verändert. Ein neues Dateisystem besitzt eine gemeinsame UUID; bei mehreren Geräten ist die Gesamtstruktur zu berücksichtigen. Eine erfolgreiche Anlage ersetzt weder Mountkompatibilität noch Backup und Wiederherstellung.

Quelle, am 2026-11-13 gelesen: [mkfs.btrfs-Projekthandbuch](https://btrfs.readthedocs.io/en/latest/mkfs.btrfs.html)

## 3. Syntax

```text
mkfs.btrfs [OPTIONEN] ZIEL [WEITERE_ZIELE ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-L NAME` | Dateisystemlabel wählen; nicht mit Geräteidentität gleichsetzen. |
| `-d PROFIL`, `-m PROFIL` | Daten-/Metadatenprofil getrennt auswählen; Gerätezahl und Unterstützung beachten. |
| `-b GROESSE` | Sichtbare Größe je Gerät festlegen, nicht allgemeine belegte Nutzdatenmenge. |
| `-K`, `--nodiscard` | Whole-device-TRIM bei Anlage unterlassen; keine Einstellung für späteren Mountbetrieb. |
| `-O FEATURES` | On-Disk-Features wählen; ältere Kernel können sie nicht unterstützen. |
| `-r ORDNER` | Dateien in das neue Dateisystem aufnehmen; kein Mount nötig. |
| `-f` | Schutz gegen erkannte vorhandene Dateisysteme übergehen; keine Lernoption. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Musterplan: ein Ziel, Datenprofil single, Metadatenprofil dup
Keine ausgeführte Anlage und keine gemessene Ausgabe
```

`dup` hält zwei Metadatenkopien auf demselben Ziel und ist keine Unabhängigkeit von dessen Hardwareausfall. `single` benennt ein Allokationsprofil, nicht die Zahl aller Dateien. Defaultwerte nicht als zeitlos voraussetzen; konkrete Werkzeug- und Kernelversion gehören in einen echten Plan.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Anlage planen:** Profil, Größe und benötigte Features gemeinsam bestimmen. **Abbildaufbau:** Eine entbehrliche Datei mit definiertem Inhalt aufbauen, erst nach eigener gesonderter Erprobung.

## 7. Risiken, Nebenwirkungen und Vorsicht

Anlage kann vorhandene Signaturen und Daten überschreiben. Mehrere Ziele erweitern den Schadenbereich. Erzwungenes Überschreiben oder duplizierte UUIDs sind keine Reparatur. Redundanzprofile ersetzen kein externes Backup; problematische Profile nicht aus einer beliebigen Anleitung übernehmen. Kein Formatierungs- oder Scanlauf ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dateisystem erkannt, Anlage verweigert | Schutzsignal; nicht -f ergänzen, sondern Ziel und Datenbedarf klären. |
| Später nicht mountbar | Kernel unterstützt Feature/Geometrie nicht. |
| Weniger nutzbar als Rohkapazität | Metadaten, Profile und Allokation benötigen Platz. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; mkfs.btrfs fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `btrfs` | Verwaltung nach Anlage. |
| `mkfs.ext4` | Anderer Ersteller mit anderen Regeln. |
| `blkid` | Kennungen erkennen; erzeugt kein Dateisystem. |

Ausgangsdatensatz 228 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
