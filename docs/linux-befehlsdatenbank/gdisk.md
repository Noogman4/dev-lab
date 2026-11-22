---
id: "gdisk"
name: "gdisk"
command: "gdisk"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "danger"
tags: ["Datentraeger & Dateisysteme", "gdisk"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 222
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; gdisk fehlt"
---

# gdisk – GPT-Tabellen und ihre Sicherungskopien verstehen

## 1. Kurzbeschreibung

`gdisk` ist der interaktive GPT-Partitionstabelleneditor aus GPT fdisk. Er kann vorhandene MBR-/BSD-Strukturen im Arbeitsspeicher nach GPT umsetzen. Das spätere Schreiben ist eine potenziell destruktive Änderung.

## 2. Was macht der Befehl?

GPT besitzt primäre und zusätzliche Tabellen-/Headerstrukturen. Ihre Prüfsummen betreffen die Partitionierung, nicht den Inhalt der Dateisysteme. Ein GPT-Partitionsname, ein Typcode und eine Dateisystembezeichnung sind verschiedene Dinge. Rohabbilder werden unterstützt, komprimierte oder spezielle VM-Container nicht einfach als gleichwertiges Ziel.

Quelle, am 2026-11-13 gelesen: [gdisk-Projekthandbuch](https://manpages.debian.org/trixie/gdisk/gdisk.8.en.html)

## 3. Syntax

```text
gdisk [-l] GERAET_ODER_ROHABBILD
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-l` | Tabelle des angegebenen Ziels lesen und beenden. |
| Dialog `p`, `i` | Zusammenfassung beziehungsweise Detaildaten einer Partition anzeigen. |
| Dialog `v` | Tabellenkonsistenz prüfen, keine vollständige automatische Reparatur. |
| Dialog `b` | Aktuelle Tabelle im Arbeitsspeicher als binäre Sicherung exportieren; schreibt Hostdatei. |
| Dialog `q` | Ohne Speichern der offenen Planänderungen beenden. |
| Dialog `w` | Tabellen schreiben; eine mögliche Konvertierung wird damit dauerhaft. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
Erfundenes Lernschema:
Partitionstyp: Linux filesystem (gdisk-Code 8300)
Partitionsname: DATEN
Dateisystemlabel: nicht daraus ableitbar
```

8300 ist eine interne Kurznotation des Werkzeugs für einen GPT-Typ, keine vollständige GUID und kein Beleg für ext4. `DATEN` benennt die Partitionstabelle, nicht automatisch das enthaltene Dateisystem. Ein Export mit `b` nach Planänderungen würde bereits den geänderten Speicherstand sichern, nicht zwingend die ursprüngliche Tabelle.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**GPT-Diagnose:** Haupt- und Sicherungstabelle vergleichen. **Umstiegsplanung:** MBR-zu-GPT-Konvertierung zusammen mit Startfähigkeit und Partitionstypen planen.

## 7. Risiken, Nebenwirkungen und Vorsicht

Konvertierung kann Bootfähigkeit verlieren lassen. Sortieren verändert Nummerierungen, die Konfigurationen referenzieren können. Eine Tabellensicherung enthält keine komplette Inhaltskopie. Wiederherstellungs- und Expertenmenüs können sofort weitreichende Veränderungen vorbereiten oder schreiben; keine reale Sitzung gestartet.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| MBR gefunden, GPT im Plan | Automatische Interpretation/Konvertierung im Arbeitsspeicher; nicht unbesehen schreiben. |
| Primär-/Backupdaten unterschiedlich | Diagnosebefund; kein zufälliges Wiederherstellungsmenü wählen. |
| Abbild nicht erkannt | Rohformat und Größe prüfen, keinen Container blind bearbeiten. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; gdisk fehlt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `sgdisk` | Nichtinteraktive GPT-Verwaltung. |
| `fdisk` | Unterstützt ebenfalls GPT und weitere Tabellen. |
| `blkid` | Signaturen und Kennungen einer anderen Ebene. |

Ausgangsdatensatz 222 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
