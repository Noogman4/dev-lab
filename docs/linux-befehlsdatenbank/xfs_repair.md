---
id: "xfs_repair"
name: "xfs_repair"
command: "xfs_repair"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: false
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "xfs_repair"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 252
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; xfs_repair fehlt"
---

# xfs_repair – XFS-Strukturprüfung von Reparatur und Logverlust trennen

## 1. Kurzbeschreibung

`xfs_repair` prüft und repariert XFS-Strukturen. Ein gewöhnlicher Lauf kann schreiben. Das Ziel muss für einen korrekten Reparaturablauf ungemountet sein. Eigene Abbildkopien benötigen keine allgemeine Rootpflicht; reale Geräte entsprechende Rechte.

## 2. Was macht der Befehl?

Ein Metadatencheck prüft Inodes, Verzeichnisbezüge, Freiraumstrukturen und weitere Konsistenzregeln. Er ist keine Wiederherstellung aller Nutzdaten. Nicht verknüpfte Objekte können unter lost+found wieder erscheinen. Ein unsauberes Log kann xfs_repair nicht selbst wie der Kernel wiedergeben; eine Fehlermeldung dazu ist kein Auftrag, das Log wegzuwerfen.

Quelle, am 2026-11-13 gelesen: [xfs_repair-Projekthandbuch](https://manpages.debian.org/trixie/xfsprogs/xfs_repair.8.en.html)

## 3. Syntax

```text
xfs_repair [OPTIONEN] ZIEL
xfs_repair -n -f ABBILD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-n` | Nur scannen und vorgeschlagene Reparaturen melden, ohne das Dateisystem zu verändern. |
| `-f` | Ziel ist reguläre Abbilddatei; hier keine Force-Option wie bei vielen anderen Tools. |
| `-L` | Log auf null setzen, auch wenn dirty; kann Dateien/Nutzdaten verlieren lassen. |
| `-m MB` | Ungefähre Speichergrenze, keine harte Garantie. |
| `-l LOG`, `-r REALTIME` | Zusätzliche Bestandteile des konkreten XFS angeben. |
| `-e` | Erfolgreiche Reparatur mit gefundenen Problemen durch Status 4 kenntlich machen; nicht mit -n. |
| `-d` | Gefährliche Reparatur eines read-only gemounteten Dateisystems; keine Einsteigeroption. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
xfs_repair -n -f ABBILD
Fiktiver Status 2: dirty log verhindert weiteren Ablauf
```

Im No-modify-Modus bedeutet Status 1 erkannte Korruption, kann aber auch einen Laufzeitfehler begleiten; Meldungen sind nötig. Status 0 bestätigt den jeweiligen Prüflauf, nicht jede Nutzdatei. Status 2 zum Log führt hier zum Stopp, nicht zu -L oder einem unerlaubten Mount. Keine dieser Situationen wurde lokal erzeugt.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Offline-Diagnose:** Eine vollständige gesicherte XFS-Kopie unter kontrollierten Bedingungen untersuchen. **Reparaturplanung:** Logzustand, Lesbarkeit und Auswirkungen möglicher Metadatenverluste dokumentieren.

## 7. Risiken, Nebenwirkungen und Vorsicht

Reparatur kann Objekte entfernen, umbenennen, Quota- oder Attributinformationen verlieren. Hardware-I/O-Fehler sind eine andere Ebene; auf sterbenden Medien nicht blind reparieren. Lognullung und Force-Geometrie sind keine Standardfehlerbehebung. Programm fehlt; kein Mount und kein XFS-Lauf ausgeführt.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Dirty log | Eigenes Wiederanlauf-/Rettungskonzept erforderlich; keine automatische Nullung. |
| Abbild als Gerät missverstanden | -f kennzeichnet hier eine Datei. |
| Status 0 nach Reparatur | Kann trotz vorgenommener Änderungen erfolgen; Bericht auswerten, gegebenenfalls -e verstehen. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; xfs_repair fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `xfs_info` | Nur Geometrie anzeigen. |
| `xfs_metadump` | Spezielle Metadatenabbilder; nicht vollständiger Datenersatz. |
| `e2fsck` | Für ext, kein XFS-Ersatz. |

Ausgangsdatensatz 252 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
