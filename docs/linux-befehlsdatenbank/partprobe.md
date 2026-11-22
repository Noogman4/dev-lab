---
id: "partprobe"
name: "partprobe"
command: "partprobe"
category: "Datentraeger & Dateisysteme"
language: "de"
root_required: true
risk_level: "caution"
tags: ["Datentraeger & Dateisysteme", "partprobe"]
status: "Ausgearbeitet; Quellen und Struktur geprüft; zur gemeinsamen Review"
source_catalog: "tools/netmon-linux-befehlsdatenbank-v1.csv"
source_record: 238
reviewed_at: "2026-11-13"
locally_checked_version: "Nicht praktisch geprüft; keine lokale Programmversion ermittelt"
---

# partprobe – Den Kernel über geänderte Partitionstabellen informieren

## 1. Kurzbeschreibung

`partprobe` informiert den Kernel über Partitionstabellenänderungen. Es ist weder ein Dateisystemprüfer noch bloß ein allgemeiner Statusbefehl. Das Aktualisieren des Kernelzustands ist eine administrative Systemaktion.

## 2. Was macht der Befehl?

Eine geschriebene Tabelle auf einem Datenträger und die aktuell vom Kernel verwendete Partitionssicht können voneinander abweichen. partprobe soll diese Sicht abgleichen, vergrößert aber kein Dateisystem. Aktive Nutzer des Geräts können die Übernahme verhindern. Vorherige Tabellenänderungen werden durch einen Fehler nicht automatisch rückgängig gemacht.

Quelle, am 2026-11-13 gelesen: [partprobe-Manpage](https://manpages.debian.org/trixie/parted/partprobe.8.en.html)

## 3. Syntax

```text
partprobe [-d] [-s] [ZIEL ...]
```

Großgeschriebene Platzhalter und eckige Klammern sind Syntaxnotation; sie werden nicht wörtlich eingegeben. Pfade mit Leerzeichen zitieren. Die installierte Implementierung muss zu den beschriebenen Optionen passen.

## 4. Wichtige Optionen

| Option / Funktion | Wirkung und Grenze |
| --- | --- |
| `-d`, `--dry-run` | Kernel nicht aktualisieren; keine Zusicherung, dass Ziele nicht gelesen werden. |
| `-s`, `--summary` | Zusammenfassung von Geräten und Partitionen ausgeben; nicht mit dry-run gleichsetzen. |
| `-h`, `--help` | Optionsübersicht anzeigen. |
| `-v`, `--version` | Programmversion anzeigen; kleines v verwenden. |

## 5. Beispiel erklärt Schritt für Schritt

### Schritt 1: Voraussetzungen und Zielgrenze verstehen

Dieses Lernbeispiel ist eine Dokumentationsübung. Es setzt keinen angeschlossenen Testdatenträger voraus. Alle Platzhalter bleiben Text; es wird weder ein echtes Gerät gewählt noch eine Änderung an Mounts, Diensten, Konten oder Systemkonfiguration vorgenommen. Für eine spätere echte Wartung müssten Zielidentität, Zugriffsrechte, aktueller Nutzungszustand und eine unabhängige Sicherung gesondert geklärt werden.

### Schritt 2: Das Muster lesen

**Nicht ausgeführtes Erklärungsmuster, keine gemessene Ausgabe und kein kopierfertiger Geräteauftrag:**

```text
partprobe -d -s ZIEL
Planfrage: Welche Partitionssicht würde verarbeitet?
```

Das Ziel bleibt ein Textplatzhalter. -d verhindert laut Handbuch die Kernelaktualisierung, während -s nur die Zusammenfassung anfordert. Ein echter Lauf würde Zugriffe und Voraussetzungen benötigen; hier wird auch der Dry-run nicht an einem realen Gerät ausprobiert. Ein leerer Bericht wäre ohne Meldungen, Ziel und Status nicht eindeutig.

### Schritt 3: Erwartung und Ergebnis trennen

Das Muster zeigt, welche Frage der Aufruf beantworten oder welche Änderung er anfordern würde. Eine erfolgreiche Syntax- oder Strukturprüfung bestätigt diese Wirkung nicht. Fehlermeldungen müssen zusammen mit Modus, Version und Ziel betrachtet werden. Ein angezeigter Zustand ist weder eine Integritätsprüfung aller Nutzdaten noch ein Nachweis zukünftiger Zuverlässigkeit. Ein unerwartetes Ergebnis ist kein Grund, Schutzoptionen zu umgehen oder den Aufruf mit erhöhten Rechten zu wiederholen.


## 6. Typische Anwendungsfälle

**Wartungsfolge verstehen:** Tabellenänderung, Kernelübernahme und Dateisystemänderung getrennt protokollieren. **Fehlerklärung:** Alte Kernelgrößen nicht mit einer nicht geschriebenen Tabelle verwechseln.

## 7. Risiken, Nebenwirkungen und Vorsicht

Ein Aufruf ohne ausdrückliche Ziele kann den Suchumfang erweitern. -s allein verhindert keine Systemaktion. Keine Partitionstabellenänderung, kein Kernel-Neueinlesen und kein erzwungenes Ablösen aktiver Dateisysteme als Dokumentationstest.

## 8. Häufige Fehler

| Beobachtung | Ursache und nächster Schritt |
| --- | --- |
| Kernel verwendet alte Partitionen | Aktive Nutzung oder Abgleich fehlgeschlagen; Wartungsablauf klären. |
| Dateisystemgröße bleibt gleich | partprobe ändert nur die Partitionssicht, nicht das Dateisystem. |
| Dry-run missverstanden | -d ist kein Nachweis einer erfolgreichen späteren Übernahme. |

## 9. Sichere Varianten oder Tipps für Einsteiger

Zuerst die lokale Hilfe und die Dokumentation der konkreten Implementierung vergleichen. Namen, Einheiten und Operationsmodus schriftlich festhalten. Schreibende Varianten und systemweite Sammeloptionen sind kein Ersatz für eine genaue Zielauswahl. Für dieses Dokument wurden keine Geräte- oder Systemoperationen ausgeführt.

**Prüfstand am 2026-11-13:** Nicht praktisch geprüft; keine lokale Programmversion ermittelt. Nicht praktisch geprüft; praktische Prüfung offen. Geräteverhalten, Rechtefälle und andere Versionen; praktische Prüfung offen. Quellenprüfung, Shellsyntaxprüfung und Funktionstest sind getrennte Nachweise. Die Strukturprüfung ersetzt keine fachliche Freigabe.

## 10. Verwandte Befehle

| Befehl | Zusammenhang |
| --- | --- |
| `parted` | Ändert Partitionstabellen. |
| `partx` | Weitere Kernel-Partitionsverwaltung. |
| `lsblk` | Zeigt vom System bekannte Gerätestrukturen. |

Ausgangsdatensatz 238 und feste Zuordnung gegen den eingefrorenen Katalog und die Original-CSV geprüft; deren Felder bleiben unverändert.
